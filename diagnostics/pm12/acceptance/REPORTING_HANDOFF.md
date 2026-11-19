# Offline reporting handoff — consolidated19November2026

## Task boundary

Write the production report from the frozen board dossier. Do not use JTAG, UART,
IPbus, SCPI, power controls or hardware leases in the reporting thread. Do not run
archived acquisition scripts. The board may already have been replaced by another
DUT. Verification, export and extraction with `dossier.py` are strictly offline.

Repository: `codex-hil/FIT_testing_sw`, branch `pm12-integrator-scan-20261113`;
upstream review https://github.com/alice-fit-fee-upgrade/FIT_testing_sw/pull/4 .
Read the publication commit/package manifest, not old conversation state or old
chronological README prefixes. The mutable `pm12-campaigns/active.json` is an
operator hint, never the report's data selector.

## Board and package

Board UID **PM12-K7-3A17A1B402212223**, FPGA DNA **3A17A1B402212223**,
secondary MCU EEPROM serial1803. Fresh identity, endpoint linkage, firmware IDs,
setup declarations and final-state records are in the package. Physical board
revision/CPU factory ID and unread tester IDs must remain unread, not inferred.

Primary local package/archive: `/srv/codex-hil-nvme/pm12-consolidation-20261119/`.
Archive name:
`PM12-K7-3A17A1B402212223-production-data-20261119-v1.tar.gz`.
SMB destination:
`\\192.168.2.6\codex-hil\ALICE\PM12-test-reports\PM12-K7-3A17A1B402212223\production-data-20261119-v1\`.
The published `evidence-production-data-20261119/package-manifest.json` records
actual archive SHA256, size and remote readback status. Check it before extraction;
the archive does not contain its own circular checksum. Credentials are not in Git.

Inside the archive:

- `dossier/release.json`: the89explicitly selected cases and their file/blob maps.
- `dossier/blobs/`: full content-addressed sources, raw data/archives, controls and
  analysis inputs. Identical files are deduplicated without losing case paths.
- `report-inputs/measurements.json`: selected normalized receipts/metrics/curves.
- `report-inputs/coverage.csv`: one current test×channel matrix.
- `report-inputs/series.csv`: named, unit-labelled curve points for common overlays.
- `verification/`: original-record integrity, all12ADC raw revalidation, final
  MCU/transport/HDMI clock-window checks, fresh PM6 returns, TDC/phase validation.
- `sessions/`: identity-bound final measurement session and linked identity receipt.
- `equipment.json`, `assets/`: equipment metadata and editable bench diagram/template
  sources. Unavailable photographs/factory IDs are explicit metadata omissions.
- `operator-source/`: the source snapshot for future hardware operations. Do not
  execute it in the reporting thread.
- `engineering/`: failed/superseded attempts and prior chronological notes,
  excluded from the production PDF.

All89functional cases are present:84PASS and5PASS_FUNCTIONAL diagnostic imports.
This is a complete functional measurement dataset, not a claim of traceable analog
calibration, absolute jitter, supply-fault protection testing or network throughput/BER.
The dossier may retain REVIEW disposition for missing photography/unread metadata.
That is distinct from a missing functional measurement.

## Offline commands

From the checkout, after verifying/extracting the archive into NEW_OUTPUT:

```
python3 diagnostics/pm12/acceptance/dossier.py verify --root NEW_OUTPUT/dossier
python3 diagnostics/pm12/acceptance/dossier.py export --root NEW_OUTPUT/dossier --out NEW_EXPORT
python3 diagnostics/pm12/acceptance/dossier.py extract --root NEW_OUTPUT/dossier \
  --case adc-lines:2 --out NEW_ADC2_CASE
```

Case receipts reference original source/clock/method epochs. Use the named current
case selections; do not choose files by modification time or merge every PASS found.
Never promote an ERROR/INCOMPLETE source or rewrite historical sealed campaigns.
The newly adopted diagnostic functional results do not retroactively change their
older campaign contracts. Different methods may share axes only with clear labels.

The matrix includes all12channels for ADC A/B transfer, sampled12bit/11adjacent-pair
exercise, integrators A/B, TDC, gate-phase response, CFD monitors and DAC B/C/D.
Board cases cover static JTAG links, MCU/SPI, I2C rails, Ethernet/bridge and finite HDMI.
JTAG coverage is168links/338vectors per retained path, not every board net.
ADC2 uses STR-edge decoding/phase32768; integrators1/3/4/6 use reset-reference
fine balance, integrator2 uses the separately documented single-leg/common-translation
method. Preserve scope differences and independent return criteria.

Fresh final checks include393216compared transport bytes and12/12correct HDMI
replies with0SYS-loss triggers and independently reconstructed clock windows.
All12selected ADC sweeps were raw-decoded again. Additional TDC3–6 and phase3–6
controls validate the new guarded entry points; use full retained101point phase
curves for characterization rather than replacing them with the11point control sweep.
The0.1sphase-return failure and1ssettled repeat are engineering history, not narrative
for the production PDF. Use1ssettling in the stated current procedure.

## Production PDF format

Create a short, factual, editable LaTeX report. No hypotheses, debugging diary,
reboot history, failed-attempt chapters or repeated follow-up introductions.
Keep engineering history outside the PDF. Preserve the older107page working
report; do not prepend another chapter to it or overwrite it.

Use one board identity/configuration section, one block diagram and one equipment/
connections table. The LHC40.0787MHz and its3×output originate INSIDE the generator.
MOD-DAC-28→CFD simulator; CFD RJ45→DIO-LVDS→Kasli. PM HDMI→LVDS/HDMI adapter,
with LHC clock injection and two RJ45 links through another DIO-LVDS to Kasli.
Show Kasli's PM SFP bridge separately from the normal LAN port.

Group comparable12channel series on common plots. Voltage monitoring is ONE
matrix page: physical channels1–12 down the rows, corrected monitored rail voltages
across columns, with limits/status. Board INA rails belong to their own compact
table. Keep raw divider readings available but show corrected signed voltages.

Follow with continuity, communications/sensors/power observations, ADC/DAC,
TDC/phase and integrator results. Give measured values, scope/limits and disposition.
Report declared unmeasured items honestly: no EN-to-PG fault injection, calibrated
current/ADC-only INL, intrinsic clock jitter or throughput/BER. Do not invent relays
or claim unlisted switching paths were exercised. Preserve waveform/FFT definitions:
zero-input clock/reset pickup is not automatically random ADC noise or ENOB.

Photographs of every module and some tester/fixture factory IDs are not complete.
Use explicit placeholders/unread labels or obtain them from the owner. Do not use
an unverified camera image as this board's photograph. The hardware UID is established
from the actual FPGA DNA, not from photography, cable serial or the mutable MCU ID.
