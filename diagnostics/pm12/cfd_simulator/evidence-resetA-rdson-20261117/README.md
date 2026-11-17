# PM2 continuous reset A — 2026-11-17

Physical follow-up requested by the owner: hold INTA HIGH, keep the original
INTB waveform and internal divider. ADC STR continues correctly; all162 buffers
pass the unchanged edge/coherency decoder. The prior assumption that a toggling
A gate was mandatory for this acquisition was disproved on this setup. No PLL
profile was changed; this observation is not a cold-start/fallback qualification.

Two separate11-point input P/N sweeps ±100mV, other input fixed1.024/2.048V,
three captures/bank/point, phase DAC32768 during acquisition. Same DC transfer
method and nominal assumptions as the B reset experiment: Rin430ohm,
G_ADC2000code/V. No fitted A point clipped.

|Integrator|P effective R|N effective R|
|---|---:|---:|
|A, this run|77.09 ohm|141.79 ohm|
|B, preceding run|68.54 ohm|137.19 ohm|

A slopes are −358.56/+659.50 code/commanded V; R²0.999880/0.999090.
These are conditional effective closed-loop resistances, not independently
calibrated transistor measurements. Actual pin voltages, input resistors and
ADC gain/reference were not measured. A/B resistance differences alone do not
establish the cause of the much larger waveform-amplitude differences.

Only CPLD2 altered, verified by all-CPLD two-pass array reads. Original restored
and all984 rows match before-programming snapshot; original image verified.
Phase0, externalDAC23=1.024/2.048V, amps/bypass/monitor inhibited, TCA0, leases
released. FPGA/MCU/Kasli/PLL profiles unchanged. No production report rebuild or
selected qualification updates. Archive includes exact executed sources, raw
buffers, JTAG/SCPI/UART/I2C records, JEDECs/SVFs/build reports; full readback checked.
