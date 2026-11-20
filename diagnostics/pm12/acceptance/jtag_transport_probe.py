#!/usr/bin/env python3
"""Measure TAP BYPASS latency and observe integrated reports; no device programming."""
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
import subprocess
import uuid
import board_session as b
from boundary import physical_identity
from station import jtag_command


def decode(text):
    rows=[]
    for source,reply in re.findall(r'^BYPASS ([a-fA-F0-9]+) ([a-fA-F0-9]+)$',text,re.M):
        x,y=int(source,16),int(reply,16)
        candidates=[n for n in range(1,49) if (x<<n)&((1<<64)-1)==y]
        rows.append(dict(tdi=source,tdo=reply,compatible_delays=candidates))
    if len(rows)!=5:raise ValueError('Incomplete BYPASS sweep')
    common=set.intersection(*(set(r['compatible_delays']) for r in rows))
    reports={name:int(value,16) for name,value in re.findall(r'^REPORT_(BEFORE|AFTER) ([0-9a-fA-F]+)$',text,re.M)}
    states={}
    for name,value in reports.items():
        if value&0xffffffff!=0x504d5a04 or (value>>208)&0xffffffff!=0x504d4442:
            states[name]={'supported_integrated_report':False,'raw_hex':f'{value:x}'}
            continue
        states[name]=dict(supported_integrated_report=True,flags=(value>>240)&0xffffffff,
                          rx_frames=(value>>272)&0xffffffff,tx_frames=(value>>304)&0xffffffff,
                          rx_bytes=(value>>336)&0xffffffff,tx_bytes=(value>>368)&0xffffffff,
                          rx_errors=(value>>400)&65535,ipbus_strobes=(value>>432)&0xffffffff,
                          net_tick=(value>>464)&0xffffffff,command=(value>>496)&65535)
    rates={}
    timestamps={name:int(value) for name,value in re.findall(r'^REPORT_TIME_(BEFORE|AFTER) ([0-9]+)$',text,re.M)}
    if all(name in timestamps and states.get(name,{}).get('supported_integrated_report') for name in ('BEFORE','AFTER')):
        elapsed=(timestamps['AFTER']-timestamps['BEFORE'])/1000
        if elapsed<=0:raise ValueError('Invalid report time interval')
        sys_counts=[(reports[name]>>32)&0xffffffff for name in ('BEFORE','AFTER')]
        rates=dict(elapsed_host_s=elapsed,sys_hz=((sys_counts[1]-sys_counts[0])&0xffffffff)/elapsed,
                   net_hz=((states['AFTER']['net_tick']-states['BEFORE']['net_tick'])&0xffffffff)/elapsed,
                   scope='Uncalibrated host/JTAG-timed observation; no jitter/clock acceptance')
    return dict(host_timed_rates=rates,bypass_rows=rows,measured_delay_candidates=sorted(common),expected_delay=13,
                bypass_pass=common=={13},integrated_states=states)


def run(cfg,root,window=1):
    if not 1<=window<=30:raise ValueError("Window outside1..30s")
    out=Path(root).resolve()/b.uid(cfg)/'setup'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-jtag-transport-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    b.write(out/'station.json',cfg)
    shutil.copy2(Path(__file__),out/Path(__file__).name);shutil.copy2(b.HERE/'probe_bypass.tcl',out/'probe_bypass.tcl')
    r=dict(board_uid=b.uid(cfg),test='jtag-transport-probe',status='ERROR',started_utc=b.now())
    try:
        with b.locks(cfg):
            r['identity_before']=physical_identity(cfg,out/'identity-before')
            local=dict(cfg,jtag_workspace=str(out/'jtag-work'))
            with jtag_command(local,out) as prefix:
                command=prefix+['-mode','batch','-nolog','-nojournal','-notrace','-source',str(b.HERE/'probe_bypass.tcl'),'-tclargs',cfg['jtag_cable'],cfg.get('hw_server','localhost:3121'),str(out),str(int(window*1000))]
                r['command']=command
                with (out/'probe.log').open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
            r['analysis']=decode((out/'probe.log').read_text())
            r['identity_after']=physical_identity(cfg,out/'identity-after')
            r['status']='COMPLETE'
    except BaseException as error:r['error']=repr(error)
    finally:
        r['finished_utc']=b.now();b.write(out/'result.json',r);b.write(out/'files.sha256.json',b.files(out))
    print(json.dumps({'path':str(out),**r},indent=2))
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--station',type=Path,required=True);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--window',type=float,default=1)
    a=p.parse_args();raise SystemExit(0 if run(b.read(a.station),a.root,a.window)['status']=='COMPLETE' else 1)
