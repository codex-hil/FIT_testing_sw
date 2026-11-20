#!/usr/bin/env python3
"""Run independent-USER2-clock regression against corrected and legacy HDL.

A local extracted Ubuntu iverilog package is sufficient; no system install or
vendor simulator is needed. The simulation has no hardware access.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def run(source,legacy,tools,out):
    source=Path(source).resolve();legacy=Path(legacy).resolve();tools=Path(tools).resolve();out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    compiler=tools/'usr/bin/iverilog';engine=tools/'usr/bin/vvp';ivl=tools/'usr/lib/x86_64-linux-gnu/ivl'
    result={'status':'ERROR','cases':{},'compiler':str(compiler),'engine':str(engine)}
    packages=list(tools.glob('*.deb'))
    result['tool_packages']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in packages}
    try:
        for name,design,defines in [('corrected',source/'jtag_report.v',[]),('legacy',legacy,['-DLEGACY'])]:
            case=out/name;case.mkdir();exe=case/'control.vvp'
            cmd=[str(compiler),'-B',str(ivl),'-g2012','-s','control_tb',*defines,'-o',str(exe),str(design),str(source/'link_monitor.v'),str(source/'tests/control_tb.v')]
            with (case/'compile.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            with (case/'run.log').open('w') as log:rc=subprocess.run([str(engine),str(exe)],cwd=case,stdout=log,stderr=subprocess.STDOUT,timeout=15).returncode
            passed=rc==0 and (case/'control-tb-pass.txt').exists()
            result['cases'][name]={'passed':passed,'returncode':rc,'command':cmd}
        if not result['cases']['corrected']['passed']:
            raise ValueError('Corrected USER2 regression failed')
        if result['cases']['legacy']['passed'] or 'USER2 run command failed without USER1 clock' not in (out/'legacy/run.log').read_text():
            raise ValueError('Same stimulus did not reproduce the legacy clock-domain failure')
        result['status']='PASS'
    except BaseException as error:result['error']=repr(error)
    finally:(out/'simulation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2));return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','legacy','tools','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();raise SystemExit(0 if run(a.source,a.legacy,a.tools,a.out)['status']=='PASS' else 1)
