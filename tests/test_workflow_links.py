"""Validate source navigation and host imports without interpreting examples."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('engineer_link_check', ROOT / 'scripts/links.py')
links = importlib.util.module_from_spec(spec)
spec.loader.exec_module(links)

class SourceNavigation(unittest.TestCase):
    def test_source_navigation(self):
        self.assertEqual([], list(links.broken_links(ROOT)))

    def test_host_imports_require_a_real_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'commands/task.md'
            reference = root / 'engineer/references/retained.md'
            reference.parent.mkdir(parents=True)
            reference.write_text('# Full method\n', encoding='utf-8')
            for host in ('claude', 'codex'):
                self.assertTrue(links.resolve_target(root, source, f'~/.{host}/engineer/references/retained.md', True))
                self.assertFalse(links.resolve_target(root, source, f'~/.{host}/engineer/references/missing.md', True))

    def test_examples_preserve_real_links_and_line_numbers(self):
        text = '```markdown\n[example](missing.md)\n```\n`[literal](also-missing.md)`\n[actual](required.md)\n'
        self.assertEqual([('required.md', 5, False)], list(links.targets(links.navigation(text))))
        self.assertEqual([], list(links.targets('Install @scope/package and @react-three/fiber.')))

    def test_missing_real_links_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'commands').mkdir()
            (root / 'commands/task.md').write_text('[Required](missing.md)\n', encoding='utf-8')
            self.assertEqual([('commands/task.md', 1, 'missing.md')], list(links.broken_links(root)))
