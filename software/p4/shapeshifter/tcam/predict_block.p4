control PRED_BLOCK(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {

        action final_predict(bit<8> cls) {
            hdr.ml_y.result = cls;
        }

        table block_final_tree_predict_t {
            key = {
                hdr.ml_y.model: exact;
                eg_md.pred_0: exact;
                eg_md.pred_1: exact;
                eg_md.pred_2: exact;
                eg_md.pred_3: exact;
                eg_md.pred_4: exact;
                eg_md.pred_5: exact;
            }

            actions = {
                final_predict;
                NoAction;
            }
            const default_action = NoAction;
            size = 32768;
        }

        action linear_predict(bit<8> cls) {
            hdr.ml_y.result_2 = cls;
        }

        table block_final_linear_predict_t {
            key = {
                hdr.ml_y.model: exact;
                eg_md.hyperplane_0[15:15]: exact;
                eg_md.hyperplane_1[15:15]: exact;
                eg_md.hyperplane_2[15:15]: exact;
            }

            actions = {
                linear_predict;
                NoAction;
            }
            const default_action = NoAction;
            size = 8;
        }
        
        apply {
            block_final_tree_predict_t.apply();
            block_final_linear_predict_t.apply();
        }
}
