"""Tie Ethernet/JTAG by a read-count challenge; tie MCU/Ethernet by restored scratch."""
from pathlib import Path
import json,subprocess,time,secrets

def count(report):
 value=int(report.strip(),16)
 if value&0xffffffff!=0x504d5a04 or (value>>208)&0xffffffff!=0x504d4442:raise ValueError('Unsupported JTAG diagnostic layout')
 return (value>>432)&0xffffffff

def check_delta(before,after,expected_strobe_cycles):
 delta=(after-before)&0xffffffff
 if delta!=expected_strobe_cycles:raise ValueError('JTAG/Ethernet endpoint mismatch or concurrent traffic')
 return delta

def bind(cfg,out,uart):
 from station import jtag_command
 from client import Client
 from pm12_console_regression import capture
 from pm12_power import require_power_good
 out=Path(out);out.mkdir();local=dict(cfg,jtag_workspace=str(out/'jtag-work'));c=Client();result={}
 try:
  uptime_before=c.read(5,2)
  with jtag_command(local,out) as prefix:
   command=prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(Path(__file__).with_name('bind_endpoint.tcl')),'-tclargs',cfg['jtag_cable'],cfg.get('hw_server','localhost:3121'),str(out)]
   with (out/'binding-jtag.log').open('w') as log:
    proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:
     deadline=time.monotonic()+90
     while not (out/'before.txt').exists():
      if proc.poll() is not None or time.monotonic()>deadline:raise TimeoutError('JTAG endpoint challenge startup')
      time.sleep(.05)
     before=count((out/'before.txt').read_text());requests=11+secrets.randbelow(21);retries=len(c.read_retry_events)
     for _ in range(requests):
      if c.read(0)!=[0x504d1202]:raise ValueError('Wrong network diagnostic')
     requests+=len(c.read_retry_events)-retries;(out/'network-done').write_text('done\n');proc.wait(timeout=30)
     if proc.returncode:raise RuntimeError('JTAG endpoint report failed')
     after=count((out/'after.txt').read_text());cycles=cfg.get('endpoint_strobe_cycles',4)
     if cycles!=4:raise ValueError('Unsupported endpoint bus handshake profile')
     result['jtag_ethernet']={'before':before,'after':after,'issued_register_reads':requests,'strobe_cycles_per_read':cycles,'observed_delta':(after-before)&0xffffffff}
     check_delta(before,after,requests*cycles)
    finally:
     if proc.poll() is None:proc.terminate();proc.wait(timeout=10)
  require_power_good(uart,capture);before=c.read(0x20,2);reply=capture(uart,'@FPGATEST');after=c.read(0x20,2)
  if reply['reply']!='FPGA TEST PASS 32 RESTORED\r\n' or before[0]!=after[0] or (after[1]-before[1])&65535!=33:raise ValueError('UART MCU and network endpoint are not the same FPGA or scratch was not restored')
  result['mcu_ethernet']={'before':before,'after':after,'reply':reply,'restored':True,'write_delta':33}
  uptime_after=c.read(5,2)
  if uptime_after[0]+(uptime_after[1]<<32)<uptime_before[0]+(uptime_before[1]<<32):raise ValueError('SYS reset during endpoint binding')
  result.update(uptime_before=uptime_before,uptime_after=uptime_after,status='PASS')
 except BaseException as error:result.update(status='ERROR',error=repr(error));raise
 finally:c.close();(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 return result
