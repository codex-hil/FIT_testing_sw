#!/usr/bin/env python3
"""Extend qualified generator image with SPI output-enable-only controls."""
import argparse,shutil,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('out',type=Path);a=p.parse_args();shutil.copytree(a.baseline,a.out)
f=a.out/'pm12_ipbus_adc.v';s=f.read_text();old=int('399ead20',16);assert s.count(f"32'd{old}")==1
s=s.replace('reg[1:0]miso_gen_mode=0;', 'reg[2:0]miso_gen_mode=0;')
s=s.replace('wire miso_pin_data=miso_gen_active?miso_gen_data:top_hdmi_mi;', '''wire miso_oe=(miso_gen_mode>=4 || miso_gen_active || HSEL);
wire miso_pin_data=(miso_gen_mode==5)?(HSEL?top_hdmi_mi:1'b0):(miso_gen_mode==4)?top_hdmi_mi:miso_gen_active?miso_gen_data:top_hdmi_mi;''')
s=s.replace("miso_gen_mode<=top_hdmi_wdata[1:0]", "miso_gen_mode<=top_hdmi_wdata[2:0]")
s=s.replace('.mode(miso_gen_mode)', ".mode(miso_gen_mode<4?miso_gen_mode[1:0]:2'b0)")
s=s.replace("((top_hdmi_address==10'd773 || top_hdmi_address==10'd774) && top_hdmi_wdata<=3)","(top_hdmi_address==10'd773 && top_hdmi_wdata<=3)||(top_hdmi_address==10'd774 && top_hdmi_wdata<=5)")
s=s.replace("{16'h474e,14'd0,miso_gen_mode}","{16'h474e,13'd0,miso_gen_mode}")
s=s.replace(".T(miso_gen_active ? 1'b0 : (~HSEL))",'.T(~miso_oe)')
s=s.replace('.miso_data(miso_pin_data)', '.miso_data(miso_pin_data),.miso_oe(miso_oe)')
s=s.replace("32'h00030003","32'h00030004")
f2=a.out/'spi_observer.v';o=f2.read_text().replace('hmosi,miso_data,','hmosi,miso_data,miso_oe,').replace('reg[12:0]pins1','reg[13:0]pins1').replace('reg[63:0]previous','reg[64:0]previous').replace("3'b0,pins2","2'b0,pins2").replace('wire[63:0]observed','wire[64:0]observed').replace('pins1<={mode,','pins1<={miso_oe,mode,');f2.write_text(o)
bid=int.from_bytes(hashlib.sha256(s.encode()+o.encode()).digest()[:4],'big');s=s.replace(f"32'd{old}",f"32'd{bid}");f.write_text(s)
(a.out/'oe-build.json').write_text(json.dumps(dict(build_id=f'{bid:08x}',csr=0x306,observer_format=0x30004,modes={'normal_hsel_oe':0,'always_oe_same_data':4,'always_oe_idle_zero':5},oe_observer_bit=13),indent=2)+'\n');print(f'{bid:08x}')
