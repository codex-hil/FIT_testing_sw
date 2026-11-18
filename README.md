Latest ADC2 timing diagnostic (2026-11-18):144buffers retained. At phase16384/32768, pair ending at STR rise has0disagreements/98112pairs; old earlier pair still fails. Phase0 has no shared clean window. Evidence favors timing/window selection; no hardware fault or production PASS established. Baseline restored, no programming.
[Timing diagnostic](diagnostics/pm12/acceptance/evidence-adc02-timing-20261118/README.md).

Latest channel2 ADC (2026-11-18): INCOMPLETE. Correct J8 response verified; full acquisitions at phase0/32768/16384 stop on two-sample stability. No ADC2 PASS or bit-test acceptance, no qualification changes. Raw failures retained; final baseline restored, no CPLD programming.
[Channel2 evidence](diagnostics/pm12/acceptance/evidence-channel02-20261118/README.md).

Latest channel1 (2026-11-18): ADC A/B and all12 data bits PASS, selected under the unchanged ADC protocol. Integrator A/B functional balance confirmed at normal20MHz with100µV steps and independent returns; separately labelled diagnostic method. USB remains1; ADC2 pending. No CPLD programming.
[Channel1 evidence](diagnostics/pm12/acceptance/evidence-channel01-20261118/README.md).

Latest channel3 after confirmed USB move: ADC A/B transfer and adjacent bits **PASS**; integrator **INCOMPLETE**.
Fresh active/inhibited probes verified the J8 route; earlier failed routing checks retained.
ADC3–12 now available; analog1–2 awaits USB moves. Integrator4/6 remain INCOMPLETE.
[Channel3 evidence and common plots](diagnostics/pm12/acceptance/evidence-channel03-20261117/README.md).

Latest fitting1–4 (2026-11-17): TDC/phase/monitor/internal-DAC results in the linked table.
Channel4 ADC/bits: **PASS/PASS**; integrator: **INCOMPLETE**. USB remains4, analog1–3 pending.
Slot7 ports0/1/2/3→PM4/3/2/1 verified. Integrator6 remains INCOMPLETE.
[Group1–4 evidence and common plots](diagnostics/pm12/acceptance/evidence-group01-04-20261117/README.md).

Latest channel6 integrator repeat after pressing CFD board (2026-11-17): **INCOMPLETE**.
Fresh13-point coarse sweep reproduces the bankB template ambiguity; fine/returns did not run.
No change to thresholds. Pressing did not remove the symptom; no hardware fault established.
ADC5–12 and integrators5,7–12 retain PASS; previous incomplete and diagnostics preserved.
[Repeat raw data and before/after comparison](diagnostics/pm12/acceptance/evidence-ch06-reseat-20261117/README.md).

Latest channel5 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
and integrator balance/sign/revisits **PASS**, matching the frozen channel8 contracts.
Both USB now5: DAC0/1→J8 ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
ADC5–12 complete; integrator5 and7–12 PASS,6 remains INCOMPLETE.
[Channel5 raw data and common plots](diagnostics/pm12/acceptance/evidence-channel05-20261117/README.md).

Latest channel6 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
**PASS** under the frozen channel8 contracts; integrator **INCOMPLETE**.
Both USB now6: DAC0/1→J8 ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
ADC6–12 available; integrator7–12 PASS,6 requires diagnosis;5 awaits USB.
[Channel6 raw data and common plots](diagnostics/pm12/acceptance/evidence-channel06-20261117/README.md).

Latest channel7 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
and integrator balance/sign/revisits **PASS**, matching the frozen channel8 contracts.
Both USB now7: DAC0/1→J8 direct ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
Analog7–12 observations available;5–6 await USB moves. Fitting5–8 timing/monitor/internal-DAC PASS unchanged.
[Channel7 raw data and common plots](diagnostics/pm12/acceptance/evidence-channel07-20261117/README.md).

Latest PM12 results (2026-11-17): TDC, gate-phase, monitor voltages and internal
DAC B/C/D tests on5–8 PASS; ADC A/B and integrators8 PASS after verified USB correction.
Both USB remain on8; ADC/integrators5–7 await their cable moves.
[107-page editable acceptance report](diagnostics/pm12/acceptance/evidence-campaign-assembly-20261113/report.pdf),
[group raw/normalized evidence](diagnostics/pm12/acceptance/evidence-group05-08-20261117/README.md).
Current diagnostic SRAM ff2f746c; original MCU and external PLL profile preserved.

# FIT hardware testing and characterization

Software, diagnostic gateware, measurement procedures and reports for testing
FIT front-end electronics, currently focused on **PM12 boards and CFD simulator
modules**. The bench combines PM12, Kasli-DIOT with DIO-LVDS interfaces,
programmable stimuli and laboratory instruments.

The current workflow uses dedicated diagnostic gateware, Python control scripts,
IPbus/Ethernet and MCU UART access. **ARTIQ is not the entry point for the current
PM12 acceptance workflow.** The original ARTIQ PMT simulator remains available as
[a historical project](docs/legacy-pmt-sim-artiq.md).

## Tests and measurements

| Area | Procedures and tools |
|---|---|
| JTAG and CPLD–FPGA connections | [Discovery, boundary scan and schematic comparison](diagnostics/pm12/README.md) for 168 link signals |
| MCU and board control | [UART, CPU–FPGA communication, sensors and power observations](diagnostics/pm12/mcu/README.md) |
| Integrated digital paths | [HDMI, ADC and TDC test runner](diagnostics/pm12/system/README.md) |
| ADC acquisition | [IPbus acquisition](diagnostics/pm12/ipbus_adc/README.md), [DC response](diagnostics/pm12/cfd_simulator/ADC_DC_SCAN.md) and [data-line checks](diagnostics/pm12/cfd_simulator/ADC_DATA_LINES.md) |
| TDC and timing | [Live TDC diagnostics](diagnostics/pm12/tdc_live120/README.md), [CFD phase scans](diagnostics/pm12/cfd_simulator/PHASE_SCAN.md) and [four-channel repair verification](diagnostics/pm12/tdc_live120/FOUR_CFD_REPAIR_REPEAT.md) |
| Integrators | [Channel 12 balance, signed ramp scans and LaTeX report](diagnostics/pm12/cfd_simulator/INTEGRATOR_SCAN.md) |
| CFD DAC outputs | [Shared-mux voltage scans with Keysight SMU2](diagnostics/pm12/cfd_simulator/SMU_DAC_SCAN.md) |
| Board dossiers | [Sequential acceptance runner, channel batches and LaTeX/PDF reports](diagnostics/pm12/acceptance/README.md) |

Each procedure describes its required image, wiring, instrument configuration,
restoration behavior and qualification status. The acquisition scripts are not
interchangeable across arbitrary FPGA images or bench connections.

## Collect data, generate chapters, assemble the dossier

For the current four-CFD bench, use the [twelve-channel campaign workflow](diagnostics/pm12/acceptance/CAMPAIGN.md): fittings1–4,5–8,9–12, explicit CFD/cable mapping, retained repeats and one combined editable LaTeX report.

1. Identify the board and instruments, configure the station profile and verify
   wiring. Acquire the shared board/instrument leases before hardware access.
2. Run the selected hardware procedures and retain raw samples, command logs,
   identities, configuration hashes and explicit validation results. CFD channels
   can be collected in separate batches.
3. Generate figures and an editable LaTeX chapter from the chosen data batches.
   Plot channels together to expose differences. Rendering is offline and does
   not open hardware connections.
4. Assemble the chapters, setup diagrams, device inventory and photographs into
   the board dossier, then compile the PDF.

Start with the [acceptance workflow](diagnostics/pm12/acceptance/README.md).
The [LaTeX template](diagnostics/pm12/acceptance/templates/report.tex) and
[parameterized bench diagram](diagnostics/pm12/acceptance/BENCH_CONFIGURATION.md)
can be edited independently of acquisition. The
[SMU DAC procedure](diagnostics/pm12/cfd_simulator/SMU_DAC_SCAN.md) also provides
standalone acquisition, plotting and LaTeX generation commands.

## Environments and tools

- **Acquisition:** Linux/Python plus the dependencies specified by each procedure.
  The laboratory setup uses the existing pinned Kasli environment and instrument
  drivers; station paths, cable identities and LAN addresses must be configured
  for the actual bench. This repository is not a self-contained station installer.
- **Offline reports:** NumPy and Matplotlib
  ([qualified requirements](diagnostics/pm12/acceptance/requirements-report.txt)),
  plus Tectonic for the validated PDF build. The report generator also supports
  `pdflatex`; see its documented validation limits.
- **Gateware builds:** use the toolchain required by the selected design.
  PM12 Kintex-7 diagnostics were validated with Vivado 2025.2. Heavy laboratory
  builds run on Dell; JTAG/UART and physical tests remain on the station owning
  the attached board. Building is separate from collecting data with an already
  qualified image.
- **Historical ARTIQ project:** its Nix/Vivado 2022.2 instructions are documented
  [separately](docs/legacy-pmt-sim-artiq.md), not as global tester requirements.

No firmware flashing or hardware operation is needed to regenerate reports from
archived measurements.

## Example evidence and reports

- **Integrator balance, channel 12:** [PDF](diagnostics/pm12/cfd_simulator/evidence-integrator-20261113/report.pdf), [procedure and results](diagnostics/pm12/cfd_simulator/INTEGRATOR_SCAN.md). Signed A/B ramp response and revisited zero crossings; 688 raw ADC buffers.

- **CFD DAC outputs, channels 10/8/6:** [PDF](diagnostics/pm12/cfd_simulator/evidence-smu-dac-20261110/report.pdf), [editable LaTeX](diagnostics/pm12/cfd_simulator/evidence-smu-dac-20261110/report.tex), [raw CSV](diagnostics/pm12/cfd_simulator/evidence-smu-dac-20261110/samples.csv). Nine transfer curves, 2727 samples; acquisition/status/restoration checks passed.
- **Board dossier and wiring tables:** [compact specimen](diagnostics/pm12/acceptance/evidence-english-setup-20261108/report.pdf).
- **ADC timing investigation:** [diagnosis and controlled repeats](diagnostics/pm12/acceptance/ADC_STROBE_DEBUG.md), with original rejected evidence retained.
- **CFD gate/TDC repair repeat:** [measurements and interpretation](diagnostics/pm12/tdc_live120/FOUR_CFD_REPAIR_REPEAT.md).

A PASS applies to the selected procedure, configuration and measured channels.
Archived examples do not certify other boards or unmeasured channels. Functional
transfer scans do not imply exhaustive INL/DNL, calibrated jitter or complete
board acceptance. Read each validation record alongside its plots and report.

2026-11-13: [four-CFD campaign, first measured channel12](diagnostics/pm12/acceptance/evidence-campaign-ch12-20261113/README.md), with editable LaTeX, raw buffers and explicit twelve-channel coverage.

[2026-11-13: SMU DAC transfer scans on physical channels9–12, with combined27-page LaTeX report](diagnostics/pm12/acceptance/evidence-campaign-smu-20261113/README.md).

[2026-11-13: channel11 ADC A/B and integrator balance, compared with channel12](diagnostics/pm12/acceptance/evidence-campaign-ch11-20261113/README.md).

[2026-11-13: channel10 ADC/integrator measurements and common plots for10–12](diagnostics/pm12/acceptance/evidence-campaign-ch10-20261113/README.md).

[2026-11-13: TDC and both gate-phase responses on9–12;39-page cumulative report](diagnostics/pm12/acceptance/evidence-campaign-timing-20261113/README.md).

Latest [assembly verification report](diagnostics/pm12/acceptance/evidence-campaign-assembly-20261113/README.md): two open findings (CFD monitor divider at11 and HDMI shared-SPI reset); this board is not unconditionally released.
