"""Successor attestations exercised through the real CLI and temporary Git history."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.ai/runtime/phase.py'
sys.path.insert(0, str(ROOT / '.ai/runtime'))
from lib import verification_successors as successors
from lib import verification_checks as checks
from lib.paths import Workspace

REPORT = '.planning/phases/01-test/01-VERIFICATION.md'
CONTRACT = dict(schema=1, report_paths=[REPORT], protected_inputs='all-other-inputs',
                revision_semantics='provenance-only')

class SuccessorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.write('.gitignore', '.generated/\n.planning/verification-receipts/\n')
        self.write('.planning/phases/01-test/01-CONTEXT.md', 'owned phase')
        self.write('input.txt', 'source')
        self.write('check.py', "from pathlib import Path\np=Path('.generated/count');p.parent.mkdir(exist_ok=True);p.write_text(str(int(p.read_text())+1 if p.exists() else 1))\n")
        self.command = dict(command=[sys.executable, 'check.py'], revision=True, reuse=False,
                            successor_independence=copy.deepcopy(CONTRACT))
        self.configure([self.command])
        self.commit('baseline')
        self.r = self.git('rev-parse', 'HEAD')

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8', newline='\n')

    def configure(self, commands):
        self.write('.planning/config.yaml', yaml.safe_dump({'verification': {'commands': commands}}))

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, capture_output=True,
                              text=True, check=True).stdout.strip()

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-qm', message)

    def cli(self, verb, *args, ok=True, environment=None):
        env = dict(os.environ, PYTHONIOENCODING='utf-8')
        env.update(environment or {})
        result = subprocess.run([sys.executable, str(RUNTIME), 'query', verb, *args],
                                cwd=self.root, env=env, capture_output=True, text=True, timeout=60)
        self.assertNotIn('Traceback', result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload['ok'], ok, payload)
        return payload

    def baseline(self):
        evidence = self.cli('verification.run-checks')
        self.assertTrue(evidence['passed'])
        path = Path(self.temp.name) / 'baseline.json'
        path.write_text(json.dumps(evidence), encoding='utf-8')
        self.evidence = path
        return evidence

    def report(self):
        self.write(REPORT, 'report\n')
        self.commit('publish report')
        return self.git('rev-parse', 'HEAD')

    def qualify(self, head=None, *args, ok=True):
        return self.cli('verification.qualify-successor', '--evidence-file', str(self.evidence),
                        '--report-only-paths', REPORT, '--expected-head', head or self.git('rev-parse', 'HEAD'),
                        *args, ok=ok)

    def test_real_cli_preserves_original_receipts_and_revision_flags(self):
        original = self.baseline()
        before = {p.name: p.read_bytes() for p in (self.root / checks.STORE).iterdir()}
        head = self.report()
        result = self.qualify(head)
        self.assertTrue(result['qualified'], result)
        self.assertEqual(result['tested_revision'], self.r)
        self.assertEqual(result['qualified_revision'], head)
        self.assertEqual(result['checks'], original['checks'])
        self.assertEqual((self.root / '.generated/count').read_text(), '1')
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.root / checks.STORE).iterdir()})
        receipt = json.loads((self.root / original['checks'][0]['receipt']).read_text())['receipt']
        self.assertTrue(receipt['inputs']['specification']['revision'])
        self.assertFalse(receipt['inputs']['specification']['reuse'])
        self.assertEqual(receipt['inputs']['revision'], self.r)

    def test_uncontracted_receipt_is_fresh_required(self):
        self.command.pop('successor_independence')
        self.configure([self.command]); self.commit('uncontracted')
        self.baseline(); self.report()
        result = self.qualify()
        self.assertFalse(result['qualified'])
        self.assertEqual(result['fresh_required'], [0])

    def proof(self, paths=None, tested=None, head=None):
        return successors.prove_report_only_successor(self.root, tested or self.r,
                    head or self.git('rev-parse', 'HEAD'), paths or [REPORT])

    def direct(self, evidence=None, fresh=None):
        configuration = yaml.safe_load((self.root / '.planning/config.yaml').read_text())['verification']
        commands = checks.normalise(configuration['commands'], 600)
        with patch.dict(os.environ, {'PYTHONIOENCODING': 'utf-8'}):
            return checks.validate_successor(Workspace(self.root), evidence or json.loads(self.evidence.read_text()),
                        [REPORT], self.git('rev-parse', 'HEAD'), commands, configuration, 600, fresh)

    def test_history_checks_touches_even_after_revert(self):
        self.write('input.txt', 'changed'); self.commit('source touch')
        self.git('revert', '--no-edit', 'HEAD'); self.report()
        result = self.proof()
        self.assertFalse(result['qualified'], result)
        self.assertIn('input.txt', result['reason'])

    def test_mixed_commit_is_not_report_only(self):
        self.write(REPORT, 'report'); self.write('input.txt', 'changed'); self.commit('mixed')
        self.assertFalse(self.proof()['qualified'])

    def test_unapproved_documents_and_success_bookkeeping_are_rejected(self):
        for name in ['README.md', 'SECURITY.md', '.planning/specs/SPEC-test.md',
                     '.planning/phases/01-test/01-01-PLAN.md', '.planning/STATE.md',
                     '.planning/ROADMAP.md', '.planning/REQUIREMENTS.md', '.planning/config.yaml']:
            with self.subTest(path=name):
                self.assertFalse(successors.prove_report_only_successor(self.root, self.r, self.r, [name])['qualified'])

    def test_report_owner_and_literal_paths_are_required(self):
        for path in ['report.md', '.planning/phases/02-missing/02-VERIFICATION.md',
                     '.planning/phases/01-test/02-VERIFICATION.md', '../escape', '/absolute',
                     'C:/absolute', REPORT + '/../x', '.planning/*/VERIFICATION.md',
                     REPORT.replace('/', '\\'), './' + REPORT]:
            with self.subTest(path=path):
                self.assertFalse(self.proof(paths=[path])['qualified'])
        self.assertFalse(self.proof(paths=[REPORT, REPORT])['qualified'])

    def test_dirty_index_tracked_and_untracked_state_rejects(self):
        self.report()
        for name in ['input.txt', 'untracked.txt']:
            self.write(name, 'dirty')
            self.assertFalse(self.proof()['qualified'])
            if name == 'input.txt':
                self.git('add', name)
                self.assertFalse(self.proof()['qualified'])
                self.git('restore', '--staged', name); self.git('restore', name)
            else:
                (self.root / name).unlink()

    def test_deleted_renamed_and_mode_changed_reports_reject(self):
        self.report()
        baseline = self.git('rev-parse', 'HEAD')
        self.git('mv', REPORT, REPORT + '.old'); self.commit('rename')
        self.assertFalse(self.proof(tested=baseline)['qualified'])

    def test_report_deletion_rejects(self):
        self.report(); baseline = self.git('rev-parse', 'HEAD')
        self.git('rm', REPORT); self.commit('delete')
        self.assertFalse(self.proof(tested=baseline)['qualified'])

    def test_report_executable_mode_change_rejects(self):
        self.report(); baseline = self.git('rev-parse', 'HEAD')
        self.git('update-index', '--chmod=+x', REPORT)
        self.git('commit', '-qm', 'mode')
        self.assertFalse(self.proof(tested=baseline)['qualified'])

    def test_noncommit_malformed_stale_and_shallow_heads_reject(self):
        head = self.report()
        blob = self.git('rev-parse', 'HEAD:input.txt')
        for tested, current in [(blob, head), ('HEAD', head), ('0' * 40, head), (self.r, self.r)]:
            with self.subTest(tested=tested, head=current):
                self.assertFalse(self.proof(tested=tested, head=current)['qualified'])
        (self.root / '.git/shallow').write_text(self.r + '\n')
        self.assertFalse(self.proof()['qualified'])

    def test_nonancestor_and_merge_parent_changes_reject(self):
        self.git('checkout', '-qb', 'side')
        self.write('side.txt', 'source'); self.commit('side source')
        side = self.git('rev-parse', 'HEAD')
        self.git('checkout', '-qb', 'main-test', self.r)
        head = self.report()
        self.assertFalse(self.proof(tested=side)['qualified'])
        self.git('merge', '--no-ff', '-m', 'merge side', 'side')
        self.assertFalse(self.proof()['qualified'])

    def test_head_movement_during_proof_rejects(self):
        self.report()
        real_git = successors.git
        def moving(root, *args, **kwargs):
            if args[:3] == ('rev-list', '--reverse', '--topo-order'):
                self.git('commit', '--allow-empty', '-qm', 'head moved')
            return real_git(root, *args, **kwargs)
        with patch.object(successors, 'git', side_effect=moving):
            self.assertFalse(self.proof()['qualified'])

    def test_contract_shape_rejects_unknown_types_and_retrospective_assertions(self):
        for contract in [None, {}, dict(CONTRACT, schema=True), dict(CONTRACT, extra=True),
                         dict(CONTRACT, protected_inputs='some'), dict(CONTRACT, revision_semantics='ignore-head'),
                         dict(CONTRACT, report_paths=[REPORT, REPORT])]:
            with self.subTest(contract=contract):
                with self.assertRaises(Exception):
                    checks.normalise([dict(self.command, successor_independence=contract)], 600)

    def test_tampered_missing_receipt_logs_and_result_flags_reject(self):
        evidence = self.baseline(); self.report()
        row = evidence['checks'][0]
        receipt = self.root / row['receipt']; saved = receipt.read_bytes()
        log = self.root / row['stdout_log']; log_saved = log.read_bytes()
        for changed in [b'{}', saved[:-5]]:
            receipt.write_bytes(changed)
            self.assertFalse(self.direct()['qualified'])
        receipt.unlink(); self.assertFalse(self.direct()['qualified']); receipt.write_bytes(saved)
        log.write_bytes(b'tampered'); self.assertFalse(self.direct()['qualified'])
        log.unlink(); self.assertFalse(self.direct()['qualified']); log.write_bytes(log_saved)
        for field, value in [('passed', False), ('passed', None), ('snapshot_valid', False),
                             ('exit_code', False), ('exit_code', None), ('reused', True)]:
            with self.subTest(field=field, value=value):
                mutated = copy.deepcopy(evidence); mutated['checks'][0][field] = value
                self.assertFalse(self.direct(mutated)['qualified'])

    def test_failed_aggregate_incomplete_extra_and_duplicate_rows_reject(self):
        evidence = self.baseline(); self.report()
        cases = []
        for field in ['passed', 'configured', 'snapshot_valid']:
            mutated = copy.deepcopy(evidence); mutated[field] = False; cases.append(mutated)
        for rows in [[], [evidence['checks'][0]] * 2, [None]]:
            mutated = copy.deepcopy(evidence); mutated['checks'] = rows; cases.append(mutated)
        for mutated in cases:
            self.assertFalse(self.direct(mutated)['qualified'])

    def test_source_test_dependency_and_config_history_changes_reject(self):
        for name in ['tests/test.py', '.ai/runtime/phase.py', 'requirements.txt', '.planning/config.yaml']:
            with self.subTest(name=name):
                self.write(name, 'changed'); self.commit('protected change')
                self.assertFalse(self.proof()['qualified'])

    def test_declared_ignored_dependency_changes_require_fresh_baseline(self):
        self.write('.generated/dependency', 'one')
        self.command['sources'] = ['input.txt', 'check.py', '.generated/dependency']
        self.configure([self.command]); self.commit('declare dependency')
        self.baseline(); self.report()
        self.write('.generated/dependency', 'two')
        result = self.direct()
        self.assertFalse(result['qualified']); self.assertIn('protected', result['qualifications'][0]['reason'])

    def test_environment_tool_and_runtime_identity_changes_reject(self):
        self.baseline(); self.report()
        with patch.dict(os.environ, {'CHECK_NEW_ENV': 'changed'}):
            self.assertFalse(self.direct()['qualified'])
        with patch.object(checks, 'tool_identity', return_value=None):
            self.assertFalse(self.direct()['qualified'])
        with patch.object(checks, 'runtime_identity', return_value={'changed': True}):
            self.assertFalse(self.direct()['qualified'])
        with patch.object(checks, 'safe_snapshot', return_value=None):
            self.assertFalse(self.direct()['qualified'])

    def test_receipt_and_report_component_reparse_points_reject(self):
        self.baseline(); self.report()
        real_lstat = Path.lstat
        target = self.root / '.planning/verification-receipts'
        def reparse(path, *args, **kwargs):
            info = real_lstat(path, *args, **kwargs)
            if path == target:
                from types import SimpleNamespace
                return SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
            return info
        with patch.object(Path, 'lstat', reparse):
            self.assertFalse(self.direct()['qualified'])
        target = self.root / '.planning/phases/01-test'
        with patch.object(Path, 'lstat', reparse):
            self.assertFalse(self.proof()['qualified'])

    def test_cli_requires_complete_option_combination(self):
        self.cli('verification.qualify-successor', '--evidence-file', 'missing', ok=False)
        self.cli('verification.qualify-successor', '--evidence-file', 'missing', '--report-only-paths',
                 REPORT, '--expected-head', self.r, '--independent', ok=False)

    def test_mixed_full_order_accounting_runs_only_real_fresh_checks_at_h(self):
        head_check = {'command': ['git', 'diff', '--check', 'HEAD^', 'HEAD'], 'revision': True, 'reuse': False}
        report_check = {'command': [sys.executable, '-c',
            "from pathlib import Path; p=Path('" + REPORT + "'); print(p.read_text() if p.exists() else 'absent')"],
                        'revision': True, 'reuse': False}
        self.configure([self.command, head_check, report_check]); self.commit('mixed configuration')
        evidence = self.baseline(); head = self.report()
        initial = self.qualify(head)
        self.assertEqual(initial['fresh_required'], [1, 2])
        fresh = self.cli('verification.run-checks', '--only-checks', '1', '2')
        self.assertTrue(fresh['partial']); self.assertFalse(fresh['passed']); self.assertTrue(fresh['selected_passed'])
        self.assertEqual([r['full_index'] for r in fresh['checks']], [1, 2])
        self.assertIn('report', fresh['checks'][1]['stdout_tail'])
        fresh_file = Path(self.temp.name) / 'fresh.json'; fresh_file.write_text(json.dumps(fresh))
        result = self.qualify(head, '--fresh-evidence-file', str(fresh_file))
        self.assertTrue(result['qualified'], result)
        self.assertEqual([r['tested_revision'] for r in result['checks']], [evidence['tested_revision'], head, head])
        self.assertEqual((self.root / '.generated/count').read_text(), '1')
        self.assertEqual(result['checks'][0], evidence['checks'][0])
        for field, value in [('selected_indices', [2, 1]), ('selected_indices', [1, 1]),
                             ('selected_indices', [1]), ('full_order_sha256', 'wrong'),
                             ('full_configuration_sha256', 'wrong'), ('checks', list(reversed(fresh['checks']))),
                             ('checks', [fresh['checks'][0]] * 2)]:
            with self.subTest(field=field, value=value):
                mutated = copy.deepcopy(fresh); mutated[field] = value
                self.assertFalse(self.direct(evidence, mutated)['qualified'])
        failed = copy.deepcopy(evidence); failed['passed'] = False
        self.assertFalse(self.direct(failed, fresh)['qualified'])

    def test_subset_rejects_empty_duplicate_malformed_out_of_range_and_reordered(self):
        for values in [[], ['0', '0'], ['-1'], ['False'], ['1'], ['0.0']]:
            with self.subTest(indices=values):
                self.cli('verification.run-checks', '--only-checks', *values, ok=False)

    def test_genuine_final_head_fallback_preserves_failed_evidence(self):
        self.write('check.py', 'raise SystemExit(7)\n'); self.commit('failing check')
        failed = self.cli('verification.run-checks')
        self.assertFalse(failed['passed'])
        old_receipt = self.root / failed['checks'][0]['receipt']; original = old_receipt.read_bytes()
        self.write('check.py', 'print("fixed")\n'); self.commit('fix source')
        self.report()
        fresh = self.cli('verification.run-checks')
        self.assertTrue(fresh['passed']); self.assertEqual(fresh['tested_revision'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(old_receipt.read_bytes(), original)
