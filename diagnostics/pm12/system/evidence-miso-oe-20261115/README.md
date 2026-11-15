# Write-only SPI and MISO output-enable diagnostics, 2026-11-15

Board PM12-K7-3A17A1B402212223, MCU serial1803. Temporary image1cf28c8f.

The final run hardware04 completed all36 scratch writes, verified by IPbus303/304
without SPI readback: normal MISO8/12 SYS reset/LOCK losses; active-parser
MISO0 clamp0/12; normal MISO return11/12. All36 writes committed correctly.
Fixed values0000/FFFF/5555/0F0F, three repetitions each, address40 only.
Qualification excludes MCU sync/reset bytes; global read-only host guard unchanged.

Then identical read0/div601 normal/always-OE/normal controls each gave6/6 resets,
with correct signatures and zero sampled OE mismatches. Removing Hi-Z alone
does not suppress the fault; Hi-Z is not necessary for reproduction. Internal
OE/data taps do not measure pad voltage or DD29 analog behavior.

The full planned protocol did NOT complete. hardware04 stopped when mode5
(always OE plus idle0) was not confirmed by register readback; that window has
no raw capture and is not counted. The write series and A0/B4/A0 blocks are
complete, but the wrapper exit is1. Earlier partial cohorts retained separately:
hardware stopped at repeated no-op write; hardware02/03 at ARM timeouts.
Fresh IPbus socket per window and bounded generation-checked ARM retries were
used in hardware04. No SPI peripheral write is retried.

Every run restored exactc7531465. Final hardware04 frontend0xfff/power healthy,
all12 physical ADC bankA PASS first attempt. Kasli outputs remained driven;
original divider restored. No MCU/CPLD/flash or external clock-profile writes.
Shared board leases released. Source/protocol: ../miso_oe/.

raw.tar.gz preserves every run, executed source, errors and restore/ADC receipts.
source-and-bit.tar.gz preserves the frozen generated source, routed checkpoints,
bitstream, Dell timing/DRC and extracted-routing simulation. Summary independently
validates raw samples, clamp/OE states, replies and write commits; partial windows
are explicit. Generator/observer common-reference-stop limitations remain.
