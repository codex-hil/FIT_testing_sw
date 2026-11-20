"""Decoder guards for actual measured BYPASS and network diagnostic layouts."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jtag_transport_probe import decode


class TransportDecoder(unittest.TestCase):
    def test_reference_analysis_invalidates_assumed_125mhz(self):
        from station_probe import analyze_record
        record={'board_uid':'PM12-K7-0000000000000123','network':{'kasli':{'status':'COMPLETE','reference_window':{
            'before':[1619318652,2957146646],'after':[2821700358,3558340692],
            'elapsed_host_s':10.0003193320008,'reference_hz_from_nominal125MHz':125000663.890673}}}}
        result=analyze_record(record)
        self.assertIn('reference_hz_from_nominal125MHz',result['invalidated_legacy_fields'])
        self.assertNotIn('reference_hz_from_nominal125MHz',result['reference_window'])
        self.assertGreater(result['reference_window']['reference_hz_host'],120200000)
        self.assertLess(result['reference_window']['reference_hz_host'],120270000)
        self.assertEqual(result['acceptance'],'NOT_EVALUATED')

    def test_measured_thirteen_device_bypass(self):
        text='''BYPASS 0000000000000000 0000000000000000
BYPASS ffffffffffffffff ffffffffffffe000
BYPASS 0123456789abcdef 68acf13579bde000
BYPASS fedcba9876543210 97530eca86420000
BYPASS a5a55a5af00f0ff0 ab4b5e01e1fe0000
'''
        result=decode(text)
        self.assertTrue(result['bypass_pass'])
        self.assertEqual(result['measured_delay_candidates'],[13])
        with self.assertRaises(ValueError):decode(text.splitlines()[0])
        self.assertFalse(decode(text.replace('68acf13579bde000','0000000000000000'))['bypass_pass'])


if __name__=='__main__':unittest.main()
