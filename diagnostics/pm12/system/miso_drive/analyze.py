#!/usr/bin/env python3
"""Recount raw SYS reset and state samples, grouping by actual drive/stage."""
import argparse, collections, json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());groups=collections.defaultdict(lambda:dict(frames=0,resets=0,bad_spi_replies=0));a.out.mkdir(parents=True,exist_ok=True)
for t in r['trials']:
 w=t.get('raw_words');assert w and len(w)==t['count']*3
 samples=[(w[i],w[i+1],w[i+2])for i in range(0,len(w),3)if w[i]>8]
 assert t['mode']==0 and t['mode_after']==0x53520000
 assert all(not(v&0x1800)for _,v,_ in samples), 'Hold/clamp unexpectedly enabled'
 reset=any(v&4 for _,v,_ in samples);assert reset==t['sys_reset_observed']
 if t['address']is None:continue
 g=groups[t['stage']];g['frames']+=1;g['resets']+=int(reset);g['bad_spi_replies']+=int(not t['signature_ok'])
s=dict(groups=dict(groups),completed=r.get('completed'),restored=r.get('restored'),adc_validated=r.get('adc_validated'),baseline_reproduced=r.get('baseline_reproduced'),chosen_divider=r.get('chosen_divider'))
(a.out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
