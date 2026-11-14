# Within-image SPI reset / MISO experiment — 14–15 November2026

**Reset-only suppression and reversal were observed. MISO clamp alone also
suppressed the effect with an active parser.** This narrows the dependency
to output behavior; it does not prove a physical short, FIN fault or unique
internal parser cause. The intermittent SYS/MMCM finding remains open.

Two completed cohorts use the identical combined bitstream30096dcc, with a
separate PM configuration before each cohort. **No programming or clock/divider
changes between conditions within either cohort.** Kasli was never reloaded.
After positive baseline search, fixed stimulus is divider601/read0.

## Primary reset-only cohort(reset_only)

Runtime mode0→1→0→2→0→1→0. Mode1 changes ONLY parser-reset bit0; explicit
MISO-clamp bit1 stays0. Parser retains its shift data with MSB0, so raw MISO
naturally becomes a constant0 while held; that is verified in trace data.

| Stage | Mode | SYS resets / frames |
|---|---:|---:|
|Selected normal baseline read0|0|2/2|
|R1: reset only|1|0/6|
|A1: release reset|0|6/6|
|C: active parser, clamp MISO0|2|0/6|
|A2: remove MISO clamp|0|6/6|
|R2: reset only|1|0/6|
|A3: release reset|0|6/6|

Initial search across reads0/1/2 was6/6; read0 was selected after two direct
reset witnesses. Whole cohort:44 complete windows,42SPI frames,2idle controls.
All responses match expected diagnostic values(0 during held/clamped cases).
Independent analysis checks sampled mode bits, actual counter activity and
SYS reset in the reset-independent recorder. Parser reaches count31 in A/C
and remains count0/reading0 in R. Physical SCK continues; this is not clock gating.

## Separate clamp-matched cohort(hardware02)

Initial mixed-address baseline5/6; selected read0 baseline2/2. Sequence
C1→B1→C2→B2→C3→A-return, six frames each. C is active parser/MISO0(mode2),
B is held parser/MISO0(mode3). C total0/18, B total0/12, A-return6/6.
Thus removing MISO data transitions/levels is sufficient to suppress the
observed fault in this tested regime without stopping the parser. It is not
an exclusive proof of the electrical mechanism: logical/internal output and
received payloads are recorded, not a continuous analog pad waveform.

This cohort also has44 complete windows(42frames+2idle), all expected replies.
Do not pool the two cohorts as one uninterrupted configuration session.
The primary comparisons above each occur within a single configuration.

## Interpretation and limitations

Normal responses reproduce before and after quiet stages; this addresses
the earlier inconclusive experiments where normal controls also stayed quiet.
Reset-only works here, but reset is not necessary: clamp-only works too.
It would be incorrect to declare the decoder state machine the unique cause.
The next physical distinction is which aspect of the MISO path matters;
steady high levels, switching, loading, contention, coupling and reference
quality have not been separately measured by this experiment.

Watch is nominal40.0787MHz MCLK1 and survives SYS reset. Ignore first8ARM
settling ticks; sampled multibit state is not an atomic CDC transfer. A common
watch/reference clock stop is not represented. Flags, actual state and LOCK
are validated from frozen raw records; network timeouts alone are not resets.
Read-only operations use bounded recovery and frozen buffers are saved before
ancillary reads. No write is blindly replayed. Two simulations cover parser/
clamp/reset separation and observer readout/retained traces, with an additional
mode1/reset-only/release simulation.

Candidate30096dcc SHA256
344d49b9eb5ded207fd1340de88d36128197ee7c2624ed5fe94ce32d686fe245;
Dell WNS0.019ns/WHS0.061ns, no DRC errors/critical warnings, baseline FIFO warning.
Runtime305 has two independent bits and observer format30003 records them.
Mode4 rejected. Source/bitstream/qualification and exact executed helpers retained.

## Execution receipts and final state

First attempt(hardware) stopped on a Python result-name error during the initial
idle capture, before any SPI test frame; exact original PM and ADC were restored.
It is retained, excluded from valid cohort counts. Corrected helpers froze their
exact source into each run. The clamp cohort launcher reported143 after complete
saved results/restoration; its final metadata and subsequent fresh identity checks
are healthy. Primary reset-only cohort exited0. See execution-status.json.

Exact PMc7531465 restored after both cohorts; final independent tailcheck PASS.
Kasli SPI remains driven(enable1/status9), frontend0xfff, power healthy and
physical ADC bankA all12channels passed on first postflight attempts. No explicit
external PLL, MCU, CPLD, flash or analog programming. Clamp/reset are not retained
as a functional workaround; normal SPI replies are restored and fault stays open.

UTC captures started14November; local WAT sessions span14–15November. Artifact
root retains the UTC start date20261114. [Primary plot](reset-only/spi-ab-result.png),
[matched-clamp plot](clamp-matched/spi-ab-result.png), [raw data](raw.tar.gz),
[source/bit](source-and-bit.tar.gz), [code/procedure](../spi_ab/README.md).
Reproduce with spi_ab/analyze.py and plot.py --help, no hardware for analysis.
