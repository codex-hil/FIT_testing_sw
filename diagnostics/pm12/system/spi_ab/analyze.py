#!/usr/bin/env python3
"""Independent validation of actual state, control flags and reset captures."""
import argparse,json,collections,csv
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--result',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(exist_ok=True,parents=True);r=json.loads(a.result.read_text());groups=collections.defaultdict(lambda:dict(frames=0,sys_resets=0,lock_triggers=0,bad_signatures=0));events=[];cases=[];contexts=[]
for t in r['trials']:
 if 'raw_words'not in t:continue
 words=t['raw_words'];assert len(words)==t['count']*3;assert t['mode_after']==0x53520000|t['mode'];es=[]
 for i in range(0,len(words),3):
  tick,w,d=words[i:i+3];e=dict(label=t['label'],stage=t['stage'],mode=t['mode'],divider=t['divider'],tick=tick,sys_reset=(w>>2)&1,lock=w&1,cap_lock=(w>>1)&1,gt_lock=(w>>10)&1,sel=(w>>3)&1,sck=(w>>4)&1,mosi=(w>>5)&1,miso=(w>>6)&1,mmcm_rst=(w>>8)&1,powerdown=(w>>9)&1,hold=(w>>11)&1,clamp=(w>>12)&1,bit_count=(w>>16)&31,reading=(w>>21)&1,address=(w>>22)&255,stable=bool(w>>31),shift=d&65535)
  assert not es or tick>es[-1]['tick'];es.append(e);events.append(e)
 valid=[e for e in es if e['tick']>8]
 if t['address']is not None:assert valid
 assert all(e['hold']==(t['mode']&1)and e['clamp']==((t['mode']>>1)&1)for e in valid)
 if t['mode']&1:assert all(e['bit_count']==0 and e['reading']==0 for e in valid)
 if t['mode']&2 or t['mode']==1:assert all(e['miso']==0 for e in valid)
 reset=any(e['sys_reset']for e in valid);assert reset==t['sys_reset_observed']
 last_fall=None
 for x,y in zip(es,es[1:]):
  if x['sel']and not y['sel']:last_fall=y['tick']
  if y['tick']>8 and y['sys_reset']and not x['sys_reset']:
   contexts.append(dict(**y,since_sel_low_nominal_us=(y['tick']-last_fall)/40078700*1e6 if last_fall is not None else None))
 edges=sum(x['sck']!=y['sck']for x,y in zip(es,es[1:]))
 if t['address']is not None:
  if not t['trigger']:assert edges==64
  if not(t['mode']&1):assert any(e['bit_count']>0 for e in valid)
  g=groups[t['stage']];g['frames']+=1;g['sys_resets']+=int(reset);g['lock_triggers']+=int(t['trigger']);g['bad_signatures']+=int(not t['signature_ok'])
 cases.append(dict(label=t['label'],stage=t['stage'],mode=t['mode'],sck_edges=edges,sys_reset=reset,events=len(es)))
g=dict(groups);reset_only={k:v for k,v in g.items()if'reset-only'in k};c=[v for k,v in g.items()if'clamp-only'in k];b=[v for k,v in g.items()if'reset-clamped'in k or'reset-only'in k];returns={k:v for k,v in g.items()if k.startswith('A')};returned=sum(v['sys_resets']for v in returns.values())
reset_reversal=bool(r.get('baseline_reproduced')and reset_only and all(v['sys_resets']==0 for v in reset_only.values())and returns and all(v['sys_resets']>0 for v in returns.values()))
if reset_reversal and c and not any(x['sys_resets']for x in c):conclusion='Reset-only suppressed both R blocks and all A releases reproduced. MISO clamp-only also suppresses; reset is sufficient in this setup but not necessary, and a parser-specific cause is not established.'
elif not r.get('baseline_reproduced'):conclusion='Baseline did not reproduce; no suppression claim.'
elif any(x['sys_resets']for x in b):conclusion='SYS resets reproduced with parser held in reset and MISO clamped0; parser state transitions are not necessary.'
elif c and all(x['sys_resets']for x in c)and returned:conclusion='Repeated clamp-only positive controls, zero held resets and positive normal return support suppression by holding parser reset under matched logical MISO output.'
elif c and not any(x['sys_resets']for x in c)and returned:conclusion='MISO clamp alone suppressed observed resets. Reset-only may also suppress via its constant MISO consequence; a parser-specific cause is not established.'
else:conclusion='Baseline positive, but control pattern does not establish reset-specific suppression; inspect stage counts.'
s=dict(captured_windows=len(cases),stimulated_frames=sum(t['address']is not None for t in r['trials']if'raw_words'in t),completed=r.get('completed'),restored=r.get('restored'),baseline_reproduced=r.get('baseline_reproduced'),chosen=r.get('chosen'),groups=g,cases=cases,control_flags_verified=True,reset_only_reversal_observed=reset_reversal,adc_validated=r.get('adc_validated'),conclusion=conclusion,limitations='Logical source MISO matching, not continuous electrical pad observation; common watch/reference stop invisible; sampled multibit SPI fields not atomic.')
(a.out/'reset-context.json').write_text(json.dumps(contexts,indent=2)+'\n')
(a.out/'summary.json').write_text(json.dumps(s,indent=2)+'\n')
with(a.out/'events.csv').open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=list(events[0]),lineterminator='\n');w.writeheader();w.writerows(events)
print(json.dumps({k:v for k,v in s.items()if k!='cases'},indent=2))
