# Recovered-RX clock counter and CDCE status — 2026-11-15

Board PM12-K7-3A17A1B402212223. Resident SRAM now **ff2f746c**,
bit SHA256 `28fb5747bafe575455bff8bf91484c8ebb5303ea18d3e0a0925fdb0c4283d0b2`.
Original MCU unchanged; AUTO selects PRIMARY/HDMI. No MCU, CPLD, CDCE EEPROM,
flash or clock-profile writes. Kasli outputs remain driven; all leases released.

## Results

Each full window spans384 recovered RXOUTCLK cycles, approximately6.387us.
Nominal reference60.11805MHz comes from Kasli's incoming serial stream.

|Trial|Valid full windows|MCLK edges|CDCE U3/2 edges|SYS edges|SYS-reset trigger|
|---|---:|---:|---:|---:|---|
|Idle|2047|256|640|256|No|
|SPI read0|1633|256–257|640–641|255–257|Yes|
|SPI read1|1616|256–257|639–641|256–257|Yes|

Expected counts256/640/256 correspond to40.0787/100.19675/40.0787MHz.
Every UART R8 snapshot before/after every trial was **20009D38**, PRIMARY,
PLL lock pin1. Both SPI signatures correct. Final fresh reload: ADT identityC3,
frontend0xfff, power healthy, physical ADC bankA12/12 PASS; candidate retained.

No observed full-window deviation exceeds one count. The one-count excursions
near SPI are within endpoint CDC quantization/phase ambiguity: they do not prove
an extra physical pulse. SYS loss occurs approximately10ms after arm, freezes
history asynchronously, and the final partial window is excluded from statistics.
R8 snapshots cannot exclude a microsecond loss or brief source switch.

## Interpretation and limitations

TI SCAS862G table48 defines payload bit6 PLLLOCKPIN and bits27:25 selected
source1 PRIMARY/2 SECONDARY/4 AUX. UART wire format adds the low address nibble;
decode payload=word>>4. These fields are current state, not documented sticky
loss/switch history. [Official datasheet](https://www.ti.com/lit/ds/symlink/cdce62005.pdf).
There is no established separate PRI_LOS event latch in this test.

Counter is clocked by GTX RXOUTCLKSEL=2 before RX MMCM, not TX net_clk.
Recovered RX reference still depends on local GTX reference/CDR/reset machinery;
it is not a completely independent laboratory reference. Partial/invalid windows
are excluded. Common clock stops, analog runt pulses and phase jumps can escape
this measurement. UART PLL polling also toggles PLL SPI; idle control included.

## Reproduction and qualification

[Sources and register map](../rx_clock_counter/README.md). Simulation PASS covers
ratios, source/ring wrap, dropped edges, reset capture, invalid reference, retention
and rearm. Dell v2 timing WNS0.016ns/WHS0.063ns; Gray bus skew maxima
0.528/0.497/0.889ns below5ns. Independent bus-skew report qualifies coherence;
legacy ASYNC_REG false paths can override absolute max-delay constraints.
Inherited lhc120 clock-alias warnings remain. V1 misaligned RAM9000 was rejected
before programming; tested v2 uses aligned a000. No v1 hardware claims.

`hardware-raw.tar.gz` contains frozen buffers, CSR/UART snapshots, exact executed
script and load/postflight evidence. `qualified-build.tar.gz` contains exact v2
source, bitstream/checkpoints and timing/DRC/skew/qualification receipts.
`summary.json`, `windows.csv` and plot retain quantitative results. Plot intervals
show host SPI call bounds, not independently measured electrical frame timing.
Use analyze.py and plot.py from the source directory for offline regeneration.
