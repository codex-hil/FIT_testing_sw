from pathlib import Path
import json,struct,collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).resolve().parent;a=json.loads((p/'acquisition-attempts.json').read_text());fig,ax=plt.subplots(1,2,figsize=(11,4));out={}
for key,v in a.items():
 if not isinstance(v,dict) or 'directory' not in v:continue
 scan=p/v['directory']/'scan';d=json.loads((scan/'status.json').read_text());assert not d['pass'];rows=d['measurements'];entry={'phase_code':v['phase_code'],'status':'INCOMPLETE','completed_buffers':len(rows),'error':d['error'],'failed_buffers':[]}
 used=set()
 for b in [0,1]:
  r=[r for r in rows if r['bank']==b and r['injection_bank']==b]
  if r:ax[b].plot([x['diff_setpoint_v'] for x in r],[x['raw_mean'] for x in r],label=f"Phase{v['phase_code']}")
  for i in range(len(r)):used.add(f'mux{b}-point{i:03d}-bank{b}.bin')
 for f in scan.glob('mux*-point*-bank*.bin'):
  if f.name in used:continue
  w=struct.unpack('<4096H',f.read_bytes());r=[i for i in range(1,len(w)) if not w[i-1]&8192 and w[i]&8192];bad=[i-1 for i in r[1:] if (w[i-1]^w[i-2])&4095];entry['failed_buffers'].append({'file':f.name,'unstable_indices':bad,'xor_masks':[hex((w[i]^w[i-1])&4095) for i in bad]})
 out[key]=entry
for b in [0,1]:ax[b].set(title=f'Channel2 ADC {"AB"[b]} — incomplete attempts',xlabel='Differential input (V)',ylabel='Mean ADC code');ax[b].grid(alpha=.3);ax[b].legend()
fig.tight_layout();fig.savefig(p/'adc2-incomplete.png',dpi=160);fig.savefig(p/'adc2-incomplete.pdf');(p/'incomplete-analysis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
