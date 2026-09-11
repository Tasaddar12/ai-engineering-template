import copy
from datetime import date
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

import test_orchestrate as fixture

orch = fixture.orch


class ContractTests(unittest.TestCase):
    def test_interleaved_steps_are_rejected_instead_of_reordered(self):
        text = fixture.plan_text('Invalid order', [
            {'id': 'docs', 'phase': 'document', 'title': 'Document'},
            {'id': 'code', 'phase': 'build', 'title': 'Implement'}])
        with self.assertRaisesRegex(orch.Blocked, 'precede'):
            orch.execution_contract(text)

    def test_invalid_lifecycle_and_unsupported_settings_fail_preflight(self):
        original = json.loads(fixture.RUNTIME.with_name('schedule.example.json').read_text())
        for stage in ('blocked', 'done/2026-Q3', 'abandoned', 'intake'):
            config = copy.deepcopy(original)
            track = config['tracks'][0]
            old = track['plans'][0]
            new = old.replace('/backlog/', '/' + stage + '/')
            for key in ('plans', 'owned_paths', 'documentation_paths'):
                track[key] = [new if p == old else p for p in track[key]]
            with self.subTest(stage=stage), self.assertRaisesRegex(orch.Blocked, 'executable lifecycle'):
                orch.validate(config)
        for key, value in (('worktree_root', 'work'), ('worktree_root', '.worktrees/nested'),
                           ('done_partition', 'week'), ('max_process_attempts', 0), ('max_process_attempts', 4),
                           ('auto_merge', 'never'), ('cleanup_on_merge', False), ('paths', {})):
            config = copy.deepcopy(original)
            config[key] = value
            with self.subTest(setting=key, value=value), self.assertRaises(orch.Blocked):
                orch.validate(config)


class ReliabilityTests(unittest.TestCase):
    setUp = fixture.RuntimeTests.setUp
    track = fixture.RuntimeTests.track
    runner = fixture.RuntimeTests.runner

    def test_interrupted_readiness_requires_reconciliation_and_reuses_valid_result(self):
        runner = self.runner()
        consume = runner.consume_readiness

        def interrupted(track):
            raise orch.Blocked('Readiness scheduler interrupted before ingestion')

        runner.consume_readiness = interrupted
        self.assertFalse(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(state['inflight_phase'], 'readiness')
        self.assertTrue(Path(state['inflight']['result_file']).is_file())
        state['worker_stopped'] = False
        runner.save()
        with self.assertRaisesRegex(orch.Blocked, 'confirming its worker stopped'):
            runner.recover('retry', 'a')
        with self.assertRaisesRegex(orch.Blocked, 'confirming its worker stopped'):
            runner.recover('reconcile', 'a', expected_head=orch.git(self.root, 'rev-parse', 'HEAD'))
        runner.consume_readiness = consume
        runner.recover('reconcile', 'a', expected_head=orch.git(self.root, 'rev-parse', 'HEAD'), workers_stopped=True)
        self.assertTrue(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(sum(state['readiness_attempts'].values()), 1)
        self.assertEqual(len(state['readiness_history']), 1)

    def test_completed_readiness_rejection_is_preserved_until_revision_changes(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'readiness-reject'
        runner = self.runner()
        self.assertFalse(runner.run())
        state = runner.state['tracks']['a']
        receipt = copy.deepcopy(state['readiness'])
        with self.assertRaisesRegex(orch.Blocked, 'changed revision'):
            runner.recover('retry', 'a')
        self.assertEqual(state['readiness'], receipt)
        self.assertEqual(len(state['readiness_history']), 1)
        self.assertFalse(runner.location(self.config['tracks'][0])[0].exists())
        (self.forge / 'resolved-decision.md').write_text('Recorded revised proposal\n')
        orch.git(self.forge, 'add', '.')
        orch.git(self.forge, 'commit', '-m', 'Revise readiness evidence')
        orch.git(self.forge, 'push')
        runner.recover('retry', 'a')
        self.assertFalse(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(len(state['readiness_history']), 2)
        self.assertEqual(state['readiness_history'][0], receipt)

    def test_lost_readiness_results_have_a_bounded_retry_budget(self):
        runner = self.runner()

        def lost(track):
            phase = runner.state['tracks']['a']['inflight']
            Path(phase['result_file']).unlink()
            raise orch.Blocked('Readiness result lost')

        runner.consume_readiness = lost
        self.assertFalse(runner.run())
        head = orch.git(self.root, 'rev-parse', 'HEAD')
        runner.recover('reconcile', 'a', expected_head=head, workers_stopped=True)
        self.assertFalse(runner.run())
        with self.assertRaisesRegex(orch.Blocked, 'budget exhausted'):
            runner.recover('reconcile', 'a', expected_head=head, workers_stopped=True)
        self.assertEqual(runner.state['tracks']['a']['readiness_attempts'][head], 2)
        self.assertFalse(runner.location(self.config['tracks'][0])[0].exists())

    def test_failed_readiness_allocates_nothing_and_independent_track_merges(self):
        self.config['tracks'] = [self.track('a', 1, env={'WORKER_MODE': 'readiness-reject'}), self.track('b', 21)]
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertFalse(runner.location(self.config['tracks'][0])[0].exists())
        self.assertEqual(runner.state['tracks']['b']['status'], 'merged')
        self.assertIn('readiness', runner.state['tracks']['a']['reason'])

    def test_slow_readiness_does_not_hold_the_dispatch_loop(self):
        self.config['tracks'] = [self.track('a', 1), self.track('b', 21)]
        runner = self.runner()
        original = runner.readiness
        independent = threading.Event()

        def readiness(track, base, contracts):
            if track['id'] == 'a':
                self.assertTrue(independent.wait(15))
            else:
                independent.set()
            original(track, base, contracts)

        runner.readiness = readiness
        self.assertTrue(runner.run())
        for state in runner.state['tracks'].values():
            self.assertEqual(state['readiness']['base_sha'], state['base'])

    def test_target_advance_invalidates_readiness_before_allocation(self):
        runner = self.runner()
        original = runner.readiness
        inspected = []

        def readiness(track, base, contracts):
            inspected.append(base)
            original(track, base, contracts)
            if len(inspected) == 1:
                (self.forge / 'new-prerequisite.txt').write_text('landed\n')
                orch.git(self.forge, 'add', '.')
                orch.git(self.forge, 'commit', '-m', 'Land prerequisite while readiness is running')
                orch.git(self.forge, 'push')

        runner.readiness = readiness
        self.assertTrue(runner.run())
        self.assertEqual(len(inspected), 2)
        self.assertNotEqual(*inspected)
        self.assertEqual(runner.state['tracks']['a']['base'], inspected[-1])

    def test_documentation_review_packets_exclude_prior_documentation_results(self):
        self.config['tracks'] = [self.track('a', 1, docs=True, env={'WORKER_MODE': 'cold-docs'})]
        self.assertTrue(self.runner().run())

    def test_out_of_scope_code_finding_never_dispatches_a_fixer(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'out-of-scope'
        runner = self.runner()
        self.assertTrue(runner.run())
        state = runner.state['tracks']['a']
        self.assertNotIn('fix', state['process_attempts'])
        self.assertIn('review-2', state['completed_phases'])
        self.assertEqual(len(runner.followup_queue()['FIX']), 1)

    def test_repeated_missing_result_exhausts_process_budget_without_completed_review(self):
        runner = self.runner()
        consume = runner.consume_result

        def lost(track):
            phase = runner.state['tracks']['a']['inflight']
            if phase['name'] == 'review-1':
                Path(phase['result_file']).unlink()
                raise orch.Blocked('Lost result')
            return consume(track)

        runner.consume_result = lost
        self.assertFalse(runner.run())
        path, _ = runner.location(self.config['tracks'][0])
        head = orch.git(path, 'rev-parse', 'HEAD')
        runner.recover('reconcile', 'a', expected_head=head, workers_stopped=True)
        self.assertFalse(runner.run())
        with self.assertRaisesRegex(orch.Blocked, 'budget exhausted'):
            runner.recover('reconcile', 'a', expected_head=head, workers_stopped=True)
        state = runner.state['tracks']['a']
        self.assertEqual(state['process_attempts']['review-1'], 2)
        self.assertNotIn('review-1', state['completed_phases'])
        self.assertEqual(orch.git(path, 'rev-parse', 'HEAD'), head)

    def test_missing_writer_result_with_commits_cannot_be_replayed(self):
        runner = self.runner()

        def lost(track):
            phase = runner.state['tracks']['a']['inflight']
            Path(phase['result_file']).unlink()
            raise orch.Blocked('Lost committed writer result')

        runner.consume_result = lost
        self.assertFalse(runner.run())
        path, _ = runner.location(self.config['tracks'][0])
        head = orch.git(path, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(orch.Blocked, 'Partial writer'):
            runner.recover('reconcile', 'a', expected_head=head, workers_stopped=True)
        self.assertEqual(orch.git(path, 'rev-parse', 'HEAD'), head)
        self.assertEqual(runner.state['tracks']['a']['process_attempts']['build'], 1)

    def test_linked_checkout_cannot_become_a_nested_scheduler_root(self):
        outer = self.root / '.worktrees/outer'
        orch.git(self.root, 'worktree', 'add', '-b', 'outer', str(outer))
        config = copy.deepcopy(self.config)
        config['repository'] = str(outer)
        with self.assertRaisesRegex(orch.Blocked, 'primary checkout'):
            orch.Runner(config)
        self.assertFalse((outer / '.worktrees').exists())

    def test_month_partition_is_used_by_delivered_lifecycle_moves(self):
        self.config['done_partition'] = 'month'
        runner = self.runner()
        self.assertTrue(runner.run())
        expected = f'.ai/plans/done/{date.today():%Y-%m}/PLAN-001-a.md'
        self.assertTrue((self.root / expected).is_file())
        self.assertEqual(runner.state['tracks']['a']['plan_moves'][self.config['tracks'][0]['plans'][0]], expected)

    def test_status_without_run_does_not_create_receipts(self):
        config = orch.validate(copy.deepcopy(self.config))
        self.assertEqual(orch.read_status(config)['status'], 'not_started')
        self.assertFalse((self.root / '.git/orchestration').exists())
        self.assertEqual(orch.git(self.root, 'status', '--porcelain'), '')

    def test_status_reports_receipt_and_live_git_drift_without_writes(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'cannot-review'
        runner = self.runner()
        self.assertFalse(runner.run())
        path, _ = runner.location(self.config['tracks'][0])
        (path / 'uncommitted.txt').write_text('preserve this\n')
        before = runner.state_path.read_bytes()
        report = orch.read_status(runner.config)['tracks'][0]
        self.assertIn('uncommitted.txt', report['dirty'])
        self.assertEqual(report['status'], 'blocked')
        self.assertIn('Git drift', report['next_action'])
        self.assertEqual(runner.state_path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
