#!/usr/bin/env python3
"""Offline boundary-batch dossier with the full, explicitly incomplete PM12 matrix."""
import argparse
import json
from pathlib import Path
import shutil
import board_session as b
import boundary
import dossier
from session_board_export import matrix


def build(evidence, out, related=(), build_history=(), failed_sessions=(), unbound=()):
    evidence = Path(evidence).resolve()
    validation = boundary.verify(evidence)
    record = b.read(evidence / 'result.json')
    uid = record['board_uid']
    out = Path(out).resolve()
    for original in [evidence,*map(Path,related),*map(Path,build_history),*map(Path,failed_sessions),*map(Path,unbound)]:
        if out.is_relative_to(original.resolve()):
            raise ValueError('Release output must be outside its input data')
    out.mkdir(parents=True, exist_ok=False)
    source = out / 'boundary-evidence'
    source.mkdir()
    shutil.copytree(evidence, source / 'acquisition', ignore=shutil.ignore_patterns('jtag-work', '__pycache__'))
    related_files = []
    for other in map(lambda p: Path(p).resolve(), related):
        row = b.read(other / 'result.json')
        if row['board_uid'] != uid or b.read(other / 'files.sha256.json') != b.files(other):
            raise ValueError('Related evidence UID/hash mismatch')
        if other == evidence:
            raise ValueError('Selected acquisition is not a related attempt')
        dest = source / 'related' / other.name
        shutil.copytree(other, dest, ignore=shutil.ignore_patterns('jtag-work', '__pycache__'))
        related_files.extend(str(p.relative_to(source)) for p in dest.rglob('*') if p.is_file())
        if row.get('test')=='station-probe':
            from station_probe import analyze_record
            analyses=source/'related-analyses';analyses.mkdir(exist_ok=True)
            normalized=analyses/(other.name+'.json');b.write(normalized,analyze_record(row))
            related_files.append(str(normalized.relative_to(source)))
    for previous in map(lambda p: Path(p).resolve(), build_history):
        if b.read(previous / 'files.sha256.json') != b.files(previous):
            raise ValueError('Build history hash mismatch')
        dest = source / 'build-history' / previous.name
        shutil.copytree(previous, dest)
        related_files.extend(str(p.relative_to(source)) for p in dest.rglob('*') if p.is_file())
    for session in map(lambda p:Path(p).resolve(),failed_sessions):
        _,state,_=b.load_session(session)
        if state['board_uid']!=uid or state['status']!='ERROR':raise ValueError('Expected failed session for same UID')
        dest=source/'failed-sessions'/session.name
        shutil.copytree(session,dest,ignore=shutil.ignore_patterns('jtag-work','__pycache__'))
        related_files.extend(str(p.relative_to(source)) for p in dest.rglob('*') if p.is_file())
    for preflight in map(lambda p:Path(p).resolve(),unbound):
        dest=source/'unbound-preflight'/preflight.name
        shutil.copytree(preflight,dest,ignore=shutil.ignore_patterns('jtag-work','__pycache__'))
        b.write(dest/'association.json',dict(status='UNBOUND',board_uid=None,note='Before valid FPGA DNA; not a qualified measurement of any board'))
        related_files.extend(str(p.relative_to(source)) for p in dest.rglob('*') if p.is_file())
    tools = out / 'offline-tools'
    tools.mkdir()
    for name in ('boundary.py','boundary_release.py','board_session.py','station.py','identity.py','lease.py','test_board.py','dossier.py','session_board_export.py','board_check.py','package_release.py','station_probe.py','publish_release.py'):
        original = b.PM / name if name == 'test_board.py' else b.HERE / name
        shutil.copy2(original, tools / name)
    shutil.copy2(b.PM / 'pinmap.json', tools / 'pinmap.json')
    metrics=[]
    for stage in ('gateware','boundary'):
        observed=validation.get('stages',{}).get(stage,{})
        for field,unit in [('matched','connection'),('total','connection'),('vectors','vector')]:
            if field in observed:metrics.append(dict(name=stage+'_'+field,value=observed[field],unit=unit))
    control=validation.get('stages',{}).get('controls',{})
    if 'repeats' in control:metrics.append(dict(name='control_repeats',value=control['repeats'],unit='cycle'))
    receipt = dict(record)
    receipt.update(original_summary='acquisition/result.json',
                   source_files=['acquisition/' + p for p in record['source_files']] + related_files,
                   curves=[], measured_utc=record['finished_utc'],
                   metrics=metrics,
                   offline_validation=validation)
    b.write(source / 'selected-result.json', receipt)
    gaps = out / 'gaps'
    gaps.mkdir()
    selections = []
    for case, test, channel in matrix():
        is_boundary = test == 'jtag'
        status = record['status'] if is_boundary else 'NOT_RUN'
        basis = ('Both raw vector sets and monitor controls reanalyzed; integrated SRAM/endpoint restoration checked'
                 if is_boundary and record['status']=='PASS' else 'Native/restoration ERROR retained; see raw stage validation'
                 if is_boundary else 'Not measured in this boundary-only batch; no prior-board data imported')
        method = record['method'] if is_boundary else 'explicit-gap-v1'
        name = case.replace(':','-') + '.json'
        if not is_boundary:
            b.write(gaps / name, dict(board_uid=uid,channel=channel,test=test,status=status,
                                     method=method,basis=basis,source_files=[],curves=[]))
        selections.append(dict(case=case,test=test,channel=channel,status=status,method=method,basis=basis,
                               source=str((source if is_boundary else gaps).relative_to(out)),
                               receipt='selected-result.json' if is_boundary else name,
                               measured_utc=record['finished_utc'] if is_boundary else None))
    spec = dict(board_uid=uid,scope='PARTIAL: second-board static CPLD/FPGA DI/STR links and explicit restoration',
                required_cases=[c for c,_,_ in matrix()],selections=selections,
                identities=[record.get('identity_before'),record.get('identity_after')],
                metadata_omissions=['Physical board revision and fixture factory labels/photos not verified'],
                scope_exclusions=['No MCU/CPLD/flash programming','No PLL/clock profile changes',
                                  'Not all board nets or analog paths; no at-speed, calibrated jitter or BER qualification'],
                open_items=[r['case']+': '+r['status'] for r in selections if r['status']!='PASS']+
                           ['All remaining measurements pending; metadata omissions retained in selection.json'])
    b.write(out / 'EXPLICIT_SELECTION.json',spec)
    result = dossier.build(out / 'EXPLICIT_SELECTION.json',out / 'dossier')
    dossier.export(out / 'dossier',out / 'report-inputs')
    b.write(out / 'offline-verification.json',validation)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--boundary',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--related',type=Path,action='append',default=[])
    p.add_argument('--build-history',type=Path,action='append',default=[])
    p.add_argument('--failed-session',type=Path,action='append',default=[])
    p.add_argument('--unbound-preflight',type=Path,action='append',default=[])
    a=p.parse_args()
    print(json.dumps(build(a.boundary,a.out,a.related,a.build_history,a.failed_session,a.unbound_preflight),indent=2))
