#!/usr/bin/env python3
"""Default quiet MISO during write frames, reversible comparison control."""
import argparse,shutil,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('baseline',type=Path);p.add_argument('out',type=Path);a=p.parse_args();shutil.copytree(a.baseline,a.out)
f=a.out/'pm12_ipbus_adc.v';s=f.read_text();old=int('1cf28c8f',16);assert s.count(f"32'd{old}")==1
s=s.replace('reg[1:0]spi_ab_mode=0;','reg[2:0]spi_ab_mode=4;')
s=s.replace('spi_ab_mode<=top_hdmi_wdata[1:0]','spi_ab_mode<=top_hdmi_wdata[2:0]')
s=s.replace("top_hdmi_address==10'd773 && top_hdmi_wdata<=3","top_hdmi_address==10'd773 && top_hdmi_wdata<=7")
s=s.replace("{16'h5352,14'd0,spi_ab_mode}","{16'h5352,13'd0,spi_ab_mode}")
s=s.replace('.mode(spi_ab_mode),.fixed_rst', '.mode(spi_ab_mode[1:0]),.write_quiet(spi_ab_mode[2]),.fixed_rst')
s=s.replace("32'h00030004","32'h00030005")
f=a.out/'ab_slave.v';v=f.read_text().replace('input[1:0]mode','input[2:0]mode').replace("assign miso=mode[1]?1'b0:raw_miso;", "// bit2 defaults enabled in top: do not echo incoming write/header data.\n assign miso=mode[1]?1'b0:(mode[2]&&!debug_state[5])?1'b0:raw_miso;");f.write_text(v)
f=a.out/'spi_observer.v';o=f.read_text().replace('miso_data,miso_oe,','miso_data,miso_oe,write_quiet,').replace('reg[13:0]pins1','reg[14:0]pins1').replace('reg[64:0]previous','reg[65:0]previous').replace("2'b0,pins2","1'b0,pins2").replace('wire[64:0]observed','wire[65:0]observed').replace('pins1<={miso_oe,','pins1<={write_quiet,miso_oe,');f.write_text(o)
bid=int.from_bytes(hashlib.sha256(s.encode()+v.encode()+o.encode()).digest()[:4],'big');s=s.replace(f"32'd{old}",f"32'd{bid}");(a.out/'pm12_ipbus_adc.v').write_text(s)
(a.out/'write-quiet-build.json').write_text(json.dumps(dict(build_id=f'{bid:08x}',csr=0x305,default=4,write_quiet_bit=2,observer_format=0x30005,write_quiet_observer_bit=14,baseline='1cf28c8f'),indent=2)+'\n');print(f'{bid:08x}')
