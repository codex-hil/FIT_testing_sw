"""Leased repeat/quiet capture and physical IPbus error-boundary checks.
No programming, peripheral writes or synthetic TDC source.
"""
import fcntl,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT.parent/'ipbus_adc')]
from client import Client
from client_tdc import download
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
leases=[]
for name in ['atmel-ice-J41800043065','pm12-210249A73E43']:
    f=(Path.home()/'.cache'/(name+'.lock')).open('a+');fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);leases.append(f)
c=Client();report=dict(captures=[])
def bus_error(address,values=None):
    words=c.transact(0 if values is None else 1,address,values=values,allow_error=True)
    assert words[1]&15,hex(address)
try:
    expected=int((ROOT/'generated/board/build-id.txt').read_text(),16)
    assert c.read(0,3)==[0x504d1202,0x10002,expected]
    for delay in [.05,.1,.2]:
        old=c.read(0x202)[0];c.write(0x200,[1])
        for _ in range(30):
            status=c.read(0x201)[0]
            if status&5:break
            time.sleep(.001)
        if status&2:
            bus_error(0x200,[1])
            bus_error(0x20000)
        time.sleep(delay)
        status=c.read(0x201)[0]
        if status&2:c.write(0x200,[2])
        for _ in range(100):
            status=c.read(0x201)[0]
            if status&1:break
            assert not status&32,hex(status)
            time.sleep(.001)
        result=download(c);generation,status,counts,data=result
        assert generation==(old+1)&0xffffffff
        writes=c.read(4)[0]
        bus_error(0x200,[3]);bus_error(0x201,[1]);bus_error(0x2c000)
        assert c.read(4)==[writes]
        guarded=[]
        for ch,count in enumerate(counts):
            if count<4096:bus_error(0x20000+(ch<<12)+count);guarded.append(ch)
        c.close();c=Client()
        assert download(c)==result,'Frozen capture changed across connection reopen'
        report['captures'].append(dict(generation=generation,status=status,listen_seconds=delay,counts=counts,unwritten_banks_guarded=guarded))
    report['pass']=True
    print(json.dumps(report,indent=2))
finally:
    c.close();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    for lease in reversed(leases):lease.close()
