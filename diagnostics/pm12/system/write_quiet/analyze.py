#!/usr/bin/env python3
import argparse,json,collections
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());groups=collections.defaultdict(lambda:dict(frames=0,sys_resets=0,lock_losses=0,bad_spi_replies=0,bad_write_commits=0,oe_mismatches=0));idle=[];cases=[];partial=[]
for t in r['trials']:
 if 'raw_words'not in t:
  partial.append({k:v for k,v in t.items()if k not in ['raw_words_partial']});continue
 w=t['raw_words'];assert len(w)==t['count']*3
 samples=[(w[i],w[i+1],w[i+2])for i in range(0,len(w),3)if w[i]>8]
 assert all(y[0]>x[0]for x,y in zip(samples,samples[1:]))
 mode=t['generator_mode'];assert t['generator_after']==0x474e0000|mode
 assert t['parser_after']==0x53520000|t['parser_hold'] and t['parser_hold']in (0,4)
 assert all(not(v&2048)and bool(v&4096)==bool(t['parser_hold']&2)for _,v,_ in samples),'Unexpected parser hold/clamp'
 assert all(bool(v&16384)==bool(t['parser_hold']&4)for _,v,_ in samples),'Quiet-write control not observed'
 if not t.get('read',True)and t['parser_hold']&4:assert all(not(v&64)for _,v,_ in samples),'Write MISO not quiet'
 resets=any(v&4 for _,v,_ in samples);loss=any(not(v&1)or v&128 for _,v,_ in samples)
 assert resets==t['sys_reset_observed']and loss==t['lock_loss_observed']
 mismatches=sum(bool(v&8192)!=(True if mode>=4 else bool(v&8))for _,v,_ in samples)
 assert mismatches==t['oe_mismatches']
 if mode>=4:assert not mismatches
 edges=sum(bool(x[1]&16)!=bool(y[1]&16)for x,y in zip(samples,samples[1:]))
 if t['address']is None:
  assert all(not(v&56)for _,v,_ in samples),'Non-idle Kasli SPI lines'
  idle.append(dict(label=t['label'],mode=mode,sys_reset=resets,lock_loss=loss));continue
 if not t['status']&8192:assert edges==64,'Incomplete SCK frame'
 assert any((v>>16)&31 for _,v,_ in samples),'Parser inactive'
 if mode>=4:
  # Selected read waveform must remain the original parser data.
  assert all(not(v&8)or bool(v&64)==bool(d&32768)for _,v,d in samples if v>>31),'Selected data changed'
 g=groups[t['stage']];g['frames']+=1;g['sys_resets']+=int(resets);g['lock_losses']+=int(loss);g['bad_spi_replies']+=int(t.get('signature_ok')is False);g['bad_write_commits']+=int(t.get('write_committed')is False);g['oe_mismatches']+=mismatches
 cases.append(dict(label=t['label'],mode=mode,divider=t['divider'],address=t['address'],read=t.get('read',True),value=t.get('value',0),sys_reset=resets,lock_loss=loss,sck_edges=edges,oe_mismatches=mismatches))
summary=dict(write_only_series_complete=all(groups.get(n,{}).get('frames')==12 and groups[n]['bad_write_commits']==0 for n in ['QUIET-before','QUIET-return']),positive_control_captured=groups.get('RAW-control',{}).get('frames',0)>=1,retained_candidate=r.get('retained_candidate'),resident_sha256=r.get('resident_sha256'),completed=bool(r.get('completed')),restored=r.get('restored'),adc_validated=r.get('adc_validated'),groups=dict(groups),idle=idle,cases=cases,partial_windows=partial,error=r.get('error'),limitations='OE/data are sampled logical source taps, not pad voltage. Shared watch/reference stop invisible; SPI bundle not atomic, data comparison uses consecutive stable samples.')
a.out.mkdir(exist_ok=True,parents=True);(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items()if k not in ['cases','idle','partial_windows']},indent=2))
