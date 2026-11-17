from pathlib import Path
import sys,json,shutil,tarfile,hashlib,statistics,subprocess
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';sys.path.insert(0,str(P/'acceptance'))
from campaign import Campaign,read,write,digest
from campaign_adapters import adc,integrator
from campaign_timing_adapter import normalize as timing
from campaign_monitor_adapter import normalize as monitor
from campaign_smu_adapter import normalize as smu
base=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223');root=base/'four-cfd-clock40-20261117';s=root/'staging';bid='ch01-04-attempt001';w=root/'batches'/bid/'working';e=P/'acceptance/evidence-group01-04-20261117';report=P/'acceptance/evidence-campaign-assembly-20261113'
pipeline=read(s/'group14-after-reboot-pipeline.json');assert pipeline.get('finished_utc')
assert all(k in pipeline['completed'] for k in ['monitor','smu-dacs','smu-final']);assert read(w/'group14-final-safe/status.json')['pass_']
analog=w/'ch04/after-owner-reboot';c=Campaign(root)
with c.locked():previous=dict(c.data['selected'])
paths=[]
if (analog/'adc-corrected-usb/line-test.json').exists():
 for kind in ['adc-dc','adc-lines']:
  out=s/(kind+'-ch04')
  if not out.exists():adc(analog/'adc-corrected-usb',out,root,bid,kind)
  paths.append(out)
else:
 # Failed route verification is an explicit incomplete attempt, not an ADC fault.
 out=s/'adc-dc-ch04-incomplete';out.mkdir();shutil.copytree(analog/'corrected-usb-probe-active',out/'active');shutil.copytree(analog/'corrected-usb-probe-inhibited',out/'inhibited')
 r=read(s/'adc-dc-ch08/campaign-result.json');r.update(channel=4,fixture_id='CFD01',measured_utc=read(out/'active/status.json')['started_utc'],status='INCOMPLETE',source_files=[str(p.relative_to(out)) for p in sorted((out/'active/sources').glob('*.py'))],metrics=[],curves=[],validation=[],channel_checks=[],connections={'usb_input':'J8','stimulus_channel':4,'dac_channels':[0,1],'routing_status':'Declared; active/inhibited route guard failed'},limits='Full ADC scan not run: no expected DAC01 response. Route is unconfirmed; no ADC hardware defect inferred.')
 write(out/'campaign-result.json',r);write(out/'validation.json',dict(pass_=False,physical_channel=4,status='INCOMPLETE',reason=r['limits']));paths.append(out)
integ=next((d for d in [analog/'integrator-corrected-usb',analog/'integrator-independent'] if (d/'analysis/analysis.json').exists()),None)
if integ:
 out=s/'integrator-ch04'
 if not out.exists():integrator(integ,integ/'analysis',out,root,bid)
 paths.append(out)
elif (analog/'integrator-independent/sweep01/status.json').exists():
 out=s/'integrator-ch04-incomplete';out.mkdir();shutil.copytree(analog/'integrator-independent',out/'acquisition');r=read(s/'integrator-ch06-incomplete/campaign-result.json');r.update(channel=4,fixture_id='CFD01',measured_utc=read(out/'acquisition/sweep01/status.json')['started_utc'],source_files=[str(p.relative_to(out))for p in sorted((out/'acquisition/sweep01/sources').glob('*.py'))],connections={'usb_input':'J6','stimulus_channel':4,'dac_channels':[2,3]},reason='Two post-reboot J6 coarse attempts lack an unambiguous bank-B crossing; fine/returns not run, thresholds unchanged',limits='INCOMPLETE attempted integrator4; no full qualification or hardware defect inferred.');write(out/'campaign-result.json',r);write(out/'validation.json',dict(pass_=False,physical_channel=4,status='INCOMPLETE',reason=r['reason']));paths.append(out)
for kind,source in [('tdc',w/'tdc-clock40'),('gate-phase',w/'gate-phase101'),('cfd-monitor',w/'monitor-after-reboot'),('cfd-dacs',w/'smu-dacs-after-reboot')]:
 out=s/(kind+'-ch01-04')
 if not out.exists():
  if kind=='cfd-monitor':monitor(source,out,root,bid)
  elif kind=='cfd-dacs':smu(source,out,root,bid)
  else:timing(kind,source,out,root,bid)
 paths += [out/f'ch{ch:02d}'for ch in range(1,5)]
for source in paths:
 r=read(source/'campaign-result.json');case=r['test']+':'+str(r['channel'])
 with c.locked():present=case in c.data['selected']
 if not present:c.record(bid,source)
 print(case,r['status'],flush=True)
with c.locked():assert all(c.data['selected'][k]==v for k,v in previous.items())
e.mkdir();shutil.copy2(Path(__file__),e/'executed-export.py');shutil.copy2(w/'group14-final-safe/status.json',e/'final-state.json');shutil.copy2(w/'smu-dacs-after-reboot/post-cleanup.json',e/'smu-final-state.json')
for source in paths:
 r=read(source/'campaign-result.json');dest=e/(r['test']+f"-ch{r['channel']:02d}");dest.mkdir()
 for n in ['campaign-result.json','validation.json']:shutil.copy2(source/n,dest/n)
summary=c.summary();write(e/'coverage.json',{k:v for k,v in summary.items()if k!='records'});lookup={(x['test'],x['channel']):x['status']for x in summary['cases']}
# Preserve every previously published sealed result and working acquisition.
parent=P/'acceptance/evidence-group05-08-20261117/campaign-raw.tar.gz';baseline={}
with tarfile.open(parent,'r|gz')as t:
 for m in t:
  if m.isfile():baseline[m.name.removeprefix('campaign/')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
prior=read(P/'acceptance/evidence-ch06-reseat-20261117/delta-provenance.json')['current_files_sha256'];current={str(p.relative_to(root)):digest(p)for p in sorted(root.rglob('*'))if p.is_file()}
for n,h in prior.items():
 if '/results/'in n or '/working/'in n:assert current.get(n)==h,('Historical evidence changed',n)
changed=[n for n,h in current.items()if baseline.get(n)!=h]
with tarfile.open(e/'group14-delta.tar.gz','w:gz')as t:
 for n in changed:t.add(root/n,arcname='campaign/'+n,recursive=False)
write(e/'delta-provenance.json',dict(base_archive='evidence-group05-08-20261117/campaign-raw.tar.gz',base_sha256=digest(parent),current_files_sha256=current,changed_files=changed,instructions='Original base plus this cumulative delta in a NEW directory; includes previous5–8 follow-ups and reseat repeat. Do not overwrite live data.'))
actual={}
for archive in [parent,e/'group14-delta.tar.gz']:
 with tarfile.open(archive,'r|gz')as t:
  for m in t:
   if m.isfile():actual[m.name.removeprefix('campaign/')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
assert actual==current;write(e/'archive-validation.json',dict(pass_=True,files_verified=len(actual)))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# ADC4--12 and qualified integrators4,5,7--12; no incomplete6 overlay.
adcs={};ints={ch:read(s/f'integrator-ch{ch:02d}/campaign-result.json')for ch in [5,7,8]}
if (s/'adc-dc-ch04/campaign-result.json').exists():adcs[4]=read(s/'adc-dc-ch04/campaign-result.json')
if (s/'integrator-ch04/campaign-result.json').exists():ints[4]=read(s/'integrator-ch04/campaign-result.json')
for p in (P/'acceptance/evidence-channel05-20261117/zero-input-figure-inputs').glob('*.json'):
 r=read(p);adcs[r['channel']]=r
ints[9]=read(base/'four-cfd-clock40-20261116/staging/integrator-ch09/campaign-result.json')
for ch in [10,11,12]:ints[ch]=read(base/f'four-cfd-20261113/staging/integrator-ch{ch}/campaign-result.json')
for kind,items in [('adc',adcs),('integrator',ints)]:
 fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
 for ch,r in sorted(items.items()):
  if r['status']!='PASS':continue
  for ax,b in zip(axes,'AB'):
   q=next(x for x in r['curves']if x['name']==('adc_response'if kind=='adc'else'ramp_response')and x['bank']==b);ax.plot(q['x']if kind=='adc'else[x*1000 for x in q['x']],q['y'],'.-'if kind=='integrator'else'-',ms=2,label=f'PM{ch}');ax.set(title=kind+' '+b,xlabel='Commanded differential voltage (V)'if kind=='adc'else'Commanded differential offset (mV)');ax.grid(alpha=.2);ax.legend(fontsize=8,ncol=3)
 axes[0].set_ylabel('ADC code'if kind=='adc'else'Late minus early ADC sample (code)');fig.tight_layout();fig.savefig(e/(kind+'-common.png'),dpi=180);plt.close(fig)
# Full12-channel timing/internal-DAC overlays; historical9--12 explicitly marked.
old=base/'four-cfd-20261113'
for kind,name,panels in [('tdc','tdc_response',['']),('gate-phase','gate_phase',['A','B']),('cfd-dacs',None,['B','C','D'])]:
 items={ch:read(s/(kind+('-ch01-04'if ch<=4 else'-ch05-08'))/f'ch{ch:02d}/campaign-result.json')for ch in range(1,9)}
 if kind=='tdc':
  import importlib.util
  spec=importlib.util.spec_from_file_location('clock40compare',P/'tdc_live120/clock40/analyze.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  for ch,v in module.curves(Path('/srv/codex-hil-nvme/pm12-tdc-clock40-20261114/hardware/tdc/status.json')).items():items[ch]=dict(status='PASS',curves=[dict(name='tdc_response',x=v['delay_ns'],y=v['fine_relative'],x_unit='ns',y_unit='fine code')])
 else:
  folder='gate-phase-ch09-12-v2'if kind=='gate-phase'else'smu-dacs-ch09-12-v2'
  for ch in range(9,13):items[ch]=read(old/'staging'/folder/f'ch{ch:02d}/campaign-result.json')
 fig,axes=plt.subplots(len(panels),1,figsize=(11,3.5*len(panels)),squeeze=False)
 for ch,r in sorted(items.items()):
  if r['status']!='PASS':continue
  for ax,b in zip(axes[:,0],panels):
   q=next(v for v in r['curves']if v['name']==('dac_'+b if kind=='cfd-dacs'else name)and(kind!='gate-phase'or v['bank']==b));ax.plot(q['x'],q['y'],'.-',ms=2,label=f'PM{ch}'+(' (historical)'if ch>=9 else''));ax.set(title=kind+(' '+b if b else''),xlabel=q['x_unit'],ylabel=q['y_unit']);ax.grid(alpha=.2);ax.legend(ncol=4,fontsize=8)
 fig.tight_layout();fig.savefig(e/(kind+'-01-12.png'),dpi=180);plt.close(fig)
subprocess.run([sys.executable,str(P/'acceptance/compare_adc_zero_inputs.py'),'--receipts',*([str(e/'adc-dc-ch04/campaign-result.json')]if 4 in adcs and adcs[4]['status']=='PASS' else []),*[str(p)for p in sorted((P/'acceptance/evidence-channel05-20261117/zero-input-figure-inputs').glob('*.json'))],'--out',str(e)],check=True)
text='''# New fitting1–4; USB4 — 17 November2026

Owner confirmed CFD modules1–4, retained RJ45 order, shared monitors on SMU;
DAC0/1→J8 ADC and2/3→J6 integrator on4. Finite discovery confirmed slot7 ports0/1/2/3→PM4/3/2/1.
PM initially not ready/IPbus unavailable; original MCU power/PLL state checked. Owner later reported reboot; PGOOD loss interrupted monitor and blockedDAC scan. Original interrupted data retained; monitor/DAC restarted in NEW directories.
Fresh FPGA DNA/MCU1803 verified; qualified ff2f746c restored to volatile SRAM.
No new build or MCU/CPLD/flash/PLL programming. Slot6 HDMI SPI stays driven.

|PM channel|ADC/bits|Integrator|TDC|Phase|Monitor|DAC B/C/D|
|---|---|---|---|---|---|---|
'''
for ch in range(1,5):text+='|'+str(ch)+'|'+('/'.join(lookup[k,ch]for k in ['adc-dc','adc-lines']))+'|'+'|'.join(lookup[k,ch]for k in ['integrator','tdc','gate-phase','cfd-monitor','cfd-dacs'])+'|\n'
text+='''
ADC/integrators1–3 await USB moves. Channel4 status is explicit in the table; failed route probes and partial attempts are not hardware fault determinations.
Integrator6 remains INCOMPLETE after pressing; previous cohorts and all selected IDs retained.
Shared ADC/integrator plots include only the qualified labelled channels; incomplete cases excluded; timing/DAC overlays all12 with historical epochs labelled.
Historical TDC9–12 is the corrected-clock14November acquisition, not withdrawn c7 data.
SCPI voltages and nominal clocks are not traceable ADC/TDC/jitter calibration.

Shared SMU is0A/local Force HI/LO; only one mux active at a time. Supply divider53/33 correction applied.
Final SMU OFF/HIZ, auto-on OFF, all monitor muxes inhibited/TCA0, exercised internal DACs0000.
External DAC park and GPIO state retained in native metadata. Full ADC/integrator results require successful independent validation. Leases released.
Portable data: original group05-08 campaign-raw.tar.gz plus group14-delta.tar.gz in a NEW directory;
complete inventory verified. Never overwrite live acquisition data. All previous source contracts retained.
'''
(e/'README.md').write_text(text)
for p in e.glob('*.png'):shutil.copy2(p,report/('group14-'+p.name))
tex=r'''\clearpage
\section{New fitting: physical channels 1--4}
The owner fitted four CFD simulators on1--4, kept the RJ45 order and connected
both USB pairs on4: DAC0/1 to J8 ADC, DAC2/3 to J6 integrator. Shared monitor
outputs remain on the SMU. Finite discovery confirms slot7 ports0/1/2/3 to PM4/3/2/1.
Initially PM IPbus was unavailable and MCU reported FPGA not ready. Fresh DNA
and MCU1803 were verified; qualified ff2f746c was restored to volatile SRAM.
No build, MCU/CPLD/flash or PLL programming. Kasli HDMI outputs stay driven.
\subsection{Recorded coverage}
\begin{center}\begin{tabular}{rllllll}\toprule
Channel & ADC/bits & Integrator & TDC & Phase & Monitor & B/C/D\\\midrule
'''
for ch in range(1,5):tex+=str(ch)+' & '+('/'.join(lookup[k,ch]for k in ['adc-dc','adc-lines'])).replace('NOT_MEASURED','NM')+' & '+' & '.join(lookup[k,ch].replace('NOT_MEASURED','NM').replace('INCOMPLETE','INC')for k in ['integrator','tdc','gate-phase','cfd-monitor','cfd-dacs'])+r'\\'+'\n'
tex+=r'''\bottomrule\end{tabular}\end{center}
NM means not measured; INC means incomplete. USB remains4; analog1--3 awaits
cable moves. Integrator6 retains its INCOMPLETE result. Previous selected IDs
and sealed raw evidence are unchanged. PASS covers functional assembly checks.
\subsection{Channel4 analog response}
The first channel4 route guard did not show the expected DAC0/1 response and
stopped before the full ADC/integrator sequence. The owner then reported a reboot;
observed PGOOD loss interrupted monitor collection, and PM FPGA became not ready.
Qualified SRAM was restored again. Interrupted data remain excluded; fresh monitor
and internal-DAC acquisitions use new directories. TDC and phase completed before
the reboot and retain that epoch. Channel4 status is given explicitly in the table.
Full ADC method, when qualified, uses257points per bank over plus/minus1.2V
at1V common mode; integrator method uses13coarse/26fine points and independent
returns/plus-minus5mV controls. An independent J6 test may proceed while J8 route
verification is incomplete. No response or ambiguous traces do not establish a defect.
\begin{center}\includegraphics[width=\linewidth]{group14-adc-common.png}\end{center}
\begin{center}\includegraphics[width=\linewidth]{group14-integrator-common.png}\end{center}
Only qualified labelled channels are overlaid. Integrator6 remains excluded.
Older10--12 use c7c42d28, newer analog uses ff2f746c; receipts retain epochs.
Commanded voltages are whole-chain observations, not calibrated ADC-only gain.
\subsection{All12 channels: TDC and gate phase}
Clock40 tests include finite discovery, quiet windows, count1/64/512/1024 and
25phase positions per port. Raw13-bit words and count conservation are checked.
Historical9--12 TDC uses the corrected-clock14November capture; withdrawn c7
clock qualification is excluded. Gate phase uses101DAC-A codes per module,
both return lanes and nominal24sampler bins per LHC period. Discontinuities
remain visible; no absolute calibration or intrinsic jitter claim.
\begin{center}\includegraphics[width=\linewidth]{group14-tdc-01-12.png}\end{center}
\begin{center}\includegraphics[width=\linewidth]{group14-gate-phase-01-12.png}\end{center}
\subsection{Shared SMU monitors and internal DACs}
Eight monitor inputs per module, three fresh readings each, were recorded with
SMU0A/local Force HI/LO. Negative/positive supply dividers use nominal53/33.
Only one shared monitor mux is active at a time. Internal B/C/D scans each use
101codes and3fresh readings; all12-channel transfer curves below retain epochs.
\begin{center}\includegraphics[width=\linewidth]{group14-cfd-dacs-01-12.png}\end{center}
Final SMU OFF/HIZ, auto-on OFF. All four monitor muxes inhibited/TCA0;
exercised internal DACs restored0000. External park/GPIO recorded in raw files.
Kasli outputs retained, leases released. Source contracts and raw inventory verified.
\subsection{Zero-input waveforms and FFT, qualified channels shown}
Separate local capture origins, not synchronized traces. FFT one-sided RMS code
per bin at nominal80.1574MS/s, not PSD or intrinsic aperture-jitter measurement.
\begin{center}\includegraphics[width=\linewidth]{group14-adc-zero-time.png}\end{center}
\begin{center}\includegraphics[width=\linewidth]{group14-adc-zero-fft.png}\end{center}
'''
(report/'group14-followup.tex').write_text(tex);p=report/'report.tex';p.write_text(p.read_text().replace('\\input{ch06-reseat-followup.tex}','\\input{group14-followup.tex}\n\\input{ch06-reseat-followup.tex}'))
print('GROUP14_EXPORTED',flush=True)
