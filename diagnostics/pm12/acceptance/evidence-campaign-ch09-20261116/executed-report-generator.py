from pathlib import Path
import sys,json,shutil,tarfile,hashlib,subprocess,statistics
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';sys.path.insert(0,str(P/'acceptance'))
from campaign_adapters import adc,integrator
from campaign import Campaign,read,write,digest
parent=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-20261113');root=parent.with_name('four-cfd-clock40-20261116');bid='ch09-12-attempt001';work=parent/'batches'/bid/'working/ch09';stage=root/'staging';stage.mkdir(exist_ok=True)
assert read(work/'integrator/validation02/status.json')['pass_']
for kind in ['adc-dc','adc-lines','integrator']:
 out=stage/(kind+'-ch09')
 if not out.exists():
  result=integrator(work/'integrator',work/'integrator/analysis',out,root,bid)if kind=='integrator'else adc(work/'adc-full',out,root,bid,kind)
  print(kind,result['status'],flush=True)
 assert read(out/'campaign-result.json')['status']=='PASS'
 c=Campaign(root)
 with c.locked(): present=any(r['case']==kind+':9' for r in c.data['results'])
 if not present:c.record(bid,out)
e=P/'acceptance/evidence-campaign-ch09-20261116';e.mkdir(exist_ok=False)
for kind in ['adc-dc','adc-lines','integrator']:
 for f in ['campaign-result.json','validation.json']:shutil.copy2(stage/(kind+'-ch09')/f,e/(kind+'-'+f))
with tarfile.open(e/'channel09-raw.tar.gz','w:gz')as t:
 t.add(work,arcname='working/ch09')
 for name in ['preflight-ch09.py','acquire-adc-ch09.py','integrator-ch09-controller.py','preflight-ch09-console.txt','acquire-adc-ch09-console.txt','integrator-ch09-console.txt']:t.add(parent/'staging'/name,arcname='controllers/'+name)
 t.add(root,arcname='revision')
shutil.copy2('/srv/codex-hil-nvme/pm12-campaign-ch9-software-tests-20261116.txt',e/'software-tests.txt')
results={9:{kind:read(stage/(kind+'-ch09')/'campaign-result.json')for kind in ['adc-dc','integrator']}}
for ch in [10,11,12]:
 results[ch]={kind:read(parent/'staging'/(kind+'-ch'+str(ch))/'campaign-result.json') for kind in ['adc-dc','integrator']}
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ch,data in results.items():
 for ax,bank in zip(axes,'AB'):
  curve=next(c for c in data['adc-dc']['curves']if c['name']=='adc_response'and c['bank']==bank)
  ax.plot(curve['x'],curve['y'],label=f'PM {ch}'+(' (ff2f746c)'if ch==9 else' (c7c42d28)'))
  ax.set_title('ADC '+bank);ax.set_xlabel('Commanded differential voltage (V)');ax.grid(alpha=.25);ax.legend(fontsize=8)
axes[0].set_ylabel('ADC code');fig.tight_layout();fig.savefig(e/'adc-response-09-12.png',dpi=180);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ch,data in results.items():
 for ax,bank in zip(axes,'AB'):
  curve=next(c for c in data['integrator']['curves']if c['name']=='ramp_response'and c['bank']==bank)
  ax.plot([x*1000 for x in curve['x']],curve['y'],'.-',label=f'PM {ch}'+(' (ff2f746c)'if ch==9 else' (c7c42d28)'))
  ax.set_title('Integrator '+bank);ax.set_xlabel('Commanded differential offset (mV)');ax.axhline(0,color='gray',lw=.7);ax.grid(alpha=.25);ax.legend(fontsize=8)
axes[0].set_ylabel('Late minus early ADC sample (code)');fig.tight_layout();fig.savefig(e/'integrator-response-09-12.png',dpi=180);plt.close(fig)
for name in ['integrator-balance.png','integrator-waveforms.png','ramp-points.csv']:shutil.copy2(work/'integrator/analysis'/name,e/name)
summary=dict(board='PM12-K7-3A17A1B402212223',channel=9,fpga_build='ff2f746c',revision=str(root),parent=str(parent),results={k:read(stage/(k+'-ch09')/'campaign-result.json')['status']for k in ['adc-dc','adc-lines','integrator']},integrator_plan=read(work/'integrator/plan.json'),validation=read(stage/'integrator-ch09/validation.json'))
write(e/'summary.json',summary)
(e/'README.md').write_text('''# Channel9 analog tests — 2026-11-16

Owner moved both USB cables10->9: MOD-DAC0/1 to J8 direct ADC,2/3 to J6 integrator.
Fitted CFD9-12 and RJ45 mapping unchanged. Fresh MCU1803/FPGA ff2f746c/power checks,
all four shared muxes inhibited, other amplifiers/bypass isolated at preflight.
ADC A/B257-point scans and adjacent-bit exercises PASS; integrator signed crossing,
fine26points and independent return/sign controls PASS. All voltages commanded
within3.3V. No FPGA/MCU/CPLD/clock/SMU programming in this acquisition.

The firmware validation guards now accept an explicitly supplied expected build;
the previous frozen source contracts are preserved. A new independent campaign
revision four-cfd-clock40-20261116 records actual ff2f746c provenance. Original
same-fitting identity receipts are copied verbatim; live16Nov preflight and owner
USB routing are archived. Old10-12 data remain under their original c7c42d28
contracts. The overlay labels this hardware difference; it is comparative,
not a claim of identical hardware/clock implementation or fresh retest10-12.

Raw archive includes full revision registry and original buffers, executed sources,
SCPI/UART receipts, controls and analysis. Summary and normalized results retain
metrics/limits. Final DAC settings and GPIO state are in validation02/status.json.
The combined report adds this chapter without rewriting historical coverage.
''')
report=P/'acceptance/evidence-campaign-assembly-20261113'
for name in ['adc-response-09-12.png','integrator-response-09-12.png','integrator-balance.png','integrator-waveforms.png']:shutil.copy2(e/name,report/('ch09-'+name))
text=r'''\clearpage
\section{Channel 9 ADC and integrators: 16 November 2026}
The owner moved both USB pairs from physical channel 10 to 9. MOD-DAC outputs
0/1 feed J8 (direct ADC), outputs 2/3 feed J6 (integrator); the four CFD fixtures
remain on channels 9--12. No firmware, gateware, clock profile or SMU changes
were made during these measurements. Actual FPGA build is \texttt{ff2f746c}.

\subsection{ADC transfer and adjacent data lines}
Both banks passed a 257-point differential sweep from -1.2 to +1.2 V at 1 V common
mode (each DAC output 0.4--1.6 V), with integrator amplifiers disabled.
Both ADCs exercised every bit at zero/one and all 44 adjacent-pair states.
This is a functional assembly check, not calibrated INL/DNL or an electrical
proof excluding every possible short.
\begin{center}\begin{tabular}{lrrr}\toprule
ADC & Gain (code/V) & Zero mean (code) & Template-removed RMS (code)\\\midrule
'''
a=results[9]['adc-dc']
for bank in 'AB':
 m={x['name']:x['value']for x in a['metrics']if x.get('bank')==bank}
 text+=f"{bank} & {m['gain']:.2f} & {m['zero_mean']:.3f} & {m['zero_four_phase_removed_rms']:.3f} \\\\\n"
text+=r'''\bottomrule\end{tabular}\end{center}
The residual RMS follows removal of a four-phase template and is not intrinsic
ADC noise or aperture jitter. Voltages are DAC commands, not calibrated readings.
\begin{center}\includegraphics[width=\linewidth]{ch09-adc-response-09-12.png}\end{center}
Channels 10--12 are historical 13 November measurements with build c7c42d28;
channel 9 uses ff2f746c. These are explicitly labelled cross-revision comparisons.
\subsection{Integrator balance and signed response}
Direct ADC injection was inhibited before releasing the integrator amplifiers.
The coordinate is DAC2 = 1.024 V + delta/2, DAC3 = 2.048 V - delta/2.
Coarse13 and fine26 points were followed by independent candidate revisits and
plus/minus5 mV checks. Clipped or ambiguous waveforms are excluded from balance.
\begin{center}\begin{tabular}{lrrr}\toprule
ADC & DAC2/DAC3 (V) & Return change (code) & Gain (code/V)\\\midrule
'''
v=summary['validation']
for bank in 'AB':
 b=v['banks'][bank];d=b['candidate_offset_V'];text+=f"{bank} & {1.024+d/2:.4f}/{2.048-d/2:.4f} & {statistics.mean(b['returned_change_codes']):+.3f} & {b['gain']:.1f} \\\\\n"
text+=r'''\bottomrule\end{tabular}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch09-integrator-response-09-12.png}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch09-integrator-balance.png}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch09-integrator-waveforms.png}\end{center}
Waveform pair assignment is not an independently timestamped gate. Balance and
gain include the complete DAC/cable/integrator/ADC chain. Separate A/B balance
points do not imply a shared setting nulls both simultaneously.

\subsection{Provenance and current state}
Analog functional coverage now includes physical channels 9--12, with the
hardware revision distinction above. Prior frozen contracts and results remain
unchanged; the new source/build combination is registered independently.
Both USB pairs remain on9. DAC0/1 are 1/1 V; DAC2/3 are parked at the measured
shared compromise. Channel9 amplifiers enabled, direct ADC injection isolated,
all monitor muxes inhibited and TCA masks zero. Kasli output directions unchanged.
This does not close unrelated board findings or establish full board acceptance.
Raw buffers and editable sources are in the dated channel9 evidence archive.
'''
(report/'channel09-analog-followup.tex').write_text(text)
f=report/'report.tex';f.write_text(f.read_text().replace('\\input{hdmi-cable-followup.tex}','\\input{channel09-analog-followup.tex}\n\\input{hdmi-cable-followup.tex}'))
for p in [e]:write(p/'files.sha256.json',{str(f.relative_to(p)):digest(f)for f in sorted(p.rglob('*'))if f.is_file()and f.name!='files.sha256.json'})
print(e,flush=True)
