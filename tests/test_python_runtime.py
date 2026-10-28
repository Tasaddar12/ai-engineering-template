"""Exercise the actual source and relocated Python helper entrypoints."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PythonRuntimeEntrypoints(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {**os.environ, "ENGINEER_ROOT": str(self.root), "ENGINEER_HOST": "codex"}

    def call(self, entry, *args, stdin=None, status=0):
        result = subprocess.run([sys.executable, "-I", str(entry), *args], cwd=self.root,
                                env=self.env, input=stdin, text=True, capture_output=True, timeout=30)
        self.assertEqual(status, result.returncode, result.stderr + result.stdout)
        self.assertNotIn("Traceback", result.stderr)
        return result

    def cli(self, *args, **kwargs):
        return self.call(ROOT / "engineer/bin/engineer.py", "query", *args, **kwargs)

    def test_depth_uses_strongest_directory_rule_and_validates_overrides(self):
        payload = {"files": ["src/auth/login.py"], "overrides": [
            {"paths": ["src"], "depth": "quick"}, {"paths": ["src/auth"], "depth": "deep"}]}
        result = json.loads(self.cli("review.depth", "--stdin", stdin=json.dumps(payload)).stdout)
        self.assertEqual(("deep", 1, 1), (result["depth"], result["matchedRule"]["index"], result["fileCount"]))
        payload["overrides"][0]["paths"] = ["../outside"]
        result = json.loads(self.cli("review.depth", "--stdin", stdin=json.dumps(payload)).stdout)
        self.assertFalse(result["ok"])
        self.assertEqual("path_traversal", result["errors"][0]["reason"])

    def test_ui_probe_proposal_auto_and_invalid_inputs(self):
        source = json.dumps([{"id": "UI1", "text": "A form", "elements": ["form"]}])
        proposal = json.loads(self.cli("spec.ui-probe", "--propose", "--stdin", stdin=source).stdout)
        self.assertEqual(["form"], proposal[0]["kinds"])
        result = json.loads(self.cli("spec.ui-probe", "--auto", "--stdin", stdin=source).stdout)
        self.assertGreater(result["coverage"]["resolved"], 0)
        self.assertEqual(0, result["coverage"]["unresolved"])
        self.cli("spec.ui-probe", "--stdin", stdin="{}", status=2)

    def test_spec_section_keeps_status_and_authored_items(self):
        (self.root / "SPEC.md").write_text("## Edge Coverage\n| Edge | R |\n|---|---|\n| Empty | R1 |\n", encoding="utf-8")
        result = json.loads(self.cli("spec.section", "SPEC.md", "edges").stdout)
        self.assertTrue(result["present"])
        self.assertEqual(1, result["dataRows"])
        self.assertEqual(["Empty | R1"], result["items"])

    def test_native_fallow_normalizes_without_discarding_findings(self):
        report = {"dead_code": {"unused_exports": [{"path": "src/app.py", "export_name": "old", "line": 9}]}}
        result = json.loads(self.cli("review.normalize-fallow", "--stdin", stdin=json.dumps(report)).stdout)
        self.assertEqual(1, result["summary"]["total"])
        self.assertEqual("unused_export", result["findings"][0]["type"])
        self.cli("review.normalize-fallow", "--stdin", stdin="{}", status=2)

    def test_helper_isolated_source_and_installed_copy(self):
        installed = self.root / ".codex/engineer/bin"
        shutil.copytree(ROOT / "engineer/bin", installed, ignore=shutil.ignore_patterns("__pycache__"))
        source = self.root / "input.json"
        source.write_text('[{"id":"R1","text":"A list of entries"}]', encoding="utf-8")
        for directory in (ROOT / "engineer/bin", installed):
            with self.subTest(directory=directory):
                entry = directory / "helper.py"
                self.assertIn("gen-health-docs", self.call(entry, "--help").stdout)
                result = self.call(entry, "edge-probe", str(source))
                self.assertGreater(json.loads(result.stdout)["coverage"]["applicable"], 0)
                self.call(entry, "edge-probe", status=2)
                self.call(entry, "../outside", status=2)
                self.assertEqual("engineer-runtime", json.loads(self.call(directory / "engineer.py", "query", "runtime-identity").stdout)["packageName"])

    def test_cli_help_and_invalid_cwd_are_structured(self):
        self.assertIn("spec.ui-probe", json.loads(self.cli("help").stdout)["verbs"])
        self.cli("no-such-verb", status=2)
        self.call(ROOT / "engineer/bin/engineer.py", "--cwd", str(self.root / "missing"), status=2)


if __name__ == "__main__":
    unittest.main()
