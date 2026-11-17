"""Offline slow-integrator waveform comparison; no absolute gate alignment."""
import argparse,csv,hashlib,json,struct,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,required=True)
args=parser.parse_args()
ROOT=args.root.resolve()
sys.path.insert(0,'/home/codex-hil/fit-testing-publish/diagnostics/pm12/ipbus_adc')
from adc_decode import decode
r=json.loads((ROOT/'hardware/status.json').read_text())
assert r['complete'] and r['restored_all_cpld_rows'] and r['restored_phase_code']==0
OUT=ROOT/'analysis';OUT.mkdir(exist_ok=False)
fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
rows=[];hashes={};valid=0
for point in r['points']:
 for bank,label in enumerate('AB'):
  arrays=[];waveforms=[];clips=[]
  period=40 if point['stage'].startswith('slow') else 4
  for cap in point['captures']:
   if cap['bank']!=bank:continue
   p=ROOT/'hardware'/cap['file'];raw=p.read_bytes();hashes[cap['file']]=hashlib.sha256(raw).hexdigest()
   if not cap['valid']:raise ValueError('Invalid capture retained: '+str(cap))
   x,timing=decode(struct.unpack('<4096H',raw),bank);valid+=1
   x=np.asarray(x);arrays.append(x);n=len(x)//period*period
   wave=np.array([x[k:n:period].mean() for k in range(period)])
   assert np.allclose(wave,cap['phase_means'])
   if period==40:
    # Align on largest upward step, without identifying the physical gate.
    wave=np.roll(wave,-int(np.argmax(np.roll(wave,-1)-wave))-1)
   waveforms.append(wave);clips.append(np.mean((x==0)|(x==4095)))
  w=np.mean(waveforms,axis=0)
  row=dict(stage=point['stage'],delta_V=point['offset_V'],bank=label,period_samples=period,
           mean_code=float(np.mean([x.mean() for x in arrays])),phase_amplitude_code=float(np.mean([np.ptp(v) for v in waveforms])),
           clip_percent=float(np.mean(clips)*100),buffers=len(arrays))
  rows.append(row)
  if point['stage'] in ['slow-baseline','slow-stimulus']:
   axes[0,bank].plot(np.arange(period)*1e9/80157400,waveforms[0],'o-',ms=3,label=f"Delta {point['offset_V']*1000:g} mV")
  if point['stage'] in ['normal-before','slow-baseline']:
   axes[1,bank].plot(np.arange(160)*1e9/80157400,arrays[0][:160],label=point['stage'],lw=1)
for bank,label in enumerate('AB'):
 axes[0,bank].set(title=f'ADC {label}: 40-sample mean waveform, first buffer',xlabel='Circularly aligned position (nominal ns)',ylabel='ADC code')
 axes[1,bank].set(title=f'ADC {label}: raw time trace, same base input',xlabel='Time from independent capture start (nominal ns)',ylabel='ADC code')
 for ax in axes[:,bank]:ax.grid(alpha=.25);ax.legend()
fig.suptitle('PM2: complementary integrator gates divided by 40, about 2.004 MHz\nADC nominal 80.1574 MS/s; aligned on largest positive step, not an absolute gate timestamp')
for ext in ['png','pdf']:fig.savefig(OUT/f'slow-gates.{ext}',dpi=160)
with (OUT/'measurements.csv').open('w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
summary=dict(validated_buffers=valid,physical_channel=2,gate_divider=40,gate_frequency_Hz_assumed=80157400/40,
             adc_sample_rate_Hz_assumed=80157400,clock_scope='Relative period measured by Kasli; absolute scale uses supplied LHC nominal frequency',
             gate_measurements={k:v for k,v in r.items() if k.endswith('-gates')},measurements=rows,raw_sha256=hashes)
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='raw_sha256'},indent=2))
