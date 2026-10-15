"""Elaborate receiver/buffer/IPbus-window wiring, without a board clock frontend.

Generated Verilog requires instrumented TDCCHAN, pin_capt and TDC_FIFO HDL.
This does not generate a deployable PM12 image.
"""
from pathlib import Path
from migen import *
from migen.fhdl import verilog
from receiver import TdcAcquisition

m = Module()
for name in ['sys', 'tdc1', 'tdc2', 'tdc3']:
    setattr(m.clock_domains, 'cd_' + name, ClockDomain(name))
m.submodules.acquisition = a = TdcAcquisition()
w = a.window
ports = set(a.cfd + a.rstr + a.rdata + a.clk300 + a.clk600 + a.clk600_90 + a.coarse_count + a.bc_time)
ports.update([a.receiver_reset,a.frontend_ready,w.address,w.wdata,w.write,w.commit,w.selected,w.error,w.rdata])
for name in ['sys', 'tdc1', 'tdc2', 'tdc3']:
    domain = getattr(m, 'cd_' + name)
    ports.update([domain.clk,domain.rst])
result = verilog.convert(m, ios=ports, name='pm12_tdc_acquisition')
out = Path(__file__).resolve().parent/'generated'
out.mkdir(exist_ok=True)
result.write(str(out/'pm12_tdc_acquisition.v'))
print('PASS elaboration: twelve original receiver instances and independent buffers/window; board frontend not included')
