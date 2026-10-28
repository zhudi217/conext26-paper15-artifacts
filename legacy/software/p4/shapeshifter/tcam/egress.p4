#include "predict_block.p4"
#include "ml_block.p4"
#include "linear_acc_block.p4"
// ---------------------------------------------------------------------------
// Egress parser
// ---------------------------------------------------------------------------
parser SwitchEgressParser(
        packet_in pkt,
        out header_t hdr,
        out eg_metadata_t eg_md,
        out egress_intrinsic_metadata_t eg_intr_md) {
    state start {
        pkt.extract(eg_intr_md);
        transition parse_ethernet;
    }

    state parse_ethernet {
        pkt.extract(hdr.ethernet);
        transition parse_ml_x;
    }

    state parse_ml_x {
        pkt.extract(hdr.ml_x);
        transition parse_ml_y;
    }

    state parse_ml_y {
        pkt.extract(hdr.ml_y);
        transition accept;
    }
}

// ---------------------------------------------------------------------------
// Egress Control
// ---------------------------------------------------------------------------
control SwitchEgress(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {
    apply {
        ML_BLOCK_0.apply(hdr, eg_md, eg_intr_md, eg_intr_md_from_prsr, ig_intr_dprs_md, eg_intr_oport_md);
        ML_BLOCK_1.apply(hdr, eg_md, eg_intr_md, eg_intr_md_from_prsr, ig_intr_dprs_md, eg_intr_oport_md);
        ML_BLOCK_2.apply(hdr, eg_md, eg_intr_md, eg_intr_md_from_prsr, ig_intr_dprs_md, eg_intr_oport_md);
        ML_BLOCK_3.apply(hdr, eg_md, eg_intr_md, eg_intr_md_from_prsr, ig_intr_dprs_md, eg_intr_oport_md);
        ML_BLOCK_4.apply(hdr, eg_md, eg_intr_md, eg_intr_md_from_prsr, ig_intr_dprs_md, eg_intr_oport_md);
        ML_BLOCK_5.apply(hdr, eg_md, eg_intr_md, eg_intr_md_from_prsr, ig_intr_dprs_md, eg_intr_oport_md);
        LINEAR_ACC_BLOCK.apply(hdr, eg_md, eg_intr_md, eg_intr_md_from_prsr, ig_intr_dprs_md, eg_intr_oport_md);
        PRED_BLOCK.apply(hdr, eg_md, eg_intr_md, eg_intr_md_from_prsr, ig_intr_dprs_md, eg_intr_oport_md);
    }
}

// ---------------------------------------------------------------------------
// Egress Deparser
// ---------------------------------------------------------------------------
control SwitchEgressDeparser(
        packet_out pkt,
        inout header_t hdr,
        in eg_metadata_t eg_md,
        in egress_intrinsic_metadata_for_deparser_t eg_intr_md_for_dprsr) {

    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ml_x);
        pkt.emit(hdr.ml_y);
    }
}