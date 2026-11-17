from pathlib import Path
import json,sys,subprocess,hashlib,datetime,shutil
repo=Path('/home/codex-hil/fit-testing-publish');a=repo/'diagnostics/pm12/acceptance';e=a/'evidence-group01-04-20261117';report=a/'evidence-campaign-assembly-20261113';root=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261117');w=root/'batches/ch01-04-attempt001/working'
read=lambda p:json.loads(p.read_text());coverage=read(e/'coverage.json');lookup={(x['test'],x['channel']):x['status']for x in coverage['cases']};adc=lookup['adc-dc',4];bits=lookup['adc-lines',4];integ=lookup['integrator',4]
full_adc=adc=='PASS'and bits=='PASS';full_int=integ=='PASS'
# Add numerical values alongside data-derived comparative plots.
tex=r'''\subsection{Numerical results for the new fitting}
\begin{center}\begin{tabular}{lrrrr}\toprule
Monitor(V) & PM1 & PM2 & PM3 & PM4\\\midrule
'''
mon={ch:read(e/f'cfd-monitor-ch{ch:02d}/validation.json')['values']for ch in range(1,5)}
for i in range(8):
 name=mon[1][i]['signal'].replace('_',r'\_');tex+=name+' & '+' & '.join(f"{mon[ch][i]['volts']:+.5f}"for ch in range(1,5))+r'\\'+'\n'
tex+=r'''\bottomrule\end{tabular}\end{center}
Values are corrected to monitored nodes, including nominal supply divider53/33;
three fresh SMU readings per input, not traceable calibration.
'''
if full_adc:
 r=read(e/'adc-dc-ch04/campaign-result.json');tex+=r'''\begin{center}\begin{tabular}{lrrr}\toprule
ADC4 & Gain(code/V) & Zero mean(code) & Template-removed RMS(code)\\\midrule
'''
 for b in 'AB':
  m={v['name']:v['value']for v in r['metrics']if v.get('bank')==b};tex+=f"{b} & {m['gain']:.2f} & {m['zero_mean']:.3f} & {m['zero_four_phase_removed_rms']:.3f} \\\\\n"
 tex+=r'''\bottomrule\end{tabular}\end{center}
After the reboot, independent active/inhibited probes verified the declared J8
route. Only the complete post-reboot acquisition is selected; the first no-response
probe remains diagnostic history. No ADC defect is inferred from that first probe.
'''
if full_int:
 r=read(e/'integrator-ch04/validation.json');tex+=r'''\begin{center}\begin{tabular}{lrrr}\toprule
Integrator4 & Balance delta(mV) & Gain(code/V) & Mean return(code)\\\midrule
'''
 import statistics
 for b in 'AB':
  v=r['banks'][b];tex+=f"{b} & {v['balance_delta']*1000:.3f} & {v['gain']:.1f} & {statistics.mean(v['returned_change_codes']):+.3f} \\\\\n"
 tex+=r'\bottomrule\end{tabular}\end{center}'+'\n'
# Preserve raw waveform evidence for incomplete integrator4 without claiming phase alignment.
if integ=='INCOMPLETE':
 import struct
 sys.path.insert(0,str(repo/'diagnostics/pm12/ipbus_adc'))
 from adc_decode import decode
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 native=w/'ch04/after-owner-reboot/integrator-independent/sweep01';raw=read(native/'status.json');fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True);inputs={}
 for bank,ax in enumerate(axes):
  for requested in [-.02,0,.02]:
   point=min(raw['points'],key=lambda v:abs(v['offset_V']-requested));cap=next(v for v in point['captures']if v['bank']==bank);f=native/cap['file'];b=f.read_bytes();inputs[str(f.relative_to(root))]=hashlib.sha256(b).hexdigest();samples,_=decode(struct.unpack('<4096H',b),bank);ax.plot([i*1e9/80157400 for i in range(20)],samples[:20],'.-',label=f"delta={point['offset_V']*1000:.0f} mV")
  ax.set(title='PM4 integrator '+ 'AB'[bank],xlabel='Local capture time (ns)');ax.legend();ax.grid(alpha=.2)
 axes[0].set_ylabel('ADC code');fig.suptitle('Diagnostic only: bank B template remains unqualified; capture origins unaligned');fig.tight_layout();fig.savefig(e/'integrator4-diagnostic.png',dpi=180);plt.close(fig);shutil.copy2(e/'integrator4-diagnostic.png',report/'group14-integrator4-diagnostic.png');(e/'integrator4-figure-inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
 tex+=r"\subsection{Integrator4 incomplete: raw waveforms}"+'\n'+r"The two coarse attempts both lacked a unique bank-B signed crossing. Fine and independent returns did not run. Traces below have separate local origins; no gate epoch is inferred."+'\n'+r"\begin{center}\includegraphics[width=\linewidth]{group14-integrator4-diagnostic.png}\end{center}"+'\n'
p=report/'group14-followup.tex';p.write_text(p.read_text()+tex)
prefix=f'''Latest fitting1–4 (2026-11-17): TDC/phase/monitor/internal-DAC results in the linked table.
Channel4 ADC/bits: **{adc}/{bits}**; integrator: **{integ}**. USB remains4, analog1–3 pending.
Slot7 ports0/1/2/3→PM4/3/2/1 verified. Integrator6 remains INCOMPLETE.
[Group1–4 evidence and common plots](LINK).

'''
for p,link in [(repo/'README.md','diagnostics/pm12/acceptance/evidence-group01-04-20261117/README.md'),(a/'README.md','evidence-group01-04-20261117/README.md'),(a/'ACTIVE_CAMPAIGN.md','evidence-group01-04-20261117/README.md'),(report/'README.md','../evidence-group01-04-20261117/README.md')]:p.write_text(prefix.replace('LINK',link)+p.read_text())
state=f'''Latest setup: CFD1–4, slot7 RJ45 ports0/1/2/3→4/3/2/1; both USB4, DAC01→J8,23→J6.
FPGA ff2f746c SRAM restored after initial not-ready state and again after owner-reported reboot;
MCU/CPLD/flash/PLL unchanged. TDC/phase completed before reboot, monitor/DAC restarted afterwards.
Interrupted/raw no-response attempts retained; no acquisition merged across reboot.
Final SMU OFF/HIZ/0A/auto-on OFF; monitors inhibited/TCA0, internal exercised DACs0000.
Slot6 HDMI SPI stays driven. Kasli outputs/directions preserved; leases released.
Final external DAC01=1/1V,23=1.024/2.048V; all1–4 amps/bypass inhibited.
Integrator4 {integ}; integrator6 INCOMPLETE. Analog1–3 pending.
Earlier dated setup states below are historical.

'''
p=a/'ACTIVE_CAMPAIGN.md';p.write_text(state+p.read_text());p=Path('/home/codex-hil/FIT_PM_FW_uPC/docs/pm12_current_hardware_state.md');p.write_text('## 2026-11-17 FINAL — fitting1–4 / USB4\n\n'+prefix.replace('LINK','fit-testing-publish/diagnostics/pm12/acceptance/evidence-group01-04-20261117/README.md')+state+p.read_text())
p=Path('/srv/codex-hil-nvme/pm12-campaigns/active.json');d=read(p);d.update(status=f'Group1–4 digital/monitor/DAC completed; ADC4 {adc}, bits4 {bits}, integrator4 {integ}; next USB3',analog_channel=4,fitted_channels=[1,2,3,4],updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());d['verified_connections']={'channel':4,'direct_adc_input':'J8','direct_adc_dac_channels':[0,1],'integrator_input':'J6','integrator_dac_channels':[2,3],'verification_status':('PASS post-reboot probes and full analog'if full_adc and full_int else f'ADC {adc}, integrator {integ}; inspect receipts')};p.write_text(json.dumps(d,indent=2)+'\n')
subprocess.run(['/srv/codex-hil-nvme/pm12-acceptance-20261107/toolchain/tectonic','report.tex'],cwd=report,check=True)
info=subprocess.check_output(['pdfinfo',str(report/'report.pdf')],text=True);pages=next(l.split(':')[1].strip()for l in info.splitlines()if l.startswith('Pages:'))
for p in [repo/'README.md',a/'README.md',report/'README.md']:p.write_text(p.read_text().replace('98-page',pages+'-page'))
p=e/'README.md';p.write_text(p.read_text()+f'\n[Current{pages}-page editable report](../evidence-campaign-assembly-20261113/report.pdf).\n')
shutil.copy2(Path(__file__),e/'executed-report-finisher.py')
for directory in [e,report]:
 m={str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(directory.rglob('*'))if p.is_file()and p.name!='files.sha256.json'and p.suffix not in ['.log','.aux','.out']};(directory/'files.sha256.json').write_text(json.dumps(m,indent=2)+'\n')
print('FINAL',pages,'pages',adc,bits,integ,flush=True)
