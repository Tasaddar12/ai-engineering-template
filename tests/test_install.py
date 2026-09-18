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

    def test_installed_summary_skeleton_satisfies_runtime_contract(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                # Fill existing slots only: adding missing keys/sections here would
                # hide the authoring defect this producer/consumer check protects.
                script = r'''
import re
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, str(Path.cwd() / sys.argv[1] / "runtime"))
from phase_records import file_template
from phase_runner import validate_summary
root = Path.cwd()
text = file_template(root, "summary.md")
for key, value in {"requirements-completed": "[R1]", "acceptance": "[A1]",
                   "documentation": "[docs/result.md]"}.items():
    text = re.sub(r"(?m)^" + key + r":.*$", key + ": " + value, text)
text = text.replace("[Tested revision or commit]", "a" * 40)
text = text.replace("[Command and scenario]", "python -m unittest tests.test_result")
text = text.replace("[Observed result, including failures or skips]", "PASS: 1 test")
summary = root / "01-01-SUMMARY.md"
summary.write_text(text, encoding="utf-8")
(root / "docs").mkdir()
(root / "docs/result.md").write_text("Verified result documentation", encoding="utf-8")
component = SimpleNamespace(id="01-01", summary=summary, data={
    "requirements": ["R1"], "acceptance": ["A1"],
    "documentation": ["docs/result.md"], "type": "execute"})
validate_summary(SimpleNamespace(root=root), component, root)
'''
                checked = subprocess.run([sys.executable, "-c", script, "." + host],
                                         cwd=self.target, text=True, encoding="utf-8",
                                         capture_output=True)
                self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)

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
        self.assertTrue((self.target / ".codex/commands/install.md").is_file())
        self.assertTrue((self.target / ".codex/commands/onboard.md").is_file())
        self.assertTrue((self.target / ".codex/commands/goal-plan.md").is_file())
        self.assertFalse((self.target / ".ai").exists())
        self.assertIn(".codex/guides/AGENT-SKILLS.md", (self.target / "AGENTS.md").read_text())
        guide = (self.target / ".codex/commands/install.md").read_text(encoding="utf-8")
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
                for relative in ("RULES.md", "runtime/phase.py", "agents/coder.md",
                                 "commands/onboard.md", "templates/context.md"):
                    self.assertTrue((self.target / namespace / relative).is_file(), relative)
                body = (self.target / entry).read_text(encoding="utf-8")
                self.assertIn(namespace + "/RULES.md", body)
                self.assertNotIn("@AGENTS.md", body)
                config = (self.target / ".planning/config.yaml").read_text(encoding="utf-8")
                self.assertEqual(host == "claude", "claude_worker.py" in config)
                self.assertNotIn(".ai/", config)
                self.assertIn("No phases yet", command(sys.executable, namespace + "/runtime/phase.py", "status", cwd=self.target))
                self.assertIn(namespace + "-venv/", (self.target / ".gitignore").read_text())
                skills = self.target / (".agents/skills" if host == "codex" else ".claude/skills")
                full = (skills / "codebase-recon/SKILL.md").read_text(encoding="utf-8")
                self.assertIn("##", full)
                self.assertNotIn("Read and follow the complete skill at", full)
                self.assertFalse((self.target / namespace / "roles").exists())
                self.assertFalse((self.target / namespace / "workflows").exists())
                if host == "codex":
                    self.assertFalse((self.target / ".codex/skills").exists())
                    self.assertFalse((self.target / ".codex/hooks.json").exists())
                else:
                    self.assertFalse((self.target / ".agents").exists())

    def test_native_agent_models_and_direct_roles_install_without_hooks(self):
        terra = {"coordinator", "researcher", "phase-preparer", "coder", "debugger"}
        roles = {"coordinator", "codebase-mapper", "researcher", "phase-preparer",
                 "phase-checker", "coder", "doc-writer", "doc-verifier",
                 "integration-checker", "code-reviewer", "debugger", "verifier"}
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host, "--no-hooks")
                self.assertEqual(0, result.returncode, result.stderr)
                installed_config = yaml.safe_load((self.target / ".planning/config.yaml").read_text(encoding="utf-8"))
                self.assertIsNone(installed_config["execution"]["claude_max_turns"])
                agents = self.target / ("." + host) / "agents"
                methods = {}
                for role in agents.glob("*.md"):
                    text = role.read_text(encoding="utf-8")
                    if text.startswith("---\n"):
                        metadata = yaml.safe_load(text.split("---", 2)[1])
                        methods[metadata["name"]] = (role, metadata)
                self.assertEqual(roles, set(methods))
                for name, (role, metadata) in methods.items():
                    self.assertEqual("sonnet", metadata["model"], name)
                    self.assertNotIn("maxTurns", metadata, name)
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
                        expected = "gpt-5.6-terra" if name in terra else "gpt-5.6-luna"
                        self.assertEqual(expected, config["model"])
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
                role.write_text(role.read_text(encoding="utf-8").replace(
                    'model = "gpt-5.6-terra"' if host == "codex" else 'model: sonnet',
                    'model = "chosen-model"' if host == "codex" else 'model: opus'),
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
                self.assertIn(settings["hooks"]["PreToolUse"][0], merged["hooks"]["PreToolUse"])
                self.assertEqual(2, len(merged["hooks"]["PreToolUse"]))
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

    def test_registered_hooks_execute_from_installed_linked_worktree_subdirectory(self):
        for host, name in (("codex", ".codex/config.toml"), ("claude", ".claude/settings.json")):
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
            settings = read_settings(worktree / name)
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
                        self.assertNotIn(b"permissionDecision", observed.stdout)
                        if event == "PostToolUse":
                            self.assertIn(b"NOTICE", observed.stdout)
                            self.assertIn(("." + host + "/RULES.md").encode(), observed.stdout)
                        else:
                            self.assertTrue(json.loads(observed.stdout)["systemMessage"])

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
