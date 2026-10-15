# Component resource check only: no target pin placement or timing qualification.
read_verilog generated/tdc_buffers.v
synth_design -top tdc_buffers -part xc7k160tffg676-3 -mode out_of_context
report_utilization -file generated/utilization.txt
write_checkpoint -force generated/tdc_buffers.dcp
exit
