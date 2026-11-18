import json,struct,collections
from pathlib import Path

def assess(w):
 edges=[i for i in range(1,len(w)) if w[i]&8192 and not w[i-1]&8192];edges=[e for e in edges if 5<=e<len(w)-4];result={}
 for offset in [-2,-1,0,1,2]:
  bad=[e for e in edges if (w[e+offset]^w[e+offset-1])&4095];bits=collections.Counter(bit for e in bad for bit in range(12) if ((w[e+offset]^w[e+offset-1])>>bit)&1)
  result[str(offset)]={'bad_pairs':len(bad),'edges':len(edges),'bits':dict(bits),'examples':[{'edge':e,'words_hex':[f'{w[i]:04x}' for i in range(e-4,e+5)],'data':[w[i]&4095 for i in range(e-4,e+5)],'str':[(w[i]>>13)&1 for i in range(e-4,e+5)]} for e in bad[:8]]}
 return result
if __name__=='__main__':
 root=Path('/srv/codex-hil-nvme/pm12-ch02-20261118');out={}
 for scan in root.glob('adc-lines-attempt*/scan'):
  for f in scan.glob('*.bin'):
   if f.name=='final-zero-bank0.bin':continue
   w=struct.unpack('<4096H',f.read_bytes());r=assess(w)
   if r['-1']['bad_pairs']:out[str(f.relative_to(root))]=r
 Path(__file__).with_name('historical-windows.json').write_text(json.dumps(out,indent=2)+'\n')
 for n,r in out.items():print(n,[(k,v['bad_pairs']) for k,v in r.items()],r['-1']['examples'][:1])
