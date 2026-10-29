control LINEAR_ACC_BLOCK(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {

        action block_6_accumulate() {
            eg_md.hyperplane_0 = eg_md.hyperplane_0 + eg_md.signed_int_0_6;
            eg_md.hyperplane_1 = eg_md.hyperplane_1 + eg_md.signed_int_1_6;
            eg_md.hyperplane_2 = eg_md.hyperplane_2 + eg_md.signed_int_2_6;
        }

        table block_6_aggregate_t {
            key = {
                hdr.ml_y.model: exact;
            }

            actions = {
                block_6_accumulate;
                NoAction;
            }
            const default_action = NoAction;
            size = 8192;
        }
        
        apply {
            block_6_aggregate_t.apply();
        }
}