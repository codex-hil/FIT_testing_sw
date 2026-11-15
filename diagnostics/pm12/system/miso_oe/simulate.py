#!/usr/bin/env python3
"""Simulate actual generated routing expressions with the original SPI parser."""
from pathlib import Path
import argparse,subprocess
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(exist_ok=True)
s=(a.source/'pm12_ipbus_adc.v').read_text();fragment=s[s.index('wire miso_oe='):s.index('always @(posedge sys_clk)if(!sys_rst && top_hdmi_commit',s.index('wire miso_oe='))]
tb='''`timescale 1ns/1ps
module tb;
reg HSCK=0,HSEL=0,HMOSI=0;reg[2:0]miso_gen_mode=0;
wire top_hdmi_mi;wire miso_gen_active=0,miso_gen_data=0;
'''+fragment+'''
wire HMISO=miso_oe?miso_pin_data:1'bz;
wire[15:0]scratch,writes,shift;wire[5:0]state;wire[7:0]address;
ab_slave parser(.clk(HSCK),.sel(HSEL),.mosi(HMOSI),.locked(1'b1),.mode(2'b0),.miso(top_hdmi_mi),.scratch_out(scratch),.writes_out(writes),.debug_state(state),.debug_address(address),.debug_shift(shift));
reg[15:0]rx;integer m;
task frame(input[7:0]addr,input[15:0]expected);integer i;reg[31:0]packet;begin
packet=32'h80000000|({24'd0,addr}<<22);rx=0;HSEL=1;#10;
for(i=31;i>=0;i=i-1)begin HMOSI=packet[i];#10;HSCK=1;#10;
if(!miso_oe||HMISO===1'bz)$fatal(1,"selected output disabled");
if(i<16)rx={rx[14:0],HMISO};HSCK=0;#10;end
HSEL=0;HMOSI=0;#10;if(rx!==expected)$fatal(1,"SPI reply changed");end endtask
initial begin
for(m=0;m<3;m=m+1)begin
miso_gen_mode=m==0?0:m==1?4:5;#10;
frame(0,16'h4844);frame(1,16'h4d49);frame(2,16'h0001);
if(m==0)begin if(HMISO!==1'bz||miso_oe)$fatal(1,"normal idle is not Hi-Z");end
else if(!miso_oe||HMISO===1'bz)$fatal(1,"forced OE lost at idle");
end
force parser.core.data=16'h8000;miso_gen_mode=4;#10;if(HMISO!==1)$fatal(1,"mode4 modified idle data");
miso_gen_mode=5;#10;if(HMISO!==0)$fatal(1,"mode5 did not force idle zero");release parser.core.data;
miso_gen_mode=0;#10;frame(0,16'h4844);if(HMISO!==1'bz)$fatal(1,"return normal");
$display("PASS actual routing: identical selected SPI replies, mode0 idle Hi-Z, mode4 unchanged data/continuous OE, mode5 idle0, normal return");$finish;
end
endmodule
'''
(a.out/'tb.v').write_text(tb)
subprocess.run(['/home/codex-hil/wr-sts/.tools/bin/iverilog','-g2012','-s','tb','-o',str(a.out/'tb'),str(a.out/'tb.v'),str(a.source/'ab_slave.v'),str(a.source/'hdmi_slave.v')],check=True)
subprocess.run(['/home/codex-hil/wr-sts/.tools/bin/vvp',str(a.out/'tb')],check=True)
