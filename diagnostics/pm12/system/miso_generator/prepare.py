#!/usr/bin/env python3
from pathlib import Path
import shutil,hashlib,json,argparse
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('out',type=Path);a=p.parse_args();shutil.copytree(a.baseline,a.out)
p=a.out/'pm12_ipbus_adc.v';s=p.read_text();old=int('30096dcc',16);assert s.count(f"32'd{old}")==1
s=s.replace('reg[1:0]spi_ab_mode=0;', '''reg[1:0]spi_ab_mode=0;
reg[1:0]miso_gen_mode=0;
wire miso_gen_active,miso_gen_data;
wire miso_pin_data=miso_gen_active?miso_gen_data:top_hdmi_mi;
always @(posedge sys_clk)if(!sys_rst && top_hdmi_commit && top_hdmi_selected && top_hdmi_write && !top_hdmi_error && top_hdmi_address==10'd774)miso_gen_mode<=top_hdmi_wdata[1:0];
miso_generator misogen(.clk(spiwatch_clk),.mode(miso_gen_mode),.active(miso_gen_active),.data(miso_gen_data));''')
s=s.replace("top_hdmi_address <= 10'd773","top_hdmi_address <= 10'd774")
s=s.replace("(top_hdmi_address==10'd773 && top_hdmi_wdata<=3)","((top_hdmi_address==10'd773 || top_hdmi_address==10'd774) && top_hdmi_wdata<=3)")
s=s.replace("10'd773:top_hdmi_rdata", "10'd774:top_hdmi_rdata<={16'h474e,14'd0,miso_gen_mode};\n10'd773:top_hdmi_rdata")
s=s.replace('.I(top_hdmi_mi),\n\t.T((~HSEL)),','.I(miso_pin_data),\n\t.T(miso_gen_active ? 1\'b0 : (~HSEL)),')
s=s.replace('.miso_data(top_hdmi_mi)', '.miso_data(miso_pin_data)')
assert '.I(miso_pin_data)'in s
v=Path(__file__).with_name('miso_generator.v').read_bytes();bid=int.from_bytes(hashlib.sha256(s.encode()+v).digest()[:4],'big');s=s.replace(f"32'd{old}",f"32'd{bid}");p.write_text(s)
shutil.copy2(Path(__file__).with_name('miso_generator.v'),a.out/'miso_generator.v')
p=a.out/'build.tcl';s=p.read_text().replace('read_verilog $here/ab_slave.v','read_verilog $here/ab_slave.v\nread_verilog $here/miso_generator.v');s=s.replace('opt_design','set_false_path -to [get_cells -hier -filter {NAME =~ *misogen/mode1_reg*}]\nopt_design',1);p.write_text(s)
(a.out/'generator-build.json').write_text(json.dumps(dict(build_id=f'{bid:08x}',csr=0x306,modes={'normal':0,'low':1,'high':2,'square':3},frequency_hz=40078700/40078,half_period_ticks=20039),indent=2)+'\n');print(f'{bid:08x}')
