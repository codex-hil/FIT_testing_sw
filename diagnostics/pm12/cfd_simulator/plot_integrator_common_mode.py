"""Offline amplitude/level/clipping analysis of a diagnostic common-shift scan."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil
import statistics
import struct
import sys

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'ipbus_adc'))
from adc_decode import decode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, help='New analysis directory; existing outputs are preserved')
    args = parser.parse_args()
    root = args.root.resolve()
    plan = json.loads((root/'plan.json').read_text())
    native = json.loads((root/'native/status.json').read_text())
    assert plan['acquisition_complete'] and not plan.get('error') and not plan.get('cleanup_error')
    assert native['pass_'] and not native.get('error')
    assert len(native['points']) == len(plan['points'])
    out = args.out.resolve() if args.out else root/'analysis'
    out.mkdir(exist_ok=False)
    shutil.copy2(Path(__file__), out/'executed-analysis.py')
    shutil.copy2(HERE.parent/'ipbus_adc/adc_decode.py', out/'adc_decode.py')
    hashes = {}
    rows = []
    for expected, point in zip(plan['points'], native['points']):
        assert expected['index'] == point['index']
        assert point['setpoints_V'] == [expected['DAC2_V'], expected['DAC3_V']]
        for bank, label in enumerate('AB'):
            measures = []
            for cap in point['captures']:
                if cap['bank'] != bank:
                    continue
                path = root/'native'/cap['file']
                raw = path.read_bytes()
                assert len(raw) == 8192
                hashes[str(path.relative_to(root))] = hashlib.sha256(raw).hexdigest()
                x, _ = decode(struct.unpack('<4096H', raw), bank)
                assert len(x) == cap['samples']
                n = len(x)//4*4
                phases = [statistics.mean(x[i:n:4]) for i in range(4)]
                clip = sum(v == 0 or v == 4095 for v in x)/len(x)
                assert abs(clip-cap['clipped_fraction']) < 1e-12
                assert all(abs(a-b) < 1e-9 for a, b in zip(phases, cap['phase_means']))
                q1, q99 = np.percentile(x, [1, 99])
                measures.append(dict(mean_code=statistics.mean(x),
                                     phase_amplitude_code=max(phases)-min(phases),
                                     robust_amplitude_code=float(q99-q1),
                                     raw_amplitude_code=max(x)-min(x),
                                     clip_percent=100*clip,
                                     near_rail_percent=100*sum(v <= 1 or v >= 4094 for v in x)/len(x)))
            assert len(measures) >= 2
            row = dict(expected, bank=label, buffers=len(measures))
            for key in measures[0]:
                row[key] = statistics.mean(m[key] for m in measures)
                row[key+'_repeat_std'] = statistics.pstdev(m[key] for m in measures)
            rows.append(row)
    with (out/'common-shift.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout='constrained')
    panels = [('phase_amplitude_code', 'Four-phase amplitude (ADC code)'),
              ('mean_code', 'Mean differential ADC code'),
              ('robust_amplitude_code', '99th minus 1st percentile (ADC code)'),
              ('clip_percent', 'ADC rail samples (%)')]
    for ax, (metric, ylabel) in zip(axes.flat, panels):
        for bank in 'AB':
            selected = [r for r in rows if r['stage'] == 'sweep' and r['bank'] == bank]
            ax.errorbar([r['common_shift_V']*1000 for r in selected],
                        [r[metric] for r in selected],
                        yerr=[r[metric+'_repeat_std'] for r in selected],
                        fmt='o-', ms=3, capsize=2, label='ADC '+bank)
        ax.set(xlabel='Commanded common shift (mV)', ylabel=ylabel)
        ax.grid(alpha=.25)
        ax.legend()
    reference = next(p for p in plan['points'] if p['stage'] == 'delta-start')
    phase_note = (f"DAC-A phase code {plan['adc_phase_code']}" if
                  plan.get('adc_phase_code') is not None else 'DAC-A phase unchanged')
    fig.suptitle(f"PM{plan['physical_channel']}: common shift at relative delta="
                 f"{reference['relative_delta_V']*1000:g} mV\n"
                 f"DAC2={reference['DAC2_V']:.4f} V+c; "
                 f"DAC3={reference['DAC3_V']:.4f} V+c; {phase_note}; repeat SD")
    for suffix in ['png', 'pdf']:
        fig.savefig(out/('common-shift.'+suffix), dpi=180)
    plt.close(fig)
    controls = [r for r in rows if r['stage'] != 'sweep']
    control_response = {}
    for bank in 'AB':
        before = next(r for r in controls if r['bank'] == bank and r['stage'] == 'baseline-start')
        shifted = next(r for r in controls if r['bank'] == bank and r['stage'] == 'delta-start')
        returned = next(r for r in controls if r['bank'] == bank and r['stage'] == 'baseline-return')
        control_response[bank] = dict(
            delta_step_mean_change_code=shifted['mean_code']-before['mean_code'],
            delta_step_amplitude_change_code=shifted['phase_amplitude_code']-before['phase_amplitude_code'],
            baseline_return_mean_change_code=returned['mean_code']-before['mean_code'])
    result = dict(status='DIAGNOSTIC_ACQUISITION_COMPLETE',
                  physical_channel=plan['physical_channel'], rows=rows,
                  adc_phase_code=plan.get('adc_phase_code'),
                  controls=controls, raw_sha256=hashes,
                  control_response=control_response,
                  native_report_sha256=hashlib.sha256((root/'native/status.json').read_bytes()).hexdigest(),
                  plan_sha256=hashlib.sha256((root/'plan.json').read_bytes()).hexdigest(),
                  definitions=dict(phase_amplitude='max minus min of four phase means; includes reset waveform',
                                   robust_amplitude='99th minus 1st sample percentile',
                                   clip='decoded differential ADC samples equal0 or4095'),
                  limits=['Commanded DAC values, not voltmeter measurements',
                          'No individual integrator-output-to-ground or common-output voltage measurement',
                          'Absence of ADC clipping does not exclude single-ended amplifier saturation',
                          'No waveform pair-selection filter applied; all captures retained',
                          'No production qualification or selected-result change'])
    (out/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    sweep = [r for r in rows if r['stage'] == 'sweep']
    endpoints = {min(r['common_shift_V'] for r in sweep),
                 max(r['common_shift_V'] for r in sweep)}
    for bank in 'AB':
        print(bank, [{k:r[k] for k in ['common_shift_V', 'phase_amplitude_code',
                                      'mean_code', 'clip_percent']}
                     for r in sweep if r['bank'] == bank and
                     (r['common_shift_V'] in endpoints or abs(r['common_shift_V']) < 1e-9)])


if __name__ == '__main__':
    main()
