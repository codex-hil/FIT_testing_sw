# Production tests: board/channel selected, resident CPLD gateware

Owner decision: routine production tests must not reprogram CPLDs. Normal20MHz
resident gateware is verified and used as found. An unresolved measurement is
reported as ERROR/INCOMPLETE; the runner does not switch to2MHz or a held-reset
image. Those procedures remain explicit diagnostics outside the production plan.
FPGA SRAM boundary diagnostics remain the existing separate connectivity step;
this policy concerns CPLD configuration programming, not read-only identification.

The production campaign scope is profiles/campaign-four-cfd.json. The optional
CPLD-reset experiment now has its own campaign-reset-diagnostic.json protocol
and diagnostic_integrator_reset.py entry point. The old run_integrator_reset.py
entry point refuses to run. Earlier sealed protocols/evidence are historical;
their hashes and selected records have not been rewritten.

## Automatic integrator step

```
python production_integrator.py --board PM12-K7-3A17A1B402212223 --channel 2 \
  --station /srv/codex-hil-nvme/pm12-production-config-20261117/station.json \
  --out NEW_OUTPUT
```

Add --plan-only to inspect without creating output or accessing hardware.
The script checks requested UID/channel/routing, runs identity-bound20MHz fine
acquisition, independently validates raw buffers and generates curves/result.json.
All analog settings are restored by the acquisition script. COMPLETE denotes
completed characterization; numerical manufacturing tolerances remain separate.

The same step is available to the existing sequential suite runner:

```
python suite.py collect --station STATION_JSON --channels 2 \
  --plan profiles/production-integrator.json --out NEW_SUITE_OUTPUT
```

The suite retains board/instrument leases across child processes and does not
accept CPLD-programming entry points. Reviewed production entry points are
allowlisted before any lease/hardware access; extending the plan requires adding
a reviewed non-programming adapter. Existing resident/acceptance/full-coverage
plans retain their previous supported tests and explicit NOT_RUN placeholders.
The new plan integrates the integrator step; it does not claim that unresolved
or placeholder tests in the broader board suite have been implemented.

## Station routing, not scan-code constants

The station file supplies board UID, CPU serial, instruments, fitted-channel
mapping and per-channel routes. For the present fixed cable, declare:

```
"routing_backend": "fixed",
"stimulated_channel": 2,
"channels": {
  "2": {
    "fixture_id": "CFD03",
    "integrator_connected": true,
    "integrator_dac_channels": [2, 3],
    "phase_lanes": [12, 13]
  }
}
```

This is a fragment, not a complete station configuration. The production wrapper
requires an explicit DAC pair; balance20's legacy default is retained only for
standalone diagnostic compatibility. ADC injection uses its existing separate
`dac_channels`/`analog_connected` route. Unconnected channels are NOT_RUN or fail
preflight, never silently measured through the currently connected channel.

With the present four CFD fixtures and one movable USB stimulus, the fitting and
USB declarations still follow real cable moves. When the extra DAC channels,
USB/analog muxes and12 CFDs are fitted, add their real routing driver and mapping
behind this interface, then iterate the existing per-board/per-channel jobs.
Unknown mux backends currently fail preflight: no fictitious selector writes or
manual interaction is hidden inside acquisition. This keeps measurement methods,
physical PM numbering, raw-data provenance and the offline report path stable.

Validation of this change is software/dry-run only. No board programming or fresh
measurement was performed; the underlying20MHz method has its separate PM2
450-buffer physical evidence.
