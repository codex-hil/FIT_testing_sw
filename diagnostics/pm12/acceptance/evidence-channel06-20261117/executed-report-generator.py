from pathlib import Path
import sys,json,hashlib,tarfile,shutil,struct,statistics
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';sys.path[:0]=[str(P/'acceptance'),str(P/'cfd_simulator'),str(P/'ipbus_adc')]
from campaign import Campaign,read,write,digest
from campaign_adapters import adc,context
from adc_decode import decode
from integrator_analysis import integration_pair
root=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261117');stage=root/'staging';bid='ch05-08-attempt001';work=root/'batches'/bid/'working/ch06';e=P/'acceptance/evidence-channel06-20261117';e.mkdir();shutil.copy2(Path(__file__),e/'executed-report-generator.py')
c=Campaign(root)
with c.locked():previous=dict(c.data['selected'])
for kind in ['adc-dc','adc-lines']:
 out=stage/(kind+'-ch06');adc(work/'adc-corrected-usb',out,root,bid,kind);assert read(out/'campaign-result.json')['status']=='PASS';c.record(bid,out);dest=e/kind;dest.mkdir()
 for n in ['campaign-result.json','validation.json']:shutil.copy2(out/n,dest/n)
# Explicit incomplete integrator record; preserve the attempted method and all raw diagnostics.
out=stage/'integrator-ch06-incomplete';out.mkdir();shutil.copytree(work/'integrator-corrected-usb',out/'acquisition');shutil.copytree(work/'phase-diagnostic',out/'phase-diagnostic');shutil.copy2(stage/'integrator-corrected-usb06-controller.py',out/'executed-controller.py')
r=read(work/'integrator-corrected-usb/sweep01/status.json');uid,fixture,hw=context(root,bid,6,r['fpga'][2]);prior=read(P/'acceptance/evidence-channel07-20261117/integrator/campaign-result.json');record=dict(mode='LIVE',board_uid=uid,test='integrator',channel=6,fixture_id=fixture,measured_utc=r['started_utc'],status='INCOMPLETE',protocol=prior['protocol'],source_files=['executed-controller.py',*[str(p.relative_to(out))for p in sorted((out/'acquisition/sweep01/sources').glob('*.py'))]],connections=dict(usb_input='J6',stimulus_channel=6,dac_channels=[2,3]),metrics=[],curves=[],limits='No qualified bank-B signed crossing; coarse acquisition complete, fine and returns not run. Waveform ambiguity is not proof of hardware defect.',reason='Bank B lacks an unambiguous integration/reset template near zero; four DAC-A phase diagnostics did not resolve it. Threshold unchanged; DAC-A restored0.')
write(out/'campaign-result.json',record);write(out/'validation.json',dict(pass_=False,physical_channel=6,status='INCOMPLETE',reason=record['reason']));c.record(bid,out);dest=e/'integrator';dest.mkdir()
for n in ['campaign-result.json','validation.json']:shutil.copy2(out/n,dest/n)
with c.locked():assert all(c.data['selected'][k]==v for k,v in previous.items())
write(e/'coverage.json',{k:v for k,v in c.summary().items()if k!='records'})
# Diagnostic figures: no extrapolated/qualified balance for B.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4))
for bank,ax in enumerate(axes):
 for requested in [-.02,0,.02]:
  pt=min(r['points'],key=lambda p:abs(p['offset_V']-requested));cap=next(v for v in pt['captures']if v['bank']==bank);samples,_=decode(struct.unpack('<4096H',(work/'integrator-corrected-usb/sweep01'/cap['file']).read_bytes()),bank);ax.plot([i*1e9/80157400 for i in range(20)],samples[:20],'.-',label=f"delta={pt['offset_V']*1000:.0f} mV")
 ax.set(title='Integrator '+ 'AB'[bank]+' — diagnostic only',xlabel='Local capture time (ns)',ylabel='ADC code');ax.grid(alpha=.2);ax.legend()
fig.suptitle('PM6: unaligned raw waveforms; bank B balance remains unqualified');fig.tight_layout();fig.savefig(e/'integrator-diagnostic.png',dpi=180);plt.close(fig)
# Shared ADC overlays6--12, each from its own selected receipt.
items={6:read(stage/'adc-dc-ch06/campaign-result.json')}
for p in (P/'acceptance/evidence-channel07-20261117/zero-input-figure-inputs').glob('*.json'):
 d=read(p);items[d['channel']]=d
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ch,d in sorted(items.items()):
 for ax,b in zip(axes,'AB'):
  q=next(v for v in d['curves']if v['name']=='adc_response'and v['bank']==b);ax.plot(q['x'],q['y'],label=f'PM{ch}');ax.set(title='ADC '+b,xlabel='Commanded differential voltage (V)');ax.grid(alpha=.2);ax.legend(fontsize=8,ncol=2)
axes[0].set_ylabel('ADC code');fig.tight_layout();fig.savefig(e/'adc-dc-06-12.png',dpi=180);plt.close(fig)
write(e/'summary.json',dict(channel=6,ADC='PASS',integrator='INCOMPLETE',adc=items[6]['metrics'],reason=record['reason'],final_state=read(work/'final-state.json')))
# Base+delta archive: original base plus this cumulative delta, independently check prior immutable files.
parent=P/'acceptance/evidence-group05-08-20261117/campaign-raw.tar.gz';baseline={}
with tarfile.open(parent,'r|gz')as t:
 for m in t:
  if m.isfile():baseline[m.name.removeprefix('campaign/')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
old=read(P/'acceptance/evidence-channel07-20261117/delta-provenance.json')['current_files_sha256'];current={str(p.relative_to(root)):digest(p)for p in sorted(root.rglob('*'))if p.is_file()}
for n,h in old.items():
 if '/results/'in n or '/working/ch07/'in n or '/working/ch08/'in n:assert current.get(n)==h,('Prior evidence changed',n)
changed=[n for n,h in current.items()if baseline.get(n)!=h]
with tarfile.open(e/'channel06-delta.tar.gz','w:gz')as t:
 for n in changed:t.add(root/n,arcname='campaign/'+n,recursive=False)
write(e/'delta-provenance.json',dict(base_archive='evidence-group05-08-20261117/campaign-raw.tar.gz',base_sha256=digest(parent),changed_files=changed,current_files_sha256=current,instructions='Extract original base into a new directory, overlay this cumulative delta; includes channel7. Never overwrite live data.'))
(e/'README.md').write_text('''# Physical channel6 — 17 November2026

Both USB moved7→6: DAC0/1→J8 ADC and2/3→J6 integrator. Active/inhibited probes verified routing.
Both257-point ADC sweeps and adjacent-bit exercise PASS under the frozen channel8 contracts.
Integrator **INCOMPLETE**: bankB has no reliably separated integration/reset template near balance.
A shows a sign reversal, but neither bank is claimed to have passed the complete fine/return protocol.
Coarse13points and all raw buffers retained. DAC-A diagnostic16384/32768/49152/65535 did not resolveB;
DAC-A explicitly restored0. This does not prove a hardware fault. Validation thresholds unchanged.
No FPGA/MCU/CPLD/flash/PLL programming, global Kasli stop, output release, or SMU access.

ADC shared plots and zero-input FFT cover6–12; integrator7–12 PASS comparisons remain unchanged.
Commanded voltages and nominal sample rate are not calibrated gain/noise/jitter.
Incremental archive: extract original group05-08 campaign-raw.tar.gz into a NEW directory,
then overlay channel06-delta.tar.gz (includes7). Hash inventory in delta-provenance.json.
All previous selected IDs and sealed raw results preserved; incomplete6 is explicitly recorded.
''')
report=P/'acceptance/evidence-campaign-assembly-20261113'
for n in ['adc-dc-06-12.png','integrator-diagnostic.png']:shutil.copy2(e/n,report/('ch06-'+n))
tex=r'''\clearpage
\section{Physical channel6: ADC PASS; integrator qualification incomplete}
Both USB pairs moved7 to6, DAC0/1 to J8 and2/3 to J6. Active/inhibited probes
verified routing; MCU1803, FPGA ff2f746c and power guards passed. No programming,
clock-profile changes, Kasli output release or SMU access.
\subsection{ADC transfer and adjacent bits: PASS}
Both257-point sweeps use differential range plus/minus1.2V, common mode1V,
outputs0.4--1.6V. All bits and44adjacent-pair states exercised. Frozen channel8
source/method contracts matched. Previous selected results unchanged.
\begin{center}\begin{tabular}{lrrr}\toprule
ADC & Gain(code/V) & Zero mean(code) & Template-removed RMS(code)\\\midrule
'''
for b in 'AB':
 m={v['name']:v['value']for v in items[6]['metrics']if v.get('bank')==b};tex+=f"{b} & {m['gain']:.2f} & {m['zero_mean']:.3f} & {m['zero_four_phase_removed_rms']:.3f} \\\\\n"
tex+=r'''\bottomrule\end{tabular}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch06-adc-dc-06-12.png}\end{center}
Whole-chain commanded-voltage response, not calibrated ADC-only gain.
Older10--12 use c7c42d28;6--9 use ff2f746c; individual receipts retain conditions.
\subsection{Integrator: INCOMPLETE, not a hardware failure determination}
The13-point coarse sweep completed. A shows a signed reversal, but B lacks a
separated integration/reset template near balance. The controller stopped before
fine/return qualification. Four additional DAC-A phase settings did not remove
this ambiguity; raw data retained, thresholds unchanged, DAC-A restored0.
Both-bank qualification remains incomplete; no balance or gain for B is reported.
\begin{center}\includegraphics[width=\linewidth]{ch06-integrator-diagnostic.png}\end{center}
Raw waveforms have separate local capture origins, not a shared trigger.
Final channel6 amplifiers disabled, direct bypass inhibited, all monitor muxes
inhibited/TCA0. External DAC0/1=1/1V,2/3=1.024/2.048V. Kasli outputs unchanged;
leases released. Channel5 analog tests still await the USB move.
'''
(report/'channel06-followup.tex').write_text(tex);p=report/'report.tex';p.write_text(p.read_text().replace('\\input{channel07-followup.tex}','\\input{channel06-followup.tex}\n\\input{channel07-followup.tex}'))
print('ADC PASS; integrator INCOMPLETE; archive built',flush=True)
