# Separate raw TDC event buffers

OFFLINE INTEGRATION CHECKPOINT. Optional IPbus window and twelve-receiver
wiring component implemented and simulated at component level. Not yet
instantiated in the PM board top; no new bitstream or hardware acquisition.
This work performs no board programming; build882901f6 is the previous
qualified ADC/IPbus/I2C reference. Current hardware state was not rechecked.

User selected separate ADC and TDC memory, and RAW TDC results only. Provide
12 independent banks,4096 events each,16bits per record:96KiB payload total.
Bits12:0 contain original `tdc_raw`, bits15:13 zero. Original raw13 comprises
fine7 from THS788 plus FPGA coarse6; fine7 alone does not span the25ns sweep.
No CH_CORR, channel offset subtraction or trigger acceptance is applied here.
Host can inspect `record &0x7f` and `(record>>7)&0x3f` separately.
Vivado2025.2 out-of-context synthesis on xc7k160tffg676-3 measured
12 RAMB36E1 +12 RAMB18E1 =18 BRAM36 equivalents,157 LUTs and740 FFs.
This is the buffer core alone; unused record bits15:13 are constant zero. Current deployed FPGA uses45/325 BRAM36; this addition is small
relative to available memory, but original receiver/clock integration still
needs synthesis, placement and timing validation.

## Original receiver hook

```
python3 instrument_receiver.py /path/to/FIT_TCM_GW_FPGA
```

Reads immutable git object857b773eec28282b357d4668ab934e95f41b6fe7 and checks
original SHA256 before making exactly three anchored edits in a generated copy.
Original sources are not edited. Adds `diag_raw_valid`, zero by default each
rising tdcclk, asserted only alongside the original unlocked TDC_raw_i update.
The instrumented copy retains entity name TDCCHAN: compile it INSTEAD OF the
unmodified entity, never both. pin_capt, TDC_FIFO and clock/reference/autophase
integration remain original dependencies. Pin/clock integration is not yet done.

Connect each buffer's event to diag_raw_valid, raw to tdc_raw. Both update after
the same tdcclk edge; the BRAM writer observes the pulse and matching stable raw
word at the following rising edge. Do not substitute original tdc_rdy, which is
sticky and asserts before the last serial bit. For continuous acquisition,
legacy tdc_raw_lock must be kept low; freeze the CAPTURE BANK, not the receiver.

## Buffer core and clock crossing

`buffers.py` is Migen TdcBuffers. Channels0..3 write in tdc1,4..7 in tdc2,
8..11 in tdc3. Each bank writes in its actual result-clock domain, one record
per valid event. The separate sys port reads frozen BRAM. No oversampling or
per-sample CDC is inserted in the TDC data path.

ARM/STOP are ONE-sys-cycle command pulses. ARM accepted only when ready;
busy rearm is rejected without modifying an in-progress capture. ARM propagates
through a3-stage toggle handshake to every source domain; wait for started
before enabling the Kasli stimulus. This is not a simultaneous physical trigger
across channels: a common stimulus after all-started establishes event alignment.
Each bank freezes after depth accepted events. A source stops itself without
waiting for IPbus, preserving all completed data. Events after that bank is full
are outside the acquisition and not counted as captured records.

STOP is accepted only while busy and all sources have acknowledged start;
otherwise rejected. It freezes partial/empty banks and waits for all source
acknowledgements. Read counts/data only after valid. Count snapshots use the
stable-mailbox contract: source count is held before completion ACK, data has
two sys synchronizer stages and ACK has three; counts latch only after all ACKs.
Read latency is synchronous BRAM (the simulation reader waits two sys cycles).
Unwritten records at indices>=counts[ch] must be rejected by the future bus map.

If any source clock stops, start/completion may remain pending. A host timeout
must report failure; never force valid or reuse an unknown bank. The optional `ipbus.py` adapter adds a bounded acquisition watchdog and
sticky failure on loss of frontend readiness. After failure it masks memory
and counts and rejects commands until a coordinated FPGA reset; a later
completion cannot make a failed generation readable. Board frontend readiness
and actual clock-presence detection still need wiring before acquisition. All domains share a coordinated
FPGA reset; independent domain resets during acquisition are unsupported and
require complete diagnostic reset/recovery. Do not treat clock-present as PLL/
autophase readiness: the frontend must qualify those separately.

## Validation

```
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python test_buffers.py
```

Behavioral Migen simulation uses three asynchronous result clocks and sys.
12 banks tested for full acquisition, distinct channel ordering, frozen memory
with sources still active, busy rearm rejection, identical consecutive raw
values, three acquisition generations, and STOP of an empty capture. This
validates the buffer core with modeled events, NOT THS788 decoding or physical
CFD pulses. The generated receiver hook is anchor/hash checked. `test_receiver_ghdl.py`
passes all128 fine values, commit-pulse timing, early/sticky ready and raw lock
using the original decoder with coarse capture/FIFO STUBBED. It explicitly
initializes the otherwise uninitialized serial bit counter in a simulation-only
copy; the deployable receiver remains unchanged. This models zero FPGA
power-up state, not a demonstrated reset/startup contract. Full coarse/FIFO
and clock/phase simulation and physical startup validation remain pending.

Next: integrate the original coarse capture/FIFO and three clock/reference/
autophase subsystems into the board top, qualify startup, validate implementation
and timing, then acquire hardware data. Hardware sweep0..24ns
requires a coherent Kasli–PM reference and verified isolated CFD injection.

## IPbus integration

`Registers(..., tdc=window)` enables ABI0x00010002, feature bit4. Without the
optional argument the existing ABI/map stays unchanged. All addresses are
32-bit WORD addresses; existing ADC/I2C windows are preserved.

| Address | Access | Meaning |
| --- | --- | --- |
| 0x200 | W | 1=ARM,2=STOP; other values ERR |
| 0x201 | R | bits0 valid,1 busy,2 started,3 arm-ready,4 frontend-ready,5 sticky fault |
| 0x202 | R | buffer completion generation; only use with valid |
| 0x203 | R | depth4096 |
| 0x204 | R | channels12 |
| 0x220..0x22b | R | frozen counts, zero unless valid |
| 0x20000..0x2bfff | R | channel0..11, stride0x1000; bits12:0 raw,15:13 zero |

Unwritten indices, active/invalid/faulted bank reads, writes to read-only
registers and invalid ARM/STOP return IPbus ERR. Wait STARTED before stimulus;
STOP can freeze partial or empty banks. Default watchdog is40million sys
cycles (1s at40MHz), starting at capture busy. Increase it for slower patterns.
A sticky fault requires a coordinated FPGA reset; resetting just the buffer
handshake or clearing a software flag is unsafe after a missing source clock.

`receiver.py:TdcAcquisition` wires twelve instrumented TDCCHAN instances to
these banks in three result-clock domains. It intentionally requires externally
provided original coarse counters, BC timestamps and300/600/quadrature clocks;
it does not invent these from the ADC clock. Caller supplies three result clock
domains and synchronized frontend readiness including PLL/autophase qualification.
Do not connect readiness to a constant for board acquisition.

Additional simulation commands (run from this directory):

```
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python test_ipbus.py
python3 test_receiver_ghdl.py --ghdl /home/codex-hil/coolrunner2-recovery/tools/ghdl
```

The IPbus test uses the actual legacy register FSM and three asynchronous source
clocks: continuous-strobe burst reads,12 banks, zero extension, address/count
bounds, empty STOP, old-generation rejection, acquisition timeout, readiness
loss/relock and legacy register access. The separate existing ADC/I2C register
regression also passes. These are simulations, not Ethernet or physical TDC tests.

`generate_component.py` successfully elaborates the twelve-receiver/buffer/window
component into Verilog. This checks Migen integration only, not binding of
VHDL dependencies or board-level synthesis/timing. `validation.json` records
the offline simulation commands, outputs and source hashes.
