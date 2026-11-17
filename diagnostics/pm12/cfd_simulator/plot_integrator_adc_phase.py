"""Plot validated ADC waveform shapes from a DAC-A sampling-phase sweep."""
import argparse
import csv
import json
from pathlib import Path
import shutil
import struct
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'ipbus_adc'))
from adc_decode import decode

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--root', type=Path, required=True)
a = p.parse_args()
r = json.loads((a.root/'phase-probe.json').read_text())
assert r['complete'] and r['restored_phase_code'] == 0
out = a.root/'analysis'
out.mkdir(exist_ok=False)
shutil.copy2(__file__, out/'executed-analysis.py')
fig, axes = plt.subplots(2, 2, figsize=(12, 8), layout='constrained')
rows = []
for j, bank in enumerate([0, 1]):
    ax, amplitude = axes[j]
    for i, point in enumerate(r['points']):
        waves = []
        clips = []
        for cap in point['captures']:
            if cap['bank'] != bank:
                continue
            words = struct.unpack('<4096H', (a.root/cap['file']).read_bytes())
            try:
                samples, _ = decode(words, bank)
                assert cap['valid']
            except ValueError:
                assert not cap['valid']
                continue
            x = np.asarray(samples)
            n = len(x)//4*4
            wave = np.array([x[k:n:4].mean() for k in range(4)])
            # Captures have arbitrary period origin: circularly align the trough.
            wave = np.roll(wave, -int(np.argmin(wave)))
            waves.append(wave)
            clips.append(100*np.mean((x == 0) | (x == 4095)))
        row = dict(bank='AB'[bank], phase_code=point['code'], valid_buffers=len(waves),
                   total_buffers=sum(c['bank'] == bank for c in point['captures']))
        if waves:
            w = np.mean(waves, axis=0)
            row.update(mean_code=float(w.mean()), amplitude_code=float(w.max()-w.min()),
                       rail_percent=float(np.mean(clips)))
            row.update({f'phase{k}_code':float(v) for k,v in enumerate(w)})
            color = plt.cm.viridis(i/max(1,len(r['points'])-1))
            ax.plot(np.arange(5)*12.5, np.r_[w,w[0]], 'o-', color=color,
                    label=f"{point['code']} ({len(waves)}/3)")
            amplitude.plot(point['code'], row['amplitude_code'], 'o', color=color)
        rows.append(row)
    ax.set(title=f'ADC {"AB"[bank]}: four-phase mean waveform',
           xlabel='Circularly aligned sample position (nominal ns)', ylabel='ADC code')
    ax.legend(fontsize=7, ncol=2)
    amplitude.set(title=f'ADC {"AB"[bank]}: four-phase amplitude', xlabel='DAC-A phase code',
                  ylabel='Max minus min (ADC code)')
    for axis in [ax, amplitude]:
        axis.grid(alpha=.25)
fields = list(dict.fromkeys(k for row in rows for k in row))
with (out/'phase-shape.csv').open('w', newline='') as f:
    writer=csv.DictWriter(f, fieldnames=fields)
    writer.writeheader(); writer.writerows(rows)
fig.suptitle(f"PM{r['physical_channel']}: ADC phase sweep; fixed DAC2/3={r['external_setpoints_V']} V\n"
             'Four samples/integrator period; circular alignment removes capture origin, not timing calibration')
for ext in ['png','pdf']:
    fig.savefig(out/f'phase-shape.{ext}', dpi=160)
print(json.dumps(rows, indent=2))
