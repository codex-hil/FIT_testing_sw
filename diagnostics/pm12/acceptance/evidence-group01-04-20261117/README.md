# New fitting1–4; USB4 — 17 November2026

Owner confirmed CFD modules1–4, retained RJ45 order, shared monitors on SMU;
DAC0/1→J8 ADC and2/3→J6 integrator on4. Finite discovery confirmed slot7 ports0/1/2/3→PM4/3/2/1.
PM initially not ready/IPbus unavailable; original MCU power/PLL state checked. Owner later reported reboot; PGOOD loss interrupted monitor and blockedDAC scan. Original interrupted data retained; monitor/DAC restarted in NEW directories.
Fresh FPGA DNA/MCU1803 verified; qualified ff2f746c restored to volatile SRAM.
No new build or MCU/CPLD/flash/PLL programming. Slot6 HDMI SPI stays driven.

|PM channel|ADC/bits|Integrator|TDC|Phase|Monitor|DAC B/C/D|
|---|---|---|---|---|---|---|
|1|NOT_MEASURED/NOT_MEASURED|NOT_MEASURED|PASS|PASS|PASS|PASS|
|2|NOT_MEASURED/NOT_MEASURED|NOT_MEASURED|PASS|PASS|PASS|PASS|
|3|NOT_MEASURED/NOT_MEASURED|NOT_MEASURED|PASS|PASS|PASS|PASS|
|4|PASS/PASS|INCOMPLETE|PASS|PASS|PASS|PASS|

ADC/integrators1–3 await USB moves. Channel4 status is explicit in the table; failed route probes and partial attempts are not hardware fault determinations.
Integrator6 remains INCOMPLETE after pressing; previous cohorts and all selected IDs retained.
Shared ADC/integrator plots include only the qualified labelled channels; incomplete cases excluded; timing/DAC overlays all12 with historical epochs labelled.
Historical TDC9–12 is the corrected-clock14November acquisition, not withdrawn c7 data.
SCPI voltages and nominal clocks are not traceable ADC/TDC/jitter calibration.

Shared SMU is0A/local Force HI/LO; only one mux active at a time. Supply divider53/33 correction applied.
Final SMU OFF/HIZ, auto-on OFF, all monitor muxes inhibited/TCA0, exercised internal DACs0000.
External DAC park and GPIO state retained in native metadata. Full ADC/integrator results require successful independent validation. Leases released.
Portable data: original group05-08 campaign-raw.tar.gz plus group14-delta.tar.gz in a NEW directory;
complete inventory verified. Never overwrite live acquisition data. All previous source contracts retained.

[Current104-page editable report](../evidence-campaign-assembly-20261113/report.pdf).

The compressed cumulative archive is split into40MiB parts for Git hosting.
Concatenate group14-delta.tar.gz.part001,part002,part003 in that order to obtain
group14-delta.tar.gz; sizes/hashes are in archive-parts.json. Then apply the original
base plus reconstructed delta to a NEW directory. A verified complete local copy
is also retained outside Git. No acquisition data was deleted.

SMB readback-verified PDF: ALICE/PM12-test-reports/PM12-K7-3A17A1B402212223/PM12-report-104pages.pdf
on the codex-hil share. Latest alias replacement was refused; the dated and104-page copies are current.
