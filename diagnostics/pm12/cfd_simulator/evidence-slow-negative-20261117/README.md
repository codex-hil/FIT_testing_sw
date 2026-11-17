# PM2 slow gates, negative differential offsets — 2026-11-17

Same complementary divide40 gate image, about2.004MHz, nominal ADC80.1574MS/s.
External DAC2=1.024V+delta/2, DAC3=2.048V-delta/2; delta0,-4,-8,-12,-20mV.
Maximum setpoint2.058V, minimum1.014V. The negative input perturbation gives
rising integration ramps with headroom above the lower ADC rail. No valid
slow-scan samples hit either ADC rail, including the -20mV point reaching
about1245(A)/1165(B)codes in its first captures. Switching steps remain visible;
charge injection/clock feedthrough is a hypothesis, not a demonstrated cause.

The published plot has81 unchanged consecutive decoded samples per panel,
two complete40-sample periods including endpoints, no folding or averaging of
plotted values. A periodic template chooses only a relative start index at
the largest positive step. It does not establish absolute gate timing.

Run01 phase DAC32768:45/48 buffers decode correctly. All three A captures at
-12mV fail the unchanged two-sample stability test at4–5 selected positions;
they are retained and excluded. Run02 repeats -12mV at phase DAC49152:
all30 buffers decode correctly, including controls/returns. This confirms a
usable readout at that phase for this trial, not a permanent repair or global
qualification of the original phase setting. Both A/B -12mV panels use the
repeat and are labelled accordingly; other points use run01. Do not interpret
the overlaid point series as a fixed-phase precision timing calibration.

Total75 valid and3 rejected raw buffers; validation.json independently decodes
every buffer and records source hashes, ranges, rail counts and rejection details.
provenance.json maps each plotted trace to its exact run/buffer/indices/phase.
CSV contains810 displayed sample values. All data and both attempts are retained.

Each run verifies the normal CPLD image first, changes only CPLD2, captures
Kasli periods48→480→48 bins and preserves held HDMI enable/state. Both restores
independently match all984 original array rows. Final normal20MHz gates,
phase0, external DAC23=1.024/2.048V, selected amps/bypass/monitor inhibited,
TCA0, leases released. No FPGA/MCU/PLL programming or Kasli direction changes.
No new build was required; the previously qualified slow-gate vectors were reused.
No production qualification/selected campaign results or production PDF changed.

The archive includes exact executed acquisition sources, raw ADC/gate buffers,
readbacks and SCPI/UART/I2C logs. Existing build/native vectors are identified
by qualified SHA-256 in run.py and retained in the
[original slow-gate archive](../evidence-slow-gates-20261117/README.md).
Full archive readback matches raw-manifest.json.

```
python slow_integrator/run.py --out NEW_RUN --vectors QUALIFIED_VECTOR_DIR \
  --station STATION_JSON --deltas-mv -4 -8 -12 -20
# Explicit readout-phase repeat when required; preserve rejected first attempt:
python slow_integrator/run.py --out NEW_REPEAT --vectors QUALIFIED_VECTOR_DIR \
  --station STATION_JSON --deltas-mv -12 --adc-phase-code 49152
python slow_integrator/plot_two_periods.py --run NEW_RUN --supplement NEW_REPEAT --out NEW_PLOT
```
