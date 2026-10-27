"""UI-gate Git/evidence behavior fixtures; execution follows the user's check order."""
import hashlib
import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class UiGate(RuntimeCase):
    BODY = "# Contract\n\nUse the existing blue action button and keyboard focus.\n"
    METADATA = {"phase": "01", "slug": "ui-contract"}

    def commit_inputs(self, message):
        self.git("add", ".")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def spec_text(self, evidence=None, body=None):
        lines = ['---', 'phase: "01"', 'slug: "ui-contract"',
                 'status: approved' if evidence else 'status: draft']
        if evidence:
            lines.append('ui_checker: ' + json.dumps(evidence))
        return "\n".join(lines) + "\n---\n" + (self.BODY if body is None else body)

    def reviewed_contract(self):
        directory = Path(self.phase("Frontend interface"))
        self.context = directory/"01-CONTEXT.md"
        self.context.write_text('---\nui_scope: true\n---\n# Decisions\nUse the existing blue design system.\n', encoding="utf-8")
        self.spec = directory/"01-UI-SPEC.md"
        self.spec.write_text(self.spec_text(), encoding="utf-8")
        revision = self.commit_inputs("record design inputs")
        payload = {"metadata": self.METADATA, "body": self.BODY}
        return {"ui_safety_gate": True, "role": "ui-checker", "verdict": "APPROVED", "phase": "01",
                "spec_path": self.spec.relative_to(self.root).as_posix(),
                "context_path": self.context.relative_to(self.root).as_posix(),
                "reviewed_revision": revision,
                "spec_digest": digest(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))),
                "context_digest": digest(self.context.read_text(encoding="utf-8")),
                "roadmap_digest": digest((self.root/".planning/ROADMAP.md").read_text(encoding="utf-8")),
                "checker_id": "fixture-checker-worker", "author_id": "fixture-researcher-worker",
                "session": "fixture-phase-session", "reviewed_at": "2026-10-27T00:00:00Z",
                "unexamined": [],
                "dimensions": [{"dimension": n, "verdict": "PASS", "evidence": f"01-UI-SPEC.md:3 dimension {n} inspected"} for n in range(1, 8)]}

    def approve(self, evidence):
        self.spec.write_text(self.spec_text(evidence), encoding="utf-8")
        self.commit_inputs("record independent design approval")

    def blocked(self):
        return self.cli("check.ui-plan-gate", "1", status=1)

    def test_ui_phase_requires_real_checker_evidence_not_status(self):
        evidence = self.reviewed_contract()
        self.assertTrue(self.blocked()["blocked"])
        self.spec.write_text(self.spec_text().replace('status: draft', 'status: approved'), encoding="utf-8")
        self.commit_inputs("status only is not evidence")
        result = self.blocked()
        self.assertIn("independent ui-checker", result["reason"])

    def test_complete_independent_review_and_exact_approval_commit_pass(self):
        evidence = self.reviewed_contract()
        evidence["dimensions"][1]["verdict"] = "FLAG"
        self.approve(evidence)
        result = self.cli("check.ui-plan-gate", "1")
        self.assertFalse(result["blocked"])
        self.assertEqual(evidence["spec_digest"], result["spec_digest"])

    def test_wrong_context_digest_blocks_even_with_approved_status(self):
        evidence = self.reviewed_contract()
        evidence["context_digest"] = "0" * 64
        self.approve(evidence)
        self.assertIn("context_digest", self.blocked()["reason"])

    def test_changed_locked_context_invalidates_prior_review(self):
        evidence = self.reviewed_contract()
        self.approve(evidence)
        self.context.write_text(self.context.read_text(encoding="utf-8") + "Use red instead.\n", encoding="utf-8")
        self.commit_inputs("change locked design decision")
        self.assertIn("context_digest", self.blocked()["reason"])

    def test_contract_changes_invalidate_spec_digest(self):
        evidence = self.reviewed_contract()
        self.approve(evidence)
        self.spec.write_text(self.spec_text(evidence, body=self.BODY + "Use a new screen.\n"), encoding="utf-8")
        self.commit_inputs("change UI contract")
        self.assertIn("spec_digest", self.blocked()["reason"])

    def test_source_change_then_restore_is_not_current_review(self):
        evidence = self.reviewed_contract()
        self.approve(evidence)
        previous = (self.root/"README.md").read_text(encoding="utf-8")
        self.put("README.md", "changed source\n")
        self.commit_inputs("change source after review")
        self.put("README.md", previous)
        self.commit_inputs("restore source does not erase intervening drift")
        self.assertIn("Source or phase inputs changed", self.blocked()["reason"])

    def test_body_change_then_restore_cannot_hide_under_approval_only_path(self):
        evidence = self.reviewed_contract()
        self.approve(evidence)
        self.spec.write_text(self.spec_text(evidence, body=self.BODY + "hidden intervening decision\n"), encoding="utf-8")
        self.commit_inputs("change same-path design semantics")
        self.spec.write_text(self.spec_text(evidence), encoding="utf-8")
        self.commit_inputs("restore same-path contract")
        self.assertIn("intervening restored version", self.blocked()["reason"])

    def test_wrong_reviewed_revision_without_actual_inputs_blocks(self):
        evidence = self.reviewed_contract()
        evidence["reviewed_revision"] = self.git("rev-parse", "HEAD~1")
        self.approve(evidence)
        self.assertTrue(self.blocked()["blocked"])

    def test_missing_dimension_or_unexamined_scope_is_not_approval(self):
        evidence = self.reviewed_contract()
        evidence["dimensions"].pop()
        self.approve(evidence)
        self.assertIn("all seven", self.blocked()["reason"])

    def test_blocking_dimension_cannot_be_status_approved(self):
        evidence = self.reviewed_contract()
        evidence["dimensions"][0]["verdict"] = "BLOCK"
        self.approve(evidence)
        self.assertIn("blocking", self.blocked()["reason"])

    def test_author_cannot_supply_own_independent_checker_identity(self):
        evidence = self.reviewed_contract()
        evidence["checker_id"] = evidence["author_id"]
        self.approve(evidence)
        self.assertIn("independent", self.blocked()["reason"])

    def test_uncommitted_contract_or_extra_source_prevents_frozen_identity(self):
        evidence = self.reviewed_contract()
        self.approve(evidence)
        self.put("extra.py", "print('unreviewed')\n")
        self.assertIn("Commit phase/source", self.blocked()["reason"])

    def test_backend_phase_has_no_ui_gate_even_when_track_enabled(self):
        self.phase("Background queue")
        self.cli("config-set", "workflow.ui_phase", "true")
        result = self.cli("check.ui-plan-gate", "1")
        self.assertFalse(result["required"])
        self.assertEqual("no-ui-scope", result["reason"])

    def test_explicit_no_ui_scope_does_not_invent_screens(self):
        directory = Path(self.phase("Backend API"))
        (directory/"01-CONTEXT.md").write_text("No UI. Build only the command line queue.\n", encoding="utf-8")
        self.assertFalse(self.cli("check.ui-plan-gate", "1")["required"])

    def test_recorded_scope_false_ignores_incidental_ui_examples(self):
        directory = Path(self.phase("Workflow UI documentation"))
        (directory/"01-CONTEXT.md").write_text("---\nui_scope: false\n---\nDocument UI examples; no product screens.\n", encoding="utf-8")
        self.assertFalse(self.cli("check.ui-plan-gate", "1")["required"])

    def test_context_only_ui_scope_activates_gate(self):
        directory = Path(self.phase("Account changes"))
        (directory/"01-CONTEXT.md").write_text("---\nui_scope: true\n---\n# Decisions\nAdd the account form.\n", encoding="utf-8")
        self.assertTrue(self.blocked()["required"])

    def test_deferred_ui_idea_does_not_trigger_backend_design(self):
        directory = Path(self.phase("Background queue"))
        (directory/"01-CONTEXT.md").write_text("## Decisions\nImplement the worker queue.\n\n## Deferred Ideas\nAdd a frontend UI later.\n", encoding="utf-8")
        self.assertFalse(self.cli("check.ui-plan-gate", "1")["required"])

    def test_unexamined_dimension_scope_prevents_approval(self):
        evidence = self.reviewed_contract()
        evidence["unexamined"] = ["registry source unavailable"]
        self.approve(evidence)
        self.assertIn("coverage is incomplete", self.blocked()["reason"])

    def test_duplicate_dimension_cannot_substitute_for_missing_dimension(self):
        evidence = self.reviewed_contract()
        evidence["dimensions"][6]["dimension"] = 1
        self.approve(evidence)
        self.assertIn("unique IDs", self.blocked()["reason"])

    def test_wrong_phase_or_context_path_cannot_reuse_another_review(self):
        evidence = self.reviewed_contract()
        evidence["context_path"] = ".planning/phases/02-other/02-CONTEXT.md"
        self.approve(evidence)
        self.assertIn("context_path", self.blocked()["reason"])

    def test_disabled_registry_dimension_requires_actual_disabled_policy(self):
        evidence = self.reviewed_contract()
        evidence["dimensions"][5]["verdict"] = "DISABLED"
        self.approve(evidence)
        self.assertIn("blocking or missing", self.blocked()["reason"])

    def test_explicit_safety_opt_out_keeps_seven_dimension_policy_record(self):
        self.cli("config-set", "workflow.ui_safety_gate", "false")
        evidence = self.reviewed_contract()
        evidence["ui_safety_gate"] = False
        evidence["dimensions"][5] = {"dimension": 6, "verdict": "DISABLED", "evidence": ".planning/config.yaml: workflow.ui_safety_gate is explicitly false"}
        self.approve(evidence)
        self.assertFalse(self.cli("check.ui-plan-gate", "1")["blocked"])
