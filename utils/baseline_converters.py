"""Count baseline resources and reconfiguration operations without generating entries.

The counting rules and capacities follow the SwitchTree, IIsy, and LEO DT
converters. All thresholds are evaluated on the local quantized feature domain.
"""
from __future__ import annotations

import itertools
import json
import math
from bisect import bisect_left, bisect_right
from functools import lru_cache

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.naive_bayes import CategoricalNB
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.utils.validation import check_is_fitted

from .constants import QUANTIZED_MIN, QUANTIZED_MAX


SYSTEMS = ("st", "st_tcam", "iisy", "iisy_range", "leo_tcam", "leo_sram")


def _prefix_count(low, high):
    count = 0
    while low <= high:
        size = low & -low if low else 1 << 16
        while size > high - low + 1:
            size >>= 1
        low += size
        count += 1
    return count


def _add(counts, table, amount, capacity):
    count = counts.get(table, 0) + amount
    if count > capacity:
        raise ValueError(f"{table} requires {count} entries; capacity is {capacity}")
    counts[table] = count


def _switchtree(model, tcam):
    tree = model.tree_
    max_depth = 19 if tcam else 13
    if model.n_features_in_ > 16 or tree.max_depth > max_depth:
        raise ValueError(f"SwitchTree supports 16 features and depth <= {max_depth}")
    counts = {"level0": 1}

    def visit(node, level, intervals):
        feature = int(tree.feature[node])
        low, high = intervals[feature]
        cutoff = math.floor(tree.threshold[node])
        for child, first, last in (
            (tree.children_left[node], low, min(high, cutoff)),
            (tree.children_right[node], max(low, cutoff + 1), high),
        ):
            if first > last:
                continue
            amount = _prefix_count(first, last) if tcam else last - first + 1
            capacity = 2048 if tcam else 128 * 2 ** (level - 1)
            _add(counts, f"level{level}", amount, capacity)
            if tree.children_left[child] != -1:
                bounds = list(intervals)
                bounds[feature] = (first, last)
                visit(child, level + 1, bounds)

    if tree.children_left[0] == -1:
        counts["level1"] = _prefix_count(QUANTIZED_MIN, QUANTIZED_MAX) if tcam else QUANTIZED_MAX - QUANTIZED_MIN + 1
    else:
        visit(0, 1, [(QUANTIZED_MIN, QUANTIZED_MAX)] * model.n_features_in_)
    return counts


def _iisy(model, range_match):
    tree = model.tree_
    feature_count = model.n_features_in_
    feature_limit, code_limit, predict_limit = (12, 63, 2048) if range_match else (20, 255, 262144)
    if feature_count > feature_limit:
        raise ValueError(f"IIsy supports at most {feature_limit} features")
    thresholds = [
        sorted(set(float(tree.threshold[node]) for node in range(tree.node_count)
                   if tree.feature[node] == feature))
        for feature in range(feature_count)
    ]
    if any(len(values) + 1 > code_limit for values in thresholds):
        raise ValueError("IIsy feature codes exceed the supported code width")
    counts = {}
    for feature, values in enumerate(thresholds):
        if range_match:
            first, amount = QUANTIZED_MIN, 0
            for threshold in values:
                last = min(QUANTIZED_MAX, math.floor(threshold))
                if first <= last:
                    amount += _prefix_count(first, last)
                    first = last + 1
            if first <= QUANTIZED_MAX:
                amount += _prefix_count(first, QUANTIZED_MAX)
        else:
            amount = QUANTIZED_MAX - QUANTIZED_MIN + 1
        _add(counts, f"feature{feature}", amount, 1024)

    seen = {}

    def visit(node, intervals):
        if tree.children_left[node] == -1:
            result = int(model.classes_[tree.value[node][0].argmax()])
            if range_match:
                keys = [tuple((1 + bisect_left(values, low), 1 + bisect_left(values, high))
                              for values, (low, high) in zip(thresholds, intervals))]
            else:
                # Enumerate reachable codes: multiple thresholds between integer
                # inputs can leave gaps in the numeric code range.
                keys = itertools.product(*(
                    sorted({1 + bisect_left(values, value) for value in range(low, high + 1)})
                    for values, (low, high) in zip(thresholds, intervals)))
            for key in keys:
                if key in seen and seen[key] != result:
                    raise ValueError("Conflicting IIsy prediction codes")
                seen[key] = result
                if len(seen) > predict_limit:
                    raise ValueError(f"IIsy prediction table exceeds {predict_limit} entries")
            return
        feature = int(tree.feature[node])
        low, high = intervals[feature]
        cutoff = math.floor(tree.threshold[node])
        for child, first, last in (
            (tree.children_left[node], low, min(high, cutoff)),
            (tree.children_right[node], max(low, cutoff + 1), high),
        ):
            if first <= last:
                bounds = list(intervals)
                bounds[feature] = (first, last)
                visit(child, bounds)

    visit(0, [(QUANTIZED_MIN, QUANTIZED_MAX)] * feature_count)
    counts["predict"] = len(seen)
    return counts


def _leo(model, tcam):
    tree = model.tree_
    if model.n_features_in_ > 10:
        raise ValueError("LEO supports at most 10 features")
    if tree.children_left[0] == -1:
        if tcam:
            raise ValueError("LEO TCAM requires a non-trivial tree")
        return {"layer_1_1": 1, "layer_2_1": 8}
    counts = {}
    capacities = {1: 1, 2: 8, 3: 32, 4: 128, 5: 512, 6: 2048, 7: 8192, 8: 32768, 9: 131072}

    def internal(node):
        return tree.children_left[node] != -1

    def slots(node):
        return (node,
                int(tree.children_left[node]) if internal(tree.children_left[node]) else None,
                int(tree.children_right[node]) if internal(tree.children_right[node]) else None)

    def add(table_index, slot, amount):
        capacity = (8 if table_index == 0 else 2048) if tcam else capacities[table_index]
        _add(counts, f"layer_{table_index}_{slot}", amount, capacity)

    for slot, node in enumerate(slots(0), start=0 if tcam else 1):
        if node is not None:
            add(0 if tcam else 1, slot, 1)

    current, layer = [0], 0
    while current:
        next_layer = []
        table_index = layer + (1 if tcam else 2)
        for root in current:
            for child in (tree.children_left[root], tree.children_right[root]):
                # An immediate leaf leaves both other ALU outcomes unconstrained.
                outcomes = [(child, 4)] if not internal(child) else [
                    (tree.children_left[child], 2), (tree.children_right[child], 2)]
                for target, expanded_count in outcomes:
                    if internal(target):
                        if layer >= (15 if tcam else 7):
                            raise ValueError("Tree exceeds the flattened LEO pipeline depth")
                        next_layer.append(int(target))
                        active_slots = slots(target)
                    else:
                        active_slots = (target,)
                    for slot, node in enumerate(active_slots, start=0 if tcam else 1):
                        if node is not None:
                            add(table_index, slot, 1 if tcam else expanded_count)
        current = next_layer
        layer += 1
    return counts


def count_dt_resources(model, system):
    """Return table/resource counts, or raise ValueError if undeployable."""
    if system not in SYSTEMS:
        raise ValueError(f"Unknown baseline system: {system}")
    if not isinstance(model, DecisionTreeClassifier):
        raise TypeError("Expected a DecisionTreeClassifier")
    check_is_fitted(model, ["tree_"])
    if any(int(value) != value or not 0 <= value < 256 for value in model.classes_):
        raise ValueError("Class IDs must be integers within 0..255")
    for feature, threshold in zip(model.tree_.feature, model.tree_.threshold):
        if feature >= 0 and not QUANTIZED_MIN - 1 <= math.floor(threshold) <= QUANTIZED_MAX:
            raise ValueError("Tree thresholds exceed the quantized domain")
    if system.startswith("st"):
        counts = _switchtree(model, system == "st_tcam")
    elif system.startswith("iisy"):
        counts = _iisy(model, system == "iisy_range")
    else:
        counts = _leo(model, system == "leo_tcam")
    total = sum(counts.values())
    tcam = total if system.endswith("tcam") or system == "iisy_range" else 0
    return {"total_entries": total, "sram_entries": total - tcam,
            "tcam_entries": tcam, "entries_by_table": counts}


class UnsupportedTransitionError(ValueError):
    """The baseline has no common layout for these model families."""


def _model_kind(model):
    for estimator, kind in (
        (DecisionTreeClassifier, "dt"), (RandomForestClassifier, "rf"),
        (IsolationForest, "if"), (CategoricalNB, "nb"), (KMeans, "km"), (SVC, "svm"),
    ):
        if isinstance(model, estimator):
            return kind
    if hasattr(model, "get_booster"):
        return "xgb"
    raise UnsupportedTransitionError(f"Unsupported estimator: {type(model).__name__}")


def _transition_layout(source, destination, system):
    if system not in SYSTEMS:
        raise ValueError(f"Unknown baseline system: {system}")
    kinds = {_model_kind(source), _model_kind(destination)}
    if system.startswith("leo"):
        supported = {"dt"}
    elif system.startswith("st"):
        supported = {"dt", "rf"}
    else:
        supported = {"dt", "rf", "xgb", "if"}
        if system == "iisy":
            supported |= {"svm", "nb", "km"}
    if not kinds <= supported:
        raise UnsupportedTransitionError(f"{system} does not support {'/'.join(sorted(kinds))}")
    if kinds <= {"dt", "rf", "xgb", "if"}:
        if "rf" in kinds:
            return "rf"
        return "dt" if kinds == {"dt"} else "xgb"
    if kinds <= {"nb", "km"}:
        return "nb_km"
    if kinds == {"svm"}:
        if len(source.classes_) != len(destination.classes_):
            raise UnsupportedTransitionError("IIsy SVM models require the same class layout")
        return "svm"
    raise UnsupportedTransitionError(f"{system} has no shared layout for {'/'.join(sorted(kinds))}")


def _encoded_classes(model):
    classes = np.asarray(model.classes_)
    if classes.ndim != 1 or any(int(value) != value or not 0 <= value < 256 for value in classes):
        raise ValueError("Class IDs must be integers within 0..255")
    return tuple(int(value) for value in classes)


def _sklearn_spec(estimator, features, mapping=None, isolation=False, integer_codes=False):
    """Return integer code boundaries and (output, input intervals) for reachable leaves."""
    tree = estimator.tree_
    mapping = tuple(range(features)) if mapping is None else tuple(int(value) for value in mapping)
    if not mapping or any(value < 0 or value >= features for value in mapping):
        raise ValueError("Invalid estimator feature mapping")
    thresholds = [set() for _ in range(features)]
    for feature, threshold in zip(tree.feature, tree.threshold):
        if feature >= 0:
            if feature >= len(mapping):
                raise ValueError("Tree references an unavailable feature")
            thresholds[mapping[feature]].add(float(threshold))
    boundaries = []
    for values in thresholds:
        points = [math.floor(value) + 1 for value in sorted(values)]
        # IF and DT-to-XGB converters deduplicate integer split points.
        boundaries.append(tuple(sorted(set(points))) if integer_codes else tuple(points))
    leaves = []

    def visit(node, depth, intervals):
        if tree.children_left[node] == -1:
            if isolation:
                samples = int(tree.n_node_samples[node])
                adjustment = 0 if samples <= 1 else (1 if samples == 2 else
                    2 * (math.log(samples - 1) + float(np.euler_gamma)) - 2 * (samples - 1) / samples)
                output = depth + adjustment
            else:
                output = int(estimator.classes_[tree.value[node][0].argmax()])
            leaves.append((output, intervals))
            return
        feature = mapping[tree.feature[node]]
        low, high = intervals[feature]
        cutoff = math.floor(tree.threshold[node])
        for child, first, last in (
            (tree.children_left[node], low, min(high, cutoff)),
            (tree.children_right[node], max(low, cutoff + 1), high),
        ):
            if first <= last:
                bounds = list(intervals)
                bounds[feature] = (first, last)
                visit(child, depth + 1, tuple(bounds))

    visit(0, 0, ((QUANTIZED_MIN, QUANTIZED_MAX),) * features)
    return boundaries, leaves


def _xgb_specs(model, features, tree_limit):
    booster = model.get_booster()
    learner = json.loads(booster.save_config())["learner"]
    objective = learner["objective"]["name"]
    classes = _encoded_classes(model)
    if not objective.startswith(("binary:", "multi:")):
        raise ValueError(f"Unsupported XGBoost classification objective: {objective}")
    if int(learner["gradient_booster"].get("gbtree_model_param", {}).get("num_parallel_tree", 1)) != 1:
        raise ValueError("IIsy supports one boosted tree per round/class")
    params = learner["learner_model_param"]
    scores = str(params.get("base_score", "0.5")).strip("[]").split(",")
    scores = [float(value) for value in scores]
    if objective.startswith("multi:"):
        if int(params["num_class"]) != len(classes) or len(scores) not in (1, len(classes)):
            raise ValueError("XGBoost class metadata does not match the estimator")
    dumps = booster.get_dump(dump_format="json")
    if not 1 <= len(dumps) <= tree_limit:
        raise ValueError(f"IIsy supports at most {tree_limit} tree outputs; got {len(dumps)}")
    if objective.startswith("multi:") and len(dumps) % len(classes):
        raise ValueError("XGBoost tree count must be divisible by the class count")
    specs = []
    for dump in dumps:
        root = json.loads(dump)
        nodes, thresholds, leaves = {}, [set() for _ in range(features)], []

        def index(node):
            nodes[node["nodeid"]] = node
            if "leaf" not in node:
                name = str(node["split"])
                feature = int(name[1:] if name.startswith("f") else name)
                if not 0 <= feature < features:
                    raise ValueError("XGBoost references an unavailable feature")
                thresholds[feature].add(float(node["split_condition"]))
            for child in node.get("children", []):
                index(child)

        def visit(node, intervals):
            if "leaf" in node:
                weight = float(node["leaf"])
                if not math.isfinite(weight):
                    raise ValueError("XGBoost leaf weights must be finite")
                leaves.append((weight, intervals))
                return
            name = str(node["split"])
            feature = int(name[1:] if name.startswith("f") else name)
            low, high = intervals[feature]
            cutoff = math.ceil(float(node["split_condition"]))
            for child, first, last in (
                (node["yes"], low, min(high, cutoff - 1)),
                (node["no"], max(low, cutoff), high),
            ):
                if first <= last:
                    bounds = list(intervals)
                    bounds[feature] = (first, last)
                    visit(nodes[child], tuple(bounds))

        index(root)
        visit(root, ((QUANTIZED_MIN, QUANTIZED_MAX),) * features)
        specs.append(([tuple(math.ceil(value) for value in sorted(values))
                       for values in thresholds], leaves))
    return specs


def _reachable_output_count(specs, features, limit):
    outputs = set()

    def visit(index, intervals, tokens):
        if index == len(specs):
            outputs.add(tokens)
            if len(outputs) > limit:
                raise ValueError(f"Prediction table exceeds {limit} entries")
            return
        for output, bounds in specs[index][1]:
            merged = tuple((max(low, first), min(high, last))
                           for (low, high), (first, last) in zip(intervals, bounds))
            if all(low <= high for low, high in merged):
                visit(index + 1, merged, tokens + (output,))

    visit(0, ((QUANTIZED_MIN, QUANTIZED_MAX),) * features, ())
    return len(outputs)


def _iisy_tree_count(model, kind, layout, tcam):
    features = int(model.n_features_in_)
    feature_limit, tree_limit, code_limit = (10, 7, 63) if tcam else (24, 8, 31)
    if not 1 <= features <= feature_limit:
        raise ValueError(f"IIsy {layout} layout supports 1..{feature_limit} features")
    if kind == "xgb":
        specs = _xgb_specs(model, features, tree_limit)
    else:
        trees = [model] if kind == "dt" else list(model.estimators_)
        if not 1 <= len(trees) <= tree_limit:
            raise ValueError(f"IIsy supports 1..{tree_limit} trees; got {len(trees)}")
        specs = []
        for index, tree in enumerate(trees):
            mapping = model.estimators_features_[index] if kind == "if" else None
            specs.append(_sklearn_spec(tree, features, mapping, kind == "if",
                                       kind == "if" or (kind == "dt" and layout == "xgb")))
    if any(len(values) + 1 > code_limit for thresholds, _ in specs for values in thresholds):
        raise ValueError(f"IIsy tree feature codes exceed {code_limit}")
    if kind == "if":
        if not math.isfinite(float(model.offset_)) or model.max_samples_ < 1:
            raise ValueError("Invalid IsolationForest scoring metadata")
    if kind in {"xgb", "if"}:
        if layout == "rf" and kind == "xgb":
            token_count = max(len({output for output, _ in leaves}) for _, leaves in specs)
        else:
            token_count = len({output for _, leaves in specs for output, _ in leaves})
        if token_count > 65535:
            raise ValueError("IIsy leaf output tokens exceed 16 bits")
    counts = {}
    for feature in range(features):
        if tcam:
            points = sorted({QUANTIZED_MIN, QUANTIZED_MAX + 1} | {
                point for thresholds, _ in specs for point in thresholds[feature]
                if QUANTIZED_MIN < point <= QUANTIZED_MAX})
            amount = sum(_prefix_count(low, next_low - 1) for low, next_low in zip(points, points[1:]))
        else:
            amount = QUANTIZED_MAX - QUANTIZED_MIN + 1
        _add(counts, f"feature{feature}", amount, 1024)
    for index, (thresholds, leaves) in enumerate(specs):
        capacity = 1024 if tcam else (32768 if layout == "rf" and index == 1 else 65536)
        seen = {}
        for output, intervals in leaves:
            options = [tuple(sorted({1 + bisect_right(values, value) for value in range(low, high + 1)}))
                       for values, (low, high) in zip(thresholds, intervals)]
            keys = [tuple((values[0], values[-1]) for values in options)] if tcam else itertools.product(*options)
            for key in keys:
                if key in seen and seen[key] != output:
                    raise ValueError("Conflicting IIsy leaf lookup codes")
                seen[key] = output
                if len(seen) > capacity:
                    raise ValueError(f"Tree {index} lookup exceeds {capacity} entries")
        _add(counts, f"lookup{index}", len(seen), capacity)
    predict_limit = 32768 if tcam or layout == "xgb" else 65536
    if kind in {"dt", "rf"}:
        prediction_count = math.prod(len({output for output, _ in leaves}) for _, leaves in specs)
    else:
        prediction_count = _reachable_output_count(specs, features, predict_limit)
    _add(counts, "predict", prediction_count, predict_limit)
    return sum(counts.values())


def _iisy_linear_count(model, kind):
    features = int(model.n_features_in_)
    domain = np.arange(QUANTIZED_MIN, QUANTIZED_MAX + 1)
    if kind == "km":
        centers = np.asarray(model.cluster_centers_, dtype=float)
        if centers.shape != (2, features) or not np.isfinite(centers).all():
            raise ValueError("IIsy KM requires two finite cluster centers")
        # The converter selects a distance divisor until the signed accumulator fits.
        if not np.isfinite((domain[None, :] - centers[:, :, None]) ** 2).all():
            raise ValueError("KMeans distances exceed the supported numeric range")
        extra = 0
        feature_limit = 15
    else:
        classes = _encoded_classes(model)
        if classes != tuple(range(len(classes))):
            raise ValueError("IIsy linear models require consecutive encoded class IDs")
        if kind == "nb":
            if len(classes) != 2:
                raise ValueError("IIsy NB supports only two classes")
            probabilities = [np.asarray(values, dtype=float) for values in model.feature_log_prob_]
            priors = np.asarray(model.class_log_prior_, dtype=float)
            if len(probabilities) != features or priors.shape != (2,) or not np.isfinite(priors).all():
                raise ValueError("Invalid CategoricalNB probability metadata")
            if any(values.ndim != 2 or values.shape[0] != 2 or values.shape[1] <= QUANTIZED_MAX
                   or not np.isfinite(values[:, domain]).all() for values in probabilities):
                raise ValueError("CategoricalNB probabilities must cover the quantized domain")
            contributions = np.array([values[1, domain] - values[0, domain] for values in probabilities])
            prior = priors[1] - priors[0]
            feature_limit, extra = 15, 1
        else:
            if model.kernel != "linear" or not 2 <= len(classes) <= 6:
                raise ValueError("IIsy SVM requires a linear kernel and 2..6 classes")
            feature_limit = {2: 15, 3: 15, 4: 14, 5: 13, 6: 12}[len(classes)]
            pairs = list(itertools.combinations(classes, 2))
            coefficients = model.coef_.toarray() if hasattr(model.coef_, "toarray") else np.asarray(model.coef_)
            intercepts = np.asarray(model.intercept_)
            if coefficients.shape != (len(pairs), features) or intercepts.shape != (len(pairs),):
                raise ValueError("IIsy SVM requires one-vs-one coefficient and intercept arrays")
            contributions = -coefficients[:, :, None] * domain
            prior = -intercepts
            votes = set()
            for signs in itertools.product((0, 1), repeat=len(pairs)):
                counts = [0] * len(classes)
                for pair, sign in zip(pairs, signs):
                    counts[pair[sign]] += 1
                votes.add(tuple(counts))
            extra = 2 + len(votes)
        if not np.isfinite(contributions).all() or not np.isfinite(prior).all():
            raise ValueError("Non-finite IIsy fixed-point contributions")
        quantized = np.rint(contributions)
        minimum = np.rint(prior) + quantized.min(axis=-1).sum(axis=-1)
        maximum = np.rint(prior) + quantized.max(axis=-1).sum(axis=-1)
        if np.any(minimum < -32767) or np.any(maximum > 32767):
            raise ValueError("IIsy accumulator overflows even at fixed-point scale 1")
    if not 1 <= features <= feature_limit or len(domain) > 1024:
        raise ValueError(f"IIsy {kind} supports 1..{feature_limit} features and 1024 values per feature")
    return features * len(domain) + extra


@lru_cache(maxsize=256)
def _model_count_result(model, system, layout):
    # Keep failures as well as successes cached for the all-pairs notebook evaluation.
    try:
        kind = _model_kind(model)
        if kind not in {"if", "km"}:
            _encoded_classes(model)
        if layout == "dt":
            total = count_dt_resources(model, system)["total_entries"]
        elif system.startswith("st"):
            trees = [model] if kind == "dt" else list(model.estimators_)
            if not 1 <= len(trees) <= 3 or model.n_features_in_ > 16:
                raise ValueError("SwitchTree RF layout supports 1..3 trees and at most 16 features")
            if max(_encoded_classes(model)) >= 255 or any(tree.tree_.max_depth > 11 for tree in trees):
                raise ValueError("SwitchTree RF layout requires depth <= 11 and class IDs < 255")
            total = sum(sum(_switchtree(tree, system == "st_tcam").values()) for tree in trees)
            votes = math.prod(len({output for output, _ in _sklearn_spec(tree, model.n_features_in_)[1]})
                              for tree in trees)
            if votes > 32768:
                raise ValueError("SwitchTree prediction table exceeds 32768 entries")
            total += votes
        elif layout in {"nb_km", "svm"}:
            total = _iisy_linear_count(model, kind)
        else:
            total = _iisy_tree_count(model, kind, layout, system == "iisy_range")
        return int(total), None
    except (ValueError, TypeError, AttributeError) as error:
        return None, error


def count_reconfiguration_operations(source_model, destination_model, system):
    """Count delete-then-add operations in a shared baseline layout.

    Raises UnsupportedTransitionError for absent model/layout support, and
    ValueError for undeployable models. Cached model counts assume fitted models
    are not mutated; use _model_count_result.cache_clear() after modifying one.
    """
    layout = _transition_layout(source_model, destination_model, system)
    totals = []
    for model in (source_model, destination_model):
        total, error = _model_count_result(model, system, layout)
        if error is not None:
            raise ValueError(f"{_model_kind(model).upper()} conversion failed: {error}") from error
        totals.append(total)
    return {"ADD": totals[1], "MOD": 0, "DEL": totals[0]}
