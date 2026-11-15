#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('summary',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());s=json.loads(a.summary.read_text());g=s['groups'];names=['QUIET-before','RAW-control','QUIET-return','READ-m0','READ-m4'];names=[n for n in names if n in g]
f,ax=plt.subplots(figsize=(10,4))
for i,n in enumerate(names):
 v=g[n];y=100*v['sys_resets']/v['frames'];ax.bar(i,y,color='#419367'if n.startswith('QUIET')else'#bf4545'if n=='RAW-control'else'#387ca6');ax.text(i,y+3,f"{v['sys_resets']}/{v['frames']}",ha='center')
ax.set_xticks(range(len(names)),names);ax.set_ylim(0,115);ax.set_ylabel('Frames with observed SYS reset (%)');ax.set_title('Write MISO echo disabled by default; same-image reversal');ax.grid(axis='y',alpha=.2);f.tight_layout();a.out.mkdir(exist_ok=True,parents=True);f.savefig(a.out/'write-quiet.png',dpi=170);f.savefig(a.out/'write-quiet.pdf')
