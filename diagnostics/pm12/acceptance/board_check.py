"""Final MCU/transport/HDMI checks under a verified board_session; volatile tests only."""
import contextlib,json,sys,time,struct,hashlib,datetime,uuid
from pathlib import Path
import board_session as session

def run(root,repeats=12):
 if not 1<=repeats<=100:raise ValueError('repeats1..100')
 root,s,cfg=session.load_session(root);out=root/'measurements'/('board-final-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
 snapshot=out/'controller-sources';snapshot.mkdir()
 import shutil
 for src in [Path(__file__),Path(session.__file__),Path(session.__file__).with_name('station.py')]:shutil.copy2(src,snapshot/src.name)
 r={'schema':1,'board_uid':s['board_uid'],'test':'board-final','channel':None,'started_utc':session.now(),'status':'ERROR','trials':[]}
 def save():session.write(out/'measurement.json',r)
 with session.locks(cfg):
  try:r['identity_before']=session.identity(cfg,out/'identity-before')['identity'];save()
  except BaseException as error:
   r.update(status='ERROR',error=repr(error),finished_utc=session.now());save();session.write(out/'files.sha256.json',session.files(out));s['measurements'].append(str(out.relative_to(root)));session.write(root/'session.json',s);return r
  from station import load_dependencies,console,mcu
  load_dependencies(cfg)
  from client import Client
  from host.gate_phase_ipbus import GatePhaseIPbusDevice
  from host.pm_system_test import HDMIAdapter
  from pm12_console_regression import capture
  from pm12_power import require_power_good
  from console import ConsoleI2C
  try:
   (out/'mcu').mkdir();r['mcu']=mcu(cfg,out/'mcu');save()
   with contextlib.ExitStack() as st:
    c=Client();st.callback(c.close);d=GatePhaseIPbusDevice();st.callback(d.close)
    r['network']={'status':'PASS','buffers':[],'bytes_compared':0}
    for bank in [0,1]:
     gen,status=c.acquire(bank,False)
     for ch in range(1,13):
      address=0x10000+((ch-1)<<12);w=c.block(address,4096);again=c.block(address,4096)
      if w!=again or c.read(0x12)!=[gen] or any(x>=16384 or ((x>>12)&1)!=bank for x in w):raise ValueError('Frozen ADC transport mismatch')
      data=struct.pack('<4096H',*w);name=f'network-ch{ch:02d}-bank{bank}.bin';(out/name).write_bytes(data);r['network']['buffers'].append({'channel':ch,'bank':bank,'file':name,'sha256':hashlib.sha256(data).hexdigest(),'generation':gen});r['network']['bytes_compared']+=2*len(data)
     save()
    if d.read(0x144)!=1 or d.read(0x150)&15!=9:raise ValueError('HDMI transmitter must remain enabled and idle')
    a=HDMIAdapter(d);r['hdmi_initial']={'enable':d.read(0x144),'state':d.read(0x150),'divider':d.read(0x154)}
    with console(cfg) as u:
     for i in range(repeats):
      require_power_good(u,capture);before=c.read(5,2);seen=c.read(0x391)[0]&8;c.write(0x390,[0x41524d31]);deadline=time.monotonic()+2
      while True:
       state=c.read(0x391)[0]
       if (state&8)!=seen and state&1:break
       if time.monotonic()>deadline:raise TimeoutError('Clock monitor arm')
      address=i%2;signature=a.transfer(True,address);deadline=time.monotonic()+2
      while not c.read(0x391)[0]&2:
       if time.monotonic()>deadline:raise TimeoutError('Clock monitor freeze')
      regs=c.read(0x390,13);words=c.block(0xa000,8192);after=c.read(5,2)
      # Full frozen monitor retained, not just success flags.
      name=f'hdmi-clock-{i:03d}.bin';(out/name).write_bytes(struct.pack('<8192I',*words))
      row={'index':i,'address':address,'signature':signature,'expected':[0x4844,0x4d49][address],'registers':regs,'raw_file':name,'sys_loss_trigger':bool(regs[1]&4),'uptime_before':before,'uptime_after':after,'pll':capture(u,'@PLL')}
      row['pass_']=signature==row['expected'] and not row['sys_loss_trigger'] and (after[0]+(after[1]<<32))>=(before[0]+(before[1]<<32));r['trials'].append(row);save();print('HDMI',i,row['pass_'],flush=True)
     r['power_final']=require_power_good(u,capture)
    r['hdmi_final']={'enable':d.read(0x144),'state':d.read(0x150),'divider':d.read(0x154)}
    assert r['hdmi_final']==r['hdmi_initial']
   r['identity_after']=session.identity(cfg,out/'identity-after')['identity']
   r['status']='PASS' if r['mcu']['status']=='PASS' and len(r['trials'])==repeats and all(v['pass_'] for v in r['trials']) else 'FAIL'
   save();r['validation']=validate(out,min_trials=repeats)
  except BaseException as error:r.update(status='ERROR',error=repr(error))
  finally:
   try:
    if 'identity_after' not in r:r['identity_cleanup']=session.identity(cfg,out/'identity-cleanup')['identity']
    r['cleanup']=session.inhibit(cfg,0,cfg['stimulated_channel'],park=True)
   except Exception as error:r.update(status='ERROR',cleanup_error=repr(error))
   r['finished_utc']=session.now();save();session.write(out/'files.sha256.json',session.files(out));s['measurements'].append(str(out.relative_to(root)));session.write(root/'session.json',s)
 print(json.dumps({'path':str(out),'status':r['status']}));return r
# Offline counterpart, also usable for historical frozen final-check records.
def validate(directory,min_trials=12):
 directory=Path(directory);r=session.read(directory/'measurement.json');uid=r['board_uid']
 if any(r[k]['uid']!=uid for k in ['identity_before','identity_after']):raise ValueError('Mixed live identities')
 if r['mcu']['status']!='PASS':raise ValueError('MCU test failed')
 expected={(ch,b) for ch in range(1,13) for b in [0,1]};seen=set()
 for row in r['network']['buffers']:
  data=(directory/row['file']).read_bytes();words=struct.unpack('<4096H',data)
  if hashlib.sha256(data).hexdigest()!=row['sha256'] or any(w>=16384 or ((w>>12)&1)!=row['bank'] for w in words):raise ValueError('Bad ADC transport buffer')
  seen.add((row['channel'],row['bank']))
 if seen!=expected or r['network']['bytes_compared']!=393216:raise ValueError('Incomplete transport coverage')
 if len(r['trials'])<min_trials:raise ValueError('Insufficient HDMI trials')
 summaries=[]
 for t in r['trials']:
  if t['signature']!=t['expected'] or t['sys_loss_trigger'] or not t['pass_']:raise ValueError('HDMI signature/clock loss')
  regs=t['registers'];count,start=regs[2:4]
  if regs[0]!=0x434c4b52 or regs[5]!=384 or regs[12]!=2048 or not 1<=count<=2048 or not 0<=start<2048:raise ValueError('Clock monitor format')
  raw=struct.unpack('<8192I',(directory/t['raw_file']).read_bytes());full=[];previous=None
  for n in range(count):
   i=(start+n)%2048;w0,w1,w2,w3=raw[4*i:4*i+4];flags=w2>>16;length=w3>>16;wid=w3&65535
   if not 1<=length<=384:raise ValueError('Clock window size')
   if previous and (wid!=(previous[0]+1)&65535 or (w0-previous[1])&0xffffffff!=length):raise ValueError('Clock record discontinuity')
   previous=(wid,w0)
   if length==384 and flags&0x18==0x18 and not flags&0x1c4:full.append((w1&65535,w1>>16,w2&65535))
  if not full:raise ValueError('No valid full clock windows')
  ranges={name:[min(x[i] for x in full),max(x[i] for x in full)] for i,name in enumerate(['mclk','gtref','sys'])}
  if any(abs(x[i]-expected)>1 for x in full for i,expected in enumerate([256,640,256])):raise ValueError('Relative clock edge-count deviation exceeds1')
  summaries.append({'index':t['index'],'valid_full_windows':len(full),'ranges':ranges})
 return {'board_uid':uid,'status':'PASS','transport_bytes_compared':393216,'hdmi_trials':len(r['trials']),'clock_windows':summaries,'scope':'Finite functional check, not analog glitch/jitter, BER or power-fault injection'}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--session',type=Path,required=True);p.add_argument('--repeats',type=int,default=12);a=p.parse_args();raise SystemExit(0 if run(a.session,a.repeats)['status']=='PASS' else 1)
