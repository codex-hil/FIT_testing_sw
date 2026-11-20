#!/usr/bin/env python3
"""Upload a new dossier archive to SMB and verify its remote content hash.

Credentials are read from the specified private file and never logged or copied.
Requires pysmb in the caller's Python environment.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path,PurePosixPath
import socket
import uuid
from smb.SMBConnection import SMBConnection
import dossier


class Sink:
    def __init__(self):self.h=hashlib.sha256();self.n=0
    def write(self,data):self.h.update(data);self.n+=len(data)


def publish(manifest, credentials, share, directory):
    manifest=Path(manifest);record=dossier.read(manifest);archive=Path(record['archive'])
    if dossier.sha(archive)!=record['sha256']:raise ValueError('Local archive hash mismatch')
    remote=PurePosixPath(directory)
    if remote.is_absolute() or '..' in remote.parts or record['board_uid'] not in remote.parts:
        raise ValueError('Remote relative directory must contain the board UID')
    cfg=dossier.read(credentials)
    client=SMBConnection(cfg['username'],cfg['password'],socket.gethostname(),'GREG-CTI',use_ntlm_v2=True,is_direct_tcp=True)
    if not client.connect(cfg['host'],445,timeout=15):raise RuntimeError('SMB connection failed')
    try:
        parent=''
        for i,name in enumerate(remote.parts):
            entries={e.filename for e in client.listPath(share,parent or '/')}
            if i==len(remote.parts)-1 and name in entries:raise FileExistsError(directory)
            next_path=parent+'/'+name if parent else name
            if name not in entries:client.createDirectory(share,next_path)
            parent=next_path
        temporary=parent+'/'+archive.name+'.partial-'+uuid.uuid4().hex
        with archive.open('rb') as stream:client.storeFile(share,temporary,stream,timeout=180)
        sink=Sink();client.retrieveFile(share,temporary,sink,timeout=180)
        if sink.h.hexdigest()!=record['sha256'] or sink.n!=record['bytes']:
            raise ValueError('SMB readback mismatch; partial retained')
        final=parent+'/'+archive.name;client.rename(share,temporary,final)
        # Verify the final named file, as well as the temporary upload.
        sink=Sink();client.retrieveFile(share,final,sink,timeout=180)
        if sink.h.hexdigest()!=record['sha256']:raise ValueError('Final SMB readback mismatch')
        result=dict(board_uid=record['board_uid'],host=cfg['host'],share=share,directory=directory,
                    archive=final,sha256=sink.h.hexdigest(),bytes=sink.n,readback='PASS')
        data=(json.dumps(result,indent=2)+'\n').encode()
        client.storeFile(share,parent+'/remote-readback.json',io.BytesIO(data),timeout=30)
        # The original local manifest is immutable. Publication gets a new receipt.
        receipt=manifest.with_name(manifest.name+'.smb.json')
        with receipt.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
        with manifest.open('rb') as stream:client.storeFile(share,parent+'/package-manifest.json',stream,timeout=60)
        return result
    finally:client.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True);p.add_argument('--credentials',type=Path,required=True)
    p.add_argument('--share',required=True);p.add_argument('--directory',required=True)
    a=p.parse_args();print(json.dumps(publish(a.manifest,a.credentials,a.share,a.directory),indent=2))
