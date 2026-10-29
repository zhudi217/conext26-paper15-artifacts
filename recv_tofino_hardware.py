import argparse
from pathlib import Path

import joblib
import numpy as np
import yaml
from scapy.all import Ether, IP, TCP
from scapy.utils import PcapReader
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.linear_model import LogisticRegression, Perceptron
from sklearn.metrics import cohen_kappa_score, f1_score
from sklearn.naive_bayes import CategoricalNB, GaussianNB
from sklearn.svm import SVC

from utils.generate_pcap import ml_feat_h, ml_result_h

FEATURE_SIZE = len(bytes(ml_feat_h()))
RESULT_SIZE = len(bytes(ml_result_h()))


def parse_packets(pcap_path, dst_mac):
    predictions = []
    with PcapReader(str(pcap_path)) as packets:
        for packet in packets:
            if not (Ether in packet and packet[Ether].dst == dst_mac
                    and IP in packet and TCP in packet and packet[TCP].dport == 12345):
                continue
            payload = bytes(packet[TCP].payload)
            if len(payload) < FEATURE_SIZE + RESULT_SIZE:
                raise ValueError("Truncated hardware ML packet")
            result = ml_result_h(payload[FEATURE_SIZE:FEATURE_SIZE + RESULT_SIZE])
            predictions.append([result.result, result.result_2])
    if not predictions:
        raise ValueError("PCAP contains no matching hardware ML packets")
    return predictions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode collected hardware packets and report prediction metrics.")
    parser.add_argument("--pcap", type=Path, required=True, help="Collected hardware PCAP.")
    parser.add_argument("--model", required=True, help="Model to compare against.")
    parser.add_argument("--dataset", required=True, help="Full test dataset in capture order.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    with (root / "network.yaml").open(encoding="utf-8") as stream:
        dst_mac = yaml.safe_load(stream)["hardware"]["dst"]["dst_mac"]
    predictions = parse_packets(args.pcap, dst_mac)
    models_dir = root / "models"
    model = joblib.load(models_dir / f"{args.model}.joblib")
    selector = joblib.load(models_dir / f"{args.model}_selector.joblib")
    label_encoder = joblib.load(models_dir / f"{args.model}_label_encoder.joblib")
    dataset_dir = root / "datasets" / args.dataset
    X_test = np.load(dataset_dir / "X_test.npy")
    Y = label_encoder.transform(np.load(dataset_dir / "Y_test.npy", allow_pickle=True).reshape(-1))
    if len(predictions) != len(X_test) or len(predictions) != len(Y):
        raise ValueError("Decoded packet count must match the full test dataset")
    is_linear = isinstance(model, (SVC, LogisticRegression, Perceptron, GaussianNB, CategoricalNB, KMeans))
    Y_swt = [row[int(is_linear)] for row in predictions]
    Y_serv = model.predict(selector.transform(X_test))
    if isinstance(model, IsolationForest):
        Y_serv = (Y_serv == -1).astype(int)

    print(f"Decoded {len(predictions)} packets")
    print("Y = original dataset labels; Y_swt = switch predictions; Y_serv = model predictions on the server.")
    print(f"Macro-F1 (Y_swt vs Y): {f1_score(Y, Y_swt, average='macro', zero_division=0):.6f}")
    print(f"Macro-F1 (Y_serv vs Y): {f1_score(Y, Y_serv, average='macro', zero_division=0):.6f}")
    print(f"Cohen's Kappa (Y_serv vs Y_swt): {cohen_kappa_score(Y_serv, Y_swt):.6f}")
