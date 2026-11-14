#!/usr/bin/env python3
"""Within-image SPI reset/MISO-clamp A-B-A with direct surviving traces and exact restoration."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hold_spi import *
from station import jtag_command,read_dna,load_dependencies
sys.path.insert(0,str(BASE));from test_board import payload
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--output-name',default='hardware');args=p.parse_args();root=args.work;out=root/args.output_name;out.mkdir(exist_ok=False);(out/'executed.py').write_bytes(Path(__file__).read_bytes())
cfg=json.loads(Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-20261113/staging/board-station.json').read_text());cfg['jtag_workspace']=str(root/'jtag-work');load_dependencies(cfg)
new=root/'candidate/pm12_ipbus_adc.bit';gold=Path('/srv/codex-hil-nvme/pm12-tdc-clock40-20261114/candidate/pm12_ipbus_adc.bit');assert hashlib.sha256(gold.read_bytes()).hexdigest()=='4f0b3edba1271eed41757bc7f21845e43a4ecb2e2c023abe28f3b5770abc8c16'
q=json.loads((root/'candidate/qualification.json').read_text());assert q['pass'] and hashlib.sha256(new.read_bytes()).hexdigest()==q['bit_sha256'];newid=int(q['build_id'],16)
r=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),qualification=q,blocks=[])
def save():(out/'result.json').write_text(json.dumps(r,indent=2)+'\n')
def connect(expected):
 c=system.Client();end=time.monotonic()+20
 while True:
  try:
   if c.read(0,3)==[0x504d1202,0x10002,expected]:return c
  except TimeoutError:pass
  if time.monotonic()>end:c.close();raise TimeoutError('PM identity')
  time.sleep(.1)
with contextlib.ExitStack() as st:
 for n in sorted(['atmel-ice-J41800043065','pm12-210249A73E43','kasli-diot-00001']):st.enter_context(acquire(Path.home()/'.cache'/(n+'.lock')))
 d=system.GatePhaseIPbusDevice();st.callback(d.close);a=HeldAdapter(d);a.stop();assert d.read(0xe0)==0
 r['kasli']=dict(cfd=d.read(0xd8),map=d.read(0x15c),enable=d.read(0x144),state=d.read(0x150));r['old_divider']=d.read(0x154);d.write(0x154,600)
 with console(cfg) as preflight_uart:
  pg=wait_power_good(preflight_uart,capture);mcu=capture(preflight_uart,'RS');assert 'Board S/N: 1803'in mcu['reply']
 preflight=connect(0xc7531465)
 try:
  before=preflight.read(5,2);dna=read_dna(cfg,out);after=preflight.read(5,2);assert int(dna,16)==int('3A17A1B402212223',16);assert after[0]+(after[1]<<32)>=before[0]+(before[1]<<32)
  r['identity_before']=dict(uid='PM12-K7-3A17A1B402212223',dna=dna,fpga=preflight.read(0,3),mcu=mcu,pgood=pg)
 finally:preflight.close()
 save()
 with console(cfg) as u:
  r['pgood_before']=wait_power_good(u,capture)
  with jtag_command(cfg,out) as prefix:
   s=(BASE/'adc/tools/load_fpga.tcl').read_text().replace('source [file join [file dirname [info script]] common.tcl]','source '+str(BASE/'adc/tools/common.tcl')).replace('0x504dad01','0x504d5a04');(out/'load.tcl').write_text(s)
   def load(bit,label):
    bits=payload(bit,out/'payload.hex')
    with (out/(label+'.log')).open('w') as log:subprocess.run(prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(out/'load.tcl'),'-tclargs',cfg['jtag_cable'],cfg['hw_server'],str(out/'payload.hex'),str(bits)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300)
    (out/'payload.hex').unlink();assert 'LOAD_PASS'in(out/(label+'.log')).read_text()
   c=None
   try:
    load(new,'candidate-load');c=connect(newid);c.s.settimeout(.1);assert c.read(0x380)==[0x53504932]
    native_read=c.read;r['read_recoveries']=[]
    def recovered_read(address,count=1,increment=True):
     end=time.monotonic()+8;failures=0
     while True:
      try:
       value=native_read(address,count,increment)
       if failures:r['read_recoveries'].append(dict(address=address,count=count,failures=failures));save()
       return value
      except TimeoutError:
       failures+=1
       if time.monotonic()>end:raise
       time.sleep(.02)
    c.read=recovered_read
    assert c.read(0x380)==[0x53504932] and c.read(0x384)==[0x30003] and c.read(0x305)==[0x53520000]
    reply=c.transact(1,0x305,values=[4],allow_error=True);assert reply[1]&15 and c.read(0x305)==[0x53520000]
    r['invalid_mode_rejected']=True
    def set_mode(mode):
     assert mode in [0,2,3];a.stop();before=c.read(0x305)[0]
     if before!=(0x53520000|mode):
      try:c.write(0x305,[mode])
      except TimeoutError:r.setdefault('mode_ack_timeouts',[]).append(mode)
     assert c.read(0x305)==[0x53520000|mode]
     time.sleep(.15)
    def trace(label,stage,mode,divider,address):
     a.stop();assert c.read(0x305)==[0x53520000|mode]
     row=dict(label=label,stage=stage,mode=mode,divider=divider,address=address,host_start=time.monotonic(),kasli_before=d.read(0x150));r['trials'].append(row);save()
     seen=c.read(0x381)[0]&0x1000
     try:c.write(0x380,[0x41524d31])
     except TimeoutError:row['arm_ack_timeout']=True
     end=time.monotonic()+12
     while True:
      status=c.read(0x381)[0]
      if status&0x1000!=seen and status&3:break
      if time.monotonic()>end:raise TimeoutError('Observer ARM acknowledgement')
     time.sleep(.005)
     if address is not None:
      row['signature']=a.transfer(True,address)
      row['expected_signature']=0 if mode&2 else [0x4844,0x4d49,1][address]
      row['signature_ok']=row['signature']==row['expected_signature']
     row['kasli_after_frame']=d.read(0x150)
     while True:
      status=c.read(0x381)[0]
      if status&2:break
      if time.monotonic()>end:raise TimeoutError('Observer freeze')
      time.sleep(.01)
     count=c.read(0x382)[0];assert 1<=count<=512
     row.update(status=status,count=count,host_frozen=time.monotonic(),raw_words_partial=[]);save()
     for offset in range(0,count*3,128):
      row['raw_words_partial']+=c.read(0x8000+offset,min(128,count*3-offset));save()
     assert c.read(0x381)==[status] and c.read(0x382)==[count]
     row['raw_words']=row.pop('raw_words_partial');row['mode_after']=c.read(0x305)[0];assert row['mode_after']==0x53520000|mode
     row['trigger']=bool(status&8192);row['sys_reset_observed']=any(row['raw_words'][i]>8 and row['raw_words'][i+1]&4 for i in range(0,len(row['raw_words']),3));row['kasli_final']=d.read(0x150)
     (out/(label+'.json')).write_text(json.dumps(row,indent=2)+'\n');save();print(label,mode,divider,address,'RESET'if row['sys_reset_observed']else'LOCKLOSS'if row['trigger']else'stable',flush=True);return row
    r.pop('blocks');r['trials']=[];set_mode(0)
    trace('idle-before','idle',0,600,None)
    chosen=None
    for divider in [601,602,600,61,62,60]:
     d.write(0x154,divider);assert d.read(0x154)==divider
     cases=[]
     for i,address in enumerate([0,1,2]*2):cases.append(trace(f'search-d{divider}-{i}','search',0,divider,address))
     failing=[x['address']for x in cases if x['sys_reset_observed']]
     if len(failing)>=2:
      from collections import Counter
      selected,hits=Counter(failing).most_common(1)[0]
      if hits<2:
       for i in range(4):
        extra=trace(f'confirm-d{divider}-{selected}-{i}','search',0,divider,selected);hits+=int(extra['sys_reset_observed'])
        if hits>=2:break
      if hits>=2:chosen=(divider,selected);break
    r['baseline_reproduced']=chosen is not None;save()
    if chosen:
     divider,address=chosen;r['chosen']=dict(divider=divider,address=address);d.write(0x154,divider)
     for stage,mode in [('C1-clamp-only',2),('B1-reset-clamped',3),('C2-clamp-only',2),('B2-reset-clamped',3),('C3-clamp-only',2),('A-return-normal',0)]:
      set_mode(mode)
      for i in range(6):trace(f'{stage}-{i}',stage,mode,divider,address)
    set_mode(0);trace('idle-after','idle',0,d.read(0x154),None)
    r['completed']=True;save()
   except BaseException as e:r['error']=repr(e);save();raise
   finally:
    if c:c.close()
    load(gold,'golden-restore');c=connect(0xc7531465);r['restored']=True;save()
    try:
     d.write(0x154,r['old_divider']);a.stop();r['identity_after']=c.read(0,3);r['frontend_ready']=c.read(0x205)[0];r['pgood_after']=require_power_good(u,capture)
     from client import save_capture
     r['adc_attempts']=[]
     for attempt in range(2):
      gen,status=c.acquire(0,False);raw=c.download(gen)
      try:
       r['adc_final']=save_capture(out/f'adc-final-{attempt}',raw,0,False,gen,status);r['adc_attempts'].append(dict(pass_=True));break
      except ValueError as error:r['adc_attempts'].append(dict(pass_=False,error=str(error)));save()
     r['adc_validated']=bool(r.get('adc_final'))
    finally:c.close();r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();a.stop()
