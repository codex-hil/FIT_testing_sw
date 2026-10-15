"""Record offline test results; requires Migen Python and an explicit GHDL tool."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--ghdl', default='ghdl')
a = p.parse_args()
root = Path(__file__).resolve().parent
commands = [
    [sys.executable, str(root/'test_buffers.py')],
    [sys.executable, str(root/'test_ipbus.py')],
    [sys.executable, str(root/'test_receiver_ghdl.py'), '--ghdl', a.ghdl],
    [sys.executable, str(root.parent/'ipbus_adc/test_registers.py')],
]
results = []
for command in commands:
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout, end='')
    if result.stderr:
        print(result.stderr, file=sys.stderr, end='')
    results.append(dict(command=command, returncode=result.returncode,
                        stdout=result.stdout, stderr=result.stderr))
report = dict(timestamp=datetime.now(timezone.utc).isoformat(),
              scope='OFFLINE simulations; serial coarse/FIFO stubbed and counter power-up explicitly modeled; no board programming',
              passed=all(r['returncode'] == 0 for r in results), results=results,
              source_sha256={str(f.relative_to(root.parent)):hashlib.sha256(f.read_bytes()).hexdigest()
                             for f in sorted(list(root.glob('*.py')) + [root/'test_receiver.vhd', root.parent/'ipbus_adc/registers.py'])})
(root/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
raise SystemExit(0 if report['passed'] else 1)
