# Fine delta then common translation, PM2 at normal20MHz — 2026-11-17

Physical J6 stimulus remains on PM2. No CPLD/FPGA/MCU image or PLL-profile changes.
Fresh MCU serial1803/FPGA DNA3A17A1B402212223/buildff2f746c checked. Kasli raw
returns confirm normal48-bin gate periods, about20.039MHz using the supplied
LHC40.0787MHz. Sampling phase DAC32768 held during the whole experiment.

Input coordinates deliberately use one-leg steps:
DAC2=1.024V+d+c; DAC3=2.048V+c.
Thus d is relative differential offset and c translates both outputs. Actual
commanded common shift is c+d/2. Single-leg100uV commands avoid rounding a
50uV half-step through the existing four-decimal SCPI formatter. Neither actual
pin voltages nor command-step accuracy were measured independently.

Protocol:13 coarse points d0..12mV,1mV step; for each bank21 fine points at
100uV steps about its coarse root; five common translations c=-10/-5/0/+5/+10mV
at that bank's selected d; independent candidate returns and±100uV neighboring
settings; final nominal-base return.75 points×2banks×3captures=450 raw buffers.
All independently decode and validate without clipped data.

|Bank|Working candidate DAC2/DAC3|Independent candidate returns (code/sample)|
|---|---|---|
|A|1.0322/2.0480V|+0.152,−0.259|
|B|1.0259/2.0480V|−0.238,−0.191|

A neighboring d8.1mV return gives−0.004code; B d1.8mV gives+0.224code and
2.0mV−0.490code. Fine-fit roots are A8.175mV/B1.829mV; the adjacent-crossing
estimator gave8.163/1.944mV. The difference, repeat variation and approximately
0.22code fit residuals show why no sub-grid precision is claimed. Practical
sampled-pair balance is around8.1–8.2mV(A),1.8–1.9mV(B).

Common translation sensitivity is approximately+394(A)/+360(B)code/V at the
respective candidates. A small common offset is a secondary adjustment and
moves both sampled-pair changes in the same direction. Within this measured
±10mV translation, it does not remove the observed separation of A/B balance
settings; simultaneous zero at one shared input pair was not demonstrated.

Estimator: establish one unambiguous high-level two-sample reference per bank
at baseline, then circularly register every four-phase template to that fixed
reference. Registration must be unique; signed changes use the same consecutive
pair, including wrap across capture-cycle boundaries. All raw words still pass
the unchanged ADC coherency decoder. This avoids reassigning a near-flat pair
at every input setting. It is a new diagnostic method, not a weakened old
qualification validator. All450 buffers were independently re-decoded, registered
and compared against the stored means. Five software tests cover capture-origin
invariance, signed response, clipping/ambiguity rejection, grid and known roots.

At20MHz there are only two samples in the integration half. The measured zero
is equality of that sampled pair at the chosen phase, **not an independently
established zero input current or absence of all switching/settling effects**.
The differing A/B offsets and the earlier2MHz waveforms must be interpreted
with that distinction. This successful PM2 run does not retest PM6 or prove
that coarse DAC spacing was the sole cause of its earlier incomplete result.
No selected campaign/production qualification flags changed.

Final nominal DAC23=1.024/2.048V, phase0, selected amps/bypass/monitor inhibited,
TCA0, PGOOD checked, held HDMI enable/state unchanged, all leases released.
The raw archive includes executed acquisition/dependency sources,450 ADC buffers,
Kasli gate captures and UART/SCPI/I2C/identity logs. Full archive readback matches
raw-manifest.json. No whole-report regeneration.

```
python balance20.py --afe 2 --station STATION_JSON --out NEW_RUN
python plot_balance20.py --run NEW_RUN --out NEW_ANALYSIS
```
