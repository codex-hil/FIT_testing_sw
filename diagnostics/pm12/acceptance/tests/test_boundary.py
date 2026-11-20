"""Guard/restoration policy and offline reanalysis of measured PM12 vectors."""
import contextlib
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import boundary as t


class BoundaryPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.uid = 'PM12-K7-0000000000000123'
        self.out = self.root / self.uid / 'setup' / 'test'
        self.cfg = {'board_uid': self.uid, 'expected_build_id': 'ff2f746c'}
        self.identity = {'uid': self.uid, 'fpga_ipbus_identity': [0x504d1202, 0x10002, 0xff2f746c],
                         'endpoint_binding': {'status': 'PASS'}}
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.check = self.stack.enter_context(patch.object(t, 'validate_inputs'))
        self.stack.enter_context(patch.object(t, 'snapshot'))
        self.stack.enter_context(patch.object(t.b, 'locks', return_value=contextlib.nullcontext(())))
        self.physical = self.stack.enter_context(patch.object(t, 'physical_identity', return_value=self.identity))
        self.native = self.stack.enter_context(patch.object(t, 'native_test'))
        self.restore = self.stack.enter_context(patch.object(t, 'restore', return_value={'status': 'PASS', 'identity_after': self.identity}))

    def test_success_requires_restoration(self):
        record = t.run(self.cfg, self.out)
        self.assertEqual(record['status'], 'PASS')
        self.assertEqual(record['restoration'], 'PASS')
        self.restore.assert_called_once()

    def test_wrong_dna_never_tests_or_restores(self):
        self.physical.side_effect = ValueError('Wrong DNA')
        record = t.run(self.cfg, self.out)
        self.assertEqual(record['status'], 'ERROR')
        self.native.assert_not_called()
        self.restore.assert_not_called()

    def test_test_failure_still_restores_and_retains_error(self):
        self.native.side_effect = ValueError('Native test failure')
        record = t.run(self.cfg, self.out)
        self.assertEqual(record['status'], 'ERROR')
        self.assertEqual(record['restoration'], 'PASS')
        self.assertIn('Native test failure', record['error'])
        self.restore.assert_called_once()

    def test_failed_restoration_never_passes(self):
        self.restore.side_effect = ValueError('No final image')
        record = t.run(self.cfg, self.out)
        self.assertEqual(record['status'], 'ERROR')
        self.assertEqual(record['restoration'], 'ERROR')
        self.assertEqual(record['static_links'], 'PASS')

    def test_changed_dut_inhibits_restore_programming(self):
        self.physical.side_effect = [self.identity, ValueError('Wrong DNA')]
        record = t.run(self.cfg, self.out)
        self.assertEqual(record['restoration'], 'ERROR')
        self.restore.assert_not_called()

    def test_wrong_hash_never_opens_hardware(self):
        self.check.side_effect = ValueError('checksum mismatch')
        self.assertEqual(t.run(self.cfg, self.out)['status'], 'ERROR')
        self.physical.assert_not_called()
        self.native.assert_not_called()
        self.restore.assert_not_called()

    def test_output_requires_uid_and_is_never_overwritten(self):
        with self.assertRaisesRegex(ValueError, 'UID'):
            t.run(self.cfg, self.root / 'unbound')
        t.run(self.cfg, self.out)
        with self.assertRaises(FileExistsError):
            t.run(self.cfg, self.out)

    def test_offline_hash_tamper_rejected(self):
        t.run(self.cfg, self.out)
        (self.out / 'station.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'modified'):
            t.verify(self.out)


class MeasuredVectors(unittest.TestCase):
    def test_success_marker_does_not_hide_missing_freeze_ack(self):
        import re
        fixtures = Path(__file__).resolve().parents[2] / 'tests/fixtures'
        text = gzip.decompress((fixtures / 'control-pass.log.gz').read_bytes()).decode()
        self.assertTrue(t.controls(text)['passed'])
        def clear_ack(match):
            return match[1] + format(int(match[2],16) & ~(1<<1504),'x')
        changed = re.sub(r'(^CONTROL FREEZE_0_A [0-9]+ )([a-fA-F0-9]+)$',clear_ack,text,flags=re.M)
        with self.assertRaisesRegex(ValueError,'Freeze not acknowledged'):
            t.controls(changed)

    def test_offline_native_summary_recomputed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            fixtures = Path(__file__).resolve().parents[2] / 'tests/fixtures'
            for source, target in [('gateware-pass', 'discover'), ('boundary-pass', 'boundary'), ('control-pass', 'control')]:
                (p / (target + '.log')).write_bytes(gzip.decompress((fixtures / (source + '.log.gz')).read_bytes()))
            (p / 'restore.log').write_text('RESTORE_PASS\n')
            original = {'status': 'PASS', 'restored': True,
                        'gateware': t.analyze((p / 'discover.log').read_text()),
                        'boundary': t.analyze((p / 'boundary.log').read_text(), boundary=True),
                        'controls': t.controls((p / 'control.log').read_text())}
            t.b.write(p / 'report.json', original)
            self.assertTrue(t.validate_native(p)['passed'])
            original['gateware']['matched'] = 167
            t.b.write(p / 'report.json', original)
            with self.assertRaisesRegex(ValueError, 'differs'):
                t.validate_native(p)


if __name__ == '__main__':
    unittest.main()
