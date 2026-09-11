import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_orchestrate as fixture

SPEC = importlib.util.spec_from_file_location('record_ids', fixture.RUNTIME.with_name('record_ids.py'))
ids = importlib.util.module_from_spec(SPEC)
with patch.dict(sys.modules, orchestrate=fixture.orch):
    SPEC.loader.exec_module(ids)


class RecordIDTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')

    def test_all_lifecycles_worktrees_and_unconsumed_blocks_raise_the_floor(self):
        self.write('one/.ai/fixes/done/2026-Q3/FIX-009-old.md', '# Old repair\n')
        self.write('two/.ai/fixes/open/FIX-011-new.md', '# New repair\n')
        self.write('one/.ai/templates/FIX-999-example.md', '# Example\n')
        self.write('one/.ai/state/orchestration/ORCH-001.md',
                   '## Reserved id blocks\n\n| Track | FIX | INTAKE |\n|---|---|---|\n| a | 12–31 | 1–20 |\n')
        self.write('common/orchestration/ORCH-002/state.json', json.dumps({'tracks': {
            'a': {'status': 'abandoned', 'ids': {'FIX': [32, 51]}}}}))
        highest = ids.highest_issued([self.root / 'one', self.root / 'two'], self.root / 'common')
        self.assertEqual(highest['FIX'], 51)
        self.assertEqual(highest['INTAKE'], 20)

    def test_machine_manifest_reservations_are_counted(self):
        self.write('repo/.ai/state/orchestration/ORCH-003.md', '## Execution schedule\n```json\n' +
                   json.dumps({'tracks': [{'ids': {'FIX': [41, 60], 'ADR': [61, 80]}}]}) + '\n```\n')
        highest = ids.highest_issued([self.root / 'repo'], self.root / 'common')
        self.assertEqual(highest['FIX'], 60)
        self.assertEqual(highest['ADR'], 80)

    def test_malformed_reservations_block_instead_of_suggesting_collisions(self):
        self.write('repo/.ai/state/orchestration/ORCH-001.md',
                   '## Reserved id blocks\n| Track | FIX |\n|---|---|\n| a | 10–unknown |\n')
        with self.assertRaisesRegex(fixture.orch.Blocked, 'Invalid FIX reservation'):
            ids.highest_issued([self.root / 'repo'], self.root / 'common')

    def test_proposal_does_not_create_reservation_or_dirty_git(self):
        fixture.orch.git(self.root, 'init', '-b', 'main')
        before = fixture.orch.git(self.root, 'status', '--porcelain')
        proposed = ids.next_range(self.root, 'FIX', 20)
        self.assertEqual(proposed, {'kind': 'FIX', 'first': 1, 'last': 20, 'reserved': False})
        self.assertEqual(fixture.orch.git(self.root, 'status', '--porcelain'), before)
        self.assertFalse((self.root / '.git/orchestration').exists())

    def test_receipt_only_orch_id_cannot_be_reissued(self):
        fixture.orch.git(self.root, 'init', '-b', 'main')
        self.write('.git/orchestration/ORCH-041/state.json', json.dumps({'tracks': {}}))
        self.assertEqual(ids.next_range(self.root, 'ORCH'),
                         {'kind': 'ORCH', 'first': 42, 'last': 42, 'reserved': False})


if __name__ == '__main__':
    unittest.main()
