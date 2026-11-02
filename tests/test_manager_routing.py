"""Execute the manager's documented capability resolver against a stub runtime."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
if os.name == "nt" and Path("C:/Program Files/Git/bin/bash.exe").is_file():
    BASH = "C:/Program Files/Git/bin/bash.exe"


@unittest.skipUnless(BASH, "Bash is required for the documented manager resolver")
class ManagerRoutingTests(unittest.TestCase):
    def resolver(self):
        blocks = re.findall(r"```bash\n(.*?)```", (ROOT / "engineer/workflows/manager.md").read_text(encoding="utf-8"), re.S)
        return next(block for block in blocks if "if FLATTEN=" in block)

    def run_resolver(self, value, status=0):
        # Count calls outside command substitution; subsequent calls deliberately
        # flip the result, exposing accidental repeated capability queries.
        script = r'''
engineer_run() {
  printf '%s\n' "$*" >> query-calls
  if [ "$(wc -l < query-calls)" -gt 1 ]; then
    printf '%s\n' false
  else
    printf '%s\n' "$QUERY_VALUE"
  fi
  return "$QUERY_STATUS"
}
''' + self.resolver() + r'''
printf 'resolved:%s:%s\n' "$FLATTEN" "$PLAN_EXECUTE_MODE"
'''
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([BASH, "--noprofile", "--norc", "-c", script], cwd=directory,
                                    env={**os.environ, "QUERY_VALUE": value, "QUERY_STATUS": str(status)},
                                    capture_output=True, text=True)
            calls = (Path(directory) / "query-calls").read_text().splitlines()
        self.assertEqual(["query dispatch-should-flatten --raw"], calls)
        return result

    def test_true_selects_inline_once(self):
        result = self.run_resolver("true")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("resolved:true:inline\n", result.stdout)

    def test_false_selects_background_once(self):
        result = self.run_resolver("false")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("resolved:false:background\n", result.stdout)

    def test_invalid_values_stop_before_dispatch(self):
        for value in ("", "True", "null", "0", "true false", "true\nfalse"):
            with self.subTest(value=value):
                result = self.run_resolver(value)
                self.assertNotEqual(0, result.returncode)
                self.assertIn("invalid dispatch-should-flatten result", result.stderr)
                self.assertNotIn("resolved:", result.stdout)

    def test_query_failure_does_not_select_a_route_even_with_boolean_output(self):
        result = self.run_resolver("true", status=7)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("capability query failed", result.stderr)
        self.assertNotIn("resolved:", result.stdout)

    def test_documented_bash_blocks_parse(self):
        text = (ROOT / "engineer/workflows/manager.md").read_text(encoding="utf-8")
        for block in re.findall(r"```bash\n(.*?)```", text, re.S):
            result = subprocess.run([BASH, "-n"], input=block, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
