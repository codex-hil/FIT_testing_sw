# PM12 MCU, FPGA SPI and config-flash diagnostic

Offline build and host tests PASS. Physical UART, MCU–FPGA SPI, flash ownership
and FPGA boot tests NOT_RUN. No MCU or configuration flash was programmed.
The original PSU startup, PG timeout/shutdown, thermal protection and bootloader
remain in the development image. PG observer records elapsed time separately.

Build the MCU image in a new isolated worktree:

```sh
diagnostics/pm12/mcu/build.sh /path/to/FIT_PM_FW_uPC /absolute/new/worktree
```

Firmware is `development/build/development.hex`. The patch pins recovered source
commit 30dec0a; native tests and zero-difference golden baseline are checked.
Firmware changes and artifact hashes are in `diagnostic_contract.json`.

Build the matching Kintex diagnostic offline:

```sh
diagnostics/pm12/mcu/fpga/build.sh
```

Vivado 2025.2 support for xc7k160tffg676-3 is required. The generated RTL and BRAM
initialization are included; pinned Python dependency commits for regeneration
are in `fpga/validation.json`. GHDL simulation checks the SPI slave. Output is
`fpga/build/pm12_mcu_spi_diag.bit`. This image also includes the existing fixed
1000BASE-X Ethernet / I2C1 diagnostic (192.168.2.240:40000). Integration in this
new image has only offline validation. SPI is MCU SCK F22, MOSI G25, MISO G24,
active-low CS E26. MISO uses OBUFT and is high impedance when CS is high.

After UART wiring/programming and volatile FPGA loading are separately prepared,
run bounded UART capture under the shared PM12 board lock:

```sh
python3 diagnostics/pm12/mcu/read_uart.py --port /dev/serial/by-id/IDENTIFIED-PM12 --out uart.json --fpga-test
```

`--fpga-test` adds register reads and 32 walking-one/zero patterns, then restores
and verifies scratch register 40. IDs 504D/5350 at 41/42 are checked before writes.
Register 43 is version 0001, 44 the write counter. Without this option only the
existing read-only MCU diagnostics run. The serial adapter suppresses DTR/RTS
assertion; add `--rtscts` only after checking the four-wire console connections.

Configuration inspection is explicit and **destroys the volatile FPGA image**:
`@CFG` reads INIT_B/DONE/PROGRAM_B, `@CFG HOLD` asserts PROGRAM_B and enables
MCU SPIE ownership, `@FLASHID` reads opcode 9F, `@FLASHREAD 000000 10` reads opcode
03 (at most 16 bytes). Wait for DONE low before flash reads. No write-enable,
program or erase command exists. The original roughly five-second FPGA retry
remains active: HOLD is a short inspection, not a persistent programming mode.
Every flash transaction verifies ownership and releases CS even on timeout.

`@CFG BOOT` disables SPIE, releases the configuration bus and raises PROGRAM_B.
The response confirms only a request. Require INIT/DONE within a bounded deadline
and arrange JTAG restoration of the known SRAM image if flash boot fails or its
contents are unknown. Config-reset operations are deliberately excluded from
`read_uart.py`. Hold the PM12 lock over reset, UART, tests and restoration.
