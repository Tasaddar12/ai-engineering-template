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
        process = subprocess.Popen([sys.executable, "-I", str(RUNTIME), "query", "run-with-timeout", "--timeout", "5", "--", sys.executable, "-u", "-c", "import time; print('live-marker', flush=True); time.sleep(20)"], cwd=self.root, env=self.env, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.addCleanup(lambda: process.kill() if process.poll() is None else None)
        start = time.monotonic()
        self.assertEqual("live-marker", process.stderr.readline().strip())
        self.assertLess(time.monotonic()-start, 4.5)
        self.assertIsNone(process.poll(), "output must arrive while the child is still running")
        out, err = process.communicate(timeout=10)
        self.assertEqual(124, process.returncode)
        result = json.loads(out)
        self.assertTrue(result["timed_out"])
        self.assertIn("live-marker", result["stdout"])


    def test_ui_and_ai_specs_do_not_supply_ordinary_phase_spec(self):
        directory = Path(self.phase())
        self.put(str(directory.relative_to(self.root)/"01-UI-SPEC.md"), "UI contract\n")
        self.put(str(directory.relative_to(self.root)/"01-AI-SPEC.md"), "AI contract\n")
        packet = self.cli("init.phase-op", "1")
        self.assertFalse(packet["has_spec"])
        self.assertIsNone(packet["spec_path"])
        actual = self.put(str(directory.relative_to(self.root)/"01-SPEC.md"), "Behavior contract\n")
        self.assertEqual(str(actual), self.cli("init.phase-op", "1")["spec_path"])

    def test_canonical_threat_table_duplicates_use_stable_ids(self):
        directory = self.phase()
        body = "<threat_model>\n| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |\n|---|---|---|---|---|---|\n| T-01-01 + Pending: review | Auth | API | high | mitigate | owner check |\n</threat_model>\n"
        first = self.plan(directory, body)
        second = Path(directory)/"01-02-PLAN.md"
        second.write_text(first.read_text(encoding="utf-8").replace('plan: "01"', 'plan: "02"').replace("Pending: review", "Pending: independent audit"), encoding="utf-8")
        result = self.cli("init.phase-op", "1")
        self.assertEqual([{"id": "T-01-01", "plans": ["01-01", "01-02"]}], result["threat_id_duplicates"])

    def test_prior_plan_commands_stay_candidates_until_committed_summary_observation(self):
        first = self.phase("First")
        self.plan(first)
        self.phase("Second")
        packet = self.cli("init.phase-op", "2")
        self.assertTrue(packet["prior_verify_candidates"])
        self.assertEqual([], packet["prior_verify_commands"])
        revision = self.git("rev-parse", "HEAD")
        summary = Path(first)/"01-01-SUMMARY.md"
        text = '---\nphase: "01"\nplan: "01"\nstatus: complete\nrequirements-completed: []\nacceptance: []\ndocumentation: []\nissue_refs: []\n---\n## Checks\n\n| Tested revision | Command argv | Observed result | Evidence |\n|---|---|---|---|\n| '+revision+' | python -m unittest discover | pass | recorded fixture result |\n'
        summary.write_text(text, encoding="utf-8")
        self.assertEqual([], self.cli("init.phase-op", "2")["prior_verify_commands"])
        self.git("add", ".planning")
        self.git("commit", "-m", "fixture: observed prior check")
        observed = self.cli("init.phase-op", "2")["prior_verify_commands"]
        self.assertEqual("python -m unittest discover", observed[0]["command"])
        self.assertEqual(revision, observed[0]["revision"])

    def test_coverage_requires_current_native_receipt_inputs(self):
        self.put("source.txt", "current input\n")
        self.put(".planning/config.yaml", json.dumps({"verification": {"commands": [{"id": "behavior", "argv": [sys.executable, "-c", "print('observed fixture')"], "sources": ["source.txt"], "environment": []}]}}))
        self.git("add", ".")
        self.git("commit", "-m", "fixture: configured actual check")
        result = self.cli("verification.run-checks")
        check = result["checks"][0]
        metadata = {"coverage": [{"description": "Observed fixture behavior", "human_judgment": False, "verification": [{"kind": "unit", "status": "passed", "ref": check["receipt"], "revision": check["tested_revision"]}]}]}
        path = self.put("SUMMARY.md", "---\n"+json.dumps(metadata)+"\n---\n")
        self.assertTrue(self.cli("uat.classify-coverage", path)["all_auto_covered"])
        self.put("source.txt", "changed input\n")
        self.assertFalse(self.cli("uat.classify-coverage", path)["all_auto_covered"])

    def test_full_quick_identity_is_required_in_artifact_frontmatter(self):
        quick = self.cli("quick.create", "Identity binding")
        report = Path(self.cli("verification.fingerprint", "--quick", quick["id"])["path"])
        self.assertTrue(self.cli("frontmatter.validate", report, "--schema", "verification")["valid"])
        text = report.read_text(encoding="utf-8").replace(quick["id"], quick["id"].split("-", 1)[0])
        report.write_text(text, encoding="utf-8")
        self.assertFalse(self.cli("frontmatter.validate", report, "--schema", "verification", status=1)["valid"])

    def test_help_aliases_are_in_the_real_registry(self):
        names = self.cli("help")["verbs"]
        for name in ("help", "verbs", "--help", "-h"):
            self.assertIn(name, names)


    def test_numeric_legacy_quick_compatibility_does_not_alias_a_date(self):
        self.put(".planning/quick/001-legacy/QUICK.md", '---\nid: "001"\nstatus: open\n---\nLegacy quick task\n')
        legacy = self.cli("verification.fingerprint", "--quick", "1")
        self.assertEqual("001-VERIFICATION.md", Path(legacy["path"]).name)
        dated = self.cli("quick.create", "Dated task")
        self.cli("verification.status", "--quick", dated["id"].split("-", 1)[0], status=1, raw=True)


    def test_literal_command_targets_return_the_selected_method_packet(self):
        directory = self.phase()
        self.put("apps/api/package.json", '{"scripts":{"test":"fixture"}}')
        path = self.plan(directory, '<task><files>future/app.py</files><verify><automated>npm --prefix apps/api run absent</automated></verify></task>')
        result = self.cli("check.verify-command-paths", "--plan", path)
        self.assertEqual("script_missing", result["commands"][0]["reason"])
        self.assertEqual("warning", result["commands"][0]["severity"])
        path.write_text(path.read_text(encoding="utf-8").replace("npm --prefix apps/api run absent", "cd missing &amp;&amp; test"), encoding="utf-8")
        result = self.cli("check.verify-command-paths", "--plan", path, status=1)
        self.assertEqual("directory_missing", result["commands"][0]["reason"])
        self.assertEqual("blocker", result["commands"][0]["severity"])
        path.write_text(path.read_text(encoding="utf-8").replace("cd missing &amp;&amp; test", "cd $TARGET"), encoding="utf-8")
        result = self.cli("check.verify-command-paths", "--plan", path)
        self.assertEqual("dynamic_path", result["commands"][0]["reason"])

    def test_phase_identity_keeps_the_canonical_decimal_contract(self):
        directory = self.phase()
        path = self.plan(directory)
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace('phase: "01"', 'phase: "03A"'), encoding="utf-8")
        self.assertFalse(self.cli("frontmatter.validate", path, "--schema", "plan", status=1)["valid"])
