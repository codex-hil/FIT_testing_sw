#!/usr/bin/env python3
from pathlib import Path
import argparse,shutil,json,hashlib
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('out',type=Path);a=p.parse_args();shutil.copytree(a.baseline,a.out)
f=a.out/'pm12_ipbus_adc.v';s=f.read_text();old=int('71ac56fb',16);assert s.count(f"32'd{old}")==1
s=s.replace('reg spiwatch_arm=0;', '''reg spiwatch_arm=0;
reg clkr_arm=0;wire[31:0]clkr_csr,clkr_data;
always @(posedge sys_clk)if(top_registers_is_ongoing0 && top_registers_wr && top_registers_adr==32'h390 && top_registers_wd==32'h41524d31)clkr_arm<=~clkr_arm;
rx_clock_counter clkr(.ref_clk(top_pma_k7_gtx_basex_rxoutclk_rebuffer),.mclk(spiwatch_clk),.gtref(top_fixed100),.sys_clk(sys_clk),.arm(clkr_arm),
.sys_lock(top_fixed_cm_locked),.cap_lock(top_cap_cm_locked),.sys_reset(sys_rst),.gt_lock(top_pma_k7_gtx_basex_pll_lock),.rx_done(top_pma_k7_gtx_basex_gtxrxinit_done),.rx_mmcm_lock(top_pma_k7_gtx_basex_rx_mmcm_locked1),
.read_index(top_registers_adr[12:0]),.csr_index(top_registers_adr[3:0]),.csr_data(clkr_csr),.data(clkr_data));''')
needle='// synthesis translate_off\n\tdummy_d_37';assert needle in s;s=s.replace(needle,'''if ((top_registers_adr>=32'h390 && top_registers_adr<=32'h39c) || (top_registers_adr>=32'ha000 && top_registers_adr<32'hc000))begin
 top_registers_valid_address<=1'b1;top_registers_writable<=(top_registers_adr==32'h390);top_registers_bad_write<=(top_registers_wd!=32'h41524d31);
 top_registers_read_value<=(top_registers_adr<32'ha000)?clkr_csr:clkr_data;
end
'''+needle)
v=Path(__file__).with_name('rx_clock_counter.v').read_bytes();bid=int.from_bytes(hashlib.sha256(s.encode()+v).digest()[:4],'big');s=s.replace(f"32'd{old}",f"32'd{bid}");f.write_text(s);shutil.copy2(Path(__file__).with_name('rx_clock_counter.v'),a.out/'rx_clock_counter.v')
f=a.out/'build.tcl';s=f.read_text().replace('report_timing_summary -file build/timing.txt','report_timing_summary -file build/timing.txt\nreport_bus_skew -warn_on_violation -file build/counter-bus-skew.txt').replace('read_verilog $here/spi_observer.v','read_verilog $here/spi_observer.v\nread_verilog $here/rx_clock_counter.v');s=s.replace('opt_design','''set_false_path -to [get_cells -hier -filter {NAME =~ *clkr/flags1_reg* || NAME =~ *clkr/arm1_reg* || NAME =~ *clkr/status1_reg*}]
foreach {source destination} {c_m m1 c_g g1 c_s s1} {
 set src [get_cells -hier -filter "NAME =~ *clkr/$source/gray_reg*"]
 set dst [get_cells -hier -filter "NAME =~ *clkr/${destination}_reg*"]
 if {![llength $src] || ![llength $dst]} {error "Missing clock counter CDC endpoints $source $destination"}
 set_max_delay -datapath_only 8 -from $src -to $dst
 set_bus_skew 5 -from $src -to $dst
}
opt_design''',1);f.write_text(s)
(a.out/'rx-counter-build.json').write_text(json.dumps(dict(build_id=f'{bid:08x}',baseline='71ac56fb',csr=0x390,memory=0xa000,window_ref_cycles=384,reference_nominal_hz=60118050,depth=2048,target_expected_counts=[256,640,256]),indent=2)+'\n');print(f'{bid:08x}')
