import sys,json,datetime
from pathlib import Path
A=Path('/home/codex-hil/fit-testing-publish/diagnostics/pm12/acceptance');sys.path.insert(0,str(A));import board_session as b
from station import load_dependencies
from boundary import physical_identity
from link_recovery import restart
cfg=b.read('/srv/codex-hil-nvme/pm12-board-sessions/PM12-K7-2A17A1B40221242B/20261120T151926Z-6e0ce39f/station.json');load_dependencies(cfg);from client import Client
O=Path('/srv/codex-hil-nvme/pm12-board-sessions')/b.uid(cfg)/'setup'/(datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-phy-retry');O.mkdir();r={'status':'ERROR','board_uid':b.uid(cfg),'started_utc':b.now(),'kasli_reads':[]}
with b.locks(cfg):
 try:
  c=Client('192.168.2.241');c.s.settimeout(.35)
  try:
   for i in range(50):
    v=c.read(0,2);assert v==[0x52504831,0x10002],v;r['kasli_reads'].append(v)
   r['kasli_retries']=c.read_retry_events;assert not c.read_retry_events
  finally:c.close()
  r['physical_identity']=physical_identity(cfg,O/'physical-identity');r['restart']=restart(cfg,O);r['status']='COMPLETE'
 except BaseException as e:r['error']=repr(e)
 finally:r['finished_utc']=b.now();b.write(O/'result.json',r);b.write(O/'files.sha256.json',b.files(O))
print(json.dumps({'path':str(O),'status':r['status'],'error':r.get('error'),'kasli_ok':len(r['kasli_reads'])}))
