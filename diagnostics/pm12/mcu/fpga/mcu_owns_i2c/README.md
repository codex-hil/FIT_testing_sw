# FPGA with MCU ownership of I2C

Build: `vivado -mode batch -nolog -nojournal -source build.tcl`.
Generated RTL and memory initialization are included. Regeneration uses the
same pinned Migen/LiteX environment as the parent diagnostic.

SDA H22, SCL H21 and RESET_N B26 are **input-only IBUF** in this variant. No FPGA
output driver exists for these nets, independently of UDP requests. RESET input
retains its pull-up. I2C1 zero-mask queries/releases are accepted; nonzero drive
requests are dropped. JTAG USER1 signature is `504d5a02`. Original MCU SPI slave
and fixed 1000BASE-X networking remain present.

Offline Vivado implementation/bitstream and generated-port checks PASS.
Physical loading and shared-bus tests NOT_RUN. This image alone does not add
INA3221 support to the MCU or serialize its legacy temperature clock on PA1.
A compatible MCU software-I2C/temperature ownership implementation is required
before direct MCU sensor testing. It is absent from both current MCU diagnostic
f9869c9 and recovery release pm12-dev-001-timer-relocated.

The latest physical attempt found no PM12 HS2 cable210249A73E43 and no identified
PDI programmer, with original UART RS timing out during user rewiring. No MCU,
FPGA or persistent memory was programmed. Confirm wiring/power/identities before
resuming under the shared PM12 lease.
