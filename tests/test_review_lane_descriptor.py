"""Reviewer lane descriptor, lane parity and documentation parity contracts.

Ported from upstream gsd-core tests/review-lane-descriptor.test.cjs and
tests/reviewer-docs-parity.test.cjs (pinned commit d37ff11b4725). Assertions are on
the frozen reason enums, never on rendered prose. The upstream shipped-repo cases
(real review.md, capability registry, docs/ mirrors, review-lane CLI) are replaced by
synthetic fixtures because those surfaces do not exist in this repo; the fast-check
properties are replaced by seeded random generators.
"""
import copy
import importlib.util
import pickle
import random
import sys
import unittest
from pathlib import Path

# `lib` is also a package name under .ai/runtime, which other tests import in the same
# discovery run, so the module is loaded by file path under a private name.
MODULE_PATH = Path(__file__).resolve().parents[1]/"engineer/bin/lib/review_lane_descriptor.py"
_spec = importlib.util.spec_from_file_location("engineer_review_lane_descriptor", MODULE_PATH)
rld = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = rld
_spec.loader.exec_module(rld)

ARGV_PLACEHOLDER = rld.ARGV_PLACEHOLDER
DOCS_PARITY_VIOLATION = rld.DOCS_PARITY_VIOLATION
LANE_SLUG_RE = rld.LANE_SLUG_RE
PARITY_VIOLATION = rld.PARITY_VIOLATION
REVIEWER_LANES = rld.REVIEWER_LANES
check_reviewer_docs_parity = rld.check_reviewer_docs_parity
check_reviewer_lane_parity = rld.check_reviewer_lane_parity
merge_reviewer_lanes = rld.merge_reviewer_lanes

ROSTER = ["claude", "codex", "coderabbit", "opencode", "qwen", "cursor", "antigravity",
          "ollama", "lm_studio", "llama_cpp", "kimi-code"]
HTTP_SLUGS = ["ollama", "lm_studio", "llama_cpp"]
AVAILABILITY = ("gsd_run review-lane availability || printf '"
                + "".join(f"{slug}:missing\\n" for slug in HTTP_SLUGS) + "'")


def workflow(availability=AVAILABILITY, invoke_extra="", eol="\n"):
    text = "\n".join([
        "# Cross-AI Plan Review",
        '<step name="invoke_reviewers">',
        invoke_extra,
        availability,
        "</step>",
        '<step name="write_reviews">',
        "## Consensus Summary",
        "</step>",
        "",
    ])
    return text.replace("\n", eol)


WORKFLOW_TEXT = workflow()


def fake_lane(slug):
    return {**REVIEWER_LANES[0], "slug": slug, "flags": [f"--{slug}"], "reviewsSection": slug}


def check(**overrides):
    data = {"descriptor": REVIEWER_LANES, "roster": ROSTER, "registry": ROSTER, "workflowText": WORKFLOW_TEXT}
    data.update(overrides)
    return check_reviewer_lane_parity(data)


def reasons(result):
    return sorted(f"{v['reason']}:{v['subject']}" for v in result["violations"])


class ShippedLanes(unittest.TestCase):
    def test_shipped_inputs_agree(self):
        result = check()
        self.assertEqual([], result["violations"])
        self.assertTrue(result["ok"])

    def test_descriptor_covers_roster_in_order(self):
        self.assertEqual(ROSTER, [lane["slug"] for lane in REVIEWER_LANES])

    def test_non_empty(self):
        self.assertGreaterEqual(len(REVIEWER_LANES), 11)

    def test_slug_grammar(self):
        for good in ("agy-revisor", "a", "lm_studio", "0x"):
            self.assertTrue(LANE_SLUG_RE.match(good), good)
        for bad in ("../evil", "", "A", "-lead", "_lead", "a.b", "ok\n"):
            self.assertFalse(LANE_SLUG_RE.match(bad), repr(bad))


class DescriptorParity(unittest.TestCase):
    def test_roster_slug_without_descriptor(self):
        self.assertEqual([f"{PARITY_VIOLATION['ROSTER_SLUG_UNDECLARED']}:kimi_code"],
                         reasons(check(roster=[*ROSTER, "kimi_code"])))

    def test_descriptor_lane_absent_from_roster(self):
        result = check(descriptor=[*REVIEWER_LANES, fake_lane("acme")])
        self.assertIn(f"{PARITY_VIOLATION['DESCRIPTOR_LANE_NOT_IN_ROSTER']}:acme", reasons(result))

    def test_registry_lane_without_descriptor(self):
        result = check(registry=[*ROSTER, "acme"])
        self.assertIn(f"{PARITY_VIOLATION['REGISTRY_LANE_UNDECLARED']}:acme", reasons(result))

    def test_descriptor_lane_absent_from_registry(self):
        result = check(descriptor=[*REVIEWER_LANES, fake_lane("acme")], roster=[*ROSTER, "acme"])
        self.assertIn(f"{PARITY_VIOLATION['DESCRIPTOR_LANE_NOT_IN_REGISTRY']}:acme", reasons(result))

    def test_empty_registry_reports_every_lane(self):
        missing = [v for v in check(registry=[])["violations"] if v["reason"] == PARITY_VIOLATION["DESCRIPTOR_LANE_NOT_IN_REGISTRY"]]
        self.assertEqual(len(REVIEWER_LANES), len(missing))

    def test_non_array_registry_degrades_to_violations(self):
        for bad in (None, 42, "gemini", {}):
            self.assertFalse(check(registry=bad)["ok"])
        self.assertFalse(check_reviewer_lane_parity({"descriptor": REVIEWER_LANES, "roster": ROSTER, "workflowText": WORKFLOW_TEXT})["ok"])

    def test_duplicates(self):
        dup = reasons(check(descriptor=[*REVIEWER_LANES, REVIEWER_LANES[0]]))
        self.assertIn(f"{PARITY_VIOLATION['DUPLICATE_SLUG']}:claude", dup)
        flag = reasons(check(descriptor=[*REVIEWER_LANES, {**fake_lane("acme"), "flags": ["--codex"]}]))
        self.assertIn(f"{PARITY_VIOLATION['DUPLICATE_FLAG']}:--codex", flag)
        section = reasons(check(descriptor=[*REVIEWER_LANES, {**fake_lane("acme"), "reviewsSection": "Codex"}]))
        self.assertIn(f"{PARITY_VIOLATION['DUPLICATE_SECTION']}:Codex", section)

    def test_malformed_and_invalid(self):
        for junk, reason in ((0, "MALFORMED_LANE"), ("x", "MALFORMED_LANE"), (None, "MALFORMED_LANE"),
                             (True, "MALFORMED_LANE"), (float("nan"), "MALFORMED_LANE"), ([], "INVALID_SLUG")):
            result = check_reviewer_lane_parity({"descriptor": [junk], "roster": [], "workflowText": ""})
            self.assertIn(PARITY_VIOLATION[reason], [v["reason"] for v in result["violations"]], repr(junk))
        subjects = {v["subject"] for v in check_reviewer_lane_parity({"descriptor": [None, True, float("nan"), 3], "roster": [], "workflowText": ""})["violations"] if v["reason"] == "malformed_lane"}
        self.assertEqual({"null", "true", "NaN", "3"}, subjects)

    def test_non_dict_input_is_total(self):
        for bad in (None, 5, "x", []):
            result = check_reviewer_lane_parity(bad)
            self.assertIsInstance(result["ok"], bool)

    def test_tuple_descriptor_accepted(self):
        self.assertTrue(check(descriptor=tuple(REVIEWER_LANES))["ok"])


class AvailabilityFallback(unittest.TestCase):
    AVAIL = PARITY_VIOLATION["AVAILABILITY_FALLBACK_MISMATCH"]

    def violations(self, result):
        return [v["subject"] for v in result["violations"] if v["reason"] == self.AVAIL]

    def with_http(self, slugs, fallback=None):
        fallback = slugs if fallback is None else fallback
        descriptor = [lane for lane in REVIEWER_LANES if lane["transport"] != "openai-http"]
        descriptor += [{**fake_lane(slug), "transport": "openai-http"} for slug in slugs]
        rows = "".join(f"{slug}:missing\\n" for slug in fallback)
        text = workflow(f"gsd_run review-lane availability || printf '{rows}'")
        return {"descriptor": descriptor, "workflowText": text, "roster": [lane["slug"] for lane in descriptor],
                "registry": [lane["slug"] for lane in descriptor]}

    def test_shipped_fallback_matches_http_lanes(self):
        self.assertEqual([], self.violations(check()))

    def test_stale_row_and_dropped_lane(self):
        text = WORKFLOW_TEXT.replace("llama_cpp:missing", "ghost:missing")
        found = reasons(check(workflowText=text))
        self.assertIn(f"{self.AVAIL}:ghost", found)
        self.assertIn(f"{self.AVAIL}:llama_cpp", found)

    def test_missing_fallback_operator(self):
        text = WORKFLOW_TEXT.replace("review-lane availability ||", "review-lane availability #")
        self.assertIn(f"{self.AVAIL}:no-fallback", reasons(check(workflowText=text)))

    def test_removed_call(self):
        text = "\n".join(line for line in WORKFLOW_TEXT.split("\n") if not line.startswith("gsd_run review-lane"))
        self.assertEqual(["no-call"], self.violations(check(workflowText=text)))

    def test_slug_charset_and_length_bound(self):
        self.assertEqual([], self.violations(check_reviewer_lane_parity(self.with_http(["llama-3_cpp2", "ollama"]))))
        for n in (31, 32):
            self.assertEqual([], self.violations(check_reviewer_lane_parity(self.with_http(["a"*n]))), n)
        self.assertEqual(["a"*33], self.violations(check_reviewer_lane_parity(self.with_http(["a"*33]))))

    def test_dropped_fallback_row_names_that_lane(self):
        rng = random.Random(20260729)
        for _ in range(50):
            slugs = list(dict.fromkeys("".join(rng.choice("abc01_-") for _ in range(rng.randint(1, 8))).lstrip("_-") or "x" for _ in range(rng.randint(1, 4))))
            self.assertEqual([], self.violations(check_reviewer_lane_parity(self.with_http(slugs))))
            self.assertEqual([slugs[0]], self.violations(check_reviewer_lane_parity(self.with_http(slugs, slugs[1:]))))

    def test_comment_or_prose_does_not_shadow_call(self):
        text = WORKFLOW_TEXT.replace("gsd_run review-lane availability",
                                     "# the review-lane availability probe follows\nsee review-lane availability docs\ngsd_run review-lane availability", 1)
        self.assertEqual([], self.violations(check(workflowText=text)))
        stale = text.replace("llama_cpp:missing", "ghost:missing")
        self.assertIn("ghost", self.violations(check(workflowText=stale)))

    def test_crlf(self):
        self.assertEqual([], self.violations(check(workflowText=workflow(eol="\r\n"))))


class AntiParity(unittest.TestCase):
    BESPOKE = PARITY_VIOLATION["BESPOKE_LEG_PRESENT"]

    def test_re_added_leg_marker(self):
        text = workflow(invoke_extra="<!-- reviewer-lane: gemini -->")
        self.assertIn(f"{self.BESPOKE}:gemini", reasons(check(workflowText=text)))

    def test_marker_whitespace_variants(self):
        text = workflow(invoke_extra="<!--reviewer-lane:qwen-->")
        self.assertEqual([f"{self.BESPOKE}:qwen"], reasons(check(workflowText=text)))

    def test_shipped_workflow_has_no_markers(self):
        self.assertEqual([], [v for v in check()["violations"] if v["reason"] == self.BESPOKE])

    def test_marker_outside_invoke_step_is_inert(self):
        text = WORKFLOW_TEXT + "\n<!-- reviewer-lane: gemini -->\n"
        self.assertEqual([], [v for v in check(workflowText=text)["violations"] if v["reason"] == self.BESPOKE])

    def test_crlf_divergence_detected(self):
        text = workflow(invoke_extra="<!-- reviewer-lane: qwen -->", eol="\r\n")
        self.assertEqual([f"{self.BESPOKE}:qwen"], reasons(check(workflowText=text)))

    def test_not_corruption(self):
        extras = [
            WORKFLOW_TEXT.replace("## Consensus Summary", "## Qwen Review (qwen-turbo)\n\n{x}\n\n---\n\n## Consensus Summary"),
            WORKFLOW_TEXT.replace("## Consensus Summary", "## Another Summary\n\n---\n\n## Consensus Summary"),
            workflow(invoke_extra="**Some new maintainer note (#9999):**\n\n```bash\necho hi\n```\n"),
        ]
        for text in extras:
            self.assertEqual([], check(workflowText=text)["violations"])

    def test_non_string_workflow_text_is_coerced(self):
        for bad in (None, 42, {}, [], True):
            result = check(workflowText=bad)
            self.assertIsInstance(result["ok"], bool)
            self.assertEqual([], [v for v in result["violations"] if v["reason"] == self.BESPOKE])

    def test_empty_workflow_reports_no_call_only(self):
        result = check(workflowText="")
        self.assertEqual([f"{AvailabilityFallback.AVAIL}:no-call"], [r for r in reasons(result) if "availability" in r][:1])
        self.assertEqual([], [v for v in result["violations"] if v["reason"] == self.BESPOKE])

    def test_repeated_evaluation_is_stable(self):
        self.assertEqual(check()["violations"], check()["violations"])
        self.assertEqual([], check()["violations"])


def _random_lane_set(rng):
    slugs = []
    while len(slugs) < rng.randint(1, 6):
        slug = rng.choice("abcdefghij") + "".join(rng.choice("abc01_-") for _ in range(rng.randint(0, 12)))
        if slug not in slugs:
            slugs.append(slug)
    return [{
        "slug": slug, "flags": [f"--{slug}"], "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": slug},
        "invoke": {"binary": slug, "args": [], "promptChannel": "stdin", "outputChannel": "stdout",
                   "modelArg": None, "effortChannel": "none"},
        "timeoutFloorMs": 1000, "emptyOutput": "stub-with-stderr", "reviewsSection": f"Sec{i}",
        "evidenceClass": "source-grounded", "requiresBinaries": [], "promptBudgetKey": None, "handler": None,
    } for i, slug in enumerate(slugs)]


NOISE = ["", "**Timeout guidance (#2194):**", "```bash", "```", "# Cross-AI Plan Review - Phase {N}",
         "## Consensus Summary", "### Agreed Concerns", "<!-- not-a-lane-marker: xyz -->", "text, (#1) *_-"]
TRIVIAL = '<step name="invoke_reviewers">\ngsd_run review-lane availability || true\n</step>'


def _doc_for(lanes, noise, eol):
    body = "\n".join([
        '<step name="invoke_reviewers">', "gsd_run review-lane availability || true", *noise,
        "\n".join(f"**{lane['slug']}:**" for lane in lanes),
        "</step>", '<step name="write_reviews">', *noise,
        "\n\n".join(f"## {lane['reviewsSection']} Review" for lane in lanes),
        "## Consensus Summary", "</step>",
    ])
    return body.replace("\n", eol)


class LaneParityProperties(unittest.TestCase):
    def test_total_on_arbitrary_input(self):
        rng = random.Random(20260729)
        atoms = [None, 0, 1, "", "x", True, [], {}, [None], {"slug": "a"}, {"slug": 3, "flags": "x"}, float("nan"), "<step>", ["a", 1]]
        for _ in range(300):
            result = check_reviewer_lane_parity({
                "descriptor": rng.choice(atoms), "roster": rng.choice(atoms), "workflowText": rng.choice(atoms)})
            self.assertEqual(result["ok"], len(result["violations"]) == 0)

    def test_bad_slug_is_named(self):
        for bad in ("a.b", "a*b", "a+b", "(a)", "[a]", "a|b", "A", "-lead", "_lead", "__proto__", ""):
            result = check_reviewer_lane_parity({
                "descriptor": [{**fake_lane("placeholder"), "slug": bad}], "roster": [bad], "registry": [bad], "workflowText": TRIVIAL})
            self.assertIn(PARITY_VIOLATION["INVALID_SLUG"], [v["reason"] for v in result["violations"]], repr(bad))

    def test_prototype_like_slugs_are_ordinary(self):
        for name in ("constructor", "tostring", "valueof", "hasownproperty", "__class__"[2:-2]):
            lane = {**fake_lane("placeholder"), "slug": name, "reviewsSection": "Sec"}
            declared = check_reviewer_lane_parity({"descriptor": [lane], "roster": [name], "registry": [name], "workflowText": TRIVIAL})
            absent = check_reviewer_lane_parity({"descriptor": [lane], "roster": [name], "registry": [], "workflowText": TRIVIAL})
            self.assertTrue(declared["ok"], name)
            self.assertIn({"reason": PARITY_VIOLATION["DESCRIPTOR_LANE_NOT_IN_REGISTRY"], "subject": name}, absent["violations"])

    def test_document_declaring_exactly_the_descriptor_satisfies_parity(self):
        rng = random.Random(1)
        for _ in range(100):
            lanes = _random_lane_set(rng)
            noise = [rng.choice(NOISE) for _ in range(rng.randint(0, 12))]
            doc = _doc_for(lanes, noise, rng.choice(["\n", "\r\n"]))
            slugs = [lane["slug"] for lane in lanes]
            result = check_reviewer_lane_parity({"descriptor": lanes, "roster": slugs, "registry": slugs, "workflowText": doc})
            self.assertTrue(result["ok"], result["violations"])

    def test_dropping_one_lane_from_registry_names_exactly_it(self):
        rng = random.Random(2)
        for _ in range(100):
            lanes = _random_lane_set(rng)
            victim = rng.choice(lanes)["slug"]
            slugs = [lane["slug"] for lane in lanes]
            result = check_reviewer_lane_parity({
                "descriptor": lanes, "roster": slugs, "registry": [s for s in slugs if s != victim], "workflowText": TRIVIAL})
            self.assertEqual([{"reason": PARITY_VIOLATION["DESCRIPTOR_LANE_NOT_IN_REGISTRY"], "subject": victim}], result["violations"])

    def test_determinism(self):
        rng = random.Random(3)
        for _ in range(50):
            lanes = _random_lane_set(rng)
            slugs = [lane["slug"] for lane in lanes]
            data = {"descriptor": lanes, "roster": slugs, "registry": slugs,
                    "workflowText": _doc_for(lanes, [rng.choice(NOISE) for _ in range(6)], "\n")}
            self.assertEqual(check_reviewer_lane_parity(data), check_reviewer_lane_parity(data))


class DeclaredShape(unittest.TestCase):
    def test_transport_is_lane_level(self):
        for lane in REVIEWER_LANES:
            self.assertIn(lane["transport"], ("spawn", "openai-http"), lane["slug"])
            self.assertNotIn("transport", lane["invoke"], lane["slug"])

    def test_transport_sub_shape(self):
        for lane in REVIEWER_LANES:
            invoke = lane["invoke"]
            if lane["transport"] == "spawn":
                self.assertTrue(invoke["binary"])
                self.assertIsInstance(invoke["args"], list)
                self.assertNotIn("hostConfigKey", invoke)
            else:
                self.assertTrue(invoke["hostConfigKey"])
                self.assertTrue(invoke["path"])
                self.assertTrue(invoke["defaultHost"])
                self.assertNotIn("binary", invoke)
                self.assertEqual("none", invoke["effortChannel"])

    def test_probe_kinds_and_bounds(self):
        for lane in REVIEWER_LANES:
            probe = lane["probe"]
            self.assertIn(probe["kind"], ("command-exists", "command-capability", "http-reachable"))
            if probe["kind"] != "command-exists":
                self.assertIsInstance(probe["timeoutMs"], int)
                self.assertGreater(probe["timeoutMs"], 0)

    def test_handlers(self):
        for lane in REVIEWER_LANES:
            self.assertIn(lane["handler"], (None, "antigravity", "openai-compatible", "opencode"))
        self.assertEqual(["antigravity", "llama_cpp", "lm_studio", "ollama", "opencode"],
                         sorted(lane["slug"] for lane in REVIEWER_LANES if lane["handler"] is not None))

    def test_timeouts_and_empty_output(self):
        for lane in REVIEWER_LANES:
            self.assertIsInstance(lane["timeoutFloorMs"], int)
            self.assertGreater(lane["timeoutFloorMs"], 0)
        self.assertEqual(["antigravity"], [lane["slug"] for lane in REVIEWER_LANES if lane["emptyOutput"] != "stub-with-stderr"])

    def test_flag_uniqueness_with_multi_flag_lane(self):
        flags = [flag for lane in REVIEWER_LANES for flag in lane["flags"]]
        self.assertEqual(len(flags), len(set(flags)))
        self.assertTrue(any(len(lane["flags"]) > 1 for lane in REVIEWER_LANES))
        self.assertEqual(["--antigravity", "--agy"], next(l for l in REVIEWER_LANES if l["slug"] == "antigravity")["flags"])

    def test_section_uniqueness(self):
        sections = [lane["reviewsSection"] for lane in REVIEWER_LANES]
        self.assertEqual(len(sections), len(set(sections)))

    def test_reason_enums_locked(self):
        self.assertEqual(["AVAILABILITY_FALLBACK_MISMATCH", "BESPOKE_LEG_PRESENT", "DESCRIPTOR_LANE_NOT_IN_REGISTRY",
                          "DESCRIPTOR_LANE_NOT_IN_ROSTER", "DUPLICATE_FLAG", "DUPLICATE_SECTION", "DUPLICATE_SLUG",
                          "INVALID_SLUG", "MALFORMED_LANE", "REGISTRY_LANE_UNDECLARED", "ROSTER_SLUG_UNDECLARED"],
                         sorted(PARITY_VIOLATION))
        self.assertEqual(["DOC_FLAG_MISSING", "DOC_FLAG_UNDECLARED", "DOC_TITLE_MISSING", "DOC_UNREADABLE",
                          "MALFORMED_LANE", "SIGNATURE_FLAG_MISSING", "TABLE_ROW_MISSING"], sorted(DOCS_PARITY_VIOLATION))

    def test_argv_placeholder_vocabulary(self):
        self.assertEqual({"MODEL": "{{model}}", "EFFORT": "{{effort}}", "OUTPUT": "{{output}}",
                          "PROMPT": "{{prompt}}", "NATIVE_TIMEOUT": "{{nativeTimeout}}"}, ARGV_PLACEHOLDER)
        known = set(ARGV_PLACEHOLDER.values())
        for lane in REVIEWER_LANES:
            if lane["transport"] != "spawn":
                continue
            for token in lane["invoke"]["args"]:
                if token.startswith("{{"):
                    self.assertIn(token, known, lane["slug"])
        by_slug = {lane["slug"]: lane for lane in REVIEWER_LANES}
        self.assertEqual(["exec", "--ephemeral", "{{model}}", "{{effort}}", "--skip-git-repo-check", "{{output}}", "-"],
                         by_slug["codex"]["invoke"]["args"])
        self.assertEqual("-o", by_slug["codex"]["invoke"]["outputArg"])
        self.assertEqual("file-arg", by_slug["codex"]["invoke"]["outputChannel"])
        self.assertEqual("review.models.agy", by_slug["antigravity"]["modelConfigKey"])
        self.assertIn(ARGV_PLACEHOLDER["NATIVE_TIMEOUT"], by_slug["antigravity"]["invoke"]["args"])
        self.assertEqual("command-capability", by_slug["kimi-code"]["probe"]["kind"])
        self.assertEqual({"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}, by_slug["claude"]["invoke"]["env"])
        self.assertEqual("diff-only", by_slug["coderabbit"]["evidenceClass"])
        self.assertEqual(1_200_000, by_slug["claude"]["timeoutFloorMs"])
        self.assertEqual(360_000, by_slug["coderabbit"]["timeoutFloorMs"])
        self.assertEqual("http://localhost:11434", by_slug["ollama"]["invoke"]["defaultHost"])
        self.assertEqual("llama.cpp", by_slug["llama_cpp"]["reviewsSection"])

    def test_tables_are_frozen(self):
        with self.assertRaises(TypeError):
            REVIEWER_LANES.append({})
        with self.assertRaises(TypeError):
            REVIEWER_LANES[0] = {}
        with self.assertRaises(TypeError):
            REVIEWER_LANES[0]["slug"] = "x"
        with self.assertRaises(TypeError):
            PARITY_VIOLATION["NEW"] = "x"
        with self.assertRaises(TypeError):
            ARGV_PLACEHOLDER["MODEL"] = "x"
        with self.assertRaises(TypeError):
            DOCS_PARITY_VIOLATION.update({"A": "b"})

    def test_frozen_tables_copy_and_serialize_as_plain_containers(self):
        import json
        for clone in (copy.copy(REVIEWER_LANES[0]), copy.deepcopy(REVIEWER_LANES[0]), pickle.loads(pickle.dumps(REVIEWER_LANES[0]))):
            self.assertEqual(REVIEWER_LANES[0], clone)
            clone["slug"] = "mutable"
        self.assertEqual(type(copy.deepcopy(REVIEWER_LANES)), list)
        self.assertEqual(REVIEWER_LANES[0], json.loads(json.dumps(REVIEWER_LANES[0])))
        self.assertEqual({**REVIEWER_LANES[0]}["slug"], "claude")

    def test_effort_declarations(self):
        rank = ["minimal", "low", "medium", "high", "xhigh", "max"]
        for lane in REVIEWER_LANES:
            slug = lane["slug"]
            if lane["invoke"]["effortChannel"] == "argv":
                self.assertEqual(f"review.effort.{slug}", lane["effortConfigKey"])
                self.assertIsInstance(lane["defaultEffort"], str)
            else:
                self.assertIsNone(lane["effortConfigKey"], slug)
                self.assertIsNone(lane["defaultEffort"], slug)
            if lane["defaultEffort"] is not None:
                self.assertEqual("source-grounded", lane["evidenceClass"])
                self.assertGreaterEqual(rank.index(lane["defaultEffort"]), rank.index("high"))
            self.assertNotEqual("inherit", lane["defaultEffort"])


FP = list(REVIEWER_LANES[:2])


def overlay_lane(**overrides):
    return {
        "slug": "agy-revisor", "flags": ["--agy-revisor"], "transport": "spawn",
        "probe": {"kind": "command-exists", "binary": "agy"},
        "invoke": {"binary": "agy", "args": ["--agent", "revisor-gsd", "{{model}}", "-p", "{{prompt}}"],
                   "promptChannel": "argv-file-ref", "outputChannel": "stdout", "modelArg": "--model", "effortChannel": "none"},
        "timeoutFloorMs": 600000, "emptyOutput": "handler-owned", "reviewsSection": "Antigravity revisor-gsd",
        "evidenceClass": "source-grounded", "requiresBinaries": [], "promptBudgetKey": None,
        "modelConfigKey": "review.models.agy-revisor", "handler": "antigravity", **overrides,
    }


def reviewer_cap(body):
    ident = body["slug"] if isinstance(body, dict) and body.get("slug") else "x"
    return {"id": ident, "role": "reviewer", "reviewer": body}


def registry(*caps):
    return {"capabilities": {cap["id"]: cap for cap in caps}}


class MergeReviewerLanes(unittest.TestCase):
    def test_overlay_absent_returns_first_party_by_identity(self):
        merged = merge_reviewer_lanes(FP, registry())
        self.assertEqual(["claude", "codex"], [lane["slug"] for lane in merged])
        self.assertIs(FP[0], merged[0])
        self.assertIs(FP[1], merged[1])
        self.assertIsNot(FP, merged)

    def test_overlay_lane_included(self):
        merged = merge_reviewer_lanes(FP, registry(reviewer_cap(overlay_lane())))
        slugs = [lane["slug"] for lane in merged]
        self.assertEqual(["claude", "codex", "agy-revisor"], slugs)
        overlay = merged[2]
        self.assertEqual("Antigravity revisor-gsd", overlay["reviewsSection"])
        self.assertEqual(["--agy-revisor"], overlay["flags"])

    def test_first_party_wins_on_collision(self):
        merged = merge_reviewer_lanes(FP, registry(reviewer_cap(overlay_lane(slug="claude", reviewsSection="EVIL CLAUDE"))))
        self.assertIs(FP[0], merged[0])
        self.assertEqual(len(FP), len(merged))
        self.assertNotEqual("EVIL CLAUDE", merged[0]["reviewsSection"])

    def test_runtime_cap_adds_no_lane(self):
        runtime = {"id": "some-runtime", "role": "runtime", "runtime": {"hostBehaviors": {"reviewerCli": True}}}
        self.assertEqual(["claude", "codex"], [l["slug"] for l in merge_reviewer_lanes(FP, registry(runtime))])

    def test_empty_slug_skipped(self):
        for slug in ("   ", "", None, 5):
            merged = merge_reviewer_lanes(FP, registry(reviewer_cap(overlay_lane(slug=slug))))
            self.assertEqual(["claude", "codex"], [l["slug"] for l in merged], repr(slug))

    def test_invalid_grammar_slug_skipped(self):
        for slug in ("../evil", "Bad", "a.b"):
            merged = merge_reviewer_lanes(FP, registry(reviewer_cap(overlay_lane(slug=slug))))
            self.assertEqual(2, len(merged), slug)

    def test_slug_is_trimmed_on_stored_lane(self):
        merged = merge_reviewer_lanes(FP, registry(reviewer_cap(overlay_lane(slug="  trimmed  "))))
        self.assertEqual("trimmed", merged[2]["slug"])

    def test_two_overlays_and_duplicate_overlay(self):
        a = reviewer_cap(overlay_lane(slug="alpha-lane", reviewsSection="Alpha"))
        b = reviewer_cap(overlay_lane(slug="beta-lane", reviewsSection="Beta"))
        merged = merge_reviewer_lanes(FP, registry(a, b))
        self.assertEqual(["claude", "codex", "alpha-lane", "beta-lane"], [l["slug"] for l in merged])
        later = {"id": "beta2", "role": "reviewer", "reviewer": overlay_lane(slug="alpha-lane", reviewsSection="Other")}
        merged = merge_reviewer_lanes(FP, {"capabilities": {"a": a, "later": later}})
        self.assertEqual("Alpha", merged[2]["reviewsSection"])
        self.assertEqual(3, len(merged))

    def test_malformed_bodies_and_registries_skipped(self):
        caps = [{"id": "n", "role": "reviewer", "reviewer": None}, {"id": "a", "role": "reviewer", "reviewer": []},
                {"id": "s", "role": "reviewer", "reviewer": "not-an-object"}, None, "cap", [], 7]
        merged = merge_reviewer_lanes(FP, {"capabilities": dict(enumerate(caps))})
        self.assertEqual(["claude", "codex"], [l["slug"] for l in merged])
        for bad in (None, {}, {"capabilities": None}, {"capabilities": "x"}, "x", 5):
            self.assertEqual(2, len(merge_reviewer_lanes(FP, bad)), repr(bad))

    def test_first_party_blank_slug_dropped_and_deduped(self):
        merged = merge_reviewer_lanes([{"slug": " "}, FP[0], FP[0], "junk", {"slug": 3}], registry())
        self.assertEqual([FP[0]], merged)
        self.assertEqual([], merge_reviewer_lanes(None, None))

    def test_overlay_body_not_mutated(self):
        body = overlay_lane(slug=" spaced ")
        merge_reviewer_lanes(FP, registry(reviewer_cap(body)))
        self.assertEqual(" spaced ", body["slug"])


# ---- documentation parity -------------------------------------------------- #

ALL_FLAGS = [flag for lane in REVIEWER_LANES for flag in lane["flags"]]
ALL_TITLES = [lane["reviewsSection"] for lane in REVIEWER_LANES]


def backtick_all(flags):
    return " ".join(f"`{f}`" for f in flags)


def bracket_all(flags):
    return " ".join(f"[{f}]" for f in flags)


def commands_doc(flags):
    return "\n".join(["### `/gsd-review`", "", f"Reviewer flags: {backtick_all(flags)}", ""])


def features_doc(sig_flags=None, titles=None, blanks=1):
    sig_flags = ALL_FLAGS if sig_flags is None else sig_flags
    titles = ALL_TITLES if titles is None else titles
    lines = [f"**Command:** `/gsd-review --phase N {bracket_all(sig_flags)} [--all]`"]
    lines += [""] * blanks
    lines.append(f"**Purpose:** Invoke {', '.join(titles)} to independently review phase plans.")
    return "\n".join(lines)


def docs_check(docs, descriptor=REVIEWER_LANES):
    return check_reviewer_docs_parity({"descriptor": descriptor, "docs": docs})


def v(reason, doc, subject):
    return {"reason": DOCS_PARITY_VIOLATION[reason], "doc": doc, "subject": subject}


def without(*dropped):
    return [flag for flag in ALL_FLAGS if flag not in dropped]


class DocsFlagArm(unittest.TestCase):
    def test_clean(self):
        result = docs_check({"d": commands_doc(ALL_FLAGS)})
        self.assertTrue(result["ok"])
        self.assertEqual([], result["violations"])
        self.assertEqual([], result["skipped"])

    def test_missing_flag(self):
        self.assertEqual([v("DOC_FLAG_MISSING", "d", "--kimi-code")], docs_check({"d": commands_doc(without("--kimi-code"))})["violations"])

    def test_every_missing_flag_named(self):
        result = docs_check({"d": commands_doc(without("--codex", "--qwen"))})
        self.assertEqual(["--codex", "--qwen"], sorted(x["subject"] for x in result["violations"]))

    def test_no_flags_reports_every_lane(self):
        result = docs_check({"d": "### `/gsd-review`\n\nSome prose with no flags.\n"})
        self.assertEqual(len(ALL_FLAGS), len(result["violations"]))
        self.assertTrue(all(x["reason"] == "doc_flag_missing" for x in result["violations"]))

    def test_dual_flag_lane_alias_caught(self):
        self.assertEqual([v("DOC_FLAG_MISSING", "d", "--agy")], docs_check({"d": commands_doc(without("--agy"))})["violations"])

    def test_bracketed_flags_satisfy(self):
        doc = f"### `/gsd-review`\n\nReviewer flags: [--codex] {backtick_all(without('--codex'))}\n"
        self.assertTrue(docs_check({"d": doc})["ok"])

    def test_flag_outside_section_does_not_satisfy(self):
        doc = f"### `/gsd-review`\n\nReviewer flags: {backtick_all(without('--codex'))}\n\n```bash\n/gsd-plan-review-convergence 3 --codex\n```\n"
        self.assertEqual([v("DOC_FLAG_MISSING", "d", "--codex")], docs_check({"d": doc})["violations"])

    def test_token_matching_is_bounded(self):
        doc = commands_doc(without("--claude")) + "\n`--claude-foo`\n"
        self.assertEqual([v("DOC_FLAG_MISSING", "d", "--claude")], docs_check({"d": doc})["violations"])

    def test_translated_description_ok(self):
        self.assertTrue(docs_check({"d": f"### `/gsd-review`\n\nInvoca CLIs de IA externas: {backtick_all(ALL_FLAGS)}\n"})["ok"])

    def test_colon_command_form_recognised(self):
        self.assertEqual([], docs_check({"d": "### `/gsd:review`\n\n" + backtick_all(ALL_FLAGS)})["skipped"])


class DocsSignatureArm(unittest.TestCase):
    def doc(self, sig, extra=""):
        return "\n".join([backtick_all(ALL_FLAGS), "", sig, "", f"**Purpose:** {', '.join(ALL_TITLES)}.{extra}"])

    def test_signature_held_to_full_roster(self):
        result = docs_check({"d": self.doc("**Command:** `/gsd-review --phase N [--codex] [--all]`")})
        omitted = without("--codex")
        self.assertEqual(sorted(omitted), sorted(x["subject"] for x in result["violations"]))
        self.assertTrue(all(x["reason"] == "signature_flag_missing" for x in result["violations"]))

    def test_undeclared_bracketed_flag(self):
        sig = f"**Command:** `/gsd-review --phase N {bracket_all(ALL_FLAGS)} [--acme] [--acme] [--all]`"
        self.assertEqual([v("DOC_FLAG_UNDECLARED", "d", "--acme")], docs_check({"d": self.doc(sig)})["violations"])

    def test_all_is_inert(self):
        sig = f"**Command:** `/gsd-review --phase N {bracket_all(ALL_FLAGS)} [--all]`"
        self.assertTrue(docs_check({"d": self.doc(sig)})["ok"])

    def test_no_signature_skips_arm(self):
        doc = f"| Command | Description |\n| --- | --- |\n| /gsd-review | {backtick_all(ALL_FLAGS)} |\n"
        self.assertTrue(docs_check({"d": doc})["ok"])


class DocsTitleArm(unittest.TestCase):
    def titles(self, doc):
        return [x for x in docs_check({"d": doc})["violations"] if x["reason"] == "doc_title_missing"]

    def test_clean(self):
        self.assertEqual([], self.titles(features_doc()))
        self.assertTrue(docs_check({"d": features_doc()})["ok"])

    def test_purpose_drift(self):
        self.assertEqual([v("DOC_TITLE_MISSING", "d", "Kimi Code")], self.titles(features_doc(titles=[t for t in ALL_TITLES if t != "Kimi Code"])))

    def test_titles_literal_not_regex(self):
        titles = ["llamaXcpp" if t == "llama.cpp" else t for t in ALL_TITLES]
        self.assertEqual([v("DOC_TITLE_MISSING", "d", "llama.cpp")], self.titles(features_doc(titles=titles)))

    def test_blank_lines_skipped(self):
        self.assertEqual([], self.titles(features_doc(blanks=3)))

    def test_signature_last_line_skips_title_arm_only(self):
        doc = "\n".join([backtick_all(ALL_FLAGS), "", f"**Command:** `/gsd-review --phase N {bracket_all(ALL_FLAGS)} [--all]`"])
        result = docs_check({"d": doc})
        self.assertTrue(result["ok"], result["violations"])


class DocsTableRowArm(unittest.TestCase):
    def rows(self, lanes):
        return [f"| {' / '.join(f'`{f}`' for f in l['flags'])} | {l['reviewsSection']} review |" for l in lanes]

    def test_deleted_row_caught_despite_forwarding_row(self):
        lanes = [l for l in REVIEWER_LANES if l["slug"] != "kimi-code"]
        doc = "\n".join(["### `/gsd-review`", "", "| Flag | Description | Notes |", "| --- | --- | --- |",
                         f"| Reviewer flags | No | {backtick_all(ALL_FLAGS)} |", *self.rows(lanes), ""])
        found = [x for x in docs_check({"d": doc})["violations"] if x["reason"] == "table_row_missing"]
        self.assertEqual([v("TABLE_ROW_MISSING", "d", "--kimi-code")], found)

    def test_dual_flag_row_satisfies_both(self):
        doc = "\n".join(["### `/gsd-review`", "", "| Flag | Description |", "| --- | --- |", *self.rows(REVIEWER_LANES), ""])
        self.assertEqual([], [x for x in docs_check({"d": doc})["violations"] if x["reason"] == "table_row_missing"])

    def test_forwarding_row_alone_is_not_a_lane_table(self):
        doc = "\n".join(["### `/gsd-review`", "", "| Flag | Description | Notes |", "| --- | --- | --- |",
                         f"| Reviewer flags | No | {backtick_all(ALL_FLAGS)} |", ""])
        self.assertEqual([], [x for x in docs_check({"d": doc})["violations"] if x["reason"] == "table_row_missing"])

    def test_features_shaped_doc_unaffected(self):
        self.assertTrue(docs_check({"d": features_doc()})["ok"])


class DocsCombination(unittest.TestCase):
    def test_clean_does_not_mask_dirty(self):
        result = docs_check({"docs/COMMANDS.md": commands_doc(ALL_FLAGS), "docs/ja-JP/COMMANDS.md": commands_doc(without("--codex"))})
        self.assertEqual([v("DOC_FLAG_MISSING", "docs/ja-JP/COMMANDS.md", "--codex")], result["violations"])

    def test_flag_and_title_violations_coexist(self):
        doc = features_doc(sig_flags=without("--qwen"), titles=[t for t in ALL_TITLES if t != "Qwen"])
        found = [x["reason"] for x in docs_check({"d": doc})["violations"]]
        self.assertIn("doc_flag_missing", found)
        self.assertIn("doc_title_missing", found)

    def test_absent_section_skips_without_disabling_others(self):
        result = docs_check({"skip": "# Some other doc\n\nNothing about reviewers here.\n", "clean": commands_doc(ALL_FLAGS),
                             "dirty": commands_doc(without("--cursor"))})
        self.assertEqual(["skip"], result["skipped"])
        self.assertEqual([v("DOC_FLAG_MISSING", "dirty", "--cursor")], result["violations"])


class DocsCommentStripping(unittest.TestCase):
    ROWS = [f"| `{f}` | d |" for f in without("--kimi-code")]

    def kimi(self, *lines):
        doc = "\n".join(["### `/gsd-review`", "", *self.ROWS, "", *lines, ""])
        return [x for x in docs_check({"d": doc})["violations"] if x["subject"] == "--kimi-code"]

    def test_nested_comment_cannot_smuggle_flag(self):
        found = self.kimi("<!-<!--DUMMY-->-| `--kimi-code` | d |-->")
        self.assertTrue([x for x in found if x["reason"] in ("doc_flag_missing", "table_row_missing")])

    def test_unterminated_opener_swallows_rest(self):
        self.assertTrue(self.kimi("<!-- open, never closed", "| `--kimi-code` | d |"))

    def test_comment_closed_on_later_line_resumes(self):
        self.assertEqual([], self.kimi("<!-- opening", "hidden line", "-->", "| `--kimi-code` | d |"))

    def test_multiple_comments_on_one_line(self):
        self.assertTrue(self.kimi("A <!-- first --> B <!-- | `--kimi-code` | d | -->"))

    def test_fenced_blocks_are_not_documentation(self):
        self.assertTrue(self.kimi("```", "| `--kimi-code` | d |", "```"))
        self.assertTrue(self.kimi("~~~md", "| `--kimi-code` | d |", "~~~"))

    def test_only_mention_inside_fence_is_skipped(self):
        result = docs_check({"d": "```\n/gsd-review\n```\n"})
        self.assertEqual(["d"], result["skipped"])


class DocsHostileInput(unittest.TestCase):
    def test_empty_docs_not_clean(self):
        result = docs_check({})
        self.assertFalse(result["ok"])
        self.assertEqual(len(ALL_FLAGS), len(result["violations"]))
        self.assertTrue(all(x["reason"] == "doc_flag_missing" and x["doc"] == "(no documents supplied)" for x in result["violations"]))

    def test_absent_docs_degrades(self):
        result = check_reviewer_docs_parity({"descriptor": REVIEWER_LANES})
        self.assertFalse(result["ok"])
        self.assertIsInstance(result["violations"], list)

    def test_non_string_values_reported(self):
        for bad, kind in ((None, "object"), (0, "number"), ([], "object"), ({}, "object"), (True, "boolean")):
            result = docs_check({"bad": bad})
            self.assertEqual([v("DOC_UNREADABLE", "bad", kind)], result["violations"], repr(bad))
            self.assertNotIn("bad", result["skipped"])

    def test_empty_string_skipped_but_non_string_is_not(self):
        self.assertEqual(["empty"], docs_check({"empty": ""})["skipped"])
        self.assertEqual([], docs_check({"bad": None})["skipped"])

    def test_unreadable_never_masks_real_violation(self):
        result = docs_check({"bad": None, "good": commands_doc(without("--kimi-code"))})
        self.assertEqual([v("DOC_UNREADABLE", "bad", "object"), v("DOC_FLAG_MISSING", "good", "--kimi-code")], result["violations"])

    def test_non_array_descriptor_is_total(self):
        result = docs_check({"d": commands_doc(ALL_FLAGS)}, descriptor="nope")
        self.assertIsInstance(result["ok"], bool)

    def test_malformed_lane_named(self):
        result = docs_check({"d": commands_doc(ALL_FLAGS)}, descriptor=[None, "not-an-object", *REVIEWER_LANES])
        malformed = [x for x in result["violations"] if x["reason"] == "malformed_lane"]
        self.assertEqual([v("MALFORMED_LANE", "(descriptor)", "null"), v("MALFORMED_LANE", "(descriptor)", "not-an-object")], malformed)

    def test_non_dict_input_is_total(self):
        for bad in (None, 3, "x"):
            result = check_reviewer_docs_parity(bad)
            # No descriptor and no docs declares nothing to violate, exactly as upstream.
            self.assertEqual(result["ok"], len(result["violations"]) == 0)
            self.assertIsInstance(result["violations"], list)

    def test_prototype_slug_is_inert(self):
        proto = {**REVIEWER_LANES[0], "slug": "__proto__", "flags": ["--proto-lane"]}
        result = docs_check({"d": commands_doc([*ALL_FLAGS, "--proto-lane"])}, descriptor=[*REVIEWER_LANES, proto])
        self.assertTrue(result["ok"])

    def test_crlf_insensitive(self):
        doc = commands_doc(ALL_FLAGS)
        self.assertEqual(docs_check({"d": doc}), docs_check({"d": doc.replace("\n", "\r\n")}))
        crlf = commands_doc(without("--kimi-code")).replace("\n", "\r\n")
        self.assertEqual([v("DOC_FLAG_MISSING", "d", "--kimi-code")], docs_check({"d": crlf})["violations"])

    def test_stable_and_order_independent(self):
        dirty, clean = commands_doc(without("--codex")), commands_doc(ALL_FLAGS)
        self.assertEqual(docs_check({"a": dirty, "b": clean}), docs_check({"a": dirty, "b": clean}))
        forward = docs_check({"a": dirty, "b": clean})
        reverse = docs_check({"b": clean, "a": dirty})
        self.assertEqual(sorted(map(str, forward["violations"])), sorted(map(str, reverse["violations"])))

    def test_total_on_arbitrary_input(self):
        rng = random.Random(20260730)
        atoms = [None, 0, "", "x", True, [], {}, [None], {"slug": "a"}, "/gsd-review [--a]", float("nan"), ["a"]]
        for _ in range(300):
            docs = {"k" + str(i): rng.choice(atoms) for i in range(rng.randint(0, 3))} if rng.random() < .8 else rng.choice(atoms)
            result = check_reviewer_docs_parity({"descriptor": rng.choice(atoms), "docs": docs})
            self.assertEqual(result["ok"], len(result["violations"]) == 0)
            self.assertIsInstance(result["skipped"], list)

    def test_pathologically_long_declared_strings(self):
        lane = {"slug": "pathological", "flags": ["--" + "a" * 200000], "reviewsSection": "T" * 200000}
        result = docs_check({"d": "/gsd-review some prose mentioning the command."}, descriptor=[lane])
        self.assertIsInstance(result["ok"], bool)
        self.assertIsInstance(result["violations"], list)


class PrivateHelpers(unittest.TestCase):
    def test_split_lines_matches_upstream_contract(self):
        self.assertEqual([""], rld._split_lines(""))
        self.assertEqual(["a", "b", ""], rld._split_lines("a\r\nb\n"))
        self.assertEqual(["a\rb"], rld._split_lines("a\rb"))
        with self.assertRaises(TypeError):
            rld._split_lines(5)

    def test_js_string_and_typeof(self):
        self.assertEqual("1", rld._js_string(1.0))
        self.assertEqual("1.5", rld._js_string(1.5))
        self.assertEqual("1,2", rld._js_string([1, 2]))
        self.assertEqual("[object Object]", rld._js_string({}))
        self.assertEqual("undefined", rld._js_string(rld._UNDEFINED))
        self.assertEqual("Infinity", rld._js_string(float("inf")))
        self.assertEqual("function", rld._js_typeof(len))
        self.assertEqual("undefined", rld._js_typeof(rld._UNDEFINED))


if __name__ == "__main__":
    unittest.main()
