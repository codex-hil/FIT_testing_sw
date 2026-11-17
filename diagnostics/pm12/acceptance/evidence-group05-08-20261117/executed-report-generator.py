from pathlib import Path
import sys,json,statistics,shutil,tarfile,subprocess,hashlib
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';sys.path.insert(0,str(P/'acceptance'))
from campaign import Campaign,read,write,digest
from campaign_adapters import adc,integrator
from campaign_monitor_adapter import normalize as monitor
from campaign_smu_adapter import normalize as smu
from campaign_timing_adapter import normalize as timing
base=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223');root=base/'four-cfd-clock40-20261117';bid='ch05-08-attempt001';work=root/'batches'/bid/'working';stage=root/'staging'
assert read(stage/'remaining-pipeline.json')['pass_']
assert read(work/'ch08/corrected-usb-analog-completed.json')['pass_']
# Native raw files are checked again by each normalizer before import.
for kind in ['adc-dc','adc-lines']:
 out=stage/(kind+'-ch08')
 if not out.exists():adc(work/'ch08/adc-corrected-usb',out,root,bid,kind)
for kind,source in [('tdc',work/'tdc-clock40'),('gate-phase',work/'gate-phase101'),('cfd-monitor',work/'monitor'),('cfd-dacs',work/'smu-dacs')]:
 out=stage/(kind+'-ch05-08')
 if not out.exists():
  if kind=='cfd-monitor':monitor(source,out,root,bid)
  elif kind=='cfd-dacs':smu(source,out,root,bid)
  else:timing(kind,source,out,root,bid)
integ=stage/'integrator-ch08'
if not integ.exists():integrator(work/'ch08/integrator-corrected-usb',work/'ch08/integrator-corrected-usb/analysis',integ,root,bid)
paths=[stage/'adc-dc-ch08',stage/'adc-lines-ch08',integ]+[stage/(kind+'-ch05-08')/f'ch{ch:02d}'for kind in ['tdc','gate-phase','cfd-monitor','cfd-dacs']for ch in range(5,9)]
for source in paths:
 receipt=read(source/'campaign-result.json');c=Campaign(root)
 with c.locked():present=any(x['case']==receipt['test']+':'+str(receipt['channel'])for x in c.data['results'])
 if not present:c.record(bid,source)
 print(receipt['test'],receipt['channel'],receipt['status'],flush=True)
e=P/'acceptance/evidence-group05-08-20261117';e.mkdir();shutil.copy2(Path(__file__),e/'executed-report-generator.py')
summary=Campaign(root).summary();write(e/'coverage.json',{k:v for k,v in summary.items()if k!='records'})
for source in paths:
 receipt=read(source/'campaign-result.json');target=e/f"{receipt['test']}-ch{receipt['channel']:02d}";target.mkdir()
 for f in ['campaign-result.json','validation.json']:shutil.copy2(source/f,target/f)
with tarfile.open(e/'campaign-raw.tar.gz','w:gz')as t:t.add(root,arcname='campaign')
for f in ['pm12-group58-tests-20261117.txt','pm12-group58-cfd-tests-20261117.txt','pm12-group58-tdc-validator-regression-20261117.txt']:shutil.copy2(Path('/srv/codex-hil-nvme')/f,e/f)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
# All-channel overlays retain their acquisition/build labels.
old=base/'four-cfd-20261113';clock16=base/'four-cfd-clock40-20261116'
adcs={8:read(stage/'adc-dc-ch08/campaign-result.json'),9:read(clock16/'staging/adc-dc-ch09/campaign-result.json')}
for ch in [10,11,12]:adcs[ch]=read(old/f'staging/adc-dc-ch{ch}/campaign-result.json')
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ch,r in sorted(adcs.items()):
 for ax,b in zip(axes,'AB'):
  q=next(x for x in r['curves']if x['name']=='adc_response'and x['bank']==b);ax.plot(q['x'],q['y'],label=f'PM{ch} ({r["protocol"]["hardware_configuration"]["pm_build"]})');ax.set_title('Capture bank '+b);ax.set_xlabel('Commanded differential voltage (V)');ax.grid(alpha=.2);ax.legend(fontsize=7)
axes[0].set_ylabel('ADC code');fig.tight_layout();fig.savefig(e/'adc-response-08-12.png',dpi=180);plt.close(fig)
integrators={8:read(stage/'integrator-ch08/campaign-result.json'),9:read(clock16/'staging/integrator-ch09/campaign-result.json')}
for ch in [10,11,12]:integrators[ch]=read(old/f'staging/integrator-ch{ch}/campaign-result.json')
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ch,r in sorted(integrators.items()):
 for ax,b in zip(axes,'AB'):
  q=next(v for v in r['curves']if v['name']=='ramp_response'and v['bank']==b);ax.plot([x*1000 for x in q['x']],q['y'],'.-',label=f'PM{ch}');ax.set_title('Integrator '+b);ax.set_xlabel('Commanded differential offset (mV)');ax.grid(alpha=.2);ax.legend(ncol=2,fontsize=8)
axes[0].set_ylabel('Late minus early ADC sample (code)');fig.tight_layout();fig.savefig(e/'integrator-response-08-12.png',dpi=180);plt.close(fig)
for kind,curvename,panels in [('tdc','tdc_response',['']),('gate-phase','gate_phase',['A','B']),('cfd-dacs',None,['B','C','D'])]:
 fig,axes=plt.subplots(len(panels),1,figsize=(10,3*len(panels)),squeeze=False)
 plot_results={ch:read(stage/(kind+'-ch05-08')/f'ch{ch:02d}/campaign-result.json') for ch in range(5,9)}
 if kind in ['gate-phase','cfd-dacs']:
  folder='gate-phase-ch09-12-v2'if kind=='gate-phase'else'smu-dacs-ch09-12-v2'
  for ch in range(9,13):plot_results[ch]=read(old/'staging'/folder/f'ch{ch:02d}/campaign-result.json')
 if kind=='tdc':
  import importlib.util
  spec=importlib.util.spec_from_file_location('clock40compare',P/'tdc_live120/clock40/analyze.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  for ch,v in module.curves(Path('/srv/codex-hil-nvme/pm12-tdc-clock40-20261114/hardware/tdc/status.json')).items():
   plot_results[ch]=dict(curves=[dict(name='tdc_response',x=v['delay_ns'],y=v['fine_relative'],x_unit='ns',y_unit='fine code')])
 for ch,r in sorted(plot_results.items()):
  for ax,b in zip(axes[:,0],panels):
   name='dac_'+b if kind=='cfd-dacs'else curvename;q=next(x for x in r['curves']if x['name']==name and(kind!='gate-phase'or x['bank']==b));ax.plot(q['x'],q['y'],'.-',ms=2,label=f'PM{ch}'+(' (historical)'if ch>=9 else''));ax.set_xlabel(q['x_unit']);ax.set_ylabel(q['y_unit']);ax.set_title(kind+(' '+b if b else''));ax.grid(alpha=.2);ax.legend(ncol=4)
 fig.tight_layout();fig.savefig(e/(kind+'-05-08.png'),dpi=180);plt.close(fig)
# Compact current-status table; only actually completed methods are PASS.
text='''# Fitting5–8 / USB8 — 2026-11-17

Owner confirmed simulators5–8, slot7ports0/1/2/3->PM8/7/6/5; both USB on8,
DAC0/1 intendedJ8 ADC and2/3 intendedJ6 integrator; all shared monitors on SMU.
Fresh DNA/MCU identity and restored qualified FPGA ff2f746c; no new build,
MCU/CPLD/flash/PLL programming. Kasli slot6 SPI held throughout, only slot7
buffer directions serviced for finite TDC pulses and receive-only phase scans.

Corrected and independently verified routing: DAC0/1->J8 ADC, DAC2/3->J6
integrator, normal MCP selector map[0,1]. All selected analog results start after
the operator corrected swapped USB pairs. Initial driver-path scans, the temporary
map[1,0], insufficient-range attempt and operator-interrupted wider-range run are
diagnostic history only. They do not establish ADC bank inversion or a gain fault.
Active/inhibited bypass probes independently confirm the corrected input route.
Selected ADC scan returns to standard±1.2V differential at1V common mode,
257points/bank, legs0.4..1.6V. Integrator uses DAC2/3 base1.024/2.048V,
coarse13/fine26points plus independent signed/return controls.
ADC/integrators5–7 await the next USB moves. Original9–12 data and selected
attempts preserved; cross-revision overlays are explicitly labelled.

|Physical PM channel|ADC transfer/bits|Integrator|TDC|Gate phase|CFD monitors|DAC B/C/D|
|---|---|---|---|---|---|---|
'''
lookup={(r['test'],r['channel']):r['status']for r in summary['cases']}
for ch in range(5,9):text+='|'+str(ch)+'|'+'/'.join(lookup[k,ch]for k in ['adc-dc','adc-lines'])+'|'+ '|'.join(lookup[k,ch]for k in ['integrator','tdc','gate-phase','cfd-monitor','cfd-dacs'])+'|\n'
(e/'README.md').write_text(text)
report=P/'acceptance/evidence-campaign-assembly-20261113'
for name in ['adc-response-08-12.png','integrator-response-08-12.png','tdc-05-08.png','gate-phase-05-08.png','cfd-dacs-05-08.png']:shutil.copy2(e/name,report/('group58-'+name))
tex=r'''\clearpage
\section{New fitting: physical channels 5--8, 17 November 2026}
The owner fitted four CFD simulators on5--8, retained the RJ45 order
(slot7 ports0/1/2/3 to PM8/7/6/5), connected both USB pairs to8 and confirmed
all four shared monitor outputs connected to the SMU. Board DNA and MCU1803
were freshly verified. Qualified FPGA ff2f746c was restored to volatile SRAM;
no new build, MCU/CPLD/flash or clock-profile programming.
\subsection{Recorded coverage}
\begin{center}\begin{tabular}{rllllll}\toprule
Channel & ADC/bits & Integrator & TDC & Phase & Monitor & B/C/D\\\midrule
'''
for ch in range(5,9):tex+=str(ch)+' & '+('/'.join(lookup[k,ch]for k in ['adc-dc','adc-lines'])).replace('NOT_MEASURED','NM')+' & '+' & '.join(lookup[k,ch].replace('NOT_MEASURED','NM').replace('INCOMPLETE','INC')for k in ['integrator','tdc','gate-phase','cfd-monitor','cfd-dacs'])+r'\\'+'\n'
tex+=r'''\bottomrule\end{tabular}\end{center}
NM means not measured; INC means incomplete. USB remains on8, so no analog
coverage is inferred for5--7. PASS values are scoped functional tests, not a
whole-board release or traceable calibration.
\subsection{Channel8 ADC and integrators after USB correction}
Initial symptoms came from swapped USB pairs: DAC0/1 drove the driver path,
DAC2/3 the ADC bypass. Four active/inhibited-bypass probes identified the route.
The operator corrected the cables; the running exploratory scan was stopped with
native cleanup and excluded in full. Independent post-correction probes confirm
DAC0/1 at J8, DAC2/3 at J6 and normal selector map[0,1].
The apparent bank inversion and lower driver-path gain are not ADC defects.

Only post-correction data enter selected results: both257-point ADC sweeps span
-1.2 to+1.2V at1V common mode (legs0.4--1.6V); every bit and all44adjacent-pair
states are exercised. Earlier driver-path and insufficient/wider-range attempts
remain archived as diagnostics, not qualification evidence.
\begin{center}\includegraphics[width=\linewidth]{group58-adc-response-08-12.png}\end{center}
Historical10--12 use c7c42d28,9 and8 use ff2f746c with their respective frozen
source contracts. Axes show commanded voltages and complete-chain response,
not calibrated ADC-only gain or input voltage.

The selected integrator scan uses corrected DAC2/3 routing and the original
1.024/2.048V base coordinate: coarse13points, fine26points at0.4mV, independent
candidate revisits and plus/minus5mV controls. Clipped or ambiguous traces are
excluded. Earlier all-zero traces came from the disconnected bypass stimulus;
they do not constitute an integrator hardware failure.
\begin{center}\includegraphics[width=\linewidth]{group58-integrator-response-08-12.png}\end{center}
\subsection{Finite TDC patterns and gate-phase scans}
The clock40 acquisition includes discovery, quiet controls, count1/64/512/1024
and25phase positions per port. All raw13-bit words and count conservation are
independently checked. Phase is relative to nominal serializer slots; no absolute
TDC calibration or intrinsic jitter measurement is claimed. Historical9--12
TDC curves use the corrected-clock c7531465 captures from14November; withdrawn
c7 TDC curves are not used. Other historical overlays retain their dated
acquisition conditions and do not imply a fresh retest of9--12.
\begin{center}\includegraphics[width=\linewidth]{group58-tdc-05-08.png}\end{center}
\begin{center}\includegraphics[width=\linewidth]{group58-gate-phase-05-08.png}\end{center}
Gate phase uses101DAC-A codes per channel and both sampled return lanes.
Nearest-continuation unwrap retains discontinuities; a functional excursion
is not a certified smooth tuning range or sub-bin accuracy.
\subsection{Shared SMU measurements}
Eight monitor inputs and three101-code DAC curves per module were read with
Keysight B2910BL as0A/local Force HI/LO voltmeter. Only one shared mux was
active at a time. Negative/positive supply divider values use nominal53/33.
\begin{center}\includegraphics[width=\linewidth]{group58-cfd-dacs-05-08.png}\end{center}
Final SMU OFF/HIZ/0A, auto-on disabled; all four monitor muxes inhibited and
TCA masks zero. Exercised B/C/D and phase DAC-A restored to0000. Kasli HDMI
SPI outputs remain driven; no global stop or slot6 direction change.
All original data and selected historical cases are preserved. Raw campaign,
source snapshots and independent validation receipts are in the dated group5--8
archive; this chapter is editable LaTeX.
'''
(report/'group58-followup.tex').write_text(tex)
p=report/'report.tex';p.write_text(p.read_text().replace('\\input{cfd11-r3-repair-followup.tex}','\\input{group58-followup.tex}\n\\input{cfd11-r3-repair-followup.tex}'))
for d in [e]:write(d/'files.sha256.json',{str(f.relative_to(d)):digest(f)for f in sorted(d.rglob('*'))if f.is_file()and f.name!='files.sha256.json'})
print(e,flush=True)
