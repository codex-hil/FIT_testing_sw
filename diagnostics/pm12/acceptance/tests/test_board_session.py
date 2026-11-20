import json,tempfile,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import board_session as b
class Sessions(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
  self.cfg={'board_uid':'PM12-K7-0000000000000123','board_serial':'3','python':sys.executable,'expected_build_id':'ff2f746c','fitted_channels':[3,4,5,6],'stimulated_channel':6,'channels':{'6':{'analog_connected':True,'integrator_connected':True,'dac_channels':[0,1],'integrator_dac_channels':[2,3]}}}
 def session(self):
  p=self.root/self.cfg['board_uid']/'run';p.mkdir(parents=True);b.write(p/'station.json',self.cfg);b.write(p/'session.json',{'board_uid':self.cfg['board_uid'],'status':'READY','measurements':[],'station_sha256':b.sha(p/'station.json')});return p
 def test_enrollment_replaces_old_identity_and_clears_routing(self):
  import contextlib,types
  station=self.root/'seed.json';b.write(station,self.cfg)
  power=types.SimpleNamespace(wait_power_good=lambda *a:[])
  console=types.SimpleNamespace(capture=lambda *a:{'reply':'Board S/N: 1804\\r\\n'})
  import station as station_module
  with patch.dict(sys.modules,{'pm12_power':power,'pm12_console_regression':console}),patch.object(b,'locks',lambda cfg:contextlib.nullcontext(())),patch.object(station_module,'load_dependencies'),patch.object(station_module,'console',lambda cfg:contextlib.nullcontext(object())),patch.object(station_module,'read_dna',return_value='0000000000000456'):
   out=b.enroll(station,self.root/'enrollment',self.root/'registry.json')
  cfg=b.read(out/'station-enrolled.json');self.assertEqual(cfg['board_uid'],'PM12-K7-0000000000000456');self.assertEqual(cfg['board_serial'],'1804');self.assertIsNone(cfg['stimulated_channel']);self.assertEqual(cfg['fitted_channels'],[]);self.assertFalse(cfg['channels']['6']['integrator_connected'])
 def test_enrollment_error_preserves_mcu_and_no_guessed_uid(self):
  import contextlib,types
  station=self.root/'seed.json';b.write(station,self.cfg)
  power=types.SimpleNamespace(wait_power_good=lambda *a:[{'reply':'raw PGOOD'}])
  console=types.SimpleNamespace(capture=lambda *a:{'reply':'Board S/N: 1803\\r\\n'})
  import station as station_module
  with patch.dict(sys.modules,{'pm12_power':power,'pm12_console_regression':console}),patch.object(b,'locks',lambda cfg:contextlib.nullcontext(())),patch.object(station_module,'load_dependencies'),patch.object(station_module,'console',lambda cfg:contextlib.nullcontext(object())),patch.object(station_module,'read_dna',side_effect=ValueError('No devices detected')):
   with self.assertRaises(ValueError):b.enroll(station,self.root/'enrollment',self.root/'registry.json')
  paths=list((self.root/'enrollment/enrollments').iterdir());self.assertEqual(len(paths),1)
  record=b.read(paths[0]/'enrollment.json');self.assertEqual(record['status'],'ERROR');self.assertIsNone(record['board_uid'])
  self.assertIn('1803',record['mcu_reply']['reply']);self.assertFalse((self.root/'registry.json').exists())
  self.assertEqual(b.read(paths[0]/'files.sha256.json'),b.files(paths[0]))
 def test_legacy_phase_mode_rejected_before_hardware(self):
  import subprocess
  script=Path(__file__).resolve().parents[2]/'cfd_simulator/phase_scan.py'
  out=self.root/'should-not-exist'
  r=subprocess.run([sys.executable,str(script),'--afe','6','--lanes','8,9','--restore-code','0','--out',str(out)],capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('Legacy output-release mode retired',r.stderr);self.assertFalse(out.exists())
 def test_wrong_image_hash_inhibits_programming(self):
  station=self.root/'station.json';b.write(station,self.cfg);bit=self.root/'image.bit';bit.write_bytes(b'bad')
  with patch.object(b,'locks') as locks:
   with self.assertRaisesRegex(ValueError,'SHA256'):b.load_sram(station,self.root/'load',bit,'0'*64)
   locks.assert_not_called()
 def test_wrong_board_configuration_rejected(self):
  p=self.session();s=b.read(p/'session.json');s['board_uid']='PM12-K7-0000000000000456';b.write(p/'session.json',s)
  with self.assertRaises(ValueError):b.load_session(p)
 def test_modified_station_rejected(self):
  p=self.session();d=b.read(p/'station.json');d['board_serial']='4';b.write(p/'station.json',d)
  with self.assertRaises(ValueError):b.load_session(p)
 def test_wrong_channel_rejected_before_hardware(self):
  with self.assertRaises(ValueError):b.plan(self.cfg,'adc',5,self.root,'str-rise',257,None)
 def test_missing_route_rejected(self):
  self.cfg['channels']['6']['integrator_connected']=False
  with self.assertRaises(ValueError):b.plan(self.cfg,'integrator',6,self.root,'before-str',257,['1.024:2.048'])
 def test_voltage_limit_rejected_before_hardware(self):
  for v in ['4:1','nan:1','1:inf']:
   with self.assertRaises(ValueError):b.plan(self.cfg,'integrator',6,self.root,'before-str',257,[v])
 def test_explicit_configuration_in_command(self):
  cmd=b.plan(self.cfg,'adc',6,self.root,'str-rise',257,None)
  self.assertEqual(cmd[cmd.index('--afe')+1],'6');self.assertEqual(cmd[cmd.index('--board-serial')+1],'3');self.assertIn('str-rise',cmd)
 def test_hash_tampering_detected(self):
  p=self.session();q=p/'measurements'/'a';q.mkdir(parents=True);b.write(q/'measurement.json',{'board_uid':self.cfg['board_uid']});(q/'raw.bin').write_bytes(b'abc');b.write(q/'files.sha256.json',b.files(q));s=b.read(p/'session.json');s['measurements']=['measurements/a'];b.write(p/'session.json',s);self.assertEqual(b.verify(p)['integrity'],'PASS');(q/'raw.bin').write_bytes(b'def')
  with self.assertRaises(ValueError):b.verify(p)
 def test_wrong_live_identity_never_runs_measurement_or_cleanup(self):
  import contextlib
  p=self.session()
  with patch.object(b,'locks',lambda cfg:contextlib.nullcontext(())),patch.object(b,'identity',side_effect=ValueError('wrong DNA')),patch.object(b,'inhibit') as inhibit,patch.object(b.subprocess,'run') as run:
   r=b.measure(p,'integrator',6,0,'before-str',257,['1.024:2.048']);self.assertEqual(r['status'],'ERROR');inhibit.assert_not_called();run.assert_not_called()
if __name__=='__main__':unittest.main()
