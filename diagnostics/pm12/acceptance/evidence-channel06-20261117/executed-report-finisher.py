from pathlib import Path
import json,shutil,hashlib,tarfile,datetime,subprocess,sys
r=Path('/home/codex-hil/fit-testing-publish');a=r/'diagnostics/pm12/acceptance';e=a/'evidence-channel06-20261117';report=a/'evidence-campaign-assembly-20261113';py=sys.executable
subprocess.run([py,str(a/'compare_adc_zero_inputs.py'),'--receipts',str(e/'adc-dc/campaign-result.json'),*[str(p)for p in sorted((a/'evidence-channel07-20261117/zero-input-figure-inputs').glob('*.json'))],'--out',str(e)],check=True)
for n in ['adc-zero-time.png','adc-zero-fft.png']:shutil.copy2(e/n,report/('ch06-'+n))
p=report/'channel06-followup.tex';p.write_text(p.read_text()+r'''
\subsection{Zero-input waveforms and FFT}
Selected zero-differential buffers for channels6--12 are compared below.
Capture origins are local, not synchronized. FFT amplitudes are one-sided RMS
code per bin at nominal80.1574MS/s, not spectral density or intrinsic aperture jitter.
\begin{center}\includegraphics[width=\linewidth]{ch06-adc-zero-time.png}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch06-adc-zero-fft.png}\end{center}
''')
summary=json.loads((e/'summary.json').read_text());dac=summary['final_state']['dac_prepared'];settings=f'DAC0/1={dac[0]:.4f}/{dac[1]:.4f}V,2/3={dac[2]:.4f}/{dac[3]:.4f}V'
prefix='''Latest channel6 follow-up (2026-11-17): ADC A/B transfer, adjacent-bit exercise,
**PASS** under the frozen channel8 contracts; integrator **INCOMPLETE**.
Both USB now6: DAC0/1→J8 ADC, DAC2/3→J6 integrator, verified by active/inhibited probes.
ADC6–12 available; integrator7–12 PASS,6 requires diagnosis;5 awaits USB.
[Channel6 raw data and common plots](LINK).

'''
for p,link in [(r/'README.md','diagnostics/pm12/acceptance/evidence-channel06-20261117/README.md'),(a/'README.md','evidence-channel06-20261117/README.md'),(a/'ACTIVE_CAMPAIGN.md','evidence-channel06-20261117/README.md'),(report/'README.md','../evidence-channel06-20261117/README.md')]:p.write_text(prefix.replace('LINK',link)+p.read_text())
state=f'''Final channel6 settings: {settings};6 amplifiers disabled, ADC bypass isolated.
All four monitor muxes inhibited/TCA0; other fitted channels isolated at preflight.
Kasli outputs/directions unchanged; leases released. No programming or clock changes.
SMU not accessed; preceding recorded state OFF/HIZ/0A/auto-on OFF.
Earlier dated states below are historical.

'''
p=a/'ACTIVE_CAMPAIGN.md';p.write_text(state+p.read_text());p=Path('/home/codex-hil/FIT_PM_FW_uPC/docs/pm12_current_hardware_state.md');p.write_text('## 2026-11-17 FINAL — channel6 ADC PASS; integrator INCOMPLETE; USB still6\n\n'+state+p.read_text())
p=Path('/srv/codex-hil-nvme/pm12-campaigns/active.json');d=json.loads(p.read_text());d['status']='Channel6 ADC/adjacent bits PASS; integrator INCOMPLETE (bankB template); next USB5';d['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();d['verified_connections']['verification_status']='PASS routing and ADC6; integrator qualification INCOMPLETE';p.write_text(json.dumps(d,indent=2)+'\n')
d=json.loads((e/'delta-provenance.json').read_text());actual={}
for archive in [a/d['base_archive'],e/'channel06-delta.tar.gz']:
 with tarfile.open(archive,'r|gz')as t:
  for m in t:
   if m.isfile():actual[m.name.removeprefix('campaign/')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
assert actual==d['current_files_sha256'];(e/'archive-validation.json').write_text(json.dumps({'pass':True,'files_verified':len(actual),'base_plus_delta_inventory_match':True},indent=2)+'\n')
subprocess.run(['/srv/codex-hil-nvme/pm12-acceptance-20261107/toolchain/tectonic','report.tex'],cwd=report,check=True)
info=subprocess.check_output(['pdfinfo',str(report/'report.pdf')],text=True);pages=next(l.split(':')[1].strip()for l in info.splitlines()if l.startswith('Pages:'))
for p in [r/'README.md',a/'README.md',report/'README.md']:p.write_text(p.read_text().replace('91-page',pages+'-page'))
p=e/'README.md';p.write_text(p.read_text()+f'\nFinal {settings}. [Current{pages}-page editable report](../evidence-campaign-assembly-20261113/report.pdf).\nBase+delta archive independently verified: {len(actual)} files.\n')
for directory in [e,report]:
 manifest={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(directory.rglob('*'))if p.is_file()and p.name!='files.sha256.json'and p.suffix not in ['.log','.aux','.out']};(directory/'files.sha256.json').write_text(json.dumps(manifest,indent=2)+'\n')
print('FINAL',pages,'pages',settings,flush=True)
