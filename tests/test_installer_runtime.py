"""Exercise the current pinned installer against real disposable repositories."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin/install.py"
PREFIXES = ("agents", "commands", "engineer", "hooks", "scripts", "skills", "bin")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


installer = load("current_installer", ROOT / "bin/install_support.py")
transforms = load("current_export_transforms", ROOT / "bin/export_transforms.py")
posix_shell = load("installer_posix_shell", ROOT / "engineer/bin/lib/posix_shell.py")


def git(directory, *args):
    result = subprocess.run(["git", "-C", str(directory), *args], capture_output=True,
                            text=True, encoding="utf-8", check=True, timeout=30)
    return result.stdout.strip()


class CurrentInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_temp = tempfile.TemporaryDirectory(prefix="engineer-source-")
        cls.source = Path(cls.source_temp.name).resolve()
        for name in PREFIXES:
            shutil.copytree(ROOT / name, cls.source / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        git(cls.source, "init", "-b", "main")
        git(cls.source, "config", "user.name", "Installer Fixture")
        git(cls.source, "config", "user.email", "fixture@example.invalid")
        git(cls.source, "config", "core.autocrlf", "false")
        git(cls.source, "add", *PREFIXES)
        # Windows does not infer this source executable bit from file permissions.
        git(cls.source, "update-index", "--chmod=+x", "engineer/bin/engineer_run")
        git(cls.source, "commit", "-m", "Pinned installer fixture")
        cls.pin = git(cls.source, "rev-parse", "HEAD")

    @classmethod
    def tearDownClass(cls):
        cls.source_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="engineer-target-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        # Dollar signs, apostrophes and whitespace must remain literal shell data.
        self.target = self.base / "project $literal ' quoted"

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, "-I", str(CLI), *map(str, args)],
                                capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(expected, result.returncode, result.stderr[:8000])
        return json.loads(result.stdout if expected == 0 else result.stderr)

    def install(self, host="codex", scope="local", *args, ref=None, expected=0):
        return self.cli("--source", self.source, "--ref", ref or self.pin,
                        "--target", self.target, "--host", host, "--" + scope,
                        *args, expected=expected)

    def apply_plan(self, plan, *args, expected=0):
        path = self.base / "reviewed-plan.json"
        path.write_text(json.dumps(plan), encoding="utf-8")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return self.cli("--apply", path, "--reviewed-plan-sha256", digest,
                        *args, expected=expected)

    def snapshot(self):
        if not self.target.exists():
            return {}
        return {path.relative_to(self.target).as_posix():
                (path.read_bytes(), path.stat().st_mtime_ns)
                for path in self.target.rglob("*") if path.is_file()}

    def test_clean_installs_both_hosts_and_scopes_are_noop_on_rerun(self):
        for host in ("codex", "claude"):
            for scope in ("local", "global"):
                with self.subTest(host=host, scope=scope):
                    self.target = self.base / (host + "-" + scope + " $literal ' quoted")
                    preview = self.install(host, scope, "--dry-run")
                    self.assertEqual([], preview["findings"])
                    self.assertTrue(preview["complete"])
                    self.assertFalse(any('/skills/SKILL/' in e['path'] for e in preview['entries']))
                    self.assertFalse(any('/scripts/' in e['path'] for e in preview['entries']))
                    self.assertFalse(self.target.exists())
                    result = self.install(host, scope)
                    self.assertTrue(result["applied"])
                    self.assertTrue(result["complete"])
                    namespace = self.target / ("." + host)
                    self.assertFalse((namespace / "scripts").exists())
                    self.assertFalse(any(path.is_dir() and path.name in {"guides", "maintenance"}
                                         for path in namespace.rglob("*")))
                    entry_name = "AGENTS.md" if host == "codex" else "CLAUDE.md"
                    entry = (namespace if scope == "global" else self.target) / entry_name
                    self.assertIn("ENGINEER MANAGED BEGIN", entry.read_text())
                    self.assertFalse((self.target / ".ai").exists())
                    self.assertFalse((self.target / ".planning").exists())
                    runtime = namespace / "engineer/bin/engineer.py"
                    env = {**os.environ, "ENGINEER_ROOT": str(self.target), "ENGINEER_HOST": host}
                    identity = subprocess.run([sys.executable, "-I", str(runtime), "query", "runtime-identity"],
                                              env=env, capture_output=True, text=True, encoding="utf-8", check=True)
                    self.assertEqual("engineer-runtime", json.loads(identity.stdout)["packageName"])
                    self.assertEqual(host, json.loads(identity.stdout)["host"])
                    if host == "codex":
                        config = tomllib.loads((namespace / "config.toml").read_text())
                        self.assertTrue(config["skills"]["config"])
                        for record in config["skills"]["config"]:
                            self.assertFalse(Path(record["path"]).is_absolute(), record)
                            self.assertTrue((namespace / record["path"]).is_file(), record)
                        wrappers = list((namespace / "agents").glob("*.toml"))
                        self.assertEqual(20, len(wrappers))
                        for wrapper in wrappers:
                            role = tomllib.loads(wrapper.read_text(encoding="utf-8"))
                            self.assertEqual(wrapper.stem, role["name"])
                            self.assertTrue(role["description"])
                            self.assertEqual("gpt-6.1-sol", role["model"])
                            self.assertEqual("high", role["model_reasoning_effort"])
                            counterpart = wrapper.with_suffix(".md")
                            instructions = role["developer_instructions"]
                            role_reference = (counterpart.relative_to(self.target).as_posix()
                                              if scope == "local" else "${CODEX_HOME:-$HOME/.codex}/agents/" + counterpart.name)
                            self.assertEqual(
                                "Read and follow the complete role at " + role_reference
                                + " before acting. Read its local workflow and referenced shared rules; "
                                "the assignment bounds your scope. Phase implementation requires the user's "
                                "explicit instruction to implement that phase. "
                                "If that file cannot be read, stop and report the missing counterpart.",
                                instructions)
                            self.assertNotIn('"', instructions)
                            instruction_line = next(line for line in wrapper.read_text(encoding="utf-8").splitlines()
                                                    if line.startswith("developer_instructions = "))
                            self.assertNotIn('\\"', instruction_line)
                            self.assertIn("stop and report", role["developer_instructions"])
                            self.assertNotIn("<role>", role["developer_instructions"])
                            self.assertIn("<role>", counterpart.read_text(encoding="utf-8"))
                            self.assertLess(len(role["developer_instructions"]), 700)
                    else:
                        settings = json.loads((namespace / "settings.json").read_text())
                        self.assertEqual(1, len(settings["hooks"]["PreToolUse"]))
                    before = self.snapshot()
                    rerun_preview = self.install(host, scope, "--dry-run")
                    self.assertTrue(all(e["action"] == "unchanged" for e in rerun_preview["entries"]))
                    rerun = self.install(host, scope)
                    self.assertTrue(rerun["no_op"])
                    self.assertEqual([], rerun["files"])
                    self.assertEqual(before, self.snapshot())

    def test_local_codex_role_references_survive_project_relocation(self):
        self.install()
        original_target = self.target
        relocated = self.base / "relocated checkout with spaces"
        original_target.rename(relocated)
        self.assertFalse(original_target.exists())
        wrappers = list((relocated / ".codex/agents").glob("*.toml"))
        self.assertEqual(20, len(wrappers))
        for wrapper in wrappers:
            with self.subTest(role=wrapper.stem):
                raw = wrapper.read_text(encoding="utf-8")
                instructions = tomllib.loads(raw)["developer_instructions"]
                prefix = "Read and follow the complete role at "
                reference = instructions.removeprefix(prefix).split(" before acting.", 1)[0]
                self.assertEqual(f".codex/agents/{wrapper.stem}.md", reference)
                self.assertNotIn('\\"', raw)
                self.assertNotIn(str(original_target), instructions)
                self.assertFalse(Path(reference).is_absolute())
                self.assertEqual(wrapper.with_suffix(".md"), relocated / reference)
                self.assertIn("<role>", (relocated / reference).read_text(encoding="utf-8"))

    def test_exported_references_do_not_depend_on_install_target(self):
        for host in ("codex", "claude"):
            for scope in ("local", "global"):
                with self.subTest(host=host, scope=scope):
                    first = installer.exports(self.source, self.pin, self.target, host, scope)["payload"]
                    other = self.base / ".worktrees/unrelated checkout"
                    second = installer.exports(self.source, self.pin, other, host, scope)["payload"]
                    self.assertEqual(first, second)
                    for name, (data, _) in first.items():
                        for absolute in (self.target, other, Path(sys.executable)):
                            for spelling in (str(absolute), absolute.as_posix()):
                                self.assertNotIn(spelling.encode(), data, name)

    def test_migration_references_remain_portable(self):
        legacy = self.target / ".ai/commands/custom.md"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("Read .ai/references/custom.md and .ai/runtime/engineer.py.\n", newline="\n")
        for scope in ("local", "global"):
            with self.subTest(scope=scope):
                plan = installer.migration_plan(self.source, self.pin, self.target, "codex", scope)
                entry = next(e for e in plan["entries"] if e.get("legacy_path") == ".ai/commands/custom.md")
                content = base64.b64decode(entry["content"]).decode()
                prefix = ".codex" if scope == "local" else "${CODEX_HOME:-$HOME/.codex}"
                self.assertEqual(f"Read {prefix}/engineer/references/custom.md and "
                                 f"{prefix}/engineer/bin/engineer.py.\n", content)
                self.assertNotIn(str(self.target), content)

    def test_global_migration_refuses_unknown_path_consumers(self):
        legacy = self.target / ".ai/commands/custom.py"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("open('.ai/references/custom.md')\n", newline="\n")
        plan = installer.migration_plan(self.source, self.pin, self.target, "codex", "global")
        self.assertIn("global-migration-reference", [f["code"] for f in plan["findings"]])
        failure = self.apply_plan(plan, "--select", ".codex/commands/custom.py", expected=2)
        self.assertEqual("export-blocked", failure["error"])
        self.assertFalse((self.target / ".codex/commands/custom.py").exists())
        self.assertEqual("open('.ai/references/custom.md')\n", legacy.read_text())

    def test_unprefixed_role_references_use_the_installed_host(self):
        source = b"Read ~/.claude/agents/security-auditor.md and @~/.claude/references/rules.md."
        for host in ("codex", "claude"):
            for scope in ("local", "global"):
                ns = installer.reference_namespace(host, scope)
                actual = installer.adapt(source, host, ns, "engineer/workflows/secure-phase.md", []).decode()
                self.assertEqual(f"Read {ns}/agents/security-auditor.md and @{ns}/engineer/references/rules.md.", actual)

    def test_global_bootstrap_and_hook_use_active_host_home(self):
        shell = posix_shell.find_posix_shell("bash")
        if not shell:
            self.skipTest("No POSIX shell is installed")
        for host, variable in (("codex", "CODEX_HOME"), ("claude", "CLAUDE_CONFIG_DIR")):
            with self.subTest(host=host):
                self.target = self.base / (host + " custom home $literal ' quoted")
                self.target.mkdir()
                git(self.target, "init", "-b", "main")
                self.install(host, "global")
                ns = self.target / ("." + host)
                env = {**os.environ, variable: str(ns), "ENGINEER_ROOT": str(self.target), "ENGINEER_HOST": host}
                source = b'_ENGINEER_SHIM_NAME=obsolete\nengineer_run query runtime-identity --pick packageName --raw\n'
                exported = installer.adapt(source, host, installer.reference_namespace(host, "global"),
                                           "engineer/workflows/smoke.sh", []).decode()
                result = subprocess.run([shell, "-c", exported], cwd=self.base, env=env,
                                        capture_output=True, text=True, encoding="utf-8", timeout=30)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("engineer-runtime", result.stdout.strip())
                settings = (tomllib.loads((ns / "config.toml").read_text()) if host == "codex"
                            else json.loads((ns / "settings.json").read_text()))
                registered = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
                event = {"tool_name": "Write", "cwd": str(self.target),
                         "tool_input": {"file_path": str(self.base / "outside.txt")}}
                result = subprocess.run([shell, "-c", registered], cwd=self.base, env=env,
                                        input=json.dumps(event), capture_output=True, text=True,
                                        encoding="utf-8", timeout=30)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("Write target is outside", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_retired_directories_are_excluded_even_from_older_sources(self):
        source = self.base / "legacy-source"
        git(self.source, "clone", "--quiet", "--no-hardlinks", str(self.source), str(source))
        git(source, "config", "user.name", "Installer Fixture")
        git(source, "config", "user.email", "fixture@example.invalid")
        retired = ("guides", "maintenance", "engineer/guides", "engineer/maintenance",
                   "bin/guides", "bin/maintenance")
        for directory in retired:
            path = source / directory / "legacy.md"
            path.parent.mkdir(parents=True)
            path.write_text("Retired authoring material must never be installed.\n", encoding="utf-8")
        git(source, "add", *retired)
        git(source, "commit", "-m", "Legacy source with retired folders")
        pin = git(source, "rev-parse", "HEAD")
        for host in ("codex", "claude"):
            for scope in ("local", "global"):
                with self.subTest(host=host, scope=scope):
                    payload = installer.exports(source, pin, self.target, host, scope)["payload"]
                    self.assertFalse(any({"guides", "maintenance"} & set(Path(name).parts[:-1])
                                         for name in payload))
                    self.assertIn("." + host + "/engineer/bin/engineer.py", payload)

    def test_install_preserves_project_instructions_settings_and_planning(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                namespace = self.target / ("." + host)
                namespace.mkdir(parents=True)
                entry = self.target / ("AGENTS.md" if host == "codex" else "CLAUDE.md")
                entry.write_bytes(b"# Customer instructions\r\nPreserve billing invariants.\r\n")
                planning = self.target / ".planning/PROJECT.md"
                planning.parent.mkdir()
                planning.write_bytes(b"# Approved customer scope\r\n")
                if host == "codex":
                    config_path = namespace / "config.toml"
                    config_path.write_text('model = "keep-model"\n[agents]\nmax_threads = 3\n')
                else:
                    config_path = namespace / "settings.json"
                    config_path.write_text(json.dumps({"env": {"KEEP": "yes"}, "hooks": {"PreToolUse": [
                        {"matcher": "Read", "hooks": [{"type": "command", "command": "keep-hook"}]}]}}))
                self.install(host)
                self.assertTrue(entry.read_bytes().startswith(b"# Customer instructions\r\n"))
                self.assertEqual(b"# Approved customer scope\r\n", planning.read_bytes())
                config = (tomllib.loads(config_path.read_text()) if host == "codex"
                          else json.loads(config_path.read_text()))
                if host == "codex":
                    self.assertEqual("keep-model", config["model"])
                    self.assertEqual(3, config["agents"]["max_threads"])
                else:
                    self.assertEqual("yes", config["env"]["KEEP"])
                    self.assertEqual("keep-hook", config["hooks"]["PreToolUse"][0]["hooks"][0]["command"])

    def test_conflicts_are_incomplete_preserved_and_explicit_replacement_is_backed_up(self):
        self.install()
        customized = self.target / ".codex/commands/ship.md"
        customized.write_bytes(b"# Customer shipping process\n")
        preview = self.install("codex", "local", "--update", "--dry-run")
        self.assertFalse(preview["complete"])
        entry = next(e for e in preview["entries"] if e["path"] == ".codex/commands/ship.md")
        self.assertEqual("conflict", entry["action"])
        result = self.apply_plan(preview)
        self.assertFalse(result["complete"])
        self.assertEqual(b"# Customer shipping process\n", customized.read_bytes())
        preview = self.install("codex", "local", "--update", "--dry-run")
        entry = next(e for e in preview["entries"] if e["path"] == ".codex/commands/ship.md")
        entry["resolution"] = "backup-and-replace"
        result = self.apply_plan(preview, "--select", entry["path"])
        self.assertTrue(result["complete"])
        journal = json.loads((Path(result["backup"]) / "journal.json").read_text())
        change = next(e for e in journal["changes"] if e["path"] == entry["path"])
        self.assertEqual(b"# Customer shipping process\n", (Path(result["backup"]) / change["backup"]).read_bytes())

    def test_update_pins_revision_and_rollback_restores_previous_bytes(self):
        self.install()
        before = (self.target / ".codex/commands/ship.md").read_bytes()
        updated = self.source / "commands/ship.md"
        original = updated.read_bytes()
        try:
            updated.write_bytes(original + b"\n<!-- fixture update -->\n")
            git(self.source, "add", "commands/ship.md")
            git(self.source, "commit", "-m", "New pinned fixture revision")
            revision = git(self.source, "rev-parse", "HEAD")
            preview = self.install("codex", "local", "--update", "--dry-run", ref=revision)
            self.assertEqual(revision, preview["revision"])
            self.assertTrue(preview["complete"])
            applied = self.apply_plan(preview)
            self.assertIn(b"fixture update", (self.target / ".codex/commands/ship.md").read_bytes())
            self.cli("--target", self.target, "--host", "codex", "--rollback", applied["backup"])
            self.assertEqual(before, (self.target / ".codex/commands/ship.md").read_bytes())
            manifest = json.loads((self.target / ".codex/engineer-install/manifest.json").read_text())
            self.assertEqual(self.pin, manifest["revision"])
        finally:
            updated.write_bytes(original)

    def test_unknown_javascript_still_refuses_before_any_install_write(self):
        content = b'```bash\nnode -e \'require("unknown-runtime").mutate()\'\n```\n'
        source = self.base / "unsupported-source"
        (source / "engineer/bin").mkdir(parents=True)
        (source / "commands").mkdir()
        (source / "engineer/bin/engineer.py").write_text("# Populated fixture runtime\n")
        (source / "commands/unknown.md").write_bytes(content)
        git(source, "init", "-b", "main")
        git(source, "config", "user.name", "Installer Fixture")
        git(source, "config", "user.email", "fixture@example.invalid")
        git(source, "add", "engineer", "commands")
        git(source, "commit", "-m", "Unsupported JavaScript fixture")
        failure = self.cli("--source", source, "--ref", "HEAD", "--target", self.target,
                           "--host", "codex", "--local", expected=2)
        self.assertEqual("export-blocked", failure["error"])
        self.assertEqual("unported-runtime-javascript", failure["findings"][0]["code"])
        self.assertFalse(self.target.exists())

    def test_stale_target_and_review_token_fail_without_overwriting_changes(self):
        preview = self.install("codex", "local", "--dry-run")
        custom = self.target / "AGENTS.md"
        custom.parent.mkdir(parents=True)
        custom.write_bytes(b"# New instructions since preview\n")
        failure = self.apply_plan(preview, expected=2)
        self.assertEqual("plan-drift", failure["error"])
        self.assertEqual(b"# New instructions since preview\n", custom.read_bytes())
        path = self.base / "bad-token.json"
        path.write_text(json.dumps(preview))
        failure = self.cli("--apply", path, "--reviewed-plan-sha256", "0" * 64, expected=2)
        self.assertEqual("review-token-mismatch", failure["error"])

    def test_installed_bootstrap_runs_from_project_root_with_relative_path(self):
        shell = posix_shell.find_posix_shell("bash")
        if not shell:
            self.skipTest("No POSIX shell is installed")
        self.install()
        namespace = Path(".codex")
        source = '_ENGINEER_SHIM_NAME="engineer_run"; obsolete bootstrap\nengineer_run query runtime-identity --pick packageName --raw\n'
        exported = installer.adapt(source.encode(), "codex", namespace,
                                   "engineer/workflows/smoke.sh", []).decode()
        env = {**os.environ, "ENGINEER_ROOT": str(self.target), "ENGINEER_HOST": "codex"}
        result = subprocess.run([shell, "-c", exported], cwd=self.target, env=env,
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("engineer-runtime", result.stdout.strip())

    def test_reviewfix_claude_mixed_hook_group_preserves_siblings_and_metadata(self):
        self.install("claude")
        settings_path = self.target / ".claude/settings.json"
        settings = json.loads(settings_path.read_text())
        own = settings["hooks"]["PreToolUse"][0]["hooks"][0]
        legacy = ('"' + sys.executable + '" -I "' + str(self.target / ".claude/hooks/worktree-path-guard.py")
                  + '" --host claude')
        siblings = [{"type": "command", "command": "keep-first", "timeout": 7},
                    {"type": "command", "command": "keep-last", "timeout": 19}]
        previous = shlex.join(["previous-python-install/python", "-I",
                               (self.target / ".claude/hooks/worktree-path-guard.py").as_posix(),
                               "--host", "claude"])
        original = {"matcher": "Write|Edit", "timeout": 23, "custom_metadata": {"keep": True},
                    "hooks": [siblings[0], own, {**own, "command": legacy},
                              {**own, "command": previous}, siblings[1]]}
        settings["hooks"]["PreToolUse"] = [original]
        settings_path.write_text(json.dumps(settings))
        self.install("claude")
        refreshed = json.loads(settings_path.read_text())["hooks"]["PreToolUse"]
        self.assertEqual({**original, "hooks": siblings}, refreshed[0])
        managed = [hook for group in refreshed for hook in group["hooks"]
                   if hook.get("command") in (own["command"], legacy)]
        self.assertEqual([own], managed)
        before = settings_path.read_bytes()
        self.assertTrue(self.install("claude")["no_op"])
        self.assertEqual(before, settings_path.read_bytes())

    def test_reviewfix_registered_hook_executes_literal_paths_and_retains_advice(self):
        shell = posix_shell.find_posix_shell("bash")
        if not shell:
            self.skipTest("No POSIX shell is installed")
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / (host + " project $ENGINEER_REVIEW_LITERAL ' $(printf injected)")
                self.target.mkdir()
                git(self.target, "init", "-b", "main")
                self.install(host)
                namespace = self.target / ("." + host)
                settings = (tomllib.loads((namespace / "config.toml").read_text()) if host == "codex"
                            else json.loads((namespace / "settings.json").read_text()))
                registered = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
                payload = {"tool_name": "Write", "cwd": str(self.target),
                           "tool_input": {"file_path": str(self.base / "outside-checkout.txt")}}
                subdirectory = self.target / "src/nested"
                subdirectory.mkdir(parents=True)
                result = subprocess.run([shell, "-c", registered], cwd=subdirectory, input=json.dumps(payload),
                                        env={**os.environ, "ENGINEER_REVIEW_LITERAL": "expanded"},
                                        capture_output=True, text=True, encoding="utf-8", timeout=30)
                self.assertEqual(0, result.returncode, result.stderr)
                advice = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertIn("Write target is outside the actual assigned checkout", advice)

    def test_reviewfix_partial_selection_does_not_claim_unowned_identical_exports(self):
        source = self.base / "minimal-source"
        (source / "engineer/bin").mkdir(parents=True)
        (source / "commands").mkdir()
        (source / "engineer/bin/engineer.py").write_text("# Fixture runtime\n")
        (source / "commands/task.md").write_text("# Fixture command\n")
        git(source, "init", "-b", "main")
        git(source, "config", "user.name", "Installer Fixture")
        git(source, "config", "user.email", "fixture@example.invalid")
        git(source, "add", "engineer", "commands")
        git(source, "commit", "-m", "Minimal source ownership fixture")
        exported = installer.exports(source, "HEAD", self.target, "codex", "local", no_hooks=True)
        self.assertEqual(5, len(exported["payload"]))
        for name, (data, mode) in exported["payload"].items():
            installer.atomic(self.target / name, data, mode)
        preview = self.cli("--source", source, "--ref", "HEAD", "--target", self.target,
                           "--host", "codex", "--local", "--no-hooks", "--dry-run")
        self.assertTrue(all(e["action"] == "unchanged" for e in preview["entries"]))
        selected = preview["entries"][0]["path"]
        applied = self.apply_plan(preview, "--select", selected)
        self.assertFalse(applied["complete"])
        manifest_path = self.target / ".codex/engineer-install/manifest.json"
        manifest = json.loads(manifest_path.read_text())
        self.assertFalse(manifest["complete"])
        self.assertEqual([selected], list(manifest["files"]))
        preview = self.cli("--source", source, "--ref", "HEAD", "--target", self.target,
                           "--host", "codex", "--local", "--no-hooks", "--dry-run")
        self.assertTrue(self.apply_plan(preview)["complete"])
        self.assertEqual(5, len(json.loads(manifest_path.read_text())["files"]))


class ExportJsonAdapters(unittest.TestCase):
    def execute(self, script, value=None, env=None, arguments=()):
        source = "node -e " + shlex.quote(script)
        converted = transforms._node_calls(source, lambda verb: "unused-runtime " + verb, "workflow.md")
        self.assertNotIn("node -e", converted)
        argv = shlex.split(converted)
        argv[0] = sys.executable
        return subprocess.run([*argv, *arguments], input=json.dumps(value),
                              env={**os.environ, **(env or {})}, capture_output=True,
                              text=True, encoding="utf-8", timeout=10)

    def test_json_adapters_preserve_scope_and_validate_arrays(self):
        script = ('let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const '
                  'v=JSON.parse(s).files_deleted||[];if(!Array.isArray(v)||v.some(x=>typeof '
                  'x!=="string"))process.exit(1);process.stdout.write(JSON.stringify(v))})')
        for value in ({}, {"files_deleted": None}, {"files_deleted": ["path with spaces", "quote'and$dollar"]}):
            result = self.execute(script, value)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(value.get("files_deleted") or [], json.loads(result.stdout))
        for value in ({"files_deleted": {}}, {"files_deleted": [42]}, {"files_deleted": "src"}):
            self.assertNotEqual(0, self.execute(script, value).returncode)
        result = self.execute('process.stdout.write(JSON.stringify(process.argv.slice(1)))',
                              arguments=("one value", "two'$") )
        self.assertEqual(["one value", "two'$"], json.loads(result.stdout))
        result = self.execute('process.stdout.write(JSON.stringify([...new Set([process.env.EXPECTED_BASE,process.env.QUICK_PLAN_PARENT].filter(Boolean))]))',
                              env={"EXPECTED_BASE": "same", "QUICK_PLAN_PARENT": "same"})
        self.assertEqual(["same"], json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
