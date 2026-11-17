# Optional integrator reset diagnostic — excluded from production

Owner correction: production scripts must not program CPLDs or switch gate
images automatically. This procedure changes CPLD gateware and is therefore
**diagnostic only**. It is absent from the default production campaign.
Use the separate campaign-reset-diagnostic.json protocol when explicitly
performing this experiment. Existing sealed protocols/evidence are retained.

Version 1 holds **A and B separately** in reset and keeps the other gate running.
It measures all four reset branches independently and records normal A/B amplitudes before and after the
reset experiment at the fixed base DAC2/3=1.024/2.048 V. This creates paired
observations for resistance-versus-waveform-amplitude comparison. Do not mix
these amplitudes with measurements at a different differential offset/common
shift, gate configuration or clock epoch.

```
# Use the hardware Python for the orchestrator; scientific Python is separate.
python diagnostic_integrator_reset.py --root CAMPAIGN --batch FITTING_ID --channel 2 \
  --vectors-root /srv/codex-hil-nvme/pm12-reset-standard-vectors-20261117 --out NEW_OUTPUT
```

The orchestrator checks the fitted group, fresh identity and protocol before
hardware access. It invokes leased acquisition, offline analysis, independent
raw validation and immutable campaign registration. The station declaration
must name the actual `stimulated_channel` and set that channel's
`integrator_connected=true`; there is no default assertion that all four USB
stimuli are connected. Board DNA and configured MCU serial are rechecked live.
The current acquisition supports the resident FPGA build ff2f746c; other builds
require explicit qualification, not merely replacing its expected signature.

Channel-specific programming vectors have a manifest binding them to one CPLD,
the qualified normal/reset JEDEC hashes and their native Tcl checksums. The
runner verifies the current normal image before changes, snapshots all CPLDs,
programs only the selected channel and verifies all unaffected arrays. It always
attempts full restoration, then compares all 984 rows and verifies the normal
image. Reconfiguration/measurement errors are retained and prevent a result.
Kasli outputs/directions and MCU/FPGA/PLL profiles remain unchanged.

Vector preparation uses the qualified JEDECs in the reset experiment archive.
On Optiplex, `prepare_reset_vectors.py prepare --bank A_OR_B --source JEDEC_DIR --out NEW_DIR
--remote REMOTE_JOB_DIR` emits 36 iMPACT command files and export.sh. Send NEW_DIR
to the matching Dell ISE workspace, execute export.sh with dell-build run ise,
fetch explicitly, then run `prepare_reset_vectors.py finalize --root NEW_DIR`.
The finalizer strictly converts SVF and verifies that all non-BYPASS CPLD
instructions target their declared physical channel. No hardware is touched by
preparation/export/finalization. The preserved example artifacts are under
`/srv/codex-hil-nvme/pm12-reset-standard-vectors-20261117/{A,B}`; only channel2 is physically
validated so far. Vectors for the other channels are generated/checked offline.

For each input P/N: eleven offsets -100..+100 mV, 20 mV step, other input fixed;
three captures per ADC bank. Both-bank normal controls, reset baseline and two
returns give 162 raw buffers per held bank, 324 for the full channel. The independently validated held-bank fit excludes any
clipped or invalid data; an incomplete set is not accepted as complete.
R_eff=abs(slope_code_per_commanded_V)*430/2000 ohm uses nominal input R and ADC
sensitivity. Store slope and assumptions alongside ohms. No calibrated absolute
R_ON or individual-transistor tolerance claim is made.

`PASS` here means the characterization completed, raw data validate, both branch
fits exist and original hardware state was restored. **Numerical resistance
acceptance limits have not been defined.** The receipt states that distinction;
report these values as measured characterization, not resistance tolerance PASS.
Physical PM2 verification confirms valid ADC strobes with either A or B held
in reset; both variants restore the original CPLD image.

Reporting: use one channel-row table with R_A,P, R_A,N, R_B,P, R_B,N and normal amplitudes A/B,
plus shared transfer/scatter figures as useful. Keep raw captures/provenance
outside the concise production PDF. Missing channels remain missing. Correlation
requires several matched channels, not a claim from the present channel2 alone.

Generate the paired twelve-channel CSV and four scatter panels offline with:

```
python plot_reset_correlation.py --root CAMPAIGN --out NEW_CORRELATION_DIR
```

Only selected, integrity-checked results enter the plots. Each bank's amplitude
comes from its own immediately preceding normal-gate control. No correlation
coefficient is inferred automatically from sparse coverage.

The complete orchestrator was physically repeated on PM2:324 buffers, immutable
campaign registration and correlation export passed.
[End-to-end evidence](../cfd_simulator/evidence-reset-standard-20261117/README.md).
