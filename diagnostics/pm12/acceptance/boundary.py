#!/usr/bin/env python3
"""DNA-bound CPLD/FPGA link test and explicit integrated SRAM restoration.

Works before IPbus is ready. Never programs CPLDs/MCU/flash or changes clocks.
The native test_board.py is the sole vector generator and decoder.
"""
import argparse
import contextlib
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import uuid

import board_session as b
from station import load_dependencies, console, read_dna, jtag_command
from identity import board_uid
sys.path.insert(0, str(b.PM))
from test_board import payload, analyze, controls, PINMAP


def validate_inputs(cfg, out):
    b.uid(cfg)
    settings = cfg['boundary']
    for path, expected in [(settings['diagnostic_bit'], settings['diagnostic_sha256']),
                           (settings['restore_bit'], cfg['measurement_configuration']['pm_bit_sha256']),
                           (settings['schematic'], PINMAP['schematic_sha256'])]:
        if b.sha(path) != expected:
            raise ValueError('Bitstream/schematic checksum mismatch: ' + str(path))
    if settings.get('build_receipt'):
        build = b.read(settings['build_receipt'])
        if b.sha(settings['build_receipt']) != settings['build_receipt_sha256'] or build['status'] != 'PASS' or build['bit_sha256'] != settings['diagnostic_sha256']:
            raise ValueError('Diagnostic build provenance mismatch')
    # Reject malformed/wrong-part payloads before acquiring hardware.
    for name in ('diagnostic_bit', 'restore_bit'):
        temporary = out / (name + '.validate.hex')
        try:
            payload(Path(settings[name]), temporary)
        finally:
            temporary.unlink(missing_ok=True)


def physical_identity(cfg, out):
    """Physical DNA is mandatory; duplicated EEPROM numbers are auxiliary only."""
    out.mkdir()
    local = dict(cfg, jtag_workspace=str(out / 'jtag-work'))
    load_dependencies(local)
    from pm12_console_regression import capture
    from pm12_power import wait_power_good
    record = {'status': 'ERROR', 'observed_utc': b.now()}
    try:
        with console(local) as uart:
            record['pgood'] = wait_power_good(uart, capture)
            record['mcu_reply'] = capture(uart, 'RS')
            match = re.search(r'Board S/N:\s*(\d+)', record['mcu_reply']['reply'])
            if not match or match[1] != str(cfg['board_serial']):
                raise ValueError('MCU serial mismatch')
            record['mcu_eeprom_serial'] = match[1]
        record['fpga_dna'] = read_dna(local, out)
        record['uid'] = board_uid(record['fpga_dna'])
        if record['uid'] != b.uid(cfg):
            raise ValueError('Wrong physical DNA; test/restoration inhibited')
        record['status'] = 'PASS'
        return record
    except BaseException as error:
        record['error'] = repr(error)
        raise
    finally:
        b.write(out / 'result.json', record)


def validate_native(directory):
    """Offline recomputation from full raw vector/control logs, never exit code alone."""
    directory = Path(directory)
    original = b.read(directory / 'report.json')
    result = {'gateware': analyze((directory / 'discover.log').read_text()),
              'boundary': analyze((directory / 'boundary.log').read_text(), boundary=True),
              'controls': controls((directory / 'control.log').read_text())}
    for key, observed in result.items():
        if observed != original[key]:
            raise ValueError('Native summary differs from raw log: ' + key)
    result['tap_restored'] = bool(original.get('restored') and
                                  'RESTORE_PASS' in (directory / 'restore.log').read_text())
    result['passed'] = (original['status'] == 'PASS' and result['tap_restored'] and
                        all(result[k]['passed'] for k in ('gateware', 'boundary', 'controls')))
    return result


def native_test(cfg, out, fds, record):
    local = dict(cfg, jtag_workspace=str(out / 'jtag-work'))
    with jtag_command(local, out) as prefix:
        command = [cfg['python'], str(b.PM / 'test_board.py'), '--serial', cfg['jtag_cable'],
                   '--server', cfg.get('hw_server', 'localhost:3121'),
                   '--bitstream', cfg['boundary']['diagnostic_bit'], '--output', str(out / 'native'),
                   '--vivado-command', shlex.join(prefix), '--step-timeout', '300']
        record['command'] = command
        b.write(out / 'result.json', record)
        with (out / 'native-console.log').open('w') as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, pass_fds=fds)
            try:
                record['native_exit_code'] = child.wait(timeout=1500)
            except (subprocess.TimeoutExpired, KeyboardInterrupt):
                child.send_signal(signal.SIGINT)
                try:
                    child.wait(timeout=360)
                except subprocess.TimeoutExpired:
                    record['native_process_still_alive'] = child.pid
                    raise RuntimeError('Native test still alive; do not race restoration against it')
                raise
        if (out / 'native/report.json').exists():
            record['native_summary'] = b.read(out / 'native/report.json')
        record['analysis'] = validate_native(out / 'native')
        if record['native_exit_code'] != 0 or not record['analysis']['passed']:
            raise ValueError('CPLD/FPGA link test failed; raw evidence retained')


def restore(cfg, out):
    # b.load_sram repeats DNA/MCU/PGOOD and checks both the bit hash and the
    # live expected image, including JTAG/Ethernet/UART endpoint binding.
    with (out / 'restoration-console.log').open('w') as log, contextlib.redirect_stdout(log):
        result = b.load_sram(out / 'station.json', out / 'restoration',
                             Path(cfg['boundary']['restore_bit']),
                             cfg['measurement_configuration']['pm_bit_sha256'])
    if result['status'] != 'PASS':
        raise ValueError('Integrated SRAM restoration not verified')
    return result


def snapshot(cfg, out):
    dest = out / 'sources'
    dest.mkdir()
    for name, directory in [('acceptance', b.HERE), ('native', b.PM),
                            ('native-tcl', b.PM / 'tcl'), ('gateware', b.PM / 'gateware'), ('loader-tcl', b.PM / 'adc/tools'),
                            ('mcu', Path(cfg['console_tools'])), ('ipbus', b.PM / 'ipbus_adc')]:
        target = dest / name
        target.mkdir()
        for path in directory.iterdir():
            if path.is_file() and path.suffix in ('.py', '.tcl', '.json', '.v', '.xdc'):
                shutil.copy2(path, target / path.name)
    if cfg['boundary'].get('build_receipt'):
        shutil.copytree(Path(cfg['boundary']['build_receipt']).parent, out / 'diagnostic-build')
    artifacts = out / 'artifacts'
    artifacts.mkdir()
    for key in ('diagnostic_bit', 'restore_bit', 'schematic'):
        path = Path(cfg['boundary'][key])
        shutil.copy2(path, artifacts / (key + path.suffix))
    b.write(out / 'provenance.json', {
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=b.HERE, text=True).strip(),
        'python': sys.version, 'source_hashes': b.files(dest),
        'pinmap_sha256': b.sha(b.PM / 'pinmap.json')})
    (out / 'sources.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary'], cwd=b.HERE))


def run(cfg, out, repeat_of=None, reason=None):
    out = Path(out).resolve()
    if repeat_of is not None:
        previous = b.read(Path(repeat_of) / 'result.json')
        if previous['board_uid'] != b.uid(cfg) or not reason:
            raise ValueError('Repeat requires the same UID and an explicit reason')
    if b.uid(cfg) not in out.parts:
        raise ValueError('Output path must include the canonical board UID')
    out.mkdir(parents=True, exist_ok=False)
    record = dict(schema=1, board_uid=b.uid(cfg), channel=None, test='jtag',
                  method='pm12-static-links-dna-restore-v2', status='ERROR',
                  started_utc=b.now(), restoration='NOT_ATTEMPTED', persistent_writes=False,
                  limits='168 DI/STR links; not all board nets, analog paths or at-speed timing')
    if repeat_of is not None:
        record.update(repeat_of=str(Path(repeat_of).resolve()), repeat_reason=reason)
    b.write(out / 'station.json', cfg)
    b.write(out / 'result.json', record)
    try:
        validate_inputs(cfg, out)
        snapshot(cfg, out)
        with b.locks(cfg) as fds:
            # If this fails, neither test nor restoration may touch the wrong DUT.
            record['identity_before'] = physical_identity(cfg, out / 'identity-before')
            b.write(out / 'result.json', record)
            try:
                native_test(cfg, out, fds, record)
                record['static_links'] = 'PASS'
            except BaseException as error:
                record['test_error'] = repr(error)
                raise
            finally:
                if record.get('native_process_still_alive'):
                    raise RuntimeError('Native process retains hardware; manual inspection required')
                try:
                    record['identity_before_restore'] = physical_identity(cfg, out / 'identity-before-restore')
                    record['restore_result'] = restore(cfg, out)
                    record['restoration'] = 'PASS'
                    record['identity_after'] = record['restore_result']['identity_after']
                except BaseException as error:
                    record['restoration'] = 'ERROR'
                    record['restoration_error'] = repr(error)
                    raise
            record['status'] = 'PASS'
    except BaseException as error:
        record['error'] = repr(error)
    finally:
        record['finished_utc'] = b.now()
        record['source_files'] = [str(p.relative_to(out)) for p in sorted(out.rglob('*'))
                                  if p.is_file() and 'jtag-work' not in p.parts and
                                  p.name not in ('result.json', 'files.sha256.json') and '__pycache__' not in p.parts]
        b.write(out / 'result.json', record)
        b.write(out / 'files.sha256.json', b.files(out))
    print(json.dumps({'path': str(out), 'board_uid': record['board_uid'],
                      'status': record['status'], 'restoration': record['restoration']}), flush=True)
    return record


def verify(out):
    out = Path(out).resolve()
    record = b.read(out / 'result.json')
    if b.read(out / 'files.sha256.json') != b.files(out):
        raise ValueError('Boundary evidence modified')
    cfg = b.read(out / 'station.json')
    if b.uid(cfg) != record['board_uid'] or b.uid(cfg) not in out.parts:
        raise ValueError('Boundary configuration UID mismatch')
    for key in ('identity_before', 'identity_before_restore', 'identity_after'):
        if key in record and record[key]['uid'] != record['board_uid']:
            raise ValueError('Mixed hardware identities')
    stages = {}
    native = out / 'native'
    if (native / 'report.json').exists():
        summary = b.read(native / 'report.json')
        for key, logfile, parser in [('gateware','discover.log',analyze),
                                      ('boundary','boundary.log',lambda text:analyze(text,boundary=True)),
                                      ('controls','control.log',controls)]:
            if not (native / logfile).exists():
                stages[key] = {'status':'NOT_RUN'}
                continue
            try:
                observed = parser((native / logfile).read_text())
            except ValueError as error:
                stages[key] = {'status':'ERROR','error':str(error)}
                if key in summary:raise ValueError('Summary contains invalid raw stage: '+key) from error
                continue
            if key not in summary or observed != summary[key]:
                raise ValueError('Native summary differs from raw stage: '+key)
            stages[key] = dict(status='PASS' if observed['passed'] else 'FAIL', **observed)
    if record['status'] == 'PASS':
        if not validate_native(out / 'native')['passed'] or record['restoration'] != 'PASS':
            raise ValueError('Boundary or restoration not passed')
        after = record['restore_result']['identity_after']
        expected = cfg['expected_build_id']
        expected = int(expected, 16) if isinstance(expected, str) else expected
        if after['fpga_ipbus_identity'] != [0x504d1202, 0x10002, expected] or after['endpoint_binding']['status'] != 'PASS':
            raise ValueError('Final integrated image/endpoint verification failed')
    return {'board_uid': record['board_uid'], 'integrity': 'PASS',
            'status': record['status'], 'restoration': record['restoration'], 'stages': stages}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--station', type=Path)
    destination = p.add_mutually_exclusive_group()
    destination.add_argument('--root', type=Path)
    destination.add_argument('--out', type=Path)
    p.add_argument('--repeat-of', type=Path)
    p.add_argument('--reason')
    p.add_argument('--verify', type=Path, help='Offline verification; no hardware imports')
    a = p.parse_args()
    if a.verify:
        print(json.dumps(verify(a.verify)))
        return 0
    if not a.station or not (a.root or a.out):
        p.error('--station and --root or --out are required')
    cfg = b.read(a.station)
    out = a.out or (a.root / b.uid(cfg) / 'setup' /
                   (datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-boundary-' + uuid.uuid4().hex[:8]))
    return 0 if run(cfg, out, a.repeat_of, a.reason)['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
