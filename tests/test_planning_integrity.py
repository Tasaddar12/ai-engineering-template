"""Behavioral planning integrity regressions against isolated real repositories."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / '.ai/runtime/phase.py'
HOOK = ROOT / '.ai/hooks/planning-integrity.py'
RECORD = '.planning/phases/01-foundation/01-01-PLAN.md'
VALID = '''---
phase: 01-foundation
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true
requirements: [REQ-01]
acceptance: []
documentation: []
checks: []
must_haves: {truths: [], artifacts: [], key_links: []}
issue_refs: []
---
# A real fixture plan
'''
INVALID = VALID.replace('issue_refs: []\n', '')


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        self.write('seed', 'seed\n')
        self.git('add', 'seed')
        self.git('commit', '-qm', 'seed')
        self.head = self.git('rev-parse', 'HEAD')

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding='utf-8')

    def runtime(self, *args):
        result = subprocess.run([sys.executable, str(RUNTIME), 'query', *args],
                                cwd=self.root, text=True, capture_output=True)
        return result, json.loads(result.stdout)

    def hook(self, command, cwd=None, tool='exec_command', field='cmd'):
        return subprocess.run([sys.executable, str(HOOK)], cwd=self.root,
                              input=json.dumps({'tool_name': tool, 'cwd': str(cwd or self.root),
                                                'tool_input': {field: command}}),
                              text=True, capture_output=True)

    def assert_denied(self, result):
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('issue_refs', result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_shell_alias_argv_native_payload_and_actual_commit(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        denied = self.hook(['git', 'commit', '-m', 'fixture'], tool='shell', field='command')
        self.assert_denied(denied)
        if denied.returncode == 0:
            self.git('commit', '-m', 'fixture')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        allowed = self.hook(['git', 'commit', '-m', 'fixture'], tool='shell', field='command')
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.git('commit', '-m', 'fixture')
        self.assertNotEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_supported_native_tool_names_and_only_source_exception(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        for tool in ('Bash', 'exec_command', 'shell_command', 'shell'):
            with self.subTest(tool=tool):
                self.assert_denied(self.hook('git commit -m fixture', tool=tool, field='command'))
        self.write('seed', 'changed source\n')
        self.assertEqual(self.hook('git commit --only -m source -- seed').returncode, 0)

    def test_worktree_clean_filter_refused_without_index_mutation(self):
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        self.write('.gitattributes', '*.md filter=fixture\n')
        self.write(RECORD, INVALID)
        before = self.git('ls-files', '--stage')
        result = self.hook('git commit --only -m fixture -- ' + RECORD)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('clean filter', result.stderr)
        self.assertEqual(before, self.git('ls-files', '--stage'))

    def test_empty_add_cannot_hide_invalid_index_and_nested_all_is_repository_wide(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        self.write(RECORD, VALID)
        self.assert_denied(self.hook('git add && git commit -m fixture'))
        self.git('add', RECORD)
        self.write(RECORD, INVALID)
        nested = self.root / 'nested'
        nested.mkdir()
        self.assert_denied(self.hook('git add -A && git commit -m fixture', nested))

    def test_real_multi_record_loss_returns_json_evidence_on_success_and_error(self):
        from test_phase_runtime import STATE, ROADMAP
        for missing_state in (False, True):
            with self.subTest(missing_state=missing_state):
                self.write('.planning/ROADMAP.md', ROADMAP + '| authored table sentinel | retain this |\n')
                if missing_state:
                    (self.root / '.planning/STATE.md').unlink()
                else:
                    self.write('.planning/STATE.md', STATE)
                result, data = self.runtime('roadmap.update-plan-progress', '01-01', '--raw')
                self.assertEqual(result.returncode, 1 if missing_state else 0, data)
                warnings = data['integrity_warnings']
                evidence = next(item for item in warnings if 'authored table sentinel' in item['content'])
                self.assertEqual(evidence['verb'], 'roadmap.update-plan-progress')
                self.assertEqual(evidence['section'], '## Progress')
                self.assertNotIn('authored table sentinel', (self.root / '.planning/ROADMAP.md').read_text())
                if missing_state:
                    self.assertEqual(data['code'], 'missing-state')
                    self.assertFalse((self.root / '.planning/STATE.md').exists())

    def test_normal_milestone_demotion_preserves_authored_notes_without_warning(self):
        from test_phase_runtime import ROADMAP
        self.write('.planning/ROADMAP.md', ROADMAP + '\n## Authored notes\nMilestone sentinel.\n')
        for name in ('v1 Foundation', 'v2 Expansion'):
            result, data = self.runtime('milestone.create', name)
            self.assertEqual(result.returncode, 0, data)
            self.assertNotIn('integrity_warnings', data)
            self.assertIn('Milestone sentinel.', (self.root / '.planning/ROADMAP.md').read_text())

    def test_bash_escaped_commit_spellings_and_transparent_wrapper_families(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        commands = [r'g\it commit -m fixture', 'gi\\\nt commit -m fixture',
                    'command env git commit -m fixture', 'env env git commit -m fixture',
                    'exec env git commit -m fixture', 'time git commit -m fixture',
                    '! git commit -m fixture']
        for command in commands:
            with self.subTest(command=command):
                self.assert_denied(self.hook(command, tool='Bash', field='command'))
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        for command in commands:
            with self.subTest(valid=command):
                result = self.hook(command, tool='Bash', field='command')
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_escaped_add_chain_and_harmless_commit_diagnostics(self):
        self.write(RECORD, INVALID)
        for command in [r'g\it add ' + RECORD + ' && git commit -m fixture',
                        'gi\\\nt add ' + RECORD + ' && git commit -m fixture']:
            with self.subTest(command=command):
                self.assert_denied(self.hook(command, tool='Bash', field='command'))
        for command in ['echo git commit', 'printf "%s" "git commit"', 'command -v git', 'git status']:
            with self.subTest(diagnostic=command):
                self.assertEqual(self.hook(command, tool='Bash', field='command').returncode, 0)

    def test_native_windows_paths_and_bash_specific_escape_meaning(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        self.assert_denied(self.hook('git -C ' + str(self.root) + ' commit -m fixture', tool='exec_command'))
        result = self.hook(r'g\it commit -m fixture', tool='exec_command')
        if os.name == 'nt':
            # Native PowerShell preserves backslash as a path separator.
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            # The native POSIX shell removes this executable-name escape.
            self.assert_denied(result)

    def test_review_cr01_attached_all_clusters_select_working_bytes(self):
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        self.git('commit', '-qm', 'tracked valid record')
        self.head = self.git('rev-parse', 'HEAD')
        self.write(RECORD, INVALID)
        self.write('unrelated', 'preserve staged bytes\n')
        self.git('add', 'unrelated')
        before = self.git('ls-files', '--stage')
        for command in ['git commit -am"fix issue 87"', 'git commit -amfix87',
                        'git commit -qam"fix 87"', 'git commit -a -m "fix 87"']:
            with self.subTest(command=command):
                self.assert_denied(self.hook(command))
                self.assertEqual(before, self.git('ls-files', '--stage'))
        for command in ['git commit -mdata', 'git commit -mfix87']:
            with self.subTest(index_control=command):
                self.assertEqual(self.hook(command).returncode, 0)

    def test_bash_commit_comments_and_literal_hash_arguments(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        before = self.git('ls-files', '--stage')
        commands = [
            'git commit -m fixture # explanatory comment',
            'git commit -m "fixture # quoted literal"',
            r'git commit -m fixture\#escaped',
            'git commit -m fixture#midtoken',
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assert_denied(self.hook(command, tool='Bash', field='command'))
                self.assertEqual(before, self.git('ls-files', '--stage'))
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        for command in commands:
            with self.subTest(valid=command):
                result = self.hook(command, tool='Bash', field='command')
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_add_then_only_checks_new_selected_record_and_preserves_index(self):
        self.write('unrelated', 'preserve this staged blob\n')
        self.git('add', 'unrelated')
        before = self.git('ls-files', '--stage')
        command = ('git add ' + RECORD +
                   ' && git commit --only -m fixture -- ":(glob)**/*-PLAN.md"')

        self.write(RECORD, INVALID)
        denied = self.hook(command)
        self.assert_denied(denied)
        self.assertEqual(before, self.git('ls-files', '--stage'))

        self.write(RECORD, VALID)
        allowed = self.hook(command)
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        self.assertEqual(before, self.git('ls-files', '--stage'))

    def test_review_cr01_controlled_native_cluster_cannot_commit_invalid_working_bytes(self):
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        self.git('commit', '-qm', 'tracked valid record')
        self.head = self.git('rev-parse', 'HEAD')
        self.write(RECORD, INVALID)
        observed = self.hook('git commit -amfix87')
        if observed.returncode == 0:
            self.git('commit', '-amfix87')
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head,
                         'native -amfix87 must not reach Git with invalid prospective bytes')
        self.assertEqual(observed.returncode, 2, observed.stderr)

    def test_review_cr02_wrapped_commits_survive_outer_segmentation(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        self.write('unrelated', 'preserve stage\n')
        self.git('add', 'unrelated')
        before = self.git('ls-files', '--stage')
        wrappers = ['bash -lc "git commit -m fixture"', 'sh -c "git commit -m fixture"',
                    'powershell -Command "git commit -m fixture"', 'cmd /c "git commit -m fixture"']
        commands = [form for wrapper in wrappers for form in
                    [wrapper, wrapper + '; echo done', wrapper + ' && echo done', 'echo start; ' + wrapper]]
        for command in commands:
            with self.subTest(invalid=command):
                self.assert_denied(self.hook(command))
                self.assertEqual(before, self.git('ls-files', '--stage'))
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        for command in commands:
            with self.subTest(valid=command):
                result = self.hook(command)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.hook('echo "git commit -m fixture"').returncode, 0)

    def test_review_cr03_duplicate_yaml_keys_are_denied_in_actual_staged_records(self):
        duplicates = [
            ('issue_refs', VALID.replace('issue_refs: []', 'issue_refs: [https://example.invalid/issues/1]\nissue_refs: []')),
            ('issue_refs', VALID.replace('issue_refs: []', 'issue_refs: [{id: review, summary: Retain declared followup, variant: UAT, state: pending-human, relationship: followup}]\nissue_refs: []')),
            ('wave', VALID.replace('wave: 1', 'wave: -2\nwave: 1')),
            ('truths', VALID.replace('must_haves: {truths: [], artifacts: [], key_links: []}', 'must_haves: {truths: [retained], truths: [], artifacts: [], key_links: []}')),
            ('path', VALID.replace('artifacts: []', 'artifacts: [{path: first, path: second}]')),
        ]
        for key, content in duplicates:
            with self.subTest(key=key, content=content):
                self.write(RECORD, content)
                self.git('add', RECORD)
                before = self.git('ls-files', '--stage')
                result = self.hook('git commit -m fixture')
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(key, result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(before, self.git('ls-files', '--stage'))
                self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
        self.write(RECORD, duplicates[0][1])
        result, data = self.runtime('commit', 'duplicate fixture', '--files', RECORD)
        self.assertEqual(result.returncode, 1, data)
        self.assertEqual(data['code'], 'planning-integrity')
        self.assertIn('issue_refs', data['error'])
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_review_cr04_cross_kind_collection_types_deny_without_traceback(self):
        for value in ['7', 'null', '{}', 'true', 'REQ-OLD']:
            with self.subTest(value=value):
                self.write(RECORD, VALID.replace('issue_refs: []', 'requirements-completed: ' + value + '\nissue_refs: []'))
                self.git('add', RECORD)
                before = self.git('ls-files', '--stage')
                result = self.hook('git commit -m fixture')
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn('requirements-completed', result.stderr)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(before, self.git('ls-files', '--stage'))
        self.write(RECORD, VALID.replace('issue_refs: []', 'requirements-completed: [REQ-OLD]\nissue_refs: []'))
        self.git('add', RECORD)
        result = self.hook('git commit -m fixture')
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_review_cr04_unexpected_inspection_error_uses_native_denial_exit(self):
        bootstrap = ('import importlib.util,sys; '
                     's=importlib.util.spec_from_file_location("review_hook",sys.argv[1]); '
                     'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); '
                     'm.inspect=lambda *args: (_ for _ in ()).throw(RuntimeError("injected inspection failure")); '
                     'sys.exit(m.main())')
        result = subprocess.run([sys.executable, '-c', bootstrap, str(HOOK)], cwd=self.root,
                                input=json.dumps({'tool_name': 'exec_command', 'tool_input': {'cmd': 'git commit -m fixture'}}),
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('inspection', result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_review_cr02_shell_diagnostics_and_unsupported_inline_shapes(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        for command in ['bash --version', 'sh --help', 'cmd /?', 'powershell -Help']:
            with self.subTest(diagnostic=command):
                self.assertEqual(self.hook(command).returncode, 0)
        for command in ['bash -lc', 'powershell -Command "git commit -m fixture" extra',
                        'cmd /c "git commit -m fixture" extra']:
            with self.subTest(unsupported=command):
                result = self.hook(command)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_review_cr03_working_duplicate_and_lenient_historical_reader_control(self):
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        self.git('commit', '-qm', 'valid tracked fixture')
        self.head = self.git('rev-parse', 'HEAD')
        duplicate = VALID.replace('wave: 1', 'wave: -2\nwave: 1')
        self.write(RECORD, duplicate)
        self.assertEqual(self.hook('git commit -m fixture').returncode, 0)
        denied = self.hook('git commit --only -m fixture -- ' + RECORD)
        self.assertEqual(denied.returncode, 2, denied.stderr)
        self.assertIn('wave', denied.stderr)
        sys.path.insert(0, str(ROOT / '.ai/runtime'))
        from lib.text import split_frontmatter
        self.assertEqual(split_frontmatter(duplicate)[0]['wave'], 1,
                         'the broad historical/warn-only reader must remain unchanged')

    def test_review_cr04_runtime_malformed_collection_returns_structured_error(self):
        self.write(RECORD, VALID.replace('issue_refs: []', 'requirements-completed: 7\nissue_refs: []'))
        result, data = self.runtime('commit', 'typed fixture', '--files', RECORD)
        self.assertEqual(result.returncode, 1, data)
        self.assertEqual(data['code'], 'planning-integrity')
        self.assertIn('requirements-completed', data['error'])
        self.assertNotIn('Traceback', result.stderr)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def review_cr05_gate_control(self, content, allowed):
        self.write(RECORD, content)
        self.write('unrelated', 'merge-control staged bytes\n')
        self.git('add', RECORD, 'unrelated')
        before = self.git('ls-files', '--stage')
        native = self.hook('git commit -m merge-control')
        with self.subTest(gate='native'):
            self.assertEqual(native.returncode, 0 if allowed else 2, native.stderr)
            self.assertNotIn('Traceback', native.stderr)
        self.assertEqual(before, self.git('ls-files', '--stage'))
        result, data = self.runtime('commit', 'merge control', '--files', RECORD)
        with self.subTest(gate='runtime'):
            self.assertEqual(result.returncode, 0 if allowed else 1, data)
            if allowed:
                self.assertTrue(data['committed'])
                self.assertEqual(self.git('show', 'HEAD:unrelated'), 'merge-control staged bytes')
            else:
                self.assertEqual(data['code'], 'planning-integrity')
                self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)
                self.assertEqual(before, self.git('ls-files', '--stage'))

    def review_cr05_merge_record(self):
        return VALID.replace('must_haves: {truths: [], artifacts: [], key_links: []}',
                             'defaults: &defaults {truths: [], artifacts: [], key_links: []}\n'
                             'must_haves: {<<: *defaults, truths: [A verified outcome]}')

    def test_review_cr05_valid_merge_explicit_override_is_allowed(self):
        self.review_cr05_gate_control(self.review_cr05_merge_record(), True)

    def test_review_cr05_equivalent_explicit_mapping_is_allowed(self):
        content = VALID.replace('truths: []', 'truths: [A verified outcome]')
        self.review_cr05_gate_control(content, True)

    def test_review_cr05_duplicate_explicit_destination_keys_are_denied(self):
        content = self.review_cr05_merge_record().replace('truths: [A verified outcome]}',
                                                         'truths: [first], truths: [second]}')
        self.review_cr05_gate_control(content, False)

    def test_review_cr05_duplicate_keys_in_anchored_source_are_denied(self):
        content = self.review_cr05_merge_record().replace('defaults: &defaults {truths: [],',
                                                         'defaults: &defaults {truths: [], truths: [erased],')
        self.review_cr05_gate_control(content, False)

    def test_review_cr05_prior_top_and_nested_duplicates_stay_denied(self):
        for content in [VALID.replace('wave: 1', 'wave: -2\nwave: 1'),
                        VALID.replace('artifacts: []', 'artifacts: [{path: first, path: second}]')]:
            with self.subTest(content=content):
                self.review_cr05_gate_control(content, False)

    def test_review_cr05_historical_reader_preserves_merge_and_lenient_controls(self):
        sys.path.insert(0, str(ROOT / '.ai/runtime'))
        from lib.text import split_frontmatter
        merged, _ = split_frontmatter(self.review_cr05_merge_record())
        explicit, _ = split_frontmatter(VALID.replace('truths: []', 'truths: [A verified outcome]'))
        self.assertEqual(merged['must_haves'], explicit['must_haves'])
        self.assertEqual(split_frontmatter(VALID.replace('wave: 1', 'wave: -2\nwave: 1'))[0]['wave'], 1)

    def test_runtime_rejects_missing_issue_refs_before_commit(self):
        self.write(RECORD, INVALID)
        result, data = self.runtime('commit', 'fixture', '--files', RECORD)
        self.assertEqual(result.returncode, 1, data)
        self.assertEqual(data['code'], 'planning-integrity')
        self.assertIn('issue_refs', data['error'])
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_runtime_inspects_staged_bytes_omitted_from_files(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        self.write(RECORD, VALID)
        self.write('source.txt', 'source\n')
        result, data = self.runtime('commit', 'fixture', '--files', 'source.txt')
        self.assertEqual(result.returncode, 1, data)
        self.assertEqual(self.git('show', ':' + RECORD), INVALID.strip())
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.head)

    def test_runtime_accepts_valid_and_ignores_maintenance(self):
        self.write(RECORD, VALID)
        self.write('docs/maintenance/CONTEXT.md', '# maintenance\n')
        result, data = self.runtime('commit', 'fixture', '--files', RECORD, 'docs/maintenance/CONTEXT.md')
        self.assertEqual(result.returncode, 0, data)
        self.assertTrue(data['committed'])

    def test_hook_index_bytes_and_unrelated_staging_are_preserved(self):
        self.write(RECORD, INVALID)
        self.write('unrelated', 'keep staged\n')
        self.git('add', RECORD, 'unrelated')
        self.write(RECORD, VALID)
        before = self.git('ls-files', '--stage')
        self.assert_denied(self.hook('git commit -m fixture'))
        self.assertEqual(self.git('ls-files', '--stage'), before)

    def test_hook_only_uses_worktree_bytes_in_both_directions(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        self.write(RECORD, VALID)
        self.assertEqual(self.hook('git commit --only -m fixture -- ' + RECORD).returncode, 0)
        self.git('add', RECORD)
        self.write(RECORD, INVALID)
        self.assert_denied(self.hook('git commit --only -m fixture -- ' + RECORD))

    def test_hook_all_checks_tracked_worktree_bytes(self):
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        self.git('commit', '-qm', 'valid')
        self.head = self.git('rev-parse', 'HEAD')
        self.write(RECORD, INVALID)
        self.assert_denied(self.hook('git commit --all -m fixture'))

    def test_hook_add_chain_and_shell_wrappers(self):
        self.write(RECORD, INVALID)
        for command in ['git add ' + RECORD + ' && git commit -m fixture',
                        'bash -lc "git add ' + RECORD + ' && git commit -m fixture"',
                        'powershell -Command "git add ' + RECORD + '; git commit -m fixture"']:
            with self.subTest(command=command):
                self.assert_denied(self.hook(command))

    def test_hook_global_cwd_options_and_nested_directory(self):
        self.write(RECORD, INVALID)
        self.git('add', RECORD)
        nested = self.root / 'nested unicode \u00e9'
        nested.mkdir()
        self.assert_denied(self.hook('git -c core.quotepath=false -C "' + str(self.root) + '" commit -m fixture', nested))
        self.assertEqual(self.hook('git status --short', nested).returncode, 0)

    def test_explicit_selected_diagnostic_and_field_types(self):
        self.write(RECORD, VALID.replace('wave: 1', 'wave: true'))
        result, data = self.runtime('planning.integrity', '--files', RECORD)
        self.assertEqual(result.returncode, 1, data)
        self.assertIn('wave', data['error'])

    def test_state_prevents_nested_authored_heading_loss(self):
        self.write('.planning/STATE.md', '''# State
## Project Reference
Authored reference sentinel.
## Current Position
Phase: 1 of 1 (Foundation)
Plan: 1 of 1
Status: Planning
Last activity: yesterday
## Accumulated Context
### Blockers/Concerns
- old blocker
#### Unexpected authored detail
DO NOT LOSE THIS SENTINEL
### Pending Todos
None yet.
''')
        original = (self.root / '.planning/STATE.md').read_text()
        result, data = self.runtime('state.clear-blocker', 'old blocker')
        saved = (self.root / '.planning/STATE.md').read_text()
        self.assertTrue('DO NOT LOSE THIS SENTINEL' in saved or result.returncode == 1, data)
        if result.returncode:
            self.assertEqual(data['code'], 'planning-integrity')
            self.assertEqual(saved, original)

    def test_real_state_and_roadmap_mutations_preserve_authored_sentinels(self):
        from test_phase_runtime import STATE, ROADMAP
        state = STATE.replace('## Current Position', '## Project Reference\n\nReference sentinel.\n\n## Current Position')
        state += '\n## Unusual authored notes\nState sentinel.\n'
        roadmap = ROADMAP.replace('## Phases', '## Authored overview\nRoadmap sentinel.\n\n## Phases')
        roadmap = roadmap.replace('**Plans**: 1 plan', 'Phase two authored sentinel.\n**Plans**: 1 plan')
        self.write('.planning/STATE.md', state)
        self.write('.planning/ROADMAP.md', roadmap)
        self.write('.planning/PROJECT.md', '# Project\n## Key Decisions\n| Decision | Rationale | Outcome |\n|---|---|---|\n')
        for command in [('state.record-session', '--stopped-at', 'fixture'),
                        ('state.update-progress',),
                        ('state.add-blocker', 'fixture blocker'),
                        ('state.clear-blocker', 'fixture'),
                        ('state.add-decision', 'fixture decision'),
                        ('phase.edit', '1', '--name', 'Renamed foundation', '--goal', 'New goal'),
                        ('roadmap.set-plans', '1', '--plans', '01-01: Scaffold', '01-02: Wire it up'),
                        ('phase.add', 'Third phase'),
                        ('phase.remove', '3', '--no-renumber'),
                        ('phase.remove', '1')]:
            with self.subTest(command=command):
                result, data = self.runtime(*command)
                self.assertEqual(result.returncode, 0, data)
                self.assertNotIn('integrity_warnings', data, data)
                saved_state = (self.root / '.planning/STATE.md').read_text()
                saved_roadmap = (self.root / '.planning/ROADMAP.md').read_text()
                for sentinel in ['Reference sentinel.', 'State sentinel.']:
                    self.assertIn(sentinel, saved_state)
                for sentinel in ['Roadmap sentinel.', 'Phase two authored sentinel.']:
                    self.assertIn(sentinel, saved_roadmap)

    def test_native_exceptions_unchanged_legacy_deletion_and_valid_index(self):
        self.write(RECORD, '# legacy without metadata\n')
        self.git('add', RECORD)
        self.git('commit', '-qm', 'legacy')
        self.head = self.git('rev-parse', 'HEAD')
        self.assertEqual(self.hook('git commit --only -m fixture -- ' + RECORD).returncode, 0)
        (self.root / RECORD).unlink()
        self.git('add', RECORD)
        self.assertEqual(self.hook('git commit -m deletion').returncode, 0)
        self.write(RECORD, VALID)
        self.git('add', RECORD)
        self.write(RECORD, INVALID)
        self.assertEqual(self.hook('git commit -m fixture').returncode, 0)
        self.assertEqual(self.hook('git commit -mdata').returncode, 0)

    def test_warn_only_validator_and_read_only_diagnostic(self):
        self.write('.planning/STATE.md', '# State fixture\n')
        result, data = self.runtime('planning.validate')
        self.assertEqual(result.returncode, 0, data)
        self.assertTrue(data.get('warnings'))
        before = self.git('status', '--porcelain')
        self.write(RECORD, VALID)
        before = self.git('status', '--porcelain')
        result, data = self.runtime('planning.integrity', '--files', RECORD)
        self.assertEqual(result.returncode, 0, data)
        self.assertEqual(before, self.git('status', '--porcelain'))


class AuthoredIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / '.ai/runtime'))
        from lib import planning_integrity, state
        from lib.paths import Workspace
        cls.integrity, cls.state, cls.Workspace = planning_integrity, state, Workspace

    def test_section_aware_loss_cannot_hide_in_another_section(self):
        before = '# State\n## Authored One\nshared sentinel\n## Authored Two\nother sentinel\n'
        after = '# State\n## Authored One\n## Authored Two\nother sentinel\nshared sentinel\n'
        losses = self.integrity.content_loss(before, after, '.planning/STATE.md', 'fixture')
        self.assertTrue(losses, 'authored content moving out of its section must be diagnosed')
        self.assertEqual(losses[0]['section'], '## Authored One')

    def test_state_save_prevents_direct_unexpected_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.Workspace(directory)
            workspace.planning.mkdir()
            original = '# State\n## Project Reference\nreference sentinel\n## Custom\ncustom sentinel\n'
            workspace.state.write_text(original, encoding='utf-8')
            parsed = self.state.State(workspace)
            parsed.body = '# State\n## Custom\ncustom sentinel\n'
            from lib.results import VerbError
            with self.assertRaisesRegex(VerbError, 'truncation'):
                parsed.save()
            self.assertEqual(workspace.state.read_text(), original)

    def test_state_nested_heading_prevents_whole_section_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.Workspace(directory)
            workspace.planning.mkdir()
            original = '# State\n### Pending Todos\n- old\n#### Authored detail\nprotected sentinel\n'
            workspace.state.write_text(original, encoding='utf-8')
            from lib.results import VerbError
            with self.assertRaisesRegex(VerbError, 'Authored detail'):
                self.state.set_pending_todos(workspace, '- new')
            self.assertEqual(workspace.state.read_text(), original)

    def test_dispatch_reports_loss_after_multi_record_write(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('integrity_phase', RUNTIME)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.Workspace(directory)
            workspace.planning.mkdir()
            workspace.roadmap.write_text('# Roadmap\n## Notes\nprotected sentinel\n', encoding='utf-8')
            def mutate(w, p, o):
                w.roadmap.write_text('# Roadmap\n## Notes\n', encoding='utf-8')
                return {'changed': True}
            module.VERBS['milestone.fixture'] = mutate
            result = module.run_verb(workspace, 'milestone.fixture', [], {})
            self.assertTrue(result['changed'])
            warning = result['integrity_warnings'][0]
            self.assertEqual(warning['record'], '.planning/ROADMAP.md')
            self.assertEqual(warning['verb'], 'milestone.fixture')
            self.assertEqual(warning['content'], 'protected sentinel')
            self.assertIn('no rollback', warning['message'])

    def test_normal_line_endings_and_digest_rotation(self):
        before = '# State\r\n### Decisions\r\n- old\r\n## Notes\r\nauthored\r\n'
        after = '# State\n### Decisions\n- new\n## Notes\nauthored\n'
        self.assertEqual([], self.integrity.content_loss(before, after, '.planning/STATE.md',
                                                       allowed_sections=('Decisions',)))


class SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / '.ai/runtime'))
        from lib import planning_integrity
        cls.integrity = planning_integrity

    def test_complete_source_file_templates_match_validator(self):
        import re
        for source, path in [('context.md', RECORD.replace('01-01-PLAN', '01-CONTEXT')),
                             ('phase-prompt.md', RECORD),
                             ('summary.md', RECORD.replace('PLAN', 'SUMMARY'))]:
            with self.subTest(template=source):
                text = (ROOT / '.ai/templates' / source).read_text(encoding='utf-8')
                body = re.search(r'```markdown\n(.*?)\n```', text, re.S)[1]
                body = body.replace('phase: XX-name', 'phase: 01-foundation')
                body = body.replace('wave: N ', 'wave: 1 ')
                body = body.replace('requirements: []', 'requirements: [REQ-01]')
                self.assertTrue(self.integrity.validate_record(path, body)['valid'])
                self.assertIn('issue_refs: []', body)

    def test_upstream_halted_summary_and_native_tdd_plan_stay_valid(self):
        from lib.text import split_frontmatter, join_frontmatter
        data, body = split_frontmatter(VALID)
        data['type'] = 'tdd'
        self.integrity.validate_record(RECORD, join_frontmatter(data, body))
        summary = {'phase': '01-foundation', 'plan': '01', 'status': 'halted',
                   'requirements-completed': [], 'acceptance': [], 'documentation': [], 'issue_refs': []}
        self.integrity.validate_record(RECORD.replace('PLAN', 'SUMMARY'), join_frontmatter(summary, body))

    def test_required_keys_and_types_for_each_record(self):
        from lib.results import VerbError
        from lib.text import split_frontmatter, join_frontmatter
        metadata, body = split_frontmatter(VALID)
        fixtures = [(RECORD, metadata),
                    (RECORD.replace('01-01-PLAN', '01-CONTEXT'),
                     {'phase': '01-foundation', 'discussion': 'complete', 'issue_refs': []}),
                    (RECORD.replace('PLAN', 'SUMMARY'),
                     {'phase': '01-foundation', 'plan': '01', 'status': 'complete',
                      'requirements-completed': [], 'acceptance': [], 'documentation': [], 'issue_refs': []})]
        for path, data in fixtures:
            self.integrity.validate_record(path, join_frontmatter(data, body))
            for key in self.integrity.REQUIRED[self.integrity.record_kind(path)]:
                missing = dict(data)
                del missing[key]
                with self.subTest(path=path, key=key):
                    with self.assertRaisesRegex(VerbError, key):
                        self.integrity.validate_record(path, join_frontmatter(missing, body))
                    wrong = dict(data, **{key: None})
                    with self.assertRaisesRegex(VerbError, key):
                        self.integrity.validate_record(path, join_frontmatter(wrong, body))

    def test_issue_declaration_mapping_semantics_are_reused(self):
        from lib.results import VerbError
        from lib.text import split_frontmatter, join_frontmatter
        data, body = split_frontmatter(VALID)
        declaration = {'id': 'fixture-1', 'summary': 'Human review', 'variant': 'UAT',
                       'state': 'pending-human', 'relationship': 'followup'}
        data['issue_refs'] = [declaration]
        self.integrity.validate_record(RECORD, join_frontmatter(data, body))
        declaration['relationship'] = 'resolving'
        with self.assertRaisesRegex(VerbError, 'issue_refs'):
            self.integrity.validate_record(RECORD, join_frontmatter(data, body))

    def test_malformed_yaml_and_noncanonical_paths(self):
        from lib.results import VerbError
        for content in ['# no frontmatter', '---\nphase: [bad\n---\n', '---\n- wrong\n---\n']:
            with self.assertRaisesRegex(VerbError, 'frontmatter'):
                self.integrity.validate_record(RECORD, content)
        for path in ['docs/maintenance/issue87/PLAN.md', '.ai/templates/summary.md',
                     '.planning/archive/phases/01-foundation/01-01-PLAN.md']:
            self.assertIsNone(self.integrity.validate_record(path, '# no schema'))


if __name__ == '__main__':
    unittest.main()
