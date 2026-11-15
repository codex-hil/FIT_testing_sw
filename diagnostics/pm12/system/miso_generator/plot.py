#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('summary',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());s=json.loads(a.summary.read_text());g=s['groups'];names=list(g)
f,ax=plt.subplots(2,1,figsize=(10,7))
for i,n in enumerate(names):
 v=g[n];y=100*v['sys_resets']/v['windows'];ax[0].bar(i,y,color='#ba4545'if n.startswith('SPI')else'#2d7eae'if n.startswith('PULSE')else'#59975b');ax[0].text(i,y+3,f"{v['sys_resets']}/{v['windows']}",ha='center')
ax[0].set_xticks(range(len(names)),names);ax[0].set_ylim(0,115);ax[0].set_ylabel('Windows with observed SYS reset (%)');ax[0].set_title('Standalone MISO activity versus static levels and normal SPI')
t=next(x for x in r['trials']if x['stage']=='PULSE1'and x['miso_edges']>3);w=t['raw_words'];ticks=[w[i]/40078.7 for i in range(0,len(w),3)];values=[int(bool(w[i+1]&64))for i in range(0,len(w),3)];ax[1].step(ticks,values,where='post');ax[1].set_xlim(0,5);ax[1].set_ylim(-.2,1.2);ax[1].set_yticks([0,1]);ax[1].set_ylabel('Sampled logical MISO');ax[1].set_xlabel('Time from acquisition arm (nominal ms)');ax[1].set_title('First square-wave window; logical source, not electrical pad voltage')
for x in ax:x.grid(axis='y',alpha=.2)
f.tight_layout();a.out.mkdir(parents=True,exist_ok=True);f.savefig(a.out/'miso-generator.png',dpi=170);f.savefig(a.out/'miso-generator.pdf')
