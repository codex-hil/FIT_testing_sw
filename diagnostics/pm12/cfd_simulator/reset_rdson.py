"""Explicit diagnostic that reprograms CPLDs; PM12 continuous integrator reset; separate DAC input sweeps with verified rollback."""
import argparse,contextlib,datetime,hashlib,json,re,shutil,struct,subprocess,sys,time
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bank',choices=['A','B'],required=True)
parser.add_argument('--afe',type=int,choices=range(1,13),required=True)
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--build-dir',type=Path,required=True,help='Verified ISE/SVF artifacts from this experiment')
parser.add_argument('--station',type=Path,required=True)
args=parser.parse_args()
ROOT=args.out.resolve();ROOT.mkdir(parents=True,exist_ok=False)
BUILD=args.build_dir.resolve()
assert all((BUILD/(n+'.tcl')).is_file() for n in ['program','restore','verify-original'])
PM=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(PM/'acceptance'),str(PM/'cfd_simulator'),str(PM/'ipbus_adc'),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from lease import acquire
from station import console,jtag_command,read_dna
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
shutil.copy2(args.station,ROOT/'station.json')
route=CFG.get('channels',{}).get(str(args.afe),{})
if not route.get('fixture_id') or not route.get('integrator_connected') or CFG.get('stimulated_channel')!=args.afe:
 raise ValueError('Confirm J6 stimulus routing for the selected physical channel in station config')
manifest=json.loads((BUILD/'manifest.json').read_text())
from prepare_reset_vectors import BANK_HASHES
assert manifest['jed_sha256']==BANK_HASHES[args.bank]
assert manifest['physical_channel']==args.afe and manifest['reset_bank']==args.bank and manifest['mode']=='INT'+args.bank+'_HIGH_INT'+('B' if args.bank=='A' else 'A')+'_ORIGINAL'
for name,value in manifest['files'].items():
 assert name in ['program.tcl','restore.tcl','verify-original.tcl']
 assert hashlib.sha256((BUILD/name).read_bytes()).hexdigest()==value
assert set(manifest['files'])=={'program.tcl','restore.tcl','verify-original.tcl'}
shutil.copytree(BUILD,ROOT/'vectors')
BUILD=ROOT/'vectors'
CFG['jtag_workspace']=str(ROOT/'jtag-work')
r=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),fixture_id=route.get('fixture_id'),physical_channel=args.afe,reset_bank=args.bank,complete=False,points=[],uart=[],change='INT'+args.bank+' high; other gate and divider retained')
r['sources']=snapshot_sources(OUT,['__main__','lease','station','console','mcp23017','phase_scan','pm12_console_regression','pm12_power','channel_settings','mod_dac28','client','adc_decode','prepare_reset_vectors'])
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
 r['mcu']=capture(u,'RS');require_serial_reply(r['mcu']['reply'],str(CFG['board_serial']))
 r['fpga_dna']=read_dna(CFG,OUT);r['board_uid']='PM12-K7-'+r['fpga_dna'];assert r['board_uid']==CFG['board_uid']
 c=Client();st.callback(c.close);r['fpga']=c.read(0,3);assert r['fpga']==[0x504d1202,0x10002,0xff2f746c]
 remote=st.enter_context(remote_lease());dac=DAC(remote,channels=[2,3]);st.callback(dac.close)
 bus=ConsoleI2C(u,capture);phase=ConsoleDAC(u,args.afe,capture,r['uart'].append)
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
     generation,status=c.acquire(bank,False);words=c.block(adc_address(args.afe),4096);assert c.read(0x12)==[generation]
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
   with bus.routed(*afe_route(args.afe)):
    regs=Registers(bus);assert regs.read(10)==regs.read(11) and not regs.read(10)&128
    regs.write(0x15,regs.read(0x15)|0x20);regs.write(1,regs.read(1)&~0x20)
    regs.write(0x14,regs.read(0x14)|0x88);regs.write(0,regs.read(0)&~0x88)
    regs.write(0x14,(regs.read(0x14)&~0x80)|8)
   collect('normal-before')
   changed=True;save();tcl(BUILD/'program.tcl','program-reset')
   after=rows(tcl('unused','after-nv',True));altered=sorted({ch for ch,i in before if before[ch,i]!=after[ch,i]})
   r['changed_channels']=altered;assert altered==[args.afe];save()
   collect('reset-baseline')
   assert all(c['valid'] for c in r['points'][-1]['captures']), 'ADC strobe/coherency unavailable with reset held'
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
     phase.set_code(0);r['restored_phase_code']=0
    except BaseException as phase_error:r['phase_cleanup_error']=repr(phase_error)
    try:
     with bus.routed(*afe_route(args.afe)):
      regs=Registers(bus);regs.write(0x14,regs.read(0x14)|0x88);regs.write(0x15,regs.read(0x15)|0x20)
      assert regs.read(0x12)&0x88==0x88
     r['tca_final']={str(a):bus.mux(a) for a in [0x70,0x71]};assert set(r['tca_final'].values())=={0}
     r['pgood_final']=require_power_good(u,capture)
    finally:r['scpi']=dac.records;r['i2c']=bus.records;save()
 r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();r['complete']=bool(r.get('scan_complete') and r.get('restored_all_cpld_rows') and not r.get('error') and not r.get('restore_error') and not r.get('phase_cleanup_error'));save()
print('COMPLETE',r['complete'],flush=True)
