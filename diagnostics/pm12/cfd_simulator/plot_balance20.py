"""Offline raw revalidation and plots of the fine20MHz balance diagnostic."""
import argparse,csv,hashlib,json,shutil,statistics,struct,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'ipbus_adc'))
from adc_decode import decode

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 r=json.loads((a.run/'status.json').read_text());assert r['complete'] and not r.get('error') and not r['cleanup_errors']
 a.out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,a.out/'executed-analysis.py')
 rows=[];hashes={};valid=0
 for point in r['points']:
  for bank in [0,1]:
   differences=[]
   for cap in point['captures']:
    if cap['bank']!=bank:continue
    path=a.run/cap['file'];raw=path.read_bytes();hashes[cap['file']]=hashlib.sha256(raw).hexdigest()
    x,_=decode(struct.unpack('<4096H',raw),bank);assert cap['valid'] and all(1<v<4094 for v in x)
    n=len(x)//4*4;means=[statistics.mean(x[k:n:4]) for k in range(4)];ref=r['references'][str(bank)]
    scores=[sum((means[(i+s)%4]-ref[i])**2 for i in range(4)) for s in range(4)];order=sorted(range(4),key=lambda i:scores[i]);start=order[0]
    assert scores[order[1]]-scores[order[0]]>=100
    change=statistics.mean(x[i+1]-x[i] for i in range(start,n-1,4))
    assert start==cap['pair']['pair_start_mod4'] and abs(change-cap['pair']['mean_change_code'])<1e-12
    differences.append(change);valid+=1
   assert len(differences)==3
   rows.append(dict(point_index=point['index'],stage=point['stage'],target_bank=point['target_bank'],bank='AB'[bank],delta_V=point['delta_V'],common_translation_V=point['common_translation_V'],positive_setpoint_V=point['setpoints_V'][0],negative_setpoint_V=point['setpoints_V'][1],mean_change_code=statistics.mean(differences),repeat_std_code=statistics.pstdev(differences)))
 fig,axes=plt.subplots(2,2,figsize=(11,8),layout='constrained');fits={};common_fits={};returns={}
 for bank,label in enumerate('AB'):
  selected=[v for v in rows if v['stage']=='fine' and v['target_bank']==bank and v['bank']==label]
  x=np.array([v['delta_V'] for v in selected]);y=np.array([v['mean_change_code'] for v in selected]);slope,intercept=np.polyfit(x,y,1);root=-intercept/slope
  assert len(selected)==21 and min(y)<0<max(y) and min(x)<=root<=max(x)
  fits[label]=dict(sampled_pair_root_V=float(root),adjacent_interpolated_root_V=r['fine_roots'][str(bank)],slope_code_per_commanded_V=float(slope),residual_rms_code=float(np.sqrt(np.mean((y-slope*x-intercept)**2))))
  ax=axes[0,bank];ax.errorbar(x*1000,y,yerr=[v['repeat_std_code'] for v in selected],fmt='o',ms=3,capsize=2,label='Three independent buffers/point')
  ax.plot(x*1000,slope*x+intercept,label=f'Local fit zero {root*1000:.3f} mV');ax.axhline(0,color='gray',ls='--')
  ax.set(title=f'ADC {label}: 100 uV single-leg steps',xlabel='Commanded relative delta (mV)',ylabel='Second minus first integration sample (code)');ax.legend(fontsize=8);ax.grid(alpha=.25)
  common=[v for v in rows if v['stage']=='common' and v['target_bank']==bank and v['bank']==label]
  cx=np.array([v['common_translation_V'] for v in common]);cy=np.array([v['mean_change_code'] for v in common]);cs,ci=np.polyfit(cx,cy,1);common_fits[label]=dict(slope_code_per_common_V=float(cs),delta_V=common[0]['delta_V'])
  axes[1,0].errorbar(cx*1000,cy,yerr=[v['repeat_std_code'] for v in common],fmt='o-',capsize=2,label=f'{label}, delta={common[0]["delta_V"]*1000:g}mV')
  controls=[v for v in rows if v['stage']=='return' and v['target_bank']==bank and v['bank']==label];returns[label]=controls
  point=next(v for v in r['points'] if v['stage']=='return' and v['target_bank']==bank)
  cap=next(v for v in point['captures'] if v['bank']==bank);w=cap['pair']['template']
  axes[1,1].plot(range(4),w,'o-',label=f'{label}, delta={point["delta_V"]*1000:g}mV')
 axes[1,0].axhline(0,color='gray',ls='--');axes[1,0].set(title='Translate both input setpoints, delta fixed',xlabel='Common translation (mV)',ylabel='Integration-pair change (code)');axes[1,0].legend();axes[1,0].grid(alpha=.25)
 axes[1,1].set(title='Independent return: four sample means',xlabel='Registered sample position (0/1 integration pair)',ylabel='ADC code');axes[1,1].set_xticks(range(4));axes[1,1].legend();axes[1,1].grid(alpha=.25)
 dac_channels=r.get('dac_channels',[2,3])
 fig.suptitle(f'PM{r["physical_channel"]}: fine balance at normal20MHz gates, phase DAC32768\nDAC{dac_channels[0]}=1.024V+delta+c; DAC{dac_channels[1]}=2.048V+c. Sampled-pair zero, not a calibrated DC-current null.')
 for ext in ['png','pdf']:fig.savefig(a.out/f'balance20.{ext}',dpi=160)
 with (a.out/'measurements.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 result=dict(validated_buffers=valid,fits=fits,common_fits=common_fits,returns=returns,raw_sha256=hashes)
 (a.out/'summary.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='raw_sha256'},indent=2))
if __name__=='__main__':main()
