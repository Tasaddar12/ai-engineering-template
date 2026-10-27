"""Real isolated Git preparation workers; execution deferred until publication."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNTIME = Path(__file__).resolve().parents[1]/"engineer/bin/engineer.py"


class ArtifactWorktrees(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git(self.root, "init", "-q", "-b", "session")
        self.git(self.root, "config", "user.name", "Artifact Test")
        self.git(self.root, "config", "user.email", "artifact@example.invalid")
        self.write(self.root, ".gitignore", ".worktrees/\n.planning/worktrees/\n")
        self.write(self.root, ".planning/phases/01-example/01-CONTEXT.md", "# Decisions\n")
        self.write(self.root, "product.txt", "original\n")
        self.git(self.root, "add", ".")
        self.git(self.root, "commit", "-qm", "baseline")
        self.artifact = ".planning/phases/01-example/01-PATTERNS.md"

    def git(self, cwd, *args):
        return subprocess.run(["git", *args], cwd=cwd, check=True, text=True, capture_output=True).stdout.strip()

    def write(self, cwd, file, content):
        path = cwd/file
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, "-I", str(RUNTIME), "query", *args],
                                cwd=self.root, env={**os.environ, "ENGINEER_ROOT": str(self.root)},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout+result.stderr)
        return json.loads(result.stdout if ok else result.stderr.splitlines()[-1])

    def create(self):
        result = self.cli("worktree.create", "patterns", "--phase", "quick-7",
                          "--artifact-role", "pattern-mapper", "--files", self.artifact)
        return Path(result["path"])

    def commit_worker(self, worker, extra=False):
        self.write(worker, self.artifact, "---\nphase: '01'\n---\n# Patterns\n\nObserved existing patterns.\n")
        if extra:
            self.write(worker, "product.txt", "unauthorized\n")
        self.git(worker, "add", ".")
        self.git(worker, "commit", "-qm", "record real pattern evidence")

    def test_merge_real_artifact_without_summary_records_ancestry_and_cleans(self):
        worker = self.create()
        self.commit_worker(worker)
        head = self.git(worker, "rev-parse", "HEAD")
        result = self.cli("worktree.merge-artifacts", "--phase", "quick-7")
        self.assertEqual(result["artifacts"], [self.artifact])
        self.assertEqual(result["merged"][0]["head"], head)
        self.git(self.root, "merge-base", "--is-ancestor", head, "HEAD")
        self.assertFalse(list(worker.rglob("*-SUMMARY.md")))
        cleaned = self.cli("worktree.cleanup-wave", "--phase", "quick-7")
        self.assertTrue(cleaned["wave_clean"])
        self.assertFalse(worker.exists())

    def test_exact_delta_refuses_product_source_and_preserves_worker(self):
        worker = self.create()
        self.commit_worker(worker, extra=True)
        failure = self.cli("worktree.merge-artifacts", "--phase", "quick-7", ok=False)
        self.assertEqual(failure["error"], "artifact-scope-violation")
        result = self.cli("worktree.cleanup-wave", "--phase", "quick-7")
        self.assertEqual(len(result["preserved"]), 1)
        self.assertTrue(worker.exists())

    def test_classification_rejects_source_writer_and_product_paths_before_creation(self):
        for role, file in (("executor", self.artifact), ("pattern-mapper", "product.txt")):
            self.cli("worktree.create", "bad", "--artifact-role", role, "--files", file, ok=False)
        self.assertEqual(len(self.git(self.root, "worktree", "list", "--porcelain").split("worktree "))-1, 1)

    def test_source_worker_still_requires_complete_summary(self):
        worker = Path(self.cli("worktree.create", "source", "--files", "product.txt")["path"])
        self.write(worker, "product.txt", "change\n")
        self.git(worker, "add", ".")
        self.git(worker, "commit", "-qm", "source change")
        self.assertEqual(self.cli("worktree.merge-wave", ok=False)["error"], "missing-worker-summary")

    def test_dirty_worker_and_post_merge_head_drift_block_removal(self):
        worker = self.create()
        self.commit_worker(worker)
        self.write(worker, "uncommitted.txt", "keep\n")
        self.assertEqual(self.cli("worktree.merge-artifacts", "--phase", "quick-7", ok=False)["error"], "dirty-worker")
        (worker/"uncommitted.txt").unlink()
        self.cli("worktree.merge-artifacts", "--phase", "quick-7")
        self.write(worker, self.artifact, "new changes\n")
        self.git(worker, "add", ".")
        self.git(worker, "commit", "-qm", "later work")
        self.assertEqual(self.cli("worktree.cleanup-wave", "--phase", "quick-7", ok=False)["error"], "worker-head-drift")
        self.assertTrue(worker.exists())
