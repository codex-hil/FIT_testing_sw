"""Fine single-leg delta and common-translation search at normal20MHz gates.

Diagnostic sampled-pair balance; no production qualification changes.
"""
import argparse,contextlib,datetime,json,math,statistics,struct,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;PM=HERE.parent
sys.path[:0]=[str(PM/'acceptance'),str(PM/'ipbus_adc'),str(HERE),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware','/home/codex-hil/kasli-phase-tester']
from lease import acquire
from station import console,read_dna
from console import ConsoleI2C,Registers
from mcp23017 import afe_route
from phase_scan import ConsoleDAC
from pm12_console_regression import capture
from pm12_power import wait_power_good,require_power_good
from channel_settings import adc_address,require_serial_reply,snapshot_sources
from mod_dac28 import DAC,remote_lease,voltage
from client import Client
from adc_decode import decode
from host.gate_phase_ipbus import GatePhaseIPbusDevice

def pair(delta,common):
 return [voltage(round(1.024+delta+common,4)),voltage(round(2.048+common,4))]

def align(samples,reference=None):
 n=len(samples)//4*4
 means=[statistics.mean(samples[k:n:4]) for k in range(4)]
 if any(v<=1 or v>=4094 for v in samples):raise ValueError('Clipped ADC samples')
 if reference is None:
  scores=[means[i]+means[(i+1)%4] for i in range(4)];order=sorted(range(4),key=lambda k:scores[k],reverse=True)
  if scores[order[0]]-scores[order[1]]<30:raise ValueError('Ambiguous reference integration pair')
  start=order[0];margin=scores[order[0]]-scores[order[1]]
 else:
  scores=[sum((means[(i+s)%4]-reference[i])**2 for i in range(4)) for s in range(4)]
  order=sorted(range(4),key=lambda k:scores[k]);start=order[0];margin=scores[order[1]]-scores[order[0]]
  if margin<100:raise ValueError('Ambiguous circular waveform registration')
 template=[means[(i+start)%4] for i in range(4)]
 differences=[samples[i+1]-samples[i] for i in range(start,n-1,4)]
 return dict(template=template,registration_margin=margin,pair_start_mod4=start,
             mean_change_code=statistics.mean(differences),change_std=statistics.pstdev(differences),cycles=len(differences))

def point_mean(point,bank):
 values=[c['pair']['mean_change_code'] for c in point['captures'] if c['bank']==bank and c.get('valid')]
 return statistics.mean(values) if len(values)==3 else None

def root_estimate(points,bank):
 values=sorted((p['delta_V'],point_mean(p,bank)) for p in points if point_mean(p,bank) is not None)
 crossings=[]
 for (x,y),(xx,yy) in zip(values,values[1:]):
  if y*yy<0:crossings.append(x-y*(xx-x)/(yy-y))
  elif y==0:crossings.append(x)
 if len(crossings)!=1:raise ValueError(f'Bank{bank}: expected one signed crossing, got{crossings}')
 return crossings[0]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--station',type=Path,required=True)
 p.add_argument('--afe',type=int,choices=range(1,13),required=True);a=p.parse_args()
 cfg=json.loads(a.station.read_text());route=cfg['channels'][str(a.afe)]
 if cfg['stimulated_channel']!=a.afe or not route.get('integrator_connected'):raise ValueError('Confirm J6 route')
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 r=dict(physical_channel=a.afe,board_uid=cfg['board_uid'],started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),points=[],phase_uart=[],complete=False,
        protocol='reference-registered sampled integration pair; P-only delta grid100uV; common translates both outputs',adc_phase_code=32768)
 r['sources']=snapshot_sources(out,['__main__','lease','station','console','mcp23017','phase_scan','pm12_console_regression','pm12_power','channel_settings','mod_dac28','client','adc_decode','host.gate_phase_ipbus'])
 def save():(out/'status.json').write_text(json.dumps(r,indent=2)+'\n')
 save()
 with contextlib.ExitStack() as st:
  for name in sorted(['atmel-ice-J41800043065','pm12-210249A73E43','kasli-diot-00001','esp32-6825dd4c49e4','lattice-VER00001']):st.enter_context(acquire(Path.home()/'.cache'/(name+'.lock')))
  u=st.enter_context(console(cfg));r['pgood']=wait_power_good(u,capture);r['mcu']=capture(u,'RS');require_serial_reply(r['mcu']['reply'],str(cfg['board_serial']))
  r['DNA']=read_dna(cfg,out);assert 'PM12-K7-'+r['DNA']==cfg['board_uid']
  c=Client();st.callback(c.close);r['fpga']=c.read(0,3);assert r['fpga']==[0x504d1202,0x10002,0xff2f746c]
  d=GatePhaseIPbusDevice();st.callback(d.close)
  r['hdmi_before']=[d.read(0x144),d.read(0x150)];assert r['hdmi_before'][0]==1 and r['hdmi_before'][1]&0xd==9
  gates=d.capture(4095,channels=cfg['channels'][str(a.afe)]['phase_lanes']);(out/'gates-normal.json').write_text(json.dumps(gates)+'\n')
  for row in gates['channels']:
   bits=[(w>>k)&1 for w in row['words'] for k in range(8)];edges=[i for i in range(1,len(bits)) if bits[i] and not bits[i-1]]
   assert len(edges)>500 and all(abs(b-a-48)<=1 for a,b in zip(edges,edges[1:])), 'Normal20MHz gate verification failed'
  remote=st.enter_context(remote_lease());dac=DAC(remote,channels=[2,3]);st.callback(dac.close)
  bus=ConsoleI2C(u,capture);phase=ConsoleDAC(u,a.afe,capture,r['phase_uart'].append);references={}
  def measure(stage,delta,common=0.,target=None):
   settings=pair(delta,common);delta=round(settings[0]-settings[1]+1.024,4);common=round(settings[1]-2.048,4)
   require_power_good(u,capture);dac.park(*settings);time.sleep(.05)
   point=dict(index=len(r['points']),stage=stage,delta_V=delta,common_translation_V=common,actual_common_shift_V=common+delta/2,setpoints_V=settings,target_bank=target,captures=[])
   r['points'].append(point)
   for bank in [0,1]:
    for repeat in range(3):
     generation,status=c.acquire(bank,False);words=c.block(adc_address(a.afe),4096);assert c.read(0x12)==[generation]
     name=f'point{point["index"]:03d}-bank{bank}-{repeat}.bin';(out/name).write_bytes(struct.pack('<4096H',*words))
     cap=dict(bank=bank,file=name,generation=generation,hardware_status=status,valid=False)
     try:
      samples,timing=decode(words,bank);result=align(samples,references.get(bank))
      if bank not in references:references[bank]=result['template'];r['references']=references
      cap.update(valid=True,pair=result,timing=timing,minimum=min(samples),maximum=max(samples))
     except ValueError as error:cap['error']=str(error)
     point['captures'].append(cap);save()
   point['means']=[point_mean(point,b) for b in [0,1]];save()
   print(stage,'d',delta,'c',common,'A/B',point['means'],flush=True)
   return point
  try:
   phase.set_code(32768);dac.park(1.024,2.048)
   with bus.routed(*afe_route(a.afe)):
    regs=Registers(bus);assert regs.read(10)==regs.read(11) and not regs.read(10)&128
    regs.write(0x15,regs.read(0x15)|0x20);regs.write(1,regs.read(1)&~0x20)
    regs.write(0x14,regs.read(0x14)|0x88);regs.write(0,regs.read(0)&~0x88);regs.write(0x14,(regs.read(0x14)&~0x80)|8)
   baseline=measure('baseline',0)
   if any(v is None for v in baseline['means']):raise ValueError('No valid baseline template')
   coarse=[measure('coarse',i*.001) for i in range(13)]
   r['coarse_roots']=[root_estimate(coarse,b) for b in [0,1]];save()
   r['fine_roots']={};r['common_response']={}
   for bank in [0,1]:
    center=round(r['coarse_roots'][bank]*10000)/10000
    fine=[measure('fine',round(center-.001+i*.0001,4),target=bank) for i in range(21)]
    root=root_estimate(fine,bank);r['fine_roots'][str(bank)]=root
    candidate=round(root*10000)/10000
    r['common_response'][str(bank)]=[measure('common',candidate,c,target=bank)['index'] for c in [-.010,-.005,0,.005,.010]]
    for delta in [candidate,candidate-.0001,candidate+.0001,candidate]:measure('return',delta,target=bank)
    save()
   measure('baseline-return',0)
   r['complete']=True
  except BaseException as error:r['error']=repr(error);save();raise
  finally:
   errors=[]
   for action in [lambda:dac.park(1.024,2.048),lambda:phase.set_code(0)]:
    try:action()
    except BaseException as error:errors.append(repr(error))
   try:
    with bus.routed(*afe_route(a.afe)):
     regs=Registers(bus);regs.write(0x14,regs.read(0x14)|0x88);regs.write(0x15,regs.read(0x15)|0x20);assert regs.read(0x12)&0x88==0x88
    r['tca_final']={str(x):bus.mux(x) for x in [0x70,0x71]};assert set(r['tca_final'].values())=={0}
    r['pgood_final']=require_power_good(u,capture);r['hdmi_final']=[d.read(0x144),d.read(0x150)];assert r['hdmi_final']==r['hdmi_before']
   except BaseException as error:errors.append(repr(error))
   r['cleanup_errors']=errors;r['complete']=r['complete'] and not errors;r['scpi']=dac.records;r['i2c']=bus.records;r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
 print('BALANCE20_COMPLETE',r['complete'],flush=True)
if __name__=='__main__':main()
