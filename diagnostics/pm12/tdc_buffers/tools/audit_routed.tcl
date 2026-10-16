open_checkpoint ../board/build/pm12_ipbus_adc.dcp
set count [get_cells -hier -filter {NAME =~ TDC*_CH*/TDC_bitcount_reg* && IS_SEQUENTIAL == 1}]
if {[llength $count] != 36} {error "Expected 36 serial bit-counter flip-flops"}
foreach cell $count {
 if {[get_property INIT $cell] ne "1'b0"} {error "Serial startup state is not zero: $cell"}
}
puts "TDC_SERIAL_COUNTER_INIT_PASS [llength $count]"
for {set n 1} {$n <= 3} {incr n} {
 foreach pin {CLKOUT0 CLKOUT1 CLKOUT2} {
  set clock [get_clocks -of_objects [get_pins tdc_mmcm$n/$pin]]
  puts "TDC_CLOCK $n $pin [get_property PERIOD $clock] [get_property WAVEFORM $clock]"
 }
}
foreach name {I2C_SDA I2C_SCL I2C_RESET_N} {
 if {[get_property DIRECTION [get_ports $name]] ne "IN"} {error "I2C pin drives unexpectedly"}
}
foreach port [get_ports {MCLK?_N TDCCLK?_N IN*_N RD*_N RS*_N}] {
 if {[get_property PACKAGE_PIN $port] eq ""} {error "Unplaced differential input $port"}
 puts "DIFFERENTIAL_MATE $port [get_property PACKAGE_PIN $port]"
}
puts FPGA_INPUT_OWNERSHIP_PASS
exit
