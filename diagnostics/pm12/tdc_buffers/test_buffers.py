"""Behavioral multi-clock tests; external events are modeled, not physical TDCs."""
from migen import *
from migen.sim import run_simulation, passive
from buffers import TdcBuffers

class DUT(Module):
    def __init__(self):
        for name in ['sys', 'tdc1', 'tdc2', 'tdc3']:
            setattr(self.clock_domains, 'cd_' + name, ClockDomain(name))
        self.submodules.buffers = TdcBuffers(depth=8)

d = DUT()
b = d.buffers
mode = {'emit': False, 'constant': False}

@passive
def producer(group):
    index = 0
    while True:
        for ch in range(group * 4, group * 4 + 4):
            yield b.events[ch].eq(mode['emit'])
            yield b.raw[ch].eq(0x123 if mode['constant'] else ((ch << 8) | (index & 255)))
        index += 1
        yield

def wait_for(signal, expected=1):
    for _ in range(150):
        if (yield signal) == expected:
            return
        yield
    raise AssertionError('bounded wait failed')

def arm():
    assert (yield b.ready)
    yield b.arm.eq(1)
    yield
    yield b.arm.eq(0)
    yield
    assert (yield b.busy) and not (yield b.valid)
    yield from wait_for(b.started)

def read(ch, count):
    out = []
    for i in range(count):
        yield b.address.eq(i)
        yield
        yield
        out.append((yield b.data[ch]))
    return out

def test():
    for _ in range(5): yield
    assert (yield b.ready) and not (yield b.valid)
    for trial in range(3):
        mode['constant'] = trial == 1
        mode['emit'] = False
        yield from arm()
        yield b.arm.eq(1)
        yield
        yield b.arm.eq(0)
        yield
        assert (yield b.rejected) and (yield b.busy)
        mode['emit'] = True
        yield from wait_for(b.valid)
        assert (yield b.capture_id) == trial + 1
        assert (yield b.ready)
        for ch in range(12):
            assert (yield b.counts[ch]) == 8
            words = yield from read(ch, 8)
            if mode['constant']:
                assert words == [0x123] * 8, words
            else:
                assert all(v >> 8 == ch for v in words), words
                assert all((v & 255) == ((words[0] + i) & 255) for i, v in enumerate(words)), words
            # Sources remain live after full: frozen memory must not change.
            for _ in range(9): yield
            assert (yield from read(ch, 8)) == words
    mode['emit'] = False
    yield from arm()
    yield b.stop.eq(1)
    yield
    yield b.stop.eq(0)
    yield from wait_for(b.valid)
    assert (yield b.capture_id) == 4
    for count in b.counts:
        assert (yield count) == 0
    mode['constant'] = True
    # Partial captures preserve a per-channel valid count, never stale tail data.
    yield from arm()
    mode['emit'] = True
    for _ in range(2): yield
    mode['emit'] = False
    for _ in range(6): yield
    yield b.stop.eq(1)
    yield
    yield b.stop.eq(0)
    yield from wait_for(b.valid)
    assert (yield b.capture_id) == 5
    for ch in range(12):
        count = (yield b.counts[ch])
        assert 0 < count < 8, (ch, count)
        assert (yield from read(ch, count)) == [0x123] * count
    print('PASS 12 independent event buffers: three asynchronous source clocks, full/freeze/rearm, repeated identical timestamps, busy rejection and empty stop')

run_simulation(d, {'sys': test(), 'tdc1': producer(0), 'tdc2': producer(1), 'tdc3': producer(2)},
               clocks={'sys': 10, 'tdc1': 6, 'tdc2': 8, 'tdc3': 14})
