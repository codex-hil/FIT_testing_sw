# Quiet MISO during diagnostic SPI writes

The old diagnostic wired MISO directly to a common RX/TX shift register.
Write frames therefore echoed delayed incoming bits even though no read response
was requested. This was an implementation shortcut, not a protocol requirement.
The canonical `tdc_live120/generated/hdmi_slave.v` now gates MISO with `reading`:
read replies are unchanged; a write drives a defined zero while selected.

The FPGA still uses HSEL-controlled output enable. DD29 has no separate OE,
so making the FPGA pin Hi-Z during a write would float its buffer input rather
than disable the cable output. No voltage standard, drive strength, external
buffer direction, clock profile or real peripheral setting is changed.

For a within-image comparison, `prepare.py BASELINE OUT` derives image71ac56fb
from diagnostic1cf28c8f. Its wrapper retains raw parser data internally and adds
quiet-write bit2 to CSR0x305 (default4, read53520004). Mode0 restores old echo;
mode4 gates data with actual parser reading state. Existing parser hold bit0 and
explicit MISO0 clamp bit1 remain available but unused. Observer format30005 adds
quiet-write enable at state bit14; OE remains bit13. Source archives retain the
original raw parser for the comparison. The canonical direct parser and wrapper
implement equivalent default quiet-write behavior.

`tb.v` verifies the wrapper and canonical implementation separately: no MISO
activity at any sample/edge in write frames, all scratch commits, read0/1/2 and
scratch readback, plus raw comparison/return when enabled.

`test_write_quiet.py --work WORK` uses the fixed qualified scratch packets from
the preceding experiment, with no SPI readback during write blocks. Sequence:
12 quiet writes,12 raw writes,9 raw/9 quiet-mode signature reads,12 quiet writes.
Fresh PM IPbus socket per capture; bounded checked retries only for idempotent
configuration levels and generation-checked ARM. SPI writes are never replayed.
Mode readback, raw buffer control flags, MISO, SYS reset/LOCK and commit counters
are checked. All three board leases and PM DNA/MCU identity checks are mandatory.

On full protocol success with correct write/read data and no quiet-write resets,
the wrapper retains candidate mode4 in SRAM only after power/frontend/physical
ADC postflight passes. Otherwise it restores exactc7531465 and validates that
image. Kasli output directions/OE remain driven and its divider is restored.
No MCU/CPLD/configuration-flash programming or external PLL writes.

The long wrapper is an exploratory stress protocol. Its first run stopped on
ARM loss after12 quiet writes (no resets) and8 raw controls (five resets),
then restoredc7531465 with ADC/power/frontend PASS. `qualify_write_quiet.py`
is the shorter bounded qualification:12 quiet writes, one rawFFFF positive
control,12 quiet writes again, then read0/1/2 in quiet-write mode. It retains
the candidate only if all25 writes commit, all24 quiet writes have no reset,
all three read replies are correct, and candidate power/frontend/ADC passes.
The smaller positive control is explicitly one frame, not a statistical rate.

Final installed state: [evidence and cohort separation](../evidence-write-quiet-20261115/README.md).
Reduced mixed fault-injection measurements completed but candidate postflight
failed an assertion and restoredc753. `install_write_quiet.py` then freshly
loaded the identical bit and checked24 quiet writes without deliberate fault
controls, mode readback, power/frontend and physical ADC. It retained71ac56fb
in SRAM after all checks passed. Read-induced SYS clock loss remains OPEN.
