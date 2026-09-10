"""Failure-path regression tests with real isolated Git repositories."""
import copy
import json
from pathlib import Path
import sys
import threading
import unittest

import test_orchestrate as fixture

FakeForge, orch = fixture.FakeForge, fixture.orch


class RecoveryTests(unittest.TestCase):
    setUp = fixture.RuntimeTests.setUp
    track = fixture.RuntimeTests.track
    runner = fixture.RuntimeTests.runner

    def seed(self, files):
        for name, text in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        orch.git(self.root, 'add', '.')
        orch.git(self.root, 'commit', '-m', 'Prepare failure-path fixture')
        orch.git(self.root, 'push')

    def test_retry_pr_failure_preserves_completed_phase(self):
        runner = self.runner()
        original = runner.gh
        def unavailable(*args):
            if args[:2] == ('pr', 'create'):
                raise orch.Blocked('Temporary forge outage')
            return original(*args)
        runner.gh = unavailable
        self.assertFalse(runner.run())
        before = copy.deepcopy(runner.state['tracks']['a']['completed_phases']['build'])
        runner.gh = original
        runner.recover('retry', 'a')
        self.assertTrue(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(before, state['completed_phases']['build'])
        self.assertEqual(state['phase_attempts'], {'build': 1, 'review-1': 1})
        self.assertEqual(len(runner.prs), 1)

    def test_retry_failed_integration_checks_reuses_review(self):
        self.config['tracks'].append(self.track('b', 21))
        runner = self.runner()
        checks, phase, finish = runner.checks, runner.phase, runner.finish_merge
        calls = []
        allocated, merged = threading.Event(), threading.Event()
        def ordered_phase(track, name, **kwargs):
            if name == 'build':
                if track['id'] == 'b':
                    allocated.set()
                else:
                    self.assertTrue(allocated.wait(10))
            if track['id'] == 'b' and name == 'review-1':
                self.assertTrue(merged.wait(30))
            return phase(track, name, **kwargs)
        def after_merge(track):
            finish(track)
            if track['id'] == 'a':
                merged.set()
        def fail_integration(path, track):
            if track['id'] == 'b':
                calls.append(path)
                if len(calls) == 2:
                    self.assertTrue((path / 'src/a.txt').exists())
                    raise orch.Blocked('Temporary check infrastructure failure')
            checks(path, track)
        runner.checks, runner.phase, runner.finish_merge = fail_integration, ordered_phase, after_merge
        self.assertFalse(runner.run())
        before = copy.deepcopy(runner.state['tracks']['b']['phase_attempts'])
        runner.recover('retry', 'b')
        self.assertTrue(runner.run())
        self.assertEqual(before, runner.state['tracks']['b']['phase_attempts'])

    def test_reconcile_completed_interrupted_writer_without_replay(self):
        runner = self.runner()
        consume = runner.consume_result
        def interrupted(track):
            raise orch.Blocked('Lost scheduler before result ingestion')
        runner.consume_result = interrupted
        self.assertFalse(runner.run())
        path, _ = runner.location(self.config['tracks'][0])
        head = orch.git(path, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(orch.Blocked, 'Confirm'):
            runner.recover('reconcile', 'a', expected_head=head)
        runner.consume_result = consume
        runner.recover('reconcile', 'a', expected_head=head, workers_stopped=True)
        self.assertTrue(runner.run())
        self.assertEqual(runner.state['tracks']['a']['phase_attempts']['build'], 1)

    def test_missing_review_result_never_resets_review_attempt(self):
        runner = self.runner()
        consume = runner.consume_result
        def interrupted(track):
            state = runner.state['tracks'][track['id']]
            if state['inflight']['name'] == 'review-1':
                Path(state['inflight']['result_file']).unlink()
                raise orch.Blocked('Reviewer result was lost')
            return consume(track)
        runner.consume_result = interrupted
        self.assertFalse(runner.run())
        path, _ = runner.location(self.config['tracks'][0])
        with self.assertRaisesRegex(orch.Blocked, 'Failed fix/review'):
            runner.recover('reconcile', 'a', expected_head=orch.git(path, 'rev-parse', 'HEAD'), workers_stopped=True)
        self.assertFalse(runner.run())
        self.assertEqual(runner.state['tracks']['a']['phase_attempts']['review-1'], 1)

    def test_abandon_preserves_work_and_allows_a_new_run(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'outside'
        runner = self.runner()
        self.assertFalse(runner.run())
        path, branch = runner.location(self.config['tracks'][0])
        head = orch.git(path, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(orch.Blocked, 'exact current'):
            runner.recover('abandon', 'a', expected_head='wrong', workers_stopped=True)
        runner.recover('abandon', 'a', expected_head=head, workers_stopped=True)
        self.assertTrue((path / 'foreign.txt').exists())
        self.assertTrue(orch.git(self.root, 'branch', '--list', branch))
        config = copy.deepcopy(self.config)
        config.update(run_id='ORCH-002', tracks=[self.track('b', 21)])
        self.assertTrue(FakeForge(config, self.forge).run())
        self.assertTrue((path / 'foreign.txt').exists())

    def test_parked_track_and_dependent_do_not_block_defect_audit(self):
        source = '.ai/plans/backlog/PLAN-001-a.md'
        self.seed({source: '# Build a\n'})
        track = self.config['tracks'][0]
        track['plans'] = [source]
        track['owned_paths'].append(source)
        track['environment']['WORKER_MODE'] = 'residual'
        self.config['tracks'] += [self.track('b', 21), self.track('c', 41, deps=['a'])]
        self.config['residual_findings'] = 'park'
        runner = self.runner()
        self.assertFalse(runner.run())
        queue = json.loads((runner.directory / 'followups.json').read_text())
        self.assertTrue(queue['eligible'])
        self.assertEqual({t['track'] for t in queue['parked_tracks']}, {'a', 'c'})
        self.assertIn('followup_audit', runner.state)
        self.assertEqual(runner.state['tracks']['b']['status'], 'merged')
        self.assertFalse((self.root / queue['FIX'][0]['record']).exists())
        self.assertTrue(Path(queue['FIX'][0]['report_file']).is_file())

    def test_blocked_worker_findings_survive_without_committing_partial_edits(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'blocked-findings'
        runner = self.runner()
        self.assertFalse(runner.run())
        queue = json.loads((runner.directory / 'followups.json').read_text())
        self.assertEqual((len(queue['FIX']), len(queue['INTAKE'])), (1, 1))
        for item in queue['FIX'] + queue['INTAKE']:
            self.assertIn('Confirmed finding', Path(item['report_file']).read_text())
        path, _ = runner.location(self.config['tracks'][0])
        self.assertEqual(orch.git(path, 'rev-parse', 'HEAD'), runner.state['tracks']['a']['base'])
        self.assertTrue((path / 'src/a.txt').is_file())
        self.assertFalse((path / '.ai/fixes').exists())

    def test_repeated_finding_updates_severity_and_retains_evidence(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'escalating'
        runner = self.runner()
        self.assertTrue(runner.run())
        finding = runner.state['tracks']['a']['findings']['code']
        self.assertEqual(finding['severity'], 'critical')
        self.assertEqual([x['severity'] for x in finding['history']], ['minor', 'critical'])
        report = (self.root / finding['record']).read_text()
        for text in ('severity: "critical"', 'Concrete regression evidence', 'New second-round evidence', 'src/critical.txt', 'Attempted correction'):
            self.assertIn(text, report)

    def test_python_caches_and_declared_generated_output_allow_cleanup(self):
        self.seed({'.gitignore': '.worktrees/\n__pycache__/\n.cache/\n', 'helper.py': 'VALUE = 1\n'})
        self.config['tracks'][0]['disposable_paths'] = ['.cache/']
        self.config['required_commands'] = [[sys.executable, '-c',
            "import helper; from pathlib import Path; assert not Path('__pycache__').exists(); "
            "Path('.cache').mkdir(exist_ok=True); Path('.cache/output').write_text('generated')"]]
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertTrue(runner.state['tracks']['a']['cleaned'])

    def test_undeclared_ignored_files_are_preserved(self):
        self.seed({'.gitignore': '.worktrees/\nprivate/\n'})
        self.config['required_commands'] = [[sys.executable, '-c',
            "from pathlib import Path; Path('private').mkdir(exist_ok=True); Path('private/notes').write_text('keep')"]]
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertEqual(runner.state['tracks']['a']['status'], 'merged')
        self.assertEqual((runner.location(self.config['tracks'][0])[0] / 'private/notes').read_text(), 'keep')

    def test_ci_wait_does_not_delay_independent_dispatch(self):
        self.config.update(max_parallel_tracks=1, tracks=[self.track('a', 1), self.track('b', 21)])
        runner = self.runner()
        started = threading.Event()
        phase, checks = runner.phase, runner.wait_checks
        def observe(track, name, **kwargs):
            if track['id'] == 'b' and name == 'build':
                started.set()
            return phase(track, name, **kwargs)
        def slow_ci(pr, head):
            self.assertTrue(started.wait(10), 'CI wait prevented independent dispatch')
            checks(pr, head)
        runner.phase, runner.wait_checks = observe, slow_ci
        self.assertTrue(runner.run())

    def test_optional_checks_do_not_gate_but_protected_checks_do(self):
        runner = self.runner()
        data = {'headRefOid': 'sha', 'state': 'OPEN', 'statusCheckRollup': [
            {'name': 'validate', 'status': 'COMPLETED', 'conclusion': 'SUCCESS'},
            {'name': 'docs', 'status': 'COMPLETED', 'conclusion': 'SKIPPED'},
            {'name': 'optional', 'status': 'IN_PROGRESS', 'conclusion': None}]}
        runner.gh = lambda *args: json.dumps(data)
        runner.wait_checks(1, 'sha')
        runner.protected_checks = {'validate', 'security'}
        with self.assertRaisesRegex(orch.Blocked, 'missing'):
            runner.wait_checks(1, 'sha')
        data['statusCheckRollup'].append({'name': 'security', 'status': 'COMPLETED', 'conclusion': 'FAILURE'})
        with self.assertRaisesRegex(orch.Blocked, 'security'):
            runner.wait_checks(1, 'sha')

    def test_retry_cannot_bypass_park_policy(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'residual'
        self.config['residual_findings'] = 'park'
        runner = self.runner()
        self.assertFalse(runner.run())
        attempts = copy.deepcopy(runner.state['tracks']['a']['phase_attempts'])
        runner.recover('retry', 'a')
        self.assertFalse(runner.run())
        self.assertFalse(runner.events)
        self.assertEqual(attempts, runner.state['tracks']['a']['phase_attempts'])

    def test_closed_reports_are_not_resurrected_from_receipts(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'residual'
        runner = self.runner()
        self.assertTrue(runner.run())
        finding = runner.state['tracks']['a']['findings']['code']
        target = self.root / '.ai/fixes/done' / Path(finding['record']).name
        target.parent.mkdir(parents=True)
        orch.git(self.root, 'mv', finding['record'], str(target))
        orch.git(self.root, 'commit', '-m', 'Close a proven defect')
        orch.git(self.root, 'push')
        self.assertEqual(runner.followup_queue()['FIX'], [])

    def test_closed_abandoned_reports_are_not_resurrected_from_receipts(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'blocked-findings'
        runner = self.runner()
        self.assertFalse(runner.run())
        path, _ = runner.location(self.config['tracks'][0])
        runner.recover('abandon', 'a', expected_head=orch.git(path, 'rev-parse', 'HEAD'), workers_stopped=True)
        findings = runner.state['tracks']['a']['findings']
        self.seed({
            f".ai/fixes/done/2026-Q3/{findings['code']['id']}-proven.md": '# Closed with regression proof\n',
            f".ai/plans/abandoned/{findings['documentation']['id']}-promoted.md": '# Promoted to a PLAN\n',
        })
        config = copy.deepcopy(self.config)
        config.update(run_id='ORCH-002', tracks=[self.track('b', 21)])
        later = FakeForge(config, self.forge)
        self.assertTrue(later.run())
        for origin in (runner, later):
            with self.subTest(run=origin.config['run_id']):
                queue = origin.followup_queue()
                self.assertEqual([item['id'] for item in queue['FIX']], [])
                self.assertEqual([item['id'] for item in queue['INTAKE']], [])
        self.assertTrue((path / 'src/a.txt').is_file())

    def test_abandoned_findings_use_current_open_reports(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'blocked-findings'
        runner = self.runner()
        self.assertFalse(runner.run())
        path, _ = runner.location(self.config['tracks'][0])
        runner.recover('abandon', 'a', expected_head=orch.git(path, 'rev-parse', 'HEAD'), workers_stopped=True)
        findings = runner.state['tracks']['a']['findings']
        queue = runner.followup_queue()
        self.assertEqual(queue['FIX'], [findings['code']])
        self.assertEqual(queue['INTAKE'], [findings['documentation']])
        record = f".ai/fixes/open/{findings['code']['id']}-current-evidence.md"
        self.seed({record: '# Current evidence after the abandoned attempt\n'})
        config = copy.deepcopy(self.config)
        config.update(run_id='ORCH-002', tracks=[self.track('b', 21)])
        later = FakeForge(config, self.forge)
        self.assertTrue(later.run())
        for origin in (runner, later):
            with self.subTest(run=origin.config['run_id']):
                queue = origin.followup_queue()
                self.assertEqual(len(queue['FIX']), 1)
                current = queue['FIX'][0]
                self.assertEqual(current['report_file'], str(self.root / record))
                self.assertEqual(current['record'], record)
                self.assertEqual(current['source_worktree'], str(self.root))
                self.assertEqual(queue['INTAKE'], [findings['documentation']])
        self.assertTrue(Path(findings['code']['report_file']).is_file())
        self.assertTrue((path / 'src/a.txt').is_file())

    def test_generated_directory_symlink_is_preserved(self):
        runner = self.runner()
        track = self.config['tracks'][0]
        self.config['tracks'][0]['disposable_paths'] = ['.cache/']
        runner.start(track)
        path, _ = runner.location(track)
        outside = self.directory / 'precious'
        outside.mkdir()
        (outside / 'notes').write_text('keep', encoding='utf-8')
        try:
            (path / '.cache').symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest('Creating a directory symlink is unavailable on this host')
        with self.assertRaisesRegex(orch.Blocked, 'redirected'):
            runner.discard_generated(track)
        self.assertEqual((outside / 'notes').read_text(), 'keep')

    def test_definitive_ci_failure_can_release_reservations(self):
        runner = self.runner()
        def failed(pr, head):
            raise orch.Blocked('GitHub check did not pass: validate: FAILURE')
        runner.wait_checks = failed
        self.assertFalse(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(state['status'], 'blocked')
        self.assertEqual(runner.prs[state['pr']]['state'], 'OPEN')
        path, _ = runner.location(self.config['tracks'][0])
        runner.recover('abandon', 'a', expected_head=orch.git(path, 'rev-parse', 'HEAD'), workers_stopped=True)
        self.assertTrue(runner.state['tracks']['a']['released'])
        self.assertTrue(path.is_dir())

    def test_resource_waiter_does_not_block_parked_defect_audit(self):
        self.config.update(residual_findings='park', tracks=[
            self.track('a', 1, resources=['port:test'], env={'WORKER_MODE': 'residual'}),
            self.track('b', 21, resources=['port:test']), self.track('c', 41)])
        runner = self.runner()
        self.assertFalse(runner.run())
        queue = runner.followup_queue()
        self.assertTrue(queue['eligible'])
        self.assertEqual({t['track'] for t in queue['parked_tracks']}, {'a', 'b'})
        self.assertEqual(runner.state['tracks']['c']['status'], 'merged')
        self.assertIn('followup_audit', runner.state)

    def test_sync_updates_base_outside_clone_fetch_filter(self):
        (self.forge / 'new-target.txt').write_text('new target', encoding='utf-8')
        orch.git(self.forge, 'add', '.')
        orch.git(self.forge, 'commit', '-m', 'Advance the filtered target branch')
        orch.git(self.forge, 'push')
        expected = orch.git(self.forge, 'rev-parse', 'HEAD')
        orch.git(self.root, 'config', 'remote.origin.fetch', '+refs/heads/unrelated:refs/remotes/origin/unrelated')
        self.assertEqual(self.runner().sync(), expected)


if __name__ == '__main__':
    unittest.main()
