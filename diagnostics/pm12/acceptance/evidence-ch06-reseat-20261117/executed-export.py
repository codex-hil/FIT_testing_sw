from pathlib import Path
import sys,json,shutil,hashlib,tarfile,statistics,struct
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';sys.path[:0]=[str(P/'acceptance'),str(P/'ipbus_adc')]
from campaign import Campaign,read,write,digest
from adc_decode import decode
root=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261117');stage=root/'staging';bid='ch05-08-attempt001';work=root/'batches'/bid/'working/ch06/reseat-repeat01';native=work/'integrator';out=stage/'integrator-ch06-reseat-repeat01-incomplete';e=P/'acceptance/evidence-ch06-reseat-20261117';report=P/'acceptance/evidence-campaign-assembly-20261113'
c=Campaign(root)
with c.locked():old_selected=dict(c.data['selected'])
out.mkdir();shutil.copytree(native,out/'acquisition');shutil.copy2(stage/'ch06-reseat-repeat01-controller.py',out/'executed-controller.py');shutil.copy2(work/'operator-reseat.json',out/'operator-reseat.json')
r=read(native/'sweep01/status.json');record=read(stage/'integrator-ch06-incomplete/campaign-result.json');record.update(measured_utc=r['started_utc'],source_files=['executed-controller.py',*[str(p.relative_to(out))for p in sorted((out/'acquisition/sweep01/sources').glob('*.py'))]],reason='Repeat after pressing CFD6 reproduces bank-B template ambiguity near balance; stopped before fine scan and returns. Thresholds unchanged. No new phase scan.',limits='Fresh coarse acquisition complete; full integrator qualification remains INCOMPLETE. Does not establish a hardware fault.')
write(out/'campaign-result.json',record);write(out/'validation.json',dict(pass_=False,status='INCOMPLETE',physical_channel=6,reason=record['reason']));row=c.record(bid,out);c.select(row['id']);write(work/'selection-change.json',dict(previous=old_selected['integrator:6'],selected=row['id'],reason='Latest independent repeat after pressing CFD6; still INCOMPLETE; old attempt retained'))
with c.locked():assert all(c.data['selected'][k]==v for k,v in old_selected.items()if k!='integrator:6')
e.mkdir();shutil.copy2(Path(__file__),e/'executed-export.py')
for n in ['campaign-result.json','validation.json']:shutil.copy2(out/n,e/n)
for n in ['operator-reseat.json','selection-change.json']:shutil.copy2(work/n,e/n)
write(e/'coverage.json',{k:v for k,v in c.summary().items()if k!='records'})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True);comparison={}
for label,directory in [('Before pressing',work.parent/'integrator-corrected-usb/sweep01'),('After pressing',native/'sweep01')]:
 d=read(directory/'status.json');pt=min(d['points'],key=lambda p:abs(p['offset_V']));comparison[label]={}
 for bank,ax in enumerate(axes):
  caps=[v for v in pt['captures']if v['bank']==bank];cap=caps[0];samples,_=decode(struct.unpack('<4096H',(directory/cap['file']).read_bytes()),bank);ax.plot([i*1e9/80157400 for i in range(20)],samples[:20],'.-',label=label);ax.set(title='Integrator '+ 'AB'[bank],xlabel='Local capture time (ns)');ax.grid(alpha=.2);ax.legend();comparison[label]['AB'[bank]]=dict(raw_mean=statistics.mean(v['mean']for v in caps),sorted_phase_means=sorted(cap['phase_means']),clipped_fraction=statistics.mean(v['clipped_fraction']for v in caps))
axes[0].set_ylabel('ADC code');fig.suptitle('PM6 delta=0: before/after pressing; local capture origins not aligned');fig.tight_layout();fig.savefig(e/'before-after.png',dpi=180);plt.close(fig)
write(e/'comparison.json',comparison);final=read(work/'final-safe/status.json');write(e/'summary.json',dict(channel=6,status='INCOMPLETE',reason=record['reason'],comparison=comparison,final_dac=final['dac_prepared'],final_gpio=final['safe_gpio'],tca_final=final['tca_final']))
parent=P/'acceptance/evidence-group05-08-20261117/campaign-raw.tar.gz';baseline={}
with tarfile.open(parent,'r|gz')as t:
 for m in t:
  if m.isfile():baseline[m.name.removeprefix('campaign/')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
old=read(P/'acceptance/evidence-channel05-20261117/delta-provenance.json')['current_files_sha256'];current={str(p.relative_to(root)):digest(p)for p in sorted(root.rglob('*'))if p.is_file()}
for n,h in old.items():
 if '/results/'in n or '/working/'in n:assert current.get(n)==h,('Prior evidence changed',n)
changed=[n for n,h in current.items()if baseline.get(n)!=h]
with tarfile.open(e/'reseat-delta.tar.gz','w:gz')as t:
 for n in changed:t.add(root/n,arcname='campaign/'+n,recursive=False)
write(e/'delta-provenance.json',dict(base_archive='evidence-group05-08-20261117/campaign-raw.tar.gz',base_sha256=digest(parent),current_files_sha256=current,changed_files=changed,instructions='Original base plus this cumulative delta in a NEW directory; never overwrite live data.'))
actual={}
for archive in [parent,e/'reseat-delta.tar.gz']:
 with tarfile.open(archive,'r|gz')as t:
  for m in t:
   if m.isfile():actual[m.name.removeprefix('campaign/')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
assert actual==current;write(e/'archive-validation.json',dict(pass_=True,files_verified=len(actual)))
(e/'README.md').write_text('''# Channel6 integrator repeat after pressing CFD board — 17 November2026

User pressed CFD6 and confirmed DAC2/3→J6 channel6. Independent13-point coarse
acquisition completed with fresh MCU1803/FPGAff2f746c/power guards. The controller
again stopped at bankB: no unambiguous integration/reset template near balance.
Fine and independent return scans did not run. **INCOMPLETE**, unchanged thresholds.
A shows a sign reversal but no complete fine/return qualification is claimed.
Pressing the board did not remove this measured symptom; no hardware defect or
specific contact failure is established. Raw before/after buffers retained.

Latest repeat explicitly selected, previous incomplete and all phase diagnostics
preserved. No other selected cases changed. ADC5–12 PASS and integrators5,7–12 PASS
remain valid. No ADC/TDC/phase/SMU repeat, programming, PLL change or Kasli release.
Final6 amplifiers disabled, ADC bypass isolated, all monitors inhibited/TCA0;
external DAC0/1=1/1V,2/3=1.024/2.048V. Leases released. DAC-A remains established0.

Reproduce archive: original group05-08 campaign-raw.tar.gz plus reseat-delta.tar.gz
in a NEW directory. Complete inventory verified; do not overwrite live data.
''')
shutil.copy2(e/'before-after.png',report/'reseat06-before-after.png')
tex=r'''\clearpage
\section{Channel6 integrator repeat after pressing the CFD board: INCOMPLETE}
The owner pressed CFD6 and confirmed DAC2/3 connected to J6 on physical6.
A fresh independent acquisition passed MCU1803, FPGA ff2f746c and power guards.
No programming, PLL change, Kasli output release or SMU access. DAC-A remained0.
The original gate mode and validation thresholds were unchanged.
The13-point coarse acquisition completed, but the controller again found no
unambiguous bank-B integration/reset template near balance. Fine and independent
return qualification did not run. A shows a sign reversal, but neither bank is
claimed to have completed the full fine/return protocol in this attempt.
\subsection{Raw comparison with the preceding attempt}
Below are unaligned raw captures at the same commanded differential offset0.
Pressing did not remove the observed ambiguity. This does not determine whether
the cause is hardware, sampling position or waveform-based phase assignment.
No particular intermittent contact or hardware defect has been established.
\begin{center}\includegraphics[width=\linewidth]{reseat06-before-after.png}\end{center}
\begin{center}\begin{tabular}{lrr}\toprule
Attempt & A mean(code) & B mean(code)\\\midrule
'''
for label,d in comparison.items():tex+=f"{label} & {d['A']['raw_mean']:.3f} & {d['B']['raw_mean']:.3f} \\\\\n"
tex+=r'''\bottomrule\end{tabular}\end{center}
The latest INCOMPLETE repeat was explicitly selected; the original incomplete
record and phase diagnostics remain immutable. Every other selected result ID
is unchanged. ADC5--12 and integrators5,7--12 retain their previous PASS results.
Final channel6 amplifiers disabled, direct bypass isolated, monitors inhibited,
TCA masks zero. External DAC channels0/1 are1/1V, channels2/3 are1.024/2.048V.
Leases released. Source and raw-data hashes are retained with the repeat.
'''
(report/'ch06-reseat-followup.tex').write_text(tex);p=report/'report.tex';p.write_text(p.read_text().replace('\\input{channel05-followup.tex}','\\input{ch06-reseat-followup.tex}\n\\input{channel05-followup.tex}'))
print(json.dumps(comparison),flush=True)
