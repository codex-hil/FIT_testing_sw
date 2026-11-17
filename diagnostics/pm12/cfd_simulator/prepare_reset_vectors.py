"""Prepare ISE iMPACT exports on Dell, then finalize channel-bound native vectors offline."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'adc/tools'))
from svf_to_tcl import convert
HASHES={'original.jed':'aaa241bed4dff4b362f1ca3bd875b8c168eb9998d07d583462ed72fadfb722ea',
        'reset.jed':'ce7cd3cff7fdf67517595cf912b5023d295d1e8853cd262153aefcb0ebf77a6b'}
BANK_HASHES={'B':HASHES,'A':dict(HASHES,**{'reset.jed':'90fb499c9a5bfefa732e83fbf3248a2c9e578aa4790b49eb3fc7d642f5b8d161'})}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare(source,out,remote,bank):
 hashes=BANK_HASHES[bank]
 out.mkdir(parents=True,exist_ok=False)
 for name in hashes:
  if digest(source/name)!=hashes[name]:raise ValueError('Unqualified JEDEC '+name)
  shutil.copy2(source/name,out/name)
 for ch in range(1,13):
  for name,operation,jed in [('program','program','reset.jed'),('restore','program','original.jed'),('verify-original','verify','original.jed')]:
   lines=['setMode -bs',f'setCable -port svf -file {remote}/ch{ch:02d}-{name}.svf']
   lines += [f'addDevice -p {i} -file {remote}/{jed}' for i in range(1,13)]
   lines += ['addDevice -p 13 -file /srv/nvme-fast-2/toolchains/ise/14.7/ISE_DS/ISE/kintex7/data/xc7k160t_ffg676.bsd',f'{operation} -p {ch}'+(' -e -v' if operation=='program' else ''),'quit']
   (out/f'ch{ch:02d}-{name}.cmd').write_text('\n'.join(lines)+'\n')
 (out/'bank.json').write_text(json.dumps(dict(bank=bank))+'\n')
 (out/'export.sh').write_text('set -eu\ncd '+remote+'\nset +u\nsource "$ISE_SETTINGS" "$(dirname "$ISE_SETTINGS")"\nset -u\nfor cmd in ch*.cmd; do impact -batch "$cmd" > "$cmd.log" 2>&1; done\n')
def finalize(root):
 bank=json.loads((root/'bank.json').read_text())['bank'];hashes=BANK_HASHES[bank]
 for name,value in hashes.items():
  if digest(root/name)!=value:raise ValueError('JEDEC hash mismatch')
 for ch in range(1,13):
  out=root/f'ch{ch:02d}';out.mkdir(exist_ok=False)
  for name in ['program','restore','verify-original']:
   text,count=convert((root/f'ch{ch:02d}-{name}.svf').read_text())
   # Verify that every non-BYPASS CPLD instruction addresses only this channel.
   import re
   for value in re.findall(r'scan_ir_hw_jtag 102 -tdi ([0-9a-f]+)',text):
    ops=[(int(value,16)>>(6+8*(12-c)))&255 for c in range(1,13)]
    if any(op!=255 and c!=ch for c,op in enumerate(ops,1)):raise ValueError('Wrong CPLD vector channel')
   (out/(name+'.tcl')).write_text(text)
  manifest=dict(schema=1,physical_channel=ch,mode='INT'+bank+'_HIGH_INT'+('B' if bank=='A' else 'A')+'_ORIGINAL',reset_bank=bank,jed_sha256=hashes,
                files={p.name:digest(p) for p in out.glob('*.tcl')})
  (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
 a=sub.add_parser('prepare');a.add_argument('--bank',choices=['A','B'],required=True);a.add_argument('--source',type=Path,required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('--remote',required=True)
 a=sub.add_parser('finalize');a.add_argument('--root',type=Path,required=True)
 a=p.parse_args()
 if a.action=='prepare':prepare(a.source,a.out,a.remote,a.bank)
 else:finalize(a.root)
