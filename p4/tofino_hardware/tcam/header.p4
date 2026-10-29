header ethernet_h {
    mac_addr_t dst_addr;
    mac_addr_t src_addr;
    bit<16> ether_type;
}

header ipv4_h {
    bit<4> version;
    bit<4> ihl;
    bit<8> diffserv;
    bit<16> total_len;
    bit<16> identification;
    bit<3> flags;
    bit<13> frag_offset;
    bit<8> ttl;
    bit<8> protocol;
    bit<16> hdr_checksum;
    ipv4_addr_t src_addr;
    ipv4_addr_t dst_addr;
}

header tcp_h {
    bit<16> src_port;
    bit<16> dst_port;

    bit<32> seq_no;
    bit<32> ack_no;
    bit<4> data_offset;
    bit<4> res;
    bit<8> flags;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgent_ptr;
}

header udp_h {
    bit<16> src_port;
    bit<16> dst_port;
    bit<16> udp_total_len;
    bit<16> checksum;
}

header ml_feat_h {
    FEATURE_TYPE feat_0;
    FEATURE_TYPE feat_1;
    FEATURE_TYPE feat_2;
    FEATURE_TYPE feat_3;
    FEATURE_TYPE feat_4;
    FEATURE_TYPE feat_5;
    FEATURE_TYPE feat_6;
    FEATURE_TYPE feat_7;
    FEATURE_TYPE feat_8;
    FEATURE_TYPE feat_9;
    FEATURE_TYPE feat_10;
    FEATURE_TYPE feat_11;
    FEATURE_TYPE feat_12;
    FEATURE_TYPE feat_13;
    FEATURE_TYPE feat_14;
    FEATURE_TYPE feat_15;
    FEATURE_TYPE feat_16;
    FEATURE_TYPE feat_17;
    FEATURE_TYPE feat_18;
    FEATURE_TYPE feat_19;
    FEATURE_TYPE feat_20;   // feat6

    FEATURE_TYPE feat_21;   // feat0
    FEATURE_TYPE feat_22;   // feat1
    FEATURE_TYPE feat_23;   // feat2
    FEATURE_TYPE feat_24;   // feat3
    FEATURE_TYPE feat_25;   // feat4
    FEATURE_TYPE feat_26;    // feat5
    FEATURE_TYPE feat_27;    // feat6

    FEATURE_TYPE feat_28;   // feat0
    FEATURE_TYPE feat_29;   // feat1
    FEATURE_TYPE feat_30;   // feat2
    FEATURE_TYPE feat_31;   // feat3
    FEATURE_TYPE feat_32;   // feat4
    FEATURE_TYPE feat_33;   // feat5
    FEATURE_TYPE feat_34;   // feat6

    FEATURE_TYPE feat_35;   // feat0
    FEATURE_TYPE feat_36;   // feat1
    FEATURE_TYPE feat_37;   // feat2
    FEATURE_TYPE feat_38;   // feat3
    FEATURE_TYPE feat_39;   // feat4
    FEATURE_TYPE feat_40;   // feat5
    FEATURE_TYPE feat_41;   // feat6
}

header ml_result_h {
    RESULT_TYPE result;
    RESULT_TYPE result_2;
    bit<4> model;
    bit<4> version;
}

struct header_t {
    ethernet_h ethernet;
    ipv4_h ipv4;
    tcp_h tcp;
    udp_h udp;
    ml_feat_h ml_x;
    ml_result_h ml_y;
}

struct ig_metadata_t {

}

struct eg_metadata_t {
    // ------- Linear accumulations -------
    ACC_TYPE signed_int_0_1;
    ACC_TYPE signed_int_1_1;
    ACC_TYPE signed_int_2_1;
    ACC_TYPE signed_int_0_2;
    ACC_TYPE signed_int_1_2;
    ACC_TYPE signed_int_2_2;
    ACC_TYPE signed_int_0_3;
    ACC_TYPE signed_int_1_3;
    ACC_TYPE signed_int_2_3;
    ACC_TYPE signed_int_0_4;
    ACC_TYPE signed_int_1_4;
    ACC_TYPE signed_int_2_4;
    ACC_TYPE signed_int_0_5;
    ACC_TYPE signed_int_1_5;
    ACC_TYPE signed_int_2_5;
    ACC_TYPE signed_int_0_6;
    ACC_TYPE signed_int_1_6;
    ACC_TYPE signed_int_2_6;

    // hyperplane results
    ACC_TYPE hyperplane_0;
    ACC_TYPE hyperplane_1;
    ACC_TYPE hyperplane_2;

    // Decisions at each layer
    bit<16> subtree_idx_0;
    bit<16> subtree_idx_1;
    bit<16> subtree_idx_2;
    bit<16> subtree_idx_3;
    bit<16> subtree_idx_4;
    bit<16> subtree_idx_5;

    // Predictions
    RESULT_TYPE pred_0;
    RESULT_TYPE pred_1;
    RESULT_TYPE pred_2;
    RESULT_TYPE pred_3;
    RESULT_TYPE pred_4;
    RESULT_TYPE pred_5;
}