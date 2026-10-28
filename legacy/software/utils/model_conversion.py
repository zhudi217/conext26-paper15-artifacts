from __future__ import annotations

import heapq
import itertools
import json
import math
from collections import deque
from dataclasses import asdict, dataclass, replace
from numbers import Integral
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.feature_selection import RFE
from sklearn.linear_model import LogisticRegression, Perceptron
from sklearn.naive_bayes import CategoricalNB, GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier, _tree
from sklearn.utils.validation import check_is_fitted

from .constants import QUANTIZED_MIN, QUANTIZED_MAX


UNUSED_FEATURE_VALUE = 1023
DT_PREDICTION_SLOT = 0
DT_PREDICTION_TOKEN_OFFSET = 0
RF_PREDICTION_TOKEN_OFFSET = 1


@dataclass(frozen=True)
class P4Config:
    P4_BLOCK_COUNT: int = 6
    P4_PREDICTION_SLOTS: int = 6
    P4_LANE_COUNT: int = 7
    P4_MAX_FEATURES: int = 42
    P4_CLASS_BITS: int = 8
    P4_CODE_BITS: int = 8
    P4_SUBTREE_NODE_LIMIT_MAX: int = 7
    P4_SELECT_TABLE_CAPACITY: int = 256
    P4_COMPUTE_TABLE_CAPACITY: int = 1024
    P4_AGGREGATE_TABLE_CAPACITY: int = 32768
    P4_FINAL_PREDICT_TABLE_CAPACITY: int = 32768
    P4_ACC_BITS: int = 16
    P4_LINEAR_HYPERPLANE_COUNT: int = 3
    P4_LINEAR_BUCKET_COUNT: int = 7
    P4_LINEAR_ACC_TABLE_CAPACITY: int = 8192
    P4_FINAL_LINEAR_TABLE_CAPACITY: int = 8
    P4_GROUP_LAYOUT: tuple[tuple[int, ...], ...] = (
        (0, 1, 2, 21, 28, 35),
        (3, 4, 5, 22, 29, 36),
        (6, 7, 8, 23, 30, 37),
        (9, 10, 11, 24, 31, 38),
        (12, 13, 14, 25, 32, 39),
        (15, 16, 17, 26, 33, 40),
        (18, 19, 20, 27, 34, 41),
    )


SRAM_P4_CONFIG = P4Config()
TCAM_P4_CONFIG = replace(SRAM_P4_CONFIG, P4_CODE_BITS=6, P4_AGGREGATE_TABLE_CAPACITY=512)
DEFAULT_P4_CONFIG = SRAM_P4_CONFIG


@dataclass(frozen=True)
class TableEntry:
    table: str
    match: dict[str, int | tuple[int, int]]
    action: str
    params: dict[str, int]


@dataclass(frozen=True)
class InstallationPlan:
    p4_name: str
    tables_to_clear: list[str]
    operations: list[tuple[str, list[TableEntry]]]
    baseline_snapshot: str | None = None


@dataclass
class ConversionResult:
    output_path: Path
    entries: list[TableEntry]
    metadata: dict[str, Any]
    plan: InstallationPlan | None = None

    @property
    def metadata_path(self) -> Path:
        return self.output_path.with_name(f"{self.output_path.stem}_metadata.json")

    @property
    def snapshot_path(self) -> Path:
        return self.output_path.with_name(f"{self.output_path.stem}_entries.json")


def resolve_p4_config(config: dict[str, Any], tcam: bool = False) -> P4Config:
    return TCAM_P4_CONFIG if tcam else SRAM_P4_CONFIG


def bfrt_match_name(field_name: str) -> str:
    return field_name.split(".")[-1].replace("[", "_").replace(":", "_").replace("]", "_")


def get_bfrt_prefix(tcam=False):
    return "bfrt.ss_range.pipe" if tcam else "bfrt.ss.pipe"


def index_entries(entries):
    indexed = {}
    for entry in entries:
        key = (entry.table, json.dumps(entry.match, sort_keys=True))
        if key in indexed and (indexed[key].action, indexed[key].params) != (entry.action, entry.params):
            raise ValueError(f"conflicting entries for key {key}")
        indexed[key] = entry
    return indexed


def classify_operations(old_entries, new_entries):
    old_index = index_entries(old_entries)
    new_index = index_entries(new_entries)
    add = [new_index[key] for key in sorted(new_index.keys() - old_index.keys())]
    mod = [new_index[key] for key in sorted(new_index.keys() & old_index.keys())
           if (old_index[key].action, old_index[key].params) != (new_index[key].action, new_index[key].params)]
    delete = [old_index[key] for key in sorted(old_index.keys() - new_index.keys())]
    unchanged = len(new_index) - len(add) - len(mod)
    return add, mod, delete, unchanged


def shapeshifter_table_names():
    # Match the tables declared by the SRAM and TCAM ShapeShifter P4 programs.
    table_names = ["SwitchIngress.version_t"]
    for block_index in range(DEFAULT_P4_CONFIG.P4_BLOCK_COUNT):
        for lane in range(DEFAULT_P4_CONFIG.P4_LANE_COUNT):
            table_names.extend((
                table_name_select(block_index, lane),
                table_name_compute(block_index, lane),
            ))
        table_names.append(table_name_aggregate(block_index))
    table_names.extend((table_name_linear_acc(), table_name_final(), table_name_final_linear()))
    return table_names


def make_installation_plan(entries, *, tcam=False, old_entries=None, baseline_snapshot=None):
    add, mod, delete, _ = classify_operations(old_entries or [], entries)
    return InstallationPlan(
        p4_name=get_bfrt_prefix(tcam).split(".")[1],
        tables_to_clear=shapeshifter_table_names() if old_entries is None else [],
        operations=[("mod", mod), ("delete", delete), ("add", add)],
        baseline_snapshot=baseline_snapshot,
    )


def emit_bfrt_python(path: Path, entries: list[TableEntry], *, tcam=False, old_entries=None, plan=None) -> None:
    if plan is None:
        plan = make_installation_plan(entries, tcam=tcam, old_entries=old_entries)
    lines = [
        f"bfrt.{plan.p4_name}.pipe.{table_name}.clear(batch=True)"
        for table_name in plan.tables_to_clear
    ]
    lines.append("")
    for operation, entry in ((operation, entry) for operation, group in plan.operations for entry in group):
        action_name = entry.action.split(".")[-1]
        arguments = []
        for field, value in entry.match.items():
            name = bfrt_match_name(field)
            arguments.extend(
                [f"{name}_start={value[0]}", f"{name}_end={value[1]}"]
                if isinstance(value, (tuple, list)) else [f"{name}={value}"]
            )
        if operation != "delete":
            arguments.extend(f"{name}={value}" for name, value in entry.params.items())
        method = "delete" if operation == "delete" else f"{operation}_with_{action_name}"
        lines.append(f"bfrt.{plan.p4_name}.pipe.{entry.table}.{method}({', '.join(arguments)})")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def convert_model(model, config, tcam, *, selector, label_encoder, output_path):
    if isinstance(model, DecisionTreeClassifier):
        converter = convert_tcam_dt if tcam else convert_dt
    elif isinstance(model, RandomForestClassifier):
        converter = convert_tcam_rf if tcam else convert_rf
    elif isinstance(model, IsolationForest):
        converter = convert_tcam_if if tcam else convert_if
    elif isinstance(model, SVC):
        converter = convert_svm
    elif isinstance(model, (LogisticRegression, Perceptron, GaussianNB, CategoricalNB, KMeans)):
        converter = convert_linear
    else:
        try:
            from xgboost import Booster, XGBClassifier
        except ImportError:
            raise TypeError("unsupported SS model; XGBoost support requires xgboost") from None
        if not isinstance(model, (Booster, XGBClassifier)):
            raise TypeError("SS conversion supports DT, RF, XGB, IF, linear SVC, LR, NB, SLP, and KM models")
        converter = convert_tcam_xgb if tcam else convert_xgb
    if tcam and converter in (convert_svm, convert_linear):
        raise NotImplementedError("TCAM conversion supports only DT, RF, XGB, and IF models")
    p4_config = resolve_p4_config(config, tcam=tcam)
    entries, metadata = converter(model, selector, label_encoder, p4_config)
    result = ConversionResult(Path(output_path), entries, metadata)
    prefix = get_bfrt_prefix(tcam)
    baseline_path = result.output_path.parent / f"{prefix.split('.')[1]}_installed_entries.json"
    old_entries = None
    baseline_snapshot = None
    if baseline_path.exists():
        baseline_snapshot = baseline_path.read_text(encoding="utf-8")
        snapshot = json.loads(baseline_snapshot)
        if snapshot["bfrt_prefix"] != prefix:
            raise ValueError("installed snapshot belongs to a different BFRT pipeline")
        old_entries = [TableEntry(**entry) for entry in snapshot["entries"]]
    result.plan = make_installation_plan(
        result.entries, tcam=tcam, old_entries=old_entries, baseline_snapshot=baseline_snapshot,
    )
    emit_bfrt_python(result.output_path, result.entries, plan=result.plan)
    # install_model promotes this candidate only after a successful installation.
    result.snapshot_path.write_text(
        json.dumps({"bfrt_prefix": prefix, "entries": [asdict(entry) for entry in entries]}, indent=2) + "\n",
        encoding="utf-8",
    )
    metadata["installed_snapshot_path"] = str(baseline_path)
    metadata["snapshot_path"] = str(result.snapshot_path)
    result.metadata_path.write_text(
        json.dumps(result.metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8",
    )
    return result


def selected_feature_indices(selector, feature_count):
    if not isinstance(selector, RFE):
        raise TypeError("SS conversion requires a fitted RFE selector")
    check_is_fitted(selector, ["support_"])
    feature_indices = selector.get_support(indices=True).tolist()
    if not feature_indices or len(feature_indices) != feature_count:
        raise ValueError("RFE selected feature count must match the model input feature count")
    return feature_indices


def validate_model_inputs(model, selector, label_encoder):
    if model.n_outputs_ != 1:
        raise ValueError("SS conversion requires a single-output classifier")
    feature_indices = selected_feature_indices(selector, model.n_features_in_)
    if not isinstance(label_encoder, LabelEncoder):
        raise TypeError("SS conversion requires a fitted LabelEncoder")
    check_is_fitted(label_encoder, ["classes_"])
    for class_id in model.classes_.tolist():
        if not isinstance(class_id, Integral) or not 0 <= class_id < len(label_encoder.classes_):
            raise ValueError("model classes must be valid integer label-encoder indices")
    return feature_indices


def validate_dt_inputs(model, selector, label_encoder, p4_config):
    check_is_fitted(model, ["tree_"])
    feature_indices = validate_model_inputs(model, selector, label_encoder)
    for class_id in model.classes_.tolist():
        dt_prediction_value(class_id, p4_config=p4_config)
    if is_leaf(model, 0):
        raise ValueError("SS DT conversion requires a non-trivial decision tree")
    return feature_indices


def convert_tcam_dt(model, selector, label_encoder, p4_config):
    feature_indices = validate_dt_inputs(model, selector, label_encoder, p4_config)
    compile_errors = []
    try:
        states, outcomes, transitions = build_states_by_block(
            model, len(feature_indices), QUANTIZED_MIN, QUANTIZED_MAX,
            lambda root_node_id, root_intervals: (root_node_id,),
            p4_config=p4_config,
            pack_block=make_tcam_block_packer(model, len(feature_indices), p4_config),
        )
        return compile_tcam_tree_entries(model, feature_indices, states, outcomes, transitions, p4_config)
    except ValueError as error:
        compile_errors.append(f"capacity-aware: {error}")
    for node_limit in range(p4_config.P4_SUBTREE_NODE_LIMIT_MAX, 0, -1):
        try:
            states, outcomes, transitions = build_states_by_block(
                model, len(feature_indices), QUANTIZED_MIN, QUANTIZED_MAX,
                lambda root_node_id, root_intervals: pack_internal_subtree(model, root_node_id, node_limit),
                p4_config=p4_config,
            )
            return compile_tcam_tree_entries(model, feature_indices, states, outcomes, transitions, p4_config)
        except ValueError as error:
            compile_errors.append(f"limit {node_limit}: {error}")
    raise ValueError("SS TCAM DT conversion failed after packing attempts: " + " | ".join(compile_errors))


def convert_dt(model, selector, label_encoder, p4_config):
    feature_indices = validate_dt_inputs(model, selector, label_encoder, p4_config)
    compile_errors = []
    for node_limit in range(p4_config.P4_SUBTREE_NODE_LIMIT_MAX, 0, -1):
        try:
            return compile_entries_for_limit(
                clf=model,
                feature_indices=feature_indices,
                node_limit=node_limit,
                p4_config=p4_config,
            )
        except ValueError as error:
            compile_errors.append(f"limit {node_limit}: {error}")
    raise ValueError(
        "SS DT conversion failed after packing attempts: " + " | ".join(compile_errors)
    )

@dataclass(frozen=True)
class PackedState:
    block_index: int
    state_id: int
    root_node_id: int
    root_intervals: dict[int, tuple[int, int]]
    included_nodes: tuple[int, ...]
    used_features: tuple[int, ...]


@dataclass(frozen=True)
class StateOutcome:
    intervals: dict[int, tuple[int, int]]
    leaf_class: int | None = None
    next_root_node_id: int | None = None


@dataclass
class DuplicatedFeatureLaneMapping:
    copies_by_feature: dict[int, tuple[int, ...]]
    physical_field_by_feature_lane: dict[tuple[int, int], int]
    unused_physical_field_by_lane: dict[int, int]
    lane_by_state_feature: dict[tuple[int, int], int]
    thresholds_by_block_lane: dict[tuple[int, int], list[int]]


def table_name_select(block_index: int, lane: int) -> str:
    return f"SwitchEgress.ML_BLOCK_{block_index}.select_feat_{lane}_t"


def table_name_compute(block_index: int, lane: int) -> str:
    return f"SwitchEgress.ML_BLOCK_{block_index}.compute_feat_{lane}_t"


def table_name_aggregate(block_index: int) -> str:
    return f"SwitchEgress.ML_BLOCK_{block_index}.block_{block_index}_aggregate_t"


def table_name_final() -> str:
    return "SwitchEgress.PRED_BLOCK.block_final_tree_predict_t"


def table_name_linear_acc() -> str:
    return "SwitchEgress.LINEAR_ACC_BLOCK.block_6_aggregate_t"


def table_name_final_linear() -> str:
    return "SwitchEgress.PRED_BLOCK.block_final_linear_predict_t"


def table_capacity(table_name: str, *, p4_config: P4Config = DEFAULT_P4_CONFIG) -> tuple[int, str] | None:
    if table_name == table_name_linear_acc():
        return p4_config.P4_LINEAR_ACC_TABLE_CAPACITY, "p4/sram/shapeshifter/linear_acc_block.p4"
    if table_name == table_name_final_linear():
        return p4_config.P4_FINAL_LINEAR_TABLE_CAPACITY, "p4/sram/shapeshifter/predict_block.p4"
    if table_name == table_name_final():
        return p4_config.P4_FINAL_PREDICT_TABLE_CAPACITY, "p4/sram/shapeshifter/predict_block.p4"

    for block_index in range(p4_config.P4_BLOCK_COUNT):
        if table_name == table_name_aggregate(block_index):
            return p4_config.P4_AGGREGATE_TABLE_CAPACITY, "p4/sram/shapeshifter/ml_block.p4"
        for lane in range(p4_config.P4_LANE_COUNT):
            if table_name == table_name_select(block_index, lane):
                return p4_config.P4_SELECT_TABLE_CAPACITY, "p4/sram/shapeshifter/ml_block.p4"
            if table_name == table_name_compute(block_index, lane):
                return p4_config.P4_COMPUTE_TABLE_CAPACITY, "p4/sram/shapeshifter/ml_block.p4"
    return None


def add_entry_count(entry_counts: dict[str, int], table_name: str, amount: int = 1, *, p4_config: P4Config = DEFAULT_P4_CONFIG, tcam=False) -> None:
    if amount <= 0:
        return
    new_count = entry_counts.get(table_name, 0) + amount
    capacity = table_capacity(table_name, p4_config=p4_config)
    if capacity is not None:
        max_count, p4_path = capacity
        if tcam:
            p4_path = p4_path.replace("/sram/", "/tcam/")
        if new_count > max_count:
            raise ValueError(
                f"{table_name} would need {new_count} entries, "
                f"but {p4_path} sets size = {max_count}"
            )
    entry_counts[table_name] = new_count


def is_leaf(clf: DecisionTreeClassifier, node_id: int) -> bool:
    return clf.tree_.children_left[node_id] == _tree.TREE_LEAF


def leaf_result(clf: DecisionTreeClassifier, node_id: int) -> int:
    class_index = int(clf.tree_.value[node_id][0].argmax())
    return int(clf.classes_[class_index])


def node_feature_slot(
    clf: DecisionTreeClassifier,
    node_id: int,
    selected_feature_count: int,
) -> int:
    feature_id = int(clf.tree_.feature[node_id])
    if feature_id < 0 or feature_id >= selected_feature_count:
        raise ValueError(
            f"tree node {node_id} references feature slot {feature_id}, but only "
            f"{selected_feature_count} selected features are available"
        )
    return feature_id


def split_floor(clf: DecisionTreeClassifier, node_id: int) -> int:
    threshold = float(clf.tree_.threshold[node_id])
    cutoff = int(math.floor(threshold))
    if cutoff < QUANTIZED_MIN - 1 or cutoff > QUANTIZED_MAX:
        raise ValueError(
            f"node {node_id} threshold floor {cutoff} exceeds the SS domain "
            f"{QUANTIZED_MIN}..{QUANTIZED_MAX}"
        )
    return cutoff


def dt_prediction_value(class_id: int, *, p4_config: P4Config = DEFAULT_P4_CONFIG) -> int:
    value = int(class_id) + DT_PREDICTION_TOKEN_OFFSET
    if value < 0 or value >= (1 << p4_config.P4_CLASS_BITS):
        raise ValueError(f"DT_sram prediction value {value} does not fit bit<{p4_config.P4_CLASS_BITS}>")
    return value


def group_layout_for_lane_count(lane_count: int, *, p4_config: P4Config = DEFAULT_P4_CONFIG) -> tuple[tuple[int, ...], ...]:
    if lane_count < 1 or lane_count > p4_config.P4_LANE_COUNT:
        raise ValueError(f"available_lanes must be in 1..{p4_config.P4_LANE_COUNT}")
    return p4_config.P4_GROUP_LAYOUT[:lane_count]


def select_action_name(block_index: int, physical_feature_id: int) -> str:
    return f"SwitchEgress.ML_BLOCK_{block_index}.select_feat{physical_feature_id}"


def compute_action_name(block_index: int, lane: int) -> str:
    return f"SwitchEgress.ML_BLOCK_{block_index}.compute_feat_{lane}"


def predict_action_name(block_index: int, prediction_slot: int = DT_PREDICTION_SLOT) -> str:
    return f"SwitchEgress.ML_BLOCK_{block_index}.predict_{prediction_slot}"


def subtree_action_name(block_index: int) -> str:
    return f"SwitchEgress.ML_BLOCK_{block_index}.subtree_decision_{block_index}"


def final_predict_action_name() -> str:
    return "SwitchEgress.PRED_BLOCK.final_predict"


def empty_intervals(
    selected_feature_count: int,
    domain_min: int,
    domain_max: int,
) -> dict[int, tuple[int, int]]:
    return {index: (domain_min, domain_max) for index in range(selected_feature_count)}


def pack_internal_subtree(
    clf: DecisionTreeClassifier,
    root_node_id: int,
    node_limit: int,
) -> tuple[int, ...]:
    if is_leaf(clf, root_node_id):
        return ()

    packed: list[int] = []
    queue: deque[int] = deque([root_node_id])
    while queue and len(packed) < node_limit:
        node_id = queue.popleft()
        if is_leaf(clf, node_id):
            continue
        packed.append(node_id)
        left_child = int(clf.tree_.children_left[node_id])
        right_child = int(clf.tree_.children_right[node_id])
        if not is_leaf(clf, left_child):
            queue.append(left_child)
        if not is_leaf(clf, right_child):
            queue.append(right_child)
    return tuple(packed)


def collect_state_outcomes(
    clf: DecisionTreeClassifier,
    *,
    state: PackedState,
    selected_feature_count: int,
) -> list[StateOutcome]:
    included = set(state.included_nodes)
    outcomes: list[StateOutcome] = []

    def visit(node_id: int, intervals: dict[int, tuple[int, int]]) -> None:
        if is_leaf(clf, node_id):
            outcomes.append(
                StateOutcome(
                    intervals=dict(intervals),
                    leaf_class=leaf_result(clf, node_id),
                )
            )
            return

        if node_id not in included:
            outcomes.append(
                StateOutcome(
                    intervals=dict(intervals),
                    next_root_node_id=node_id,
                )
            )
            return

        feature_slot = node_feature_slot(clf, node_id, selected_feature_count)
        low, high = intervals[feature_slot]
        if low > high:
            return

        threshold = split_floor(clf, node_id)
        left_child = int(clf.tree_.children_left[node_id])
        right_child = int(clf.tree_.children_right[node_id])

        left_high = min(high, threshold)
        if low <= left_high:
            left_intervals = dict(intervals)
            left_intervals[feature_slot] = (low, left_high)
            visit(left_child, left_intervals)

        right_low = max(low, threshold + 1)
        if right_low <= high:
            right_intervals = dict(intervals)
            right_intervals[feature_slot] = (right_low, high)
            visit(right_child, right_intervals)

    visit(state.root_node_id, dict(state.root_intervals))
    return outcomes


def interval_signature(
    intervals: dict[int, tuple[int, int]],
    selected_feature_count: int,
) -> tuple[tuple[int, int], ...]:
    return tuple(intervals[index] for index in range(selected_feature_count))


def build_states_by_block(
    clf: DecisionTreeClassifier,
    selected_feature_count: int,
    domain_min: int,
    domain_max: int,
    pack_subtree: Callable[[int, dict[int, tuple[int, int]]], tuple[int, ...]],
    *,
    available_lanes: int | None = None,
    available_blocks: int | None = None,
    p4_config: P4Config = DEFAULT_P4_CONFIG,
    pack_block: Callable[[list[PackedState]], list[PackedState]] | None = None,
) -> tuple[
    list[list[PackedState]],
    dict[int, list[StateOutcome]],
    dict[tuple[int, int], PackedState],
]:
    if available_lanes is None:
        available_lanes = p4_config.P4_LANE_COUNT
    if available_blocks is None:
        available_blocks = p4_config.P4_BLOCK_COUNT
    if available_lanes < 1 or available_lanes > p4_config.P4_LANE_COUNT:
        raise ValueError(f"available_lanes must be in 1..{p4_config.P4_LANE_COUNT}")
    if available_blocks < 1 or available_blocks > p4_config.P4_BLOCK_COUNT:
        raise ValueError(f"available_blocks must be in 1..{p4_config.P4_BLOCK_COUNT}")
    initial_intervals = empty_intervals(selected_feature_count, domain_min, domain_max)
    initial_state = PackedState(
        block_index=0,
        state_id=1,
        root_node_id=0,
        root_intervals=initial_intervals,
        included_nodes=pack_subtree(0, initial_intervals),
        used_features=(),
    )
    states_by_block: list[list[PackedState]] = [[initial_state]]
    outcomes_by_state_id: dict[int, list[StateOutcome]] = {}
    transition_targets: dict[tuple[int, int], PackedState] = {}
    next_state_id = 2

    for block_index in range(available_blocks):
        current_states = states_by_block[block_index]
        if pack_block is not None:
            current_states = pack_block(current_states)
        updated_states: list[PackedState] = []
        next_block_states: list[PackedState] = []
        next_state_lookup: dict[tuple[int, tuple[tuple[int, int], ...]], PackedState] = {}

        for state in current_states:
            if not state.included_nodes:
                raise ValueError("SS conversion requires a nonempty packed subtree")

            used_features = tuple(
                sorted(
                    {
                        node_feature_slot(clf, node_id, selected_feature_count)
                        for node_id in state.included_nodes
                    }
                )
            )
            if len(used_features) > available_lanes:
                raise ValueError(
                    f"packed subtree rooted at node {state.root_node_id} requires {len(used_features)} "
                    f"distinct features, but this run allows only {available_lanes} feature lanes"
                )
            updated_state = PackedState(
                block_index=state.block_index,
                state_id=state.state_id,
                root_node_id=state.root_node_id,
                root_intervals=dict(state.root_intervals),
                included_nodes=state.included_nodes,
                used_features=used_features,
            )
            updated_states.append(updated_state)
            outcomes = collect_state_outcomes(
                clf,
                state=updated_state,
                selected_feature_count=selected_feature_count,
            )
            outcomes_by_state_id[updated_state.state_id] = outcomes

            frontier_outcomes = [
                (outcome_index, outcome)
                for outcome_index, outcome in enumerate(outcomes)
                if outcome.next_root_node_id is not None
            ]

            if not frontier_outcomes:
                continue
            if block_index == available_blocks - 1:
                raise ValueError(
                    f"trained tree exceeds the {available_blocks}-block SS pipeline depth"
                )

            for outcome_index, outcome in frontier_outcomes:
                next_root = int(outcome.next_root_node_id)
                signature = interval_signature(outcome.intervals, selected_feature_count)
                lookup_key = (next_root, signature)
                next_state = next_state_lookup.get(lookup_key)
                if next_state is None:
                    next_state = PackedState(
                        block_index=block_index + 1,
                        state_id=next_state_id,
                        root_node_id=next_root,
                        root_intervals=dict(outcome.intervals),
                        included_nodes=pack_subtree(next_root, outcome.intervals),
                        used_features=(),
                    )
                    next_state_id += 1
                    next_state_lookup[lookup_key] = next_state
                    next_block_states.append(next_state)
                transition_targets[(updated_state.state_id, outcome_index)] = next_state

        states_by_block[block_index] = updated_states
        if next_block_states:
            states_by_block.append(next_block_states)
        else:
            break

    return states_by_block, outcomes_by_state_id, transition_targets


def make_tcam_block_packer(clf, selected_feature_count, p4_config):
    counts, heights = {}, {}
    for node_id in reversed(range(clf.tree_.node_count)):
        if is_leaf(clf, node_id):
            counts[node_id] = heights[node_id] = 0
        else:
            left, right = int(clf.tree_.children_left[node_id]), int(clf.tree_.children_right[node_id])
            counts[node_id] = 1 + counts[left] + counts[right]
            heights[node_id] = 1 + max(heights[left], heights[right])

    def pack_block(seeds):
        works, outcome_counts, candidates = [], {}, []
        aggregate_count, feature_occurrences, sequence = 0, 0, 0

        def push_children(work_index, node_id):
            nonlocal sequence
            work = works[work_index]
            thresholds = state_feature_thresholds(clf, work, selected_feature_count)
            for child in (int(clf.tree_.children_left[node_id]), int(clf.tree_.children_right[node_id])):
                if is_leaf(clf, child):
                    continue
                feature = node_feature_slot(clf, child, selected_feature_count)
                priority = (
                    -heights[child], -counts[child], int(feature not in work.used_features),
                    int(split_floor(clf, child) not in thresholds.get(feature, set())), work.state_id, child,
                )
                heapq.heappush(candidates, (priority, sequence, work_index, child))
                sequence += 1

        for seed in seeds:
            feature = node_feature_slot(clf, seed.root_node_id, selected_feature_count)
            work = replace(seed, included_nodes=(seed.root_node_id,), used_features=(feature,))
            outcome_count = len(collect_state_outcomes(clf, state=work, selected_feature_count=selected_feature_count))
            aggregate_count += outcome_count
            feature_occurrences += 1
            if aggregate_count > p4_config.P4_AGGREGATE_TABLE_CAPACITY:
                raise ValueError("mandatory TCAM roots exceed the block aggregate capacity")
            if math.ceil(feature_occurrences / p4_config.P4_LANE_COUNT) > p4_config.P4_SELECT_TABLE_CAPACITY:
                raise ValueError("mandatory TCAM roots exceed the select capacity lower bound")
            works.append(work)
            outcome_counts[work.state_id] = outcome_count
            push_children(len(works) - 1, work.root_node_id)

        while candidates:
            _, _, work_index, node_id = heapq.heappop(candidates)
            work = works[work_index]
            if node_id in work.included_nodes:
                continue
            feature = node_feature_slot(clf, node_id, selected_feature_count)
            features = tuple(sorted(set(work.used_features) | {feature}))
            if len(features) > p4_config.P4_LANE_COUNT:
                continue
            thresholds = state_feature_thresholds(clf, work, selected_feature_count)
            if len(thresholds.get(feature, set()) | {split_floor(clf, node_id)}) + 1 >= (1 << p4_config.P4_CODE_BITS):
                continue
            candidate = replace(work, included_nodes=work.included_nodes + (node_id,), used_features=features)
            outcome_count = len(collect_state_outcomes(clf, state=candidate, selected_feature_count=selected_feature_count))
            aggregate_delta = outcome_count - outcome_counts[work.state_id]
            feature_delta = len(features) - len(work.used_features)
            if aggregate_count + aggregate_delta > p4_config.P4_AGGREGATE_TABLE_CAPACITY:
                continue
            if math.ceil((feature_occurrences + feature_delta) / p4_config.P4_LANE_COUNT) > p4_config.P4_SELECT_TABLE_CAPACITY:
                continue
            works[work_index] = candidate
            outcome_counts[work.state_id] = outcome_count
            aggregate_count += aggregate_delta
            feature_occurrences += feature_delta
            push_children(work_index, node_id)
        return works

    return pack_block


def state_feature_thresholds(
    clf: DecisionTreeClassifier,
    state: PackedState,
    selected_feature_count: int,
) -> dict[int, set[int]]:
    thresholds: dict[int, set[int]] = {}
    for node_id in state.included_nodes:
        feature_slot = node_feature_slot(clf, node_id, selected_feature_count)
        thresholds.setdefault(feature_slot, set()).add(split_floor(clf, node_id))
    return thresholds


def choose_state_lane_matching(
    *,
    state: PackedState,
    physical_block_index: int,
    feature_thresholds: dict[int, set[int]],
    copies_by_feature: dict[int, set[int]],
    lane_loads: list[int],
    select_counts: dict[tuple[int, int], int],
    thresholds_by_block_lane: dict[tuple[int, int], set[int]],
    available_lanes: int | None = None,
    group_layout: tuple[tuple[int, ...], ...] | None = None,
    p4_config: P4Config = DEFAULT_P4_CONFIG,
    threshold_count_fits: Callable[[int], bool] | None = None,
) -> dict[int, int]:
    if available_lanes is None:
        available_lanes = p4_config.P4_LANE_COUNT
    group_layout = group_layout or group_layout_for_lane_count(available_lanes, p4_config=p4_config)
    if len(state.used_features) > available_lanes:
        raise ValueError(
            f"packed subtree rooted at node {state.root_node_id} requires "
            f"{len(state.used_features)} distinct features, but a SS block "
            f"has only {available_lanes} available feature lanes"
        )

    features = tuple(
        sorted(
            state.used_features,
            key=lambda feature_slot: (
                len(copies_by_feature.get(feature_slot, set())),
                feature_slot,
            ),
        )
    )
    best_cost: tuple[Any, ...] | None = None
    best_mapping: dict[int, int] | None = None

    def evaluate(mapping: dict[int, int]) -> None:
        nonlocal best_cost, best_mapping

        projected_lane_loads = list(lane_loads)
        new_copies = 0
        for feature_slot, lane in mapping.items():
            if lane not in copies_by_feature.get(feature_slot, set()):
                projected_lane_loads[lane] += 1
                new_copies += 1
                if projected_lane_loads[lane] > len(group_layout[lane]):
                    return

        projected_select_counts = dict(select_counts)
        for lane in mapping.values():
            key = (physical_block_index, lane)
            projected_select_counts[key] = projected_select_counts.get(key, 0) + 1
            if projected_select_counts[key] > p4_config.P4_SELECT_TABLE_CAPACITY:
                return

        threshold_additions = 0
        projected_threshold_peak = 0
        for feature_slot, lane in mapping.items():
            key = (physical_block_index, lane)
            existing = thresholds_by_block_lane.get(key, set())
            additions = feature_thresholds.get(feature_slot, set()).difference(existing)
            projected_size = len(existing) + len(additions)
            if threshold_count_fits is not None and not threshold_count_fits(projected_size):
                return
            threshold_additions += len(additions)
            projected_threshold_peak = max(projected_threshold_peak, projected_size)

        select_peak = max(projected_select_counts.values(), default=0)
        sorted_features = tuple(sorted(mapping))
        cost = (
            new_copies,
            max(projected_lane_loads, default=0),
            projected_threshold_peak,
            threshold_additions,
            select_peak,
            tuple(projected_lane_loads),
            tuple(mapping[feature_slot] for feature_slot in sorted_features),
        )
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_mapping = dict(mapping)

    def backtrack(
        index: int,
        used_lanes: set[int],
        mapping: dict[int, int],
    ) -> None:
        if index == len(features):
            evaluate(mapping)
            return

        feature_slot = features[index]
        existing_lanes = sorted(copies_by_feature.get(feature_slot, set()))
        new_lanes = [
            lane
            for lane in range(available_lanes)
            if lane not in copies_by_feature.get(feature_slot, set())
        ]
        for lane in existing_lanes + new_lanes:
            if lane in used_lanes:
                continue
            if lane not in copies_by_feature.get(feature_slot, set()):
                if lane_loads[lane] >= len(group_layout[lane]):
                    continue
            mapping[feature_slot] = lane
            used_lanes.add(lane)
            backtrack(index + 1, used_lanes, mapping)
            used_lanes.remove(lane)
            mapping.pop(feature_slot, None)

    backtrack(0, set(), {})
    if best_mapping is None:
        raise ValueError(
            f"could not assign duplicated feature copies for packed subtree state "
            f"{state.state_id} rooted at node {state.root_node_id}"
        )
    return best_mapping


def assign_duplicated_feature_lanes(
    clf: DecisionTreeClassifier,
    states_by_block: list[list[PackedState]],
    selected_feature_count: int,
    start_block_index: int = 0,
    available_lanes: int | None = None,
    group_layout: tuple[tuple[int, ...], ...] | None = None,
    *,
    p4_config: P4Config = DEFAULT_P4_CONFIG,
    estimators_by_state: dict[int, DecisionTreeClassifier] | None = None,
    threshold_count_fits: Callable[[int], bool] | None = None,
) -> DuplicatedFeatureLaneMapping:
    if available_lanes is None:
        available_lanes = p4_config.P4_LANE_COUNT
    group_layout = group_layout or group_layout_for_lane_count(available_lanes, p4_config=p4_config)
    states = [state for block_states in states_by_block for state in block_states]
    used_features = sorted(
        {
            feature_slot
            for state in states
            for feature_slot in state.used_features
        }
    )
    physical_slot_count = sum(len(layout) for layout in group_layout)
    if len(used_features) > physical_slot_count:
        raise ValueError(
            f"SS has {physical_slot_count} physical feature slots, "
            f"but the packed tree uses {len(used_features)} logical features"
        )

    copies_by_feature: dict[int, set[int]] = {feature_slot: set() for feature_slot in used_features}
    lane_loads = [0 for _ in range(available_lanes)]
    select_counts: dict[tuple[int, int], int] = {}
    thresholds_by_block_lane: dict[tuple[int, int], set[int]] = {}
    lane_by_state_feature: dict[tuple[int, int], int] = {}

    ordered_states = sorted(
        states,
        key=lambda state: (
            -len(state.used_features),
            start_block_index + state.block_index,
            state.state_id,
        ),
    )
    for state in ordered_states:
        physical_block_index = start_block_index + state.block_index
        estimator = clf if estimators_by_state is None else estimators_by_state[state.state_id]
        feature_thresholds = state_feature_thresholds(estimator, state, selected_feature_count)
        matching = choose_state_lane_matching(
            state=state,
            physical_block_index=physical_block_index,
            feature_thresholds=feature_thresholds,
            copies_by_feature=copies_by_feature,
            lane_loads=lane_loads,
            select_counts=select_counts,
            thresholds_by_block_lane=thresholds_by_block_lane,
            available_lanes=available_lanes,
            group_layout=group_layout,
            p4_config=p4_config, threshold_count_fits=threshold_count_fits,
        )
        for feature_slot, lane in matching.items():
            if lane not in copies_by_feature[feature_slot]:
                copies_by_feature[feature_slot].add(lane)
                lane_loads[lane] += 1
            lane_by_state_feature[(state.state_id, feature_slot)] = lane
            select_key = (physical_block_index, lane)
            select_counts[select_key] = select_counts.get(select_key, 0) + 1
            threshold_key = (physical_block_index, lane)
            thresholds_by_block_lane.setdefault(threshold_key, set()).update(
                feature_thresholds.get(feature_slot, set())
            )

    physical_field_by_feature_lane: dict[tuple[int, int], int] = {}
    unused_physical_field_by_lane: dict[int, int] = {}
    lanes_requiring_unused_feature: set[int] = set()
    for state in states:
        active_lanes = {
            lane_by_state_feature[(state.state_id, feature_slot)]
            for feature_slot in state.used_features
        }
        lanes_requiring_unused_feature.update(
            lane for lane in range(available_lanes) if lane not in active_lanes
        )

    for lane in range(available_lanes):
        feature_slots = sorted(
            feature_slot
            for feature_slot, lanes in copies_by_feature.items()
            if lane in lanes
        )
        if len(feature_slots) > len(group_layout[lane]):
            raise ValueError(
                f"lane {lane} would need {len(feature_slots)} feature copies, "
                f"but the SS header layout exposes only {len(group_layout[lane])}"
            )
        for layout_index, feature_slot in enumerate(feature_slots):
            physical_field_by_feature_lane[(feature_slot, lane)] = group_layout[lane][layout_index]
        if lane in lanes_requiring_unused_feature:
            if len(feature_slots) >= len(group_layout[lane]):
                raise ValueError(
                    f"lane {lane} needs an unused-feature sentinel field, but all "
                    f"{len(group_layout[lane])} physical fields are assigned"
                )
            unused_physical_field_by_lane[lane] = group_layout[lane][len(feature_slots)]

    return DuplicatedFeatureLaneMapping(
        copies_by_feature={
            feature_slot: tuple(sorted(lanes))
            for feature_slot, lanes in sorted(copies_by_feature.items())
            if lanes
        },
        physical_field_by_feature_lane=physical_field_by_feature_lane,
        unused_physical_field_by_lane=unused_physical_field_by_lane,
        lane_by_state_feature=lane_by_state_feature,
        thresholds_by_block_lane={
            key: sorted(values)
            for key, values in sorted(thresholds_by_block_lane.items())
        },
    )


def code_for_value(value: int, thresholds: list[int]) -> int:
    code = 1
    for threshold in thresholds:
        if value > threshold:
            code += 1
        else:
            break
    return code


def codes_for_interval(low: int, high: int, thresholds: list[int]) -> tuple[int, ...]:
    return tuple(sorted({code_for_value(value, thresholds) for value in range(low, high + 1)}))


def validate_code_width(thresholds_by_block_group: dict[tuple[int, int], list[int]], *, p4_config: P4Config = DEFAULT_P4_CONFIG) -> None:
    max_code = max(
        (len(thresholds) + 1 for thresholds in thresholds_by_block_group.values()),
        default=0,
    )
    if max_code >= (1 << p4_config.P4_CODE_BITS):
        raise ValueError(
            f"SS P4 CODE_TYPE is bit<{p4_config.P4_CODE_BITS}>, but "
            f"threshold encoding needs code value {max_code}"
        )


def compile_entries_for_limit(
    *,
    clf: DecisionTreeClassifier,
    feature_indices: list[int],
    node_limit: int,
    p4_config: P4Config = DEFAULT_P4_CONFIG,
) -> tuple[list[TableEntry], dict[str, Any]]:
    states, outcomes, transitions = build_states_by_block(
        clf, len(feature_indices), QUANTIZED_MIN, QUANTIZED_MAX,
        lambda root_node_id, root_intervals: pack_internal_subtree(clf, root_node_id, node_limit),
        p4_config=p4_config,
    )
    return compile_tree_entries(clf, feature_indices, states, outcomes, transitions, p4_config)


def build_dt_final_entries(reachable_classes, p4_config):
    for class_id in reachable_classes.get(DT_PREDICTION_SLOT, {}):
        prediction_values = [0] * p4_config.P4_PREDICTION_SLOTS
        prediction_values[DT_PREDICTION_SLOT] = dt_prediction_value(class_id, p4_config=p4_config)
        match = {f"eg_md.pred_{slot}": value for slot, value in enumerate(prediction_values)}
        match["hdr.ml_y.model"] = 0
        yield TableEntry(table_name_final(), match, final_predict_action_name(), {"cls": class_id})


def build_rf_final_entries(reachable_classes, p4_config):
    token_domains = [
        [rf_prediction_token(class_id, p4_config=p4_config) for class_id in sorted(reachable_classes[slot])]
        if slot in reachable_classes else [0]
        for slot in range(p4_config.P4_PREDICTION_SLOTS)
    ]
    add_entry_count({}, table_name_final(), math.prod(map(len, token_domains)), p4_config=p4_config)
    for tokens in itertools.product(*token_domains):
        counts = {token: tokens.count(token) for token in tokens if token != 0}
        winning_token = min(counts, key=lambda token: (-counts[token], token))
        match = {f"eg_md.pred_{slot}": token for slot, token in enumerate(tokens)}
        match["hdr.ml_y.model"] = 0
        yield TableEntry(
            table_name_final(), match, final_predict_action_name(),
            {"cls": winning_token - RF_PREDICTION_TOKEN_OFFSET},
        )


def tree_state_match(state, root_state_ids=(), local_state_ids=None):
    match = {}
    if state.block_index > 0:
        match[f"eg_md.subtree_idx_{state.block_index - 1}"] = (
            0 if state.state_id in root_state_ids else (local_state_ids or {}).get(state.state_id, state.state_id)
        )
    match["hdr.ml_y.model"] = 0
    return match


def tree_input_entries(states_by_block, lane_mapping, p4_config, root_state_ids=(), local_state_ids=None):
    thresholds_by_block_group = lane_mapping.thresholds_by_block_lane
    for block_states in states_by_block:
        for state in block_states:
            feature_by_lane = {
                lane_mapping.lane_by_state_feature[(state.state_id, feature)]: feature
                for feature in state.used_features
            }
            for lane in range(p4_config.P4_LANE_COUNT):
                feature = feature_by_lane.get(lane)
                physical_field = (
                    lane_mapping.unused_physical_field_by_lane[lane] if feature is None
                    else lane_mapping.physical_field_by_feature_lane[(feature, lane)]
                )
                yield TableEntry(
                    table_name_select(state.block_index, lane),
                    {"hdr.ml_y.model": 0, **tree_state_match(state, root_state_ids, local_state_ids)},
                    select_action_name(state.block_index, physical_field), {},
                )

    for (block_index, lane), thresholds in sorted(thresholds_by_block_group.items()):
        for value in range(QUANTIZED_MIN, QUANTIZED_MAX + 1):
            yield TableEntry(
                table_name_compute(block_index, lane), {f"feat_{lane}": value, "hdr.ml_y.model": 0},
                compute_action_name(block_index, lane), {"code": code_for_value(value, thresholds)},
            )


def tree_conversion_metadata(feature_indices, lane_mapping, entry_counts):
    return {
        "feature_slot_mapping": {
            f"hdr.ml_x.feat_{physical_field}": feature_indices[feature]
            for (feature, _), physical_field in sorted(
                lane_mapping.physical_field_by_feature_lane.items(), key=lambda item: item[1],
            )
        },
        "unused_lane_feature_mapping": {
            str(lane): physical_field
            for lane, physical_field in sorted(lane_mapping.unused_physical_field_by_lane.items())
        },
        "total_entries": sum(entry_counts.values()),
    }


def compile_tree_entries(
    clf, feature_indices, states_by_block, outcomes_by_state_id, transition_targets, p4_config,
    *, estimators_by_state=None, tree_slots_by_state=None, root_state_ids=(),
    prediction_value=dt_prediction_value, final_entry_builder=build_dt_final_entries,
):
    lane_mapping = assign_duplicated_feature_lanes(
        clf, states_by_block, len(feature_indices),
        p4_config=p4_config, estimators_by_state=estimators_by_state,
    )
    thresholds_by_block_group = lane_mapping.thresholds_by_block_lane
    validate_code_width(thresholds_by_block_group, p4_config=p4_config)
    tree_slots_by_state = tree_slots_by_state or {}
    entries = []
    entry_counts = {}

    def append_entry(entry):
        add_entry_count(entry_counts, entry.table, p4_config=p4_config)
        entries.append(entry)

    for entry in tree_input_entries(states_by_block, lane_mapping, p4_config, root_state_ids):
        append_entry(entry)

    aggregate_entries = {}
    reachable_classes = {}
    for block_states in states_by_block:
        for state in block_states:
            tree_slot = tree_slots_by_state.get(state.state_id, DT_PREDICTION_SLOT)
            feature_by_lane = {
                lane_mapping.lane_by_state_feature[(state.state_id, feature)]: feature
                for feature in state.used_features
            }
            for outcome_index, outcome in enumerate(outcomes_by_state_id[state.state_id]):
                code_options = []
                for lane in range(p4_config.P4_LANE_COUNT):
                    feature = feature_by_lane.get(lane)
                    if feature is None:
                        code_options.append((0,))
                    else:
                        low, high = outcome.intervals[feature]
                        thresholds = thresholds_by_block_group[(state.block_index, lane)]
                        code_options.append(codes_for_interval(low, high, thresholds))
                if outcome.leaf_class is not None:
                    action = predict_action_name(state.block_index, tree_slot)
                    params = {"cls": prediction_value(outcome.leaf_class, p4_config=p4_config)}
                else:
                    target = transition_targets.get((state.state_id, outcome_index))
                    if target is None:
                        raise ValueError(f"missing chained SS subtree state for root {outcome.next_root_node_id}")
                    action = subtree_action_name(state.block_index)
                    params = {"decision": target.state_id}
                for code_tuple in itertools.product(*code_options):
                    if outcome.leaf_class is not None:
                        reachable_classes.setdefault(tree_slot, {})[outcome.leaf_class] = None
                    match = {f"code_{lane}": code for lane, code in enumerate(code_tuple)}
                    match.update(tree_state_match(state, root_state_ids))
                    table = table_name_aggregate(state.block_index)
                    key = (table, tuple(sorted(match.items())))
                    entry = TableEntry(table, match, action, params)
                    existing = aggregate_entries.get(key)
                    if existing is not None and existing != entry:
                        raise ValueError(f"conflicting SS aggregate entry for {table} {match}")
                    if existing is None:
                        aggregate_entries[key] = entry
                        append_entry(entry)

    for entry in final_entry_builder(reachable_classes, p4_config):
        append_entry(entry)
    return entries, tree_conversion_metadata(feature_indices, lane_mapping, entry_counts)


def compile_tcam_tree_entries(
    clf, feature_indices, states_by_block, outcomes_by_state_id, transition_targets, p4_config,
    *, estimators_by_state=None, tree_slots_by_state=None, root_state_ids=(), local_state_ids=None,
    prediction_value=dt_prediction_value, final_entry_builder=build_dt_final_entries,
):
    lane_mapping = assign_duplicated_feature_lanes(
        clf, states_by_block, len(feature_indices), p4_config=p4_config, estimators_by_state=estimators_by_state,
        threshold_count_fits=lambda count: count + 1 < (1 << p4_config.P4_CODE_BITS),
    )
    thresholds_by_block_lane = lane_mapping.thresholds_by_block_lane
    validate_code_width(thresholds_by_block_lane, p4_config=p4_config)
    entries, entry_counts, aggregate_entries, reachable_classes = [], {}, {}, {}
    tree_slots_by_state = tree_slots_by_state or {}
    local_state_ids = local_state_ids or {}

    def append_entry(entry):
        add_entry_count(entry_counts, entry.table, p4_config=p4_config, tcam=True)
        entries.append(entry)

    for entry in tree_input_entries(states_by_block, lane_mapping, p4_config, root_state_ids, local_state_ids):
        append_entry(entry)
    for block_states in states_by_block:
        for state in block_states:
            tree_slot = tree_slots_by_state.get(state.state_id, DT_PREDICTION_SLOT)
            feature_by_lane = {
                lane_mapping.lane_by_state_feature[(state.state_id, feature)]: feature
                for feature in state.used_features
            }
            for outcome_index, outcome in enumerate(outcomes_by_state_id[state.state_id]):
                match = {}
                for lane in range(p4_config.P4_LANE_COUNT):
                    feature = feature_by_lane.get(lane)
                    bounds = (0, 0)
                    if feature is not None:
                        low, high = outcome.intervals[feature]
                        thresholds = thresholds_by_block_lane[(state.block_index, lane)]
                        bounds = (code_for_value(low, thresholds), code_for_value(high, thresholds))
                    match[f"code_{lane}"] = bounds
                match.update(tree_state_match(state, root_state_ids, local_state_ids))
                if outcome.leaf_class is not None:
                    action = predict_action_name(state.block_index, tree_slot)
                    params = {"cls": prediction_value(outcome.leaf_class, p4_config=p4_config)}
                    reachable_classes.setdefault(tree_slot, {})[outcome.leaf_class] = None
                else:
                    target = transition_targets.get((state.state_id, outcome_index))
                    if target is None:
                        raise ValueError(f"missing chained TCAM subtree state for root {outcome.next_root_node_id}")
                    action = subtree_action_name(state.block_index)
                    params = {"decision": local_state_ids.get(target.state_id, target.state_id)}
                table = table_name_aggregate(state.block_index)
                key = (table, tuple(sorted(match.items())))
                entry = TableEntry(table, match, action, params)
                existing = aggregate_entries.get(key)
                if existing is not None and existing != entry:
                    raise ValueError(f"conflicting TCAM aggregate entry for {table} {match}")
                if existing is None:
                    aggregate_entries[key] = entry
                    append_entry(entry)
    for entry in final_entry_builder(reachable_classes, p4_config):
        append_entry(entry)
    return entries, tree_conversion_metadata(feature_indices, lane_mapping, entry_counts)


@dataclass
class ForestTreeCandidate:
    tree_slot: int
    states_by_block: list[list[PackedState]]
    outcomes_by_state_id: dict[int, list[StateOutcome]]
    transition_targets: dict[tuple[int, int], PackedState]


def rf_prediction_token(class_id: int, *, p4_config: P4Config = DEFAULT_P4_CONFIG) -> int:
    token = int(class_id) + RF_PREDICTION_TOKEN_OFFSET
    if not 0 < token < (1 << p4_config.P4_CLASS_BITS):
        raise ValueError(f"RF class ID plus one must fit bit<{p4_config.P4_CLASS_BITS}>")
    return token


def prepare_rf(model, selector, label_encoder, p4_config):
    check_is_fitted(model, ["estimators_"])
    feature_indices = validate_model_inputs(model, selector, label_encoder)
    for class_id in model.classes_.tolist():
        rf_prediction_token(class_id, p4_config=p4_config)
    for estimator in model.estimators_:
        check_is_fitted(estimator, ["tree_"])
    return feature_indices


def convert_rf(model, selector, label_encoder, p4_config):
    feature_indices = prepare_rf(model, selector, label_encoder, p4_config)
    return convert_forest(model.estimators_, feature_indices, p4_config, class_ids=model.classes_)


def convert_tcam_rf(model, selector, label_encoder, p4_config):
    feature_indices = prepare_rf(model, selector, label_encoder, p4_config)
    return convert_tcam_forest(model.estimators_, feature_indices, p4_config, class_ids=model.classes_)


def convert_tcam_forest(
    estimators, feature_indices, p4_config, *, class_ids=None, final_entry_builder=build_rf_final_entries,
):
    if not estimators:
        raise ValueError("trained forest has no estimators")
    max_trees = min(p4_config.P4_BLOCK_COUNT, p4_config.P4_PREDICTION_SLOTS)
    if len(estimators) > max_trees:
        raise ValueError(f"TCAM forest conversion supports at most {max_trees} trees")
    states_by_block, outcomes_by_state_id, transition_targets = [], {}, {}
    estimators_by_state, tree_slots_by_state, local_state_ids = {}, {}, {}
    root_state_ids = set()
    next_state_id = 1
    for tree_slot, estimator in enumerate(estimators):
        if is_leaf(estimator, 0):
            raise ValueError(f"TCAM forest conversion requires non-trivial trees; tree slot {tree_slot} is constant")
        try:
            states, outcomes, transitions = build_states_by_block(
                estimator, len(feature_indices), QUANTIZED_MIN, QUANTIZED_MAX,
                lambda root_node_id, root_intervals: (root_node_id,), p4_config=p4_config,
                pack_block=make_tcam_block_packer(estimator, len(feature_indices), p4_config),
            )
        except ValueError as error:
            raise ValueError(f"TCAM forest conversion failed for tree slot {tree_slot}: {error}") from error
        start_block = len(states_by_block)
        if start_block + len(states) > p4_config.P4_BLOCK_COUNT:
            raise ValueError("could not schedule the forest trees within the available TCAM ML blocks")
        shifted_states = {}
        for block_states in states:
            shifted_block = []
            for state in block_states:
                shifted = replace(state, block_index=start_block + state.block_index, state_id=next_state_id)
                next_state_id += 1
                shifted_states[state.state_id] = shifted
                shifted_block.append(shifted)
                local_state_ids[shifted.state_id] = state.state_id
                estimators_by_state[shifted.state_id] = estimator
                tree_slots_by_state[shifted.state_id] = tree_slot
                outcomes_by_state_id[shifted.state_id] = [
                    replace(outcome, leaf_class=int(class_ids[outcome.leaf_class]))
                    if outcome.leaf_class is not None and class_ids is not None else outcome
                    for outcome in outcomes[state.state_id]
                ]
                if state.block_index == 0:
                    root_state_ids.add(shifted.state_id)
            states_by_block.append(shifted_block)
        for (state_id, outcome_index), target in transitions.items():
            transition_targets[(shifted_states[state_id].state_id, outcome_index)] = shifted_states[target.state_id]
    return compile_tcam_tree_entries(
        estimators[0], feature_indices, states_by_block, outcomes_by_state_id, transition_targets, p4_config,
        estimators_by_state=estimators_by_state, tree_slots_by_state=tree_slots_by_state,
        root_state_ids=root_state_ids, local_state_ids=local_state_ids,
        prediction_value=rf_prediction_token, final_entry_builder=final_entry_builder,
    )


def convert_forest(
    estimators, feature_indices, p4_config, *, class_ids=None, final_entry_builder=build_rf_final_entries,
):
    if not estimators:
        raise ValueError("trained forest has no estimators")
    max_trees = min(p4_config.P4_BLOCK_COUNT, p4_config.P4_PREDICTION_SLOTS)
    if len(estimators) > max_trees:
        raise ValueError(f"SS forest conversion supports at most {max_trees} trees")
    candidates = []
    for tree_slot, estimator in enumerate(estimators):
        if is_leaf(estimator, 0):
            raise ValueError(f"SS forest conversion requires non-trivial trees; tree slot {tree_slot} is constant")
        def pack_subtree(root_node_id, root_intervals):
            return pack_rf_capacity_subtree(
                estimator, root_node_id=root_node_id, root_intervals=root_intervals,
                selected_feature_count=len(feature_indices), p4_config=p4_config,
            )

        try:
            states, outcomes, transitions = build_states_by_block(
                estimator, len(feature_indices), QUANTIZED_MIN, QUANTIZED_MAX, pack_subtree,
                p4_config=p4_config,
            )
        except ValueError as error:
            raise ValueError(f"SS forest conversion failed for tree slot {tree_slot}: {error}") from error
        candidates.append(ForestTreeCandidate(tree_slot, states, outcomes, transitions))
    return compile_forest_entries(
        estimators, candidates, feature_indices, p4_config,
        class_ids=class_ids, final_entry_builder=final_entry_builder,
    )


def evaluate_rf_packed_state(
    clf: DecisionTreeClassifier,
    *,
    root_node_id: int,
    root_intervals: dict[int, tuple[int, int]],
    included_nodes: tuple[int, ...],
    selected_feature_count: int,
    available_lanes: int | None = None,
    p4_config: P4Config = DEFAULT_P4_CONFIG,
) -> tuple[tuple[int, ...], list[StateOutcome], int]:
    if available_lanes is None:
        available_lanes = p4_config.P4_LANE_COUNT
    used_features = tuple(
        sorted(
            {
                node_feature_slot(clf, node_id, selected_feature_count)
                for node_id in included_nodes
            }
        )
    )
    if len(used_features) > available_lanes:
        raise ValueError(
            f"packed subtree rooted at node {root_node_id} requires {len(used_features)} "
            f"distinct features, but this run allows only {available_lanes} feature lanes"
        )

    probe_state = PackedState(
        block_index=0,
        state_id=0,
        root_node_id=root_node_id,
        root_intervals=dict(root_intervals),
        included_nodes=included_nodes,
        used_features=used_features,
    )
    outcomes = collect_state_outcomes(
        clf,
        state=probe_state,
        selected_feature_count=selected_feature_count,
    )
    thresholds_by_feature = {
        feature: sorted(thresholds)
        for feature, thresholds in state_feature_thresholds(clf, probe_state, selected_feature_count).items()
    }

    aggregate_entries: dict[tuple[tuple[int, ...], int | None, int | None], None] = {}
    for outcome in outcomes:
        code_options: list[tuple[int, ...]] = []
        for feature_slot in used_features:
            low, high = outcome.intervals[feature_slot]
            thresholds = thresholds_by_feature[feature_slot]
            code_options.append(codes_for_interval(low, high, thresholds))

        for code_tuple in itertools.product(*code_options):
            key = (
                tuple(int(code) for code in code_tuple),
                outcome.leaf_class,
                outcome.next_root_node_id,
            )
            aggregate_entries[key] = None
            if len(aggregate_entries) > p4_config.P4_AGGREGATE_TABLE_CAPACITY:
                raise ValueError(
                    f"packed subtree rooted at node {root_node_id} would need more than "
                    f"{p4_config.P4_AGGREGATE_TABLE_CAPACITY} aggregate entries"
                )

    return used_features, outcomes, len(aggregate_entries)


def pack_rf_capacity_subtree(
    clf: DecisionTreeClassifier,
    *,
    root_node_id: int,
    root_intervals: dict[int, tuple[int, int]],
    selected_feature_count: int,
    available_lanes: int | None = None,
    p4_config: P4Config = DEFAULT_P4_CONFIG,
) -> tuple[int, ...]:
    if available_lanes is None:
        available_lanes = p4_config.P4_LANE_COUNT
    if is_leaf(clf, root_node_id):
        return ()

    packed: list[int] = []
    queue: deque[int] = deque([root_node_id])
    while queue:
        node_id = queue.popleft()
        if is_leaf(clf, node_id):
            continue

        candidate_nodes = tuple(packed + [node_id])
        try:
            evaluate_rf_packed_state(
                clf,
                root_node_id=root_node_id,
                root_intervals=root_intervals,
                included_nodes=candidate_nodes,
                selected_feature_count=selected_feature_count,
                available_lanes=available_lanes,
                p4_config=p4_config,
            )
        except ValueError:
            continue

        packed.append(node_id)
        left_child = int(clf.tree_.children_left[node_id])
        right_child = int(clf.tree_.children_right[node_id])
        if not is_leaf(clf, left_child):
            queue.append(left_child)
        if not is_leaf(clf, right_child):
            queue.append(right_child)

    return tuple(packed)


def compile_forest_entries(
    estimators, candidates, feature_indices, p4_config, *, class_ids=None, final_entry_builder=build_rf_final_entries,
):
    if sum(len(candidate.states_by_block) for candidate in candidates) > p4_config.P4_BLOCK_COUNT:
        raise ValueError("could not schedule the forest trees within the available SS ML blocks")
    states_by_block = []
    outcomes_by_state_id = {}
    transition_targets = {}
    estimators_by_state = {}
    tree_slots_by_state = {}
    root_state_ids = set()
    next_state_id = 1
    for candidate in sorted(
        candidates, key=lambda candidate: (len(candidate.states_by_block), candidate.tree_slot), reverse=True,
    ):
        start_block = len(states_by_block)
        shifted_states = {}
        for block_states in candidate.states_by_block:
            shifted_block = []
            for state in block_states:
                shifted = replace(state, block_index=start_block + state.block_index, state_id=next_state_id)
                next_state_id += 1
                shifted_states[state.state_id] = shifted
                shifted_block.append(shifted)
                estimators_by_state[shifted.state_id] = estimators[candidate.tree_slot]
                tree_slots_by_state[shifted.state_id] = candidate.tree_slot
                outcomes_by_state_id[shifted.state_id] = [
                    replace(outcome, leaf_class=int(class_ids[outcome.leaf_class]))
                    if outcome.leaf_class is not None and class_ids is not None else outcome
                    for outcome in candidate.outcomes_by_state_id[state.state_id]
                ]
                if state.block_index == 0:
                    root_state_ids.add(shifted.state_id)
            states_by_block.append(shifted_block)
        for (state_id, outcome_index), target in candidate.transition_targets.items():
            transition_targets[(shifted_states[state_id].state_id, outcome_index)] = shifted_states[target.state_id]

    return compile_tree_entries(
        estimators[0], feature_indices, states_by_block, outcomes_by_state_id, transition_targets, p4_config,
        estimators_by_state=estimators_by_state, tree_slots_by_state=tree_slots_by_state,
        root_state_ids=root_state_ids, prediction_value=rf_prediction_token, final_entry_builder=final_entry_builder,
    )

def tokenize_forest(trees, leaf_values, p4_config):
    values = sorted({value for leaves in leaf_values for value in leaves.values()})
    if not values or not all(math.isfinite(value) for value in values):
        raise ValueError("forest leaf values must be nonempty and finite")
    if len(values) >= (1 << p4_config.P4_CLASS_BITS):
        raise ValueError("forest leaf-value tokens exceed the nonzero prediction field capacity")
    value_indices = {value: index for index, value in enumerate(values)}
    adapters = []
    for tree, leaves in zip(trees, leaf_values):
        tree.value = np.zeros((tree.node_count, 1, len(values)))
        for node_id, value in leaves.items():
            tree.value[node_id, 0, value_indices[value]] = 1.0
        adapters.append(SimpleNamespace(tree_=tree, classes_=np.arange(len(values))))
    return adapters, {index + 1: value for index, value in enumerate(values)}


def reachable_final_entries(adapters, feature_count, classify):
    initial = empty_intervals(feature_count, QUANTIZED_MIN, QUANTIZED_MAX)
    leaves_by_tree = []
    for adapter in adapters:
        state = PackedState(
            0, 1, 0, initial,
            tuple(node for node in range(adapter.tree_.node_count) if not is_leaf(adapter, node)), (),
        )
        leaves_by_tree.append(collect_state_outcomes(adapter, state=state, selected_feature_count=feature_count))

    def build_entries(reachable_classes, p4_config):
        tokens = [0] * p4_config.P4_PREDICTION_SLOTS
        predictions = {}
        entry_counts = {}

        def visit(tree_slot, intervals):
            if tree_slot == len(adapters):
                key = tuple(tokens)
                if key not in predictions:
                    add_entry_count(entry_counts, table_name_final(), p4_config=p4_config)
                    predictions[key] = classify(key)
                return
            for leaf in leaves_by_tree[tree_slot]:
                merged = {
                    feature: (max(low, leaf.intervals[feature][0]), min(high, leaf.intervals[feature][1]))
                    for feature, (low, high) in intervals.items()
                }
                if any(low > high for low, high in merged.values()):
                    continue
                tokens[tree_slot] = rf_prediction_token(leaf.leaf_class, p4_config=p4_config)
                visit(tree_slot + 1, merged)
            tokens[tree_slot] = 0

        visit(0, initial)
        if not predictions:
            raise ValueError("forest has no reachable leaf combinations in the quantized domain")
        for tokens, class_id in sorted(predictions.items()):
            match = {f"eg_md.pred_{slot}": token for slot, token in enumerate(tokens)}
            match["hdr.ml_y.model"] = 0
            yield TableEntry(table_name_final(), match, final_predict_action_name(), {"cls": int(class_id)})

    return build_entries


def prepare_xgb(model, selector, label_encoder, p4_config):
    if hasattr(model, "missing") and not np.isnan(model.missing):
        raise ValueError("XGBoost models with non-NaN missing-value sentinels are unsupported")
    booster = model.get_booster() if hasattr(model, "get_booster") else model
    feature_indices = selected_feature_indices(selector, booster.num_features())
    if not isinstance(label_encoder, LabelEncoder):
        raise TypeError("SS XGB conversion requires a fitted LabelEncoder")
    check_is_fitted(label_encoder, ["classes_"])
    learner = json.loads(booster.save_config())["learner"]
    parameters = learner["learner_model_param"]
    training = learner["learner_train_param"]
    objective = training["objective"]
    supported = {"binary:logistic", "binary:logitraw", "binary:hinge", "multi:softprob", "multi:softmax"}
    if objective not in supported or training["booster"] != "gbtree":
        raise ValueError("SS XGB conversion requires a supported gbtree classification objective")
    parallel_trees = int(learner["gradient_booster"]["gbtree_model_param"].get("num_parallel_tree", 1))
    if parallel_trees != 1 or int(parameters.get("num_target", 1)) != 1:
        raise ValueError("parallel-tree and multi-output XGBoost models are unsupported")
    if booster.feature_types and "c" in booster.feature_types:
        raise ValueError("categorical XGBoost splits are unsupported")
    best_iteration = booster.attr("best_iteration")
    if best_iteration is not None and int(best_iteration) + 1 != booster.num_boosted_rounds():
        raise ValueError("XGBoost early-stopping prediction ranges are unsupported; save the selected trees first")
    multiclass = objective.startswith("multi:")
    class_count = int(parameters["num_class"]) if multiclass else 2
    if len(label_encoder.classes_) != class_count or class_count > (1 << p4_config.P4_CLASS_BITS):
        raise ValueError("XGBoost class count must match the label encoder and fit the result field")
    base_scores = json.loads(parameters["base_score"])
    base_scores = base_scores if isinstance(base_scores, list) else [base_scores]
    base_scores = [float(value) for value in base_scores]
    if multiclass and len(base_scores) == 1:
        base_scores *= class_count
    if len(base_scores) != (class_count if multiclass else 1) or not all(map(math.isfinite, base_scores)):
        raise ValueError("invalid XGBoost base scores")
    if objective == "binary:logistic":
        if not 0 < base_scores[0] < 1:
            raise ValueError("binary logistic base score must be between zero and one")
        base_scores[0] = math.log(base_scores[0] / (1 - base_scores[0]))

    dumps = booster.get_dump(dump_format="json")
    if multiclass and len(dumps) % class_count:
        raise ValueError("multiclass XGBoost tree count must be divisible by the class count")
    feature_names = {name: index for index, name in enumerate(booster.feature_names or [])}
    trees, leaf_values = [], []
    for dumped_tree in dumps:
        nodes, pending = [], [json.loads(dumped_tree)]
        while pending:
            node = pending.pop()
            nodes.append(node)
            pending.extend(reversed(node.get("children", [])))
        indices = {node["nodeid"]: index for index, node in enumerate(nodes)}
        tree = SimpleNamespace(
            node_count=len(nodes), children_left=np.full(len(nodes), _tree.TREE_LEAF),
            children_right=np.full(len(nodes), _tree.TREE_LEAF),
            feature=np.full(len(nodes), _tree.TREE_UNDEFINED), threshold=np.full(len(nodes), -2.0),
        )
        leaves = {}
        for node_id, node in enumerate(nodes):
            if "leaf" in node:
                leaves[node_id] = float(node["leaf"])
                continue
            split = str(node["split"])
            feature = feature_names.get(split)
            if feature is None:
                numeric = split[1:] if split.startswith("f") else split
                if not numeric.isdigit():
                    raise ValueError(f"unsupported XGBoost feature name: {split}")
                feature = int(numeric)
            threshold = node["split_condition"]
            if not isinstance(threshold, (int, float)) or not math.isfinite(threshold):
                raise ValueError("XGBoost splits must have finite numeric thresholds")
            if not 0 <= feature < len(feature_indices):
                raise ValueError("XGBoost split feature is outside the selected feature range")
            tree.feature[node_id] = feature
            tree.threshold[node_id] = math.ceil(threshold) - 1
            tree.children_left[node_id] = indices[node["yes"]]
            tree.children_right[node_id] = indices[node["no"]]
        trees.append(tree)
        leaf_values.append(leaves)
    adapters, weight_by_token = tokenize_forest(trees, leaf_values, p4_config)

    def classify(tokens):
        scores = list(base_scores)
        for tree_slot in range(len(adapters)):
            scores[tree_slot % class_count if multiclass else 0] += weight_by_token[tokens[tree_slot]]
        return min(range(class_count), key=lambda label: (-scores[label], label)) if multiclass else int(scores[0] > 0)

    return adapters, feature_indices, reachable_final_entries(adapters, len(feature_indices), classify)


def convert_xgb(model, selector, label_encoder, p4_config):
    adapters, feature_indices, final_entries = prepare_xgb(model, selector, label_encoder, p4_config)
    return convert_forest(adapters, feature_indices, p4_config, final_entry_builder=final_entries)


def convert_tcam_xgb(model, selector, label_encoder, p4_config):
    adapters, feature_indices, final_entries = prepare_xgb(model, selector, label_encoder, p4_config)
    return convert_tcam_forest(adapters, feature_indices, p4_config, final_entry_builder=final_entries)


def average_path_length(sample_count):
    if sample_count <= 1:
        return 0.0
    if sample_count == 2:
        return 1.0
    return 2.0 * (math.log(sample_count - 1.0) + float(np.euler_gamma)) - 2.0 * (sample_count - 1.0) / sample_count


def prepare_if(model, selector, label_encoder, p4_config):
    check_is_fitted(model, ["estimators_", "estimators_features_", "max_samples_", "offset_"])
    feature_indices = selected_feature_indices(selector, model.n_features_in_)
    if model.max_samples_ < 1 or not math.isfinite(model.offset_):
        raise ValueError("IsolationForest sample count and offset must be valid")
    trees, leaf_values = [], []
    for estimator, features in zip(model.estimators_, model.estimators_features_, strict=True):
        check_is_fitted(estimator, ["tree_"])
        source = estimator.tree_
        feature = np.full(source.node_count, _tree.TREE_UNDEFINED)
        depths = source.compute_node_depths()
        leaves = {}
        for node_id in range(source.node_count):
            if source.children_left[node_id] == _tree.TREE_LEAF:
                leaves[node_id] = float(depths[node_id] + average_path_length(source.n_node_samples[node_id]) - 1)
            else:
                local_feature = int(source.feature[node_id])
                if not 0 <= local_feature < len(features) or not 0 <= features[local_feature] < len(feature_indices):
                    raise ValueError("IsolationForest estimator feature is outside the selected feature range")
                feature[node_id] = features[local_feature]
        trees.append(SimpleNamespace(
            node_count=source.node_count, children_left=source.children_left, children_right=source.children_right,
            feature=feature, threshold=source.threshold,
        ))
        leaf_values.append(leaves)
    adapters, path_by_token = tokenize_forest(trees, leaf_values, p4_config)
    denominator = len(adapters) * average_path_length(model.max_samples_)

    def classify(tokens):
        path_sum = sum(path_by_token[tokens[slot]] for slot in range(len(adapters)))
        score = -(2.0 ** (-(path_sum / denominator))) if denominator else -0.5
        return int(score - model.offset_ < 0.0)

    return adapters, feature_indices, reachable_final_entries(adapters, len(feature_indices), classify)


def convert_if(model, selector, label_encoder, p4_config):
    adapters, feature_indices, final_entries = prepare_if(model, selector, label_encoder, p4_config)
    return convert_forest(adapters, feature_indices, p4_config, final_entry_builder=final_entries)


def convert_tcam_if(model, selector, label_encoder, p4_config):
    adapters, feature_indices, final_entries = prepare_if(model, selector, label_encoder, p4_config)
    return convert_tcam_forest(adapters, feature_indices, p4_config, final_entry_builder=final_entries)

@dataclass(frozen=True)
class LinearCell:
    block_index: int
    lane: int
    bucket: int
    physical_feature_id: int


def svm_contribution(coefficients, intercepts, feature_slot, values, scale):
    raw = coefficients[:, feature_slot, None] * np.asarray(values)
    if feature_slot == 0:
        raw = raw + intercepts[:, None]
    return np.rint(raw * scale)


def choose_svm_scale(coefficients, intercepts, cells, p4_config):
    contributions = coefficients[:, :, None] * np.arange(QUANTIZED_MIN, QUANTIZED_MAX + 1)
    contributions[:, 0, :] += intercepts[:, None]
    return choose_linear_scale(contributions, cells, p4_config, normalize=False)[1]


def choose_linear_scale(contributions, cells, p4_config, *, normalize):
    if not np.all(np.isfinite(contributions)):
        raise ValueError("linear score contributions must be finite")
    maximum = (1 << (p4_config.P4_ACC_BITS - 1)) - 1
    minimum = -maximum - 1

    def fits(scale):
        buckets = np.zeros((p4_config.P4_LINEAR_BUCKET_COUNT, p4_config.P4_LINEAR_HYPERPLANE_COUNT, 2))
        for feature_slot, cell in enumerate(cells):
            with np.errstate(over="ignore", invalid="ignore"):
                values = np.rint(contributions[:, feature_slot, :] * scale)
                bounds = np.stack((values.min(axis=1), values.max(axis=1)), axis=1)
            if not np.all(np.isfinite(bounds)) or np.any(bounds < minimum) or np.any(bounds > maximum):
                return False
            buckets[cell.bucket] += bounds
        return all(
            np.all(bounds >= minimum) and np.all(bounds <= maximum)
            for bounds in (buckets, np.cumsum(buckets, axis=0))
        )

    if normalize:
        original = contributions
        factor = 1.0
        while not fits(1):
            factor *= 2.0
            if not math.isfinite(factor):
                raise ValueError("linear score normalization factor overflowed")
            contributions = original / factor
    low, high, best = 1, maximum, 0
    while low <= high:
        scale = (low + high) // 2
        if fits(scale):
            best, low = scale, scale + 1
        else:
            high = scale - 1
    if best == 0:
        raise ValueError("even fixed-point scale 1 can overflow the signed linear accumulators")
    return contributions, best


def linear_contributions(model, feature_count, class_count):
    domain = np.arange(QUANTIZED_MIN, QUANTIZED_MAX + 1, dtype=np.float64)
    pairs = list(itertools.combinations(range(class_count), 2))
    contributions = np.zeros((len(pairs), feature_count, len(domain)))
    if isinstance(model, (GaussianNB, CategoricalNB)):
        if isinstance(model, GaussianNB):
            check_is_fitted(model, ["theta_", "var_", "class_prior_"])
            theta, variance, priors = map(np.asarray, (model.theta_, model.var_, model.class_prior_))
            if theta.shape != (class_count, feature_count) or variance.shape != theta.shape:
                raise ValueError("GaussianNB parameter shapes must match classes and selected features")
            if priors.shape != (class_count,) or np.any(priors <= 0):
                raise ValueError("GaussianNB class priors must be positive and match classes")
            if not all(np.all(np.isfinite(value)) for value in (theta, variance, priors)):
                raise ValueError("GaussianNB parameters must be finite")
            variance = np.maximum(variance, np.finfo(np.float64).tiny)
            terms = np.log(variance[:, :, None]) + (domain - theta[:, :, None]) ** 2 / variance[:, :, None]
            priors = np.log(priors)
        else:
            check_is_fitted(model, ["feature_log_prob_", "class_log_prior_"])
            probabilities = [np.asarray(value) for value in model.feature_log_prob_]
            priors = np.asarray(model.class_log_prior_)
            if QUANTIZED_MIN < 0 or len(probabilities) != feature_count or priors.shape != (class_count,):
                raise ValueError("CategoricalNB parameters must match classes, features, and a nonnegative domain")
            if any(value.ndim != 2 or value.shape[0] != class_count or value.shape[1] <= QUANTIZED_MAX
                   for value in probabilities):
                raise ValueError("CategoricalNB probabilities must cover every configured category")
            terms = np.stack([value[:, QUANTIZED_MIN:QUANTIZED_MAX + 1] for value in probabilities], axis=1)
        if not np.all(np.isfinite(terms)) or not np.all(np.isfinite(priors)):
            raise ValueError("NB scores and priors must be finite")
        for plane, (left, right) in enumerate(pairs):
            contributions[plane] = terms[left] - terms[right]
            if isinstance(model, GaussianNB):
                contributions[plane] *= -0.5
            contributions[plane, 0, :] += priors[left] - priors[right]
        return contributions
    if isinstance(model, KMeans):
        centers = np.asarray(model.cluster_centers_, dtype=np.float64)
        if centers.shape != (class_count, feature_count):
            raise ValueError("KMeans centers must match clusters and selected features")
        coefficients, intercepts = 2.0 * centers, -np.sum(centers * centers, axis=1)
    else:
        check_is_fitted(model, ["coef_", "intercept_"])
        coefficients, intercepts = np.asarray(model.coef_, dtype=np.float64), np.asarray(model.intercept_, dtype=np.float64)
    row_count = len(pairs) if isinstance(model, SVC) else class_count
    if not isinstance(model, SVC) and class_count == 2 and coefficients.shape == (1, feature_count):
        coefficients = np.vstack((np.zeros_like(coefficients), coefficients))
        if intercepts.shape == (1,):
            intercepts = np.concatenate(([0.0], intercepts))
    if coefficients.shape != (row_count, feature_count) or intercepts.shape != (row_count,):
        raise ValueError("linear coefficient and intercept shapes must match classes and selected features")
    if not np.all(np.isfinite(coefficients)) or not np.all(np.isfinite(intercepts)):
        raise ValueError("linear coefficients and intercepts must be finite")
    for plane, (left, right) in enumerate(pairs):
        coefficient = coefficients[plane] if isinstance(model, SVC) else coefficients[left] - coefficients[right]
        intercept = intercepts[plane] if isinstance(model, SVC) else intercepts[left] - intercepts[right]
        contributions[plane] = coefficient[:, None] * domain
        contributions[plane, 0, :] += intercept
    return contributions


def convert_svm(model, selector, label_encoder, p4_config):
    return convert_linear(model, selector, label_encoder, p4_config)


def convert_linear(model, selector, label_encoder, p4_config):
    is_svm = isinstance(model, SVC)
    if is_svm and (model.kernel != "linear" or model.break_ties):
        raise ValueError("SS SVM conversion requires SVC(kernel='linear', break_ties=False)")
    check_is_fitted(model, ["n_features_in_", "cluster_centers_" if isinstance(model, KMeans) else "classes_"])
    feature_indices = selected_feature_indices(selector, model.n_features_in_)
    if isinstance(model, KMeans):
        class_count = len(model.cluster_centers_)
    else:
        if not isinstance(label_encoder, LabelEncoder):
            raise TypeError("SS linear classification requires a fitted LabelEncoder")
        check_is_fitted(label_encoder, ["classes_"])
        class_count = len(label_encoder.classes_)
        if not np.array_equal(model.classes_, np.arange(class_count)):
            raise ValueError("linear classifiers require contiguous label-encoder class IDs")
        if any(not isinstance(class_id, Integral) for class_id in model.classes_.tolist()):
            raise ValueError("linear classes must be integer label-encoder indices")
    if class_count not in ((2, 3) if is_svm else (1, 2, 3)):
        raise ValueError("linear conversion supports at most three classes or clusters")
    if class_count > (1 << p4_config.P4_CLASS_BITS):
        raise ValueError("linear class IDs do not fit the result field")
    dimensions = (
        p4_config.P4_BLOCK_COUNT, p4_config.P4_LANE_COUNT, p4_config.P4_ACC_BITS,
        p4_config.P4_LINEAR_HYPERPLANE_COUNT, p4_config.P4_LINEAR_BUCKET_COUNT,
    )
    if dimensions != (6, 7, 16, 3, 7):
        raise ValueError("linear conversion requires the existing 6-block, 7-lane, 16-bit, 3-hyperplane, 7-bucket interface")
    if any(len(group) < p4_config.P4_BLOCK_COUNT for group in p4_config.P4_GROUP_LAYOUT):
        raise ValueError("linear header layout must provide one physical feature per block in each lane")
    class_pairs = list(itertools.combinations(range(class_count), 2))
    cells = [
        LinearCell(block, lane, block + lane, p4_config.P4_GROUP_LAYOUT[lane][block])
        for block in range(p4_config.P4_BLOCK_COUNT)
        for lane in range(p4_config.P4_LANE_COUNT)
        if block + lane < p4_config.P4_LINEAR_BUCKET_COUNT
    ]
    if len(feature_indices) > len(cells):
        raise ValueError(f"model selects {len(feature_indices)} features, but only {len(cells)} linear cells are available")
    cells = cells[:len(feature_indices)]
    contributions = linear_contributions(model, len(feature_indices), class_count)
    contributions = np.pad(contributions, ((0, p4_config.P4_LINEAR_HYPERPLANE_COUNT - len(class_pairs)), (0, 0), (0, 0)))
    contributions, scale = choose_linear_scale(contributions, cells, p4_config, normalize=not is_svm)
    entries, entry_counts = [], {}

    def append_entry(entry):
        add_entry_count(entry_counts, entry.table, p4_config=p4_config)
        entries.append(entry)

    for cell in cells:
        match = {"hdr.ml_y.model": 0}
        if cell.block_index > 0:
            match[f"eg_md.subtree_idx_{cell.block_index - 1}"] = 0
        append_entry(TableEntry(
            table_name_select(cell.block_index, cell.lane), match,
            select_action_name(cell.block_index, cell.physical_feature_id), {},
        ))
    for feature_slot, cell in enumerate(cells):
        for value in range(QUANTIZED_MIN, QUANTIZED_MAX + 1):
            contribution = np.rint(contributions[:, feature_slot, value - QUANTIZED_MIN] * scale)
            append_entry(TableEntry(
                table_name_compute(cell.block_index, cell.lane), {f"feat_{cell.lane}": value, "hdr.ml_y.model": 0},
                f"SwitchEgress.ML_BLOCK_{cell.block_index}.sum_integer_{cell.bucket}",
                dict(zip(("value", "value2", "value3"), map(int, contribution))),
            ))
    for bucket in sorted({cell.bucket for cell in cells}):
        if bucket < p4_config.P4_BLOCK_COUNT:
            match = {f"code_{lane}": 0 for lane in range(p4_config.P4_LANE_COUNT)}
            if bucket > 0:
                match[f"eg_md.subtree_idx_{bucket - 1}"] = 0
            match["hdr.ml_y.model"] = 0
            append_entry(TableEntry(
                table_name_aggregate(bucket), match, f"SwitchEgress.ML_BLOCK_{bucket}.block_{bucket}_accumulate", {},
            ))
        else:
            append_entry(TableEntry(
                table_name_linear_acc(), {"hdr.ml_y.model": 0}, "SwitchEgress.LINEAR_ACC_BLOCK.block_6_accumulate", {},
            ))
    for signs in itertools.product((0, 1), repeat=p4_config.P4_LINEAR_HYPERPLANE_COUNT):
        if is_svm and class_count == 2:
            prediction = 0 if signs[0] else 1
        else:
            votes = [0] * class_count
            for sign, (left, right) in zip(signs, class_pairs):
                votes[right if sign else left] += 1
            prediction = votes.index(max(votes))
        match = {"hdr.ml_y.model": 0}
        match.update({f"eg_md.hyperplane_{plane}[15:15]": sign for plane, sign in enumerate(signs)})
        append_entry(TableEntry(
            table_name_final_linear(), match, "SwitchEgress.PRED_BLOCK.linear_predict", {"cls": prediction},
        ))
    return entries, {
        "feature_slot_mapping": {
            f"hdr.ml_x.feat_{cell.physical_feature_id}": feature_indices[slot]
            for slot, cell in enumerate(cells)
        },
        "unused_lane_feature_mapping": {},
        "total_entries": sum(entry_counts.values()),
    }
