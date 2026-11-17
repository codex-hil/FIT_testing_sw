from pathlib import Path
import csv,hashlib,json,shutil,tarfile
repo=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12')
root=Path('/srv/codex-hil-nvme/pm12-reset-standard-run01-20261117')
campaign=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/reset-standard-20261117')
e=repo/'cfd_simulator/evidence-reset-standard-20261117';e.mkdir(exist_ok=False)
receipt=json.loads((root/'receipt/campaign-result.json').read_text())
assert receipt['status']=='PASS'
shutil.copy2(root/'receipt/campaign-result.json',e/'campaign-result.json')
shutil.copy2(root/'receipt/validation.json',e/'validation.json')
for bank in 'AB':
 for name in ['reset-transfer.png','reset-transfer.pdf','summary.json']:
  shutil.copy2(root/'run'/bank/'analysis'/name,e/(bank+'-'+name))
for name in ['reset-correlation.csv','reset-correlation.png','reset-correlation.pdf','coverage.json']:
 shutil.copy2(root/'correlation'/name,e/name)
manifest={}
with tarfile.open(e/'raw-standard-run.tar.gz','w:gz') as t:
 for prefix,source in [('measurement',root),('campaign',campaign)]:
  for p in sorted(source.rglob('*')):
   if not p.is_file() or 'jtag-work' in p.parts or '__pycache__' in p.parts:continue
   name=str(Path(prefix)/p.relative_to(source));t.add(p,arcname=name,recursive=False);manifest[name]=hashlib.sha256(p.read_bytes()).hexdigest()
with tarfile.open(e/'raw-standard-run.tar.gz') as t:
 for m in t.getmembers():assert hashlib.sha256(t.extractfile(m).read()).hexdigest()==manifest[m.name]
(e/'raw-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
shutil.copy2(__file__,e/'executed-packager.py')
ms={(m['name'],m.get('bank')):m['value'] for m in receipt['metrics']}
for bank in 'AB':
 print(bank,'R P/N',[ms['reset_R_'+leg,bank] for leg in ['P','N']], 'amplitude',ms[f'during_reset_{bank}_normal-before_amplitude',bank])
print('RAW_ARCHIVE_READBACK_VERIFIED',len(manifest))
