# Standalone PM12 MISO generator

This diagnostic tests whether MISO activity alone can reproduce SYS MMCM lock
loss, without sending SPI frames from Kasli. It preserves LVCMOS33 DRIVE12,
SLEW SLOW and the existing DD29/47-ohm/cable path.

IPbus CSR 0x306 reads `0x474e0000 | mode`:

| Mode | HMISO behavior |
| --- | --- |
| 0 | Original SPI data and HSEL-controlled output enable |
| 1 | Continuously driven low |
| 2 | Continuously driven high |
| 3 | Continuously driven square wave, 1000.017466 Hz nominal |

Nonzero modes override the FPGA MISO output enable independently of HSEL.
The mode register survives SYS resets. Two flip-flops synchronize it to MCLK1.
A 20039-tick half-period divider runs from the 40.0787 MHz MCLK1 reference,
independently of SYS reset. It is **not independent of the external clock chip**:
a complete loss of this reference can stop both generator and observer.

The existing CSR0x305 parser hold is enabled during non-SPI comparisons.
Kasli SEL/SCK/MOSI remain actively driven at idle; DIO directions/OE are unchanged.
No external function-generator connection is required and no second transmitter
is connected to the MISO net.

`prepare.py BASELINE OUT` derives the source from the qualified combined SPI
observer image. Build `build.tcl` on Dell with its shared slot launcher.
`tb.v` verifies default, static levels, divider spacing and mode changes.
`test_generator.py --work WORK` runs on Optiplex under all three board leases,
verifies board identity, loads the diagnostic, and compares:

1. Six normal SPI read0 frames at divider601.
2. Six static-low windows.
3. Twelve 1kHz windows.
4. Six static-high windows.
5. Twelve further 1kHz windows.
6. Six static-low windows.
7. Six normal SPI read0 return controls.

Observer raw captures include actual logical MISO, HSEL/SCK/MOSI, parser state,
SYS reset and SYS/CAP/GTX lock. Each window freezes at one second, 512 state
changes, or shortly after a lock-loss trigger. Quiet windows have sparse records:
last recorded tick is not their full exposure duration. No scope measurement of
pad voltage, edge rate, clock waveform or cable current is implied.

On completion/error after loading, the wrapper restores exact c7531465,
then verifies power, frontend readiness and physical ADC captures. Raw incremental
results and load/restore logs remain in the unique run directory.
