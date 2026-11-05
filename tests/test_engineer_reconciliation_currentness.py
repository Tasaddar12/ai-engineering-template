"""Current snapshot qualification around offline publication effects and retries."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

try:
    from . import test_engineer_publication_boundaries as publication
except ImportError:
    import test_engineer_publication_boundaries as publication

security = publication.security
REAL_INPUTS, REAL_DIGEST = security._inputs, security.digest


def register(identifier='T-04-01'):
    return ('<threat_model>\n'
            '| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |\n'
            '|---|---|---|---|---|---|\n'
            '| ' + identifier + ' | Tampering | owner | high | mitigate | Refuse foreign owner |\n'
            '</threat_model>\n')


class ReconciliationCurrentness(unittest.TestCase):
    def setUp(self):
        self.fixture = publication.AnchorReconciliation()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        _, old_path, self.original_intent, self.state_path = f.repair_fixture()
        risk = {**publication.entry(), 'match_review': {'disposition': 'no-match',
                'evidence': 'Offline explicit reviewed fixture', 'reviewed_issue_urls': [], 'reviewed_pr_urls': []}}
        self.plan = f.directory / risk['plan']
        self.plan.write_bytes(register().encode())
        self.entries = f.directory / 'original-entries.json'
        self.entries.write_bytes(json.dumps([risk]).encode())
        original = security.load_json(old_path)
        original['entries'] = [risk]
        self.security_report = f.directory / '04-SECURITY.md'
        self.security_report.write_bytes(b'Original source audit\r\n')
        sources = [self.plan, self.security_report, self.entries]
        original['source_files'] = [str(p) for p in sources]
        original['source_digest'] = REAL_DIGEST(sources, base=f.directory)
        f.preview['source_digest'] = original['source_digest']
        self.old_token = f.resign_original(old_path, self.original_intent, self.state_path, original)
        self.old_path = old_path.parent / (self.old_token + '.json')
        self.original_receipts = self.old_path.read_bytes(), self.original_intent.read_bytes()
        f.stack.enter_context(patch.object(security, 'safe_path', side_effect=lambda p:
            self.entries if str(p) == 'original-entries.json' else Path(p)))
        f.stack.enter_context(patch.object(security, 'digest', side_effect=lambda paths:
            REAL_DIGEST(paths, base=f.directory)))
        self.inputs = f.stack.enter_context(patch.object(security, '_inputs', side_effect=REAL_INPUTS))
        self.head = ['b' * 40]
        f.stack.enter_context(patch.object(security, '_head', side_effect=lambda: self.head[0]))
        self.preview = f.repair_preview(self.old_token)
        self.token = self.preview['preview_token']
        self.preview_path = self.old_path.parent / (self.token + '.json')
        self.target = f.url + '#actual-provider-proof'

    def publish(self):
        return self.fixture.repair_publish(self.old_token, self.token)

    def assert_originals_preserved(self):
        self.assertEqual(self.original_receipts, (self.old_path.read_bytes(), self.original_intent.read_bytes()))

    def assert_effect_recoverable_without_registration(self, before):
        f = self.fixture
        self.assertEqual(before, self.state_path.read_bytes())
        self.assert_originals_preserved()
        saved = security.load_json(self.preview_path)
        self.assertTrue(saved['consumed'])
        self.assertEqual([{'key': self.preview['operations'][0]['key'], 'url': f.url}], saved['results'])
        intents = [security.load_json(p) for p in (f.directory / 'intents').glob('*.json')]
        repair = next(i for i in intents if ':anchor-reconcile:' in i['operation']['key'])
        self.assertEqual('complete', repair['state'])
        self.assertEqual(f.url, repair['url'])
        self.assertEqual(1, len(f.writes))

    def test_new_head_advanced_during_html_refuses_registration_and_recovers_readonly(self):
        before = self.state_path.read_bytes()

        def advanced(*args):
            self.head[0] = 'c' * 40  # Original ancestor and all captured bytes still match.
            return {publication.entry()['key']: self.target}, []

        with patch.object(security, 'rendered_targets', side_effect=advanced), self.assertRaises(security.Failure):
            self.publish()
        self.assert_effect_recoverable_without_registration(before)
        self.head[0] = self.preview['revision']
        with patch.object(security, 'rendered_targets', return_value=({publication.entry()['key']: self.target}, [])):
            self.assertTrue(self.publish()['ready'])
        self.assertEqual(1, len(self.fixture.writes))

    def test_consumed_pending_retry_reenumerates_new_owning_plan_before_any_write(self):
        self.assertFalse(self.publish()['ready'])
        (self.fixture.directory / '04-02-PLAN.md').write_bytes(register('T-04-02').encode())
        before = self.state_path.read_bytes()
        self.inputs.reset_mock()
        with patch.object(security, 'write_json', wraps=security.write_json) as writes, \
                patch.object(security, 'rendered_targets', return_value=({publication.entry()['key']: self.target}, [])), \
                self.assertRaises(security.Failure):
            self.publish()
        self.assertGreater(self.inputs.call_count, 0)
        writes.assert_not_called()
        self.assertEqual(before, self.state_path.read_bytes())
        self.assertEqual(1, len(self.fixture.writes))
        self.assert_originals_preserved()

    def test_consumed_pending_retry_parses_new_malformed_register_before_any_write(self):
        self.assertFalse(self.publish()['ready'])
        (self.fixture.directory / '04-02-PLAN.md').write_bytes(register('T-04-02').replace('Mitigation Plan', 'Unsupported').encode())
        before = self.state_path.read_bytes()
        self.inputs.reset_mock()
        with patch.object(security, 'write_json', wraps=security.write_json) as writes, \
                patch.object(security, 'rendered_targets', return_value=({publication.entry()['key']: self.target}, [])), \
                self.assertRaises(security.Failure) as error:
            self.publish()
        self.assertEqual('invalid-plan-threat-register', error.exception.code)
        self.assertGreater(self.inputs.call_count, 0)
        writes.assert_not_called()
        self.assertEqual(before, self.state_path.read_bytes())
        self.assertEqual(1, len(self.fixture.writes))
        self.assert_originals_preserved()

    def test_new_matching_source_added_during_html_refuses_registration(self):
        before = self.state_path.read_bytes()

        def added(*args):
            (self.fixture.directory / '04-REVIEW.md').write_bytes(b'New current review\n')
            return {publication.entry()['key']: self.target}, []

        with patch.object(security, 'rendered_targets', side_effect=added), self.assertRaises(security.Failure):
            self.publish()
        self.assert_effect_recoverable_without_registration(before)

    def test_captured_security_bytes_drift_during_html_refuses(self):
        before = self.state_path.read_bytes()
        changed = b'Changed audit retains exact CRLF\r\n'

        def changed_audit(*args):
            self.security_report.write_bytes(changed)
            return {publication.entry()['key']: self.target}, []

        with patch.object(security, 'rendered_targets', side_effect=changed_audit), self.assertRaises(security.Failure):
            self.publish()
        self.assertEqual(changed, self.security_report.read_bytes())
        self.assert_effect_recoverable_without_registration(before)

    def test_consumed_retry_validates_all_authored_values_without_rebuilding(self):
        self.assertFalse(self.publish()['ready'])
        before = self.state_path.read_bytes()
        real_values = REAL_INPUTS
        for field in (*security.FIELDS, 'match_review', 'additional_authored_fact'):
            def changed(args, ctx):
                entries, sources, threats = real_values(args, ctx)
                entries[0][field] = 'Changed authored evidence'
                return entries, sources, threats
            with self.subTest(field=field), patch.object(security, '_inputs', side_effect=changed), \
                    patch.object(security, 'write_json', wraps=security.write_json) as writes, \
                    self.assertRaises(security.Failure):
                self.publish()
            writes.assert_not_called()
            self.assertEqual(before, self.state_path.read_bytes())
        self.assertEqual(1, len(self.fixture.writes))
        self.assert_originals_preserved()

    def test_unchanged_current_snapshot_registers_and_consumed_retry_rechecks_inputs(self):
        self.assertFalse(self.publish()['ready'])
        self.inputs.reset_mock()
        with patch.object(security, 'rendered_targets', return_value=({publication.entry()['key']: self.target}, [])):
            self.assertTrue(self.publish()['ready'])
            self.assertGreaterEqual(self.inputs.call_count, 2, 'Revalidate before state writes and after provider calls')
            self.assertTrue(self.publish()['ready'])
        self.assertEqual(1, len(self.fixture.writes))
        self.assert_originals_preserved()


if __name__ == '__main__':
    unittest.main()
