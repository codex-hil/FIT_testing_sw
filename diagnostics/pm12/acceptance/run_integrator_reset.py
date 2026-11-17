"""Standard per-channel reset characterization: acquire, analyze, validate, register."""
import argparse,json,subprocess,sys
from pathlib import Path
from campaign import Campaign,read
HERE=Path(__file__).resolve().parent
CFD=HERE.parent/'cfd_simulator'

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--root',type=Path,required=True);p.add_argument('--batch',required=True)
 p.add_argument('--channel',type=int,choices=range(1,13),required=True)
 p.add_argument('--vectors-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--analysis-python',type=Path,default=Path('/srv/codex-hil-nvme/tool-venvs/fit-measurements/bin/python'))
 a=p.parse_args();c=Campaign(a.root)
 with c.locked():
  directory,b=c.batch(a.batch);c.check_identity(directory,b)
  if not any(t['id']=='integrator-reset' for t in c.protocol['tests']):raise ValueError('Initialize a new protocol revision containing integrator-reset; do not edit sealed protocol.json')
  if a.channel not in b['channels']:raise ValueError('Channel not fitted')
  station=directory/'station.json';cfg=read(station);route=cfg['channels'][str(a.channel)]
  if not route.get('integrator_connected') or cfg.get('stimulated_channel')!=a.channel:raise ValueError('Confirm the current J6 USB route in station.json')
 a.out.mkdir(parents=True,exist_ok=False)
 for bank in 'AB':
  subprocess.run([sys.executable,str(CFD/'reset_rdson.py'),'--afe',str(a.channel),'--bank',bank,'--out',str(a.out/'run'/bank),'--build-dir',str(a.vectors_root/bank/f'ch{a.channel:02d}'),'--station',str(station)],check=True)
  subprocess.run([str(a.analysis_python),str(CFD/'plot_reset_rdson.py'),'--root',str(a.out/'run'/bank)],check=True)
 from campaign_reset_adapter import normalize
 result=normalize(a.out/'run',a.out/'receipt',a.root,a.batch)
 record=c.record(a.batch,a.out/'receipt')
 print(json.dumps(dict(status=result['status'],record=record),indent=2))
if __name__=='__main__':main()
