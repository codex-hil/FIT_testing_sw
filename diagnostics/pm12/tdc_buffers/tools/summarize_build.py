"""Seal the routed build and explicit timing scope before hardware use."""
from pathlib import Path
import hashlib,json,re
root=Path(__file__).resolve().parents[1];board=root/'generated/board';build=board/'build'
timing=(build/'timing.txt').read_text();drc=(build/'drc.txt').read_text();util=(build/'utilization.txt').read_text()
assert 'All user specified timing constraints are met.' in timing
assert 'checking no_clock (0)' in timing and 'checking unconstrained_internal_endpoints (0)' in timing
assert not re.search(r'\|\s*(Error|Critical Warning)\s*\|',drc)
lines=timing.splitlines();heading=next(i for i,line in enumerate(lines) if line.strip().startswith('WNS(ns)'))
values=lines[heading+2].split();wns,whs,wpws=map(float,[values[0],values[4],values[8]])
assert min(wns,whs,wpws)>=0
files=['pm12_ipbus_adc.bit','timing.txt','drc.txt','utilization.txt','pm12_ipbus_adc.dcp']
record=dict(build_id=(board/'build-id.txt').read_text().strip(),part='xc7k160tffg676-3',timing_pass=True,setup_slack_ns=wns,hold_slack_ns=whs,pulse_width_slack_ns=wpws,bram36_equivalents=int(re.search(r'Block RAM Tile\s*\|\s*(\d+)',util)[1]),scope='Routed internal timing and upstream serial input delays. CFD sampling aperture is intentionally asynchronous; external stimulus accuracy/phase sweep NOT_RUN.',sha256={f:hashlib.sha256((build/f).read_bytes()).hexdigest() for f in files},gateware_source_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in [root/'buffers.py',root/'ipbus.py',root/'receiver.py',root/'frontend.py',root/'tdc-ip.tcl',root/'tdc-timing.tcl']})
(build/'qualification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
