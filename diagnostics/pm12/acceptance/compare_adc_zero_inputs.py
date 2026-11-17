#!/usr/bin/env python3
"""Offline zero-input waveform/FFT overlays from explicitly selected ADC receipts."""
import argparse,hashlib,json,math,shutil
from pathlib import Path

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--receipts',type=Path,nargs='+',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 a.out.mkdir(parents=True,exist_ok=True);inputs=a.out/'zero-input-figure-inputs';inputs.mkdir(exist_ok=True);records={};hashes={}
 for path in a.receipts:
  r=json.loads(path.read_text());assert r['status']=='PASS'and r['test']=='adc-dc'and r['channel']not in records
  records[r['channel']]=r;dest=inputs/f"pm{r['channel']:02d}.json"
  if path.resolve()!=dest.resolve():shutil.copy2(path,dest)
  hashes[dest.name]=hashlib.sha256(dest.read_bytes()).hexdigest()
 assert len({r['board_uid']for r in records.values()})==1
 for kind in ['time','fft']:
  fig,axes=plt.subplots(2,1,figsize=(10,7),layout='constrained',sharex=True)
  for ch,r in sorted(records.items()):
   for ax,bank in zip(axes,'AB'):
    c=next(v for v in r['curves']if v['name']=='zero_input_'+kind and v['bank']==bank);x,y=c['x'],c['y'];assert len(x)==len(y)and all(math.isfinite(v)for v in x+y)
    if kind=='fft':ax.semilogy([v/1e6 for v in x[1:]],[max(v,1e-9)for v in y[1:]],label=f'PM {ch}')
    else:ax.plot(x,y,'.-',ms=3,label=f'PM {ch}')
    ax.set_title('ADC '+bank);ax.grid(alpha=.2);ax.legend(ncol=3);ax.set_ylabel('ADC code RMS/bin'if kind=='fft'else'ADC code')
  axes[-1].set_xlabel('Assumed frequency (MHz)'if kind=='fft'else'Local capture time (ns)')
  fig.suptitle('Zero differential input: '+('one-sided RMS spectrum'if kind=='fft'else'raw waveforms; capture phases not aligned'))
  for ext in ['png','pdf']:fig.savefig(a.out/f'adc-zero-{kind}.{ext}',dpi=180)
  plt.close(fig)
 (a.out/'zero-input-figure-provenance.json').write_text(json.dumps(dict(board_uid=next(iter(records.values()))['board_uid'],channels=sorted(records),inputs_sha256=hashes,scope='Explicit PASS receipts; local capture origins, assumed80.1574MS/s, whole-chain code fluctuations, no intrinsic ADC noise/jitter claim',generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()),indent=2)+'\n')
if __name__=='__main__':main()
