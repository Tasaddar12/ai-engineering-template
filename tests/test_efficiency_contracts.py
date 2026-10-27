"""Guard the shared evidence and verification workflow contracts."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EfficiencyContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_scout_dispatch_routes_required_work_and_keeps_cited_evidence(self):
        dispatch = self.read("engineer/references/scout-dispatch.md")
        self.assertIn("one discovery scout", dispatch)
        self.assertIn("named unresolved claim", dispatch)
        self.assertIn("task_class:", dispatch)
        self.assertIn("field_results:", dispatch)
        self.assertIn("do not dispatch a second scout when one result answers", " ".join(dispatch.split()))
        self.assertNotIn("at least two specialized", dispatch)
        self.assertIn("{claim, citation, excerpt}", dispatch)
        self.assertIn("revision: [inspected full SHA]", dispatch)

    def test_required_scout_scope_keeps_owner_reads_and_evidence_reuse(self):
        contract = " ".join(self.read("engineer/references/scout-dispatch.md").split())
        for instruction in ("Use one discovery scout when source location is unknown",
                            "requested inventories", "fact extraction", "classification",
                            "structured summaries", "transformation proposals",
                            "even when input paths are known", "including coordinator work",
                            "Directly inspect already-known source", "runtime and Git metadata",
                            "Reuse matching evidence before dispatching another scout",
                            "Batch compatible fields", "delegate every read",
                            "direct scout dispatch is unsupported", "block only the dependent claim"):
            self.assertIn(instruction, contract)

    def test_role_adapters_use_shared_scout_route_without_forcing_fanout(self):
        for path in (ROOT / "agents").glob("*.md"):
            if path.stem in {"AGENT", "code-fixer", "scout"}:
                continue
            body = path.read_text(encoding="utf-8")
            adapter = body
            self.assertIn("scout dispatch", adapter, path.name)
        rules = self.read("engineer/RULES.md")
        self.assertIn("references/scout-dispatch.md", rules)

    def test_review_triggers_and_parallel_readonly_work_are_explicit(self):
        readme = self.read("agents/AGENT.md")
        verifier = self.read("engineer/workflows/verify-work.md")
        self.assertIn("fresh code-reviewer for every source-changing phase", readme)
        self.assertIn("When plans declare documentation or user-facing/API/CLI behavior changed", verifier)
        self.assertIn("When the phase crosses component, service, runtime or host boundaries", verifier)
        for path in ("engineer/workflows/execute-phase.md", "engineer/workflows/plan-phase.md",
                     "engineer/workflows/quick.md"):
            workflow = self.read(path)
            self.assertIn("read-only", workflow, path)
            self.assertIn("independent", workflow.lower(), path)
            self.assertIn("concurrently", workflow, path)
            self.assertTrue("same frozen revision" in workflow or "one frozen revision" in workflow, path)
        scout = self.read("engineer/references/scout-dispatch.md")
        self.assertIn("one bounded follow-up", scout)
        self.assertIn("block only the dependent", scout)
        self.assertIn("question, revision, search scope and supplied", scout)

    def test_execute_keeps_dependency_waves_and_uses_receipts(self):
        workflow = self.read("engineer/workflows/execute-phase.md")
        adaptation = self.read("engineer/references/agent-adaptation.md")
        self.assertIn("phase-plan-index", workflow)
        self.assertIn("plans with overlapping files_modified, files_deleted or conflicting shared resources into later waves", workflow)
        self.assertIn("passing receipts", workflow)
        self.assertIn("dependency and file-overlap waves", adaptation)
        self.assertNotIn("displayed waves do not impose a global barrier", adaptation)
        for path in ("agents/plan-checker.md",
                     "engineer/references/planner-chunked.md",
                     "engineer/references/template-contract.md",
                     "engineer/templates/phase-prompt.md"):
            self.assertNotIn("not a global barrier", self.read(path))
            self.assertNotIn("no global wave barrier", self.read(path))

    def test_verifier_joins_evidence_before_success_bookkeeping_and_final_report(self):
        workflow = self.read("engineer/workflows/verify-work.md")
        evidence = self.read("engineer/references/verification-evidence.md")
        handoff = self.read("engineer/references/worker-handoff.md")
        workflow = " ".join(workflow.split())
        evidence = " ".join(evidence.split())
        self.assertIn("applicable read-only specialists", workflow)
        self.assertIn("wait for every result before editing source", workflow)
        self.assertIn('step name="reconcile_evidence"', workflow)
        self.assertIn("Commit only the exact canonical VERIFICATION report path", workflow)
        self.assertLess(workflow.index('step name="verify_docs"'),
                        workflow.index('step name="reconcile_evidence"'))
        self.assertLess(workflow.index('step name="update_state"'),
                        workflow.index('step name="final_frozen_reconciliation"'))
        self.assertIn("ship repair/refresh", workflow)
        self.assertIn("Do not recursively invoke ship", workflow)
        self.assertIn("For every commit, run", evidence)
        self.assertIn("does not enforce currentness", evidence)
        self.assertIn("Final-report lifecycle", evidence)
        self.assertIn("the coordinator alone", evidence)
        self.assertIn("report-only commit", handoff)

    def test_verifier_consumes_shared_evidence_and_limits_duplicate_inspection(self):
        verifier = self.read("agents/verifier.md")
        patterns = self.read("engineer/references/verification-patterns.md")
        verifier = " ".join(verifier.split())
        patterns = " ".join(patterns.split())
        self.assertIn("For each declared connection without applicable cited evidence", verifier)
        self.assertNotIn("For every declared `from`", verifier)
        self.assertIn("Do not finalize status until the coordinator resumes you", verifier)
        self.assertIn("do not rerun broad import and usage searches", verifier)
        self.assertIn("matching configured-check receipts", verifier)
        self.assertIn("A valid shared receipt satisfies its covered behavior without duplicate execution", verifier)
        self.assertIn("not a mandatory second scan", patterns)
        self.assertIn("every required artifact/link", patterns)

    def test_ship_consumes_receipts_and_shares_currentness_rule(self):
        workflow = self.read("engineer/workflows/ship.md")
        workflow = " ".join(workflow.split())
        self.assertIn("valid current passing receipts", workflow)
        self.assertIn("verification-evidence.md", workflow)
        self.assertIn("verification.current", workflow)
        self.assertIn("does not enforce currentness", self.read("engineer/references/verification-evidence.md"))
        self.assertLess(workflow.index('step name="prepare_shipping_record"'),
                        workflow.index('step name="final_reconciliation"'))
        self.assertLess(workflow.index('step name="final_reconciliation"'),
                        workflow.index('step name="push_branch"'))
        self.assertIn("Preparing publication", workflow)
        self.assertIn("verify-work in ship-repair/return-to-caller mode", workflow)
        self.assertIn("Do not create tracked post-push bookkeeping", workflow)


if __name__ == "__main__":
    unittest.main()
