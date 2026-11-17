# Physical channel5 ADC and integrators — 2026-11-17

Owner confirmed moving both USB6->5, preserving0/1->J8 ADC and2/3->J6 integrator.
Active/inhibited probes verified the route, normal selector map[0,1]. Fresh MCU1803,
FPGA ff2f746c and power guards passed. Both ADC257-point sweeps/adjacent-bit checks
and integrator coarse13/fine26points/independent returns/±5mV controls PASS.
No FPGA/MCU/CPLD/clock/SMU programming or new TDC/phase/DAC scan was needed.
Existing fitting5-8 timing/monitor/internal-DAC results remain selected unchanged.

The importer matched the same frozen method/source contracts as channel8.
Previous selected result IDs and all sealed/ch06/ch07/ch08 files remain byte-for-byte.
Shared transfer/integrator/zero-input waveform/FFT overlays now include5–12 (integrator6 excluded);
older acquisition/build versions remain separately identified in their receipts.
Commanded voltages and nominal sample rate are not calibrated ADC-only gain/noise.

`channel05-delta.tar.gz` is an incremental portable campaign archive: extract the
base `evidence-group05-08-20261117/campaign-raw.tar.gz` into a NEW directory, then
extract the delta there. `delta-provenance.json` gives the base SHA and complete
resulting inventory. Run campaign_report.py on the reconstructed campaign for an
offline report. Do not overwrite live hardware data with archive extraction.
Channel5 logs have unique names; previous native data/source snapshots are immutable.
The delta includes channel6 and7 as well, so it only requires the original base archive.

Final DAC0/1=1.0000/1.0000V,2/3=1.0268/2.0452V. [Current97-page editable report](../evidence-campaign-assembly-20261113/report.pdf).
Base+delta archive independently verified: 27433 files.

ADC gains A/B: -1778.61/-1790.04code/V; template-removed RMS0.621/0.557code.
Integrator gains -2592.4/-2635.1code/V, balance deltas3.245/8.228mV.
ADC5–12 now PASS; integrators5 and7–12 PASS. Channel6 remains INCOMPLETE,
excluded from the common integrator PASS overlays; channels1–4 await the next fitting.
