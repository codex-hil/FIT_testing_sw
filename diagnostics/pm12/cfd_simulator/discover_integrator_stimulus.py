"""Locate the J6 DAC2/3 stimulus among four fitted channels, diagnostic only.

Invalid ADC words remain saved and explicitly invalid. They do not abort
collection on other banks/channels and are never used as amplitude observations.
"""
import argparse
import contextlib
import datetime
import json
from pathlib import Path
import statistics
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
from pm12_console_regression import capture
from pm12_power import wait_power_good, require_power_good
from channel_settings import adc_address, require_serial_reply, snapshot_sources
from mod_dac28 import remote_lease, DAC
from client import Client
from adc_decode import decode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--connected', nargs=4, type=int, choices=range(1, 13), required=True,
                        help='All four fitted CFD physical channels')
    args = parser.parse_args()
    if len(set(args.connected)) != 4:
        parser.error('Four distinct fitted channels required')
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = dict(mode='LIVE_DIAGNOSTIC', started_utc=datetime.datetime.now(
        datetime.timezone.utc).isoformat(), physical_channels=args.connected,
        points=[], acquisition_complete=False, stimulus_candidates=[])
    report['executed_sources'] = snapshot_sources(out, ['__main__', 'lease', 'station',
        'console', 'mcp23017', 'pm12_power', 'pm12_console_regression',
        'channel_settings', 'mod_dac28', 'client', 'adc_decode'])

    def save():
        (out/'discovery.json').write_text(json.dumps(report, indent=2)+'\n')

    save()
    identified = False
    with contextlib.ExitStack() as stack:
        for name in sorted(['atmel-ice-J41800043065', 'pm12-210249A73E43',
                            'kasli-diot-00001', 'esp32-6825dd4c49e4', 'lattice-VER00001']):
            stack.enter_context(acquire(Path.home()/'.cache'/(name+'.lock')))
        uart = stack.enter_context(console(dict(uart='/dev/serial/by-id/'
            'usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0')))
        client = Client()
        stack.callback(client.close)
        bus = ConsoleI2C(uart, capture)
        dac = None

        def route_state(ch, enabled):
            require_power_good(uart, capture)
            with bus.routed(*afe_route(ch)):
                regs = Registers(bus)
                assert regs.read(10) == regs.read(11) and not regs.read(10) & 128
                regs.write(0x15, regs.read(0x15) | 0x20)
                regs.write(1, regs.read(1) & ~0x20)
                latch = regs.read(0x14) | 0x88
                regs.write(0x14, latch)
                regs.write(0, regs.read(0) & ~0x88)
                if enabled:
                    regs.write(0x14, latch & ~0x80)
                assert regs.read(0x12) & 0x88 == (8 if enabled else 0x88)
                assert regs.read(0x13) & 0x20

        try:
            report['pgood'] = wait_power_good(uart, capture)
            report['mcu'] = capture(uart, 'RS')
            require_serial_reply(report['mcu']['reply'], '1803')
            report['fpga'] = client.read(0, 3)
            assert report['fpga'] == [0x504d1202, 0x10002, 0xff2f746c]
            identified = True
            remote = stack.enter_context(remote_lease())
            dac = DAC(remote, channels=[2, 3])
            stack.callback(dac.close)
            report['dac_before'] = dac.snapshot()
            for ch in report['physical_channels']:
                route_state(ch, False)
            for ch in report['physical_channels']:
                route_state(ch, True)
                try:
                    for stage, pair in [('before', [1.024, 2.048]),
                                        ('delta20', [1.034, 2.038]),
                                        ('return', [1.024, 2.048])]:
                        require_power_good(uart, capture)
                        dac.park(*pair)
                        time.sleep(.1)
                        point = dict(channel=ch, stage=stage, setpoints=pair, captures=[])
                        report['points'].append(point)
                        for bank in [0, 1]:
                            for repeat in range(2):
                                generation, status = client.acquire(bank, False)
                                words = client.block(adc_address(ch), 4096)
                                assert client.read(0x12) == [generation]
                                name = f'ch{ch:02d}-{stage}-bank{bank}-{repeat}.bin'
                                (out/name).write_bytes(struct.pack('<4096H', *words))
                                row = dict(bank=bank, file=name, generation=generation,
                                           hardware_status=status, valid=False)
                                try:
                                    x, timing = decode(words, bank)
                                    means = [statistics.mean(x[i:len(x)//4*4:4]) for i in range(4)]
                                    row.update(valid=True, mean_code=statistics.mean(x),
                                               phase_amplitude=max(means)-min(means), timing=timing)
                                except ValueError as ex:
                                    row['decode_error'] = str(ex)
                                point['captures'].append(row)
                                save()
                        print('CH', ch, stage,
                              [(r['bank'], round(r['mean_code'], 2) if r['valid'] else 'INVALID')
                               for r in point['captures']], flush=True)
                finally:
                    route_state(ch, False)
            report['responses'] = []
            for ch in report['physical_channels']:
                for bank in [0, 1]:
                    stages = {}
                    for point in report['points']:
                        if point['channel'] != ch:
                            continue
                        values = [c['mean_code'] for c in point['captures']
                                  if c['bank'] == bank and c['valid']]
                        stages[point['stage']] = values
                    row = dict(channel=ch, bank=bank, valid_counts={k:len(v) for k,v in stages.items()})
                    if all(len(stages.get(k, [])) == 2 for k in ['before', 'delta20', 'return']):
                        row['response_code'] = statistics.mean(stages['delta20']) - (
                            statistics.mean(stages['before'])+statistics.mean(stages['return']))/2
                        row['return_change_code'] = statistics.mean(stages['return'])-statistics.mean(stages['before'])
                        if abs(row['response_code']) > 10 and abs(row['return_change_code']) < 5:
                            report['stimulus_candidates'].append(ch)
                    report['responses'].append(row)
            report['stimulus_candidates'] = sorted(set(report['stimulus_candidates']))
            report['acquisition_complete'] = True
        except BaseException as ex:
            report['error'] = repr(ex)
            raise
        finally:
            try:
                if identified:
                    for ch in report['physical_channels']:
                        route_state(ch, False)
                if dac:
                    dac.park(1.024, 2.048)
                    report['dac_final'] = dac.snapshot()
                    report['scpi'] = dac.records
                report['tca_final'] = {str(a):bus.mux(a) for a in [0x70, 0x71]} if identified else {}
            except BaseException as ex:
                report['cleanup_error'] = repr(ex)
                raise
            finally:
                report['i2c'] = bus.records
                report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                save()
    print('STIMULUS_CANDIDATES', report['stimulus_candidates'], flush=True)


if __name__ == '__main__':
    main()
