"""Diagnostic phase assignment from the reset pair; raw ADC validation unchanged."""
import argparse,copy,csv,hashlib,json,math,statistics,struct,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ipbus_adc'))
from adc_decode import decode
from analysis_identity import require_same
p=argparse.ArgumentParser();p.add_argument('--board-uid');p.add_argument('--phase-code',type=int,required=True);p.add_argument('--coarse',type=Path,required=True);p.add_argument('--fine',type=Path,required=True);p.add_argument('--validation',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
bound_uid=require_same([a.coarse,a.fine]+([a.validation] if a.validation else []),a.board_uid,a.phase_code)
reports={k:json.loads((path/'status.json').read_text()) for k,path in [('coarse',a.coarse),('fine',a.fine)]+([('validation',a.validation)] if a.validation else [])}
assert all(r['pass_'] for r in reports.values());assert len({r['physical_channel'] for r in reports.values()})==1;assert len({r['fpga'][2] for r in reports.values()})==1
channel=reports['coarse']['physical_channel']
assert len({r.get('sample_window','before-str') for r in reports.values()})==1
paths={'coarse':a.coarse,'fine':a.fine,'validation':a.validation};cache={};hashes={}
def samples(kind,cap):
 key=(kind,cap['file'])
 if key not in cache:
  data=(paths[kind]/cap['file']).read_bytes();hashes[kind+'/'+cap['file']]=hashlib.sha256(data).hexdigest()
  x,_=decode(struct.unpack('<4096H',data),cap['bank'],sample_window=reports[kind].get('sample_window','before-str'));cache[key]=x
 return cache[key]
def means(kind,cap):
 x=samples(kind,cap);n=len(x)//4*4;return [statistics.mean(x[i:n:4]) for i in range(4)]
def rotation(m,s):return [m[(s+i)%4] for i in range(4)]
models={}
for bank in [0,1]:
 seeds=[]
 for wanted in [-.02,-.01]:
  point=next(p for p in reports['coarse']['points'] if abs(p['offset_V']-wanted)<1e-8);templates=[]
  for cap in point['captures']:
   if cap['bank']!=bank:continue
   x=samples('coarse',cap);assert all(1<v<4094 for v in x);m=means('coarse',cap)
   if not seeds:
    jumps=[m[(s+1)%4]-m[s] for s in range(4)]
    candidates=[s for s in range(4) if jumps[s]>30 and min(m[s],m[(s+1)%4])>max(m[(s+2)%4],m[(s+3)%4])]
    assert len(candidates)==1, 'Negative-stimulus integration pair not uniquely above reset pair'
    s=candidates[0]
   else:s=min(range(4),key=lambda s:sum((m[(s+2+i)%4]-seeds[0][2+i])**2 for i in range(2)))
   templates.append(rotation(m,s))
  seeds.append([statistics.mean(t[i] for t in templates) for i in range(4)])
 slopes=[(seeds[1][i]-seeds[0][i])/.01 for i in [2,3]];intercepts=[seeds[0][i]+.02*slopes[j] for j,i in enumerate([2,3])]
 models[str(bank)]=dict(reset_slopes=slopes,reset_intercepts=intercepts,seed_templates=seeds)
initial_models=copy.deepcopy(models)
training_phases={}
for bank in [0,1]:
 training=[];model=initial_models[str(bank)]
 for point in reports['fine']['points']:
  assert abs(point['setpoints_V'][1]-2.048)<1e-8, 'Fine model requires fixed negative input'
  delta=point['actual_requested_offset_V'];pred=[v+s*delta for v,s in zip(model['reset_intercepts'],model['reset_slopes'])]
  for cap in point['captures']:
   if cap['bank']!=bank:continue
   x=samples('fine',cap);assert all(1<v<4094 for v in x);m=means('fine',cap)
   scores=[math.sqrt(sum((m[(s+2+i)%4]-pred[i])**2 for i in range(2))/2) for s in range(4)];order=sorted(range(4),key=lambda i:scores[i]);phase=order[0]
   assert scores[phase]<=5 and scores[order[1]]-scores[phase]>=3, 'Fine phase seed uncertain'
   training.append((delta,m[(phase+2)%4],m[(phase+3)%4]));training_phases[cap['file']]=phase
 assert len(training)>=84
 fits=[statistics.linear_regression([row[0] for row in training],[row[j] for row in training]) for j in [1,2]]
 models[str(bank)]['reset_slopes']=[f.slope for f in fits];models[str(bank)]['reset_intercepts']=[f.intercept for f in fits]
 models[str(bank)]['calibration']='Reset-pair-only fit from fine P-only sweep; no validation inputs used'
 models[str(bank)]['calibration_buffers']=len(training)
rows=[];rejected=[];traces={}
for kind,r in reports.items():
 for point in r['points']:
  delta=point['actual_requested_offset_V']
  for bank in [0,1]:
   changes=[];model=(initial_models if kind=='coarse' else models)[str(bank)];pred=[v+s*delta for v,s in zip(model['reset_intercepts'],model['reset_slopes'])]
   for cap in point['captures']:
    if cap['bank']!=bank:continue
    x=samples(kind,cap);m=means(kind,cap);scores=[math.sqrt(sum((m[(s+2+i)%4]-pred[i])**2 for i in range(2))/2) for s in range(4)];order=sorted(range(4),key=lambda s:scores[s]);s=order[0]
    error=None
    if any(v<=1 or v>=4094 for v in x):error='ADC rail/near-rail sample'
    elif scores[s]>5:error='Reset prediction RMS >5codes'
    elif scores[order[1]]-scores[s]<3:error='Reset-pair registration separation <3codes RMS'
    if error:
     rejected.append(dict(run=kind,file=cap['file'],bank=bank,delta=delta,error=error,scores=scores));continue
    if kind=='fine':assert s==training_phases[cap['file']], 'Recalibration changed a training phase'
    n=len(x)//4*4;change=statistics.mean(x[i+1]-x[i] for i in range(s,n-1,4));changes.append(change)
    traces[(kind,point['index'],bank)]=dict(template=rotation(m,s),pair_change=change,file=cap['file'],phase=s)
   rows.append(dict(run=kind,index=point['index'],bank='AB'[bank],delta_V=delta,DAC2_V=point['setpoints_V'][0],DAC3_V=point['setpoints_V'][1],buffers=len(changes),change_code=statistics.mean(changes) if changes else None,repeat_std=statistics.pstdev(changes) if changes else None))
a.out.mkdir(exist_ok=False)
fig,axes=plt.subplots(2,2,figsize=(11,7.5),layout='constrained');fits={};checks={};passed=True
for bank,label in enumerate('AB'):
 selected=[v for v in rows if v['run']=='fine' and v['bank']==label and v['buffers']>=3];assert len(selected)>=21
 x=np.array([v['delta_V'] for v in selected]);y=np.array([v['change_code'] for v in selected]);fit=statistics.linear_regression(x,y);root=-fit.intercept/fit.slope;assert min(y)<0<max(y) and min(x)<root<max(x)
 fits[label]=dict(root_V=root,commanded_delta_100uV=round(root*10000)/10000,slope_code_per_V=fit.slope,residual_rms_code=float(np.sqrt(np.mean((y-fit.slope*x-fit.intercept)**2))))
 axes[0,bank].errorbar(x*1000,y,yerr=[v['repeat_std'] for v in selected],fmt='o',ms=3,capsize=2);axes[0,bank].plot(x*1000,fit.slope*x+fit.intercept,label=f'Zero {root*1000:.3f}mV');axes[0,bank].axhline(0,color='gray',ls='--');axes[0,bank].set(title=f'ADC {label}: 100uV single-leg scan',xlabel='Relative delta (mV)',ylabel='Integration-pair change (code)');axes[0,bank].grid(alpha=.25);axes[0,bank].legend()
 if a.validation:
  vals=[v for v in rows if v['run']=='validation' and v['bank']==label and v['buffers']>=3];candidate=fits[label]['commanded_delta_100uV']
  near=[v for v in vals if abs(v['delta_V']-candidate)<1e-8]
  lower=[v for v in vals if abs(v['delta_V']-(candidate-.005))<1e-8];upper=[v for v in vals if abs(v['delta_V']-(candidate+.005))<1e-8]
  ok=len(near)>=2 and all(abs(v['change_code'])<=2 for v in near) and any(v['change_code']>4 for v in lower) and any(v['change_code']< -4 for v in upper)
  checks[label]=dict(pass_=ok,candidate_delta_V=candidate,returns=[v['change_code'] for v in near],lower=[v['change_code'] for v in lower],upper=[v['change_code'] for v in upper]);passed &=ok
  chosen=near[0] if near else vals[0];t=traces['validation',chosen['index'],bank]['template'];axes[1,bank].plot(range(4),t,'o-');axes[1,bank].set(title=f'Independent return {label}; delta {chosen["delta_V"]*1000:g}mV',xlabel='Assigned sample position (0/1 integration)',ylabel='ADC code');axes[1,bank].grid(alpha=.25)
 else:
  axes[1,bank].plot([v['delta_V']*1000 for v in rows if v['run']=='coarse' and v['bank']==label and v['change_code'] is not None],[v['change_code'] for v in rows if v['run']=='coarse' and v['bank']==label and v['change_code'] is not None],'o-');axes[1,bank].axhline(0,color='gray',ls='--');axes[1,bank].set(title='Coarse signed response',xlabel='Relative delta (mV)',ylabel='Integration-pair change (code)');axes[1,bank].grid(alpha=.25)
fig.suptitle(f'PM{channel}: normal20MHz, phase DAC{a.phase_code}; reset-pair calibration from fine sweep\nDiagnostic phase assignment; strict raw stability. Not an absolute DC-current null.')
for ext in ['png','pdf']:fig.savefig(a.out/f'integrator{channel}.{ext}',dpi=160)
with (a.out/'points.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
summary=dict(status=('PASS_FUNCTIONAL' if passed else 'INCOMPLETE') if a.validation else 'FINE_SCAN_ONLY',board_uid=bound_uid,physical_channel=channel,phase_code=a.phase_code,sample_window=reports['coarse'].get('sample_window','before-str'),initial_symmetric_models=initial_models,models=models,fits=fits,validation=checks,analysis_rejected=rejected,raw_coherent_buffers=len(cache),raw_sha256=hashes,limits='Independent returns <=2codes, +/-5mV responses beyond +/-4codes; phase assigned by reset model, not external gate timestamp; command voltages uncalibrated')
(a.out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['raw_sha256','analysis_rejected']},indent=2));print('ANALYSIS_REJECTED',len(rejected))
