"""Frozen-download integrity checks; simulated transport, no network or hardware."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from client_tdc import download

class Transport:
    def __init__(self, fault=None):self.fault=fault
    def read(self,address,count=1):
        if address==0:return [0x504d1202]
        if address==1:return [0x10002]
        if address==0x201:return ([1,8] if self.fault=='generation' else [1,7]) if count==2 else [33 if self.fault=='fault' else 1]
        if address==0x202:return [7,4096,12]
        if address==0x220:return [4097 if self.fault=='count' else 3]*12
        raise AssertionError(hex(address))
    def block(self,address,count):return [0x2000 if self.fault=='reserved' else (address>>12)]*count

ident,status,counts,data=download(Transport())
assert ident==7 and status==1 and counts==[3]*12
assert data==[[0x20+ch]*3 for ch in range(12)]
for mode in ['fault','generation','reserved','count']:
    try:download(Transport(mode))
    except RuntimeError:pass
    else:raise AssertionError('accepted '+mode)
print('PASS simulated TDC download: 12 banks and fail-closed fault/generation/reserved-bits/count guards')
