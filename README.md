# FIT Testing Software — PM12

Functional assembly testing of FIT PM12 boards using JTAG, the MCU console,
IPbus, Kasli-DIOT/DIO-LVDS, CFD simulators, MOD-DAC-28 and a guarded SMU voltmeter.
The current tester uses dedicated Kasli gateware; ARTIQ is not required.

Start with [the production workflow](diagnostics/pm12/acceptance/PRODUCTION_WORKFLOW.md).
Use the identity-guarded session entry points there, rather than invoking archived
hardware experiments directly. Every newly attached board must be enrolled from
its FPGA DNA. Cable IDs, IP addresses and mutable MCU serials are not board UIDs.

- [Handoff for the next hardware-testing thread](diagnostics/pm12/acceptance/TESTING_HANDOFF.md)
- [Current board, fitting and data package](diagnostics/pm12/acceptance/ACTIVE_CAMPAIGN.md)
- [Frozen data index and verified SMB archive](diagnostics/pm12/acceptance/evidence-production-data-20261119/README.md)
- [Offline reporting handoff](diagnostics/pm12/acceptance/REPORTING_HANDOFF.md)
- [Declarative bench diagram](diagnostics/pm12/acceptance/bench_setup.json)
- [Measurement method/source history](diagnostics/pm12/acceptance/README.md)

`board_session.py` binds sessions and analog acquisitions to live hardware identity.
`fixture_batch.py` discovers actual CFD port mapping and runs TDC/phase or guarded
shared-monitor/DAC batches. `board_check.py` runs final MCU/I2C/transport/HDMI checks.
`dossier.py` builds and verifies a portable, offline evidence package from explicit
case selections. No routine runner programs CPLDs or silently changes clock profiles.

The current board UID is **PM12-K7-3A17A1B402212223**. Its dossier selects89functional
cases across retained measurement epochs. New diagnostic methods are labelled;
older sealed campaign approvals are not rewritten. Photographs and unread tester
factory IDs remain explicit metadata omissions, not invented identities.
