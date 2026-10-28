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

def field(value, scope="complete", **extra):
    return {"value": value, "scope": scope, **extra}


def make_snapshot(**overrides):
    """A healthy, empty PlanningSnapshot-shaped dict (upstream field names)."""
    snapshot = {
        "cwd": "/project",
        "workstream": None,
        "phaseIdConvention": None,
        "projectSections": {"exists": True, "value": ["What This Is", "Core Value", "Requirements"], "scope": "complete"},
        "milestone": field({"version": "v1.0"}),
        "currentPhaseLabel": field("1 of 1"),
        "stateStatus": field("executing"),
        "statePhaseTokens": field([]),
        "config": field({}, exists=True),
        "phaseDirs": field([]),
        "allPhaseDirNames": field([]),
        "archivedPhaseTokens": field([]),
        "phases": field([]),
        "roadmapDeclaredPhases": field([]),
        "roadmapSentinelPhaseTokens": field([]),
        "roadmapPhaseCheckboxes": field({}),
        "roadmapBracketIncoherences": field([]),
        "currentMilestoneRoadmapPhaseIds": field([]),
        "researchValidationStatus": field([]),
        "agentInstall": field({"agents_installed": True, "installed_agents": ["a"], "missing_agents": [], "incomplete_agents": [],
                               "agents_dir": "/agents"}),
        "milestoneArchiveStatus": field({"archivedVersions": [], "documentedVersions": []}),
        "planningRootFiles": field([]),
        "worktreeHealth": field([], reason=None),
        "perPhasePlanNumbering": field([]),
        "perPhaseOrphanSummaries": field([]),
        "perPhaseWaveMissingPlans": field([]),
    }
    snapshot.update(overrides)
    return snapshot


def codes(diagnostics):
    return [d["code"] for d in diagnostics]


def group(name):
    return {r["code"]: r for r in rules_mod.RULE_GROUPS[name]}


def run_rule(name, code, snapshot):
    return group(name)[code]["check"](snapshot)


class RootExistence(unittest.TestCase):
    def test_rules_and_severities(self):
        rules = group("root-existence")
        self.assertEqual(["E002", "E003", "E004", "W001"], list(rules))
        self.assertEqual(["error", "error", "error", "warning"], [r["severity"] for r in rules.values()])
        self.assertEqual([False] * 4, [r["repairable"] for r in rules.values()])

    def test_e002(self):
        self.assertEqual([], run_rule("root-existence", "E002", make_snapshot()))
        found = run_rule("root-existence", "E002", make_snapshot(projectSections={"exists": False, "value": None, "scope": "unreadable"}))
        self.assertEqual([{"code": "E002", "severity": "error", "message": "PROJECT.md not found",
                           "remedy": {"action": "advise", "risk": "none", "args": {"command": "/gsd-new-project"}}}], found)

    def test_e003_fires_on_unreadable_milestone(self):
        self.assertEqual([], run_rule("root-existence", "E003", make_snapshot()))
        found = run_rule("root-existence", "E003", make_snapshot(milestone=field(None, "unreadable")))
        self.assertEqual("ROADMAP.md not found", found[0]["message"])
        self.assertEqual("/gsd-new-milestone", found[0]["remedy"]["args"]["command"])

    def test_e004_is_destructive_regenerate_state(self):
        self.assertEqual([], run_rule("root-existence", "E004", make_snapshot()))
        found = run_rule("root-existence", "E004", make_snapshot(currentPhaseLabel=field(None, "unreadable")))
        self.assertEqual({"action": "regenerateState", "risk": "destructive", "args": {}}, found[0]["remedy"])

    def test_w001_once_per_missing_section(self):
        missing_all = make_snapshot(projectSections={"exists": True, "value": [], "scope": "complete"})
        found = run_rule("root-existence", "W001", missing_all)
        self.assertEqual(["PROJECT.md missing section: ## What This Is", "PROJECT.md missing section: ## Core Value",
                          "PROJECT.md missing section: ## Requirements"], [d["message"] for d in found])
        one = make_snapshot(projectSections={"exists": True, "value": ["What This Is", "Requirements"], "scope": "complete"})
        self.assertEqual(["PROJECT.md missing section: ## Core Value"], [d["message"] for d in run_rule("root-existence", "W001", one)])
        self.assertEqual([], run_rule("root-existence", "W001", make_snapshot()))
        absent = make_snapshot(projectSections={"exists": False, "value": None, "scope": "unreadable"})
        self.assertEqual([], run_rule("root-existence", "W001", absent))


def with_config(value, exists=True):
    return make_snapshot(config=field(value, exists=exists))


class ConfigValidation(unittest.TestCase):
    def test_table_shape(self):
        rules = group("config-validation")
        self.assertEqual(["W003", "E005", "W004", "W008", "W016", "W012", "W013", "W014", "W015", "W022", "W029"], list(rules))
        self.assertEqual("error", rules["E005"]["severity"])
        self.assertEqual({"W003", "W008", "W016"}, {c for c, r in rules.items() if r["repairable"]})

    def test_w003(self):
        self.assertEqual([], run_rule("config-validation", "W003", with_config({})))
        found = run_rule("config-validation", "W003", with_config(None, exists=False))
        self.assertEqual({"action": "createConfig", "risk": "none", "args": {}}, found[0]["remedy"])

    def test_e005(self):
        self.assertEqual([], run_rule("config-validation", "E005", with_config(None, exists=False)))
        self.assertEqual([], run_rule("config-validation", "E005", with_config({})))
        found = run_rule("config-validation", "E005", with_config(None, exists=True))
        self.assertEqual("config.json: JSON parse error", found[0]["message"])
        self.assertEqual({"action": "resetConfig", "risk": "destructive", "args": {}}, found[0]["remedy"])

    def test_w004(self):
        found = run_rule("config-validation", "W004", with_config({"model_profile": "turbo"}))
        self.assertEqual('config.json: invalid model_profile "turbo"', found[0]["message"])
        self.assertEqual("Valid values: quality, balanced, budget, adaptive, inherit", found[0]["remedy"]["args"]["command"])
        self.assertEqual([], run_rule("config-validation", "W004", with_config({"model_profile": "balanced"})))
        self.assertEqual([], run_rule("config-validation", "W004", with_config({})))
        self.assertEqual([], run_rule("config-validation", "W004", with_config(None)))

    def test_w008_and_w016(self):
        for code, key, action in (("W008", "nyquist_validation", "addNyquistKey"), ("W016", "ai_integration_phase", "addAiIntegrationPhaseKey")):
            found = run_rule("config-validation", code, with_config({"workflow": {}}))
            self.assertEqual(action, found[0]["remedy"]["action"])
            self.assertEqual([], run_rule("config-validation", code, with_config({"workflow": {key: False}})))
            self.assertEqual([], run_rule("config-validation", code, with_config({"workflow": {key: None}})))
            self.assertEqual([], run_rule("config-validation", code, with_config({})))
            self.assertEqual([], run_rule("config-validation", code, with_config(None)))
        found = run_rule("config-validation", "W016", with_config({"workflow": {}}))
        self.assertIn("run /gsd-ai-integration-phase before planning AI system phases", found[0]["message"])

    def test_w012(self):
        found = run_rule("config-validation", "W012", with_config({"branching_strategy": "trunk"}))
        self.assertEqual('config.json: invalid branching_strategy "trunk"', found[0]["message"])
        for valid in ("none", "phase", "milestone"):
            self.assertEqual([], run_rule("config-validation", "W012", with_config({"branching_strategy": valid})))
        self.assertEqual([], run_rule("config-validation", "W012", with_config({})))

    def test_w013(self):
        for bad, text in (("big", "big"), (0, "0"), (-5, "-5"), (1.5, "1.5"), (None, "null"), (True, "true"), ([], "")):
            found = run_rule("config-validation", "W013", with_config({"context_window": bad}))
            self.assertEqual(f'config.json: context_window should be a positive integer, got "{text}"', found[0]["message"], bad)
        for good in (1, 200000, 2.0):
            self.assertEqual([], run_rule("config-validation", "W013", with_config({"context_window": good})))
        self.assertEqual([], run_rule("config-validation", "W013", with_config({})))

    def test_w014_and_w015(self):
        found = run_rule("config-validation", "W014", with_config({"phase_branch_template": "gsd/phase"}))
        self.assertEqual("config.json: phase_branch_template missing {phase} placeholder", found[0]["message"])
        self.assertEqual([], run_rule("config-validation", "W014", with_config({"phase_branch_template": "gsd/{phase}"})))
        self.assertEqual([], run_rule("config-validation", "W014", with_config({})))
        found = run_rule("config-validation", "W015", with_config({"milestone_branch_template": "gsd/ms"}))
        self.assertEqual("config.json: milestone_branch_template missing {milestone} placeholder", found[0]["message"])
        self.assertEqual([], run_rule("config-validation", "W015", with_config({"milestone_branch_template": "{milestone}"})))
        self.assertEqual([], run_rule("config-validation", "W015", with_config({"milestone_branch_template": ""})))

    def test_w022_unknown_phase_type_and_invalid_tier(self):
        models = {"planning": "sonnet", "bogus": "opus", "execution": "gigantic", "research": 7}
        found = run_rule("config-validation", "W022", with_config({"models": models}))
        self.assertEqual([
            'config.json: models has an unknown phase type "bogus" which will be ignored',
            'config.json: models.execution has an invalid tier value "gigantic" which will be ignored',
            "config.json: models.research has an invalid tier value 7 which will be ignored"], [d["message"] for d in found])
        self.assertEqual("Valid phase types: planning, discuss, research, execution, verification, completion", found[0]["remedy"]["args"]["command"])
        self.assertEqual("Valid tiers: opus, sonnet, haiku, inherit", found[1]["remedy"]["args"]["command"])

    def test_w022_non_object_models(self):
        for bad, text in (("sonnet", '"sonnet"'), (["a"], '["a"]'), (5, "5"), (False, "false")):
            found = run_rule("config-validation", "W022", with_config({"models": bad}))
            self.assertEqual(1, len(found), bad)
            self.assertEqual(f"config.json: models is set to {text}, but must be an object mapping phase types to tiers — this value will be ignored",
                             found[0]["message"])
        for fine in ({"models": {"planning": "inherit"}}, {"models": {}}, {"models": None}, {}):
            self.assertEqual([], run_rule("config-validation", "W022", with_config(fine)))

    def test_w029(self):
        def tracked(ignored, tracked_, scope="complete"):
            return make_snapshot(planningTracked=field({"ignored": ignored, "tracked": tracked_}, scope))
        found = run_rule("config-validation", "W029", tracked(True, True))
        self.assertEqual("Run `git rm -r --cached .planning/` to untrack it (the ignore rule then takes effect); this does not delete the files on disk",
                         found[0]["remedy"]["args"]["command"])
        for snapshot in (tracked(False, True), tracked(True, False), tracked(False, False), tracked(True, True, "unreadable"), make_snapshot()):
            self.assertEqual([], run_rule("config-validation", "W029", snapshot))
        self.assertFalse(group("config-validation")["W029"]["repairable"])


class AgentInstall(unittest.TestCase):
    def check(self, **status):
        base = {"agents_installed": False, "installed_agents": ["x"], "missing_agents": [], "incomplete_agents": [], "agents_dir": "/a"}
        base.update(status)
        return run_rule("agent-install", "W010", make_snapshot(agentInstall=field(base)))

    def test_single_rule(self):
        self.assertEqual(["W010"], list(group("agent-install")))

    def test_all_installed(self):
        self.assertEqual([], self.check(agents_installed=True))

    def test_unreadable_scan_is_silent(self):
        snapshot = make_snapshot(agentInstall=field({"agents_installed": False}, "unreadable"))
        self.assertEqual([], run_rule("agent-install", "W010", snapshot))

    def test_zero_agents(self):
        found = self.check(installed_agents=[])
        self.assertEqual('No GSD agents found in /a — Task(subagent_type="gsd-*") will fall back to general-purpose', found[0]["message"])
        self.assertEqual("Run the GSD installer: npx @opengsd/gsd-core@latest", found[0]["remedy"]["args"]["command"])

    def test_incomplete_only(self):
        found = self.check(incomplete_agents=["p", "q"])
        self.assertEqual("Incomplete agent installs (missing generated file): p, q — affected workflows may fall back to general-purpose", found[0]["message"])
        self.assertEqual("Re-run the GSD installer to complete the install: npx @opengsd/gsd-core@latest", found[0]["remedy"]["args"]["command"])

    def test_missing_and_incomplete(self):
        found = self.check(missing_agents=["m"], incomplete_agents=["p"])
        self.assertEqual("Missing 1 GSD agents: m; incomplete agent installs (missing generated file): p — affected workflows will fall back to general-purpose",
                         found[0]["message"])

    def test_missing_only(self):
        found = self.check(missing_agents=["m", "n"])
        self.assertEqual("Missing 2 GSD agents: m, n — affected workflows will fall back to general-purpose", found[0]["message"])


class MilestoneArchiveHygiene(unittest.TestCase):
    def archive(self, archived, documented):
        return make_snapshot(milestoneArchiveStatus=field({"archivedVersions": archived, "documentedVersions": documented}))

    def test_one_aggregate_diagnostic(self):
        found = run_rule("milestone-archive-hygiene", "W018", self.archive(["v1.0", "v1.1", "v2.0"], ["v1.0"]))
        self.assertEqual(1, len(found))
        self.assertEqual("MILESTONES.md missing 2 archived milestone(s): v1.1, v2.0", found[0]["message"])
        self.assertEqual({"action": "backfillMilestones", "risk": "none", "args": {}}, found[0]["remedy"])

    def test_w018_silent_cases(self):
        self.assertEqual([], run_rule("milestone-archive-hygiene", "W018", self.archive([], ["v1.0"])))
        self.assertEqual([], run_rule("milestone-archive-hygiene", "W018", self.archive(["v1.0"], ["v1.0"])))

    def test_w019_one_per_unrecognized_markdown_file(self):
        files = ["PROJECT.md", "ROADMAP.md", "STATE.md", "notes.md", "TODO.md", "config.json", "random.txt", "v1.0-MILESTONE-AUDIT.md",
                 "v2.1-summary.md", "PATTERNS.md"]
        found = run_rule("milestone-archive-hygiene", "W019", make_snapshot(planningRootFiles=field(files)))
        self.assertEqual(["Unrecognized .planning/ file: notes.md — not a canonical GSD artifact",
                          "Unrecognized .planning/ file: TODO.md — not a canonical GSD artifact"], [d["message"] for d in found])

    def test_canonical_planning_file_predicate(self):
        self.assertTrue(rules_mod.is_canonical_planning_file("MILESTONES.md"))
        self.assertTrue(rules_mod.is_canonical_planning_file("V3.2.1-notes.MD"))
        self.assertFalse(rules_mod.is_canonical_planning_file("state.md"))
        self.assertFalse(rules_mod.is_canonical_planning_file("v3-notes.md"))

    def test_repairable_flags(self):
        rules = group("milestone-archive-hygiene")
        self.assertEqual([True, False], [rules["W018"]["repairable"], rules["W019"]["repairable"]])


class WorktreeHealth(unittest.TestCase):
    def health(self, findings, scope="complete", reason=None, cwd="/project"):
        return make_snapshot(worktreeHealth=field(findings, scope, reason=reason), cwd=cwd)

    def test_w020_timeout_and_list_failure(self):
        found = run_rule("worktree-health", "W020", self.health([], "unreadable", "git_timed_out"))
        self.assertEqual("Worktree health check degraded: git worktree list timed out after 10s — orphan/stale worktrees could not be inspected", found[0]["message"])
        found = run_rule("worktree-health", "W020", self.health([], "unreadable", "git_list_failed"))
        self.assertEqual("Worktree health check degraded: git worktree list failed — orphan/stale worktrees could not be inspected", found[0]["message"])
        self.assertEqual([], run_rule("worktree-health", "W020", self.health([], "unreadable", "not_a_git_repo")))
        self.assertEqual([], run_rule("worktree-health", "W020", self.health([], "unreadable", "exception")))
        self.assertEqual([], run_rule("worktree-health", "W020", self.health([])))

    def test_w020_once_per_unverified_finding(self):
        findings = [{"kind": "unverified", "path": "/wt/a"}, {"kind": "orphan", "path": "/wt/b"}, {"kind": "unverified", "path": "/wt/c"}]
        found = run_rule("worktree-health", "W020", self.health(findings))
        self.assertEqual(["Worktree health check degraded: could not stat /wt/a — presence/staleness could not be verified",
                          "Worktree health check degraded: could not stat /wt/c — presence/staleness could not be verified"], [d["message"] for d in found])

    def test_w017_orphans_only(self):
        findings = [{"kind": "orphan", "path": "/wt/o"}, {"kind": "stale", "path": "/wt/s", "ageMinutes": 9}, {"kind": "unverified", "path": "/wt/u"}]
        found = run_rule("worktree-health", "W017", self.health(findings))
        self.assertEqual(["Orphan git worktree: /wt/o (path no longer exists on disk)"], [d["message"] for d in found])
        self.assertEqual("git worktree prune", found[0]["remedy"]["args"]["command"])

    def test_w027_stale_only_and_message(self):
        findings = [{"kind": "stale", "path": "/wt/s", "ageMinutes": 90}, {"kind": "orphan", "path": "/wt/o"}]
        found = run_rule("worktree-health", "W027", self.health(findings, cwd="/elsewhere"))
        self.assertEqual(1, len(found))
        self.assertEqual("Stale git worktree: /wt/s (last modified 90 minutes ago). Inspect uncommitted work first: git -C /wt/s status --porcelain; "
                         "if clean run: git worktree remove /wt/s; only add --force to discard changes", found[0]["message"])
        self.assertEqual("git -C <path> status --porcelain; if clean: git worktree remove <path>; add --force only to discard changes",
                         found[0]["remedy"]["args"]["command"])

    def test_w027_excludes_the_active_worktree(self):
        stale = os.path.abspath(os.path.join(os.sep, "wt", "active")).replace("\\", "/")
        findings = [{"kind": "stale", "path": stale, "ageMinutes": 90}]
        self.assertEqual([], run_rule("worktree-health", "W027", self.health(findings, cwd=stale)))
        self.assertEqual([], run_rule("worktree-health", "W027", self.health(findings, cwd=stale + "/sub/dir")))
        self.assertEqual(1, len(run_rule("worktree-health", "W027", self.health(findings, cwd=stale + "-other"))))

    def test_is_active_worktree_path(self):
        is_active = rules_mod.is_active_worktree_path
        base = os.path.abspath(os.path.join(os.sep, "Repo", "WT")).replace("\\", "/")
        self.assertTrue(is_active(base, base, "linux"))
        self.assertTrue(is_active(base + "/nested", base, "linux"))
        self.assertFalse(is_active(base.lower(), base, "linux"))
        self.assertTrue(is_active(base.lower(), base, "win32"))
        self.assertTrue(is_active(base.lower() + "/nested", base, "win32"))
        self.assertFalse(is_active(base + "x", base, "win32"))
        self.assertTrue(is_active(base + "/", base, "win32"))
        self.assertTrue(is_active(base, base + "/", "win32"))
        self.assertFalse(is_active(os.path.dirname(base), base, "win32"))

    def test_rule_order(self):
        self.assertEqual(["W020", "W017", "W027"], list(group("worktree-health")))


class ConsistencyRules(unittest.TestCase):
    def test_table(self):
        rules = group("consistency")
        self.assertEqual(["C001", "C002", "C003", "C004"], list(rules))
        for rule in rules.values():
            self.assertEqual(("warning", False), (rule["severity"], rule["repairable"]))

    def test_c001_gaps(self):
        snapshot = make_snapshot(allPhaseDirNames=field(["01-a", "02-b", "04-d", "10-j"]))
        found = run_rule("consistency", "C001", snapshot)
        self.assertEqual(["Gap in phase numbering: 2 → 4", "Gap in phase numbering: 4 → 10"], [d["message"] for d in found])
        self.assertEqual("Create the missing phase directory or renumber to close the gap", found[0]["remedy"]["args"]["command"])

    def test_c001_baseline_custom_sentinel_and_dotted(self):
        self.assertEqual([], run_rule("consistency", "C001", make_snapshot(allPhaseDirNames=field(["01-a", "02-b", "03-c"]))))
        custom = make_snapshot(allPhaseDirNames=field(["01-a", "05-e"]), config=field({"phase_naming": "custom"}, exists=True))
        self.assertEqual([], run_rule("consistency", "C001", custom))
        sentinel = make_snapshot(allPhaseDirNames=field(["01-a", "02-b", "999-interim", "0-drafts"]))
        self.assertEqual([], run_rule("consistency", "C001", sentinel))
        dotted = make_snapshot(allPhaseDirNames=field(["01-a", "02.1-b", "03-c", "GSD.02-05-x", "notes"]))
        self.assertEqual(["Gap in phase numbering: 1 → 3"], [d["message"] for d in run_rule("consistency", "C001", dotted)])

    def test_c002(self):
        snapshot = make_snapshot(perPhasePlanNumbering=field([{"phaseDir": "01-a", "planNums": [1, 3, 4]}, {"phaseDir": "02-b", "planNums": [1, 2]}]))
        found = run_rule("consistency", "C002", snapshot)
        self.assertEqual(["Gap in plan numbering in 01-a: plan 1 → 3"], [d["message"] for d in found])

    def test_c003_and_c004(self):
        found = run_rule("consistency", "C003", make_snapshot(perPhaseOrphanSummaries=field([{"phaseDir": "01-a", "orphanSummary": "02-SUMMARY.md"}])))
        self.assertEqual("Summary 02-SUMMARY.md in 01-a has no matching PLAN.md", found[0]["message"])
        found = run_rule("consistency", "C004", make_snapshot(perPhaseWaveMissingPlans=field([{"phaseDir": "01-a", "plan": "01-PLAN.md"}])))
        self.assertEqual("01-a/01-PLAN.md: missing 'wave' in frontmatter", found[0]["message"])
        self.assertEqual("Add a 'wave' key to the plan's frontmatter", found[0]["remedy"]["args"]["command"])


class InstallSurfaceShadowing(unittest.TestCase):
    def tearDown(self):
        rules_mod.set_install_shadow_renderer(None)

    def test_inert_without_a_renderer(self):
        self.assertEqual(["W028"], list(group("install-surface-shadowing")))
        self.assertEqual([], run_rule("install-surface-shadowing", "W028", make_snapshot()))

    def test_renderer_lines_become_one_diagnostic(self):
        rules_mod.set_install_shadow_renderer(lambda cwd: ("claude", [f"scope shadowed in {cwd}", "second line"]))
        found = run_rule("install-surface-shadowing", "W028", make_snapshot(cwd="/proj"))
        self.assertEqual("scope shadowed in /proj second line", found[0]["message"])
        self.assertEqual("Review install scopes for claude: npx @opengsd/gsd-core@latest", found[0]["remedy"]["args"]["command"])

    def test_no_lines_or_a_throwing_renderer_degrade_to_nothing(self):
        rules_mod.set_install_shadow_renderer(lambda cwd: ("claude", []))
        self.assertEqual([], run_rule("install-surface-shadowing", "W028", make_snapshot()))

        def boom(cwd):
            raise RuntimeError("no resolver")
        rules_mod.set_install_shadow_renderer(boom)
        self.assertEqual([], run_rule("install-surface-shadowing", "W028", make_snapshot()))


class JavaScriptSemanticsHelpers(unittest.TestCase):
    def test_truthy(self):
        truthy = rules_mod._truthy
        for value in ({}, [], "x", 1, -1, True, 0.5):
            self.assertTrue(truthy(value), value)
        for value in (None, False, 0, 0.0, "", float("nan"), rules_mod._UNDEF):
            self.assertFalse(truthy(value), value)

    def test_js_string(self):
        js = rules_mod._js_string
        self.assertEqual(["null", "true", "false", "5", "1.5", "a,b", "[object Object]", "x"],
                         [js(None), js(True), js(False), js(5.0), js(1.5), js(["a", "b"]), js({}), js("x")])


if __name__ == "__main__":
    unittest.main()
