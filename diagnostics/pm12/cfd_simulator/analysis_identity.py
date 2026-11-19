"""Read-only identity binding for offline analyses; never infer identity from IP/channel."""
import json,re
from pathlib import Path

def context(directory):
 directory=Path(directory).resolve()
 for parent in [directory,*list(directory.parents)[:4]]:
  record=parent/'measurement.json'
  if record.is_file():
   data=json.loads(record.read_text())
   if data.get('status')!='COMPLETE':raise ValueError('Parent measurement is not complete')
   if data.get('board_uid'):return data['board_uid'],data.get('phase_code')
  station=parent/'station.json'
  if station.is_file():
   data=json.loads(station.read_text())
   if data.get('board_uid'):return data['board_uid'],None
 raise ValueError('No board identity context for '+str(directory))

def require_same(directories,expected=None,phase=None):
 records=[context(p) for p in directories];uids={r[0] for r in records}
 if len(uids)!=1:raise ValueError('Cannot combine different physical boards')
 uid=next(iter(uids))
 if not re.fullmatch(r'PM12-K7-[0-9A-F]{16}',uid) or int(uid[8:],16) in (0,(1<<64)-1):raise ValueError('Noncanonical hardware identity')
 if expected is not None and uid!=expected:raise ValueError('Analysis board UID mismatch')
 if phase is not None and any(r[1] is not None and r[1]!=phase for r in records):raise ValueError('Analysis phase differs from measurement setting')
 return uid
