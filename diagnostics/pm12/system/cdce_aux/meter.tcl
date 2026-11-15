source /home/codex-hil/fit-testing-publish/diagnostics/pm12/adc/tools/common.tcl
set dir $::env(PM12_PAYLOAD)
pm12_open
scan_ir_hw_jtag 102 -tdi 3fffffffffffffffffffffffc2
set ready [open [file join $dir ready] w];puts $ready 1;close $ready
set deadline [expr {[clock seconds]+180}]
while {![file exists [file join $dir stop]] && [clock seconds]<$deadline} {
 set req [file join $dir request]
 if {[file exists $req]} {
  set f [open $req r];set seq [string trim [read $f]];close $f;file delete $req
  if {![string is integer -strict $seq]} {error "Bad request"}
  set before [clock microseconds]
  set report [scan_dr_hw_jtag 524 -tdi 0]
  set after [clock microseconds]
  if {[expr {("0x$report") & 0xffffffff}] != 0x504d5a04} {error "Wrong image tag"}
  set tmp [file join $dir response.tmp];set f [open $tmp w];puts $f "$seq $report $before $after";close $f
  file rename -force $tmp [file join $dir response]
 }
 after 2
}
pm12_close
puts METER_PASS
exit
