import tempfile
from pathlib import Path
import unittest
from tests.test_overhaul_scripts import load_tool

tool = load_tool("verbs")


class VerbsTests(unittest.TestCase):
    def test_registry_is_read_without_executing_runtime(self):
        source = "raise RuntimeError('must never execute')\nVERBS: dict = {'phase.locate': handler, 'help': module.function}\n"
        self.assertEqual(tool.registered_verbs(source), {"phase.locate", "help"})
        self.assertEqual(tool.registered_verbs("VERBS = {'help', 'config-get'}"), {"help", "config-get"})
        with self.assertRaises(ValueError):
            tool.registered_verbs("VERBS = build_registry()")
        with self.assertRaises(ValueError):
            tool.registered_verbs("OTHER = {}")

    def test_dotted_calls_and_locations_ignore_dynamic_placeholders(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "commands").mkdir()
            (root / "commands" / "sample.md").write_text("engineer_run query phase.locate\nengineer_run query <verb>\nengineer_run query $VERB\nengineer_run query missing\n", encoding="utf-8")
            self.assertEqual(tool.call_sites(root), [("phase.locate", "commands/sample.md", 1), ("missing", "commands/sample.md", 4)])
