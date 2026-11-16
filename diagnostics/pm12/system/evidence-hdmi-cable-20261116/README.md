# HDMI cable comparison — 2026-11-16

PM12-K7-3A17A1B402212223, unchanged FPGA ff2f746c, original MCU and AUTO/PRIMARY.
User supplied cable photograph label389G1848DAA1400NEH and requested comparison
on replacement cable. Physical cable change and internal shielding are not independently
instrumented; no claim that a shield defect has been established.

Two completed cohorts: initial2 reads, then12 reads (6 per signature).
**0/14 SYS-loss triggers; 14/14 correct signatures**, idle controls without trigger.
Prior same-image2026-11-15 comparison was2/2 SYS-loss triggers. Every CDCE R8
before/after remains20009D38 (PRIMARY, PLL lock pin1). Both fresh final reloads
passed physical ADC bankA12/12, frontend0xfff, ADT C3 and power checks.
Kasli held driven throughout; divider600 restored; no MCU/CPLD/flash/CDCE changes.

The observation is consistent with cable/connector-path sensitivity, but this is
before/after rather than controlled A/B/A. It does not identify HEC shielding,
MISO crosstalk or the cable itself as uniquely responsible. Replugging contacts
and elapsed time are uncontrolled variables. The original clock-loss finding
is not closed by this finite series.

Each non-triggering run times out after100ms. The circular RAM contains the last
approximately13ms, so the initial SPI frame has been overwritten. Sticky SYS loss
and global edge-count extrema span the whole armed interval; frozen raw buffers
must not be described as waveforms around SPI in this no-trigger cohort.
Recovered-reference/CDC limitations from the preceding counter evidence remain.

Reproduce with rx_clock_counter/test_counter.py --expected-resident ff2f746c
--repetitions6 and a new output-name, using the qualified counter work directory.
Archives include exact executed scripts, all CSR/extrema, UART status, frozen raw
windows, JTAG identity/reload logs and final ADC data. No heavy rebuild was needed.
