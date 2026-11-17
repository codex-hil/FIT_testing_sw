"""Software-only balance estimator checks; never opens a board or instrument."""
import unittest
from balance20 import align,pair,root_estimate
class Balance20Tests(unittest.TestCase):
 def test_capture_origin_does_not_change_signed_pair_difference(self):
  reference=[270,271,100,99]
  for shift in range(4):
   waveform=reference[shift:]+reference[:shift]
   result=align(waveform*255+waveform[:3],reference)
   self.assertEqual(result['mean_change_code'],1)
   self.assertEqual(result['template'],reference)
 def test_reference_tracks_negative_change_without_reclassifying_pair(self):
  result=align([272,269,100,99]*256,[270,271,100,99])
  self.assertEqual(result['mean_change_code'],-3)
 def test_clipping_and_ambiguous_registration_rejected(self):
  for samples in [[270,271,0,99]*256,[150]*1024]:
   with self.assertRaises(ValueError):align(samples,[270,271,100,99])
 def test_single_leg_100uV_step_and_common_translation(self):
  self.assertEqual(pair(.0082,.005),[1.0372,2.053])
  self.assertEqual(round(pair(.0083,0)[0]-pair(.0082,0)[0],7),.0001)
 def test_known_signed_zero(self):
  def point(delta,change):
   return dict(delta_V=delta,captures=[dict(bank=0,valid=True,pair=dict(mean_change_code=change)) for _ in range(3)])
  self.assertAlmostEqual(root_estimate([point(.001,1),point(.003,-1)],0),.002)
if __name__=='__main__':unittest.main()
