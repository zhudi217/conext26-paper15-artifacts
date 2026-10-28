import argparse
import json
from pathlib import Path

import numpy as np
import yaml

from scapy.all import Ether, IP, sendp
from scapy.packet import Packet
from scapy.fields import BitField, ByteField, SignedShortField
from scapy.utils import PcapWriter

class ml_feat_h(Packet):
    name = "ml_feat_h"
    fields_desc = [
        SignedShortField(f"feat_{index}", 0) for index in range(42)
    ]


class ml_result_h(Packet):
    name = "ml_result_h"
    fields_desc = [
        ByteField("result", 0),
        ByteField("result_2", 0),
        BitField("model", 0, 4),
        BitField("version", 0, 4),
    ]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send Shapeshifter dataset packets, then save them to PCAP.")
    parser.add_argument("--config", type=str, required=True, help="Configuration to use.")
    args = parser.parse_args()

    software_dir = Path(__file__).resolve().parent
    with (software_dir / "configs" / f"{args.config}.yaml").open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    metadata_path = software_dir / "x" / f"{args.config}_{config['model']}_metadata.json"
    with metadata_path.open(encoding="utf-8") as metadata_file:
        metadata = json.load(metadata_file)
    X_test = np.load(software_dir / "datasets" / config["dataset"] / "X_test.npy")

    pcap_dir = software_dir / "x"
    pcap_dir.mkdir(parents=True, exist_ok=True)
    pcap_path = pcap_dir / f"{args.config}_{config['model']}.pcap"
    packet_count = len(X_test)
    packets = []
    for packet_index, sample in enumerate(X_test, start=1):
        feature_values = {
            field.split(".")[-1]: int(sample[index])
            for field, index in metadata["feature_slot_mapping"].items()
        }
        for physical_field in metadata["unused_lane_feature_mapping"].values():
            feature_values[f"feat_{physical_field}"] = 1023
        pkt = Ether(dst="02:00:00:00:00:02") / ml_feat_h(**feature_values) / ml_result_h()
        packets.append(pkt)
        if packet_index % 1000 == 0 or packet_index == packet_count:
            print(f"Prepared {packet_index}/{packet_count} packets", flush=True)

    print(f"Sending {packet_count} packets on veth1...", flush=True)
    sendp(packets, iface="veth1", count=1, verbose=False)
    print(f"Sent {packet_count}/{packet_count} packets", flush=True)

    print(f"Saving to PCAP... {pcap_path}", flush=True)
    with PcapWriter(str(pcap_path), linktype=1) as capture:
        for packet_index, pkt in enumerate(packets, start=1):
            capture.write(pkt)
            if packet_index % 1000 == 0 or packet_index == packet_count:
                print(f"Saved {packet_index}/{packet_count} packets", flush=True)

