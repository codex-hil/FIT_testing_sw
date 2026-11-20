import sys,json,time,datetime,hashlib,struct
from pathlib import Path
A=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/acceptance');sys.path[:0]=[str(A),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware'];import board_session as b
from station import console,load_dependencies
from pm12_console_regression import capture
from pm12_power import require_power_good
cfg=b.read('/srv/codex-hil-nvme/pm12-board-sessions/PM12-K7-2A17A1B40221242B/20261120T151926Z-6e0ce39f/station.json');load_dependencies(cfg);from client import Client
O=Path('/srv/codex-hil-nvme/pm12-board-sessions')/b.uid(cfg)/'setup'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-read-only-ipbus');O.mkdir()
r={'board_uid':b.uid(cfg),'scope':'Read-only IPbus after one Kasli PM PHY restart, native1s timeout; following guarded SRAM load; endpoint count challenge remains failed, no guard relaxation and no register/ARM writes. Buffer stability is not ADC functional acceptance.','status':'ERROR','polls':[],'errors':[],'started_utc':b.now()}
def save():b.write(O/'result.json',r)
with b.locks(cfg):
 c=Client();c.s.settimeout(1.0)
 try:
  previous=None;deadline=time.monotonic()+35
  for i in range(100):
   if time.monotonic()>deadline:break
   start=time.monotonic()
   try:
    ids=c.read(0,3);assert ids==[0x504d1202,0x10002,0xff2f746c],ids
    words=c.read(5,2);u=words[0]+(words[1]<<32);reset=previous is not None and u<previous
    r['polls'].append({'index':i,'uptime':u,'counter_restart':reset,'latency_s':time.monotonic()-start,'utc':b.now()});previous=u
   except Exception as e:r['errors'].append({'index':i,'error':repr(e)});save()
   if len(r['errors'])>=5:break
   time.sleep(.1)
  r['retry_events']=list(c.read_retry_events);save();r['buffers']=[]
  if len(r['polls'])==100 and not r['errors']:
   gen0=c.read(0x12)
   for ch in range(12):
    addr=0x10000+ch*4096;before=c.block(addr,4096);after=c.block(addr,4096);assert before==after
    name=f'frozen-read-ch{ch+1:02d}.bin';raw=struct.pack('<4096H',*before);(O/name).write_bytes(raw);r['buffers'].append({'channel':ch+1,'file':name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes_compared':2*len(raw)})
   assert gen0==c.read(0x12);r['buffer_generation']=gen0
  r['all_retry_events']=c.read_retry_events
  r['status']='PASS_READ_ONLY' if len(r['polls'])==100 and not r['errors'] and not c.read_retry_events and not any(x['counter_restart'] for x in r['polls']) and len(r['buffers'])==12 else 'FAIL_READ_ONLY'
  with console(cfg) as u:r['pgood']=require_power_good(u,capture);r['uart']=[capture(u,x) for x in ['RS','@PLL','@TEMP']]
 except BaseException as e:r['error']=repr(e)
 finally:c.close();r['finished_utc']=b.now();save();b.write(O/'files.sha256.json',b.files(O))
print(json.dumps({'path':str(O),'status':r['status'],'polls':len(r['polls']),'errors':r['errors'],'retries':len(r.get('all_retry_events',[])),'counter_restarts':sum(x['counter_restart'] for x in r['polls']),'buffers':len(r.get('buffers',[])),'error':r.get('error')}))
