"""Automatic normal-gate integrator acquisition/analysis for one board and channel.

No CPLD programming or automatic gateware fallback. Diagnostics are separate.
"""
import argparse,json,os,subprocess,sys
from pathlib import Path
from lease import ENV
HERE=Path(__file__).resolve().parent
CFD=HERE.parent/'cfd_simulator'

def make_plan(station,board,channel,out,python,analysis_python):
 cfg=json.loads(station.read_text())
 if cfg.get('board_uid')!=board:raise ValueError('Requested board UID does not match station configuration')
 route=cfg.get('channels',{}).get(str(channel),{})
 if cfg.get('routing_backend','fixed')!='fixed':raise ValueError('Routing backend not implemented; install the actual DAC/mux driver before selecting it')
 if not route.get('integrator_connected') or cfg.get('stimulated_channel')!=channel:raise ValueError('J6 route is not confirmed for this channel')
 pair=route.get('integrator_dac_channels')
 if pair is None:raise ValueError('Declare integrator_dac_channels explicitly for production')
 if len(pair)!=2 or len(set(pair))!=2 or any(type(c) is not int or not 0<=c<8 for c in pair):raise ValueError('Invalid configured DAC pair')
 return dict(board_uid=board,channel=channel,cpld_programming=False,gateware_fallback=False,dac_channels=pair,
             commands=[[str(python),str(CFD/'balance20.py'),'--afe',str(channel),'--station',str(station.resolve()),'--out',str(out/'native')],
                       [str(analysis_python),str(CFD/'plot_balance20.py'),'--run',str(out/'native'),'--out',str(out/'analysis')]])
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--board',required=True);p.add_argument('--channel',type=int,choices=range(1,13),required=True)
 p.add_argument('--station',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 p.add_argument('--analysis-python',type=Path,default=Path('/srv/codex-hil-nvme/tool-venvs/fit-measurements/bin/python'))
 p.add_argument('--plan-only',action='store_true');a=p.parse_args()
 plan=make_plan(a.station,a.board,a.channel,a.out.resolve(),sys.executable,a.analysis_python)
 if a.plan_only:print(json.dumps(plan,indent=2));return
 a.out.mkdir(parents=True,exist_ok=False);(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
 inherited=tuple(int(v) for v in json.loads(os.environ.get(ENV,'{}')).values())
 try:
  subprocess.run(plan['commands'][0],check=True,pass_fds=inherited)
  subprocess.run(plan['commands'][1],check=True)
  raw=json.loads((a.out/'native/status.json').read_text());analysis=json.loads((a.out/'analysis/summary.json').read_text())
  assert raw['complete'] and raw['board_uid']==a.board and raw['physical_channel']==a.channel and not raw['cleanup_errors']
  assert analysis['validated_buffers']==sum(len(point['captures']) for point in raw['points'])
  result=dict(status='COMPLETE',board_uid=a.board,channel=a.channel,cpld_programming=False,gateware_fallback=False,
              scope='Normal20MHz sampled-pair characterization; manufacturing tolerances are separate',fits=analysis['fits'],common_fits=analysis['common_fits'],validated_buffers=analysis['validated_buffers'])
 except BaseException as error:
  (a.out/'result.json').write_text(json.dumps(dict(status='ERROR',board_uid=a.board,channel=a.channel,error=repr(error)),indent=2)+'\n');raise
 (a.out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
