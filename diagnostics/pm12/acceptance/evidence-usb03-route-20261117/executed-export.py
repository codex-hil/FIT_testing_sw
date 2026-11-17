from pathlib import Path
import json,datetime,tarfile,shutil,hashlib
repo=Path('/home/codex-hil/fit-testing-publish');root=Path('/srv/codex-hil-nvme/pm12-campaigns/PM12-K7-3A17A1B402212223/four-cfd-clock40-20261117');w=root/'batches/ch01-04-attempt001/working/ch03';e=repo/'diagnostics/pm12/acceptance/evidence-usb03-route-20261117';e.mkdir()
shutil.copy2(Path(__file__),e/'executed-export.py')
for name in ['route-control-comparison.json','operator-request.json','route-final-park.json']:shutil.copy2(w/name,e/name)
with tarfile.open(e/'route-checks.tar.gz','w:gz')as t:
 t.add(w,arcname='channel03-route-checks')
 for name in ['acquire-corrected-usb03.py','ch03-route-final-park.py']:t.add(root/'staging'/name,arcname='executed-sources/'+name)
(e/'README.md').write_text('''# USB route guard before requested channel3 measurements

Owner requested continuing after channel4. Native ff2f746c/MCU1803/power guards passed.
Active/inhibited probes on physical3 show negligible response; no full ADC/integrator3 scan ran.
A subsequent control probe on physical4 responds -1776.83/-1761.33code/V;
physical3 response -1.15/-0.39code/V. DAC0/1 still reach ADC4 at this observation.
This is a wiring-route diagnostic, not an ADC3 hardware failure or qualification.

All prior selected measurement results remain unchanged. Native captures, executed
sources and cleanup records are retained. External DAC01=1/1V,23=1.024/2.048V;
route probes restored their original inhibited bypass/monitor state, TCA0.
No FPGA/MCU/CPLD/clock/Kasli direction changes or SMU access. Leases released.
Both USB must be moved to3: DAC01→J8,23→J6, before the next full scan.
The104-page measurement report remains current; these route checks add no qualified ADC3 coverage.
''')
p=root/'batches/ch01-04-attempt001/station.json';d=json.loads(p.read_text());d['requested_analog_channel']=3;d['stimulated_channel']=4
for ch,v in d['channels'].items():v['analog_connected']=ch=='4'
d['board_test_note']='Route guard3 failed; control probe confirms DAC01 still ADC4. Requested move both USB to3; DAC23 J6 route not newly verified.';p.write_text(json.dumps(d,indent=2)+'\n')
p=Path('/srv/codex-hil-nvme/pm12-campaigns/active.json');d=json.loads(p.read_text());d.update(analog_channel=4,requested_analog_channel=3,status='Requested3; route control confirms DAC01 still ADC4. Waiting physical USB move; no full3 scan');d['verified_connections']={'channel':4,'direct_adc_input':'J8','direct_adc_dac_channels':[0,1],'verification_status':'ADC4 control response verified; ADC3 no response; DAC23 route last declared4'};p.write_text(json.dumps(d,indent=2)+'\n')
text='''Latest route check before requested analog3: DAC01 still observed on ADC4, not3.
Gains A/B:4=-1776.83/-1761.33code/V;3=-1.15/-0.39code/V. Full3 scans not started.
Both USB move to3 pending; DAC01→J8,23→J6. Safe park01=1/1V,23=1.024/2.048V.
Prior selected results unchanged;104-page report remains current. No programming/clock/Kasli changes.
[Route diagnostic and raw captures](evidence-usb03-route-20261117/README.md).

'''
p=repo/'diagnostics/pm12/acceptance/ACTIVE_CAMPAIGN.md';p.write_text(text+p.read_text());p=Path('/home/codex-hil/FIT_PM_FW_uPC/docs/pm12_current_hardware_state.md');p.write_text('## Route check: requested3, direct ADC USB still4\n\n'+text+p.read_text())
m={str(p.relative_to(e)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(e.rglob('*'))if p.is_file()and p.name!='files.sha256.json'};(e/'files.sha256.json').write_text(json.dumps(m,indent=2)+'\n')
print('ROUTE_DIAGNOSTIC_SAVED')
