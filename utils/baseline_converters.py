"""Count DT resources for the scalability baselines without generating entries.

The counting rules and capacities follow the SwitchTree, IIsy, and LEO DT
converters. All thresholds are evaluated on the local quantized feature domain.
"""
from __future__ import annotations

import itertools
import math
from bisect import bisect_left

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
            ranges = [(1 + bisect_left(values, low), 1 + bisect_left(values, high))
                      for values, (low, high) in zip(thresholds, intervals)]
            keys = [tuple(ranges)] if range_match else itertools.product(
                *(range(low, high + 1) for low, high in ranges))
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
