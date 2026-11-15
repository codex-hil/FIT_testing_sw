set_param general.maxThreads 4
open_checkpoint [lindex $argv 0]
set p [get_ports HMISO]
if {[get_property IOSTANDARD $p] ne "LVCMOS33" || [get_property DRIVE $p]!=12 || [get_property SLEW $p] ne "SLOW"} {error "Unexpected baseline port"}
# Change exactly one output electrical setting. Do not rerun synthesis/place/route.
set_property DRIVE 4 $p
if {[get_property DRIVE $p]!=4 || [get_property SLEW $p] ne "SLOW"} {error "Drive change failed"}
set f [open port-4ma.txt w]
puts $f "PORT $p PIN=[get_property PACKAGE_PIN $p] IOSTANDARD=[get_property IOSTANDARD $p] DRIVE=[get_property DRIVE $p] SLEW=[get_property SLEW $p]"
close $f
report_drc -file drc-4ma.txt
report_timing_summary -file timing-4ma.txt
foreach corner {max min} {
 if {[llength [get_timing_paths -quiet -delay_type $corner -slack_lesser_than 0 -max_paths 1]]} {error "Timing failed $corner"}
}
write_checkpoint -force drive4.dcp
write_bitstream -force drive4.bit
exit
