"""Leased volatile PM12 ADC/TDC smoke test; restore known ADC image on failure.

No CPLD, MCU, configuration flash or peripheral configuration writes.
Uncontrolled TDC records do not constitute a calibrated CFD phase test.
"""
import argparse,fcntl,hashlib,json,os,signal,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT.parent/'ipbus_adc'),str(ROOT.parent),'/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from client import Client,describe
from client_tdc import download
from test_board import payload
from pm12_console_regression import capture,PORT
from pm12_power import wait_power_good
import serial
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
board=ROOT/'generated/board';candidate=board/'build/pm12_ipbus_adc.bit'
golden=Path('/home/codex-hil/fit-bringup/gateware/pm12_ipbus_adc/build/pm12_ipbus_adc.bit')
assert hashlib.sha256(golden.read_bytes()).hexdigest()=='d4026ffe30109672224951a61c43d0d6b0b5272bf9b22c9ec0d4cfc5e4ea199d'
assert candidate.is_file() and (board/'build/timing.txt').is_file(), 'Build/timing qualification required'
expected=int((board/'build-id.txt').read_text(),16)
qualification=json.loads((board/'build/qualification.json').read_text())
assert qualification['timing_pass'] and int(qualification['build_id'],16)==expected
assert qualification['sha256']['pm12_ipbus_adc.bit']==hashlib.sha256(candidate.read_bytes()).hexdigest()
report=dict(started=time.time(),expected_build=hex(expected),candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest(),mcu_programmed=False,cpld_programmed=False,flash_written=False)
leases=[];owned_server=False;attempted=False;success=False;container=None
base=['docker','-H','unix:///run/user/1001/docker-vivado.sock']
for name in ['atmel-ice-J41800043065','pm12-210249A73E43']:
    f=(Path.home()/'.cache'/(name+'.lock')).open('a+')
    fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);leases.append(f)
def console():
    u=serial.Serial(port=None,baudrate=115200,timeout=.03,write_timeout=1,rtscts=True,exclusive=True)
    u.dtr=False;u.rts=True;u.port=PORT;u.open()
    try:
        u.read(4096);ready=wait_power_good(u,capture)
        rows=[capture(u,c) for c in ['@PING','RS','@FPGATEST']]
        assert rows[0]['reply']=='PONG\r\n' and 'Board power ON, OK' in rows[1]['reply'] and 'PASS 32 RESTORED' in rows[2]['reply'],rows
        return dict(power=ready,rows=rows)
    finally:u.rts=False;u.dtr=False;u.close()
def identify(build,abi):
    c=Client();c.s.settimeout(.5)
    try:
        for i in range(12):
            try:
                ids=c.read(0,3)
                assert ids==[0x504d1202,abi,build],ids
                return ids
            except TimeoutError:
                if i==11:raise
                time.sleep(.15)
    finally:c.close()
def tcl(text,label,args=None):
    path=out/(label+'.tcl');path.write_text(text)
    cmd=base+['exec','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1',container,
        'timeout','150','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/vivado','-mode','batch','-nolog','-nojournal','-notrace','-source',str(path),'-tclargs','210249A73E43','localhost:3121']+(args or ['unused','0'])
    with (out/(label+'.log')).open('w') as log:
        subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=180)
    return (out/(label+'.log')).read_text()
common=ROOT.parent/'adc/tools/common.tcl'
load_script=(ROOT.parent/'adc/tools/load_fpga.tcl').read_text().replace('source [file join [file dirname [info script]] common.tcl]','source '+str(common)).replace('0x504dad01','0x504d5a04')
def load(bit,label):
    count=payload(bit,out/(label+'.hex'))
    text=tcl(load_script,label,[str(out/(label+'.hex')),str(count)])
    assert 'LOAD_PASS' in text
def start_server():
    # Use a private server filtered to PM12; the shared host server may belong
    # to Genesys or another board. No host port mapping is needed for docker exec.
    global container,owned_server
    name='pm12-tdc-hw-'+str(os.getpid())
    cmd=base+['run','-d','--rm','--init','--name',name,'--mount','type=bind,src=/dev/bus/usb,dst=/dev/bus/usb','--mount','type=bind,src=/home/codex-hil,dst=/home/codex-hil','--mount','type=bind,src=/srv/codex-hil-data,dst=/srv/codex-hil-data','codex-vivado-runtime:ubuntu22.04','/srv/codex-hil-data/toolchains/amd/Xilinx/2025.2/Vivado/bin/hw_server','-e','set jtag-port-filter 210249A73E43']
    container=subprocess.check_output(cmd,text=True).strip();owned_server=True;time.sleep(1)

signal.signal(signal.SIGTERM,lambda *_:(_ for _ in ()).throw(KeyboardInterrupt('SIGTERM')))
try:
    print('CONSOLE_BASELINE',flush=True);report['console_before']=console()
    report['baseline_identity']=identify(0x882901f6,0x10001)
    # Preserve currently frozen observations before reconfiguration.
    c=Client()
    try:
        state=c.read(0x11)[0]
        if state&3==1:
            ident=c.read(0x12)[0];data=c.download(ident)
            (out/'baseline-adc.json').write_text(json.dumps(dict(generation=ident,status=state,data=data)))
        n,active=c.read(0x101,2)
        if not active and 0<n<=2048:
            (out/'baseline-i2c.json').write_text(json.dumps(dict(count=n,words=c.block(0x2000,n*2))))
    finally:c.close()
    start_server()
    tcl('source '+str(common)+'\npm12_open\nputs PM12_CHAIN_READY\npm12_close\nexit\n','chain-probe')
    report['container']=container
    print('PROGRAM_VOLATILE_FPGA',flush=True);attempted=True;load(candidate,'candidate-load')
    report['candidate_identity']=identify(expected,0x10002)
    c=Client()
    try:
        states=[]
        for i in range(100):
            state=c.read(0x201)[0];front=c.read(0x205)[0];states.append([state,front])
            if state&8:break
            time.sleep(.02)
        report['frontend_states']=states
        assert state&8,('TDC frontend not ready',hex(state),hex(front))
        print('TDC_ARM_STOP_DOWNLOAD',flush=True)
        c.write(0x200,[1])
        for i in range(30):
            state=c.read(0x201)[0]
            if state&1:break
            if state&4:c.write(0x200,[2]);break
            time.sleep(.001)
        for i in range(100):
            state=c.read(0x201)[0]
            if state&1:break
            assert not state&32,hex(state)
            time.sleep(.002)
        generation,state,counts,data=download(c)
        report['tdc']=dict(generation=generation,status=state,counts=counts,scope='uncontrolled input; no calibrated stimulus')
        (out/'tdc-raw.json').write_text(json.dumps(data))
        # Read the frozen capture twice and ensure neither data nor generation changes.
        assert download(c)==(generation,state,counts,data)
        print('ADC_SYNTHETIC_REGRESSION',flush=True)
        ident,state=c.acquire(pattern=True);adc=c.download(ident);describe(adc,0,True)
        report['adc']=dict(generation=ident,status=state,words=sum(map(len,adc)))
        report['read_retries']=c.read_retry_events
    finally:c.close()
    report['console_after']=console();success=True;report['pass']=True
    print('PASS TDC ARM/STOP/frozen metadata and ADC/SPI regression; candidate retained in SRAM',flush=True)
except BaseException as exc:
    report['error']=repr(exc);report['traceback']=traceback.format_exc();raise
finally:
    try:
        if attempted and not success:
            # End any still-running remote scan before starting restoration.
            # This is our private, PM12-filtered container only.
            if owned_server:
                subprocess.run(base+['stop',container],capture_output=True,timeout=15)
                owned_server=False
            start_server()
            print('RESTORE_GOLDEN_ADC_IMAGE',flush=True);load(golden,'restore-load')
            report['restored_identity']=identify(0x882901f6,0x10001)
    except BaseException as exc:
        report['restore_error']=repr(exc);raise
    finally:
        if owned_server:subprocess.run(base+['stop',container],capture_output=True,timeout=15)
        report['finished']=time.time();(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        for lease in reversed(leases):lease.close()
