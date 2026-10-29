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
        transition select (hdr.ethernet.ether_type) {
            ETHERTYPE_IPV4 : parse_ipv4;
            default : reject;
        }
    }

    state parse_ipv4 {
        pkt.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol) {
            IP_PROTOCOLS_TCP : parse_tcp;
            IP_PROTOCOLS_UDP : parse_udp;
            default : accept;
        }
    }

    state parse_tcp {
        pkt.extract(hdr.tcp);
        transition select(hdr.tcp.dst_port) {
            12345: parse_ml_x;
            default : accept;
        }
    }

    state parse_ml_x {
        pkt.extract(hdr.ml_x);
        transition parse_ml_y;
    }

    state parse_ml_y {
        pkt.extract(hdr.ml_y);
        transition accept;
    }

    state parse_udp {
        pkt.extract(hdr.udp);
        transition select(hdr.udp.dst_port) {
            default : accept;
        }
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

        // L2 forwarding
        action unicast(PortId_t port_id) {
            ig_intr_tm_md.ucast_egress_port = port_id;
        }

        @pragma stage 5
        table l2_forward_t {
            key = {
                ig_intr_md.ingress_port : exact;
            }
            actions = {
                unicast;
                NoAction;
            }
            const default_action = NoAction;
            size = 8;
        }

        apply {
            // version control
            version_t.apply();

            // L2 forwaring
            l2_forward_t.apply();
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
        pkt.emit(hdr.ipv4);
        pkt.emit(hdr.tcp);
        pkt.emit(hdr.udp);
        pkt.emit(hdr.ml_x);
        pkt.emit(hdr.ml_y);
    }
}