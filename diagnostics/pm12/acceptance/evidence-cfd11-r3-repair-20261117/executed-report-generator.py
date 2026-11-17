from pathlib import Path
import sys,json,shutil,tarfile,statistics,hashlib
repo=Path('/home/codex-hil/fit-testing-publish');P=repo/'diagnostics/pm12';sys.path.insert(0,str(P/'acceptance'))
from campaign import Campaign,read,write,digest
work=Path('/srv/codex-hil-nvme/pm12-cfd11-r3-repair-20261117-attempt02');r=read(work/'result.json');assert r['pass_']and not r.get('error')and r['finished_utc']and len(r['readings'])==9
assert r['final_smu']['OUTP?']=='0'and r['final_smu']['OUTP:OFF:MODE?']=='HIZ'and float(r['final_smu']['SOUR:CURR?'])==0 and int(r['final_smu']['SYST:ERR?'].split(',')[0])==0 and set(r['final_tca'].values())=={0}
for name,expected in r['executed_sources'].items():assert digest(work/name)==expected
root=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261116');out=root/'staging/cfd-monitor11-repaired-20261117';out.mkdir();shutil.copytree(work,out/'acquisition')
valid=dict(pass_=True,physical_channel=11,checks=r['checks'],monitor7_repeats=[v['converted']for v in r['readings']if v['mux_channel']==7],samples=45,smu_safe_final=True,repair_confirmed_by_owner='Missing R3=33kohm fitted')
write(out/'validation.json',valid)
receipt=dict(mode='LIVE',board_uid='PM12-K7-3A17A1B402212223',test='cfd-monitor',channel=11,fixture_id='CFD02',measured_utc=r['started_utc'],status='PASS',protocol=dict(method='MCU-only-repaired-monitor-v1',hardware_configuration=dict(pm_build='NOT USED: MCU-only monitor; FPGA not ready and IPbus unavailable',kasli_build='NOT USED: Kasli outputs untouched',clock_profile='MCU reports PRIMARY/PLL LOCKED; monitor DC measurement independent of FPGA clocks',cpld_gate_mode='NOT USED for DC monitor'),samples_per_input=5,mux7_revisits=2,source_current_A=0,sense='local Force HI/LO',divider_correction=53/33),source_files=['acquisition/'+name for name in r['executed_sources']],validation=[dict(file='validation.json',key='pass_',equals=True)],channel_checks=[dict(file='validation.json',key='physical_channel')],connections=dict(shared_monitor_channels=[9,10,11,12],selection='One mux active, others inhibited'),metrics=[dict(name=v['converted']['signal'],value=v['converted']['volts'],unit='V')for v in r['readings'][:8]],curves=[dict(name='monitor_voltages',x=list(range(8)),y=[v['converted']['volts']for v in r['readings'][:8]],x_unit='monitor input',y_unit='V')],limits='Postrepair DC functional check, MCU-only; does not qualify FPGA/IPbus or repeat ADC/integrator/TDC. Owner confirmed fitted33kohm; nominal divider ratio, no traceable calibration.')
write(out/'campaign-result.json',receipt);Campaign(root).record('ch09-12-attempt001',out)
e=P/'acceptance/evidence-cfd11-r3-repair-20261117';e.mkdir()
for f in ['validation.json','campaign-result.json']:shutil.copy2(out/f,e/f)
with tarfile.open(e/'raw.tar.gz','w:gz')as t:
 for name in ['pm12-cfd11-r3-repair-20261117','pm12-cfd11-r3-repair-20261117-attempt02']:
  t.add(work.parent/name,arcname=name)
  console=work.parent/('pm12-cfd11-r3-repair-console-20261117'+('-attempt02'if name.endswith('attempt02')else'')+'.txt');t.add(console,arcname=console.name)
shutil.copy2(Path(__file__),e/'executed-report-generator.py')
values=[v['converted']for v in r['readings'][:8]];a,b=valid['monitor7_repeats'];summary=dict(channel=11,fixture='CFD02',repair='Owner confirmed missing R3=33kohm and fitted it',old_mux7_raw_V=5.479,after_mux7_raw_V=[a['volts_at_mux'],b['volts_at_mux']],after_positive_rail_V=[a['volts'],b['volts']],all_eight_checks_pass=True,values=values,fpga_status=r.get('fpga_unavailable',r.get('fpga')),no_programming=True)
write(e/'summary.json',summary)
text='''# CFD02 / physical PM11: R3 repair verified — 2026-11-17

Owner confirmed missing33kohm R3 and fitted it. Monitor MUX7 previously measured
5.479V raw (divider output incorrectly near full rail). After repair two visits,
five fresh readings each, measured3.405970 and3.406098V raw; applying53/33 gives
+5.470194 and+5.470400V. All eight monitor values and relative-reference checks PASS.

Keysight B2910BL MY63320299, Force HI/LO local sense, source0A,20V/1PLC.
Only one of four shared muxes active at a time. Final SMU OFF/HIZ/0A, auto-on OFF;
all four muxes inhibited, both TCA masks0. Analog GPIO upper bits/B controls preserved.
No DAC writes, firmware/gateware/flash/profile changes, Kasli outputs untouched.

MCU1803 confirms power healthy, PRIMARY and PLL LOCKED. It reports FPGA not ready;
IPbus timed out. First attempt stopped before mux selection on the old FPGA guard.
Second completed MCU-only check is the selected result. This is a repaired monitor
PASS, not FPGA/Ethernet qualification or a repeat of ADC/integrator/TDC tests.
Both attempts retained in raw archive. Old faulty measurement remains historical.
New independent monitor method registered in clock40 revision; parent source
contracts and original FAIL raw data preserved. Report erratum closes this specific
fixture-divider finding after repair; other board findings remain separate.

|Input|Signal|Raw V|Converted V|
|---|---|---:|---:|
'''
for i,v in enumerate(values):text+=f"|{i}|{v['signal']}|{v['volts_at_mux']:.6f}|{v['volts']:.6f}|\n"
(e/'README.md').write_text(text)
report=P/'acceptance/evidence-campaign-assembly-20261113'
tex=r'''\clearpage
\section{CFD fixture on channel 11: missing R3 repaired, 17 November 2026}
The owner confirmed that the 33 kohm resistor R3 was missing and fitted it.
This closes the previously documented positive-supply divider assembly finding
for provisional fixture CFD02, physical PM channel11. The original faulty
measurement remains preserved as historical evidence.
\begin{center}\begin{tabular}{lrr}\toprule
Condition & MUX7 raw voltage (V) & Divider-corrected rail (V)\\\midrule
Before repair & 5.479 & Invalid divider: do not convert\\
After repair, visit1 & 3.405970 & 5.470194\\
After repair, visit2 & 3.406098 & 5.470400\\\bottomrule
\end{tabular}\end{center}
Five fresh samples were acquired per visit. After repair the nominal divider
factor is 53/33. All eight monitor inputs and the relative reference checks pass.
\begin{center}\begin{tabular}{rlrr}\toprule
Input & Signal & Raw voltage (V) & Converted voltage (V)\\\midrule
'''
for i,v in enumerate(values):tex+=f"{i} & \\texttt{{{v['signal'].replace('_',r'\_')}}} & {v['volts_at_mux']:.6f} & {v['volts']:.6f} \\\\\n"
tex+=r'''\bottomrule\end{tabular}\end{center}
Measurement used Keysight B2910BL MY63320299 as a 0A voltmeter, Force HI/LO
local sensing,20V range,1PLC. Exactly one shared monitor mux was active at a time.
Final state: SMU OFF/HIZ/0A, auto-on disabled; all four muxes inhibited and both
TCA masks zero. Upper analog GPIO controls were preserved. No DAC, firmware,
gateware, flash or clock-profile writes were made; Kasli outputs were untouched.

MCU1803 confirmed healthy power and PRIMARY/PLL LOCKED. It reported FPGA not
ready and IPbus did not respond. The first attempt stopped on its FPGA guard;
the selected second attempt used the independent MCU/I2C route. This PASS applies
to the repaired DC monitor, not FPGA/Ethernet or a new ADC/integrator/TDC test.
Other findings and historical test conditions are unchanged. Raw data and both
attempts are retained in the dated CFD11 repair evidence archive.
'''
(report/'cfd11-r3-repair-followup.tex').write_text(tex)
f=report/'report.tex';f.write_text(f.read_text().replace('\\input{channel09-analog-followup.tex}','\\input{cfd11-r3-repair-followup.tex}\n\\input{channel09-analog-followup.tex}'))
for d in [e]:write(d/'files.sha256.json',{str(f.relative_to(d)):digest(f)for f in sorted(d.rglob('*'))if f.is_file()and f.name!='files.sha256.json'})
print(summary)
