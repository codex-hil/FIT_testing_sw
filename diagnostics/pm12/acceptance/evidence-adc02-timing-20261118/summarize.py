import json,collections,shutil,struct,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent;d=json.loads((p/'acquisition.json').read_text());assert d['complete'] and d['cleanup_returncode']==0
summary={'scope':'DIAGNOSTIC, NOT ADC qualification','board_uid':'PM12-K7-3A17A1B402212223','channel':2,'buffers':len(d['measurements']),'groups':[],'cleanup_wrapper_error':'Redundant inhibit callback ran after I2C route closed and received NACK; normal routed inhibit already completed. Independent final cleanup exit0/verified safe. Acquisition complete before callback error.'}
fig,ax=plt.subplots(1,2,figsize=(12,4));labels=[];counts=[[],[]]
for phase in d['phases']:
 for bank in [0,1]:
  rows=[r for r in d['measurements'] if r['phase']==phase and r['bank']==bank];v={'phase':phase,'bank':'AB'[bank],'buffers':len(rows),'offsets':{}}
  for offset in ['-1','0']:
   v['offsets'][offset]={'unstable_pairs':sum(r['windows'][offset]['bad_pairs'] for r in rows),'checked_pairs':sum(r['windows'][offset]['edges'] for r in rows),'buffers_with_unstable_pairs':sum(bool(r['windows'][offset]['bad_pairs']) for r in rows)}
  summary['groups'].append(v);labels.append(f'{phase}/{"AB"[bank]}');counts[0].append(v['offsets']['-1']['unstable_pairs']);counts[1].append(v['offsets']['0']['unstable_pairs'])
x=np.arange(6);ax[0].bar(x-.18,counts[0],.36,label='Pair before STR rise (old)');ax[0].bar(x+.18,counts[1],.36,label='Pair ending at STR rise');ax[0].set(xticks=x,xticklabels=labels,ylabel='Unequal consecutive data pairs',xlabel='Phase DAC code / ADC bank',title='144 buffers: 3 voltages × 8 repeats per group');ax[0].legend(fontsize=8);ax[0].grid(axis='y',alpha=.3)
h=json.loads((p/'historical-windows.json').read_text());row=next(r for n,r in h.items() if 'attempt002' in n)['-1']['examples'][0];xx=np.arange(-4,5);ax[1].step(xx,row['str'],where='post',label='STR');ax[1].step(xx,[((v>>6)&1)+1.3 for v in row['data']],where='post',label='D6 (offset vertically)');ax[1].axvspan(-2,-1,alpha=.15,color='red',label='Old comparison');ax[1].axvspan(-1,0,alpha=.15,color='green',label='Later comparison');ax[1].set(xlabel='FPGA sample relative to STR rising edge',yticks=[],title='Recorded rejected bankB word: D6 settles late');ax[1].legend(fontsize=8);ax[1].grid(alpha=.3)
fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(p/('timing-diagnostic.'+ext),dpi=160)
(p/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');shutil.copy2('/srv/codex-hil-nvme/pm12-ch02-20261118/final-safe.json',p/'final-safe.json');print(json.dumps(summary,indent=2))
