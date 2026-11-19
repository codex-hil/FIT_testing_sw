"""Portable board dossier: explicit selections, content-addressed evidence, offline verify.

No hardware, network or report rendering. Original files are never modified.
"""
import argparse,hashlib,json,shutil,datetime
from pathlib import Path
from identity import board_uid

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def contained(root,relative):
 p=(root/relative).resolve()
 if not p.is_relative_to(root.resolve()):raise ValueError('Path escapes dossier')
 return p

def build(spec_path,out):
 spec=read(spec_path);uid=spec['board_uid']
 if board_uid(uid.removeprefix('PM12-K7-'))!=uid:raise ValueError('Invalid board UID')
 out=Path(out);out.mkdir(parents=True,exist_ok=False);(out/'blobs').mkdir()
 release={'schema':1,'board_uid':uid,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':spec['scope'],'cases':[],'open_items':spec.get('open_items',[]),'identities':spec.get('identities',[]),'scope_exclusions':spec.get('scope_exclusions',[])}
 keys=set()
 for selection in spec['selections']:
  case=selection['case']
  if case in keys:raise ValueError('Duplicate case selection')
  keys.add(case);src=Path(selection['source']).resolve();record=read(src/selection['receipt'])
  observed=record.get('board_uid',record.get('uid'))
  if observed!=uid:raise ValueError('Wrong/missing board UID in selected receipt: '+case)
  if record.get('status')!=selection['status']:raise ValueError('Selected status differs from receipt')
  for relative in record.get('source_files',[]):
   if not contained(src,relative).is_file():raise ValueError('Receipt references missing source: '+relative)
  if record.get('original_summary') and not contained(src,record['original_summary']).is_file():raise ValueError('Missing original diagnostic summary')
  channel=selection.get('channel')
  if record.get('channel',record.get('physical_channel'))!=channel:raise ValueError('Selected receipt has wrong physical channel')
  row=dict(case=case,channel=channel,test=selection['test'],status=selection['status'],basis=selection['basis'],method=selection['method'],measured_utc=selection.get('measured_utc'),receipt=selection['receipt'],files={})
  for p in sorted(src.rglob('*')):
   if not p.is_file() or '__pycache__' in p.parts or 'jtag-work' in p.parts:continue
   if p.is_symlink():raise ValueError('Symlink in evidence source')
   digest=sha(p);target=out/'blobs'/digest
   if not target.exists():shutil.copyfile(p,target)
   elif sha(target)!=digest:raise ValueError('Corrupt existing evidence blob')
   row['files'][str(p.relative_to(src))]=digest
  release['cases'].append(row)
 missing=set(spec['required_cases'])-keys
 if missing:raise ValueError('Missing selections: '+str(sorted(missing)))
 release['coverage']={'required_cases':len(spec['required_cases']),'included_cases':len(keys),'statuses':{s:sum(r['status']==s for r in release['cases']) for s in sorted({r['status'] for r in release['cases']})}}
 # This is coverage and evidence disposition, not a rewrite of sealed campaign approvals.
 release['disposition']='REVIEW' if release['open_items'] or any(r['status'] not in ('PASS','PASS_FUNCTIONAL') for r in release['cases']) else 'FUNCTIONAL_DATA_COMPLETE'
 write(out/'release.json',release);write(out/'selection.json',spec)
 write(out/'files.sha256.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file()})
 return verify(out)

def verify(root):
 root=Path(root).resolve();m=read(root/'files.sha256.json')
 actual={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name!='files.sha256.json'}
 if m!=actual:raise ValueError('Dossier file hash mismatch')
 d=read(root/'release.json');uid=d['board_uid'];keys=set()
 for r in d['cases']:
  if r['case'] in keys:raise ValueError('Duplicate case')
  keys.add(r['case'])
  for name,h in r['files'].items():
   if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Invalid content hash')
   if sha(contained(root,'blobs/'+h))!=h:raise ValueError('Evidence blob modified')
   contained(Path('/tmp/dossier-contained'),name)
  receipt=read(root/'blobs'/r['files'][r['receipt']])
  if receipt.get('board_uid',receipt.get('uid'))!=uid:raise ValueError('Mixed board identities')
 return dict(board_uid=uid,integrity='PASS',coverage=d['coverage'],disposition=d['disposition'],open_items=d['open_items'])

def materialize(root,case,out):
 verify(root);root=Path(root);d=read(root/'release.json');r=next(r for r in d['cases'] if r['case']==case);out=Path(out);out.mkdir(parents=True,exist_ok=False)
 for n,h in r['files'].items():
  dest=contained(out,n);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/'blobs'/h,dest)

def export(root,out):
 verify(root);root=Path(root);d=read(root/'release.json');out=Path(out);out.mkdir(parents=True,exist_ok=False)
 import csv
 cases=[];series=[]
 for row in d['cases']:
  receipt=read(root/'blobs'/row['files'][row['receipt']]);cases.append(dict(index=row,measurement=receipt))
  for curve in receipt.get('curves',[]):
   if len(curve.get('x',[]))!=len(curve.get('y',[])):raise ValueError('Curve length mismatch')
   for i,(x,y) in enumerate(zip(curve.get('x',[]),curve.get('y',[]))):
    series.append(dict(board_uid=d['board_uid'],case=row['case'],channel=row['channel'],method=row['method'],curve=curve.get('name'),bank=curve.get('bank'),x_unit=curve.get('x_unit'),y_unit=curve.get('y_unit'),point=i,x=x,y=y))
 write(out/'measurements.json',dict(board_uid=d['board_uid'],coverage=d['coverage'],cases=cases,open_items=d['open_items'],scope_exclusions=d.get('scope_exclusions',[])))
 with (out/'coverage.csv').open('w',newline='') as f:
  columns=['case','test','channel','status','method','measured_utc','basis'];w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(d['cases'])
 with (out/'series.csv').open('w',newline='') as f:
  columns=['board_uid','case','channel','method','curve','bank','x_unit','y_unit','point','x','y'];w=csv.DictWriter(f,fieldnames=columns);w.writeheader();w.writerows(series)
 return {'cases':len(cases),'series_points':len(series),'board_uid':d['board_uid']}


def main():
 p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='action',required=True)
 b=s.add_parser('build');b.add_argument('--selection',type=Path,required=True);b.add_argument('--out',type=Path,required=True)
 v=s.add_parser('verify');v.add_argument('--root',type=Path,required=True)
 e=s.add_parser('export');e.add_argument('--root',type=Path,required=True);e.add_argument('--out',type=Path,required=True)
 x=s.add_parser('extract');x.add_argument('--root',type=Path,required=True);x.add_argument('--case',required=True);x.add_argument('--out',type=Path,required=True)
 a=p.parse_args()
 if a.action=='build':r=build(a.selection,a.out)
 elif a.action=='verify':r=verify(a.root)
 elif a.action=='export':r=export(a.root,a.out)
 else:materialize(a.root,a.case,a.out);r={'extracted':a.case}
 print(json.dumps(r,indent=2))
if __name__=='__main__':main()
