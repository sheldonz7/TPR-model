# Bambu tips
## Some devices that might be of interest
xcku060-3ffva1156-VVD
xc7z020-1clg484-VVD

## Useful Bambu parameters

### memory
--channels-number=8
--channels-number=16

--rom-duplication

### pipeline
-p=atax
--pipelining


### clock constraint
--clock-period=10
--clock-period=5

### binding algorithms
--module-binding=BIPARTITE_MATCHING
--module-binding=WEIGHTED_COLORING
--module-binding=TTT_FAST
--module-binding=TTT_FAST2
--module-binding=TTT_FULL
--module-binding=TTT_FULL2

### EDA tool
--xilinx-root=/res/EDATool/Xilinx/Xilinx2021.2


### simulation and testbench
--simulator=XSIM
--generate-tb=../test_atax.xml --simulate --simulator=VERILATOR
--generate-vcd

### interface
--generate-interface=INFER      # infer interface from the source code as well as HLS interface pragmas
--memory-mapped-top             # AXI4 memory mapped interface
--reset-level=high              # reset signal is active high to follow Vitis HLS standard


## Sample Bambu script used in this codebase

bambu ../atax.c --top-fname=atax --print-dot --compiler=I386_CLANG13 -O2 --debug 4 --verbosity 4 > stdout.txt 2> stderr.txt --device=xcku060-3ffva1156-VVD --disable-function-proxy 