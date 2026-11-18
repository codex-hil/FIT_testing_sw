import contextlib,json,sys,time,struct,subprocess,hashlib,datetime
from pathlib import Path
PM=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12');sys.path[:0]=[str(PM/'acceptance'),str(PM/'cfd_simulator'),str(PM/'ipbus_adc'),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from lease import acquire
from station import console
from adc_dc_scan import Injection
from console import ConsoleI2C,Registers
from mcp23017 import afe_route
from pm12_console_regression import capture
from pm12_power import wait_power_good,require_power_good
from phase_scan import ConsoleDAC
from mod_dac28 import DAC,remote_lease
from client import Client
from adc_decode import decode
from analyze import assess
p=Path(__file__).resolve().parent;cfg=json.loads(Path('/srv/codex-hil-nvme/pm12-ch02-20261118/station.json').read_text());report={'mode':'DIAGNOSTIC_NOT_QUALIFICATION','channel':2,'phases':[0,16384,32768],'differences':[-.234375,.046875,.3375],'repeats':8,'measurements':[],'phase_uart':[],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(p/'frozen-analysis-sha256.json').write_text(json.dumps({n:hashlib.sha256((p/n).read_bytes()).hexdigest() for n in ['analyze.py','acquire_diagnostic.py']},indent=2)+'\n')
def save():(p/'acquisition.json').write_text(json.dumps(report,indent=2)+'\n')
try:
 with contextlib.ExitStack() as st:
  for n in sorted(cfg['run_leases']):st.enter_context(acquire(Path.home()/'.cache'/(n+'.lock')))
  u=st.enter_context(console(cfg));report['power']=wait_power_good(u,capture);report['mcu']=capture(u,'RS');assert '1803' in report['mcu']['reply']
  c=Client();st.callback(c.close);report['fpga']=c.read(0,3);assert report['fpga']==[0x504d1202,0x10002,0xff2f746c]
  bus=ConsoleI2C(u,capture)
  for ch in [1,2,3,4]:
   with bus.routed(*afe_route(ch)):assert Registers(bus).read(0x12)&0x88==0x88
  remote=st.enter_context(remote_lease());dac=DAC(remote,channels=[2,3]);st.callback(dac.close);dac.park(2.048,1.024);dac.channels=(0,1)
  phase=ConsoleDAC(u,2,capture,report['phase_uart'].append)
  with bus.routed(*afe_route(2)):
   inj=Injection(Registers(bus));st.callback(inj.inhibit)
   try:
    for code in report['phases']:
     inj.inhibit();phase.set_code(code);time.sleep(.05)
     for bank in [0,1]:
      inj.select(bank)
      for diff in report['differences']:
       require_power_good(u,capture);dac.pair(1+diff/2,1-diff/2);time.sleep(.03)
       for rep in range(8):
        ident,state=c.acquire(bank,False);raw=c.block(0x11000,4096);assert c.read(0x12)==[ident] and all(w<16384 and ((w>>12)&1)==bank for w in raw)
        name=f'phase{code}-bank{bank}-d{diff:+.6f}-r{rep}.bin';(p/name).write_bytes(struct.pack('<4096H',*raw));row={'phase':code,'bank':bank,'diff':diff,'repeat':rep,'file':name,'generation':ident,'windows':assess(raw)}
        try:_,timing=decode(raw,bank);row['original_decode']='PASS';row['timing']=timing
        except ValueError as error:row['original_decode']=str(error)
        report['measurements'].append(row);save()
       print('PHASE',code,'BANK',bank,'DIFF',diff,'BUFFERS',len(report['measurements']),flush=True)
   finally:inj.inhibit();dac.baseline();report['scpi']=dac.records;report['i2c']=bus.records;save()
  report['complete']=True;save()
finally:
 with (p/'cleanup-console.txt').open('w') as f:r=subprocess.run([sys.executable,'/srv/codex-hil-nvme/pm12-ch02-20261118/cleanup.py'],stdout=f,stderr=subprocess.STDOUT)
 report['cleanup_returncode']=r.returncode;save()
