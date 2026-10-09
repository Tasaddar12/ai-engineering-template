"""Adversarial specialist evidence and acceptance currentness, real Git/CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml

RUNTIME = Path(__file__).resolve().parents[1] / '.ai/runtime/phase.py'


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repo'
        self.root.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Evidence Test')
        self.git('config', 'user.email', 'evidence@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        self.write('.gitignore', '.planning/verification-evidence/\n')
        self.write('src/a.py', 'a = 1\n')
        self.write('deps.lock', 'v1\n')
        self.write('.planning/ROADMAP.md', '''# Roadmap

- [ ] **Phase 1: Evidence** - bounded

### Phase 1: Evidence

**Goal**: Verify evidence
**Requirements**: REQ-01

Plans:
- [ ] 01-01: Implement evidence
''')
        self.write('.planning/REQUIREMENTS.md', '''# Requirements

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-01 | 1 | In progress |
''')
        self.state(False)
        summary = dict(phase='01-evidence', plan='01', status='complete', acceptance=['AC-01'],
                       documentation=[], coverage=[dict(id='D1', description='Evidence implementation',
                       requirement='REQ-01', human_judgment=False,
                       verification=[dict(kind='unit', ref='tests/test_evidence.py', status='pass')])])
        summary['requirements-completed'] = ['REQ-01']
        self.write('.planning/phases/01-evidence/01-01-SUMMARY.md',
                   '---\n' + yaml.safe_dump(summary) + '---\n# Summary\n\nImplemented and checked.\n')
        self.commit('initial')

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True,
                              text=True, encoding='utf-8').stdout.strip()

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def commit(self, message):
        self.git('add', '-A')
        self.git('commit', '-qm', message)
        return self.git('rev-parse', 'HEAD')

    def query(self, verb, *args, ok=True):
        process = subprocess.run([sys.executable, str(RUNTIME), 'query', verb, *map(str, args)],
                                 cwd=self.root, capture_output=True, text=True, encoding='utf-8',
                                 env=dict(os.environ, PYTHONIOENCODING='utf-8'), timeout=30)
        self.assertNotIn('Traceback', process.stderr, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result['ok'], ok, result)
        self.assertEqual(process.returncode, 0 if ok else 1, result)
        return result

    def external(self, name, value):
        path = Path(self.temp.name) / name
        path.write_text(json.dumps(value), encoding='utf-8')
        return path

    def request(self, kind='review', **updates):
        result = dict(schema=1, kind=kind, revision=self.git('rev-parse', 'HEAD'), scope=['src'],
                      inputs=['deps.lock'], configuration={'mode': 'strict'}, question='Assess source correctness')
        if kind == 'review':
            result['requirements'] = ['correctness', 'security']
        if kind == 'scout':
            result['requested_fields'] = ['symbols']
        result.update(updates)
        return result

    def packet(self, request, **updates):
        result = dict(status='passed', inspected_revision=request['revision'], findings=[],
                      provenance={'reviewer': 'independent-test', 'role': 'code-reviewer', 'report_sha256': 'example'})
        if request['kind'] == 'scout':
            result.update(status='complete', field_results={'symbols': dict(status='found', value=['a'], evidence=['src/a.py:1'])}, evidence=['src/a.py:1'],
                          search_scope=['src/a.py'], absence_claims=[])
        else:
            result['covered_paths'] = ['src/a.py']
        result.update(updates)
        return result

    def record(self, request=None, packet=None, ok=True):
        request = request or self.request()
        return self.query('evidence.record', self.external('request.json', request), '--result',
                          self.external('result.json', packet or self.packet(request)), ok=ok)

    def lookup(self, request=None, ok=True):
        return self.query('evidence.lookup', self.external('lookup.json', request or self.request()), ok=ok)

    def state(self, complete):
        progress = dict(total_phases=1, completed_phases=int(complete), total_plans=1,
                        completed_plans=int(complete), percent=100 if complete else 0)
        metadata = dict(workflow_state_version='1.0', status='executing', progress=progress)
        self.write('.planning/STATE.md', '---\n' + yaml.safe_dump(metadata) + '---\n' + '''# State

## Current Position

Phase: 1 of 1 (Evidence)
Plan: 1 of 1 in current phase
Status: ''' + ('Complete' if complete else 'In progress') + '''
Last activity: 2026-10-09 - evidence work

## Session Continuity

Last session: 2026-10-09 10:00
Stopped at: evidence work
Resume file: .planning/STATE.md
''')

    def report(self, **updates):
        source = self.git('rev-parse', 'HEAD')
        metadata = dict(schema=1, phase='01-evidence', status='passed', revision=source,
                        verified_at='2026-10-09T10:00:00Z', findings=[],
                        acceptance=['AC-01'], requirements_completed=['REQ-01'])
        metadata.update(updates)
        self.write('.planning/phases/01-evidence/01-VERIFICATION.md',
                   '---\n' + yaml.safe_dump(metadata) + '---\n# Acceptance\n\nSource checked.\n')
        return source, self.commit('report only')

    def bookkeeping(self):
        before = self.git('rev-parse', 'HEAD')
        for name in ('.planning/ROADMAP.md',):
            text = (self.root / name).read_text().replace('- [ ]', '- [x]')
            self.write(name, text)
        self.query('requirements.set-status', 'REQ-01', 'Complete')
        self.state(True)
        return before, self.commit('completion bookkeeping')

    def test_review_reuse_keeps_original_revision_and_accepts_delayed_result(self):
        request = self.request()
        original = request['revision']
        self.write('unrelated.txt', 'unrelated')
        self.commit('unrelated')
        self.record(request)
        result = self.lookup()
        self.assertTrue(result['reusable'])
        self.assertEqual(result['inspected_revision'], original)
        self.assertEqual(result['result']['provenance']['role'], 'code-reviewer')

    def test_source_dependency_question_config_requirements_and_manifest_invalidate(self):
        self.record()
        for updates in ({'question': 'Different question'}, {'configuration': {'mode': 'loose'}},
                        {'requirements': ['different requirement']}, {'scope': ['src/a.py']},
                        {'inputs': []}):
            self.assertFalse(self.lookup(self.request(**updates))['reusable'])
        for name, value in [('deps.lock', 'v2'), ('src/a.py', 'a = 2'), ('src/new.py', 'new = 1')]:
            self.write(name, value)
            self.commit('change input')
            self.assertEqual(self.lookup()['status'], 'never_run')
        self.assertEqual(self.lookup(self.request(schema=2), ok=False)['code'], 'bad-evidence')

    def test_failed_incomplete_unresolved_and_corrupt_are_distinct(self):
        request = self.request()
        self.assertEqual(self.lookup()['status'], 'never_run')
        for status in ('failed', 'incomplete'):
            self.record(request, self.packet(request, status=status, covered_paths=[]))
            result = self.lookup()
            self.assertEqual(result['status'], status)
            self.assertFalse(result['reusable'])
        receipt = self.record(request, self.packet(request, findings=[dict(severity='high', message='bug', resolved=False)]))
        self.assertFalse(self.lookup()['reusable'])
        path = self.root / receipt['receipt']
        envelope = json.loads(path.read_text())
        envelope['receipt']['result']['findings'] = []
        path.write_text(json.dumps(envelope))
        self.assertEqual(self.lookup()['status'], 'never_run')
        path.write_text('{broken')
        self.assertEqual(self.lookup()['status'], 'never_run')

    def test_dirty_tree_wrong_head_coverage_and_inspected_revision_fail_closed(self):
        request = self.request()
        self.record()
        self.write('dirty.txt', 'dirty')
        self.assertFalse(self.lookup()['reusable'])
        self.record(ok=False)
        (self.root / 'dirty.txt').unlink()
        self.record(request, self.packet(request, covered_paths=[]), ok=False)
        self.record(request, self.packet(request, inspected_revision='0' * 40), ok=False)
        self.git('commit', '--allow-empty', '-qm', 'head advanced')
        self.assertEqual(self.lookup(request)['reason'], 'dirty_or_wrong_head')

    def test_strict_json_unknown_fields_duplicates_nonfinite_and_path_literals(self):
        for updates in ({'scope': ['../src']}, {'scope': ['src/*']}, {'scope': ['missing']},
                        {'unknown': True}, {'schema': True}, {'kind': []}, {'configuration': []}):
            self.record(self.request(**updates), ok=False)
        request_path = self.external('invalid.json', self.request())
        for content in ('{"schema":1,"schema":1}', '{"schema":NaN}', '[0]'):
            request_path.write_text(content)
            self.query('evidence.lookup', request_path, ok=False)

    def test_scout_absence_requires_complete_declared_coverage(self):
        request = self.request('scout')
        self.record(request)
        self.assertTrue(self.lookup(request)['reusable'])
        self.record(request, self.packet(request, search_scope=[], absence_claims=['symbols']), ok=False)
        self.record(request, self.packet(request, status='incomplete', absence_claims=['symbols']), ok=False)
        self.record(request, self.packet(request, field_results={'extra': []}), ok=False)
        self.write('src/new.py', 'b = 2')
        self.commit('new search target')
        self.assertFalse(self.lookup(self.request('scout'))['reusable'])

    def test_report_only_currentness_and_source_edit_revert(self):
        source, _ = self.report()
        current = self.query('verification.currentness', '1')
        self.assertTrue(current['current'], current)
        self.assertEqual(current['revision'], source)
        self.write('src/a.py', 'a = 2')
        edit = self.commit('source edit')
        self.git('revert', '--no-edit', edit)
        self.assertFalse(self.query('verification.currentness', '1')['current'])

    def test_missing_failed_malformed_unresolved_and_dirty_reports(self):
        self.assertEqual(self.query('verification.currentness', '1')['status'], 'never_run')
        for changes in ({'status': 'gaps_found'}, {'schema': 2}, {'revision': 'missing'},
                        {'findings': {}}, {'findings': [dict(severity='critical', message='bug', resolved=False)]},
                        {'behavior_unverified': 1}, {'verified_at': 'not-a-date'}, {'phase': 'wrong'}):
            self.report(**changes)
            self.assertFalse(self.query('verification.currentness', '1')['current'])
        self.report()
        self.write('untracked', 'dirty')
        self.assertFalse(self.query('verification.currentness', '1')['current'])

    def test_bookkeeping_requires_validated_exact_delta_receipt(self):
        source, _ = self.report()
        before, after = self.bookkeeping()
        self.assertFalse(self.query('verification.currentness', '1')['current'])
        result = self.query('verification.validate-bookkeeping', '--before', before, '--after', after)
        self.assertTrue(result['valid'])
        current = self.query('verification.currentness', '1')
        self.assertTrue(current['current'], current)
        self.assertEqual(current['revision'], source)
        envelope = json.loads((self.root / result['receipt']).read_text())
        self.assertEqual(envelope['receipt']['source_revision'], source)
        self.assertEqual(set(envelope['receipt']['delta']),
                         {'.planning/STATE.md', '.planning/ROADMAP.md', '.planning/REQUIREMENTS.md'})
        envelope['receipt']['after'] = before
        (self.root / result['receipt']).write_text(json.dumps(envelope))
        self.assertFalse(self.query('verification.currentness', '1')['current'])

    def test_bookkeeping_rejects_other_paths_bad_counters_and_goal_changes(self):
        self.report()
        before, after = self.bookkeeping()
        self.write('src/a.py', 'a = 2')
        changed = self.commit('source change')
        self.query('verification.validate-bookkeeping', '--before', after, '--after', changed, ok=False)
        self.query('verification.validate-bookkeeping', '--before', before, '--after', changed, ok=False)

    def test_invalid_bookkeeping_schema_and_completion_transitions(self):
        self.report()
        before, _ = self.bookkeeping()
        for name, transform in (
            ('.planning/STATE.md', lambda text: text.replace('percent: 100', 'percent: 99')),
            ('.planning/ROADMAP.md', lambda text: text.replace('Verify evidence', 'New goal')),
            ('.planning/REQUIREMENTS.md', lambda text: text.replace('| REQ-01 | 1 | Complete |', '| REQ-01 | 2 | Complete |'))):
            self.git('restore', '--source', before, '--', *sorted({'.planning/STATE.md', '.planning/ROADMAP.md', '.planning/REQUIREMENTS.md'}))
            self.git('commit', '-am', 'restore bookkeeping')
            start = self.git('rev-parse', 'HEAD')
            self.write(name, transform((self.root / name).read_text().replace('In progress', 'Complete')))
            after = self.commit('invalid bookkeeping')
            self.query('verification.validate-bookkeeping', '--before', start, '--after', after, ok=False)

    def test_individual_review_receipts_cover_final_source_without_claiming_new_files(self):
        original = self.request(scope=['src/a.py'])
        self.record(original)
        self.write('src/b.py', 'b = 2')
        self.commit('new source')
        old = self.lookup(self.request(scope=['src/a.py']))
        self.assertTrue(old['reusable'])
        self.assertEqual(old['result']['covered_paths'], ['src/a.py'])
        self.assertFalse(self.lookup()['reusable'])
        new = self.request(scope=['src/b.py'])
        self.record(new, self.packet(new, covered_paths=['src/b.py']))
        covered = set(old['result']['covered_paths']) | set(self.lookup(new)['result']['covered_paths'])
        self.assertEqual(covered, {'src/a.py', 'src/b.py'})

    def test_merges_fail_closed_even_when_final_tree_matches(self):
        source, tip = self.report()
        merge = self.git('commit-tree', self.git('rev-parse', 'HEAD^{tree}'), '-p', tip, '-p', source,
                         '-m', 'merge unchanged tree')
        self.git('update-ref', self.git('symbolic-ref', 'HEAD'), merge, tip)
        self.assertFalse(self.query('verification.currentness', '1')['current'])

    def test_bookkeeping_replay_rejects_forged_integrity_valid_allowlist_receipt(self):
        self.report()
        before, after = self.bookkeeping()
        valid = self.query('verification.validate-bookkeeping', '--before', before, '--after', after)
        packet = json.loads((self.root / valid['receipt']).read_text())
        state = (self.root / '.planning/STATE.md').read_text().replace('percent: 100', 'percent: 99')
        self.write('.planning/STATE.md', state)
        invalid = self.commit('malformed state counter')
        receipt = packet['receipt']
        receipt.update(before=after, after=invalid)
        receipt['delta'] = {'.planning/STATE.md': {
            'before': ['100644', 'blob', self.git('rev-parse', after + ':.planning/STATE.md')],
            'after': ['100644', 'blob', self.git('rev-parse', invalid + ':.planning/STATE.md')]}}
        digest = lambda value: __import__('hashlib').sha256(json.dumps(
            value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
        key = digest(dict(kind='bookkeeping', schema=1, before=after, after=invalid))
        self.write('.planning/verification-evidence/' + key + '.json',
                   json.dumps(dict(receipt=receipt, sha256=digest(receipt))))
        self.assertFalse(self.query('verification.currentness', '1')['current'])

    def test_bookkeeping_cannot_complete_without_actual_summary_coverage(self):
        name = '.planning/phases/01-evidence/01-01-SUMMARY.md'
        content = (self.root / name).read_text().replace('human_judgment: false', 'human_judgment: true')
        self.write(name, content)
        self.commit('human coverage requires independent reconciliation')
        self.report()
        before, after = self.bookkeeping()
        result = self.query('verification.validate-bookkeeping', '--before', before, '--after', after, ok=False)
        self.assertIn('human judgment', result['error'])

    def test_duplicate_report_yaml_fields_fail_closed(self):
        self.report()
        name = '.planning/phases/01-evidence/01-VERIFICATION.md'
        self.write(name, (self.root / name).read_text().replace('schema: 1', 'schema: 1\nschema: 1'))
        self.commit('ambiguous report')
        self.assertFalse(self.query('verification.currentness', '1')['current'])

    def test_deleted_scope_and_storage_schema_mismatch_are_cache_misses(self):
        record = self.record()
        path = self.root / record['receipt']
        packet = json.loads(path.read_text())
        packet['receipt']['schema'] = 2
        path.write_text(json.dumps(packet))
        self.assertFalse(self.lookup()['reusable'])
        (self.root / 'src/a.py').unlink()
        self.commit('deleted source')
        self.assertEqual(self.lookup(ok=False)['code'], 'bad-evidence')

    def test_phase_one_report_cannot_complete_phase_two(self):
        name = '.planning/ROADMAP.md'
        content = (self.root / name).read_text()
        content = content.replace('### Phase 1:', '- [ ] **Phase 2: Other** - unrelated\n\n### Phase 1:')
        content += '\n### Phase 2: Other\n\n**Goal**: Other goal\n\nPlans:\n- [ ] 02-01: Other work\n'
        self.write(name, content)
        self.query('state.update-progress')
        self.commit('second phase exists')
        self.report()
        before = self.git('rev-parse', 'HEAD')
        self.write(name, (self.root / name).read_text().replace('- [ ]', '- [x]'))
        self.query('state.update-progress')
        after = self.commit('unrelated phase completion')
        result = self.query('verification.validate-bookkeeping', '--before', before, '--after', after, ok=False)
        self.assertIn('accepted completion', result['error'])

    def test_missing_summary_and_failed_coverage_reject_completion(self):
        name = '.planning/phases/01-evidence/01-01-SUMMARY.md'
        self.write(name, (self.root / name).read_text().replace('status: pass', 'status: fail'))
        self.commit('failed coverage')
        self.report()
        before, after = self.bookkeeping()
        result = self.query('verification.validate-bookkeeping', '--before', before, '--after', after, ok=False)
        self.assertIn('automated passing', result['error'])

    def test_bookkeeping_receipt_chain_and_valid_progress_table(self):
        roadmap = self.root / '.planning/ROADMAP.md'
        self.write('.planning/ROADMAP.md', roadmap.read_text() + '\n## Progress\n\n'
                   '| Phase | Plans Complete | Status | Completed |\n'
                   '|-------|----------------|--------|-----------|\n'
                   '| 1. Evidence | 0/1 | Not started | - |\n')
        self.commit('progress table')
        source, _ = self.report()
        before = self.git('rev-parse', 'HEAD')
        self.query('roadmap.update-plan-progress', '01-01')
        self.query('requirements.set-status', 'REQ-01', 'Complete')
        self.query('state.update-progress')
        self.query('state.record-session', '--status', 'Complete', '--stopped-at', 'validated completion')
        # Runtime set-plan also derives its phase checklist and progress table.
        after = self.commit('native completion')
        first = self.query('verification.validate-bookkeeping', '--before', before, '--after', after)
        self.assertTrue(first['valid'])
        self.query('state.record-session', '--status', 'Preparing publication', '--stopped-at', 'publication preparation')
        second = self.commit('native publication session')
        self.query('verification.validate-bookkeeping', '--before', after, '--after', second)
        current = self.query('verification.currentness', '1')
        self.assertTrue(current['current'], current)
        self.assertEqual(current['revision'], source)

    def test_compensation_and_nonpass_session_cannot_reuse_old_passed_report(self):
        self.report()
        before, after = self.bookkeeping()
        self.query('verification.validate-bookkeeping', '--before', before, '--after', after)
        self.assertTrue(self.query('verification.currentness', '1')['current'])
        self.git('revert', '--no-edit', after)
        self.assertFalse(self.query('verification.currentness', '1')['current'])
        self.query('state.record-session', '--status', 'Verification gaps_found', '--stopped-at', 'verification failed')
        self.commit('nonpass session')
        self.assertEqual(self.query('verification.status', '1')['status'], 'passed')
        self.assertFalse(self.query('verification.currentness', '1')['current'])

    def test_unresolved_questions_and_nonconclusive_fields_are_incomplete(self):
        request = self.request()
        self.record(request, self.packet(request, unresolved_questions=['security dependency unresolved']))
        self.assertEqual(self.lookup()['status'], 'incomplete')
        self.assertFalse(self.lookup()['reusable'])
        self.record(request, self.packet(request, findings=[dict(severity='low', message='advisory accepted', resolved=True)]))
        self.assertTrue(self.lookup()['reusable'])
        scout = self.request('scout')
        self.record(scout, self.packet(scout, field_results={'symbols': dict(status='incomplete', evidence=[])}))
        self.assertEqual(self.lookup(scout)['status'], 'incomplete')
        self.assertFalse(self.lookup(scout)['reusable'])
        self.record(scout, self.packet(scout, field_results={'symbols': None}), ok=False)
        absent = self.packet(scout, field_results={'symbols': dict(status='absent', evidence=['src/a.py searched'])},
                             absence_claims=['symbols'])
        self.record(scout, absent)
        self.assertTrue(self.lookup(scout)['reusable'])

    def test_review_diff_base_covers_deletion_rename_and_new_files(self):
        base = self.git('rev-parse', 'HEAD')
        self.write('src/remaining.py', 'remaining = 1')
        self.git('mv', 'src/a.py', 'src/renamed.py')
        self.write('src/new.py', 'new = 2')
        inspected = self.commit('rename and add source')
        request = self.request(base_revision=base)
        covered = ['src/a.py', 'src/remaining.py', 'src/renamed.py', 'src/new.py']
        recorded = self.record(request, self.packet(request, covered_paths=covered))
        self.assertTrue(recorded['reusable'])
        packet = json.loads((self.root / recorded['receipt']).read_text())['receipt']
        manifest = packet['inputs']['scope_manifest']
        self.assertIsNone(manifest['src/a.py']['after'])
        self.assertEqual(manifest['src/a.py']['before'][1], self.git('rev-parse', base + ':src/a.py'))
        self.assertIsNone(manifest['src/renamed.py']['before'])
        self.assertTrue(self.lookup(request)['reusable'])
        self.write('unrelated.txt', 'unrelated')
        self.commit('unrelated source-independent work')
        reuse = self.lookup(self.request(base_revision=base))
        self.assertTrue(reuse['reusable'])
        self.assertEqual(reuse['inspected_revision'], inspected)
        self.write('src/later.py', 'later = 3')
        self.commit('new covered source')
        self.assertFalse(self.lookup(self.request(base_revision=base))['reusable'])

    def test_review_diff_base_rejects_typos_nonancestors_and_incomplete_deletion_coverage(self):
        base = self.git('rev-parse', 'HEAD')
        (self.root / 'src/a.py').unlink()
        self.write('src/survivor.py', 'survivor = 1')
        self.commit('delete source')
        request = self.request(base_revision=base, scope=['src/a.py', 'src/survivor.py'])
        self.record(request, self.packet(request, covered_paths=['src/survivor.py']), ok=False)
        self.record(self.request(base_revision=base, scope=['src/typo.py']), ok=False)
        self.record(self.request('scout', base_revision=base), ok=False)
        self.record(self.request(base_revision='not-a-commit'), ok=False)
        orphan = self.git('commit-tree', self.git('rev-parse', 'HEAD^{tree}'), '-m', 'unrelated root')
        self.record(self.request(base_revision=orphan), ok=False)
        result = self.record(request, self.packet(request, covered_paths=['src/a.py', 'src/survivor.py']))
        self.assertTrue(result['reusable'])
        # Dependencies remain mandatory final-tree inputs, even for a base review.
        self.record(self.request(base_revision=base, inputs=['missing.lock']), ok=False)

    def test_evidence_attempts_preserve_failures_and_require_explicit_finding_resolution(self):
        request = self.request()
        finding = dict(severity='high', message='must retain this defect', resolved=False, evidence='src/a.py:1')
        failed = self.record(request, self.packet(request, status='failed', findings=[finding]))
        original = (self.root / failed['receipt']).read_bytes()
        missing = self.record(request, self.packet(request))
        self.assertNotEqual(failed['receipt'], missing['receipt'])
        self.assertFalse(missing['reusable'])
        self.assertEqual(missing['status'], 'incomplete')
        latest = self.lookup(request)
        self.assertFalse(latest['reusable'])
        self.assertEqual(latest['unresolved_findings'], [finding])
        self.assertEqual((self.root / failed['receipt']).read_bytes(), original)
        # An intermediate empty failed result cannot discard the active defect.
        self.record(request, self.packet(request, status='failed'))
        self.record(request, self.packet(request))
        self.assertFalse(self.lookup(request)['reusable'])
        self.record(request, self.packet(request, findings=[dict(severity='high', message=finding['message'],
                                                               resolved=True)]), ok=False)
        disposition = dict(finding, resolved=True, evidence='review-followup.md: resolution independently confirmed')
        passed = self.record(request, self.packet(request, findings=[disposition]))
        self.assertTrue(passed['reusable'])
        self.assertTrue(self.lookup(request)['reusable'])
        self.assertEqual((self.root / failed['receipt']).read_bytes(), original)
        self.assertEqual(json.loads((self.root / failed['receipt']).read_text())['receipt']['result']['status'], 'failed')

    def test_latest_failed_attempt_never_falls_back_and_incomplete_history_is_readable(self):
        request = self.request()
        first = self.record(request, self.packet(request, status='incomplete', covered_paths=[]))
        content = (self.root / first['receipt']).read_bytes()
        completed = self.record(request)
        self.assertTrue(completed['reusable'])
        failed = self.record(request, self.packet(request, status='failed'))
        result = self.lookup(request)
        self.assertEqual(result['receipt'], failed['receipt'])
        self.assertEqual(result['status'], 'failed')
        self.assertFalse(result['reusable'])
        self.assertEqual(result['attempts'], [first['receipt'], completed['receipt'], failed['receipt']])
        self.assertEqual((self.root / first['receipt']).read_bytes(), content)
        self.assertEqual(json.loads((self.root / first['receipt']).read_text())['receipt']['result']['provenance'],
                         self.packet(request)['provenance'])

    def test_attempt_index_corruption_or_dropped_history_is_a_cache_miss(self):
        request = self.request()
        failed = self.record(request, self.packet(request, status='failed', findings=[
            dict(severity='high', message='retained failure', resolved=False)]))
        self.record(request, self.packet(request))
        index = self.root / failed['index']
        packet = json.loads(index.read_text())
        packet['receipt']['attempts'] = packet['receipt']['attempts'][1:]
        # Recomputing a checksum cannot hide the prior immutable attempt file.
        import hashlib
        packet['sha256'] = hashlib.sha256(json.dumps(packet['receipt'], sort_keys=True,
            separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
        index.write_text(json.dumps(packet))
        self.assertEqual(self.lookup(request)['status'], 'never_run')
        self.record(request, ok=False)
        index.write_text('{corrupt')
        self.assertFalse(self.lookup(request)['reusable'])
        self.record(request, ok=False)
        self.assertTrue((self.root / failed['receipt']).is_file())

    def test_reordered_checksum_valid_index_cannot_revive_older_pass(self):
        request = self.request()
        passed = self.record(request)
        failed = self.record(request, self.packet(request, status='failed'))
        old_bytes = (self.root / passed['receipt']).read_bytes()
        failed_bytes = (self.root / failed['receipt']).read_bytes()
        first = json.loads(old_bytes)['receipt']
        second = json.loads(failed_bytes)['receipt']
        self.assertEqual(first['sequence'], 1)
        self.assertIsNone(first['predecessor'])
        self.assertEqual(second['sequence'], 2)
        self.assertEqual(second['predecessor']['file'], Path(passed['receipt']).name)
        self.assertEqual(second['predecessor']['sha256'], json.loads(old_bytes)['sha256'])
        index = self.root / failed['index']
        envelope = json.loads(index.read_text())
        envelope['receipt']['attempts'].reverse()
        import hashlib
        envelope['sha256'] = hashlib.sha256(json.dumps(envelope['receipt'], sort_keys=True,
            separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()
        index.write_text(json.dumps(envelope))
        result = self.lookup(request)
        self.assertFalse(result['reusable'])
        self.assertEqual(result['status'], 'never_run')
        self.record(request, ok=False)
        self.assertEqual((self.root / passed['receipt']).read_bytes(), old_bytes)
        self.assertEqual((self.root / failed['receipt']).read_bytes(), failed_bytes)

    def test_review_base_inputs_include_deleted_dependency_directory_files(self):
        self.write('deps/retained.lock', 'retained v1')
        self.write('deps/removed.lock', 'old dependency v1')
        first_base = self.commit('base dependencies')
        # An unrelated base commit with identical declared content reuses evidence.
        self.git('commit', '--allow-empty', '-qm', 'unrelated base revision')
        equivalent_base = self.git('rev-parse', 'HEAD')
        (self.root / 'deps/removed.lock').unlink()
        newer_base = self.commit('removed old dependency')
        request = self.request(base_revision=first_base, inputs=['deps'])
        receipt = self.record(request)
        self.assertTrue(receipt['reusable'])
        packet = json.loads((self.root / receipt['receipt']).read_text())['receipt']
        self.assertIn('deps/removed.lock', packet['inputs']['base_input_manifest'])
        self.assertNotIn('deps/removed.lock', packet['inputs']['input_manifest'])
        self.assertTrue(self.lookup(self.request(base_revision=equivalent_base, inputs=['deps']))['reusable'])
        # Same final dependencies and source cannot hide different actual old inputs.
        changed = self.lookup(self.request(base_revision=newer_base, inputs=['deps']))
        self.assertFalse(changed['reusable'])
        self.assertEqual(changed['status'], 'never_run')
        self.record(self.request(base_revision=first_base, inputs=['missing']), ok=False)

    def copied_runtime(self, name, changed=None):
        import shutil
        runtime = Path(self.temp.name) / name
        shutil.copytree(RUNTIME.parent, runtime)
        if changed:
            dependency = runtime / changed
            dependency.write_bytes(dependency.read_bytes() + b'\n# changed validation dependency\n')
        return runtime

    def copied_query(self, runtime, verb, *args):
        process = subprocess.run([sys.executable, str(runtime / 'phase.py'), 'query', verb, *map(str, args)],
                                 cwd=self.root, capture_output=True, text=True, encoding='utf-8', timeout=30)
        self.assertNotIn('Traceback', process.stderr, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(process.returncode, 0, result)
        self.assertTrue(result['ok'], result)
        return result

    def test_validator_dependency_changes_invalidate_specialist_packets(self):
        self.record()
        request = self.external('lookup.json', self.request())
        baseline = self.copied_runtime('runtime-baseline')
        self.assertTrue(self.copied_query(baseline, 'evidence.lookup', request)['reusable'])
        dependencies = ('verification.py', 'verification_evidence.py', 'verification_checks.py', 'roadmap.py',
                        'text.py', 'phases.py', 'paths.py', 'config.py', 'results.py')
        for name in dependencies:
            with self.subTest(dependency=name):
                runtime = self.copied_runtime('packet-' + name, 'lib/' + name)
                result = self.copied_query(runtime, 'evidence.lookup', request)
                self.assertFalse(result['reusable'])
                self.assertEqual(result['status'], 'never_run')
        entry = self.copied_runtime('packet-entry', 'phase.py')
        self.assertFalse(self.copied_query(entry, 'evidence.lookup', request)['reusable'])

    def test_validator_dependency_changes_invalidate_bookkeeping_receipts(self):
        self.report()
        before, after = self.bookkeeping()
        self.query('verification.validate-bookkeeping', '--before', before, '--after', after)
        baseline = self.copied_runtime('currentness-baseline')
        self.assertTrue(self.copied_query(baseline, 'verification.currentness', '1')['current'])
        dependencies = ('verification.py', 'verification_evidence.py', 'verification_checks.py', 'roadmap.py',
                        'text.py', 'phases.py', 'paths.py', 'config.py', 'results.py')
        for name in dependencies:
            with self.subTest(dependency=name):
                runtime = self.copied_runtime('bookkeeping-' + name, 'lib/' + name)
                result = self.copied_query(runtime, 'verification.currentness', '1')
                self.assertFalse(result['current'])
                self.assertIn('bookkeeping provenance mismatch', result['reason'])
        entry = self.copied_runtime('bookkeeping-entry', 'phase.py')
        self.assertFalse(self.copied_query(entry, 'verification.currentness', '1')['current'])

    def test_acceptance_record_is_exact_revision_and_checks_report(self):
        self.report()
        request = self.request('acceptance', report_path='.planning/phases/01-evidence/01-VERIFICATION.md')
        self.record(request)
        self.assertTrue(self.lookup(request)['reusable'])
        self.git('commit', '--allow-empty', '-qm', 'new revision')
        self.assertFalse(self.lookup(self.request('acceptance', report_path=request['report_path']))['reusable'])


if __name__ == '__main__':
    unittest.main()
