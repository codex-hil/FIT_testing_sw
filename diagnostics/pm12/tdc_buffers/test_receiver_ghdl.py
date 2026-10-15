"""Portable serial-only test; explicitly models FPGA counter power-up as zero.

Does NOT validate coarse capture, FIFO, clock generation or physical startup.
"""
import argparse
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--ghdl', default='ghdl')
a = p.parse_args()
root = Path(__file__).resolve().parent
source = (root / 'generated/TDCCHAN_instrumented.vhd').read_text()
anchor = 'signal C_BITS, TDC_bitcount : STD_LOGIC_VECTOR (2 downto 0);'
assert source.count(anchor) == 1
source = source.replace(anchor, 'signal C_BITS : STD_LOGIC_VECTOR (2 downto 0);\n'
                        'signal TDC_bitcount : STD_LOGIC_VECTOR (2 downto 0) := "000";')
work = root / 'generated/ghdl-serial'
work.mkdir(parents=True, exist_ok=True)
(work / 'TDCCHAN_sim.vhd').write_text(source)
def run(*args):
    subprocess.run([a.ghdl, *args], cwd=work, check=True)
run('-a', '--std=08', '-fsynopsys', 'TDCCHAN_sim.vhd', str(root / 'test_receiver.vhd'))
run('-e', '--std=08', '-fsynopsys', 'test_receiver')
run('-r', '--std=08', '-fsynopsys', 'test_receiver', '--assert-level=error', '--ieee-asserts=disable')
