import sys
import time
import warnings
from copy import copy
from dataclasses import replace
from itertools import product
from pathlib import Path
from types import SimpleNamespace

if "sklearn" in sys.modules:
    raise RuntimeError("Restart the kernel: sklearnex must be enabled before scikit-learn imports.")
from sklearnex import patch_sklearn
patch_sklearn(verbose=False)

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import HTML, display
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFE, f_classif
from sklearn.metrics import accuracy_score, f1_score
from sklearn.naive_bayes import CategoricalNB
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

GITHUB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(GITHUB_ROOT))
from utils import model_conversion as conversion
from utils.constants import RANDOM_SEED

if Path(conversion.__file__).resolve().parent != GITHUB_ROOT / "utils":
    raise ImportError("Another utils package is cached; restart the kernel and run this notebook first.")

CONFIG_COLUMNS = ["model", "features", "depth", "trees", "max_leaves", "targets"]



CURVES = [
    ("dt", "SRAM", "DT_sram SRAM", "#1F77B4", "o", "-"),
    ("dt", "TCAM", "DT_sram TCAM", "#1F77B4", "^", "--"),
    ("rf", "SRAM", "RF_sram SRAM", "#FF7F0E", "o", "-"),
    ("rf", "TCAM", "RF_sram TCAM", "#FF7F0E", "^", "--"),
]


class Progress:
    def __init__(self):
        self.started = time.perf_counter()
        self.last_update = -float("inf")
        self.handle = None

    def update(self, stage, completed, total, force=False):
        now = time.perf_counter()
        if not force and now - self.last_update < 1:
            return
        elapsed = int(now - self.started)
        content = HTML(f"<div>{stage}: {completed:,}/{total:,} &middot; "
                       f"Elapsed: {elapsed // 60}m {elapsed % 60:02d}s</div>")
        if self.handle is None:
            self.handle = display(content, display_id=True)
        else:
            self.handle.update(content)
        self.last_update = now



def load_dataset(dataset="ciciot22"):
    dataset_dir = GITHUB_ROOT / "datasets" / dataset
    X_train, X_test = (np.load(dataset_dir / f"X_{split}.npy").astype(np.float64)
                       for split in ("train", "test"))
    y_train_raw, y_test_raw = (np.load(dataset_dir / f"Y_{split}.npy", allow_pickle=True)
                               for split in ("train", "test"))
    assert X_train.ndim == X_test.ndim == 2
    assert X_train.shape == (11878, 45) and X_test.shape == (2970, 45)
    assert y_train_raw.shape == (len(X_train),) and y_test_raw.shape == (len(X_test),)
    for values in (X_train, X_test):
        assert np.isfinite(values).all() and ((values >= 0) & (values <= 99)).all()
        assert np.equal(values, np.floor(values)).all()
    encoder = LabelEncoder().fit(y_train_raw)
    y_train, y_test = encoder.transform(y_train_raw), encoder.transform(y_test_raw)
    assert encoder.classes_.tolist() == ["Idle", "Interactions", "Power"]
    return SimpleNamespace(X_train=X_train, X_test=X_test, y_train=y_train,
                           y_test=y_test, encoder=encoder, dataset_dir=dataset_dir)


def build_configurations(feature_values, depth_values, tree_values, leaf_limits):
    configurations = [
        (model, features, depth, trees, leaves, ("SRAM", "TCAM"))
        for model in ("dt", "rf")
        for features, depth, trees, leaves in product(
            feature_values[model], depth_values[model], tree_values[model], leaf_limits,
        )
    ]
    assert len(set(configurations)) == len(configurations)
    return configurations



def make_estimator(cfg):
    options = dict(max_depth=cfg["depth"], max_leaf_nodes=cfg["max_leaves"],
                   random_state=RANDOM_SEED, min_samples_leaf=1)
    if cfg["model"] == "dt":
        return DecisionTreeClassifier(**options)
    return RandomForestClassifier(n_estimators=cfg["trees"], criterion="gini",
                                  max_features="sqrt", n_jobs=1, **options)


def train_candidates(configurations, data, feature_values, progress=None):
    trained, path_cache = [], {}
    if progress is not None:
        progress.update("Training", 0, len(configurations), force=True)
    for order, values in enumerate(configurations):
        cfg = dict(zip(CONFIG_COLUMNS, values))
        key = (cfg["model"], cfg["depth"], cfg["trees"], cfg["max_leaves"], RANDOM_SEED)
        minimum = min(feature_values[cfg["model"]])
        if key not in path_cache:
            path_cache[key] = RFE(
                make_estimator(cfg), n_features_to_select=minimum, step=1,
            ).fit(data.X_train, data.y_train)
        path = path_cache[key]
        selector = copy(path)
        selector.n_features_to_select = cfg["features"]
        selector.n_features_ = cfg["features"]
        selector.support_ = path.ranking_ <= cfg["features"] - minimum + 1
        selector.ranking_ = np.maximum(1, path.ranking_ - cfg["features"] + minimum)
        assert selector.support_.sum() == cfg["features"]
        estimator = (
            path.estimator_ if cfg["features"] == minimum
            else make_estimator(cfg).fit(selector.transform(data.X_train), data.y_train)
        )
        selector.estimator_ = estimator
        predictions = estimator.predict(selector.transform(data.X_test))
        score = f1_score(data.y_test, predictions, average="macro", labels=range(3), zero_division=0)
        trained.append(dict(cfg, order=order, selector=selector, estimator=estimator,
                            f1_raw=score, f1=round(score, 6),
                            accuracy=accuracy_score(data.y_test, predictions)))
        if progress is not None:
            progress.update("Training", order + 1, len(configurations),
                            force=order + 1 == len(configurations))
    return trained


def convert_point(candidate, system, lanes, blocks, encoder):
    limits = replace(
        conversion.TCAM_P4_CONFIG if system == "TCAM" else conversion.SRAM_P4_CONFIG,
        P4_LANE_COUNT=lanes, P4_BLOCK_COUNT=blocks,
    )
    converters = {
        ("dt", "SRAM"): conversion.convert_dt, ("dt", "TCAM"): conversion.convert_tcam_dt,
        ("rf", "SRAM"): conversion.convert_rf, ("rf", "TCAM"): conversion.convert_tcam_rf,
    }
    entries, metadata = converters[candidate["model"], system](
        candidate["estimator"], candidate["selector"], encoder, limits,
    )
    total = int(metadata["total_entries"])
    assert total == len(entries)
    tcam_entries = sum(entry.table.endswith("_aggregate_t") for entry in entries) if system == "TCAM" else 0
    slots = len(metadata["feature_slot_mapping"])
    return dict(entries=total, sram_entries=total - tcam_entries,
                tcam_entries=tcam_entries, used_slots=slots,
                duplication=slots / candidate["features"])


def should_prune(score, incumbent):
    return incumbent is not None and score < incumbent


def sweep_candidates(trained, encoder, lanes, blocks, resources=None, prune=True, progress=None):
    resources = (list(product(reversed(lanes), reversed(blocks)))
                 if resources is None else list(resources))
    records, best_f1 = [], {}
    total = sum(len(candidate["targets"]) for candidate in trained) * len(resources)
    if progress is not None:
        progress.update("Conversion", 0, total, force=True)
    for candidate in sorted(trained, key=lambda c: (c["model"], -c["f1"], c["order"])):
        for lanes, blocks in resources:
            for system in candidate["targets"]:
                row = {k: candidate[k] for k in (
                    "model", "features", "depth", "trees", "order", "f1", "accuracy",
                )}
                row.update(max_leaves=candidate["max_leaves"] or "no_limit",
                           system=system, lanes=lanes, blocks=blocks, reason="")
                key = candidate["model"], system, lanes, blocks
                tick = time.perf_counter()
                if prune and should_prune(candidate["f1"], best_f1.get(key)):
                    row.update(status="pruned", reason="Strictly higher F1 already feasible at this exact budget.")
                else:
                    try:
                        row.update(convert_point(candidate, system, lanes, blocks, encoder), status="ok")
                        best_f1[key] = max(candidate["f1"], best_f1.get(key, -np.inf))
                    except ValueError as error:
                        row.update(status="failed", reason=str(error))
                row["seconds"] = time.perf_counter() - tick
                records.append(row)
                if progress is not None:
                    progress.update("Conversion", len(records), total,
                                    force=len(records) == total)
    return pd.DataFrame(records)


def train_nb(data, lane_features, block_features, progress=None):
    counts = sorted(set(lane_features + block_features))
    if progress is not None:
        progress.update("NB training", 0, len(counts), force=True)
    with warnings.catch_warnings(), np.errstate(invalid="ignore", divide="ignore"):
        warnings.filterwarnings("ignore", message="Features .* are constant.", category=UserWarning)
        scores, _ = f_classif(data.X_train, data.y_train)
    scores = np.nan_to_num(scores, nan=-np.inf, posinf=np.finfo(float).max, neginf=-np.inf)
    models, rows = {}, []
    for index, features in enumerate(counts):
        indices = np.sort(np.argsort(scores)[-features:])
        model = CategoricalNB(alpha=0.1, min_categories=100).fit(
            data.X_train[:, indices], data.y_train,
        )
        f1 = f1_score(data.y_test, model.predict(data.X_test[:, indices]),
                      average="macro", labels=range(3), zero_division=0)
        models[features] = (model, indices)
        rows.append(dict(features=features, used_slots=len(indices),
                         duplication=len(indices) / features, f1=round(f1, 6)))
        if progress is not None:
            progress.update("NB training", index + 1, len(counts),
                            force=index + 1 == len(counts))
    return models, pd.DataFrame(rows).set_index("features")


def run_experiment(data, configurations, feature_values, lanes, blocks,
                   nb_lane_features, nb_block_features, *, resources=None):
    progress = Progress()
    trained = train_candidates(configurations, data, feature_values, progress)
    training_seconds = time.perf_counter() - progress.started
    nb_models, nb_results = train_nb(data, nb_lane_features, nb_block_features, progress)
    results = sweep_candidates(trained, data.encoder, lanes, blocks,
                               resources=resources, progress=progress)
    runtime_seconds = time.perf_counter() - progress.started
    progress.update("Complete", len(results), len(results), force=True)
    return SimpleNamespace(
        trained=trained, results=results, nb_models=nb_models, nb_results=nb_results,
        training_seconds=training_seconds, runtime_seconds=runtime_seconds,
    )



def pair_winners(frame):
    feasible = frame.loc[frame["status"].eq("ok")].copy()
    if feasible.empty:
        raise RuntimeError("No deployable results; inspect results[['model', 'system', 'reason']].")
    return (feasible.sort_values(
        ["model", "system", "lanes", "blocks", "f1", "entries", "order"],
        ascending=[True, True, True, True, False, True, True], kind="stable",
    ).drop_duplicates(["model", "system", "lanes", "blocks"]).reset_index(drop=True))


def select_by_budget(frame, axis):
    other = "blocks" if axis == "lanes" else "lanes"
    return (frame.sort_values(
        ["model", "system", axis, "f1", other, "entries", "order"],
        ascending=[True, True, True, False, True, True, True], kind="stable",
    ).drop_duplicates(["model", "system", axis]).reset_index(drop=True))


def pareto_frontier(frame):
    keep = []
    for _, group in frame.groupby(["model", "system"], sort=False):
        for index, row in group.iterrows():
            dominates = (
                group["lanes"].le(row["lanes"]) & group["blocks"].le(row["blocks"])
                & group["f1"].ge(row["f1"])
                & (group["lanes"].lt(row["lanes"]) | group["blocks"].lt(row["blocks"])
                   | group["f1"].gt(row["f1"]))
            )
            if not dominates.any():
                keep.append(index)
    return frame.loc[keep].reset_index(drop=True)


def configure_plotting():
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 22, "pdf.fonttype": 42, "ps.fonttype": 42,
    })


def plot_panel(points, axis, metric, nb_features, ylabel, figsize, *, nb_results, budgets):
    budgets = list(budgets)
    fig, ax = plt.subplots(figsize=figsize)
    all_values = []
    for model, system, label, color, marker, style in CURVES:
        selected = points.loc[points["model"].eq(model) & points["system"].eq(system)]
        values = selected.set_index(axis)[metric].reindex(budgets).to_numpy(dtype=float)
        all_values.extend(values[np.isfinite(values)])
        ax.plot(budgets, values, label=label, color=color, marker=marker,
                linestyle=style, linewidth=2, markersize=7)
    nb_values = [nb_results.loc[k, metric] for k in nb_features]
    all_values.extend(nb_values)
    ax.plot(budgets, nb_values, label="NB", color="#2CA02C", marker="o",
            linestyle="-", linewidth=2, markersize=7)
    ax.set_xlabel("# Lanes" if axis == "lanes" else "# ML blocks")
    ax.set_ylabel(ylabel)
    ax.set_xticks(budgets)
    ax.set_xlim(0.8, budgets[-1] + 0.2)
    if metric == "f1" and axis == "lanes":
        ax.set_ylim(0.55, 0.9)
    else:
        low, high = min(all_values), max(all_values)
        padding = max(0.01 if metric == "f1" else 0.05, (high - low) * 0.15)
        ax.set_ylim(max(0, low - padding), min(1, high + padding) if metric == "f1" else high + padding)
    ax.grid(True, axis="y", alpha=0.3)
    ax.grid(True, axis="x", alpha=0.12)
    ax.spines[["top", "right"]].set_visible(False)
    if metric == "f1" and axis == "lanes":
        ax.legend(frameon=False, fontsize=12, ncol=3, loc="lower left", columnspacing=0.8)
    fig.tight_layout()
    plt.show()
    return fig

