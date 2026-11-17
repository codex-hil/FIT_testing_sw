# Standard reset procedure, end-to-end hardware repeat — 2026-11-17

The unmodified standard orchestrator ran on identified PM2/J6, first A then B,
with fresh DNA/MCU enrollment, channel-bound programming vectors, normal controls,
22 input sweep points per held bank, raw validation, campaign registration and
matched-channel CSV/scatter generation. All324 buffers independently validate.
Both CPLD restorations match all984 pre-programming rows. The selected receipt
is result-4816bb98fca8436db06fb8f926e41a9e, case integrator-reset:2, in the new
reset-standard-20261117 campaign. The existing full-board campaign and selected
historical qualifications were not modified. Other11 channels in this new
protocol remain unmeasured; this is not full-board acceptance.

|Integrator|Nominal R P (ohm)|Nominal R N (ohm)|Normal four-phase amplitude (code)|
|---|---:|---:|---:|
|A|76.59|141.68|204.69|
|B|68.64|137.97|106.71|

Amplitudes are the same bank's normal-gate control immediately before its reset
experiment, at DAC2/3=1.024/2.048V, phase DAC32768. They include reset and
integration, not an isolated calibrated pulse height. Estimates remain conditional
on430-ohm input resistance,2000ADC codes/V and commanded DAC voltage changes.
The earlier standalone trials gave A77.09/141.79 and B68.54/137.19ohm. This
repeat is consistent with those values. Similar A/B resistance estimates coexist
with almost twofold different waveform amplitudes; one channel does not establish
or exclude a multi-channel correlation or identify the cause.

Both normal images restored/verified; final phase0, externalDAC23=1.024/2.048V,
selected amps/bypass/monitor inhibited, TCA0, leases released. No FPGA/MCU/PLL
programming or Kasli direction changes. PASS means complete characterization and
validated restoration, not numerical R_ON tolerance acceptance.

During preflight a variable-name collision in the generalized plotting script
was corrected: capture-bank iteration could overwrite the selected reset bank.
An offline archived-buffer replay regression now tests both selections. All26
campaign software tests pass. The standalone experiment analyses were unaffected.

raw-standard-run.tar.gz contains the acquisition/analysis source snapshots,
channel vectors, all raw buffers/readbacks and control/SCPI/UART records, immutable
normalized receipt, fresh identity and campaign protocol/registration. Temporary
Vivado extraction caches are excluded. Every archived file was read back and
SHA-256 checked against raw-manifest.json. The correlation CSV retains12 rows
with missing measurements explicit; plots contain the single measured channel
and do not infer a correlation coefficient. No production PDF was rebuilt.
