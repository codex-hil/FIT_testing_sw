from pathlib import Path
import sys,json,shutil,hashlib,tarfile,statistics,struct,subprocess
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';sys.path[:0]=[str(P/'acceptance'),str(P/'ipbus_adc')]
from campaign import Campaign,read,write,digest
from campaign_adapters import adc,integrator
from adc_decode import decode
base=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223');root=base/'four-cfd-clock40-20261117';s=root/'staging';bid='ch01-04-attempt001';w=root/'batches'/bid/'working/ch03/after-usb-move';e=P/'acceptance/evidence-channel03-20261117';report=P/'acceptance/evidence-campaign-assembly-20261113'
assert read(w/'corrected-usb-route-verified.json')['active_gain_code_per_V'][0]<-500
assert read(w/'adc-corrected-usb/line-test.json')['pass_']
c=Campaign(root)
with c.locked():previous=dict(c.data['selected'])
paths=[]
for kind in ['adc-dc','adc-lines']:
 out=s/(kind+'-ch03');adc(w/'adc-corrected-usb',out,root,bid,kind);assert read(out/'campaign-result.json')['status']=='PASS';paths.append(out)
native=w/'integrator-corrected-usb';out=s/'integrator-ch03'
if (native/'analysis/analysis.json').exists():
 integrator(native,native/'analysis',out,root,bid)
else:
 r=read(native/'sweep01/status.json');assert r['pass_'] and not r.get('error')
 out.mkdir();shutil.copytree(native,out/'acquisition');record=read(s/'integrator-ch04-incomplete/campaign-result.json')if (s/'integrator-ch04-incomplete/campaign-result.json').exists()else read(s/'integrator-ch06-incomplete/campaign-result.json')
 record.update(channel=3,fixture_id='CFD02',measured_utc=r['started_utc'],source_files=[str(p.relative_to(out))for p in sorted((out/'acquisition/sweep01/sources').glob('*.py'))],connections={'usb_input':'J6','stimulus_channel':3,'dac_channels':[2,3]},reason='Channel3 coarse13 and fine26 acquisitions completed; bankB fine scan retained only one unambiguous point, so signed crossing/return qualification did not run',limits='INCOMPLETE waveform-based integrator qualification; no hardware defect inferred.')
 write(out/'campaign-result.json',record);write(out/'validation.json',dict(pass_=False,status='INCOMPLETE',physical_channel=3,reason=record['reason']))
paths.append(out)
for p in paths:
 r=read(p/'campaign-result.json');c.record(bid,p);print(r['test'],r['status'],flush=True)
with c.locked():assert all(c.data['selected'][k]==v for k,v in previous.items())
e.mkdir();shutil.copy2(Path(__file__),e/'executed-export.py')
for p in paths:
 dest=e/read(p/'campaign-result.json')['test'];dest.mkdir()
 for n in ['campaign-result.json','validation.json']:shutil.copy2(p/n,dest/n)
summary=c.summary();write(e/'coverage.json',{k:v for k,v in summary.items()if k!='records'});status=read(out/'campaign-result.json')['status'];final=read(w/'final-safe/status.json');write(e/'summary.json',dict(channel=3,ADC='PASS',ADC_lines='PASS',integrator=status,adc_metrics=read(s/'adc-dc-ch03/campaign-result.json')['metrics'],integrator_validation=read(out/'validation.json'),final_park=final['dac_prepared'],final_gpio=final['safe_gpio'],route=read(w/'corrected-usb-route-verified.json')))
# New delta relative to the published complete group14 snapshot, avoiding repeated large archives.
parent=P/'acceptance/evidence-group01-04-20261117/delta-provenance.json';old=read(parent)['current_files_sha256'];current={str(p.relative_to(root)):digest(p)for p in sorted(root.rglob('*'))if p.is_file()}
for n,h in old.items():
 if '/results/'in n or '/working/'in n:assert current.get(n)==h,('Previous immutable evidence changed',n)
assert set(old)<=set(current),'Incremental reconstruction cannot silently drop files'
changed=[n for n,h in current.items()if old.get(n)!=h]
with tarfile.open(e/'channel03-delta.tar.gz','w:gz')as t:
 for n in changed:t.add(root/n,arcname='campaign/'+n,recursive=False)
virtual=dict(old)
with tarfile.open(e/'channel03-delta.tar.gz','r|gz')as t:
 for m in t:
  if m.isfile():virtual[m.name.removeprefix('campaign/')]=hashlib.sha256(t.extractfile(m).read()).hexdigest()
assert virtual==current
write(e/'delta-provenance.json',dict(parent_manifest='evidence-group01-04-20261117/delta-provenance.json',parent_manifest_sha256=digest(parent),changed_files=changed,current_files_sha256=current,instructions='Extract original group05-08 base, overlay concatenated group14 delta parts, then this channel03 delta in a NEW directory. Never overwrite live data.'))
write(e/'archive-validation.json',dict(pass_=True,parent_inventory_plus_delta_matches_current=True,files_verified=len(current),changed_files=len(changed),delta_sha256=digest(e/'channel03-delta.tar.gz')))
# Shared receipt-derived curves; exclude incomplete integrators3/4/6.
adcs={3:read(s/'adc-dc-ch03/campaign-result.json')};ints={ch:read(s/f'integrator-ch{ch:02d}/campaign-result.json')for ch in [5,7,8]}
if status=='PASS':ints[3]=read(out/'campaign-result.json')
for p in (P/'acceptance/evidence-group01-04-20261117/zero-input-figure-inputs').glob('*.json'):
 r=read(p);adcs[r['channel']]=r
ints[9]=read(base/'four-cfd-clock40-20261116/staging/integrator-ch09/campaign-result.json')
for ch in [10,11,12]:ints[ch]=read(base/f'four-cfd-20261113/staging/integrator-ch{ch}/campaign-result.json')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
for kind,items in [('adc',adcs),('integrator',ints)]:
 fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
 for ch,r in sorted(items.items()):
  if r['status']!='PASS':continue
  for ax,b in zip(axes,'AB'):
   q=next(v for v in r['curves']if v['name']==('adc_response'if kind=='adc'else'ramp_response')and v['bank']==b);ax.plot(q['x']if kind=='adc'else[x*1000 for x in q['x']],q['y'],'.-'if kind=='integrator'else'-',ms=2,label=f'PM{ch}');ax.set(title=kind+' '+b,xlabel='Commanded differential voltage (V)'if kind=='adc'else'Commanded differential offset (mV)');ax.grid(alpha=.2);ax.legend(ncol=3,fontsize=8)
 axes[0].set_ylabel('ADC code'if kind=='adc'else'Late minus early ADC sample (code)');fig.tight_layout();fig.savefig(e/(kind+'-common.png'),dpi=180);plt.close(fig)
subprocess.run([sys.executable,str(P/'acceptance/compare_adc_zero_inputs.py'),'--receipts',str(e/'adc-dc/campaign-result.json'),*[str(p)for p in sorted((P/'acceptance/evidence-group01-04-20261117/zero-input-figure-inputs').glob('*.json'))],'--out',str(e)],check=True)
if status!='PASS':
 fine=read(native/'fine01/status.json');fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True);inputs={}
 for bank,ax in enumerate(axes):
  for requested in [0,.004,.0088]:
   pt=min(fine['points'],key=lambda v:abs(v['offset_V']-requested));cap=next(v for v in pt['captures']if v['bank']==bank);p=native/'fine01'/cap['file'];b=p.read_bytes();samples,_=decode(struct.unpack('<4096H',b),bank);inputs[str(p.relative_to(root))]=hashlib.sha256(b).hexdigest();ax.plot([i*1e9/80157400 for i in range(20)],samples[:20],'.-',label=f"delta={pt['offset_V']*1000:.1f} mV")
  ax.set(title='PM3 integrator '+ 'AB'[bank],xlabel='Local capture time (ns)');ax.grid(alpha=.2);ax.legend()
 axes[0].set_ylabel('ADC code');fig.suptitle('Diagnostic fine scan: bank B template unqualified; capture origins unaligned');fig.tight_layout();fig.savefig(e/'integrator3-diagnostic.png',dpi=180);plt.close(fig);write(e/'integrator3-figure-inputs.json',inputs)
for p in e.glob('*.png'):shutil.copy2(p,report/('ch03-'+p.name))
text=f'''# Channel3 after confirmed USB move — 17 November2026

First route checks found DAC01 still on4. Owner then confirmed moving both USB to3.
Fresh active/inhibited probes verify DAC01→J8, DAC23→J6 declared, normal selector[0,1].
Qualified ff2f746c/MCU1803/power guards passed; no programming or clock changes.
ADC257points/bank and adjacent-bit exercise **PASS**. Integrator **{status}**.
No TDC/phase/SMU repeat: current group1–4 already measured. All prior selected results unchanged.
Shared ADC waveform/FFT overlays3–12; integrators include only qualified labelled channels.
Integrator4/6 remain INCOMPLETE. Historical acquisition/build epochs are retained.

Final all1–4 amps/bypass/monitor muxes inhibited, TCA0; external DAC01=1/1V,23=1.024/2.048V.
Kasli outputs/directions preserved, leases released. Raw final state in summary.json.
ADC/integrators1–2 remain pending USB moves. These are functional assembly checks,
not traceable gain/noise/timing calibration or a whole-board release.

Archive reconstruction: original group05-08 base, then concatenated group14 delta parts,
then channel03-delta.tar.gz in a NEW directory. Parent-inventory plus delta verified;
no previous raw result/working acquisition was changed. Initial failed routing diagnostics retained.
''';(e/'README.md').write_text(text)
tex=r'''\clearpage
\section{Physical channel3 after confirmed USB move}
The first requested channel3 probe found no response; a control probe confirmed
DAC0/1 still reached4. The owner then confirmed moving both USB cables to3.
Fresh active/inhibited probes verify the J8 ADC route and normal selector map[0,1].
MCU1803, FPGA ff2f746c and power guards passed. No programming, clock changes,
Kasli output release, or repeated timing/SMU tests. Earlier qualified results are unchanged.
\subsection{ADC and adjacent bits: PASS}
Both257-point sweeps span plus/minus1.2V differential at common mode1V,
output legs0.4--1.6V. All bits and44adjacent-pair states exercised.
The frozen source/method contract matches the qualified preceding channels.
\begin{center}\begin{tabular}{lrrr}\toprule
ADC & Gain(code/V) & Zero mean(code) & Template-removed RMS(code)\\\midrule
'''
r=adcs[3]
for b in 'AB':
 m={v['name']:v['value']for v in r['metrics']if v.get('bank')==b};tex+=f"{b} & {m['gain']:.2f} & {m['zero_mean']:.3f} & {m['zero_four_phase_removed_rms']:.3f} \\\\\n"
tex+=r'''\bottomrule\end{tabular}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch03-adc-common.png}\end{center}
Older10--12 use c7c42d28; newer analog uses ff2f746c. Individual receipts retain
epochs and source versions; commanded voltage is whole-chain response, not ADC-only calibration.
'''
tex+='\\subsection{Integrator: '+status+'}\n'
if status=='PASS':
 v=read(out/'validation.json');tex+=r'''Coarse13/fine26points and independent candidate returns/plus-minus5mV controls
passed with unchanged waveform-separation thresholds and the same frozen method contract.
\begin{center}\begin{tabular}{lrrr}\toprule
Bank & Balance delta(mV) & Gain(code/V) & Mean return(code)\\\midrule
'''
 for b in 'AB':
  q=v['banks'][b];tex+=f"{b} & {q['balance_delta']*1000:.3f} & {q['gain']:.1f} & {statistics.mean(q['returned_change_codes']):+.3f} \\\\\n"
 tex+=r'\bottomrule\end{tabular}\end{center}'+'\n'
else:tex+='The13-point coarse and26-point fine acquisitions completed. BankB retained only one unambiguous fine point; no signed fine crossing could be established, and independent returns did not run. No full integrator PASS or hardware defect is inferred; thresholds unchanged.\n'
if status!='PASS':tex+=r'\begin{center}\includegraphics[width=\linewidth]{ch03-integrator3-diagnostic.png}\end{center}'+'\n'
tex+=r'''\begin{center}\includegraphics[width=\linewidth]{ch03-integrator-common.png}\end{center}
Only qualified labelled channels are overlaid; incomplete3/4/6 are excluded.
Final amplifiers, direct ADC bypass and monitor muxes inhibited, TCA masks zero;
external DAC0/1 are1/1V and2/3 are1.024/2.048V. Leases released. Analog1--2 awaits USB moves.
\subsection{Zero-input waveforms and FFT, channels3--12}
Independent local capture origins, not synchronized traces. FFT amplitudes are
one-sided RMS code per bin at nominal80.1574MS/s, not PSD or intrinsic aperture jitter.
\begin{center}\includegraphics[width=\linewidth]{ch03-adc-zero-time.png}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch03-adc-zero-fft.png}\end{center}
'''
(report/'channel03-followup.tex').write_text(tex);p=report/'report.tex';p.write_text(p.read_text().replace('\\input{group14-followup.tex}','\\input{channel03-followup.tex}\n\\input{group14-followup.tex}'))
print('EXPORTED_CHANNEL3',status,flush=True)
