"""Actual maintenance script CLI smoke and destructive-operation preflight tests."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import common
import delete_batch
import check
import verbs


class PythonScripts(unittest.TestCase):
    def test_every_script_has_help_and_dispatcher_rejects_unknown(self):
        for name in ("anchor", "check", "delete_batch", "inventory", "links", "progress", "rename", "verbs", "SCRIPT"):
            with self.subTest(script=name):
                result = subprocess.run([sys.executable, "-I", str(ROOT / "scripts" / (name + ".py")), "--help"], capture_output=True, text=True, timeout=15)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("Usage:" if name == "SCRIPT" else "usage:", result.stdout)
        result = subprocess.run([sys.executable, "-I", str(ROOT / "scripts/SCRIPT.py"), "../outside"], capture_output=True, text=True)
        self.assertEqual(2, result.returncode)

    def test_delete_preflights_entire_batch_before_git_rm(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "keep.md"
            target.write_text("keep", encoding="utf-8")
            for unsafe in ("../outside", ".ai/owned.md", "/absolute", "C:/outside", "keep.md/.."):
                with self.subTest(path=unsafe), self.assertRaises(ValueError):
                    delete_batch.delete_paths(root, ["keep.md", unsafe], apply=True)
                self.assertTrue(target.exists())

    def test_check_selection_and_unknown_phase(self):
        plan = "### Phase 5: Core\n```check\npython -I scripts/progress.py\n```\n### Phase 8: Features\n```check\npython -V\n```\n"
        self.assertIn("--stage core", check.selected_checks(plan, ["5"])[0][1])
        self.assertEqual([("8b", "python -V")], check.selected_checks(plan, ["8b"]))
        with self.assertRaises(ValueError):
            check.selected_checks(plan, ["99"])

    def test_registry_parser_handles_current_dynamic_registry(self):
        known = verbs.registered_verbs((ROOT / "engineer/bin/engineer.py").read_text(encoding="utf-8"))
        self.assertTrue({"review.normalize-fallow", "spec.ui-probe", "manager.run", "pipeline.run", "idea.capture"} <= known)

    def test_row_credit_requires_terminal_valid_trailer(self):
        self.assertEqual({"R-AG-01", "V-02"}, common.completed_rows("subject\n\nRows: R-AG-01, V-02\x1e"))
        self.assertEqual(set(), common.completed_rows("Rows: R-AG-01\n\nbody\x1e"))


if __name__ == "__main__":
    unittest.main()
