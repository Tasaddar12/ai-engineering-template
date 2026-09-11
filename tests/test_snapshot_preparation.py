import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml
import test_orchestrate as fixture

SPEC = importlib.util.spec_from_file_location('prepare', fixture.RUNTIME.with_name('prepare.py'))
prepare = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, orchestrate=fixture.orch):
    SPEC.loader.exec_module(prepare)


class SnapshotPreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fixture.orch.git(self.root, 'init', '-b', 'main')
        fixture.orch.git(self.root, 'config', 'user.name', 'Preparation Test')
        fixture.orch.git(self.root, 'config', 'user.email', 'test@example.invalid')
        self.config = yaml.safe_load(fixture.RUNTIME.parents[1].joinpath('config.yaml').read_text())
        self.config['verification']['commands'] = [[sys.executable, '-c', 'print("checked")']]
        self.config['orchestration'].update(base_branch='main', required_status_checks=['validate'])
        example = json.loads(fixture.RUNTIME.with_name('schedule.example.json').read_text())
        self.schedule = {key: example[key] for key in ('run_id', 'remote', 'github_repo', 'worker_command', 'tracks')}
        self.manifest = '.ai/state/orchestration/ORCH-001.md'
        self.commit()

    def commit(self):
        config = self.root / '.ai/config.yaml'
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(yaml.safe_dump(self.config), encoding='utf-8')
        manifest = self.root / self.manifest
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text('# Approved schedule\n\n## Execution schedule\n\nScheduling guidance.\n\n```json\n' +
                            json.dumps(self.schedule) + '\n```\n', encoding='utf-8')
        fixture.orch.git(self.root, 'add', '.')
        fixture.orch.git(self.root, 'commit', '-m', 'Prepare the schedule')

    def test_snapshot_uses_immutable_sources_and_configured_commands(self):
        revision = fixture.orch.git(self.root, 'rev-parse', 'HEAD')
        (self.root / '.ai/config.yaml').write_text('invalid uncommitted YAML', encoding='utf-8')
        before = fixture.orch.git(self.root, 'status', '--porcelain')
        snapshot = prepare.compile_snapshot(self.root, self.manifest)
        self.assertEqual(snapshot['required_commands'], self.config['verification']['commands'])
        self.assertEqual(snapshot['documentation_worker_command'], self.config['orchestration']['documentation']['worker_command'])
        self.assertEqual(snapshot['sources']['revision'], revision)
        self.assertEqual(snapshot['sources']['manifest']['blob'], fixture.orch.git(self.root, 'rev-parse', f'{revision}:{self.manifest}'))
        self.assertEqual(snapshot, prepare.compile_snapshot(self.root, self.manifest, revision))
        self.assertEqual(fixture.orch.git(self.root, 'status', '--porcelain'), before)

    def test_duplicate_configuration_in_manifest_is_rejected(self):
        self.schedule['max_parallel_tracks'] = 20
        self.commit()
        with self.assertRaisesRegex(fixture.orch.Blocked, 'duplicates configuration'):
            prepare.compile_snapshot(self.root, self.manifest)

    def test_shell_command_strings_are_rejected_without_interpretation(self):
        self.config['verification']['commands'] = ['python -m unittest']
        self.commit()
        with self.assertRaisesRegex(fixture.orch.Blocked, 'argv arrays'):
            prepare.compile_snapshot(self.root, self.manifest)

    def test_custom_record_paths_and_review_counts_are_not_silently_dropped(self):
        original = copy.deepcopy(self.config)
        for key, value in (('paths', {'plans': 'custom/plans'}), ('review', {'max_rounds': 3})):
            self.config = copy.deepcopy(original)
            if key == 'review':
                self.config['orchestration'][key] = value
            else:
                self.config[key].update(value)
            self.commit()
            with self.subTest(setting=key), self.assertRaises(fixture.orch.Blocked):
                prepare.compile_snapshot(self.root, self.manifest)

    def test_custom_intent_state_and_journal_paths_are_rejected(self):
        original = copy.deepcopy(self.config)
        for key in ('project', 'state', 'journal'):
            self.config = copy.deepcopy(original)
            self.config['paths'][key] = 'custom/' + key
            self.commit()
            with self.subTest(path=key), self.assertRaisesRegex(fixture.orch.Blocked, 'fixed record paths'):
                prepare.compile_snapshot(self.root, self.manifest)

    def test_custom_numeric_id_formats_and_lifecycle_stages_are_rejected(self):
        original = copy.deepcopy(self.config)
        settings = [('ids', 'research', 'RESEARCH-{nnn}-{slug}'),
                    ('ids', 'orchestration', 'RUN-{nnn}'),
                    ('lifecycle', 'stages', ['delivered' if stage == 'done' else stage
                                             for stage in original['lifecycle']['stages']]),
                    ('lifecycle', 'fix_stages', ['open', 'closed'])]
        for group, key, value in settings:
            self.config = copy.deepcopy(original)
            self.config[group][key] = value
            self.commit()
            with self.subTest(setting=f'{group}.{key}'), self.assertRaises(fixture.orch.Blocked):
                prepare.compile_snapshot(self.root, self.manifest)


if __name__ == '__main__':
    unittest.main()
