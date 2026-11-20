#!/usr/bin/env python3
"""Package a verified dossier release; hash and read back every archived file.

No hardware or network access. Archive and external manifest never overwrite.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import dossier


def pack(root, archive):
    root=Path(root).resolve();archive=Path(archive).resolve()
    validation=dossier.verify(root/'dossier')
    if archive.is_relative_to(root):raise ValueError('Archive must be outside its input tree')
    manifest=archive.with_name(archive.name+'.manifest.json')
    if manifest.exists():raise FileExistsError(manifest)
    expected={str(p.relative_to(root)):dossier.sha(p) for p in sorted(root.rglob('*')) if p.is_file()}
    for p in root.rglob('*'):
        if p.is_symlink():raise ValueError('Symlink in release source')
    with tarfile.open(archive,'x:gz') as stream:stream.add(root,arcname=root.name)
    with tarfile.open(archive,'r:gz') as stream:
        observed={str(Path(m.name).relative_to(root.name)):hashlib.sha256(stream.extractfile(m).read()).hexdigest()
                  for m in stream.getmembers() if m.isfile()}
    if expected!=observed:raise ValueError('Archive readback differs from release')
    result=dict(board_uid=validation['board_uid'],archive=str(archive),sha256=dossier.sha(archive),
                bytes=archive.stat().st_size,archive_readback='PASS',dossier=validation,file_hashes=expected)
    with manifest.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    return {k:v for k,v in result.items() if k!='file_hashes'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--archive',type=Path,required=True)
    a=p.parse_args();print(json.dumps(pack(a.root,a.archive),indent=2))
