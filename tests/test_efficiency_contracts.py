"""Guard the shared evidence and verification workflow contracts."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EfficiencyContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_scout_dispatch_routes_required_work_and_keeps_cited_evidence(self):
        dispatch = self.read(".ai/references/scout-dispatch.md")
        self.assertIn("one discovery scout", dispatch)
        self.assertIn("named unresolved claim", dispatch)
        self.assertIn("task_class:", dispatch)
        self.assertIn("field_results:", dispatch)
        self.assertIn("Do not dispatch a second scout when one result answers", " ".join(dispatch.split()))
        self.assertNotIn("at least two specialized", dispatch)
        self.assertIn("citation: <path:line", dispatch)
        self.assertIn("revision: <inspected revision>", dispatch)

    def test_broad_scout_boundary_preserves_owner_reads_and_evidence_reuse(self):
        contract = " ".join(self.read(".ai/references/scout-dispatch.md").split())
        for instruction in ("configured cheap `scout`", "every agent, including the coordinator",
                            "Dispatch `scout` before unknown-location discovery",
                            "requested repository inventories", "fact extraction", "classification",
                            "structured summaries", "transformation proposals",
                            "even when the input paths are known", "search examples in every role method",
                            "Batch compatible fields", "technical/design decisions and authoring",
                            "Directly inspect already-known source", "for every read",
                            "known runtime and Git metadata", "coordinator cannot dispatch either",
                            "Block only dependent work", "Preserve owned progress",
                            "Do not silently perform required scout work yourself"):
            self.assertIn(instruction, contract)

    def test_scout_operations_use_short_direct_items_and_structured_examples(self):
        contract = self.read(".ai/references/scout-dispatch.md")
        in_code = False
        for number, line in enumerate(contract.splitlines(), 1):
            if line.startswith("```"):
                in_code = not in_code
            elif not in_code and line.strip():
                self.assertTrue(line.startswith(("#", "- ")), f"line {number}: {line}")
                self.assertNotIn(";", line, f"compound instruction at line {number}")
                self.assertNotRegex(line, r"\b(?:and|or) (?:inspect|proceed|decide|record|resume|report|respect)\b")
        self.assertFalse(in_code)
        self.assertIn("python .ai/runtime/phase.py query resolve-agent scout --host codex", contract)
        self.assertIn("python .ai/runtime/phase.py query resolve-agent scout --host claude", contract)
        for status in ("complete", "incomplete", "blocked"):
            self.assertIn(status, contract)

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
        scout = self.read(".ai/references/scout-dispatch.md")
        self.assertIn("one bounded follow-up", scout)
        self.assertIn("block only the dependent", scout.lower())
        self.assertIn("question, revision, search scope and supplied", scout)

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
