#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('summary',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.summary.read_text());g=r['groups'];names=list(g)
f,ax=plt.subplots(figsize=(9,4))
for i,n in enumerate(names):
 v=g[n];value=100*v['resets']/v['frames'];ax.bar(i,value,color='#327eac'if n.startswith('B4')else'#bb4444');ax.text(i,value+3,f"{v['resets']}/{v['frames']}",ha='center')
ax.set_xticks(range(len(names)),names,rotation=12);ax.set_ylim(0,115);ax.set_ylabel('Frames with observed SYS reset (%)');ax.set_title('PM12 MISO drive: normal SPI, no parser reset or output clamp');ax.grid(axis='y',alpha=.2);f.tight_layout();a.out.mkdir(parents=True,exist_ok=True);f.savefig(a.out/'miso-drive.png',dpi=170);f.savefig(a.out/'miso-drive.pdf')
