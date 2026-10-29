"""Exercise real validate.health CLI against disposable native repositories."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "engineer/bin/engineer.py"


class HealthRuntime(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="native-health-")
        self.addCleanup(temporary.cleanup)
        # CLI evidence paths are canonical, including Windows short TEMP aliases.
        self.root = Path(temporary.name).resolve()
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True, capture_output=True)

    def write(self, path, text):
        target = self.root / ".planning" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def initialized(self):
        self.write("PROJECT.md", "# Widget\n\n## What This Is\nA widget.\n## Core Value\nUseful.\n## Requirements\nREQ-01\n")
        self.write("REQUIREMENTS.md", "# Requirements\nREQ-01\n")
        self.write("ROADMAP.md", "# Roadmap\n\n- [ ] **Phase 01: Start**\n\n### Phase 01: Start\n")
        self.write("STATE.md", "# State\n\nPhase: 01 of 1 (Start)\nStatus: Planning\n")
        self.write("config.yaml", "model_profile: balanced\nworkflow:\n  nyquist_validation: true\n")

    def health(self, *flags):
        return self.runtime("validate.health", *flags)

    def runtime(self, *args):
        result = subprocess.run([sys.executable, "-I", str(CLI), "query", *args],
                                cwd=self.root, env={**os.environ, "ENGINEER_ROOT": str(self.root)},
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_real_phase_add_letter_and_dotted_native_identifiers(self):
        self.runtime("project.init", "--name", "Widget", "--description", "A widget", "--core-value", "Useful")
        for identifier in ("1a", "1.1a", "1a.2b", "1.2.3", "2"):
            self.runtime("phase.add", "Named " + identifier, "--number", identifier)
        phases = self.runtime("phases.list")["phases"]
        self.assertEqual({"01a", "01.1a", "01a.2b", "01.2.3", "02"}, {p["number"] for p in phases})
        for identifier in ("01a", "01.1a", "01a.2b", "01.2.3", "02"):
            with self.subTest(identifier=identifier):
                self.runtime("state.patch", json.dumps({"phase": identifier + " of 5"}))
                packet = self.health()
                self.assertFalse({"W002", "W005", "W006", "W007", "W023", "C001"} & self.codes(packet), packet)
                self.assertEqual([], packet["evidence_gaps"])
        self.write("STATE.md", "Phase: 01A.2B of 5\nStatus: Planning\n")
        roadmap = self.root / ".planning/ROADMAP.md"
        roadmap.write_text(roadmap.read_text(encoding="utf-8").replace("01a.2b:", "01A.2B:"), encoding="utf-8")
        self.assertFalse({"W002", "W005", "W006", "W007", "W023"} & self.codes(self.health()))

    def test_unreadable_matching_summary_is_not_completion_evidence(self):
        self.initialized()
        self.write("phases/01-start/01-01-PLAN.md", "---\nwave: 1\n---\n# Plan\n")
        summary = self.write("phases/01-start/01-01-SUMMARY.md", "# Summary\n")
        summary.write_bytes(b"\xff\xfe")
        before = self.contents()
        packet = self.health()
        self.assertEqual("broken", packet["status"])
        self.assertIn("I001", self.codes(packet))
        self.assertNotIn("C003", self.codes(packet))
        gaps = [g for g in packet["evidence_gaps"] if g["path"] == str(summary)]
        self.assertEqual(1, len(gaps))
        errors = [d for d in packet["errors"] if d["code"] == "unreadable-evidence" and str(summary) in d["message"]]
        self.assertEqual(1, len(errors))
        self.assertEqual(before, self.contents())
        result = subprocess.run([sys.executable, "-I", str(CLI), "query", "validate.health", "--repair"],
                                cwd=self.root, env={**os.environ, "ENGINEER_ROOT": str(self.root)},
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertNotEqual(0, result.returncode)
        failure = json.loads(result.stderr)
        self.assertEqual("health-repair-evidence-unavailable", failure["error"])
        self.assertTrue(any(g["path"] == str(summary) for g in failure["evidence_gaps"]))
        self.assertEqual(before, self.contents())

    def test_bootstrap_only_gap_reaches_default_health_report(self):
        self.initialized()
        artifact = self.write("notes.md", "# Notes\n")
        artifact.write_bytes(b"\xff\xfe")
        before = self.contents()
        packet = self.health()
        self.assertEqual("broken", packet["status"])
        self.assertEqual(1, sum(g["path"] == str(artifact) for g in packet["evidence_gaps"]))
        self.assertTrue(any(d["code"] == "unreadable-evidence" and d.get("path") == str(artifact) for d in packet["errors"]))
        self.assertEqual(before, self.contents())

    def contents(self):
        return {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*")
                if p.is_file() and ".git" not in p.relative_to(self.root).parts}

    def codes(self, packet):
        return {d["code"] for d in packet["diagnostics"]}

    def test_fresh_repository_reports_missing_records_and_never_initializes(self):
        before = self.contents()
        packet = self.health()
        self.assertEqual("broken", packet["status"])
        self.assertTrue({"E001", "E002", "E003", "E004", "W003", "missing-record"} <= self.codes(packet))
        self.assertEqual(before, self.contents())
        self.assertFalse((self.root / ".planning").exists())

    def test_healthy_native_config_and_not_started_phase(self):
        self.initialized()
        packet = self.health()
        self.assertEqual("healthy", packet["status"], packet)
        self.assertEqual([], packet["evidence_gaps"])
        self.assertFalse(packet["structuralOnly"])
        self.assertIn("W006", packet["coverage"]["evaluated"])
        self.assertEqual({"W010", "W016", "W024", "W028"}, {r["code"] for r in packet["coverage"]["skipped"]})
        self.assertFalse(packet["coverage"]["complete"])

    def test_unonboarded_skeleton_is_reported_without_adopting_identity(self):
        self.initialized()
        self.write("PROJECT.md", "> **Unfilled adoption skeleton:** CHANGEME\n## What This Is\n## Core Value\n## Requirements\n")
        before = self.contents()
        self.assertIn("unonboarded", self.codes(self.health()))
        self.assertEqual(before, self.contents())

    def test_malformed_config_and_record_missing_section_are_real_findings(self):
        self.initialized()
        self.write("PROJECT.md", "# Widget\n")
        self.write("config.yaml", "workflow: [unterminated\n")
        packet = self.health()
        self.assertEqual("broken", packet["status"])
        self.assertTrue({"E005", "W001", "invalid-yaml"} <= self.codes(packet))
        self.assertTrue(all("config.json" not in d["message"] for d in packet["diagnostics"]))

    def test_invalid_native_schema_is_error_even_when_yaml_parses(self):
        self.initialized()
        self.write("config.yaml", "context_window: nope\n")
        packet = self.health()
        self.assertTrue({"invalid-config-type", "W013"} <= self.codes(packet))
        self.assertEqual("broken", packet["status"])

    def test_state_mismatch_and_orphan_summary_and_plan_advisory(self):
        self.initialized()
        self.write("STATE.md", "Phase: 99 of 99\nStatus: Executing\n")
        self.write("phases/01-start/01-01-PLAN.md", "---\nwave: 1\n---\n# Plan\n")
        self.write("phases/01-start/01-02-SUMMARY.md", "# Orphan\n")
        packet = self.health()
        self.assertTrue({"W002", "C003", "I001"} <= self.codes(packet))
        self.assertEqual("degraded", packet["status"])

    def test_phase_naming_missing_disk_and_unlisted_disk(self):
        self.initialized()
        self.write("ROADMAP.md", "# Roadmap\n### Phase 02: Missing\n")
        self.write("phases/invalid/01-01-PLAN.md", "# Plan\n")
        self.assertTrue({"W005", "W006", "W007", "C004"} <= self.codes(self.health()))

    def test_completed_checkbox_and_research_validation_advisories(self):
        self.initialized()
        self.write("ROADMAP.md", "# Roadmap\n- [x] **Phase 01: Start**\n### Phase 01: Start\n")
        self.write("phases/01-start/01-RESEARCH.md", "# Research\n## Validation Architecture\n")
        self.assertTrue({"W011", "W009"} <= self.codes(self.health()))

    def test_default_preserves_every_record_and_does_not_create_json_config(self):
        self.initialized()
        self.write("config.yaml", "# keep this\nworkflow:\n  research: false\n")
        before = self.contents()
        packet = self.health()
        self.assertIn("W008", self.codes(packet))
        self.assertEqual(1, packet["repairable_count"])
        self.assertEqual(before, self.contents())
        self.assertFalse((self.root / ".planning/config.json").exists())

    def test_explicit_safe_repair_uses_native_yaml_handler_then_rechecks(self):
        self.initialized()
        self.write("config.yaml", "# keep this\nworkflow:\n  research: false\n")
        before = self.contents()
        packet = self.health("--repair")
        self.assertEqual(["W008"], packet["repairs"]["applied"])
        self.assertNotIn("W008", self.codes(packet))
        after = self.contents()
        changes = {key for key in before if before[key] != after[key]}
        self.assertEqual({".planning/config.yaml"}, changes)
        text = (self.root / ".planning/config.yaml").read_text()
        self.assertIn("# keep this", text)
        self.assertIn("research: false", text)
        self.assertIn("nyquist_validation: true", text)
        self.assertFalse((self.root / ".planning/config.json").exists())

    def test_unsupported_and_destructive_repair_is_refused_without_changes(self):
        self.initialized()
        self.write("config.yaml", "workflow: [broken\n")
        self.write("phases/01-start/01-VERIFICATION.md", "---\nstatus: pass_with_caveats\n---\n# Do not rewrite\n")
        before = self.contents()
        packet = self.health("--repair")
        self.assertTrue({"E005", "W030"} <= set(packet["repairs"]["refused"]))
        self.assertEqual(before, self.contents())

    def test_backfill_advises_and_refuses_upstream_record_mutation(self):
        self.initialized()
        self.write("milestones/v1.0-ROADMAP.md", "# Milestone v1.0\n")
        before = self.contents()
        packet = self.health("--backfill")
        self.assertIn("W018", self.codes(packet))
        self.assertEqual(["W018"], packet["repairs"]["refused"])
        self.assertEqual(before, self.contents())

    def test_git_ignore_and_tracked_planning_are_actually_probed(self):
        self.initialized()
        subprocess.run(["git", "add", "--", ".planning"], cwd=self.root, check=True, capture_output=True)
        (self.root / ".gitignore").write_text(".planning/\n")
        self.assertIn("W029", self.codes(self.health()))

    def test_corrupt_plan_bytes_are_reported_and_cannot_authorize_repair(self):
        self.initialized()
        plan = self.write("phases/01-start/01-01-PLAN.md", "# Plan\n")
        plan.write_bytes(b"---\nwave: 1\n---\n\xff\xfe")
        self.write("config.yaml", "workflow:\n  research: false\n")
        before = self.contents()
        packet = self.health()
        self.assertEqual("broken", packet["status"])
        self.assertIn("unreadable-evidence", self.codes(packet))
        self.assertTrue(any(gap["path"] == str(plan) for gap in packet["evidence_gaps"]))
        result = subprocess.run([sys.executable, "-I", str(CLI), "query", "validate.health", "--repair"],
                                cwd=self.root, env={**os.environ, "ENGINEER_ROOT": str(self.root)},
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("health-repair-evidence-unavailable", json.loads(result.stderr)["error"])
        self.assertEqual(before, self.contents())

    def test_health_and_backfill_mutation_classification_stays_narrow(self):
        # Legacy tests also import a package named lib. Match the native CLI's
        # process isolation instead of depending on discovery/import order.
        script = textwrap.dedent('''
            import sys
            import unittest
            sys.path.insert(0, sys.argv[1])
            from lib.core import Args, Failure
            from lib.planning_integrity import finish, mutates
            checks = unittest.TestCase()
            checks.assertFalse(mutates("validate.health"))
            checks.assertFalse(mutates("validate.health", Args(["--backfill"])))
            checks.assertTrue(mutates("validate.health", Args(["--repair"])))
            before = {"digest": "before", "findings": set()}
            after = {"digest": "after", "findings": set()}
            for flags in ([], ["--backfill"]):
                with checks.assertRaises(Failure) as raised:
                    finish("validate.health", before, after, Args(flags))
                checks.assertEqual("unexpected-planning-write", raised.exception.code)
        ''')
        result = subprocess.run([sys.executable, "-I", "-c", script, str(ROOT / "engineer/bin")],
                                cwd=self.root, capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, result.returncode, result.stderr + result.stdout)

    def test_native_validation_error_does_not_echo_configuration_values(self):
        self.initialized()
        self.write("config.yaml", "runtime: private-sensitive-value\n")
        packet = self.health()
        self.assertEqual("broken", packet["status"])
        self.assertNotIn("private-sensitive-value", json.dumps(packet))

    def test_missing_git_evidence_is_explicit_and_not_claimed_as_a_pass(self):
        self.initialized()
        result = subprocess.run([sys.executable, "-I", str(CLI), "query", "validate.health"],
                                cwd=self.root, env={**os.environ, "ENGINEER_ROOT": str(self.root), "PATH": ""},
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        packet = json.loads(result.stdout)
        self.assertEqual("degraded", packet["status"])
        self.assertIn("W020", self.codes(packet))
        self.assertTrue(any(gap.get("kind") == "git" for gap in packet["evidence_gaps"]))
        self.assertTrue({"W017", "W027", "W029"} <= {row["code"] for row in packet["coverage"]["skipped"]})

    def test_home_directory_guard_prevents_inspection_and_repair(self):
        self.initialized()
        before = self.contents()
        result = subprocess.run([sys.executable, "-I", str(CLI), "query", "validate.health", "--repair"],
                                cwd=self.root, env={**os.environ, "ENGINEER_ROOT": str(self.root),
                                                   "USERPROFILE": str(self.root), "HOME": str(self.root)},
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(0, result.returncode, result.stderr)
        packet = json.loads(result.stdout)
        self.assertTrue({"E010", "I010"} <= self.codes(packet))
        self.assertEqual([], packet["coverage"]["evaluated"])
        self.assertEqual(before, self.contents())


if __name__ == "__main__":
    unittest.main()
