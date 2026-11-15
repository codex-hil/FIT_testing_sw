# CDCE-output counter referenced to recovered RXCLK

Counts MCLK1 (CDCE U2), MGT_REF/2 (CDCE U3/2) and SYS, using the already-buffered
GTX RXOUTCLK as reference. RXOUTCLKSEL=2 selects receiver PMA clock; this path
precedes the RX MMCM and is not net_clk (= TX clock). In the normal LHC setup,
reference≈60.11805MHz and expected counts per384 reference cycles are256/640/256.
A full window is≈6.387us;2048 records retain≈13.08ms of rolling history.

The target16-bit counters run without SYS reset, transmit registered Gray code
through two-stage synchronizers, and are sampled/subtracted modulo16bits.
Bus-skew constraints bound each crossing to5ns, below the fastest10ns source
period. Existing asynchronous clock exceptions can override absolute max-delay
constraints; the independent routed bus-skew report is required for qualification.

Acquisition survives SYS reset. A sticky asynchronous SYS-reset latch freezes
at the next RX edge, storing a final partial window. Host must exclude partial,
post-reset or invalid-reference samples from quantitative frequency claims.
Full-window global minima/maxima persist even if older records roll out of RAM.
No-reset acquisitions stop at≈100ms, leaving only the final13ms in RAM.

RXCLK is not an independent laboratory oscillator: the GTX CDR needs the local
reference and its reset controller belongs to SYS. A disturbance can therefore
stop/restart RX clock too. Qualification flags and a partial event record expose
some of this, but a complete common clock stop is not measurable in its own
clock units. Stable pre-trigger samples are the intended comparison. Counting
edges cannot exclude narrow analog glitches, phase steps, or a single extra
edge hidden by endpoint quantization. This is not an analog jitter instrument.

## Word-addressed IPbus interface

| Address | Meaning |
| --- | --- |
|390|Read magic434c4b52; write41524d31 to arm|
|391|bit0 active,1 frozen,2 SYS trigger,3 arm epoch,4 sticky SYS loss,5 invalid RX seen,6 RX valid|
|392|Record count, max2048|
|393|Oldest physical record index, wrap-aware|
|394|Nominal RX reference60118050Hz|
|395|Window length384 reference cycles|
|396|Reference ticks since arm|
|397|Window identifier counter|
|398/399/39a|MCLK / MGT_REF2 / SYS extrema: minimum high16, maximum low16|
|39b/39c|Timeout reference cycles / record depth|
|a000..bfff|2048 physical records, four32-bit words each|

Record words: reference tick; `{gt_edges,mclk_edges}`; `{flags,sys_edges}`;
`{window_length,window_id}`. Flags:0 SYS lock,1 CAP lock,2 SYS reset,3 GTX PLL
lock,4 RX init done,5 RX MMCM lock,6 sticky SYS loss,7 partial,8 invalid RX seen.
Host reads only frozen RAM, reorders from393 and verifies unchanged status/count/
start before and after the complete download. Metadata crossings are not atomic.

Initial v1 used misaligned RAM base9000 and was rejected before programming.
The installed/tested candidate must use aligned basea000, buildff2f746c.
No v1 hardware measurement is claimed. Baseline synthesis warnings about old
lhc120 clock aliases are retained; targeted DRC, timing and bus-skew reports
qualify the final image, not merely the launcher return code.

## CDCE status

`cdce_status.py` decodes installed UART @PLL R8 words. The low nibble is the
register address, so payload=word>>4. Payload bit6 is PLLLOCKPIN; bits27:25
identify selected source1 PRIMARY,2 SECONDARY,4 AUX. These are current status,
not documented sticky LOS/event counters. No separate PRI_LOS register is claimed.
Source: [TI SCAS862G, table48](https://www.ti.com/lit/ds/symlink/cdce62005.pdf).
UART polling can miss a microsecond loss or brief source switch. It also toggles
the PLL's SPI pins while reading, so idle-only control captures are included.

`tb.v` verifies clock ratios, source counter wrap, ring wrap/readout, dropped
MCLK edges, asynchronous SYS-reset capture, reference-invalid marking and rearm.
`prepare.py` builds from resident71ac56fb; heavy compilation goes to Dell.
`test_counter.py --work WORK` runs on Optiplex with all three existing leases,
board DNA/MCU identity checks, driven Kasli outputs and unchanged CDCE firmware.
It compares idle and read0/read1, logging UART R8 before/after and all raw windows.
The tested image is freshly reloaded after deliberate reset-provoking reads and
retained only after power/frontend/temperature/physical ADC checks; failure
restores the previous71ac56fb SRAM. No MCU/CPLD/flash/clock-profile programming.

## Physical results

See [2026-11-15 frozen raw data and qualification](../evidence-rx-clock-counter-20261115/README.md).
Resident ff2f746c retained; idle exact, read0/read1 SYS triggers with at most
one-count deviations in valid windows. R8 PRIMARY/locked before/after; transient
loss or switching remains unexcluded. Final physical ADC12/12 PASS.
