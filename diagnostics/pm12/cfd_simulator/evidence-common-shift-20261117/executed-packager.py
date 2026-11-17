from pathlib import Path
import json,hashlib,shutil,tarfile,datetime
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';data=Path('/srv/codex-hil-nvme/pm12-integrator-common-shift-20261117');run=data/'run03-ch02-phase32768';summary=json.loads((run/'analysis/summary.json').read_text());plan=json.loads((run/'plan.json').read_text());discovery=json.loads((data/'stimulus-discovery/discovery.json').read_text());phase=json.loads((data/'adc-phase-ch02/phase-probe.json').read_text())
assert plan['acquisition_complete'] and not plan.get('error') and not plan.get('cleanup_error');assert plan['adc_phase_code']==32768 and plan['adc_phase_restored']==0;assert set(plan['tca_final'].values())=={0};assert discovery['stimulus_candidates']==[2];assert 32768 in phase['valid_codes'] and phase['restored_phase_code']==0
assert len(summary['rows'])==50 and len(summary['raw_sha256'])==200
for b in 'AB':assert abs(summary['control_response'][b]['delta_step_mean_change_code'])>10 and abs(summary['control_response'][b]['baseline_return_mean_change_code'])<5
out=P/'cfd_simulator/evidence-common-shift-20261117';out.mkdir();shutil.copy2(Path(__file__),out/'executed-packager.py')
for src,dest in [(run/'analysis/common-shift.png','common-shift.png'),(run/'analysis/common-shift.pdf','common-shift.pdf'),(run/'analysis/common-shift.csv','common-shift.csv'),(run/'analysis/summary.json','analysis.json'),(run/'plan.json','acquisition-plan.json'),(data/'stimulus-discovery/discovery.json','stimulus-discovery.json'),(data/'adc-phase-ch02/phase-probe.json','adc-phase-probe.json')]:shutil.copy2(src,out/dest)
manifest={str(p.relative_to(data)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(data.rglob('*'))if p.is_file()}
with tarfile.open(out/'experiment-raw.tar.gz','w:gz')as t:t.add(data,arcname='experiment')
actual={}
with tarfile.open(out/'experiment-raw.tar.gz','r|gz')as t:
 for m in t:
  if m.isfile():actual[m.name.removeprefix('experiment/')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
assert actual==manifest
(out/'raw-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(out/'validation.json').write_text(json.dumps(dict(status='DIAGNOSTIC_COMPLETE',physical_channel=2,stimulus_response_confirmed=True,raw_buffers_validated=200,raw_files_verified=len(actual),phase_code_during_measurement=32768,phase_code_restored=0,qualification_results_changed=False,limits='Differential ADC observables only; physical DAC voltages and individual output-to-ground saturation not measured'),indent=2)+'\n')
rows=summary['rows'];selected=[]
for shift in [-.1,0,.1]:
 item={'common_shift_V':shift,'banks':{}}
 for bank in 'AB':
  r=next(v for v in rows if v['bank']==bank and v['stage']=='sweep'and abs(v['common_shift_V']-shift)<1e-9);item['banks'][bank]={k:r[k]for k in ['phase_amplitude_code','mean_code','clip_percent']}
 selected.append(item)
(out/'key-points.json').write_text(json.dumps(selected,indent=2)+'\n')
(out/'README.md').write_text('''# Fixed differential offset, common-shift experiment — 17 November2026

**Diagnostic only; no production qualification or selected campaign result changed.**
The owner requested holding a20mV relative differential offset and moving both
input setpoints together over±100mV. The confirmed stimulus is J6 on physical PM2.

## Successful acquisition

DAC2=1.034V+c, DAC3=2.038V+c, c=-0.100..+0.100V in10mV steps.
Commanded DAC2−DAC3=-1.004V throughout;20mV refers to offset from1.024/2.048V.
There are21sweep positions plus baseline/delta controls before and after:
25points×2banks×4captures=200 raw buffers independently decoded and checked.
DAC-A phase code32768 was held during acquisition to obtain coherent ADC B data.
Afterwards DAC-A restored0, DAC23 parked1.024/2.048V, amps/bypass/monitor inhibited,
TCA0. Kasli outputs/directions, FPGA/MCU/CPLD/flash/PLL profiles and other DAC
channels unchanged. No SMU access, no new build and no report/PDF regeneration.

|Common shift|A four-phase amplitude(code)|B four-phase amplitude(code)|A/B ADC rail samples|
|---|---:|---:|---|
|-100mV|172.99|79.13|25.02% /43.89%|
|0mV|154.82|70.07|0% /0%|
|+100mV|193.22|97.69|0% /0%|

Amplitude means max−min of four phase means and includes the reset waveform.
Negative-end clipped amplitudes are cropped observations, not true unclipped amplitudes.
The0→20mV delta controls changed mean A/B by−39.37/−37.21codes, with baseline
returns−0.13/+0.33codes. Thus the successful run has a demonstrated stimulus response.
Both shifted setpoints materially change the differential waveform. This does not
identify a physical cause or prove individual-amplifier saturation: actual DAC pin
voltages and the two single-ended integrator outputs were not measured.
The absence of ADC clipping also does not exclude individual output saturation.

## Route and sampling diagnostics retained separately

- First full scan on3 was coherent but had no stimulus control response; it is
  **not** evidence of common-mode insensitivity.
- Automated0→20mV→0 trials with one fitted channel enabled at a time located
  the J6 stimulus uniquely on2. Invalid ADC captures were retained and excluded
  from response calculations, not decoded with weakened checks.
- Initial mini-scan on2 stopped on ADC B two-sample coherency errors.
- Phase probe: code0 gave3/6 valid buffers,16384/32768/49152/65535 gave6/6.
  Code32768 was then used for the full scan and restored0 afterwards. The issue
  at0 is not silently marked repaired or production-qualified.
- An unsuccessful controller start from a missing import path performed no scan;
  its error/cleanup record is retained. The corrected executable is included.

All attempts and exact executed controller/native/decoder source snapshots are
in experiment-raw.tar.gz. raw-manifest.json and validation.json document full
archive readback. common-shift.csv/json/PNG/PDF are generated from successful
run03-ch02-phase32768 only. This is laboratory diagnostic evidence; engineering
history belongs outside the production PDF.

## Reproduce on this identified PM12 bench

The helpers enforce MCU1803/buildff2f746c, the established board/instrument leases,
external DAC0..3.3V bounds, and output inhibition. Identify current physical wiring
first; do not run fitted-channel discovery against absent fixtures.

```
# Hardware Python: /home/codex-hil/kasli-diot-bringup/.venv/bin/python
# Offline Python: /srv/codex-hil-nvme/tool-venvs/fit-measurements/bin/python
python discover_integrator_stimulus.py --connected 1 2 3 4 --out NEW_DISCOVERY
python probe_integrator_adc_phase.py --afe 2 --out NEW_PHASE_PROBE
python integrator_common_mode.py --afe 2 --adc-phase-code 32768 --out NEW_RUN
python plot_integrator_common_mode.py --root NEW_RUN
```

The current native acquisition module and existing selected qualification methods
were not edited. Plan-only checks verified25points, fixed differential voltage,
bounds, quantization-grid validation and rejection of invalid arguments.
''')
active=Path('/srv/codex-hil-nvme/pm12-campaigns/active.json');d=json.loads(active.read_text());d.update(analog_channel=2,status='J6 DAC23 discovered on2; common-shift diagnostic complete at temporary phase32768, restored0. No qualification change. J8 DAC01 current route not checked.',updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());d['verified_connections']={'integrator_channel':2,'integrator_input':'J6','integrator_dac_channels':[2,3],'verification_status':'Reversible delta response uniquely detected on2','direct_ADC_current_route':'Unknown/not rechecked; last qualified on3'};active.write_text(json.dumps(d,indent=2)+'\n')
cfgpath=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261117/batches/ch01-04-attempt001/station.json');cfg=json.loads(cfgpath.read_text());cfg['stimulated_channel']=2
for ch,v in cfg['channels'].items():v['analog_connected']=False;v['integrator_connected']=ch=='2'
cfg['board_test_note']='J6 DAC23 confirmed on2 by reversible response; current J8 DAC01 route not checked. CM experiment at DAC-A2=32768 restored0. No production qualification change.';cfgpath.write_text(json.dumps(cfg,indent=2)+'\n')
text='''Latest diagnostic: J6 DAC23 is on physical2, found by reversible delta response.
J8 DAC01 route is currently unknown (last qualified ADC3). Common sweep2 completed
at DAC-A2=32768 for coherent B capture; restored0 afterwards. At0, ADC B2 needs
sampling-coherency attention before qualification. DAC23=1.024/2.048V; fitted amps,
bypass and monitor muxes inhibited/TCA0. Kasli directions held, leases released.
No selected qualification changes, no report regeneration. Production ADC/integrator1–2
coverage remains pending; integrators3/4/6 retain INCOMPLETE.
[Common-shift diagnostic](../cfd_simulator/evidence-common-shift-20261117/README.md).

'''
p=P/'acceptance/ACTIVE_CAMPAIGN.md';p.write_text(text+p.read_text());p=Path('/home/codex-hil/FIT_PM_FW_uPC/docs/pm12_current_hardware_state.md');p.write_text('## Integrator common-shift diagnostic, J6 discovered on2\n\n'+text+p.read_text())
files={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(out.rglob('*'))if p.is_file()and p.name!='files.sha256.json'};(out/'files.sha256.json').write_text(json.dumps(files,indent=2)+'\n');print('PACKAGED',out,'raw files',len(actual),flush=True)
