import sys,json,datetime,time,contextlib
from pathlib import Path
P=Path(__file__).parent;O=P/'original-control';O.mkdir()
A=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/acceptance');sys.path[:0]=[str(A),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from lease import acquire
from station import console
from pm12_console_regression import capture
from pm12_power import wait_power_good,require_power_good
cfg=json.loads((A/'profiles/optiplex-session.example.json').read_text());r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'ERROR','scope':'Resident original firmware, read-only UART control after exact rollback; no MCU/PLL/FPGA programming','before':[],'polls':[],'after':[]}
def save():(O/'result.json').write_text(json.dumps(r,indent=2)+'\n')
with contextlib.ExitStack() as st:
 for n in sorted(['pm12-210249A73E43','atmel-ice-J41800043065','kasli-diot-00001']):st.enter_context(acquire(Path.home()/'.cache'/(n+'.lock')))
 try:
  with console(cfg) as u:
   r['pgood']=wait_power_good(u,capture)
   for c in ['RS','@TEMP']:
    require_power_good(u,capture);r['before'].append(capture(u,c));save()
   assert 'ADT7311 REG=03 C3' in r['before'][1]['reply']
   for i in range(40):
    require_power_good(u,capture);row=capture(u,'@PLL');row['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();r['polls'].append(row);save();time.sleep(.1)
   for c in ['@TEMP','@POWER','RS']:
    require_power_good(u,capture);r['after'].append(capture(u,c));save()
   assert 'ADT7311 REG=03 C3' in r['after'][0]['reply'];assert 'ERR ' not in r['after'][1]['reply'];r['status']='PASS'
 except BaseException as e:r['error']=repr(e);raise
 finally:r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
print(json.dumps(r))
