from pathlib import Path
import hashlib,json,shutil
r=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/acceptance/evidence-group01-04-20261117');src=r/'group14-delta.tar.gz';store=Path('/srv/codex-hil-nvme/pm12-group14-packaging-20261117');store.mkdir(exist_ok=True);full=store/src.name
shutil.copy2(src,full)
def digest(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
assert digest(src)==digest(full);h=hashlib.sha256();parts=[]
with full.open('rb')as f:
 i=1
 while b:=f.read(40*1024*1024):
  p=r/(src.name+f'.part{i:03d}');p.write_bytes(b);h.update(b);parts.append(dict(file=p.name,bytes=len(b),sha256=digest(p)));i+=1
assert h.hexdigest()==digest(full)
metadata=dict(compressed_archive=src.name,bytes=full.stat().st_size,sha256=h.hexdigest(),parts=parts,instructions='Concatenate part001,part002,part003 in order to reconstruct group14-delta.tar.gz. Extract original base into a NEW directory, then overlay reconstructed delta. Do not overwrite live data.')
(r/'archive-parts.json').write_text(json.dumps(metadata,indent=2)+'\n');src.unlink()
p=r/'delta-provenance.json';d=json.loads(p.read_text());d['delta_archive_parts']='archive-parts.json';d['delta_archive_sha256']=metadata['sha256'];d['instructions']=metadata['instructions'];p.write_text(json.dumps(d,indent=2)+'\n')
p=r/'README.md';p.write_text(p.read_text()+'''\nThe compressed cumulative archive is split into40MiB parts for Git hosting.\nConcatenate group14-delta.tar.gz.part001,part002,part003 in that order to obtain\ngroup14-delta.tar.gz; sizes/hashes are in archive-parts.json. Then apply the original\nbase plus reconstructed delta to a NEW directory. A verified complete local copy\nis also retained outside Git. No acquisition data was deleted.\n''')
print(json.dumps(metadata,indent=2))
