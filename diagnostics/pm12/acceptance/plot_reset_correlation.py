"""Offline matched-channel R/amplitude table and scatter plots from selected receipts."""
import argparse,csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from campaign import Campaign

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 summary=Campaign(a.root).summary();a.out.mkdir(parents=True,exist_ok=False)
 rows=[]
 for ch in range(1,13):
  row=dict(channel=ch,status='NOT_MEASURED')
  record=summary['records'].get(f'integrator-reset:{ch}')
  if record:
   result=record['result'];row['status']=result['status'];row['result_id']=record['id']
   if result['status']=='PASS':
    ms={(m['name'],m.get('bank')):m['value'] for m in result['metrics']}
    for bank in 'AB':
     for leg in ['P','N']:row[f'R_{bank}_{leg}_ohm']=ms['reset_R_'+leg,bank]
     row[f'amplitude_{bank}_code']=ms[f'during_reset_{bank}_normal-before_amplitude',bank]
  rows.append(row)
 fields=['channel','status','result_id','R_A_P_ohm','R_A_N_ohm','R_B_P_ohm','R_B_N_ohm','amplitude_A_code','amplitude_B_code']
 with (a.out/'reset-correlation.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 fig,axes=plt.subplots(2,2,figsize=(9,7),layout='constrained')
 for i,bank in enumerate('AB'):
  for j,leg in enumerate(['P','N']):
   ax=axes[i,j]
   for row in rows:
    if row['status']!='PASS':continue
    x=row[f'R_{bank}_{leg}_ohm'];y=row[f'amplitude_{bank}_code']
    ax.plot(x,y,'o');ax.annotate(str(row['channel']),(x,y))
   ax.set(xlabel=f'Effective R {bank}/{leg} (nominal ohm)',ylabel=f'Normal ADC {bank} amplitude (code)');ax.grid(alpha=.3)
 fig.suptitle(summary['board_uid']+'\nMatched channel measurements; no correlation inferred from sparse coverage')
 for ext in ['png','pdf']:fig.savefig(a.out/f'reset-correlation.{ext}',dpi=160)
 (a.out/'coverage.json').write_text(json.dumps(dict(board_uid=summary['board_uid'],channels=rows),indent=2)+'\n')
if __name__=='__main__':main()
