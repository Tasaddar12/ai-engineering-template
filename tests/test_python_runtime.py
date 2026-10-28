"""Exercise the actual source and relocated Python helper entrypoints."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase

ROOT = Path(__file__).resolve().parents[1]


class PythonRuntimeEntrypoints(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = {**os.environ, "ENGINEER_ROOT": str(self.root), "ENGINEER_HOST": "codex"}

    def call(self, entry, *args, stdin=None, status=0):
        result = subprocess.run([sys.executable, "-I", str(entry), *args], cwd=self.root,
                                env=self.env, input=stdin, text=True, encoding="utf-8", capture_output=True, timeout=30)
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
        installed = self.root / "café/.codex/engineer/bin"
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
                identity = json.loads(self.call(directory / "engineer.py", "query", "runtime-identity").stdout)
                self.assertEqual("engineer-runtime", identity["packageName"])
                if directory == installed:
                    self.assertIn("café", identity["namespace"])

    def test_cli_help_and_invalid_cwd_are_structured(self):
        self.assertIn("spec.ui-probe", json.loads(self.cli("help").stdout)["verbs"])
        self.cli("no-such-verb", status=2)
        self.call(ROOT / "engineer/bin/engineer.py", "--cwd", str(self.root / "missing"), status=2)


class PythonDurableFlows(RuntimeCase):
    def test_new_state_version_and_legacy_metadata_preservation(self):
        self.init_records()
        path = self.root / ".planning/STATE.md"
        self.assertIn("workflow_state_version:", path.read_text(encoding="utf-8"))
        for legacy in ("engineer_state_version", "gsd_state_version"):
            self.put(".planning/STATE.md", "---\n" + legacy + ": '1.0'\nstatus: planning\n---\n# Project State\n")
            self.cli("state.patch", json.dumps({"status": "executing"}))
            content = path.read_text(encoding="utf-8")
            self.assertIn(legacy + ":", content)
            self.assertNotIn("workflow_state_version:", content)

    def test_idea_capture_update_and_pipeline_promotion_are_idempotent(self):
        captured = self.cli("idea.capture", "--title", "Cache invalidation", "--content", "Track cache dependencies", "--key", "cache-1")
        identifier = captured["idea"]["id"]
        duplicate = self.cli("idea.capture", "--title", "Cache invalidation", "--content", "Track cache dependencies", "--key", "cache-1")
        self.assertTrue(duplicate["duplicate"])
        self.cli("idea.update", identifier, "--context", "Investigate scoped invalidation")
        updated = self.cli("idea.get", identifier)["idea"]
        self.assertEqual("Track cache dependencies", updated["original"]["content"])
        self.assertEqual(1, len(updated["history"]))
        promoted = self.cli("idea.promote", identifier, "--to", "pipeline")
        pipeline = promoted["result"]["id"]
        self.assertTrue(self.cli("idea.promote", identifier, "--to", "pipeline")["duplicate"])
        self.assertEqual(identifier.lower(), self.cli("pipeline.status", pipeline)["tasks"][0]["id"])
        self.assertEqual([pipeline], self.cli("manager.status")["pipelines"])
        self.assertTrue(self.cli("manager.cancel", pipeline)["cancel_requested"])
        self.assertTrue(self.cli("pipeline.status", pipeline)["cancel_requested"])

    def test_pipeline_dependency_validation_and_host_authority(self):
        tasks = [{"id": "first", "prompt": "Implement the first task"},
                 {"id": "second", "prompt": "Implement the next task", "depends_on": ["first"]}]
        created = self.cli("manager.enqueue", "--id", "queue-1", "--tasks", json.dumps(tasks))
        self.assertEqual("pending", created["status"])
        self.assertTrue(self.cli("pipeline.create", "--id", "queue-1", "--tasks", json.dumps(tasks))["reused"])
        self.cli("pipeline.run", "queue-1", "--host", "codex", "--command-json", json.dumps([sys.executable, "-c", "print('not a host')"]), status=2, raw=True)
        self.assertEqual([], self.cli("pipeline.status", "queue-1")["tasks"][0]["attempts"])
        tasks[0]["depends_on"] = ["second"]
        self.cli("pipeline.create", "--tasks", json.dumps(tasks), status=2, raw=True)

    def test_manager_recommends_discussion_and_enforces_phase_authority(self):
        self.phase("Discuss before implementation")
        dashboard = self.cli("manager.dashboard")
        self.assertEqual("discuss-phase", dashboard["recommended_actions"][0]["action"])
        self.assertTrue(dashboard["recommended_actions"][0]["requires_input"])
        self.cli("manager.enqueue", "--phase", "1", status=1, raw=True)
        self.cli("manager.enqueue", "--phase", "1", "--authorize-execution", status=1, raw=True)
        self.assertEqual([], self.cli("pipeline.status", "--list")["pipelines"])


if __name__ == "__main__":
    unittest.main()
