#!/usr/bin/env python3
"""MISO DRIVE12→4→12 output-only ECO, same placed/routed logic, direct reset capture."""
import sys,subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hold_spi import *
from station import jtag_command,read_dna,load_dependencies
sys.path.insert(0,str(BASE));from test_board import payload
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--output-name',default='hardware');args=p.parse_args();root=args.work;out=root/args.output_name;out.mkdir(exist_ok=False);(out/'executed.py').write_bytes(Path(__file__).read_bytes())
cfg=json.loads(Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-20261113/staging/board-station.json').read_text());cfg['jtag_workspace']=str(root/'jtag-work');load_dependencies(cfg)
new=root/'candidate/drive4.bit';gold=Path('/srv/codex-hil-nvme/pm12-tdc-clock40-20261114/candidate/pm12_ipbus_adc.bit');assert hashlib.sha256(gold.read_bytes()).hexdigest()=='4f0b3edba1271eed41757bc7f21845e43a4ecb2e2c023abe28f3b5770abc8c16'
q=json.loads((root/'candidate/qualification.json').read_text());assert q['pass'] and hashlib.sha256(new.read_bytes()).hexdigest()==q['bit_sha256'];newid=int(q['rtl_id'],16)
base12=Path('/srv/codex-hil-nvme/pm12-spi-ab-20261114/candidate/pm12_ipbus_adc.bit');assert hashlib.sha256(base12.read_bytes()).hexdigest()=='344d49b9eb5ded207fd1340de88d36128197ee7c2624ed5fe94ce32d686fe245'
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
    load(base12,'baseline12-load')
    r['read_recoveries']=[]
    def attach():
     client=connect(newid);client.s.settimeout(.1);native=client.read
     def recovered(address,count=1,increment=True):
      deadline=time.monotonic()+8;failures=0
      while True:
       try:
        value=native(address,count,increment)
        if failures:r['read_recoveries'].append(dict(address=address,failures=failures));save()
        return value
       except TimeoutError:
        failures+=1
        if time.monotonic()>deadline:raise
        time.sleep(.02)
     client.read=recovered;assert client.read(0x380)==[0x53504932] and client.read(0x384)==[0x30003] and client.read(0x305)==[0x53520000]
     return client
    c=attach()
    def trace(label,stage,drive,divider,address):
     a.stop();d.write(0x154,divider);assert d.read(0x154)==divider and c.read(0x305)==[0x53520000]
     row=dict(label=label,stage=stage,drive_ma=drive,mode=0,divider=divider,address=address,host_start=time.monotonic());r['trials'].append(row);save()
     seen=c.read(0x381)[0]&4096
     try:c.write(0x380,[0x41524d31])
     except TimeoutError:row['arm_ack_timeout']=True
     deadline=time.monotonic()+12
     while True:
      status=c.read(0x381)[0]
      if status&4096!=seen and status&1:break
      if status&4096!=seen and status&2:raise RuntimeError('Observer froze before stimulus')
      if time.monotonic()>deadline:raise TimeoutError('ARM')
     time.sleep(.005)
     if address is not None:
      row['signature']=a.transfer(True,address);row['signature_ok']=row['signature']==[0x4844,0x4d49,1][address]
     while True:
      status=c.read(0x381)[0]
      if status&2:break
      if time.monotonic()>deadline:raise TimeoutError('freeze')
      time.sleep(.01)
     count=c.read(0x382)[0];assert 1<=count<=512
     row.update(status=status,count=count,raw_words_partial=[]);save()
     for offset in range(0,count*3,128):row['raw_words_partial']+=c.read(0x8000+offset,min(128,count*3-offset));save()
     assert c.read(0x381)==[status] and c.read(0x382)==[count]
     row['raw_words']=row.pop('raw_words_partial');row['mode_after']=c.read(0x305)[0];assert row['mode_after']==0x53520000
     row['sys_reset_observed']=any(row['raw_words'][i]>8 and row['raw_words'][i+1]&4 for i in range(0,len(row['raw_words']),3));row['trigger']=bool(status&8192);row['kasli_final']=d.read(0x150);a.stop()
     (out/(label+'.json')).write_text(json.dumps(row,indent=2)+'\n');save();print(label,drive,divider,address,'RESET'if row['sys_reset_observed']else'stable','DATA_OK'if row.get('signature_ok',True)else'BAD_DATA',flush=True);return row
    r.pop('blocks');r['trials']=[];time.sleep(.5)
    trace('idle12-before','idle-before',12,601,None)
    chosen=None
    for divider in [601,602,61]:
     cases=[trace(f'A12-d{divider}-{i}','A12-search',12,divider,0)for i in range(6)]
     if sum(x['sys_reset_observed']for x in cases)>=2:chosen=divider;break
    r['baseline_reproduced']=chosen is not None;r['chosen_divider']=chosen or 601;save();divider=r['chosen_divider']
    c.close();c=None;load(new,'drive4-load');c=attach();time.sleep(.5)
    trace('idle4-before','idle4',4,divider,None)
    for i in range(12):trace(f'B4-primary-{i}','B4-primary',4,divider,0)
    for div in [601,61]:
     for rep in range(3):
      for addr in [0,1,2]:trace(f'B4-functional-d{div}-r{rep}-a{addr}','B4-functional',4,div,addr)
    c.close();c=None;load(base12,'baseline12-return');c=attach();time.sleep(.5)
    for i in range(12):trace(f'A12-return-{i}','A12-return',12,divider,0)
    trace('idle12-after','idle-after',12,divider,None)
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
