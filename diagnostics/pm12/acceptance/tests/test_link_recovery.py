"""Only the established PM PHY reset is allowed; profiles/DIO stay untouched."""
import sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import link_recovery as r


class FakeClient:
    def __init__(self):
        self.values={0:0x52504831,4:0x10002,0xb0:3,0xd0:0x49504232,0xe0:0,
                     0x100:0,0x104:15,0x114:0x504d4c31,0x120:1,0x124:1,
                     0x13c:0x42524731,0x144:1,0x150:9}
        self.writes=[];self.closed=False
    def read(self,address):return [self.values[address*4]]
    def write(self,address,values):self.writes.append((address,values));self.values[address*4]=values[0]
    def close(self):self.closed=True


class RecoveryPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name);self.client=FakeClient()
    def call(self):
        with patch.object(r,'load_dependencies'),patch.dict(sys.modules,{'client':types.SimpleNamespace(Client=lambda host:self.client)}),patch.object(r.time,'sleep'):
            return r.restart({},self.out)
    def test_only_pm_phy_reset_pulsed_and_cleared(self):
        before=dict(self.client.values);result=self.call()
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(self.client.writes,[(0x40,[256]),(0x40,[0])])
        self.assertEqual(before,self.client.values);self.assertTrue(self.client.closed)
    def test_wrong_translator_never_written(self):
        self.client.values[0]=0
        with self.assertRaises(ValueError):self.call()
        self.assertEqual(self.client.writes,[])
    def test_unexpected_clock_profile_never_written(self):
        self.client.values[0xb0]=2
        with self.assertRaises(ValueError):self.call()
        self.assertEqual(self.client.writes,[])
    def test_nonpacket_mode_never_overridden(self):
        self.client.values[0x100]=16
        with self.assertRaises(ValueError):self.call()
        self.assertEqual(self.client.writes,[])


if __name__=='__main__':unittest.main()
