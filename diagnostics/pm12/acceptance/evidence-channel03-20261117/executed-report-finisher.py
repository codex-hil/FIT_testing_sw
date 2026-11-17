from pathlib import Path
import json,shutil,hashlib,subprocess,datetime
repo=Path('/home/codex-hil/fit-testing-publish');a=repo/'diagnostics/pm12/acceptance';e=a/'evidence-channel03-20261117';report=a/'evidence-campaign-assembly-20261113';d=json.loads((e/'summary.json').read_text());status=d['integrator'];park=d['final_park']
prefix=f'''Latest channel3 after confirmed USB move: ADC A/B transfer and adjacent bits **PASS**; integrator **{status}**.
Fresh active/inhibited probes verified the J8 route; earlier failed routing checks retained.
ADC3–12 now available; analog1–2 awaits USB moves. Integrator4/6 remain INCOMPLETE.
[Channel3 evidence and common plots](LINK).

'''
for p,link in [(repo/'README.md','diagnostics/pm12/acceptance/evidence-channel03-20261117/README.md'),(a/'README.md','evidence-channel03-20261117/README.md'),(a/'ACTIVE_CAMPAIGN.md','evidence-channel03-20261117/README.md'),(report/'README.md','../evidence-channel03-20261117/README.md')]:p.write_text(prefix.replace('LINK',link)+p.read_text())
state=f'''Final setup: CFD1–4 retained; both USB3, DAC01→J8 ADC,23→J6 integrator.
ADC3 PASS, adjacent bits PASS, integrator3 {status}. Earlier timing/monitor/internal-DAC1–4 unchanged.
All1–4 amps/bypass/monitor muxes inhibited; TCA0. External01={park[0]:.4f}/{park[1]:.4f}V,23={park[2]:.4f}/{park[3]:.4f}V.
No programming/clock/Kasli direction changes, no SMU access. Slot6 SPI stays held; leases released.
Analog1–2 awaits USB moves; integrators4/6 remain INCOMPLETE. Previous selected cases unchanged.
Earlier dated states below are historical.

'''
p=a/'ACTIVE_CAMPAIGN.md';p.write_text(state+p.read_text());p=Path('/home/codex-hil/FIT_PM_FW_uPC/docs/pm12_current_hardware_state.md');p.write_text('## FINAL channel3 after confirmed USB move\n\n'+state+p.read_text())
p=Path('/srv/codex-hil-nvme/pm12-campaigns/active.json');active=json.loads(p.read_text());active.update(analog_channel=3,status=f'ADC3/bits PASS; integrator3 {status}; next USB2',updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());active['verified_connections']={'channel':3,'direct_adc_input':'J8','direct_adc_dac_channels':[0,1],'integrator_input':'J6','integrator_dac_channels':[2,3],'verification_status':f'ADC route active/inhibited verified; ADC PASS, integrator {status}'};p.write_text(json.dumps(active,indent=2)+'\n')
subprocess.run(['/srv/codex-hil-nvme/pm12-acceptance-20261107/toolchain/tectonic','report.tex'],cwd=report,check=True)
info=subprocess.check_output(['pdfinfo',str(report/'report.pdf')],text=True);pages=next(l.split(':')[1].strip()for l in info.splitlines()if l.startswith('Pages:'))
for p in [repo/'README.md',a/'README.md',report/'README.md']:p.write_text(p.read_text().replace('104-page',pages+'-page'))
p=e/'README.md';p.write_text(p.read_text()+f'\n[Current{pages}-page editable report](../evidence-campaign-assembly-20261113/report.pdf).\n');shutil.copy2(Path(__file__),e/'executed-report-finisher.py')
for folder in [e,report]:
 manifest={str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(folder.rglob('*'))if p.is_file()and p.name!='files.sha256.json'and p.suffix not in ['.log','.aux','.out']};(folder/'files.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('FINAL',pages,'pages','integrator',status,flush=True)
