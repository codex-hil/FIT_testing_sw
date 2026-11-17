# PM2 integrator gates at ADC_CLK/40 — 2026-11-17

New experimental CPLD divider gives complementary A/B50% gates at ADC_CLK/40;
CLK40, ADC_CLK/DV and the EV/data mux are preserved. With the supplied
LHC40.0787MHz reference, ADC80.1574MS/s implies gates2.003935MHz, period499.018ns,
20 ADC samples per249.509ns integration/reset half. Absolute frequency is based
on that reference assumption, not an independent calibrated counter.

Physical PM2/J6 only. Kasli raw returns12/13 verify48 sample bins per normal gate
period,480 with the divider, then48 after restoration. Slow captures have exactly
480-bin rising-edge intervals on both lanes and about50% high occupancy. Kasli
reports a nominal960MS/s scale; the physical scale follows the shared LHC clock.
No Kasli direction changes or stop/release commands; HDMI held enable/state
unchanged before/after. PM FPGA ff2f746c and MCU/PLL profiles unchanged.

All42 ADC buffers pass the unchanged STR-edge and data-coherency decoder.
Normal-before, slow baseline, relative differential deltas4/8/12mV, slow return,
and restored-normal controls each have three A/B captures. External DAC input
base1.024/2.048V, symmetric delta perturbation, phase DAC32768 during acquisition.
Long ramps and reset plateaux become visible. Larger deltas clip at ADC zero:
B already5.73% at4mV; at8mV A17.79%/B27.08%;12mV A27.89%/B35.06%.
Baseline and return do not clip. Clipped data are retained and not used for a
linear gain/balance acceptance claim.

The final plot is analysis-v3. Upper curves fold the first capture for each
setting into40 sample positions, then align its largest positive sampled step;
this is not an absolute physical gate timestamp. Lower plots show first-buffer
raw time traces with independent origins. Scalar amplitudes are computed per
buffer before averaging. Earlier intermediate plots combined arbitrarily shifted
normal four-phase means across buffers; they are superseded, retained only in
the raw archive. This diagnostic does not change selected qualification results
or rebuild the production report.

Only CPLD2 changed, verified by all-CPLD two-pass array reads. Original image
restored and verified; all984 rows equal the before snapshot. Final normal gates
about20.039MHz, phase0, DAC23=1.024/2.048V, amps/bypass/monitor inhibited,
TCA0, leases released. Slow mode is available in the saved image, not left active.

ISE synthesis/fitting and GHDL comparison ran on Dell. Fit24/128 macrocells,
7 registers. Simulation checks1000 clock cycles, divide40/duty/complementarity,
unchanged CLK40/DV/mux and default-divider equivalence to original RTL.
Archive contains modified/original RTL/JEDECs, reports, native vectors, simulation,
executed acquisition/analysis sources, UART/SCPI/I2C records, all ADC buffers,
Kasli raw gate samples and full nonvolatile readbacks. Full archive readback and
SHA-256 manifest checked. Reusable bench-specific source/build/simulation under
[slow_integrator](../slow_integrator/README.md).
