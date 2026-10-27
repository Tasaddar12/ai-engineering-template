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
INSTALLER = ROOT / "bin/install.py"
spec = importlib.util.spec_from_file_location("workflow_installer", INSTALLER)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def command(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, encoding="utf-8", capture_output=True, check=True).stdout


def read_settings(path):
    content = path.read_text(encoding="utf-8")
    return tomllib.loads(content) if path.suffix == ".toml" else json.loads(content)


class CodexConcurrencySettings(unittest.TestCase):
    def test_multiline_string_examples_are_preserved_byte_for_byte(self):
        incoming = b'[agents]\nmax_concurrent_threads_per_session = 12\n'
        for delimiter in (b'"""', b"'''"):
            for closing_width in (3, 4, 5):
                for managed_first in (False, True):
                    for cap in (5, 12):
                        with self.subTest(delimiter=delimiter, closing_width=closing_width,
                                          managed_first=managed_first, cap=cap):
                            escaped = (b'escaped quote run: ' + bytes([92]) + delimiter + b'\r\n'
                                       if delimiter == b'"""' else b'')
                            example = (b'developer_instructions = ' + delimiter + b'\r\n'
                                       b'[agents]\r\nmax_threads = 3\r\n'
                                       b'[[hooks.Stop]]\r\n' + escaped
                                       + delimiter[:1] * closing_width + b'\r\n')
                            actual = (b'[agents]\r\nmax_concurrent_threads_per_session = '
                                      + str(cap).encode() + b' # actual cap\r\n')
                            original = b'\xef\xbb\xbf# triple quotes in comments: """ \'\'\'\r\n'
                            original += (actual + b'[profiles.demo]\r\n' + example if managed_first
                                         else example + actual)
                            merged = installer.merge_codex_config(original, incoming, "project config")
                            expected = original.replace(str(cap).encode() + b' # actual cap',
                                                        b'12 # actual cap')
                            self.assertEqual(expected, merged)
                            self.assertEqual(merged, installer.merge_codex_config(merged, incoming, "project config"))

    def test_matching_hook_registrations_preserve_original_layout(self):
        for newline in (b"\n", b"\r\n"):
            with self.subTest(newline=newline):
                incoming = installer.host_payload("codex")[".codex/config.toml"]
                original = b"\xef\xbb\xbf# User settings\n" + incoming
                original = original.replace(b"\n", newline)
                self.assertEqual(original, installer.merge_codex_config(original, incoming))

    def test_append_preserves_bom_crlf_and_trailing_user_whitespace(self):
        original = b"\xef\xbb\xbf# User instructions\r\nretain trailing spaces  \r\n\r\n"
        incoming = (installer.AGENT_MARKER + "\nManaged instructions\n" + installer.AGENT_END + "\n").encode()
        merged = installer.merge_entry(original, incoming)
        self.assertTrue(merged.startswith(original))
        self.assertEqual(merged, installer.merge_entry(merged, incoming))
        ignore = b"\xef\xbb\xbf/build\r\n# Keep trailing spaces  \r\n\r\n"
        merged_ignore = installer.merge_file(".gitignore", ignore, installer.IGNORE_BLOCK.encode(), "codex")
        self.assertTrue(merged_ignore.startswith(ignore))
        self.assertEqual(merged_ignore, installer.merge_file(".gitignore", merged_ignore,
                                                          installer.IGNORE_BLOCK.encode(), "codex"))

    def test_hook_removal_ignores_embedded_multiline_table_examples(self):
        for delimiter in (b'"""', b"'''"):
            with self.subTest(delimiter=delimiter):
                example = (b'developer_instructions = ' + delimiter + b'\n'
                           b'[[hooks.Stop]]\n[[hooks.Stop.hooks]]\n'
                           + delimiter + b'\n')
                stale = {"matcher": "Old", "hooks": [{"type": "command", "command": "old"}]}
                actual = installer.hooks_toml({"Stop": [stale]})
                text = (example + actual + b'[agents]\nmax_concurrent_threads_per_session = 12\n').decode()
                result = installer.remove_toml_groups(text, {"Stop": [stale]})
                self.assertTrue(result.startswith(example.decode()))
                parsed = tomllib.loads(result)
                self.assertNotIn("hooks", parsed)
                self.assertEqual(tomllib.loads(example.decode())["developer_instructions"],
                                 parsed["developer_instructions"])

    def test_supported_key_forms_canonicalize_and_are_idempotent(self):
        cases = (
            b'#[agents] comment\nmodel = "keep"\n',
            b'[agents]\nmax_threads = 2\nother = 9\n',
            b'["agents"] # quoted\n"max_concurrent_threads_per_session" = 2 # keep\nmax_threads = 5\n',
            b"['agents']\n'max_threads' = 2\n",
            b'agents.max_threads = 2\nmodel = "keep"\n[features]\nflag = true\n',
            b'"agents"."max_concurrent_threads_per_session" = 5\n"agents"."max_threads" = 7\n',
            b'agents.other = 3',
            b'[agents]',
            b'[agents.executor]\nconfig_file = "executor.toml"\n',
        )
        incoming = b'[agents]\nmax_concurrent_threads_per_session = 12\n'
        for original in cases:
            with self.subTest(original=original):
                before = tomllib.loads(original.decode())
                merged = installer.merge_codex_config(original, incoming, "project/.codex/config.toml")
                expected = dict(before)
                expected["agents"] = dict(before.get("agents", {}))
                expected["agents"].pop("max_threads", None)
                expected["agents"]["max_concurrent_threads_per_session"] = 12
                self.assertEqual(expected, tomllib.loads(merged.decode()))
                self.assertEqual(merged, installer.merge_codex_config(merged, incoming, "project/.codex/config.toml"))


class InstallerTests(unittest.TestCase):
    def test_standalone_cleanup_payload_for_both_hosts_without_global_guard(self):
        cleanup_paths = ("scripts/cleanup.py", "engineer/bin/lib/cleanup.py", "commands/cleanup.md",
                         "engineer/workflows/cleanup.md", "engineer/references/cleanup.md")
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                namespace = "." + host
                installed = self.target / namespace
                payload = installer.payload(self.source, host)
                for relative in cleanup_paths:
                    self.assertIn(namespace + "/" + relative, payload)
                    self.assertTrue((installed / relative).is_file(), relative)
                skill = installer.skill_root(host) + "/cleanup/SKILL.md"
                self.assertIn(skill, payload)
                self.assertTrue((self.target / skill).is_file())
                self.assertFalse((installed / "hooks/destructive-git-guard.py").exists())
                self.assertFalse((installed / "runtime/lib/destructive_guard.py").exists())
                settings = read_settings(installed / ("config.toml" if host == "codex" else "settings.json"))
                hooks = settings["hooks"]
                commands = [hook["command"] for groups in hooks.values()
                            for group in groups for hook in group["hooks"]]
                self.assertFalse(any("cleanup.py" in command or "destructive" in command
                                     for command in commands))
                advisory = [hook["command"] for group in hooks["PreToolUse"]
                            for hook in group["hooks"]]
                self.assertTrue(advisory)
                self.assertTrue(any("worktree-path-guard.py" in command for command in advisory))
                self.assertTrue(all("worktree-path-guard.py" in command or "planning-integrity.sh" in command
                                    for command in advisory))

    def test_claude_role_defaults_replace_stale_metadata_and_preserve_body(self):
        for name, model, effort in (("scout", "haiku", None), ("targeted-fixer", "haiku", None),
                                    ("executor", "sonnet", None), ("planner", "opus", "medium")):
            with self.subTest(role=name):
                source = (ROOT / "agents" / (name + ".md")).read_text(encoding="utf-8")
                stale = source.replace("---\n", "---\nmodel: wrong\nmodel: stale\neffort: max\nmodel_reasoning_effort: high\n", 1)
                exported = installer.render_asset("agents/" + name + ".md", stale.encode(), "claude").decode()
                header = exported.split("---", 2)[1]
                metadata = yaml.safe_load(header)
                self.assertEqual(model, metadata["model"])
                self.assertEqual(effort, metadata.get("effort"))
                self.assertEqual(1, header.count("\nmodel:"))
                self.assertEqual(int(effort is not None), header.count("\neffort:"))
                self.assertNotIn("model_reasoning_effort", metadata)
                # Metadata normalization must not alter the complete relocated role body.
                clean = installer.render_asset("agents/" + name + ".md", source.encode(), "claude").decode()
                self.assertEqual(clean.split("---", 2)[2], exported.split("---", 2)[2])
                original = yaml.safe_load(source.split("---", 2)[1])
                for key, value in original.items():
                    self.assertEqual(value, metadata[key])
                codex = yaml.safe_load(installer.render_asset("agents/" + name + ".md", stale.encode(), "codex").decode().split("---", 2)[1])
                self.assertTrue({"model", "effort", "model_reasoning_effort", "maxTurns"}.isdisjoint(codex))

    def test_fresh_payload_excludes_source_only_maintenance_history_for_both_hosts(self):
        self.assertTrue((self.source / ".ai/maintenance/agent-scout-SUMMARY.md").is_file())
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host, "--no-hooks")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse((self.target / ("." + host) / "maintenance").exists())
                self.assertFalse(any("maintenance/" in name for name in installer.payload(self.source, host)))

    def test_migration_records_pinned_source_revision_and_selected_host(self):
        for host in ("codex", "claude"):
            self.target = self.base / host
            legacy = self.target / ".ai"
            legacy.mkdir(parents=True)
            (legacy / "RULES.md").write_text("Custom legacy rules\n")
            result = self.install("--host", host, "--migrate-existing", "--no-hooks")
            self.assertEqual(0, result.returncode, result.stderr)
            manifest = json.loads((self.target / ("." + host) / "workflow-ownership.json").read_bytes())
            self.assertEqual(host, manifest["host"])
            self.assertEqual(self.revision, manifest["current"]["revision"])
            self.assertEqual(str(self.source), manifest["current"]["source"])
            self.assertEqual(b"Custom legacy rules\n", (self.target / ("." + host) / "engineer/RULES.md").read_bytes())

    @classmethod
    def setUpClass(cls):
        cls.source_temp = tempfile.TemporaryDirectory(prefix="installer-source-")
        cls.source = Path(cls.source_temp.name)
        for directory in ("agents", "commands", "engineer", "hooks", "scripts", "skills", "bin"):
            if not (ROOT / directory).exists():
                continue
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
        legacy_fixture = cls.source / ".ai/maintenance/agent-scout-SUMMARY.md"
        legacy_fixture.parent.mkdir(parents=True, exist_ok=True)
        legacy_fixture.write_text("Source-only maintenance fixture; never installed.\n", encoding="utf-8")
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

    def test_registered_hooks_run_planning_integrity_from_installed_hosts(self):
        valid = '''---
phase: 01-foundation
plan: "01"
type: execute
wave: 1
depends_on: []
files_modified: []
files_deleted: []
resources: []
autonomous: true
requirements: [REQ-01]
acceptance: []
documentation: []
checks: []
must_haves: {truths: [], artifacts: [], key_links: []}
issue_refs: []
---
# Complete canonical plan fixture
'''
        valid += "\n## Goal\n\nComplete the bounded planning integrity installation integration.\n\n"
        valid += "## Acceptance Criteria\n\n- Install hook on both supported hosts.\n"
        invalid = valid.replace("issue_refs: []\n", "")
        record = ".planning/phases/01-foundation/01-01-PLAN.md"
        unrelated = "unrelated.txt"
        for host, name in (("codex", ".codex/config.toml"), ("claude", ".claude/settings.json")):
            with self.subTest(host=host):
                self.target = self.base / (host + " projet caf" + chr(0xE9) + " nested")
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                settings = read_settings(self.target / name)
                groups = settings["hooks"]["PreToolUse"]
                matches = [group for group in groups
                           if group.get("matcher") == "^(Bash|exec_command|shell_command|shell)$"]
                self.assertEqual(1, len(matches), "standalone planning integrity owns the shell registration")
                handler = matches[0]["hooks"][0]
                self.assertIn("planning-integrity.sh", handler["command"])
                self.assertEqual(10, handler["timeout"])

                cwd = self.target / "sub directory"
                cwd.mkdir()
                record_path = self.target / record
                record_path.parent.mkdir(parents=True)
                record_path.write_text(valid, encoding="utf-8")
                (self.target / unrelated).write_text("baseline\n", encoding="utf-8")
                command("git", "add", record, unrelated, cwd=self.target)
                command("git", "-c", "user.name=Installer Test", "-c", "user.email=test@example.invalid",
                        "commit", "--quiet", "-m", "valid fixture", cwd=self.target)
                head = command("git", "rev-parse", "HEAD", cwd=self.target).strip()

                # The index contains invalid prospective bytes while the worktree
                # has a valid copy. Keep another real staged path to prove that
                # the checker leaves the user's index untouched.
                record_path.write_text(invalid, encoding="utf-8")
                command("git", "add", record, cwd=self.target)
                record_path.write_text(valid, encoding="utf-8")
                (self.target / unrelated).write_text("preserve staged index\n", encoding="utf-8")
                command("git", "add", unrelated, cwd=self.target)
                staged_before = command("git", "ls-files", "--stage", cwd=self.target)
                environment = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.target))
                launcher = self.launcher_argv(host, handler)
                tools = ("Bash", "exec_command", "shell_command", "shell")
                for index, tool in enumerate(tools):
                    field = "command" if index % 2 == 0 else "cmd"
                    payload = {"cwd": str(cwd), "hook_event_name": "PreToolUse", "tool_name": tool,
                               "tool_input": {field: "git commit -m invalid"}}
                    observed = subprocess.run(launcher, cwd=cwd, env=environment,
                                              input=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
                                              capture_output=True)
                    self.assertEqual(2, observed.returncode, observed.stderr.decode("utf-8", "replace"))
                    self.assertIn(b"issue_refs", observed.stderr,
                                  f"cwd={str(cwd)!r} exists={cwd.is_dir()} host={host} tool={tool}")
                    self.assertEqual(head, command("git", "rev-parse", "HEAD", cwd=self.target).strip())
                    self.assertEqual(staged_before, command("git", "ls-files", "--stage",
                                                            cwd=self.target))

                # A complete record using --only is checked from prospective
                # worktree bytes; unrelated staged content remains in the index.
                record_path.write_text(valid.replace("Complete canonical", "Updated canonical"),
                                       encoding="utf-8")
                payloads = (
                    {"command": "git -C .. commit --only -m valid -- " + record},
                    {"cmd": "git status --short"},
                    {"command": ["git", "-C", "..", "commit", "--only", "-m", "valid", "--", record]},
                )
                for payload_input in payloads:
                    payload = {"cwd": str(cwd), "hook_event_name": "PreToolUse", "tool_name": "Bash",
                               "tool_input": payload_input}
                    observed = subprocess.run(launcher, cwd=cwd, env=environment,
                                              input=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
                                              capture_output=True)
                    self.assertEqual(0, observed.returncode,
                                     observed.stderr.decode("utf-8", "replace"))
                    self.assertEqual(staged_before, command("git", "ls-files", "--stage",
                                                            cwd=self.target))

    def test_installed_runtime_answers_its_verb_contract(self):
        """The installed runtime resolves its own namespace and returns pure results."""
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host)
                self.assertEqual(0, result.returncode, result.stderr)
                runtime = "." + host + "/engineer/bin/engineer.py"
                identity = json.loads(command(sys.executable, runtime, "query",
                                              "runtime-identity", cwd=self.target))
                self.assertEqual("2.0", identity["contract"])
                self.assertEqual(host, identity["host"])
                self.assertEqual((self.target / ("." + host)).resolve(), Path(identity["namespace"]).resolve())
                self.assertEqual("engineer-runtime", identity["packageName"])
                listed = json.loads(command(sys.executable, runtime, "query", "phases.list",
                                            cwd=self.target))
                self.assertEqual(0, listed["count"])
                self.assertEqual([], listed["phases"])
                verbs = json.loads(command(sys.executable, runtime, "query", "help",
                                           cwd=self.target))["verbs"]
                self.assertIn("phase.locate", verbs)
                self.assertIn("session.adopt", verbs)
                before = self.snapshot()
                located = json.loads(command(sys.executable, runtime, "query", "phase.locate", "01",
                                             cwd=self.target))
                self.assertFalse(located["phase_found"])
                adoption = subprocess.run([sys.executable, runtime, "query", "session.adopt", "phase", "01"],
                                          cwd=self.target, text=True, encoding="utf-8", capture_output=True)
                self.assertEqual(adoption.returncode, 1)
                self.assertNotIn("Traceback", adoption.stderr)
                self.assertEqual(json.loads(adoption.stdout)["code"], "phase-not-found")
                self.assertFalse((self.target / ".git" / "ai-phase" / "sessions.json").exists())
                self.assertEqual(before, self.snapshot())
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
        listed = json.loads(command(sys.executable, ".codex/engineer/bin/engineer.py", "query",
                                    "phases.list", cwd=self.target))
        self.assertEqual([], listed["phases"])
        for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE"):
            pinned = subprocess.run(["git", "show", self.revision + ":bin/install-assets/" + name + ".txt"], cwd=self.source,
                                    check=True, capture_output=True).stdout
            self.assertEqual(pinned,
                             (self.target / ".planning" / (name + ".md")).read_bytes())
        for omitted in ("README.md", "tests", ".github", ".planning/maintenance", ".ai-venv",
                        "docs", ".ai/install-assets", ".planning/phases/99-source",
                        ".planning/specs/SPEC-source.md", ".planning/decisions/ADR-source.md",
                        ".planning/codebase/source-map.md"):
            self.assertFalse((self.target / omitted).exists(), omitted)
        self.assertEqual([], list(self.target.glob("*.log")))
        for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE"):
            body = (self.target / ".planning" / (name + ".md")).read_text(encoding="utf-8")
            self.assertNotIn("Source-only project history", body)
            self.assertNotIn("ai-engineering-template", body)
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
        self.assertIn("/<PIN>/bin/install.py", guide)
        self.assertIn("exact Git commit", guide)
        # Local-only workflow scratch stays out of the project's history.
        for ignored in (".workflow-backups/probe.txt",
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
                for relative in ("engineer/RULES.md", "engineer/bin/engineer.py", "agents/executor.md",
                                 "commands/onboard.md", "engineer/templates/context.md"):
                    self.assertTrue((self.target / namespace / relative).is_file(), relative)
                body = (self.target / entry).read_text(encoding="utf-8")
                self.assertIn(namespace + "/engineer/RULES.md", body)
                self.assertNotIn("@AGENTS.md", body)
                config = (self.target / ".planning/config.yaml").read_text(encoding="utf-8")
                self.assertIn("verification:", config)
                self.assertNotIn(".ai/", config)
                listed = json.loads(command(sys.executable, namespace + "/engineer/bin/engineer.py",
                                            "query", "phases.list", cwd=self.target))
                self.assertEqual([], listed["phases"])
                self.assertIn(".planning/handoffs/", (self.target / ".gitignore").read_text())
                skills = self.target / (".agents/skills" if host == "codex" else ".claude/skills")
                full = (skills / "onboard/SKILL.md").read_text(encoding="utf-8")
                self.assertIn("<process>", full)
                self.assertNotIn("Read and follow the complete skill at", full)
                self.assertFalse((self.target / namespace / "roles").exists())
                for workflow in ("execute-phase.md", "plan-phase.md", "new-project.md"):
                    self.assertTrue((self.target / namespace / "engineer/workflows" / workflow).is_file(),
                                    workflow)
                if host == "codex":
                    self.assertFalse((self.target / ".codex/skills").exists())
                    self.assertFalse((self.target / ".codex/hooks.json").exists())
                else:
                    self.assertFalse((self.target / ".agents").exists())

    def test_native_agent_models_and_direct_roles_install_without_hooks(self):
        roles = {p.stem for p in (self.source / "agents").glob("*.md")
                 if p.stem not in {"AGENT", "code-fixer"}}
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                result = self.install("--host", host, "--no-hooks")
                self.assertEqual(0, result.returncode, result.stderr)
                agents = self.target / ("." + host) / "agents"
                methods = {}
                for role in agents.glob("*.md"):
                    text = role.read_text(encoding="utf-8")
                    if text.startswith("---\n") and role.stem != "code-fixer":
                        metadata = yaml.safe_load(text.split("---", 2)[1])
                        methods[metadata["name"]] = (role, metadata)
                self.assertEqual(roles, set(methods))
                method_path = (self.target / ".claude/engineer/references/code-fixer.md" if host == "claude"
                               else agents / "code-fixer.md")
                self.assertEqual(installer.render_asset("agents/code-fixer.md", (self.source / "agents/code-fixer.md").read_bytes(), host),
                                 method_path.read_bytes())
                self.assertFalse((agents / "code-fixer.toml").exists())
                if host == "claude":
                    self.assertFalse((agents / "code-fixer.md").exists())
                for name, (role, metadata) in methods.items():
                    if host == "claude" and name in {"scout", "targeted-fixer", "executor", "planner"}:
                        self.assertEqual({"scout": "haiku", "targeted-fixer": "haiku",
                                          "executor": "sonnet", "planner": "opus"}[name], metadata["model"])
                    else:
                        self.assertNotIn("model", metadata, name)
                    self.assertEqual("medium" if host == "claude" and name == "planner" else None,
                                     metadata.get("effort"), name)
                    self.assertNotIn("model_reasoning_effort", metadata, name)
                    # Full source methods survive relocation, not compact substitutes.
                    self.assertEqual(installer.render_asset("agents/" + role.name,
                        (self.source / "agents" / role.name).read_bytes(), host),
                        role.read_bytes())
                if host == "codex":
                    self.assertEqual(roles, {p.stem for p in agents.glob("*.toml")})
                    for definition in agents.glob("*.toml"):
                        config = tomllib.loads(definition.read_text(encoding="utf-8"))
                        name = config["name"]
                        self.assertEqual(definition.stem, name)
                        self.assertEqual(methods[name][1]["description"], config["description"])
                        expected = "gpt-6-luna" if name in {"scout", "targeted-fixer"} else "gpt-6.1-sol"
                        self.assertEqual(expected, config["model"])
                        checkers = {"executor", "doc-verifier", "integration-checker"}
                        effort = "medium" if name in checkers else "high"
                        self.assertEqual(effort, config["model_reasoning_effort"])
                        role_path = ".codex/agents/" + name + ".md"
                        self.assertIn(role_path, config["developer_instructions"])
                        self.assertNotIn(".ai/", config["developer_instructions"])
                        self.assertTrue((self.target / role_path).is_file())
                        if name == "scout":
                            self.assertEqual("read-only", config["sandbox_mode"])
                else:
                    self.assertEqual([], list(agents.glob("*.toml")))
                before = self.snapshot()
                repeated = self.install("--host", host, "--no-hooks")
                self.assertEqual(0, repeated.returncode, repeated.stderr)
                self.assertEqual(before, self.snapshot())

    def test_installed_resolver_uses_native_codex_and_preserves_claude_overrides(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                self.assertEqual(0, self.install("--host", host, "--no-hooks").returncode)
                runtime = "." + host + "/engineer/bin/engineer.py"
                for name, model, effort in (("executor", "sonnet", "high"), ("planner", "opus", "medium")):
                    default = json.loads(command(sys.executable, runtime, "query", "resolve-agent", name, cwd=self.target))
                    self.assertEqual("gpt-6.1-sol" if host == "codex" else model, default["model"])
                    self.assertEqual(("medium" if name == "executor" else "high") if host == "codex" else effort, default["effort"])
                config = self.target / ".planning/config.yaml"
                config.write_text("agents:\n  executor:\n    model: opus\n    effort: max\n"
                                  "  planner:\n    model: sonnet\n    effort: low\n"
                                  "  scout:\n    model: wrong\n    effort: max\n"
                                  "  targeted-fixer:\n    model: wrong\n    effort: max\n")
                if host == "codex":
                    native = self.target / ".codex/agents/executor.toml"
                    native.write_text(native.read_text().replace('"gpt-6.1-sol"', '"custom-codex"')
                                      .replace('"medium"', '"xhigh"'))
                    for name in ("scout", "targeted-fixer"):
                        fixed = self.target / ".codex/agents" / (name + ".toml")
                        fixed.write_text(fixed.read_text().replace('"gpt-6-luna"', '"wrong"')
                                         .replace('"high"', '"max"'))
                runtime = "." + host + "/engineer/bin/engineer.py"
                resolved = json.loads(command(sys.executable, runtime, "query", "resolve-agent",
                                              "executor", cwd=self.target))
                self.assertEqual("custom-codex" if host == "codex" else "opus", resolved["model"])
                self.assertEqual("xhigh" if host == "codex" else "max", resolved["effort"])
                preparer = json.loads(command(sys.executable, runtime, "query", "resolve-agent", "planner", cwd=self.target))
                self.assertEqual("gpt-6.1-sol" if host == "codex" else "sonnet", preparer["model"])
                self.assertEqual("high" if host == "codex" else "low", preparer["effort"])
                for name in ("scout", "targeted-fixer"):
                    fixed = json.loads(command(sys.executable, runtime, "query", "resolve-agent",
                                               name, cwd=self.target))
                    self.assertEqual("gpt-6-luna" if host == "codex" else "haiku", fixed["model"])
                    self.assertEqual("high" if host == "codex" else "inherit", fixed["effort"])
                    self.assertEqual(name, fixed["model_source"])

    def test_settings_only_preserves_bom_crlf_unrelated_text_and_hooks(self):
        self.target.mkdir()
        path = self.target / ".codex/config.toml"
        path.parent.mkdir()
        original = (b'\xef\xbb\xbf# mine\r\nmodel = "custom"\r\n["agents"] # table\r\n'
                    b'"max_threads" = 3 # legacy note\r\nother = "keep"\r\n'
                    b'[hooks]\r\nStop = []\r\n')
        path.write_bytes(original)
        result = self.install("--no-hooks")
        self.assertEqual(0, result.returncode, result.stderr)
        content = path.read_bytes()
        self.assertTrue(content.startswith(b'\xef\xbb\xbf# mine\r\nmodel = "custom"\r\n'))
        self.assertIn(b'# legacy note\r\nother = "keep"\r\n[hooks]\r\nStop = []\r\n', content)
        self.assertNotIn(b"\n", content.replace(b"\r\n", b""))
        parsed = tomllib.loads(content.decode("utf-8-sig"))
        self.assertEqual(12, parsed["agents"]["max_concurrent_threads_per_session"])
        self.assertNotIn("max_threads", parsed["agents"])
        self.assertEqual({"Stop": []}, parsed["hooks"])
        before = self.snapshot()
        self.assertEqual(0, self.install("--no-hooks").returncode)
        self.assertEqual(before, self.snapshot())

    def test_unsupported_codex_settings_fail_preflight_without_writes(self):
        for content in (b'agents = {max_threads = 3}\n', b'agents = 3\n',
                        b'[agents]\nmax_threads = 3\nmax_threads = 4\n',
                        b'[agents]\nmax_concurrent_threads_per_session = "3"\n'):
            with self.subTest(content=content):
                self.target.mkdir(exist_ok=True)
                path = self.target / ".codex/config.toml"
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(content)
                before = self.snapshot()
                result = self.install("--no-hooks")
                self.assertNotEqual(0, result.returncode)
                self.assertIn("nothing was installed", result.stderr)
                self.assertEqual(before, self.snapshot())

    def test_custom_native_agent_is_not_overwritten(self):
        for host, suffix in (("codex", "toml"), ("claude", "md")):
            with self.subTest(host=host):
                self.target = self.base / host
                self.assertEqual(0, self.install("--host", host).returncode)
                role = self.target / ("." + host) / "agents" / ("executor." + suffix)
                # A comment is valid in both formats, so the edit stays representative.
                role.write_text(role.read_text(encoding="utf-8") + "\n# local customization\n",
                                encoding="utf-8")
                before = self.snapshot()
                result = self.install("--host", host)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("executor." + suffix, result.stderr)
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
                runtime = "." + host + "/engineer/bin/engineer.py"
                added = json.loads(command(sys.executable, runtime, "query", "phase.add",
                                           "Installed runtime", "--goal", "Prove the install",
                                           cwd=worktree))
                self.assertTrue(added["added"])
                self.assertEqual("01", added["padded"])
                created = Path(added["directory"])
                created = created if created.is_absolute() else worktree / created
                self.assertEqual(worktree / ".planning/phases/01-installed-runtime", created)
                self.assertTrue((worktree / added["directory"]).is_dir())
                roadmap = (worktree / ".planning/ROADMAP.md").read_text(encoding="utf-8")
                self.assertRegex(roadmap, r"### Phase 0?1: Installed runtime")
                listed = json.loads(command(sys.executable, runtime, "query", "phases.list",
                                            cwd=worktree))
                self.assertEqual(["01"], [phase["phase_number"] for phase in listed["phases"]])
                self.assertEqual(["Installed runtime"], [phase["name"] for phase in listed["phases"]])
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
                output = result.stdout.replace("\\", "/")
                if host == "codex":
                    self.assertIn("write " + name, output)
                else:
                    self.assertNotIn("write " + name, output)
                result = self.install("--host", host, "--no-hooks")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertTrue((self.target / ("." + host) / "engineer/bin/engineer.py").exists())
                if host == "codex":
                    settings = read_settings(self.target / name)
                    self.assertEqual(12, settings["agents"]["max_concurrent_threads_per_session"])
                    self.assertNotIn("hooks", settings)
                else:
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
            destination = self.target / ("." + host) / "engineer/RULES.md"
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
                self.assertIn(b"NOTICE", observed.stderr)
                self.assertIn(("." + host + "/engineer/RULES.md").encode(), observed.stderr)

            # The installed dispatch guard must preserve warning-and-continue
            # behavior and actionable isolation guidance from nested directories.
            groups = settings["hooks"]["PreToolUse"]
            dispatch = [group for group in groups if "Agent" in group.get("matcher", "")]
            self.assertEqual(1, len(dispatch),
                             "exactly one managed Agent/Task registration is expected")
            with self.subTest(host=host, hook="worktree-guard dispatch"):
                argv = self.launcher_argv(host, dispatch[0]["hooks"][0])
                payload = {"cwd": str(cwd), "hook_event_name": "PreToolUse",
                           "tool_name": "Agent",
                           "tool_input": {"subagent_type": "executor", "description": "x"}}
                observed = subprocess.run(argv, cwd=cwd, env=environment,
                                          input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                          capture_output=True)
                self.assertEqual(0, observed.returncode,
                                 "an unisolated executor dispatch must warn and continue: "
                                 + observed.stderr.decode("utf-8", "replace"))
                self.assertIn(b"WARNING", observed.stderr)
                self.assertIn(b'isolation="worktree"', observed.stderr)
                self.assertEqual(b"", observed.stdout)
                # Same registration, isolated dispatch: must get out of the way.
                payload["tool_input"]["isolation"] = "worktree"
                observed = subprocess.run(argv, cwd=cwd, env=environment,
                                          input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                          capture_output=True)
                self.assertEqual(0, observed.returncode, observed.stderr)
                self.assertEqual(b"", observed.stdout)
                self.assertEqual(b"", observed.stderr)

            writes = [group for group in groups if "NotebookEdit" in group.get("matcher", "")]
            self.assertEqual(1, len(writes),
                             "exactly one managed editing-tool registration is expected")
            with self.subTest(host=host, hook="worktree-guard scratchpad"):
                argv = self.launcher_argv(host, writes[0]["hooks"][0])
                scratchpad = self.target / ".planning/scratchpads/notes.md"
                payload = {"cwd": str(cwd), "hook_event_name": "PreToolUse",
                           "tool_name": "Edit", "tool_input": {"file_path": str(scratchpad)}}
                observed = subprocess.run(argv, cwd=cwd, env=environment,
                                          input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                                          capture_output=True)
                self.assertEqual(0, observed.returncode, observed.stderr)
                self.assertEqual(b"", observed.stdout)
                self.assertIn(b"WARNING", observed.stderr)
                self.assertIn(b"session.open", observed.stderr)
                self.assertIn(b"scratchpads", observed.stderr)

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
        self.assertTrue((self.target / ".codex/engineer/bin/engineer.py").is_file())

    def test_git_line_ending_changes_do_not_duplicate_or_conflict_with_context(self):
        self.target.mkdir()
        (self.target / "AGENTS.md").write_bytes(b"# Product instructions\n")
        self.assertEqual(0, self.install().returncode)
        for name in ("AGENTS.md", ".gitignore", ".codex/engineer/RULES.md", ".codex/engineer/references/checkpoints.md"):
            path = self.target / name
            path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        before = self.snapshot()
        result = self.install()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_installed_guidance_references_resolve_in_both_destinations(self):
        import re
        for host in ("codex", "claude"):
            self.target = self.base / host
            result = self.install("--host", host)
            self.assertEqual(0, result.returncode, result.stderr)
            namespace = "." + host
            for name, data in installer.payload(self.source, host).items():
                if not name.endswith((".md", ".toml")):
                    continue
                text = data.decode("utf-8")
                self.assertNotRegex(text, r"(?m)^@(?:engineer|agents|commands|hooks|scripts|bin)/")
                for reference in re.findall(r"(?m)^@(" + re.escape(namespace) + r"/[A-Za-z0-9_./-]+)", text):
                    self.assertTrue((self.target / reference).is_file(), (name, reference))

    def test_missing_or_placeholder_skill_tree_exports_complete_command_mirrors(self):
        with tempfile.TemporaryDirectory(prefix="native-skills-source-") as folder:
            source = Path(folder)
            for directory in ("agents", "commands", "engineer", "hooks", "scripts", "bin"):
                shutil.copytree(self.source / directory, source / directory)
            for placeholder in (False, True):
                if placeholder:
                    (source / "skills").mkdir()
                    (source / "skills/SKILL").write_text("placeholder")
                for host in ("codex", "claude"):
                    payload = installer.payload(source, host, False)
                    for command_path in (source / "commands").glob("*.md"):
                        name = installer.skill_root(host) + "/" + command_path.stem + "/SKILL.md"
                        self.assertEqual(installer.render_asset("commands/" + command_path.name,
                                                              command_path.read_bytes(), host), payload[name])
                        self.assertNotIn(b"Read and follow the complete skill at", payload[name])
                    self.assertNotIn("." + host + "/skills/SKILL", payload)

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
        (self.target / ".codex/engineer").mkdir()
        (self.target / ".codex/engineer/RULES.md").write_text("Custom engineering rules")
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
        self.assertTrue((canonical / ".codex/engineer/bin/engineer.py").is_file())
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
