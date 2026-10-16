# PM12 current FPGA state,2026-10-16

- Board S/N1803, Kintex xc7k160tffg676-3, Digilent210249A73E43.
- Resident volatile FPGA: integrated ADC/TDC/I2C/SPI build`4bbe9dfc`,
  USER1`504d5a04`, IPbus device`504d1202`, ABI`00010002`.
- Bit SHA256:`5b9c5fb30722a49cb8fdeea524f7541e0b10dce1e575b015a5d5e43d6ff6d5d4`.
- Source: branch`pm12-tdc-buffers`; build and hardware records in`measured/`.
- Endpoint`192.168.2.240:50001`, MAC`02:00:00:00:12:01`.
- TDC status`0x19`, frontend`0xFFF`: all three PLLs/autophase/result clocks ready.
- Frozen TDC generation5: all12 counts zero; repeated50/100/200ms quiet windows
  found no events. No nonempty raw TDC buffer, calibrated pulse or phase sweep
  is qualified. Need verified external LVDS CFD stimulus.
- ADC generation1 is SYNTHETIC,49152 exact words checked. Previously frozen real
  ADC and passive I2C data were backed up under hardware-02 before reprogramming.
- ADC and I2C address windows retained. I2C remains input-only at FPGA; no new
  I2C trace was armed during this qualification.
- MCU UART/PGOOD and32-vector SPI diagnostic pass. MCU reports board power ON,
  internal clock and PLL locked. Its legacy `FPGA not ready` status also occurred
  with the baseline diagnostic; it is not the diagnostic IPbus readiness register.
- No CPLD, MCU, fuse, EEPROM, configuration-flash or peripheral configuration writes.
  CPLDs were not altered; real ADC acquisition still needs the separate mux image.
- Both board leases released after qualification/readout. Only the private PM12
  hw_server was stopped. Existing Genesys server was not changed.

Reproducer: README. Full local evidence:
`/home/codex-hil/fit-bringup/evidence/pm12-tdc-2026-10-16/`.
`hardware-01` is a failed server-selection attempt with no FPGA scan/programming;
`hardware-02`, `retained-01`, `readout-01` and `cli-capture-01` are the successful runs.
Golden ADC restore image remains unchanged at
`/home/codex-hil/fit-bringup/gateware/pm12_ipbus_adc/build/pm12_ipbus_adc.bit`
(build882901f6, SHA256d4026ffe30109672224951a61c43d0d6b0b5272bf9b22c9ec0d4cfc5e4ea199d).
