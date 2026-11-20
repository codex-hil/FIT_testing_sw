import json,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import dossier as d
class Dossier(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.p=Path(self.t.name);self.uid='PM12-K7-0000000000000123';src=self.p/'source';src.mkdir();d.write(src/'result.json',{'board_uid':self.uid,'channel':1,'status':'PASS'});(src/'raw.bin').write_bytes(b'abc');self.spec={'board_uid':self.uid,'scope':'test','required_cases':['adc:1'],'selections':[{'case':'adc:1','test':'adc','channel':1,'source':str(src),'receipt':'result.json','status':'PASS','basis':'test','method':'v1'}]};d.write(self.p/'spec.json',self.spec)
 def test_relative_selection_survives_relocation_and_different_cwd(self):
  import shutil,os
  self.spec['selections'][0]['source']='source';d.write(self.p/'spec.json',self.spec)
  moved=self.p/'relocated';moved.mkdir();shutil.move(str(self.p/'source'),moved/'source');shutil.move(str(self.p/'spec.json'),moved/'spec.json')
  previous=os.getcwd()
  try:
   os.chdir('/')
   self.assertEqual(d.build(moved/'spec.json',moved/'out')['integrity'],'PASS')
  finally:os.chdir(previous)
 def test_pack_readback_and_no_overwrite(self):
  from package_release import pack
  root=self.p/'release';d.build(self.p/'spec.json',root/'dossier')
  archive=self.p/'release.tar.gz';result=pack(root,archive)
  self.assertEqual(result['archive_readback'],'PASS')
  self.assertEqual(result['sha256'],d.sha(archive))
  with self.assertRaises(FileExistsError):pack(root,archive)
 def test_roundtrip(self):
  r=d.build(self.p/'spec.json',self.p/'out');self.assertEqual(r['integrity'],'PASS');d.materialize(self.p/'out','adc:1',self.p/'extracted');self.assertEqual((self.p/'extracted/raw.bin').read_bytes(),b'abc')
 def test_cannot_promote_failed_receipt(self):
  d.write(self.p/'source/result.json',{'board_uid':self.uid,'channel':1,'status':'FAIL'})
  with self.assertRaises(ValueError):d.build(self.p/'spec.json',self.p/'out')
 def test_wrong_uid_rejected(self):
  d.write(self.p/'source/result.json',{'board_uid':'PM12-K7-0000000000000456','channel':1})
  with self.assertRaises(ValueError):d.build(self.p/'spec.json',self.p/'out')
 def test_missing_case_rejected(self):
  self.spec['required_cases'].append('adc:2');d.write(self.p/'spec.json',self.spec)
  with self.assertRaises(ValueError):d.build(self.p/'spec.json',self.p/'out')
 def test_tamper_rejected(self):
  d.build(self.p/'spec.json',self.p/'out');next((self.p/'out/blobs').iterdir()).write_bytes(b'changed')
  with self.assertRaises(ValueError):d.verify(self.p/'out')
 def test_wrong_channel_rejected(self):
  self.spec['selections'][0]['channel']=2;d.write(self.p/'spec.json',self.spec)
  with self.assertRaises(ValueError):d.build(self.p/'spec.json',self.p/'out')
if __name__=='__main__':unittest.main()
