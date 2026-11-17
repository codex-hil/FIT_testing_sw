# Channel6 integrator repeat after pressing CFD board — 17 November2026

User pressed CFD6 and confirmed DAC2/3→J6 channel6. Independent13-point coarse
acquisition completed with fresh MCU1803/FPGAff2f746c/power guards. The controller
again stopped at bankB: no unambiguous integration/reset template near balance.
Fine and independent return scans did not run. **INCOMPLETE**, unchanged thresholds.
A shows a sign reversal but no complete fine/return qualification is claimed.
Pressing the board did not remove this measured symptom; no hardware defect or
specific contact failure is established. Raw before/after buffers retained.

Latest repeat explicitly selected, previous incomplete and all phase diagnostics
preserved. No other selected cases changed. ADC5–12 PASS and integrators5,7–12 PASS
remain valid. No ADC/TDC/phase/SMU repeat, programming, PLL change or Kasli release.
Final6 amplifiers disabled, ADC bypass isolated, all monitors inhibited/TCA0;
external DAC0/1=1/1V,2/3=1.024/2.048V. Leases released. DAC-A remains established0.

Reproduce archive: original group05-08 campaign-raw.tar.gz plus reseat-delta.tar.gz
in a NEW directory. Complete inventory verified; do not overwrite live data.

[Current98-page editable report](../evidence-campaign-assembly-20261113/report.pdf).
