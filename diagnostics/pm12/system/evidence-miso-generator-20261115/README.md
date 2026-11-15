# Standalone MISO generator, 2026-11-15

PM12-K7-3A17A1B402212223 / MCU serial1803. Diagnostic399ead20.

Normal SPI controls:6/6 SYS resets before and6/6 after, all replies correct.
Continuously driven square-wave MISO:0/24 windows with reset or LOCK loss;
12216 logical MISO edges captured, every measured half-period20039 MCLK1 ticks.
Static low:0/12; static high:0/6. Kasli SEL/SCK/MOSI stayed driven at idle,
confirmed in raw observer samples; parser held, explicit MISO clamp disabled.

Thus continuous1kHz MISO alone did not reproduce the fault. This does not
exclude effects of SPI edge timing/phase, bit patterns, simultaneous signals,
or the normal HSEL-controlled output enable/Hi-Z transitions. The generator
continuously enables MISO. Its1kHz phase is fixed relative to MCLK1. Generator
and observer share MCLK1, so a complete common reference stop is invisible.
No electrical pad/clock waveform or load current measurement is claimed.

Image restoration and hardware regression PASS: exactc7531465 restored,
frontend_ready0xfff, power healthy, all12 physical ADC bankA first attempt PASS.
No Kasli reload, buffer direction/OE release, MCU/CPLD/flash or external PLL writes.
Run exit0. All leases released.

Source/protocol: ../miso_generator/. Complete frozen source/bit/qualified
Dell reports in source-and-bit.tar.gz. Incremental raw traces, executed wrapper,
identity/load/restore/ADC evidence in raw.tar.gz. Simulation receipt included.
