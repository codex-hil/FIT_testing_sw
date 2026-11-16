# Channel9 analog tests — 2026-11-16

Owner moved both USB cables10->9: MOD-DAC0/1 to J8 direct ADC,2/3 to J6 integrator.
Fitted CFD9-12 and RJ45 mapping unchanged. Fresh MCU1803/FPGA ff2f746c/power checks,
all four shared muxes inhibited, other amplifiers/bypass isolated at preflight.
ADC A/B257-point scans and adjacent-bit exercises PASS; integrator signed crossing,
fine26points and independent return/sign controls PASS. All voltages commanded
within3.3V. No FPGA/MCU/CPLD/clock/SMU programming in this acquisition.

The firmware validation guards now accept an explicitly supplied expected build;
the previous frozen source contracts are preserved. A new independent campaign
revision four-cfd-clock40-20261116 records actual ff2f746c provenance. Original
same-fitting identity receipts are copied verbatim; live16Nov preflight and owner
USB routing are archived. Old10-12 data remain under their original c7c42d28
contracts. The overlay labels this hardware difference; it is comparative,
not a claim of identical hardware/clock implementation or fresh retest10-12.

Raw archive includes full revision registry and original buffers, executed sources,
SCPI/UART receipts, controls and analysis. Summary and normalized results retain
metrics/limits. Final DAC settings and GPIO state are in validation02/status.json.
The combined report adds this chapter without rewriting historical coverage.
