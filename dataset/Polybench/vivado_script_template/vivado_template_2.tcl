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
write_checkpoint -force $outputDir/post_place.dcp
report_utilization -file $outputDir/post_place_util.rpt
report_utilization -hierarchical -file $outputDir/post_place_util_hier.rpt
report_timing_summary -file $outputDir/post_place_timing_summary.rpt
dump_statistics
route_design -directive Explore
write_checkpoint -force $outputDir/post_route.dcp
report_route_status -file $outputDir/post_route_status.rpt
report_timing_summary -file $outputDir/post_route_timing_summary.rpt
report_power -file $outputDir/post_route_power.rpt
report_drc -file $outputDir/post_imp_drc.rpt
report_utilization -file $outputDir/post_route_util.rpt
report_utilization -hierarchical -file $outputDir/post_route_util_hier.rpt
dump_statistics
close_design
close_project