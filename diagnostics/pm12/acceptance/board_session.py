"""Identity-guarded PM12 sessions. No programming, resets or implicit channel routing.

begin/measure access hardware; verify is strictly offline. Native tools remain
low-level adapters, not entry points for a newly attached board.
"""
import argparse,contextlib,datetime,hashlib,json,os,subprocess,sys,uuid,shutil
from pathlib import Path
HERE=Path(__file__).resolve().parent
PM=HERE.parent
from identity import board_uid
from lease import acquire,ENV

def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def files(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and 'jtag-work' not in p.parts and p.name!='files.sha256.json'}
def uid(cfg):
 value=cfg['board_uid']
 if board_uid(value.removeprefix('PM12-K7-'))!=value:raise ValueError('Noncanonical board UID')
 return value
@contextlib.contextmanager
def locks(cfg):
 with contextlib.ExitStack() as st:
  names=sorted(set(cfg['run_leases'])|set(cfg['identity_leases']))
  streams=[st.enter_context(acquire(Path.home()/'.cache'/(n+'.lock'))) for n in names]
  previous=os.environ.get(ENV);os.environ[ENV]=json.dumps({str((Path.home()/'.cache'/(n+'.lock')).resolve()):f.fileno() for n,f in zip(names,streams)})
  try:yield tuple(f.fileno() for f in streams)
  finally:
   if previous is None:os.environ.pop(ENV,None)
   else:os.environ[ENV]=previous

def identity(cfg,out):
 from station import load_dependencies,identify
 out.mkdir()
 # Unique temporary JTAG working files never share another thread's extraction.
 local=dict(cfg,jtag_workspace=str(out/'jtag-work'),verify_endpoints=True)
 load_dependencies(local)
 result=identify(local,out)
 if result['identity']['uid']!=uid(cfg):raise ValueError('Wrong physical board')
 write(out/'result.json',result);return result

def load_session(root):
 root=Path(root).resolve();s=read(root/'session.json');cfg=read(root/'station.json')
 if uid(cfg)!=s['board_uid'] or root.parent.name!=s['board_uid']:raise ValueError('Session path/configuration UID mismatch')
 if sha(root/'station.json')!=s['station_sha256']:raise ValueError('Session station configuration changed')
 return root,s,cfg

def enroll(station,root,registry):
 from station import load_dependencies,console,read_dna
 from identity import register
 import re
 cfg=read(station)
 for key in ['board_uid','board_serial']:cfg.pop(key,None)
 if str(cfg.get('asset_label','')).startswith('PM12-K7-'):cfg.pop('asset_label',None)
 out=Path(root).resolve()/'enrollments'/uuid.uuid4().hex;out.mkdir(parents=True)
 cfg['jtag_workspace']=str(out/'jtag-work');load_dependencies(cfg)
 from pm12_console_regression import capture
 from pm12_power import wait_power_good
 with locks(cfg):
  with console(cfg) as u:
   pg=wait_power_good(u,capture);serial=capture(u,'RS');match=re.search(r'Board S/N:\s*(\d+)',serial['reply'])
   if not match:raise ValueError('No MCU identity')
  jtag=out/'identity';jtag.mkdir();dna=read_dna(cfg,jtag)
 identity_record=dict(uid=board_uid(dna),fpga_dna=dna,mcu_eeprom_serial=match[1],observed_utc=now(),asset_label=cfg.get('asset_label') or board_uid(dna),mcu_reply=serial,pgood=pg)
 register(registry,identity_record);cfg.update(board_uid=identity_record['uid'],board_serial=match[1],asset_label=identity_record['asset_label'],stimulated_channel=None,fitted_channels=[],shared_monitors_connected=False,smu_sense=None)
 for route in cfg.get('channels',{}).values():route.update(analog_connected=False,integrator_connected=False,phase_lanes=[])
 for module in cfg.get('modules',[]):
  if module.get('role')=='DUT':module.update(hardware_uid=cfg['board_uid'],eeprom_serial=cfg['board_serial'])
 write(out/'identity.json',identity_record);write(out/'station-enrolled.json',cfg)
 print(json.dumps(dict(board_uid=cfg['board_uid'],configuration=str(out/'station-enrolled.json'),note='Declare actual fitting and USB routing before begin; FPGA diagnostic readiness checked by begin')))
 return out


def load_sram(station,root,bit,expected_sha):
 cfg=read(station);board=uid(cfg)
 if len(expected_sha)!=64 or sha(bit)!=expected_sha:raise ValueError('Bitstream SHA256 mismatch')
 out=Path(root).resolve()/board/'configuration'/uuid.uuid4().hex;out.mkdir(parents=True)
 from station import load_dependencies,read_dna,jtag_command,console
 load_dependencies(cfg)
 sys.path.insert(0,str(PM));from test_board import payload
 from pm12_console_regression import capture
 from pm12_power import wait_power_good
 import re
 record={'board_uid':board,'bit_sha256':expected_sha,'volatile_sram_only':True,'status':'ERROR','started_utc':now()}
 local=dict(cfg,jtag_workspace=str(out/'jtag-work'))
 try:
  with locks(cfg):
   with console(cfg) as u:
    record['pgood']=wait_power_good(u,capture);record['mcu']=capture(u,'RS')
    if not re.search(r'Board S/N:\s*'+re.escape(str(cfg['board_serial']))+r'\b',record['mcu']['reply']):raise ValueError('Wrong MCU')
   before=out/'identity-before';before.mkdir();dna=read_dna(local,before)
   if board_uid(dna)!=board:raise ValueError('Wrong physical DNA; SRAM programming inhibited')
   record['dna']=dna;bits=payload(Path(bit),out/'payload.hex')
   script=(PM/'adc/tools/load_fpga.tcl').read_text().replace('source [file join [file dirname [info script]] common.tcl]','source '+str(PM/'adc/tools/common.tcl')).replace('0x504dad01','0x504d5a04');(out/'load.tcl').write_text(script)
   with jtag_command(local,out) as prefix:
    with (out/'load.log').open('w') as log:subprocess.run(prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(out/'load.tcl'),'-tclargs',cfg['jtag_cable'],cfg.get('hw_server','localhost:3121'),str(out/'payload.hex'),str(bits)],stdout=log,stderr=subprocess.STDOUT,check=True,timeout=300,start_new_session=True)
   if 'LOAD_PASS' not in (out/'load.log').read_text():raise ValueError('No SRAM loader acknowledgement')
   record['identity_after']=identity(cfg,out/'identity-after')['identity'];record['status']='PASS'
 except BaseException as error:record['error']=repr(error);raise
 finally:
  record['finished_utc']=now();write(out/'configuration.json',record)
 print(json.dumps({'path':str(out),'status':record['status']}));return record


def begin(station,root):
 cfg=read(station);board=uid(cfg)
 session=Path(root).resolve()/board/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]);session.mkdir(parents=True)
 write(session/'station.json',cfg)
 row=dict(schema=1,board_uid=board,started_utc=now(),station_sha256=sha(session/'station.json'),status='UNVERIFIED',measurements=[])
 write(session/'session.json',row)
 try:
  with locks(cfg):row['identity']=identity(cfg,session/'identity')['identity']
  row['status']='READY';write(session/'session.json',row)
 except BaseException as error:
  row.update(status='ERROR',error=repr(error));write(session/'session.json',row);raise
 print(session);return session

def plan(cfg,kind,channel,out,window,points,pairs):
 if window not in ('before-str','str-rise'):raise ValueError('Unknown sample window')
 if not 17<=points<=4097:raise ValueError('ADC points must be17..4097')
 route=cfg.get('channels',{}).get(str(channel),{})
 if channel not in cfg.get('fitted_channels',[]):raise ValueError('Selected channel is not in declared fitting')
 if cfg.get('stimulated_channel')!=channel:raise ValueError('Selected channel does not match declared USB route')
 key='analog_connected' if kind=='adc' else 'integrator_connected'
 if not route.get(key):raise ValueError('Requested input route not declared connected')
 pair=route.get('dac_channels' if kind=='adc' else 'integrator_dac_channels')
 if not isinstance(pair,list) or len(pair)!=2 or len(set(pair))!=2 or any(type(x)is not int or x not in range(8) for x in pair):raise ValueError('Explicit DAC pair required')
 expected=cfg['expected_build_id'];expected=f'{expected:08x}' if isinstance(expected,int) else expected
 base=[cfg['python'],str(PM/'cfd_simulator'/('adc_line_test.py' if kind=='adc' else 'integrator_scan.py')),'--afe',str(channel),'--board-serial',str(cfg['board_serial']),'--expected-build',expected,'--sample-window',window,'--dac-channels',*map(str,pair),'--out',str(out/'native')]
 if kind=='adc':
  other=route.get('integrator_dac_channels')
  if not other:raise ValueError('Declare parked integrator DAC pair')
  return base+['--acquire','--points',str(points),'--integrator-dac-channels',*map(str,other)]
 if not pairs:raise ValueError('Integrator requires explicit P:N voltage pairs')
 from math import isfinite
 for text in pairs:
  v=list(map(float,text.split(':')))
  if len(v)!=2 or any(not isfinite(x) or not 0<=x<=3.3 for x in v):raise ValueError('Integrator command outside0..3.3V')
 return base+['--base','1.024','2.048','--offsets','0','--pairs',*pairs,'--repeats','4','--park','1.024','2.048']

def inhibit(cfg,phase=None,channel=None,park=False):
 from station import console,load_dependencies
 load_dependencies(cfg)
 from console import ConsoleI2C,Registers
 from mcp23017 import afe_route
 from phase_scan import ConsoleDAC
 from pm12_console_regression import capture
 from pm12_power import require_power_good
 from mod_dac28 import DAC,remote_lease
 result={'gpio':{},'phase_uart':[]}
 with console(cfg) as u:
  result['pgood']=require_power_good(u,capture);bus=ConsoleI2C(u,capture)
  for ch in cfg['fitted_channels']:
   with bus.routed(*afe_route(ch)):
    r=Registers(bus);assert r.read(10)==r.read(11) and not r.read(10)&128
    r.write(0x14,r.read(0x14)|0x88);r.write(0x15,r.read(0x15)|0x20)
    r.write(0,r.read(0)&~0x88);r.write(1,r.read(1)&~0x20)
    assert r.read(0x12)&0x88==0x88 and r.read(0x13)&0x20
    result['gpio'][str(ch)]={str(a):r.read(a) for a in [0,1,0x12,0x13,0x14,0x15]}
  if phase is not None:ConsoleDAC(u,channel,capture,result['phase_uart'].append).set_code(phase)
  if park:
   route=cfg['channels'][str(channel)]
   with remote_lease() as remote:
    d=DAC(remote,channels=route['dac_channels'])
    try:
     d.park(1,1);d.channels=tuple(route['integrator_dac_channels']);d.park(1.024,2.048);result['dac_final']=d.snapshot()
    finally:d.close()
  result['tca_final']={str(a):bus.mux(a) for a in [0x70,0x71]};assert set(result['tca_final'].values())=={0}
 return result

def measure(root,kind,channel,phase,window,points,pairs):
 root,session,cfg=load_session(root)
 if session['status']!='READY':raise ValueError('Session not verified')
 # Validate everything before touching hardware.
 name=now().replace(':','')+'-'+kind+f'-ch{channel:02d}-'+uuid.uuid4().hex[:6]
 out=root/'measurements'/name;cmd=plan(cfg,kind,channel,out,window,points,pairs)
 if phase not in range(65536):raise ValueError('Phase code outside16bits')
 out.mkdir(parents=True);snap=out/'controller-sources';snap.mkdir()
 for src in [Path(__file__),HERE/'station.py',HERE/'lease.py',HERE/'identity.py',HERE/'endpoint_binding.py',HERE/'bind_endpoint.tcl']:
  shutil.copy2(src,snap/src.name)
 record=dict(schema=1,board_uid=uid(cfg),channel=channel,test=kind,phase_code=phase,sample_window=window,started_utc=now(),status='ERROR',command=cmd,station_sha256=session['station_sha256'],controller_sources=files(snap))
 try:
  with locks(cfg) as fds:
   # Identity mismatch must never execute cleanup against the wrong board.
   record['identity_before']=identity(cfg,out/'identity-before')['identity']
   try:
    record['setup']=inhibit(cfg,phase,channel,park=True)
    with (out/'console.txt').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,pass_fds=fds,check=True)
    record['identity_after']=identity(cfg,out/'identity-after')['identity']
    record['status']='COMPLETE'
   finally:
    if 'identity_after' not in record:
     record['identity_cleanup']=identity(cfg,out/'identity-cleanup')['identity']
    record['cleanup']=inhibit(cfg,0,channel,park=True)
 except BaseException as error:record.update(status='ERROR',error=repr(error))
 finally:
  record['finished_utc']=now();write(out/'measurement.json',record);write(out/'files.sha256.json',files(out))
  session['measurements'].append(str(out.relative_to(root)));write(root/'session.json',session)
 print(json.dumps({'path':str(out),'status':record['status']}));return record

def verify(root):
 root,s,cfg=load_session(root)
 for rel in s['measurements']:
  out=(root/rel).resolve()
  if not out.is_relative_to(root):raise ValueError('Measurement path escapes session')
  r=read(out/'measurement.json')
  if r['board_uid']!=s['board_uid']:raise ValueError('Mixed board identities')
  if read(out/'files.sha256.json')!=files(out):raise ValueError('Measurement evidence modified')
  for key in ['identity_before','identity_after']:
   if r.get(key) and r[key]['uid']!=s['board_uid']:raise ValueError('Wrong live identity')
 return {'board_uid':s['board_uid'],'measurements':len(s['measurements']),'integrity':'PASS','note':'Integrity is not acceptance; ERROR records remain ERROR'}

def main():
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
 e=sub.add_parser('enroll');e.add_argument('--station',type=Path,required=True);e.add_argument('--root',type=Path,required=True);e.add_argument('--registry',type=Path,required=True)
 l=sub.add_parser('load-sram');l.add_argument('--station',type=Path,required=True);l.add_argument('--root',type=Path,required=True);l.add_argument('--bit',type=Path,required=True);l.add_argument('--sha256',required=True)
 b=sub.add_parser('begin');b.add_argument('--station',type=Path,required=True);b.add_argument('--root',type=Path,required=True)
 m=sub.add_parser('measure');m.add_argument('--session',type=Path,required=True);m.add_argument('--kind',choices=['adc','integrator'],required=True);m.add_argument('--channel',type=int,choices=range(1,13),required=True);m.add_argument('--phase-code',type=int,required=True);m.add_argument('--sample-window',choices=['before-str','str-rise'],required=True);m.add_argument('--points',type=int,default=257);m.add_argument('--pairs',nargs='+')
 v=sub.add_parser('verify');v.add_argument('--session',type=Path,required=True)
 a=p.parse_args()
 if a.action=='enroll':enroll(a.station,a.root,a.registry)
 elif a.action=='load-sram':load_sram(a.station,a.root,a.bit,a.sha256)
 elif a.action=='begin':begin(a.station,a.root)
 elif a.action=='verify':print(json.dumps(verify(a.session)))
 else:return 0 if measure(a.session,a.kind,a.channel,a.phase_code,a.sample_window,a.points,a.pairs)['status']=='COMPLETE' else 1
 return 0
if __name__=='__main__':raise SystemExit(main())
