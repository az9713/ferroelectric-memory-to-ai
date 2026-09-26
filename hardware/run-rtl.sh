#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
iverilog -g2012 -s tb -o controller-sim controller.v memory-behavior.v tb.v
vvp controller-sim > rtl-validation.log
yosys -p 'read_verilog controller.v; hierarchy -check -top controller; synth -top controller; check; stat; write_verilog -noattr controller-synth.v; write_json controller-synth.json' > synthesis.log
iverilog -g2012 -s tb -o controller-gate-sim controller-synth.v memory-behavior.v tb.v
vvp controller-gate-sim > gate-validation.log
cat rtl-validation.log gate-validation.log
