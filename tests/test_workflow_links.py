"""Check navigable local workflow guidance after the planning/template cutover."""
from pathlib import Path
import re
import unittest
from workflow_navigation import audit, without_fences


ROOT = Path(__file__).resolve().parents[1]


def guidance_files():
    for name in ("AGENTS.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md"):
        if (ROOT / name).is_file():
            yield ROOT / name
    for directory in (".ai", ".codex", ".claude", ".agents", ".planning", "docs"):
        for path in (ROOT / directory).rglob("*.md"):
            yield path


class WorkflowNavigationTests(unittest.TestCase):
    def test_scout_contract_has_fixed_task_routes_and_complete_structures(self):
        body = (ROOT / ".ai/references/scout-dispatch.md").read_text(encoding="utf-8")
        procedure = body.split("## Dispatch procedure", 1)[1].split("## Direct nested", 1)[0]
        self.assertEqual([str(n) for n in range(1, 7)], re.findall(r"^(\d+)\. ", procedure, re.M))
        for field in ("scout_assignment:", "scout_result:", "scout_request:", "search_scope:",
                      "revision:", "task_class:", "requested_fields:", "field_results:",
                      "uncertainty:", "unresolved_questions:", "missing_test_cases:",
                      "parent_assignment_id:", "resume_with:"):
            self.assertIn(field, body)
        for task_class in ("FACT_EXTRACTION", "REVIEW_INVENTORY", "DOC_CLAIM_COMPARE",
                           "INTEGRATION_MAP", "TEST_RESULT_SUMMARY", "FAILURE_FACTS",
                           "DOC_TRANSFORM_PROPOSAL", "CODE_TRANSFORM_PROPOSAL"):
            self.assertIn(task_class, body)
        for instruction in ("one discovery scout", "same frozen revision", "concurrently",
                            "not runtime enforcement", "bounded follow-up",
                            "verification.run-checks",
                            "If source changes, assign a separate fresh code-reviewer."):
            self.assertIn(instruction, body)
        self.assertIn("Do not perform duplicate searches", " ".join(body.split()))

    def test_phase_handoff_producers_and_post_merge_reconciliation_are_wired(self):
        execute = (ROOT / ".ai/workflows/execute-phase.md").read_text(encoding="utf-8")
        ship = (ROOT / ".ai/workflows/ship.md").read_text(encoding="utf-8")
        git = (ROOT / ".ai/references/git-workflow.md").read_text(encoding="utf-8")
        runtime = (ROOT / ".ai/runtime/README.md").read_text(encoding="utf-8")
        self.assertIn('step name="review_phase_issues"', execute)
        for boundary in ("normal", "deferral", "blocked/halted", "early termination"):
            self.assertIn(boundary, execute)
        self.assertIn("phase.issue-declare", execute)
        self.assertIn("phase.handoff", execute)
        wave_tracking = execute.split('<step name="track_integrated_slice">', 1)[1].split("</step>", 1)[0]
        self.assertLess(wave_tracking.index("review_phase_issues"), wave_tracking.index("phase_run query pr.open"))
        self.assertIn("canonical issue URL", wave_tracking)
        self.assertIn("same-execution fixed-work exemption", wave_tracking)
        self.assertNotIn("query todo.complete", execute)
        self.assertNotIn('step name="close_phase_todos"', execute)
        self.assertLess(ship.index("Require `merged: true`"), ship.index("query phase.reconcile-todos"))
        self.assertIn("reconciliation-only", ship)
        self.assertIn("no repeated issue", execute)
        self.assertNotIn("Publish only when the user authorized it", git)
        for verb in ("phase.issue-declare", "phase.issue-preview", "phase.issue-publish", "phase.issue-update", "phase.handoff", "phase.reconcile-todos"):
            self.assertIn(verb, runtime)
        self.assertIn("Direct", runtime)
        self.assertIn("warn-only", runtime)

    def test_literal_link_examples_do_not_hide_real_navigation(self):
        body = without_fences("`[example](missing.md)` and [actual](required.md)\n"
                              "```markdown\n[example](also-missing.md)\n```\n")
        self.assertNotIn("missing.md", body)
        self.assertIn("[actual](required.md)", body)

    def test_local_guidance_links_resolve_with_portable_case(self):
        failures = []
        for source in guidance_files():
            failures.extend(f"{source.relative_to(ROOT)} -> {failure}"
                            for failure in audit(source, ROOT))
        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
