"""Policy changes exercised through real Git histories and worker processes."""
import json
import unittest

import test_orchestrate as fixture

orch = fixture.orch


class PolicyWorkflowTests(unittest.TestCase):
    setUp = fixture.RuntimeTests.setUp
    track = fixture.RuntimeTests.track
    runner = fixture.RuntimeTests.runner

    def seed(self, files):
        for name, content in files.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding='utf-8')
        orch.git(self.root, 'add', '.')
        orch.git(self.root, 'commit', '-m', 'Prepare explicit policy scenario')
        orch.git(self.root, 'push')

    def test_pending_intent_blocks_only_its_track_before_worktree_allocation(self):
        self.seed({'.ai/plans/backlog/PLAN-001-a.md': fixture.plan_text('Change intent', [
            {'id': 'implementation', 'phase': 'build', 'title': 'Implement the approved choice'}], [
            {'request': 'Change the supported platform', 'decision': 'pending', 'human_resolution': ''}])})
        self.config['tracks'].append(self.track('b', 21))
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertIn('Human intent decision required', runner.state['tracks']['a']['reason'])
        self.assertFalse(runner.location(self.config['tracks'][0])[0].exists())
        self.assertEqual(runner.state['tracks']['b']['status'], 'merged')

    def test_approved_intent_and_every_step_have_separate_commits(self):
        self.seed({'.ai/plans/backlog/PLAN-001-a.md': fixture.plan_text('Approved behavior', [
            {'id': 'first', 'phase': 'build', 'title': 'Implement the first behavior'},
            {'id': 'second', 'phase': 'build', 'title': 'Implement the second behavior'}], [
            {'request': 'Change the supported platform', 'decision': 'approved',
             'human_resolution': 'The user approved this exact change in the recorded assignment.'}])})
        runner = self.runner()
        self.assertTrue(runner.run())
        commits = runner.state['tracks']['a']['build_step_commits']
        self.assertEqual([step['id'] for step in commits], ['first', 'second'])
        self.assertEqual(len({step['commit'] for step in commits}), 2)
        for step in commits:
            self.assertIn(f"PLAN-Step: .ai/plans/backlog/PLAN-001-a.md#{step['id']}",
                          orch.git(self.root, 'show', '-s', '--format=%B', step['commit']))

    def test_missing_step_commit_cannot_merge(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'uncommitted-step'
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertIn('Missing PLAN step commits', runner.state['tracks']['a']['reason'])
        self.assertFalse(runner.events)

    def test_unfinished_code_cannot_close_even_without_review_findings(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'incomplete-code'
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertIn('Missing code or functionality', runner.state['tracks']['a']['reason'])
        self.assertNotIn('document', runner.state['tracks']['a']['process_attempts'])
        self.assertFalse(runner.events)

    def test_residual_functionality_defect_is_a_fix_and_prevents_merge(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'residual'
        runner = self.runner()
        self.assertFalse(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(state['findings']['code']['id'], 'FIX-001')
        self.assertIn('Missing code or functionality', state['reason'])
        self.assertEqual(state['phase_attempts']['review-2'], 1)
        self.assertFalse(runner.events)

    def test_editorial_findings_are_retained_without_blocking_merge(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'docs-only'
        runner = self.runner()
        self.assertTrue(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(state['documentation_review_verdict'], 'changes_requested')
        self.assertEqual({item['impact'] for item in state['findings'].values()}, {'editorial'})

    def test_missing_spec_coverage_blocks_even_when_worker_claims_complete(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'no-spec-coverage'
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertIn('SPEC coverage', runner.state['tracks']['a']['reason'])
        self.assertFalse(runner.events)

    def test_closeout_moves_only_verified_declared_intake_to_done(self):
        intake = '.ai/plans/intake/INTAKE-901-request.md'
        untouched = '.ai/plans/intake/INTAKE-902-later.md'
        plan = '.ai/plans/backlog/PLAN-001-request.md'
        self.seed({intake: '# Implement the request\n\n[PLAN](../backlog/PLAN-001-request.md)\n', untouched: '# Future fragment\n',
                   plan: fixture.plan_text('Implement request', [
                       {'id': 'implement', 'phase': 'build', 'title': 'Implement request'}], completed_intake=[intake]) +
                   '\n[SPEC](../../specs/SPEC-001-behavior.md)\n[Request](../intake/INTAKE-901-request.md)\n'})
        track = self.config['tracks'][0]
        track['plans'] = [plan]
        track['owned_paths'] += [plan, intake]
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertFalse((self.root / intake).exists())
        self.assertEqual(len(list((self.root / '.ai/plans/done').rglob('INTAKE-901-request.md'))), 1)
        self.assertEqual(len(list((self.root / '.ai/plans/done').rglob('PLAN-001-request.md'))), 1)
        self.assertTrue((self.root / untouched).is_file())
        delivered = next((self.root / '.ai/plans/done').rglob('PLAN-001-request.md')).read_text()
        self.assertIn('[SPEC](../../../specs/SPEC-001-behavior.md)', delivered)
        self.assertIn('[Request](INTAKE-901-request.md)', delivered)
        capture = next((self.root / '.ai/plans/done').rglob('INTAKE-901-request.md')).read_text()
        self.assertIn('[PLAN](PLAN-001-request.md)', capture)

    def test_implementor_can_create_a_reserved_code_finding(self):
        self.config['tracks'][0]['environment']['WORKER_MODE'] = 'direct-finding'
        runner = self.runner()
        self.assertTrue(runner.run())
        record = '.ai/fixes/open/FIX-001-worker.md'
        self.assertTrue((self.root / record).is_file())
        self.assertEqual(runner.followup_queue()['FIX'][0]['id'], 'FIX-001')

    def test_research_note_reaches_code_and_documentation_reviewers(self):
        track = self.config['tracks'][0]
        track['environment']['WORKER_MODE'] = 'research'
        track['research_paths'] = ['.ai/research/RES-001-fixture.md']
        track['owned_paths'] += track['research_paths']
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertTrue((self.root / track['research_paths'][0]).is_file())

    def test_documentor_can_update_plan_notes_after_code_review(self):
        track = self.config['tracks'][0]
        track['documentation_paths'] = ['.ai/plans/backlog/PLAN-001-a.md']
        track['environment']['WORKER_MODE'] = 'plan-notes'
        self.seed({'.ai/plans/backlog/PLAN-001-a.md': fixture.plan_text('Plan notes', [
            {'id': 'implement', 'phase': 'build', 'title': 'Implement behavior'},
            {'id': 'document', 'phase': 'document', 'title': 'Record delivered documentation'}])})
        runner = self.runner()
        self.assertTrue(runner.run())
        delivered = next((self.root / '.ai/plans/done').rglob('PLAN-001-a.md'))
        self.assertIn('Implementation and SPEC coverage verified.', delivered.read_text())

    def test_late_python_documentation_preserves_behavior(self):
        self.seed({'src/module.py': 'VALUE = 1\n'})
        track = self.config['tracks'][0]
        track['source_documentation_paths'] = ['src/module.py']
        track['code_paths'].append('src/module.py')
        track['owned_paths'].append('src/module.py')
        track['environment']['WORKER_MODE'] = 'source-doc'
        runner = self.runner()
        self.assertTrue(runner.run())
        self.assertEqual((self.root / 'src/module.py').read_text(), '"""Runtime module."""\nVALUE = 1\n')

    def test_late_documentor_cannot_change_python_behavior(self):
        self.seed({'src/module.py': 'VALUE = 1\n'})
        track = self.config['tracks'][0]
        track['source_documentation_paths'] = ['src/module.py']
        track['code_paths'].append('src/module.py')
        track['owned_paths'].append('src/module.py')
        track['environment']['WORKER_MODE'] = 'source-doc-code'
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertIn('changed executable behavior', runner.state['tracks']['a']['reason'])
        self.assertFalse(runner.events)

    def test_source_documentation_findings_receive_correction_and_proof(self):
        self.seed({'src/module.py': 'VALUE = 1\n'})
        track = self.config['tracks'][0]
        track['source_documentation_paths'] = ['src/module.py']
        track['code_paths'].append('src/module.py')
        track['owned_paths'].append('src/module.py')
        track['environment']['WORKER_MODE'] = 'source-doc-corrected'
        runner = self.runner()
        self.assertTrue(runner.run())
        state = runner.state['tracks']['a']
        self.assertEqual(state['phase_attempts']['docs-fix'], 1)
        self.assertEqual(state['documentation_review_verdict'], 'approved')
        self.assertEqual((self.root / 'src/module.py').read_text(), '\"\"\"Corrected runtime module.\"\"\"\nVALUE = 1\n')
        finding = state['findings']['source-doc']
        self.assertEqual(finding['attempts'], ['Completed docs-fix'])
        self.assertIn('Completed docs-fix', (self.root / finding['record']).read_text())

    def test_missing_human_evidence_and_short_id_blocks_are_rejected(self):
        self.seed({'.ai/plans/backlog/PLAN-001-a.md': fixture.plan_text('Unresolved intent', [], [
            {'request': 'Change intent', 'decision': 'approved', 'human_resolution': ''}])})
        runner = self.runner()
        self.assertFalse(runner.run())
        self.assertFalse(runner.started)
        self.config['tracks'][0]['ids']['SPEC'] = [1, 5]
        with self.assertRaisesRegex(orch.Blocked, '20 IDs'):
            orch.validate(self.config)


if __name__ == '__main__':
    unittest.main()
