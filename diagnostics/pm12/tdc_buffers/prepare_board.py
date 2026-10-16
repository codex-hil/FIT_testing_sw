"""Prepare isolated ADC+TDC build with immutable original HDL and pin mapping."""
from pathlib import Path
import shutil,subprocess,re,json,hashlib
from instrument_receiver import REVISION, instrument, SOURCE
root=Path(__file__).resolve().parent
repo=Path('/home/codex-hil/fit-bringup/sources/FIT_TCM_GW_FPGA')
out=root/'generated/board'
out.mkdir(parents=True,exist_ok=True)
base=root.parent/'ipbus_adc'
for f in base.iterdir():
    if f.is_file() and f.suffix in ('.py','.v','.vhd','.xdc','.tcl','.txt','.json'):
        shutil.copy2(f,out/f.name)
shutil.copytree(base/'ipbus',out/'ipbus',dirs_exist_ok=True)
manifest={}
def original(path):
    data=subprocess.check_output(['git','-C',str(repo),'show',REVISION+':'+path]);manifest[path]=hashlib.sha256(data).hexdigest();return data
(out/'TDCCHAN_instrumented.vhd').write_bytes(instrument(original(SOURCE)))
for name in ['pin_capt.vhd','autophase.vhd']:
    (out/name).write_bytes(original('firmware/FT0/PM/hdl/'+name))
for name in ['CLK600_pll','TDC_FIFO']:
    (out/(name+'-original.txt')).write_bytes(original('firmware/FT0/PM/ipcore_properties/'+name+'.txt'))
ios=original('firmware/FT0/PM/xdc/ios.xdc').decode()
names=['MCLK%d_%s'%(i,s) for i in [2,3] for s in 'PN']
names+=['TDCCLK%d_%s'%(i,s) for i in [1,2,3] for s in 'PN']
names += ['%s%s%d_%s'%(prefix,l,i,s) for prefix in ['IN','RS','RD'] for l in 'ABCD' for i in [1,2,3] for s in 'PN']
lines=[]
for name in names:
    matches=re.findall(r'^set_property PACKAGE_PIN (\w+) \[get_ports '+name+r'\]',ios,re.M)
    if not matches and name.endswith('_N'):
        lines += ['set_property IOSTANDARD LVDS [get_ports %s]'%name]
        continue  # Original XDC fixes P; Vivado infers the physical differential mate.
    if len(matches)!=1:raise ValueError((name,matches))
    lines += ['set_property PACKAGE_PIN %s [get_ports %s]'%(matches[0],name),'set_property IOSTANDARD LVDS [get_ports %s]'%name]
fit_clock=original('firmware/FT0/PM/xdc/fit.xdc').decode()
for line in fit_clock.splitlines():
    if (line.startswith('create_clock') and ('TDCCLK' in line or 'MCLK2' in line or 'MCLK3' in line)) or (line.startswith('set_input_delay') and 'TDCCLK' in line):
        lines.append(line)
(out/'tdc-pins.xdc').write_text('\n'.join(lines)+'\n')
s=(out/'generate.py').read_text();s='import sys\nsys.path.insert(0, '+repr(str(root))+')\nfrom frontend import Frontend\n'+s
s=s.replace("m=Signal();ref=Signal()", "m=Signal();ref=Signal();sys_ref=Signal()")
s=s.replace("Instance('BUFG',i_I=m,o_O=self.cd_sys.clk)", "Instance('BUFG',i_I=sys_ref,o_O=self.cd_sys.clk)")
s=s.replace('self.submodules.registers=regs=Registers(cap,trace,build_id)', 'self.submodules.tdc_frontend=tdc=Frontend(m);self.ios.update(tdc.ios);self.comb += sys_ref.eq(tdc.sys_reference)\n  self.submodules.registers=regs=Registers(cap,trace,build_id,tdc=tdc.acquisition.window)')
# Include all TDC source inputs in build identity, not just the legacy ADC files.
s=s.replace("build_id=int.from_bytes", "build_sources += ['TDCCHAN_instrumented.vhd','pin_capt.vhd','autophase.vhd','tdc-pins.xdc','tdc-ip.tcl','tdc-timing.tcl']\nextra_sources=b''.join(p.read_bytes() for p in sorted(Path("+repr(str(root))+").glob('*.py')))\nbuild_id=int.from_bytes")
s=s.replace("hashlib.sha256(b''.join", "hashlib.sha256(extra_sources+b''.join")
(out/'generate.py').write_text(s)
tcl=(out/'build.tcl').read_text().replace('read_xdc $here/pins.xdc','source $here/tdc-ip.tcl\nread_vhdl $here/pin_capt.vhd\nread_vhdl $here/autophase.vhd\nread_vhdl $here/TDCCHAN_instrumented.vhd\nread_xdc $here/pins.xdc\nread_xdc $here/tdc-pins.xdc')
tcl=tcl.replace('opt_design', 'file mkdir build\nwrite_checkpoint -force build/pm12_ipbus_adc_synth.dcp\nsource $here/tdc-timing.tcl\nopt_design')
tcl=tcl.replace('foreach corner {max min}', 'write_checkpoint -force build/pm12_ipbus_adc_routed.dcp\nforeach corner {max min}')
(out/'build.tcl').write_text(tcl)
shutil.copy2(root/'tdc-timing.tcl',out/'tdc-timing.tcl')
shutil.copy2(root/'tdc-ip.tcl',out/'tdc-ip.tcl')
(out/'tdc-source-manifest.json').write_text(json.dumps(dict(revision=REVISION,sha256=manifest),indent=2)+'\n')
print(out)
