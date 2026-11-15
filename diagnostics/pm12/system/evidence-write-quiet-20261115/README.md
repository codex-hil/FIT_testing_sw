# Quiet-write MISO implementation, 2026-11-15

Resident PM image71ac56fb, SRAM bit SHA256
0407f67e189a25bfee0f6fe02bc6d805c79eedc8b75ce1cca24d2a6dca06daf1.
MCU serial1803 / DNA3A17A1B402212223 verified. CSR305=53520004 (quiet-write
enabled, parser hold/clamp disabled), CSR306=474e0000 (normal SPI/OE).

Old raw shift-register echo during writes is disabled by default. MISO stays0
for write frames; original read replies remain correct. FPGA OE remains HSEL,
DD29 is unchanged. Canonical parser and comparison wrapper separately simulated.

Three separate same-bitstream cohorts:
- hardware:12 quiet writes, no reset;8 complete raw controls,5 resets; then ARM
  loss. Restored exactc7531465; original-image ADC/power/frontend PASS.
- hardware02:12 quiet writes0/12 resets, one rawFFFF control1/1,12 quiet return
  writes0/12. All25 commits verified through IPbus with no SPI readback during
  write blocks. Three signature reads correct, but3/3 SYS lock losses. Full
  reduced measurement protocol completed; candidate postflight assertion failed
  without enough receipt detail to identify the exact check. Originalc7531465
  restored and its ADC/power/frontend passed. No candidate postflight PASS claimed.
- hardware03 fresh installation:24 quiet writes, all commits correct, zero MISO
  edges, zero resets/lock losses. No deliberate raw/read fault controls repeated.
  Candidate mode readback, power/frontend0xfff and all12 physical ADC bankA
  PASS first attempt; candidate retained, exit0.

The read-induced clock fault remains OPEN. Correct reply data is not a clock
health PASS. Quiet-write change is not claimed to repair physical clock coupling.
Logical MISO/controls are observed, not electrical pad voltage; shared-reference
stop limitations remain.

Kasli outputs stayed driven, original divider restored600, CFD e0=0. No MCU/CPLD/
configuration-flash or external PLL writes. All three hardware leases released.
Sources/protocol: ../write_quiet/. raw.tar.gz includes every executed wrapper,
partial/error record and postflight. source-and-bit.tar.gz freezes the exact
comparison build, routed checkpoints, bitstream and Dell timing/DRC reports.
