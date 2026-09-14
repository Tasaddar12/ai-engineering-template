"""Exercise the downloaded installer against real Git sources and target projects."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / ".ai/install.py"


def command(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=True).stdout


class InstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_temp = tempfile.TemporaryDirectory(prefix="installer-source-")
        cls.source = Path(cls.source_temp.name)
        for directory in (".ai", ".agents", ".planning", "docs"):
            shutil.copytree(ROOT / directory, cls.source / directory,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for name in ("AGENTS.md", "changes.log", "README.md", ".gitattributes"):
            shutil.copy2(ROOT / name, cls.source / name)
        # Source-project records must never become destination-project history.
        for name in ("phases/99-source/99-CONTEXT.md", "specs/SPEC-source.md",
                     "decisions/ADR-source.md", "codebase/source-map.md"):
            path = cls.source / ".planning" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Source-only project history", encoding="utf-8")
        command("git", "init", "--quiet", str(cls.source))
        command("git", "add", ".", cwd=cls.source)
        command("git", "-c", "user.name=Installer Test", "-c", "user.email=test@example.invalid",
                "commit", "--quiet", "-m", "Template fixture", cwd=cls.source)
        cls.revision = command("git", "rev-parse", "HEAD", cwd=cls.source).strip()

    @classmethod
    def tearDownClass(cls):
        cls.source_temp.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="installer-target-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.target = self.base / "project with spaces"

    def install(self, *extra):
        return subprocess.run([sys.executable, str(INSTALLER), "--source", str(self.source),
                               "--ref", self.revision, "--target", str(self.target),
                               "--skip-deps", *extra], text=True, capture_output=True)

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): p.read_bytes()
                for p in self.target.rglob("*") if p.is_file() and ".git" not in p.relative_to(self.target).parts}

    def test_new_project_starts_runtime_and_omits_template_history(self):
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(self.revision, result.stdout)
        self.assertIn("human must review and commit", result.stdout)
        self.assertEqual(self.target.resolve(), Path(command("git", "rev-parse", "--show-toplevel", cwd=self.target).strip()).resolve())
        self.assertEqual("", command("git", "remote", cwd=self.target))
        status = command(sys.executable, ".ai/runtime/phase.py", "status", cwd=self.target)
        self.assertIn("No phases yet", status)
        self.assertIn("Onboarding pending", (self.target / ".planning/PROJECT.md").read_text(encoding="utf-8"))
        for omitted in ("README.md", "tests", ".github", ".planning/maintenance", ".ai-venv",
                        "changes.log", "docs/WORKFLOW-DIRECTION.md", ".ai/install-assets",
                        ".planning/phases/99-source", ".planning/specs/SPEC-source.md",
                        ".planning/decisions/ADR-source.md", ".planning/codebase/source-map.md"):
            self.assertFalse((self.target / omitted).exists(), omitted)
        for name in ("AGENTS.md", ".ai/RULES.md", ".ai/README.md", ".planning/PROJECT.md",
                     ".planning/REQUIREMENTS.md", ".planning/ROADMAP.md", ".planning/STATE.md"):
            body = (self.target / name).read_text(encoding="utf-8")
            for source_claim in ("This repository is a reusable engineering workflow template",
                                 "This is a reusable template", "CHANGEME", "AUTH-01", "Critical Fix"):
                self.assertNotIn(source_claim, body, name)
        self.assertTrue((self.target / ".agents/skills/codebase-recon/SKILL.md").is_file())
        self.assertTrue((self.target / "docs/INSTALL.md").is_file())
        (self.target / ".worktrees").mkdir()
        (self.target / ".worktrees/local.txt").write_text("local")
        self.assertIn(".worktrees/local.txt", command("git", "check-ignore", ".worktrees/local.txt", cwd=self.target))

    def test_existing_repository_preserves_files_history_remote_and_reruns(self):
        self.target.mkdir()
        original = {"README.md": b"Existing product\n", "app.py": b"print('hello')\n",
                    "AGENTS.md": b"# Existing instructions\r\nKeep these.\r\n", ".gitignore": b"/build\r\n"}
        for name, content in original.items():
            (self.target / name).write_bytes(content)
        command("git", "init", "--quiet", str(self.target))
        command("git", "add", ".", cwd=self.target)
        command("git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "commit", "--quiet", "-m", "Existing project", cwd=self.target)
        head = command("git", "rev-parse", "HEAD", cwd=self.target)
        command("git", "remote", "add", "origin", "https://example.invalid/existing.git", cwd=self.target)
        (self.target / "app.py").write_bytes(b"uncommitted work\n")
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(original["README.md"], (self.target / "README.md").read_bytes())
        self.assertEqual(b"uncommitted work\n", (self.target / "app.py").read_bytes())
        for name in ("AGENTS.md", ".gitignore"):
            self.assertTrue((self.target / name).read_bytes().startswith(original[name]))
        before = self.snapshot()
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(head, command("git", "rev-parse", "HEAD", cwd=self.target))
        self.assertIn("existing.git", command("git", "remote", "get-url", "origin", cwd=self.target))

    def test_dry_run_leaves_nonexistent_target_absent(self):
        result = self.install("--dry-run")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Would change", result.stdout)
        self.assertFalse(self.target.exists())

    def test_existing_project_records_and_config_are_authoritative(self):
        records = {name: f"Existing project {name}; preserve decisions and progress.\n".encode()
                   for name in ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md", "STATE.md")}
        records["config.yaml"] = b"verification:\n  commands: [[npm, test]]\n"
        (self.target / ".planning").mkdir(parents=True)
        for name, content in records.items():
            (self.target / ".planning" / name).write_bytes(content)
        for options in ((), ("--repair-template-context",)):
            result = self.install(*options)
            self.assertEqual(0, result.returncode, result.stderr)
            for name, content in records.items():
                self.assertEqual(content, (self.target / ".planning" / name).read_bytes())
        self.assertTrue((self.target / ".ai/runtime/phase.py").is_file())

    def test_git_line_ending_changes_do_not_duplicate_or_conflict_with_context(self):
        self.target.mkdir()
        (self.target / "AGENTS.md").write_bytes(b"# Product instructions\n")
        self.assertEqual(0, self.install().returncode)
        for name in ("AGENTS.md", ".ai/RULES.md", "docs/TEMPLATE-GUIDE.md"):
            path = self.target / name
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        before = self.snapshot()
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, self.snapshot())

    def seed_legacy_context(self, appended=False):
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        legacy = json.loads((ROOT / ".ai/install-assets/legacy-context.json").read_text(encoding="utf-8"))
        agent = legacy["agent_entry"].encode()
        if appended:
            agent = b"# Existing product guidance\r\nKeep this.\r\n\n\n<!-- ai-engineering-template -->\n" + agent + b"\nUser added this later.\r\n"
        (self.target / "AGENTS.md").write_bytes(agent)
        (self.target / ".ai/RULES.md").write_text(legacy["rules"], encoding="utf-8")
        for name, text in legacy["obsolete_files"].items():
            content = text.encode()
            self.assertEqual(legacy["sha256"][name], hashlib.sha256(content).hexdigest())
            (self.target / name).write_bytes(content)
        for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE"):
            (self.target / f".planning/{name}.md").write_bytes((ROOT / f".planning/{name}.md").read_bytes())

    def test_explicit_repair_replaces_old_context_and_removes_only_known_history(self):
        self.seed_legacy_context(appended=True)
        custom = b"# Actual project\nThese are confirmed product decisions.\n"
        (self.target / ".planning/PROJECT.md").write_bytes(custom)
        before = self.snapshot()
        preview = self.install("--repair-template-context", "--dry-run")
        self.assertEqual(0, preview.returncode, preview.stderr)
        self.assertIn("remove changes.log", preview.stdout)
        self.assertEqual(before, self.snapshot())
        result = self.install("--repair-template-context")
        self.assertEqual(0, result.returncode, result.stderr)
        agent = (self.target / "AGENTS.md").read_bytes()
        self.assertTrue(agent.startswith(b"# Existing product guidance\r\nKeep this.\r\n"))
        self.assertTrue(agent.endswith(b"User added this later.\r\n"))
        self.assertNotIn(b"This repository is a reusable engineering workflow template", agent)
        self.assertNotIn("This is a reusable template", (self.target / ".ai/RULES.md").read_text(encoding="utf-8"))
        self.assertEqual(custom, (self.target / ".planning/PROJECT.md").read_bytes())
        self.assertNotIn("AUTH-01", (self.target / ".planning/REQUIREMENTS.md").read_text(encoding="utf-8"))
        self.assertNotIn("Critical Fix", (self.target / ".planning/ROADMAP.md").read_text(encoding="utf-8"))
        self.assertFalse((self.target / "changes.log").exists())
        self.assertFalse((self.target / "docs/WORKFLOW-DIRECTION.md").exists())
        repaired = self.snapshot()
        self.assertEqual(0, self.install("--repair-template-context").returncode)
        self.assertEqual(repaired, self.snapshot())
        self.assertIn("No phases yet", command(sys.executable, ".ai/runtime/phase.py", "status", cwd=self.target))

    def test_repair_handles_unmarked_old_entry_and_preserves_custom_history(self):
        self.seed_legacy_context()
        (self.target / "changes.log").write_bytes(b"Actual product release history\n")
        result = self.install("--repair-template-context")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("reusable engineering workflow template", (self.target / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual(b"Actual product release history\n", (self.target / "changes.log").read_bytes())

    def test_edited_legacy_instruction_block_requires_reconciliation(self):
        self.seed_legacy_context(appended=True)
        agent = self.target / "AGENTS.md"
        agent.write_bytes(agent.read_bytes().replace(b"Keep the adopting", b"CUSTOM: Keep the adopting"))
        before = self.snapshot()
        result = self.install("--repair-template-context")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("reconcile", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_installed_guidance_links_resolve_in_the_destination(self):
        import test_workflow_links

        self.target.mkdir()
        (self.target / "README.md").write_text("# Existing product\n", encoding="utf-8")
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        with patch.object(test_workflow_links, "ROOT", self.target):
            test_workflow_links.WorkflowNavigationTests().test_local_guidance_links_resolve_with_portable_case()

    def test_conflicts_abort_before_any_copy(self):
        (self.target / ".ai").mkdir(parents=True)
        (self.target / ".ai/RULES.md").write_text("Custom engineering rules")
        (self.target / "AGENTS.md").write_text("Keep instructions")
        before = self.snapshot()
        result = self.install()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("RULES.md", result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.target / ".git").exists())

    def test_file_as_parent_aborts_before_any_copy(self):
        self.target.mkdir()
        (self.target / "docs").write_text("Existing file")
        before = self.snapshot()
        result = self.install()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, self.snapshot())

    def test_non_utf8_append_targets_are_preserved_and_rejected_before_copy(self):
        self.target.mkdir()
        for name in ("AGENTS.md", ".gitignore"):
            with self.subTest(name=name):
                path = self.target / name
                path.write_bytes("Existing Windows text\n".encode("utf-16"))
                before = self.snapshot()
                result = self.install()
                self.assertNotEqual(0, result.returncode)
                self.assertIn("must be UTF-8", result.stderr)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.target / ".git").exists())
                path.unlink()

    def test_symlink_is_not_followed(self):
        self.target.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        try:
            (self.target / ".ai").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Host does not permit creating symlinks")
        result = self.install()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("linked path", result.stderr)
        self.assertEqual([], list(outside.iterdir()))

    def test_bad_ref_leaves_target_absent(self):
        result = self.install("--ref", "nonexistent-installer-test-ref")
        self.assertNotEqual(0, result.returncode)
        self.assertFalse(self.target.exists())

    @unittest.skipUnless(os.name == "nt", "Windows junction behavior")
    def test_windows_junction_is_not_followed(self):
        self.target.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        command("cmd", "/c", "mklink", "/J", str(self.target / ".ai"), str(outside))
        result = self.install()
        self.assertNotEqual(0, result.returncode)
        self.assertEqual([], list(outside.iterdir()))

    @unittest.skipUnless(os.name == "nt", "Windows short-path aliases")
    def test_windows_short_path_alias_is_accepted(self):
        import ctypes
        from ctypes import wintypes

        long_parent = self.base / "Long Installer Directory Name"
        long_parent.mkdir()
        get_short_path = ctypes.WinDLL("kernel32", use_last_error=True).GetShortPathNameW
        get_short_path.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        get_short_path.restype = wintypes.DWORD
        buffer = ctypes.create_unicode_buffer(32768)
        length = get_short_path(str(long_parent), buffer, len(buffer))
        self.assertGreater(length, 0, ctypes.get_last_error())
        if Path(buffer.value) == long_parent:
            self.skipTest("Filesystem does not generate short-path aliases")
        self.target = Path(buffer.value) / "new project"
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        canonical = long_parent.resolve() / "new project"
        self.assertTrue((canonical / ".ai/runtime/phase.py").is_file())
        self.assertEqual(canonical, Path(command("git", "rev-parse", "--show-toplevel", cwd=canonical).strip()).resolve())

    def test_rejects_subdirectory_but_accepts_linked_worktree(self):
        command("git", "init", "--quiet", str(self.base))
        command("git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "commit", "--allow-empty", "--quiet", "-m", "Initial", cwd=self.base)
        result = self.install()
        self.assertNotEqual(0, result.returncode)
        self.assertIn("inside another repository", result.stderr)
        command("git", "worktree", "add", "-b", "codex/setup", str(self.target), cwd=self.base)
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((self.target / ".git").is_file())


if __name__ == "__main__":
    unittest.main()
