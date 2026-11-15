set_param general.maxThreads 4
open_checkpoint [lindex $argv 0]
set f [open [lindex $argv 1] w]
set p [get_ports HMISO]
puts $f "PORT $p PIN=[get_property PACKAGE_PIN $p] IOSTANDARD=[get_property IOSTANDARD $p] DRIVE=[get_property DRIVE $p] SLEW=[get_property SLEW $p]"
report_property $p
foreach b [get_iobanks -quiet -of_objects $p] {puts $f "BANK $b";report_property $b}
close $f
exit
