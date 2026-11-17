from pathlib import Path
import sys,json,struct,hashlib,statistics,shutil,collections
P=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12');sys.path[:0]=[str(P/'cfd_simulator'),str(P/'ipbus_adc')]
from integrator_analysis import integration_pair
from adc_decode import decode
root=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261117');native=root/'batches/ch01-04-attempt001/working/ch03/after-usb-move/integrator-corrected-usb';e=P/'acceptance/evidence-channel03-20261117';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(P/'cfd_simulator/integrator_analysis.py')==h(root/'staging/integrator-ch05/analysis-sources/integrator_analysis.py')
result=dict(status='INCOMPLETE',physical_channel=3,validation_scope='Rebuild fine-scan waveform qualification from raw buffers; unchanged minimum_separation30; no new hardware test',minimum_separation=30,banks={},raw_sha256={})
d=json.loads((native/'fine01/status.json').read_text());assert d['pass_'] and len(d['points'])==26
for bank,label in enumerate('AB'):
 points=[];rejected=collections.Counter();retained_buffers=0
 for point in d['points']:
  vals=[]
  for cap in point['captures']:
   if cap['bank']!=bank:continue
   p=native/'fine01'/cap['file'];b=p.read_bytes();result['raw_sha256'][str(p.relative_to(root))]=hashlib.sha256(b).hexdigest();samples,_=decode(struct.unpack('<4096H',b),bank)
   try:vals.append(integration_pair(samples)['mean_change']);retained_buffers+=1
   except ValueError as ex:rejected[str(ex)]+=1
  if len(vals)>=2:points.append(dict(offset_V=point['offset_V'],mean_change=statistics.mean(vals),buffers=len(vals)))
 roots=[a['offset_V']-a['mean_change']*(b['offset_V']-a['offset_V'])/(b['mean_change']-a['mean_change'])for a,b in zip(points,points[1:])if a['mean_change']*b['mean_change']<0]
 result['banks'][label]=dict(acquired_points=26,retained_points=len(points),retained_buffers=retained_buffers,rejected_buffers=dict(rejected),signed_crossings=roots,points=points)
assert result['banks']['B']['retained_points']==1 and not result['banks']['B']['signed_crossings']
(e/'integrator-diagnostic-validation.json').write_text(json.dumps(result,indent=2)+'\n');shutil.copy2(Path(__file__),e/'validate-incomplete-integrator.py');sd=e/'diagnostic-analysis-sources';sd.mkdir()
for p in [P/'cfd_simulator/integrator_analysis.py',P/'ipbus_adc/adc_decode.py']:shutil.copy2(p,sd/p.name)
print(json.dumps({k:{n:v for n,v in row.items()if n!='points'}for k,row in result['banks'].items()},indent=2))
report=P/'acceptance/evidence-campaign-assembly-20261113';f=report/'channel03-followup.tex';s=f.read_text();needle='No full integrator PASS or hardware defect is inferred; thresholds unchanged.';s=s.replace(needle,needle+' Independent raw-buffer revalidation retained '+str(result['banks']['A']['retained_points'])+' of26fine points on A and1of26 on B. The separation threshold remains30codes.');f.write_text(s)
