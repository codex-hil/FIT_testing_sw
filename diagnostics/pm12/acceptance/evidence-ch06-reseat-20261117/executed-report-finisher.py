from pathlib import Path
import json,datetime,subprocess,sys,shutil
repo=Path('/home/codex-hil/fit-testing-publish');a=repo/'diagnostics/pm12/acceptance';e=a/'evidence-ch06-reseat-20261117';report=a/'evidence-campaign-assembly-20261113'
assert json.loads((e/'archive-validation.json').read_text())['pass_']
prefix='''Latest channel6 integrator repeat after pressing CFD board (2026-11-17): **INCOMPLETE**.
Fresh13-point coarse sweep reproduces the bankB template ambiguity; fine/returns did not run.
No change to thresholds. Pressing did not remove the symptom; no hardware fault established.
ADC5–12 and integrators5,7–12 retain PASS; previous incomplete and diagnostics preserved.
[Repeat raw data and before/after comparison](LINK).

'''
for p,link in [(repo/'README.md','diagnostics/pm12/acceptance/evidence-ch06-reseat-20261117/README.md'),(a/'README.md','evidence-ch06-reseat-20261117/README.md'),(a/'ACTIVE_CAMPAIGN.md','evidence-ch06-reseat-20261117/README.md'),(report/'README.md','../evidence-ch06-reseat-20261117/README.md')]:p.write_text(prefix.replace('LINK',link)+p.read_text())
state='''Final after integrator6 repeat: DAC2/3→J6 channel6 confirmed; direct ADC USB route not freshly confirmed.
External DAC0/1=1/1V,2/3=1.024/2.048V. All5–8 amps/bypass/monitor outputs inhibited; TCA masks0.
Kasli outputs/directions unchanged, leases released. No programming/PLL changes or SMU access.
Latest integrator6 selected INCOMPLETE; previous attempts retained. Earlier dated states below historical.

'''
p=a/'ACTIVE_CAMPAIGN.md';p.write_text(state+p.read_text());p=Path('/home/codex-hil/FIT_PM_FW_uPC/docs/pm12_current_hardware_state.md');p.write_text('## 2026-11-17 FINAL — reseat repeat6 still INCOMPLETE\n\n'+state+p.read_text())
p=Path('/srv/codex-hil-nvme/pm12-campaigns/active.json');d=json.loads(p.read_text());d['analog_channel']=6;d['status']='Reseat-repeat01 integrator6 still INCOMPLETE: bankB template; ADC5–12 retained';d['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['verified_connections']={'channel':6,'integrator_dac_channels':[2,3],'integrator_input':'J6','verification_status':'Owner confirmed J6 for6; fresh power/build guards; response recorded','direct_ADC_USB_route':'Not freshly confirmed; no ADC repeat'};p.write_text(json.dumps(d,indent=2)+'\n')
subprocess.run(['/srv/codex-hil-nvme/pm12-acceptance-20261107/toolchain/tectonic','report.tex'],cwd=report,check=True)
info=subprocess.check_output(['pdfinfo',str(report/'report.pdf')],text=True);pages=next(l.split(':')[1].strip()for l in info.splitlines()if l.startswith('Pages:'))
for p in [repo/'README.md',a/'README.md',report/'README.md']:p.write_text(p.read_text().replace('97-page',pages+'-page'))
p=e/'README.md';p.write_text(p.read_text()+f'\n[Current{pages}-page editable report](../evidence-campaign-assembly-20261113/report.pdf).\n')
shutil.copy2(Path(__file__),e/'executed-report-finisher.py')
s=json.load(open('/tmp/pm12-pr4-before-reseat.json'))['body'];s=s.replace('97-page',pages+'-page').replace('Both USB are currently on5.','After the latest integrator6 repeat, DAC2/3→J6 channel6 is confirmed; direct ADC USB routing was not freshly confirmed.').replace('Final channel5 amplifiers enabled','Final fitted5–8 amplifiers disabled').replace('2/3=1.0268/2.0452V','2/3=1.024/2.048V');s+='\nIndependent integrator6 repeat after the owner pressed the CFD board again remained INCOMPLETE:13-point coarse acquisition completed, bankB template ambiguous near balance, fine/returns not run. Thresholds unchanged. Before/after raw traces and means retained; newest incomplete selected explicitly, original result and phase diagnostics immutable. No new ADC/TDC/phase/SMU scan, programming or PLL change. Pressing did not remove the observed symptom and does not establish its cause.\n';Path('/tmp/pm12-pr4-update-reseat.json').write_text(json.dumps({'body':s}))
print('FINAL',pages,'pages',flush=True)
