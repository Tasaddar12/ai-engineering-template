import unittest
from pathlib import Path
import subprocess
import sys
import tempfile
from tests.test_overhaul_scripts import load_tool, TOOL_DIR

tool = load_tool("check")


class CheckTests(unittest.TestCase):
    def test_phase_parser_keeps_blocks_scoped_and_inversion_literal(self):
        text = "### Phase 0: Tools\n```check\ntrue\n! false\n```\n### Phase 8: Features\n```check\nfeature-test\n```\n## 6. Scripts\n```check\nignored\n```\n"
        self.assertEqual(tool.check_blocks(text), {"0": ["true", "! false"], "8": ["feature-test"]})
        self.assertEqual(tool.selected_checks(text, ["8a", "8f"]), [("8a", "feature-test"), ("8f", "feature-test")])
        with self.assertRaises(ValueError):
            tool.selected_checks(text, ["99"])

    def test_core_workflow_check_defers_feature_rows(self):
        text = "### Phase 5: Workflows\n```check\npython -I scripts/progress.py --prefix R-WF --require-done\n```\n"
        self.assertTrue(tool.selected_checks(text, ["5"])[0][1].endswith("--stage core"))

    def test_checks_require_apply_and_bash_handles_inversion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "PLANNED-UPDATES.md").write_text("### Phase 0: Tools\n```check\nprintf ran > marker.txt\n! false\n```\n", encoding="utf-8")
            command = [sys.executable, "-I", str(TOOL_DIR / "check.py"), "--root", directory, "--phase", "0"]
            preview = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            self.assertFalse((root / "marker.txt").exists())
            applied = subprocess.run(command + ["--apply"], capture_output=True, text=True)
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertEqual((root / "marker.txt").read_text(encoding="utf-8"), "ran")
