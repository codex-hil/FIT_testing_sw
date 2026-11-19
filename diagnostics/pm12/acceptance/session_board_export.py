"""Offline partial dossier for an explicitly selected board_check acquisition.

Keeps the full 89-case matrix. NOT_RUN is evidence of a gap, never a passed
measurement. No historical board results are imported and no hardware is opened.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

import board_session as b
import board_check
import dossier

BOARD = ('jtag', 'mcu', 'i2c', 'hdmi', 'ethernet')
CHANNEL = ('cfd-monitor', 'cfd-dacs', 'gate-phase', 'tdc', 'adc-dc', 'adc-lines', 'integrator')


def matrix():
    return [(test + ':board', test, None) for test in BOARD] + [
        (f'{test}:{ch}', test, ch) for test in CHANNEL for ch in range(1, 13)]


def build(session, measurement, out):
    session, state, cfg = b.load_session(session)
    b.verify(session)
    measurement = Path(measurement).resolve()
    if not measurement.is_relative_to(session) or str(measurement.relative_to(session)) not in state['measurements']:
        raise ValueError('Select an explicit registered measurement from this session')
    record = b.read(measurement / 'measurement.json')
    if record['test'] != 'board-final' or record['board_uid'] != state['board_uid']:
        raise ValueError('Expected board-final receipt for this UID')
    if not record.get('finished_utc'):
        raise ValueError('Acquisition still open')
    # Re-run the shared analysis, including all binary buffers. An ERROR never
    # inherits a PASS from some successful intermediate field.
    validation = board_check.validate(measurement) if record['status'] == 'PASS' else None
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = out / 'source'
    shutil.copytree(session, source / 'session', ignore=shutil.ignore_patterns('jtag-work', '__pycache__'))
    tools = source / 'offline-tools'
    tools.mkdir()
    for name in ('board_session.py', 'board_check.py', 'identity.py', 'lease.py', 'dossier.py', 'session_board_export.py'):
        shutil.copy2(b.HERE / name, tools / name)
    repo = b.HERE.parents[2]
    provenance = {'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
                  'selected_measurement': str(measurement.relative_to(session)),
                  'station_sha256': state['station_sha256'],
                  'offline_analysis': validation}
    (source / 'git-diff.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary'], cwd=repo))
    b.write(source / 'provenance.json', provenance)
    required = matrix()
    selections = []
    for case, test, channel in required:
        status = 'NOT_RUN'
        basis = ('Current connection not confirmed; no measurement selected' if channel else
                 'Boundary scan not executed; DNA identification does not substitute for boundary scan')
        metrics = []
        if test in ('mcu', 'i2c', 'hdmi', 'ethernet'):
            status = 'PASS_FUNCTIONAL' if validation else record['status']
            basis = 'Shared board_check.validate; finite functional scope only'
            if test == 'i2c':
                # INA replies are retained observations, with no calibrated
                # rail/current acceptance or fitting assumptions introduced here.
                status = 'COMPLETE' if validation else record['status']
                basis = 'Sensor replies recorded; numerical rail/current acceptance not evaluated'
            if validation and test == 'ethernet':
                metrics = [{'name': 'transport_bytes_compared', 'value': validation['transport_bytes_compared'], 'unit': 'byte'}]
            if validation and test == 'hdmi':
                metrics = [{'name': 'signature_trials', 'value': validation['hdmi_trials'], 'unit': 'trial'}]
        relative = 'receipts/' + case.replace(':', '-') + '.json'
        (source / 'receipts').mkdir(exist_ok=True)
        receipt = {'board_uid': state['board_uid'], 'channel': channel, 'test': test,
                   'status': status, 'method': 'session-board-check-partial-v1', 'basis': basis,
                   'measured_utc': record['finished_utc'] if status != 'NOT_RUN' else None,
                   'source_files': ['session/session.json', 'session/station.json',
                                    'session/' + str(measurement.relative_to(session)) + '/measurement.json',
                                    'provenance.json'],
                   'metrics': metrics, 'curves': [],
                   'scope': 'No boundary links, calibrated analog acceptance, BER, jitter or power fault injection'}
        b.write(source / relative, receipt)
        selections.append(dict(case=case, test=test, channel=channel, source=str(source),
                               receipt=relative, status=status, method=receipt['method'],
                               basis=basis, measured_utc=receipt['measured_utc']))
    gaps = [r['case'] + ': ' + r['status'] for r in selections if r['status'] not in ('PASS', 'PASS_FUNCTIONAL')]
    spec = {'board_uid': state['board_uid'], 'scope': 'PARTIAL current-session board checks; full 89-case matrix retained',
            'required_cases': [c for c, _, _ in required], 'selections': selections,
            'open_items': gaps + ['Physical CFD/USB/SMU connections and fixture labels/photos unconfirmed',
                                  'MCU RS reports FPGA not ready although endpoint binding passes; raw reply retained'],
            'scope_exclusions': ['No previous sealed results imported', 'No automatic clock/CPLD/MCU programming'],
            'identities': [state['identity']]}
    b.write(out / 'EXPLICIT_SELECTION.json', spec)
    result = dossier.build(out / 'EXPLICIT_SELECTION.json', out / 'dossier')
    dossier.export(out / 'dossier', out / 'report-inputs')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--session', type=Path, required=True)
    p.add_argument('--measurement', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(build(a.session, a.measurement, a.out), indent=2))
