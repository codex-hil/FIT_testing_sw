# Combined observer / runtime parser reset A-B-A

Single temporary PM image derived from the reset-independent state observer.
Kasli, clock profiles and output-buffer directions/OE are unchanged. No
programming between modes. Retained IPbus305 accepts0..3, reads53520000|mode:

| Mode | Parser | MISO data |
|---|---|---|
|0(A)|normal|normal response|
|2(C)|normal|forced0|
|3(B)|held in reset|forced0|

Mode1 is reset with retained raw MISO and is used in the additional reset-only
cohort (test_reset_only.py):0→1→0→2→0→1→0, six frames per stage. Only bit0
changes in reset/release pairs; the clamp bit remains0. Normal diagnostic
signatures have bit15=0, so retained raw MISO is verified0 while held. The first
clamp-matched cohort uses modes0/2/3. Holding the parser uses its original deselected/reset branch;
count/reading stay0, data/address/scratch/write counters are retained. Physical
SCK still clocks the circuit. This is not a clock gate. MISO physical output
enable remains governed by actual HSEL. Logical output matching is not a
continuous electrical observation of the pad, especially during tristate.

Mode is FPGA-initialized0 and survives SYS reset. Observer format30003 records
hold/clamp in state-word bits11/12, plus actual parser state and MMCM controls.
Tests verify mode readback and sampled flags after SYS resets. Mode4 is rejected.
Simulations distinguish active/clamped parser from held/clamped and release.

Protocol: get positive direct SYS-reset traces in mode0 (not just host read
timeouts), choose fixed divider/address with at least2 confirmed resets, then
C1→B1→C2→B2→C3→A-return, six frames each. Search starts601,602,600,61,62,60,
two repeats of reads0/1/2; if hits are spread between addresses, up to4 extra
normal confirmations on the selected address. Only runtime mode changes after
selection. If baseline does not reproduce, no suppression conclusion is made.
If C alone suppresses while normal returns, parser-specific suppression is not
established: removal of MISO data transitions already changes the outcome.
If B still resets, parser transitions are not necessary for this condition.

Read-only operations retry with bounded recovery; writes are not replayed
blindly. ARM toggle is confirmed through seen-state change. Frozen records
are saved incrementally before ancillary operations. First8watch ticks are
ARM settling. Sampled multibit state is not atomic; common watch/reference
clock stop is invisible. Exact executed.py is authoritative for each series.

All3 shared hardware leases, MCU1803 and FPGA DNA checks required. Heavy
builds run on Dell; programming stays Optiplex. Finally restore exact PMc7531465,
old SPI divider and held Kasli outputs; check PGOOD/frontend/physical ADC.
No MCU/CPLD/flash or explicit external PLL/analog changes. No Kasli reload.

prepare.py --baseline ORIGINAL_OBSERVER_SOURCE --out NEW emits generated HDL;
old Migen regeneration omits the extension. ab-build.json is the authoritative
manifest. test_ab.py --work ROOT [--output-name NEW] runs hardware.
analyze.py --result RUN/result.json --out NEW validates raw control and state.

Two cohorts use the identical bitstream but are reconfigured separately; never pool
their conditions as though no reload occurred between cohorts. Within each cohort
there is no programming between conditions. The executed.py in each raw directory
is authoritative. First rejected attempt stopped on a Python name error before SPI.
