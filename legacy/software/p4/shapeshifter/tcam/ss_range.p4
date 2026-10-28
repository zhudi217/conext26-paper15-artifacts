#include <core.p4>
#include <t2na.p4>
#include "defines.p4"
#include "header.p4"
#include "ingress.p4"
#include "egress.p4"

Pipeline(
    SwitchIngressParser(),
    SwitchIngress(),
    SwitchIngressDeparser(),
    SwitchEgressParser(),
    SwitchEgress(),
    SwitchEgressDeparser()
) pipe;

Switch(pipe) main;