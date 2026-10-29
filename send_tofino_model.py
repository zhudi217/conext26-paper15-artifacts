import argparse
from pathlib import Path

import yaml

from scapy.all import rdpcap, sendp

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send packets from a prepared Shapeshifter PCAP.")
    parser.add_argument("--pcap", type=Path, required=True, help="Saved PCAP to send (relative to the working directory).")
    args = parser.parse_args()

    software_dir = Path(__file__).resolve().parent
    with (software_dir / "network.yaml").open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)
    interface = config["model"]["src"]["interface"]
    packets = rdpcap(str(args.pcap))
    packet_count = len(packets)
    if not packet_count:
        parser.error("PCAP contains no packets")

    print(f"Sending {packet_count} packets on {interface}...", flush=True)
    sendp(packets, iface=interface, count=1, verbose=False)
    print(f"Sent {packet_count}/{packet_count} packets", flush=True)

