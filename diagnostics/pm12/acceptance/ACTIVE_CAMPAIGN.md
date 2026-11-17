Latest setup: CFD1–4, slot7 RJ45 ports0/1/2/3→4/3/2/1; both USB4, DAC01→J8,23→J6.
FPGA ff2f746c SRAM restored after initial not-ready state and again after owner-reported reboot;
MCU/CPLD/flash/PLL unchanged. TDC/phase completed before reboot, monitor/DAC restarted afterwards.
Interrupted/raw no-response attempts retained; no acquisition merged across reboot.
Final SMU OFF/HIZ/0A/auto-on OFF; monitors inhibited/TCA0, internal exercised DACs0000.
Slot6 HDMI SPI stays driven. Kasli outputs/directions preserved; leases released.
Final external DAC01=1/1V,23=1.024/2.048V; all1–4 amps/bypass inhibited.
Integrator4 INCOMPLETE; integrator6 INCOMPLETE. Analog1–3 pending.
Earlier dated setup states below are historical.

Latest fitting1–4 (2026-11-17): TDC/phase/monitor/internal-DAC results in the linked table.
Channel4 ADC/bits: **PASS/PASS**; integrator: **INCOMPLETE**. USB remains4, analog1–3 pending.
Slot7 ports0/1/2/3→PM4/3/2/1 verified. Integrator6 remains INCOMPLETE.
[Group1–4 evidence and common plots](evidence-group01-04-20261117/README.md).

Final after integrator6 repeat: DAC2/3→J6 channel6 confirmed; direct ADC USB route not freshly confirmed.
External DAC0/1=1/1V,2/3=1.024/2.048V. All5–8 amps/bypass/monitor outputs inhibited; TCA masks0.
Kasli outputs/directions unchanged, leases released. No programming/PLL changes or SMU access.
Latest integrator6 selected INCOMPLETE; previous attempts retained. Earlier dated states below historical.

Latest channel6 integrator repeat after pressing CFD board (2026-11-17): **INCOMPLETE**.
Fresh13-point coarse sweep reproduces the bankB template ambiguity; fine/returns did not run.
No change to thresholds. Pressing did not remove the symptom; no hardware fault established.
ADC5–12 and integrators5,7–12 retain PASS; previous incomplete and diagnostics preserved.
[Repeat raw data and before/after comparison](evidence-ch06-reseat-20261117/README.md).

Final channel5 settings: DAC0/1=1.0000/1.0000V,2/3=1.0268/2.0452V;5 amplifiers enabled, ADC bypass isolated.
All four monitor muxes inhibited/TCA0; other fitted channels isolated at preflight.
Kasli outputs/directions unchanged; leases released. No programming or clock changes.
SMU not accessed; preceding recorded state OFF/HIZ/0A/auto-on OFF.
Earlier dated states below are historical.

Latest channel5 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
and integrator balance/sign/revisits **PASS**, matching the frozen channel8 contracts.
Both USB now5: DAC0/1→J8 ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
ADC5–12 complete; integrator5 and7–12 PASS,6 remains INCOMPLETE.
[Channel5 raw data and common plots](evidence-channel05-20261117/README.md).

Final channel6 settings: DAC0/1=1.0000/1.0000V,2/3=1.0240/2.0480V;6 amplifiers disabled, ADC bypass isolated.
All four monitor muxes inhibited/TCA0; other fitted channels isolated at preflight.
Kasli outputs/directions unchanged; leases released. No programming or clock changes.
SMU not accessed; preceding recorded state OFF/HIZ/0A/auto-on OFF.
Earlier dated states below are historical.

Latest channel6 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
**PASS** under the frozen channel8 contracts; integrator **INCOMPLETE**.
Both USB now6: DAC0/1→J8 ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
ADC6–12 available; integrator7–12 PASS,6 requires diagnosis;5 awaits USB.
[Channel6 raw data and common plots](evidence-channel06-20261117/README.md).

Current final settings7: DAC0/1=1/1V,2/3=1.0265/2.0455V; channel7 amplifiers enabled,
direct ADC bypass isolated, all four monitor muxes inhibited/TCA0. Channel8 isolated at preflight.
Kasli outputs/directions unchanged, leases released. SMU untouched in this follow-up;
its preceding recorded state is OFF/HIZ/0A/auto-on OFF. No programming or clock changes.
Earlier dated states below are historical.

Latest channel7 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
and integrator balance/sign/revisits **PASS**, matching the frozen channel8 contracts.
Both USB now7: DAC0/1→J8 direct ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
Analog7–12 observations available;5–6 await USB moves. Fitting5–8 timing/monitor/internal-DAC PASS unchanged.
[Channel7 raw data and common plots](evidence-channel07-20261117/README.md).

## Current2026-11-17 — fitting5–8, both USB on8, verified routing

BoardPM12-K7-3A17A1B402212223/MCU1803, qualified SRAM ff2f746c restored and retained.
Slot7 ports0/1/2/3 map to PM8/7/6/5, confirmed by finite TDC discovery.
All four shared monitors connected to Keysight B2910BL MY63320299 Force HI/LO.
**PASS on5,6,7,8: TDC, DAC-A/gate phase, eight monitor voltages, internal DAC B/C/D.**
**PASS on8: ADC A/B transfer/adjacent-bit exercise and integrator balance/sign/returns.**
ADC/integrators5–7 await the next USB moves. Earlier9–12 results remain preserved.

Initial USB pairs were swapped. Active/inhibited bypass probes identified the
routes; the owner corrected them. Selected analog results are all after the fix:
**DAC0/1→J8 direct ADC; DAC2/3→J6 integrator; normal selector map[0,1].**
Temporary map[1,0], lower driver-path gain, insufficient-range and interrupted
wider-range measurements remain diagnostic history, excluded from qualification.
They do not establish a board bank inversion or ADC gain fault.
Selected ADC:257points/bank, Vdiff±1.2V, Vcm1V, outputs0.4..1.6V.
Integrator:13coarse/26fine0.4mV points and independent revisits/±5mV controls.

Final DAC0/1=1/1V,2/3=1.0272/2.0448V;8 amps enabled, direct bypass inhibited,
all four monitor muxes inhibited and both TCA masks0. Final SMU OFF/HIZ/0A,
auto-on OFF. Internal exercised B/C/D and phase DAC-A restored0000.
Kasli slot6 SPI held driven, only slot7 directions serviced. Leases released.
No MCU/CPLD/flash/PLL writes; FPGA load was SRAM only. Active registry:
`/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261117`.
[Raw/normalized group evidence](evidence-group05-08-20261117/README.md),
[88-page cumulative report](evidence-campaign-assembly-20261113/report.pdf).
Earlier wiring/current-image statements below are dated history.

## Current2026-11-17 — CFD11 R3 repair verified

Owner fitted missing R3=33kohm on CFD02/PM11. All eight monitor voltages PASS;
MUX7 raw3.405970/3.406098V, corrected+5.470194/+5.470400V. New current monitor11
result is registered in clock40 revision; original failed data remain historical.
[Repair evidence](evidence-cfd11-r3-repair-20261117/README.md).
MCU1803/power/PRIMARY/PLL healthy; MCU reports FPGA not ready, IPbus unavailable.
The test used MCU/I2C only; no FPGA/MCU/CPLD/clock or DAC writes. All four muxes
inhibited, TCA0/0, SMU OFF/HIZ/0A/auto-on OFF, analog GPIO upper controls preserved.
Kasli outputs untouched. All leases released. Previous resident FPGA build is
historical, not confirmed resident today. USB routing last declared on9 unchanged.

## Current2026-11-16 — analog USB on physical9, group9–12 complete

Owner moved both USB pairs10→9; voltage-response probe confirmed both ADC paths.
ADC A/B257-point transfer and adjacent-bit checks PASS. Integrator balance,
independent revisits and±5mV signed controls PASS. Actual FPGA ff2f746c unchanged;
no programming, PLL profile or SMU changes. USB0/1→J8 direct ADC,2/3→J6 integrator.
All four channels9–12 now have analog functional observations;9 uses the new
clock40 diagnostic revision while10–12 retain their original c7c42d28 data.
Frozen parent source contracts remain unchanged. New registry:
`/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261116`.
Combined plots label the differing hardware versions; no fresh10–12 retest claimed.
[Channel9 raw/normalized evidence](evidence-campaign-ch09-20261116/README.md),
[82-page cumulative report](evidence-campaign-assembly-20261113/report.pdf).

Final0/1=1/1V,2/3=1.0264/2.0456V (shared compromise, not simultaneous A/B zero).
Channel9 amplifiers enabled, direct ADC bypass inhibited, all four monitor muxes
inhibited and both TCA masks0. Other fitted channels isolated at preflight.
Kasli output directions unchanged; all local/remote DAC and board leases released.
Earlier wiring/build/coverage statements below are dated history.

**Current 2026-11-14:** corrected-clock SRAM build `c7531465` retained; TDC9–12 repeat PASS (19,268 events), ADC digital regression all12/both banks PASS. HDMI/SPI SYS restarts persist (8/12 reads). [Evidence](../tdc_live120/evidence-clock40-20261114/README.md). No external PLL profile was changed. Slot6 SPI outputs must remain driven. Historical c7c42d28 results below are not correct-clock qualification.

# Active PM12 campaign — 2026-11-13

Board **PM12-K7-3A17A1B402212223**, MCU1803. Fresh JTAG DNA and MCU identity
were confirmed for the current fitting, `ch09-12-attempt001`.

Live registry on Optiplex NVMe:

`/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-20261113/`

Active pointer: `/srv/codex-hil-nvme/pm12-campaigns/active.json`.
Read the registry for current measurement/selection status. Reports are snapshots.

## Current fitting and wiring

Four emulators are fitted on physical PM channels **9,10,11,12**.
Fresh pulse discovery established this reverse port mapping; every stimulated
port produced16 TDC events only on its expected channel, with quiet controls.

| PM channel | Provisional CFD label | Slot7 RJ45 port | Phase lanes |
|---|---|---|---|
|12|CFD01|0|8/9|
|11|CFD02|1|10/11|
|10|CFD03|2|12/13|
|9|CFD04|3|14/15|

Labels identify bench port assignments, not verified factory serial numbers.
The initial ascending declaration is preserved in `mapping-declared.json`.

Both analog USB cables currently terminate on **channel10 only**, after the owner confirmed the move from11:

| MOD-DAC-28 outputs | CFD_SIM input | Measurement |
|---|---|---|
|0/1|J8, direct ADC|ADC transfer and adjacent-bit exercise|
|2/3|J6, integrator|Balance and signed ramp response|

Next move both cables together to9 only after the owner confirms the move.
Other fitted channels are not implicitly analog-connected. Update that receipt
before acquiring them; never infer the analog destination from an RJ45 route.

## Acquisition order and preservation

1. Confirm fitting/identity, PGOOD and route map. Original CPLD A/B gates remain
   enabled, nominal20MHz; ADC sampling is nominal80MHz.
2. Direct ADC: disable integrator amplifiers, select only the measured A/B bypass
   input, inhibit all shared monitor muxes;257 points per ADC, Vcm1V and
   requested Vdiff−1.2..+1.2V. DAC0/1 remain within0.4..1.6V. DAC2/3 were parked
   at2.048/1.024V for this first ADC dataset. Retain that condition for comparisons.
3. Integrator: isolate direct ADC injection before enabling amplifiers. Keep
   DAC0/1=1/1V. **This cable pair needs DAC2=1.024V+δ/2,
   DAC3=2.048V−δ/2**, opposite to the earlier single-pair experiment.
   The initial opposite-polarity saturated scan is retained and excluded from
   balance fits. Coarse13 points, fine26 points at0.4mV, independent revisits
   and±5mV sign checks. No clipped trace counts as balance.
4. Archive raw buffers, executed source snapshots, SCPI/UART receipts and
   normalized test result. Compare all12 channels on common plots only after
   selecting valid independently acquired results.
5. Repeat for the next confirmed analog destination. Generate a report snapshot
   after each fitted group; incomplete coverage remains explicit.

On the first preflight the PM SRAM image had been lost during mounting/power
cycling. The same qualified diagnostic image `c7c42d28` was restored via JTAG
and the existing Kasli private bridge re-enabled. No PLL profile, CPU firmware,
CPLD image, power protection or flash was changed.

Expected station input `station-base.json` requires the four-port Kasli CFD4
image, not the older single-port profile. Per-method executed sources/settings
are frozen when a successful result is first imported. A software change that
alters a frozen dependency requires a reviewed new protocol/campaign version;
do not bypass the mismatch or silently merge different versions.

[Campaign procedure and CLI](CAMPAIGN.md). Earlier preliminary channel12 and
12/10/8/6 measurements were not imported as new campaign data.

## Completed SMU scans on the current fitting

Internal DAC B/C/D transfer tests now PASS on9,10,11,12:12curves,
101codes/curve and3fresh READ? samples per point. Keysight B2910BL
MY63320299, Force HI/LO local sensing,0A,20V/1PLC. First attempt is retained
as INCOMPLETE after process termination without final metadata. Second attempt
is selected explicitly after raw validation and independent post-cleanup.
The original restored TCA masks(0,8) are retained in raw metadata; post-cleanup
explicitly cleared both to0. All monitor muxes inhibited, SMU OFF/HIZ, exercised
B/C/D sent0000; phase DAC-A and external MOD-DAC-28 were not written.
At the end of that SMU scan both USB cables were still declared on12.
The subsequent confirmed move to11 and its analog measurements are recorded below. See[evidence](evidence-campaign-smu-20261113/README.md).

## Completed analog tests on channel11

The owner confirmed moving both pairs to11:0/1→J8 ADC,2/3→J6 integrator.
Routing receipt and the previous station map are retained. Preflight confirmed
MCU1803, FPGAc7c42d28, stable PGOOD and TCA masks0; all four monitor muxes,
integrator amps and direct-ADC muxes were initially inhibited before parking
DAC2/3 at the frozen ADC-test bias2.048/1.024V. Probe A/B responses and the
full257-point scans passed. ADC gains are−1783.31/−1776.86codes/V; phase-template
residual RMS0.539/0.512codes (total RMS61.46/59.54 includes periodic structure).
Adjacent-bit tests PASS for both ADC banks.

Integrator balance: A at DAC2/3=1.0260/2.0460V, B at1.0288/2.0432V. Fine-scan
gains−2558.7/−2553.3codes/V. Four candidate revisits per bank and±5mV sign checks
PASS. A/B balance separation is about5.70mV in the differential coordinate;
a common setting does not null both. Final shared park2/3=1.0274/2.0446V;
0/1=1/1V, other DAC outputs unchanged. Channel11 integrator amps enabled,
direct ADC injection isolated, all monitor muxes inhibited, TCA masks0, ADC A
last. Other fitted channels' amps/bypass were disabled at preflight.
No firmware/gateware/clock changes. Hardware leases released after acquisition.

The channel11 ADC imports used the exact frozen ADC-v1 normalizer, materialized
at `staging/method-tools/adc-v1/` in the live campaign. Its5source files match
the channel12 sealed analysis snapshots byte-for-byte. Native acquisition and
integrator analysis dependencies also matched their frozen per-method versions;
all three new cases imported without changing comparison contracts.

Analog ADC/integrator coverage is now11and12;9and10 still await confirmed USB
moves. All four internal DAC B/C/D tests remain covered.

## Completed analog tests on channel10

Owner confirmed both USB pairs moved11→10, with RJ45 mapping unchanged.
Preflight MCU1803/FPGAc7c42d28/PGOOD/TCA masks0 and selected A/B voltage probes
PASS. Both257-point ADC transfer and adjacent-bit cases PASS. Gains are
−1777.67/−1778.27code/V; residual RMS after phase-template removal0.513/0.508code.

Integrator fine26points and four candidate revisits per ADC with±5mV controls
PASS. A pair2/3=1.0251/2.0469V, B=1.0284/2.0436V. Mean near-balance changes
−0.234/+0.191code. A/B differential balance separation6.766mV. The coarse
waveform high-pair assignment produced an additional positive-going crossing
near+40mV; it was not used as balance. Fine acquisition followed the central
negative-going crossing, confirmed independently. Both controller versions and
all original coarse data remain archived; the measurement source/settings
contracts were unchanged. Of552buffers analyzed,512were retained:28clipped
coarse,4ambiguous coarse and8ambiguous auxiliary validation buffers excluded.
Required candidate returns and positive/negative response controls passed.

Final external DAC0/1=1/1V,2/3=1.0268/2.0452V; other outputs unchanged.
Channel10 amps enabled, direct ADC injection isolated, all monitor muxes
inhibited, both TCA masks0, ADC A last. Other fitted channels' amps/bypass
remain disabled from preflight. No MCU/CPLD/FPGA/flash/clock/SMU changes.
Analog coverage now10,11,12;9 awaits the next confirmed USB move. Earlier
results remain selected for their own physical channels. See
[evidence](evidence-campaign-ch10-20261113/README.md).

## Completed timing tests on all four connected channels9–12

No USB move: both cables remain on10. Slot7 ports0/1/2/3→PM12/11/10/9
reconfirmed with16TDC events each.25phases×128events per channel passed;
12800scan events,64discovery events, eight empty quiet windows, no cross-talk.
TDC slope magnitudes46.171..46.176fine codes/ns; this is relative response,
not an absolute calibration. All raw13bits were independently validated.

DAC-A sweeps101points/channel produced404captures with all eight A/B returns
valid at every point. Independent validation checked105880320sampled bits and
4411680hardware phase records. Observed A/B excursions(ns):
PM9=20.792/20.792,10=21.832/20.792,11=20.905/20.792,12=19.753/19.753.
No adjacent step exceeded two sampling bins in this repeat. Native time scale
assumes40.0787MHz×24; gate period48bins. These are sampled relative phases,
not calibrated fine delay or intrinsic jitter.

All eight new timing cases imported PASS with frozen source/settings contracts.
Postflight confirmed MCU1803, PMc7c42d28, PGOOD,12ready TDC frontends and all-zero
quiet counts after the gate sweep. DAC A sent0000 on9–12, CFD TX0/port0, DIO6/7
inputs, PM bridge1, all monitor inhibits HIGH and TCA masks0. No programming,
clock profile, external DAC or SMU commands. Prior analog controls preserved;
prior ADC/integrator measurements remain observations at their own capture
settings. Hardware leases released. Analog channel9 still awaits USB move.
See[TIMING_CAMPAIGN.md](TIMING_CAMPAIGN.md) and the
[combined report](evidence-campaign-timing-20261113/report.pdf).

## Fresh assembly verification — 2026-11-13

Completed available tests without moving USB from physical10. Scoped JTAG168links in both paths, MCU/FPGA32patterns, populated rail voltages and Ethernet/IPbus PASS. CFD monitors9/10/12 PASS; fixture11 MUX7 FAIL (5.479V raw; check R3/R4 divider). HDMI data lanes pass but pad release after SPI reads resets SYS: overall HDMI FAIL. These findings prevent unconditional release. Analog9 awaits the next USB move. Current coverage:28PASS,2FAIL,59NOT_MEASURED. See [52-page report and reproducible evidence](evidence-campaign-assembly-20261113/README.md).

HDMI follow-up: [held-output isolation](../system/evidence-held-spi-20261113/README.md) reproduces delayed SYS restart after SPI reads without releasing outputs. Earlier attribution to release is superseded; HDMI remains FAIL. Slot6 SPI is now held driven at idle0, direction0x00b0. Avoid legacy integrated/STOP/input_cards cleanup.

Clock observer follow-up: [direct traces](../system/evidence-clock-observer-20261113/README.md) establish SYS MMCM LOCK loss and reset after complete SPI frames. No FIN/electrical root cause is established. No case status changes. Golden restored; Kasli still held driven. Watch input frequency metadata needs audit (observed≈40MHz, source120MHz).

2026-11-14: [clock audit](../system/evidence-clock-audit-20261114/README.md) identifies an invalid120MHz assumption in c7 TDC frontend. Historical TDC phase/count passes remain raw functional evidence; their correct-clock qualification is withdrawn pending clock40 retest. Other frozen cases are not overwritten.
