"""Quick verification uses its own planning owner and the existing evidence gates."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

try:
    from .test_engineer_runtime import RuntimeCase, RUNTIME
except ImportError:
    from test_engineer_runtime import RuntimeCase, RUNTIME


class QuickVerification(RuntimeCase):
    def setUp(self):
        super().setUp()
        self.git("config", "core.autocrlf", "false")

    def quick_fixture(self, legacy=False):
        if legacy:
            identifier = "260808-abc"
            directory = self.root / ".planning/quick/260808-abc-repair"
            self.put(str(directory / "QUICK.md"),
                     '---\nid: "260808-abc"\ndescription: Repair behavior\nstatus: pending\n---\nRepair\n')
        else:
            task = self.cli("quick.create", "Repair behavior")
            identifier = task["quick_id"]
            directory = Path(task["directory"])
        self.put(str(directory / (identifier + "-PLAN.md")),
                 '---\nfiles_modified: [src/app.py]\nmust_haves: {}\n---\nRepair the behavior\n')
        self.put("src/app.py", "value = 1\n")
        report = self.put(str(directory / (identifier + "-VERIFICATION.md")),
                          '---\nstatus: passed\n---\nObserved behavior\n')
        return directory, report

    def commit_all(self, message):
        self.git("add", ".")
        self.git("commit", "-m", message)

    def test_quick_status_fingerprint_and_current_without_roadmap_for_both_hosts(self):
        directory, report = self.quick_fixture()
        self.commit_all("quick source")
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.env["ENGINEER_HOST"] = host
                captured = self.cli("verification.fingerprint", directory)
                self.assertEqual(str(report), captured["path"])
                self.assertEqual("passed", self.cli("verification.status", directory)["status"])
                self.commit_all("quick report " + host)
                self.assertTrue(self.cli("verification.current", directory)["current"])
        self.assertFalse((self.root / ".planning/ROADMAP.md").exists())

    def test_quick_fingerprint_binds_plan_context_summary_and_covered_source(self):
        directory, report = self.quick_fixture()
        initial = self.cli("verification.fingerprint", directory)["fingerprint"]
        self.cli("frontmatter.set", report, "--field", "x-note", "--value", "report-only")
        self.assertEqual(initial, self.cli("verification.fingerprint", directory)["fingerprint"])
        for path in (directory / "001-PLAN.md", directory / "001-CONTEXT.md",
                     directory / "001-SUMMARY.md", self.root / "src/app.py"):
            with self.subTest(path=path):
                path.write_text(path.read_text() + "\nChanged goal or input\n" if path.exists()
                                else "New evidence\n", encoding="utf-8")
                changed = self.cli("verification.fingerprint", directory)["fingerprint"]
                self.assertNotEqual(initial, changed)
                initial = changed

    def test_quick_current_rejects_dirty_tree_and_intervening_source_commits(self):
        directory, report = self.quick_fixture()
        self.commit_all("source")
        self.cli("verification.fingerprint", directory)
        self.commit_all("report")
        self.assertTrue(self.cli("verification.current", directory)["current"])
        self.put("src/app.py", "value = 2\n")
        result = self.cli("verification.current", directory)
        self.assertFalse(result["current"])
        self.assertIn("working tree is dirty", result["reasons"])
        self.commit_all("source changed")
        self.put("src/app.py", "value = 1\n")
        self.commit_all("source restored")
        result = self.cli("verification.current", directory)
        self.assertFalse(result["current"])
        self.assertIn("source changed since the frozen verification revision", result["reasons"])

    def test_quick_current_requires_configured_check_receipts(self):
        directory, report = self.quick_fixture()
        self.put(".gitignore", ".planning/verification-receipts/\n")
        self.cli("config-set", "verification.commands", json.dumps([
            {"id": "behavior", "argv": [sys.executable, "-c", "assert True"], "inputs": ["src/app.py"]}]))
        self.commit_all("source and configured check")
        self.cli("verification.fingerprint", directory)
        self.commit_all("report")
        result = self.cli("verification.current", directory)
        self.assertFalse(result["current"])
        self.assertIn("configured checks lack passing receipts at current HEAD", result["reasons"])
        self.assertTrue(self.cli("verification.run-checks")["passed"])
        self.assertTrue(self.cli("verification.current", directory)["current"])

    def test_legacy_quick_report_resolution_uses_complete_task_id(self):
        directory, report = self.quick_fixture(legacy=True)
        report.unlink()
        missing = self.cli("verification.status", directory)
        self.assertEqual(str(report), missing["path"])
        self.assertFalse(missing["exists"])
        self.assertEqual("missing", missing["status"])
        report.write_text('---\nstatus: passed\n---\nObserved behavior\n', encoding="utf-8")
        captured = self.cli("verification.fingerprint", directory)
        self.assertEqual(str(report), captured["path"])
        self.assertFalse((directory / "260808-VERIFICATION.md").exists())

    def test_quick_status_is_total_and_fails_closed_for_invalid_status(self):
        directory, report = self.quick_fixture()
        self.assertEqual("phase_dir_not_found", self.cli("verification.status", directory.parent / "002-missing")["status"])
        self.cli("verification.fingerprint", directory)
        self.assertEqual("passed", self.cli("verification.status", directory)["status"])
        self.put("src/app.py", "changed\n")
        self.assertEqual("stale", self.cli("verification.status", directory)["status"])
        report.write_text('---\nstatus: [broken\n---\n', encoding="utf-8")
        self.assertEqual("unparseable", self.cli("verification.status", directory)["status"])
        report.write_text('---\nstatus: invented\n---\n', encoding="utf-8")
        self.assertIn("invalid-verification-status", self.cli_error("verification.status", directory))

    def test_quick_records_and_report_cannot_borrow_another_identity(self):
        directory, report = self.quick_fixture()
        for path in (directory / "QUICK.md", directory / "001-PLAN.md", report):
            with self.subTest(path=path):
                original = path.read_text(encoding="utf-8")
                path.write_text('---\nid: "999"\nphase: "999"\ndescription: Foreign task\nstatus: passed\n---\n', encoding="utf-8")
                self.assertIn("identity", self.cli_error("verification.fingerprint", directory))
                path.write_text(original, encoding="utf-8")
        report.rename(directory / "999-VERIFICATION.md")
        self.assertIn("quick-report-identity-mismatch", self.cli_error("verification.status", directory))

    def test_quick_goal_record_changes_invalidate_fingerprint(self):
        directory, report = self.quick_fixture()
        self.cli("verification.fingerprint", directory)
        record = directory / "QUICK.md"
        record.write_text(record.read_text(encoding="utf-8").replace("Repair behavior", "Different goal"), encoding="utf-8")
        self.assertEqual("stale", self.cli("verification.status", directory)["status"])

    def test_quick_report_coverage_survives_fingerprint_refresh(self):
        directory, report = self.quick_fixture()
        self.put("dependency.py", "value = 1\n")
        first = self.cli("verification.fingerprint", directory, "--files", "dependency.py")["fingerprint"]
        self.assertEqual(first, self.cli("verification.fingerprint", directory)["fingerprint"])
        self.put("dependency.py", "value = 2\n")
        self.assertEqual("stale", self.cli("verification.status", directory)["status"])

    def test_quick_report_only_successor_qualifies_without_rewriting_receipts(self):
        directory, report = self.quick_fixture()
        report_path = report.relative_to(self.root).as_posix()
        self.put(".gitignore", ".planning/verification-receipts/\n")
        self.cli("config-set", "verification.commands", json.dumps([
            {"id": "behavior", "argv": [sys.executable, "-c", "assert True"], "revision": True,
             "reuse": False, "successor_independence": {
                 "schema": 1, "report_paths": [report_path], "protected_inputs": "all-other-inputs",
                 "revision_semantics": "provenance-only"}}]))
        self.commit_all("quick source and prospective contract")
        self.cli("verification.fingerprint", directory)
        self.commit_all("frozen quick report")
        evidence = self.cli("verification.run-checks")
        self.assertTrue(evidence["passed"])
        receipts = self.root / ".planning/verification-receipts"
        original = {p.name: p.read_bytes() for p in receipts.iterdir() if p.is_file()}
        with tempfile.TemporaryDirectory() as temp:
            evidence_file = Path(temp) / "baseline.json"
            evidence_file.write_text(json.dumps(evidence), encoding="utf-8")
            report.write_text(report.read_text(encoding="utf-8") + "\n## Audit\nObserved\n", encoding="utf-8")
            self.commit_all("report-only audit")
            head = self.git("rev-parse", "HEAD")
            flags = ("--evidence-file", evidence_file, "--expected-head", head)
            self.assertFalse(self.cli("verification.current", directory)["current"])
            result = self.cli("verification.current", directory, *flags)
            self.assertTrue(result["current"], result)
            self.assertTrue(result["successor_qualification"]["qualified"])
            self.assertEqual(original, {p.name: p.read_bytes() for p in receipts.iterdir() if p.is_file()})
            # A goal-record touch remains disqualifying even after reverting its bytes.
            record = directory / "QUICK.md"
            record.write_text(record.read_text(encoding="utf-8") + "\nChanged\n", encoding="utf-8")
            self.commit_all("touch quick owner")
            self.git("revert", "--no-edit", "HEAD")
            flags = ("--evidence-file", evidence_file, "--expected-head", self.git("rev-parse", "HEAD"))
            result = self.cli("verification.current", directory, *flags)
            self.assertFalse(result["current"])
            self.assertFalse(result["successor_qualification"]["qualified"])

    def test_report_ambiguity_and_foreign_or_nested_directories_are_rejected(self):
        directory, report = self.quick_fixture()
        self.put(str(directory / "other-VERIFICATION.md"), "---\nstatus: passed\n---\n")
        self.assertIn("ambiguous-verification-report",
                      self.cli_error("verification.status", directory))
        for path in (self.root / "src", directory / "nested", self.root / ".planning/quick"):
            path.mkdir(parents=True, exist_ok=True)
            with self.subTest(path=path):
                self.assertIn("invalid-phase-directory", self.cli_error("verification.fingerprint", path))

    def cli_error(self, *args):
        process = subprocess.run([sys.executable, "-I", str(RUNTIME), "query", *map(str, args)],
                                 cwd=self.root, env=self.env, text=True, encoding="utf-8", capture_output=True)
        self.assertNotEqual(0, process.returncode)
        return process.stderr
