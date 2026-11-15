# Manual CDCE reference-isolation experiment — not a normal acceptance test

**Current state is restored AUTO/PRIMARY, not forced AUX.** MCU full-FLASH hash
f49643c80c6189afebdaa3f7301f4ecebacb55645e60456f66831106d38b9464;
FPGA71ac56fb quiet-write SRAM retained. Final ADT ID C3, physical ADC12/12,
power/frontend and PM Ethernet checks passed. Kasli outputs stayed driven.

The ordinary @PLL command only reads register8; @PLL ALL was rejected by the
installed firmware. The original PC command must NOT be used: it loads another
profile including CDCE EEPROM copy. These manual scripts program MCU application
memory under PM/ICE/Kasli leases, with complete backup, bounded application-only
writes, protected-memory comparison and exact rollback. They are intentionally
excluded from routine acceptance. MCU memory dumps remain private, outside Git.

Reference [TI SCAS862G](https://www.ti.com/lit/ds/symlink/cdce62005.pdf), register5
Smart MUX. Forced AUX uses existing40040F35 rather than automatic40040FF5.
Only PRI/SEC selection bits are cleared; output dividers remain unchanged.
These R5 values are established from firmware/code, not freshly dumped RAM.
UART RS independently confirmed INTERNAL/PLL LOCKED. Nominal outputs become
40/200/40/200MHz rather than40.0787/200.3935/40.0787/200.3935MHz.

## Results and separate cohorts

- Initial hardware process received SIGTERM before MCU programming; orphan JTAG
  client was bounded/cleaned under the board lease. Cause not established.
- hardware02: one-byte startup patch at0xAF9 EF->E3 changes LDI R16,F5 to35,
  preserving native IRQ/power flow. Compiler verified opcodes05EF/05E3. Full
  readback/protected memories passed. INTERNAL/PLL LOCKED achieved, but PM
  Ethernet did not respond; original MCU and SRAM restored.
- hardware03: same startup patch, measured through read-only JTAG. PRIMARY:
  4/6 SYS counter restarts, all replies correct; AUX:0/12, all replies correct.
  Approximate SYS rates40.079211/39.999998MHz. AUX ADT readback was all zero;
  candidate rejected and original MCU/SRAM restored. ADC not measured on AUX.
- hardware04: attempted a runtime-only alternative, changing two unused PC
  operands0x1A45 E3->E2 and0x1A48 49->41, selecting existing R5 word0x292E
  with count1, excluding EEPROM-copy. Native AUTO startup remained unchanged.
  ADT also read zero on PRIMARY before any PC command. Rejected before AUX
  switching; original MCU/SRAM restored. Thus the ADT startup failure is not
  established as caused by AUX selection. PC was NOT invoked in this cohort.

The clock comparison supports a relationship with external-reference operation,
but does not identify cable crosstalk, termination, clock electrical quality or
phase as the unique cause. Temperature initialization differed, so this is not
unconditional validation of a new operational clock profile.

`meter.tcl`/`jtag_meter.py` read USER1 tick bits63:32. RTL increments this counter
on SYS and clears it on SYS reset. Before/after samples around each SPI read
use modulo32-bit subtraction, including legitimate wrap. An elapsed-time envelope
20–60MHz flags discontinuities; this is SYS restart evidence, not an analog
clock measurement or capture of every brief MMCM LOCK pulse. Raw reports,
timestamps, flags and signatures are retained. No PM Ethernet is required.

Kasli still uses the external120.2361MHz reference and its SFP1 link at1.202361Gb/s.
AUX changes the PM nominal link to1.2Gb/s. PM Ethernet was unavailable during
AUX; speed mismatch is a plausible explanation, not independently proved here.
PM/Kasli are no longer phase-synchronous during AUX, so ordinary phase scans
cannot be compared as common-clock measurements in that temporary state.

Rollback images/protected dumps remain under the experiment hardware*/mcu-before
and mcu-rollback directories on Optiplex NVMe. Restore only under all existing
leases, using the bounded application alias, verified original full application
and protected-memory comparisons; reload71ac56fb after MCU reset. No CDCE EEPROM,
MCU EEPROM/fuse/bootloader or CPLD changes were retained or requested.

[Public measurements and final restoration](../evidence-cdce-aux-20261115/README.md).
