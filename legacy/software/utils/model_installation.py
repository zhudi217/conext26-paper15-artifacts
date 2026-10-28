import json
import os
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

from .model_conversion import bfrt_match_name


BATCH_SIZE = 256


def load_bfrt_client():
    sde_install = os.environ.get("SDE_INSTALL")
    if not sde_install:
        raise RuntimeError("SDE_INSTALL must point to the SDE install directory")
    python_version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    root = (Path(sde_install) / "lib" / python_version / "site-packages").resolve()
    package_root = next(
        (directory for directory in (root / "tofino", root) if (directory / "bfrt_grpc").is_dir()), None,
    )
    if package_root is None:
        raise RuntimeError(f"Cannot find the SDE BFRT client under {root}. Use the SDE's matching Python version.")

    for directory in (root, package_root):
        directory = str(directory)
        if directory in sys.path:
            sys.path.remove(directory)
        sys.path.insert(0, directory)

    try:
        import grpc  # noqa: F401
    except ImportError as error:
        raise RuntimeError(f"Cannot import grpc: {error}. Install grpcio in the active Python environment.") from error

    try:
        from bfrt_grpc import client as gc
    except ImportError as error:
        raise RuntimeError(f"Cannot load the SDE BFRT client from {package_root}: {error}") from error
    if Path(gc.__file__).resolve().parent != (package_root / "bfrt_grpc").resolve():
        raise RuntimeError("bfrt_grpc is already loaded outside SDE_INSTALL; restart Python using the SDE environment")
    return gc


def get_table(bfrt_info, table_name):
    for candidate in (table_name, f"pipe.{table_name}"):
        try:
            return bfrt_info.table_get(candidate)
        except KeyError:
            continue
    raise KeyError(f"BFRT table not found: {table_name}")


def key_field_aliases(table):
    names = set(table.info.key_field_name_list_get())
    aliases = {name: name for name in names}
    for name in names:
        for alias in (name.split(".")[-1], bfrt_match_name(name), bfrt_match_name(name.replace(".", "_"))):
            if alias in names:
                continue
            if alias not in aliases:
                aliases[alias] = name
            elif aliases[alias] != name:
                aliases[alias] = None
    return aliases


def make_key(gc, table, aliases, entry):
    key_tuples = []
    for name, value in entry.match.items():
        canonical_name = aliases.get(name)
        if canonical_name is None:
            raise KeyError(f"Unknown or ambiguous BFRT key field: {name}")
        if isinstance(value, (tuple, list)):
            low, high = value
            key_tuples.append(gc.KeyTuple(canonical_name, low=int(low), high=int(high)))
        else:
            key_tuples.append(gc.KeyTuple(canonical_name, value=int(value)))
    return table.make_key(key_tuples)


def make_data(gc, table, entry):
    data = [gc.DataTuple(name, val=int(value)) for name, value in entry.params.items()]
    for action in dict.fromkeys((entry.action, entry.action.split(".")[-1])):
        try:
            return table.make_data(data, action)
        except KeyError:
            continue
    raise KeyError(f"BFRT action not found: {entry.action}")


def save_installed_snapshot(path, snapshot):
    temporary_path = None
    try:
        with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False) as stream:
            temporary_path = Path(stream.name)
            stream.write(snapshot)
        temporary_path.replace(path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def install_model(conversion, *, grpc_addr="localhost:50052"):
    plan = conversion.plan
    if plan is None:
        raise ValueError("Conversion result has no installation plan")
    baseline_path = Path(conversion.metadata["installed_snapshot_path"])
    baseline_snapshot = baseline_path.read_text(encoding="utf-8") if baseline_path.exists() else None
    if baseline_snapshot != plan.baseline_snapshot:
        raise RuntimeError("Installed snapshot changed after conversion; convert the model again")
    snapshot = json.dumps({
        "bfrt_prefix": f"bfrt.{plan.p4_name}.pipe",
        "entries": [asdict(entry) for entry in conversion.entries],
    }, indent=2) + "\n"

    gc = load_bfrt_client()

    interface = gc.ClientInterface(
        grpc_addr=grpc_addr, client_id=0, device_id=0, timeout=1, num_tries=5,
    )
    try:
        interface.bind_pipeline_config(plan.p4_name)
        bfrt_info = interface.bfrt_info_get(plan.p4_name)
        target = gc.Target(device_id=0, pipe_id=0xFFFF, direction=0xFF, prsr_id=0xFF)
        table_names = plan.tables_to_clear + [entry.table for _, entries in plan.operations for entry in entries]
        tables = {name: get_table(bfrt_info, name) for name in dict.fromkeys(table_names)}
        aliases = {name: key_field_aliases(table) for name, table in tables.items()}
        calls = [(tables[name].entry_del, {}) for name in plan.tables_to_clear]
        for operation, entries in plan.operations:
            grouped = defaultdict(list)
            for entry in entries:
                grouped[entry.table].append(entry)
            for table_name, table_entries in grouped.items():
                table = tables[table_name]
                method = getattr(table, {"mod": "entry_mod", "delete": "entry_del", "add": "entry_add"}[operation])
                for index in range(0, len(table_entries), BATCH_SIZE):
                    batch = table_entries[index:index + BATCH_SIZE]
                    arguments = {"key_list": [make_key(gc, table, aliases[table_name], entry) for entry in batch]}
                    if operation != "delete":
                        arguments["data_list"] = [make_data(gc, table, entry) for entry in batch]
                    calls.append((method, arguments))
        for method, arguments in calls:
            method(target, p4_name=plan.p4_name, **arguments)
        save_installed_snapshot(baseline_path, snapshot)
    finally:
        if not getattr(interface, "is_independent", True):
            interface.tear_down_stream()
        else:
            interface.channel.close()
