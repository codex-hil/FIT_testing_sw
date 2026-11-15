# CDCE PRIMARY versus AUX experiment, 2026-11-15

CURRENT: restored original MCU hashf49643c80c6189afebdaa3f7301f4ecebacb55645e60456f66831106d38b9464,
AUTO selecting PRIMARY/HDMI, PLL LOCKED; FPGA71ac56fb in SRAM, quiet-write mode4.
Final ADT ID C3, physical ADC bankA all12 PASS, frontend0xfff and PGOOD healthy.
PM Ethernet restored; Kasli outputs still driven, divider600, CFD e0=0.

Main completed measurement cohort hardware03 uses read-only JTAG SYS-counter
pairs around Kasli SPI reads, independent of PM Ethernet:
PRIMARY:4/6 counter restarts; AUX:0/12. All18 replies correct. Approximate
SYS40.079211MHz versus39.999998MHz. Direct digital counter observations, not
analog clock/jitter or fast LOCK-waveform measurements.

AUX was achieved and confirmed by UART INTERNAL/PLL LOCKED using a one-byte
MCU startup selector overlay. CDCE output dividers were unchanged, no CDCE
EEPROM copy command sent. Full flash/protected MCU memories verified.
PM Ethernet did not respond at AUX; Kasli nominal1.202361Gb/s versus PM1.2Gb/s
is a plausible explanation, not independently proved. ADC on AUX NOT_MEASURED.

AUX was NOT retained: ADT readback returned zeros. The later two-byte runtime
PC alternative also saw zeros on PRIMARY before any PC invocation, so the
sensor initialization failure is not established as caused by AUX. Both
candidates rejected; exact original MCU/protected memories and SRAM restored.
Runtime PC alternative was never invoked. The normal original PC command is
unsafe for this task because it copies settings to CDCE EEPROM; do not use it.

The result supports a relationship with external-reference operation, but
not a unique electrical cause. Other initialization state differed, so this
is not a fully matched operational-profile acceptance. Clock fault remains OPEN.

Private full MCU/EEPROM/boot/prodsig backups remain on Optiplex under
/srv/codex-hil-nvme/pm12-cdce-aux-20261115/hardware*/mcu-*. They are deliberately
excluded from Git. public-raw.tar.gz includes every textual result/log, executed
wrapper, JTAG raw reports/timestamps and final restored ADC data. First run
SIGTERM before MCU programming; hardware02 aborted on PM Ethernet, hardware03
on ADT, hardware04 before runtime switch. All are retained without a blanket PASS.

Source/procedures: ../cdce_aux/. Independent raw validator: analyze.py; plot.py.
FPGA bit/source is unchanged from evidence-write-quiet-20261115, hash
0407f67e189a25bfee0f6fe02bc6d805c79eedc8b75ce1cca24d2a6dca06daf1.
