"""Registration against real records, including malformed input and readback drift."""
import sys
from unittest.mock import patch

from test_phase_runtime import ROOT, RuntimeCase

sys.path.insert(0, str(ROOT / ".ai/runtime"))
from lib import plan_reconciliation, planning_integrity, state
from lib.paths import Workspace
from lib.results import VerbError

PLAN_METADATA = ("type: execute\nwave: 1\ndepends_on: []\nfiles_modified: []\n"
                 "autonomous: true\nrequirements: [REQ-01]\nacceptance: [AC-01]\n"
                 "documentation: []\nchecks: [[python, --version]]\n"
                 "must_haves: {truths: [], artifacts: [], key_links: []}\nissue_refs: []\n")


class PlanReconciliation(RuntimeCase):
    def setUp(self):
        super().setUp()
        self.phase_dir = self.directory / ".planning/phases/01-foundation"
        self.phase_dir.mkdir(parents=True)
        self.write_plan("01", "Establish the request path.\n\nWire its consumer.")
        self.write_plan("02", "Handle responses.")

    def write_plan(self, number, objective="An outcome", phase="01-foundation"):
        path = self.phase_dir / ("01-" + number + "-PLAN.md")
        path.write_text("---\nphase: " + phase + "\nplan: '" + number
                        + "'\n" + PLAN_METADATA + "---\n<objective>" + objective + "</objective>\n", encoding="utf-8")
        return path

    def records(self):
        return tuple((self.directory / ".planning" / name).read_bytes()
                     for name in ("ROADMAP.md", "STATE.md"))

    def reject_unchanged(self, *arguments, code):
        before = self.records()
        result = self.run_verb("plan.reconcile", "1", *arguments, expect_ok=False)
        self.assertEqual(result["code"], code)
        self.assertEqual(before, self.records())

    def test_proposal_contains_full_objectives_and_delta_without_writes(self):
        before = self.records()
        result = self.run_verb("plan.reconcile", "1")
        self.assertEqual(before, self.records())
        self.assertFalse(result["applied"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["plans"][0]["objective"], "Establish the request path.\n\nWire its consumer.")
        self.assertEqual(result["entries"][0], "01-01: Establish the request path. Wire its consumer.")
        self.assertTrue(result["delta"]["changed"])

    def test_each_plan_is_read_and_parsed_once_per_proposal_or_apply(self):
        workspace = Workspace(self.directory)
        for apply in (False, True):
            with self.subTest(apply=apply):
                proposal = plan_reconciliation.reconcile(workspace, "1")
                with patch.object(plan_reconciliation, "read_text", wraps=plan_reconciliation.read_text) as reader:
                    with patch.object(planning_integrity, "parse_record",
                                      wraps=planning_integrity.parse_record) as parser:
                        with patch.object(planning_integrity.yaml, "load", wraps=planning_integrity.yaml.load) as loader:
                            result = plan_reconciliation.reconcile(
                                workspace, "1", ["01-01: First", "01-02: Second"],
                                apply=apply, expected=proposal["fingerprint"])
                plan_reads = [call.args[0].name for call in reader.call_args_list
                              if call.args[0].name.endswith("-PLAN.md")]
                self.assertEqual(plan_reads, ["01-01-PLAN.md", "01-02-PLAN.md"])
                self.assertEqual(parser.call_count, 2)
                self.assertEqual(sum(call.kwargs.get("Loader") is planning_integrity.IntegrityLoader
                                     for call in loader.call_args_list), 2)
                self.assertEqual(result["applied"], apply)

    def test_apply_preserves_completed_work_adds_gap_plan_and_verifies_records(self):
        self.run_verb("roadmap.update-plan-progress", "01-01")
        self.write_plan("03", "Close a gap")
        proposal = self.run_verb("plan.reconcile", "1")
        result = self.run_verb("plan.reconcile", "1", "--apply", "--expected", proposal["fingerprint"], "--plans",
                               "01-01: Request path", "01-02: Responses", "01-03: Close gap")
        self.assertTrue(result["verified"])
        self.assertFalse(result.get("integrity_warnings"), result.get("integrity_warnings"))
        self.assertTrue(result["applied"])
        self.assertEqual(result["delta"]["added"], ["01-03"])
        self.assertEqual(result["progress"]["total_plans"], 4)
        self.assertEqual(result["progress"]["completed_plans"], 1)
        phase = self.run_verb("roadmap.get-phase", "1")
        self.assertTrue(phase["plans"][0]["done"])
        self.assertEqual([plan["description"] for plan in phase["plans"]],
                         ["Request path", "Responses", "Close gap"])

    def test_apply_requires_semantically_reviewed_descriptions(self):
        self.reject_unchanged("--apply", code="missing-plans")

    def test_invalid_state_is_rejected_before_registration_writes(self):
        (self.directory / ".planning/STATE.md").write_text("# Missing position\n", encoding="utf-8")
        proposal = self.run_verb("plan.reconcile", "1")
        self.reject_unchanged("--apply", "--expected", proposal["fingerprint"], "--plans",
                              "01-01: First", "01-02: Second", code="bad-state")

    def test_registration_preserves_authored_prose_and_does_not_exempt_its_loss(self):
        target = self.directory / ".planning/ROADMAP.md"
        original = target.read_text(encoding="utf-8").replace(
            "Plans:\n", "Authored acceptance must remain.\n\nPlans:\n", 1)
        target.write_text(original, encoding="utf-8")
        proposal = self.run_verb("plan.reconcile", "1")
        result = self.run_verb("plan.reconcile", "1", "--apply", "--expected", proposal["fingerprint"],
                               "--plans", "01-01: First", "01-02: Second")
        saved = target.read_text(encoding="utf-8")
        self.assertIn("Authored acceptance must remain.", saved)
        self.assertFalse(result.get("integrity_warnings"))
        damaged = saved.replace("Authored acceptance must remain.\n", "")
        normalized = planning_integrity.expected_roadmap(original, damaged, "plan.reconcile",
                                                          ["1"], {"apply": True}, result)
        findings = planning_integrity.content_loss(normalized, damaged, ".planning/ROADMAP.md")
        self.assertTrue(findings, "registration exemption must not hide authored prose loss")

    def test_apply_requires_inspected_fingerprint_and_rejects_changed_inputs(self):
        entries = ["01-01: First", "01-02: Second"]
        self.reject_unchanged("--apply", "--plans", *entries, code="missing-review")
        for target in (self.phase_dir / "01-01-PLAN.md", self.directory / ".planning/STATE.md",
                       self.directory / ".planning/REQUIREMENTS.md",
                       self.phase_dir / "01-CONTEXT.md"):
            with self.subTest(target=target):
                proposal = self.run_verb("plan.reconcile", "1")
                content = target.read_text(encoding="utf-8") if target.exists() else ""
                target.write_text(content + "\nChanged constraint\n", encoding="utf-8")
                self.reject_unchanged("--apply", "--expected", proposal["fingerprint"],
                                      "--plans", *entries, code="stale-review")

    def test_malformed_filename_cannot_be_silently_omitted(self):
        for name in ("01-1-PLAN.md", "02-01-PLAN.md", "01-03-plan.md", "PLAN-03.md"):
            with self.subTest(name=name):
                path = self.phase_dir / name
                path.write_text("bad", encoding="utf-8")
                self.reject_unchanged(code="plan-filename")
                path.unlink()

    def test_wrong_missing_or_malformed_frontmatter_is_rejected(self):
        path = self.phase_dir / "01-01-PLAN.md"
        valid = path.read_text(encoding="utf-8")
        for content, code in (("<objective>Missing metadata</objective>", "planning-integrity"),
                              ("---\nphase: [broken\n---\n<objective>x</objective>", "planning-integrity"),
                              (valid.replace("phase: 01-foundation", "phase: 02-other"), "plan-frontmatter"),
                              (valid.replace("plan: '01'", "plan: true"), "planning-integrity")):
            with self.subTest(content=content):
                path.write_text(content, encoding="utf-8")
                before = self.records()
                result = self.run_verb("plan.reconcile", "1", expect_ok=False)
                self.assertEqual(result["code"], code)
                self.assertEqual(before, self.records())

    def test_empty_or_duplicate_objective_is_rejected(self):
        for objective in (" ", "one</objective><objective>two"):
            self.write_plan("01", objective)
            self.reject_unchanged(code="plan-objective")

    def test_missing_existing_plan_even_if_uncompleted_is_rejected(self):
        (self.phase_dir / "01-02-PLAN.md").unlink()
        self.reject_unchanged(code="missing-plan-file")

    def test_reviewed_entries_must_match_ids_order_count_and_single_line(self):
        for entries, code in ((["01-01: Only one"], "plan-set-mismatch"),
                              (["01-02: Second", "01-01: First"], "plan-set-mismatch"),
                              (["01-01: First", "01-01: Duplicate"], "duplicate-plan"),
                              (["01-01: First\nInjected", "01-02: Second"], "bad-plan")):
            with self.subTest(entries=entries):
                self.reject_unchanged("--apply", "--plans", *entries, code=code)

    def test_unquoted_yaml_plan_number_and_decimal_phase_are_supported(self):
        self.run_verb("phase.insert", "1", "Gap")
        path = self.directory / ".planning/phases/01.1-gap/01.1-01-PLAN.md"
        path.write_text("---\nphase: 01.1-gap\nplan: 01\n" + PLAN_METADATA
                        + "---\n<objective>Fix gap</objective>", encoding="utf-8")
        proposal = self.run_verb("plan.reconcile", "1.1")
        result = self.run_verb("plan.reconcile", "1.1", "--apply", "--expected", proposal["fingerprint"],
                               "--plans", "01.1-01: Fix gap")
        self.assertEqual(result["count"], 1)
        self.assertTrue(result["verified"])

    def test_canonical_invalid_metadata_is_rejected_in_proposal_and_apply(self):
        path = self.phase_dir / "01-01-PLAN.md"
        valid = path.read_text(encoding="utf-8")
        invalid_cases = {
            "missing required fields": "---\nphase: 01-foundation\nplan: '01'\n---\n<objective>x</objective>",
            "zero wave": valid.replace("wave: 1", "wave: 0"),
            "empty requirements": valid.replace("requirements: [REQ-01]", "requirements: []"),
            "scalar acceptance": valid.replace("acceptance: [AC-01]", "acceptance: AC-01"),
            "checks string list": valid.replace("checks: [[python, --version]]", "checks: [python]"),
            "duplicate phase": valid.replace("phase: 01-foundation", "phase: 02-other\nphase: 01-foundation"),
            "duplicate plan": valid.replace("plan: '01'", "plan: '02'\nplan: '01'"),
        }
        for name, content in invalid_cases.items():
            with self.subTest(case=name):
                path.write_text(valid, encoding="utf-8")
                proposal = self.run_verb("plan.reconcile", "1")
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(VerbError):
                    planning_integrity.validate_record(".planning/phases/01-foundation/01-01-PLAN.md", content)
                self.reject_unchanged(code="planning-integrity")
                self.reject_unchanged("--apply", "--expected", proposal["fingerprint"], "--plans",
                                      "01-01: First", "01-02: Second", code="planning-integrity")

    def test_corrupted_postwrite_records_are_reported_not_marked_verified(self):
        original = state.register_plans
        for record in ("ROADMAP.md", "STATE.md"):
            with self.subTest(record=record):
                def corrupt(*args, **kwargs):
                    result = original(*args, **kwargs)
                    target = self.directory / ".planning" / record
                    target.write_text(target.read_text(encoding="utf-8") + "unexpected drift\n", encoding="utf-8")
                    return result
                with patch.object(state, "register_plans", side_effect=corrupt):
                    proposal = plan_reconciliation.reconcile(Workspace(self.directory), "1")
                    with self.assertRaises(VerbError) as caught:
                        plan_reconciliation.reconcile(Workspace(self.directory), "1",
                                                      ["01-01: First", "01-02: Second"], apply=True,
                                                      expected=proposal["fingerprint"])
                self.assertEqual(caught.exception.code, "plan-readback")
