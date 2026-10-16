"""Acquire or download PM12 raw TDC banks through IPbus, under both board leases."""
from pathlib import Path
import argparse,fcntl,json,struct,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT.parent/'ipbus_adc')]
from client import Client
from client_tdc import download
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--host',default='192.168.2.240');p.add_argument('--out',type=Path,required=True)
p.add_argument('--acquire',action='store_true',help='arm a new capture; otherwise download the frozen capture')
p.add_argument('--duration',type=float,default=.2,help='seconds before partial STOP, <=0.5 to leave watchdog margin')
a=p.parse_args()
if not 0<a.duration<=.5:p.error('duration must be >0 and <=0.5 seconds')
if a.out.exists():p.error('output directory already exists')
leases=[]
for name in ['atmel-ice-J41800043065','pm12-210249A73E43']:
    f=(Path.home()/'.cache'/(name+'.lock')).open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);leases.append(f)
c=Client(a.host)
try:
    if c.read(0)!=[0x504d1202] or c.read(1)!=[0x10002]:raise RuntimeError('TDC ABI mismatch')
    if a.acquire:
        c.write(0x200,[1]);deadline=time.monotonic()+.05
        while True:
            status=c.read(0x201)[0]
            if status&5:break  # all-started or already complete
            if status&32 or time.monotonic()>deadline:raise RuntimeError('TDC start failed: '+hex(status))
        print('ARM_STARTED',flush=True)
        time.sleep(a.duration)
        if c.read(0x201)[0]&2:c.write(0x200,[2])
        deadline=time.monotonic()+.1
        while not c.read(0x201)[0]&1:
            if time.monotonic()>deadline:raise RuntimeError('TDC stop timeout')
            time.sleep(.001)
    generation,status,counts,data=download(c)
    a.out.mkdir(parents=True,exist_ok=False)
    for ch,words in enumerate(data):
        (a.out/('tdc%02d.bin'%(ch+1))).write_bytes(struct.pack('<%dH'%len(words),*words))
    report=dict(generation=generation,status=status,counts=counts,acquired=a.acquire,
                format='little-endian u16; raw bits12:0, fine=raw&127,coarse=(raw>>7)&63; no time calibration',read_retries=c.read_retry_events)
    (a.out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
finally:
    try:
        # An interrupted download must not leave a new capture running.
        if a.acquire:
            status=c.read(0x201)[0]
            if status&6==6:c.write(0x200,[2])
    finally:
        c.close()
        for lease in reversed(leases):lease.close()
