# TAP reset, IDCODE and BYPASS only. No USER2 write, EXTEST or configuration.
lassign $argv cable server output window_ms
if {$window_ms eq ""} {set window_ms 1000}
if {$window_ms<1000 || $window_ms>30000} {error "Window outside1..30s"}
set argv [list $cable $server {} 0]
source [file join [file dirname [info script]] .. adc tools common.tcl]
pm12_open
set status [catch {
 scan_ir_hw_jtag 102 -tdi 3fffffffffffffffffffffffff
 foreach pattern {0000000000000000 ffffffffffffffff 0123456789abcdef fedcba9876543210 a5a55a5af00f0ff0} {
  puts "BYPASS $pattern [scan_dr_hw_jtag 64 -tdi $pattern]"
 }
 scan_ir_hw_jtag 102 -tdi 3fffffffffffffffffffffffc2
 puts "REPORT_BEFORE [scan_dr_hw_jtag 524 -tdi 0]"
 puts "REPORT_TIME_BEFORE [clock milliseconds]"
 after $window_ms
 puts "REPORT_AFTER [scan_dr_hw_jtag 524 -tdi 0]"
 puts "REPORT_TIME_AFTER [clock milliseconds]"
} err opts]
pm12_close
if {$status} {return -options $opts $err}
exit
