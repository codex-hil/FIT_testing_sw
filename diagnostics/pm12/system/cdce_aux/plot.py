import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=argparse.ArgumentParser();p.add_argument('summary',type=Path);p.add_argument('out',type=Path);a=p.parse_args();s=json.loads(a.summary.read_text());f,ax=plt.subplots(figsize=(8,4))
for i,(name,label,color)in enumerate([('jtag_primary','PRIMARY / HDMI','#bc4545'),('jtag_aux','AUX / local crystal','#3c9772')]):
 d=s['groups'][name];y=100*d['counter_discontinuities']/d['frames'];ax.bar(i,y,color=color);ax.text(i,y+3,f"{d['counter_discontinuities']}/{d['frames']}",ha='center');ax.text(i,8,f"SYS ≈ {d['approximate_sys_hz']/1e6:.3f} MHz",ha='center',color='white'if y>20 else'black')
ax.set_xticks([0,1],['PRIMARY / HDMI','AUX / local crystal']);ax.set_ylim(0,105);ax.set_ylabel('SPI reads with SYS counter restart (%)');ax.set_title('CDCE reference selection: JTAG counter observations');ax.grid(axis='y',alpha=.2);f.tight_layout();a.out.mkdir(exist_ok=True,parents=True);f.savefig(a.out/'cdce-aux.png',dpi=170);f.savefig(a.out/'cdce-aux.pdf')
