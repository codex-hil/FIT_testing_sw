"""Real register FSM + event banks; no physical receiver is modeled here."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ipbus_adc'))
from migen import *
from migen.sim import run_simulation, passive
from capture import Capture
from analyzer import Analyzer
from registers import Registers
from buffers import TdcBuffers
from ipbus import TdcWindow

class DUT(Module):
    def __init__(self):
        for name in ['sys', 'cap', 'tdc1', 'tdc2', 'tdc3']:
            setattr(self.clock_domains, 'cd_' + name, ClockDomain(name))
        self.submodules.cap = Capture([Signal(14) for _ in range(12)], depth=8)
        self.submodules.trace = Analyzer(Signal(3), Signal(16), cycles=16, depth=8)
        self.submodules.b = TdcBuffers(depth=8)
        self.submodules.t = TdcWindow(self.b, timeout=200)
        self.submodules.r = Registers(self.cap, self.trace, tdc=self.t)

d = DUT()
r, b, t = d.r, d.b, d.t
mode = {'emit': False}
@passive
def producer(group):
    while True:
        for ch in range(group * 4, group * 4 + 4):
            yield b.raw[ch].eq(0x1000 + ch)
            yield b.events[ch].eq(mode['emit'])
        yield

def bus(addresses, values=None, error=False):
    out = []
    yield r.strobe.eq(1)
    yield r.write.eq(values is not None)
    for i, address in enumerate(addresses):
        yield r.address.eq(address)
        if values is not None:
            yield r.wdata.eq(values[i])
        yield
        for _ in range(30):
            if (yield r.ack): break
            yield
        else: raise AssertionError('ack timeout')
        assert (yield r.err) == error, (hex(address), (yield r.err))
        out.append((yield r.rdata))
    yield r.strobe.eq(0)
    yield
    yield
    return out

def rd(a, n=1, error=False): return (yield from bus(range(a,a+n), error=error))
def wr(a, v, error=False): return (yield from bus([a], [v], error))
def wait(signal):
    for _ in range(150):
        if (yield signal): return
        yield
    raise AssertionError('wait timeout')

def test():
    for _ in range(5): yield
    yield from rd(0x20000, error=True)
    yield from wr(0x200, 1, error=True)  # unqualified frontend
    yield t.frontend_ready.eq(1)
    yield
    yield from wr(0x200, 3, error=True)
    yield from wr(0x201, 1, error=True)
    yield from wr(0x200, 1)
    yield from wait(b.started)
    yield from wr(0x200, 1, error=True)
    yield from rd(0x20000, error=True)
    mode['emit'] = True
    yield from wait(t.valid)
    assert (yield from rd(0x203, 2)) == [8,12]
    assert (yield from rd(0x220, 12)) == [8]*12
    for ch in range(12):
        assert (yield from rd(0x20000 + (ch<<12), 8)) == [0x1000+ch]*8
        yield from rd(0x20008 + (ch<<12), error=True)
    yield from rd(0x2c000, error=True)
    mode['emit'] = False
    yield from wr(0x200, 1)
    yield from wait(b.started)
    yield from wr(0x200, 2)
    yield from wait(t.valid)
    assert (yield from rd(0x220, 12)) == [0]*12
    yield from rd(0x20000, error=True)  # old generation must be inaccessible
    assert (yield from rd(0x202)) == [2]
    # Source never completes: watchdog must mask the entire generation.
    yield from wr(0x200, 1)
    yield from wait(b.started)
    for _ in range(210): yield
    assert (yield t.fault) and not (yield t.valid)
    yield from wr(0x200, 1, error=True)
    mode['emit'] = True
    for _ in range(40): yield
    assert (yield b.valid) and not (yield t.valid)
    yield from rd(0x20000, error=True)
    assert (yield from rd(0x220,12)) == [0]*12
    # Existing register space remains functional.
    yield from wr(3, 0xa55a)
    assert (yield from rd(3)) == [0xa55a]
    print('PASS TDC IPbus: continuous-strobe bursts, 12 raw banks, bounds, empty STOP, stale-generation rejection, timeout fail-closed, legacy scratch')

run_simulation(d, {'sys':test(), 'tdc1':producer(0), 'tdc2':producer(1), 'tdc3':producer(2)},
               clocks={'sys':10,'cap':4,'tdc1':6,'tdc2':8,'tdc3':14})

# A different capture fails immediately when frontend qualification disappears.
d = DUT()
r, b, t = d.r, d.b, d.t
mode['emit'] = False
def lost_lock():
    yield t.frontend_ready.eq(1)
    for _ in range(5): yield
    assert (yield from rd(1)) == [0x10002]
    assert (yield from rd(9)) == [31]
    yield from wr(0x200, 1)
    yield from wait(b.started)
    yield t.frontend_ready.eq(0)
    for _ in range(3): yield
    assert (yield t.fault) and not (yield t.valid)
    yield t.frontend_ready.eq(1)
    for _ in range(3): yield
    yield from wr(0x200, 2, error=True)
    yield from wr(0x200, 1, error=True)
    yield from rd(0x20000, error=True)
    print('PASS frontend lock loss: sticky fault, no stale read or rearm after relock')
run_simulation(d, {'sys':lost_lock(), 'tdc1':producer(0), 'tdc2':producer(1), 'tdc3':producer(2)},
               clocks={'sys':10,'cap':4,'tdc1':6,'tdc2':8,'tdc3':14})

d = DUT()
r, b, t = d.r, d.b, d.t
def missing_clock():
    # No result clocks are scheduled at all, even though readiness was claimed.
    yield t.frontend_ready.eq(1)
    for _ in range(5): yield
    yield from wr(0x200, 1)
    for _ in range(220): yield
    assert not (yield b.started) and (yield t.fault)
    yield from rd(0x20000, error=True)
    yield from wr(0x200, 1, error=True)
    print('PASS missing result clocks: bounded start timeout, invalid bank and rearm rejection')
run_simulation(d, missing_clock(), clocks={'sys':10,'cap':4})
