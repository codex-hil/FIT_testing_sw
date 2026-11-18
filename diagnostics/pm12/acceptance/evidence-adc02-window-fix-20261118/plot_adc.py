from pathlib import Path
import sys,json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,'/home/codex-hil/fit-testing-publish/diagnostics/pm12/ipbus_adc')
from adc_decode import decode
p=Path(__file__).resolve().parent;scan=p/'adc-lines-standard/scan';d=json.loads((scan/'status.json').read_text());assert d['pass']
fig,ax=plt.subplots(1,3,figsize=(15,4));fs=80157400
for b in [0,1]:
 rows=[r for r in d['measurements'] if r['bank']==b and r['injection_bank']==b];label='AB'[b];ax[0].plot([r['diff_setpoint_v'] for r in rows],[r['raw_mean'] for r in rows],label=label)
 i=min(range(len(rows)),key=lambda i:abs(rows[i]['diff_setpoint_v']));raw=np.frombuffer((scan/f'mux{b}-point{i:03d}-bank{b}.bin').read_bytes(),dtype='<u2');v=np.array(decode([int(w) for w in raw],b,sample_window='str-rise')[0],dtype=float)
 ax[1].plot(np.arange(80)/fs*1e6,v[:80],label=label)
 # Windowed amplitude spectrum; referenced to ADC full-scale sine peak2048codes.
 x=v-v.mean();w=np.hanning(len(x));a=2*np.abs(np.fft.rfft(x*w))/w.sum();ax[2].plot(np.fft.rfftfreq(len(x),1/fs)/1e6,20*np.log10(np.maximum(a,1e-12)/2048),label=label)
for a in ax:a.grid(alpha=.3);a.legend()
ax[0].set(xlabel='Differential input (V)',ylabel='Mean ADC code',title='Channel2 DC transfer')
ax[1].set(xlabel='Time (µs)',ylabel='ADC code',title='Zero differential input')
ax[2].set(xlabel='Frequency (MHz)',ylabel='Amplitude (dBFS)',title='Zero-input spectrum (Hann)')
fig.suptitle('PM12 channel2 · phase DAC32768 · ADC80.1574MS/s');fig.tight_layout()
for ext in ['png','pdf']:fig.savefig(p/('adc2.'+ext),dpi=160)
