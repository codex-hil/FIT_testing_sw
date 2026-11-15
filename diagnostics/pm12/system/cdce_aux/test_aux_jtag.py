#!/usr/bin/env python3
"""MISO OE reversal and restricted write-only scratch diagnostics."""
import sys,subprocess
from jtag_meter import cases as meter_cases
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hold_spi import *
from station import jtag_command,read_dna,load_dependencies
# Isolate hardware-tool subprocess groups from the supervising Python process.
import inspect,station
_jtag_src=inspect.getsource(station.jtag_command).replace('subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)','subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)')
_jtag_globals=dict(vars(station));exec(_jtag_src,_jtag_globals);jtag_command=_jtag_globals['jtag_command'];station.jtag_command=jtag_command
sys.path.insert(0,str(BASE));from test_board import payload
class DiagnosticWrites(HeldAdapter):
 def transfer(self,read,address,value=0):
  if read:return super().transfer(read,address,value)
  if address!=0x40 or value not in (0,0xffff,0x5555,0x0f0f):raise ValueError('Only fixed diagnostic scratch writes qualified')
  packet=(address<<22)|value
  # These fixed packets contain neither MCU sync bytes nor AA reset bytes.
  assert not set(packet.to_bytes(4,'big'))&set(bytes.fromhex('7856341298badcfeaa'))
  before=self.d.read(0x158);self.d.write(0x148,packet);deadline=time.monotonic()+1
  while self.d.read(0x158)==before:
   if self.d.read(0x150)&4:raise RuntimeError('HDMI SPI error')
   if time.monotonic()>deadline:raise TimeoutError('HDMI SPI timeout')
  assert self.d.read(0x158)==(before+1)&0xffffffff
  return self.d.read(0x14c)&65535
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True);p.add_argument('--output-name',default='hardware');args=p.parse_args();root=args.work;out=root/args.output_name;out.mkdir(exist_ok=False);(out/'executed.py').write_bytes(Path(__file__).read_bytes())
cfg=json.loads(Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-20261113/staging/board-station.json').read_text());cfg['jtag_workspace']=str(root/'jtag-work');load_dependencies(cfg)
new=Path('/srv/codex-hil-nvme/pm12-write-quiet-20261115/candidate/pm12_ipbus_adc.bit');gold=Path('/srv/codex-hil-nvme/pm12-tdc-clock40-20261114/candidate/pm12_ipbus_adc.bit');assert hashlib.sha256(gold.read_bytes()).hexdigest()=='4f0b3edba1271eed41757bc7f21845e43a4ecb2e2c023abe28f3b5770abc8c16'
q=json.loads((Path('/srv/codex-hil-nvme/pm12-write-quiet-20261115/candidate/qualification.json')).read_text());assert q['pass'] and hashlib.sha256(new.read_bytes()).hexdigest()==q['bit_sha256'];newid=int(q['build_id'],16)
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
 d=system.GatePhaseIPbusDevice();st.callback(d.close);a=DiagnosticWrites(d);a.stop();assert d.read(0xe0)==0
 r['kasli']=dict(cfd=d.read(0xd8),map=d.read(0x15c),enable=d.read(0x144),state=d.read(0x150));r['old_divider']=d.read(0x154);d.write(0x154,600)
 with console(cfg) as preflight_uart:
  pg=wait_power_good(preflight_uart,capture);mcu=capture(preflight_uart,'RS');assert 'Board S/N: 1803'in mcu['reply']
 preflight=connect(newid)
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
    # Current71ac56fb identity/DNA is already checked; no initial reprogram needed.
    c=connect(newid);c.s.settimeout(.1);native=c.read;r['read_recoveries']=[]
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
    c.read=recovered
    assert c.read(0x306)==[0x474e0000]and c.read(0x305)==[0x53520004]and c.read(0x384)==[0x30005]
    r.pop('blocks');r['trials']=[]
    def trace(label,stage,genmode,parserhold,address=None,read=True,value=0):
     global c,native
     c.close();c=connect(newid);c.s.settimeout(.1);native=c.read;c.read=recovered
     a.stop();assert d.read(0x150)==9
     assert parserhold in (0,4)
     for attempt in range(4):
      if c.read(0x305)==[0x53520000|parserhold]:break
      try:c.write(0x305,[parserhold])
      except TimeoutError:pass
     assert c.read(0x305)==[0x53520000|parserhold]
     row=dict(label=label,stage=stage,generator_mode=genmode,parser_hold=parserhold,address=address,read=read,value=value,divider=d.read(0x154),host_start=time.monotonic());r['trials'].append(row);save()
     if c.read(0x306)!=[0x474e0000|genmode]:
      try:c.write(0x306,[genmode])
      except TimeoutError:row['mode_ack_timeout']=True
      assert c.read(0x306)==[0x474e0000|genmode]
     time.sleep(.05)
     seen=c.read(0x381)[0]&4096
     row['arm_attempts']=[];deadline=time.monotonic()+12;next_attempt=0
     while True:
      status=c.read(0x381)[0]
      if status&4096!=seen:
       if status&1:break
       if status&2:raise RuntimeError('Capture froze before stimulus')
      now=time.monotonic()
      if now>deadline:raise TimeoutError('ARM')
      if now>=next_attempt:
       row['arm_attempts'].append(dict(host_time=now));save()
       try:c.write(0x380,[0x41524d31])
       except TimeoutError:row['arm_attempts'][-1]['ack_timeout']=True;save()
       next_attempt=time.monotonic()+.5
      time.sleep(.005)
     if address is not None:
      if not read:row['writes_before']=c.read(0x304)[0]
      row['signature']=a.transfer(read,address,value)
      if read:row['signature_ok']=row['signature']==[0x4844,0x4d49,1][address]
     while True:
      status=c.read(0x381)[0]
      if status&2:break
      if time.monotonic()>deadline:raise TimeoutError('freeze')
      time.sleep(.01)
     count=c.read(0x382)[0];assert 1<=count<=512
     row.update(status=status,count=count,raw_words_partial=[]);save()
     for offset in range(0,count*3,128):row['raw_words_partial']+=c.read(0x8000+offset,min(128,count*3-offset));save()
     assert c.read(0x381)==[status]and c.read(0x382)==[count]
     if address is not None and not read:
      row['writes_after']=c.read(0x304)[0];row['scratch_after']=c.read(0x303)[0]
      row['write_committed']=(row['writes_after']==(row['writes_before']+1)&65535 and row['scratch_after']==value)
     row['raw_words']=row.pop('raw_words_partial');row['generator_after']=c.read(0x306)[0];row['parser_after']=c.read(0x305)[0]
     assert row['generator_after']==0x474e0000|genmode and row['parser_after']==0x53520000|parserhold
     samples=[(row['raw_words'][i],row['raw_words'][i+1])for i in range(0,len(row['raw_words']),3)if row['raw_words'][i]>8]
     row['sys_reset_observed']=any(w&4 for t,w in samples);row['lock_loss_observed']=any(not(w&1)or w&128 for t,w in samples)
     row['miso_edges']=sum(bool(x[1]&64)!=bool(y[1]&64)for x,y in zip(samples,samples[1:]));row['watch_span_ticks']=samples[-1][0]-samples[0][0]if samples else 0
     row['oe_samples_high']=sum(bool(w&8192)for t,w in samples);row['samples']=len(samples)
     row['oe_mismatches']=sum(bool(w&8192)!=(True if genmode>=4 else bool(w&8))for t,w in samples)
     if genmode>=4:assert row['oe_mismatches']==0, 'Forced output enable not observed'
     (out/(label+'.json')).write_text(json.dumps(row,indent=2)+'\n');save();print(label,'RESET'if row['sys_reset_observed']else'stable','edges',row['miso_edges'],flush=True);return row
    d.write(0x154,601)
    r['jtag_primary']=meter_cases(prefix,cfg,out/'primary-meter',a,2);save()
    c.close();c=None
    memories=['flash','boot','eeprom','fuse0','fuse1','fuse2','fuse4','fuse5','lock','usersig','prodsig','signature']
    avbase=['/home/codex-hil/.local/bin/avrdude','-c','atmelice_pdi','-p','x128a3u','-P','usb:J41800043065','-B','10','-u']
    def memory_reads(dest):return sum((['-U',m+':r:'+str(dest/(m+'.bin'))+':r']for m in memories),[])
    def avr(command,label):
     with(out/(label+'.log')).open('w')as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
    r['pdi_started']=True;save();before=out/'mcu-before';before.mkdir();avr(avbase+memory_reads(before),'mcu-backup')
    old=(before/'flash.bin').read_bytes().ljust(0x22000,b'\xff');assert len(old)==0x22000 and (before/'signature.bin').read_bytes()==bytes.fromhex('1e9742')
    anchor=bytes.fromhex('05ef1fe024e030e4');assert old[0xaf8:0xb00]==anchor
    expected=bytearray(old);expected[0xaf9]=0xe3;expected=bytes(expected)
    assert [i for i,(x,y)in enumerate(zip(old,expected))if x!=y]==[0xaf9]
    application=out/'application-aux.bin';application.write_bytes(expected[:0x20000])
    original=out/'application-original.bin';original.write_bytes(old[:0x20000])
    r['mcu_patch']=dict(address=0xaf9,before=0xef,after=0xe3,original_sha256=hashlib.sha256(old).hexdigest(),patched_sha256=hashlib.sha256(expected).hexdigest(),r5_before='40040FF5',r5_after='40040F35',meaning='PRI/SEC/AUX auto -> forced AUX; same output dividers');save()
    conf=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/mcu/pdi-application-only.conf')
    def program_image(image,label):
     dest=out/label;dest.mkdir();command=['/home/codex-hil/.local/bin/avrdude','-C','+'+str(conf),'-c','atmelice_pdi','-p','pm12_full_app','-P','usb:J41800043065','-B','10','-u','-U','app_full:w:'+str(image)+':r']+memory_reads(dest);avr(command,label);return dest
    r['program_attempted']=True;save()
    try:
     after=program_image(application,'mcu-after')
     assert (after/'flash.bin').read_bytes().ljust(0x22000,b'\xff')==expected
     r['protected_memories']={m:(after/(m+'.bin')).read_bytes()==(before/(m+'.bin')).read_bytes()for m in memories if m!='flash'};assert all(r['protected_memories'].values());save()
     r['aux_pgood']=wait_power_good(u,capture);r['aux_rs']=capture(u,'RS');r['aux_pll']=capture(u,'@PLL');assert 'Clock source INTERNAL, PLL LOCKED'in r['aux_rs']['reply']
     load(new,'aux-fpga-load');c=None
     r['jtag_aux']=meter_cases(prefix,cfg,out/'aux-meter',a,4);save()
     test=system.Client();test.s.settimeout(.1)
     try:r['aux_ethernet_identity']=test.read(0,3);r['aux_ethernet_available']=True
     except TimeoutError:r['aux_ethernet_available']=False
     finally:test.close()
     load(new,'aux-final-reload')
     import re
     report=int(re.search(r'LOAD_PASS ([0-9a-fA-F]+)',(out/'aux-final-reload.log').read_text()).group(1),16)
     r['final_jtag_report']=f'{report:x}';r['final_clock_flags']=(report>>240)&0xfff;assert r['final_clock_flags']&0x26==0x26
     r['aux_final_rs']=capture(u,'RS');assert 'Clock source INTERNAL, PLL LOCKED'in r['aux_final_rs']['reply']
     r['aux_final_temp']=capture(u,'@TEMP');assert 'REG=03 C3'in r['aux_final_temp']['reply']
     r['adc_status']='NOT_MEASURED: no PM Ethernet at AUX clock'
     r['pgood_after']=require_power_good(u,capture);r['aux_retained']=True;r['completed']=True;save()
    except BaseException as auxerror:
     r['aux_error']=repr(auxerror);save();rollback=program_image(original,'mcu-rollback');assert(rollback/'flash.bin').read_bytes().ljust(0x22000,b'\xff')==old;assert all((rollback/(m+'.bin')).read_bytes()==(before/(m+'.bin')).read_bytes()for m in memories if m!='flash');r['mcu_restored']=True;wait_power_good(u,capture);load(new,'original-clock-fpga-restore');save();raise
   except BaseException as e:r['error']=repr(e);save();raise
   finally:
    if c:c.close()
    if not r.get('aux_retained'):
     try:
      r['fallback_pgood']=wait_power_good(u,capture);load(new,'fallback-sram');r['fallback_rs']=capture(u,'RS');r['fallback_sram_restored']=True
     except BaseException as cleanup:r['fallback_error']=repr(cleanup)
    d.write(0x154,r['old_divider']);a.stop();r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
