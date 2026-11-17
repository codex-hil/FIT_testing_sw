"""PM2 continuous INTB reset; separate DAC input sweeps with verified rollback."""
import argparse,contextlib,json,re,struct,subprocess,sys,time
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--build-dir',type=Path,required=True,help='Verified ISE/SVF artifacts from this experiment')
parser.add_argument('--station',type=Path,required=True)
args=parser.parse_args()
ROOT=args.out.resolve();ROOT.mkdir(parents=True,exist_ok=False)
BUILD=args.build_dir.resolve()
assert all((BUILD/(n+'.tcl')).is_file() for n in ['program','restore','verify-original'])
PM=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12')
sys.path[:0]=[str(PM/'acceptance'),str(PM/'cfd_simulator'),str(PM/'ipbus_adc'),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from lease import acquire
from station import console,jtag_command
from console import ConsoleI2C,Registers
from mcp23017 import afe_route
from phase_scan import ConsoleDAC
from pm12_console_regression import capture
from pm12_power import wait_power_good,require_power_good
from channel_settings import adc_address,require_serial_reply,snapshot_sources
from mod_dac28 import DAC,remote_lease
from client import Client
from adc_decode import decode
OUT=ROOT/'hardware';OUT.mkdir(exist_ok=False)
CFG=json.loads(args.station.read_text())
CFG['jtag_workspace']=str(ROOT/'jtag-work')
r=dict(physical_channel=2,complete=False,points=[],uart=[],change='INTB high; INTA and clocks unchanged')
r['sources']=snapshot_sources(OUT,['__main__','lease','station','console','mcp23017','phase_scan','pm12_console_regression','pm12_power','channel_settings','mod_dac28','client','adc_decode'])
def save():(OUT/'status.json').write_text(json.dumps(r,indent=2)+'\n')
def rows(text):
 a=re.findall(r'^ARRAY (\d+) ([AB]) (\d+) ([0-9a-fA-F]+)$',text,re.M)
 p={(int(c),int(i)):int(v,16) for c,s,i,v in a if s=='A'}
 q={(int(c),int(i)):int(v,16) for c,s,i,v in a if s=='B'}
 assert len(a)==1968 and len(p)==984 and p==q
 return p
with contextlib.ExitStack() as st:
 for n in sorted(['atmel-ice-J41800043065','pm12-210249A73E43','kasli-diot-00001','esp32-6825dd4c49e4','lattice-VER00001']):st.enter_context(acquire(Path.home()/'.cache'/(n+'.lock')))
 u=st.enter_context(console(CFG));r['pgood']=wait_power_good(u,capture)
 r['mcu']=capture(u,'RS');require_serial_reply(r['mcu']['reply'],'1803')
 c=Client();st.callback(c.close);r['fpga']=c.read(0,3);assert r['fpga']==[0x504d1202,0x10002,0xff2f746c]
 remote=st.enter_context(remote_lease());dac=DAC(remote,channels=[2,3]);st.callback(dac.close)
 bus=ConsoleI2C(u,capture);phase=ConsoleDAC(u,2,capture,r['uart'].append)
 changed=False
 with jtag_command(CFG,OUT) as prefix:
  def tcl(payload,tag,read=False):
   script=PM/'adc/tools'/('read_cplds.tcl' if read else 'execute_native.tcl')
   with (OUT/(tag+'.log')).open('w') as log:
    subprocess.run(prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(script),'-tclargs',CFG['jtag_cable'],CFG['hw_server'],str(payload),'0'],stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
   text=(OUT/(tag+'.log')).read_text();assert ('CPLD_READ_PASS' if read else 'NATIVE_EXECUTE_PASS') in text
   return text
  def collect(stage,leg='baseline',offset=0.,pair=(1.024,2.048)):
   require_power_good(u,capture);dac.park(*pair);time.sleep(.15)
   row=dict(stage=stage,leg=leg,offset_V=offset,setpoints_V=pair,captures=[]);r['points'].append(row)
   for bank in [0,1]:
    for repeat in range(3):
     generation,status=c.acquire(bank,False);words=c.block(adc_address(2),4096);assert c.read(0x12)==[generation]
     name=f'point{len(r["points"])-1:03d}-bank{bank}-{repeat}.bin';(OUT/name).write_bytes(struct.pack('<4096H',*words))
     cap=dict(bank=bank,file=name,generation=generation,hardware_status=status,valid=False)
     try:
      x,timing=decode(words,bank);n=len(x)//4*4
      cap.update(valid=True,mean=sum(x)/len(x),minimum=min(x),maximum=max(x),clipped_fraction=sum(v in [0,4095] for v in x)/len(x),phase_means=[sum(x[k:n:4])/len(x[k:n:4]) for k in range(4)],timing=timing)
     except ValueError as e:cap['decode_error']=str(e)
     row['captures'].append(cap);save()
   print(stage,leg,offset,[(v['bank'],round(v.get('mean',-1),2)) for v in row['captures']],flush=True)
  try:
   before=rows(tcl('unused','before-nv',True));tcl(BUILD/'verify-original.tcl','verify-original')
   r['original_verified']=True;save()
   dac.park(1.024,2.048);phase.set_code(32768)
   with bus.routed(*afe_route(2)):
    regs=Registers(bus);assert regs.read(10)==regs.read(11) and not regs.read(10)&128
    regs.write(0x15,regs.read(0x15)|0x20);regs.write(1,regs.read(1)&~0x20)
    regs.write(0x14,regs.read(0x14)|0x88);regs.write(0,regs.read(0)&~0x88)
    regs.write(0x14,(regs.read(0x14)&~0x80)|8)
   collect('normal-before')
   changed=True;save();tcl(BUILD/'program.tcl','program-reset')
   after=rows(tcl('unused','after-nv',True));altered=sorted({ch for ch,i in before if before[ch,i]!=after[ch,i]})
   r['changed_channels']=altered;assert altered==[2];save()
   collect('reset-baseline')
   for leg in ['P','N']:
    for i in range(11):
     off=round(-.1+i*.02,4)
     pair=(round(1.024+off,4),2.048) if leg=='P' else (1.024,round(2.048+off,4))
     collect('reset-sweep',leg,off,pair)
    collect('reset-return',leg)
   r['scan_complete']=True
  except BaseException as e:r['error']=repr(e);save();raise
  finally:
   try:
    dac.park(1.024,2.048)
    if changed:
     tcl(BUILD/'restore.tcl','restore-original')
     restored=rows(tcl('unused','restored-nv',True));assert restored==before
     r['restored_all_cpld_rows']=True
     tcl(BUILD/'verify-original.tcl','verify-restored')
     collect('normal-after')
    phase.set_code(0);r['restored_phase_code']=0
   except BaseException as e:r['restore_error']=repr(e);save();raise
   finally:
    try:
     with bus.routed(*afe_route(2)):
      regs=Registers(bus);regs.write(0x14,regs.read(0x14)|0x88);regs.write(0x15,regs.read(0x15)|0x20)
      assert regs.read(0x12)&0x88==0x88
     r['tca_final']={str(a):bus.mux(a) for a in [0x70,0x71]};assert set(r['tca_final'].values())=={0}
     r['pgood_final']=require_power_good(u,capture)
    finally:r['scpi']=dac.records;r['i2c']=bus.records;save()
 r['complete']=bool(r.get('scan_complete') and r.get('restored_all_cpld_rows') and not r.get('error') and not r.get('restore_error'));save()
print('COMPLETE',r['complete'],flush=True)
