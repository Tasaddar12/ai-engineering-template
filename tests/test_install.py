"""Exercise the downloaded installer against real Git sources and target projects."""

from pathlib import Path
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import yaml


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / ".ai/install.py"
spec = importlib.util.spec_from_file_location("workflow_installer", INSTALLER)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def command(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", capture_output=True, check=True).stdout


def read_settings(path):
    content = path.read_text(encoding="utf-8")
    return tomllib.loads(content) if path.suffix == ".toml" else json.loads(content)


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

    def test_installed_runtime_answers_its_verb_contract(self):
        """The installed runtime resolves its own namespace and returns pure results."""
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                runtime = "." + host + "/runtime/phase.py"
                identity = json.loads(command(sys.executable, runtime, "query",
                                              "runtime-identity", cwd=self.target))
                self.assertTrue(identity["ok"])
                self.assertEqual("ai-phase-runtime", identity["packageName"])
                listed = json.loads(command(sys.executable, runtime, "query", "phases.list",
                                            cwd=self.target))
                self.assertTrue(listed["ok"])
                self.assertEqual([], listed["phases"])
                # An expected failure is a result, not a traceback.
                failed = subprocess.run([sys.executable, runtime, "query", "roadmap.get-phase", "9"],
                                        cwd=self.target, text=True, encoding="utf-8",
                                        capture_output=True)
                self.assertEqual(1, failed.returncode)
                self.assertNotIn("Traceback", failed.stderr)
                self.assertEqual("phase-not-found", json.loads(failed.stdout)["code"])

    def test_new_project_starts_runtime_and_omits_template_history(self):
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn(self.revision, result.stdout)
        self.assertIn("human must review and commit", result.stdout)
        self.assertEqual(self.target.resolve(), Path(command("git", "rev-parse", "--show-toplevel", cwd=self.target).strip()).resolve())
        self.assertEqual("", command("git", "remote", cwd=self.target))
        listed = json.loads(command(sys.executable, ".codex/runtime/phase.py", "query",
                                    "phases.list", cwd=self.target))
        self.assertEqual([], listed["phases"])
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
        # Capture and milestone destinations exist before the first todo is written.
        for scaffold in (".planning/todos/README.md", ".planning/todos/pending/.gitkeep",
                         ".planning/todos/completed/.gitkeep", ".planning/milestones/.gitkeep"):
            self.assertTrue((self.target / scaffold).is_file(), scaffold)
        self.assertTrue((self.target / ".agents/skills/onboard/SKILL.md").is_file())
        self.assertTrue((self.target / ".codex/commands/install.md").is_file())
        self.assertTrue((self.target / ".codex/commands/onboard.md").is_file())
        self.assertTrue((self.target / ".codex/commands/new-milestone.md").is_file())
        self.assertFalse((self.target / ".ai").exists())
        self.assertIn(".agents/skills/", (self.target / "AGENTS.md").read_text())
        guide = (self.target / ".codex/commands/install.md").read_text(encoding="utf-8")
        self.assertIn("/main/.ai/install.py", guide)
        # Local-only workflow scratch stays out of the project's history.
        for ignored in (".codex-venv/probe.txt", ".workflow-backups/probe.txt",
                        ".planning/handoffs/sess--agent-a1.json"):
            (self.target / ignored).parent.mkdir(parents=True, exist_ok=True)
            (self.target / ignored).write_text("local")
            self.assertIn(ignored, command("git", "check-ignore", ignored, cwd=self.target))

    def test_an_older_ignore_block_gains_only_the_missing_rules(self):
        """A project installed before `.planning/handoffs/` was a rule carries the
        older block. Installing again adds that one rule, not a second copy of
        every rule the project already has."""
        self.target.mkdir()
        older = ("/build\n\n# AI engineering workflow (local only)\n.codex-venv/\n"
                 ".workflow-backups/\n__pycache__/\n*.pyc\n")
        (self.target / ".gitignore").write_bytes(older.encode())
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        text = (self.target / ".gitignore").read_text(encoding="utf-8")
        self.assertTrue(text.startswith(older))
        lines = text.splitlines()
        for rule in (".codex-venv/", ".workflow-backups/", "__pycache__/", "*.pyc",
                     ".planning/handoffs/", "# AI engineering workflow (local only)"):
            self.assertEqual(1, lines.count(rule), rule)
        before = self.snapshot()
        self.assertEqual(0, self.install().returncode)
        self.assertEqual(before, self.snapshot())

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
                for relative in ("RULES.md", "runtime/phase.py", "agents/coder.md",
                                 "commands/onboard.md", "templates/context.md"):
                    self.assertTrue((self.target / namespace / relative).is_file(), relative)
                body = (self.target / entry).read_text(encoding="utf-8")
                self.assertIn(namespace + "/RULES.md", body)
                self.assertNotIn("@AGENTS.md", body)
                config = (self.target / ".planning/config.yaml").read_text(encoding="utf-8")
                self.assertIn("verification:", config)
                self.assertNotIn(".ai/", config)
                listed = json.loads(command(sys.executable, namespace + "/runtime/phase.py",
                                            "query", "phases.list", cwd=self.target))
                self.assertEqual([], listed["phases"])
                self.assertIn(namespace + "-venv/", (self.target / ".gitignore").read_text())
                skills = self.target / (".agents/skills" if host == "codex" else ".claude/skills")
                full = (skills / "onboard/SKILL.md").read_text(encoding="utf-8")
                self.assertIn("<objective>", full)
                self.assertNotIn("Read and follow the complete skill at", full)
                self.assertFalse((self.target / namespace / "roles").exists())
                for workflow in ("execute-phase.md", "plan-phase.md", "onboard.md"):
                    self.assertTrue((self.target / namespace / "workflows" / workflow).is_file(),
                                    workflow)
                if host == "codex":
                    self.assertFalse((self.target / ".codex/skills").exists())
                    self.assertFalse((self.target / ".codex/hooks.json").exists())
                else:
                    self.assertFalse((self.target / ".agents").exists())

    def test_native_agent_models_and_direct_roles_install_without_hooks(self):
        astra = {"coordinator", "researcher", "phase-preparer", "coder"}
        sol = {"debugger", "code-reviewer", "verifier", "phase-checker"}
        roles = {"coordinator", "codebase-mapper", "researcher", "phase-preparer",
                 "phase-checker", "coder", "doc-writer", "doc-verifier",
                 "integration-checker", "code-reviewer", "debugger", "verifier"}
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host, "--no-hooks")
                self.assertEqual(0, result.returncode, result.stderr)
                agents = self.target / ("." + host) / "agents"
                methods = {}
                for role in agents.glob("*.md"):
                    text = role.read_text(encoding="utf-8")
                    if text.startswith("---\n"):
                        metadata = yaml.safe_load(text.split("---", 2)[1])
                        methods[metadata["name"]] = (role, metadata)
                self.assertEqual(roles, set(methods))
                for name, (role, metadata) in methods.items():
                    self.assertNotIn("model", metadata, name)
                    # Full source methods survive relocation, not compact substitutes.
                    self.assertEqual(installer.render_asset(".ai/agents/" + role.name,
                        (self.source / ".ai/agents" / role.name).read_bytes(), host),
                        role.read_bytes())
                if host == "codex":
                    self.assertEqual(roles, {p.stem for p in agents.glob("*.toml")})
                    for definition in agents.glob("*.toml"):
                        config = tomllib.loads(definition.read_text(encoding="utf-8"))
                        name = config["name"]
                        self.assertEqual(definition.stem, name)
                        self.assertEqual(methods[name][1]["description"], config["description"])
                        expected = ("gpt-6-astra" if name in astra else
                                    "gpt-6-sol" if name in sol else "gpt-6-luna")
                        self.assertEqual(expected, config["model"])
                        checkers = {"doc-verifier", "integration-checker"}
                        effort = "medium" if name in checkers else "high"
                        self.assertEqual(effort, config["model_reasoning_effort"])
                        role_path = ".codex/agents/" + name + ".md"
                        self.assertIn(role_path, config["developer_instructions"])
                        self.assertNotIn(".ai/", config["developer_instructions"])
                        self.assertTrue((self.target / role_path).is_file())
                else:
                    self.assertEqual([], list(agents.glob("*.toml")))
                before = self.snapshot()
                repeated = self.install("--host", host, "--no-hooks")
                self.assertEqual(0, repeated.returncode, repeated.stderr)
                self.assertEqual(before, self.snapshot())

    def test_custom_native_agent_is_not_overwritten(self):
        for host, suffix in (("codex", "toml"), ("claude", "md")):
            with self.subTest(host=host):
                self.target = self.base / host
                self.assertEqual(0, self.install("--host", host).returncode)
                role = self.target / ("." + host) / "agents" / ("coder." + suffix)
                # A comment is valid in both formats, so the edit stays representative.
                role.write_text(role.read_text(encoding="utf-8") + "\n# local customization\n",
                                encoding="utf-8")
                before = self.snapshot()
                result = self.install("--host", host)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("coder." + suffix, result.stderr)
                self.assertEqual(before, self.snapshot())

    def test_installed_runtime_creates_phase_from_native_templates(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                command("git", "config", "user.name", "Installer Test", cwd=self.target)
                command("git", "config", "user.email", "test@example.invalid", cwd=self.target)
                # Git must finish writes before this temporary repository is removed.
                command("git", "config", "maintenance.autoDetach", "false", cwd=self.target)
                command("git", "config", "gc.autoDetach", "false", cwd=self.target)
                command("git", "add", ".", cwd=self.target)
                command("git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                        "commit", "--quiet", "-m", "Install workflow", cwd=self.target)
                worktree = self.target / ".worktrees/phase"
                command("git", "worktree", "add", "-b", "codex/phase", str(worktree), cwd=self.target)
                runtime = "." + host + "/runtime/phase.py"
                added = json.loads(command(sys.executable, runtime, "query", "phase.add",
                                           "Installed runtime", "--goal", "Prove the install",
                                           cwd=worktree))
                self.assertTrue(added["ok"])
                self.assertEqual("01", added["padded"])
                self.assertEqual(".planning/phases/01-installed-runtime", added["directory"])
                self.assertTrue((worktree / added["directory"]).is_dir())
                roadmap = (worktree / ".planning/ROADMAP.md").read_text(encoding="utf-8")
                self.assertIn("### Phase 1: Installed runtime", roadmap)
                listed = json.loads(command(sys.executable, runtime, "query", "phases.list",
                                            cwd=worktree))
                self.assertEqual(["Installed runtime"],
                                 [phase["name"] for phase in listed["phases"]])
                self.assertFalse((worktree / ".ai").exists())
                self.assertFalse((self.target / ".planning/phases/01-installed-runtime").exists())

    def test_selected_host_preserves_settings_instructions_and_worker_routes(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                (self.target / ".claude").mkdir(parents=True)
                (self.target / ".codex").mkdir()
                settings = {"permissions": {"deny": ["Read(.env)"]}, "disableAllHooks": False,
                            "hooks": {"PreToolUse": [{"matcher": "Write", "hooks": [
                                {"type": "command", "command": "echo custom"}]}]}}
                name = ".codex/config.toml" if host == "codex" else ".claude/settings.json"
                original_settings = (b'model = "existing-model"\n[features]\nhooks = false\n' + installer.hooks_toml(settings["hooks"])
                                     if host == "codex" else installer.json_bytes(settings))
                (self.target / name).write_bytes(original_settings)
                personal = b'{"model":"personal-local-choice"}\n'
                (self.target / ".claude/settings.local.json").write_bytes(personal)
                codex_config = b'model = "existing-model"\n[features]\nhooks = false\n'
                if host == "claude":
                    (self.target / ".codex/config.toml").write_bytes(codex_config)
                prose = b"# Product instructions\r\nPreserve this context.\r\n"
                entry = "AGENTS.md" if host == "codex" else "CLAUDE.md"
                (self.target / entry).write_bytes(prose)
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                merged = read_settings(self.target / name)
                if host == "claude":
                    self.assertEqual(settings["permissions"], merged["permissions"])
                else:
                    self.assertTrue((self.target / name).read_bytes().startswith(original_settings))
                # The user's own group survives verbatim, and every managed
                # group is registered alongside it rather than replacing it.
                managed = installer.hook_settings(host)["hooks"]
                for event, groups in managed.items():
                    for group in groups:
                        self.assertIn(group, merged["hooks"][event])
                self.assertIn(settings["hooks"]["PreToolUse"][0],
                              merged["hooks"]["PreToolUse"])
                self.assertTrue((self.target / entry).read_bytes().startswith(prose))
                (self.target / ".planning/config.yaml").write_text("existing: project worker routes\n")
                before = self.snapshot()
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(before, self.snapshot())
                if host == "claude":
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
            for host, name in (("claude", ".claude/settings.json"),):
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

    def test_invalid_codex_toml_aborts_before_any_copy(self):
        for contents in ('[', 'hooks = []', '[hooks]\nPreToolUse = {}',
                         'model = "one"\nmodel = "two"',
                         '[[hooks.PreToolUse]]\nhooks = [{}]'):
            with self.subTest(contents=contents):
                path = self.target / ".codex/config.toml"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(contents, encoding="utf-8")
                before = self.snapshot()
                result = self.install()
                self.assertNotEqual(0, result.returncode)
                self.assertIn("host settings", result.stderr)
                self.assertEqual(before, self.snapshot())

    def test_customized_host_registration_and_entry_require_reconciliation(self):
        for host, setting, entry in (("codex", ".codex/config.toml", "AGENTS.md"),
                                     ("claude", ".claude/settings.json", "CLAUDE.md")):
            self.target = self.base / host
            self.assertEqual(0, self.install("--host", host).returncode)
            for name in (setting, entry):
                with self.subTest(host=host, name=name):
                    path = self.target / name
                    original = path.read_bytes()
                    modified = (original.replace(b'"timeout": 10', b'"timeout": 99')
                                if name.endswith("json") else original.replace(b"timeout = 10", b"timeout = 99")
                                if name.endswith("toml") else original.replace(b"RULES.md", b"OTHER.md"))
                    self.assertNotEqual(original, modified)
                    path.write_bytes(modified)
                    before = self.snapshot()
                    result = self.install("--host", host)
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("reconcile", result.stderr)
                    self.assertEqual(before, self.snapshot())
                    path.write_bytes(original)

    def test_no_hooks_skips_registration_without_removing_existing_hooks(self):
        for host, name in (("codex", ".codex/config.toml"), ("claude", ".claude/settings.json")):
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

    def launcher_argv(self, host, handler):
        """The command line the host would actually run for one registration."""
        if host == "codex" and os.name == "nt":
            return ["powershell", "-NoProfile", "-Command", handler["commandWindows"]]
        if host == "codex":
            return ["sh", "-c", handler["command"]]
        bash = shutil.which("bash")
        if os.name == "nt":
            git_bash = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
            if git_bash.is_file():
                bash = str(git_bash)
        self.assertIsNotNone(bash, "Claude hooks require Bash (Git Bash on Windows)")
        return [bash, "-c", handler["command"]]

    def test_registered_hooks_execute_from_installed_subdirectory(self):
        """Every managed hook resolves the project root from a nested directory."""
        for host, name in (("codex", ".codex/config.toml"), ("claude", ".claude/settings.json")):
            self.target = self.base / (host + " projet café 日本語")
            result = self.install("--host", host)
            self.assertEqual(0, result.returncode, result.stderr)
            cwd = self.target / "sub directory"
            cwd.mkdir()
            environment = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.target))
            settings = read_settings(self.target / name)
            destination = self.target / ("." + host) / "RULES.md"
            with self.subTest(host=host, destination=destination):
                argv = self.launcher_argv(host, settings["hooks"]["PostToolUse"][0]["hooks"][0])
                tool_input = ({"command": f"*** Begin Patch\n*** Add File: {destination.as_posix()}\n+x\n*** End Patch"}
                              if host == "codex" else {"file_path": str(destination)})
                payload = {"cwd": str(cwd), "hook_event_name": "PostToolUse",
                           "tool_name": "apply_patch" if host == "codex" else "Write",
                           "tool_input": tool_input}
                observed = subprocess.run(argv, cwd=cwd, env=environment,
                                          input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                          capture_output=True)
                self.assertEqual(0, observed.returncode, observed.stderr)
                self.assertNotIn(b"permissionDecision", observed.stdout)
                self.assertIn(b"NOTICE", observed.stdout)
                self.assertIn(("." + host + "/RULES.md").encode(), observed.stdout)

            # The dispatch guard is the only managed hook that returns a
            # permission decision, so proving it launches from the installed
            # path matters more than for an advisory one: a registration that
            # silently fails to run is an isolation requirement that is not
            # enforced at all.
            groups = settings["hooks"]["PreToolUse"]
            dispatch = [group for group in groups if "Agent" in group.get("matcher", "")]
            self.assertEqual(1, len(dispatch),
                             "exactly one managed Agent/Task registration is expected")
            with self.subTest(host=host, hook="worktree-guard dispatch"):
                argv = self.launcher_argv(host, dispatch[0]["hooks"][0])
                payload = {"cwd": str(cwd), "hook_event_name": "PreToolUse",
                           "tool_name": "Agent",
                           "tool_input": {"subagent_type": "coder", "description": "x"}}
                observed = subprocess.run(argv, cwd=cwd, env=environment,
                                          input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                          capture_output=True)
                self.assertEqual(2, observed.returncode,
                                 "an unisolated coder dispatch must be blocked: "
                                 + observed.stderr.decode("utf-8", "replace"))
                self.assertIn(b"BLOCKED", observed.stderr)
                # Same registration, isolated dispatch: must get out of the way.
                payload["tool_input"]["isolation"] = "worktree"
                observed = subprocess.run(argv, cwd=cwd, env=environment,
                                          input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                          capture_output=True)
                self.assertEqual(0, observed.returncode, observed.stderr)

    def test_claude_worktrees_are_placed_by_the_project_hook(self):
        """Claude Code would put a subagent's checkout under .claude/worktrees/;
        the project's WorktreeCreate hook puts it under the worktree root."""
        for host, name in (("claude", ".claude/settings.json"), ("codex", ".codex/config.toml")):
            with self.subTest(host=host):
                self.target = self.base / (host + " worktree hooks")
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                hooks = read_settings(self.target / name)["hooks"]
                self.assertTrue((self.target / ("." + host) / "hooks/worktree-location.sh").is_file())
                if host == "codex":
                    # Codex has no such event; its worktrees come from the runtime.
                    self.assertNotIn("WorktreeCreate", hooks)
                    self.assertNotIn("WorktreeRemove", hooks)
                    # It does record the orchestrator's transcript, which is how
                    # the handoff hook recognises it without an agent id.
                    self.assertEqual(1, len(hooks["SessionStart"]))
                    self.assertIn("/.codex/hooks/context-handoff.sh",
                                  hooks["SessionStart"][0]["hooks"][0]["command"])
                    before = self.snapshot()
                    self.assertEqual(0, self.install("--host", host).returncode)
                    self.assertEqual(before, self.snapshot(), "a rerun must not register it twice")
                    continue
                self.assertNotIn("SessionStart", hooks)
                for event, timeout in (("WorktreeCreate", 180), ("WorktreeRemove", 60)):
                    self.assertEqual(1, len(hooks[event]), event)
                    handler = hooks[event][0]["hooks"][0]
                    self.assertNotIn("matcher", hooks[event][0])
                    self.assertIn("/.claude/hooks/worktree-location.sh", handler["command"])
                    self.assertEqual(timeout, handler["timeout"])
                before = self.snapshot()
                self.assertEqual(0, self.install("--host", host).returncode)
                self.assertEqual(before, self.snapshot(), "a rerun must not register it twice")

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
        for _ in range(2):
            result = self.install()
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
                guide = (self.target / ("." + host) / "commands/install.md").read_text(encoding="utf-8")
                self.assertIn("/main/.ai/install.py", guide)

    def test_existing_ai_is_preserved_and_requires_explicit_migration(self):
        (self.target / ".ai/runtime").mkdir(parents=True)
        (self.target / ".ai/runtime/custom.py").write_text("# Valuable custom workflow\n")
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                before = self.snapshot()
                result = self.install("--host", host)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.target / ".git").exists())

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
