# Current attachment changed20November2026 — board2

MCU diagnostic application, copied board1 EEPROM and fuses are verified.
EEPROM serial1803 is now intentionally shared. FPGA DNA is PENDING: the expected
JTAG cable detects no devices. Owner soldered the sensor jumpers: all three INA now respond, LINES07;
three repeated voltage reads per sensor are valid and stable. No new functional measurement campaign
is enrolled. Do not assign new data to the old UID below.

See [provisioning evidence](../mcu/evidence-board2-20261120/README.md).
See [sensor readings after jumper soldering](../mcu/evidence-board2-sensors-20261120/README.md).

Raw setup receipts: `/srv/codex-hil-nvme/pm12-board2-mcu-20261120/`.
Identify FPGA DNA and actual fitting before enrollment or further tests.

The remainder is the frozen previous-board state, retained for reporting.

# Active PM12 — consolidated19November2026

- Board UID **PM12-K7-3A17A1B402212223**, FPGA DNA **3A17A1B402212223**, MCU EEPROM1803.
- Resident SRAM **ff2f746c**; image SHA256
  `28fb5747bafe575455bff8bf91484c8ebb5303ea18d3e0a0925fdb0c4283d0b2`.
- Fitted CFD simulators **3,4,5,6**, both external DAC USB inputs on **6**.
- Fresh TDC discovery: slot7 RJ45 ports0/1/2/3→PM6/5/4/3;
  phase lanes8–15 in pairs follow that mapping. Individual moved fixture factory IDs unread.
- Final analog state: fitted3–6 amps/bypass/monitor outputs inhibited; I2C muxes0;
  external DAC0/1=1/1V and2/3=1.024/2.048V; exercised DAC-A codes restored0.
  Kasli slot6 HDMI/SPI remains driven; slot7 receiver configuration retained;
  CFD generation disabled. No power/PLL/Flash/CPLD changes in consolidation.

The89case dossier and offline report inputs are the current reporting source of
truth. It combines labelled historical epochs with fresh identity-guarded final
checks. Do not use older chronological README prefixes as a current status matrix.
Original sealed campaigns and failed attempts are preserved and were not rewritten.

Coverage: ADC A/B, sampled adjacent data-bit states, integrators, TDC, gate phase,
CFD monitors and internal DAC B/C/D for all12channels; board JTAG, MCU/SPI,
I2C, Ethernet/bridge and finite HDMI checks. Integrators1/2/3/4/6 are explicitly
labelled diagnostic functional methods rather than retroactive old-contract approval.
ADC2 uses a separately versioned STR-edge sampling window.

Fresh consolidation checks: correct UID before/after, MCU/SPI/sensors PASS,
393216transport bytes compared,12/12HDMI signatures with0clock-loss triggers,
PM6 independent returns PASS, TDC4-channel repeat PASS and all four phase-code
returns exact after1ssettling. The0.1sphase-return failure is engineering history,
not deleted. All12selected ADC raw sweeps were independently decoded again.

Metadata omissions: complete module photography and unread tester/fixture factory
IDs. Scope exclusions: supply fault injection/EN-to-PG timeout protection test,
traceable analog calibration, absolute jitter and network throughput/BER.

See [reporting handoff](REPORTING_HANDOFF.md) for exact package locations,
checksums and offline commands. For another board use
[the identity-bound workflow](PRODUCTION_WORKFLOW.md); never reuse this board's
UID or mutable station snapshot as proof of a new board's identity.
