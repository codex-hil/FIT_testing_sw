"""Production policy/route tests, no hardware access."""
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(HERE))
from suite import validate_production_plan,collect
from production_integrator import make_plan
from campaign import initialize
class ProductionPolicyTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.cfg=dict(board_uid='PM12-K7-0000000000000123',routing_backend='fixed',stimulated_channel=2,
                channels={'2':dict(integrator_connected=True,integrator_dac_channels=[4,5])})
  self.station=self.root/'station.json';self.station.write_text(json.dumps(self.cfg))
 def plan(self,board=None,channel=2):
  return make_plan(self.station,board or self.cfg['board_uid'],channel,self.root/'out',sys.executable,sys.executable)
 def test_default_scope_has_no_cpld_programming_diagnostic(self):
  profile=json.loads((HERE/'profiles/campaign-four-cfd.json').read_text())
  self.assertFalse(profile['cpld_programming']);self.assertFalse(profile['automatic_gateware_fallback'])
  self.assertNotIn('integrator-reset',[t['id'] for t in profile['tests']])
 def test_diagnostic_commands_cannot_enter_production_runner(self):
  for script in ['acceptance/diagnostic_integrator_reset.py','acceptance/run_integrator_reset.py','cfd_simulator/reset_rdson.py','cfd_simulator/slow_integrator/run.py']:
   plan=dict(steps=[dict(command=['{python}','{repo}/diagnostics/pm12/'+script])])
   with self.assertRaises(ValueError):validate_production_plan(plan)
 def test_production_integrator_profile_accepted(self):
  validate_production_plan(json.loads((HERE/'profiles/production-integrator.json').read_text()))
 def test_board_and_route_mismatch_fail_before_execution(self):
  with self.assertRaises(ValueError):self.plan(board='wrong')
  with self.assertRaises(ValueError):self.plan(channel=3)
 def test_dac_pair_is_configuration_not_channel_number(self):
  plan=self.plan();self.assertEqual(plan['dac_channels'],[4,5]);self.assertFalse(plan['cpld_programming'])
  self.assertFalse(plan['gateware_fallback']);self.assertFalse((self.root/'out').exists())
 def test_unknown_mux_backend_not_silently_accepted(self):
  self.cfg['routing_backend']='future-usb-mux';self.station.write_text(json.dumps(self.cfg))
  with self.assertRaises(ValueError):self.plan()
 def test_rejected_plan_never_acquires_a_board_lease(self):
  p=self.root/'plan.json';p.write_text(json.dumps(dict(mode='DIAGNOSTIC',steps=[])))
  with patch('suite.acquire',side_effect=AssertionError('Hardware touched')):
   with self.assertRaises(ValueError):collect(self.station,p,self.root/'out',[2])
 def test_sealed_production_scope_cannot_require_reset_programming(self):
  p=self.root/'protocol.json';p.write_text(json.dumps(dict(mode='PRODUCTION',tests=[dict(id='integrator-reset',scope='channel')])))
  with self.assertRaises(ValueError):initialize(self.root/'campaign',self.cfg['board_uid'],'1803',p)
 def test_old_reset_entry_point_fails_without_importing_hardware(self):
  r=subprocess.run([sys.executable,str(HERE/'run_integrator_reset.py')],capture_output=True,text=True)
  self.assertNotEqual(r.returncode,0);self.assertIn('Removed from production',r.stderr)
if __name__=='__main__':unittest.main()
