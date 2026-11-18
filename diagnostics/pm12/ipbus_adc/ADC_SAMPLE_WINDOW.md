# ADC sample windows

The decoder retains `before-str` as the historical default. Channel2 diagnostics
show some data bits settle within the interval this older policy requires stable.
Explicit `--sample-window str-rise` selects the sample at the observed STR rising
edge and requires it to equal the immediately preceding ADC-data sample. It does
not skip mismatches, interpolate bits, retry failed captures or weaken STR/tag checks.

Both `adc_line_test.py --acquire` and `adc_dc_scan.py` accept the option. Acquisition
records the policy, independent raw validation reads it, and campaign receipts mark
str-rise as a new method/version. Absent metadata always means the legacy policy;
old captures are not silently reinterpreted. Other callers keep their legacy default.

Use only after checking the phase-dependent stability window. On channel2 the
initial repeated diagnostic supported phase16384/32768, but not phase0. Full-scan
validation is recorded separately. Factory timing margins/complete CDC integrity
are not proved merely by agreement of two oversamples.
