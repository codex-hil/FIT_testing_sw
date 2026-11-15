#!/usr/bin/env python3
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('result',type=Path);p.add_argument('out',type=Path);a=p.parse_args();r=json.loads(a.result.read_text());groups={}
for name in ['jtag_primary','jtag_aux']:
 d=r[name];assert d['cases'];restarts=0
 for t in d['cases']:
  b=t['before'];e=t['after'];assert int(b['report_hex'],16)&0xffffffff==0x504d5a04 and int(e['report_hex'],16)&0xffffffff==0x504d5a04
  for q in [b,e]:assert q['tick']==(int(q['report_hex'],16)>>32)&0xffffffff
  dt=((e['jtag_before_us']+e['jtag_after_us'])-(b['jtag_before_us']+b['jtag_after_us']))/2e6
  delta=(e['tick']-b['tick'])&0xffffffff;bad=not(20e6*dt<delta<60e6*dt);assert delta==t['delta']and bad==t['sys_counter_discontinuity'];assert t['signature_ok']and t['signature']==[0x4844,0x4d49,1][t['address']];restarts+=bad
 groups[name]=dict(frames=len(d['cases']),counter_discontinuities=restarts,all_signatures_correct=True,approximate_sys_hz=d['rate']['nominal_sys_hz'])
s=dict(groups=groups,completed_clock_measurements=True,aux_retained=bool(r.get('aux_retained')),mcu_restored=r.get('mcu_restored'),trial_error=r.get('aux_error'),adc_aux='NOT_MEASURED',limitations='Sparse read-only JTAG counter pairs detect SYS counter restarts, not analog clock noise or every short LOCK excursion. Temperature initialization did not qualify; original MCU restored. Clock rates are uncalibrated estimates.')
a.out.mkdir(exist_ok=True,parents=True);(a.out/'summary.json').write_text(json.dumps(s,indent=2)+'\n');print(json.dumps(s,indent=2))
