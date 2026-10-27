from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.test_overhaul_scripts import load_tool, TOOL_DIR

tool = load_tool("rename")


class RenameTests(unittest.TestCase):
    def test_token_boundaries_and_full_content_preservation(self):
        original = "Keep this entire paragraph.\n/gsd:plan-phase gsd-planner gsd-planner-extra\n@~/.claude/gsd-core/references/tdd.md\nname: gsd:test\nCLAUDE.md phase_run query help\n"
        expected = "Keep this entire paragraph.\n/plan-phase planner gsd-planner-extra\n@engineer/references/tdd.md\nname: test\nAGENTS.md engineer_run query help\n"
        replaced, counts = tool.substitutions(original, {"agents/gsd-planner.md": "agents/planner.md"})
        self.assertEqual(replaced, expected)
        self.assertEqual(sum(counts.values()), 6)
        self.assertEqual(tool.substitutions(replaced, {})[1], {})

    def test_launcher_is_replaced_as_complete_line_and_requires_port(self):
        original = "before\n_GSD_SHIM_NAME=old; gsd_run() { node old; };\nafter\n"
        with self.assertRaises(ValueError):
            tool.substitutions(original, {}, "gsd_run old")
        replaced, counts = tool.substitutions(original, {}, "engineer_run() { python engineer.py \"$@\"; }\n")
        self.assertEqual(replaced, "before\nengineer_run() { python engineer.py \"$@\"; }\nafter\n")
        self.assertEqual(counts, {"launcher": 1})

    def test_isolated_cli_dry_run_and_apply_protect_legacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "agents").mkdir()
            source = root / "agents" / "role.md"
            source.write_bytes(b"body\r\ngsd-planner\r\n")
            (root / ".ai").mkdir()
            protected = root / ".ai" / "old.md"
            protected.write_text("gsd-planner", encoding="utf-8")
            command = [sys.executable, "-I", str(TOOL_DIR / "rename.py"), "--root", directory]
            preview = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            self.assertEqual(source.read_bytes(), b"body\r\ngsd-planner\r\n")
            applied = subprocess.run(command + ["--apply"], capture_output=True, text=True)
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertEqual(source.read_bytes(), b"body\nplanner\n")
            self.assertEqual(protected.read_text(encoding="utf-8"), "gsd-planner")
            denied = subprocess.run(command + ["--path", ".ai/old.md", "--apply"], capture_output=True, text=True)
            self.assertNotEqual(denied.returncode, 0)
