# MISO output enable versus normal SPI

This diagnostic extends qualified generator image399ead20. New image1cf28c8f
retains normal parser operation, LVCMOS33 DRIVE12/SLEW SLOW and external DD29.
It adds two modes to retained IPbus CSR0x306 (`0x474e0000 | mode`):

| Mode | MISO data | FPGA output enable |
| --- | --- | --- |
| 0 | Original raw SPI parser data | HSEL |
| 4 | Original raw SPI parser data, unchanged even at idle | Always enabled |
| 5 | Original SPI data when HSEL, otherwise zero | Always enabled |

Mode4 isolates the output-enable change. Mode5 additionally establishes zero
at idle. No parser hold or explicit data clamp is used (CSR0x305 remains0).
The existing generator modes1/2/3 are retained but not exercised in this test.
Selected data and normal read replies must remain correct in all SPI modes.

Observer format0x30004 adds logical MISO OE at state-word bit13; all existing
fields keep their positions. This is an internal source tap, not pad voltage,
DD29 input analog behavior, or an independent measurement of electrical Hi-Z.
Modes4/5 must show OE1 in all settled samples. Mode0 compares OE against HSEL;
any sampled mismatches are retained rather than hidden. The MCLK1 reference
and prior common-clock-stop/multibit-CDC limitations remain.

`prepare.py BASELINE OUT` derives complete source. Run heavy `build.tcl` on Dell.
`simulate.py SOURCE OUT` extracts the actual generated routing expressions,
then verifies original parser read0/1/2 replies, idle Hi-Z, continuous enable,
mode4 unchanged idle data, mode5 idle0, and normal-mode return.

`test_oe.py --work WORK` runs on Optiplex, acquiring all three existing leases,
verifying PM DNA/MCU identity, loading the temporary image and preserving Kasli
outputs/directions. It compares ordered blocks A0(6), B4(12), A0(6), C5(12),
A0(6), B4(12), A0(6), with an idle capture per block. All these frames use
read0/divider601. Additional functional blocks exercise reads0/1/2 at dividers
601 and61 (three repetitions per address/divider/mode), followed by six normal
read0 positive controls. Each mode is read back and allowed50ms settling before
arming; mode-change transients outside these windows are not characterized.

Direct raw SYS reset and MMCM LOCK captures decide each result. A quiet modified
mode only supports suppression if normal positive controls reproduce in the same
configuration. All failures/partial records remain in incremental JSON. The
wrapper restores exactc7531465, original Kasli divider, power/frontend/physical
ADC checks; it does not release Kasli outputs or change external PLL settings.

The first hardware run stopped after one positive normal-SPI control because
an unnecessary repeated write of unchanged parser mode0 timed out after SYS
reset. Its partial traces, executed source and successful restoration/ADC
postflight are preserved separately. The second wrapper removes that no-op
write and verifies the mode by bounded readback instead. Traceback source lines
can reflect later edits; each run's executed.py is the authoritative snapshot.

## Write-only extension and completed retry

`test_writes_reconnect.py` runs writes first, then a shorter OE comparison.
It uses a new PM IPbus UDP socket per window; the same FPGA image, logic state,
clocks and Kasli outputs remain in place. This follows partial runs where reads
continued but ARM writes stopped working after repeated SYS resets. The bounded
ARM retry checks the retained arm generation before reissuing; frozen status and
count are checked again after downloading. No peripheral write is replayed.

Write-only blocks use normal MISO, explicit MISO0 clamp, then normal MISO again.
Each has three repetitions of0x0000/0xffff/0x5555/0x0f0f to scratch0x40. The
original global host read-only allowlist remains unchanged. A local adapter
permits only these exact packets after loading the qualified diagnostic.
Original MCU DMA code matches sync7856341298badcfe or eightAA bytes; the fixed
packets contain none of those sync/reset bytes. Qualification receipt records
reference hash and exact packets. No production register sweeps are permitted.

The write counter and scratch value are verified through IPbus303/304, without
SPI readback. Raw MISO may toggle even during write frames because the parser's
shift register drives the output; write mode by itself does not imply constant
MISO. The clamp comparison leaves parsing/write commits active and verifies
sampled MISO0. The shorter OE blocks are A0/B4/A0/C5/A0, six read0/div601 frames
each, with an idle window before each block.

Results and run limits: [evidence](../evidence-miso-oe-20261115/README.md).
The write-only blocks completed (36/36 verified commits); the broader final
wrapper exited1 at an unconfirmed mode5 change. This is not a full protocol PASS.
