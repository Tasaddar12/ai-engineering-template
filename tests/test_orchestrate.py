import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest

RUNTIME = Path(__file__).resolve().parents[1] / '.ai/runtime/orchestrate.py'
SPEC = importlib.util.spec_from_file_location('orchestrate', RUNTIME)
orch = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(orch)


class FakeForge(orch.Runner):
    """Replace GitHub transport only; exercise real Git push/merge/sync/cleanup."""
    def __init__(self, config, remote_worktree):
        super().__init__(config)
        self.forge_root = remote_worktree
        self.prs = {}
        self.started = {}
        self.finished = {}
        self.events = []
        self.guard = threading.Lock()

    def gh(self, *args):
        if args[:2] == ('repo', 'view'):
            return self.config['github_repo']
        if args[0] == 'api':
            return json.dumps({'required_status_checks': {'strict': True, 'contexts': ['validate']},
                               'enforce_admins': {'enabled': True}})
        if args[:2] == ('pr', 'list'):
            branch = args[args.index('--head') + 1]
            return json.dumps([{'number': n, 'state': p['state']} for n, p in self.prs.items() if p['branch'] == branch])
        if args[:2] == ('pr', 'create'):
            with self.guard:
                number = len(self.prs) + 1
                self.prs[number] = {'state': 'OPEN', 'branch': args[args.index('--head') + 1]}
            return f'https://github.com/fixture/repo/pull/{number}'
        number = int(args[2])
        pr = self.prs[number]
        head = orch.git(self.forge_root, 'ls-remote', 'origin', f'refs/heads/{pr["branch"]}').split()[0]
        if args[:2] == ('pr', 'view'):
            return json.dumps({'state': pr['state'], 'headRefOid': head,
                               'mergeCommit': {'oid': pr.get('merge')}, 'reviewDecision': '',
                               'statusCheckRollup': [{'name': 'validate', 'status': 'COMPLETED', 'conclusion': 'SUCCESS'}]})
        if args[:2] == ('pr', 'edit'):
            return ''
        if args[:2] == ('pr', 'merge'):
            assert args[args.index('--match-head-commit') + 1] == head
            orch.git(self.forge_root, 'fetch', 'origin')
            orch.git(self.forge_root, 'merge', '--ff-only', 'origin/main')
            orch.git(self.forge_root, 'merge', '--no-ff', '--no-edit', head)
            orch.git(self.forge_root, 'push', 'origin', 'main')
            pr.update(state='MERGED', merge=orch.git(self.forge_root, 'rev-parse', 'HEAD'))
            self.events.append(('merge', pr['branch']))
            return ''
        raise AssertionError(args)

    def phase(self, track, name, **kwargs):
        if name == 'build':
            self.started[track['id']] = time.monotonic()
        result = super().phase(track, name, **kwargs)
        if name == 'build':
            self.finished[track['id']] = time.monotonic()
        return result


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.root = self.directory / 'repo'
        self.root.mkdir()
        orch.git(self.root, 'init', '-b', 'main')
        for key, value in [('user.name', 'Runtime Test'), ('user.email', 'test@example.invalid'), ('core.autocrlf', 'false')]:
            orch.git(self.root, 'config', key, value)
        (self.root / '.gitignore').write_text('.worktrees/\n', encoding='utf-8')
        (self.root / 'docs.md').write_text('original docs\n', encoding='utf-8')
        for name in ('a', 'b', 'c'):
            (self.root / f'PLAN-{name}.md').write_text('Build ' + name, encoding='utf-8')
        orch.git(self.root, 'add', '.')
        orch.git(self.root, 'commit', '-m', 'Initialize fixture')
        self.remote = self.directory / 'remote.git'
        orch.git(self.directory, 'init', '--bare', str(self.remote))
        orch.git(self.root, 'remote', 'add', 'origin', str(self.remote))
        orch.git(self.root, 'push', '-u', 'origin', 'main')
        self.forge = self.directory / 'forge'
        orch.git(self.directory, 'clone', '--branch', 'main', str(self.remote), str(self.forge))
        orch.git(self.forge, 'config', 'user.name', 'Forge Test')
        orch.git(self.forge, 'config', 'user.email', 'forge@example.invalid')
        self.config = dict(run_id='ORCH-001', repository=str(self.root), base_branch='main', remote='origin',
                           github_repo='fixture/repo', branch_prefix='orch', max_parallel_tracks=3,
                           worker_command=[sys.executable, str(Path(__file__).with_name('worker_fixture.py').resolve())],
                           required_commands=[[sys.executable, '-c', 'print("checks pass")']],
                           required_status_checks=['validate'], github_timeout_seconds=0, tracks=[self.track('a', 1)])

    def track(self, name, start, **kwargs):
        return dict(id=name, plans=[f'PLAN-{name}.md'], depends_on=kwargs.get('deps', []),
                    owned_paths=[f'src/{name}.txt', f'PLAN-{name}.md', 'docs.md'] if kwargs.get('docs') else
                                [f'src/{name}.txt', f'PLAN-{name}.md'],
                    code_paths=[f'src/{name}.txt'], resources=kwargs.get('resources', []),
                    environment=kwargs.get('env', {}), ids={'FIX': [start, start + 19], 'INTAKE': [start, start + 19]})

    def runner(self):
        return FakeForge(self.config, self.forge)

    def test_parallel_tracks_sync_before_dependent_and_cleanup(self):
        self.config['tracks'] = [self.track('a', 1, env={'WORKER_DELAY': '0.4'}),
                                 self.track('b', 21, env={'WORKER_DELAY': '0.4'}),
                                 self.track('c', 41, deps=['a'], env={'REQUIRE_FILES': '["src/a.txt"]'})]
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertLess(runner.started['b'], runner.finished['a'])
        self.assertTrue(all(s['cleaned'] for s in runner.state['tracks'].values()))
        self.assertEqual(orch.git(self.root, 'rev-parse', 'HEAD'), orch.git(self.root, 'rev-parse', 'origin/main'))
        self.assertEqual(orch.git(self.root, 'branch', '--format=%(refname:short)'), 'main')
        self.assertEqual(len(orch.git(self.root, 'worktree', 'list', '--porcelain').split('worktree ')), 2)
        self.assertTrue(json.loads((runner.directory / 'followups.json').read_text())['eligible'])

    def test_residual_findings_are_code_fix_and_separate_intakes_after_two_rounds(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'residual'
        runner = self.runner()
        self.assertTrue(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(set(state['completed_phases']), {'build', 'review-1', 'fix', 'review-2'})
        self.assertEqual(state['review_verdict'], 'changes_requested')
        self.assertEqual(len(list((self.root / '.ai/fixes/open').glob('FIX-*.md'))), 1)
        self.assertEqual(len(list((self.root / '.ai/plans/intake').glob('INTAKE-*.md'))), 2)
        self.assertNotEqual(state['reviewed_sha'], state['phase_heads']['review-1'])
        self.assertIn('followup_audit', runner.state)
        report = next((self.root / '.ai/fixes/open').glob('FIX-*.md')).read_text()
        self.assertIn('Attempted correction', report)
        self.assertIn('Completed fix', report)

    def test_documentation_findings_do_not_invoke_code_fixer(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'docs-only'
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertEqual(set(runner.state['tracks']['a']['completed_phases']), {'build', 'review-1'})
        self.assertFalse((self.root / '.ai/fixes/open').exists())

    def test_final_plan_run_audits_open_fixes_from_earlier_runs(self):
        report = self.root / '.ai/fixes/open/FIX-900-earlier-run.md'
        report.parent.mkdir(parents=True)
        report.write_text('# Earlier code defect\n\nProof still needs verification.\n', encoding='utf-8')
        orch.git(self.root, 'add', '.ai')
        orch.git(self.root, 'commit', '-m', 'Retain an earlier deferred defect')
        orch.git(self.root, 'push')
        runner = self.runner()
        self.assertTrue(runner.run())
        queue = json.loads((runner.directory / 'followups.json').read_text())
        self.assertEqual(queue['FIX'][0]['id'], 'FIX-900')
        self.assertIn('followup_audit', runner.state)

    def test_plan_lifecycle_moves_are_in_pr_and_other_plans_delay_audit(self):
        source = '.ai/plans/backlog/PLAN-001-a.md'
        other = '.ai/plans/backlog/PLAN-999-later.md'
        for name in (source, other):
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text('# Planned behavior\n', encoding='utf-8')
        orch.git(self.root, 'add', '.ai')
        orch.git(self.root, 'commit', '-m', 'Add fixture plans')
        orch.git(self.root, 'push')
        track = self.config['tracks'][0]
        track['plans'] = [source]
        track['owned_paths'].append(source)
        track['environment']['WORKER_MODE'] = 'residual'
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertFalse((self.root / source).exists())
        self.assertEqual(len(list((self.root / '.ai/plans/done').rglob('PLAN-001-a.md'))), 1)
        queue = json.loads((runner.directory / 'followups.json').read_text())
        self.assertFalse(queue['eligible'])
        self.assertNotIn('followup_audit', runner.state)

    def test_cannot_review_parks_track_but_independent_plan_merges(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'cannot-review'
        self.config['tracks'].append(self.track('b', 21))
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertEqual(runner.state['tracks']['a']['status'], 'blocked')
        self.assertEqual(runner.state['tracks']['b']['status'], 'merged')
        self.assertFalse(json.loads((runner.directory / 'followups.json').read_text())['eligible'])

    def test_scope_escape_and_mutating_review_and_doc_fix_are_blocked(self):
        for mode in ('outside', 'mutating-review', 'fix-doc'):
            with self.subTest(mode=mode):
                # Each isolated schedule uses a separate fixture from setUp.
                config = copy.deepcopy(self.config)
                config['run_id'] = mode
                config['tracks'][0]['environment']['WORKER_MODE'] = mode
                config['tracks'][0]['owned_paths'].append('docs.md')
                runner = FakeForge(config, self.forge)
                runner.preflight = runner.sync
                self.assertFalse(runner.run())
                self.assertEqual(runner.state['tracks']['a']['status'], 'blocked')

    def test_required_command_failure_cannot_merge(self):
        self.config['required_commands'] = [[sys.executable, '-c', 'raise SystemExit(3)']]
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertEqual(runner.state['tracks']['a']['status'], 'blocked')
        self.assertFalse(runner.events)

    def test_declared_resource_serializes_independent_tracks(self):
        self.config['tracks'] = [self.track('a', 1, resources=['port:8000'], env={'WORKER_DELAY': '0.2'}),
                                 self.track('b', 21, resources=['port:8000'])]
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertGreater(runner.started['b'], runner.finished['a'])

    def test_same_owned_directory_serializes_tracks(self):
        self.config['tracks'] = [self.track('a', 1), self.track('b', 21)]
        for track in self.config['tracks']:
            track['owned_paths'].append('src/')
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertGreater(runner.started['b'], runner.finished['a'])

    def test_example_directory_scopes_validate(self):
        config = json.loads(RUNTIME.with_name('schedule.example.json').read_text())
        orch.validate(config)
        self.assertTrue(orch.overlaps('src/api/', 'src/api/'))
        self.assertTrue(orch.overlaps('src/api/', 'SRC/API/'))
        self.config['tracks'][0]['owned_paths'].append('src')
        self.config['tracks'][0]['code_paths'] = ['src/']
        with self.assertRaisesRegex(orch.Blocked, 'Code paths'):
            orch.validate(self.config)

    def test_missing_github_check_is_not_success(self):
        runner = self.runner()
        original = runner.gh
        def missing(*args):
            if args[:2] == ('pr', 'view'):
                data = json.loads(original(*args))
                data['statusCheckRollup'] = []
                return json.dumps(data)
            return original(*args)
        runner.gh = missing
        self.assertFalse(runner.run())
        self.assertFalse(runner.events)
        self.assertIn('missing', runner.state['tracks']['a']['reason'])

    def test_pr_creation_failure_cannot_report_ready(self):
        runner = self.runner()
        original = runner.gh
        def failing(*args):
            if args[:2] == ('pr', 'create'):
                raise orch.Blocked('PR creation failed')
            return original(*args)
        runner.gh = failing
        self.assertFalse(runner.run())
        self.assertEqual(runner.state['tracks']['a']['status'], 'blocked')
        self.assertFalse(runner.events)

    def test_target_advance_requires_reintegration_before_merge(self):
        runner = self.runner()
        check = runner.wait_checks
        def advance(pr, head):
            check(pr, head)
            (self.forge / 'target.txt').write_text('external change\n', encoding='utf-8')
            orch.git(self.forge, 'add', 'target.txt')
            orch.git(self.forge, 'commit', '-m', 'Advance target during validation')
            orch.git(self.forge, 'push', 'origin', 'main')
        runner.wait_checks = advance
        self.assertFalse(runner.run())
        self.assertFalse(runner.events)
        self.assertIn('Target advanced', runner.state['tracks']['a']['reason'])
        runner.wait_checks = check
        self.assertTrue(runner.run())
        self.assertTrue((self.root / 'target.txt').is_file())

    def test_cleanup_failure_preserves_merged_status_and_local_files(self):
        runner = self.runner()
        cleanup = runner.cleanup
        def dirty(track):
            (runner.location(track)[0] / 'precious.txt').write_text('keep me', encoding='utf-8')
            cleanup(track)
        runner.cleanup = dirty
        self.assertFalse(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(state['status'], 'merged')
        self.assertFalse(state.get('cleaned'))
        self.assertTrue((runner.location(self.config['tracks'][0])[0] / 'precious.txt').exists())

    def test_pr_head_failure_skipped_check_and_formal_rejection_block(self):
        runner = self.runner()
        for data in [
            {'headRefOid': 'other', 'state': 'OPEN', 'statusCheckRollup': []},
            {'headRefOid': 'sha', 'state': 'OPEN', 'statusCheckRollup': [
                {'name': 'validate', 'status': 'COMPLETED', 'conclusion': 'SKIPPED'}]},
            {'headRefOid': 'sha', 'state': 'OPEN', 'statusCheckRollup': [], 'reviewDecision': 'CHANGES_REQUESTED'},
        ]:
            with self.subTest(data=data), self.assertRaises(orch.Blocked):
                runner.gh = lambda *args: json.dumps(data)
                runner.wait_checks(1, 'sha')

    def test_protection_must_require_up_to_date_checks_without_admin_bypass(self):
        runner = self.runner()
        runner.api = lambda suffix: {'required_status_checks': {'strict': True, 'contexts': ['validate']},
                                    'enforce_admins': {'enabled': False}}
        with self.assertRaisesRegex(orch.Blocked, 'administrators'):
            runner.preflight()

    def test_restart_after_uncertain_merge_syncs_and_cleans_without_new_reviews(self):
        runner = self.runner()
        finish = runner.finish_merge
        def interrupted(track):
            raise orch.Blocked('Simulated lost response after merge')
        runner.finish_merge = interrupted
        self.assertFalse(runner.run())
        before = copy.deepcopy(runner.state['tracks']['a']['completed_phases'])
        runner.finish_merge = finish
        self.assertTrue(runner.run())
        self.assertEqual(before, runner.state['tracks']['a']['completed_phases'])
        self.assertEqual(len(runner.prs), 1)

    def test_interrupted_writer_is_not_replayed(self):
        runner = self.runner()
        runner.state['tracks']['a'].update(status='running', inflight_phase='fix')
        runner.save()
        self.assertFalse(runner.run())
        self.assertFalse(runner.started)
        self.assertIn('Interrupted worker', runner.state['tracks']['a']['reason'])

    def test_invalid_schedules(self):
        for field, value in [('required_commands', []), ('required_status_checks', []), ('max_parallel_tracks', 0)]:
            config = copy.deepcopy(self.config)
            config[field] = value
            with self.subTest(field=field), self.assertRaises(orch.Blocked):
                orch.validate(config)
        for path in ('../outside', '/absolute', 'C:/escape', '.', 'src/*', 'src/../docs.md'):
            with self.subTest(path=path), self.assertRaises(orch.Blocked):
                orch.relative_path(path)
        self.config['tracks'].append(self.track('b', 1, deps=['a']))
        with self.assertRaisesRegex(orch.Blocked, 'reservations'):
            orch.validate(self.config)
        self.config['tracks'][1] = self.track('b', 21, deps=['a'])
        self.config['tracks'][0]['depends_on'] = ['b']
        with self.assertRaisesRegex(orch.Blocked, 'Cyclic'):
            orch.validate(self.config)

    def test_scope_prefix_boundaries(self):
        self.assertTrue(orch.covers('src/api/', 'src/api/server.py'))
        self.assertFalse(orch.covers('src/api/', 'src/api2/server.py'))
        self.assertTrue(orch.overlaps('src/', 'src/api/'))
        self.assertTrue(orch.overlaps('src/api/', 'SRC/API/file.py'))
        self.assertFalse(orch.overlaps('a.txt', 'a.txt.bak'))


if __name__ == '__main__':
    unittest.main()
