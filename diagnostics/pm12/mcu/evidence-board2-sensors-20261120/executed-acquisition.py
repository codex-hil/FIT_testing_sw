import sys,json,fcntl,contextlib,datetime,uuid
from pathlib import Path
P=Path(__file__).parent;O=P/('sensors-jumpers-'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S')+'-'+uuid.uuid4().hex[:6]);O.mkdir()
A=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/acceptance');sys.path[:0]=[str(A),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from station import console
from pm12_console_regression import capture
from pm12_power import wait_power_good,require_power_good
cfg=json.loads((A/'profiles/optiplex-session.example.json').read_text());r={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'board_uid':None,'operator_label':'board2','identity_note':'FPGA DNA pending; MCU prodsig f1b955294628e001d491e6117e1ae48886342fed01f4536b8dd731f2b083c11c from prior PDI provisioning; EEPROM serial1803 is copied','operator_action':'Owner confirmed sensor jumpers soldered','status':'ERROR','commands':[]}
def save():(O/'result.json').write_text(json.dumps(r,indent=2)+'\n')
with contextlib.ExitStack() as st:
 for n in sorted(['pm12-210249A73E43','atmel-ice-J41800043065']):
  f=st.enter_context(open('/home/codex-hil/.cache/'+n+'.lock','a+'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  with console(cfg) as u:
   r['pgood']=wait_power_good(u,capture)
   for c in ['RS','@I2C']:
    r['commands'].append(capture(u,c));save()
   for trial in range(3):
    for route in [4,5,6]:
     r.setdefault('sensor_pgood',[]).append(require_power_good(u,capture));row=capture(u,'@INA '+str(route));row['trial']=trial;r['commands'].append(row);save()
   r['temperature_pgood']=require_power_good(u,capture);r['commands'].append(capture(u,'@TEMP'));r['commands'].append(capture(u,'@I2C'))
   reads=[x for x in r['commands'] if x['command'].startswith('@INA')]
   r['status']='PASS_COMMUNICATION' if all('CONFIG=7127' in x['reply'] and 'ERR ' not in x['reply'] and x['reply'].count(' CH=')==3 for x in reads) else 'ERROR_SENSOR_READ'
 except BaseException as e:r['error']=repr(e);raise
 finally:r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
print(json.dumps({'path':str(O),**r}))
