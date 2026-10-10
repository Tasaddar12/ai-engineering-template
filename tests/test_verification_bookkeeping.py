"""Exercise the guarded rollback contract against a real temporary Git repo."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    ".planning/ROADMAP.md",
    ".planning/STATE.md",
    ".planning/REQUIREMENTS.md",
}


class BookkeepingCompensationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.git("init")
        self.git("config", "user.name", "Workflow Contract Test")
        self.git("config", "user.email", "workflow-contract@example.invalid")

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True,
            capture_output=True, text=True,
        ).stdout.strip()

    def write(self, path, value):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")

    def commit(self, message, *paths):
        self.git("add", "--", *paths)
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def changed_paths(self, revision):
        output = self.git(
            "diff-tree", "--no-commit-id", "--name-only", "--no-renames",
            "-r", revision,
        )
        return set(output.splitlines()) if output else set()

    def assert_clean(self):
        self.assertEqual("", self.git("status", "--porcelain", "--untracked-files=all"))

    def seed(self):
        self.write(".planning/ROADMAP.md", "phase: open\n")
        self.write(".planning/STATE.md", "status: active\n")
        self.write(".planning/REQUIREMENTS.md", "REQ-1: Pending\n")
        self.write("src/app.py", "value = 'implemented'\n")
        return self.commit(
            "phase source and open planning records",
            ".planning/ROADMAP.md", ".planning/STATE.md",
            ".planning/REQUIREMENTS.md", "src/app.py",
        )

    def test_reverts_only_direct_clean_bookkeeping_commit_and_preserves_source(self):
        before = self.seed()
        self.write(".planning/ROADMAP.md", "phase: complete\n")
        self.write(".planning/STATE.md", "status: verified\n")
        self.write(".planning/REQUIREMENTS.md", "REQ-1: Complete\n")
        bookkeeping = self.commit(
            "coordinator success bookkeeping", *sorted(ALLOWED)
        )

        self.assert_clean()
        self.assertEqual(before, self.git("rev-parse", f"{bookkeeping}^"))
        self.assertEqual(ALLOWED, self.changed_paths(bookkeeping))

        self.git("revert", "--no-edit", bookkeeping)

        self.assert_clean()
        self.assertNotEqual(bookkeeping, self.git("rev-parse", "HEAD"))
        self.assertEqual("phase: open\n", (self.repo / ".planning/ROADMAP.md").read_text())
        self.assertEqual("status: active\n", (self.repo / ".planning/STATE.md").read_text())
        self.assertEqual("REQ-1: Pending\n", (self.repo / ".planning/REQUIREMENTS.md").read_text())
        self.assertEqual("value = 'implemented'\n", (self.repo / "src/app.py").read_text())

    def test_source_touch_fails_guard_and_is_preserved(self):
        self.seed()
        self.write(".planning/ROADMAP.md", "phase: complete\n")
        self.write(".planning/STATE.md", "status: verified\n")
        self.write(".planning/REQUIREMENTS.md", "REQ-1: Complete\n")
        self.write("src/app.py", "value = 'new source'\n")
        mixed = self.commit(
            "mixed source and bookkeeping", *sorted(ALLOWED), "src/app.py"
        )

        self.assertFalse(self.changed_paths(mixed) <= ALLOWED)
        self.assertEqual(mixed, self.git("rev-parse", "HEAD"))
        self.assertEqual("value = 'new source'\n", (self.repo / "src/app.py").read_text())

    def test_workflow_documents_the_guarded_failure_path(self):
        workflow = (ROOT / ".ai/workflows/verify-work.md").read_text(encoding="utf-8")
        evidence = (ROOT / ".ai/references/verification-evidence.md").read_text(encoding="utf-8")
        self.assertIn("pre_bookkeeping_revision=$(git rev-parse HEAD)", workflow)
        self.assertIn('git revert --no-edit "${bookkeeping_commit}"', evidence)
        self.assertIn('git rev-parse "${bookkeeping_commit}^"', evidence)
        self.assertIn("The exact direct-child commit", workflow)
        self.assertIn("never a pass", workflow)
        ship = (ROOT / ".ai/workflows/ship.md").read_text(encoding="utf-8")
        ship = " ".join(ship.split())
        self.assertIn("preparation_record_changed=false", ship)
        self.assertIn("skip another verifier dispatch and report commit", ship)
        self.assertIn("verification.currentness ${phase_number}", ship)
        self.assertIn("does not start another broad verifier", ship)


if __name__ == "__main__":
    unittest.main()
