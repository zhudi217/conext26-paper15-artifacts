import argparse
from pathlib import Path

import joblib
import numpy as np
import yaml

from utils.generate_forwarding_rule import forwarding_rule_generation
from utils.generate_pcap import generate_pcap
from utils.model_conversion import TableEntry, convert_model, get_bfrt_prefix
from utils.model_installation import install_model


ROOT = Path(__file__).resolve().parent


def parse_args():
    parser = argparse.ArgumentParser(description="Prepare Shapeshifter for Tofino hardware or model.")
    parser.add_argument("--target", choices=("hardware", "model"), required=True)
    parser.add_argument("--model", type=str, required=True, help="Model to use.")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset to use.")
    parser.add_argument("--tcam", action="store_true", help="Use the TCAM implementation.")
    return parser.parse_args()


def load_config(target):
    with (ROOT / "network.yaml").open(encoding="utf-8") as config_file:
        network = yaml.safe_load(config_file)[target]
    sender = {"mac": network["src"]["src_mac"]}
    receiver = {"mac": network["dst"]["dst_mac"]}
    if target == "hardware":
        sender["port_num"] = network["src"]["src_port"]
        receiver["port_num"] = network["dst"]["dst_port"]
    return {"network": {"sender": sender, "receiver": receiver}, "tofino_address": network["tofino_address"]}


def load_model(model_name):
    models_dir = ROOT / "models"
    model = joblib.load(models_dir / f"{model_name}.joblib")
    label_encoder = joblib.load(models_dir / f"{model_name}_label_encoder.joblib")
    selector = joblib.load(models_dir / f"{model_name}_selector.joblib")
    return model, label_encoder, selector


def load_dataset(dataset_name):
    return np.load(ROOT / "datasets" / dataset_name / "X_test.npy")


def prepare(model, config, tcam, *, target, selector, label_encoder, model_name, X_test):
    output_dir = ROOT / "x" / target
    model_dir = output_dir / model_name if target == "hardware" else output_dir
    output_path = model_dir / f"{model_name}_{'tcam' if tcam else 'sram'}.py"
    conversion = convert_model(
        model=model, config=config, tcam=tcam,
        selector=selector, label_encoder=label_encoder, output_path=output_path,
        installed_snapshot_path=output_dir / f"{get_bfrt_prefix(tcam).split('.')[1]}_installed_entries.json",
    )
    generate_pcap(X_test, conversion.metadata, config, conversion.output_path.with_suffix(".pcap"))

    forwarding_entries = []
    if target == "hardware":
        forwarding_rule_generation(
            config=config, tcam=tcam,
            output_path=output_path.with_name(f"{output_path.stem}_forwarding.py"),
        )
        sender_port = config["network"]["sender"]["port_num"]
        receiver_port = config["network"]["receiver"]["port_num"]
        forwarding_entries = [
            TableEntry("SwitchIngress.l2_forward_t", {"ingress_port": source},
                       "SwitchIngress.unicast", {"port_id": destination})
            for source, destination in ((sender_port, receiver_port), (receiver_port, sender_port))
        ]

    try:
        install_model(conversion, grpc_addr=config["tofino_address"], forwarding_entries=forwarding_entries)
    except Exception as error:
        raise RuntimeError(f"Installation failed; generated artifacts remain in {output_path.parent}: {error}") from error
    return conversion


if __name__ == "__main__":
    args = parse_args()
    config = load_config(args.target)
    model, label_encoder, selector = load_model(args.model)
    X_test = load_dataset(args.dataset)
    try:
        prepare(
            model=model, config=config, tcam=args.tcam, target=args.target,
            selector=selector, label_encoder=label_encoder, model_name=args.model, X_test=X_test,
        )
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
