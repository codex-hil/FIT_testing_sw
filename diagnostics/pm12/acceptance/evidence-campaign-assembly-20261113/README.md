Latest channel6 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
**PASS** under the frozen channel8 contracts; integrator **INCOMPLETE**.
Both USB now6: DAC0/1→J8 ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
ADC6–12 available; integrator7–12 PASS,6 requires diagnosis;5 awaits USB.
[Channel6 raw data and common plots](../evidence-channel06-20261117/README.md).

Latest channel7 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
and integrator balance/sign/revisits **PASS**, matching the frozen channel8 contracts.
Both USB now7: DAC0/1→J8 direct ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
Analog7–12 observations available;5–6 await USB moves. Fitting5–8 timing/monitor/internal-DAC PASS unchanged.
[Channel7 raw data and common plots](../evidence-channel07-20261117/README.md).

Latest fitting5–8: [group evidence and USB correction](../evidence-group05-08-20261117/README.md).
All four TDC/phase/monitor/internal-DAC cases PASS; ADC/integrators8 PASS,5–7 await USB.
Both USB now8, verified0/1→J8 and2/3→J6; original selector map[0,1].
Current94-page report includes common8–12 analog and5–12 timing/DAC overlays.
Earlier sizes/coverage below describe their dated cohorts.

Latest repair verification2026-11-17: **CFD02/PM11 monitor PASS after fitting missing33kohm R3**.
MUX7 raw3.405970/3.406098V, corrected+5.470194/+5.470400V; all eight inputs PASS.
[Raw/normalized repair evidence](../evidence-cfd11-r3-repair-20261117/README.md).
The old divider FAIL is superseded for this repaired fixture; historical data preserved.
Current report83pages. MCU-only measurement: FPGA reports not ready/IPbus unavailable; no programming.

Latest analog completion: [physical9 ADC/integrators PASS](../evidence-campaign-ch09-20261116/README.md).
Group9–12 analog functional coverage now complete across explicitly labelled FPGA revisions.
Current report82pages; earlier coverage tables remain dated historical snapshots.

Latest cable comparison2026-11-16: **0/14 SYS-loss triggers, 14/14 correct SPI signatures**, versus prior2/2 triggers.
Original MCU/AUTO-PRIMARY and ff2f746c unchanged; ADC12/12 PASS.
Before/after observation, not proof of a HEC shield defect or completed A/B/A.
[Raw comparison](../../system/evidence-hdmi-cable-20261116/README.md).

[Current 94-page PDF](report.pdf).

Latest resident state: **ff2f746c**, recovered-RX clock counter, original MCU/AUTO-PRIMARY.
[Raw counter/status evidence](../../system/evidence-rx-clock-counter-20261115/README.md).
Idle counts exact; read0/read1 SYS resets with at most one-count deviations.
R8 PRIMARY/locked before/after; short loss or switching not excluded. ADC12/12 PASS.
Historical resident-image statements below describe their dated cohorts.

Latest clock isolation: [PRIMARY versus AUX and final rollback](../../system/evidence-cdce-aux-20261115/README.md).
JTAG counter restarts PRIMARY4/6, AUX0/12, all replies correct. AUX not retained:
PM Ethernet unavailable and ADT initialization unqualified (also failed on PRIMARY
in a later candidate). Original MCU/AUTO-PRIMARY restored; FPGA71ac56fb, ADT C3,
ADC12/12/power/frontend PASS, Ethernet works. Clock fault remains OPEN.

Latest quiet-write implementation: [comparison and installation evidence](../../system/evidence-write-quiet-20261115/README.md).
Resident71ac56fb, default CSR305=4: no MISO echo during writes. Reduced comparison
quiet0/24 resets, raw control1/1; all25 commits correct. Three read replies correct
but3/3 clock resets: read fault remains OPEN. Separate fresh-load installation
quiet24/24 commits/no resets and ADC12/12/power/frontend PASS, candidate retained.
Earlier partial/failed postflight cohorts explicitly separate. No flash writes.

Latest write-only/OE evidence: [completed series and partial-run limits](../../system/evidence-miso-oe-20261115/README.md).
Normal writes8/12 resets; same writes with MISO0 clamp0/12; normal return11/12.
All36 scratch writes verified via IPbus, no SPI readback. Normal/always-OE/normal
read controls6/6 each; removing Hi-Z does not suppress. Mode5 unmeasured after
failed readback; full planned protocol incomplete, all errors/raw retained.
Exactc753 restored; ADC12/12/power/frontend PASS.

Latest standalone MISO test: [raw traces and results](../../system/evidence-miso-generator-20261115/README.md).
1kHz continuously driven MISO:0/24 SYS resets or lock losses,12216 sampled edges.
Static low0/12, high0/6. Normal SPI controls12/12 resets, all replies correct.
Clock integrity and output-enable/Hi-Z effects remain open. Exactc753 restored;
ADC12/12, power and frontend PASS.

Latest MISO drive comparison: [raw captures and restored state](../../system/evidence-miso-drive-20261115/README.md).
Matched SPI read0/divider601:12mA6/6 SYS resets,4mA12/12,12mA return12/12.
All replies correct; minimum FPGA drive does not suppress the issue. DD29 still
drives HDMI. Exactc7531465 restored; ADC12/12, power and frontend PASS.

Latest within-image reset-only reversal: [full data and controls](../../system/evidence-spi-ab-20261115/README.md).
Reset-only R1/R2:0/12; resetting bit cleared in A1/A3:12/12. Independent active
parser/MISO0 control:0/6; removing clamp:6/6. All stages in one30096dcc image
at601/read0. Separate matched-clamp cohort confirms MISO0 suppression without
reset. Physical cause remains open. Exactc7531465 restored, Kasli unchanged,
ADC/power/frontend/final tailcheckPASS. Raw/failed attempts retained separately.

Latest direct SPI-state/clock correlation: [four reset traces and netlist audit](../../system/evidence-spi-state-20261114/README.md).
All four SYS resets occur with parserIDLE9.6–10.2nominal ms after frame end;
fixedMMCMLOCK falls withRST/PWR0, CAP/GTXLOCK1.600:0/6,601:4/6 (small ordered
partial series). No SPI merge found in audited clock/reset/control cone.
Exactc7531465 restored, Kasli unchanged/driven, ADC/power/frontend postflightPASS.

Latest parser-reset A/B: [raw records](../../system/evidence-spi-reset-20261114/README.md).
132 measured frames stable in both held and normal modes: inconclusive for
suppression. After exactc7531465 restore,36 ordinary signatures also stable.
Fault remains open/intermittent. Kasli unchanged, SPI driven, ADC postflightPASS.

Individual SPI pin follow-up: temporary GPIO mode confirmed by MCU pin reads;
SEL/SCK/MOSI separately36 cycles and selected MOSI24 cycles without observed
reset. Full-frame controls still reproduce (2/12 confirmed before and after;
read timeouts retained as unknown). MISO probe inconclusive because controls
also stable after restore. Onech01 ADC capture warning retained, fresh capture
passed. [Raw evidence](../../system/evidence-spi-pins-20261114/README.md).
Original four-port Kasli restored, PMc7531465 unchanged, SPI stays driven.

Latest selective HDMI follow-up: each of four data outputs160 isolated cycles,
no SYS restart. Coupled SPI remains the reproducer, including at917Hz SCK.
An apparent busy/reset overlap was caused by delayed counter readback and
is not causal evidence. Timed nominal epochs are after frame completion.
[Raw traces and conservative reanalysis](../../system/evidence-selective-20261114/README.md).

**Latest 2026-11-14:** the report starts with the corrected-clock TDC repeat.
Current SRAM build **c7531465**; TDC9–12 PASS, 19,268 events, 25 phase
positions/channel. ADC digital regression all12/both banks PASS. HDMI/SPI
SYS restarts persist (8/12 reads); CFD11 MUX7 finding remains open.
[New raw evidence and plots](../../tdc_live120/evidence-clock40-20261114/README.md).
External PLL profiles were not changed; slot6 SPI stays driven. Historical
campaign coverage below is unchanged. The previous c7 image is not a
correct-clock TDC qualification. USB stimulus still on PM10.

# Assembly verification, fitted group9–12 — 2026-11-13

[66-page report](report.pdf), editable [template](report.tex), [findings](assembly-findings.tex), [content](content.tex), [connection table](assembly-connections.tex), [monitor plot](monitor-assembly.png), [raw campaign](campaign-raw.tar.gz).

Board PM12-K7-3A17A1B402212223. USB stimulus stays on physical10. This is assembly verification, not an unconditional board release: 30 selected cases,28 PASS,2 FAIL,59 NOT_MEASURED.

Fresh scoped JTAG/static connections168/168 in both independent paths, MCU/FPGA32walking patterns, populated rail voltages and functional Ethernet/IPbus transfers PASS. Monitor inputs on9,10,12 PASS.

Two open findings:

* CFD fixture at11 MUX7 reads5.479V raw instead of approximately3.41V. Independently repeated. Inspect its R3=33kΩ to ground and R4=20kΩ from P5V5, soldering or intended variant. The nominal-divider equivalent8.80V is NOT a measured PM rail; independent PM telemetry is5.496V.
* HDMI walking/PRBS/idle data pass, but SYS resets on FPGA-pad release after SPI signature reads. Full HDMI case remains FAIL. Legacy boundary wrapper consequently reports ERROR after restoration; raw evidence retained. Static JTAG PASS is scoped and independently validated, with healthy ADC/TDC after restoration.

Analog9 remains NOT_MEASURED until the next USB move; fixtures1–8 are absent. Existing analog10–12 and timing9–12 remain selected with original settings. The fitted3.8V shunt is1mΩ; host conversion gives nominal3.12A from raw INA data while retaining the stale firmware flag.

Final state: diagnostic SRAM restored, MCU power protection untouched, DIO outputs released, SMU OFF/HIZ/0A, all four monitor muxes inhibited and TCA masks zero. No persistent programming or clock changes.

Reproduce offline: extract campaign-raw.tar.gz to a NEW directory; run campaign_report.py (see --help), then assembly_appendix.py --report REPORT --work EXTRACTED/batches/ch09-12-attempt001/working --latex /path/to/tectonic. Matplotlib is required. Alternatively edit the supplied TeX and run tectonic report.tex in this directory. Figures are generated from raw inputs; no hardware access is required. Test results:37acceptance and46CFD tests PASS.

Later follow-up: the PDF now prepends an erratum. Delayed SPI-related SYS resets also occur with outputs held driven. Earlier release attribution is superseded; see [raw follow-up](../../system/evidence-held-spi-20261113/README.md). The selected historical case results and raw archive are unchanged. Current direction/idle state is held, rather than released.

Further direct clock-observer evidence is prepended to the PDF: MMCM LOCK/SYS reset captured, without a proven FIN/external-PLL root cause. Nominal watch time is40.0787MHz, contrary to source120MHz metadata. [Raw follow-up](../../system/evidence-clock-observer-20261113/README.md).
