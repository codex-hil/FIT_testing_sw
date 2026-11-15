#!/usr/bin/env python3
import argparse,json,statistics,csv
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());a.out.mkdir(exist_ok=True,parents=True);trials=[];all_records=[]
for t in r.get('trials',[]):
 if 'raw_words'not in t:continue
 regs=t['registers'];count,start=regs[2:4];assert regs[0]==0x434c4b52 and regs[5]==384 and regs[12]==2048 and len(t['raw_words'])==8192
 words=t['raw_words'];records=[]
 for n in range(count):
  physical=(start+n)%2048;w0,w1,w2,w3=words[physical*4:physical*4+4];flags=w2>>16;length=w3>>16
  row=dict(label=t['label'],index=n,physical=physical,tick=w0,mclk=w1&65535,gtref=w1>>16,sys=w2&65535,flags=flags,length=length,window_id=w3&65535)
  assert 1<=length<=384
  if records:
   assert row['window_id']==(records[-1]['window_id']+1)&65535
   assert (row['tick']-records[-1]['tick'])&0xffffffff==length
  row['valid_full']=length==384 and(flags&0x18)==0x18 and not(flags&0x1c4)
  records.append(row);all_records.append(row)
 full=[x for x in records if x['valid_full']];assert full,'No qualified full-window samples'
 clocks={}
 for key,expected in [('mclk',256),('gtref',640),('sys',256)]:
  values=[x[key]for x in full];clocks[key]=dict(min=min(values),max=max(values),mean=statistics.mean(values),expected=expected,more_than_one_count_off=sum(abs(v-expected)>1 for v in values),mean_hz=sum(values)*regs[4]/sum(x['length']for x in full))
 trial=dict(label=t['label'],record_count=count,valid_full_windows=len(full),triggered=t['triggered'],status=regs[1],clocks=clocks,cdce_before=t['cdce_before'].get('decoded'),cdce_after=t['cdce_after'].get('decoded'),signature_ok=t.get('signature_ok'),last_record=records[-1]);trials.append(trial)
summary=dict(completed=r.get('completed'),retained_candidate=r.get('retained_candidate'),restored=r.get('restored'),adc_validated=r.get('adc_validated'),postflight_error=r.get('postflight_error'),error=r.get('error'),trials=trials,limitations='Relative edge counts, not analog glitch/phase measurement. Endpoint quantization and CDR/local-reference coupling limit interpretation; partial and invalid-reference records excluded.')
(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if all_records:
 with(a.out/'windows.csv').open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(all_records[0]),lineterminator='\n');w.writeheader();w.writerows(all_records)
print(json.dumps(summary,indent=2))
