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

    def test_spec_fallback_supplied_requires_authored_rows(self):
        for name, text, present, supplied in (
            ("missing.md", None, False, False),
            ("absent.md", "# Specification\n", False, False),
            ("empty.md", "## Edge Coverage\n| Edge | R |\n|---|---|\n", True, False),
            ("populated.md", "## Edge Coverage\n| Edge | R |\n|---|---|\n| Empty | R1 |\n", True, True),
        ):
            for kind in ("edges", "prohibitions"):
                with self.subTest(name=name, kind=kind):
                    if text is not None:
                        content = text.replace("Edge Coverage", "Prohibitions") if kind == "prohibitions" else text
                        (self.root / name).write_text(content, encoding="utf-8")
                    result = json.loads(self.cli("spec.section", name, kind).stdout)
                    self.assertEqual(present, result["present"])
                    self.assertEqual(supplied, result["supplied"])

    def test_native_fallow_normalizes_without_discarding_findings(self):
        report = {"dead_code": {"unused_exports": [{"path": "src/app.py", "export_name": "old", "line": 9}]}}
        result = json.loads(self.cli("review.normalize-fallow", "--stdin", stdin=json.dumps(report)).stdout)
        self.assertEqual(1, result["summary"]["total"])
        self.assertEqual("unused_export", result["findings"][0]["type"])
        self.cli("review.normalize-fallow", "--stdin", stdin="{}", status=2)

    def test_native_fallow_rejects_malformed_sections_and_preserves_empty_reports(self):
        for malformed in ({"schema_version": 3, "dead_code": "invalid section"},
                          {"dead_code": {"unused_exports": {}}},
                          {"duplication": {"clone_groups": ["bad"]}},
                          {"dead_code": {"circular_dependencies": [{"files": "a.py"}]}}):
            with self.subTest(report=malformed):
                self.cli("review.normalize-fallow", "--stdin", stdin=json.dumps(malformed), status=2)
        for empty in ({"dead_code": {}}, {"duplication": {"clone_groups": []}}, {"dead_code": None}):
            with self.subTest(report=empty):
                result = json.loads(self.cli("review.normalize-fallow", "--stdin", stdin=json.dumps(empty)).stdout)
                self.assertEqual(0, result["summary"]["total"])

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
    def test_phase_letter_and_multidot_ids_add_find_sort_insert_and_manager(self):
        self.init_records()
        for identifier in ("2", "1a", "1.2", "1.1.1", "1"):
            self.cli("phase.add", "Named " + identifier, "--number", identifier)
        self.assertEqual("01a", self.cli("find-phase", "1a")["number"])
        self.assertEqual("01.1.1", self.cli("find-phase", "01.01.01")["number"])
        phases = self.cli("phases.list")["phases"]
        self.assertEqual(["01", "01.1.1", "01.2", "01a", "02"], [phase["number"] for phase in phases])
        self.assertEqual("01a.1", self.cli("phase.insert", "1a", "Inserted letter child")["phase"])
        self.assertEqual("01.1.1.1", self.cli("phase.insert", "1.1.1", "Nested child")["phase"])
        self.cli("phase.edit", "2", "--depends-on", "Phase 1a and Phase 1.1.1")
        dependencies = self.cli("roadmap.get-phase", "2")["dependencies"]
        self.assertEqual(["01a", "01.1.1"], dependencies)
        self.assertEqual(7, self.cli("manager.status")["phase_count"])
        self.assertEqual("03", self.cli("phase.add", "Next integer")["phase"])

    def release_fixture(self):
        for name in ("backend", "frontend"):
            directory = self.root / name
            directory.mkdir()
            for args in (("init", "-b", "main"), ("config", "user.name", "Release Test"), ("config", "user.email", "release@example.invalid")):
                self.git("-C", str(directory), *args)
            (directory / "app.txt").write_text("release fixture", encoding="utf-8")
            self.git("-C", str(directory), "add", "app.txt")
            self.git("-C", str(directory), "commit", "-m", "fixture")
        self.put(".planning/config.yaml", json.dumps({"sub_repos": ["backend", "frontend"], "git": {"create_tag": True}}))
        return [{"repo": name, "tag": "v1.0", "ref": "HEAD"} for name in ("backend", "frontend")]

    def test_release_tags_preflight_annotated_creation_and_idempotence(self):
        entries = self.release_fixture()
        self.put("tags.json", json.dumps({"repositories": entries}))
        preview = self.cli("milestone.release-tags", "--map", "tags.json", "--dry-run")
        self.assertEqual(["would_tag", "would_tag"], [item["status"] for item in preview["results"]])
        self.assertEqual("", self.git("-C", str(self.root / "backend"), "tag", "--list"))
        created = self.cli("milestone.release-tags", "--map", "tags.json")
        self.assertEqual(2, created["created"])
        self.assertFalse(created["pushed"])
        self.assertEqual("tag", self.git("-C", str(self.root / "backend"), "cat-file", "-t", "refs/tags/v1.0"))
        repeat = self.cli("milestone.release-tags", "--map", "tags.json")
        self.assertEqual(["already_tagged"] * 2, [item["status"] for item in repeat["results"]])
        frontend = self.root / "frontend"
        (frontend / "app.txt").write_text("next release", encoding="utf-8")
        self.git("-C", str(frontend), "commit", "-am", "next fixture")
        self.cli("milestone.release-tags", "--map", "tags.json", status=1, raw=True)
        self.cli("config-set", "git.create_tag", "false")
        for entry in entries:
            entry["tag"] = "v2.0"
        self.put("tags.json", json.dumps(entries))
        disabled = self.cli("milestone.release-tags", "--map", "tags.json")
        self.assertEqual(["skipped"] * 2, [item["status"] for item in disabled["results"]])
        self.assertEqual("v1.0", self.git("-C", str(frontend), "tag", "--list"))

    def test_release_tags_invalid_later_entry_prevents_partial_writes(self):
        entries = self.release_fixture()
        entries[1]["tag"] = "bad tag"
        self.put("tags.json", json.dumps(entries))
        self.cli("milestone.release-tags", "--map", "tags.json", status=2, raw=True)
        self.assertEqual("", self.git("-C", str(self.root / "backend"), "tag", "--list"))
        entries[1]["tag"] = "v1.0"
        entries[1]["repo"] = "unconfigured"
        self.put("tags.json", json.dumps(entries))
        self.cli("milestone.release-tags", "--map", "tags.json", status=2, raw=True)
        self.assertEqual("", self.git("-C", str(self.root / "backend"), "tag", "--list"))

    def test_release_map_resume_archives_recorded_value(self):
        packet = {"repositories": [{"repo": "backend", "tag": None, "status": "unreleased"}]}
        self.put("tags.json", json.dumps(packet))
        (self.root / ".planning/phases").mkdir(parents=True)
        journal = {"version": "v1.0", "name": "Milestone", "state": "prepared", "archive_phases": False,
                   "phase_inventory": {}, "record_hashes": {}, "archive_id": "fixture", "block": "## v1.0: Milestone\n",
                   "phase_count": 1, "plan_count": 1, "task_count": 1, "release_map": packet}
        self.put(".planning/milestones/operations/v1.0.json", json.dumps(journal))
        self.cli("milestone.complete", "v1.0", "--name", "Milestone", "--no-archive-phases", "--confirm", "--release-map", "tags.json")
        self.put("tags.json", "[]")
        archived = self.root / ".planning/milestones/v1.0-RELEASE-MAP.json"
        self.assertEqual(packet, json.loads(archived.read_text(encoding="utf-8")))

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
