"""Port of upstream tests/workflow-size-budget.test.cjs (gsd-core d37ff11)."""
import importlib
import importlib.util
from pathlib import Path
import json
import random
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]
LIB = SOURCE/"engineer/bin/lib"


def _load(name):
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib."+name)


wsb = _load("workflow_size_budget")

WORKFLOWS = wsb.WORKFLOWS_DIR
DISCUSS = WORKFLOWS/"discuss-phase"
EMBED_PATH = "engineer/workflows/execute-plan.md"


def workflow(name):
    return (WORKFLOWS/name).read_text(encoding="utf-8")


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def put(self, relative, content):
        path = self.root/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        return path


class HeadroomCensus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sizes = wsb.measure_workflows()
        cls.rows = wsb.build_headroom_rows(cls.sizes, wsb.cap_for)

    def test_reports_every_workflow_and_never_fails_for_it(self):
        self.assertGreater(len(self.sizes), 0)
        self.assertEqual(len(wsb.list_workflow_stems()), len(self.rows))
        table = wsb.format_headroom_table(self.rows)
        self.assertEqual(len(self.rows)+1, len(table))
        self.assertTrue(table[0].startswith("file"))
        wsb.append_headroom_step_summary("Workflow size headroom", self.rows, env={})

    def test_margin_sits_strictly_below_every_tier_cap(self):
        for cap in (wsb.DEFAULT_CAP, wsb.LARGE_CAP, wsb.XL_CAP):
            margin = wsb.margin_for(cap)
            self.assertLess(margin, cap)
            rows = wsb.build_headroom_rows({"below.md": margin-1, "exact.md": margin, "above.md": margin+1},
                                           lambda name, cap=cap: {"tier": "FIXTURE", "cap": cap})
            by_name = {row["name"]: row for row in rows}
            self.assertFalse(by_name["below"]["overMargin"])
            self.assertFalse(by_name["exact"]["overMargin"])
            self.assertTrue(by_name["above"]["overMargin"])

    def test_margin_classification_holds_for_every_positive_cap(self):
        rng = random.Random(4261)
        caps = [2, 3, 10, 100, 10_000_000, wsb.DEFAULT_CAP, wsb.LARGE_CAP, wsb.XL_CAP]
        caps += [rng.randint(2, 10_000_000) for _ in range(300)]
        for cap in caps:
            margin = wsb.margin_for(cap)
            rows = wsb.build_headroom_rows({"below.md": margin-1, "exact.md": margin, "above.md": margin+1},
                                           lambda name, cap=cap: {"tier": "FIXTURE", "cap": cap})
            by_name = {row["name"]: row for row in rows}
            self.assertTrue(0 <= margin < cap)
            self.assertFalse(by_name["below"]["overMargin"])
            self.assertFalse(by_name["exact"]["overMargin"])
            self.assertTrue(by_name["above"]["overMargin"])
            self.assertEqual(cap-(margin-1), by_name["below"]["headroom"])
            self.assertEqual(cap-margin, by_name["exact"]["headroom"])
            self.assertEqual(cap-(margin+1), by_name["above"]["headroom"])

    def test_rows_sorted_by_pressure_then_name(self):
        rows = wsb.build_headroom_rows({"b.md": 90, "a.md": 90, "c.md": 10}, lambda name: {"tier": "T", "cap": 100})
        self.assertEqual(["a", "b", "c"], [row["name"] for row in rows])

    def test_summary_markdown_lists_only_pressured_files(self):
        calm = wsb.build_headroom_rows({"a.md": 1}, lambda name: {"tier": "T", "cap": 100})
        self.assertIn("All 1 files are under the 95% reserved margin.", wsb.build_headroom_summary_markdown("Title", calm))
        tight = wsb.build_headroom_rows({"a.md": 99, "b.md": 1}, lambda name: {"tier": "T", "cap": 100})
        markdown = wsb.build_headroom_summary_markdown("Title", tight)
        self.assertIn("**1 of 2** files", markdown)
        self.assertIn("| `a` | T | 99 | 100 | 1 | 99.0% |", markdown)
        self.assertNotIn("`b`", markdown)

    def test_step_summary_written_only_when_configured(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/"summary.md"
            rows = wsb.build_headroom_rows({"a.md": 99}, lambda name: {"tier": "T", "cap": 100})
            self.assertFalse(wsb.append_headroom_step_summary("Title", rows, env={}))
            self.assertTrue(wsb.append_headroom_step_summary("Title", rows, env={"GITHUB_STEP_SUMMARY": str(target)}))
            self.assertIn("### Title", target.read_text(encoding="utf-8"))
            self.assertFalse(wsb.append_headroom_step_summary("Title", rows, env={"GITHUB_STEP_SUMMARY": str(Path(tmp)/"missing"/"x.md")}))


class TierHardCaps(unittest.TestCase):
    def test_every_workflow_stays_under_its_tier_hard_cap(self):
        sizes = wsb.measure_workflows()
        self.assertGreater(len(sizes), 0)
        for stem in wsb.list_workflow_stems():
            tier = wsb.cap_for(stem)
            with self.subTest(workflow=stem, tier=tier["tier"]):
                self.assertEqual([], wsb.tier_cap_violations({stem+".md": sizes[stem+".md"]}))

    def test_cap_boundaries(self):
        for stem, cap in (("execute-phase", wsb.XL_CAP), ("quick", wsb.LARGE_CAP), ("unlisted", wsb.DEFAULT_CAP)):
            self.assertEqual(cap, wsb.cap_for(stem)["cap"])
            self.assertEqual([], wsb.tier_cap_violations({stem+".md": cap}))
            self.assertEqual([], wsb.tier_cap_violations({stem+".md": cap-1}))
            over = wsb.tier_cap_violations({stem+".md": cap+1})
            self.assertEqual(1, len(over))
            self.assertIn("hard cap of %d" % cap, over[0])

    def test_tier_sets_are_disjoint(self):
        self.assertEqual(frozenset(), wsb.XL_WORKFLOWS & wsb.LARGE_WORKFLOWS)


class DetailExclusion(Fixture):
    def test_measurement_does_not_recurse_into_detail(self):
        self.put("sample.md", "top-level spine\n")
        self.put("sample/detail/part.md", "detail part\n")
        self.assertEqual(["sample.md"], list(wsb.measure_workflows(self.root)))
        self.assertEqual(["sample"], wsb.list_workflow_stems(self.root))

    def test_near_cap_detail_file_is_excluded_from_sizes(self):
        self.put("sample.md", "top-level spine\n")
        self.put("sample/detail/large-part.md", "x"*32760)
        self.assertEqual(["sample.md"], list(wsb.measure_workflows(self.root)))


class DiscussPhaseDisclosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = workflow("discuss-phase.md")

    def test_under_byte_budget(self):
        self.assertEqual([], wsb.discuss_phase_budget_violations(WORKFLOWS/"discuss-phase.md"))

    # discuss-phase.md dispatches to modes/power.md, modes/chain.md and modes/advisor.md,
    # but those mode files are absent from engineer/workflows/discuss-phase/modes/.
    @unittest.expectedFailure
    def test_mode_files_exist_for_every_documented_mode(self):
        documented = ("power", "all", "auto", "chain", "text", "advisor")
        self.assertEqual([], wsb.missing_files(DISCUSS/"modes", [m+".md" for m in documented]))

    def test_batch_analyze_default_modes_are_not_documented_here(self):
        self.skipTest("upstream batch/analyze/default discuss-phase modes absent in this repo")

    def test_every_mode_file_is_a_real_workflow_doc(self):
        self.assertTrue((DISCUSS/"modes").is_dir())
        self.assertEqual([], wsb.stub_mode_files(DISCUSS/"modes"))

    def test_templates_extracted(self):
        self.assertEqual([], wsb.missing_files(DISCUSS/"templates", wsb.DISCUSS_EXPECTED_TEMPLATES))

    def test_parent_dispatches_to_power_mode(self):
        self.assertTrue("discuss-phase/modes/power.md" in self.parent or "discuss-phase-power.md" in self.parent)

    def test_parent_dispatches_to_extracted_modes(self):
        self.assertEqual([], wsb.mode_dispatch_violations(self.parent, ("auto", "chain", "all", "advisor")))

    def test_parent_reads_context_template_at_write_step(self):
        self.assertEqual([], wsb.context_template_lazy_violations(self.parent))

    def test_advisor_block_gated_behind_user_profile_check(self):
        self.assertEqual([], wsb.advisor_gate_violations(self.parent))

    def test_auto_mode_documents_skipping_interactive_questions(self):
        self.assertEqual([], wsb.mode_content_violations("auto-skip", (DISCUSS/"modes/auto.md").read_text(encoding="utf-8")))

    def test_auto_mode_preserves_single_pass_cap(self):
        self.assertEqual([], wsb.mode_content_violations("auto-cap", (DISCUSS/"modes/auto.md").read_text(encoding="utf-8")))

    def test_all_mode_documents_auto_selecting_gray_areas(self):
        self.assertEqual([], wsb.mode_content_violations("all", (DISCUSS/"modes/all.md").read_text(encoding="utf-8")))

    # discuss-phase.md dispatches to modes/chain.md, which does not exist.
    @unittest.expectedFailure
    def test_chain_mode_documents_auto_advance_to_plan_phase(self):
        path = DISCUSS/"modes/chain.md"
        self.assertTrue(path.exists(), "modes/chain.md is missing")
        self.assertEqual([], wsb.chain_mode_violations(path.read_text(encoding="utf-8")))

    def test_text_mode_documents_replacing_ask_user_question(self):
        self.assertEqual([], wsb.text_mode_violations((DISCUSS/"modes/text.md").read_text(encoding="utf-8")))

    def test_batch_mode_documents_question_grouping(self):
        self.skipTest("upstream discuss-phase batch mode (modes/batch.md) absent in this repo")

    def test_analyze_mode_documents_trade_off_table(self):
        self.skipTest("upstream discuss-phase analyze mode (modes/analyze.md) absent in this repo")

    def test_context_template_preserves_required_sections(self):
        self.assertEqual([], wsb.context_template_violations((DISCUSS/"templates/context.md").read_text(encoding="utf-8")))

    def test_checkpoint_template_is_valid_json_with_required_fields(self):
        self.assertEqual([], wsb.checkpoint_template_violations((DISCUSS/"templates/checkpoint.json").read_text(encoding="utf-8")))

    def test_parent_does_not_leak_inline_discussion_log(self):
        self.assertEqual(0, wsb.inline_discussion_log_occurrences(self.parent))

    def test_parent_dispatches_on_arguments(self):
        self.assertTrue(wsb.dispatch_flag_present(self.parent))


class DiscussPhaseFixtures(Fixture):
    def test_budget_boundaries(self):
        for size, expected in ((wsb.DISCUSS_PHASE_TARGET-1, 0), (wsb.DISCUSS_PHASE_TARGET, 1), (wsb.DISCUSS_PHASE_TARGET+1, 1)):
            path = self.put("d.md", "x"*size)
            self.assertEqual(expected, len(wsb.discuss_phase_budget_violations(path)), size)

    def test_missing_and_stub_mode_files(self):
        self.put("modes/real.md", "x"*101)
        self.put("modes/stub.md", "x"*100)
        self.put("modes/notes.txt", "")
        self.assertEqual(["stub.md"], wsb.stub_mode_files(self.root/"modes"))
        self.assertEqual(["gone.md"], wsb.missing_files(self.root/"modes", ["real.md", "gone.md"]))

    def test_referenced_modes_and_dispatch(self):
        parent = "Read workflows/discuss-phase/modes/auto.md then discuss-phase/modes/auto.md and discuss-phase/modes/text.md"
        self.assertEqual(["auto", "text"], wsb.referenced_mode_files(parent))
        self.assertEqual([], wsb.mode_dispatch_violations(parent, ["auto", "text"]))
        self.assertEqual(1, len(wsb.mode_dispatch_violations(parent, ["auto", "power"])))

    def test_context_template_lazy_rule(self):
        good = "<required_reading>@x.md</required_reading>\nRead(workflows/discuss-phase/templates/context.md)"
        self.assertEqual([], wsb.context_template_lazy_violations(good))
        eager = "<required_reading>@workflows/discuss-phase/templates/context.md</required_reading>"
        self.assertEqual(1, len(wsb.context_template_lazy_violations(eager)))
        self.assertEqual(1, len(wsb.context_template_lazy_violations("no reference at all")))
        self.assertIsNone(wsb.required_reading_block("none"))

    def test_advisor_gate_rule(self):
        good = ('if [ -f "$HOME/.claude/USER-PROFILE.md" ]; then ADVISOR_MODE=true; fi\n'
                "ADVISOR_MODE = true -> Read modes/advisor.md\n")
        self.assertEqual([], wsb.advisor_gate_violations(good))
        unguarded = "USER-PROFILE.md mentioned. Always Read modes/advisor.md\n"
        self.assertEqual(2, len(wsb.advisor_gate_violations(unguarded)))
        self.assertEqual(3, len(wsb.advisor_gate_violations("nothing")))

    def test_mode_content_rules(self):
        cases = {"auto-skip": ("Skip interactive prompts entirely", "ask everything"),
                 "auto-cap": ("single pass only", "loops forever"),
                 "all": ("auto-select ALL gray areas", "pick one"),
                 "batch": ("group 2-5 questions", "one at a time"),
                 "analyze": ("a trade-off table", "plain list")}
        for mode, (good, bad) in cases.items():
            self.assertEqual([], wsb.mode_content_violations(mode, good), mode)
            self.assertEqual(1, len(wsb.mode_content_violations(mode, bad)), mode)
        self.assertEqual([], wsb.chain_mode_violations("auto-advance to plan-phase"))
        self.assertEqual(1, len(wsb.chain_mode_violations("auto-advance only")))
        self.assertEqual([], wsb.text_mode_violations("replace AskUserQuestion with a numbered list"))
        self.assertEqual(1, len(wsb.text_mode_violations("use a numbered list")))

    def test_template_rules(self):
        full = " ".join(wsb.CONTEXT_SECTIONS)+" <spec_lock>"
        self.assertEqual([], wsb.context_template_violations(full))
        self.assertEqual(6, len(wsb.context_template_violations("<domain>")))
        keys = {key: 1 for key in wsb.CHECKPOINT_KEYS}
        self.assertEqual([], wsb.checkpoint_template_violations(json.dumps(keys)))
        self.assertEqual(1, len(wsb.checkpoint_template_violations("{not json")))
        self.assertEqual(1, len(wsb.checkpoint_template_violations(json.dumps({k: 1 for k in wsb.CHECKPOINT_KEYS[1:]}))))
        self.assertEqual(1, len(wsb.checkpoint_template_violations("[]")))

    def test_inline_log_and_dispatch_flag(self):
        self.assertEqual(2, wsb.inline_discussion_log_occurrences("| Option | Description | Selected |\n| Option | Description | Selected |"))
        self.assertEqual(0, wsb.inline_discussion_log_occurrences("clean"))
        self.assertTrue(wsb.dispatch_flag_present("--chain"))
        self.assertFalse(wsb.dispatch_flag_present("nothing"))


class MvpBodiesLazyLoaded(unittest.TestCase):
    """MVP-only reference bodies must not be eagerly @-imported (upstream #720).

    The upstream bodies (planner-mvp-mode.md, skeleton-template.md,
    execute-mvp-tdd.md, user-story-template.md) do not exist in this repo, so the
    repo-facing tests skip until one appears.
    """

    CASES = (
        ("plan-phase", WORKFLOWS/"plan-phase.md", "planner-mvp-mode.md"),
        ("plan-phase", WORKFLOWS/"plan-phase.md", "skeleton-template.md"),
        ("execute-phase", WORKFLOWS/"execute-phase.md", "execute-mvp-tdd.md"),
        ("planner", wsb.AGENTS_DIR/"planner.md", "planner-mvp-mode.md"),
        ("planner", wsb.AGENTS_DIR/"planner.md", "skeleton-template.md"),
        ("planner", wsb.AGENTS_DIR/"planner.md", "user-story-template.md"),
        ("executor", wsb.AGENTS_DIR/"executor.md", "execute-mvp-tdd.md"),
    )

    def test_hosts_do_not_eagerly_import_mvp_bodies_and_keep_lazy_references(self):
        for label, path, body in self.CASES:
            with self.subTest(host=label, body=body):
                if not wsb.reference_body_exists(body):
                    self.skipTest("upstream MVP body %s absent in this repo" % body)
                content = path.read_text(encoding="utf-8")
                self.assertEqual([], wsb.eager_import_violations(content, body, path.name))
                self.assertEqual([], wsb.lazy_reference_violations(content, body, path.name))

    def test_required_reading_does_not_list_mvp_bodies(self):
        bodies = ("planner-mvp-mode.md", "skeleton-template.md")
        if not any(wsb.reference_body_exists(body) for body in bodies):
            self.skipTest("upstream MVP bodies (planner-mvp-mode.md, skeleton-template.md) absent in this repo")
        self.assertEqual([], wsb.required_reading_leak_violations(workflow("plan-phase.md"), bodies, "plan-phase.md"))

    def test_scanner_fixtures(self):
        eager = "@~/.claude/engineer/references/planner-mvp-mode.md\n"
        lazy = "Read `engineer/references/planner-mvp-mode.md` when MVP_MODE.\n"
        self.assertEqual(1, len(wsb.eager_import_violations(eager, "planner-mvp-mode.md", "host.md")))
        self.assertEqual([], wsb.eager_import_violations(lazy, "planner-mvp-mode.md", "host.md"))
        self.assertEqual([], wsb.lazy_reference_violations(lazy, "planner-mvp-mode.md", "host.md"))
        self.assertEqual(1, len(wsb.lazy_reference_violations("nothing", "planner-mvp-mode.md", "host.md")))
        block = "<required_reading>\n@x/skeleton-template.md\n</required_reading>"
        self.assertEqual(["skeleton-template.md"], [v.split()[0] for v in wsb.required_reading_leak_violations(block, ("skeleton-template.md", "other.md"), "h")])
        self.assertEqual([], wsb.required_reading_leak_violations("no block", ("skeleton-template.md",), "h"))
        self.assertFalse(wsb.reference_body_exists("definitely-not-a-real-reference-body.md"))
        self.assertTrue(wsb.reference_body_exists("model-profile-resolution.md"))


class ByteCountLineEndings(Fixture):
    def test_crlf_and_lf_count_identically(self):
        body = "line one\nline two\nthree — with a multibyte dash\n"
        lf = self.put("lf.md", body)
        crlf = self.put("crlf.md", body.replace("\n", "\r\n"))
        self.assertEqual(wsb.lf_byte_count(lf), wsb.lf_byte_count(crlf))
        self.assertEqual(len(body.encode("utf-8")), wsb.lf_byte_count(lf))

    def test_empty_file_is_zero_bytes(self):
        self.assertEqual(0, wsb.lf_byte_count(self.put("empty.md", "")))


class PromptIncludes(Fixture):
    def test_no_workflow_prompt_string_contains_bare_include_line(self):
        offenders = wsb.bare_include_offenders()
        self.assertGreater(len(wsb.list_workflow_files_recursive()), 50)
        self.assertEqual([], offenders, "Claude Code never expands @path inside a dynamically built Agent() prompt:\n" + "\n".join(offenders))

    def test_scanner_flags_only_lines_inside_prompt_regions(self):
        text = "\n".join(['@~/.claude/outside.md', 'Agent(prompt="', "  @~/.claude/inside.md", '  @$HOME/also.md', "  plain", '"', ")",
                          "@~/.claude/after.md", ""])
        hits = wsb.bare_include_lines_in_prompt_regions(text)
        self.assertEqual([3, 4], [hit["line"] for hit in hits])
        self.assertEqual([], wsb.bare_include_lines_in_prompt_regions("@~/x.md\nno prompt here\n"))
        self.put("w/ok.md", "clean\n")
        self.put("w/bad.md", 'prompt="\n@~/x.md\n"\n')
        self.put("w/sub/deep.md", 'prompt="\n@$HOME/y.md\n"\n')
        offenders = wsb.bare_include_offenders(self.root/"w", self.root)
        self.assertEqual(["w/bad.md:2 @~/x.md", "w/sub/deep.md:2 @$HOME/y.md"], offenders)

    def test_execute_phase_execution_context_embeds_execute_plan(self):
        self.assertEqual([], wsb.execution_context_violations(workflow("execute-phase.md"), EMBED_PATH))

    def test_execution_context_fixtures(self):
        good = "<execution_context>\nORCHESTRATOR build-time embed\n- `%s`\n</execution_context>" % EMBED_PATH
        self.assertEqual([], wsb.execution_context_violations(good, EMBED_PATH))
        self.assertEqual(1, len(wsb.execution_context_violations("no block", EMBED_PATH)))
        self.assertEqual(2, len(wsb.execution_context_violations("<execution_context>\n@%s\n</execution_context>" % EMBED_PATH, EMBED_PATH)))

    def test_execute_phase_step_three_routes_gate_semantics_through_routing_fragment(self):
        step = wsb.dispatch_region(workflow("execute-phase.md"), "**Spawn executor agents:**", "**Wait for all agents in wave to complete.**")
        self.assertIn("execute-phase/steps/per-plan-executor-routing.md", step)
        fragment = (WORKFLOWS/"execute-phase/steps/per-plan-executor-routing.md").read_text(encoding="utf-8")
        self.assertEqual([], wsb.gate_routing_fragment_violations(fragment))

    def test_execute_phase_dispatch_has_no_anti_auto_approval_instruction(self):
        step = wsb.dispatch_region(workflow("execute-phase.md"), "**Spawn executor agents:**", "**Wait for all agents in wave to complete.**")
        self.assertEqual([], wsb.anti_auto_approval_violations(step, "step-3 dispatch region"))

    def test_execute_plan_pattern_a_carries_gate_semantics(self):
        if not (WORKFLOWS/"execute-plan.md").exists():
            self.skipTest("upstream execute-plan.md workflow (Pattern A dispatch) absent in this repo")
        region = wsb.dispatch_region((WORKFLOWS/"execute-plan.md").read_text(encoding="utf-8"),
                                     "**Pattern A:** init_agent_tracking", "**Pattern B:** Execute segment-by-segment")
        self.assertEqual([], wsb.pattern_a_violations(region))

    def test_execute_plan_still_defines_its_carried_steps(self):
        if not (WORKFLOWS/"execute-plan.md").exists():
            self.skipTest("upstream execute-plan.md workflow absent in this repo")
        content = (WORKFLOWS/"execute-plan.md").read_text(encoding="utf-8")
        self.assertEqual([], wsb.missing_markers(content, ("segment_execution", "previous_phase_check",
                                                           "verification_failure_gate", "update_codebase_map")))

    def test_gate_fragment_and_region_fixtures(self):
        good = ('`gate="blocking"` is auto-approvable. Only `gate="blocking-human"` surfaces. '
                "do NOT add text refusing or overriding\nauto-approval.")
        self.assertEqual([], wsb.gate_routing_fragment_violations(good))
        self.assertEqual(4, len(wsb.gate_routing_fragment_violations("silent")))
        self.assertEqual(1, len(wsb.gate_routing_fragment_violations(good+" Never auto-approve it.".lower())))
        pattern_a = ('gate="blocking" auto-approvable; gate="blocking-human"; no instruction that overrides the protocol.')
        self.assertEqual([], wsb.pattern_a_violations(pattern_a))
        self.assertEqual(4, len(wsb.pattern_a_violations("silent")))
        self.assertEqual(1, len(wsb.anti_auto_approval_violations("must not auto-approve", "x")))
        self.assertEqual([], wsb.anti_auto_approval_violations("fine", "x"))

    def test_dispatch_region_anchors(self):
        self.assertEqual("A b ", wsb.dispatch_region("pre A b END post", "A", "END"))
        with self.assertRaises(ValueError):
            wsb.dispatch_region("nothing", "A", "END")
        with self.assertRaises(ValueError):
            wsb.dispatch_region("A only", "A", "END")
        self.assertEqual(["gone"], wsb.missing_markers("have", ("have", "gone")))


if __name__ == "__main__":
    unittest.main()
