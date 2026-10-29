"""Measure saved-model reconfiguration on an already loaded Tofino 2 pipeline.

From the test directory, using the SDE's Python environment:
    python reconfiguration_test.py --system SS
    python reconfiguration_test.py --system SS_RANGE --reconfiguration-mode differential

SDE_INSTALL must identify the installed SDE, and bf_switchd must already expose
the selected ss/ss_range program. The benchmark clears ShapeShifter model and
version tables before each pair; forwarding tables are left alone.

Each iteration measures A->B and B->A separately. Reported seconds are the sum
of synchronous BFRT call durations, including legacy version blocking. Loading,
conversion, key/data preparation, baseline installation, pauses, and CSV I/O
are excluded. Counts include two version-block ADDs and two DELs per direction.
Existing nonempty CSV cells, including FAILED, are preserved when resuming.
Pairs are selected in CSV row/column order. Each pair runs in a fresh Python
process and BFRT connection, using the legacy search over starting blocks 0..5.
The selected CSV in reconfiguration is read and updated in place by default.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import perf_counter, sleep

import joblib
from sklearn.exceptions import InconsistentVersionWarning

GITHUB_ROOT = Path("..")
sys.path.insert(0, str(GITHUB_ROOT))
from utils import model_conversion as conversion
from utils.model_installation import (
    BATCH_SIZE, get_table, key_field_aliases, load_bfrt_client, make_data, make_key,
)


RECONFIG_ROOT = Path("reconfiguration")
MODELS_DIR = RECONFIG_ROOT / "models"
SUMMARY_PREFIX = "RECONFIG_RESULT_JSON: "


@dataclass
class SavedModel:
    name: str
    estimator: object
    selector: object
    label_encoder: object


@dataclass
class Placement:
    name: str
    start_block: int
    entries: list
    metadata: dict


@dataclass
class PreparedCall:
    table_name: str
    operation: str
    method: object
    arguments: dict


def load_model(name, directory=MODELS_DIR):
    stem = name.strip().removesuffix(".joblib").lower()
    paths = [path for path in directory.glob("*.joblib") if path.stem.lower() == stem]
    if len(paths) != 1 or stem.endswith(("_selector", "_label_encoder")):
        raise ValueError(f"Expected one model named '{name}' in {directory}")
    path = paths[0]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InconsistentVersionWarning)
        model = joblib.load(path)
        selector = joblib.load(path.parent.parent / "selectors" / f"{path.stem}_selector.joblib")
        encoder = None if isinstance(model, conversion.IsolationForest) else joblib.load(
            path.with_name(f"{path.stem}_label_encoder.joblib"),
        )
    return SavedModel(path.stem, model, selector, encoder)


def placement_candidates(model, tcam):
    candidates, errors = [], []
    for start_block in range(conversion.DEFAULT_P4_CONFIG.P4_BLOCK_COUNT):
        try:
            entries, metadata = conversion.convert_model_entries(
                model.estimator, {}, tcam, selector=model.selector,
                label_encoder=model.label_encoder, start_block_index=start_block,
            )
        except ValueError as error:
            errors.append(f"block {start_block}: {error}")
            continue
        candidates.append(Placement(model.name, start_block, entries, metadata))
    if not candidates:
        raise RuntimeError(f"No feasible placement for {model.name}: " + " | ".join(errors))
    return candidates


def choose_placement(candidates, old_entries=None, mode="differential"):
    def ranking(candidate):
        if old_entries is None:
            counts = (len(candidate.entries), 0, 0)
        elif mode == "delete_then_add":
            counts = (len(candidate.entries), 0, len(old_entries))
        else:
            add, mod, delete, _ = conversion.classify_operations(old_entries, candidate.entries)
            counts = (len(add), len(mod), len(delete))
        return sum(counts), -counts[1], counts[0], candidate.start_block

    return min(candidates, key=ranking)


def load_matrix(path):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or len(reader.fieldnames) < 2:
            raise ValueError(f"{path} is not an experiment matrix")
        fields, rows = list(reader.fieldnames), list(reader)
    names = [row[fields[0]].strip() for row in rows]
    if len(set(names)) != len(names) or any(name not in fields[1:] for name in names):
        raise ValueError("CSV row models must be unique and present in the column header")
    return fields, rows


def write_matrix(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent,
                                suffix=".tmp", delete=False) as stream:
            temporary_path = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def version_block(version):
    return conversion.TableEntry(
        "SwitchIngress.version_t", {"hdr.ml_y.model": 0, "hdr.ml_y.version": version},
        "SwitchIngress.drop", {},
    )


def transition_operations(old_entries, new_entries, mode, old_version=0):
    if mode == "differential":
        add, mod, delete, _ = conversion.classify_operations(old_entries, new_entries)
    else:
        add, mod, delete = new_entries, [], old_entries
    old_block, new_block = version_block(old_version), version_block(1 - old_version)
    operations = [
        ("add", [old_block, new_block]), ("mod", mod), ("delete", delete), ("add", add),
        ("delete", [new_block]), ("delete", [old_block]),
    ]
    return operations, (len(add) + 2, len(mod), len(delete) + 2)


class BfrtSession:
    def __init__(self, grpc_addr, p4_name, batch_size):
        self.grpc_addr = grpc_addr
        self.p4_name = p4_name
        self.batch_size = batch_size
        self.interface = None
        self.tables = {}
        self.aliases = {}

    def __enter__(self):
        self.gc = load_bfrt_client()
        self.interface = self.gc.ClientInterface(
            grpc_addr=self.grpc_addr, client_id=0, device_id=0, timeout=1, num_tries=5,
        )
        try:
            self.interface.bind_pipeline_config(self.p4_name)
            self.info = self.interface.bfrt_info_get(self.p4_name)
            self.target = self.gc.Target(device_id=0, pipe_id=0xFFFF, direction=0xFF, prsr_id=0xFF)
        except Exception:
            self.close()
            raise
        return self

    def close(self):
        if self.interface is not None:
            if not getattr(self.interface, "is_independent", True):
                self.interface.tear_down_stream()
            else:
                self.interface.channel.close()

    def __exit__(self, error_type, error, traceback):
        try:
            self.close()
        except Exception:
            if error is None:
                raise

    def table(self, name):
        if name not in self.tables:
            self.tables[name] = get_table(self.info, name)
            self.aliases[name] = key_field_aliases(self.tables[name])
        return self.tables[name]

    def prepare_clear(self, names):
        return [PreparedCall(name, "clear", self.table(name).entry_del, {}) for name in sorted(set(names))]

    def prepare(self, operations):
        calls = []
        for operation, entries in operations:
            grouped = defaultdict(list)
            for entry in entries:
                grouped[entry.table].append(entry)
            for name, table_entries in grouped.items():
                table = self.table(name)
                method = getattr(table, {"add": "entry_add", "mod": "entry_mod", "delete": "entry_del"}[operation])
                for index in range(0, len(table_entries), self.batch_size):
                    batch = table_entries[index:index + self.batch_size]
                    arguments = {"key_list": [make_key(self.gc, table, self.aliases[name], entry) for entry in batch]}
                    if operation != "delete":
                        arguments["data_list"] = [make_data(self.gc, table, entry) for entry in batch]
                    calls.append(PreparedCall(name, operation, method, arguments))
        return calls

    def execute(self, calls):
        elapsed = 0.0
        for call in calls:
            start = perf_counter()
            try:
                call.method(self.target, p4_name=self.p4_name, **call.arguments)
            except Exception as error:
                raise RuntimeError(f"BFRT {call.operation} failed on {call.table_name}: {error}") from error
            elapsed += perf_counter() - start
        return elapsed


def format_cell(summary):
    return (f"{summary['average_time']:.6f} "
            f"({summary['add_ops']}, {summary['mod_ops']}, {summary['delete_ops']})")


def direction_summary(source, destination, times, counts):
    return {
        "from": source, "to": destination,
        "average_time": sum(times) / len(times), "min_time": min(times), "max_time": max(times),
        "add_ops": counts[0], "mod_ops": counts[1], "delete_ops": counts[2],
    }


def measure_pair(session, source, destination, args, clear_calls):
    forward, forward_counts = transition_operations(source.entries, destination.entries, args.reconfiguration_mode)
    reverse, reverse_counts = transition_operations(destination.entries, source.entries, args.reconfiguration_mode, 1)
    baseline_calls = session.prepare([("add", source.entries)])
    forward_calls = session.prepare(forward)
    reverse_calls = session.prepare(reverse)
    session.execute(clear_calls)
    session.execute(baseline_calls)
    forward_times, reverse_times = [], []
    for iteration in range(1, args.iterations + 1):
        forward_times.append(session.execute(forward_calls))
        sleep(args.pause)
        reverse_times.append(session.execute(reverse_calls))
        sleep(args.pause)
        print(f"Iteration {iteration}/{args.iterations}: {source.name}->{destination.name} "
              f"{forward_times[-1]:.6f}s; {destination.name}->{source.name} {reverse_times[-1]:.6f}s", flush=True)
    return {
        "forward": direction_summary(source.name, destination.name, forward_times, forward_counts),
        "reverse": direction_summary(destination.name, source.name, reverse_times, reverse_counts),
    }


def hardware_address():
    import yaml

    with (GITHUB_ROOT / "network.yaml").open(encoding="utf-8") as stream:
        address = yaml.safe_load(stream)["hardware"]["tofino_address"]
    if not isinstance(address, str) or not address.strip():
        raise ValueError("network.yaml must provide hardware.tofino_address")
    return address


def run_single_pair(args):
    tcam = args.system == "SS_RANGE"
    source_model = load_model(args.previous_model)
    destination_model = load_model(args.new_model)
    source = choose_placement(placement_candidates(source_model, tcam))
    destination = choose_placement(
        placement_candidates(destination_model, tcam), source.entries, args.reconfiguration_mode,
    )
    print(f"Selected placements: {source.name} block {source.start_block}; "
          f"{destination.name} block {destination.start_block}.", flush=True)
    p4_name = args.p4_name or conversion.get_bfrt_prefix(tcam).split(".")[1]
    with BfrtSession(args.grpc_addr or hardware_address(), p4_name, args.batch_size) as session:
        clear_calls = session.prepare_clear(conversion.shapeshifter_table_names())
        result = measure_pair(session, source, destination, args, clear_calls)
    result.update(system=args.system, p4_name=p4_name, iterations=args.iterations,
                  reconfiguration_mode=args.reconfiguration_mode)
    return result


def run_pair(args, source, destination):
    command = [
        sys.executable, "-u", "reconfiguration_test.py", "--system", args.system,
        "--previous-model", source.strip().lower(), "--new-model", destination.strip().lower(),
        "--iterations", str(args.iterations), "--pause", str(args.pause),
        "--batch-size", str(args.batch_size), "--reconfiguration-mode", args.reconfiguration_mode,
        "--json-summary",
    ]
    for flag, value in (("--grpc-addr", args.grpc_addr), ("--p4-name", args.p4_name)):
        if value:
            command.extend((flag, value))
    print(f"Running {source} -> {destination}", flush=True)
    process = subprocess.Popen(
        command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    captured = []
    for line in process.stdout:
        captured.append(line)
        if not line.startswith(SUMMARY_PREFIX):
            print(line, end="", flush=True)
    return_code = process.wait()
    if return_code != 0:
        raise RuntimeError(f"Experiment failed for {source}->{destination} with exit code {return_code}")
    for line in reversed(captured):
        if line.startswith(SUMMARY_PREFIX):
            return json.loads(line[len(SUMMARY_PREFIX):])
    raise RuntimeError(f"No reconfiguration summary returned for {source}->{destination}")


def run(args):
    tcam = args.system == "SS_RANGE"
    prefix = "ss_t" if tcam else "ss_s"
    mode_suffix = "_d" if args.reconfiguration_mode == "differential" else ""
    default_csv = RECONFIG_ROOT / f"{prefix}{mode_suffix}_ds1.csv"
    output = args.output_csv
    if output is None:
        output = default_csv
    elif not output.is_absolute():
        output = RECONFIG_ROOT / output
    source_csv = args.input_csv
    if source_csv is None:
        source_csv = output if output.exists() else default_csv
    elif not source_csv.is_absolute():
        source_csv = RECONFIG_ROOT / source_csv
    fields, rows = load_matrix(source_csv)
    row_by_name = {row[fields[0]].strip(): row for row in rows}
    for source, row in row_by_name.items():
        for destination in fields[1:]:
            if source == destination or row.get(destination, "").strip():
                continue
            result = run_pair(args, source, destination)
            row[destination] = format_cell(result["forward"])
            reverse_row = row_by_name.get(destination)
            if reverse_row is not None and not reverse_row.get(source, "").strip():
                reverse_row[source] = format_cell(result["reverse"])
            write_matrix(output, fields, rows)
    write_matrix(output, fields, rows)
    print(f"Wrote results to {output}")
    return output


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--system", type=str.upper, choices=("SS", "SS_RANGE"), required=True)
    parser.add_argument("--reconfiguration-mode", choices=("delete_then_add", "differential"), default="delete_then_add")
    parser.add_argument("--iterations", type=int, default=50, help="measured iterations per direction (default: 50)")
    parser.add_argument("--pause", type=float, default=0.5, help="seconds between transitions (default: 0.5)")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help="maximum entries per BFRT call (default: 256)")
    parser.add_argument("--grpc-addr", help="BFRT address; defaults to ../network.yaml hardware.tofino_address")
    parser.add_argument("--p4-name", help="loaded program name; defaults to ss or ss_range")
    parser.add_argument("--input-csv", type=Path, help="experiment matrix, relative to reconfiguration; defaults to the selected CSV or existing output")
    parser.add_argument("--output-csv", type=Path, help="result matrix, relative to reconfiguration; defaults to the selected CSV there")
    parser.add_argument("--previous-model", help="source model name for single-pair execution")
    parser.add_argument("--new-model", help="destination model name for single-pair execution")
    parser.add_argument("--json-summary", action="store_true", help="emit the legacy JSON summary for a single pair")
    args = parser.parse_args(argv)
    if args.iterations < 1 or args.batch_size < 1 or not math.isfinite(args.pause) or args.pause < 0:
        parser.error("iterations and batch size must be positive; pause must be finite and nonnegative")
    if bool(args.previous_model) != bool(args.new_model):
        parser.error("--previous-model and --new-model must be provided together")
    if args.json_summary and not args.previous_model:
        parser.error("--json-summary requires --previous-model and --new-model")
    return args


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.previous_model:
            result = run_single_pair(args)
            if args.json_summary:
                print(SUMMARY_PREFIX + json.dumps(result))
            else:
                print(f"Forward: {format_cell(result['forward'])}; reverse: {format_cell(result['reverse'])}")
        else:
            run(args)
    except KeyboardInterrupt:
        print("Interrupted; completed pairs remain in the CSV.", file=sys.stderr)
        return 130
    except Exception as error:
        print(f"Benchmark stopped; completed pairs remain in the CSV: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
