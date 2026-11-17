# Slow complementary integrator gates

Experimental CPLD ADC-mux variant, with `GATE_DIV` even and >=4. Default4
reproduces the original nominal20MHz gate logic. Qualified build setting40
produces complementary A/B at ADC_CLK/40, with50% duty. CLK40, DV/ADC strobe,
EV chain and ADC mux are unchanged. Compile-time selection, not a runtime CSR.
The original production mux source remains separate.

For ADC80.1574MHz, gate2.003935MHz, period499.018ns, each half249.509ns.
There are40 ADC samples per gate period,20 per integration/reset half.
Do not use the previous four-phase estimator to analyze these waveforms.

The included build.sh explicitly selects GATE_DIV40. New ISE/GHDL jobs belong
on Dell using the shared remote-build handoff; only physical JTAG/acquisition
runs on Optiplex under PM12/MCU/Kasli/DAC leases. Preserve the normal-image
JEDEC and verify it before programming. Scope to the selected CPLD and verify
all twelve array readbacks; restore and verify the original after comparisons.

Simulation compares against original.vhd for1000 CLK80 cycles: divide40,
complementary50% gates, unchanged CLK40/DV/data mux and default4 compatibility.
The physical diagnostic is currently channel2 only, using the existing J6
DAC2/3 cable and Kasli return lanes12/13. Other channels have not been retested.

Hardware repeat with the exact qualified channel2 native vectors (from evidence):

```
python run.py --out NEW_RUN --vectors EXTRACTED_VECTOR_DIR --station STATION_JSON
python analyze.py --root NEW_RUN
```

This diagnostic is deliberately bound to the identified PM2 bench, qualified
vector hashes and confirmed J6 route. It captures Kasli lanes12/13 before,
during and after the change without stopping/releasing shared outputs. It
collects normal controls and slow-gate relative differential offsets0/4/8/12mV;
these are characterization setpoints, not an unclipped linear-fit guarantee.
Native decoding validates all ADC words before waveform analysis. The time
scale uses the supplied LHC40.0787MHz, not an independently calibrated frequency
measurement. Publication selects final analysis-v3; the first intermediate
analysis incorrectly combined unaligned normal-period means across buffers.
Final amplitudes average each buffer's own span, and displayed folded curves
use the first buffer's period means, aligned on the largest positive step.
This is waveform alignment, not a physical gate timestamp. Raw captures and
all intermediate outputs remain in the evidence archive.

For two complete contiguous periods instead of the folded display, run
`python plot_two_periods.py --run ORIGINAL_RUN --out NEW_OUTPUT`. It shows81
unchanged consecutive samples per trace, including both period endpoints.

Signed offsets can be selected with `--deltas-mv -4 -8 -12 -20`.
`--adc-phase-code` defaults32768; any alternate setting must be retained and
labelled. `plot_two_periods.py --supplement EXPLICIT_REPEAT` may replace a whole
point if either bank has no valid capture, preserving the repeat run/phase in
every trace provenance. Invalid raw captures remain archived and are not plotted.
[Negative-offset results](../evidence-slow-negative-20261117/README.md).
