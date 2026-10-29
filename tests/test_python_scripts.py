"""Actual maintenance script CLI smoke and destructive-operation preflight tests."""
import importlib.util
from pathlib import Path
import subprocess
import shutil
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
    def test_rename_preview_apply_and_repeat_are_consistent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "commands").mkdir()
            target = root / "commands/example.md"
            original = "Read .ai/references/example.md and phase_run query help\n"
            target.write_text(original, encoding="utf-8")
            def invoke(*args):
                return subprocess.run([sys.executable, "-I", str(ROOT / "scripts/rename.py"), "--root", str(root), *args], capture_output=True, text=True, encoding="utf-8")
            preview = invoke()
            self.assertEqual(0, preview.returncode, preview.stderr)
            self.assertIn("WOULD WRITE", preview.stdout)
            self.assertEqual(original, target.read_text(encoding="utf-8"))
            applied = invoke("--apply")
            self.assertEqual(0, applied.returncode, applied.stderr)
            self.assertIn("engineer_run query help", target.read_text(encoding="utf-8"))
            self.assertIn("0 files; 0 substitutions", invoke("--apply").stdout)

    def test_link_checker_reports_and_clears_real_missing_target(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "commands").mkdir()
            (root / "commands/sample.md").write_text("[missing](target.md)\n", encoding="utf-8")
            argv = [sys.executable, "-I", str(ROOT / "scripts/links.py"), "--root", str(root)]
            failed = subprocess.run(argv, capture_output=True, text=True)
            self.assertEqual(1, failed.returncode)
            self.assertIn("BROKEN commands/sample.md:1: target.md", failed.stdout)
            (root / "commands/target.md").write_text("# Target\n", encoding="utf-8")
            passed = subprocess.run(argv, capture_output=True, text=True)
            self.assertEqual(0, passed.returncode, passed.stderr)

    def test_delete_preview_apply_verify_and_modified_file_refusal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, check=True).stdout.strip()
            git("init", "-b", "main")
            git("config", "user.name", "Script Test")
            git("config", "user.email", "scripts@example.invalid")
            (root / "remove.md").write_text("original\n", encoding="utf-8")
            git("add", "remove.md")
            git("commit", "-m", "fixture")
            delete_batch.delete_paths(root, ["remove.md"])
            self.assertEqual("", git("status", "--porcelain"))
            (root / "remove.md").write_text("modified\n", encoding="utf-8")
            with self.assertRaises(subprocess.CalledProcessError):
                delete_batch.delete_paths(root, ["remove.md"], apply=True)
            self.assertTrue((root / "remove.md").exists())
            (root / "remove.md").write_text("original\n", encoding="utf-8")
            self.assertEqual(0, delete_batch.delete_paths(root, ["remove.md"], apply=True))
            self.assertEqual(0, delete_batch.delete_paths(root, ["remove.md"], verify=True))
            self.assertFalse((root / "remove.md").exists())

    def test_inventory_preview_apply_and_check_real_git_baseline(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            subprocess.run(["git", "init", str(root)], capture_output=True, check=True)
            baseline = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "1eb6c97"], text=True).strip()
            subprocess.run(["git", "-C", str(root), "fetch", "--no-tags", "--depth", "1", str(ROOT), baseline], capture_output=True, check=True)
            (root / "commands").mkdir()
            (root / "commands/sample.md").write_text("# Sample\n", encoding="utf-8")
            argv = [sys.executable, "-I", str(ROOT / "scripts/inventory.py"), "--root", str(root)]
            preview = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(0, preview.returncode, preview.stderr)
            self.assertFalse((root / "docs/INVENTORY.md").exists())
            applied = subprocess.run([*argv, "--apply"], capture_output=True, text=True)
            self.assertEqual(0, applied.returncode, applied.stderr)
            checked = subprocess.run([*argv, "--check"], capture_output=True, text=True)
            self.assertEqual(0, checked.returncode, checked.stderr)
            (root / "commands/sample.md").write_text("# Changed\nnew line\n", encoding="utf-8")
            self.assertEqual(1, subprocess.run([*argv, "--check"], capture_output=True).returncode)

    def test_progress_reads_actual_terminal_git_trailers(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
            git("init", "-b", "main")
            git("config", "user.name", "Script Test")
            git("config", "user.email", "scripts@example.invalid")
            (root / "PLANNED-UPDATES.md").write_text("## 11. Agents\n| R-AG-01 | Example |\n", encoding="utf-8")
            git("add", "PLANNED-UPDATES.md")
            git("commit", "-m", "fixture")
            argv = [sys.executable, "-I", str(ROOT / "scripts/progress.py"), "--root", str(root), "--require-done"]
            self.assertEqual(1, subprocess.run(argv, capture_output=True).returncode)
            git("commit", "--allow-empty", "-m", "Complete fixture", "-m", "Rows: R-AG-01")
            self.assertEqual(0, subprocess.run(argv, capture_output=True).returncode)

    def test_anchor_reads_immutable_baseline_and_check_previews_without_execution(self):
        anchored = subprocess.run([sys.executable, "-I", str(ROOT / "scripts/anchor.py"), "R-AG-001"], capture_output=True, text=True)
        self.assertEqual(0, anchored.returncode, anchored.stderr)
        self.assertIn("baseline 9443672", anchored.stdout)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "PLANNED-UPDATES.md").write_text("### Phase 1: Fixture\n```check\necho fixture-check\n```\n", encoding="utf-8")
            argv = [sys.executable, "-I", str(ROOT / "scripts/check.py"), "--root", str(root), "--phase", "1"]
            result = subprocess.run(argv, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("WOULD RUN [1] echo fixture-check", result.stdout)
            if shutil.which("bash"):
                available = subprocess.run(["bash", "-c", "exit 0"], capture_output=True).returncode == 0
                self.assertEqual(0 if available else 1, subprocess.run([*argv, "--apply"], capture_output=True).returncode)

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
