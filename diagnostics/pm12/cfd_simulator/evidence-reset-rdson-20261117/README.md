# PM2 continuous-reset resistance experiment — 2026-11-17

Integrator B reset held HIGH at CPLD2 P54; original A gate/divider retained to
preserve the ADC phase-clock reference. Only CPLD2 changed, confirmed by two-pass
nonvolatile array reads of all twelve CPLDs. Original image verified before
programming, then restored/verified afterwards; all 984 rows equal the pre-test
snapshot. FPGA ff2f746c, MCU, PLL profiles and Kasli outputs unchanged.

Two independent 11-point DC sweeps, -100..+100 mV in 20 mV steps: DAC2/P varied
around 1.024 V with DAC3/N fixed 2.048 V, then DAC3/N varied with DAC2/P fixed.
Each point has three raw buffers per ADC bank. Baseline/return and normal-gate
before/after controls retained. All 162 buffers independently decode correctly.
ADC-A was a normal-gate control, not used to estimate reset resistance; some
large stimulus ADC-A waveforms clip. All 22 fitted ADC-B points are unclipped.

|B input branch|Transfer slope (code/commanded V)|Nominal effective R|R²|
|---|---:|---:|---:|
|P, VT5|−318.79|68.54 ohm|0.999812|
|N, VT6|+638.07|137.19 ohm|0.999474|

Model: virtual summing node held at its reference; DC current through the
430-ohm input resistance (210+220 ohm, optional parallel resistor unpopulated
according to schematic) returns through the conducting reset switch. Thus
R_eff = abs(dADC/dV_command) * 430 / G_ADC.
G_ADC = 4096/(2*1.024) = 2000 codes/V is the **nominal**, uncalibrated value.
This is an effective closed-loop small-signal resistance over the scanned range,
not a four-wire transistor measurement. DAC pin voltage changes, installed input
resistance and actual ADC reference/gain were not independently measured.
Consequently absolute ohmic values are conditional on those assumptions.

At baseline, B four-phase amplitude drops from 106.59 to 7.10 codes when held
in reset; restored normal gating gives 106.11 codes. Reset baseline means are
94.76 before sweeps and 94.95/95.02 after P/N returns. Normal-gate B mean is
135.26 before and 134.54 afterwards. Residual periodic structure in reset is
retained, not labelled pure random noise. The test estimates B's two branches;
it does not yet explain all A/B differences across channels.

Internal phase DAC-A held at 32768 for acquisition and restored to 0 afterwards;
external DAC2/3 parked 1.024/2.048 V, selected amplifiers/bypass/monitor inhibited,
TCA masks zero, leases released. No production qualification flags changed and
no production report rebuilt.

ISE build and GHDL comparison ran on Dell. Simulation verified constant reset B
and equality of ADC mux, A gate and clock outputs against original RTL. Archive
contains modified RTL, original/diagnostic JEDECs, ISE reports, iMPACT SVFs,
strictly converted native JTAG Tcl, executed acquisition/analysis sources,
readbacks, UART/SCPI/I2C records and raw buffers; full archive readback checked.

Reproduction uses hardware Python from kasli-diot-bringup; analysis uses the
fit-measurements scientific environment. Extract the archived build vectors into
BUILD_DIR and identify the same physical PM2/J6 wiring before running:

```
python reset_rdson.py --out NEW_RUN --build-dir BUILD_DIR --station STATION_JSON
python plot_reset_rdson.py --root NEW_RUN
```

Primary references: local FIT_PM12v1.1.PDF sheets7/8/11 and cfd_sim.pdf sheet1;
[AD9236 reference/range](https://www.analog.com/media/en/technical-documentation/data-sheets/AD9236.pdf),
[Linear Systems SD/SST210 DMOS datasheet](https://cms.nacsemi.com/content/AuthDatasheets/LISIS00175-1.pdf).
