# Fixed differential offset, common-shift experiment — 17 November2026

**Diagnostic only; no production qualification or selected campaign result changed.**
The owner requested holding a20mV relative differential offset and moving both
input setpoints together over±100mV. The confirmed stimulus is J6 on physical PM2.

## Successful acquisition

DAC2=1.034V+c, DAC3=2.038V+c, c=-0.100..+0.100V in10mV steps.
Commanded DAC2−DAC3=-1.004V throughout;20mV refers to offset from1.024/2.048V.
There are21sweep positions plus baseline/delta controls before and after:
25points×2banks×4captures=200 raw buffers independently decoded and checked.
DAC-A phase code32768 was held during acquisition to obtain coherent ADC B data.
Afterwards DAC-A restored0, DAC23 parked1.024/2.048V, amps/bypass/monitor inhibited,
TCA0. Kasli outputs/directions, FPGA/MCU/CPLD/flash/PLL profiles and other DAC
channels unchanged. No SMU access, no new build and no report/PDF regeneration.

|Common shift|A four-phase amplitude(code)|B four-phase amplitude(code)|A/B ADC rail samples|
|---|---:|---:|---|
|-100mV|172.99|79.13|25.02% /43.89%|
|0mV|154.82|70.07|0% /0%|
|+100mV|193.22|97.69|0% /0%|

Amplitude means max−min of four phase means and includes the reset waveform.
Negative-end clipped amplitudes are cropped observations, not true unclipped amplitudes.
The0→20mV delta controls changed mean A/B by−39.37/−37.21codes, with baseline
returns−0.13/+0.33codes. Thus the successful run has a demonstrated stimulus response.
Both shifted setpoints materially change the differential waveform. This does not
identify a physical cause or prove individual-amplifier saturation: actual DAC pin
voltages and the two single-ended integrator outputs were not measured.
The absence of ADC clipping also does not exclude individual output saturation.

## Route and sampling diagnostics retained separately

- First full scan on3 was coherent but had no stimulus control response; it is
  **not** evidence of common-mode insensitivity.
- Automated0→20mV→0 trials with one fitted channel enabled at a time located
  the J6 stimulus uniquely on2. Invalid ADC captures were retained and excluded
  from response calculations, not decoded with weakened checks.
- Initial mini-scan on2 stopped on ADC B two-sample coherency errors.
- Phase probe: code0 gave3/6 valid buffers,16384/32768/49152/65535 gave6/6.
  Code32768 was then used for the full scan and restored0 afterwards. The issue
  at0 is not silently marked repaired or production-qualified.
- An unsuccessful controller start from a missing import path performed no scan;
  its error/cleanup record is retained. The corrected executable is included.

All attempts and exact executed controller/native/decoder source snapshots are
in experiment-raw.tar.gz. raw-manifest.json and validation.json document full
archive readback. common-shift.csv/json/PNG/PDF are generated from successful
run03-ch02-phase32768 only. This is laboratory diagnostic evidence; engineering
history belongs outside the production PDF.

## Reproduce on this identified PM12 bench

The helpers enforce MCU1803/buildff2f746c, the established board/instrument leases,
external DAC0..3.3V bounds, and output inhibition. Identify current physical wiring
first; do not run fitted-channel discovery against absent fixtures.

```
# Hardware Python: /home/codex-hil/kasli-diot-bringup/.venv/bin/python
# Offline Python: /srv/codex-hil-nvme/tool-venvs/fit-measurements/bin/python
python discover_integrator_stimulus.py --connected 1 2 3 4 --out NEW_DISCOVERY
python probe_integrator_adc_phase.py --afe 2 --out NEW_PHASE_PROBE
python integrator_common_mode.py --afe 2 --adc-phase-code 32768 --out NEW_RUN
python plot_integrator_common_mode.py --root NEW_RUN
```

The current native acquisition module and existing selected qualification methods
were not edited. Plan-only checks verified25points, fixed differential voltage,
bounds, quantization-grid validation and rejection of invalid arguments.
