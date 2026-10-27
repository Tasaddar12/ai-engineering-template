"""Regression contracts for final runtime reconciliation (execution deferred)."""
import json
from pathlib import Path
import subprocess
import sys
import time

from test_engineer_runtime import RuntimeCase, RUNTIME


class FinalRuntimeContracts(RuntimeCase):
    def test_dated_quick_identity_survives_fingerprint_status_and_currentness(self):
        task = self.cli("quick.create", "Dated identity")
        identifier = task["quick_id"]
        self.assertGreaterEqual(identifier.count("-"), 2)
        self.git("add", ".planning")
        self.git("commit", "-m", "fixture: quick record")
        report = Path(self.cli("verification.fingerprint", "--quick", identifier)["path"])
        self.assertEqual(identifier + "-VERIFICATION.md", report.name)
        text = report.read_text(encoding="utf-8").replace('status: "not_started"', 'status: "passed"')
        report.write_text(text, encoding="utf-8")
        self.git("add", ".planning")
        self.git("commit", "-m", "fixture: dated quick verification")
        status = self.cli("verification.status", "--quick", identifier)
        self.assertEqual(identifier, status["quick"])
        self.assertIn(identifier, status["next_command"])
        self.assertTrue(self.cli("verification.current", "--quick", identifier)["current"])
        self.put("source.py", "changed = True\n")
        self.git("add", "source.py")
        self.git("commit", "-m", "fixture: source drift")
        self.assertFalse(self.cli("verification.current", "--quick", identifier)["current"])

    def test_canonical_spec_tables_and_empty_sections(self):
        path = self.put("SPEC.md", "## Edge Cases\n\n| Category | Requirement | Status | Resolution / Reason |\n|---|---|---|---|\n| empty | R1 | covered | test_empty |\n\n## Prohibitions\n\n| Prohibition (must-NOT statement) | Requirement | Status | Verification / Reason |\n|---|---|---|---|\n| MUST NOT leak tokens | R2 | resolved | assertion |\n")
        self.assertEqual(1, len(self.cli("spec.section", path, "edges")["items"]))
        self.assertEqual(1, len(self.cli("spec.section", path, "prohibitions")["items"]))
        path.write_text("## Edge Cases\n\n## Prohibitions\n", encoding="utf-8")
        self.assertFalse(self.cli("spec.section", path, "edges")["supplied"])

    def test_empty_or_unbound_uat_coverage_cannot_auto_pass(self):
        path = self.put("SUMMARY.md", "---\ncoverage: []\n---\n")
        self.assertFalse(self.cli("uat.classify-coverage", path)["all_auto_covered"])
        path.write_text('---\ncoverage:\n  - description: behavior\n    human_judgment: false\n    verification:\n      - kind: unit\n        status: passed\n        ref: fake.json\n---\n', encoding="utf-8")
        self.assertFalse(self.cli("uat.classify-coverage", path)["all_auto_covered"])

    def test_checkpoint_auto_select_binds_declared_option_and_retains_options(self):
        path = self.plan(self.phase(), '<task type="checkpoint:decision" auto_select="missing"><decision>Choose</decision><options><option id="actual"><name>Actual</name></option></options></task>')
        self.assertFalse(self.cli("verify.plan-structure", path, status=1)["valid"])
        path.write_text(path.read_text(encoding="utf-8").replace('auto_select="missing"', 'auto_select="actual"'), encoding="utf-8")
        self.assertTrue(self.cli("verify.plan-structure", path)["valid"])
        task = self.cli("plan.task-structure", path)["tasks"][0]
        self.assertEqual("actual", task["options"][0]["id"])
        self.assertNotIn("approved", task)

    def test_failing_directions_bind_first_statement_to_preceding_command(self):
        path = self.plan(self.phase(), '<task><verify><fails_when>orphan</fails_when><automated>python one.py</automated><fails_when>nonzero</fails_when><fails_when>extra</fails_when><automated>python two.py</automated><fails_when>TBD</fails_when></verify></task>')
        result = self.cli("check.verify-failure-directions", "--plan", path, status=1)
        self.assertEqual(["orphan", "ok", "placeholder"], [row["status"] for row in result["commands"]])
        self.assertEqual("nonzero", result["commands"][1]["fails_when"])
        self.assertEqual("blocker", result["commands"][-1]["severity"])

    def test_timeout_forwards_live_output_and_preserves_single_json_stdout(self):
        process = subprocess.Popen([sys.executable, "-I", str(RUNTIME), "query", "run-with-timeout", "--timeout", "0.8", "--", sys.executable, "-u", "-c", "import time; print('live-marker', flush=True); time.sleep(20)"], cwd=self.root, env=self.env, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        start = time.monotonic()
        self.assertEqual("live-marker", process.stderr.readline().strip())
        self.assertLess(time.monotonic()-start, 0.75)
        out, err = process.communicate(timeout=10)
        self.assertEqual(124, process.returncode)
        result = json.loads(out)
        self.assertTrue(result["timed_out"])
        self.assertIn("live-marker", result["stdout"])
