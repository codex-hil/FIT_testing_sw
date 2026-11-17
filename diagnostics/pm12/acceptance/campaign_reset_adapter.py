"""Offline raw validator/receipt for continuous-reset A/B characterization."""
import argparse,hashlib,json,math,re,shutil,statistics,struct,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'ipbus_adc'),str(HERE)]
from adc_decode import decode
from campaign import Campaign,read,write,digest

def validate(source,bank="B"):
 r=read(source/'hardware/status.json');s=read(source/'analysis/summary.json')
 ch=r['physical_channel']
 if r.get('reset_bank',bank)!=bank:raise ValueError('Wrong reset bank')
 if not (r['complete'] and r['restored_all_cpld_rows'] and r['restored_phase_code']==0 and r['changed_channels']==[ch]):
  raise ValueError('Incomplete measurement/restoration')
 if r.get('error') or r.get('restore_error') or r.get('phase_cleanup_error'):raise ValueError('Acquisition contains errors')
 arrays={}
 for tag in ['before-nv','after-nv','restored-nv']:
  text=(source/'hardware'/(tag+'.log')).read_text()
  if 'CPLD_READ_PASS' not in text:raise ValueError('Incomplete CPLD readback')
  matches=re.findall(r'^ARRAY (\d+) ([AB]) (\d+) ([0-9a-fA-F]+)$',text,re.M)
  a={(int(c),int(i)):int(v,16) for c,b,i,v in matches if b=='A'}
  b={(int(c),int(i)):int(v,16) for c,b,i,v in matches if b=='B'}
  if len(matches)!=1968 or len(a)!=984 or a!=b:raise ValueError('Inconsistent CPLD readback')
  arrays[tag]=a
 if arrays['before-nv']!=arrays['restored-nv']:raise ValueError('CPLD restoration differs')
 changed={c for c,i in arrays['before-nv'] if arrays['before-nv'][c,i]!=arrays['after-nv'][c,i]}
 if changed!={ch}:raise ValueError('Unexpected CPLD programming scope')
 data=[];count=0
 for point in r['points']:
  caps=[]
  for cap in point['captures']:
   raw=(source/'hardware'/cap['file']).read_bytes()
   if hashlib.sha256(raw).hexdigest()!=s['raw_hashes'][cap['file']]:raise ValueError('Raw hash mismatch')
   samples,_=decode(struct.unpack('<4096H',raw),cap['bank'])
   if not cap['valid']:raise ValueError('Invalid capture')
   mean=statistics.mean(samples);n=len(samples)//4*4
   wave=[statistics.mean(samples[k:n:4]) for k in range(4)]
   if abs(mean-cap['mean'])>1e-9:raise ValueError('Raw mean mismatch')
   caps.append(dict(bank=cap['bank'],mean=mean,amplitude=max(wave)-min(wave),
                    clipped=any(x<=1 or x>=4094 for x in samples)))
   count+=1
  data.append((point,caps))
 if count!=s['validated_buffers']:raise ValueError('Buffer count mismatch')
 metrics=[];curves=[];fits={}
 for leg in ['P','N']:
  points=[]
  for point,caps in data:
   if point['stage']!='reset-sweep' or point['leg']!=leg:continue
   selected=[c for c in caps if c['bank']=='AB'.index(bank)]
   if len(selected)!=3 or any(c['clipped'] for c in selected):raise ValueError('Reset B fit clipped/incomplete')
   points.append((point['offset_V'],statistics.mean(c['mean'] for c in selected)))
  points.sort()
  if len(points)!=11 or any(abs(x-(-.1+i*.02))>1e-9 for i,(x,y) in enumerate(points)):
   raise ValueError('Expected fixed eleven-point sweep')
  fit=statistics.linear_regression([p[0] for p in points],[p[1] for p in points]);ron=abs(fit.slope)*430/2000
  if abs(ron-s['fits'][leg]['nominal_R_on_ohm'])>1e-6:raise ValueError('Fit mismatch')
  fits[leg]=ron
  metrics += [dict(name='reset_R_'+leg,bank=bank,value=ron,unit='ohm (nominal)'),dict(name='reset_slope_'+leg,bank=bank,value=fit.slope,unit='code/commanded V')]
  curves.append(dict(name='reset_response_'+leg,bank=bank,x=[p[0] for p in points],y=[p[1] for p in points],x_unit='commanded V offset',y_unit='code'))
 for stage in ['normal-before','normal-after','reset-baseline']:
  matches=[caps for point,caps in data if point['stage']==stage]
  if len(matches)!=1:raise ValueError('Missing control')
  for bank,label in enumerate('AB'):
   caps=[c for c in matches[0] if c['bank']==bank]
   if len(caps)!=3:raise ValueError('Missing control repeat')
   metrics.append(dict(name=stage+'_amplitude',bank=label,value=statistics.mean(c['amplitude'] for c in caps),unit='code'))
 if set(r['tca_final'].values())!={0}:raise ValueError('TCA not released')
 return r,s,metrics,curves,count

def normalize(source,out,root,batch):
 validated={bank:validate(source/bank,bank) for bank in 'AB'}
 r=validated['A'][0];other=validated['B'][0];ch=r['physical_channel']
 if other['physical_channel']!=ch or other['board_uid']!=r['board_uid'] or other['fixture_id']!=r['fixture_id']:
  raise ValueError('A/B runs belong to different board/channel/fixture')
 c=Campaign(root)
 with c.locked():
  directory,b=c.batch(batch);c.check_identity(directory,b)
  cfg=read(directory/'station.json')
  if not any(t['id']=='integrator-reset' for t in c.protocol['tests']):raise ValueError('New campaign protocol revision required')
  if ch not in b['channels'] or r['board_uid']!=c.data['board_uid'] or r['fixture_id']!=b['assignments'][str(ch)]:raise ValueError('Wrong board/channel/fixture')
  uid=c.data['board_uid'];fixture=b['assignments'][str(ch)]
 if r['fpga']!=other['fpga']:raise ValueError('Mixed FPGA builds')
 out.mkdir(parents=True,exist_ok=False)
 shutil.copy2(__file__,out/'executed-adapter.py');sources=['executed-adapter.py']
 metrics=[];curves=[];count=0
 for bank,(report,summary,ms,cs,n) in validated.items():
  target=out/bank;target.mkdir()
  shutil.copytree(source/bank/'hardware',target/'acquisition')
  shutil.copytree(source/bank/'analysis',target/'analysis')
  shutil.copytree(source/bank/'vectors',target/'vectors')
  count+=n
  sources += [bank+'/analysis/executed-analysis.py',bank+'/analysis/adc_decode.py']
  for name,value in report['sources'].items():
   if digest(target/'acquisition'/name)!=value:raise ValueError('Acquisition source snapshot mismatch')
   sources.append(str(Path(bank)/'acquisition'/name))
  metrics += [m for m in ms if m['name'].startswith('reset_')]
  # Preserve both acquisitions' normal controls instead of merging different times.
  metrics += [dict(m,name='during_reset_'+bank+'_'+m['name']) for m in ms if not m['name'].startswith('reset_')]
  curves += cs
 mc=cfg['measurement_configuration']
 protocol=dict(method='continuous-reset-AB-v1',base_V=[1.024,2.048],offsets_V=[round(-.1+i*.02,4) for i in range(11)],
               repeats_per_bank=3,adc_phase_code=32768,input_R_ohm=430,adc_codes_per_V=2000,
               acceptance='Characterization completion only; no numerical R_ON acceptance limits',
               hardware_configuration=dict(pm_build=f"{r['fpga'][2]:08x}",kasli_build=dict(ABI='CFD4',expected_bit_sha256=mc['kasli_bit_sha256']),
                    clock_profile=dict(reference_mhz=mc['reference_mhz'],adc_rate='2x reference',kasli_rate='3x reference'),
                    cpld_gate_mode='Each bank reset HIGH separately; other gate retained; original restored'))
 write(out/'validation.json',dict(pass_=True,physical_channel=ch,raw_buffers=count,restored_all_cpld_rows=True))
 result=dict(mode='LIVE',board_uid=uid,test='integrator-reset',channel=ch,fixture_id=fixture,
             measured_utc=min(v[0]['started_utc'] for v in validated.values()),status='PASS',
             protocol=protocol,source_files=sources,validation=[dict(file='validation.json',key='pass_',equals=True)],
             channel_checks=[dict(file='validation.json',key='physical_channel')],connections=dict(usb_input='J6',stimulus_channel=ch,dac_channels=[2,3]),
             metrics=metrics,curves=curves,limits='Conditional effective A/B branch R; nominal ADC/input resistance, commanded DAC voltage. PASS means completed characterization, not resistance tolerance.')
 write(out/'campaign-result.json',result)
 return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['source','out','root']:p.add_argument('--'+name,type=Path,required=True)
 p.add_argument('--batch',required=True);a=p.parse_args();normalize(a.source,a.out,a.root,a.batch)
