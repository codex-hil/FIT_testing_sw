# Read-only USER1 report. No USER2 commands, EXTEST, programming or logic reset.
lassign $argv cable server directory
set argv [list $cable $server {} 0]
source [file join [file dirname [info script]] .. adc tools common.tcl]
pm12_open
scan_ir_hw_jtag 102 -tdi 3fffffffffffffffffffffffc2
proc emit_report {directory label} {
 set report [scan_dr_hw_jtag 524 -tdi 0]
 set f [open [file join $directory "$label.tmp"] w]
 puts $f $report
 close $f
 file rename [file join $directory "$label.tmp"] [file join $directory "$label.txt"]
}
emit_report $directory before
set deadline [expr {[clock milliseconds]+30000}]
while {![file exists [file join $directory network-done]]} {
 if {[clock milliseconds]>$deadline} {error "Host identity challenge did not complete"}
 after 20
}
emit_report $directory after
pm12_close
exit
