from numbers import Integral
from pathlib import Path

import numpy as np
from scapy.fields import BitField, ByteField, SignedShortField
from scapy.layers.inet import IP, TCP
from scapy.layers.l2 import Ether
from scapy.packet import Packet
from scapy.utils import PcapWriter

from .constants import QUANTIZED_MIN, QUANTIZED_MAX
from .model_conversion import UNUSED_FEATURE_VALUE


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


def generate_pcap(X_test, metadata, config, output_path):
    X_test = np.asarray(X_test)
    if X_test.ndim != 2 or not len(X_test) or X_test.dtype.kind not in "iuf":
        raise ValueError("X_test must be a nonempty 2D numeric feature matrix")
    field_names = {field.name for field in ml_feat_h.fields_desc}
    feature_fields = {}
    for header_name, column in metadata["feature_slot_mapping"].items():
        if not isinstance(header_name, str) or not header_name.startswith("hdr.ml_x."):
            raise ValueError(f"invalid feature header name: {header_name!r}")
        name = header_name.removeprefix("hdr.ml_x.")
        if name not in field_names or not isinstance(column, Integral) or isinstance(column, bool):
            raise ValueError(f"invalid feature mapping: {header_name!r} -> {column!r}")
        if not 0 <= column < X_test.shape[1]:
            raise ValueError(f"dataset feature index out of bounds: {column}")
        feature_fields[name] = int(column)
    if not feature_fields:
        raise ValueError("feature_slot_mapping must not be empty")
    unused_fields = {}
    for physical_field in metadata["unused_lane_feature_mapping"].values():
        if not isinstance(physical_field, Integral) or isinstance(physical_field, bool):
            raise ValueError(f"invalid unused feature index: {physical_field!r}")
        name = f"feat_{physical_field}"
        if name not in field_names or name in feature_fields:
            raise ValueError(f"invalid or overlapping unused feature: {name}")
        unused_fields[name] = UNUSED_FEATURE_VALUE
    values = X_test[:, list(feature_fields.values())]
    if (not np.all(np.isfinite(values)) or np.any(values != np.floor(values))
            or np.any(values < QUANTIZED_MIN) or np.any(values > QUANTIZED_MAX)):
        raise ValueError(f"mapped features must be integers in {QUANTIZED_MIN}..{QUANTIZED_MAX}")
    network = config["network"]
    base_packet = (
        Ether(src=network["sender"]["mac"], dst=network["receiver"]["mac"])
        / IP(src="10.0.0.1", dst="10.0.0.2") / TCP(dport=12345)
    )
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with PcapWriter(str(output_path), linktype=1, append=False) as writer:
        for row in X_test:
            fields = {**unused_fields, **{name: int(row[column]) for name, column in feature_fields.items()}}
            writer.write(base_packet / ml_feat_h(**fields) / ml_result_h(result=255, result_2=255))
    return output_path
