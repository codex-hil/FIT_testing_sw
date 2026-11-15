#!/usr/bin/env python3
import argparse,json,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('csv',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());rows=list(csv.DictReader(a.csv.open()));cases=[x for x in r['trials']if x.get('address')is not None and 'raw_words'in x];fig,axes=plt.subplots(3,len(cases),figsize=(12,8),squeeze=False,sharex='col',sharey=True)
for col,t in enumerate(cases):
 selected=[q for q in rows if q['label']==t['label']];full=[q for q in selected if q['valid_full']=='True'];xs=[int(q['tick'])/60118.05 for q in full];spi0=(t['stimulus_host_before']-t['arm_requests'][-1])*1000;spi1=(t['stimulus_host_after']-t['arm_requests'][-1])*1000;end=int(selected[-1]['tick'])/60118.05
 for row,(key,expected,title)in enumerate([('mclk',256,'CDCE MCLK1'),('gtref',640,'CDCE MGT_REF/2'),('sys',256,'SYS')]):
  ax=axes[row,col];ys=[int(q[key])-expected for q in full];ax.scatter(xs,ys,s=3,color='#3979a3');bad=[(x,y)for x,y in zip(xs,ys)if y];ax.scatter([q[0]for q in bad],[q[1]for q in bad],s=25,color='#c34838',zorder=3)
  ax.axhline(0,color='gray',lw=.6);ax.axvspan(spi0,spi1,color='#e8ae38',alpha=.25);ax.axvline(end,color='#a42b38',ls='--',lw=1);ax.set_ylim(-1.4,1.4);ax.set_yticks([-1,0,1]);ax.grid(axis='y',alpha=.2);ax.set_title(f"{t['label']}: {title}")
  if col==0:ax.set_ylabel('Edge-count deviation')
  if row==2:ax.set_xlabel('Nominal RX-reference time from arm (ms)')
fig.suptitle('384 RX-cycle windows: one-count endpoint uncertainty applies\nOrange: host-timed SPI interval (approximate); dashed: SYS-triggered partial final record',fontsize=11);fig.tight_layout(rect=[0,0,1,.93]);a.out.mkdir(exist_ok=True,parents=True);fig.savefig(a.out/'rx-clock-counter.png',dpi=170);fig.savefig(a.out/'rx-clock-counter.pdf')
