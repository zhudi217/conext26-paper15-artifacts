control ML_BLOCK_0(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {
        
        FEATURE_TYPE feat_0;
        FEATURE_TYPE feat_1;
        FEATURE_TYPE feat_2;
        FEATURE_TYPE feat_3;
        FEATURE_TYPE feat_4;
        FEATURE_TYPE feat_5;
        FEATURE_TYPE feat_6;

        CODE_TYPE code_0;
        CODE_TYPE code_1;
        CODE_TYPE code_2;
        CODE_TYPE code_3;
        CODE_TYPE code_4;
        CODE_TYPE code_5;
        CODE_TYPE code_6;
        
        action select_feat0() {
            feat_0 = hdr.ml_x.feat_0;
        }
        
        action select_feat1() {
            feat_0 = hdr.ml_x.feat_1;
        }
        
        action select_feat2() {
            feat_0 = hdr.ml_x.feat_2;
        }
        
        action select_feat3() {
            feat_1 = hdr.ml_x.feat_3;
        }

        action select_feat4() {
            feat_1 = hdr.ml_x.feat_4;
        }

        action select_feat5() {
            feat_1 = hdr.ml_x.feat_5;
        }

        action select_feat6() {
            feat_2 = hdr.ml_x.feat_6;
        }

        action select_feat7() {
            feat_2 = hdr.ml_x.feat_7;
        }

        action select_feat8() {
            feat_2 = hdr.ml_x.feat_8;
        }

        action select_feat9() {
            feat_3 = hdr.ml_x.feat_9;
        }

        action select_feat10() {
            feat_3 = hdr.ml_x.feat_10;
        }

        action select_feat11() {
            feat_3 = hdr.ml_x.feat_11;
        }

        action select_feat12() {
            feat_4 = hdr.ml_x.feat_12;
        }

        action select_feat13() {
            feat_4 = hdr.ml_x.feat_13;
        }

        action select_feat14() {
            feat_4 = hdr.ml_x.feat_14;
        }

        action select_feat15() {
            feat_5 = hdr.ml_x.feat_15;
        }

        action select_feat16() {
            feat_5 = hdr.ml_x.feat_16;
        }

        action select_feat17() {
            feat_5 = hdr.ml_x.feat_17;
        }

        action select_feat18() {
            feat_6 = hdr.ml_x.feat_18;
        }

        action select_feat19() {
            feat_6 = hdr.ml_x.feat_19;
        }

        action select_feat20() {
            feat_6 = hdr.ml_x.feat_20;
        }

        action select_feat21() {
            feat_0 = hdr.ml_x.feat_21;
        }

        action select_feat22() {
            feat_1 = hdr.ml_x.feat_22;
        }

        action select_feat23() {
            feat_2 = hdr.ml_x.feat_23;
        }

        action select_feat24() {
            feat_3 = hdr.ml_x.feat_24;
        }

        action select_feat25() {
            feat_4 = hdr.ml_x.feat_25;
        }

        action select_feat26() {
            feat_5 = hdr.ml_x.feat_26;
        }

        action select_feat27() {
            feat_6 = hdr.ml_x.feat_27;
        }

        action select_feat28() {
            feat_0 = hdr.ml_x.feat_28;
        }

        action select_feat29() {
            feat_1 = hdr.ml_x.feat_29;
        }

        action select_feat30() {
            feat_2 = hdr.ml_x.feat_30;
        }

        action select_feat31() {
            feat_3 = hdr.ml_x.feat_31;
        }

        action select_feat32() {
            feat_4 = hdr.ml_x.feat_32;
        }

        action select_feat33() {
            feat_5 = hdr.ml_x.feat_33;
        }

        action select_feat34() {
            feat_6 = hdr.ml_x.feat_34;
        }

        action select_feat35() {
            feat_0 = hdr.ml_x.feat_35;
        }

        action select_feat36() {
            feat_1 = hdr.ml_x.feat_36;
        }

        action select_feat37() {
            feat_2 = hdr.ml_x.feat_37;
        }

        action select_feat38() {
            feat_3 = hdr.ml_x.feat_38;
        }

        action select_feat39() {
            feat_4 = hdr.ml_x.feat_39;
        }

        action select_feat40() {
            feat_5 = hdr.ml_x.feat_40;
        }

        action select_feat41() {
            feat_6 = hdr.ml_x.feat_41;
        }

        @pragma stage 0
        table select_feat_0_t {
            key = {
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat0;
                select_feat1;
                select_feat2;
                select_feat21;
                select_feat28;
                select_feat35;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 0
        table select_feat_1_t {
            key = {
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat3;
                select_feat4;
                select_feat5;
                select_feat22;
                select_feat29;
                select_feat36;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 0
        table select_feat_2_t {
            key = {
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat6;
                select_feat7;
                select_feat8;
                select_feat23;
                select_feat30;
                select_feat37;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 0
        table select_feat_3_t {
            key = {
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat9;
                select_feat10;
                select_feat11;
                select_feat24;
                select_feat31;
                select_feat38;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 0
        table select_feat_4_t {
            key = {
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat12;
                select_feat13;
                select_feat14;
                select_feat25;
                select_feat32;
                select_feat39;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 0
        table select_feat_5_t {
            key = {
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat15;
                select_feat16;
                select_feat17;
                select_feat26;
                select_feat33;
                select_feat40;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 0
        table select_feat_6_t {
            key = {
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat18;
                select_feat19;
                select_feat20;
                select_feat27;
                select_feat34;
                select_feat41;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        // Compute feature actions for even numbered stages
        action compute_feat_0(CODE_TYPE code) {
            code_0 = code;
        }

        action compute_feat_1(CODE_TYPE code) {
            code_1 = code;
        }

        action compute_feat_2(CODE_TYPE code) {
            code_2 = code;
        }

        action compute_feat_3(CODE_TYPE code) {
            code_3 = code;
        }

        action compute_feat_4(CODE_TYPE code) {
            code_4 = code;
        }

        action compute_feat_5(CODE_TYPE code) {
            code_5 = code;
        }

        action compute_feat_6(CODE_TYPE code) {
            code_6 = code;
        }

        // Linear accumulations
        ACC_TYPE signed_int_0_0;
        ACC_TYPE signed_int_1_0;
        ACC_TYPE signed_int_2_0;

        action sum_integer_0(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            signed_int_0_0 = signed_int_0_0 + value;
            signed_int_1_0 = signed_int_1_0 + value2;
            signed_int_2_0 = signed_int_2_0 + value3;
        }

        action sum_integer_1(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_1 = eg_md.signed_int_0_1 + value;
            eg_md.signed_int_1_1 = eg_md.signed_int_1_1 + value2;
            eg_md.signed_int_2_1 = eg_md.signed_int_2_1 + value3;
        }

        action sum_integer_2(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_2 = eg_md.signed_int_0_2 + value;
            eg_md.signed_int_1_2 = eg_md.signed_int_1_2 + value2;
            eg_md.signed_int_2_2 = eg_md.signed_int_2_2 + value3;
        }

        action sum_integer_3(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_3 = eg_md.signed_int_0_3 + value;
            eg_md.signed_int_1_3 = eg_md.signed_int_1_3 + value2;
            eg_md.signed_int_2_3 = eg_md.signed_int_2_3 + value3;
        }

        action sum_integer_4(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_4 = eg_md.signed_int_0_4 + value;
            eg_md.signed_int_1_4 = eg_md.signed_int_1_4 + value2;
            eg_md.signed_int_2_4 = eg_md.signed_int_2_4 + value3;
        }

        action sum_integer_5(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_5 = eg_md.signed_int_0_5 + value;
            eg_md.signed_int_1_5 = eg_md.signed_int_1_5 + value2;
            eg_md.signed_int_2_5 = eg_md.signed_int_2_5 + value3;
        }

        action sum_integer_6(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_6 = eg_md.signed_int_0_6 + value;
            eg_md.signed_int_1_6 = eg_md.signed_int_1_6 + value2;
            eg_md.signed_int_2_6 = eg_md.signed_int_2_6 + value3;
        }

        @pragma stage 1
        table compute_feat_0_t {
            key = {
                feat_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_0;
                sum_integer_0;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 1
        table compute_feat_1_t {
            key = {
                feat_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_1;
                sum_integer_1;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 1
        table compute_feat_2_t {
            key = {
                feat_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_2;
                sum_integer_2;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 1
        table compute_feat_3_t {
            key = {
                feat_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_3;
                sum_integer_3;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 1
        table compute_feat_4_t {
            key = {
                feat_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_4;
                sum_integer_4;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 1
        table compute_feat_5_t {
            key = {
                feat_5: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_5;
                sum_integer_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 1
        table compute_feat_6_t {
            key = {
                feat_6: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_6;
                sum_integer_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        action predict_0(RESULT_TYPE cls) {
            eg_md.pred_0 = cls;
        }

        action predict_1(RESULT_TYPE cls) {
            eg_md.pred_1 = cls;
        }

        action predict_2(RESULT_TYPE cls) {
            eg_md.pred_2 = cls;
        }

        action predict_3(RESULT_TYPE cls) {
            eg_md.pred_3 = cls;
        }

        action predict_4(RESULT_TYPE cls) {
            eg_md.pred_4 = cls;
        }

        action predict_5(RESULT_TYPE cls) {
            eg_md.pred_5 = cls;
        }

        action subtree_decision_0(bit<16> decision) {
            eg_md.subtree_idx_0 = decision;
        }

        action block_0_accumulate() {
            eg_md.hyperplane_0 = eg_md.hyperplane_0 + signed_int_0_0;
            eg_md.hyperplane_1 = eg_md.hyperplane_1 + signed_int_1_0;
            eg_md.hyperplane_2 = eg_md.hyperplane_2 + signed_int_2_0;
        }

        @pragma stage 2
        table block_0_aggregate_t {
            key = {
                code_0: exact;
                code_1: exact;
                code_2: exact;
                code_3: exact;
                code_4: exact;
                code_5: exact;
                code_6: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                predict_0;
                predict_1;
                predict_2;
                predict_3;
                predict_4;
                predict_5;
                subtree_decision_0;
                block_0_accumulate;
                NoAction;
            }
            const default_action = NoAction;
            size = AGGREGATE_SIZE;
        }

    apply {
        //
        code_0 = 0;
        code_1 = 0;
        code_2 = 0;
        code_3 = 0;
        code_4 = 0;
        code_5 = 0;
        code_6 = 0;

        // select feature
        select_feat_0_t.apply();
        select_feat_1_t.apply();
        select_feat_2_t.apply();
        select_feat_3_t.apply();
        select_feat_4_t.apply();
        select_feat_5_t.apply();
        select_feat_6_t.apply();

        // feature compute
        compute_feat_0_t.apply();
        compute_feat_1_t.apply();
        compute_feat_2_t.apply();
        compute_feat_3_t.apply();
        compute_feat_4_t.apply();
        compute_feat_5_t.apply();
        compute_feat_6_t.apply();

        // aggregate
        block_0_aggregate_t.apply();
    }
}

control ML_BLOCK_1(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {

        FEATURE_TYPE feat_0;
        FEATURE_TYPE feat_1;
        FEATURE_TYPE feat_2;
        FEATURE_TYPE feat_3;
        FEATURE_TYPE feat_4;
        FEATURE_TYPE feat_5;
        FEATURE_TYPE feat_6;

        CODE_TYPE code_0;
        CODE_TYPE code_1;
        CODE_TYPE code_2;
        CODE_TYPE code_3;
        CODE_TYPE code_4;
        CODE_TYPE code_5;
        CODE_TYPE code_6;

        action select_feat0() {
            feat_0 = hdr.ml_x.feat_0;
        }

        action select_feat1() {
            feat_0 = hdr.ml_x.feat_1;
        }

        action select_feat2() {
            feat_0 = hdr.ml_x.feat_2;
        }

        action select_feat3() {
            feat_1 = hdr.ml_x.feat_3;
        }

        action select_feat4() {
            feat_1 = hdr.ml_x.feat_4;
        }

        action select_feat5() {
            feat_1 = hdr.ml_x.feat_5;
        }

        action select_feat6() {
            feat_2 = hdr.ml_x.feat_6;
        }

        action select_feat7() {
            feat_2 = hdr.ml_x.feat_7;
        }

        action select_feat8() {
            feat_2 = hdr.ml_x.feat_8;
        }

        action select_feat9() {
            feat_3 = hdr.ml_x.feat_9;
        }

        action select_feat10() {
            feat_3 = hdr.ml_x.feat_10;
        }

        action select_feat11() {
            feat_3 = hdr.ml_x.feat_11;
        }

        action select_feat12() {
            feat_4 = hdr.ml_x.feat_12;
        }

        action select_feat13() {
            feat_4 = hdr.ml_x.feat_13;
        }

        action select_feat14() {
            feat_4 = hdr.ml_x.feat_14;
        }

        action select_feat15() {
            feat_5 = hdr.ml_x.feat_15;
        }

        action select_feat16() {
            feat_5 = hdr.ml_x.feat_16;
        }

        action select_feat17() {
            feat_5 = hdr.ml_x.feat_17;
        }

        action select_feat18() {
            feat_6 = hdr.ml_x.feat_18;
        }

        action select_feat19() {
            feat_6 = hdr.ml_x.feat_19;
        }

        action select_feat20() {
            feat_6 = hdr.ml_x.feat_20;
        }

        action select_feat21() {
            feat_0 = hdr.ml_x.feat_21;
        }

        action select_feat22() {
            feat_1 = hdr.ml_x.feat_22;
        }

        action select_feat23() {
            feat_2 = hdr.ml_x.feat_23;
        }

        action select_feat24() {
            feat_3 = hdr.ml_x.feat_24;
        }

        action select_feat25() {
            feat_4 = hdr.ml_x.feat_25;
        }

        action select_feat26() {
            feat_5 = hdr.ml_x.feat_26;
        }

        action select_feat27() {
            feat_6 = hdr.ml_x.feat_27;
        }

        action select_feat28() {
            feat_0 = hdr.ml_x.feat_28;
        }

        action select_feat29() {
            feat_1 = hdr.ml_x.feat_29;
        }

        action select_feat30() {
            feat_2 = hdr.ml_x.feat_30;
        }

        action select_feat31() {
            feat_3 = hdr.ml_x.feat_31;
        }

        action select_feat32() {
            feat_4 = hdr.ml_x.feat_32;
        }

        action select_feat33() {
            feat_5 = hdr.ml_x.feat_33;
        }

        action select_feat34() {
            feat_6 = hdr.ml_x.feat_34;
        }

        action select_feat35() {
            feat_0 = hdr.ml_x.feat_35;
        }

        action select_feat36() {
            feat_1 = hdr.ml_x.feat_36;
        }

        action select_feat37() {
            feat_2 = hdr.ml_x.feat_37;
        }

        action select_feat38() {
            feat_3 = hdr.ml_x.feat_38;
        }

        action select_feat39() {
            feat_4 = hdr.ml_x.feat_39;
        }

        action select_feat40() {
            feat_5 = hdr.ml_x.feat_40;
        }

        action select_feat41() {
            feat_6 = hdr.ml_x.feat_41;
        }

        @pragma stage 3
        table select_feat_0_t {
            key = {
                eg_md.subtree_idx_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat0;
                select_feat1;
                select_feat2;
                select_feat21;
                select_feat28;
                select_feat35;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 3
        table select_feat_1_t {
            key = {
                eg_md.subtree_idx_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat3;
                select_feat4;
                select_feat5;
                select_feat22;
                select_feat29;
                select_feat36;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 3
        table select_feat_2_t {
            key = {
                eg_md.subtree_idx_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat6;
                select_feat7;
                select_feat8;
                select_feat23;
                select_feat30;
                select_feat37;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 3
        table select_feat_3_t {
            key = {
                eg_md.subtree_idx_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat9;
                select_feat10;
                select_feat11;
                select_feat24;
                select_feat31;
                select_feat38;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 3
        table select_feat_4_t {
            key = {
                eg_md.subtree_idx_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat12;
                select_feat13;
                select_feat14;
                select_feat25;
                select_feat32;
                select_feat39;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 3
        table select_feat_5_t {
            key = {
                eg_md.subtree_idx_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat15;
                select_feat16;
                select_feat17;
                select_feat26;
                select_feat33;
                select_feat40;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 3
        table select_feat_6_t {
            key = {
                eg_md.subtree_idx_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat18;
                select_feat19;
                select_feat20;
                select_feat27;
                select_feat34;
                select_feat41;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        // Compute feature actions for even numbered stages
        action compute_feat_0(CODE_TYPE code) {
            code_0 = code;
        }

        action compute_feat_1(CODE_TYPE code) {
            code_1 = code;
        }

        action compute_feat_2(CODE_TYPE code) {
            code_2 = code;
        }

        action compute_feat_3(CODE_TYPE code) {
            code_3 = code;
        }

        action compute_feat_4(CODE_TYPE code) {
            code_4 = code;
        }

        action compute_feat_5(CODE_TYPE code) {
            code_5 = code;
        }

        action compute_feat_6(CODE_TYPE code) {
            code_6 = code;
        }

        // Linear accumulation
        action sum_integer_1(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_1 = eg_md.signed_int_0_1 + value;
            eg_md.signed_int_1_1 = eg_md.signed_int_1_1 + value2;
            eg_md.signed_int_2_1 = eg_md.signed_int_2_1 + value3;
        }

        action sum_integer_2(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_2 = eg_md.signed_int_0_2 + value;
            eg_md.signed_int_1_2 = eg_md.signed_int_1_2 + value2;
            eg_md.signed_int_2_2 = eg_md.signed_int_2_2 + value3;
        }

        action sum_integer_3(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_3 = eg_md.signed_int_0_3 + value;
            eg_md.signed_int_1_3 = eg_md.signed_int_1_3 + value2;
            eg_md.signed_int_2_3 = eg_md.signed_int_2_3 + value3;
        }

        action sum_integer_4(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_4 = eg_md.signed_int_0_4 + value;
            eg_md.signed_int_1_4 = eg_md.signed_int_1_4 + value2;
            eg_md.signed_int_2_4 = eg_md.signed_int_2_4 + value3;
        }

        action sum_integer_5(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_5 = eg_md.signed_int_0_5 + value;
            eg_md.signed_int_1_5 = eg_md.signed_int_1_5 + value2;
            eg_md.signed_int_2_5 = eg_md.signed_int_2_5 + value3;
        }

        action sum_integer_6(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_6 = eg_md.signed_int_0_6 + value;
            eg_md.signed_int_1_6 = eg_md.signed_int_1_6 + value2;
            eg_md.signed_int_2_6 = eg_md.signed_int_2_6 + value3;
        }

        @pragma stage 4
        table compute_feat_0_t {
            key = {
                feat_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_0;
                sum_integer_1;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 4
        table compute_feat_1_t {
            key = {
                feat_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_1;
                sum_integer_2;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 4
        table compute_feat_2_t {
            key = {
                feat_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_2;
                sum_integer_3;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 4
        table compute_feat_3_t {
            key = {
                feat_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_3;
                sum_integer_4;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 4
        table compute_feat_4_t {
            key = {
                feat_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_4;
                sum_integer_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 4
        table compute_feat_5_t {
            key = {
                feat_5: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_5;
                sum_integer_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 4
        table compute_feat_6_t {
            key = {
                feat_6: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        action predict_0(RESULT_TYPE cls) {
            eg_md.pred_0 = cls;
        }

        action predict_1(RESULT_TYPE cls) {
            eg_md.pred_1 = cls;
        }

        action predict_2(RESULT_TYPE cls) {
            eg_md.pred_2 = cls;
        }

        action predict_3(RESULT_TYPE cls) {
            eg_md.pred_3 = cls;
        }

        action predict_4(RESULT_TYPE cls) {
            eg_md.pred_4 = cls;
        }

        action predict_5(RESULT_TYPE cls) {
            eg_md.pred_5 = cls;
        }

        action subtree_decision_1(bit<16> decision) {
            eg_md.subtree_idx_1 = decision;
        }

        action block_1_accumulate() {
            eg_md.hyperplane_0 = eg_md.hyperplane_0 + eg_md.signed_int_0_1;
            eg_md.hyperplane_1 = eg_md.hyperplane_1 + eg_md.signed_int_1_1;
            eg_md.hyperplane_2 = eg_md.hyperplane_2 + eg_md.signed_int_2_1;
        }

        @pragma stage 5
        table block_1_aggregate_t {
            key = {
                code_0: exact;
                code_1: exact;
                code_2: exact;
                code_3: exact;
                code_4: exact;
                code_5: exact;
                code_6: exact;
                eg_md.subtree_idx_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                predict_0;
                predict_1;
                predict_2;
                predict_3;
                predict_4;
                predict_5;
                subtree_decision_1;
                block_1_accumulate;
                NoAction;
            }
            const default_action = NoAction;
            size = AGGREGATE_SIZE;
        }

    apply {
        //
        code_0 = 0;
        code_1 = 0;
        code_2 = 0;
        code_3 = 0;
        code_4 = 0;
        code_5 = 0;
        code_6 = 0;

        // select feature
        select_feat_0_t.apply();
        select_feat_1_t.apply();
        select_feat_2_t.apply();
        select_feat_3_t.apply();
        select_feat_4_t.apply();
        select_feat_5_t.apply();
        select_feat_6_t.apply();

        // feature compute
        compute_feat_0_t.apply();
        compute_feat_1_t.apply();
        compute_feat_2_t.apply();
        compute_feat_3_t.apply();
        compute_feat_4_t.apply();
        compute_feat_5_t.apply();
        compute_feat_6_t.apply();

        // aggregate
        block_1_aggregate_t.apply();
    }
}

control ML_BLOCK_2(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {

        FEATURE_TYPE feat_0;
        FEATURE_TYPE feat_1;
        FEATURE_TYPE feat_2;
        FEATURE_TYPE feat_3;
        FEATURE_TYPE feat_4;
        FEATURE_TYPE feat_5;
        FEATURE_TYPE feat_6;

        CODE_TYPE code_0;
        CODE_TYPE code_1;
        CODE_TYPE code_2;
        CODE_TYPE code_3;
        CODE_TYPE code_4;
        CODE_TYPE code_5;
        CODE_TYPE code_6;

        action select_feat0() {
            feat_0 = hdr.ml_x.feat_0;
        }

        action select_feat1() {
            feat_0 = hdr.ml_x.feat_1;
        }

        action select_feat2() {
            feat_0 = hdr.ml_x.feat_2;
        }

        action select_feat3() {
            feat_1 = hdr.ml_x.feat_3;
        }

        action select_feat4() {
            feat_1 = hdr.ml_x.feat_4;
        }

        action select_feat5() {
            feat_1 = hdr.ml_x.feat_5;
        }

        action select_feat6() {
            feat_2 = hdr.ml_x.feat_6;
        }

        action select_feat7() {
            feat_2 = hdr.ml_x.feat_7;
        }

        action select_feat8() {
            feat_2 = hdr.ml_x.feat_8;
        }

        action select_feat9() {
            feat_3 = hdr.ml_x.feat_9;
        }

        action select_feat10() {
            feat_3 = hdr.ml_x.feat_10;
        }

        action select_feat11() {
            feat_3 = hdr.ml_x.feat_11;
        }

        action select_feat12() {
            feat_4 = hdr.ml_x.feat_12;
        }

        action select_feat13() {
            feat_4 = hdr.ml_x.feat_13;
        }

        action select_feat14() {
            feat_4 = hdr.ml_x.feat_14;
        }

        action select_feat15() {
            feat_5 = hdr.ml_x.feat_15;
        }

        action select_feat16() {
            feat_5 = hdr.ml_x.feat_16;
        }

        action select_feat17() {
            feat_5 = hdr.ml_x.feat_17;
        }

        action select_feat18() {
            feat_6 = hdr.ml_x.feat_18;
        }

        action select_feat19() {
            feat_6 = hdr.ml_x.feat_19;
        }

        action select_feat20() {
            feat_6 = hdr.ml_x.feat_20;
        }

        action select_feat21() {
            feat_0 = hdr.ml_x.feat_21;
        }

        action select_feat22() {
            feat_1 = hdr.ml_x.feat_22;
        }

        action select_feat23() {
            feat_2 = hdr.ml_x.feat_23;
        }

        action select_feat24() {
            feat_3 = hdr.ml_x.feat_24;
        }

        action select_feat25() {
            feat_4 = hdr.ml_x.feat_25;
        }

        action select_feat26() {
            feat_5 = hdr.ml_x.feat_26;
        }

        action select_feat27() {
            feat_6 = hdr.ml_x.feat_27;
        }

        action select_feat28() {
            feat_0 = hdr.ml_x.feat_28;
        }

        action select_feat29() {
            feat_1 = hdr.ml_x.feat_29;
        }

        action select_feat30() {
            feat_2 = hdr.ml_x.feat_30;
        }

        action select_feat31() {
            feat_3 = hdr.ml_x.feat_31;
        }

        action select_feat32() {
            feat_4 = hdr.ml_x.feat_32;
        }

        action select_feat33() {
            feat_5 = hdr.ml_x.feat_33;
        }

        action select_feat34() {
            feat_6 = hdr.ml_x.feat_34;
        }

        action select_feat35() {
            feat_0 = hdr.ml_x.feat_35;
        }

        action select_feat36() {
            feat_1 = hdr.ml_x.feat_36;
        }

        action select_feat37() {
            feat_2 = hdr.ml_x.feat_37;
        }

        action select_feat38() {
            feat_3 = hdr.ml_x.feat_38;
        }

        action select_feat39() {
            feat_4 = hdr.ml_x.feat_39;
        }

        action select_feat40() {
            feat_5 = hdr.ml_x.feat_40;
        }

        action select_feat41() {
            feat_6 = hdr.ml_x.feat_41;
        }

        @pragma stage 6
        table select_feat_0_t {
            key = {
                eg_md.subtree_idx_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat0;
                select_feat1;
                select_feat2;
                select_feat21;
                select_feat28;
                select_feat35;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 6
        table select_feat_1_t {
            key = {
                eg_md.subtree_idx_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat3;
                select_feat4;
                select_feat5;
                select_feat22;
                select_feat29;
                select_feat36;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 6
        table select_feat_2_t {
            key = {
                eg_md.subtree_idx_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat6;
                select_feat7;
                select_feat8;
                select_feat23;
                select_feat30;
                select_feat37;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 6
        table select_feat_3_t {
            key = {
                eg_md.subtree_idx_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat9;
                select_feat10;
                select_feat11;
                select_feat24;
                select_feat31;
                select_feat38;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 6
        table select_feat_4_t {
            key = {
                eg_md.subtree_idx_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat12;
                select_feat13;
                select_feat14;
                select_feat25;
                select_feat32;
                select_feat39;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 6
        table select_feat_5_t {
            key = {
                eg_md.subtree_idx_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat15;
                select_feat16;
                select_feat17;
                select_feat26;
                select_feat33;
                select_feat40;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 6
        table select_feat_6_t {
            key = {
                eg_md.subtree_idx_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat18;
                select_feat19;
                select_feat20;
                select_feat27;
                select_feat34;
                select_feat41;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        // Compute feature actions for even numbered stages
        action compute_feat_0(CODE_TYPE code) {
            code_0 = code;
        }

        action compute_feat_1(CODE_TYPE code) {
            code_1 = code;
        }

        action compute_feat_2(CODE_TYPE code) {
            code_2 = code;
        }

        action compute_feat_3(CODE_TYPE code) {
            code_3 = code;
        }

        action compute_feat_4(CODE_TYPE code) {
            code_4 = code;
        }

        action compute_feat_5(CODE_TYPE code) {
            code_5 = code;
        }

        action compute_feat_6(CODE_TYPE code) {
            code_6 = code;
        }

        // Linear accumulation
        action sum_integer_2(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_2 = eg_md.signed_int_0_2 + value;
            eg_md.signed_int_1_2 = eg_md.signed_int_1_2 + value2;
            eg_md.signed_int_2_2 = eg_md.signed_int_2_2 + value3;
        }

        action sum_integer_3(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_3 = eg_md.signed_int_0_3 + value;
            eg_md.signed_int_1_3 = eg_md.signed_int_1_3 + value2;
            eg_md.signed_int_2_3 = eg_md.signed_int_2_3 + value3;
        }

        action sum_integer_4(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_4 = eg_md.signed_int_0_4 + value;
            eg_md.signed_int_1_4 = eg_md.signed_int_1_4 + value2;
            eg_md.signed_int_2_4 = eg_md.signed_int_2_4 + value3;
        }

        action sum_integer_5(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_5 = eg_md.signed_int_0_5 + value;
            eg_md.signed_int_1_5 = eg_md.signed_int_1_5 + value2;
            eg_md.signed_int_2_5 = eg_md.signed_int_2_5 + value3;
        }

        action sum_integer_6(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_6 = eg_md.signed_int_0_6 + value;
            eg_md.signed_int_1_6 = eg_md.signed_int_1_6 + value2;
            eg_md.signed_int_2_6 = eg_md.signed_int_2_6 + value3;
        }

        @pragma stage 7
        table compute_feat_0_t {
            key = {
                feat_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_0;
                sum_integer_2;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 7
        table compute_feat_1_t {
            key = {
                feat_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_1;
                sum_integer_3;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 7
        table compute_feat_2_t {
            key = {
                feat_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_2;
                sum_integer_4;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 7
        table compute_feat_3_t {
            key = {
                feat_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_3;
                sum_integer_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 7
        table compute_feat_4_t {
            key = {
                feat_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_4;
                sum_integer_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 7
        table compute_feat_5_t {
            key = {
                feat_5: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 7
        table compute_feat_6_t {
            key = {
                feat_6: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        action predict_0(RESULT_TYPE cls) {
            eg_md.pred_0 = cls;
        }

        action predict_1(RESULT_TYPE cls) {
            eg_md.pred_1 = cls;
        }

        action predict_2(RESULT_TYPE cls) {
            eg_md.pred_2 = cls;
        }

        action predict_3(RESULT_TYPE cls) {
            eg_md.pred_3 = cls;
        }

        action predict_4(RESULT_TYPE cls) {
            eg_md.pred_4 = cls;
        }

        action predict_5(RESULT_TYPE cls) {
            eg_md.pred_5 = cls;
        }

        action subtree_decision_2(bit<16> decision) {
            eg_md.subtree_idx_2 = decision;
        }

        action block_2_accumulate() {
            eg_md.hyperplane_0 = eg_md.hyperplane_0 + eg_md.signed_int_0_2;
            eg_md.hyperplane_1 = eg_md.hyperplane_1 + eg_md.signed_int_1_2;
            eg_md.hyperplane_2 = eg_md.hyperplane_2 + eg_md.signed_int_2_2;
        }

        @pragma stage 8
        table block_2_aggregate_t {
            key = {
                code_0: exact;
                code_1: exact;
                code_2: exact;
                code_3: exact;
                code_4: exact;
                code_5: exact;
                code_6: exact;
                eg_md.subtree_idx_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                predict_0;
                predict_1;
                predict_2;
                predict_3;
                predict_4;
                predict_5;
                subtree_decision_2;
                block_2_accumulate;
                NoAction;
            }
            const default_action = NoAction;
            size = AGGREGATE_SIZE;
        }

    apply {
        //
        code_0 = 0;
        code_1 = 0;
        code_2 = 0;
        code_3 = 0;
        code_4 = 0;
        code_5 = 0;
        code_6 = 0;

        // select feature
        select_feat_0_t.apply();
        select_feat_1_t.apply();
        select_feat_2_t.apply();
        select_feat_3_t.apply();
        select_feat_4_t.apply();
        select_feat_5_t.apply();
        select_feat_6_t.apply();

        // feature compute
        compute_feat_0_t.apply();
        compute_feat_1_t.apply();
        compute_feat_2_t.apply();
        compute_feat_3_t.apply();
        compute_feat_4_t.apply();
        compute_feat_5_t.apply();
        compute_feat_6_t.apply();

        // aggregate
        block_2_aggregate_t.apply();
    }
}

control ML_BLOCK_3(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {

        FEATURE_TYPE feat_0;
        FEATURE_TYPE feat_1;
        FEATURE_TYPE feat_2;
        FEATURE_TYPE feat_3;
        FEATURE_TYPE feat_4;
        FEATURE_TYPE feat_5;
        FEATURE_TYPE feat_6;

        CODE_TYPE code_0;
        CODE_TYPE code_1;
        CODE_TYPE code_2;
        CODE_TYPE code_3;
        CODE_TYPE code_4;
        CODE_TYPE code_5;
        CODE_TYPE code_6;

        action select_feat0() {
            feat_0 = hdr.ml_x.feat_0;
        }

        action select_feat1() {
            feat_0 = hdr.ml_x.feat_1;
        }

        action select_feat2() {
            feat_0 = hdr.ml_x.feat_2;
        }

        action select_feat3() {
            feat_1 = hdr.ml_x.feat_3;
        }

        action select_feat4() {
            feat_1 = hdr.ml_x.feat_4;
        }

        action select_feat5() {
            feat_1 = hdr.ml_x.feat_5;
        }

        action select_feat6() {
            feat_2 = hdr.ml_x.feat_6;
        }

        action select_feat7() {
            feat_2 = hdr.ml_x.feat_7;
        }

        action select_feat8() {
            feat_2 = hdr.ml_x.feat_8;
        }

        action select_feat9() {
            feat_3 = hdr.ml_x.feat_9;
        }

        action select_feat10() {
            feat_3 = hdr.ml_x.feat_10;
        }

        action select_feat11() {
            feat_3 = hdr.ml_x.feat_11;
        }

        action select_feat12() {
            feat_4 = hdr.ml_x.feat_12;
        }

        action select_feat13() {
            feat_4 = hdr.ml_x.feat_13;
        }

        action select_feat14() {
            feat_4 = hdr.ml_x.feat_14;
        }

        action select_feat15() {
            feat_5 = hdr.ml_x.feat_15;
        }

        action select_feat16() {
            feat_5 = hdr.ml_x.feat_16;
        }

        action select_feat17() {
            feat_5 = hdr.ml_x.feat_17;
        }

        action select_feat18() {
            feat_6 = hdr.ml_x.feat_18;
        }

        action select_feat19() {
            feat_6 = hdr.ml_x.feat_19;
        }

        action select_feat20() {
            feat_6 = hdr.ml_x.feat_20;
        }

        action select_feat21() {
            feat_0 = hdr.ml_x.feat_21;
        }

        action select_feat22() {
            feat_1 = hdr.ml_x.feat_22;
        }

        action select_feat23() {
            feat_2 = hdr.ml_x.feat_23;
        }

        action select_feat24() {
            feat_3 = hdr.ml_x.feat_24;
        }

        action select_feat25() {
            feat_4 = hdr.ml_x.feat_25;
        }

        action select_feat26() {
            feat_5 = hdr.ml_x.feat_26;
        }

        action select_feat27() {
            feat_6 = hdr.ml_x.feat_27;
        }

        action select_feat28() {
            feat_0 = hdr.ml_x.feat_28;
        }

        action select_feat29() {
            feat_1 = hdr.ml_x.feat_29;
        }

        action select_feat30() {
            feat_2 = hdr.ml_x.feat_30;
        }

        action select_feat31() {
            feat_3 = hdr.ml_x.feat_31;
        }

        action select_feat32() {
            feat_4 = hdr.ml_x.feat_32;
        }

        action select_feat33() {
            feat_5 = hdr.ml_x.feat_33;
        }

        action select_feat34() {
            feat_6 = hdr.ml_x.feat_34;
        }

        action select_feat35() {
            feat_0 = hdr.ml_x.feat_35;
        }

        action select_feat36() {
            feat_1 = hdr.ml_x.feat_36;
        }

        action select_feat37() {
            feat_2 = hdr.ml_x.feat_37;
        }

        action select_feat38() {
            feat_3 = hdr.ml_x.feat_38;
        }

        action select_feat39() {
            feat_4 = hdr.ml_x.feat_39;
        }

        action select_feat40() {
            feat_5 = hdr.ml_x.feat_40;
        }

        action select_feat41() {
            feat_6 = hdr.ml_x.feat_41;
        }

        @pragma stage 9
        table select_feat_0_t {
            key = {
                eg_md.subtree_idx_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat0;
                select_feat1;
                select_feat2;
                select_feat21;
                select_feat28;
                select_feat35;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 9
        table select_feat_1_t {
            key = {
                eg_md.subtree_idx_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat3;
                select_feat4;
                select_feat5;
                select_feat22;
                select_feat29;
                select_feat36;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 9
        table select_feat_2_t {
            key = {
                eg_md.subtree_idx_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat6;
                select_feat7;
                select_feat8;
                select_feat23;
                select_feat30;
                select_feat37;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 9
        table select_feat_3_t {
            key = {
                eg_md.subtree_idx_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat9;
                select_feat10;
                select_feat11;
                select_feat24;
                select_feat31;
                select_feat38;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 9
        table select_feat_4_t {
            key = {
                eg_md.subtree_idx_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat12;
                select_feat13;
                select_feat14;
                select_feat25;
                select_feat32;
                select_feat39;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 9
        table select_feat_5_t {
            key = {
                eg_md.subtree_idx_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat15;
                select_feat16;
                select_feat17;
                select_feat26;
                select_feat33;
                select_feat40;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 9
        table select_feat_6_t {
            key = {
                eg_md.subtree_idx_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat18;
                select_feat19;
                select_feat20;
                select_feat27;
                select_feat34;
                select_feat41;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        // Compute feature actions for even numbered stages
        action compute_feat_0(CODE_TYPE code) {
            code_0 = code;
        }

        action compute_feat_1(CODE_TYPE code) {
            code_1 = code;
        }

        action compute_feat_2(CODE_TYPE code) {
            code_2 = code;
        }

        action compute_feat_3(CODE_TYPE code) {
            code_3 = code;
        }

        action compute_feat_4(CODE_TYPE code) {
            code_4 = code;
        }

        action compute_feat_5(CODE_TYPE code) {
            code_5 = code;
        }

        action compute_feat_6(CODE_TYPE code) {
            code_6 = code;
        }

        // Linear accumulation
        action sum_integer_3(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_3 = eg_md.signed_int_0_3 + value;
            eg_md.signed_int_1_3 = eg_md.signed_int_1_3 + value2;
            eg_md.signed_int_2_3 = eg_md.signed_int_2_3 + value3;
        }

        action sum_integer_4(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_4 = eg_md.signed_int_0_4 + value;
            eg_md.signed_int_1_4 = eg_md.signed_int_1_4 + value2;
            eg_md.signed_int_2_4 = eg_md.signed_int_2_4 + value3;
        }

        action sum_integer_5(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_5 = eg_md.signed_int_0_5 + value;
            eg_md.signed_int_1_5 = eg_md.signed_int_1_5 + value2;
            eg_md.signed_int_2_5 = eg_md.signed_int_2_5 + value3;
        }

        action sum_integer_6(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_6 = eg_md.signed_int_0_6 + value;
            eg_md.signed_int_1_6 = eg_md.signed_int_1_6 + value2;
            eg_md.signed_int_2_6 = eg_md.signed_int_2_6 + value3;
        }

        @pragma stage 10
        table compute_feat_0_t {
            key = {
                feat_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_0;
                sum_integer_3;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 10
        table compute_feat_1_t {
            key = {
                feat_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_1;
                sum_integer_4;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 10
        table compute_feat_2_t {
            key = {
                feat_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_2;
                sum_integer_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 10
        table compute_feat_3_t {
            key = {
                feat_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_3;
                sum_integer_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 10
        table compute_feat_4_t {
            key = {
                feat_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_4;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 10
        table compute_feat_5_t {
            key = {
                feat_5: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 10
        table compute_feat_6_t {
            key = {
                feat_6: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        action predict_0(RESULT_TYPE cls) {
            eg_md.pred_0 = cls;
        }

        action predict_1(RESULT_TYPE cls) {
            eg_md.pred_1 = cls;
        }

        action predict_2(RESULT_TYPE cls) {
            eg_md.pred_2 = cls;
        }

        action predict_3(RESULT_TYPE cls) {
            eg_md.pred_3 = cls;
        }

        action predict_4(RESULT_TYPE cls) {
            eg_md.pred_4 = cls;
        }

        action predict_5(RESULT_TYPE cls) {
            eg_md.pred_5 = cls;
        }

        action subtree_decision_3(bit<16> decision) {
            eg_md.subtree_idx_3 = decision;
        }

        action block_3_accumulate() {
            eg_md.hyperplane_0 = eg_md.hyperplane_0 + eg_md.signed_int_0_3;
            eg_md.hyperplane_1 = eg_md.hyperplane_1 + eg_md.signed_int_1_3;
            eg_md.hyperplane_2 = eg_md.hyperplane_2 + eg_md.signed_int_2_3;
        }

        @pragma stage 11
        table block_3_aggregate_t {
            key = {
                code_0: exact;
                code_1: exact;
                code_2: exact;
                code_3: exact;
                code_4: exact;
                code_5: exact;
                code_6: exact;
                eg_md.subtree_idx_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                predict_0;
                predict_1;
                predict_2;
                predict_3;
                predict_4;
                predict_5;
                subtree_decision_3;
                block_3_accumulate;
                NoAction;
            }
            const default_action = NoAction;
            size = AGGREGATE_SIZE;
        }

    apply {
        code_0 = 0;
        code_1 = 0;
        code_2 = 0;
        code_3 = 0;
        code_4 = 0;
        code_5 = 0;
        code_6 = 0;

        // select feature
        select_feat_0_t.apply();
        select_feat_1_t.apply();
        select_feat_2_t.apply();
        select_feat_3_t.apply();
        select_feat_4_t.apply();
        select_feat_5_t.apply();
        select_feat_6_t.apply();

        // feature compute
        compute_feat_0_t.apply();
        compute_feat_1_t.apply();
        compute_feat_2_t.apply();
        compute_feat_3_t.apply();
        compute_feat_4_t.apply();
        compute_feat_5_t.apply();
        compute_feat_6_t.apply();

        // aggregate
        block_3_aggregate_t.apply();
    }
}

control ML_BLOCK_4(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {

        FEATURE_TYPE feat_0;
        FEATURE_TYPE feat_1;
        FEATURE_TYPE feat_2;
        FEATURE_TYPE feat_3;
        FEATURE_TYPE feat_4;
        FEATURE_TYPE feat_5;
        FEATURE_TYPE feat_6;

        CODE_TYPE code_0;
        CODE_TYPE code_1;
        CODE_TYPE code_2;
        CODE_TYPE code_3;
        CODE_TYPE code_4;
        CODE_TYPE code_5;
        CODE_TYPE code_6;

        action select_feat0() {
            feat_0 = hdr.ml_x.feat_0;
        }

        action select_feat1() {
            feat_0 = hdr.ml_x.feat_1;
        }

        action select_feat2() {
            feat_0 = hdr.ml_x.feat_2;
        }

        action select_feat3() {
            feat_1 = hdr.ml_x.feat_3;
        }

        action select_feat4() {
            feat_1 = hdr.ml_x.feat_4;
        }

        action select_feat5() {
            feat_1 = hdr.ml_x.feat_5;
        }

        action select_feat6() {
            feat_2 = hdr.ml_x.feat_6;
        }

        action select_feat7() {
            feat_2 = hdr.ml_x.feat_7;
        }

        action select_feat8() {
            feat_2 = hdr.ml_x.feat_8;
        }

        action select_feat9() {
            feat_3 = hdr.ml_x.feat_9;
        }

        action select_feat10() {
            feat_3 = hdr.ml_x.feat_10;
        }

        action select_feat11() {
            feat_3 = hdr.ml_x.feat_11;
        }

        action select_feat12() {
            feat_4 = hdr.ml_x.feat_12;
        }

        action select_feat13() {
            feat_4 = hdr.ml_x.feat_13;
        }

        action select_feat14() {
            feat_4 = hdr.ml_x.feat_14;
        }

        action select_feat15() {
            feat_5 = hdr.ml_x.feat_15;
        }

        action select_feat16() {
            feat_5 = hdr.ml_x.feat_16;
        }

        action select_feat17() {
            feat_5 = hdr.ml_x.feat_17;
        }

        action select_feat18() {
            feat_6 = hdr.ml_x.feat_18;
        }

        action select_feat19() {
            feat_6 = hdr.ml_x.feat_19;
        }

        action select_feat20() {
            feat_6 = hdr.ml_x.feat_20;
        }

        action select_feat21() {
            feat_0 = hdr.ml_x.feat_21;
        }

        action select_feat22() {
            feat_1 = hdr.ml_x.feat_22;
        }

        action select_feat23() {
            feat_2 = hdr.ml_x.feat_23;
        }

        action select_feat24() {
            feat_3 = hdr.ml_x.feat_24;
        }

        action select_feat25() {
            feat_4 = hdr.ml_x.feat_25;
        }

        action select_feat26() {
            feat_5 = hdr.ml_x.feat_26;
        }

        action select_feat27() {
            feat_6 = hdr.ml_x.feat_27;
        }

        action select_feat28() {
            feat_0 = hdr.ml_x.feat_28;
        }

        action select_feat29() {
            feat_1 = hdr.ml_x.feat_29;
        }

        action select_feat30() {
            feat_2 = hdr.ml_x.feat_30;
        }

        action select_feat31() {
            feat_3 = hdr.ml_x.feat_31;
        }

        action select_feat32() {
            feat_4 = hdr.ml_x.feat_32;
        }

        action select_feat33() {
            feat_5 = hdr.ml_x.feat_33;
        }

        action select_feat34() {
            feat_6 = hdr.ml_x.feat_34;
        }

        action select_feat35() {
            feat_0 = hdr.ml_x.feat_35;
        }

        action select_feat36() {
            feat_1 = hdr.ml_x.feat_36;
        }

        action select_feat37() {
            feat_2 = hdr.ml_x.feat_37;
        }

        action select_feat38() {
            feat_3 = hdr.ml_x.feat_38;
        }

        action select_feat39() {
            feat_4 = hdr.ml_x.feat_39;
        }

        action select_feat40() {
            feat_5 = hdr.ml_x.feat_40;
        }

        action select_feat41() {
            feat_6 = hdr.ml_x.feat_41;
        }

        @pragma stage 12
        table select_feat_0_t {
            key = {
                eg_md.subtree_idx_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat0;
                select_feat1;
                select_feat2;
                select_feat21;
                select_feat28;
                select_feat35;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 12
        table select_feat_1_t {
            key = {
                eg_md.subtree_idx_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat3;
                select_feat4;
                select_feat5;
                select_feat22;
                select_feat29;
                select_feat36;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 12
        table select_feat_2_t {
            key = {
                eg_md.subtree_idx_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat6;
                select_feat7;
                select_feat8;
                select_feat23;
                select_feat30;
                select_feat37;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 12
        table select_feat_3_t {
            key = {
                eg_md.subtree_idx_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat9;
                select_feat10;
                select_feat11;
                select_feat24;
                select_feat31;
                select_feat38;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 12
        table select_feat_4_t {
            key = {
                eg_md.subtree_idx_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat12;
                select_feat13;
                select_feat14;
                select_feat25;
                select_feat32;
                select_feat39;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 12
        table select_feat_5_t {
            key = {
                eg_md.subtree_idx_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat15;
                select_feat16;
                select_feat17;
                select_feat26;
                select_feat33;
                select_feat40;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 12
        table select_feat_6_t {
            key = {
                eg_md.subtree_idx_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat18;
                select_feat19;
                select_feat20;
                select_feat27;
                select_feat34;
                select_feat41;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        // Compute feature actions for even numbered stages
        action compute_feat_0(CODE_TYPE code) {
            code_0 = code;
        }

        action compute_feat_1(CODE_TYPE code) {
            code_1 = code;
        }

        action compute_feat_2(CODE_TYPE code) {
            code_2 = code;
        }

        action compute_feat_3(CODE_TYPE code) {
            code_3 = code;
        }

        action compute_feat_4(CODE_TYPE code) {
            code_4 = code;
        }

        action compute_feat_5(CODE_TYPE code) {
            code_5 = code;
        }

        action compute_feat_6(CODE_TYPE code) {
            code_6 = code;
        }

        // Linear accumulation
        action sum_integer_4(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_4 = eg_md.signed_int_0_4 + value;
            eg_md.signed_int_1_4 = eg_md.signed_int_1_4 + value2;
            eg_md.signed_int_2_4 = eg_md.signed_int_2_4 + value3;
        }

        action sum_integer_5(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_5 = eg_md.signed_int_0_5 + value;
            eg_md.signed_int_1_5 = eg_md.signed_int_1_5 + value2;
            eg_md.signed_int_2_5 = eg_md.signed_int_2_5 + value3;
        }

        action sum_integer_6(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_6 = eg_md.signed_int_0_6 + value;
            eg_md.signed_int_1_6 = eg_md.signed_int_1_6 + value2;
            eg_md.signed_int_2_6 = eg_md.signed_int_2_6 + value3;
        }

        @pragma stage 13
        table compute_feat_0_t {
            key = {
                feat_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_0;
                sum_integer_4;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 13
        table compute_feat_1_t {
            key = {
                feat_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_1;
                sum_integer_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 13
        table compute_feat_2_t {
            key = {
                feat_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_2;
                sum_integer_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 13
        table compute_feat_3_t {
            key = {
                feat_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_3;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 13
        table compute_feat_4_t {
            key = {
                feat_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_4;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 13
        table compute_feat_5_t {
            key = {
                feat_5: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 13
        table compute_feat_6_t {
            key = {
                feat_6: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        action predict_0(RESULT_TYPE cls) {
            eg_md.pred_0 = cls;
        }

        action predict_1(RESULT_TYPE cls) {
            eg_md.pred_1 = cls;
        }

        action predict_2(RESULT_TYPE cls) {
            eg_md.pred_2 = cls;
        }

        action predict_3(RESULT_TYPE cls) {
            eg_md.pred_3 = cls;
        }

        action predict_4(RESULT_TYPE cls) {
            eg_md.pred_4 = cls;
        }

        action predict_5(RESULT_TYPE cls) {
            eg_md.pred_5 = cls;
        }

        action subtree_decision_4(bit<16> decision) {
            eg_md.subtree_idx_4 = decision;
        }

        action block_4_accumulate() {
            eg_md.hyperplane_0 = eg_md.hyperplane_0 + eg_md.signed_int_0_4;
            eg_md.hyperplane_1 = eg_md.hyperplane_1 + eg_md.signed_int_1_4;
            eg_md.hyperplane_2 = eg_md.hyperplane_2 + eg_md.signed_int_2_4;
        }

        @pragma stage 14
        table block_4_aggregate_t {
            key = {
                code_0: exact;
                code_1: exact;
                code_2: exact;
                code_3: exact;
                code_4: exact;
                code_5: exact;
                code_6: exact;
                eg_md.subtree_idx_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                predict_0;
                predict_1;
                predict_2;
                predict_3;
                predict_4;
                predict_5;
                subtree_decision_4;
                block_4_accumulate;
                NoAction;
            }
            const default_action = NoAction;
            size = AGGREGATE_SIZE;
        }

    apply {
        code_0 = 0;
        code_1 = 0;
        code_2 = 0;
        code_3 = 0;
        code_4 = 0;
        code_5 = 0;
        code_6 = 0;

        // select feature
        select_feat_0_t.apply();
        select_feat_1_t.apply();
        select_feat_2_t.apply();
        select_feat_3_t.apply();
        select_feat_4_t.apply();
        select_feat_5_t.apply();
        select_feat_6_t.apply();

        // feature compute
        compute_feat_0_t.apply();
        compute_feat_1_t.apply();
        compute_feat_2_t.apply();
        compute_feat_3_t.apply();
        compute_feat_4_t.apply();
        compute_feat_5_t.apply();
        compute_feat_6_t.apply();

        // aggregate
        block_4_aggregate_t.apply();
    }
}

control ML_BLOCK_5(
        inout header_t hdr,
        inout eg_metadata_t eg_md,
        in egress_intrinsic_metadata_t eg_intr_md,
        in egress_intrinsic_metadata_from_parser_t eg_intr_md_from_prsr,
        inout egress_intrinsic_metadata_for_deparser_t ig_intr_dprs_md,
        inout egress_intrinsic_metadata_for_output_port_t eg_intr_oport_md) {

        FEATURE_TYPE feat_0;
        FEATURE_TYPE feat_1;
        FEATURE_TYPE feat_2;
        FEATURE_TYPE feat_3;
        FEATURE_TYPE feat_4;
        FEATURE_TYPE feat_5;
        FEATURE_TYPE feat_6;

        CODE_TYPE code_0;
        CODE_TYPE code_1;
        CODE_TYPE code_2;
        CODE_TYPE code_3;
        CODE_TYPE code_4;
        CODE_TYPE code_5;
        CODE_TYPE code_6;

        action select_feat0() {
            feat_0 = hdr.ml_x.feat_0;
        }

        action select_feat1() {
            feat_0 = hdr.ml_x.feat_1;
        }

        action select_feat2() {
            feat_0 = hdr.ml_x.feat_2;
        }

        action select_feat3() {
            feat_1 = hdr.ml_x.feat_3;
        }

        action select_feat4() {
            feat_1 = hdr.ml_x.feat_4;
        }

        action select_feat5() {
            feat_1 = hdr.ml_x.feat_5;
        }

        action select_feat6() {
            feat_2 = hdr.ml_x.feat_6;
        }

        action select_feat7() {
            feat_2 = hdr.ml_x.feat_7;
        }

        action select_feat8() {
            feat_2 = hdr.ml_x.feat_8;
        }

        action select_feat9() {
            feat_3 = hdr.ml_x.feat_9;
        }

        action select_feat10() {
            feat_3 = hdr.ml_x.feat_10;
        }

        action select_feat11() {
            feat_3 = hdr.ml_x.feat_11;
        }

        action select_feat12() {
            feat_4 = hdr.ml_x.feat_12;
        }

        action select_feat13() {
            feat_4 = hdr.ml_x.feat_13;
        }

        action select_feat14() {
            feat_4 = hdr.ml_x.feat_14;
        }

        action select_feat15() {
            feat_5 = hdr.ml_x.feat_15;
        }

        action select_feat16() {
            feat_5 = hdr.ml_x.feat_16;
        }

        action select_feat17() {
            feat_5 = hdr.ml_x.feat_17;
        }

        action select_feat18() {
            feat_6 = hdr.ml_x.feat_18;
        }

        action select_feat19() {
            feat_6 = hdr.ml_x.feat_19;
        }

        action select_feat20() {
            feat_6 = hdr.ml_x.feat_20;
        }

        action select_feat21() {
            feat_0 = hdr.ml_x.feat_21;
        }

        action select_feat22() {
            feat_1 = hdr.ml_x.feat_22;
        }

        action select_feat23() {
            feat_2 = hdr.ml_x.feat_23;
        }

        action select_feat24() {
            feat_3 = hdr.ml_x.feat_24;
        }

        action select_feat25() {
            feat_4 = hdr.ml_x.feat_25;
        }

        action select_feat26() {
            feat_5 = hdr.ml_x.feat_26;
        }

        action select_feat27() {
            feat_6 = hdr.ml_x.feat_27;
        }

        action select_feat28() {
            feat_0 = hdr.ml_x.feat_28;
        }

        action select_feat29() {
            feat_1 = hdr.ml_x.feat_29;
        }

        action select_feat30() {
            feat_2 = hdr.ml_x.feat_30;
        }

        action select_feat31() {
            feat_3 = hdr.ml_x.feat_31;
        }

        action select_feat32() {
            feat_4 = hdr.ml_x.feat_32;
        }

        action select_feat33() {
            feat_5 = hdr.ml_x.feat_33;
        }

        action select_feat34() {
            feat_6 = hdr.ml_x.feat_34;
        }

        action select_feat35() {
            feat_0 = hdr.ml_x.feat_35;
        }

        action select_feat36() {
            feat_1 = hdr.ml_x.feat_36;
        }

        action select_feat37() {
            feat_2 = hdr.ml_x.feat_37;
        }

        action select_feat38() {
            feat_3 = hdr.ml_x.feat_38;
        }

        action select_feat39() {
            feat_4 = hdr.ml_x.feat_39;
        }

        action select_feat40() {
            feat_5 = hdr.ml_x.feat_40;
        }

        action select_feat41() {
            feat_6 = hdr.ml_x.feat_41;
        }

        @pragma stage 15
        table select_feat_0_t {
            key = {
                eg_md.subtree_idx_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat0;
                select_feat1;
                select_feat2;
                select_feat21;
                select_feat28;
                select_feat35;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 15
        table select_feat_1_t {
            key = {
                eg_md.subtree_idx_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat3;
                select_feat4;
                select_feat5;
                select_feat22;
                select_feat29;
                select_feat36;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 15
        table select_feat_2_t {
            key = {
                eg_md.subtree_idx_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat6;
                select_feat7;
                select_feat8;
                select_feat23;
                select_feat30;
                select_feat37;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 15
        table select_feat_3_t {
            key = {
                eg_md.subtree_idx_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat9;
                select_feat10;
                select_feat11;
                select_feat24;
                select_feat31;
                select_feat38;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 15
        table select_feat_4_t {
            key = {
                eg_md.subtree_idx_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat12;
                select_feat13;
                select_feat14;
                select_feat25;
                select_feat32;
                select_feat39;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 15
        table select_feat_5_t {
            key = {
                eg_md.subtree_idx_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat15;
                select_feat16;
                select_feat17;
                select_feat26;
                select_feat33;
                select_feat40;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        @pragma stage 15
        table select_feat_6_t {
            key = {
                eg_md.subtree_idx_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                select_feat18;
                select_feat19;
                select_feat20;
                select_feat27;
                select_feat34;
                select_feat41;
                NoAction;
            }
            const default_action = NoAction;
            size = SELECT_FEAT_SIZE;
        }

        // Compute feature actions for even numbered stages
        action compute_feat_0(CODE_TYPE code) {
            code_0 = code;
        }

        action compute_feat_1(CODE_TYPE code) {
            code_1 = code;
        }

        action compute_feat_2(CODE_TYPE code) {
            code_2 = code;
        }

        action compute_feat_3(CODE_TYPE code) {
            code_3 = code;
        }

        action compute_feat_4(CODE_TYPE code) {
            code_4 = code;
        }

        action compute_feat_5(CODE_TYPE code) {
            code_5 = code;
        }

        action compute_feat_6(CODE_TYPE code) {
            code_6 = code;
        }

        // Linear accumulation
        action sum_integer_5(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_5 = eg_md.signed_int_0_5 + value;
            eg_md.signed_int_1_5 = eg_md.signed_int_1_5 + value2;
            eg_md.signed_int_2_5 = eg_md.signed_int_2_5 + value3;
        }

        action sum_integer_6(ACC_TYPE value, ACC_TYPE value2, ACC_TYPE value3) {
            eg_md.signed_int_0_6 = eg_md.signed_int_0_6 + value;
            eg_md.signed_int_1_6 = eg_md.signed_int_1_6 + value2;
            eg_md.signed_int_2_6 = eg_md.signed_int_2_6 + value3;
        }

        @pragma stage 16
        table compute_feat_0_t {
            key = {
                feat_0: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_0;
                sum_integer_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 16
        table compute_feat_1_t {
            key = {
                feat_1: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_1;
                sum_integer_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 16
        table compute_feat_2_t {
            key = {
                feat_2: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_2;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 16
        table compute_feat_3_t {
            key = {
                feat_3: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_3;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 16
        table compute_feat_4_t {
            key = {
                feat_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_4;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 16
        table compute_feat_5_t {
            key = {
                feat_5: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_5;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        @pragma stage 16
        table compute_feat_6_t {
            key = {
                feat_6: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                compute_feat_6;
                NoAction;
            }
            size = COMPUTE_FEAT_SIZE;
        }

        action predict_0(RESULT_TYPE cls) {
            eg_md.pred_0 = cls;
        }

        action predict_1(RESULT_TYPE cls) {
            eg_md.pred_1 = cls;
        }

        action predict_2(RESULT_TYPE cls) {
            eg_md.pred_2 = cls;
        }

        action predict_3(RESULT_TYPE cls) {
            eg_md.pred_3 = cls;
        }

        action predict_4(RESULT_TYPE cls) {
            eg_md.pred_4 = cls;
        }

        action predict_5(RESULT_TYPE cls) {
            eg_md.pred_5 = cls;
        }

        action subtree_decision_5(bit<16> decision) {
            eg_md.subtree_idx_5 = decision;
        }

        action block_5_accumulate() {
            eg_md.hyperplane_0 = eg_md.hyperplane_0 + eg_md.signed_int_0_5;
            eg_md.hyperplane_1 = eg_md.hyperplane_1 + eg_md.signed_int_1_5;
            eg_md.hyperplane_2 = eg_md.hyperplane_2 + eg_md.signed_int_2_5;
        }

        @pragma stage 17
        table block_5_aggregate_t {
            key = {
                code_0: exact;
                code_1: exact;
                code_2: exact;
                code_3: exact;
                code_4: exact;
                code_5: exact;
                code_6: exact;
                eg_md.subtree_idx_4: exact;
                hdr.ml_y.model: exact;
            }

            actions = {
                predict_0;
                predict_1;
                predict_2;
                predict_3;
                predict_4;
                predict_5;
                subtree_decision_5;
                block_5_accumulate;
                NoAction;
            }
            const default_action = NoAction;
            size = AGGREGATE_SIZE;
        }

    apply {
        code_0 = 0;
        code_1 = 0;
        code_2 = 0;
        code_3 = 0;
        code_4 = 0;
        code_5 = 0;
        code_6 = 0;

        // select feature
        select_feat_0_t.apply();
        select_feat_1_t.apply();
        select_feat_2_t.apply();
        select_feat_3_t.apply();
        select_feat_4_t.apply();
        select_feat_5_t.apply();
        select_feat_6_t.apply();

        // feature compute
        compute_feat_0_t.apply();
        compute_feat_1_t.apply();
        compute_feat_2_t.apply();
        compute_feat_3_t.apply();
        compute_feat_4_t.apply();
        compute_feat_5_t.apply();
        compute_feat_6_t.apply();

        // aggregate
        block_5_aggregate_t.apply();
    }
}
