"""Record navigation and preparation behavior, including fresh-worktree handoffs."""
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import unquote, urlsplit

import yaml

import test_phase_runtime as fixtures


SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / ".ai/runtime"))
from phase_records import PhaseError, git as record_git, overlaps, owns, read_yaml, record  # noqa: E402


class PhaseRecordTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.PhaseRuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_new_phase_stays_pending_and_allocates_across_worktrees(self):
        f = self.fixture
        f.cli("new", "second", "--title", "Second change")
        context = f.checkout / ".ai/phases/02-second/02-CONTEXT.md"
        self.assertEqual(record(context)[0]["approval"], "pending")
        self.assertIn("02-CONTEXT.md", (f.checkout / ".ai/ROADMAP.md").read_text())
        self.assertEqual(f.git(f.checkout, "status", "--porcelain"), "")
        sibling = f.primary / ".worktrees/another"
        f.git(f.primary, "worktree", "add", "-b", "codex/another", str(sibling), "codex/phase-test")
        f.cli("new", "third", "--title", "Third change", root=sibling)
        self.assertTrue((sibling / ".ai/phases/03-third/03-CONTEXT.md").is_file())
        f.cli("run", "02", succeeds=False)
        self.assertEqual(f.events(), [])
        f.assert_primary_untouched()

    def test_sync_commits_only_derived_state(self):
        f = self.fixture
        before = f.git(f.checkout, "rev-parse", "HEAD")
        f.cli("sync")
        paths = f.git(f.checkout, "diff", "--name-only", before, "HEAD").splitlines()
        self.assertEqual(paths, [".ai/STATE.md"])
        self.assertIn("01-example", (f.checkout / ".ai/STATE.md").read_text())
        f.assert_primary_untouched()

    def test_git_text_normalizes_line_endings_while_raw_preserves_them(self):
        f = self.fixture
        content = b"first\r\nsecond\rthird\n"
        (f.checkout / "line-endings.txt").write_bytes(content)
        f.commit("Record a blob with mixed line endings")
        self.assertEqual(record_git(f.checkout, "show", "HEAD:line-endings.txt"), "first\nsecond\nthird")
        self.assertEqual(record_git(f.checkout, "show", "HEAD:line-endings.txt", raw=True), content.decode())

    def test_readiness_rejects_coordinator_ownership_and_bad_configuration(self):
        f = self.fixture
        for path in (".ai/", ".AI/PHASES/", ".ai/state.md", ".ai/config.yaml"):
            with self.subTest(path=path):
                f.component("01-01", files=[path])
                f.commit("Declare invalid coordinator ownership")
                f.cli("check", "01", succeeds=False)
        f.component("01-01")
        f.config["execution"]["max_parallel"] = True
        f.configure()
        f.commit("Reject boolean concurrency")
        f.cli("check", "01", succeeds=False)
        self.assertEqual(f.events(), [])

    def test_approved_flag_does_not_accept_placeholder_authorization(self):
        f = self.fixture
        context = f.checkout / fixtures.PHASE_PATH / "01-CONTEXT.md"
        context.write_text(context.read_text().replace(
            "The user approved implementing and verifying this phase in worktrees.", "CHANGEME"
        ), encoding="utf-8")
        f.commit("Leave authorization unresolved")
        f.cli("check", "01", succeeds=False)
        self.assertEqual(f.events(), [])

    def test_explicit_replan_after_check_mutation_preserves_prior_implementation(self):
        f = self.fixture
        original = f.config["verification"]["commands"]
        f.config["verification"]["commands"] = [[sys.executable, "-c",
            "from pathlib import Path; import subprocess; "
            "p=Path('check-created.txt'); apply=Path.cwd().name=='phase'; "
            "p.write_text('Unintended change') if apply else None; "
            "subprocess.run(['git','add','check-created.txt'],check=True) if apply else None; "
            "subprocess.run(['git','commit','-m','Unintended check commit'],check=True) if apply else None"]]
        f.configure()
        f.commit("Prepare a check that unexpectedly changes source")
        f.cli("run", "01", succeeds=False)
        self.assertTrue((f.checkout / "check-created.txt").is_file())
        (f.checkout / "check-created.txt").unlink()
        f.config["verification"]["commands"] = original
        f.configure()
        f.commit("Resolve inspected check mutation and restore read-only check")
        f.cli("run", "01", "--replan", "--workers-stopped")
        self.assertEqual(len(f.events()), 1)
        self.assertTrue(f.summary("01-01").is_file())
        self.assertFalse((f.checkout / "check-created.txt").exists())

    def test_committed_verification_remains_visible_without_local_checkpoint(self):
        f = self.fixture
        f.cli("run", "01")
        f.cli("verify", "01")
        sibling = f.primary / ".worktrees/inspection"
        f.git(f.primary, "worktree", "add", "-b", "codex/inspection", str(sibling), "codex/phase-test")
        before = f.git(sibling, "rev-parse", "HEAD")
        result = f.cli("status", "01", root=sibling)
        self.assertIn("recorded verification: passed", result.stdout)
        self.assertIn("checkpoint unavailable", result.stdout)
        self.assertEqual(f.git(sibling, "rev-parse", "HEAD"), before)


class OwnershipBoundaryTests(unittest.TestCase):
    def test_exact_ownership_and_conservative_overlap_have_separate_case_rules(self):
        self.assertTrue(owns("README.md", "README.md"))
        self.assertFalse(owns("README.md", "readme.md"))
        self.assertFalse(owns("src/", "Src/component.py"))
        self.assertTrue(overlaps(["README.md"], ["readme.md"]))
        self.assertTrue(overlaps(["src/"], ["Src/component.py"]))


class DocumentNavigationTests(unittest.TestCase):
    def test_active_markdown_links_resolve_to_files_and_headings(self):
        documents = [SOURCE / "AGENTS.md", SOURCE / "README.md"]
        documents += list((SOURCE / ".ai").rglob("*.md")) + list((SOURCE / "docs").rglob("*.md"))
        checked = 0
        for path in documents:
            if path.name.startswith("FIX-"):
                continue  # Historical references belong to their original Git revisions.
            body = re.sub(r"(?ms)^```.*?^```[^\n]*$", "", path.read_text(encoding="utf-8-sig"))
            for match in re.finditer(r"\[[^\]\n]+\]\((<[^>]+>|[^)\s]+)\)", body):
                target = match[1].strip("<>")
                parts = urlsplit(target)
                if parts.scheme or parts.netloc:
                    continue
                destination = (path.parent / unquote(parts.path)).resolve() if parts.path else path
                with self.subTest(file=path.relative_to(SOURCE), link=target):
                    self.assertTrue(destination.exists(), f"Missing linked file: {destination}")
                    if parts.fragment and destination.suffix == ".md":
                        headings = re.findall(r"(?m)^#{1,6}\s+(.+?)\s*#*\s*$", destination.read_text(encoding="utf-8-sig"))
                        anchors = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
                        self.assertIn(unquote(parts.fragment), anchors)
                checked += 1
        self.assertGreater(checked, 100, "Link inspection unexpectedly skipped the active documentation")

    def test_templates_and_config_use_readable_unambiguous_yaml(self):
        for path in (SOURCE / ".ai/templates").glob("*.md"):
            if path.read_text(encoding="utf-8").startswith("---\n"):
                with self.subTest(template=path.name):
                    metadata, body = record(path)
                    self.assertTrue(metadata)
                    self.assertTrue(body.strip())
        config = read_yaml((SOURCE / ".ai/config.yaml").read_text(encoding="utf-8"))
        self.assertEqual(config["verification"]["commands"], [])
        with self.assertRaisesRegex(PhaseError, "Duplicate YAML key"):
            read_yaml("approval: pending\napproval: approved\n")


if __name__ == "__main__":
    unittest.main()
