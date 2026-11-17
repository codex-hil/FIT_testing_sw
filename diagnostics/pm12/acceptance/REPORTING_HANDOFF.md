# PM12 reporting thread handoff — 2026-11-17

## Assignment and boundary

The owner requested separating report production from hardware testing because
the accumulated report mixes successive attempts, diagnostics and acceptance
results. The hardware thread continues measurements and publishes evidence.
The reporting thread works offline and builds the board dossier from that evidence.

Do not use JTAG, UART, IPbus, SCPI, power controls or instrument leases in the
reporting thread. Do not change native acquisitions, selected result IDs,
contracts, fitting declarations or sealed receipts to make a report pass.
Request additional measurements from the hardware thread when evidence is missing.

Use an isolated worktree/output directory on the mounted NVMe, preferably under
`/srv/codex-hil-nvme/pm12-reporting/`. The acquisition checkout has frozen source
contracts: editing its scan/decoder/driver files can invalidate later comparisons.
The starting repository commit is `79570d6`, branch
`pm12-integrator-scan-20261113` in `/home/codex-hil/fit-testing-publish`.
Publication is through https://github.com/alice-fit-fee-upgrade/FIT_testing_sw/pull/4
(fork remote `publish`: `codex-hil/FIT_testing_sw`). Coordinate future changes
through commits and evidence manifests, not assumed shared conversation history.

## What needs changing in the report

The current 107-page PDF is a retained working dossier, assembled by prepending
dated follow-up chapters. It is not a clean final acceptance report. Preserve it;
build the replacement in a separate output directory.

Organize the replacement by test and physical channel, with one current coverage
matrix and one equipment/connections table. Group comparable channel curves on
shared axes. Put superseded attempts, reboot interruptions, cable investigations,
fixture repairs and rejected analyses in a separate engineering dossier, outside
the production report. The owner's production-format requirements below supersede
the earlier suggestion of a diagnostic appendix in that report.
Do not present successive chapter status tables as simultaneous current states.
Keep LaTeX editable and figures reproducible from identified raw inputs. Length
should follow the evidence; do not add pages merely to reach 200 pages.

Each plotted series/result needs board UID, physical PM channel, fixture label,
acquisition timestamp, hardware/source/method version and raw-data provenance.
Different source/clock epochs may be shown together only with explicit labels;
their overlay does not constitute a fresh common-protocol retest.

## Mandatory production report format — owner clarification

Produce a short, factual production acceptance report, not a development journal.
The workflow is: connect the board, automatically acquire its hardware identity,
record the station/configuration, run the defined test sequence, and generate one
report plus its linked machine-readable evidence package.

The PDF contains measured results, acceptance limits and statuses. It contains
no hypotheses, troubleshooting narrative, chronological attempts, conversations,
reboot history or repeated follow-up chapters. Retain those separately for
engineering traceability; exclude them from the production PDF entirely.

Suggested test order / contents:

1. Board identity: hardware UID/DNA, MCU identity and readable factory IDs,
   hardware revision where available, firmware/gateware identifiers, timestamp,
   test-run ID and overall disposition. Mark unread identities explicitly.
2. One tester block diagram and one equipment/connections/configuration table.
3. Continuity/interconnect testing: JTAG/boundary scan and relevant chip-to-chip
   connections, with checked coverage and exception counts.
4. Communication interfaces: CPU–FPGA and applicable SPI, I2C, Ethernet/IPbus,
   HDMI/LVDS and other implemented links, each with measured checks/status.
5. Power, voltage/current/temperature sensors and monitoring muxes.
6. ADC, DAC, integrator, TDC and phase-shifter characterization.
7. All fitted relays/switching/control outputs and other production checks
   actually present on the board/fixture; enumerate them from the design/test
   specification. Do not assume a relay exists or was tested from this checklist.
8. One compact final coverage/disposition table and evidence-package reference.

Voltage presentation is specifically **one page**, not a sequence of spread
plots. Use one matrix with physical channels1–12 down the rows and monitored
rails/nodes across the columns, e.g. +5.5V, negative rail with its actual nominal
label, +3.3V and the other applicable signals. Show units and acceptance ranges
once in headers/legend; show values and any exception status in the cells.
Include corrected node voltages after known dividers, not unexplained raw mux
voltages. A board-wide rail measured only once belongs in a separate small
board-wide table, not copied into12 independently measured channel cells.
Use equivalent compact matrices for currents/temperatures when applicable.

Characterization plots should normally combine the12 comparable channels on
shared axes. Use compact numerical tables for offset/gain/noise, ranges,
linearity/monotonicity, timing response and applicable limits. Add plots only
when they convey information the table does not. Do not print each raw capture,
individual voltage distribution, channel or scan attempt on its own page.
Detailed raw buffers, histograms, per-point readings and optional detailed
figures remain in the evidence package, referenced by run ID/hash.

Report missing coverage as NOT TESTED and an unfinished/ambiguous analysis as
INCOMPLETE (or the project's equivalent controlled status), without speculating
about its cause. Separate these from a measured FAIL. Missing required tests
prevent a whole-board PASS/release. Include a concise factual reason, such as
"insufficient valid samples for balance estimate", rather than a fault hypothesis.

Keep the English LaTeX template editable, with stable section names and data
tables generated from the selected receipts for this identified board/test run.
Do not silently combine incompatible versions or present old measurements as
newly acquired. Historical validated evidence, when used, needs a compact source
date/configuration field, not a retelling of its acquisition history.

## Board and bench

- Board UID: `PM12-K7-3A17A1B402212223`; raw FPGA DNA `3A17A1B402212223`.
- MCU EEPROM serial: `1803` (secondary, mutable identification).
- Current FPGA diagnostic build: `ff2f746c`; SRAM bit SHA-256
  `28fb5747bafe575455bff8bf91484c8ebb5303ea18d3e0a0925fdb0c4283d0b2`.
- Original MCU/CPLD/flash/PLL configurations were retained. SRAM restoration
  occurred after power cycles; distinguish these acquisition epochs.
- Shared reference: nominal LHC 40.0787 MHz. Multiplication x3 is **inside the
  external generator**, not a separate box. ADC nominal 80.1574 MS/s; Kasli
  reference x3 and serializer/deserializer x8, giving 24 slots per LHC period.
- PM HDMI passes through the LVDS–HDMI adapter to DIO-LVDS slot6 on Kasli.
  CFD simulator RJ45 cables use slot7. Preserve the existing parameterized
  connection diagram and consolidate its descriptions into a table.
- MOD-DAC-28 DAC0/1 feed CFD J8, direct ADC; DAC2/3 feed J6, integrator.
  FIT software limits each external DAC output to 0–3.3 V.
- Shared monitor voltmeter is **Keysight B2910BL MY63320299**, current source
  0 A, output enabled only during voltage measurements, **local Force HI/LO**.
  Sense terminals are not the current connection. Final recorded SMU state
  was OFF/HIZ, auto-on disabled. Later ADC-only tests did not access the SMU.
- CFD01–CFD04 are provisional fixture labels by retained RJ45 port, not factory
  serial numbers. Do not invent missing instrument/fixture IDs or photographs.

Current fitting: physical channels1–4, slot7 ports0/1/2/3 → PM4/3/2/1,
fixtures CFD01/02/03/04 respectively. Both USB are on3 after owner confirmation.
Final recorded state: all fitted amps, direct bypass and monitor muxes inhibited,
TCA masks0; external DAC01=1/1 V, DAC23=1.024/2.048 V. Kasli slot6 HDMI SPI
remains driven. Reporting must never change this hardware state.

## Evidence locations and qualification scope

Private native campaign roots under
`/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/`:

| Root | Use |
|---|---|
| `four-cfd-20261113` | Earlier9–12 cohort, ADC/integrators10–12 and other historical tests |
| `four-cfd-clock40-20261116` | ADC/integrator9; separately dated follow-ups |
| `four-cfd-clock40-20261117` | Current5–8 and1–4 fittings, subsequent analog moves and repeat6 |

Read `campaign.json`, immutable `results/*/record.json`, raw receipts and
manifests. The selected cases in one root alone are **not** the complete
cross-epoch board coverage: do not turn older valid9–12 data into missing
measurements merely because they are absent from the newest root.

Current measured coverage:

| Test | Coverage / limitation |
|---|---|
| ADC transfer and adjacent bits | PASS on3–12;1–2 await USB moves |
| Integrator full signed/fine/return protocol | PASS on5,7–12; INCOMPLETE on3,4,6;1–2 pending |
| TDC | Qualified1–8 in current campaign; historical9–12 use corrected-clock data below |
| DAC-A/gate phase |1–12, with historical9–12 epoch explicitly identified |
| Eight CFD monitor inputs and internal B/C/D |1–12 cohorts; preserve fixture-repair chronology |
| Board-wide JTAG/CPU–FPGA/etc. | Existing historical evidence has its own epoch; do not invent a fresh retest |

Corrected-clock historical TDC9–12 raw source:
`/srv/codex-hil-nvme/pm12-tdc-clock40-20261114/hardware/tdc/status.json`
(c7531465 acquisition). Withdrawn c7 TDC clock qualification is not valid
replacement evidence. Historical ADC10–12 uses c7c42d28; newer analog uses
ff2f746c, with separate source contracts retained.

CFD02 previously lacked a 33 kohm R3 supply-divider resistor while fitted at11.
Repair verification is in `evidence-cfd11-r3-repair-20261117`. This was a fixture
repair; do not describe it as a permanent defect of physical PM channel11.
The fixture subsequently moved with its retained port order.

Repository evidence is under `diagnostics/pm12/acceptance/evidence-*`.
Useful recent entry points:

- `evidence-group05-08-20261117/README.md`
- `evidence-channel05-20261117/README.md`
- `evidence-ch06-reseat-20261117/README.md`
- `evidence-group01-04-20261117/README.md`
- `evidence-usb03-route-20261117/README.md`
- `evidence-channel03-20261117/README.md`

Initial channel8 swapped-USB scans, channel4 no-response probes before reboot,
the interrupted group1–4 monitor acquisition and channel3 probes before the
actual cable move are diagnostics, excluded from qualified analog results.
They must not be interpreted as demonstrated ADC defects.

## Integrator interpretation — important correction

INCOMPLETE does **not** establish inability of the physical integrator to balance.
The existing algorithm has no measured gate-phase tag. It chooses the highest
adjacent pair among four phase means and requires the best pair score to exceed
the runner-up by30 ADC codes. A waveform failing that heuristic is rejected.

For channel3, coarse13 and fine26 acquisitions completed. Independent reanalysis
of the raw fine buffers retained26/26 points on A and1/26 on B;100/104 B buffers
were rejected as ambiguous. A has a tentative fine crossing near3.950 mV, but
independent return controls did not run because B stopped the controller.
Do not label A as having completed the whole qualification either.

Detailed evidence and exact analysis/decoder sources:
`evidence-channel03-20261117/integrator-diagnostic-validation.json` and
`diagnostic-analysis-sources/`. Channels4/6 have their own incomplete attempts;
pressing fixture6 did not remove its observed ambiguity.

The owner suggested integrator sensitivity and finer voltage steps. The present
fine step is0.4 mV differential (each DAC leg moves0.2 mV in opposite directions).
DAC80508 is16-bit over nominal0–5 V: about76.3 microvolt per code. Existing FIT
client formatting and scan rounding use100 microvolt per output. A one-leg
100 microvolt scan, or a genuine single-code scan after a separate control
revision, has been **proposed, not performed**. Do not describe those as measured.
Neither refine the threshold nor change old PASS/INCOMPLETE labels silently.
Alternative phase tagging/minimum-variation analysis belongs to a separately
versioned hardware/analysis task, with its validation stated explicitly.

## Archives, tools and publication

For current native data reconstruction in a NEW directory:

1. Extract `evidence-group05-08-20261117/campaign-raw.tar.gz`.
2. Concatenate the three `evidence-group01-04-20261117/group14-delta.tar.gz.part*`
   files in numeric order, verify `archive-parts.json`, then overlay that delta.
3. Overlay `evidence-channel03-20261117/channel03-delta.tar.gz`.

The channel3 delta extends the group14 snapshot; it is not another standalone
delta against the original base. Parent inventories, hashes and reconstruction
validation accompany the archives. Never extract over live acquisition roots.
For older9–12 cohorts use their own dated archives and manifests.

- Offline scientific Python:
  `/srv/codex-hil-nvme/tool-venvs/fit-measurements/bin/python`.
- TeX: `/srv/codex-hil-nvme/pm12-acceptance-20261107/toolchain/tectonic`.
- Existing generic tools: `campaign_report.py`, `campaign_adapters.py`,
  timing/monitor/SMU adapters and `compare_adc_zero_inputs.py` in this directory.
- Existing working dossier:
  `evidence-campaign-assembly-20261113/report.tex` and `report.pdf` (107pages).
  Use this as retained input/reference; do not append more chronological chapters
  when constructing the replacement report.
- Current readback-verified SMB PDF:
  `\\192.168.2.6\codex-hil\ALICE\PM12-test-reports\PM12-K7-3A17A1B402212223\PM12-report-107pages.pdf`.
  The older `latest` alias could not be replaced. Use dated/versioned filenames
  and confirm the PDF hash; do not assume that alias is current.
- SMB credentials remain private in the existing local configuration; never put
  them in this handoff, repository, PDF or transfer manifest.

## Communication contract between threads

Hardware thread supplies a concise measurement receipt: board/channel/fixture,
method/source version, timestamp, raw location and hashes, validation result and
limitations, selected/superseded status, and final bench state. It publishes
evidence commits; it no longer rebuilds the whole dossier after every cable move.

Reporting thread consumes a specified evidence commit/snapshot, records a list
of included receipts, generates figures and LaTeX offline, and publishes its own
reviewable commits/output. Questions about missing or inconsistent evidence go
back to the hardware thread. Do not resolve them by relabeling channels, changing
hardware settings or treating diagnostic data as qualification.

Next hardware step is USB move to2; analog1–2 remains unmeasured. New measurement
receipts should be incorporated by the reporting thread without duplicating the
entire test narrative in the final report.
