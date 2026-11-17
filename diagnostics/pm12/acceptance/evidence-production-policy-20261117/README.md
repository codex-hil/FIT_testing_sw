# Production policy correction — 2026-11-17

Software-only change; no hardware programming or fresh measurement.
Default production scope excludes CPLD reset programming. The sequential runner
rejects diagnostic entry points before acquiring leases. The retired production
reset entry fails closed; explicit diagnostics have a separately named runner
and protocol. Sealed earlier protocols/results remain unchanged.

Production integrator invocation selects board UID/channel, checks the configured
fixed J6 route and explicit DAC pair, acquires normal20MHz data, validates and
plots automatically. Board/channel mismatch, unconnected routing and unknown
future mux backends fail preflight. Native balance20 now reads its DAC pair from
channel configuration; legacy standalone diagnostic defaults are preserved.

51 production/campaign software tests and5 estimator tests pass. All450 archived
PM2 buffers were reanalyzed with identical fit results. pm2-plan-only.json is a
non-executed real board/channel plan. The new wrapper was not physically rerun;
its underlying measurement has the separate450-buffer PM2 evidence.

The new automatic entry currently integrates the integrator test. Existing wider
suite plans retain their supported tests and explicit unavailable placeholders;
this change does not claim all hardware tests or future12-CFD/mux hardware are
implemented. Full unattended routing requires the actual added hardware driver.
