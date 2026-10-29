typedef bit<48> mac_addr_t;
typedef bit<32> ipv4_addr_t;
typedef bit<16> ether_type_t;
const ether_type_t ETHERTYPE_IPV4 = 16w0x0800;
const ether_type_t ETHERTYPE_VLAN = 16w0x0810;

typedef bit<8> ip_protocol_t;
const ip_protocol_t IP_PROTOCOLS_ICMP = 1;
const ip_protocol_t IP_PROTOCOLS_TCP = 6;
const ip_protocol_t IP_PROTOCOLS_UDP = 17;

typedef bit<16> tcp_port_t;
const tcp_port_t ML_PORT = 12345;

typedef int<16> FEATURE_TYPE;
typedef bit<8> RESULT_TYPE;
typedef bit<8> CODE_TYPE;
typedef int<16> ACC_TYPE;

const int SELECT_FEAT_SIZE = 256;
const int COMPUTE_FEAT_SIZE = 1024;
const int AGGREGATE_SIZE = 32768;