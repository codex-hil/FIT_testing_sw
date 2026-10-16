# PM12 raw TDC capture through IPbus

Integrated ADC + TDC + passive I2C + MCU SPI diagnostic. Vivado2025.2 build
`4bbe9dfc` is running in PM12 S/N1803 FPGA SRAM after physical smoke tests.
See [CURRENT_STATE.md](CURRENT_STATE.md) and [measured](measured/).

Twelve independent banks hold4096 events each,16bits per record. Bits12:0
are original `tdc_raw`; bits15:13 are zero. The raw13 is FPGA coarse6 plus
THS788 fine7, not fine7 alone. No channel correction, offset subtraction or
trigger acceptance is applied. Decode `fine=raw&127`, `coarse=(raw>>7)&63`;
conversion into calibrated time is not implemented.

The buffer core uses12 RAMB36E1 +12 RAMB18E1,18 BRAM36 equivalents. The routed
combined diagnostic uses63/325 BRAM36 equivalents. Setup slack0.082ns, hold
slack0.050ns, pulse-width slack0.317ns; zero unclocked registers and zero
unconstrained internal endpoints. One DRC warning concerns unused almost-full
nets inside the generated FIFO; no DRC errors. See [timing](reports/integrated-timing.txt)
and [DRC](reports/integrated-drc.txt). These are the diagnostic's constraints,
including asynchronous CFD sampling; they do not qualify external pulse accuracy.

## Physical validation and its limits

- Three PLL locks, three autophase completions and three live result clocks:
  frontend diagnostic0xFFF.
- Five ARM/STOP captures, generation/count snapshots and client reconnects pass.
  All twelve counts are zero, including50/100/200ms quiet observation windows.
- Actual IPbus returns ERR for busy ARM, invalid commands, read-only writes,
  out-of-range memory and the first unwritten record of all12 banks.
- Existing ADC synthetic capture/readback passes all49152 words. This does not
  establish actual ADC conversion or the analog front end.
- ATxmega power-good, UART and32-vector FPGA SPI scratch/restore tests pass.
- No MCU/CPLD/configuration-flash programming or peripheral reconfiguration.

**No real TDC event has been acquired in this run.** Nonempty raw-bank readout,
coarse/fine correctness, FIFO throughput/overflow and a coherent0..24ns CFD
phase sweep remain NOT_RUN. Inject isolated, verified LVDS CFD pulses before
claiming TDC conversion. The external Kasli/PM reference must be coherent for
phase measurements. Presence monitoring alone is not a measurement of clock
frequency or jitter.

## Receiver and clock implementation

`prepare_board.py` reads immutable objects from upstream
`FIT_TCM_GW_FPGA` commit857b773eec28282b357d4668ab934e95f41b6fe7.
`instrument_receiver.py` verifies original TDCCHAN SHA256
`dde8d417ef7770b329e853cb845d43b8d74e0259ea37f86647695c817f8bf833`
and makes exactly three observational edits in a generated copy: new output
`diag_raw_valid`, default zero per rising result clock, pulse at the original
unlocked raw-register commit. Original sources are not edited. Compile the
instrumented entity INSTEAD OF the original TDCCHAN, never both.

The pulse and raw word update together; the bank consumes them on the next
result-clock edge. Original `tdc_rdy` is sticky and asserts before the final
serial bit, so it is not the write-enable. Keep `tdc_raw_lock=0`: freeze the
capture banks rather than the receiver. Identical consecutive timestamps are
valid events and are retained.

`receiver.py` wires twelve original receivers to banks in three result-clock
domains. `frontend.py` implements the original per-chip300/600MHz/quadrature
clock, pin_capt reference, BC timestamp and autophase topology. MMCM multiplier30,
feedback phase3degrees and fine feedback shifting follow the pinned IP property
report. The system clock takes the reference sampler's combinational bypass
output, avoiding conflicting direct IBUF/ISERDES clock routing. Original
pin_capt oversampling is retained; the ADC320MHz clock is not substituted.
`tdc-ip.tcl` recreates the original6x16 standard common-clock shift-register FIFO,
not FWFT or an asynchronous FIFO. Final full-design timing uses300MHz even
though the IP's OOC synthesis emits a100MHz/default-clock warning.

Pins and300MHz result-clock/input-delay constraints come from the pinned PM XDC.
For a few pairs, original XDC specifies P only; Vivado assigns its physical N
mate. The routed audit verifies every differential N pin has a package location.
It also verifies all36 serial bit-counter flip-flops initialize to zero and I2C
pads are strictly inputs. The original serial counter has no HDL reset: physical
power-up INIT is verified, not an independently resettable receiver contract.

## Control, CDC and memory map

`Registers(..., tdc=window)` enables ABI0x00010002 and feature bit4. Existing
ADC/I2C addresses are preserved. Addresses below are32-bit WORD addresses.

| Address | Access | Meaning |
| --- | --- | --- |
| 0x200 | W | 1=ARM,2=STOP; other values ERR |
| 0x201 | R | bit0 valid,1 busy,2 started,3 arm-ready,4 frontend-ready,5 sticky fault |
| 0x202 | R | completion generation; only use with valid |
| 0x203 | R | depth4096 |
| 0x204 | R | channels12 |
| 0x205 | R | bits0..2 PLL locks,3..5 autophase,6..8 result-clock alive,9..11 ready |
| 0x220..0x22b | R | frozen per-channel counts; zero unless valid |
| 0x20000..0x2bfff | R | channel0..11, stride0x1000; one raw record per word |

ARM/STOP are one-sys-cycle pulses. ARM requires idle/ready frontend; busy ARM
returns ERR. A three-stage epoch handshake reaches each source clock. Wait
STARTED before starting an external sequencer. ARM is not a simultaneous physical
trigger across channels; a common stimulus after STARTED establishes alignment.
Each bank independently freezes after4096 events. STOP requires STARTED and
freezes partial or empty banks; source acknowledgements must all complete.

Frozen count transfer is a stable mailbox: source counts remain held, count CDC
uses two stages, completion acknowledgement uses three; counts latch after all
acknowledgements. BRAM reads are synchronous. Unwritten indices, active/invalid
or faulted banks return IPbus ERR. Records after a bank is full are outside this
capture; this is not an overflow counter for the original receiver FIFO.

A40million-sys-cycle watchdog (1s at40MHz) and loss of frontend readiness set a
sticky fault. Fault masks data/counts and rejects commands even if a source
later completes. Recovery requires a coordinated FPGA reset/reload, not a
software flag clear or independent source-domain reset. Board frontend combines
MMCM lock, original autophase completion and divided-clock activity monitoring.

## Build and use

Existing workspace Migen/LiteX/LiteEth/LiteICLink checkouts and shared Vivado are
used, with no package downloads. The isolated combined build is generated under
`generated/board`; the qualified legacy ADC source/build is not overwritten.

```
./build_board.sh
```

Output: `generated/board/build/pm12_ipbus_adc.bit`, checkpoints, reports and
`qualification.json` with build/source hashes. Build fails on negative setup or
hold slack. The additional routed audit checks startup INIT and input ownership.

Native IPbus endpoint192.168.2.240:50001. Both leases are taken by each hardware
script, in order: Atmel-ICE J41800043065 and PM12 Digilent210249A73E43.
`tools/qualify_board.py --out /absolute/evidence/directory` is the initial
volatile-load/smoke-test runner: it requires known legacy build882901f6, preserves
frozen ADC/I2C observations on disk and restores the golden ADC image on failure.
It starts a private hw_server filtered to PM12 and never reuses the Genesys
server. `tools/check_retained.py /absolute/evidence/directory` repeats acquisition
and boundary checks on the currently installed combined image without programming.

With the CFD source connected and running, acquire a bounded event window:

```
python3 tools/acquire.py --acquire --duration 0.2 --out /absolute/path/tdc-run
```

`ARM_STARTED` marks readiness for an external controller. The script stops partial
banks before the1s watchdog. Omit `--acquire` to download the current frozen banks.
Output is12 little-endianu16 files of the reported lengths plus `summary.json`.
Empty banks produce empty files; they are not zero-filled synthetic events.
No calibrated nanosecond conversion is applied.

## Offline tests

```
/srv/codex-hil-data/artiq-zynqmp/venv/bin/python run_tests.py --ghdl /home/codex-hil/coolrunner2-recovery/tools/ghdl
python3 tools/test_client_tdc.py
```

Buffer simulation uses three asynchronous result clocks: full/partial/empty
captures, freeze, rearm rejection and repeated identical raw values. IPbus tests
use the actual legacy register FSM, continuous-strobe bursts,12 banks, bounds,
missing clocks, timeout and readiness loss/relock. The existing ADC/I2C regression
also passes. `validation.json` records the exact test commands/source hashes.
The portable serial-only receiver test covers128 fine codes, commit/ready timing
and raw lock; coarse capture/FIFO are STUBBED and zero startup counter state is
explicitly modeled. Full receiver/clock/FIFO simulation is not claimed.
