"""Portable installed artifacts, including the host discovery surface."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib
import unittest

import test_installer_runtime as fixtures

installer, git, posix_shell = fixtures.installer, fixtures.git, fixtures.posix_shell


class PortableInstallerTests(unittest.TestCase):
    setUpClass = classmethod(fixtures.CurrentInstallerTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.CurrentInstallerTests.tearDownClass.__func__)
    setUp = fixtures.CurrentInstallerTests.setUp
    cli = fixtures.CurrentInstallerTests.cli
    install = fixtures.CurrentInstallerTests.install
    apply_plan = fixtures.CurrentInstallerTests.apply_plan

    def test_every_export_is_independent_of_checkout_and_interpreter(self):
        for host in ("codex", "claude"):
            for scope in ("local", "global"):
                with self.subTest(host=host, scope=scope):
                    a = installer.exports(self.source, self.pin, self.target, host, scope)
                    b = installer.exports(self.source, self.pin, self.base / "other checkout", host, scope)
                    self.assertEqual(set(a["payload"]), set(b["payload"]))
                    self.assertEqual([], [name for name in a["payload"]
                                          if a["payload"][name] != b["payload"][name]])
                    for name, (content, _) in a["payload"].items():
                        for path in (self.source, self.target, Path(sys.executable)):
                            for spelling in (str(path), path.as_posix()):
                                self.assertNotIn(spelling.encode(), content, name)

    def test_native_codex_skills_and_portable_manifest(self):
        self.install()
        config = tomllib.loads((self.target / ".codex/config.toml").read_text())
        for record in config["skills"]["config"]:
            self.assertEqual({"name", "enabled"}, set(record))
            skill = self.target / ".agents/skills" / record["name"] / "SKILL.md"
            self.assertTrue(skill.is_file(), skill)
            self.assertIn("name: " + record["name"], skill.read_text())
        manifest = (self.target / ".codex/engineer-install/manifest.json").read_text()
        self.assertNotIn(self.source.as_posix(), manifest)
        self.assertNotIn(str(self.source).replace("\\", "\\\\"), manifest)
        self.assertEqual("git:explicit-source-required", json.loads(manifest)["source"])
        self.assertFalse((self.target / ".codex/engineer-install/backups").exists())
        for name in [*json.loads(manifest)["files"], ".codex/engineer-install/manifest.json"]:
            content = (self.target / name).read_bytes()
            for path in (self.source, self.target, Path(sys.executable)):
                for spelling in (str(path), path.as_posix(), str(path).replace("\\", "\\\\")):
                    self.assertNotIn(spelling.encode(), content, name)
        runtime = self.target / ".codex/engineer/bin/engineer.py"
        base = [sys.executable, "-I", str(runtime), "query"]
        env = {**os.environ, "ENGINEER_ROOT": str(self.target), "ENGINEER_HOST": "codex"}
        result = subprocess.run([*base, "update-context", "--config-dir", str(runtime.parents[2])],
                                capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["source_required"])
        result = subprocess.run([*base, "update.changes", "--ref", self.pin],
                                capture_output=True, text=True, env=env, timeout=30)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("pinned-update-required", result.stderr)
        result = subprocess.run([*base, "update.changes", "--ref", self.pin, "--source", str(self.source)],
                                capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(0, json.loads(result.stdout)["count"])

    def shell(self, command, cwd, env=None, payload=None):
        shell = posix_shell.find_posix_shell("bash")
        if not shell:
            self.skipTest("No POSIX shell is installed")
        result = subprocess.run([shell, "-c", command], cwd=cwd,
                                env={**os.environ, **(env or {})}, input=payload,
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        return result.stdout

    def exercise(self, checkout, namespace, host, env=None, scope="local"):
        nested = checkout / "nested $literal ' directory"
        nested.mkdir(parents=True, exist_ok=True)
        resolver = (namespace / "engineer/references/run-resolver.md").read_text()
        bootstrap = resolver.split("```bash\n", 1)[1].split("```", 1)[0]
        command = bootstrap + '\nengineer_run query runtime-identity --pick packageName --raw'
        self.assertEqual("engineer-runtime", self.shell(command, nested, env).strip())
        # An actual exported shell adapter must also resolve the live checkout,
        # even without a previously defined engineer_run function.
        source = b'```bash\nprintf \'{"items":[1,2]}\' | node -e \'JSON.parse(s).items.length\'\n```\n'
        converted = installer.adapt(source, host, namespace, "commands/check.md", [], scope).decode()
        self.assertNotIn("node -e", converted)
        command = converted.split("```bash\n", 1)[1].split("```", 1)[0]
        self.assertEqual("2", self.shell(command, nested, env).strip())
        settings = (tomllib.loads((namespace / "config.toml").read_text()) if host == "codex"
                    else json.loads((namespace / "settings.json").read_text()))
        hook = settings["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        payload = {"tool_name": "Write", "cwd": str(nested),
                   "tool_input": {"file_path": str(self.base / "outside.txt")}}
        advice = json.loads(self.shell(hook, nested, env, json.dumps(payload)))
        self.assertIn("outside the actual assigned checkout", advice["hookSpecificOutput"]["additionalContext"])

    def test_relocated_clone_and_linked_worktree_use_live_nested_checkout(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / (host + " original $literal ' target")
                self.target.mkdir()
                git(self.target, "init", "-b", "main")
                git(self.target, "config", "user.name", "Portable Fixture")
                git(self.target, "config", "user.email", "fixture@example.invalid")
                # Ownership deliberately hashes exact bytes. Isolate path
                # portability from the user's independent Git newline policy.
                git(self.target, "config", "core.autocrlf", "false")
                self.install(host)
                git(self.target, "add", "." + host, *( [".agents"] if host == "codex" else []),
                    "AGENTS.md" if host == "codex" else "CLAUDE.md")
                git(self.target, "commit", "-m", "Portable host installation")
                clone = self.base / (host + " relocated $literal ' clone")
                git(self.target, "clone", "--quiet", "--no-hardlinks", "-c", "core.autocrlf=false",
                    str(self.target), str(clone))
                worktree = self.base / (host + " linked $literal ' worktree")
                git(clone, "worktree", "add", "-b", "fixture-worker", str(worktree))
                # A stale host main-project hint must not redirect the hook/runtime.
                env = {"CLAUDE_PROJECT_DIR": str(self.target), "ENGINEER_ROOT": str(self.target)}
                for checkout in (clone, worktree):
                    self.exercise(checkout, checkout / ("." + host), host, env)
                    for wrapper in (checkout / ".codex/agents").glob("*.toml"):
                        role = tomllib.loads(wrapper.read_text())
                        self.assertTrue(role["developer_instructions"].startswith(
                            "Read and follow the complete role at .codex/agents/" + wrapper.stem + ".md before acting."))
                    self.target = checkout
                    self.assertTrue(self.install(host)["no_op"])
                # External machine-local journals are absent from Git exports.
                tracked = git(clone, "ls-files").splitlines()
                self.assertFalse(any("backups/" in path or "reviewed-plan" in path for path in tracked))

    def test_global_exports_resolve_default_and_custom_host_directories(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / (host + " home $literal ' source")
                self.install(host, "global")
                moved = self.base / (host + " home $literal ' moved")
                self.target.rename(moved)
                project = self.base / (host + " unrelated project")
                project.mkdir()
                git(project, "init", "-b", "main")
                namespace = moved / ("." + host)
                self.target = moved
                self.assertTrue(self.install(host, "global")["no_op"])
                env = {"HOME": str(moved), "CODEX_HOME": str(moved / ".codex"),
                       "CLAUDE_CONFIG_DIR": str(moved / ".claude")}
                self.exercise(project, namespace, host, env, "global")
                custom = moved / ("custom " + host + " $literal ' configuration")
                namespace.rename(custom)
                env["CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"] = str(custom)
                self.exercise(project, custom, host, env, "global")
                if host == "codex":
                    config = tomllib.loads((custom / "config.toml").read_text())
                    self.assertTrue(all((moved / ".agents/skills" / record["name"] / "SKILL.md").is_file()
                                        for record in config["skills"]["config"]))

    def test_external_transactions_remain_bound_and_legacy_backups_recover(self):
        installed = self.install()
        backup = Path(installed["backup"])
        self.assertFalse(backup.is_relative_to(self.target))
        binding = json.loads((backup.parent.parent / "binding.json").read_text())
        self.assertEqual({"target": str(self.target), "host": "codex"}, binding)
        # An exact legacy transaction is still recoverable after exporter upgrade.
        legacy = self.target / ".codex/engineer-install/backups" / backup.name
        legacy.parent.mkdir(parents=True)
        backup.rename(legacy)
        journal = json.loads((legacy / "journal.json").read_text())
        journal["target"] = str(self.base / "wrong target")
        (legacy / "journal.json").write_text(json.dumps(journal))
        failure = self.cli("--target", self.target, "--host", "codex", "--rollback", legacy, expected=2)
        self.assertEqual("rollback-target-mismatch", failure["error"])
        self.assertTrue((self.target / ".codex/config.toml").is_file())
        journal["target"] = str(self.target)
        (legacy / "journal.json").write_text(json.dumps(journal))
        self.assertTrue(self.cli("--target", self.target, "--host", "codex", "--rollback", legacy)["rolled_back"])
        self.assertFalse((self.target / ".codex/config.toml").exists())


if __name__ == "__main__":
    unittest.main()
