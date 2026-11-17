"""Conditional effective switch resistance from continuous-reset DC transfer."""
import argparse,json,struct,sys,csv,hashlib,shutil
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--root',type=Path,required=True)
args=parser.parse_args()
ROOT=args.root.resolve()
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'ipbus_adc'))
from adc_decode import decode
r=json.loads((ROOT/'hardware/status.json').read_text())
assert r['complete'] and r['restored_all_cpld_rows'] and r['restored_phase_code']==0
OUT=ROOT/'analysis';OUT.mkdir(exist_ok=False)
shutil.copy2(__file__,OUT/'executed-analysis.py')
shutil.copy2(Path(__file__).resolve().parent.parent/'ipbus_adc/adc_decode.py',OUT/'adc_decode.py')
bank=r.get('reset_bank','B')
rows=[];hashes={}
for pt in r['points']:
 for bank in [0,1]:
  caps=[]
  for cap in pt['captures']:
   if cap['bank']!=bank:continue
   path=ROOT/'hardware'/cap['file'];raw=path.read_bytes();hashes[cap['file']]=hashlib.sha256(raw).hexdigest()
   try:x,_=decode(struct.unpack('<4096H',raw),bank)
   except ValueError:
    assert not cap['valid'];continue
   assert cap['valid'];a=np.asarray(x);n=len(a)//4*4
   wave=np.array([a[k:n:4].mean() for k in range(4)])
   caps.append(dict(mean_code=float(a.mean()),rms_code=float(a.std()),clip_fraction=float(np.mean((a<=1)|(a>=4094))),phase_amplitude_code=float(np.ptp(wave))))
  row={k:v for k,v in pt.items() if k not in ['captures','setpoints_V']};row.update(bank='AB'[bank],valid_buffers=len(caps))
  if caps:
   for k in caps[0]:row[k]=float(np.mean([c[k] for c in caps]))
   row['mean_repeat_std']=float(np.std([c['mean_code'] for c in caps]))
  rows.append(row)
fig,axs=plt.subplots(1,2,figsize=(11,4.5),layout='constrained');fits={}
for ax,leg in zip(axs,['P','N']):
 selected=[q for q in rows if q['stage']=='reset-sweep' and q['bank']==bank and q['leg']==leg and q['valid_buffers']==3 and q['clip_fraction']==0]
 assert len(selected)>=8
 x=np.array([q['offset_V'] for q in selected]);y=np.array([q['mean_code'] for q in selected]);slope,intercept=np.polyfit(x,y,1)
 residual=y-(slope*x+intercept);r2=1-float(np.sum(residual**2)/np.sum((y-y.mean())**2))
 # Nominal ADC sensitivity: 4096/(2*1.024)=2000 codes/V.
 # Each integrator input branch: 210 + 220 ohm, optional parallel resistor absent.
 ron=abs(float(slope))/2000*430
 fits[leg]=dict(slope_code_per_commanded_V=float(slope),intercept_code=float(intercept),r_squared=r2,residual_rms_code=float(np.sqrt(np.mean(residual**2))),nominal_R_on_ohm=ron,fit_points=len(x))
 ax.errorbar(x*1000,y,yerr=[q['mean_repeat_std'] for q in selected],fmt='o',capsize=3,label=f'ADC {bank}: three buffers/point')
 ax.plot(x*1000,slope*x+intercept,label=f'Fit: {slope:.1f} code/V; nominal R={ron:.1f} ohm')
 ax.set(title=f'Sweep input {leg}; other input fixed',xlabel=f'Commanded input {leg} offset (mV)',ylabel=f'ADC {bank} mean (code)');ax.grid(alpha=.3);ax.legend(fontsize=8)
fig.suptitle(f'PM{r["physical_channel"]}: continuous reset {bank}, other gate retained\nNominal R estimate assumes 430 ohm input resistance and 2000 ADC codes/V')
for ext in ['png','pdf']:fig.savefig(OUT/f'reset-transfer.{ext}',dpi=170)
with (OUT/'measurements.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for q in rows for k in q)));w.writeheader();w.writerows(rows)
summary=dict(physical_channel=r['physical_channel'],reset_bank=bank,fits=fits,assumptions=['ADC VREF nominal 1.024 V; external-reference differential span 2*VREF','Input R nominal 210+220=430 ohm; optional parallel resistors DNP per schematic','Commanded external DAC voltage changes equal pin voltage changes; not measured in this run','ADC/opamp static gain error and finite loop gain not removed'],scope='Effective closed-loop resistance estimate, not individually calibrated transistor measurement',validated_buffers=sum(q['valid_buffers'] for q in rows),raw_hashes=hashes,controls=[q for q in rows if q['stage']!='reset-sweep'])
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='raw_hashes'},indent=2))
