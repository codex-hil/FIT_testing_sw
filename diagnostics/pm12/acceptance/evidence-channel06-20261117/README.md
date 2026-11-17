# Physical channel6 — 17 November2026

Both USB moved7→6: DAC0/1→J8 ADC and2/3→J6 integrator. Active/inhibited probes verified routing.
Both257-point ADC sweeps and adjacent-bit exercise PASS under the frozen channel8 contracts.
Integrator **INCOMPLETE**: bankB has no reliably separated integration/reset template near balance.
A shows a sign reversal, but neither bank is claimed to have passed the complete fine/return protocol.
Coarse13points and all raw buffers retained. DAC-A diagnostic16384/32768/49152/65535 did not resolveB;
DAC-A explicitly restored0. This does not prove a hardware fault. Validation thresholds unchanged.
No FPGA/MCU/CPLD/flash/PLL programming, global Kasli stop, output release, or SMU access.

ADC shared plots and zero-input FFT cover6–12; integrator7–12 PASS comparisons remain unchanged.
Commanded voltages and nominal sample rate are not calibrated gain/noise/jitter.
Incremental archive: extract original group05-08 campaign-raw.tar.gz into a NEW directory,
then overlay channel06-delta.tar.gz (includes7). Hash inventory in delta-provenance.json.
All previous selected IDs and sealed raw results preserved; incomplete6 is explicitly recorded.

Final DAC0/1=1.0000/1.0000V,2/3=1.0240/2.0480V. [Current94-page editable report](../evidence-campaign-assembly-20261113/report.pdf).
Base+delta archive independently verified: 22756 files.
