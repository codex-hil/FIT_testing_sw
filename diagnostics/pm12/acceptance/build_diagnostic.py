#!/usr/bin/env python3
"""Snapshot, simulate and build the PM12 SRAM diagnostic on Dell; fetch explicitly.

No hardware access. Uses the shared Dell Vivado slot launcher, four threads.
"""
import argparse
import datetime
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import uuid
import sys
import board_session as b


def build(root):
    job=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
    out=Path(root).resolve()/job;out.mkdir(parents=True)
    source=out/'source';shutil.copytree(b.PM/'gateware',source,ignore=shutil.ignore_patterns('build','__pycache__','.Xil'))
    shutil.copy2(Path(__file__),out/'build_diagnostic.py')
    legacy=subprocess.check_output(['git','show','c251c40e3fbca9f3449e2c7b10743503909577d4:diagnostics/pm12/gateware/jtag_report.v'],cwd=b.HERE)
    (source/'legacy_jtag_report.v.reference').write_bytes(legacy)
    remote='/srv/nvme-fast-1/vivado-work/pm12-control-'+job
    host='codex-hil@192.168.2.7';ssh=['ssh','-i','/home/codex-hil/.ssh/dell_build','-o','IdentitiesOnly=yes','-o','BatchMode=yes']
    shell=lambda command:ssh+[host,command]
    rsync=['rsync','-a','-e',shlex.join(ssh)]
    record=dict(started_utc=b.now(),status='ERROR',source_hashes=b.files(source),remote=remote,
                git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=b.HERE,text=True).strip())
    (out/'sources.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=b.HERE))
    try:
        simulation=[sys.executable,str(source/'tests/run_control.py'),'--source',str(source),'--legacy',str(source/'legacy_jtag_report.v.reference'),'--tools','/srv/codex-hil-nvme/pm12-simulation-tools/iverilog-12.0','--out',str(out/'simulation')]
        with (out/'simulation-console.log').open('w') as log:subprocess.run(simulation,stdout=log,stderr=subprocess.STDOUT,check=True)
        if subprocess.check_output(shell('hostname'),text=True).strip()!='codex-hil-Precision-5820-Tower-X-Series':
            raise ValueError('Wrong remote host')
        subprocess.run(shell('mkdir -p '+shlex.quote(remote+'/source')),check=True)
        subprocess.run(rsync+[str(source)+'/',host+':'+remote+'/source/'],check=True)
        # Run the corrected independent-USER2 simulation and implementation.
        command='cd '+shlex.quote(remote)+' && /home/codex-hil/.local/bin/dell-build-slot -- /home/codex-hil/.local/bin/vivado -mode batch -nojournal -log vivado.log -source source/build.tcl'
        record['command']=command;b.write(out/'build.json',record)
        with (out/'console.log').open('w') as log:subprocess.run(shell(command),stdout=log,stderr=subprocess.STDOUT,check=True)
        subprocess.run(rsync+[host+':'+remote+'/source/build/',str(out/'artifacts')+'/'],check=True)
        subprocess.run(rsync+[host+':'+remote+'/vivado.log',str(out/'vivado.log')],check=True)
        bit=out/'artifacts/pm12_link_diag.bit'
        record.update(status='PASS',bitstream=str(bit),bit_sha256=b.sha(bit),simulation='PASS',legacy_regression='REPRODUCED')
    except BaseException as error:record.update(status='ERROR',error=repr(error))
    finally:
        record['finished_utc']=b.now();b.write(out/'build.json',record);b.write(out/'files.sha256.json',b.files(out))
    print(json.dumps({'path':str(out),**record},indent=2))
    return record


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    raise SystemExit(0 if build(a.root)['status']=='PASS' else 1)
