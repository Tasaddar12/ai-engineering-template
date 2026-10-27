import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
try:
    from .test_engineer_runtime import RuntimeCase, RUNTIME, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, RUNTIME, SOURCE


class CliContract(RuntimeCase):
    def test_identity_host_and_pick(self):
        self.assertEqual("engineer-runtime", self.cli("runtime-identity", "--pick", "packageName", raw=True))
        self.assertEqual("codex", self.cli("runtime-identity")["host"])
        self.cli("runtime-identity", "--pick", "absent.key", status=1, raw=True)

    def test_missing_config_and_explicit_defaults(self):
        self.cli("config-get", "workflow.absent", status=1, raw=True)
        self.assertEqual("x", self.cli("config-get", "workflow.absent", "--default", "x", "--raw", raw=True))
        self.assertEqual("", self.cli("config-get", "workflow.absent", "--default", "", "--raw", raw=True))
        self.assertEqual("false", self.cli("config-get", "workflow.tdd_mode", "--raw", raw=True))

    def test_real_yaml_config_and_frontmatter_types(self):
        self.put(".planning/config.yaml", """# project configuration
verification:
  commands:
    - name: tests
      argv: ["python", "-m", "unittest"]
      timeout: 30
workflow:
  tdd_mode: true # a comment
response_language: "en#US"
""")
        self.assertEqual(["python", "-m", "unittest"], self.cli("config-get", "verification.commands", "--pick", "0.argv"))
        self.cli("config-set", "workflow.code_review", "false")
        self.assertFalse(self.cli("config-get", "workflow.code_review"))

    def test_yaml_tags_and_duplicate_keys_are_rejected(self):
        for content in ("x: !!python/object:os.system foo\n", "x: 1\nx: 2\n", "x: &anchor value\n"):
            with self.subTest(content=content):
                self.put(".planning/config.yaml", content)
                self.cli("config-get", "x", status=2, raw=True)

    def test_installed_namespace_identity(self):
        destination = self.root/".claude/engineer/bin"
        shutil.copytree(SOURCE/"engineer/bin", destination)
        env = dict(self.env)
        env.pop("ENGINEER_HOST", None)
        result = subprocess.run([sys.executable, "-I", str(destination/"engineer.py"), "query", "runtime-identity"], cwd=self.root, env=env, text=True, encoding="utf-8", capture_output=True, check=True)
        self.assertEqual("claude", json.loads(result.stdout)["host"])

    def test_shim_when_posix_shell_available(self):
        shell = shutil.which("sh")
        if not shell:
            self.skipTest("POSIX shell unavailable")
        result = subprocess.run([shell, str(SOURCE/"engineer/bin/engineer_run"), "query", "runtime-identity", "--pick", "packageName"], cwd=self.root, env=self.env, text=True, encoding="utf-8", capture_output=True, check=True)
        self.assertEqual("engineer-runtime", result.stdout.strip())


class LauncherAndRegistryContract(RuntimeCase):
    def shell(self):
        shell = shutil.which("sh")
        if not shell:
            self.skipTest("POSIX shell unavailable")
        return shell

    def launch_snippet(self, snippet, environment):
        result = subprocess.run(
            [self.shell(), "-c", '. "$1"; engineer_run query runtime-identity; printf "%s\\n" "$ENGINEER_RUN"',
             "launcher-contract", snippet.as_posix()], cwd=self.root, env=environment,
            text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        document, launcher = result.stdout.rstrip().rsplit("\n", 1)
        return json.loads(document), launcher

    def test_launcher_snippet_selects_source_runtime(self):
        environment = {**self.env, "RUNTIME_DIR": SOURCE.as_posix()}
        environment.pop("ENGINEER_RUN", None)
        identity, launcher = self.launch_snippet(SOURCE / "engineer/workflows/_runtime-launcher.snippet.sh", environment)
        self.assertEqual("engineer-runtime", identity["packageName"])
        self.assertEqual("codex", identity["host"])
        self.assertTrue(launcher.replace("\\", "/").endswith("/engineer/bin/engineer_run"), launcher)
        self.assertNotIn("/.claude/", launcher)

    def test_launcher_snippet_selects_fake_claude_installed_runtime(self):
        installed = self.root / ".claude"
        shutil.copytree(SOURCE / "engineer/bin", installed / "engineer/bin")
        snippet = installed / "engineer/workflows/_runtime-launcher.snippet.sh"
        snippet.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE / "engineer/workflows/_runtime-launcher.snippet.sh", snippet)
        environment = dict(self.env)
        for key in ("ENGINEER_RUN", "ENGINEER_HOST", "RUNTIME_DIR"):
            environment.pop(key, None)
        nested = self.root / "src/nested"
        nested.mkdir(parents=True)
        # Selection must find the install from the project, including nested cwd.
        previous = self.root
        self.root = nested
        try:
            identity, launcher = self.launch_snippet(snippet, environment)
        finally:
            self.root = previous
        self.assertEqual("engineer-runtime", identity["packageName"])
        self.assertEqual("claude", identity["host"])
        self.assertTrue(launcher.replace("\\", "/").endswith("/.claude/engineer/bin/engineer_run"), launcher)

    def test_every_literal_workflow_verb_is_in_real_help_registry(self):
        registered = set(self.cli("help")["verbs"])
        calls = re.compile(r"\bengineer_run\s+query\s+([A-Za-z][A-Za-z0-9_]*(?:[.-][A-Za-z0-9_]+)*)(?![A-Za-z0-9_.-])")
        families = {"init", "check", "verify", "frontmatter", "quick-batch", "spec", "phase", "state", "roadmap", "worktree", "uat"}
        unknown, observed = [], set()
        for directory in ("agents", "commands", "engineer"):
            for path in sorted((SOURCE / directory).rglob("*")):
                if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeError:
                    continue
                for number, line in enumerate(text.splitlines(), 1):
                    for match in calls.finditer(line):
                        verb = match[1]
                        if verb in families:
                            subcommand = re.match(r"\s+([A-Za-z][A-Za-z0-9_-]*)", line[match.end():])
                            if subcommand:
                                verb += "." + subcommand[1]
                        observed.add(verb)
                        if verb not in registered:
                            unknown.append(f"{path.relative_to(SOURCE).as_posix()}:{number}: {verb}")
        self.assertTrue({"phase.add", "config-get", "handoff.write", "resolve-model"} <= observed)
        self.assertEqual([], unknown, "\n".join(unknown))
