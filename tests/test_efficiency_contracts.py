"""Guard the shared evidence and verification workflow contracts."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EfficiencyContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_scout_dispatch_routes_triggered_work_and_keeps_cited_evidence(self):
        dispatch = self.read(".ai/references/scout-dispatch.md")
        self.assertIn("one discovery scout", dispatch)
        self.assertIn("named unresolved claim", dispatch)
        self.assertIn("task_class:", dispatch)
        self.assertIn("field_results:", dispatch)
        self.assertIn("Do not dispatch a second scout when one result answers", " ".join(dispatch.split()))
        self.assertNotIn("at least two specialized", dispatch)
        self.assertIn("citation: <path:line", dispatch)
        self.assertIn("revision: <inspected revision>", dispatch)

    def test_planning_discovery_requires_scout_but_preserves_named_reads_and_batching(self):
        dispatch = " ".join(self.read(".ai/references/scout-dispatch.md").split())
        for boundary in ("files, symbols, history or matching skills",
                         "every repository inventory", "MUST go to the configured exact `scout` role",
                         "before the owner uses search tools", "SUMMARY metadata",
                         "entry points/callers/config/tests"):
            self.assertIn(boundary, dispatch)
        self.assertIn("A decision owner may read already specified files", dispatch)
        self.assertIn("Known runtime metadata queries", dispatch)
        self.assertIn("Do not add a scout for a trivial named-file read", dispatch)
        self.assertIn("Batch compatible field requests for the same bounded scope", dispatch)
        self.assertIn("same question, revision, search scope and supplied inputs", dispatch)
        self.assertIn("Researcher and phase-preparer retain technical/design decisions and authoring", dispatch)

    def test_planning_evidence_gate_precedes_research_and_preparer(self):
        workflow = self.read(".ai/workflows/plan-phase.md")
        self.assertIn("orchestrator, scout, researcher", workflow)
        self.assertIn("@~/.ai/references/scout-dispatch.md", workflow)
        self.assertIn("- scout -", workflow)
        gate_start = workflow.index('<step name="planning_evidence_gate">')
        self.assertLess(gate_start, workflow.index('<step name="handle_research">'))
        self.assertLess(gate_start, workflow.index('<step name="spawn_preparer">'))
        gate = " ".join(workflow[gate_start:workflow.index("</step>", gate_start)].split())
        for instruction in ("dispatch configured exact `scout` BEFORE owner search tools",
                            "resolve-agent scout --host codex", "`--host claude`",
                            "same question, revision, scope and inputs", "Batch compatible fields",
                            "Do not launch a scout solely for a trivial read",
                            "`--skip-research`", "do not skip this gate"):
            self.assertIn(instruction, gate)

    def test_every_planning_worker_handles_requests_before_output_or_verdict_checks(self):
        workflow = self.read(".ai/workflows/plan-phase.md")
        steps = dict(re.findall(r'<step name="([^"]+)"[^>]*>(.*?)</step>', workflow, re.S))
        research = steps["handle_research"]
        handling = research[research.index("**Handle the return.**"):]
        self.assertLess(handling.index("scout_return_protocol"), handling.index("exists;"))
        preparer = steps["handle_preparer_return"]
        self.assertLess(preparer.index("scout_return_protocol"), preparer.index("phase-plan-index"))
        for role, step in (("researcher", "handle_research"), ("phase-preparer", "spawn_preparer"),
                           ("phase-checker", "spawn_checker"), ("codebase-mapper", "refresh_codebase_maps")):
            with self.subTest(role=role):
                self.assertIn("<scout_evidence_contract>", steps[step])
                self.assertIn("packet IDs/paths and bounded cited fields", steps[step])
                self.assertIn("scout_request", steps[step])
        self.assertIn("BEFORE interpreting", steps["spawn_checker"])
        self.assertIn("protocol again on the continuation return", steps["spawn_checker"])
        self.assertIn("BEFORE map", steps["refresh_codebase_maps"])
        self.assertIn("every revision and", steps["revision_loop"])
        self.assertIn("its continuations before checking files", steps["revision_loop"])

    def test_scout_fallback_releases_capacity_and_resumes_without_partial_counter_reuse(self):
        dispatch = " ".join(self.read(".ai/references/scout-dispatch.md").split())
        workflow = self.read(".ai/workflows/plan-phase.md")
        protocol = " ".join(workflow.split("<scout_return_protocol>", 1)[1]
                            .split("</scout_return_protocol>", 1)[0].split())
        for required in ("assignments: [<complete scout_assignment objects>]", "saved_progress:",
                         "resume_with:", "count queued/open workers", "stop scheduling additional workers",
                         "return and release its occupied slot before", "actual host continuation",
                         "fresh assignment with saved progress", "live duplicate writer",
                         "SCOUT UNAVAILABLE", "missing_fields:", "dependent_steps:"):
            self.assertIn(required, dispatch)
        for required in ("BEFORE required output-file existence", "EVERY researcher, phase-preparer",
                         "codebase-mapper and phase-checker return", "Count queued/open workers",
                         "releases its occupied slot before", "join/retire", "actual host continuation",
                         "fresh assignment with saved progress", "live duplicate writer",
                         "does not consume context PARTIAL, research-incomplete or plan-revision counters",
                         "SCOUT UNAVAILABLE", "missing fields, dependent steps and saved progress",
                         "required missing repository evidence into an `[ASSUMED]` precondition"):
            self.assertIn(required, protocol)
        self.assertIn("no research or PLAN output file is required", dispatch)
        self.assertIn("Do not wait inside a worker while holding capacity", dispatch)
        self.assertIn("Do not invent lifecycle tools or runtime commands", dispatch)

    def test_planning_dispatch_binds_current_identity_and_reconciles_owned_progress(self):
        workflow = self.read(".ai/workflows/plan-phase.md")
        procedure = " ".join(workflow.split("<dispatch_identity_and_currentness>", 1)[1]
                             .split("</dispatch_identity_and_currentness>", 1)[0].split())
        for required in ("BEFORE EVERY evidence or worker dispatch", "git rev-parse --show-toplevel",
                         "git rev-parse HEAD", "git status --porcelain=v1", "git hash-object --no-filters",
                         "unique logical worker assignment ID and its exact role",
                         "Retain that logical ID across its continuations and scout resumes",
                         "distinct dispatch identity for each call", "original ownership, starting snapshot",
                         "Bind `{worker assignment id}`, `{checkout}` and `{revision}`",
                         "Never send unresolved placeholders", "relevant dirty input content identity",
                         "Never relabel stale packets as current", "not blanket discovery",
                         "at EVERY boundary", "Freeze relevant inputs through each scout join",
                         "after researcher/preparer/mapper commits", "BEFORE resume, checker or any other dispatch",
                         "retained original parent assignment", "permits verified owned commits"):
            self.assertIn(required, procedure)
        steps = dict(re.findall(r'<step name="([^"]+)"[^>]*>(.*?)</step>', workflow, re.S))
        for role, step in (("researcher", "handle_research"), ("phase-preparer", "spawn_preparer"),
                           ("phase-checker", "spawn_checker"), ("codebase-mapper", "refresh_codebase_maps")):
            body = steps[step]
            with self.subTest(role=role):
                self.assertLess(body.index("dispatch_identity_and_currentness"), body.index("Agent("))
                contract = body.split("<scout_evidence_contract>", 1)[1].split("</scout_evidence_contract>", 1)[0]
                self.assertIn("exact role: " + role, contract)
                self.assertIn("lineage: {dispatch lineage}", contract)
                self.assertIn("captured inputs: {input snapshot}", contract)
                self.assertIn("current question/revision/scope/input tuple", contract)
        self.assertIn("before EACH evidence dispatch", steps["planning_evidence_gate"])
        research_continuation = steps["handle_research"].split("**Continuing partial research.**", 1)[1]
        self.assertIn("dispatch_identity_and_currentness", research_continuation)
        preparer_continuation = steps["handle_preparer_return"].split("If the preparer returned", 1)[1]
        self.assertIn("dispatch_identity_and_currentness", preparer_continuation)
        self.assertIn("before EVERY revision/continuation call", steps["revision_loop"])
        protocol = " ".join(workflow.split("<scout_return_protocol>", 1)[1]
                            .split("</scout_return_protocol>", 1)[0].split())
        self.assertIn("refresh the input/evidence tuple BEFORE resuming", protocol)
        dispatch = " ".join(self.read(".ai/references/scout-dispatch.md").split())
        for required in ("revision: <actual observed HEAD commit SHA>", "stable content identifiers",
                         "inputs: [<inspected input identifiers matching the retained assignment>]",
                         "recheck HEAD and relevant content identifiers", "parent_role:", "dispatch_lineage:",
                         "actual observed HEAD after any owned committed progress",
                         "Permit verified owned committed progress rather than requiring the stale initial HEAD",
                         "evidence at its reported snapshot", "BEFORE resume", "never relabel stale evidence"):
            self.assertIn(required, dispatch)

    def test_role_adapters_use_shared_scout_route_without_forcing_fanout(self):
        for path in (ROOT / ".ai/agents").glob("*.md"):
            if path.stem in {"README", "scout"}:
                continue
            body = path.read_text(encoding="utf-8")
            adapter = body.split("</local_workflow>", 1)[0]
            self.assertIn("scout dispatch", adapter, path.name)
        rules = self.read(".ai/RULES.md")
        self.assertIn("separately named questions", rules)

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
        self.assertIn("block only the dependent", scout)
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
