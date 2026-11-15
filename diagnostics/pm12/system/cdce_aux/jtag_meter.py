"""Read-only USER1 counter measurements, independent of Ethernet writes."""
import subprocess,time,json
from pathlib import Path
class Meter:
 def __init__(self,prefix,cfg,path):
  self.path=Path(path);self.path.mkdir();self.seq=0;self.log=(self.path/'vivado.log').open('w')
  self.proc=subprocess.Popen(prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(Path(__file__).with_name('meter.tcl')),'-tclargs',cfg['jtag_cable'],cfg['hw_server'],str(self.path),'0'],stdout=self.log,stderr=subprocess.STDOUT,start_new_session=True)
  end=time.monotonic()+100
  while not(self.path/'ready').exists():
   if self.proc.poll()is not None or time.monotonic()>end:raise RuntimeError('JTAG meter start')
   time.sleep(.1)
 def read(self):
  self.seq+=1;t0=time.monotonic();tmp=self.path/'request.tmp';tmp.write_text(str(self.seq));tmp.replace(self.path/'request');end=time.monotonic()+8
  while True:
   if(self.path/'response').exists():
    fields=(self.path/'response').read_text().split()
    if int(fields[0])==self.seq:break
   if self.proc.poll()is not None or time.monotonic()>end:raise TimeoutError('JTAG meter read')
   time.sleep(.002)
  t1=time.monotonic();v=int(fields[1],16)
  return dict(seq=self.seq,report_hex=fields[1],tick=(v>>32)&0xffffffff,clock_flags=(v>>240)&0xfff,host_before=t0,host_after=t1,jtag_before_us=int(fields[2]),jtag_after_us=int(fields[3]))
 def close(self):
  (self.path/'stop').touch()
  try:self.proc.wait(timeout=20)
  finally:self.log.close()
def cases(prefix,cfg,path,adapter,repetitions):
 meter=Meter(prefix,cfg,path);rows=[]
 try:
  first=meter.read();time.sleep(2);second=meter.read();dt=((second['jtag_before_us']+second['jtag_after_us'])-(first['jtag_before_us']+first['jtag_after_us']))/2e6
  rate=dict(before=first,after=second,nominal_sys_hz=((second['tick']-first['tick'])&0xffffffff)/dt)
  for rep in range(repetitions):
   for address in [0,1,2]:
    time.sleep(.2);before=meter.read();signature=adapter.transfer(True,address);time.sleep(.06);after=meter.read()
    dt=((after['jtag_before_us']+after['jtag_after_us'])-(before['jtag_before_us']+before['jtag_after_us']))/2e6
    delta=(after['tick']-before['tick'])&0xffffffff;discontinuous=not(20e6*dt<delta<60e6*dt)
    row=dict(rep=rep,address=address,signature=signature,signature_ok=signature==[0x4844,0x4d49,1][address],before=before,after=after,elapsed=dt,delta=delta,sys_counter_discontinuity=discontinuous)
    rows.append(row);(Path(path)/'result.json').write_text(json.dumps(dict(rate=rate,cases=rows),indent=2)+'\n');print(Path(path).name,rep,address,'DISCONTINUITY'if discontinuous else'continuous',flush=True)
 finally:meter.close()
 return dict(rate=rate,cases=rows)
