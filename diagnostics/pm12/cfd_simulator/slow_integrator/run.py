"""PM2 slow complementary integrator gates and signed input offsets, with rollback."""
import argparse,contextlib,hashlib,json,math,re,statistics,struct,subprocess,sys,time
from pathlib import Path
parser=argparse.ArgumentParser(description='PM2-only slow gate diagnostic with verified rollback')
parser.add_argument('--out',type=Path,required=True)
parser.add_argument('--vectors',type=Path,required=True)
parser.add_argument('--station',type=Path,required=True)
parser.add_argument('--adc-phase-code',type=int,default=32768)
parser.add_argument('--deltas-mv',type=float,nargs='+',default=[4,8,12])
args=parser.parse_args()
if not 0<=args.adc_phase_code<=65535:parser.error('ADC phase code must be0..65535')
if not all(math.isfinite(v) and 0<=1.024+v/2000<=3.3 and 0<=2.048-v/2000<=3.3 for v in args.deltas_mv):
 parser.error('All symmetric DAC setpoints must be finite and within0..3.3V')
ROOT=args.out.resolve();ROOT.mkdir(parents=True,exist_ok=False)
BUILD=args.vectors.resolve()
QUALIFIED={'program.tcl': 'b06de99eb23c452a19c909a46dc3dd62bbf95cb8d51c1efd4c05525cbf9a8c64', 'restore.tcl': 'a21fbc28d21d6612d24dd2834ab801a30f07a3a12219006c109b1b714b0ba1d2', 'verify-original.tcl': '8a659e773644da5a201ed96e153c1024778d53300205253f4a62b7fe133ca766'}
for name,value in QUALIFIED.items():
 assert hashlib.sha256((BUILD/name).read_bytes()).hexdigest()==value, 'Unqualified/channel-mismatched vector'
PM=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12')
sys.path[:0]=[str(PM/'acceptance'),str(PM/'cfd_simulator'),str(PM/'ipbus_adc'),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware','/home/codex-hil/kasli-phase-tester']
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
from host.gate_phase_ipbus import GatePhaseIPbusDevice
OUT=ROOT/'hardware';OUT.mkdir(exist_ok=False)
CFG=json.loads(args.station.read_text())
assert CFG['board_uid']=='PM12-K7-3A17A1B402212223'
assert CFG['stimulated_channel']==2 and CFG['channels']['2'].get('integrator_connected'), 'Confirm J6 on PM2'
CFG['jtag_workspace']=str(ROOT/'jtag-work')
r=dict(adc_phase_code=args.adc_phase_code,requested_deltas_mV=args.deltas_mv,physical_channel=2,complete=False,points=[],uart=[],change='Gate A/B complementary divide40; CLK40 and ADC CLK80 preserved')
r['sources']=snapshot_sources(OUT,['host.gate_phase_ipbus','host.gate_phase_device','host.lvds8_device','host.device','__main__','lease','station','console','mcp23017','phase_scan','pm12_console_regression','pm12_power','channel_settings','mod_dac28','client','adc_decode'])
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
 d=GatePhaseIPbusDevice();st.callback(d.close)
 r['hdmi_before']=[d.read(0x144),d.read(0x150)];assert r['hdmi_before'][0]==1 and r['hdmi_before'][1]&0xd==9
 changed=False
 with jtag_command(CFG,OUT) as prefix:
  def tcl(payload,tag,read=False):
   script=PM/'adc/tools'/('read_cplds.tcl' if read else 'execute_native.tcl')
   with (OUT/(tag+'.log')).open('w') as log:
    subprocess.run(prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(script),'-tclargs',CFG['jtag_cable'],CFG['hw_server'],str(payload),'0'],stdout=log,stderr=subprocess.STDOUT,timeout=300,check=True)
   text=(OUT/(tag+'.log')).read_text();assert ('CPLD_READ_PASS' if read else 'NATIVE_EXECUTE_PASS') in text
   return text
  def gates(stage,period):
   data=d.capture(4095,channels=[12,13]);(OUT/(stage+'-gates.json')).write_text(json.dumps(data)+'\n')
   results=[]
   for row in data['channels']:
    bits=[(w>>i)&1 for w in row['words'] for i in range(8)]
    edges=[i for i in range(1,len(bits)) if bits[i] and not bits[i-1]]
    gaps=[b-a for a,b in zip(edges,edges[1:])]
    assert len(gaps)>20 and all(abs(x-period)<=1 for x in gaps), (stage,row['logical'],gaps[:20])
    results.append(dict(logical=row['logical'],rising_edges=len(edges),period_samples_median=statistics.median(gaps),period_samples_range=[min(gaps),max(gaps)],high_fraction=sum(bits)/len(bits),sample_hz_nominal=d.sample_hz))
   r[stage+'-gates']=results;save()
   print('GATES',stage,results,flush=True)
  def collect(stage,leg='baseline',offset=0.,pair=(1.024,2.048)):
   require_power_good(u,capture);dac.park(*pair);time.sleep(.15)
   row=dict(stage=stage,leg=leg,offset_V=offset,setpoints_V=pair,captures=[]);r['points'].append(row)
   for bank in [0,1]:
    for repeat in range(3):
     generation,status=c.acquire(bank,False);words=c.block(adc_address(2),4096);assert c.read(0x12)==[generation]
     name=f'point{len(r["points"])-1:03d}-bank{bank}-{repeat}.bin';(OUT/name).write_bytes(struct.pack('<4096H',*words))
     cap=dict(bank=bank,file=name,generation=generation,hardware_status=status,valid=False)
     try:
      x,timing=decode(words,bank);fold=40 if stage.startswith('slow') else 4;n=len(x)//fold*fold
      cap.update(valid=True,mean=sum(x)/len(x),minimum=min(x),maximum=max(x),clipped_fraction=sum(v in [0,4095] for v in x)/len(x),fold_samples=fold,phase_means=[sum(x[k:n:fold])/len(x[k:n:fold]) for k in range(fold)],timing=timing)
     except ValueError as e:cap['decode_error']=str(e)
     row['captures'].append(cap);save()
   print(stage,leg,offset,[(v['bank'],round(v.get('mean',-1),2)) for v in row['captures']],flush=True)
  try:
   before=rows(tcl('unused','before-nv',True));tcl(BUILD/'verify-original.tcl','verify-original')
   r['original_verified']=True;save()
   dac.park(1.024,2.048);phase.set_code(args.adc_phase_code)
   with bus.routed(*afe_route(2)):
    regs=Registers(bus);assert regs.read(10)==regs.read(11) and not regs.read(10)&128
    regs.write(0x15,regs.read(0x15)|0x20);regs.write(1,regs.read(1)&~0x20)
    regs.write(0x14,regs.read(0x14)|0x88);regs.write(0,regs.read(0)&~0x88)
    regs.write(0x14,(regs.read(0x14)&~0x80)|8)
   collect('normal-before');gates('normal-before',48)
   changed=True;save();tcl(BUILD/'program.tcl','program-reset')
   after=rows(tcl('unused','after-nv',True));altered=sorted({ch for ch,i in before if before[ch,i]!=after[ch,i]})
   r['changed_channels']=altered;assert altered==[2];save()
   collect('slow-baseline')
   assert all(cap['valid'] for cap in r['points'][-1]['captures']), 'ADC clock/coherency changed at slow gates'
   gates('slow',480)
   for delta in [v/1000 for v in args.deltas_mv]:
    collect('slow-stimulus','differential',delta,(round(1.024+delta/2,4),round(2.048-delta/2,4)))
   collect('slow-return')
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
     collect('normal-after');gates('normal-after',48)
     r['hdmi_final']=[d.read(0x144),d.read(0x150)];assert r['hdmi_final']==r['hdmi_before']
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
