"""Diagnostic common-shift sweep using the frozen native integrator acquisition.

No qualification status or campaign selection is changed. Delta is relative to
the two reference setpoints, not an absolute DAC2-DAC3 voltage of delta.
"""
import argparse
import contextlib
import datetime
import hashlib
import json
import math
import os
import shutil
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PM = HERE.parent
sys.path[:0] = [str(PM/'acceptance'), str(HERE), str(PM/'ipbus_adc'),
                '/home/codex-hil/FIT_PM_FW_uPC/tools/hardware']
from lease import acquire, ENV
from mod_dac28 import voltage


def make_plan(delta, span, step):
    if not all(math.isfinite(v) for v in (delta, span, step)) or span <= 0 or step <= 0:
        raise ValueError('Finite delta and positive span/step required')
    if (abs(delta*5000-round(delta*5000)) > 1e-7 or
            any(abs(v*10000-round(v*10000)) > 1e-7 for v in (span, step))):
        raise ValueError('Current SCPI formatter requires 0.2mV differential and 0.1mV common grids')
    intervals = round(2*span/step)
    if not 2 <= intervals <= 200 or abs(intervals*step-2*span) > 1e-9:
        raise ValueError('Span must contain 2..200 whole steps')
    rows = [('baseline-start', 0.0, 0.0), ('delta-start', 0.0, delta)]
    rows += [('sweep', -span+i*step, delta) for i in range(intervals+1)]
    rows += [('delta-return', 0.0, delta), ('baseline-return', 0.0, 0.0)]
    points = []
    for index, (stage, common, offset) in enumerate(rows):
        v2 = voltage(round(1.024+offset/2+common, 4))
        v3 = voltage(round(2.048-offset/2+common, 4))
        points.append(dict(index=index, stage=stage, common_shift_V=common,
                           relative_delta_V=offset, DAC2_V=v2, DAC3_V=v3,
                           commanded_common_V=(v2+v3)/2,
                           commanded_DAC2_minus_DAC3_V=v2-v3))
    return points


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--afe', type=int, choices=range(1, 13), required=True)
    parser.add_argument('--delta-v', type=float, default=.020)
    parser.add_argument('--span-v', type=float, default=.100)
    parser.add_argument('--step-v', type=float, default=.010)
    parser.add_argument('--repeats', type=int, default=4, choices=range(1, 33))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--adc-phase-code', type=int,
                        help='Diagnostic DAC-A phase setting; explicitly establish and restore A=0')
    args = parser.parse_args()
    if args.adc_phase_code is not None and not 0 <= args.adc_phase_code <= 65535:
        parser.error('ADC phase code must be0..65535')
    points = make_plan(args.delta_v, args.span_v, args.step_v)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out/'executed-controller.py').write_bytes(Path(__file__).read_bytes())
    command = [sys.executable, str(HERE/'integrator_scan.py'),
               '--afe', str(args.afe), '--expected-build', 'ff2f746c',
               '--board-serial', '1803', '--dac-channels', '2', '3',
               '--base', '1.024', '2.048', '--offsets', '0',
               '--pairs', *[f"{p['DAC2_V']:.4f}:{p['DAC3_V']:.4f}" for p in points],
               '--repeats', str(args.repeats), '--park', '1.024', '2.048',
               '--out', str(out/'native')]
    result = dict(mode='PLAN_ONLY' if args.plan_only else 'LIVE_DIAGNOSTIC',
                  physical_channel=args.afe, started_utc=datetime.datetime.now(
                      datetime.timezone.utc).isoformat(), points=points,
                  command=command, acquisition_complete=False,
                  adc_phase_code=args.adc_phase_code,
                  limits='ADC differential observables only; individual output saturation '
                         'and actual analog DAC common voltage are not measured')

    def save():
        (out/'plan.json').write_text(json.dumps(result, indent=2)+'\n')

    save()
    if args.plan_only:
        print(json.dumps(points, indent=2))
        return
    with contextlib.ExitStack() as stack:
        names = sorted(['atmel-ice-J41800043065', 'pm12-210249A73E43',
                        'kasli-diot-00001', 'esp32-6825dd4c49e4', 'lattice-VER00001'])
        locks = {}
        for name in names:
            path = (Path.home()/'.cache'/(name+'.lock')).resolve()
            locks[str(path)] = stack.enter_context(acquire(path)).fileno()
        env = dict(os.environ)
        env[ENV] = json.dumps(locks)
        phase_identified = False
        try:
            if args.adc_phase_code is not None:
                from station import console
                from phase_scan import ConsoleDAC
                from pm12_console_regression import capture
                from pm12_power import require_power_good
                from channel_settings import require_serial_reply
                from client import Client
                phase_source = HERE/'phase_scan.py'
                shutil.copy2(phase_source, out/'phase_scan.py')
                result['phase_source_sha256'] = hashlib.sha256(phase_source.read_bytes()).hexdigest()
                result['phase_uart'] = []
                with console(dict(uart='/dev/serial/by-id/'
                        'usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0')) as uart:
                    result['phase_pgood'] = require_power_good(uart, capture)
                    result['phase_mcu'] = capture(uart, 'RS')
                    require_serial_reply(result['phase_mcu']['reply'], '1803')
                    client = Client()
                    try:
                        assert client.read(0, 3) == [0x504d1202, 0x10002, 0xff2f746c]
                    finally:
                        client.close()
                    phase_identified = True
                    phase = ConsoleDAC(uart, args.afe, capture, result['phase_uart'].append)
                    phase.set_code(0)
                    phase.set_code(args.adc_phase_code)
                import time
                time.sleep(.2)
            with (out/'native-console.txt').open('w') as log:
                subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                               env=env, pass_fds=tuple(locks.values()), check=True)
            result['acquisition_complete'] = True
        except BaseException as ex:
            result['error'] = repr(ex)
            raise
        finally:
            # Keep the existing parent leases through native cleanup and final inhibit.
            try:
                from station import console
                from console import ConsoleI2C, Registers
                from mcp23017 import afe_route
                from pm12_console_regression import capture
                from pm12_power import require_power_good
                from channel_settings import require_serial_reply
                with console(dict(uart='/dev/serial/by-id/'
                                  'usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0')) as uart:
                    result['pgood_cleanup'] = require_power_good(uart, capture)
                    result['mcu_cleanup'] = capture(uart, 'RS')
                    require_serial_reply(result['mcu_cleanup']['reply'], '1803')
                    if phase_identified:
                        phase = ConsoleDAC(uart, args.afe, capture, result['phase_uart'].append)
                        phase.set_code(0)
                        result['adc_phase_restored'] = 0
                    bus = ConsoleI2C(uart, capture)
                    with bus.routed(*afe_route(args.afe)):
                        regs = Registers(bus)
                        regs.write(0x14, regs.read(0x14) | 0x88)
                        regs.write(0x15, regs.read(0x15) | 0x20)
                        assert regs.read(0x12) & 0x88 == 0x88
                        assert regs.read(0x13) & 0x20
                        result['final_gpio'] = {str(a): regs.read(a) for a in
                                                [0, 1, 0x12, 0x13, 0x14, 0x15]}
                    result['tca_final'] = {str(a): bus.mux(a) for a in [0x70, 0x71]}
                    assert set(result['tca_final'].values()) == {0}
                    result['cleanup_i2c'] = bus.records
            except BaseException as ex:
                result['cleanup_error'] = repr(ex)
                raise
            finally:
                result['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                save()
    print('COMMON_MODE_ACQUISITION_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
