"""Reconcile actual receipts/provider payloads through the public runtime CLI."""
import json
import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

import yaml

RUNTIME = Path(__file__).resolve().parents[1] / '.ai/runtime/phase.py'
sys.path.insert(0, str(RUNTIME.parent))
from lib.evidence_reconciliation import reconcile
from lib.paths import Workspace
from lib.results import VerbError
from lib.verification_checks import digest
REPORT = '.planning/phases/01-test/01-VERIFICATION.md'


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.write('.gitignore', '.planning/verification-receipts/\n')
        self.write('.planning/phases/01-test/01-CONTEXT.md', 'owned phase')
        self.write('check.py', "print('PRIVATE OUTPUT')\n")
        self.command = dict(command=[sys.executable, 'check.py'], environment=['PATH'])
        self.configure()
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def configure(self):
        self.write('.planning/config.yaml', yaml.safe_dump({'verification': {'commands': [self.command]}}))

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True, text=True,
                              check=True).stdout.strip()

    def commit(self):
        self.git('add', '-A')
        self.git('commit', '-qm', 'fixture')

    def cli(self, verb, *args):
        completed = subprocess.run([sys.executable, str(RUNTIME), 'query', verb, *args], cwd=self.root,
                                   env=dict(os.environ, PYTHONIOENCODING='utf-8'), capture_output=True,
                                   text=True, encoding='utf-8', timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        return json.loads(completed.stdout)

    def reconcile(self, evidence, claim=None, kind='local', *args):
        path = Path(self.temp.name) / 'private-evidence.json'
        path.write_text(json.dumps(evidence), encoding='utf-8')
        return self.cli('verification.reconcile-evidence', '--evidence-file', str(path),
                        '--claimed-revision', claim or self.head, '--expected-head', self.head,
                        '--kind', kind, *args)

    def live(self, evidence):
        with patch('lib.delivery.gh', return_value=SimpleNamespace(stdout=json.dumps(evidence))) as read:
            result = reconcile(Workspace(self.root), None, self.head, self.head, kind='github',
                               provider_run='42', repository='example/project')
        read.assert_called_once()
        self.assertEqual(read.call_args.args[1:], ('api', 'repos/example/project/actions/runs/42'))
        return result

    def test_fresh_and_reused_receipts_pass_without_output_disclosure(self):
        for _ in range(2):
            evidence = self.cli('verification.run-checks')
            result = self.reconcile(evidence)
            self.assertEqual(result['classification'], 'Passed', result)
            self.assertNotIn('PRIVATE OUTPUT', json.dumps(result))
            self.assertEqual(result['observations'][0]['actual_revision'], self.head)

    def test_claim_mismatch_keeps_actual_success_unverified(self):
        result = self.reconcile(self.cli('verification.run-checks'), '0' * 40)
        self.assertEqual(result['classification'], 'Unverified')
        self.assertEqual(result['terminal_result'], 'Passed')
        self.assertIn('claimed tested SHA', result['reason'])

    def test_new_invocation_sha_does_not_relabel_cached_actual_sha(self):
        self.cli('verification.run-checks')
        original = self.head
        self.git('commit', '--allow-empty', '-qm', 'new candidate')
        self.head = self.git('rev-parse', 'HEAD')
        evidence = self.cli('verification.run-checks')
        self.assertTrue(evidence['checks'][0]['reused'])
        result = self.reconcile(evidence)
        self.assertEqual(result['classification'], 'Unverified')
        self.assertEqual(result['observations'][0]['actual_revision'], original)

    def test_changed_declared_environment_does_not_reuse_evidence(self):
        self.command['environment'].append('RECONCILE_INPUT')
        self.configure()
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        with patch.dict(os.environ, RECONCILE_INPUT='before'):
            evidence = self.cli('verification.run-checks')
        with patch.dict(os.environ, RECONCILE_INPUT='after'):
            result = self.reconcile(evidence)
        self.assertEqual(result['classification'], 'Unverified')
        self.assertIn('current configured checks', result['reason'])

    def test_receipt_failure_is_not_missing_evidence(self):
        self.write('check.py', 'raise SystemExit(3)\n')
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        result = self.reconcile(self.cli('verification.run-checks'))
        self.assertEqual(result['classification'], 'Failed', result)

    def test_tampered_receipt_and_changed_configuration_fail_closed(self):
        evidence = self.cli('verification.run-checks')
        receipt = self.root / evidence['checks'][0]['receipt']
        original = receipt.read_text(encoding='utf-8')
        receipt.write_text(original.replace('PRIVATE OUTPUT', 'ALTERED OUTPUT'), encoding='utf-8')
        self.assertEqual(self.reconcile(evidence)['classification'], 'Unverified')
        receipt.write_text(original, encoding='utf-8')
        self.command['timeout'] = 5
        self.configure()
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        result = self.reconcile(evidence, evidence['tested_revision'])
        self.assertEqual(result['classification'], 'Unverified')
        self.assertFalse(result['current'])

    def test_provider_pending_failed_unknown_and_passed(self):
        for status, conclusion, expected in [('in_progress', None, 'Pending'),
                                              ('completed', 'failure', 'Failed'),
                                              ('completed', 'success', 'Passed'),
                                              ('completed', 'skipped', 'Unverified')]:
            result = self.live(dict(id=42, head_sha=self.head, event='push', status=status, conclusion=conclusion))
            self.assertEqual(result['classification'], expected, result)
        result = self.reconcile(dict(id=43, sha=self.head, source='push', status='running'), kind='gitlab')
        self.assertEqual(result['classification'], 'Unverified')
        self.assertEqual(result['terminal_result'], 'Pending')

    def test_provider_pr_head_never_substitutes_for_run_sha(self):
        result = self.reconcile(dict(id=42, headRefOid=self.head, status='completed', conclusion='success'), kind='github')
        self.assertEqual(result['classification'], 'Unverified')
        result = self.reconcile(dict(id=42, head_sha='0' * 40, event='push', status='in_progress'), kind='github')
        self.assertEqual(result['classification'], 'Unverified')
        self.assertEqual(result['terminal_result'], 'Pending')

    def test_trusted_workflow_sha_is_distinct_from_test_checkout(self):
        evidence = dict(id=42, head_sha=self.head, event='pull_request_target',
                        status='completed', conclusion='success')
        result = self.live(evidence)
        self.assertEqual(result['classification'], 'Unverified')
        self.assertEqual(result['observations'][0]['provider_run_revision'], self.head)
        evidence['tested_revision'] = '0' * 40
        self.assertEqual(self.live(evidence)['classification'], 'Unverified')
        evidence.update(head_sha='0' * 40, tested_revision=self.head)
        result = self.live(evidence)
        self.assertEqual(result['classification'], 'Unverified')
        self.assertNotEqual(result['observations'][0]['provider_run_revision'],
                            result['observations'][0]['actual_revision'])

    def test_successful_provider_snapshot_cannot_authenticate_itself(self):
        result = self.reconcile(dict(id=42, head_sha=self.head, event='push',
                                     status='completed', conclusion='success'), kind='github')
        self.assertEqual(result['classification'], 'Unverified')
        self.assertEqual(result['terminal_result'], 'Passed')
        self.assertIn('snapshot provenance', result['reason'])

    def test_live_provider_unavailable_and_wrong_run_are_unverified(self):
        with patch('lib.delivery.gh', side_effect=VerbError('read denied', 'gh-failed')):
            result = reconcile(Workspace(self.root), None, self.head, self.head, kind='github',
                               provider_run='42', repository='example/project')
        self.assertEqual(result['classification'], 'Unverified')
        self.assertIn('provider read unavailable', result['reason'])
        result = self.live(dict(id=43, head_sha=self.head, event='push', status='completed', conclusion='success'))
        self.assertEqual(result['classification'], 'Unverified')
        self.assertIn('different run identity', result['reason'])

    def test_dirty_candidate_and_missing_logs_are_unverified(self):
        evidence = self.cli('verification.run-checks')
        self.write('untracked.txt', 'dirty')
        self.assertIn('dirty', self.reconcile(evidence)['reason'])
        (self.root / 'untracked.txt').unlink()
        (self.root / evidence['checks'][0]['stdout_log']).unlink()
        self.assertEqual(self.reconcile(evidence)['classification'], 'Unverified')

    def test_report_only_successor_reuses_existing_policy(self):
        self.command['successor_independence'] = dict(schema=1, report_paths=[REPORT],
            protected_inputs='all-other-inputs', revision_semantics='provenance-only')
        self.configure()
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        evidence = self.cli('verification.run-checks')
        tested = self.head
        self.write(REPORT, 'verification report')
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.reconcile(evidence, tested)['classification'], 'Unverified')
        result = self.reconcile(evidence, tested, 'local', '--report-only-paths', REPORT)
        self.assertEqual(result['classification'], 'Passed', result)
        self.assertEqual(result['observations'][0]['actual_revision'], tested)
        self.assertNotIn('PRIVATE OUTPUT', json.dumps(result))

    def test_complete_selected_current_evidence_and_invalid_accounting(self):
        evidence = self.cli('verification.run-checks', '--only-checks', '0')
        self.assertFalse(evidence['partial'])
        self.assertEqual(self.reconcile(evidence)['classification'], 'Passed')
        for field, value in [('selected_indices', []), ('selected_indices', [True]),
                             ('selected_indices', [0, 0]), ('selected_passed', False),
                             ('full_configuration_sha256', 'wrong'), ('full_order_sha256', 'wrong')]:
            with self.subTest(field=field, value=value):
                invalid = copy.deepcopy(evidence)
                invalid[field] = value
                self.assertEqual(self.reconcile(invalid)['classification'], 'Unverified')
        missing = copy.deepcopy(evidence)
        del missing['selected_indices']
        self.assertEqual(self.reconcile(missing)['classification'], 'Unverified')
        normal = self.cli('verification.run-checks')
        forged = dict(normal, **{key: evidence[key] for key in
                                 ('selected_indices', 'selected_passed', 'full_configuration_sha256', 'full_order_sha256')})
        forged['partial'] = False
        self.assertEqual(self.reconcile(forged)['classification'], 'Unverified')
        self.git('commit', '--allow-empty', '-qm', 'advance candidate')
        self.head = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.reconcile(evidence)['classification'], 'Unverified')

    def test_partial_selected_evidence_cannot_claim_complete_configuration(self):
        self.write('.planning/config.yaml', yaml.safe_dump({'verification': {'commands':
                   [self.command, dict(self.command, command=[sys.executable, '-c', 'print(2)'])]}}))
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        evidence = self.cli('verification.run-checks', '--only-checks', '0')
        self.assertTrue(evidence['partial'])
        self.assertEqual(self.reconcile(evidence)['classification'], 'Unverified')
        evidence.update(partial=False, passed=True, selected_passed=True, selected_indices=[0, 1])
        self.assertEqual(self.reconcile(evidence)['classification'], 'Unverified')

    def test_selected_receipt_requires_current_fresh_execution_revision(self):
        evidence = self.cli('verification.run-checks', '--only-checks', '0')
        envelope = json.loads((self.root / evidence['checks'][0]['receipt']).read_text(encoding='utf-8'))
        receipt = envelope['receipt']
        receipt['inputs']['fresh_execution_revision'] = '0' * 40
        receipt['key'] = digest(receipt['inputs'])
        reference = '.planning/verification-receipts/' + receipt['key'] + '.json'
        receipt['result']['receipt'] = reference
        envelope['sha256'] = digest(receipt)
        (self.root / reference).write_text(json.dumps(envelope), encoding='utf-8')
        evidence['checks'][0]['receipt'] = reference
        result = self.reconcile(evidence)
        self.assertEqual(result['classification'], 'Unverified')
        self.assertIn('complete current selected-check accounting', result['reason'])

    def test_missing_and_malformed_fresh_successor_evidence_preserve_observations(self):
        evidence = self.cli('verification.run-checks')
        tested = self.head
        self.write(REPORT, 'verification report')
        self.commit()
        self.head = self.git('rev-parse', 'HEAD')
        missing = Path(self.temp.name) / 'missing-fresh.json'
        malformed = Path(self.temp.name) / 'malformed-fresh.json'
        malformed.write_text('{invalid JSON', encoding='utf-8')
        for fresh in (missing, malformed):
            with self.subTest(path=fresh.name):
                result = self.reconcile(evidence, tested, 'local', '--report-only-paths', REPORT,
                                        '--fresh-evidence-file', str(fresh))
                self.assertTrue(result['ok'])
                self.assertEqual(result['classification'], 'Unverified')
                self.assertEqual(result['terminal_result'], 'Passed')
                self.assertEqual(result['observations'][0]['actual_revision'], tested)
                self.assertIn('successor evidence unavailable', result['reason'])
                self.assertNotIn('PRIVATE OUTPUT', json.dumps(result))


if __name__ == '__main__':
    unittest.main()
