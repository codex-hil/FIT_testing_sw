# Full CDCE62005 register audit —board2,20 November2026

**Register consistency PASS; temporary firmware system trial REJECTED; original application restored PASS.**

Three physical dumps R0..R8 matched. R0..R7 exactly match the installed firmware
profile after its documented AUX→AUTO transition; R5=40040FF5. The40subsequent
R8 polls were20009D38: PRIMARY reference selected and lock high at every sample.
Original-firmware control after rollback also passed:40R8 polls all20009D38,
ADT ID C3 before/after, INA reads healthy. This is a separate boot/observation
interval, not one pooled continuous-lock measurement.
No mismatched output divider, input selection or encoded loop-filter setting was
found. The nominal VCO calculation is2003.935MHz, within TI1.75..2.356GHz range.

Calculated frequencies with assumed PRIMARY40.0787MHz:
U0=40.0787MHz, U1=200.3935MHz, U2=40.0787MHz, U3=200.3935MHz, U4disabled.
These are register-derived frequencies, NOT fresh scope/counter measurements.
Loop-filter codes match the known firmware; this is not independent validation
of physical filter components, loop bandwidth, phase noise or clock waveform.
UART polling does not exclude short loss-of-lock/source transitions.

## Method and state changes

Resident f49643c8 diagnostic reads only R8. An isolated source copy added only
bounded read-register0..8 and @PLL ALL. The optional patch is retained here.
No legacy PLL-write/initialization/interrupt bodies were replaced. Native tests
verify every selector, both IRQ states, each byte-timeout, invalid addresses,
GPIO/SPI restoration and existing peripheral/PG behavior. Full development-check
passed. Build sources and private complete NVM backups are on NVMe:
`/srv/codex-hil-nvme/pm12-pll-register-audit-20261120/`.

The temporary application was physically read back. MCU PDI programming restarts
the MCU and reruns its ORIGINAL PLL startup writes, so this audit observes a new
startup state, not an undisturbed pre-audit configuration. Extension transactions
send read selectors only; no host profile/PLL-EEPROM commands or PC were issued.
The pre-audit resident application and MCU production signature were guarded;
FPGA was not ready before reset. No FPGA/CPLD programming was performed.

The temporary system trial was REJECTED: ADT7311 returned zero registers after
the dumps/status polling, although INA reads still worked. Software tests alone
did not qualify this image. Cause is not isolated (startup/shared bus/firmware
timing remain possibilities); do not deploy the patch as an accepted release.
The PLL raw register comparisons remain independently reproducible from receipts.

The original pre-audit application is restored at the end, with full readback
and boot/EEPROM/fuse/lock/user/prodsig/signature comparisons. Final UART/PGOOD,
PLL/temperature/INA readback is retained in hardware-result.json. The temporary
@PLL ALL command is therefore not left resident; ordinary @PLL remains R8-only.
MCU EEPROM serial1803 is copied and nonunique; board2 remains staged with UIDnull
and physical MCU production signature checked, not attributed to the old FPGA DNA.

This supports profile-consistency acceptance only. It does NOT close the reported
instability investigation. Next physical qualification needs independent output
frequency/waveform measurements and a continuous clock/LOCK/source event recorder.

Source of frequency mapping: prior audited profile at
../../system/evidence-clock-audit-20261114/profile.json (all applicable active
registers independently checked this time). TI register and calibration limits:
https://www.ti.com/lit/ds/symlink/cdce62005.pdf
