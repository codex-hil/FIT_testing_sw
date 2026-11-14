#!/usr/bin/env python3
from pathlib import Path
import argparse,shutil,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();shutil.copytree(a.baseline,a.out)
f=a.out/'pm12_ipbus_adc.v';s=f.read_text();old=int(json.loads((a.out/'spi-state-build.json').read_text())['build_id'],16);assert s.count(f"32'd{old}")==1
s=s.replace('reg [31:0] top_hdmi_rdata;', '''reg [31:0] top_hdmi_rdata;
reg[1:0]spi_ab_mode=0;
// Retained across SYS resets; only a new FPGA configuration initializes it.
always @(posedge sys_clk)if(!sys_rst && top_hdmi_commit && top_hdmi_selected && top_hdmi_write && !top_hdmi_error && top_hdmi_address==10'd773)spi_ab_mode<=top_hdmi_wdata[1:0];''')
s=s.replace("top_hdmi_address <= 10'd772","top_hdmi_address <= 10'd773")
before="assign top_hdmi_error = ($signed({1'd0, top_hdmi_write}) & ($signed({1'd0, (top_hdmi_address != 10'd769)}) | (($signed({1'd0, top_hdmi_wdata}) & 9'sd320) != $signed({1'd0, 1'd0}))));";assert before in s;s=s.replace(before,"assign top_hdmi_error = top_hdmi_write && !((top_hdmi_address==10'd769 && (top_hdmi_wdata & 32'd320)==0)||(top_hdmi_address==10'd773 && top_hdmi_wdata<=3));")
s=s.replace('case (top_hdmi_address)\n',"case (top_hdmi_address)\n10'd773:top_hdmi_rdata<={16'h5352,14'd0,spi_ab_mode};\n",1)
s=s.replace('top_hdmi_command <= top_hdmi_wdata;',"if(top_hdmi_address==10'd769)top_hdmi_command <= top_hdmi_wdata;")
s=s.replace('hdmi_slave hdmi_slave(','ab_slave hdmi_slave(\n.mode(spi_ab_mode),')
s=s.replace('.fixed_rst(s7mmcm0_reset7)', '.mode(spi_ab_mode),.fixed_rst(s7mmcm0_reset7)')
s=s.replace("32'h00030002","32'h00030003")
f2=a.out/'spi_observer.v';o=f2.read_text().replace('input fixed_rst,','input[1:0]mode,input fixed_rst,').replace('reg[10:0]pins1','reg[12:0]pins1').replace('reg[61:0]previous','reg[63:0]previous').replace("5'b0,pins2","3'b0,pins2").replace('wire[61:0]observed','wire[63:0]observed').replace('pins1<={gt_lock,','pins1<={mode,gt_lock,');f2.write_text(o)
shutil.copy2(Path(__file__).with_name('ab_slave.v'),a.out/'ab_slave.v')
id=int.from_bytes(hashlib.sha256(s.encode()+o.encode()+(a.out/'ab_slave.v').read_bytes()).digest()[:4],'big');s=s.replace(f"32'd{old}",f"32'd{id}");f.write_text(s)
f=a.out/'build.tcl';f.write_text(f.read_text().replace('read_verilog $here/hdmi_slave.v','read_verilog $here/hdmi_slave.v\nread_verilog $here/ab_slave.v'))
(a.out/'ab-build.json').write_text(json.dumps(dict(build_id=f'{id:08x}',baseline=f'{old:08x}',mode_csr=0x305,mode_bits={'hold':0,'clamp_miso':1},observer_format=0x30003,sources={str(p.relative_to(a.out)):hashlib.sha256(p.read_bytes()).hexdigest()for p in a.out.rglob('*')if p.is_file()}),indent=2)+'\n');print(f'{id:08x}')
