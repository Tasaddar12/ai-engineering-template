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
    return subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", capture_output=True, check=True).stdout


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
                               "--skip-deps", *extra], text=True, encoding="utf-8", capture_output=True)

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
        status = command(sys.executable, ".codex/runtime/phase.py", "status", cwd=self.target)
        self.assertIn("No phases yet", status)
        self.assertIn("Onboarding pending", (self.target / ".planning/PROJECT.md").read_text(encoding="utf-8"))
        for omitted in ("README.md", "tests", ".github", ".planning/maintenance", ".ai-venv",
                        "docs", ".ai/install-assets",
                        ".planning/phases/99-source", ".planning/specs/SPEC-source.md",
                        ".planning/decisions/ADR-source.md", ".planning/codebase/source-map.md"):
            self.assertFalse((self.target / omitted).exists(), omitted)
        self.assertEqual([], list(self.target.glob("*.log")))
        for name in ("AGENTS.md", ".codex/RULES.md", ".codex/README.md", ".planning/PROJECT.md",
                     ".planning/REQUIREMENTS.md", ".planning/ROADMAP.md", ".planning/STATE.md"):
            body = (self.target / name).read_text(encoding="utf-8")
            for source_claim in ("This repository is a reusable engineering workflow template",
                                 "This is a reusable template", "CHANGEME", "AUTH-01", "Critical Fix"):
                self.assertNotIn(source_claim, body, name)
        self.assertTrue((self.target / ".agents/skills/codebase-recon/SKILL.md").is_file())
        self.assertTrue((self.target / ".codex/workflows/install.md").is_file())
        self.assertTrue((self.target / ".codex/workflows/onboard.md").is_file())
        self.assertTrue((self.target / ".codex/workflows/goal-plan.md").is_file())
        self.assertFalse((self.target / ".ai").exists())
        self.assertIn(".codex/guides/AGENT-SKILLS.md", (self.target / "AGENTS.md").read_text())
        guide = (self.target / ".codex/workflows/install.md").read_text(encoding="utf-8")
        self.assertIn("/main/.ai/install.py", guide)
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

    def test_host_profiles_install_complete_selected_workflow(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / (host + " project")
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                namespace = "." + host
                other = ".claude" if host == "codex" else ".codex"
                entry = "AGENTS.md" if host == "codex" else "CLAUDE.md"
                self.assertFalse((self.target / ".ai").exists())
                self.assertFalse((self.target / other).exists())
                self.assertFalse((self.target / ("CLAUDE.md" if host == "codex" else "AGENTS.md")).exists())
                for relative in ("RULES.md", "runtime/phase.py", "roles/coder.md",
                                 "workflows/onboard.md", "templates/context.md", "skills/codebase-recon/SKILL.md"):
                    self.assertTrue((self.target / namespace / relative).is_file(), relative)
                body = (self.target / entry).read_text(encoding="utf-8")
                self.assertIn(namespace + "/RULES.md", body)
                self.assertNotIn("@AGENTS.md", body)
                config = (self.target / ".planning/config.yaml").read_text(encoding="utf-8")
                self.assertEqual(host == "claude", "claude_worker.py" in config)
                self.assertNotIn(".ai/", config)
                self.assertIn("No phases yet", command(sys.executable, namespace + "/runtime/phase.py", "status", cwd=self.target))
                self.assertIn(namespace + "-venv/", (self.target / ".gitignore").read_text())
                if host == "codex":
                    canonical = list((self.target / namespace / "skills").glob("*/SKILL.md"))
                    wrappers = list((self.target / ".agents/skills").glob("*/SKILL.md"))
                    self.assertEqual(len(canonical), len(wrappers))
                    for wrapper in wrappers:
                        original = self.target / namespace / "skills" / wrapper.parent.name / "SKILL.md"
                        wrapped = wrapper.read_text(encoding="utf-8")
                        full = original.read_text(encoding="utf-8")
                        self.assertEqual(full.split("---", 2)[1], wrapped.split("---", 2)[1])
                        target = wrapped.split("](", 1)[1].split(")", 1)[0]
                        self.assertEqual(original.resolve(), (wrapper.parent / target).resolve())
                        self.assertGreater(len(full), len(wrapped))
                else:
                    self.assertFalse((self.target / ".agents").exists())

    def test_installed_runtime_creates_phase_from_native_templates(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                command("git", "config", "user.name", "Installer Test", cwd=self.target)
                command("git", "config", "user.email", "test@example.invalid", cwd=self.target)
                command("git", "add", ".", cwd=self.target)
                command("git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "--quiet", "-m", "Install workflow", cwd=self.target)
                worktree = self.target / ".worktrees/phase"
                command("git", "worktree", "add", "-b", "codex/phase", str(worktree), cwd=self.target)
                runtime = "." + host + "/runtime/phase.py"
                command(sys.executable, runtime, "new", "example", "--title", "Installed runtime", cwd=worktree)
                context = worktree / ".planning/phases/01-example/01-CONTEXT.md"
                self.assertIn("<domain>", context.read_text(encoding="utf-8"))
                self.assertIn("01-example", command(sys.executable, runtime, "status", cwd=worktree))
                self.assertFalse((worktree / ".ai").exists())
                self.assertFalse((self.target / ".planning/phases/01-example").exists())

    def test_selected_host_preserves_settings_instructions_and_worker_routes(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                (self.target / ".claude").mkdir(parents=True)
                (self.target / ".codex").mkdir()
                settings = {"permissions": {"deny": ["Read(.env)"]}, "disableAllHooks": False,
                            "hooks": {"PreToolUse": [{"matcher": "Write", "hooks": [
                                {"type": "command", "command": "echo custom"}]}]}}
                name = ".codex/hooks.json" if host == "codex" else ".claude/settings.json"
                (self.target / name).write_text(json.dumps(settings), encoding="utf-8")
                personal = b'{"model":"personal-local-choice"}\n'
                (self.target / ".claude/settings.local.json").write_bytes(personal)
                codex_config = b'model = "existing-model"\n[features]\nhooks = false\n'
                (self.target / ".codex/config.toml").write_bytes(codex_config)
                prose = b"# Product instructions\r\nPreserve this context.\r\n"
                entry = "AGENTS.md" if host == "codex" else "CLAUDE.md"
                (self.target / entry).write_bytes(prose)
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                merged = json.loads((self.target / name).read_text())
                self.assertEqual(settings["permissions"], merged["permissions"])
                self.assertIn(settings["hooks"]["PreToolUse"][0], merged["hooks"]["PreToolUse"])
                self.assertEqual(2, len(merged["hooks"]["PreToolUse"]))
                self.assertTrue((self.target / entry).read_bytes().startswith(prose))
                (self.target / ".planning/config.yaml").write_text("existing: project worker routes\n")
                before = self.snapshot()
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(before, self.snapshot())
                self.assertEqual(codex_config, (self.target / ".codex/config.toml").read_bytes())
                self.assertEqual(personal, (self.target / ".claude/settings.local.json").read_bytes())

    def test_switching_installed_host_requires_migration_without_partial_copy(self):
        for host, other in (("codex", "claude"), ("claude", "codex")):
            with self.subTest(host=host):
                self.target = self.base / host
                self.assertEqual(0, self.install("--host", host).returncode)
                before = self.snapshot()
                result = self.install("--host", other)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.target / ("." + other) / "runtime").exists())

    def test_invalid_host_settings_abort_before_any_copy(self):
        for contents in ('{', '[]', '{"hooks": []}', '{"hooks": {"PreToolUse": {}}}',
                         '{"hooks": {"PreToolUse": [{"hooks": null}]}}',
                         '{"hooks": {"PreToolUse": [{"hooks": [{}]}]}}',
                         '{"hooks": {}, "hooks": {}}', '{"hooks": {}, "timeout": NaN}'):
            for host, name in (("codex", ".codex/hooks.json"), ("claude", ".claude/settings.json")):
                with self.subTest(contents=contents, name=name):
                    path = self.target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(contents, encoding="utf-8")
                    before = self.snapshot()
                    result = self.install("--host", host)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("host settings", result.stderr)
                    self.assertEqual(before, self.snapshot())
                    self.assertFalse((self.target / ".git").exists())
                    path.unlink()

    def test_customized_host_registration_and_entry_require_reconciliation(self):
        for host, setting, entry in (("codex", ".codex/hooks.json", "AGENTS.md"),
                                     ("claude", ".claude/settings.json", "CLAUDE.md")):
            self.target = self.base / host
            self.assertEqual(0, self.install("--host", host).returncode)
            for name in (setting, entry):
                with self.subTest(host=host, name=name):
                    path = self.target / name
                    original = path.read_bytes()
                    modified = (original.replace(b'"timeout": 10', b'"timeout": 99')
                                if name.endswith("json") else original.replace(b"RULES.md", b"OTHER.md"))
                    self.assertNotEqual(original, modified)
                    path.write_bytes(modified)
                    before = self.snapshot()
                    result = self.install("--host", host)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("reconcile", result.stderr)
                    self.assertEqual(before, self.snapshot())
                    path.write_bytes(original)

    def test_no_hooks_skips_registration_without_removing_existing_hooks(self):
        for host, name in (("codex", ".codex/hooks.json"), ("claude", ".claude/settings.json")):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host, "--no-hooks", "--dry-run")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse(self.target.exists())
                self.assertNotIn("write " + name, result.stdout)
                result = self.install("--host", host, "--no-hooks")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertTrue((self.target / ("." + host) / "runtime/phase.py").exists())
                self.assertFalse((self.target / name).exists())
                self.assertEqual(0, self.install("--host", host).returncode)
                before = self.snapshot()
                self.assertEqual(0, self.install("--host", host, "--no-hooks").returncode)
                self.assertEqual(before, self.snapshot())

    def test_registered_hooks_execute_from_installed_linked_worktree_subdirectory(self):
        for host, name in (("codex", ".codex/hooks.json"), ("claude", ".claude/settings.json")):
            self.target = self.base / (host + " projet caf\u00e9 \u65e5\u672c\u8a9e")
            result = self.install("--host", host)
            self.assertEqual(0, result.returncode, result.stderr)
            command("git", "add", ".", cwd=self.target)
            command("git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                    "commit", "--quiet", "-m", "Installed host", cwd=self.target)
            worktree = self.target / ".worktrees/assigned space"
            command("git", "worktree", "add", "-b", "codex/installed", str(worktree), cwd=self.target)
            cwd = worktree / "sub directory"
            cwd.mkdir()
            environment = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.target))
            settings = json.loads((worktree / name).read_text(encoding="utf-8"))
            for event, destination in (("PreToolUse", self.target / "outside.txt"),
                                       ("PreToolUse", worktree / "inside.txt"),
                                       ("PostToolUse", worktree / ("." + host) / "RULES.md")):
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
                                              input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                              capture_output=True)
                    self.assertEqual(0, observed.returncode, observed.stderr)
                    if destination == worktree / "inside.txt":
                        self.assertEqual(b"", observed.stdout.strip())
                    else:
                        warning = json.loads(observed.stdout)
                        self.assertTrue(warning["systemMessage"])
                        self.assertNotIn(b"permissionDecision", observed.stdout)
                        if event == "PostToolUse":
                            self.assertIn("." + host + "/RULES.md", warning["systemMessage"])

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
        self.assertTrue((self.target / ".codex/runtime/phase.py").is_file())

    def test_git_line_ending_changes_do_not_duplicate_or_conflict_with_context(self):
        self.target.mkdir()
        (self.target / "AGENTS.md").write_bytes(b"# Product instructions\n")
        self.assertEqual(0, self.install().returncode)
        for name in ("AGENTS.md", ".gitignore", ".codex/RULES.md", ".codex/guides/ARTIFACT-GUIDE.md"):
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
        (self.target / ".codex/RULES.md").write_bytes(legacy[".ai/RULES.md"])
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
        self.assertNotIn("This is a reusable template", (self.target / ".codex/RULES.md").read_text(encoding="utf-8"))
        self.assertEqual(custom, (self.target / ".planning/PROJECT.md").read_bytes())
        self.assertNotIn("AUTH-01", (self.target / ".planning/REQUIREMENTS.md").read_text(encoding="utf-8"))
        self.assertNotIn("Critical Fix", (self.target / ".planning/ROADMAP.md").read_text(encoding="utf-8"))
        self.assertEqual([], list(self.target.glob("*.log")))
        self.assertFalse((self.target / "docs/WORKFLOW-DIRECTION.md").exists())
        self.assertEqual([], list((self.target / "docs").rglob("*.md")))
        repaired = self.snapshot()
        self.assertEqual(0, self.install("--repair-template-context").returncode)
        self.assertEqual(repaired, self.snapshot())
        self.assertIn("No phases yet", command(sys.executable, ".codex/runtime/phase.py", "status", cwd=self.target))

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

    def test_installed_guidance_links_resolve_in_both_destinations(self):
        import test_workflow_links

        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                with patch.object(test_workflow_links, "ROOT", self.target.resolve()):
                    paths = list(test_workflow_links.guidance_files())
                    self.assertTrue(any(("." + host) in path.parts for path in paths))
                    test_workflow_links.WorkflowNavigationTests().test_local_guidance_links_resolve_with_portable_case()
                guide = (self.target / ("." + host) / "workflows/install.md").read_text(encoding="utf-8")
                self.assertIn("/main/.ai/install.py", guide)

    def test_existing_ai_is_preserved_and_requires_explicit_migration(self):
        (self.target / ".ai/runtime").mkdir(parents=True)
        (self.target / ".ai/runtime/custom.py").write_text("# Valuable custom workflow\n")
        for host in ("codex", "claude"):
            for repair in ((), ("--repair-template-context",)):
                with self.subTest(host=host, repair=repair):
                    before = self.snapshot()
                    result = self.install("--host", host, *repair)
                    self.assertNotEqual(0, result.returncode)
                    self.assertEqual(before, self.snapshot())
                    self.assertFalse((self.target / ".git").exists())

    def test_original_ai_release_migrates_only_with_explicit_repair(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                for name, content in self.legacy.items():
                    if name.startswith(".ai/") or name == "AGENTS.md":
                        path = self.target / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(content)
                before = self.snapshot()
                result = self.install("--host", host)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual(before, self.snapshot())
                result = self.install("--host", host, "--repair-template-context", "--dry-run")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(before, self.snapshot())
                result = self.install("--host", host, "--repair-template-context")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse((self.target / ".ai").exists())
                self.assertIn("No phases yet", command(sys.executable, "." + host + "/runtime/phase.py", "status", cwd=self.target))

    def test_conflicts_abort_before_any_copy(self):
        (self.target / ".codex").mkdir(parents=True)
        (self.target / ".codex/RULES.md").write_text("Custom engineering rules")
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
        self.assertTrue((canonical / ".codex/runtime/phase.py").is_file())
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
