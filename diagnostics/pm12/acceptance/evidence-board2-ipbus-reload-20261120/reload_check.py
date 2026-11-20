import sys,json,datetime,uuid,subprocess,time,contextlib,struct,hashlib
from pathlib import Path
A=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/acceptance');sys.path.insert(0,str(A))
import board_session as b
from boundary import physical_identity
from station import load_dependencies,jtag_command,console
from link_recovery import restart
cfg=b.read('/srv/codex-hil-nvme/pm12-board-sessions/PM12-K7-2A17A1B40221242B/20261120T151926Z-6e0ce39f/station.json');uid=b.uid(cfg)
O=Path('/srv/codex-hil-nvme/pm12-board-sessions')/uid/'setup'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-ipbus-reload-'+uuid.uuid4().hex[:8]);O.mkdir();b.write(O/'station.json',cfg)
BIT=Path('/srv/codex-hil-nvme/pm12-rx-clock-counter-20261115/candidate-v2/pm12_ipbus_adc.bit');expected='28fb5747bafe575455bff8bf91484c8ebb5303ea18d3e0a0925fdb0c4283d0b2';assert b.sha(BIT)==expected
load_dependencies(cfg);sys.path.insert(0,str(A.parent));from test_board import payload
from client import Client
from pm12_console_regression import capture
from pm12_power import require_power_good
r={'board_uid':uid,'started_utc':b.now(),'status':'ERROR','bit_sha256':expected,'build_id':'ff2f746c','scope':'PM FPGA SRAM only. No MCU/CPLD/Flash/PLL profile writes. Guarded optional Kasli PM PHY restart only; management/HDMI/DIO settings preserved.'}
def save():b.write(O/'result.json',r)
def ids(c):
 v=c.read(0,3);assert v==[0x504d1202,0x10002,0xff2f746c],v;return v
def netprobe():
 c=Client()
 try:return ids(c)
 finally:c.close()
with b.locks(cfg):
 try:
  r['identity_before']=physical_identity(cfg,O/'identity-before');save()
  try:r['network_before']=netprobe()
  except Exception as e:r['network_before_error']=repr(e)
  save();bits=payload(BIT,O/'payload.hex');script=(A.parent/'adc/tools/load_fpga.tcl').read_text().replace('source [file join [file dirname [info script]] common.tcl]','source '+str(A.parent/'adc/tools/common.tcl')).replace('0x504dad01','0x504d5a04');(O/'load.tcl').write_text(script)
  local=dict(cfg,jtag_workspace=str(O/'jtag-work'))
  with jtag_command(local,O) as prefix:
   with (O/'load.log').open('w') as f:subprocess.run(prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(O/'load.tcl'),'-tclargs',cfg['jtag_cable'],cfg.get('hw_server','localhost:3121'),str(O/'payload.hex'),str(bits)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
  assert 'LOAD_PASS' in (O/'load.log').read_text();r['sram_load']='PASS';save()
  try:r['network_after']=netprobe()
  except Exception as e:
   r['initial_network_after_error']=repr(e);save();r['phy_restart']=restart(cfg,O);r['network_after']=netprobe()
  save();r['identity_bound']=b.identity(cfg,O/'identity-bound')['identity'];save()
  c=Client();r['polls']=[];r['network_errors']=[]
  try:
   previous=None;deadline=time.monotonic()+35
   for i in range(100):
    if time.monotonic()>deadline:break
    t=time.monotonic()
    try:
     ident=ids(c);u=c.read(5,2);value=u[0]+(u[1]<<32)
     if previous is not None:assert value>=previous,'SYS counter restarted'
     previous=value;r['polls'].append({'index':i,'utc':b.now(),'uptime':value,'latency_s':time.monotonic()-t})
    except Exception as e:
     r['network_errors'].append({'index':i,'error':repr(e)});save()
     if len(r['network_errors'])>=3:break
    time.sleep(.08)
   r['read_retry_events']=c.read_retry_events;save();assert len(r['polls'])==100 and not r['network_errors'] and not c.read_retry_events,'IPbus polling not stable'
   r['transport']={'buffers':[],'bytes_compared':0}
   for bank in [0,1]:
    gen,status=c.acquire(bank,True)
    for ch in range(12):
     address=0x10000+ch*4096;words=c.block(address,4096);again=c.block(address,4096);assert words==again and c.read(0x12)==[gen]
     assert words==[i^(ch*0x1111)^(bank<<15) for i in range(4096)],(bank,ch)
     name=f'pattern-bank{bank}-ch{ch+1:02d}.bin';data=struct.pack('<4096H',*words);(O/name).write_bytes(data);r['transport']['buffers'].append({'bank':bank,'channel':ch+1,'file':name,'sha256':hashlib.sha256(data).hexdigest(),'generation':gen});r['transport']['bytes_compared']+=2*len(data)
    save()
   r['transport']['status']='PASS';r['physical_bank0_capture']=list(c.acquire(0,False));r['final_ids']=ids(c);r['final_uptime']=c.read(5,2);r['all_read_retry_events']=c.read_retry_events;assert not c.read_retry_events
  finally:c.close()
  with console(cfg) as u:
   r['pgood_after']=require_power_good(u,capture);r['uart_after']=[capture(u,cmd) for cmd in ['RS','@PLL','@TEMP']];assert 'ADT7311 REG=03 C3' in r['uart_after'][2]['reply']
  r['status']='PASS'
 except BaseException as e:r['error']=repr(e)
 finally:r['finished_utc']=b.now();save();b.write(O/'files.sha256.json',b.files(O))
print(json.dumps({'path':str(O),'status':r['status'],'error':r.get('error'),'sram_load':r.get('sram_load'),'polls':len(r.get('polls',[])),'transport':r.get('transport',{}).get('status')}))
