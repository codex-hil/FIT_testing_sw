from pathlib import Path
import hashlib,json,re,shutil,struct,sys,tarfile
PM=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12')
sys.path.insert(0,str(PM/'ipbus_adc'))
from adc_decode import decode
ROOTS=[Path('/srv/codex-hil-nvme/pm12-slow-negative-20261117-run01'),Path('/srv/codex-hil-nvme/pm12-slow-negative-20261117-run02-phase49152')]
PLOT=Path('/srv/codex-hil-nvme/pm12-slow-negative-two-periods-20261117')
E=PM/'cfd_simulator/evidence-slow-negative-20261117';E.mkdir(exist_ok=False)
validation=dict(runs=[],valid_buffers=0,rejected_buffers=0,scope='Diagnostic; not production qualification')
for root in ROOTS:
 r=json.loads((root/'hardware/status.json').read_text())
 assert r['complete'] and r['restored_all_cpld_rows'] and r['restored_phase_code']==0 and r['hdmi_before']==r['hdmi_final']
 assert not r.get('error') and not r.get('restore_error') and set(r['tca_final'].values())=={0}
 arrays={}
 for tag in ['before-nv','after-nv','restored-nv']:
  text=(root/'hardware'/(tag+'.log')).read_text();assert 'CPLD_READ_PASS' in text
  matches=re.findall(r'^ARRAY (\d+) ([AB]) (\d+) ([0-9a-fA-F]+)$',text,re.M)
  a={(int(c),int(i)):int(v,16) for c,b,i,v in matches if b=='A'}
  b={(int(c),int(i)):int(v,16) for c,b,i,v in matches if b=='B'}
  assert len(matches)==1968 and len(a)==984 and a==b;arrays[tag]=a
 assert arrays['before-nv']==arrays['restored-nv']
 assert {ch for ch,i in arrays['before-nv'] if arrays['before-nv'][ch,i]!=arrays['after-nv'][ch,i]}=={2}
 row=dict(run=root.name,adc_phase_code=r.get('adc_phase_code',32768),valid=0,rejected=[],points=[])
 for point in r['points']:
  stats=[]
  for cap in point['captures']:
   raw=(root/'hardware'/cap['file']).read_bytes()
   try:
    x,_=decode(struct.unpack('<4096H',raw),cap['bank']);assert cap['valid']
    row['valid']+=1;validation['valid_buffers']+=1
    stats.append(dict(bank='AB'[cap['bank']],file=cap['file'],minimum=min(x),maximum=max(x),rail_samples=sum(v in [0,4095] for v in x),samples=len(x),sha256=hashlib.sha256(raw).hexdigest()))
   except ValueError as error:
    assert not cap['valid'];validation['rejected_buffers']+=1
    row['rejected'].append(dict(file=cap['file'],delta_V=point['offset_V'],bank='AB'[cap['bank']],reason=str(error),sha256=hashlib.sha256(raw).hexdigest()))
  row['points'].append(dict(stage=point['stage'],delta_V=point['offset_V'],setpoints_V=point['setpoints_V'],captures=stats))
 validation['runs'].append(row)
for p in PLOT.iterdir():
 if p.is_file():shutil.copy2(p,E/p.name)
(E/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
manifest={}
with tarfile.open(E/'raw-hardware.tar.gz','w:gz') as t:
 for root in ROOTS:
  for p in sorted(root.rglob('*')):
   if not p.is_file() or 'jtag-work' in p.parts or '__pycache__' in p.parts:continue
   name=str(Path(root.name)/p.relative_to(root));t.add(p,arcname=name,recursive=False);manifest[name]=hashlib.sha256(p.read_bytes()).hexdigest()
with tarfile.open(E/'raw-hardware.tar.gz') as t:
 for m in t.getmembers():assert hashlib.sha256(t.extractfile(m).read()).hexdigest()==manifest[m.name]
(E/'raw-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(__file__,E/'executed-validation-packager.py')
shutil.copy2(PM/'cfd_simulator/slow_integrator/plot_two_periods.py',E/'executed-plot.py')
print('BUFFERS valid/rejected',validation['valid_buffers'],validation['rejected_buffers'],'archive files',len(manifest))
