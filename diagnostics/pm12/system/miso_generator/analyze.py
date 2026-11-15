#!/usr/bin/env python3
"""Validate sampled raw controls/edges and recount lock/reset observations."""
import argparse,json,collections,statistics
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());groups=collections.defaultdict(lambda:dict(windows=0,sys_resets=0,lock_losses=0,miso_edges=0,bad_spi_replies=0));details=[]
for t in r['trials']:
 w=t['raw_words'];assert len(w)==t['count']*3
 samples=[(w[i],w[i+1],w[i+2])for i in range(0,len(w),3)if w[i]>8]
 assert all(y[0]>x[0]for x,y in zip(samples,samples[1:]))
 assert t['generator_after']==0x474e0000|t['generator_mode']
 assert t['parser_after']==0x53520000|t['parser_hold']
 assert all(((v>>11)&1)==t['parser_hold']and not(v&4096)for _,v,_ in samples)
 reset=any(v&4 for _,v,_ in samples);loss=any(not(v&1)or v&128 for _,v,_ in samples)
 assert reset==t['sys_reset_observed']and loss==t['lock_loss_observed']
 edges=[y[0]for x,y in zip(samples,samples[1:])if bool(x[1]&64)!=bool(y[1]&64)]
 assert len(edges)==t['miso_edges']
 if t['generator_mode']:
  assert all(not(v&56)for _,v,_ in samples),'Unexpected SEL/SCK/MOSI activity'
 spacing=[y-x for x,y in zip(edges,edges[1:])]
 row=dict(label=t['label'],stage=t['stage'],miso_edges=len(edges),sys_reset=reset,lock_loss=loss,median_half_period_ticks=statistics.median(spacing)if spacing else None,min_spacing_ticks=min(spacing)if spacing else None,max_spacing_ticks=max(spacing)if spacing else None)
 details.append(row);g=groups[t['stage']];g['windows']+=1;g['sys_resets']+=int(reset);g['lock_losses']+=int(loss);g['miso_edges']+=len(edges);g['bad_spi_replies']+=int(t.get('signature_ok')is False)
summary=dict(completed=r.get('completed'),restored=r.get('restored'),adc_validated=r.get('adc_validated'),groups=dict(groups),windows=details,limitations='MISO is sampled logical source, not pad voltage. Generator and observer use MCLK1 and cannot prove behavior during a complete common reference stop. Static captures are sparse, not duration records.')
a.out.mkdir(parents=True,exist_ok=True);(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items()if k!='windows'},indent=2))
