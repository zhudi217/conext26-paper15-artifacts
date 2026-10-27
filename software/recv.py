import argparse
import csv
from pathlib import Path

import numpy as np
import yaml
from scapy.all import Ether, sniff
from scapy.utils import PcapReader, PcapWriter

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
    capture.write(packet)
    captured_count += 1
    if captured_count % 1000 == 0:
        print(f"Captured {captured_count}/{packet_count} packets", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture and decode Shapeshifter packets.")
    parser.add_argument("--config", type=str, required=True, help="Configuration to use.")
    parser.add_argument("--read", action="store_true", help="Decode the saved PCAP without capturing.")
    args = parser.parse_args()

    software_dir = Path(__file__).resolve().parent
    with (software_dir / "configs" / f"{args.config}.yaml").open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    capture_dir = software_dir / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    pcap_path = capture_dir / f"{args.config}_{config['model']}.pcap"
    csv_path = pcap_path.with_suffix(".csv")

    if not args.read:
        packet_count = np.load(
            software_dir / "datasets" / config["dataset"] / "X_test.npy", mmap_mode="r",
        ).shape[0]
        if packet_count < 1:
            raise ValueError("The configured test dataset contains no packets to capture.")
        with PcapWriter(str(pcap_path), linktype=1, sync=True) as capture:
            captured_count = 0

            sniff(
                iface="veth3", count=packet_count, store=False,
                lfilter=is_ml_packet, prn=capture_packet,
                started_callback=lambda: print(f"Capturing {packet_count} packets on veth3 to {pcap_path}", flush=True),
            )

    with PcapReader(str(pcap_path)) as packets, csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["result", "result_2"])
        for packet in packets:
            if not is_ml_packet(packet):
                continue
            payload = bytes(packet[Ether].payload)
            result = ml_result_h(payload[FEATURE_SIZE:FEATURE_SIZE + RESULT_SIZE])
            writer.writerow([result.result, result.result_2])
    print(f"Decoded packets saved to {csv_path}")
