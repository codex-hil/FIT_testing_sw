# PM12 board2 MCU provisioning —20 November2026

Owner authorized the same diagnostic application as board1, the deployed fuse
profile and explicitly copying board1 EEPROM. See provisioning.json for hashes,
independent readback, exact commands/replies and scope. Application programming,
EEPROM copy and final fuses FF/00/FE/F3/E8 verified. Boot remains initially erased;
no bootloader, FPGA, CPLD, chip erase, user signature or production signature writes.

Board2 has a different MCU production signature; FPGA DNA remains unread because
the expected JTAG chain is not detected. Keep this provision record unbound rather
than putting it under the old board UID. EEPROM serial1803 is intentionally copied
and is not a unique identity. Full private raw backup is on NVMe, not in Git.

PGOOD, UART diagnostic console, PLL lock and temperature readback work. All three
INA3221 reads return BUS_STUCK (SDA low, SCL/RESET high). Owner confirms new-board
I2C wiring is not yet prepared; no voltage values/acceptance can be reported.

Legacy AVRDUDE standard fuse4 write falsely reported verification while leaving
FE; a subsequent raw alias write produced F3. The alias configuration renames the
inherited fuse4 memory to fuse4raw; do not request both names in one invocation.
The final independent read uses the standard x128a3u profile and confirms F3.
The first alias invocation exited late when asked for the renamed standard memory;
its writes had already succeeded. Preserve that log; it is not a hardware failure.

Next: prepare sensor wiring, inspect JTAG attachment, read DNA and enroll a new
board session. Then rerun @POWER under PGOOD/leases and retain all raw INA words.
Do not reuse board1 measurement selections, fitting or hardware status.
