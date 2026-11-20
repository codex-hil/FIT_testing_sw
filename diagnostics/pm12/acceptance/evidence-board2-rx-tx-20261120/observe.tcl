source /home/codex-hil/fit-testing-publish/diagnostics/pm12/adc/tools/common.tcl
pm12_open
scan_ir_hw_jtag 102 -tdi 3fffffffffffffffffffffffc2
foreach label {q0 q1 q2 q3} {
 for {set sample 0} {$sample<3} {incr sample} {
  set report [scan_dr_hw_jtag 524 -tdi 0]
  set f [open [file join $::env(PM12_PAYLOAD) "$label-$sample.txt"] w]
  puts $f $report
  close $f
  after 25
 }
 set f [open [file join $::env(PM12_PAYLOAD) "$label.ready"] w]; puts $f ready; close $f
 if {$label ne "q3"} {
  set deadline [expr {[clock milliseconds]+90000}]
  while {![file exists [file join $::env(PM12_PAYLOAD) "$label.done"]]} {
   if {[clock milliseconds]>$deadline} {error "Host stage timeout"}
   after 20
  }
 }
}
pm12_close
exit
