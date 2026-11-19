import unittest,tempfile,json,struct,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from board_check import validate
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
if __name__=='__main__':unittest.main()
