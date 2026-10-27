parser TofinoIngressParser(
        packet_in pkt,
        inout ig_metadata_t ig_md,
        out ingress_intrinsic_metadata_t ig_intr_md) {
    state start {
        pkt.extract(ig_intr_md);
        transition select(ig_intr_md.resubmit_flag) {
            1 : parse_resubmit;
            0 : parse_port_metadata;
        }
    }

    state parse_resubmit {
        // Parse resubmitted packet here.
        pkt.advance(64);        // why 64 here?
        transition accept;
    }

    state parse_port_metadata {
	pkt.advance(PORT_METADATA_SIZE);
        transition accept;
    }
}

parser SwitchIngressParser(
        packet_in pkt,
        out header_t hdr,
        out ig_metadata_t ig_md,
        out ingress_intrinsic_metadata_t ig_intr_md) {

    TofinoIngressParser() tofino_parser;

    state start {
        tofino_parser.apply(pkt, ig_md, ig_intr_md);
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


control SwitchIngress(
        inout header_t hdr,
        inout ig_metadata_t ig_md,
        in ingress_intrinsic_metadata_t ig_intr_md,
        in ingress_intrinsic_metadata_from_parser_t ig_intr_prsr_md,
        inout ingress_intrinsic_metadata_for_deparser_t ig_intr_dprsr_md,
        inout ingress_intrinsic_metadata_for_tm_t ig_intr_tm_md) {

        // For debugging only
        action drop() {
            ig_intr_dprsr_md.drop_ctl = 0x1; // Drop packet.
        }

        @pragma stage 2
        table version_t {
            key = {
                hdr.ml_y.model: exact;
                hdr.ml_y.version: exact;
            }

            actions = {
                drop;
                NoAction;
            }
            const default_action = NoAction;
        }

        apply {
            // version control
            version_t.apply();

            // L2 forwarding
            if (ig_intr_md.ingress_port == 8) {
                ig_intr_tm_md.ucast_egress_port = 9;
            } else if (ig_intr_md.ingress_port == 9) {
                ig_intr_tm_md.ucast_egress_port = 8;
            }
        }

}

// ---------------------------------------------------------------------------
// Ingress Deparser
// ---------------------------------------------------------------------------
control SwitchIngressDeparser(
        packet_out pkt,
        inout header_t hdr,
        in ig_metadata_t ig_md,
        in ingress_intrinsic_metadata_for_deparser_t ig_intr_dprsr_md) {

    apply {
        pkt.emit(hdr.ethernet);
        pkt.emit(hdr.ml_x);
        pkt.emit(hdr.ml_y);
    }
}