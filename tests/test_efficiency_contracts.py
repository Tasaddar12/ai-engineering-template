"""Guard the shared evidence and verification workflow contracts."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EfficiencyContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_scout_routes_discovery_and_requested_mechanical_outputs(self):
        contract = " ".join(self.read(".ai/references/scout-dispatch.md").split())
        self.assertIn("MUST dispatch `scout`", contract)
        for task in ("discovery", "file/symbol", "inventories", "extraction",
                     "classification", "transformations", "structured summaries"):
            self.assertIn(task, contract)
        self.assertIn("even at known paths", contract)
        self.assertIn("configured cheap scout model", contract)
        self.assertIn("resolve-agent", contract)
        self.assertIn("model and effort inline", contract)

    def test_scout_request_and_evidence_are_bounded_and_reusable(self):
        contract = " ".join(self.read(".ai/references/scout-dispatch.md").split())
        for context in ("bounded question", "checkout/revision", "dirty content",
                        "search scope", "requested output", "citations",
                        "uncertainty", "missing evidence"):
            self.assertIn(context, contract)
        self.assertIn("question, revision, scope and inputs match", contract)
        self.assertIn("batch compatible requests", contract)
        self.assertIn("Join results before using them", contract)
        self.assertIn("verify consequential citations", contract)
        self.assertIn("uncovered or stale evidence", contract)
        self.assertIn("Do not repeat covered searches", contract)
        self.assertIn("for every read", contract)

    def test_scout_keeps_owner_decisions_and_coordinator_fallback(self):
        contract = " ".join(self.read(".ai/references/scout-dispatch.md").split())
        self.assertIn("owning agent keeps reasoning, design, authoring and correctness", contract)
        self.assertIn("directly inspect already-known source", contract)
        self.assertIn("read-only leaves", contract)
        self.assertIn("never edit, run tests or project code", contract)
        self.assertIn("decide acceptance or spawn children", contract)
        self.assertIn("nested spawning is unavailable", contract)
        self.assertIn("bounded request and resume point", contract)
        self.assertIn("coordinator for dispatch", contract)
        self.assertIn("block only dependent work", contract)
        self.assertIn("do not silently perform required scout work yourself", contract)

    def test_role_adapters_use_shared_scout_route_without_forcing_fanout(self):
        for path in (ROOT / ".ai/agents").glob("*.md"):
            if path.stem in {"README", "scout"}:
                continue
            body = path.read_text(encoding="utf-8")
            adapter = body.split("</local_workflow>", 1)[0]
            self.assertIn("scout dispatch", adapter, path.name)
        rules = self.read(".ai/RULES.md")
        self.assertIn("scout usage contract", rules)

    def test_review_triggers_and_parallel_readonly_work_are_explicit(self):
        readme = self.read(".ai/agents/README.md")
        verifier = self.read(".ai/workflows/verify-work.md")
        self.assertIn("fresh code-reviewer for every source-changing phase", readme)
        self.assertIn("when documentation changed", verifier)
        self.assertIn("when acceptance covers a", verifier)
        for path in (".ai/workflows/execute-phase.md", ".ai/workflows/plan-phase.md",
                     ".ai/workflows/quick.md"):
            workflow = self.read(path)
            self.assertIn("Independent read-only", workflow, path)
            self.assertIn("same frozen revision", workflow, path)

    def test_execute_keeps_dependency_waves_and_uses_receipts(self):
        workflow = self.read(".ai/workflows/execute-phase.md")
        adaptation = self.read(".ai/references/agent-adaptation.md")
        self.assertIn("phase-plan-index", workflow)
        self.assertIn("Plans that declare overlapping `files_modified`", workflow)
        self.assertIn("successful receipts", workflow)
        self.assertIn("dependency and file-overlap waves", adaptation)
        self.assertNotIn("displayed waves do not impose a global barrier", adaptation)
        for path in (".ai/agents/phase-checker.md",
                     ".ai/references/methods/planner-chunked.md",
                     ".ai/references/template-adaptation.md",
                     ".ai/templates/phase-prompt.md"):
            self.assertNotIn("not a global barrier", self.read(path))
            self.assertNotIn("no global wave barrier", self.read(path))

    def test_verifier_joins_evidence_before_success_bookkeeping_and_final_report(self):
        workflow = self.read(".ai/workflows/verify-work.md")
        evidence = self.read(".ai/references/verification-evidence.md")
        handoff = self.read(".ai/references/worker-handoff.md")
        workflow = " ".join(workflow.split())
        evidence = " ".join(evidence.split())
        self.assertIn("read-only evidence assignments", workflow)
        self.assertIn("results are pending", workflow)
        self.assertIn('step name="reconcile_evidence"', workflow)
        self.assertIn("commits only `NN-VERIFICATION.md`", workflow)
        self.assertLess(workflow.index('step name="verify_docs"'),
                        workflow.index('step name="reconcile_evidence"'))
        self.assertLess(workflow.index('step name="update_state"'),
                        workflow.index('step name="final_frozen_reconciliation"'))
        self.assertIn("refresh-only", workflow)
        self.assertIn("do not start another `/ship`", workflow)
        self.assertIn("For each commit, run", evidence)
        self.assertIn("does not enforce the currentness rule", evidence)
        self.assertIn("Final-report lifecycle", evidence)
        self.assertIn("the coordinator alone", evidence)
        self.assertIn("report-only commit", handoff)

    def test_verifier_consumes_shared_evidence_and_limits_duplicate_inspection(self):
        verifier = self.read(".ai/agents/verifier.md")
        patterns = self.read(".ai/references/methods/verification-patterns.md")
        verifier = " ".join(verifier.split())
        patterns = " ".join(patterns.split())
        self.assertIn("For each declared connection without applicable cited evidence", verifier)
        self.assertNotIn("For every declared `from`", verifier)
        self.assertIn("do not finalize status until the coordinator resumes you", verifier)
        self.assertIn("do not rerun broad import and usage searches", verifier)
        self.assertIn("valid configured-check receipt", verifier)
        self.assertIn("Shared-receipt exception", verifier)
        self.assertIn("not a mandatory second scan", patterns)
        self.assertIn("every required artifact/link", patterns)

    def test_ship_consumes_receipts_and_shares_currentness_rule(self):
        workflow = self.read(".ai/workflows/ship.md")
        workflow = " ".join(workflow.split())
        self.assertIn("valid successful receipt", workflow)
        self.assertIn("verification evidence", workflow)
        self.assertIn("does not enforce freshness", workflow)
        self.assertLess(workflow.index('step name="prepare_shipping_record"'),
                        workflow.index('step name="final_reconciliation"'))
        self.assertLess(workflow.index('step name="final_reconciliation"'),
                        workflow.index('step name="push_branch"'))
        self.assertIn("Preparing publication for phase", workflow)
        self.assertIn("/verify-work {phase_number}", workflow)
        self.assertIn("do not add a tracked post-push bookkeeping commit", workflow)


if __name__ == "__main__":
    unittest.main()
