#!/usr/bin/env python3
"""Guarded PM SFP1 PHY restart, as used by the established SRAM restore recipe.

No PLL/Silabs/CDCE configuration writes, DIO release, MCU/CPLD/flash programming,
or bridge enable changes. Only PM PHY CTRL[8] is pulsed then restored to packet
mode0. The SFP0 management path is not reset.
"""
import argparse
import datetime
import json
from pathlib import Path
import shutil
import time
import uuid
import board_session as b
from boundary import physical_identity
from station import load_dependencies


def restart(cfg,out):
    load_dependencies(cfg)
    from client import Client
    client=Client(cfg.get('kasli_ip','192.168.2.241'))
    addresses=[0,4,0xb0,0xd0,0xe0,0x100,0x104,0x114,0x120,0x124,0x13c,0x144,0x150]
    r={'status':'ERROR','writes':[]}
    read=lambda address:client.read(address//4)[0]
    try:
        r['before']={hex(a):read(a) for a in addresses};before=r['before']
        expected={0:0x52504831,4:0x10002,0xb0:3,0xd0:0x49504232,0x114:0x504d4c31,0x13c:0x42524731}
        if any(before[hex(a)]!=v for a,v in expected.items()):raise ValueError('Wrong Kasli translator ABI/profile')
        if before['0x100']!=0 or before['0x120']!=1:raise ValueError('Translator not in established packet/bridge mode')
        try:
            r['writes'].append({'byte_address':'0x100','value':256})
            client.write(0x100//4,[256]);time.sleep(.05)
        finally:
            r['writes'].append({'byte_address':'0x100','value':0})
            client.write(0x100//4,[0])
        time.sleep(1)
        r['after']={hex(a):read(a) for a in addresses}
        for key in ('0xb0','0xe0','0x100','0x120','0x144','0x150'):
            if r['after'][key]!=before[key]:raise ValueError('Profile/DIO/HDMI state changed: '+key)
        r['status']='COMPLETE'
        return r
    except BaseException as error:r['error']=repr(error);raise
    finally:client.close();b.write(out/'phy-restart.json',r)


def run(cfg,root):
    out=Path(root).resolve()/b.uid(cfg)/'setup'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-link-recovery-'+uuid.uuid4().hex[:8]);out.mkdir(parents=True)
    b.write(out/'station.json',cfg)
    shutil.copy2(Path(__file__),out/Path(__file__).name)
    r=dict(board_uid=b.uid(cfg),test='link-recovery',status='ERROR',started_utc=b.now(),clock_configuration_changes=False)
    try:
        with b.locks(cfg):
            r['identity_before']=physical_identity(cfg,out/'identity-before')
            r['phy_restart']=restart(cfg,out)
            r['identity_after']=b.identity(cfg,out/'identity-after')['identity']
            r['status']='PASS'
    except BaseException as error:r['error']=repr(error)
    finally:r['finished_utc']=b.now();b.write(out/'result.json',r);b.write(out/'files.sha256.json',b.files(out))
    print(json.dumps({'path':str(out),'status':r['status'],'error':r.get('error')},indent=2))
    return r


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--station',type=Path,required=True);p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if run(b.read(a.station),a.root)['status']=='PASS' else 1)
