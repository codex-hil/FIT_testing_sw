from pathlib import Path
import sys,json,hashlib,tarfile,shutil,statistics,os
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';sys.path.insert(0,str(P/'acceptance'))
from campaign import Campaign,read,write,digest
from campaign_adapters import adc,integrator
base=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223');root=base/'four-cfd-clock40-20261117';bid='ch05-08-attempt001';stage=root/'staging';work=root/'batches'/bid/'working/ch07'
assert read(work/'corrected-usb-analog-completed.json')['pass_']
c=Campaign(root)
with c.locked():previous=dict(c.data['selected'])
paths=[]
for kind in ['adc-dc','adc-lines','integrator']:
 out=stage/(kind+'-ch07')
 if not out.exists():
  if kind=='integrator':integrator(work/'integrator-corrected-usb',work/'integrator-corrected-usb/analysis',out,root,bid)
  else:adc(work/'adc-corrected-usb',out,root,bid,kind)
 assert read(out/'campaign-result.json')['status']=='PASS'
 with c.locked():present=kind+':7'in c.data['selected']
 if not present:c.record(bid,out)
 paths.append(out);print(kind,'PASS',flush=True)
with c.locked():assert all(c.data['selected'][k]==v for k,v in previous.items())
# Recover old ch08 staging logs byte-for-byte; keep the new ch07 logs distinctly named.
parent_archive=P/'acceptance/evidence-group05-08-20261117/campaign-raw.tar.gz'
names=['corrected-usb-preflight.py']+['corrected-usb-'+k+'-console.txt'for k in ['preflight','probe-active','probe-inhibited','adc-full','integrator']]
audit={}
for name in names:
 current=stage/name;target=stage/('ch07-'+name)
 if current.exists():shutil.copy2(current,target);audit[name]=dict(ch07_saved_as=target.name,ch07_sha256=digest(target))
base_inventory={}
with tarfile.open(parent_archive,'r|gz')as t:
 for member in t:
  if not member.isfile():continue
  rel=member.name.removeprefix('campaign/');data=t.extractfile(member).read();base_inventory[rel]=hashlib.sha256(data).hexdigest()
  if rel.startswith('staging/')and rel[len('staging/'):]in names:
   p=root/rel;p.write_bytes(data);os.utime(p,(member.mtime,member.mtime));audit[p.name]['ch08_restored_sha256']=base_inventory[rel]
write(stage/'ch07-log-reconciliation.json',audit)
e=P/'acceptance/evidence-channel07-20261117';e.mkdir();shutil.copy2(Path(__file__),e/'executed-report-generator.py')
for out in paths:
 kind=read(out/'campaign-result.json')['test'];dest=e/kind;dest.mkdir()
 for name in ['campaign-result.json','validation.json']:shutil.copy2(out/name,dest/name)
summary=Campaign(root).summary();write(e/'coverage.json',{k:v for k,v in summary.items()if k!='records'})
current={str(f.relative_to(root)):digest(f)for f in sorted(root.rglob('*'))if f.is_file()}
changed=[n for n,h in current.items()if base_inventory.get(n)!=h]
for n in base_inventory:
 if '/results/'in n or '/working/ch08/'in n:
  assert current.get(n)==base_inventory[n],('Historical immutable evidence changed',n)
with tarfile.open(e/'channel07-delta.tar.gz','w:gz')as t:
 for name in changed:t.add(root/name,arcname='campaign/'+name,recursive=False)
write(e/'delta-provenance.json',dict(base_archive='evidence-group05-08-20261117/campaign-raw.tar.gz',base_sha256=digest(parent_archive),changed_files=changed,current_files_sha256=current,instructions='Extract the base archive into a NEW directory, then overlay this delta there; do not apply to live acquisition data. No previous selected results changed.'))
# Compare all measured analog channels on shared axes.
old=base/'four-cfd-20261113';clock16=base/'four-cfd-clock40-20261116'
sets={kind:{7:read(stage/(kind+'-ch07')/'campaign-result.json'),8:read(stage/(kind+'-ch08')/'campaign-result.json'),9:read(clock16/'staging'/(kind+'-ch09')/'campaign-result.json')}for kind in ['adc-dc','integrator']}
for kind,items in sets.items():
 for ch in [10,11,12]:items[ch]=read(old/'staging'/(kind+'-ch'+str(ch))/'campaign-result.json')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
for kind,items in sets.items():
 fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
 for ch,r in sorted(items.items()):
  for ax,b in zip(axes,'AB'):
   q=next(v for v in r['curves']if v['name']==('adc_response'if kind=='adc-dc'else'ramp_response')and v['bank']==b);ax.plot(q['x']if kind=='adc-dc'else[x*1000 for x in q['x']],q['y'],'.-'if kind=='integrator'else'-',ms=2,label=f'PM{ch}');ax.set_title(('ADC 'if kind=='adc-dc'else'Integrator ')+b);ax.grid(alpha=.2);ax.legend(ncol=2,fontsize=8);ax.set_xlabel('Commanded differential voltage (V)'if kind=='adc-dc'else'Commanded differential offset (mV)')
 axes[0].set_ylabel('ADC code'if kind=='adc-dc'else'Late minus early ADC sample (code)');fig.tight_layout();fig.savefig(e/(kind+'-07-12.png'),dpi=180);plt.close(fig)
adc_result=sets['adc-dc'][7];val=read(stage/'integrator-ch07/validation.json');last=read(work/'integrator-corrected-usb/validation02/status.json');write(e/'summary.json',dict(channel=7,adc=adc_result['metrics'],integrator=val,final_dac=last['dac_final'],route=read(work/'corrected-usb-route-verified.json')))
text='''# Physical channel7 ADC and integrators — 2026-11-17

Owner confirmed moving both USB8->7, preserving0/1->J8 ADC and2/3->J6 integrator.
Active/inhibited probes verified the route, normal selector map[0,1]. Fresh MCU1803,
FPGA ff2f746c and power guards passed. Both ADC257-point sweeps/adjacent-bit checks
and integrator coarse13/fine26points/independent returns/±5mV controls PASS.
No FPGA/MCU/CPLD/clock/SMU programming or new TDC/phase/DAC scan was needed.
Existing fitting5-8 timing/monitor/internal-DAC results remain selected unchanged.

The importer matched the same frozen method/source contracts as channel8.
Previous selected result IDs and all sealed/ch08 files remain byte-for-byte.
Shared transfer/integrator/zero-input waveform/FFT overlays now include7–12;
older acquisition/build versions remain separately identified in their receipts.
Commanded voltages and nominal sample rate are not calibrated ADC-only gain/noise.

`channel07-delta.tar.gz` is an incremental portable campaign archive: extract the
base `evidence-group05-08-20261117/campaign-raw.tar.gz` into a NEW directory, then
extract the delta there. `delta-provenance.json` gives the base SHA and complete
resulting inventory. Run campaign_report.py on the reconstructed campaign for an
offline report. Do not overwrite live hardware data with archive extraction.
Exact executed outer source is retained with an executed suffix; ch07 staging
logs were prefixed and ch08 logs restored from the base, with a reconciliation
journal. Native data/source snapshots are immutable.
'''
(e/'README.md').write_text(text)
report=P/'acceptance/evidence-campaign-assembly-20261113'
for name in ['adc-dc-07-12.png','integrator-07-12.png']:shutil.copy2(e/name,report/('ch07-'+name))
tex=r'''\clearpage
\section{Physical channel7: ADC and integrators, 17 November 2026}
Both USB pairs moved8 to7 in the same5--8 fitting. Independent active/inhibited
bypass probes verified DAC0/1 at J8, DAC2/3 at J6 and normal selector map[0,1].
MCU1803, FPGA ff2f746c and power checks passed. The same frozen method/source
contracts as channel8 were matched; previous selected result IDs are unchanged.
No programming or clock changes, and no repetition of the completed5--8 timing,
monitor or internal-DAC scans.
\subsection{ADC transfer and adjacent bits: PASS}
Both banks were swept at257points from-1.2 to+1.2V differential,1V common mode,
with outputs0.4--1.6V. Every bit and all44adjacent-pair states were exercised.
\begin{center}\begin{tabular}{lrrr}\toprule
ADC & Gain(code/V) & Zero mean(code) & Template-removed RMS(code)\\\midrule
'''
for bank in 'AB':
 m={v['name']:v['value']for v in adc_result['metrics']if v.get('bank')==bank};tex+=f"{bank} & {m['gain']:.2f} & {m['zero_mean']:.3f} & {m['zero_four_phase_removed_rms']:.3f} \\\\\n"
tex+=r'''\bottomrule\end{tabular}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch07-adc-dc-07-12.png}\end{center}
These are commanded-voltage, whole-chain observations. Template-removed RMS is
not intrinsic ADC noise or aperture jitter. Older10--12 use c7c42d28;7--9 use
ff2f746c with their separately recorded source contracts and capture conditions.
\subsection{Integrator balance and signed response: PASS}
Coarse13 and fine26points at0.4mV, followed by independent candidate returns
and plus/minus5mV controls, verified an unclipped signed zero crossing per bank.
\begin{center}\begin{tabular}{lrrr}\toprule
ADC & DAC2/DAC3(V) & Return change(code) & Gain(code/V)\\\midrule
'''
for bank in 'AB':
 v=val['banks'][bank];d=v['candidate_offset_V'];tex+=f"{bank} & {1.024+d/2:.4f}/{2.048-d/2:.4f} & {statistics.mean(v['returned_change_codes']):+.3f} & {v['gain']:.1f} \\\\\n"
tex+=r'''\bottomrule\end{tabular}\end{center}
\begin{center}\includegraphics[width=\linewidth]{ch07-integrator-07-12.png}\end{center}
The sampled integration pair is waveform-derived, not independently gate-tagged.
Final DAC0/1 are1/1V; DAC2/3 use the shared measured compromise recorded in the
raw metadata. Channel7 amplifiers enabled, direct ADC bypass isolated, all
monitor muxes inhibited/TCA0. Other fitted channels were isolated at preflight.
Kasli outputs/directions unchanged; leases released. Analog7--12 observations
are now available;5--6 await their USB moves.
'''
(report/'channel07-followup.tex').write_text(tex)
f=report/'report.tex';f.write_text(f.read_text().replace('\\input{group58-followup.tex}','\\input{channel07-followup.tex}\n\\input{group58-followup.tex}'))
print(e,flush=True)
