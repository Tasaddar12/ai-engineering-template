import importlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "engineer/bin/lib"


def _load(name):
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module("engineer_bin_lib." + name)


hd = _load("health_diagnostic")
rules_mod = _load("health_diagnostic_rules")
SEVERITY, REMEDY_ACTION, REMEDY_RISK, SCOPE = hd.SEVERITY, hd.REMEDY_ACTION, hd.REMEDY_RISK, hd.SCOPE


def fake_diagnostic(code, action, risk, args=None):
    return {"code": code, "severity": SEVERITY["WARNING"], "message": f"fake diagnostic for {code}",
            "remedy": {"action": action, "risk": risk, "args": args or {}}}


class TempProject(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="health-diagnostic-")
        self.addCleanup(self._tmp.cleanup)
        self.cwd = Path(self._tmp.name)
        self.planning = self.cwd / ".planning"
        self.planning.mkdir()

    def write(self, rel, text):
        path = self.planning / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def read(self, rel):
        with open(self.planning / rel, "r", encoding="utf-8", newline="") as handle:
            return handle.read()

    def write_valid_config(self):
        self.write("config.json", json.dumps({"model_profile": "balanced", "commit_docs": True,
                                              "workflow": {"nyquist_validation": True, "ai_integration_phase": True}}, indent=2))


class Enums(unittest.TestCase):
    def test_remedy_action_locks_eight_members(self):
        self.assertEqual(sorted(REMEDY_ACTION), [
            "ADD_AI_INTEGRATION_PHASE_KEY", "ADD_NYQUIST_KEY", "ADVISE", "BACKFILL_MILESTONES", "CREATE_CONFIG",
            "REGENERATE_STATE", "REPAIR_VERIFICATION_STATUS", "RESET_CONFIG"])
        self.assertEqual(sorted(REMEDY_ACTION.values()), [
            "addAiIntegrationPhaseKey", "addNyquistKey", "advise", "backfillMilestones", "createConfig",
            "regenerateState", "repairVerificationStatus", "resetConfig"])

    def test_remedy_risk_and_severity(self):
        self.assertEqual(sorted(REMEDY_RISK.values()), ["destructive", "none"])
        self.assertEqual(sorted(SEVERITY.values()), ["error", "info", "warning"])
        self.assertEqual(sorted(SEVERITY), ["ERROR", "INFO", "WARNING"])

    def test_enums_are_frozen(self):
        for table in (REMEDY_ACTION, REMEDY_RISK, SEVERITY, SCOPE):
            with self.assertRaises(TypeError):
                table["NEW"] = "x"

    def test_scope_members(self):
        self.assertEqual({"COMPLETE": "complete", "TRUNCATED": "truncated", "UNSCOPED": "unscoped", "UNREADABLE": "unreadable"}, dict(SCOPE))

    def test_advise_remedy_shape(self):
        self.assertEqual({"action": "advise", "risk": "none", "args": {"command": "do it"}}, hd.advise_remedy("do it"))


class ApplyRepairsGating(TempProject):
    def test_destructive_remedies_are_refused_when_repair_requested(self):
        diagnostics = [fake_diagnostic("E005", REMEDY_ACTION["RESET_CONFIG"], REMEDY_RISK["DESTRUCTIVE"]),
                       fake_diagnostic("E004", REMEDY_ACTION["REGENERATE_STATE"], REMEDY_RISK["DESTRUCTIVE"])]
        result = hd.apply_repairs("/fake/cwd", diagnostics, True, False)
        self.assertEqual([], result["applied"])
        self.assertEqual(["E004", "E005"], sorted(result["refused"]))
        for row in result["details"]:
            self.assertFalse(row["success"])
            self.assertIn("destructive remedy and is not auto-applied by --repair", row["error"])

    def test_none_risk_actions_are_applied_on_a_real_project(self):
        self.write_valid_config()
        diagnostics = [fake_diagnostic("W003", REMEDY_ACTION["CREATE_CONFIG"], REMEDY_RISK["NONE"]),
                       fake_diagnostic("W008", REMEDY_ACTION["ADD_NYQUIST_KEY"], REMEDY_RISK["NONE"]),
                       fake_diagnostic("W016", REMEDY_ACTION["ADD_AI_INTEGRATION_PHASE_KEY"], REMEDY_RISK["NONE"]),
                       fake_diagnostic("W018", REMEDY_ACTION["BACKFILL_MILESTONES"], REMEDY_RISK["NONE"])]
        result = hd.apply_repairs(self.cwd, diagnostics, True, False)
        self.assertEqual(["W003", "W008", "W016", "W018"], sorted(result["applied"]))
        self.assertEqual([], result["refused"])

    def test_advise_is_never_applied_nor_refused(self):
        result = hd.apply_repairs("/fake/cwd", [fake_diagnostic("W001", REMEDY_ACTION["ADVISE"], REMEDY_RISK["NONE"])], True, True)
        self.assertEqual({"applied": [], "refused": [], "details": []}, result)

    def test_not_requested_is_skipped_entirely(self):
        for action, risk in ((REMEDY_ACTION["CREATE_CONFIG"], REMEDY_RISK["NONE"]), (REMEDY_ACTION["RESET_CONFIG"], REMEDY_RISK["DESTRUCTIVE"])):
            result = hd.apply_repairs("/fake/cwd", [fake_diagnostic("X", action, risk)], False, False)
            self.assertEqual({"applied": [], "refused": [], "details": []}, result)

    def test_backfill_flag_alone_applies_backfill_milestones(self):
        result = hd.apply_repairs(self.cwd, [fake_diagnostic("W018", REMEDY_ACTION["BACKFILL_MILESTONES"], REMEDY_RISK["NONE"])], False, True)
        self.assertEqual(["W018"], result["applied"])
        self.assertEqual([], result["refused"])

    def test_backfill_skipped_without_either_flag(self):
        result = hd.apply_repairs("/fake/cwd", [fake_diagnostic("W018", REMEDY_ACTION["BACKFILL_MILESTONES"], REMEDY_RISK["NONE"])], False, False)
        self.assertEqual({"applied": [], "refused": [], "details": []}, result)

    def test_failing_handler_is_recorded_and_not_applied(self):
        # addNyquistKey reads config.json, which is absent: the handler throws.
        result = hd.apply_repairs(self.cwd, [fake_diagnostic("W008", REMEDY_ACTION["ADD_NYQUIST_KEY"], REMEDY_RISK["NONE"])], True, False)
        self.assertEqual([], result["applied"])
        self.assertEqual([], result["refused"])
        self.assertEqual(1, len(result["details"]))
        row = result["details"][0]
        self.assertEqual(("W008", "addNyquistKey", False), (row["code"], row["action"], row["success"]))
        self.assertTrue(row["error"])

    def test_unknown_action_has_no_handler(self):
        result = hd.apply_repairs(self.cwd, [fake_diagnostic("X", "nope", REMEDY_RISK["NONE"])], True, False)
        self.assertEqual([], result["applied"])
        self.assertEqual('no repair handler registered for action "nope"', result["details"][0]["error"])


class RepairHandlers(TempProject):
    def test_repair_paths(self):
        paths = hd.repair_paths(self.cwd)
        self.assertEqual(self.planning / "config.json", paths["configPath"])
        self.assertEqual(self.planning / "STATE.md", paths["statePath"])
        self.assertEqual(self.planning / "MILESTONES.md", paths["milestonesPath"])
        self.assertEqual(self.planning / "milestones", paths["milestonesArchiveDir"])

    def test_create_config_writes_the_default_payload(self):
        result = hd.apply_repairs(self.cwd, [fake_diagnostic("W003", REMEDY_ACTION["CREATE_CONFIG"], REMEDY_RISK["NONE"])], True, False)
        self.assertEqual(["W003"], result["applied"])
        self.assertEqual({"code": "W003", "action": "createConfig", "success": True, "path": "config.json"}, result["details"][0])
        self.assertEqual(hd.default_config_payload(), json.loads(self.read("config.json")))
        self.assertEqual(json.dumps(hd.default_config_payload(), indent=2, ensure_ascii=False), self.read("config.json"))

    def test_default_config_payload_values(self):
        payload = hd.default_config_payload()
        self.assertEqual(["model_profile", "commit_docs", "search_gitignored", "branching_strategy", "phase_branch_template",
                          "milestone_branch_template", "quick_branch_template", "workflow", "parallelization", "brave_search"], list(payload))
        self.assertEqual({"research": True, "plan_check": True, "verifier": True, "nyquist_validation": True}, payload["workflow"])
        self.assertIsNone(payload["quick_branch_template"])

    def test_add_keys_patch_config_and_never_overwrite(self):
        self.write("config.json", json.dumps({"model_profile": "balanced", "workflow": {"nyquist_validation": False}}))
        diagnostics = [fake_diagnostic("W008", REMEDY_ACTION["ADD_NYQUIST_KEY"], REMEDY_RISK["NONE"]),
                       fake_diagnostic("W016", REMEDY_ACTION["ADD_AI_INTEGRATION_PHASE_KEY"], REMEDY_RISK["NONE"])]
        result = hd.apply_repairs(self.cwd, diagnostics, True, False)
        self.assertEqual(["W008", "W016"], result["applied"])
        config = json.loads(self.read("config.json"))
        self.assertEqual({"nyquist_validation": False, "ai_integration_phase": True}, config["workflow"])

    def test_add_key_creates_workflow_object_when_missing(self):
        self.write("config.json", json.dumps({"model_profile": "balanced"}))
        hd.apply_repairs(self.cwd, [fake_diagnostic("W008", REMEDY_ACTION["ADD_NYQUIST_KEY"], REMEDY_RISK["NONE"])], True, False)
        self.assertEqual({"nyquist_validation": True}, json.loads(self.read("config.json"))["workflow"])

    def test_missing_milestone_versions(self):
        self.write("milestones/v1.0-ROADMAP.md", "# Milestone v1.0 Alpha\n")
        self.write("milestones/v1.1-ROADMAP.md", "# Milestone v1.1 Beta\n")
        self.write("milestones/notes.md", "ignored")
        self.write("MILESTONES.md", "# Milestones\n\n## v1.0 Alpha\n")
        paths = hd.repair_paths(self.cwd)
        self.assertEqual(["v1.1"], hd.compute_missing_milestone_versions(paths["milestonesArchiveDir"], paths["milestonesPath"]))
        self.assertEqual([], hd.compute_missing_milestone_versions(self.cwd / "nope", self.cwd / "nope.md"))

    def test_backfill_inserts_after_header_and_names_the_milestone(self):
        self.write("milestones/v1.1-ROADMAP.md", "# Milestone v1.1 Beta Launch\n")
        self.write("MILESTONES.md", "# Milestones\n\n## v1.0 Alpha\n")
        result = hd.apply_repairs(self.cwd, [fake_diagnostic("W018", REMEDY_ACTION["BACKFILL_MILESTONES"], REMEDY_RISK["NONE"])], False, True)
        self.assertEqual({"code": "W018", "action": "backfillMilestones", "success": True,
                          "detail": "Backfilled 1 milestone(s) into MILESTONES.md"}, result["details"][0])
        text = self.read("MILESTONES.md")
        self.assertTrue(text.startswith("# Milestones\n\n## v1.1 Beta Launch (Backfilled: "))
        self.assertIn("Synthesized from archive snapshot by `/gsd-health --backfill`", text)
        self.assertTrue(text.endswith("## v1.0 Alpha\n"))

    def test_backfill_into_empty_registry_and_without_header(self):
        self.write("milestones/v2.0-ROADMAP.md", "no title here\n")
        hd.apply_repairs(self.cwd, [fake_diagnostic("W018", REMEDY_ACTION["BACKFILL_MILESTONES"], REMEDY_RISK["NONE"])], True, False)
        self.assertTrue(self.read("MILESTONES.md").startswith("# Milestones\n\n## v2.0 (Backfilled: "))
        self.write("MILESTONES.md", "plain text without a heading\n")
        hd.apply_repairs(self.cwd, [fake_diagnostic("W018", REMEDY_ACTION["BACKFILL_MILESTONES"], REMEDY_RISK["NONE"])], True, False)
        self.assertTrue(self.read("MILESTONES.md").startswith("## v2.0 (Backfilled: "))
        self.assertTrue(self.read("MILESTONES.md").endswith("plain text without a heading\n"))

    def test_regenerate_state_handler_backs_up_and_writes(self):
        self.write("STATE.md", "old state\n")
        paths = hd.repair_paths(self.cwd)
        outcome = hd.run_repair_action(self.cwd, REMEDY_ACTION["REGENERATE_STATE"], paths)
        self.assertTrue(outcome["success"])
        self.assertEqual("STATE.md", outcome["path"])
        self.assertEqual("backupState", outcome["extraDetails"][0]["action"])
        backup = Path(outcome["extraDetails"][0]["path"])
        self.assertEqual("old state\n", backup.read_text(encoding="utf-8"))
        text = self.read("STATE.md")
        self.assertTrue(text.startswith("# Session State\n\n## Project Reference\n\nSee: .planning/PROJECT.md\n"))
        self.assertIn("STATE.md regenerated by /gsd-health --repair", text)

    def test_non_destructive_regenerate_aborts_on_an_invalid_report_status_before_any_write(self):
        self.write("phases/01-setup/01-VERIFICATION.md", "---\nstatus: verified\n---\nbody\n")
        diagnostics = [fake_diagnostic("W003", REMEDY_ACTION["CREATE_CONFIG"], REMEDY_RISK["NONE"]),
                       fake_diagnostic("E004", REMEDY_ACTION["REGENERATE_STATE"], REMEDY_RISK["NONE"])]
        result = hd.apply_repairs(self.cwd, diagnostics, True, False)
        self.assertEqual([], result["applied"])
        self.assertFalse((self.planning / "config.json").exists())
        self.assertFalse((self.planning / "STATE.md").exists())
        self.assertIn("outside the closed set", result["details"][0]["error"])
        self.assertTrue(result["details"][0]["error"].startswith("not applied: the run stopped before its first write"))
        self.assertIn("outside the closed set", result["details"][1]["error"])
        self.assertFalse(result["details"][1]["error"].startswith("not applied"))


class RepairVerificationStatus(TempProject):
    def report(self, text, name="01-VERIFICATION.md"):
        return self.write(f"phases/01-setup/{name}", text)

    def repair(self, path):
        diagnostic = fake_diagnostic("W030", REMEDY_ACTION["REPAIR_VERIFICATION_STATUS"], REMEDY_RISK["NONE"],
                                     {"file": str(path), "from": "pass_with_caveats", "to": "passed"})
        return hd.apply_repairs(self.cwd, [diagnostic], True, False)

    def test_known_legacy_status_is_rewritten_and_original_kept(self):
        path = self.report("---\nphase: 01\nstatus: pass_with_caveats\nscore: 3/4\n---\n\n# Report\nstatus: body line stays\n")
        result = self.repair(path)
        self.assertEqual(["W030"], result["applied"])
        self.assertEqual(".planning/phases/01-setup/01-VERIFICATION.md", result["details"][0]["path"])
        self.assertEqual("status pass_with_caveats -> passed; original kept as legacy_status", result["details"][0]["detail"])
        self.assertEqual("---\nphase: 01\nstatus: passed\nlegacy_status: pass_with_caveats\nscore: 3/4\n---\n\n# Report\nstatus: body line stays\n",
                         self.read("phases/01-setup/01-VERIFICATION.md"))

    def test_existing_legacy_status_is_left_alone_and_crlf_preserved(self):
        path = self.report("---\r\nstatus: 'pass_with_caveats' # note\r\nlegacy_status: earlier\r\n---\r\nbody\r\n")
        result = self.repair(path)
        self.assertEqual(["W030"], result["applied"])
        self.assertIn("legacy_status was left as it was", result["details"][0]["detail"])
        self.assertEqual("---\r\nstatus: passed\r\nlegacy_status: earlier\r\n---\r\nbody\r\n", self.read("phases/01-setup/01-VERIFICATION.md"))

    def test_unknown_status_has_no_known_repair_and_is_untouched(self):
        text = "---\nstatus: partial\n---\n"
        path = self.report(text)
        result = self.repair(path)
        self.assertEqual([], result["applied"])
        self.assertIn("has no known repair", result["details"][0]["error"])
        self.assertEqual(text, self.read("phases/01-setup/01-VERIFICATION.md"))

    def test_missing_path_no_frontmatter_no_status_and_uncontained_are_refused(self):
        self.assertEqual("no report path on the finding",
                         hd.run_repair_action(self.cwd, "repairVerificationStatus", hd.repair_paths(self.cwd), {})["error"])
        for text, reason in (("no fence\n", "the report has no closed frontmatter"),
                             ("---\nstatus: x\n", "the report has no closed frontmatter"),
                             ("---\nphase: 1\n---\n", "the report frontmatter has no status")):
            path = self.report(text)
            outcome = hd.run_repair_action(self.cwd, "repairVerificationStatus", hd.repair_paths(self.cwd), {"file": str(path)})
            self.assertEqual({"success": False, "error": reason}, outcome)
        with tempfile.TemporaryDirectory() as outside:
            stray = Path(outside) / "01-VERIFICATION.md"
            stray.write_text("---\nstatus: pass_with_caveats\n---\n", encoding="utf-8")
            outcome = hd.run_repair_action(self.cwd, "repairVerificationStatus", hd.repair_paths(self.cwd), {"file": str(stray)})
            self.assertEqual("the report is not contained in its phase directory", outcome["error"])

    def test_status_repairs_run_before_the_other_repairs(self):
        path = self.report("---\nstatus: pass_with_caveats\n---\n")
        diagnostics = [fake_diagnostic("W003", REMEDY_ACTION["CREATE_CONFIG"], REMEDY_RISK["NONE"]),
                       fake_diagnostic("W030", REMEDY_ACTION["REPAIR_VERIFICATION_STATUS"], REMEDY_RISK["NONE"], {"file": str(path)})]
        result = hd.apply_repairs(self.cwd, diagnostics, True, False)
        self.assertEqual(["W030", "W003"], result["applied"])


class Evaluator(unittest.TestCase):
    def test_duplicate_code_guard(self):
        rules = [{"code": "W999", "severity": "warning", "check": lambda s: []}] * 2
        with self.assertRaisesRegex(ValueError, "duplicate rule code \"W999\" in rule table"):
            hd.evaluate_rule_table(rules, {})

    def test_unique_codes_flatten_in_order(self):
        def diag(code, message):
            return {"code": code, "severity": "warning", "message": message, "remedy": hd.advise_remedy("x")}
        rules = [{"code": "W997", "severity": "warning", "check": lambda s: [diag("W997", "a")]},
                 {"code": "W998", "severity": "warning", "check": lambda s: [diag("W998", "b"), diag("W998", "c")]}]
        self.assertEqual(["a", "b", "c"], [d["message"] for d in hd.evaluate_rule_table(rules, {})])

    def test_empty_table(self):
        self.assertEqual([], hd.evaluate_rule_table([], {}))


if __name__ == "__main__":
    unittest.main()
