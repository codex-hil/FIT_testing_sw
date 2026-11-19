# PM12 identity-bound production workflow

For a new hardware-testing thread, read [the operational handoff](TESTING_HANDOFF.md).
It documents the acquisition/report contract and remaining normalization work.

## Boundaries

Use these entry points for a newly connected board. Archived scripts are source
provenance and low-level adapters, not safe board-selection interfaces. Production
measurements never program CPLDs, try2MHz fallbacks, reset the MCU, or write Flash.
The old `station.py integrated` entry is disabled because its cleanup releases
shared Kasli outputs. Slot6 HDMI/SPI must stay driven; timing batches only service
slot7 and explicitly stop the CFD transmitter.

One DUT at a time uses the diagnostic's static PM IP/MAC. Do not connect two copies
at192.168.2.240. Verify identity through the specified physical JTAG/UART attachments,
not an old IP, ttyUSB number, mutable EEPROM serial or Digilent cable serial alone.

Hardware prerequisites: PM12-compatible FPGA/CPLD gateware, working MCU diagnostic
console, PGOOD, shared LHC clock and the established Kasli bridge. Setup/programming
is a separate operation; no test silently repairs readiness or changes PLL profiles.
Heavy compilation stays on Dell; these operations are local hardware access only.

## Enroll each newly attached board

Use the hardware Python on Optiplex, and an unbound template:

```
PY=/home/codex-hil/kasli-diot-bringup/.venv/bin/python
A=diagnostics/pm12/acceptance
ROOT=/srv/codex-hil-nvme/pm12-board-sessions
$PY $A/board_session.py enroll \
  --station $A/profiles/optiplex-session.example.json --root "$ROOT" \
  --registry /srv/codex-hil-nvme/pm12-board-registry.json
```

Enrollment reads FPGA DNA and the MCU serial under shared hardware leases; it
works before the IPbus diagnostic is ready. It replaces old board identity and
clears inherited fitting/USB/phase-lane/SMU connection declarations. It does not
program IDs, switch board power or configure an FPGA. Preserve its actual receipt.

If FPGA SRAM is empty, explicitly load the reviewed image using the enrolled
configuration. For the current clock40 family the known artifact is
`/srv/codex-hil-nvme/pm12-rx-clock-counter-20261115/candidate-v2/pm12_ipbus_adc.bit`,
SHA256 `28fb5747bafe575455bff8bf91484c8ebb5303ea18d3e0a0925fdb0c4283d0b2`.
The generic `board_session.py load-sram --station ENROLLED --root ROOT --bit BIT
--sha256 HASH` checks physical DNA/MCU and the bitstream hash before volatile
configuration, then checks the expected live image. No Flash/CPLD/MCU programming.
This wrapper uses the previously physically validated loader; the new generic
wrapper's wrong-hash gate is software-tested, not a separate new hardware reload.

Edit the enrolled configuration to reflect the actual fitting and cables:
`fitted_channels`, `stimulated_channel`, and per-channel `analog_connected`,
`integrator_connected`, `dac_channels`, `integrator_dac_channels`. Do not inherit
fixture identities or phase-lane mappings without discovery. For SMU batches also
require `shared_monitors_connected=true`, `smu_sense="local-force-0A"`, and explicit
`smu_host`/`smu_serial`. All fitted shared monitor muxes are inhibited before selection.
Do not claim a route is measured merely because it has been declared.

Begin an immutable configuration snapshot:

```
$PY $A/board_session.py begin --station ENROLLED_CONFIG --root "$ROOT"
```

The returned path is `ROOT/BOARD_UID/UTC-unique-session`. `begin` checks live DNA,
MCU, PGOOD, expected FPGA build and monotonic SYS during identification. Different
boards and different fittings require their own enrollment/configuration/session.
Changing a session's station file invalidates its hash rather than modifying history.
Live identities also bind the network endpoint to JTAG using a random register-read
challenge (the supported bus counts4STROBE cycles/read). MCU/UART is tied to the
same endpoint by32walking scratch patterns plus restoration, observed as33writes.
Thus a matching software build or stale IP alone cannot bind a second board.

## Measurements

All commands below require the returned `--session SESSION`. They acquire shared
leases, check physical identity before and after, preserve errors/raw data, and
write a measurement manifest. Wrong preflight identity never executes stimulation
or cleanup against the unexpected board. No old result directory is overwritten.

- ADC: `board_session.py measure --session SESSION --kind adc --channel N
  --phase-code CODE --sample-window WINDOW --points 257`.
- Integrator acquisition: `board_session.py measure --session SESSION --kind
  integrator --channel N --phase-code CODE --sample-window WINDOW
  --pairs P:N P:N ...`. Voltages are constrained to0..3.3V. Base1.024/2.048V;
  use100µV single-leg steps for fine balance. Acquire a coarse bracket, fine scan,
  freeze the model, then independent candidate returns and±5mV controls.
  `cfd_simulator/analyze_reset_reference.py` verifies common board identity of its
  inputs, strict raw decoding and reset-reference alignment. Explicit uncertainty
  remains ERROR/INCOMPLETE; narrow and repeat a justified scan, never relax guards.
- TDC and phase: `fixture_batch.py --session SESSION --kind timing`.
  Four16-pulse discovery captures establish the actual RJ45→PM mapping before
  quiet/count/25phase TDC tests and DAC-A phase scans. Only declared fitted
  physical channels are accepted. Default phase settling is1s; default100intervals.
- Phase-only repeat with fresh discovery: `fixture_batch.py --session SESSION
  --kind phase --phase-intervals 100 --settle 1`.
- Shared monitors: `fixture_batch.py --session SESSION --kind monitors`.
- Internal DAC B/C/D: `fixture_batch.py --session SESSION --kind dacs`.
  SMU uses verified0A/local Force sensing; its source is disabled at cleanup.
  Never enable multiple CFD monitor outputs on the shared wire.
- Final common check: `board_check.py --session SESSION --repeats 12`.
  MCU/SPI/sensors,393216bytes of compared frozen ADC transport, finite HDMI
  signatures and frozen clock-monitor windows. No global Kasli stop/direction cleanup.

Run the commands through `$PY $A/...`. Some native adapters retain historical
station paths/defaults; the guarded entry points explicitly pass serial/build/route
parameters. New SMU serial/endpoint plumbing is software-validated against existing
native procedures; no new SMU acquisition was needed during the final consolidation.

Phase/window settings must be measured for the board/channel. The current board's
ADC2 full scan required `str-rise`/32768; its integrators3/4/6 used `before-str`/0.
These are starting settings for another board, not an automatic acceptance guarantee.
Both decode modes still require consecutive equal data samples and valid STR/tags.

## Integrity, selection and report separation

```
python3 $A/board_session.py verify --session SESSION
python3 $A/dossier.py build --selection EXPLICIT_SELECTION.json --out NEW_DOSSIER
python3 $A/dossier.py verify --root DOSSIER
python3 $A/dossier.py export --root DOSSIER --out NEW_REPORT_INPUTS
python3 $A/dossier.py extract --root DOSSIER --case adc-lines:2 --out NEW_CASE_DIR
```

Session integrity does not promote COMPLETE to numerical manufacturing acceptance.
The dossier requires every declared case, matching UID/channel/status, referenced
sources and original summaries, and hashes all files. Content-addressed blobs deduplicate
sources/raw data while keeping full case file maps. Extraction/verification is offline.
Keep ERROR/INCOMPLETE records, source snapshots, method versions and clock epochs.
Use explicit selections; never aggregate every file named latest or infer a new
board from the previous board's `active.json`.

A manufacturing tolerance is distinct from demonstrated functional behavior.
Supply fault injection, calibrated analog accuracy, absolute jitter and Ethernet
throughput/BER are outside the current functional scope unless explicitly measured.
Writing the production report belongs in the offline reporting thread.
