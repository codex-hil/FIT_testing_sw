"""Offline regression using archived PM2 captures; never opens hardware."""
import json
from pathlib import Path
import sys,tarfile,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from campaign_reset_adapter import validate
class ResetEvidenceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();root=Path(cls.tmp.name)
  archive=Path(__file__).resolve().parents[2]/'cfd_simulator/evidence-reset-rdson-20261117/raw-build-hardware.tar.gz'
  with tarfile.open(archive) as t:t.extractall(root,filter='data')
  cls.source=root/'pm12-reset-rdson-20261117'
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def test_raw_replay_and_effective_resistance(self):
  r,s,m,c,n=validate(self.source)
  self.assertEqual(n,162)
  self.assertAlmostEqual(s['fits']['P']['nominal_R_on_ohm'],68.5396805,places=5)
  self.assertEqual(len(c),2)
 def test_false_restoration_flag_rejected(self):
  p=self.source/'hardware/status.json';old=p.read_text()
  try:
   d=json.loads(old);d['restored_all_cpld_rows']=False;p.write_text(json.dumps(d))
   with self.assertRaises(ValueError):validate(self.source)
  finally:p.write_text(old)
 def test_raw_corruption_rejected(self):
  p=self.source/'hardware/point000-bank0-0.bin';old=p.read_bytes()
  try:
   p.write_bytes(bytes([old[0]^1])+old[1:])
   with self.assertRaisesRegex(ValueError,'hash'):validate(self.source)
  finally:p.write_bytes(old)
 def test_restoration_claim_requires_matching_readback(self):
  p=self.source/'hardware/restored-nv.log';old=p.read_text()
  try:
   p.write_text(old.replace('ARRAY 1 A 0 ', 'INVALID 1 A 0 ',1))
   with self.assertRaises(ValueError):validate(self.source)
  finally:p.write_text(old)
if __name__=='__main__':unittest.main()
