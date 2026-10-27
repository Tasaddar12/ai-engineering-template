"""Check navigable local workflow guidance after the planning/template cutover."""
from pathlib import Path
import posixpath
import re
import unittest
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


def guidance_files():
    for name in ("AGENTS.md", "CLAUDE.md", "README.md"):
        if (ROOT / name).is_file():
            yield ROOT / name
    for directory in ("agents", "commands", "engineer", "hooks", "skills", ".planning", "docs"):
        for path in (ROOT / directory).rglob("*.md"):
            relative = path.relative_to(ROOT).as_posix()
            if relative.startswith("engineer/templates/"):
                continue  # Imported source has its own provenance/reference audit.
            yield path


def without_fences(text):
    text = re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", text)
    return re.sub(r"`+[^`\n]*`+", "", text)  # Literal link syntax in inline examples is not navigation.


class WorkflowNavigationTests(unittest.TestCase):
    def test_scout_contract_has_fixed_task_routes_and_complete_structures(self):
        body = (ROOT / "engineer/references/scout-dispatch.md").read_text(encoding="utf-8")
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
                            "A source-changing phase always gets a separate fresh code-reviewer"):
            self.assertIn(instruction, body)
        self.assertIn("Do not perform duplicate searches", " ".join(body.split()))

    def test_thinking_partner_keeps_full_selected_activation_and_nonactivation_method(self):
        text = (ROOT / "engineer/workflows/discuss-phase/modes/default.md").read_text(encoding="utf-8")
        body = text.split("**Thinking partner (conditional):**", 1)[1].split("**Scope creep handling:**", 1)[0]
        duties = {
            "opt in": ("features.thinking_partner", "config.yaml", "default false", "when disabled"),
            "keyword signals": ('"or"', '"versus"', '"vs"', '"tradeoff"', '"trade-off"', '"tradeoffs"',
                                '"on one hand"', '"on the other hand"', '"pros and cons"',
                                '"not sure between"', '"torn between"'),
            "structural signals": ("two or more competing options", '"which is better"',
                                   '"what would you recommend"', "reverses a previous decision"),
            "nonactivation": ("already made a clear choice", "rhetorical or trivial", "tabs or spaces",
                              "simple yes/no", "explicitly asks to move on", "does not override these exclusions"),
            "analysis choice": ("[Yes, analyze]", "[No, decision made]", "three-to-five-bullet",
                                "each approach optimizes", "each sacrifices", "PROJECT.md goals",
                                "recommendation with reasons", "declines, preserve their decision",
                                "Return to the normal discussion loop"),
        }
        def errors(value):
            return [label for label, cues in duties.items() if not all(cue in value for cue in cues)]
        self.assertEqual([], errors(body))
        for label, cues in duties.items():
            for cue in cues:
                with self.subTest(duty=label, cue=cue):
                    # Every selected signal/exclusion must survive; unrelated prose cannot cover its loss.
                    self.assertIn(label, errors(body.replace(cue, "Removed")))

    def test_feature_response_language_rules_are_inline_and_cover_all_user_prose(self):
        for name in ("audit-fix", "audit-uat", "quick-batch", "code-review", "code-review-fix"):
            with self.subTest(workflow=name):
                text = (ROOT / "engineer/workflows" / (name + ".md")).read_text(encoding="utf-8")
                for required in ("config-get response_language --raw", "narration between tool calls",
                                 "status updates", "progress notes", "questions", "reported findings",
                                 "Preserve code, paths", "machine-readable keys", "protocol markers verbatim"):
                    self.assertIn(required, text)
                self.assertNotIn("@engineer/references/response-language-directive.md", text)

    def test_batch_review_and_worker_completion_have_no_legacy_shortcuts(self):
        base = ROOT / "engineer/workflows/quick-batch/steps"
        checker = (base / "plan-checker-loop.md").read_text(encoding="utf-8")
        expected = checker.split("<expected_output>", 1)[1].split("</expected_output>", 1)[0]
        self.assertIn("## PLAN REVIEW", expected)
        self.assertIn("Verdict: approved | needs-revision", expected)
        self.assertNotIn("## VERIFICATION PASSED", expected)
        for condition in ("absent/malformed verdict", "contradictory verdicts", "incomplete assigned coverage",
                          "all-INFO list without canonical approval", "retry cap never waives"):
            self.assertIn(condition, checker)
        dispatch = (base / "worktree-dispatch.md").read_text(encoding="utf-8")
        for duty in ("MUST commit your owned source changes", "required complete SUMMARY.md",
                     'effort="{resolved_executor_effort}"', 'isolation="worktree"', "worktree.record-agent"):
            self.assertIn(duty, dispatch)
        self.assertNotIn("{harnessFlag}", dispatch)
        self.assertNotIn("Do NOT commit docs artifacts", dispatch)
        verification = (base / "verification-wave.md").read_text(encoding="utf-8")
        self.assertLess(verification.index("persist its full content verbatim"),
                        verification.index("query verification.status"))

    def test_next_and_summary_apply_response_language_to_full_prose(self):
        for name in ("next", "milestone-summary"):
            text = (ROOT / "engineer/workflows" / (name + ".md")).read_text(encoding="utf-8")
            policy = text.split("<response_language>", 1)[1].split("</response_language>", 1)[0]
            for surface in ("config-get response_language --raw", "narration between tool calls",
                            "status updates", "progress notes", "findings", "final result",
                            "Preserve literal code", "canonical markers"):
                self.assertIn(surface, policy)

    def test_phase_handoff_producers_and_post_merge_reconciliation_are_wired(self):
        execute = (ROOT / "engineer/workflows/execute-phase.md").read_text(encoding="utf-8")
        ship = (ROOT / "engineer/workflows/ship.md").read_text(encoding="utf-8")
        git = (ROOT / "engineer/references/git-workflow.md").read_text(encoding="utf-8")
        runtime = (ROOT / "engineer/bin/README.md").read_text(encoding="utf-8")
        self.assertIn('step name="review_phase_issues"', execute)
        for boundary in ("normal", "deferral", "blocked/halted", "early termination"):
            self.assertIn(boundary, execute)
        self.assertIn("phase.issue-declare", execute)
        self.assertIn("phase.handoff", execute)
        wave_tracking = execute.split('<step name="track_integrated_slice">', 1)[1].split("</step>", 1)[0]
        self.assertLess(wave_tracking.index("review_phase_issues"), wave_tracking.index("engineer_run query pr.open"))
        self.assertIn("canonical issue URL", wave_tracking)
        self.assertIn("same-execution fixed-work exemption", wave_tracking)
        self.assertNotIn("query todo.complete", execute)
        self.assertNotIn('step name="close_phase_todos"', execute)
        self.assertLess(ship.index("Require provider-confirmed merged state"), ship.index("query phase.reconcile-todos"))
        self.assertIn("reconciliation-only", ship)
        self.assertIn("no repeated issue", execute)
        self.assertNotIn("Publish only when the user authorized it", git)
        for verb in ("phase.issue-declare", "phase.issue-preview", "phase.issue-publish", "phase.issue-update", "phase.handoff", "phase.reconcile-todos"):
            self.assertIn(verb, runtime)
        self.assertIn("--preview-token", runtime)
        self.assertIn("--expect-digest", runtime)
        self.assertIn("warn-only", runtime)

    def test_literal_link_examples_do_not_hide_real_navigation(self):
        body = without_fences("`[example](missing.md)` and [actual](required.md)\n"
                              "```markdown\n[example](also-missing.md)\n```\n")
        self.assertNotIn("missing.md", body)
        self.assertIn("[actual](required.md)", body)

    def test_local_guidance_links_resolve_with_portable_case(self):
        failures = []
        for source in guidance_files():
            text = without_fences(source.read_text(encoding="utf-8-sig"))
            for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
                target = match[1].strip().strip("<>")
                if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue
                file_part = unquote(target.split("#", 1)[0])
                if not file_part:
                    continue
                relative_text = posixpath.normpath(source.parent.relative_to(ROOT).as_posix() + "/" + file_part)
                destination = (ROOT / relative_text).resolve()
                label = f"{source.relative_to(ROOT)} -> {target}"
                if not destination.is_relative_to(ROOT) or not destination.exists():
                    failures.append(label + " (missing or outside repository)")
                    continue
                # resolve() can correct filename casing on Windows. Audit the
                # spelling in the link, not the filesystem's corrected result.
                relative = Path(relative_text)
                cursor = ROOT
                for part in relative.parts:
                    if part not in {child.name for child in cursor.iterdir()}:
                        failures.append(label + " (case does not match tracked path)")
                        break
                    cursor /= part
        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
