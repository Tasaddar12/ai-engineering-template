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

    def test_finite_registration_families_are_inspected_without_handlers(self):
        source = '''
raise RuntimeError("never execute the module")
def registry():
    verbs = {"direct": dangerous_handler()}
    for action in ("create", "health"):
        verbs["worktree." + action] = lambda a: dangerous_handler(a)
    verbs["phase.complete"] = missing.handler
    return verbs
VERBS = registry()
'''
        self.assertEqual(tool.registered_verbs(source), {"direct", "worktree.create", "worktree.health", "phase.complete"})

    def test_dynamic_constructor_behavior_and_registry_reassignment_fail_closed(self):
        for source in (
            'def registry():\n    return discover()\nVERBS = registry()',
            'def registry():\n    verbs = {}\n    for key in imported_names:\n        verbs[key] = handler\n    return verbs\nVERBS = registry()',
            'def registry():\n    verbs = {}\n    side_effect()\n    return verbs\nVERBS = registry()',
            'def registry():\n    verbs = {}\n    verbs[compute_key()] = handler\n    return verbs\nVERBS = registry()',
            'VERBS = {"old": handler}\nVERBS = {"new": handler}',
            'VERBS = registry()\ndef registry():\n    return {}',
        ):
            with self.subTest(source=source), self.assertRaises(ValueError):
                tool.registered_verbs(source)

    def test_dynamic_dotted_calls_do_not_become_partial_unknown_verbs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "commands").mkdir()
            (root / "commands/sample.md").write_text('engineer_run query init.<workflow>\nengineer_run query worktree.$ACTION\nengineer_run query state.save\n', encoding="utf-8")
            self.assertEqual(tool.call_sites(root), [("state.save", "commands/sample.md", 3)])
