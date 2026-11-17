# Physical channel7 ADC and integrators — 2026-11-17

Owner confirmed moving both USB8->7, preserving0/1->J8 ADC and2/3->J6 integrator.
Active/inhibited probes verified the route, normal selector map[0,1]. Fresh MCU1803,
FPGA ff2f746c and power guards passed. Both ADC257-point sweeps/adjacent-bit checks
and integrator coarse13/fine26points/independent returns/±5mV controls PASS.
No FPGA/MCU/CPLD/clock/SMU programming or new TDC/phase/DAC scan was needed.
Existing fitting5-8 timing/monitor/internal-DAC results remain selected unchanged.

The importer matched the same frozen method/source contracts as channel8.
Previous selected result IDs and all sealed/ch08 files remain byte-for-byte.
Shared transfer/integrator/zero-input waveform/FFT overlays now include7–12;
older acquisition/build versions remain separately identified in their receipts.
Commanded voltages and nominal sample rate are not calibrated ADC-only gain/noise.

`channel07-delta.tar.gz` is an incremental portable campaign archive: extract the
base `evidence-group05-08-20261117/campaign-raw.tar.gz` into a NEW directory, then
extract the delta there. `delta-provenance.json` gives the base SHA and complete
resulting inventory. Run campaign_report.py on the reconstructed campaign for an
offline report. Do not overwrite live hardware data with archive extraction.
Exact executed outer source is retained with an executed suffix; ch07 staging
logs were prefixed and ch08 logs restored from the base, with a reconciliation
journal. Native data/source snapshots are immutable.

Channel7 ADC gains A/B: -1780.88/-1777.82code/V; template-removed RMS0.558/0.554code.
Integrator gains -2683.0/-2612.8code/V; repeated mean changes +0.265/-0.285code
at the respective balance candidates. Final external DAC0/1=1/1V,2/3=1.0265/2.0455V.
[Current91-page editable report](../evidence-campaign-assembly-20261113/report.pdf).
Base+delta inventory independently verified from archive bytes; see archive-validation.json.
