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
new=root/'candidate-v2/pm12_ipbus_adc.bit';gold=Path('/srv/codex-hil-nvme/pm12-write-quiet-20261115/candidate/pm12_ipbus_adc.bit');assert hashlib.sha256(gold.read_bytes()).hexdigest()=='0407f67e189a25bfee0f6fe02bc6d805c79eedc8b75ce1cca24d2a6dca06daf1'
q=json.loads((root/'candidate-v2/qualification.json').read_text());assert q['pass']and hashlib.sha256(new.read_bytes()).hexdigest()==q['bit_sha256'];newid=int(q['build_id'],16)
from cdce_status import decode
import inspect,station
_jtag_src=inspect.getsource(station.jtag_command).replace('subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)','subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)')
_jtag_globals=dict(vars(station));exec(_jtag_src,_jtag_globals);jtag_command=_jtag_globals['jtag_command'];station.jtag_command=jtag_command
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
 preflight=connect(0x71ac56fb)
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
    with (out/(label+'.log')).open('w') as log:subprocess.run(prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(out/'load.tcl'),'-tclargs',cfg['jtag_cable'],cfg['hw_server'],str(out/'payload.hex'),str(bits)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300,start_new_session=True)
    (out/'payload.hex').unlink();assert 'LOAD_PASS'in(out/(label+'.log')).read_text()
   c=None
   try:
    load(new,'counter-load');r.pop('blocks');r['trials']=[];c=None
    def attach():
     client=connect(newid);client.s.settimeout(.1);native=client.read
     def recovered(address,count=1,increment=True):
      deadline=time.monotonic()+8
      while True:
       try:return native(address,count,increment)
       except TimeoutError:
        if time.monotonic()>deadline:raise
        time.sleep(.02)
     client.read=recovered;assert client.read(0x390)==[0x434c4b52]and client.read(0x305)==[0x53520004];return client
    def pll():
     row=capture(u,'@PLL');match=__import__('re').search(r'CDCE62005 ([0-9A-F]{8})',row['reply'])
     try:row['decoded']=decode(int(match.group(1),16))if match else None
     except ValueError as error:row['decoded']=None;row['decode_error']=str(error)
     return row
    for label,address in [('idle-before',None),('read0',0),('read1',1)]:
     if c:c.close()
     c=attach();a.stop();d.write(0x154,601)
     row=dict(label=label,address=address,cdce_before=pll(),host_start=time.monotonic());r['trials'].append(row);save()
     ready=False
     for attempt in range(6):
      seen=c.read(0x391)[0]&8;row.setdefault('arm_requests',[]).append(time.monotonic())
      try:c.write(0x390,[0x41524d31])
      except TimeoutError:row.setdefault('arm_ack_timeouts',0);row['arm_ack_timeouts']+=1
      deadline=time.monotonic()+1
      while time.monotonic()<deadline:
       status=c.read(0x391)[0]
       if status&8!=seen:
        if status&1 or(address is None and status&2):ready=True
        break
       time.sleep(.005)
      if ready:break
     assert ready,'RX monitor did not arm'
     row['armed_host_seen']=time.monotonic()
     if address is not None:
      row['stimulus_host_before']=time.monotonic();row['signature']=a.transfer(True,address);row['stimulus_host_after']=time.monotonic();row['signature_ok']=row['signature']==[0x4844,0x4d49,1][address]
     time.sleep(.0095);row['cdce_after']=pll();save();deadline=time.monotonic()+8
     while True:
      regs=c.read(0x390,13)
      if regs[1]&2:break
      if time.monotonic()>deadline:raise TimeoutError('RX monitor freeze/reference stopped')
      time.sleep(.01)
     row['registers']=regs;count=regs[2];start=regs[3];assert 1<=count<=2048 and 0<=start<2048
     row['raw_words_partial']=[];save()
     for offset in range(0,8192,128):row['raw_words_partial']+=c.read(0xa000+offset,128);save()
     after=c.read(0x390,13);row['registers_after']=after;assert (after[1]&63,after[2],after[3])==(regs[1]&63,regs[2],regs[3])
     row['raw_words']=row.pop('raw_words_partial');row['triggered']=bool(regs[1]&4)
     (out/(label+'.json')).write_text(json.dumps(row,indent=2)+'\n');save();print(label,'SYS_TRIGGER'if row['triggered']else'timed',regs[8:11],flush=True)
    r['completed']=True;save()
   except BaseException as e:r['error']=repr(e);save();raise
   finally:
    if c:c.close()
    # Freshly configure after deliberate reset-provoking SPI controls.
    target=new if r.get('completed')else gold;targetid=newid if r.get('completed')else 0x71ac56fb
    load(target,'final-reload');c=connect(targetid)
    try:
     d.write(0x154,r['old_divider']);a.stop();r['identity_after']=c.read(0,3);r['frontend_ready']=c.read(0x205)[0];assert r['frontend_ready']==0xfff;r['pgood_after']=require_power_good(u,capture);r['temp_after']=capture(u,'@TEMP');assert 'REG=03 C3'in r['temp_after']['reply']
     from client import save_capture
     gen,status=c.acquire(0,False);raw=c.download(gen);r['adc_final']=save_capture(out/'adc-final',raw,0,False,gen,status);r['adc_validated']=True;r['retained_candidate']=targetid==newid;r['resident_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    except BaseException as error:
     r['postflight_error']=repr(error);c.close();load(gold,'golden-fallback');c=connect(0x71ac56fb);r['restored']=True;r['retained_candidate']=False;raise
    finally:c.close();r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save();a.stop()
