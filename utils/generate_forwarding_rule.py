from pathlib import Path

from .model_conversion import get_bfrt_prefix


def forwarding_rule_generation(config, tcam, output_path):
    sender_port = config["network"]["sender"]["port_num"]
    receiver_port = config["network"]["receiver"]["port_num"]
    if any(type(port) is not int or port < 0 for port in (sender_port, receiver_port)):
        raise ValueError("sender and receiver ports must be nonnegative integers")
    if sender_port == receiver_port:
        raise ValueError("sender and receiver ports must be distinct")
    table = f"{get_bfrt_prefix(tcam)}.SwitchIngress.l2_forward_t"
    lines = [
        f"{table}.add_with_unicast(ingress_port={sender_port}, port_id={receiver_port})",
        f"{table}.add_with_unicast(ingress_port={receiver_port}, port_id={sender_port})",
    ]
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
