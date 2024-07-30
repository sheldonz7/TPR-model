proc dump_statistics {  } {
  set util_rpt [report_utilization -return_string]
  set ram_rpt [report_ram_utilization -return_string]
  set CLBLUTs 0
  set CLBRegisters 0
  set CLBs 0
  set BRAMFIFO36 0
  set BRAMFIFO18 0
  set BRAMFIFO36_star 0
  set BRAMFIFO18_star 0
  set BRAM18 0
  set BRAMFIFO 0
  set DRAM 0
  set URAM 0
  set BIOB 0
  set DSPs 0
  set TotPower 0
  set design_slack 0
  set design_req 0
  set design_delay 0
  regexp --  {\s*LUT as Logic\s*\|\s*([^[:blank:]]+)} $util_rpt ignore CLBLUTs
  regexp --  {\s*CLB Registers\s*\|\s*([^[:blank:]]+)} $util_rpt ignore CLBRegisters
  regexp --  {\s*CLB\s*\|\s*([^[:blank:]]+)} $util_rpt ignore CLBs
  regexp --  {\s*RAMB36/FIFO36\s*\|\s*([^[:blank:]]+)} $util_rpt ignore BRAMFIFO36
  regexp --  {\s*RAMB18/FIFO18\s*\|\s*([^[:blank:]]+)} $util_rpt ignore BRAMFIFO18
  regexp --  {\s*RAMB36/FIFO\*\s*\|\s*([^[:blank:]]+)} $util_rpt ignore BRAMFIFO36_star
  regexp --  {\s*RAMB18/FIFO\*\s*\|\s*([^[:blank:]]+)} $util_rpt ignore BRAMFIFO18_star
  regexp --  {\s*RAMB18\s*\|\s*([^[:blank:]]+)} $util_rpt ignore BRAM18
  set BRAMFIFO [expr {(2 *$BRAMFIFO36) + $BRAMFIFO18 + (2*$BRAMFIFO36_star) + $BRAMFIFO18_star + $BRAM18}]
  regexp --  {\s*LUT as Memory\s*\|\s*([^[:blank:]]+)} $util_rpt ignore DRAM
  regexp --  {\s*URAM\s*\|\s*([^[:blank:]]+)} $ram_rpt ignore URAM
  regexp --  {\s*Bonded IOB\s*\|\s*([^[:blank:]]+)} $util_rpt ignore BIOB
  regexp --  {\s*DSPs\s*\|\s*([^[:blank:]]+)} $util_rpt ignore DSPs
  set power_rpt [report_power -return_string]
  regexp --  {\s*Total On-Chip Power \(W\)\s*\|\s*([^[:blank:]]+)} $power_rpt ignore TotPower
  set Timing_Paths [get_timing_paths -max_paths 1 -nworst 1 -setup]
  if { [expr {$Timing_Paths == ""}] } {
    set design_slack 0
    set design_req 0
  } else {
    set design_slack [get_property SLACK $Timing_Paths]
    set design_req [get_property REQUIREMENT  $Timing_Paths]
  }
  if { [expr {$design_slack == ""}] } {
    set design_slack 0
  }
  if { [expr {$design_req == ""}] } {
    set design_req 0
  }
  set design_delay [expr {$design_req - $design_slack}]
  file delete -force HLS_output/Synthesis/vivado_flow/gesummv_report.xml 
  set ofile_report [open HLS_output/Synthesis/vivado_flow/gesummv_report.xml w]
  puts $ofile_report "<?xml version=\"1.0\"?>"
  puts $ofile_report "<document>"
  puts $ofile_report "  <application>"
  puts $ofile_report "    <section stringID=\"XILINX_SYNTHESIS_SUMMARY\">"
  puts $ofile_report "      <item stringID=\"XILINX_SLICE\" value=\"$CLBs\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_SLICE_REGISTERS\" value=\"$CLBRegisters\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_SLICE_LUTS\" value=\"$CLBLUTs\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_BLOCK_RAMFIFO\" value=\"$BRAMFIFO\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_DRAM\" value=\"$DRAM\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_URAM\" value=\"$URAM\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_IOPIN\" value=\"$BIOB\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_DSPS\" value=\"$DSPs\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_POWER\" value=\"$TotPower\"/>"
  puts $ofile_report "      <item stringID=\"XILINX_DESIGN_DELAY\" value=\"$design_delay\"/>"
  puts $ofile_report "    </section>"
  puts $ofile_report "  </application>"
  puts $ofile_report "</document>"
  close $ofile_report
}; #END PROC
set_param general.maxThreads 1
set outputDir HLS_output/Synthesis/vivado_flow
file mkdir $outputDir
create_project gesummv -part xcu55c-fsvh2892-2L-e -force
read_verilog gesummv.v
set rfile_sdc [open HLS_output/Synthesis/vivado_flow/gesummv.sdc r]
set clk_constraint [regexp -all --  CLK_SRC [read $rfile_sdc [file size HLS_output/Synthesis/vivado_flow/gesummv.sdc]]]
if { [expr {$clk_constraint == 0}] } {
  set ofile_sdc [open HLS_output/Synthesis/vivado_flow/gesummv.sdc a]
  puts $ofile_sdc "set_property HD.CLK_SRC BUFGCTRL_X0Y0 \[get_ports clock\]"
  close $ofile_sdc
}
read_xdc HLS_output/Synthesis/vivado_flow/gesummv.sdc
synth_design -mode out_of_context -no_iobuf -top gesummv -part xcu55c-fsvh2892-2L-e
write_checkpoint -force $outputDir/post_synth.dcp
report_timing_summary -file $outputDir/post_synth_timing_summary.rpt
report_utilization -file $outputDir/post_synth_util.rpt
report_utilization -hierarchical -file $outputDir/post_synth_util_hier.rpt
dump_statistics
opt_design  -directive ExploreWithRemap
dump_statistics
report_utilization -file $outputDir/post_opt_design_util.rpt
report_utilization -hierarchical -file $outputDir/post_opt_design_util_hier.rpt
place_design -directive Explore
report_clock_utilization -file $outputDir/clock_util.rpt
# Optionally run optimization if there are timing violations after placement
if {[get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]] < [expr {0.05 * 10}]} {
  puts "Found setup timing violations => running physical optimization"
  phys_opt_design -directive AlternateFlowWithRetiming
}
write_checkpoint -force $outputDir/post_place.dcp
report_utilization -file $outputDir/post_place_util.rpt
report_utilization -hierarchical -file $outputDir/post_place_util_hier.rpt
report_timing_summary -file $outputDir/post_place_timing_summary.rpt
dump_statistics
route_design -directive Explore
# Optionally run optimization if there are timing violations after routing
if {[get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]] < 0.0} {
  puts "Found setup timing violations => running physical optimization"
  place_design -post_place_opt
  phys_opt_design
  route_design -directive Explore
}
write_checkpoint -force $outputDir/post_route.dcp
report_route_status -file $outputDir/post_route_status.rpt
report_timing_summary -file $outputDir/post_route_timing_summary.rpt
report_power -file $outputDir/post_route_power.rpt
report_drc -file $outputDir/post_imp_drc.rpt
report_utilization -file $outputDir/post_route_util.rpt
report_utilization -hierarchical -file $outputDir/post_route_util_hier.rpt
report_ram_utilization -file $outputDir/post_route_ram_util.rpt
dump_statistics
close_design
close_project

