#!/usr/bin/env python3
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('summary',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());s=json.loads(a.summary.read_text());g=s['groups'];names=[n for n in g if not n.startswith(('functional','WRITE'))]
f,ax=plt.subplots(figsize=(11,4))
for i,n in enumerate(names):
 v=g[n];y=100*v['sys_resets']/v['frames'];ax.bar(i,y,color='#bf4545'if n.startswith('A0')else'#337fa7'if n.startswith('B4')else'#419367');ax.text(i,y+3,f"{v['sys_resets']}/{v['frames']}",ha='center')
ax.set_xticks(range(len(names)),names,rotation=15);ax.set_ylim(0,115);ax.set_ylabel('SPI frames with observed SYS reset (%)');ax.set_title('Normal parser: HSEL-gated MISO versus continuous output enable');ax.grid(axis='y',alpha=.2);f.tight_layout();a.out.mkdir(exist_ok=True,parents=True);f.savefig(a.out/'miso-oe.png',dpi=170);f.savefig(a.out/'miso-oe.pdf')
f,axes=plt.subplots(2,1,figsize=(10,6),sharex=True)
for ax,stage in zip(axes,['A0-before','B4-oe-only']):
 t=next(x for x in r['trials']if x['stage']==stage and x['address']==0);w=t['raw_words'];ticks=[w[i]/40078.7 for i in range(0,len(w),3)]
 for bit,offset,label in [(3,4,'HSEL'),(13,2,'MISO OE'),(0,0,'SYS LOCK')]:
  values=[offset+int(bool(w[i+1]&(1<<bit)))for i in range(0,len(w),3)]
  if not(t['status']&8192)and t['count']<511:ax.step(ticks+[1000],values+[values[-1]],where='post',label=label)
  else:ax.step(ticks,values,where='post',label=label)
 ax.set_yticks([.5,2.5,4.5],['SYS LOCK','MISO OE','HSEL']);ax.set_title(stage+' (unchanged final state extended to timed freeze)'if not(t['status']&8192)and t['count']<511 else stage);ax.grid(alpha=.2)
axes[-1].set_xlabel('Time from arm (nominal ms)');axes[-1].set_xlim(0,16);f.suptitle('Sampled logical source taps; electrical pad voltage is not measured');f.tight_layout();f.savefig(a.out/'miso-oe-traces.png',dpi=170);f.savefig(a.out/'miso-oe-traces.pdf')

write_names=[n for n in g if n.startswith('WRITE')]
if write_names:
 f,ax=plt.subplots(figsize=(8,4))
 for i,n in enumerate(write_names):
  v=g[n];y=100*v['sys_resets']/v['frames'];ax.bar(i,y,color='#419367'if n=='WRITE-clamped'else'#bf4545');ax.text(i,y+3,f"{v['sys_resets']}/{v['frames']}",ha='center')
 ax.set_xticks(range(len(write_names)),write_names);ax.set_ylim(0,115);ax.set_ylabel('Write-only frames with observed SYS reset (%)');ax.set_title('Diagnostic scratch writes: active parser, no SPI readback');ax.grid(axis='y',alpha=.2);f.tight_layout();f.savefig(a.out/'spi-writes.png',dpi=170);f.savefig(a.out/'spi-writes.pdf')
