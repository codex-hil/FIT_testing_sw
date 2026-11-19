import unittest,tempfile,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'cfd_simulator'))
from analysis_identity import require_same
class Identity(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name)
 def folder(self,name,uid):
  p=self.root/name;p.mkdir();(p/'station.json').write_text(json.dumps({'board_uid':uid}));return p
 def test_same_board(self):self.assertEqual(require_same([self.folder('a','PM12-K7-0000000000000123'),self.folder('b','PM12-K7-0000000000000123')]),'PM12-K7-0000000000000123')
 def test_mixed_boards_fail(self):
  with self.assertRaises(ValueError):require_same([self.folder('a','PM12-K7-0000000000000123'),self.folder('b','PM12-K7-0000000000000456')])
 def test_missing_context_fail(self):
  with self.assertRaises(ValueError):require_same([self.root])
if __name__=='__main__':unittest.main()
