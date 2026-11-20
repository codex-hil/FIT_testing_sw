#!/usr/bin/env python3
"""Declare a new fitting without modifying enrollment or any existing session.

Offline only. USB pairs are explicit; timing lanes await discovery. This records
operator declarations, not independently measured connections.
"""
import argparse
import json
from pathlib import Path
import board_session as b


def prepare(args):
    cfg = b.read(args.enrolled)
    b.uid(cfg)
    fitted = args.fitted
    if len(set(fitted)) != len(fitted):
        raise ValueError('Duplicate fitted channels')
    if args.usb_channel is not None and args.usb_channel not in fitted:
        raise ValueError('USB channel must be fitted')
    if args.usb_channel is not None:
        if args.adc_dac is None or args.integrator_dac is None:
            raise ValueError('Both explicit DAC pairs required for dual USB connection')
        if len(set(args.adc_dac + args.integrator_dac)) != 4:
            raise ValueError('DAC routes must not overlap')
    cfg.update(fitted_channels=fitted, stimulated_channel=args.usb_channel,
               fitting_note=args.note, shared_monitors_connected=False, smu_sense=None)
    for ch, route in cfg['channels'].items():
        connected = int(ch) == args.usb_channel
        route.update(analog_connected=connected, integrator_connected=connected, phase_lanes=[])
        if connected:
            route.update(dac_channels=args.adc_dac, integrator_dac_channels=args.integrator_dac)
    if args.restore_bit:
        if b.sha(args.restore_bit) != cfg['measurement_configuration']['pm_bit_sha256']:
            raise ValueError('Restore bit SHA256 differs from enrolled expected image')
        cfg['boundary']['restore_bit'] = str(args.restore_bit.resolve())
    if args.diagnostic_build:
        build = b.read(args.diagnostic_build)
        bit = Path(build['bitstream'])
        if build['status'] != 'PASS' or b.sha(bit) != build['bit_sha256']:
            raise ValueError('Diagnostic build not verified')
        cfg['boundary'].update(diagnostic_bit=str(bit),diagnostic_sha256=build['bit_sha256'],
                               build_receipt=str(args.diagnostic_build.resolve()),
                               build_receipt_sha256=b.sha(args.diagnostic_build))
    if args.schematic:
        cfg['boundary']['schematic'] = str(args.schematic.resolve())
    cfg['configuration_declaration'] = dict(created_utc=b.now(), enrollment=str(args.enrolled.resolve()),
                                           enrollment_sha256=b.sha(args.enrolled), physical_routes='operator-declared')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(cfg, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'board_uid': cfg['board_uid'], 'configuration': str(args.out.resolve())}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--enrolled', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--fitted', type=int, choices=range(1, 13), nargs='+', required=True)
    p.add_argument('--usb-channel', type=int, choices=range(1, 13))
    p.add_argument('--adc-dac', type=int, choices=range(8), nargs=2)
    p.add_argument('--integrator-dac', type=int, choices=range(8), nargs=2)
    p.add_argument('--restore-bit', type=Path)
    p.add_argument('--schematic', type=Path)
    p.add_argument('--diagnostic-build', type=Path)
    p.add_argument('--note', required=True)
    prepare(p.parse_args())
