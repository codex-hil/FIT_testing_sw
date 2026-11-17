# Fitting5–8 / USB8 — 2026-11-17

Owner confirmed simulators5–8, slot7ports0/1/2/3->PM8/7/6/5; both USB on8,
DAC0/1 intendedJ8 ADC and2/3 intendedJ6 integrator; all shared monitors on SMU.
Fresh DNA/MCU identity and restored qualified FPGA ff2f746c; no new build,
MCU/CPLD/flash/PLL programming. Kasli slot6 SPI held throughout, only slot7
buffer directions serviced for finite TDC pulses and receive-only phase scans.

Corrected and independently verified routing: DAC0/1->J8 ADC, DAC2/3->J6
integrator, normal MCP selector map[0,1]. All selected analog results start after
the operator corrected swapped USB pairs. Initial driver-path scans, the temporary
map[1,0], insufficient-range attempt and operator-interrupted wider-range run are
diagnostic history only. They do not establish ADC bank inversion or a gain fault.
Active/inhibited bypass probes independently confirm the corrected input route.
Selected ADC scan returns to standard±1.2V differential at1V common mode,
257points/bank, legs0.4..1.6V. Integrator uses DAC2/3 base1.024/2.048V,
coarse13/fine26points plus independent signed/return controls.
ADC/integrators5–7 await the next USB moves. Original9–12 data and selected
attempts preserved; cross-revision overlays are explicitly labelled.

|Physical PM channel|ADC transfer/bits|Integrator|TDC|Gate phase|CFD monitors|DAC B/C/D|
|---|---|---|---|---|---|---|
|5|NOT_MEASURED/NOT_MEASURED|NOT_MEASURED|PASS|PASS|PASS|PASS|
|6|NOT_MEASURED/NOT_MEASURED|NOT_MEASURED|PASS|PASS|PASS|PASS|
|7|NOT_MEASURED/NOT_MEASURED|NOT_MEASURED|PASS|PASS|PASS|PASS|
|8|PASS/PASS|PASS|PASS|PASS|PASS|PASS|

Zero-input waveform/FFT overlays8–12 use copied selected PASS receipts under
`zero-input-figure-inputs/`. Regenerate offline with
`compare_adc_zero_inputs.py --receipts INPUTS/*.json --out NEW-DIRECTORY`.
The per-bin one-sided RMS spectrum and local waveform origins are not intrinsic
ADC noise/jitter estimates; axes use the declared80.1574MS/s.
