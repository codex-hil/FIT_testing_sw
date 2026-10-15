from pathlib import Path
from migen import *
from migen.fhdl import verilog
from buffers import TdcBuffers

dut = Module()
for name in ['sys', 'tdc1', 'tdc2', 'tdc3']:
    setattr(dut.clock_domains, 'cd_' + name, ClockDomain(name))
dut.submodules.buffers = b = TdcBuffers()
ios = {b.arm,b.stop,b.ready,b.started,b.busy,b.valid,b.done,b.rejected,b.capture_id,b.address}
ios.update(b.events + b.raw + b.data + b.counts)
for name in ['sys', 'tdc1', 'tdc2', 'tdc3']:
    domain = getattr(dut, 'cd_' + name)
    ios.update([domain.clk, domain.rst])
out = Path(__file__).parent/'generated'
out.mkdir(exist_ok=True)
verilog.convert(dut, ios=ios, name='tdc_buffers').write(str(out/'tdc_buffers.v'))
