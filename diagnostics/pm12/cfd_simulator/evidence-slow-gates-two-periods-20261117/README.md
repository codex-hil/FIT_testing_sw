# Two complete contiguous slow-gate periods — 2026-11-17

Offline view of the already acquired PM2 buffers, not a new hardware run.
Each panel shows81 unchanged consecutive decoded ADC samples:80 sample
intervals, exactly two40-sample gate periods including both endpoints.
There is no folding or averaging of the displayed values. A periodic mean
is used only to choose the initial sample at the largest upward step; this
is a relative display origin, not a measured physical gate timestamp.

Both ADC banks and relative differential offsets0/4/8/12mV are shown.
The time scale uses nominal80.1574MS/s. Zero-clipped samples at larger
stimuli remain visible. Every source buffer has1023 valid decoded samples;
provenance.json identifies the raw file, SHA-256 and selected sample indices.
Full raw files are in the [original slow-gate archive](../evidence-slow-gates-20261117/README.md).
CSV contains all648 displayed sample values. No programming or settings changed.

```
python slow_integrator/plot_two_periods.py --run ORIGINAL_SLOW_RUN --out NEW_OUTPUT
```
