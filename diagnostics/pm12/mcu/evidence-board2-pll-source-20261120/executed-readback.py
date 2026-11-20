import sys,json,fcntl,contextlib,datetime,time,re
from pathlib import Path
P=Path(__file__).parent;O=P/('pll-source-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));O.mkdir()
A=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/acceptance');sys.path[:0]=[str(A),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware',str(A.parent/'system/rx_clock_counter')]
from station import console
from pm12_console_regression import capture
from pm12_power import wait_power_good,require_power_good
from cdce_status import decode
cfg=json.loads((A/'profiles/optiplex-session.example.json').read_text());r={'operator_label':'board2','board_uid':None,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read current CDCE R8/source/lock only; no profile, clock-source, reset or EEPROM changes. Sparse polling cannot exclude brief transitions.','status':'ERROR','samples':[]}
def save():(O/'result.json').write_text(json.dumps(r,indent=2)+'\n')
with contextlib.ExitStack() as st:
 for n in sorted(['pm12-210249A73E43','atmel-ice-J41800043065']):
  f=st.enter_context(open('/home/codex-hil/.cache/'+n+'.lock','a+'));fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
 try:
  with console(cfg) as u:
   r['pgood']=wait_power_good(u,capture);r['rs_before']=capture(u,'RS');save()
   for i in range(12):
    require_power_good(u,capture);x=capture(u,'@PLL');x['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();m=re.search(r'CDCE62005 ([0-9A-F]{8})',x['reply']);assert m,x;x['decoded']=decode(int(m.group(1),16));r['samples'].append(x);save();time.sleep(.15)
   r['rs_after']=capture(u,'RS');r['status']='PASS_READBACK'
 except BaseException as e:r['error']=repr(e);raise
 finally:r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
print(json.dumps({'path':str(O),**r}))
