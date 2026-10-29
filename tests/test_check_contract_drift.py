"""Behavior contract for lib.check_contract_drift (port of scripts/check-contract-drift.cjs).

Three layers: pure-function tests over the typed IR, a seeded property over fence tracking, and
end-to-end tests against --root fixture trees including negative fixtures proving each rule can fail.
"""
import contextlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "engineer" / "bin"
LIB = BIN / "lib"


def _load(name):
    """Import engineer/bin/lib/<name> as an isolated package (another `lib` package exists under .ai/runtime)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py",
                                                      submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib." + name)


drift = _load("check_contract_drift")


def row(agent, markers, kind, **extra):
    return {"agent": agent, "completion_markers": markers, "kind": kind, **extra}


def run_violations(registry, producers=None, candidates=None, consumers=None):
    return drift.contract_violations(
        registry=registry,
        producer_markers=producers or {},
        candidate_markers=candidates or {},
        consumer_texts=consumers or {},
    )


def kinds_of(violations):
    return sorted({v["kind"] for v in violations})


class ExtractMarkers(unittest.TestCase):
    KNOWN = ["RESEARCH COMPLETE", "PLANNING COMPLETE"]

    def test_marker_heading_inside_a_fence_is_in_fence(self):
        result = drift.extract_markers("prose\n\n```\n## RESEARCH COMPLETE\n```\n", self.KNOWN)
        self.assertEqual([{"marker": "RESEARCH COMPLETE", "inFence": True}],
                         [{"marker": m["marker"], "inFence": m["inFence"]} for m in result["markers"]])

    def test_same_heading_outside_a_fence_has_in_fence_false(self):
        result = drift.extract_markers("## RESEARCH COMPLETE\n", self.KNOWN)
        self.assertEqual([False], [m["inFence"] for m in result["markers"]])

    def test_prose_is_not_extracted(self):
        result = drift.extract_markers("Execute the plan, then mark each complete in STATE.md.\n", self.KNOWN)
        self.assertEqual([], result["markers"])
        self.assertEqual([], result["candidates"])

    def test_heading_whose_complete_is_not_terminal_is_not_a_candidate(self):
        result = drift.extract_markers("```\n## Nearly Complete Refactor\n```\n", self.KNOWN)
        self.assertEqual([], result["markers"])
        self.assertEqual([], result["candidates"])

    def test_marker_shaped_unknown_heading_in_fence_is_a_candidate(self):
        result = drift.extract_markers("```\n## MYSTERY COMPLETE\n```\n\n## OUTSIDE COMPLETE\n", self.KNOWN)
        self.assertEqual(["MYSTERY COMPLETE"], [c["marker"] for c in result["candidates"]])

    def test_candidate_longer_than_sixty_characters_is_ignored(self):
        heading = "X" * 61
        result = drift.extract_markers(f"```\n## {heading}\n```\n", self.KNOWN)
        self.assertEqual([], result["candidates"])

    def test_empty_known_markers_never_guess(self):
        result = drift.extract_markers("```\n## RESEARCH COMPLETE\n```\n")
        self.assertEqual([], result["markers"])

    def test_heading_levels_one_through_six_are_extracted(self):
        content = "\n".join(f"{'#' * level} PLANNING COMPLETE" for level in range(1, 7))
        self.assertEqual(6, len(drift.extract_markers(content, self.KNOWN)["markers"]))

    def test_unclosed_fence_is_reported(self):
        result = drift.extract_markers("```\n## RESEARCH COMPLETE\n", self.KNOWN)
        self.assertTrue(result["unclosedFence"])
        self.assertTrue(result["markers"][0]["inFence"])

    def test_three_backticks_inside_four_backtick_fence_do_not_close_it(self):
        content = "\n".join(["````", "## PLANNING COMPLETE", "", "```", "inner", "```", "", "## RESEARCH COMPLETE", "````"])
        result = drift.extract_markers(content, self.KNOWN)
        self.assertFalse(result["unclosedFence"])
        self.assertEqual(2, len(result["markers"]))
        self.assertTrue(all(m["inFence"] for m in result["markers"]))

    def test_tilde_fences_behave_like_backtick_fences(self):
        result = drift.extract_markers("~~~\n## RESEARCH COMPLETE\n~~~\n", self.KNOWN)
        self.assertFalse(result["unclosedFence"])
        self.assertEqual([True], [m["inFence"] for m in result["markers"]])

    def test_a_tilde_run_does_not_close_a_backtick_fence(self):
        result = drift.extract_markers("```\n~~~\n## RESEARCH COMPLETE\n", self.KNOWN)
        self.assertTrue(result["unclosedFence"])

    def test_crlf_matches_lf(self):
        lf = "```\n## RESEARCH COMPLETE\n```\n\n## PLANNING COMPLETE\n"
        crlf = lf.replace("\n", "\r\n")
        a, b = drift.extract_markers(lf, self.KNOWN), drift.extract_markers(crlf, self.KNOWN)
        self.assertEqual(a["markers"], b["markers"])
        self.assertEqual(a["unclosedFence"], b["unclosedFence"])

    def test_empty_and_whitespace_only_input(self):
        empty = {"markers": [], "candidates": [], "unclosedFence": False}
        self.assertEqual(empty, drift.extract_markers("", self.KNOWN))
        self.assertEqual(empty, drift.extract_markers("   \n\t\n", self.KNOWN))
        self.assertEqual(empty, drift.extract_markers(None, self.KNOWN))

    def test_trailing_spaces_after_a_heading_are_trimmed(self):
        result = drift.extract_markers("## RESEARCH COMPLETE   \n", self.KNOWN)
        self.assertEqual(["RESEARCH COMPLETE"], [m["marker"] for m in result["markers"]])

    def test_the_same_marker_twice_reports_distinct_lines(self):
        content = "```\n## RESEARCH COMPLETE\n```\n\n```\n## RESEARCH COMPLETE\n```\n"
        self.assertEqual([2, 6], [m["line"] for m in drift.extract_markers(content, self.KNOWN)["markers"]])

    def test_a_five_thousand_line_file_terminates(self):
        lines = ["## RESEARCH COMPLETE" if i == 2500 else f"filler line {i}" for i in range(5000)]
        result = drift.extract_markers("\n".join(lines), self.KNOWN)
        self.assertEqual(["RESEARCH COMPLETE"], [m["marker"] for m in result["markers"]])


class FenceProperty(unittest.TestCase):
    """Fence tracking is invariant under any interleaving of fenced and unfenced blocks (seeded)."""
    LINES = ["plain prose line", "- list item", "## HEADING ONE", "## HEADING TWO", "## Mixed Case Heading",
             "```", "text after a bare three-backtick run"]
    KNOWN = {"HEADING ONE", "HEADING TWO"}

    def build(self, rng):
        parts, expected = [], []
        for _ in range(rng.randint(1, 20)):
            fenced = rng.random() < 0.5
            lines = [rng.choice(self.LINES) for _ in range(rng.randint(0, 6))]
            if fenced:
                parts.append("````")
            else:
                lines = [line for line in lines if not line.startswith("```")]
            for line in lines:
                parts.append(line)
                if line.startswith("## ") and line[3:] in self.KNOWN:
                    expected.append({"line": line[3:], "inFence": fenced})
            if fenced:
                parts.append("````")
        return "\n".join(parts), expected

    def test_every_extracted_marker_matches_its_block_fencedness(self):
        rng = random.Random(3565)
        for run in range(200):
            content, expected = self.build(rng)
            result = drift.extract_markers(content, sorted(self.KNOWN))
            with self.subTest(run=run):
                self.assertFalse(result["unclosedFence"], "4-backtick blocks always close")
                got = [{"line": m["marker"], "inFence": m["inFence"]} for m in result["markers"]]
                self.assertEqual(expected, got)


REGISTRY_MD = "\n".join([
    "# Agent Contracts",
    "",
    "## Agent Registry",
    "",
    "| Agent | Role | Completion Markers | Consumed by | Kind |",
    "|-------|------|--------------------|--------------|------|",
    "| a | First | `## ALPHA COMPLETE` | `engineer/workflows/w.md` | sentinel-match |",
    "| b | Second | `## BETA COMPLETE`, `## BETA BLOCKED` | prose only | sentinel-match |",
    "| c | Third | `## GAMMA DRAFT` (unconsumed: user draft, approved in chat) | `engineer/workflows/w.md` | sentinel-match |",
    "| d | Fourth | No marker (writes a file) | `engineer/workflows/w.md` | artifact+query |",
    "",
])


class ParseAgentContracts(unittest.TestCase):
    def test_rows_parse_with_marker_arrays_and_kind(self):
        result = drift.parse_agent_contracts(REGISTRY_MD)
        self.assertEqual([], result["errors"])
        rows = result["rows"]
        self.assertEqual(4, len(rows))
        self.assertEqual(["ALPHA COMPLETE"], rows[0]["completion_markers"])
        self.assertEqual("sentinel-match", rows[0]["kind"])
        self.assertEqual("a", rows[0]["agent"])
        self.assertEqual(["BETA COMPLETE", "BETA BLOCKED"], rows[1]["completion_markers"])

    def test_no_marker_row_has_empty_markers_and_keeps_note(self):
        rows = drift.parse_agent_contracts(REGISTRY_MD)["rows"]
        self.assertEqual([], rows[3]["completion_markers"])
        self.assertEqual(["writes a file"], rows[3]["notes"])

    def test_unconsumed_annotation_lands_in_unconsumed_markers(self):
        rows = drift.parse_agent_contracts(REGISTRY_MD)["rows"]
        self.assertEqual([], rows[2]["completion_markers"])
        self.assertEqual(["GAMMA DRAFT"], rows[2]["unconsumed_markers"])

    def test_comma_inside_annotation_does_not_split_the_entry(self):
        md = "\n".join(["## Agent Registry", "", "| Agent | Completion Markers |", "|-------|--------------------|",
                        "| x | `## X DRAFT` (unconsumed: draft display, approved interactively) |"])
        rows = drift.parse_agent_contracts(md)["rows"]
        self.assertEqual(["X DRAFT"], rows[0]["unconsumed_markers"])
        self.assertEqual([], rows[0]["completion_markers"])

    def test_pipe_inside_backticks_does_not_split_a_row(self):
        md = "\n".join(["## Agent Registry", "", "| Agent | Role |", "|---|---|", "| x | uses `a | b` here |"])
        result = drift.parse_agent_contracts(md)
        self.assertEqual([], result["errors"])
        self.assertEqual("uses `a | b` here", result["rows"][0]["role"])

    def test_malformed_rows_are_reported_not_raised(self):
        md = "\n".join(["## Agent Registry", "", "| Agent | Completion Markers |", "|-------|--------------------|",
                        "| good | `## OK COMPLETE` |", "| broken row missing cells |", "|  | `## NO AGENT` |"])
        result = drift.parse_agent_contracts(md)
        self.assertEqual(1, len(result["rows"]))
        self.assertEqual(2, len(result["errors"]))
        self.assertTrue(all(isinstance(e["line"], int) and e["reason"] for e in result["errors"]))
        self.assertEqual("column count mismatch: expected 2, got 1", result["errors"][0]["reason"])
        self.assertEqual("empty agent name", result["errors"][1]["reason"])

    def test_markdown_without_a_registry_section_is_empty(self):
        self.assertEqual({"rows": [], "errors": []}, drift.parse_agent_contracts("# Nothing here\n"))
        self.assertEqual({"rows": [], "errors": []}, drift.parse_agent_contracts(None))

    def test_registry_heading_without_a_table_is_empty(self):
        self.assertEqual({"rows": [], "errors": []}, drift.parse_agent_contracts("## Agent Registry\n\nprose only\n"))

    def test_table_ends_at_the_first_non_table_line(self):
        md = "\n".join(["## Agent Registry", "", "| Agent | Role |", "|---|---|", "| a | one |", "", "| b | two |"])
        self.assertEqual(["a"], [r["agent"] for r in drift.parse_agent_contracts(md)["rows"]])

    def test_completion_markers_cell_parser(self):
        parsed = drift.parse_completion_markers_cell("`## A COMPLETE`, ### B DONE (title case), No marker (none)")
        self.assertEqual(["A COMPLETE", "B DONE"], parsed["markers"])
        self.assertEqual(["title case", "none"], parsed["notes"])
        self.assertEqual([], parsed["unconsumedMarkers"])
        self.assertEqual({"markers": [], "notes": [], "unconsumedMarkers": []}, drift.parse_completion_markers_cell(""))


class ContractViolations(unittest.TestCase):
    def test_workflow_consumer_satisfies_a_sentinel_row(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match")], {"a": ["ALPHA COMPLETE"]},
                            consumers={"engineer/workflows/w.md": "match `## ALPHA COMPLETE` here"})
        self.assertEqual([], vs)

    def test_command_consumer_satisfies_a_sentinel_row(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match")], {"a": ["ALPHA COMPLETE"]},
                            consumers={"commands/x.md": "dispatch on `## ALPHA COMPLETE`"})
        self.assertEqual([], vs)

    def test_another_agent_may_consume(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match")], {"a": ["ALPHA COMPLETE"]},
                            consumers={"agents/b.md": "when the agent returns `## ALPHA COMPLETE`"})
        self.assertEqual([], vs)

    def test_no_consumer_names_producer_and_token(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match")], {"a": ["ALPHA COMPLETE"]},
                            consumers={"engineer/workflows/w.md": "unrelated text"})
        self.assertEqual(1, len(vs))
        self.assertEqual(("no_consumer", "a", "ALPHA COMPLETE"), (vs[0]["kind"], vs[0]["agent"], vs[0]["marker"]))
        self.assertEqual('no consumer text contains "ALPHA COMPLETE" (exact case)', vs[0]["detail"])

    def test_an_agent_never_satisfies_its_own_marker(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match")], {"a": ["ALPHA COMPLETE"]},
                            consumers={"agents/a.md": "I emit `## ALPHA COMPLETE` myself"})
        self.assertEqual(["no_consumer"], [v["kind"] for v in vs])

    def test_artifact_row_with_no_marker_is_satisfied(self):
        self.assertEqual([], run_violations([row("d", [], "artifact+query")], {"d": []}))

    def test_artifact_row_that_still_emits_a_marker_is_vestigial(self):
        vs = run_violations([row("d", [], "artifact+query")], {"d": ["VESTIGIAL COMPLETE"]},
                            {"d": ["VESTIGIAL COMPLETE"]})
        self.assertEqual(1, len(vs))
        self.assertEqual(("vestigial_marker", "VESTIGIAL COMPLETE"), (vs[0]["kind"], vs[0]["marker"]))

    def test_unconsumed_annotation_exempts_vestigial_marker(self):
        vs = run_violations([row("v", [], "artifact+query", unconsumed_markers=["Verification Complete"])],
                            {"v": ["Verification Complete"]})
        self.assertEqual([], vs)

    def test_structured_return_is_held_like_artifact(self):
        vs = run_violations([row("i", [], "structured-return")], {"i": ["EXTRA COMPLETE"]})
        self.assertEqual(["vestigial_marker"], [v["kind"] for v in vs])

    def test_roster_agent_with_no_row_is_agent_without_contract(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match")],
                            {"a": ["ALPHA COMPLETE"], "orphan": []},
                            consumers={"engineer/workflows/w.md": "x `## ALPHA COMPLETE`"})
        self.assertEqual(1, len(vs))
        self.assertEqual(("agent_without_contract", "orphan"), (vs[0]["kind"], vs[0]["agent"]))

    def test_two_rows_for_one_agent_are_duplicate_registry_row(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match"), row("a", ["ALPHA RETRY"], "sentinel-match")],
                            {"a": ["ALPHA COMPLETE", "ALPHA RETRY"]},
                            consumers={"engineer/workflows/w.md": "`## ALPHA COMPLETE` and `## ALPHA RETRY`"})
        self.assertEqual(["duplicate_registry_row"], [v["kind"] for v in vs])

    def test_row_naming_a_missing_agent_is_unknown_producer_without_marker_noise(self):
        vs = run_violations([row("ghost", ["GHOST COMPLETE"], "sentinel-match"), row("real", [], "artifact+query")],
                            {"real": []})
        self.assertEqual(["unknown_producer"], kinds_of(vs))

    def test_unresolved_file_shaped_consumed_by_is_unknown_consumer(self):
        vs = run_violations(
            [row("a", ["ALPHA COMPLETE"], "sentinel-match",
                 consumed_by="`engineer/workflows/missing.md`, `engineer/workflows/real.md`")],
            {"a": ["ALPHA COMPLETE"]},
            consumers={"engineer/workflows/real.md": "`## ALPHA COMPLETE`"})
        self.assertEqual(["unknown_consumer"], kinds_of(vs))

    def test_empty_registry_and_producers_yield_nothing(self):
        self.assertEqual([], run_violations([], {}))
        self.assertEqual([], drift.contract_violations())

    def test_empty_registry_flags_every_producer(self):
        vs = run_violations([], {"a": [], "b": []})
        self.assertEqual(["agent_without_contract"], kinds_of(vs))
        self.assertEqual(2, len(vs))

    def test_fourteen_valid_plus_one_broken_yields_exactly_the_broken_one(self):
        registry, producers, text = [], {}, ""
        for i in range(14):
            marker = f"M{i} COMPLETE"
            registry.append(row(f"a{i}", [marker], "sentinel-match"))
            producers[f"a{i}"] = [marker]
            text += f" `{marker}`"
        registry.append(row("broken", ["BROKEN COMPLETE"], "sentinel-match"))
        producers["broken"] = []
        vs = run_violations(registry, producers, consumers={"engineer/workflows/w.md": text})
        self.assertEqual(1, len(vs))
        self.assertEqual(("declared_marker_not_emitted", "broken"), (vs[0]["kind"], vs[0]["agent"]))

    def test_case_variant_tokens_are_a_case_collision(self):
        vs = run_violations([row("a", ["SYNTHESIS COMPLETE"], "sentinel-match"), row("b", ["Synthesis Complete"], "sentinel-match")],
                            {"a": ["SYNTHESIS COMPLETE"], "b": ["Synthesis Complete"]},
                            consumers={"engineer/workflows/w.md": "`## SYNTHESIS COMPLETE` `## Synthesis Complete`"})
        self.assertEqual(2, len(vs))
        self.assertTrue(all(v["kind"] == "case_collision" for v in vs))
        self.assertEqual("case-insensitive collision with: Synthesis Complete", vs[0]["detail"])

    def test_case_insensitive_only_match_is_case_only_match(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match")], {"a": ["ALPHA COMPLETE"]},
                            consumers={"engineer/workflows/w.md": "then the alpha complete step runs"})
        self.assertEqual(["case_only_match"], kinds_of(vs))

    def test_a_token_in_ordinary_prose_must_not_satisfy_the_contract(self):
        vs = run_violations([row("a", ["VERIFICATION COMPLETE"], "sentinel-match")], {"a": ["VERIFICATION COMPLETE"]},
                            consumers={"engineer/workflows/w.md": "Once verification complete, proceed."})
        self.assertEqual(["case_only_match"], kinds_of(vs))

    def test_unconsumed_marker_is_exempt_from_consumers_but_must_be_emitted(self):
        ok = run_violations([row("c", [], "sentinel-match", unconsumed_markers=["GAMMA DRAFT"])], {"c": ["GAMMA DRAFT"]})
        self.assertEqual([], ok)
        missing = run_violations([row("c", [], "sentinel-match", unconsumed_markers=["GAMMA DRAFT"])], {"c": []})
        self.assertEqual(["declared_marker_not_emitted"], kinds_of(missing))
        self.assertEqual("GAMMA DRAFT", missing[0]["marker"])

    def test_unconsumed_marker_still_participates_in_case_collision(self):
        vs = run_violations([row("a", ["GAMMA DRAFT"], "sentinel-match"),
                             row("c", [], "sentinel-match", unconsumed_markers=["Gamma Draft"])],
                            {"a": ["GAMMA DRAFT"], "c": ["Gamma Draft"]},
                            consumers={"engineer/workflows/w.md": "`## GAMMA DRAFT`"})
        self.assertTrue(any(v["kind"] == "case_collision" and v["marker"] == "Gamma Draft" for v in vs))

    def test_emitted_but_undeclared_candidate_is_deduped_per_marker(self):
        vs = run_violations([row("a", [], "sentinel-match")], {"a": []}, {"a": ["MYSTERY COMPLETE", "MYSTERY COMPLETE"]})
        self.assertEqual(["emitted_marker_not_declared"], [v["kind"] for v in vs])

    def test_emitted_marker_on_an_artifact_row_is_vestigial_never_also_undeclared(self):
        vs = run_violations([row("a", [], "artifact+query")], {"a": ["MYSTERY COMPLETE"]}, {"a": ["MYSTERY COMPLETE"]})
        self.assertEqual(["vestigial_marker"], [v["kind"] for v in vs])

    def test_unknown_kind_is_reported(self):
        vs = run_violations([row("a", [], "sometimes")], {"a": []})
        self.assertEqual(["unknown_kind"], kinds_of(vs))
        self.assertEqual('row declares unknown kind "sometimes"', vs[0]["detail"])

    def test_missing_kind_is_held_to_the_sentinel_contract(self):
        vs = run_violations([{"agent": "a", "completion_markers": ["ALPHA COMPLETE"]}], {"a": ["ALPHA COMPLETE"]},
                            consumers={"engineer/workflows/w.md": "nothing"})
        self.assertEqual(["no_consumer"], kinds_of(vs))

    def test_marker_consumed_only_outside_the_declared_consumers(self):
        vs = run_violations([row("a", ["ALPHA COMPLETE"], "sentinel-match", consumed_by="`engineer/workflows/w.md`")],
                            {"a": ["ALPHA COMPLETE"]},
                            consumers={"engineer/workflows/w.md": "no match here",
                                       "engineer/workflows/other.md": "dispatch `## ALPHA COMPLETE`"})
        self.assertEqual(1, len(vs))
        self.assertEqual(("declared_consumer_no_match", "ALPHA COMPLETE"), (vs[0]["kind"], vs[0]["marker"]))
        self.assertIn("( engineer/workflows/w.md )", vs[0]["detail"])

    def test_internal_failure_fails_red(self):
        with self.assertRaisesRegex(RuntimeError, r"contract_violations \(internal failure — failing red\)"):
            drift.contract_violations(registry=[{"agent": "a", "completion_markers": [3]}])


class TypedSurface(unittest.TestCase):
    def test_violation_kinds_are_exactly_the_emitted_vocabulary(self):
        self.assertEqual(sorted([
            "agent_without_contract", "case_collision", "case_only_match", "declared_consumer_no_match",
            "declared_marker_not_emitted", "duplicate_registry_row", "emitted_marker_not_declared",
            "legacy_read_tag", "no_consumer", "parse_error", "read_tag_gate_missing", "unclosed_fence",
            "unknown_consumer", "unknown_kind", "unknown_producer", "unmatched_consumer_token",
            "unresolved_reference_include", "vestigial_marker"]), sorted(drift.VIOLATION_KINDS.values()))

    def test_remedies_cover_exactly_the_violation_kinds(self):
        self.assertEqual(sorted(drift.REMEDIES), sorted(drift.VIOLATION_KINDS.values()))
        for kind, remedy in drift.REMEDIES.items():
            self.assertGreater(len(remedy), 10, f"remedy for {kind} must be actionable prose")

    def test_remedy_for_falls_back_for_an_unknown_kind(self):
        self.assertEqual("review the registry row and agent file for drift", drift.remedy_for("no-such-kind"))
        self.assertEqual(drift.REMEDIES["no_consumer"], drift.remedy_for("no_consumer"))

    def test_sanitize_echo_strips_control_characters_and_caps_length(self):
        self.assertEqual("clean text", drift.sanitize_echo("clean text"))
        self.assertEqual("abcd", drift.sanitize_echo("a\x00b\x07c\x1fd"))
        self.assertEqual("ab", drift.sanitize_echo("a\x7fb"))
        self.assertEqual(200, len(drift.sanitize_echo("x" * 500)))

    def test_non_agent_tokens_membership_is_locked(self):
        self.assertEqual([], sorted(drift.NON_AGENT_TOKENS))


class ParseConsumedByCell(unittest.TestCase):
    def test_backticked_paths_are_extracted(self):
        self.assertEqual(["engineer/workflows/a.md", "commands/b.md"],
                         drift.parse_consumed_by_cell("`engineer/workflows/a.md`, `commands/b.md`"))

    def test_globs_commands_and_prose_are_ignored(self):
        cell = "`*-VERIFICATION.md` artifact + `engineer_run query verification.status` in `engineer/workflows/v.md`"
        self.assertEqual(["engineer/workflows/v.md"], drift.parse_consumed_by_cell(cell))

    def test_paths_with_spaces_are_ignored_not_mangled(self):
        self.assertEqual(["docs/ok-file.md"], drift.parse_consumed_by_cell("`docs/Some File.md` and `docs/ok-file.md`"))

    def test_traversal_segments_are_dropped(self):
        self.assertEqual(["docs/real.md"], drift.parse_consumed_by_cell("`docs/../../etc/secret.md` plus `docs/real.md`"))
        self.assertEqual([], drift.parse_consumed_by_cell("`../outside.md`"))

    def test_empty_and_non_string_input(self):
        self.assertEqual([], drift.parse_consumed_by_cell(""))
        self.assertEqual([], drift.parse_consumed_by_cell(None))
        self.assertEqual([], drift.parse_consumed_by_cell(5))


class ReadTagViolations(unittest.TestCase):
    REG = [{"agent": "a", "consumed_by": "`engineer/workflows/w.md`"}]

    def test_consumer_emitting_required_reading_with_no_gate_is_reported(self):
        vs = drift.read_tag_violations(self.REG, {"a": "# Agent\n\nNo gate mention."},
                                       {"engineer/workflows/w.md": "<required_reading>\n- UI-SPEC.md\n</required_reading>"})
        self.assertEqual(1, len(vs))
        self.assertEqual(("read_tag_gate_missing", "a"), (vs[0]["kind"], vs[0]["agent"]))
        self.assertEqual("consumer engineer/workflows/w.md emits <required_reading> but agents/a.md never references the gate",
                         vs[0]["detail"])

    def test_agent_referencing_the_gate_is_satisfied(self):
        vs = drift.read_tag_violations(self.REG, {"a": "If the prompt contains a `<required_reading>` block, you MUST Read every file."},
                                       {"engineer/workflows/w.md": "<required_reading>\n- X.md\n</required_reading>"})
        self.assertEqual([], vs)

    def test_consumer_without_a_read_tag_imposes_nothing(self):
        self.assertEqual([], drift.read_tag_violations(self.REG, {"a": "nothing"}, {"engineer/workflows/w.md": "plain dispatch"}))

    def test_legacy_files_to_read_anywhere_is_reported(self):
        vs = drift.read_tag_violations([], {}, {"agents/a.md": "<files_to_read>\n- x\n</files_to_read>"})
        self.assertEqual(["legacy_read_tag"], [v["kind"] for v in vs])
        self.assertEqual("agents/a.md still contains the retired <files_to_read> tag", vs[0]["detail"])

    def test_row_for_a_missing_agent_is_skipped(self):
        self.assertEqual([], drift.read_tag_violations(self.REG, {}, {"engineer/workflows/w.md": "<required_reading>x</required_reading>"}))

    def test_one_violation_per_agent(self):
        reg = [{"agent": "a", "consumed_by": "`engineer/workflows/w.md`, `engineer/workflows/v.md`"}]
        vs = drift.read_tag_violations(reg, {"a": "none"}, {"engineer/workflows/w.md": "<required_reading>", "engineer/workflows/v.md": "<required_reading>"})
        self.assertEqual(1, len(vs))

    def test_defaults_to_empty_inputs(self):
        self.assertEqual([], drift.read_tag_violations())


class UnmatchedConsumerTokens(unittest.TestCase):
    def test_workflow_matching_a_phantom_token_is_reported(self):
        vs = drift.unmatched_consumer_tokens({"engineer/workflows/w.md": "dispatch on `## PHANTOM COMPLETE`"}, {"REAL COMPLETE"})
        self.assertEqual(1, len(vs))
        self.assertEqual(("unmatched_consumer_token", "PHANTOM COMPLETE"), (vs[0]["kind"], vs[0]["marker"]))
        self.assertEqual("engineer/workflows/w.md matches `## PHANTOM COMPLETE` but no agent declares or emits it", vs[0]["detail"])

    def test_declared_token_is_not_a_violation(self):
        self.assertEqual([], drift.unmatched_consumer_tokens({"engineer/workflows/w.md": "dispatch on `## REAL COMPLETE`"}, {"REAL COMPLETE"}))

    def test_vocabulary_may_be_a_list(self):
        self.assertEqual([], drift.unmatched_consumer_tokens({"commands/x.md": "`## REAL COMPLETE`"}, ["REAL COMPLETE"]))

    def test_agents_are_not_scanned(self):
        self.assertEqual([], drift.unmatched_consumer_tokens({"agents/a.md": "returns `## PHANTOM COMPLETE`"}, set()))

    def test_retired_graphify_markers_are_not_exempt(self):
        findings = drift.unmatched_consumer_tokens({"commands/x.md": "display `## GRAPHIFY BUILD COMPLETE`"}, set())
        self.assertEqual(["GRAPHIFY BUILD COMPLETE"], [finding["marker"] for finding in findings])

    def test_mixed_case_and_long_tokens_are_not_flagged(self):
        text = "match `## Self-Check: FAILED` and `## " + "X" * 61 + " COMPLETE`"
        self.assertEqual([], drift.unmatched_consumer_tokens({"engineer/workflows/w.md": text}, set()))

    def test_double_quoted_matches_are_scanned(self):
        vs = drift.unmatched_consumer_tokens({"engineer/workflows/w.md": 'stall_watch "## PHANTOM COMPLETE"'}, set())
        self.assertEqual(["PHANTOM COMPLETE"], [v["marker"] for v in vs])

    def test_the_same_token_is_reported_once_per_file(self):
        text = "`## PHANTOM COMPLETE` and again `## PHANTOM COMPLETE`"
        vs = drift.unmatched_consumer_tokens({"engineer/workflows/w.md": text, "commands/x.md": text}, set())
        self.assertEqual(2, len(vs))


class ReferenceIncludes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "engineer" / "references").mkdir(parents=True)

    def includes(self, text):
        return drift.reference_includes(text, self.root)

    def test_every_followed_spelling(self):
        for pointer in ("@~/.claude/engineer/references/ref.md", "@$HOME/.claude/engineer/references/ref.md",
                        "@engineer/references/ref.md", "@.claude/engineer/references/ref.md",
                        "@config/nested/engineer/references/ref.md"):
            with self.subTest(pointer=pointer):
                self.assertEqual({"includes": ["engineer/references/ref.md"], "declined": []}, self.includes(pointer))

    def test_nested_names_are_followed(self):
        result = self.includes("@~/.claude/engineer/references/few-shot-examples/verifier.md")
        self.assertEqual(["engineer/references/few-shot-examples/verifier.md"], result["includes"])

    def test_prefixes_that_are_not_followed(self):
        for pointer in ("@./engineer/references/ref.md", "@../engineer/references/ref.md", "@a/../engineer/references/ref.md"):
            with self.subTest(pointer=pointer):
                self.assertEqual({"includes": [], "declined": []}, self.includes(pointer))

    def test_includes_are_deduplicated_in_first_seen_order(self):
        result = self.includes("@engineer/references/b.md @engineer/references/a.md @engineer/references/b.md")
        self.assertEqual(["engineer/references/b.md", "engineer/references/a.md"], result["includes"])

    def test_a_token_continuing_past_the_name_is_declined_whole(self):
        result = self.includes("see @~/.claude/engineer/references/tdd.md/xx/yy here")
        self.assertEqual([], result["includes"])
        self.assertEqual("@~/.claude/engineer/references/tdd.md/xx/yy", result["declined"][0]["pointer"])
        self.assertTrue(result["declined"][0]["reason"].startswith("does not name a reference whole"))

    def test_javascript_whitespace_semantics_in_the_token(self):
        # U+0085 is not whitespace in the contract, U+0020 is: one token continues, the other ends.
        self.assertEqual([], self.includes("@engineer/references/tdd.md\u0085xx")["includes"])
        self.assertEqual(["engineer/references/tdd.md"], self.includes("@engineer/references/tdd.md xx")["includes"])

    def test_closing_prose_punctuation_is_stripped(self):
        for follower in ("", "`", "**", ")", ".", ",", "`.", "]", ":"):
            with self.subTest(follower=follower):
                self.assertEqual(["engineer/references/tdd.md"], self.includes(f"@engineer/references/tdd.md{follower}")["includes"])

    def test_name_class_characters_are_never_stripped(self):
        for tail in ("_", "-", "_.", "._", "-)", "x"):
            with self.subTest(tail=tail):
                self.assertEqual([], self.includes(f"@engineer/references/tdd.md{tail}")["includes"])

    def test_ambiguity_when_the_unstripped_token_names_a_file(self):
        try:
            (self.root / "engineer" / "references" / "tdd.md)").write_text("x", encoding="utf-8")
        except OSError as error:
            self.skipTest(f"file name unavailable on this host ({error})")
        result = self.includes("@engineer/references/tdd.md)")
        self.assertEqual([], result["includes"])
        self.assertEqual(
            "is ambiguous — `tdd.md)` itself names something on disk, so stripping it to `tdd.md` would pick one of two readings; neither is followed",
            result["declined"][0]["reason"])

    def test_a_trailing_dot_alias_is_not_ambiguous(self):
        # On Windows `tdd.md.` is an alias of `tdd.md`; either way the pointer is the real file.
        (self.root / "engineer" / "references" / "tdd.md").write_text("x", encoding="utf-8")
        self.assertEqual(["engineer/references/tdd.md"], self.includes("@engineer/references/tdd.md.")["includes"])


FIXTURE_REGISTRY = "\n".join([
    "| Agent | Role | Completion Markers | Consumed by | Kind |",
    "|-------|------|--------------------|--------------|------|",
    "| alpha | Fixture | `## ALPHA COMPLETE` | `engineer/workflows/w.md` | sentinel-match |",
])
CLEAN_AGENTS = {"alpha.md": "\n".join(["# Alpha", "", "Return:", "", "```markdown", "## ALPHA COMPLETE", "done", "```",
                                       "", "Gate: `<required_reading>` MUST be Read.", ""])}
CLEAN_EXTRA = {"engineer/workflows/w.md": "Dispatch on `## ALPHA COMPLETE`.\n\n<required_reading>\n- x.md\n</required_reading>\n"}
MARKER_REFERENCE = "```markdown\n## ALPHA COMPLETE\n```\n"


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)

    def write_fixture(self, registry_body, agents=None, extra=None):
        for sub in ("engineer/references", "agents", "engineer/workflows", "commands"):
            (self.dir / sub).mkdir(parents=True, exist_ok=True)
        (self.dir / "engineer/references/agent-contracts.md").write_text(
            "\n".join(["## Agent Registry", "", registry_body, ""]), encoding="utf-8")
        for name, body in (agents or {}).items():
            (self.dir / "agents" / name).write_text(body, encoding="utf-8")
        for relative, body in (extra or {}).items():
            target = self.dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")

    def check(self, *flags):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = drift.main(["--root", str(self.dir), *flags])
        return code, out.getvalue(), err.getvalue()

    def check_json(self):
        code, out, err = self.check("--json")
        return code, json.loads(out), err

    def delegated(self, pointer):
        self.write_fixture(FIXTURE_REGISTRY,
                           {"alpha.md": f"# Alpha\n\nProcedure: {pointer}\n\nGate: `<required_reading>` MUST be Read.\n"},
                           {**CLEAN_EXTRA, "engineer/references/ref.md": MARKER_REFERENCE})


class EndToEnd(FixtureCase):
    def test_clean_fixture_exits_zero(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, CLEAN_EXTRA)
        code, report, err = self.check_json()
        self.assertEqual(0, code, err)
        self.assertEqual({"check": "check-contract-drift", "status": "ok", "agents": 1, "markers": 1, "violations": []}, report)

    def test_clean_fixture_text_output(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, CLEAN_EXTRA)
        code, out, err = self.check()
        self.assertEqual((0, "ok check-contract-drift: 1 agents, 1 markers, 0 violations\n", ""), (code, out, err))

    def test_followed_pointer_spellings_delegate_the_marker(self):
        for label, pointer in [("tilde", "@~/.claude/engineer/references/ref.md"), ("home", "@$HOME/.claude/engineer/references/ref.md"),
                               ("bare", "@engineer/references/ref.md"), ("project-relative", "@.claude/engineer/references/ref.md"),
                               ("nested project-relative", "@config/nested/engineer/references/ref.md")]:
            with self.subTest(label=label):
                self.delegated(pointer)
                code, report, err = self.check_json()
                self.assertEqual(0, code, f"{pointer} was not followed; stderr: {err}")
                self.assertEqual([], report["violations"])

    def test_unfollowed_pointer_spellings_leave_the_marker_undeclared(self):
        for label, pointer in [("dot prefix", "@./engineer/references/ref.md"), ("dot-dot prefix", "@../engineer/references/ref.md"),
                               ("dot-dot in a non-first position", "@a/../engineer/references/ref.md"),
                               ("token continuing past the name", "@~/.claude/engineer/references/ref.md/xx?"),
                               ("trailing traversal", "@~/.claude/engineer/references/ref.md/../../ref.md")]:
            with self.subTest(label=label):
                self.delegated(pointer)
                code, report, _ = self.check_json()
                self.assertEqual(1, code, f"{pointer} was followed and should not have been")
                self.assertTrue(any(v["kind"] == "declared_marker_not_emitted" for v in report["violations"]),
                                json.dumps(report["violations"]))

    def test_planted_unmatched_sentinel_names_the_producer(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, {"engineer/workflows/w.md": "No markers matched here.\n"})
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        self.assertEqual("violations", report["status"])
        found = next(v for v in report["violations"] if v["kind"] == "no_consumer")
        self.assertEqual(("alpha", "ALPHA COMPLETE"), (found["agent"], found["marker"]))

    def test_planted_reverse_violation_fails(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS,
                           {"engineer/workflows/w.md": "Dispatch on `## ALPHA COMPLETE` or `## PHANTOM COMPLETE`.\n"})
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        found = next(v for v in report["violations"] if v["kind"] == "unmatched_consumer_token")
        self.assertEqual("PHANTOM COMPLETE", found["marker"])

    def test_planted_case_collision_fails(self):
        registry = "\n".join([
            "| Agent | Role | Completion Markers | Consumed by | Kind |",
            "|-------|------|--------------------|--------------|------|",
            "| alpha | Fixture | `## ALPHA COMPLETE` | `engineer/workflows/w.md` | sentinel-match |",
            "| beta | Fixture | `## Alpha Complete` | `engineer/workflows/w.md` | sentinel-match |",
        ])
        self.write_fixture(registry, {**CLEAN_AGENTS, "beta.md": "```\n## Alpha Complete\n```\n"},
                           {"engineer/workflows/w.md": "`## ALPHA COMPLETE` `## Alpha Complete`\n"})
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        self.assertTrue(any(v["kind"] == "case_collision" for v in report["violations"]))

    def test_roster_agent_missing_from_the_registry_fails(self):
        self.write_fixture(FIXTURE_REGISTRY, {**CLEAN_AGENTS, "unregistered.md": "# Unregistered\n"}, CLEAN_EXTRA)
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        found = next(v for v in report["violations"] if v["kind"] == "agent_without_contract")
        self.assertEqual("unregistered", found["agent"])

    def test_compact_variants_need_no_registry_row(self):
        self.write_fixture(FIXTURE_REGISTRY, {**CLEAN_AGENTS, "alpha.compact.md": "# Alpha compact\n"}, CLEAN_EXTRA)
        code, report, _ = self.check_json()
        self.assertEqual((0, []), (code, report["violations"]))

    def test_planted_legacy_read_tag_fails(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, {"engineer/workflows/w.md": "<files_to_read>\n- x.md\n</files_to_read>\n"})
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        self.assertTrue(any(v["kind"] == "legacy_read_tag" for v in report["violations"]))

    def test_consumer_emitting_required_reading_to_a_gateless_agent_fails(self):
        self.write_fixture(FIXTURE_REGISTRY, {"alpha.md": "# Alpha\n\nNo gate anywhere.\n\n```\n## ALPHA COMPLETE\n```\n"}, CLEAN_EXTRA)
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        found = next(v for v in report["violations"] if v["kind"] == "read_tag_gate_missing")
        self.assertEqual("alpha", found["agent"])

    def test_gate_delivered_by_an_included_reference_counts(self):
        self.write_fixture(FIXTURE_REGISTRY,
                           {"alpha.md": "# Alpha\n\n@~/.claude/engineer/references/gate.md\n\n```\n## ALPHA COMPLETE\n```\n"},
                           {**CLEAN_EXTRA, "engineer/references/gate.md": "If the prompt has a `<required_reading>` block, Read it.\n"})
        code, report, err = self.check_json()
        self.assertEqual((0, []), (code, report["violations"]), err)

    def test_missing_contracts_file_exits_one_with_a_named_path(self):
        (self.dir / "agents").mkdir()
        code, out, err = self.check()
        self.assertEqual(1, code)
        self.assertEqual("\nERROR check-contract-drift: contracts file not found at engineer/references/agent-contracts.md\n\n", err)
        self.assertEqual("", out)

    def test_malformed_registry_row_fails_as_parse_error(self):
        registry = FIXTURE_REGISTRY + "\n| broken row with too few cells |"
        self.write_fixture(registry, CLEAN_AGENTS, CLEAN_EXTRA)
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        found = next(v for v in report["violations"] if v["kind"] == "parse_error")
        self.assertTrue(found["detail"].startswith("agent-contracts.md:"))

    def test_unclosed_fence_fails(self):
        self.write_fixture(FIXTURE_REGISTRY, {"alpha.md": "# Alpha\n\n```\n## ALPHA COMPLETE\nnever closed\n"}, CLEAN_EXTRA)
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        self.assertTrue(any(v["kind"] == "unclosed_fence" for v in report["violations"]))

    def test_unknown_consumer_fails(self):
        registry = FIXTURE_REGISTRY.replace("engineer/workflows/w.md", "engineer/workflows/missing.md")
        self.write_fixture(registry, CLEAN_AGENTS, CLEAN_EXTRA)
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        self.assertTrue(any(v["kind"] == "unknown_consumer" for v in report["violations"]))

    def test_consumed_by_file_outside_the_scanned_trees_participates(self):
        registry = FIXTURE_REGISTRY.replace("`engineer/workflows/w.md`", "`docs/adr/plan.md`")
        self.write_fixture(registry, CLEAN_AGENTS, {"docs/adr/plan.md": "Dispatch on `## ALPHA COMPLETE`.\n"})
        code, report, _ = self.check_json()
        self.assertEqual(0, code, json.dumps(report["violations"]))

    def test_human_output_groups_by_kind_with_remedies(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, {"engineer/workflows/w.md": "No markers matched here.\n"})
        code, out, err = self.check()
        self.assertEqual((1, ""), (code, out))
        self.assertIn("\nERROR check-contract-drift: 1 violation(s) across 1 kind(s)\n\n", err)
        self.assertIn("  no_consumer (1):\n", err)
        self.assertIn('    - alpha marker "ALPHA COMPLETE": no consumer text contains "ALPHA COMPLETE" (exact case)\n', err)
        self.assertIn(f"      remedy: {drift.REMEDIES['no_consumer']}\n", err)
        self.assertTrue(err.endswith("See engineer/references/agent-contracts.md for the registry contract spec.\n\n"))

    def test_human_output_labels_registry_level_violations(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, {"engineer/workflows/w.md": "`## ALPHA COMPLETE` `## PHANTOM COMPLETE`\n"})
        _, _, err = self.check()
        self.assertIn('    - (registry) marker "PHANTOM COMPLETE": ', err)

    def test_json_detail_is_sanitized(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, {"engineer/workflows/w.md": "`## ALPHA COMPLETE` `## PH\x07ANTOM COMPLETE`\n"})
        _, report, _ = self.check_json()
        for violation in report["violations"]:
            self.assertNotIn("\x07", violation["detail"])


class ReferenceIncludeReporting(FixtureCase):
    """Reference includes resolve exactly, or are reported: nothing is silently dropped."""

    def include_only_agent(self, tail):
        return {"alpha.md": f"# Alpha\n\nFull procedure: @~/.claude/engineer/references/{tail}\n\nGate: `<required_reading>` MUST be Read.\n"}

    def violations_of(self, kind, report):
        return [v for v in report["violations"] if v["kind"] == kind]

    def test_pointer_continuing_past_a_real_name_is_reported_and_does_not_borrow_it(self):
        verdicts = []
        for present in (True, False):
            with self.subTest(present=present):
                self.write_fixture(FIXTURE_REGISTRY, self.include_only_agent("tdd.md/xx/yy"),
                                   {**CLEAN_EXTRA, **({"engineer/references/tdd.md": MARKER_REFERENCE} if present else {})})
                code, report, _ = self.check_json()
                self.assertEqual(1, code)
                found = self.violations_of("unresolved_reference_include", report)[0]
                self.assertEqual("alpha", found["agent"])
                self.assertIn("tdd.md/xx/yy", found["detail"])
                self.assertTrue(any(v["kind"] == "declared_marker_not_emitted" and v["marker"] == "ALPHA COMPLETE"
                                    for v in report["violations"]))
                verdicts.append(sorted(f"{v['kind']}:{v['marker']}" for v in report["violations"]))
        self.assertEqual(verdicts[0], verdicts[1], "the verdict must not depend on a file the agent text never names")

    CONTINUATIONS = [
        "tdd.md/xx/yy", "tdd.md./xx", "tdd.mdx/xx", "tdd.md\\xx", "tdd.md%2fxx", "tdd.md⁄xx",
        "tdd.md∕xx", "tdd.md／xx", "tdd.md⧸xx", "tdd.md＼xx", "tdd.md%252fxx",
        "tdd.md%2e%2e", "tdd.md\u0085xx", "tdd.md​xx",
        "tdd.md_", "tdd.md-", "tdd.md_.", "tdd.md._", "tdd.md-)",
    ]

    def test_every_continuation_spelling_is_reported_once_as_written(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, {**CLEAN_EXTRA, "engineer/references/tdd.md": MARKER_REFERENCE})
        block = "".join(f"See @~/.claude/engineer/references/{tail} here.\n" for tail in self.CONTINUATIONS)
        with open(self.dir / "agents" / "alpha.md", "a", encoding="utf-8", newline="") as handle:
            handle.write(block * 2)
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        details = [v["detail"] for v in self.violations_of("unresolved_reference_include", report)]
        self.assertEqual(len(self.CONTINUATIONS), len(details), json.dumps(details))
        for tail in self.CONTINUATIONS:
            needle = f"@~/.claude/engineer/references/{tail} does not name a reference whole"
            self.assertTrue(any(needle in d for d in details), f"{tail!r} must be reported as written: {details!r}")

    def test_closing_punctuation_still_includes_the_named_file_unreported(self):
        for follower in ("", " next", "`", "**", ")", ".", ". Next", ",", "`.", "]", ":"):
            with self.subTest(follower=follower):
                self.write_fixture(FIXTURE_REGISTRY, self.include_only_agent(f"tdd.md{follower}"),
                                   {**CLEAN_EXTRA, "engineer/references/tdd.md": MARKER_REFERENCE})
                code, report, err = self.check_json()
                self.assertEqual(0, code, f"stderr: {err} violations: {report['violations']}")
                self.assertEqual([], report["violations"])

    def test_unstripped_token_naming_a_file_is_reported_as_ambiguous(self):
        for label, with_stripped in (("stripped name also exists", True), ("only the unstripped token exists", False)):
            with self.subTest(label=label):
                self.write_fixture(FIXTURE_REGISTRY, self.include_only_agent("tdd.md)"),
                                   {**CLEAN_EXTRA, **({"engineer/references/tdd.md": MARKER_REFERENCE} if with_stripped else {})})
                try:
                    (self.dir / "engineer/references" / "tdd.md)").write_text(MARKER_REFERENCE, encoding="utf-8")
                except OSError as error:
                    self.skipTest(f"file name unavailable on this host ({error})")
                code, report, _ = self.check_json()
                self.assertEqual(1, code)
                found = self.violations_of("unresolved_reference_include", report)[0]
                self.assertIn("tdd.md) is ambiguous — `tdd.md)` itself names something on disk, so stripping it to `tdd.md`", found["detail"])
                self.assertTrue(any(v["kind"] == "declared_marker_not_emitted" and v["marker"] == "ALPHA COMPLETE"
                                    for v in report["violations"]), "neither reading may satisfy the marker")

    def test_a_real_include_still_delegates_the_marker(self):
        self.write_fixture(FIXTURE_REGISTRY, self.include_only_agent("tdd.md."),
                           {**CLEAN_EXTRA, "engineer/references/tdd.md": MARKER_REFERENCE})
        code, report, err = self.check_json()
        self.assertEqual(0, code, f"stderr: {err} violations: {report['violations']}")
        self.assertEqual([], report["violations"])

    def test_include_naming_a_missing_file_is_reported(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, CLEAN_EXTRA)
        with open(self.dir / "agents" / "alpha.md", "a", encoding="utf-8") as handle:
            handle.write("See @~/.claude/engineer/references/absent.md\n")
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        found = self.violations_of("unresolved_reference_include", report)[0]
        self.assertIn("absent.md does not exist", found["detail"])
        self.assertTrue(found["detail"].startswith("agents/alpha.md: engineer/references/absent.md"))

    def test_include_naming_a_directory_is_not_a_regular_file(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, CLEAN_EXTRA)
        (self.dir / "engineer/references/dir.md").mkdir()
        with open(self.dir / "agents" / "alpha.md", "a", encoding="utf-8") as handle:
            handle.write("See @~/.claude/engineer/references/dir.md\n")
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        self.assertIn("dir.md is not a regular file", self.violations_of("unresolved_reference_include", report)[0]["detail"])

    def make_symlink(self, target, link):
        try:
            os.symlink(target, link)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f"symlink unavailable on this host ({error})")

    def test_dangling_symlink_is_reported_and_not_followed(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, CLEAN_EXTRA)
        self.make_symlink(self.dir / "nowhere" / "gone.md", self.dir / "engineer/references" / "gone.md")
        with open(self.dir / "agents" / "alpha.md", "a", encoding="utf-8") as handle:
            handle.write("See @~/.claude/engineer/references/gone.md\n")
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        self.assertIn("gone.md does not resolve inside engineer/references/",
                      self.violations_of("unresolved_reference_include", report)[0]["detail"])

    def test_include_whose_realpath_leaves_the_references_tree_is_not_followed(self):
        self.write_fixture(FIXTURE_REGISTRY, self.include_only_agent("out.md"),
                           {**CLEAN_EXTRA, "outside/out.md": MARKER_REFERENCE})
        self.make_symlink(self.dir / "outside" / "out.md", self.dir / "engineer/references" / "out.md")
        code, report, _ = self.check_json()
        self.assertEqual(1, code)
        self.assertIn("does not resolve inside engineer/references/",
                      self.violations_of("unresolved_reference_include", report)[0]["detail"])
        self.assertTrue(any(v["kind"] == "declared_marker_not_emitted" and v["marker"] == "ALPHA COMPLETE"
                            for v in report["violations"]), "the escaped file must not satisfy the marker")


class TryWithinRoot(FixtureCase):
    def test_contained_relative_path_resolves(self):
        (self.dir / "a.md").write_text("x", encoding="utf-8")
        resolved = drift._try_within_root("a.md", str(self.dir))
        self.assertEqual(os.path.realpath(self.dir / "a.md"), resolved)

    def test_missing_contained_path_is_still_contained(self):
        self.assertEqual(os.path.realpath(self.dir) + os.sep + "nope.md", drift._try_within_root("nope.md", str(self.dir)))

    def test_traversal_absolute_nul_and_empty_are_refused(self):
        for candidate in ("../x.md", "a/../../x.md", str(self.dir / "a.md"), "a\0b", "", None):
            with self.subTest(candidate=candidate):
                self.assertIsNone(drift._try_within_root(candidate, str(self.dir)))
        self.assertIsNone(drift._try_within_root("a.md", ""))

    def link_directory(self, target, link):
        try:
            os.symlink(target, link, target_is_directory=True)
            return
        except (OSError, NotImplementedError):
            pass
        if os.name == "nt":
            made = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
            if made.returncode == 0:
                return
        self.skipTest("directory links unavailable on this host")

    def test_an_intermediate_link_that_leaves_the_root_is_refused(self):
        root, outside = self.dir / "refs", self.dir / "outside"
        root.mkdir()
        outside.mkdir()
        (outside / "out.md").write_text("x", encoding="utf-8")
        self.link_directory(outside, root / "linked")
        self.assertIsNone(drift._try_within_root("linked/out.md", str(root)))
        self.assertIsNone(drift._try_within_root("linked/missing.md", str(root)))

    def test_an_intermediate_link_that_stays_inside_the_root_is_followed(self):
        root = self.dir / "refs"
        (root / "real").mkdir(parents=True)
        (root / "real" / "a.md").write_text("x", encoding="utf-8")
        self.link_directory(root / "real", root / "alias")
        self.assertEqual(os.path.realpath(root / "real" / "a.md"), drift._try_within_root("alias/a.md", str(root)))

    def test_a_sibling_sharing_the_root_prefix_is_not_contained(self):
        self.assertFalse(drift._is_contained_in(str(self.dir) + "-evil", str(self.dir)))
        self.assertTrue(drift._is_contained_in(str(self.dir), str(self.dir)))


class CommandLine(FixtureCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, "-m", "lib.check_contract_drift", *map(str, args)],
                              cwd=BIN, capture_output=True, text=True, encoding="utf-8")

    def test_clean_fixture_exits_zero_as_a_module(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, CLEAN_EXTRA)
        process = self.run_cli("--root", self.dir, "--json")
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual("ok", json.loads(process.stdout)["status"])

    def test_violations_exit_one_with_diagnostics_on_stderr(self):
        self.write_fixture(FIXTURE_REGISTRY, CLEAN_AGENTS, {"engineer/workflows/w.md": "nothing\n"})
        process = self.run_cli("--root", self.dir)
        self.assertEqual(1, process.returncode)
        self.assertEqual("", process.stdout)
        self.assertIn("ERROR check-contract-drift: 1 violation(s) across 1 kind(s)", process.stderr)

    def test_missing_contracts_file_exits_one(self):
        (self.dir / "agents").mkdir()
        process = self.run_cli("--root", self.dir)
        self.assertEqual(1, process.returncode)
        self.assertIn("agent-contracts.md", process.stdout + process.stderr)

    def test_root_without_a_value_exits_one(self):
        process = self.run_cli("--root")
        self.assertEqual(1, process.returncode)
        self.assertIn("--root requires a directory argument", process.stderr)

    def test_resolve_root(self):
        self.assertEqual(ROOT, drift.resolve_root([]))
        self.assertEqual(Path(os.path.abspath("somewhere")), drift.resolve_root(["--root", "somewhere", "--json"]))
        with self.assertRaises(ValueError):
            drift.resolve_root(["--root", ""])
        with self.assertRaises(ValueError):
            drift.resolve_root(["--root"])

    def test_walk_markdown_files_skips_unreadable_directories_and_non_markdown(self):
        (self.dir / "sub").mkdir()
        (self.dir / "sub" / "a.md").write_text("x", encoding="utf-8")
        (self.dir / "b.txt").write_text("x", encoding="utf-8")
        found = [drift.to_repo_relative(p, self.dir) for p in drift.walk_markdown_files(str(self.dir))]
        self.assertEqual(["sub/a.md"], found)
        self.assertEqual([], drift.walk_markdown_files(str(self.dir / "absent")))


class RealRepository(unittest.TestCase):
    @unittest.expectedFailure
    def test_real_tree_passes(self):
        """The real repository drifts from its registry; this stays expected-failing until the content is repaired.

        Violations at the pinned base: agent_without_contract (agents/AGENT.md has no registry row);
        unknown_consumer (planner -> engineer/workflows/plan-review-convergence.md, plan-checker ->
        engineer/workflows/import.md, pattern-mapper -> engineer/workflows/settings.md name files that do
        not exist); case_only_match (executor `PLAN COMPLETE`); read_tag_gate_missing (executor, whose
        `@~/.claude/references/...` pointers omit `engineer/`, so the mandatory-initial-read gate is never
        followed); unmatched_consumer_token (`SYNTHESIS COMPLETE`, `ROADMAP BLOCKED`, `ROADMAP PROPOSED`
        in new-milestone.md and new-project.md are not declared by any registry row).
        """
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = drift.main(["--root", str(ROOT)])
        self.assertEqual(0, code, err.getvalue()[:600])
        self.assertTrue(out.getvalue().startswith("ok check-contract-drift: "))

    def test_real_tree_is_scanned_non_vacuously(self):
        result = drift.collect_violations(ROOT)
        self.assertIsNotNone(result)
        self.assertGreater(result["agents"], 0)
        self.assertGreater(result["markers"], 0)


if __name__ == "__main__":
    unittest.main()
