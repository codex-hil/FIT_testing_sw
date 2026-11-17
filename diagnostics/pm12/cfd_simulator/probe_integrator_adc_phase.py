"""Diagnostic ADC coherency at a few DAC-A phase settings; always restore A=0."""
import argparse
import contextlib
import datetime
import json
from pathlib import Path
import struct
import sys
import time

HERE = Path(__file__).resolve().parent
PM = HERE.parent
sys.path[:0] = [str(PM/'acceptance'), str(HERE), str(PM/'ipbus_adc'),
                '/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from lease import acquire
from station import console
from console import ConsoleI2C, Registers
from mcp23017 import afe_route
from phase_scan import ConsoleDAC
from pm12_console_regression import capture
from pm12_power import wait_power_good, require_power_good
from channel_settings import adc_address, require_serial_reply, snapshot_sources
from mod_dac28 import remote_lease, DAC
from client import Client
from adc_decode import decode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--afe', type=int, choices=range(1, 13), required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--codes', type=int, nargs='+', default=[0, 16384, 32768, 49152, 65535])
    parser.add_argument('--delta-v', type=float, default=0.0,
                        help='Relative differential offset from DAC2/3=1.024/2.048 V')
    args = parser.parse_args()
    if any(not 0 <= code <= 65535 for code in args.codes):
        parser.error('Phase codes must be 0..65535')
    voltages = [round(1.024 + args.delta_v/2, 4), round(2.048 - args.delta_v/2, 4)]
    if not all(0 <= v <= 3.3 for v in voltages):
        parser.error('External DAC setpoints must be 0..3.3 V')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    r = dict(physical_channel=args.afe, mode='LIVE_DIAGNOSTIC', points=[], uart=[],
             complete=False, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    r.update(requested_phase_codes=args.codes, external_setpoints_V=voltages,
             relative_delta_V=args.delta_v)
    r['sources'] = snapshot_sources(out, ['__main__', 'lease', 'station', 'console',
        'mcp23017', 'phase_scan', 'pm12_console_regression', 'pm12_power',
        'channel_settings', 'mod_dac28', 'client', 'adc_decode'])
    save = lambda: (out/'phase-probe.json').write_text(json.dumps(r, indent=2)+'\n')
    save()
    with contextlib.ExitStack() as stack:
        for name in sorted(['atmel-ice-J41800043065', 'pm12-210249A73E43',
                            'kasli-diot-00001', 'esp32-6825dd4c49e4', 'lattice-VER00001']):
            stack.enter_context(acquire(Path.home()/'.cache'/(name+'.lock')))
        u = stack.enter_context(console(dict(uart='/dev/serial/by-id/'
            'usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0')))
        c = Client()
        stack.callback(c.close)
        r['pgood'] = wait_power_good(u, capture)
        r['mcu'] = capture(u, 'RS')
        require_serial_reply(r['mcu']['reply'], '1803')
        r['fpga'] = c.read(0, 3)
        assert r['fpga'] == [0x504d1202, 0x10002, 0xff2f746c]
        remote = stack.enter_context(remote_lease())
        dac = DAC(remote, channels=[2, 3])
        stack.callback(dac.close)
        bus = ConsoleI2C(u, capture)
        phase = ConsoleDAC(u, args.afe, capture, r['uart'].append)
        try:
            dac.park(*voltages)
            with bus.routed(*afe_route(args.afe)):
                regs = Registers(bus)
                assert regs.read(10) == regs.read(11) and not regs.read(10) & 128
                regs.write(0x15, regs.read(0x15) | 0x20)
                regs.write(1, regs.read(1) & ~0x20)
                regs.write(0x14, regs.read(0x14) | 0x88)
                regs.write(0, regs.read(0) & ~0x88)
                regs.write(0x14, (regs.read(0x14) & ~0x80) | 8)
                for code in args.codes:
                    require_power_good(u, capture)
                    before = c.read(5, 2)
                    phase.set_code(code)
                    time.sleep(.2)
                    row = dict(code=code, captures=[])
                    r['points'].append(row)
                    for bank in [0, 1]:
                        for repeat in range(3):
                            generation, status = c.acquire(bank, False)
                            words = c.block(adc_address(args.afe), 4096)
                            assert c.read(0x12) == [generation]
                            name = f'phase{code:05d}-bank{bank}-{repeat}.bin'
                            (out/name).write_bytes(struct.pack('<4096H', *words))
                            cap = dict(bank=bank, file=name, generation=generation,
                                       hardware_status=status, valid=False)
                            try:
                                _, timing = decode(words, bank)
                                cap.update(valid=True, timing=timing)
                            except ValueError as ex:
                                cap['decode_error'] = str(ex)
                            row['captures'].append(cap)
                            save()
                    after = c.read(5, 2)
                    assert after[0]+(after[1] << 32) >= before[0]+(before[1] << 32)
                    row['uptime_before'], row['uptime_after'] = before, after
                    print('PHASE', code, 'VALID', sum(v['valid'] for v in row['captures']), '/6', flush=True)
            r['valid_codes'] = [p['code'] for p in r['points'] if all(v['valid'] for v in p['captures'])]
            r['complete'] = True
        finally:
            try:
                dac.park(1.024, 2.048)
                r['restored_external_setpoints_V'] = [1.024, 2.048]
                require_power_good(u, capture)
                phase.set_code(0)
                r['restored_phase_code'] = 0
                with bus.routed(*afe_route(args.afe)):
                    regs = Registers(bus)
                    regs.write(0x14, regs.read(0x14) | 0x88)
                    regs.write(0x15, regs.read(0x15) | 0x20)
                    assert regs.read(0x12) & 0x88 == 0x88
                    r['final_gpio'] = {str(a):regs.read(a) for a in [0, 1, 0x12, 0x13, 0x14, 0x15]}
                r['tca_final'] = {str(a):bus.mux(a) for a in [0x70, 0x71]}
                assert set(r['tca_final'].values()) == {0}
            finally:
                r['scpi'] = dac.records
                r['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                save()
    print('VALID_PHASE_CODES', r['valid_codes'], flush=True)


if __name__ == '__main__':
    main()
