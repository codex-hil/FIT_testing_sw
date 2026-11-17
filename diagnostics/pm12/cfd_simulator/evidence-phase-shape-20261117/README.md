# PM2 ADC sampling-phase DAC sweep — 2026-11-17

Diagnostic follow-up to the common-shift experiment. Fixed external DAC2/3
at 1.034/2.038 V (relative differential offset 20 mV); sweep internal DAC-A
through ten evenly spaced codes 0..65535. Three independent captures per bank
and setting, 60 raw buffers total. All pass the unchanged ADC coherency decoder;
no hard ADC rail samples. This also includes six valid buffers at phase code 0;
the earlier intermittent coherency error is retained as historical evidence.

Four-phase max-minus-min amplitude ranges: ADC A 154.09..156.15 codes;
ADC B 67.00..71.56 codes. The waveform changes little at this fixed input.
No phase-versus-code calibration was acquired, so these are commanded phase
DAC settings, not measured delay values. Four sample positions per period
limit waveform detail; straight lines between samples are visual guides.
Each capture is circularly rotated to align its minimum, removing the arbitrary
capture origin. This does not preserve absolute phase or establish timing delay.
One sequential scan without a return control does not separate small drift/noise
from DAC-dependent changes.

Afterwards internal DAC-A restored to 0, external DAC2/3 to 1.024/2.048 V,
selected amplifiers/bypass/monitor inhibited, TCA masks zero, leases released.
No FPGA/CPLD/MCU programming, PLL profile changes or SMU use. Qualification
results unchanged. Raw archive includes executed source snapshots and UART records.

```
python probe_integrator_adc_phase.py --afe 2 --delta-v .020 \
  --codes 0 7282 14563 21845 29127 36408 43690 50972 58253 65535 --out NEW_RUN
python plot_integrator_adc_phase.py --root NEW_RUN
```
