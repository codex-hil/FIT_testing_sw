import sys,json,contextlib,datetime
from pathlib import Path
sys.path.insert(0,'/home/codex-hil/fit-testing-publish/diagnostics/pm12/system')
from hold_spi import *
r={}
with contextlib.ExitStack()as st:
 for n in sorted(['atmel-ice-J41800043065','pm12-210249A73E43','kasli-diot-00001']):st.enter_context(acquire(Path.home()/'.cache'/(n+'.lock')))
 u=st.enter_context(console(dict(uart='/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0')));c=system.Client();st.callback(c.close);d=system.GatePhaseIPbusDevice();st.callback(d.close)
 r.update(identity=c.read(0,3),frontend=c.read(0x205)[0],enable=d.read(0x144),state=d.read(0x150),pgood=require_power_good(u,capture),mcu=capture(u,'RS'))
 assert r['identity']==[0x504d1202,0x10002,0xc7531465]and r['frontend']==0xfff and r['enable']==1 and r['state']&15==9 and 'Board S/N: 1803'in r['mcu']['reply']
 r['pass']=True;r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
Path(__file__).with_name('tailcheck.json').write_text(json.dumps(r,indent=2)+'\n');print('TAILCHECK_PASS')
