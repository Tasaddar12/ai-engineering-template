import contextlib
import io
from pathlib import Path
import subprocess
import re
import tempfile
import unittest
from unittest.mock import patch
from tests.test_overhaul_scripts import load_tool

tool = load_tool("delete_batch")
common = load_tool("common")


class DeleteBatchTests(unittest.TestCase):
    def test_manifest_has_exact_counts_and_disjoint_batches(self):
        data = common.manifest()
        self.assertEqual(len(data["batch_a"]), 227)
        self.assertEqual(len(data["batch_b"]), 6)
        self.assertEqual(len(set(data["batch_a"])), 227)
        self.assertFalse(set(data["batch_a"]) & set(data["batch_b"]))
        self.assertEqual(len(data["renames"]), 18)
        plan = (Path(__file__).resolve().parents[1] / "PLANNED-UPDATES.md").read_text(encoding="utf-8")
        section = plan.split("## 10. Delete list", 1)[1].split("## 11.", 1)[0]
        a, b = section.split("### Batch B:", 1)
        def paths(text):
            return [line.strip() for block in re.findall(r'```text\n(.*?)```', text, re.DOTALL) for line in block.splitlines() if line.strip()]
        self.assertEqual(data["batch_a"], paths(a))
        self.assertEqual(data["batch_b"], paths(b))

    def test_unsafe_paths_fail_before_git_or_deletion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            victim = root / "safe.md"
            victim.write_text("keep", encoding="utf-8")
            for unsafe in (".", "../outside", "/", "C:/outside", ".ai/rules.md", ".planning/STATE.md", ".git/config", "nested/../safe.md"):
                with self.subTest(unsafe=unsafe), patch.object(tool.subprocess, "run") as run:
                    with self.assertRaises(ValueError):
                        tool.delete_paths(root, ["safe.md", unsafe], apply=True)
                    run.assert_not_called()
                    self.assertTrue(victim.exists())

    def test_symlink_and_directory_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "nested").mkdir()
            with self.assertRaises(ValueError):
                tool.delete_paths(root, ["nested"], apply=True)
            try:
                (root / "link").symlink_to(root / "nested", target_is_directory=True)
            except OSError:
                self.skipTest("Symlink privilege unavailable")
            with self.assertRaises(ValueError):
                tool.delete_paths(root, ["link/child.md"], apply=True)

    def test_preview_verify_and_apply_in_real_git_repository(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            root = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            (root / "remove.md").write_text("copied upstream\n", encoding="utf-8")
            subprocess.run(["git", "-C", directory, "add", "remove.md"], check=True)
            self.assertEqual(tool.delete_paths(root, ["remove.md"]), 0)
            self.assertTrue((root / "remove.md").exists())
            self.assertEqual(tool.delete_paths(root, ["remove.md"], verify=True), 1)
            self.assertEqual(tool.delete_paths(root, ["remove.md"], apply=True), 0)
            self.assertEqual(tool.delete_paths(root, ["remove.md"], verify=True), 0)
