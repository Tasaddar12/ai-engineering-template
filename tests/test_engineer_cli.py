import json
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
        result = subprocess.run([sys.executable, "-I", str(destination/"engineer.py"), "query", "runtime-identity"], cwd=self.root, env=env, text=True, capture_output=True, check=True)
        self.assertEqual("claude", json.loads(result.stdout)["host"])

    def test_shim_when_posix_shell_available(self):
        shell = shutil.which("sh")
        if not shell:
            self.skipTest("POSIX shell unavailable")
        result = subprocess.run([shell, str(SOURCE/"engineer/bin/engineer_run"), "query", "runtime-identity", "--pick", "packageName"], cwd=self.root, env=self.env, text=True, capture_output=True, check=True)
        self.assertEqual("engineer-runtime", result.stdout.strip())
