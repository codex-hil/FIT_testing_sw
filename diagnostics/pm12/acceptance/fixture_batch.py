"""Identity-bound four-CFD timing/phase or SMU batches. No CPLD programming."""
import argparse,contextlib,importlib.util,json,subprocess,sys,uuid,shutil
from pathlib import Path
import board_session as b

def load_timing():
 path=b.PM/'tdc_live120/clock40/retest.py';spec=importlib.util.spec_from_file_location('pm12_clock40_retest',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def validate_config(cfg,kind):
 fitted=cfg.get('fitted_channels',[])
 if len(fitted)!=4 or len(set(fitted))!=4 or any(type(ch)is not int or ch not in range(1,13) for ch in fitted):raise ValueError('Declare four distinct fitted physical channels')
 if kind in ('monitors','dacs'):
  if not cfg.get('shared_monitors_connected') or cfg.get('smu_sense')!='local-force-0A':raise ValueError('Explicit shared-monitor connection and Force0A voltmeter configuration required')
  if not cfg.get('smu_host') or not cfg.get('smu_serial'):raise ValueError('Explicit SMU endpoint/identity required')
 return fitted

def run(root,kind,intervals,settle=1.0):
 if not 1<=intervals<=1000:raise ValueError('Phase intervals1..1000')
 if not .01<=settle<=10:raise ValueError('Phase settle outside.01..10s')
 root,s,cfg=b.load_session(root);fitted=validate_config(cfg,kind);out=root/'measurements'/(kind+'-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True);shutil.copy2(Path(__file__),out/'executed-fixture-batch.py')
 r={'board_uid':s['board_uid'],'test':kind,'channel':None,'channels':fitted,'started_utc':b.now(),'status':'ERROR','commands':[],'note':'Four-CFD fitting, actual TDC port discovery for timing; finite functional tests'}
 def save():b.write(out/'measurement.json',r)
 try:
  with b.locks(cfg) as fds:
   r['identity_before']=b.identity(cfg,out/'identity-before')['identity']
   try:
    r['setup']=b.inhibit(cfg)
    def command(cmd):
     r['commands'].append(cmd);save()
     snapshot=out/'command-sources'/str(len(r['commands']));snapshot.mkdir(parents=True)
     for label,source in [('cfd',b.PM/'cfd_simulator'),('ipbus',b.PM/'ipbus_adc'),('host',Path(cfg['kasli_root'])/'host'),('mcu',Path(cfg['console_tools']))]:
      dest=snapshot/label;dest.mkdir()
      for file in source.glob('*.py'):shutil.copy2(file,dest/file.name)
     b.write(snapshot/'sources.sha256.json',b.files(snapshot))
     with (out/f'command{len(r["commands"]):02d}.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,pass_fds=fds,check=True)
    if kind in ('timing','phase'):
     from station import console
     m=load_timing();mapping={};discovery=out/'discovery';discovery.mkdir()
     with contextlib.ExitStack() as st:
      d=m.GatePhaseIPbusDevice();st.callback(d.close);c=m.Client();st.callback(c.close)
      if c.read(0x205)!=[0xfff]:raise ValueError('TDC frontends not ready')
      try:
       with m.dio_directions(m.Slot7Inputs(d),0):pass
       for port in range(4):
        burst=m.RoutedBurst(d,port)
        with m.dio_directions(burst,burst.mask):
         quiet=m.acquire(c,discovery,f'port{port}-quiet')
         if any(quiet['counts']):raise ValueError('Nonempty quiet TDC window')
         burst.upload_patch(m.pattern_words(1200,24,20));row=m.acquire(c,discovery,f'port{port}-discovery',burst,16,24)
         hit=[i+1 for i,n in enumerate(row['counts']) if n==16]
         if len(hit)!=1 or sum(row['counts'])!=16:raise ValueError('Ambiguous/crosstalk TDC mapping')
         mapping[port]=hit[0]
       if set(mapping.values())!=set(fitted):raise ValueError('Actual TDC cable map differs from declared fitted channels')
       r['mapping']={str(port):{'physical_channel':ch,'phase_lanes':[8+2*port,9+2*port]} for port,ch in mapping.items()};save()
       if kind=='timing':
        with console(cfg) as u:
         expected=cfg['expected_build_id'];expected=int(expected,16) if isinstance(expected,str) else expected
         result=m.run(d,c,u,out/'tdc',expected,tuple(mapping[p] for p in range(4)),str(cfg['board_serial']))
         if not result['pass']:raise ValueError('TDC batch did not pass')
      finally:d.write(0xe0,0);m.HeldAdapter(d).stop()
     for port,ch in mapping.items():
      lanes=f'{8+2*port},{9+2*port}'
      command([cfg['python'],str(b.PM/'cfd_simulator/phase_scan.py'),'--afe',str(ch),'--lanes',lanes,'--restore-code','0','--initialize-zero','--held-slot7','--clock-mhz','20','--transport','ipbus','--intervals',str(intervals),'--settle',str(settle),'--board-serial',str(cfg['board_serial']),'--out',str(out/f'phase-ch{ch:02d}')])
    else:
     script='smu_monitor_scan.py' if kind=='monitors' else 'smu_dac_sweep.py'
     cmd=[cfg['python'],str(b.PM/'cfd_simulator'/script),'--out',str(out/'native'),'--connected',*map(str,fitted),'--board-serial',str(cfg['board_serial']),'--smu-host',cfg['smu_host'],'--smu-serial',cfg['smu_serial']]
     if kind=='dacs':cmd+=['--confirm-force-voltmeter']
     command(cmd)
    r['identity_after']=b.identity(cfg,out/'identity-after')['identity'];r['status']='COMPLETE'
   finally:
    if 'identity_after' not in r:r['identity_cleanup']=b.identity(cfg,out/'identity-cleanup')['identity']
    r['cleanup']=b.inhibit(cfg)
 except BaseException as error:r.update(status='ERROR',error=repr(error))
 finally:
  r['finished_utc']=b.now();save();b.write(out/'files.sha256.json',b.files(out));s['measurements'].append(str(out.relative_to(root)));b.write(root/'session.json',s)
 print(json.dumps({'path':str(out),'status':r['status']}));return r
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--session',type=Path,required=True);p.add_argument('--kind',choices=['timing','phase','monitors','dacs'],required=True);p.add_argument('--phase-intervals',type=int,default=100);p.add_argument('--settle',type=float,default=1.0);a=p.parse_args();raise SystemExit(0 if run(a.session,a.kind,a.phase_intervals,a.settle)['status']=='COMPLETE' else 1)
