import argparse
import csv
from contextlib import nullcontext
from pathlib import Path

import joblib
import numpy as np
import yaml
from scapy.all import Ether, sniff
from scapy.utils import PcapWriter
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression, Perceptron
from sklearn.metrics import cohen_kappa_score, f1_score
from sklearn.naive_bayes import CategoricalNB, GaussianNB
from sklearn.svm import SVC

from sendp import ml_feat_h, ml_result_h


FEATURE_SIZE = len(bytes(ml_feat_h()))
RESULT_SIZE = len(bytes(ml_result_h()))


def is_ml_packet(packet):
    return (
        Ether in packet
        and packet[Ether].dst == "02:00:00:00:00:02"
        and len(bytes(packet[Ether].payload)) >= FEATURE_SIZE + RESULT_SIZE
    )


def capture_packet(packet):
    global captured_count
    if capture is not None:
        capture.write(packet)
    payload = bytes(packet[Ether].payload)
    result = ml_result_h(payload[FEATURE_SIZE:FEATURE_SIZE + RESULT_SIZE])
    predictions.append([result.result, result.result_2])
    writer.writerow(predictions[-1])
    captured_count += 1
    if captured_count % 1000 == 0:
        print(f"Captured {captured_count}/{packet_count} packets", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture and decode Shapeshifter packets.")
    parser.add_argument("--config", type=str, required=True, help="Configuration to use.")
    parser.add_argument("--save", action="store_true", help="Save captured packets to PCAP.")
    args = parser.parse_args()

    software_dir = Path(__file__).resolve().parent
    with (software_dir / "configs" / f"{args.config}.yaml").open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    capture_dir = software_dir / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    pcap_path = capture_dir / f"{args.config}_{config['model']}.pcap"
    csv_path = pcap_path.with_suffix(".csv")

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["result", "result_2"])
        predictions = []
        X_test = np.load(
            software_dir / "datasets" / config["dataset"] / "X_test.npy", mmap_mode="r",
        )
        packet_count = len(X_test)
        if packet_count < 1:
            raise ValueError("The configured test dataset contains no packets to capture.")
        with (PcapWriter(str(pcap_path), linktype=1, sync=True) if args.save else nullcontext()) as capture:
            captured_count = 0

            sniff(
                iface="veth3", count=packet_count, store=False,
                lfilter=is_ml_packet, prn=capture_packet,
                started_callback=lambda: print(f"Capturing {packet_count} packets on veth3", flush=True),
            )

    print(f"Decoded packets saved to {csv_path}")
    if captured_count != packet_count:
        raise RuntimeError(f"Captured {captured_count}/{packet_count} packets; cannot compare predictions.")
    models_dir = software_dir / "models"
    model = joblib.load(models_dir / f"{config['model']}.joblib")
    selector = joblib.load(models_dir / f"{config['model']}_selector.joblib")
    label_encoder = joblib.load(models_dir / f"{config['model']}_label_encoder.joblib")
    is_linear = isinstance(model, (SVC, LogisticRegression, Perceptron, GaussianNB, CategoricalNB, KMeans))
    Y_swt = [row[int(is_linear)] for row in predictions]
    Y = label_encoder.transform(np.load(
        software_dir / "datasets" / config["dataset"] / "Y_test.npy", allow_pickle=True,
    ).reshape(-1))
    Y_serv = model.predict(selector.transform(X_test))
    if isinstance(model, IsolationForest):
        Y_serv = (Y_serv == -1).astype(int)
    print("Y = original dataset labels; Y_swt = switch predictions; Y_serv = model predictions on the server.")
    print(f"Macro-F1 (Y_swt vs Y): {f1_score(Y, Y_swt, average='macro', zero_division=0):.6f}")
    print(f"Macro-F1 (Y_serv vs Y): {f1_score(Y, Y_serv, average='macro', zero_division=0):.6f}")
    print(f"Cohen's Kappa (Y_serv vs Y_swt): {cohen_kappa_score(Y_serv, Y_swt):.6f}")
