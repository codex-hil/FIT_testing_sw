import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from endpoint_binding import count,check_delta
class Binding(unittest.TestCase):
 def test_decode_and_wrap(self):
  self.assertEqual(count(f'{(0x504d5a04|(0x504d4442<<208)|(123<<432)):0131x}'),123)
  self.assertEqual(check_delta(0xfffffff0,5,21),21)
 def test_supported_bus_has_four_strobe_cycles_per_register_read(self):
  self.assertEqual(check_delta(19812092,19812216,4*31),124)
 def test_wrong_physical_network_peer_rejected(self):
  with self.assertRaises(ValueError):check_delta(42,42,19)
 def test_unsupported_layout_rejected(self):
  with self.assertRaises(ValueError):count('0')
if __name__=='__main__':unittest.main()
