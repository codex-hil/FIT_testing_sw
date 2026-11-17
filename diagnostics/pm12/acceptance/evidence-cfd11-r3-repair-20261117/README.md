# CFD02 / physical PM11: R3 repair verified — 2026-11-17

Owner confirmed missing33kohm R3 and fitted it. Monitor MUX7 previously measured
5.479V raw (divider output incorrectly near full rail). After repair two visits,
five fresh readings each, measured3.405970 and3.406098V raw; applying53/33 gives
+5.470194 and+5.470400V. All eight monitor values and relative-reference checks PASS.

Keysight B2910BL MY63320299, Force HI/LO local sense, source0A,20V/1PLC.
Only one of four shared muxes active at a time. Final SMU OFF/HIZ/0A, auto-on OFF;
all four muxes inhibited, both TCA masks0. Analog GPIO upper bits/B controls preserved.
No DAC writes, firmware/gateware/flash/profile changes, Kasli outputs untouched.

MCU1803 confirms power healthy, PRIMARY and PLL LOCKED. It reports FPGA not ready;
IPbus timed out. First attempt stopped before mux selection on the old FPGA guard.
Second completed MCU-only check is the selected result. This is a repaired monitor
PASS, not FPGA/Ethernet qualification or a repeat of ADC/integrator/TDC tests.
Both attempts retained in raw archive. Old faulty measurement remains historical.
New independent monitor method registered in clock40 revision; parent source
contracts and original FAIL raw data preserved. Report erratum closes this specific
fixture-divider finding after repair; other board findings remain separate.

|Input|Signal|Raw V|Converted V|
|---|---|---:|---:|
|0|CFD_OFFSET|1.034134|1.034134|
|1|CFD_CMP_OFFSET|0.004000|0.004000|
|2|BUFFER_OFFSET|1.023886|1.023886|
|3|DRV_OFFSET|1.043962|1.043962|
|4|DRV_VOCM|1.535840|1.535840|
|5|N5V5_PM12|-3.428492|-5.506366|
|6|P1V3|1.304536|1.304536|
|7|P5V5_PM12|3.405970|5.470194|
