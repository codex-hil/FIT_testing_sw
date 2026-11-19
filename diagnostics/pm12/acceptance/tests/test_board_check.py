import unittest,tempfile,json,struct,hashlib,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from board_check import validate, cleanup
from unittest.mock import patch
class ClockAndTransport(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name);uid='PM12-K7-0000000000000123';buffers=[]
  for b in [0,1]:
   for ch in range(1,13):
    name=f'{b}-{ch}.bin';data=struct.pack('<4096H',*([100|(b<<12)]*4096));(self.p/name).write_bytes(data);buffers.append(dict(file=name,channel=ch,bank=b,sha256=hashlib.sha256(data).hexdigest()))
  regs=[0]*13;regs[0]=0x434c4b52;regs[2]=1;regs[5]=384;regs[12]=2048;words=[0]*8192;words[:4]=[384,(640<<16)|256,(0x18<<16)|256,(384<<16)|1];(self.p/'clock.bin').write_bytes(struct.pack('<8192I',*words))
  self.r=dict(board_uid=uid,identity_before={'uid':uid},identity_after={'uid':uid},mcu={'status':'PASS'},network={'buffers':buffers,'bytes_compared':393216},trials=[dict(signature=0x4844,expected=0x4844,sys_loss_trigger=False,pass_=True,registers=regs,raw_file='clock.bin',index=0)])
  self.save()
 def save(self):(self.p/'measurement.json').write_text(json.dumps(self.r))
 def test_valid_capture(self):self.assertEqual(validate(self.p,1)['status'],'PASS')
 def test_reported_success_does_not_hide_bad_clock_counts(self):
  words=list(struct.unpack('<8192I',(self.p/'clock.bin').read_bytes()));words[1]=(640<<16)|259;(self.p/'clock.bin').write_bytes(struct.pack('<8192I',*words))
  with self.assertRaisesRegex(ValueError,'edge-count'):validate(self.p,1)
 def test_no_reference_window_rejected(self):
  words=list(struct.unpack('<8192I',(self.p/'clock.bin').read_bytes()));words[2]=256;(self.p/'clock.bin').write_bytes(struct.pack('<8192I',*words))
  with self.assertRaisesRegex(ValueError,'No valid'):validate(self.p,1)
 def test_mixed_identity_rejected(self):
  self.r['identity_after']['uid']='PM12-K7-0000000000000456';self.save()
  with self.assertRaisesRegex(ValueError,'Mixed'):validate(self.p,1)
 def test_partial_dossier_preserves_full_matrix_and_offline_buffers(self):
  import board_session as b
  import dossier
  from session_board_export import build, matrix
  self.assertEqual(len(matrix()),89)
  # The shared validator requires twelve trials for a released board check.
  self.r['trials']=[dict(self.r['trials'][0],index=i) for i in range(12)]
  self.r.update(test='board-final',status='PASS',finished_utc='2026-11-19T00:00:00Z')
  self.save()
  root=self.p/'export-test';uid=self.r['board_uid'];session=root/uid/'session'
  measurement=session/'measurements'/'explicit-board-check'
  measurement.mkdir(parents=True)
  for p in self.p.iterdir():
   if p.is_file():shutil.copy2(p,measurement/p.name)
  cfg={'board_uid':uid}
  b.write(session/'station.json',cfg)
  b.write(session/'session.json',dict(board_uid=uid,status='READY',station_sha256=b.sha(session/'station.json'),
          measurements=['measurements/explicit-board-check'],identity={'uid':uid}))
  b.write(measurement/'files.sha256.json',b.files(measurement))
  result=build(session,measurement,root/'release')
  self.assertEqual(result['disposition'],'REVIEW')
  self.assertEqual(result['coverage']['required_cases'],89)
  self.assertEqual(result['coverage']['statuses'],{'NOT_RUN':85,'COMPLETE':1,'PASS_FUNCTIONAL':3})
  self.assertEqual(dossier.verify(root/'release/dossier')['integrity'],'PASS')
  exported=b.read(root/'release/report-inputs/measurements.json')
  self.assertEqual(len(exported['cases']),89)
  # A changed raw buffer is rejected before creating another release.
  (measurement/'0-1.bin').write_bytes(b'bad')
  with self.assertRaisesRegex(ValueError,'modified'):build(session,measurement,root/'bad-release')
class UndeclaredAnalogCleanup(unittest.TestCase):
 def test_unassigned_fitting_does_not_touch_external_dac_or_phase(self):
  cfg={'stimulated_channel':None,'fitted_channels':[],'channels':{}}
  with patch('board_check.session.inhibit') as inhibit:
   cleanup(cfg)
   inhibit.assert_called_once_with(cfg,None,None,park=False)
 def test_fitted_but_unconfirmed_usb_does_not_drive_dac(self):
  cfg={'stimulated_channel':3,'fitted_channels':[3],
       'channels':{'3':{'analog_connected':False,'integrator_connected':False}}}
  with patch('board_check.session.inhibit') as inhibit:
   cleanup(cfg)
   inhibit.assert_called_once_with(cfg,None,None,park=False)
 def test_declared_usb_route_retains_parking(self):
  cfg={'stimulated_channel':3,'fitted_channels':[3],
       'channels':{'3':{'analog_connected':True}}}
  with patch('board_check.session.inhibit') as inhibit:
   cleanup(cfg)
   inhibit.assert_called_once_with(cfg,0,3,park=True)
if __name__=='__main__':unittest.main()
