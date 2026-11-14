#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
p=argparse.ArgumentParser();p.add_argument('--result',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True);r=json.loads(a.result.read_text());chosen=r['chosen'];reset_only=any(x['stage']=='R1-reset-only'for x in r['trials'])
if reset_only:
 stages=['baseline','R1-reset-only','A1-release','C-clamp-only','A2-release','R2-reset-only','A3-release'];labels=['A: before','R1: reset','A1: release','C: clamp','A2: release','R2: reset','A3: release']
else:
 stages=['baseline','C1-clamp-only','B1-reset-clamped','C2-clamp-only','B2-reset-clamped','C3-clamp-only','A-return-normal'];labels=['A: before','C1','B1','C2','B2','C3','A: return']
groups=[]
for stage in stages:
 if stage=='baseline':rows=[x for x in r['trials']if x['stage']=='search'and x['address']==chosen['address']and x['divider']==chosen['divider']]
 else:rows=[x for x in r['trials']if x['stage']==stage]
 groups.append(rows)
colors=['#c43d3d'if g[0]['mode']==0 else'#367ab2'if g[0]['mode']==2 else'#33966d'for g in groups]
fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True)
for i,rows in enumerate(groups):
 count=sum(x['sys_reset_observed']for x in rows);axes[0].bar(i,100*count/len(rows),color=colors[i],width=.65);axes[0].plot(i,0,'o',color=colors[i]);axes[0].text(i,100*count/len(rows)+4,f'{count}/{len(rows)}',ha='center')
 maxcounts=[max((w[j+1]>>16)&31 for j in range(0,len(w),3))for w in [x['raw_words']for x in rows]]
 jitter=[(j-(len(rows)-1)/2)*.05 for j in range(len(rows))];axes[1].scatter([i+x for x in jitter],maxcounts,color=colors[i],s=38)
axes[0].set_ylim(-5,118);axes[0].set_ylabel('Frames with observed SYS reset (%)');axes[0].set_title(f"Within-image SPI experiment: divider {chosen['divider']}, diagnostic read {chosen['address']}")
axes[0].legend(handles=[Patch(color='#c43d3d',label='A: active parser, normal MISO'),Patch(color='#367ab2',label='C: active parser, MISO=0'),Patch(color='#33966d',label='R: reset only; clamp bit unchanged'if reset_only else'B: parser held reset, MISO=0')],loc='upper center',bbox_to_anchor=(.5,-.03),ncol=1,frameon=False)
axes[1].set_ylim(-2,34);axes[1].set_yticks([0,16,31]);axes[1].set_ylabel('Maximum sampled SPI bit count');axes[1].set_xticks(range(len(labels)),labels);axes[1].set_xlabel('Acquisition order; no FPGA reload or clock/divider change between stages');axes[1].set_title('Direct state probe: parser active in A/C; held in R/B')
for ax in axes:ax.grid(axis='y',alpha=.2)
fig.tight_layout(h_pad=6);fig.savefig(a.out/'spi-ab-result.png',dpi=160);fig.savefig(a.out/'spi-ab-result.pdf')
