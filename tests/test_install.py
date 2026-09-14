"""Exercise the downloaded installer against real Git sources and target projects."""

from pathlib import Path
import importlib.util
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
spec = importlib.util.spec_from_file_location("workflow_installer", INSTALLER)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


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
        for name in ("AGENTS.md", "README.md", ".gitattributes"):
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
        cls.legacy = installer.load_legacy(cls.source, installer.SOURCE)

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
                        "docs", ".ai/install-assets",
                        ".planning/phases/99-source", ".planning/specs/SPEC-source.md",
                        ".planning/decisions/ADR-source.md", ".planning/codebase/source-map.md"):
            self.assertFalse((self.target / omitted).exists(), omitted)
        self.assertEqual([], list(self.target.glob("*.log")))
        for name in ("AGENTS.md", ".ai/RULES.md", ".ai/README.md", ".planning/PROJECT.md",
                     ".planning/REQUIREMENTS.md", ".planning/ROADMAP.md", ".planning/STATE.md"):
            body = (self.target / name).read_text(encoding="utf-8")
            for source_claim in ("This repository is a reusable engineering workflow template",
                                 "This is a reusable template", "CHANGEME", "AUTH-01", "Critical Fix"):
                self.assertNotIn(source_claim, body, name)
        self.assertTrue((self.target / ".agents/skills/codebase-recon/SKILL.md").is_file())
        self.assertTrue((self.target / ".ai/commands/install.md").is_file())
        self.assertTrue((self.target / ".ai/commands/onboard.md").is_file())
        self.assertTrue((self.target / ".ai/commands/goal-plan.md").is_file())
        # Core instructions must work as shipped, without rewritten links or docs exports.
        for name in (".ai/commands/install.md", ".ai/commands/onboard.md", ".ai/commands/goal-plan.md"):
            self.assertEqual((self.source / name).read_bytes().replace(b"\r\n", b"\n"),
                             (self.target / name).read_bytes().replace(b"\r\n", b"\n"))
        self.assertIn(".ai/guides/AGENT-SKILLS.md", (self.target / "AGENTS.md").read_text())
        (self.target / ".worktrees").mkdir()
        (self.target / ".worktrees/local.txt").write_text("local")
        self.assertIn(".worktrees/local.txt", command("git", "check-ignore", ".worktrees/local.txt", cwd=self.target))

    def test_existing_repository_preserves_files_history_remote_and_reruns(self):
        self.target.mkdir()
        original = {"README.md": b"Existing product\n", "app.py": b"print('hello')\n",
                    "AGENTS.md": b"# Existing instructions\r\nKeep these.\r\n", ".gitignore": b"/build\r\n",
                    "docs/INSTALL.md": b"Product setup instructions\r\n",
                    "docs/architecture.md": b"Actual application architecture\n"}
        for name, content in original.items():
            (self.target / name).parent.mkdir(parents=True, exist_ok=True)
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
        self.assertEqual({name: content for name, content in original.items() if name.startswith("docs/")},
                         {p.relative_to(self.target).as_posix(): p.read_bytes()
                          for p in (self.target / "docs").rglob("*") if p.is_file()})
        self.assertEqual(b"uncommitted work\n", (self.target / "app.py").read_bytes())
        for name in ("AGENTS.md", ".gitignore"):
            self.assertTrue((self.target / name).read_bytes().startswith(original[name]))
        before = self.snapshot()
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(head, command("git", "rev-parse", "HEAD", cwd=self.target))
        self.assertIn("existing.git", command("git", "remote", "get-url", "origin", cwd=self.target))

    def test_host_profiles_install_only_selected_native_integrations(self):
        for host in ("codex", "claude", "both"):
            with self.subTest(host=host):
                self.target = self.base / (host + " project")
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(host != "claude", (self.target / ".codex/hooks.json").exists())
                self.assertEqual(host != "codex", (self.target / ".claude/settings.json").exists())
                self.assertEqual(host != "codex", (self.target / "CLAUDE.md").exists())
                config = (self.target / ".planning/config.yaml").read_text(encoding="utf-8")
                self.assertEqual(host == "claude", "claude_worker.py" in config)
                self.assertIn("Onboarding pending", (self.target / ".planning/PROJECT.md").read_text())
                if host != "codex":
                    self.assertIn("@AGENTS.md", (self.target / "CLAUDE.md").read_text())
                    canonical = list((self.target / ".agents/skills").glob("*/SKILL.md"))
                    wrappers = list((self.target / ".claude/skills").glob("*/SKILL.md"))
                    self.assertEqual(len(canonical), len(wrappers))
                    for wrapper in wrappers:
                        original = self.target / ".agents/skills" / wrapper.parent.name / "SKILL.md"
                        body = wrapper.read_text(encoding="utf-8")
                        self.assertEqual(original.read_text(encoding="utf-8").split("---", 2)[1],
                                         body.split("---", 2)[1])
                        target = body.split("](", 1)[1].split(")", 1)[0]
                        self.assertEqual(original.resolve(), (wrapper.parent / target).resolve())

    def test_adding_second_host_preserves_settings_instructions_and_worker_routes(self):
        (self.target / ".claude").mkdir(parents=True)
        (self.target / ".codex").mkdir()
        settings = {"permissions": {"deny": ["Read(.env)"]}, "disableAllHooks": False,
                    "hooks": {"PreToolUse": [{"matcher": "Write", "hooks": [
                        {"type": "command", "command": "echo custom"}]}]}}
        (self.target / ".claude/settings.json").write_text(json.dumps(settings), encoding="utf-8")
        personal = b'{"model":"personal-local-choice"}\n'
        (self.target / ".claude/settings.local.json").write_bytes(personal)
        codex_config = b'model = "existing-model"\n[features]\nhooks = false\n'
        (self.target / ".codex/config.toml").write_bytes(codex_config)
        prose = b"# Product instructions\r\nPreserve this context.\r\n"
        (self.target / "CLAUDE.md").write_bytes(prose)
        self.assertEqual(0, self.install("--host", "codex").returncode)
        config = (self.target / ".planning/config.yaml").read_bytes()
        result = self.install("--host", "both")
        self.assertEqual(0, result.returncode, result.stderr)
        merged = json.loads((self.target / ".claude/settings.json").read_text())
        self.assertEqual(settings["permissions"], merged["permissions"])
        self.assertIn(settings["hooks"]["PreToolUse"][0], merged["hooks"]["PreToolUse"])
        self.assertEqual(2, len(merged["hooks"]["PreToolUse"]))
        self.assertTrue((self.target / "CLAUDE.md").read_bytes().startswith(prose))
        before = self.snapshot()
        result = self.install("--host", "claude")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(config, (self.target / ".planning/config.yaml").read_bytes())
        self.assertEqual(codex_config, (self.target / ".codex/config.toml").read_bytes())
        self.assertEqual(personal, (self.target / ".claude/settings.local.json").read_bytes())

    def test_invalid_host_settings_abort_before_any_copy(self):
        for contents in ('{', '[]', '{"hooks": []}', '{"hooks": {"PreToolUse": {}}}',
                         '{"hooks": {"PreToolUse": [{"hooks": null}]}}',
                         '{"hooks": {"PreToolUse": [{"hooks": [{}]}]}}',
                         '{"hooks": {}, "hooks": {}}', '{"hooks": {}, "timeout": NaN}'):
            for name in (".codex/hooks.json", ".claude/settings.json"):
                with self.subTest(contents=contents, name=name):
                    path = self.target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(contents, encoding="utf-8")
                    before = self.snapshot()
                    result = self.install("--host", "both")
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("host settings", result.stderr)
                    self.assertEqual(before, self.snapshot())
                    self.assertFalse((self.target / ".git").exists())
                    path.unlink()

    def test_customized_host_registration_and_claude_block_require_reconciliation(self):
        self.assertEqual(0, self.install("--host", "both").returncode)
        for name in (".codex/hooks.json", "CLAUDE.md"):
            with self.subTest(name=name):
                path = self.target / name
                original = path.read_bytes()
                path.write_bytes(original.replace(b'"timeout": 10', b'"timeout": 99')
                                 if name.endswith("json") else original.replace(b"@AGENTS.md", b"@OTHER.md"))
                before = self.snapshot()
                result = self.install("--host", "both")
                self.assertNotEqual(0, result.returncode)
                self.assertIn("reconcile", result.stderr)
                self.assertEqual(before, self.snapshot())
                path.write_bytes(original)

    def test_no_hooks_skips_registration_without_removing_existing_hooks(self):
        result = self.install("--host", "both", "--no-hooks", "--dry-run")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse(self.target.exists())
        self.assertNotIn("write .codex", result.stdout)
        self.assertNotIn("settings.json", result.stdout)
        result = self.install("--host", "both", "--no-hooks")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue((self.target / "CLAUDE.md").exists())
        self.assertFalse((self.target / ".codex").exists())
        self.assertFalse((self.target / ".claude/settings.json").exists())
        self.assertEqual(0, self.install("--host", "both").returncode)
        before = self.snapshot()
        self.assertEqual(0, self.install("--host", "both", "--no-hooks").returncode)
        self.assertEqual(before, self.snapshot())

    def test_registered_hooks_execute_from_installed_linked_worktree_subdirectory(self):
        result = self.install("--host", "both")
        self.assertEqual(0, result.returncode, result.stderr)
        command("git", "add", ".", cwd=self.target)
        command("git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "commit", "--quiet", "-m", "Installed hosts", cwd=self.target)
        worktree = self.target / ".worktrees/assigned space"
        command("git", "worktree", "add", "-b", "codex/installed", str(worktree), cwd=self.target)
        cwd = worktree / "sub directory"
        cwd.mkdir()
        environment = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.target))
        for host, name in (("codex", ".codex/hooks.json"), ("claude", ".claude/settings.json")):
            settings = json.loads((worktree / name).read_text(encoding="utf-8"))
            for event, destination in (("PreToolUse", self.target / "outside.txt"),
                                       ("PreToolUse", worktree / "inside.txt"),
                                       ("PostToolUse", worktree / ".planning/PROJECT.md")):
                with self.subTest(host=host, event=event, destination=destination):
                    handler = settings["hooks"][event][0]["hooks"][0]
                    if host == "codex" and os.name == "nt":
                        argv = ["powershell", "-NoProfile", "-Command", handler["commandWindows"]]
                    elif host == "codex":
                        argv = ["sh", "-c", handler["command"]]
                    else:
                        bash = shutil.which("bash")
                        if os.name == "nt":
                            git_bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
                            if git_bash.is_file():
                                bash = str(git_bash)
                        self.assertIsNotNone(bash, "Claude hooks require Bash (Git Bash on Windows)")
                        argv = [bash, "-c", handler["command"]]
                    tool_input = ({"command": f"*** Begin Patch\n*** Add File: {destination.as_posix()}\n+x\n*** End Patch"}
                                  if host == "codex" else {"file_path": str(destination)})
                    payload = {"cwd": str(cwd), "hook_event_name": event,
                               "tool_name": "apply_patch" if host == "codex" else "Write",
                               "tool_input": tool_input}
                    observed = subprocess.run(argv, cwd=cwd, env=environment,
                                              input=json.dumps(payload), text=True, capture_output=True)
                    self.assertEqual(0, observed.returncode, observed.stderr)
                    if destination == worktree / "inside.txt":
                        self.assertEqual("", observed.stdout.strip())
                    else:
                        warning = json.loads(observed.stdout)
                        self.assertTrue(warning["systemMessage"])
                        self.assertNotIn("permissionDecision", observed.stdout)

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
        for name in ("AGENTS.md", ".gitignore", ".ai/RULES.md", ".ai/guides/ARTIFACT-GUIDE.md"):
            path = self.target / name
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        before = self.snapshot()
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, self.snapshot())

    def seed_legacy_context(self, appended=False):
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        legacy = self.legacy
        agent = legacy["AGENTS.md"]
        if appended:
            agent = b"# Existing product guidance\r\nKeep this.\r\n\n\n<!-- ai-engineering-template -->\n" + agent + b"\nUser added this later.\r\n"
        (self.target / "AGENTS.md").write_bytes(agent)
        (self.target / ".ai/RULES.md").write_bytes(legacy[".ai/RULES.md"])
        for name, content in legacy.items():
            if ("/" not in name and name.endswith(".log")) or name.startswith("docs/"):
                path = self.target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)
        for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE"):
            (self.target / f".planning/{name}.md").write_bytes((ROOT / f".planning/{name}.md").read_bytes())

    def test_explicit_repair_replaces_old_context_and_removes_only_known_history(self):
        self.seed_legacy_context(appended=True)
        custom = b"# Actual project\nThese are confirmed product decisions.\n"
        (self.target / ".planning/PROJECT.md").write_bytes(custom)
        before = self.snapshot()
        preview = self.install("--repair-template-context", "--dry-run")
        self.assertEqual(0, preview.returncode, preview.stderr)
        for name in self.legacy:
            if "/" not in name and name.endswith(".log"):
                self.assertIn(f"remove {name}", preview.stdout)
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
        self.assertEqual([], list(self.target.glob("*.log")))
        self.assertFalse((self.target / "docs/WORKFLOW-DIRECTION.md").exists())
        self.assertEqual([], list((self.target / "docs").rglob("*.md")))
        repaired = self.snapshot()
        self.assertEqual(0, self.install("--repair-template-context").returncode)
        self.assertEqual(repaired, self.snapshot())
        self.assertIn("No phases yet", command(sys.executable, ".ai/runtime/phase.py", "status", cwd=self.target))

    def test_repair_handles_unmarked_old_entry_and_preserves_custom_history(self):
        self.seed_legacy_context()
        agent = self.target / "AGENTS.md"
        agent.write_bytes(agent.read_bytes() + b"\nKeep this later project guidance.\r\n")
        (self.target / "docs/INSTALL.md").write_bytes(b"Actual product install instructions\n")
        result = self.install("--repair-template-context")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn("reusable engineering workflow template", (self.target / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertTrue(agent.read_bytes().endswith(b"Keep this later project guidance.\r\n"))
        self.assertEqual(b"Actual product install instructions\n", (self.target / "docs/INSTALL.md").read_bytes())

    def test_edited_unmarked_legacy_instructions_are_not_silently_retained(self):
        self.seed_legacy_context()
        agent = self.target / "AGENTS.md"
        agent.write_bytes(agent.read_bytes().replace(b"Keep the adopting", b"CUSTOM: Keep the adopting"))
        before = self.snapshot()
        result = self.install("--repair-template-context")
        self.assertNotEqual(0, result.returncode)
        self.assertIn("reconcile", result.stderr)
        self.assertEqual(before, self.snapshot())

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
        # CI may expose TEMP through a Windows 8.3 alias. Compare canonical roots,
        # while the checker still audits the original link spelling and casing.
        with patch.object(test_workflow_links, "ROOT", self.target.resolve()):
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
        (self.target / ".ai").write_text("Existing file")
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
