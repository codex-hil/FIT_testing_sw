#!/usr/bin/env python3
"""Leased physical-DNA/UART/network observations; read-only network probe.

Does not enable/reset the bridge, release DIO, program devices or change clocks.
"""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import sys
import uuid
import time
import board_session as b
from boundary import physical_identity
from station import load_dependencies,console


def analyze_record(record):
    result={'board_uid':record['board_uid'],'method':'station-observations-v2','acceptance':'NOT_EVALUATED',
            'network_statuses':{name:value['status'] for name,value in record.get('network',{}).items()}}
    row=record.get('network',{}).get('kasli',{}).get('reference_window')
    if row:
        before,after=row['before'],row['after'];elapsed=row['elapsed_host_s']
        if elapsed<=0:raise ValueError('Invalid host interval')
        ds=(after[0]-before[0])&0xffffffff;dr=(after[1]-before[1])&0xffffffff
        if not ds:raise ValueError('No system counter advancement')
        result['reference_window']=dict(elapsed_host_s=elapsed,sys_hz_host=ds/elapsed,
            reference_hz_host=2*dr/elapsed,reference_to_sys_ratio=2*dr/ds,
            scope='Uncalibrated host-timed observation; no nominal125MHz assumption')
        if 'reference_hz_from_nominal125MHz' in row:
            result['invalidated_legacy_fields']={'reference_hz_from_nominal125MHz':
                'INVALID_ASSUMPTION: RPH1 system clock is not established as125MHz. Use retained counters and host interval.'}
    return result


def run(cfg,root,window=0):
    if not 0<=window<=30:raise ValueError("Window outside0..30s")
    out=Path(root).resolve()/b.uid(cfg)/'setup'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-station-probe-'+uuid.uuid4().hex[:8])
    out.mkdir(parents=True,exist_ok=False)
    b.write(out/'station.json',cfg)
    sources=out/'sources';sources.mkdir()
    for name in ('station_probe.py','boundary.py','board_session.py','station.py','lease.py','identity.py'):
        shutil.copy2(b.HERE/name,sources/name)
    r=dict(board_uid=b.uid(cfg),test='station-probe',status='ERROR',started_utc=b.now(),network={})
    try:
        with b.locks(cfg):
            r['identity_before']=physical_identity(cfg,out/'identity-before')
            load_dependencies(cfg)
            from client import Client
            from pm12_console_regression import capture
            from pm12_power import require_power_good
            with console(cfg) as uart:
                r['uart']=[capture(uart,cmd) for cmd in ('@PING','RS','@PLL','@FPGA','@FPGATEST')]
                r['pgood']=require_power_good(uart,capture)
            for name,host,registers in [('kasli',cfg.get('kasli_ip','192.168.2.241'),[0,4,0x74,0xa8,0xac,0xb0,0xd0,0xe0,0x100,0x104,0x108,0x10c,0x110,0x114,0x120,0x124,0x128,0x12c,0x130,0x134,0x138,0x13c,0x144,0x150]),
                                        ('pm12','192.168.2.240',[0,4,8,20,24])]:
                result=dict(host=host,status='ERROR',registers={});r['network'][name]=result
                client=Client(host)
                try:
                    for address in registers:result['registers'][hex(address)]=client.read(address//4)[0]
                    if name=='kasli' and window:
                        before=[client.read(a//4)[0] for a in (0x10c,0x110)];start=time.monotonic()
                        time.sleep(window)
                        after=[client.read(a//4)[0] for a in (0x10c,0x110)];elapsed=time.monotonic()-start
                        ds=(after[0]-before[0])&0xffffffff;dr=(after[1]-before[1])&0xffffffff
                        if not ds:raise ValueError('Kasli system counter did not advance')
                        result['reference_window']=dict(before=before,after=after,elapsed_host_s=elapsed,
                             reference_to_sys_ratio=2*dr/ds,sys_hz_host=ds/elapsed,reference_hz_host=2*dr/elapsed,
                             scope='Uncalibrated host-timed observation; no assumed system frequency or clock reconfiguration')
                    result['status']='COMPLETE'
                except Exception as error:result['error']=repr(error)
                finally:client.close()
            r['identity_after']=physical_identity(cfg,out/'identity-after')
            r['status']='COMPLETE'
    except BaseException as error:r['error']=repr(error)
    finally:
        r['finished_utc']=b.now();b.write(out/'result.json',r);b.write(out/'files.sha256.json',b.files(out))
    print(json.dumps({'path':str(out),'status':r['status'],'network':r['network']},indent=2))
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--station',type=Path,required=True);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--window',type=float,default=0)
    a=p.parse_args();raise SystemExit(0 if run(b.read(a.station),a.root,a.window)['status']=='COMPLETE' else 1)
