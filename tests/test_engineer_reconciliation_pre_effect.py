"""Offline requalification after blocking lookup and immediately before an edit."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

try:
    from . import test_engineer_reconciliation_currentness as currentness
except ImportError:
    import test_engineer_reconciliation_currentness as currentness

security = currentness.security


class ReconciliationPreEffect(unittest.TestCase):
    def setUp(self):
        self.current = currentness.ReconciliationCurrentness()
        self.current.setUp()
        self.addCleanup(self.current.doCleanups)
        self.f = self.current.fixture
        self.issue_get = security.issues.issue_get.side_effect

    def changed_owner(self):
        state = security.load_json(self.current.state_path)
        key = next(iter(state['risk_intents']))
        state['risk_intents'][key] = {'scope': 'different-owner', 'token': 'foreign-token'}
        security.write_json(self.current.state_path, state)

    def receipt_and_state(self):
        c = self.current
        return c.old_path.read_bytes(), c.original_intent.read_bytes(), c.state_path.read_bytes()

    def repair_intents(self):
        return [p for p in (self.f.directory / 'intents').glob('*.json') if p != self.current.original_intent]

    def refuse_after_lookup(self, tamper):
        c = self.current
        calls = []
        expected = []

        def blocking_lookup(*args):
            result = self.issue_get(*args)
            calls.append(args)
            if len(calls) == 2:  # Fresh publish's exact before-image lookup, after initial qualification.
                tamper()
                expected.append(self.receipt_and_state())
            return result

        with patch.object(security.issues, 'issue_get', side_effect=blocking_lookup), self.assertRaises(security.Failure):
            c.publish()
        self.assertEqual(1, len(expected), 'Exercise the exact blocking pre-edit lookup')
        self.assertEqual([], self.f.writes, 'No external edit may use stale source or provenance')
        self.assertEqual([], self.repair_intents(), 'Refuse before journaling a new attempt')
        self.assertFalse(security.load_json(c.preview_path)['consumed'])
        self.assertEqual(expected[0], self.receipt_and_state())
        self.assertFalse(security.load_json(c.state_path)['risks'])
        self.assertNotIn('reconciliations', security.load_json(c.state_path))

    def test_head_advanced_during_preedit_lookup_refuses_before_intent_or_consumption(self):
        self.refuse_after_lookup(lambda: self.current.head.__setitem__(0, 'c' * 40))

    def test_new_owning_plan_during_preedit_lookup_refuses_before_attempt(self):
        self.refuse_after_lookup(lambda: (self.f.directory / '04-02-PLAN.md').write_bytes(
            currentness.register('T-04-02').encode()))

    def test_malformed_owning_plan_during_preedit_lookup_refuses_before_attempt(self):
        self.refuse_after_lookup(lambda: (self.f.directory / '04-02-PLAN.md').write_bytes(
            currentness.register('T-04-02').replace('Mitigation Plan', 'Unsupported').encode()))

    def test_captured_raw_security_change_during_preedit_lookup_refuses_before_attempt(self):
        changed = b'Changed reviewed audit\r\nUnicode: \xce\x94\n'
        self.refuse_after_lookup(lambda: self.current.security_report.write_bytes(changed))
        self.assertEqual(changed, self.current.security_report.read_bytes())

    def test_original_preview_bytes_changed_during_preedit_lookup_refuse_before_attempt(self):
        self.refuse_after_lookup(lambda: self.current.old_path.write_bytes(self.current.old_path.read_bytes() + b'\n'))

    def test_original_intent_bytes_changed_during_preedit_lookup_refuse_before_attempt(self):
        self.refuse_after_lookup(lambda: self.current.original_intent.write_bytes(self.current.original_intent.read_bytes() + b'\n'))

    def test_live_reservation_changed_during_preedit_lookup_refuses_before_attempt(self):
        self.refuse_after_lookup(self.changed_owner)

    def test_authored_entry_changed_during_preedit_lookup_refuses_before_attempt(self):
        def changed_entry():
            entries = json.loads(self.current.entries.read_bytes())
            entries[0]['scope_acceptance'] = 'A different authored acceptance condition'
            self.current.entries.write_bytes(json.dumps(entries).encode())
        self.refuse_after_lookup(changed_entry)

    def refuse_after_body_write(self, tamper):
        c = self.current
        original_write = Path.write_bytes
        expected = []

        def blocking_write(path, body):
            count = original_write(path, body)
            if path.name == 'body.md' and path.parent.name.startswith('engineer-security-reconcile-'):
                tamper()
                expected.append(self.receipt_and_state())
            return count

        with patch.object(Path, 'write_bytes', blocking_write), self.assertRaises(security.Failure):
            c.publish()
        self.assertEqual(1, len(expected), 'Exercise the exact publication body-file write')
        self.assertEqual([], self.f.writes)
        self.assertEqual(expected[0], self.receipt_and_state())
        saved = security.load_json(c.preview_path)
        self.assertTrue(saved['consumed'])
        self.assertEqual([], saved['results'])
        intents = self.repair_intents()
        self.assertEqual(1, len(intents))
        intent = security.load_json(intents[0])
        self.assertEqual('attempting', intent['state'])
        self.assertEqual(self.f.url, intent['url'])
        return intent

    def test_head_change_during_body_write_refuses_edit_and_consumed_retry_stays_readonly(self):
        intent = self.refuse_after_body_write(lambda: self.current.head.__setitem__(0, 'c' * 40))
        self.current.head[0] = self.current.preview['revision']
        with self.assertRaises(security.Failure) as error:
            self.current.publish()
        self.assertEqual('security-readback-mismatch', error.exception.code)
        self.assertEqual([], self.f.writes, 'Even a known unchanged provider body cannot authorize a repeat edit')
        self.assertEqual(intent, security.load_json(self.repair_intents()[0]))

    def test_raw_security_change_during_body_write_refuses_edit_with_durable_attempt(self):
        changed = b'Later raw audit\r\n'
        self.refuse_after_body_write(lambda: self.current.security_report.write_bytes(changed))
        self.assertEqual(changed, self.current.security_report.read_bytes())

    def test_live_ownership_change_during_body_write_refuses_edit_with_durable_attempt(self):
        self.refuse_after_body_write(self.changed_owner)

    def test_original_receipt_change_during_body_write_refuses_edit_with_durable_attempt(self):
        self.refuse_after_body_write(lambda: self.current.original_intent.write_bytes(
            self.current.original_intent.read_bytes() + b'\n'))

    def test_unchanged_lookup_and_body_write_preserve_one_edit_then_readonly_recovery(self):
        self.assertFalse(self.current.publish()['ready'])
        self.assertFalse(self.current.publish()['ready'])
        self.assertEqual(1, len(self.f.writes))
        self.assertEqual('complete', security.load_json(self.repair_intents()[0])['state'])
        self.current.assert_originals_preserved()


if __name__ == '__main__':
    unittest.main()
