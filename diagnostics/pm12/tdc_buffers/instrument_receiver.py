#!/usr/bin/env python3
"""Add an observational raw-commit pulse to a pinned original TDCCHAN copy."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

REVISION = '857b773eec28282b357d4668ab934e95f41b6fe7'
SOURCE = 'firmware/FT0/PM/hdl/TDCCHAN.vhd'
EXPECTED = 'dde8d417ef7770b329e853cb845d43b8d74e0259ea37f86647695c817f8bf833'

def instrument(raw):
    if hashlib.sha256(raw).hexdigest() != EXPECTED:
        raise ValueError('unexpected original receiver bytes')
    edits = [
        ('tdc_raw_lock : in STD_LOGIC\n', 'tdc_raw_lock : in STD_LOGIC;\n           diag_raw_valid : out STD_LOGIC\n'),
        ("if (tdcclk'event and tdcclk='1') then \n", "if (tdcclk'event and tdcclk='1') then \n    diag_raw_valid <= '0';\n"),
        ('TDC_raw_i<=C_FIFO(5 downto 0) & TDC(6 downto 0);',
         "TDC_raw_i<=C_FIFO(5 downto 0) & TDC(6 downto 0); diag_raw_valid <= '1';"),
    ]
    text = raw.decode('ascii')
    for before, after in edits:
        if text.count(before) != 1:
            raise ValueError('receiver edit anchor must occur exactly once')
        text = text.replace(before, after)
    return text.encode('ascii')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--out', type=Path, default=Path(__file__).parent/'generated')
    args = parser.parse_args()
    raw = subprocess.check_output(['git', '-C', str(args.repository), 'show', REVISION+':'+SOURCE])
    output = instrument(raw)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/'TDCCHAN.vhd').write_bytes(raw)
    (args.out/'TDCCHAN_instrumented.vhd').write_bytes(output)
    (args.out/'manifest.json').write_text(json.dumps({
        'revision': REVISION, 'source': SOURCE, 'original_sha256': EXPECTED,
        'instrumented_sha256': hashlib.sha256(output).hexdigest(),
        'changes': 'one new output, default zero each rising tdcclk, pulse only at original unlocked raw commit',
        'status': 'generated observational hook; run tests separately; full coarse/FIFO/clock and hardware qualification pending',
    }, indent=2)+'\n')
    print('PASS pinned receiver extraction and three unique observational edit anchors')

if __name__ == '__main__':
    main()
