# Board2 known FPGA reload and IPbus stability —20 November2026

Physical UID **PM12-K7-2A17A1B40221242B** confirmed by JTAG before SRAM loading.
Last qualified image **ff2f746c**, SHA25628fb5747bafe575455bff8bf91484c8ebb5303ea18d3e0a0925fdb0c4283d0b2,
loaded and acknowledged with LOAD_PASS. IPbus ID504d1202/10002/ff2f746c returned.
This is volatile SRAM only, no MCU/CPLD/Flash/PLL programming.

**Communication stability FAIL.** An exact endpoint-count challenge failed
72versus76STROBE cycles; its guard was not weakened. Subsequent probes were
read-only and are not identity-bound functional acceptance or ADC tests.

Initial diagnostic at0.35s socket timeout:7complete poll iterations,5failed
iterations,20read timeout events. Independent Kasli management control50/50,
no timeout events. One reviewed private-PHY reset used Kasli CTRL100:256→0;
management Ethernet, packet/bridge mode and held HDMI/DIO settings preserved.
Native1s timeout repeat:14complete poll iterations,2failed iterations,
35read timeout events in the bounded run. Timeout events include final failed
attempts, not just actual retransmissions; do not interpret as packet-loss ratio.

No SYS counter restart was observed between successful polls. Missing periods
were not continuously observed, so short resets/clock disturbances are not ruled
out. Frozen-buffer/ADC transport acceptance was skipped. MCU status remained
PRIMARY/LOCKED, power good, ADT ID C3. Image is retained; no clocks were retuned.
The reload and one private-link reset did not fix the reported issue.

All four original setup receipts remain immutable in their UID directory, hashes
verified. Exact paths are in summary.json. Executed controllers and raw subset
are here. Continue fault isolation of PM↔Kasli transport/clock/forwarding; this
result does not isolate a hardware fault or justify changing the PLL profile.
