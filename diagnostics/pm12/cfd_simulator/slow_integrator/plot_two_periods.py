"""Show two contiguous raw gate periods, without folding or sample averaging."""
import argparse,csv,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
PM=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PM/'ipbus_adc'))
from adc_decode import decode

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--run',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();r=json.loads((a.run/'hardware/status.json').read_text())
 assert r['complete'] and r['restored_all_cpld_rows']
 selected=[point for point in r['points'] if point['stage'] in ['slow-baseline','slow-stimulus']]
 assert len(selected)==4
 a.out.mkdir(parents=True,exist_ok=False)
 fig,axes=plt.subplots(4,2,figsize=(12,10),layout='constrained',sharex=True)
 rows=[];sources=[];sample_ns=1e9/80157400;period_ns=40*sample_ns
 for i,point in enumerate(selected):
  for bank,label in enumerate('AB'):
   cap=next(c for c in point['captures'] if c['bank']==bank)
   raw=(a.run/'hardware'/cap['file']).read_bytes()
   assert cap['valid']
   x,_=decode(struct.unpack('<4096H',raw),bank)
   # Only choose an origin from the periodic template; plotted values below
   # are 81 unchanged, consecutive raw decoded samples from this one buffer.
   n=len(x)//40*40
   template=np.array([np.mean(x[k:n:40]) for k in range(40)])
   start=(int(np.argmax(np.roll(template,-1)-template))+1)%40
   y=x[start:start+81];assert len(y)==81
   t=np.arange(81)*sample_ns;ax=axes[i,bank]
   ax.plot(t,y,'o-',ms=3,lw=1)
   for boundary in [0,period_ns,2*period_ns]:ax.axvline(boundary,color='gray',ls='--',lw=.8)
   ax.set(title=f"ADC {label}; relative delta {point['offset_V']*1000:g} mV",ylabel='ADC code',xlim=(0,2*period_ns))
   ax.grid(alpha=.25)
   if i==3:ax.set_xlabel('Time from selected sample (nominal ns)')
   for k,(time,value) in enumerate(zip(t,y)):
    rows.append(dict(bank=label,delta_V=point['offset_V'],sample_index_in_buffer=start+k,time_ns=float(time),ADC_code=value))
   sources.append(dict(bank=label,delta_V=point['offset_V'],file=cap['file'],sha256=hashlib.sha256(raw).hexdigest(),decoded_samples_in_buffer=len(x),start_index=start,plotted_samples=81))
 fig.suptitle('PM2: two complete slow-gate periods, 81 consecutive ADC samples\n'
              'No waveform folding or averaging; sampled-edge alignment, not absolute gate timing')
 for ext in ['png','pdf']:fig.savefig(a.out/f'two-periods.{ext}',dpi=160)
 with (a.out/'two-periods.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 (a.out/'provenance.json').write_text(json.dumps(dict(sample_rate_Hz_assumed=80157400,gate_period_samples=40,sources=sources),indent=2)+'\n')
 print('8 traces,81 contiguous samples each; full raw buffers retained')
if __name__=='__main__':main()
