"""Ports of the upstream prohibition-enforcement tests for engineer/bin/lib/prohibition_probe.py.

Upstream sources: tests/prohibition-enforcement.test.cjs, prohibition-enforcement.property.test.cjs,
prohibition-probe.validators/verify-tier/schema.test.cjs and gate-prohibition-enforcement.unit.test.cjs.

The real runners spawn ``node`` and eslint. Those suites run here against a fake ``node`` placed on
PATH (it prints TAP / eslint JSON driven by small spec files), so the default runner, prover, timeout
bound and process-tree reaping are exercised without a Node install; a few tests also run against a
real ``node`` when one is installed.
"""
import contextlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT/"engineer/bin/lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package (another ``lib`` package exists under .ai/runtime)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib."+name)


pp = _load("prohibition_probe")
pc = _load("probe_core")

TEST_TIER = {"requirement_id": "R1", "category": "safety", "status": "resolved", "verification": "test", "resolution": None,
             "reason": None, "statement": "MUST NOT read source files and text-search them in tests"}
PROVEN = {"provenFailFirst": True, "method": "violation-fixture"}
NODE_CHECK = {"kind": "node-test", "target": "tests/neg.test.cjs", "failFirst": True}
HAS_REAL_NODE = shutil.which("node") is not None


def passing(_check):
    return {"passed": True}


def failing(_check):
    return {"passed": False}


def proving(_check):
    return dict(PROVEN)


def not_proving(_check):
    return {"provenFailFirst": False}


def enforce(check, **options):
    return pp.run_prohibition_enforcement(TEST_TIER, check, **options)


class ProducerDecisionTests(unittest.TestCase):
    def test_locate_miss_fails_closed(self):
        result = enforce(None, run_check=passing)
        self.assertEqual((False, True, None, []), (result["located"], result["flagged"], result["kind"], result["evidence"]))
        self.assertNotEqual("green", result["status"])

    def test_malformed_descriptors_are_not_located(self):
        for check in ({"kind": "node-test"}, {"kind": "node-test", "target": "   "}, {"kind": "node-test", "target": 5},
                      {"kind": "lint-rule", "target": "tests/", "failFirst": True}, {"kind": "lint-rule", "target": "tests/", "rule": " "},
                      {"kind": "other", "target": "t"}, "node-test", 7, [], {}):
            with self.subTest(check=check):
                result = enforce(check, run_check=passing, prove_fail_first=proving)
                self.assertEqual((False, True), (result["located"], result["flagged"]))
                self.assertNotEqual("green", result["status"])
                self.assertEqual([], result["evidence"])

    def test_node_test_proven_and_passing_is_green(self):
        result = enforce(NODE_CHECK, run_check=passing, prove_fail_first=proving)
        self.assertEqual(("green", False, "test", True, "node-test"), (result["status"], result["flagged"], result["tier"], result["located"], result["kind"]))
        self.assertEqual([{"kind": "node-test", "target": "tests/neg.test.cjs", "failFirst": True, "passed": True, "failFirstProof": "violation-fixture"}], result["evidence"])

    def test_lint_rule_evidence_carries_rule(self):
        result = enforce({"kind": "lint-rule", "rule": "local/no-source-grep", "target": "tests/", "failFirst": True}, run_check=passing, prove_fail_first=proving)
        self.assertEqual(("green", "lint-rule"), (result["status"], result["kind"]))
        self.assertEqual(("local/no-source-grep", "tests/"), (result["evidence"][0]["rule"], result["evidence"][0]["target"]))

    def test_proof_without_a_method_omits_failfirstproof(self):
        result = enforce(NODE_CHECK, run_check=passing, prove_fail_first=lambda check: {"provenFailFirst": True})
        self.assertEqual("green", result["status"])
        self.assertNotIn("failFirstProof", result["evidence"][0])

    def test_failing_check_hard_gates_in_both_modes(self):
        for mode in ("interactive", "autonomous"):
            result = enforce(NODE_CHECK, run_check=failing, prove_fail_first=proving, mode=mode)
            self.assertEqual((True, True, [], mode), (result["flagged"], result["located"], result["evidence"], result["mode"]))
            self.assertNotEqual("green", result["status"])

    def test_attestation_alone_never_greens(self):
        for prover in (not_proving, lambda check: {}, lambda check: {"provenFailFirst": "yes"}, lambda check: None):
            result = enforce(NODE_CHECK, run_check=passing, prove_fail_first=prover)
            self.assertNotEqual("green", result["status"])
            self.assertEqual((True, True), (result["flagged"], result["located"]))
        self.assertNotEqual("green", enforce({**NODE_CHECK, "failFirst": False}, run_check=passing)["status"])

    def test_non_true_run_results_never_green(self):
        for outcome in ({"passed": "true"}, {}, None, {"passed": 1}):
            self.assertNotEqual("green", enforce(NODE_CHECK, run_check=lambda check, o=outcome: o, prove_fail_first=proving)["status"])

    def test_fails_on_clean_even_when_proven(self):
        result = enforce(NODE_CHECK, run_check=failing, prove_fail_first=proving)
        self.assertEqual((True, True), (result["flagged"], result["located"]))

    def test_throwing_seams_fail_closed(self):
        def boom(check):
            raise RuntimeError("blew up")
        for options in ({"run_check": boom, "prove_fail_first": proving}, {"run_check": passing, "prove_fail_first": boom}):
            result = enforce(NODE_CHECK, **options)
            self.assertNotEqual("green", result["status"])
            self.assertEqual((True, True), (result["flagged"], result["located"]))

    def test_mode_is_echoed_and_omitted_when_absent(self):
        self.assertEqual("autonomous", enforce(NODE_CHECK, run_check=passing, prove_fail_first=proving, mode="autonomous")["mode"])
        self.assertNotIn("mode", enforce(NODE_CHECK, run_check=passing, prove_fail_first=proving))
        self.assertNotIn("mode", enforce(None, mode=""))

    def test_result_key_order_is_the_wire_order(self):
        self.assertEqual(["status", "flagged", "tier", "reason", "located", "kind", "evidence", "mode"],
                         list(enforce(NODE_CHECK, run_check=passing, prove_fail_first=proving, mode="m")))

    def test_verify_tier_cases(self):
        wired = {"kind": "node-test", "target": "tests/some-negative.test.cjs", "failFirst": True}
        result = pp.run_prohibition_enforcement(TEST_TIER, wired, run_check=passing, prove_fail_first=lambda check: {"provenFailFirst": True})
        self.assertEqual(("green", False, "test", True), (result["status"], result["flagged"], result["tier"], result["located"]))
        self.assertGreaterEqual(len(result["evidence"]), 1)
        self.assertNotEqual("green", pp.run_prohibition_enforcement(TEST_TIER, None, run_check=passing)["status"])
        self.assertNotEqual("green", pp.run_prohibition_enforcement(TEST_TIER, {**wired, "failFirst": False}, run_check=passing)["status"])

    def test_non_test_tier_prohibitions_never_green(self):
        judgment = {"verification": "judgment", "statement": "prefer clarity"}
        result = pp.run_prohibition_enforcement(judgment, NODE_CHECK, run_check=passing, prove_fail_first=proving)
        self.assertEqual(("unverified", True, "judgment"), (result["status"], result["flagged"], result["tier"]))

    def test_default_seams_fail_closed_without_a_wired_check(self):
        with tempfile.TemporaryDirectory() as directory:
            result = enforce({"kind": "node-test", "target": "missing.test.cjs"}, cwd=directory)
        self.assertNotEqual("green", result["status"])
        self.assertTrue(result["located"])


class DescriptorFromProjectionTests(unittest.TestCase):
    PROJECTED = {"statement": "MUST NOT auto-execute fetched code", "status": "resolved", "verification": "test"}

    def test_absent_or_non_object_is_none(self):
        self.assertIsNone(pp.descriptor_from_projection(dict(self.PROJECTED)))
        for value in (None, "x", 7, []):
            self.assertIsNone(pp.descriptor_from_projection(value))
        result = enforce(pp.descriptor_from_projection(dict(self.PROJECTED)), run_check=passing)
        self.assertEqual((False, True, []), (result["located"], result["flagged"], result["evidence"]))

    def test_fixtures_map_for_both_kinds(self):
        node = pp.descriptor_from_projection({**self.PROJECTED, "check_kind": "node-test", "check_target": "tests/neg.test.cjs",
                                              "check_violation_fixture": "tests/fixtures/bad-subject.txt", "check_clean_fixture": "tests/fixtures/clean-subject.txt"})
        self.assertEqual({"kind": "node-test", "target": "tests/neg.test.cjs", "violationFixture": "tests/fixtures/bad-subject.txt",
                          "cleanFixture": "tests/fixtures/clean-subject.txt"}, node)
        lint = pp.descriptor_from_projection({**self.PROJECTED, "check_kind": "lint-rule", "check_target": "src/", "check_rule": "local/no-source-grep",
                                              "check_violation_fixture": "tests/_ff_lint_violation.cjs"})
        self.assertEqual({"kind": "lint-rule", "target": "src/", "rule": "local/no-source-grep", "violationFixture": "tests/_ff_lint_violation.cjs"}, lint)

    def test_absent_fixtures_are_not_fabricated(self):
        descriptor = pp.descriptor_from_projection({**self.PROJECTED, "check_kind": "node-test", "check_target": "tests/neg.test.cjs"})
        self.assertEqual({"kind": "node-test", "target": "tests/neg.test.cjs"}, descriptor)
        blank = pp.descriptor_from_projection({**self.PROJECTED, "check_kind": "node-test", "check_target": "t", "check_violation_fixture": "  ", "check_clean_fixture": ""})
        self.assertEqual({"kind": "node-test", "target": "t"}, blank)

    def test_under_specified_descriptors_are_not_located(self):
        for fields in ({"check_kind": "lint-rule", "check_target": "src/"}, {"check_kind": "shell-script", "check_target": "x"}, {"check_kind": "node-test"}):
            descriptor = pp.descriptor_from_projection({**self.PROJECTED, **fields})
            result = enforce(descriptor, run_check=passing, prove_fail_first=proving)
            self.assertEqual((False, True), (result["located"], result["flagged"]), fields)
            self.assertNotEqual("green", result["status"])

    def test_well_formed_but_not_passing_is_located_not_green(self):
        descriptor = pp.descriptor_from_projection({**self.PROJECTED, "check_kind": "node-test", "check_target": "tests/no-autoexec.test.cjs"})
        result = enforce({**descriptor, "failFirst": True}, run_check=failing)
        self.assertEqual((True, True), (result["located"], result["flagged"]))
        self.assertNotEqual("green", result["status"])

    def test_numeric_scalars_become_strings(self):
        descriptor = pp.descriptor_from_projection({**self.PROJECTED, "check_kind": "node-test", "check_target": 12345})
        self.assertEqual("12345", descriptor["target"])
        self.assertTrue(enforce(descriptor, run_check=passing)["located"])
        coerced = pp.descriptor_from_projection({"check_kind": 7, "check_target": True})
        self.assertEqual({"kind": "7", "target": ""}, coerced)

    def test_stray_rule_on_node_test_is_dropped(self):
        descriptor = pp.descriptor_from_projection({**self.PROJECTED, "check_kind": "node-test", "check_target": "t.cjs", "check_rule": "local/no-source-grep"})
        self.assertNotIn("rule", descriptor)
        self.assertNotIn("failFirst", descriptor)


class ProjectionRoundTripTests(unittest.TestCase):
    """projectProhibitions -> serialize -> flat read-back -> descriptor (test-local flat parser)."""

    @staticmethod
    def render(entries):
        lines = ["---", "phase: 01-x", "plan: 01", "must_haves:", "  prohibitions:"]
        for entry in entries:
            lines.append(f'    - statement: "{entry["statement"]}"')
            lines.append(f"      status: {entry['status']}")
            for key in ("verification",):
                if key in entry:
                    lines.append(f"      {key}: {entry[key]}")
            if "reason" in entry:
                lines.append(f'      reason: "{entry["reason"]}"')
            for key in ("check_kind", "check_target", "check_rule", "check_violation_fixture", "check_clean_fixture"):
                if key in entry:
                    lines.append(f"      {key}: {entry[key]}")
        lines += ["---", "", "Body.", ""]
        return "\n".join(lines)

    @staticmethod
    def parse(content):
        """Flat continuation-KV reader for ``must_haves.prohibitions`` (numbers coerced like the upstream parser)."""
        items, current, inside = [], None, False
        for line in content.split("\n"):
            if line.strip() == "prohibitions:":
                inside = True
                continue
            if not inside:
                continue
            if line.strip() == "---" :
                break
            stripped = line.strip()
            if stripped.startswith("- "):
                current = {}
                items.append(current)
                stripped = stripped[2:]
            if current is None or ":" not in stripped:
                continue
            key, _, value = stripped.partition(":")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
            elif value.isdigit():
                value = int(value)
            current[key.strip()] = value
        return items

    def test_descriptor_less_items_round_trip(self):
        items = [
            {"requirement_id": "R1", "category": "values", "status": "resolved", "verification": "judgment", "resolution": None, "reason": None, "statement": "MUST NOT shame the user"},
            {"requirement_id": "R1", "category": "privacy", "status": "dismissed", "verification": "test", "resolution": None, "reason": "out of scope this phase", "statement": "MUST NOT store raw SSN"},
            {"requirement_id": "R2", "category": "safety", "status": "unresolved", "verification": None, "resolution": None, "reason": None, "statement": "MUST NOT auto-execute fetched code"},
        ]
        projected = pc.project_prohibitions(items)
        self.assertEqual(projected, self.parse(self.render(projected)))
        self.assertEqual([], pc.project_prohibitions([]))
        self.assertEqual([], pc.project_prohibitions(None))

    def test_descriptors_round_trip_through_the_read_back_adapter(self):
        for extra in ({"check_kind": "node-test", "check_target": "tests/no-autoexec.test.cjs"},
                      {"check_kind": "lint-rule", "check_target": "src/", "check_rule": "local/no-source-grep"},
                      {"check_kind": "node-test", "check_target": "tests/no-autoexec.test.cjs", "check_violation_fixture": "tests/fixtures/autoexec-bad.txt",
                       "check_clean_fixture": "tests/fixtures/autoexec-clean.txt"}):
            item = {"requirement_id": "R1", "category": "safety", "status": "resolved", "verification": "test", "resolution": None, "reason": None,
                    "statement": "MUST NOT auto-execute fetched code", **extra}
            projected = pc.project_prohibitions([item])
            reparsed = self.parse(self.render(projected))
            self.assertEqual(projected, reparsed)
            descriptor = pp.descriptor_from_projection(reparsed[0])
            self.assertEqual(extra["check_kind"], descriptor["kind"])
            self.assertEqual(extra["check_target"], descriptor["target"])

    def test_random_descriptors_reconstruct_exactly_or_fail_closed(self):
        rng = random.Random(1278)
        alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/._-"
        base = {"requirement_id": "R1", "category": "safety", "status": "resolved", "verification": "test", "resolution": None, "reason": None,
                "statement": "MUST NOT do the forbidden thing"}

        def scalar(numeric):
            return str(rng.randint(0, 9999999)) if numeric else "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 24)))

        for _ in range(200):
            kind = rng.choice(["node-test", "lint-rule"])
            target, fixture, clean, rule = (scalar(rng.random() < .3) for _ in range(4))
            if not any(ch.isalpha() or ch in "/._-" for ch in rule) and kind == "lint-rule":
                rule = "r" + rule
            item = {**base, "check_kind": kind, "check_target": target, "check_violation_fixture": fixture, "check_clean_fixture": clean}
            if kind == "lint-rule":
                item["check_rule"] = rule
            reparsed = self.parse(self.render(pc.project_prohibitions([item])))
            descriptor = pp.descriptor_from_projection(reparsed[0])
            self.assertEqual((kind, target, fixture, clean), (descriptor["kind"], descriptor["target"], descriptor["violationFixture"], descriptor["cleanFixture"]))
            self.assertTrue(all(isinstance(v, str) for v in descriptor.values()))
            if kind == "lint-rule":
                self.assertEqual(rule, descriptor["rule"])
            else:
                self.assertNotIn("rule", descriptor)

    def test_malformed_descriptors_never_green_and_are_unlocated(self):
        base = {"requirement_id": "R1", "category": "safety", "status": "resolved", "verification": "test", "resolution": None, "reason": None,
                "statement": "MUST NOT do the forbidden thing"}
        malformed = [dict(base), {**base, "check_kind": "node-test"}, {**base, "check_kind": "lint-rule", "check_target": "src"},
                     *[{**base, "check_kind": kind, "check_target": "t"} for kind in ("shell-script", "bash", "python", "exec", "")]]
        for item in malformed * 3:
            descriptor = pp.descriptor_from_projection(item)
            result = pp.run_prohibition_enforcement(item, descriptor, run_check=passing)
            self.assertNotEqual("green", result["status"])
            self.assertEqual((True, False), (result["flagged"], result["located"]))


class EnforcementHelperTests(unittest.TestCase):
    def test_build_args(self):
        self.assertEqual(["--test", "--test-reporter=tap", "--", "tests/neg.test.cjs"], pp.build_node_test_args({"target": "tests/neg.test.cjs"}))
        argv = pp.build_lint_args({"kind": "lint-rule", "rule": "local/no-source-grep", "target": "tests/"})
        self.assertEqual("json", argv[argv.index("--format")+1])
        self.assertIn("--no-warn-ignored", argv)
        self.assertNotIn("--rule", argv)
        self.assertEqual("tests/", argv[-1])
        self.assertEqual("--", argv[-2])

    def test_parse_node_test_summary(self):
        self.assertEqual({"tests": 3, "pass": 2, "fail": 1, "cancelled": 1}, pp.parse_node_test_summary("# tests 3\n# pass 2\n# fail 1\n# cancelled 1\n"))
        self.assertEqual({"tests": 0, "pass": 0, "fail": 0, "cancelled": 0}, pp.parse_node_test_summary("no summary here"))
        self.assertEqual({"tests": 0, "pass": 0, "fail": 0, "cancelled": 0}, pp.parse_node_test_summary(None))

    def test_is_node_test_red_boundary(self):
        self.assertTrue(pp.is_node_test_red("# fail 1\n"))
        self.assertFalse(pp.is_node_test_red("# fail 0\n"))
        self.assertTrue(pp.is_node_test_red("# fail 2\n"))
        self.assertFalse(pp.is_node_test_red("no summary"))

    def test_non_vacuous_red(self):
        self.assertFalse(pp.is_non_vacuous_node_test_red("not ok 1 - neg.test.cjs\n# tests 1\n# pass 0\n# fail 1\n", "neg.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_red("not ok 1 - /tmp/x/neg.test.cjs\n# tests 1\n# pass 0\n# fail 1\n", "neg.test.cjs"))
        self.assertTrue(pp.is_non_vacuous_node_test_red("not ok 1 - rejects the forbidden pattern\n# tests 1\n# pass 0\n# fail 1\n", "neg.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_red("ok 1 - guards\n# tests 1\n# pass 1\n# fail 0\n", "neg.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_red("not ok 1 - rejects the forbidden pattern # SKIP\n# tests 1\n# pass 0\n# fail 1\n", "neg.test.cjs"))

    def test_tap_names_exclude_skip_and_todo(self):
        self.assertEqual(["guards the must-NOT"], pp.tap_test_names("ok 1 - guards the must-NOT\nok 2 - other # SKIP\nok 3 - later # TODO\n"))
        self.assertEqual(["a"], pp.tap_test_names("ok 1 - a\nok 2 - b # skip\n"))
        self.assertEqual(["named"], pp.tap_test_names("ok 1 - named # extra note\n"))
        self.assertEqual([], pp.tap_test_names(None))
        self.assertEqual(["boom"], pp.tap_failed_test_names("ok 1 - fine\nnot ok 2 - boom\nnot ok 3 - later # TODO\n"))

    def test_non_vacuous_pass(self):
        self.assertFalse(pp.is_non_vacuous_node_test_pass("ok 1 - empty.test.cjs\nok 2 - the negative test # SKIP\n# tests 2\n# pass 2\n# fail 0\n# cancelled 0\n", "empty.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_pass("ok 1 - guards\n# tests 1\n# pass 1\n# fail 0\n# cancelled 1\n", "neg.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_pass("ok 1 - empty.test.cjs\n1..1\n# tests 1\n# pass 1\n# fail 0\n", "empty.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_pass("ok 1 - /tmp/x/empty.test.cjs\n1..1\n# tests 1\n# pass 1\n# fail 0\n", "empty.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_pass("ok 1 - neg.test.cjs\n1..1\n# tests 1\n# pass 1\n# fail 0\n", "/abs/path/neg.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_pass("ok 1 - C:\\x\\neg.test.cjs\n1..1\n# tests 1\n# pass 1\n# fail 0\n", "neg.test.cjs"))
        self.assertTrue(pp.is_non_vacuous_node_test_pass("ok 1 - guards the must-NOT\n1..1\n# tests 1\n# pass 1\n# fail 0\n", "/abs/path/neg.test.cjs"))
        self.assertFalse(pp.is_non_vacuous_node_test_pass("not ok 1 - guards\n# tests 1\n# pass 0\n# fail 1\n", "neg.test.cjs"))

    def test_eslint_json_helpers(self):
        rule = "local/no-source-grep"
        self.assertTrue(pp.eslint_json_has_rule(json.dumps([{"messages": [{"ruleId": rule}]}]), rule))
        self.assertFalse(pp.eslint_json_has_rule(json.dumps([{"messages": [{"ruleId": "other"}]}]), rule))
        self.assertTrue(pp.eslint_json_has_rule("not json", rule), "an unreadable report is a violation, never a silent pass")
        self.assertTrue(pp.eslint_json_has_rule("{}", rule))
        self.assertTrue(pp.eslint_json_has_rule(json.dumps([{"messages": [], "suppressedMessages": [{"ruleId": rule}]}]), rule))
        self.assertEqual(2, pp.eslint_file_result_count(json.dumps([{}, {}])))
        self.assertEqual(0, pp.eslint_file_result_count("[]"))
        self.assertEqual(0, pp.eslint_file_result_count("garbage"))
        self.assertEqual(0, pp.eslint_file_result_count("{}"))
        fatal = json.dumps([{"messages": [{"ruleId": None, "fatal": True, "severity": 2, "message": "Parsing error"}], "fatalErrorCount": 1}])
        self.assertTrue(pp.eslint_has_fatal_error(fatal))
        self.assertTrue(pp.eslint_has_fatal_error(json.dumps([{"messages": [{"fatal": True}]}])))
        self.assertFalse(pp.eslint_has_fatal_error(json.dumps([{"messages": [], "fatalErrorCount": 0}])))
        self.assertTrue(pp.eslint_has_fatal_error("not json"))
        self.assertTrue(pp.eslint_has_fatal_error("{}"))


class SchemaLayerTests(unittest.TestCase):
    def test_validators_and_dispositions_reexported(self):
        self.assertIs(True, pp.validate_prohibition_resolution({"requirement_id": "R1", "category": "values", "status": "resolved", "verification": "judgment", "resolution": None}))
        self.assertEqual(["test", "judgment"], pp.PROHIBITION_VALIDATORS["verification"])

    def test_judgment_is_never_silently_green(self):
        evidence = {"enforcementEvidence": ["a wired negative test reference"]}
        disposition = pc.disposition_for_prohibition({"status": "resolved", "verification": "judgment", "statement": "MUST NOT shame the user"}, evidence)
        self.assertNotEqual("green", disposition["status"])
        self.assertTrue(disposition["flagged"])
        for tier in ("test", "judgment"):
            empty = pc.disposition_for_prohibition({"status": "resolved", "verification": tier, "statement": "x"}, {"enforcementEvidence": []})
            self.assertEqual(("unverified", True), (empty["status"], empty["flagged"]))


# ------------------------------------------------------------------------------------------------
# Gate
# ------------------------------------------------------------------------------------------------

USAGE = {"failure": {"code": "sdk_missing_arg", "message": "prohibition-enforcement requires a JSON request: check prohibition-enforcement <request.json> | --json '{\"prohibition\":{...},\"check\":{...}}'"}}
PROHIBITION = {"verification": "test", "text": "never log secrets"}
REQUEST = {"prohibition": PROHIBITION, "check": None}


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.dir = Path(self.temporary.name)

    def evaluate(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            result = pp.evaluate_prohibition_enforcement_gate(project_dir=str(self.dir), args=args)
        self.assertEqual(("", ""), (out.getvalue(), err.getvalue()), "a gate must not write to stdout/stderr")
        return result

    def inline(self, request):
        return self.evaluate(["--json", request if isinstance(request, str) else json.dumps(request)])

    def test_usage_failures(self):
        (self.dir/"bad.json").write_text("{not json\n", encoding="utf-8")
        for args in ([], [""], [str(self.dir/"absent.json")], [str(self.dir)], [str(self.dir/"bad.json")], ["--json"],
                     ["--json", "{not json"], ["--json", "null"], ["--json", ""], ["--json", "NaN"], ["--json", "Infinity"]):
            with self.subTest(args=args):
                self.assertEqual(USAGE, self.evaluate(args))

    def test_scalar_documents_parse_and_fail_closed(self):
        for body in ("7", '"x"', "[]", "true"):
            result = self.inline(body)
            self.assertNotIn("failure", result)
            self.assertEqual("advisory", result["outcome"])
            self.assertEqual((True, False), (result["payload"]["flagged"], result["payload"]["located"]))

    def test_delivers_the_producer_disposition_as_advisory(self):
        result = self.inline(REQUEST)
        self.assertEqual(("advisory", False), (result["outcome"], result["block"]))
        self.assertEqual(pp.run_prohibition_enforcement(PROHIBITION, None), dict(result["payload"]))
        self.assertEqual(("unverified", True, False), (result["payload"]["status"], result["payload"]["flagged"], result["payload"]["located"]))
        self.assertEqual(list(pp.run_prohibition_enforcement(PROHIBITION, None)), list(result["payload"]))
        self.assertEqual(["outcome", "block", "payload"], list(result))

    def test_request_file_and_inline_agree(self):
        (self.dir/"req.json").write_text(json.dumps(REQUEST), encoding="utf-8")
        from_file = self.evaluate([str(self.dir/"req.json")])
        self.assertEqual(dict(self.inline(REQUEST)["payload"]), dict(from_file["payload"]))
        self.assertEqual("advisory", from_file["outcome"])

    def test_judgment_tier_is_never_green(self):
        prohibition = {"verification": "judgment", "text": "prefer clarity"}
        check = {"kind": "unknown-kind", "target": "t"}
        result = self.inline({"prohibition": prohibition, "check": check})
        self.assertEqual(("unverified", "judgment"), (result["payload"]["status"], result["payload"]["tier"]))
        self.assertEqual(pp.run_prohibition_enforcement(prohibition, check), dict(result["payload"]))

    def test_mode_handling(self):
        self.assertEqual("autonomous", self.inline({**REQUEST, "mode": "autonomous"})["payload"]["mode"])
        for mode in ("", 7, None):
            self.assertNotIn("mode", self.inline({**REQUEST, "mode": mode})["payload"])
        self.assertNotIn("mode", self.inline(REQUEST)["payload"])

    def test_non_object_checks_are_no_check(self):
        for check in ("node-test", 7, None, True, []):
            self.assertFalse(self.inline({"prohibition": PROHIBITION, "check": check})["payload"]["located"], check)

    def test_under_specified_descriptors_are_not_located(self):
        for check in ({"kind": "node-test"}, {"kind": "node-test", "target": "   "}, {"kind": "lint-rule", "target": "src"},
                      {"kind": "lint-rule", "target": "src", "rule": " "}, {"kind": "other", "target": "t"}):
            result = self.inline({"prohibition": PROHIBITION, "check": check})
            self.assertEqual(("advisory", False, []), (result["outcome"], result["payload"]["located"], result["payload"]["evidence"]))

    def test_missing_prohibition_is_read_as_empty(self):
        result = self.inline({"check": None})
        self.assertEqual(("advisory", True, None), (result["outcome"], result["payload"]["flagged"], result["payload"]["tier"]))

    def test_inline_json_takes_precedence_over_a_path(self):
        result = self.evaluate(["ignored.json", "--json", json.dumps({"prohibition": {"verification": "judgment"}, "check": None})])
        self.assertEqual("judgment", result["payload"]["tier"])

    def test_property_any_inline_argument_is_usage_or_advisory(self):
        rng = random.Random(5219)
        samples = ["", "{", "[", "{}", "[1,2]", '{"check": 5}', '{"prohibition": null, "check": {"kind": "node-test"}}', "null", '"s"', "1e999", "-Infinity"]
        alphabet = '{}[]",:0123456789 nulltruefalse\\'
        samples += ["".join(rng.choice(alphabet) for _ in range(rng.randint(0, 30))) for _ in range(150)]
        samples += [json.dumps(rng.choice([None, 0, 1.5, "x", [], {}, {"mode": 3}, {"check": {"kind": "lint-rule", "target": "t"}}])) for _ in range(50)]
        for sample in samples:
            result = pp.evaluate_prohibition_enforcement_gate(args=["--json", sample])
            if "failure" in result:
                self.assertEqual(USAGE, result)
            else:
                self.assertEqual((False, "advisory"), (result["block"], result["outcome"]), sample)

    def test_a_throw_is_an_unreadable_fail_closed_verdict(self):
        with mock.patch.object(pc, "disposition_for_prohibition", side_effect=RuntimeError("simulated disposition failure")):
            result = self.inline(REQUEST)
        self.assertEqual(("unreadable", False), (result["outcome"], result["block"]))
        self.assertEqual({"status": "unverified", "flagged": True, "tier": None, "reason": "exception: simulated disposition failure",
                          "located": False, "kind": None, "evidence": []}, dict(result["payload"]))
        self.assertEqual(["status", "flagged", "tier", "reason", "located", "kind", "evidence"], list(result["payload"]))

    def test_the_fail_closed_payload_keeps_the_request_mode(self):
        with mock.patch.object(pc, "disposition_for_prohibition", side_effect=RuntimeError("boom")):
            result = self.inline({**REQUEST, "mode": "autonomous"})
        self.assertEqual(("autonomous", "unreadable"), (result["payload"]["mode"], result["outcome"]))

    def test_non_error_throws_are_reported_by_their_string_form(self):
        with mock.patch.object(pc, "disposition_for_prohibition", side_effect=ValueError("plain string")):
            self.assertEqual("exception: plain string", self.inline(REQUEST)["payload"]["reason"])

    def test_verdict_payloads_are_frozen(self):
        payload = self.inline(REQUEST)["payload"]
        for mutate in (lambda: payload.__setitem__("status", "green"), lambda: payload.pop("status"), lambda: payload.update(a=1),
                       lambda: payload.clear(), lambda: payload.setdefault("x", 1), lambda: payload.__delitem__("status")):
            with self.assertRaises(TypeError):
                mutate()
        self.assertEqual("unverified", payload["status"])
        self.assertIsInstance(json.dumps(payload), str)


# ------------------------------------------------------------------------------------------------
# Real runners against a fake `node` on PATH
# ------------------------------------------------------------------------------------------------

FAKE_NODE = r'''
import json, os, subprocess, sys, time

args = sys.argv[1:]


def emit(text):
    sys.stdout.write(text)
    sys.stdout.flush()


def tap(ok, name):
    failed = 0 if ok else 1
    emit(("ok" if ok else "not ok") + " 1 - " + name + "\n1..1\n# tests 1\n# pass %d\n# fail %d\n# cancelled 0\n" % (1 - failed, failed))
    sys.exit(0 if ok else 1)


if args and args[0].endswith("eslint.js"):
    target = args[-1]
    if not os.path.exists(target):
        emit("[]")
        sys.exit(0)
    content = open(target, encoding="utf-8").read()
    messages = [{"ruleId": "local/no-source-grep", "severity": 2}] if "VIOLATION" in content else []
    emit(json.dumps([{"filePath": target, "messages": messages, "fatalErrorCount": 0}]))
    sys.exit(1 if messages else 0)

assert "--test" in args and "--test-reporter=tap" in args, args
target = args[args.index("--") + 1]
if not os.path.exists(target):
    tap(False, os.path.basename(target))
spec = json.load(open(target, encoding="utf-8"))
mode = spec["mode"]
subject = os.environ.get("ENGINEER_PROHIB_SUBJECT") or os.environ.get("GSD_PROHIB_SUBJECT")
if spec.get("envfile"):
    with open(spec["envfile"], "w", encoding="utf-8") as stream:
        json.dump({key: os.environ.get(key) for key in ("NODE_TEST_CONTEXT", "NODE_OPTIONS", "ENGINEER_PROHIB_SUBJECT", "GSD_PROHIB_SUBJECT")}, stream)
if mode == "content":
    path = subject or os.path.join(os.path.dirname(os.path.abspath(target)), "clean-subject.txt")
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        tap(False, "rejects the forbidden content")
    tap("FORBIDDEN" not in text, "rejects the forbidden content")
elif mode == "strict-content":
    text = open(subject, encoding="utf-8").read()
    tap("FORBIDDEN" not in text, "rejects the forbidden content")
elif mode == "deceptive":
    tap(not subject, "reds whenever a subject is present")
elif mode == "empty":
    tap(True, os.path.abspath(target))
elif mode == "fail":
    tap(False, "fails immediately")
elif mode == "always-pass":
    tap(True, "always passes")
elif mode == "hang":
    time.sleep(30)
elif mode == "spawnchild":
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    with open(spec["pidfile"], "w", encoding="utf-8") as stream:
        stream.write(str(child.pid))
    time.sleep(30)
else:
    raise SystemExit("unknown mode " + mode)
'''


def pid_alive(pid):
    if sys.platform == "win32":
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False
        code = ctypes.c_ulong()
        kernel.GetExitCodeProcess(handle, ctypes.byref(code))
        kernel.CloseHandle(handle)
        return code.value == 259
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    try:
        with open(f"/proc/{pid}/stat", encoding="utf-8") as stream:
            return stream.read().rsplit(")", 1)[1].split()[0] != "Z"
    except OSError:
        return True


class FakeNodeCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.bin, self.dir = base/"bin", base/"work"
        self.bin.mkdir()
        self.dir.mkdir()
        script = self.bin/"fake_node.py"
        script.write_text(FAKE_NODE, encoding="utf-8")
        if sys.platform == "win32":
            (self.bin/"node.cmd").write_text(f'@echo off\r\n"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
        else:
            wrapper = self.bin/"node"
            wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
            wrapper.chmod(wrapper.stat().st_mode | stat.S_IEXEC)
        patcher = mock.patch.dict(os.environ, {"PATH": str(self.bin) + os.pathsep + os.environ.get("PATH", "")})
        patcher.start()
        self.addCleanup(patcher.stop)

    def spec(self, name, mode, **extra):
        path = self.dir/name
        path.write_text(json.dumps({"mode": mode, **extra}), encoding="utf-8")
        return str(path)

    def subjects(self):
        (self.dir/"clean-subject.txt").write_text("this subject is clean\n", encoding="utf-8")
        (self.dir/"bad-subject.txt").write_text("this subject contains FORBIDDEN content\n", encoding="utf-8")
        return str(self.dir/"bad-subject.txt"), str(self.dir/"clean-subject.txt")

    def full(self, descriptor, **options):
        return pp.run_prohibition_enforcement(TEST_TIER, descriptor, cwd=str(self.dir), **options)


class FakeNodeRunnerTests(FakeNodeCase):
    def test_fake_node_is_what_the_runner_finds(self):
        self.assertTrue(Path(pp._node_executable()).resolve().is_relative_to(self.bin.resolve()))

    def test_genuine_proven_pass_greens_via_real_runner_and_prover(self):
        bad, clean = self.subjects()
        target = self.spec("neg.test.cjs", "content")
        result = self.full({"kind": "node-test", "target": target, "failFirst": True, "violationFixture": bad, "cleanFixture": clean}, run_check=passing)
        self.assertEqual(("green", True, 1, "violation-fixture"), (result["status"], result["located"], len(result["evidence"]), result["evidence"][0]["failFirstProof"]))

    def test_full_producer_with_neither_seam_injected_greens(self):
        bad, clean = self.subjects()
        result = self.full({"kind": "node-test", "target": self.spec("neg.test.cjs", "content"), "violationFixture": bad, "cleanFixture": clean})
        self.assertEqual(("green", "node-test", True, 1), (result["status"], result["kind"], result["located"], len(result["evidence"])))

    def test_subject_is_injected_under_both_env_names(self):
        bad, clean = self.subjects()
        envfile = str(self.dir/"env.json")
        target = self.spec("neg.test.cjs", "content", envfile=envfile)
        proof = pp.default_prove_fail_first({"kind": "node-test", "target": target, "violationFixture": bad, "cleanFixture": clean}, str(self.dir))
        self.assertTrue(proof["provenFailFirst"])
        seen = json.loads(Path(envfile).read_text(encoding="utf-8"))
        self.assertEqual((clean, clean), (seen["ENGINEER_PROHIB_SUBJECT"], seen["GSD_PROHIB_SUBJECT"]), "the last run is the clean control")

    def test_deceptive_content_independent_red_is_not_proven(self):
        bad, clean = self.subjects()
        target = self.spec("neg.test.cjs", "deceptive")
        for fixtures in ({"violationFixture": bad, "cleanFixture": clean}, {"violationFixture": bad}):
            result = self.full({"kind": "node-test", "target": target, "failFirst": True, **fixtures}, run_check=passing)
            self.assertNotEqual("green", result["status"], fixtures)

    def test_honest_test_without_the_clean_control_hard_gates(self):
        bad, _ = self.subjects()
        result = self.full({"kind": "node-test", "target": self.spec("neg.test.cjs", "content"), "failFirst": True, "violationFixture": bad}, run_check=passing)
        self.assertNotEqual("green", result["status"])
        self.assertTrue(result["located"])

    def test_missing_fixtures_fail_closed(self):
        bad, clean = self.subjects()
        target = self.spec("neg.test.cjs", "content")
        for fixtures in ({}, {"violationFixture": str(self.dir/"nope.txt"), "cleanFixture": clean},
                         {"violationFixture": bad, "cleanFixture": str(self.dir/"nope.txt")}):
            proof = pp.default_prove_fail_first({"kind": "node-test", "target": target, **fixtures}, str(self.dir))
            self.assertFalse(proof["provenFailFirst"], fixtures)

    def test_honest_test_with_a_missing_violation_fixture_cannot_forge_a_proof(self):
        target = self.spec("neg.test.cjs", "strict-content")
        _, clean = self.subjects()
        proof = pp.default_prove_fail_first({"kind": "node-test", "target": target, "violationFixture": str(self.dir/"does-not-exist.txt"), "cleanFixture": clean}, str(self.dir))
        self.assertFalse(proof["provenFailFirst"])

    def test_relative_fixtures_resolve_against_cwd(self):
        self.subjects()
        target = self.spec("neg.test.cjs", "content")
        proof = pp.default_prove_fail_first({"kind": "node-test", "target": target, "violationFixture": "bad-subject.txt", "cleanFixture": "clean-subject.txt"}, str(self.dir))
        self.assertEqual({"provenFailFirst": True, "method": "violation-fixture"}, proof)

    def test_toothless_test_is_not_proven(self):
        bad, clean = self.subjects()
        proof = pp.default_prove_fail_first({"kind": "node-test", "target": self.spec("neg.test.cjs", "always-pass"), "violationFixture": bad, "cleanFixture": clean}, str(self.dir))
        self.assertFalse(proof["provenFailFirst"])

    def test_empty_test_file_does_not_green(self):
        result = self.full({"kind": "node-test", "target": self.spec("empty.test.cjs", "empty"), "failFirst": True}, prove_fail_first=proving)
        self.assertNotEqual("green", result["status"])
        self.assertEqual((True, []), (result["located"], result["evidence"]))

    def test_default_runner_passes_only_a_non_vacuous_pass(self):
        self.subjects()
        self.assertEqual({"passed": True}, pp._default_run_check({"kind": "node-test", "target": self.spec("neg.test.cjs", "content")}, str(self.dir)))
        self.assertEqual({"passed": False}, pp._default_run_check({"kind": "node-test", "target": self.spec("e.test.cjs", "empty")}, str(self.dir)))
        self.assertEqual({"passed": False}, pp._default_run_check({"kind": "node-test", "target": self.spec("f.test.cjs", "fail")}, str(self.dir)))
        self.assertEqual({"passed": False}, pp._default_run_check({"kind": "node-test", "target": str(self.dir/"missing.test.cjs")}, str(self.dir)))
        self.assertEqual({"passed": False}, pp._default_run_check({"kind": "other", "target": "x"}, str(self.dir)))

    def test_ordinary_failure_fails_closed(self):
        result = self.full({"kind": "node-test", "target": self.spec("fails.test.cjs", "fail"), "failFirst": True})
        self.assertNotEqual("green", result["status"])
        self.assertEqual((True, []), (result["located"], result["evidence"]))

    def test_ambient_test_runner_environment_is_stripped(self):
        envfile = str(self.dir/"env.json")
        target = self.spec("neg.test.cjs", "always-pass", envfile=envfile)
        with mock.patch.dict(os.environ, {"NODE_TEST_CONTEXT": "child-v8", "NODE_OPTIONS": "--require x"}):
            pp._default_run_check({"kind": "node-test", "target": target}, str(self.dir))
        seen = json.loads(Path(envfile).read_text(encoding="utf-8"))
        self.assertEqual((None, None), (seen["NODE_TEST_CONTEXT"], seen["NODE_OPTIONS"]))

    def test_hanging_test_is_killed_by_the_bounded_timeout(self):
        target = self.spec("hang.test.cjs", "hang")
        started = time.monotonic()
        result = self.full({"kind": "node-test", "target": target, "failFirst": True}, timeout_ms=1500)
        self.assertLess(time.monotonic() - started, 20)
        self.assertNotEqual("green", result["status"])
        self.assertTrue(result["located"])

    def test_non_positive_timeouts_fall_back_to_the_bound(self):
        self.assertEqual(30_000, pp._pos_timeout(0, 30_000))
        self.assertEqual(30_000, pp._pos_timeout(-5, 30_000))
        self.assertEqual(30_000, pp._pos_timeout(None, 30_000))
        self.assertEqual(30_000, pp._pos_timeout(True, 30_000))
        self.assertEqual(1500, pp._pos_timeout(1500, 30_000))

    def test_a_hanging_checks_descendants_are_reaped(self):
        pidfile = self.dir/"child.pid"
        target = self.spec("hang-pid.test.cjs", "spawnchild", pidfile=str(pidfile))
        child = None
        try:
            result = self.full({"kind": "node-test", "target": target, "failFirst": True}, timeout_ms=1500)
            self.assertNotEqual("green", result["status"])
            for _ in range(50):
                if pidfile.exists() and pidfile.read_text(encoding="utf-8").strip():
                    break
                time.sleep(0.1)
            child = int(pidfile.read_text(encoding="utf-8"))
            for _ in range(50):
                if not pid_alive(child):
                    break
                time.sleep(0.1)
            self.assertFalse(pid_alive(child), f"descendant {child} must be reaped, not orphaned")
        finally:
            if child and pid_alive(child):
                try:
                    os.kill(child, 9)
                except OSError:
                    pass


class FakeEslintTests(FakeNodeCase):
    def setUp(self):
        super().setUp()
        cli = self.dir/"node_modules/eslint/bin"
        cli.mkdir(parents=True)
        (self.dir/"node_modules/eslint/package.json").write_text('{"name": "eslint"}', encoding="utf-8")
        (cli/"eslint.js").write_text("// fake\n", encoding="utf-8")
        (self.dir/"clean.txt").write_text("nothing wrong here\n", encoding="utf-8")
        (self.dir/"violation.txt").write_text("VIOLATION\n", encoding="utf-8")
        self.lint = {"kind": "lint-rule", "rule": "local/no-source-grep", "target": "clean.txt", "violationFixture": "violation.txt"}

    def test_clean_target_with_a_teeth_proof_greens(self):
        result = self.full(self.lint)
        self.assertEqual(("green", "lint-rule", True, 1, "violation-fixture", "local/no-source-grep"),
                         (result["status"], result["kind"], result["located"], len(result["evidence"]),
                          result["evidence"][0]["failFirstProof"], result["evidence"][0]["rule"]))

    def test_toothless_fixture_hard_gates_in_both_modes(self):
        for mode in ("interactive", "autonomous"):
            result = self.full({**self.lint, "violationFixture": "clean.txt"}, mode=mode)
            self.assertEqual((True, True, [], mode), (result["flagged"], result["located"], result["evidence"], result["mode"]))
            self.assertNotEqual("green", result["status"])

    def test_prover_directions(self):
        self.assertEqual({"provenFailFirst": True, "method": "violation-fixture"}, pp.default_prove_fail_first(self.lint, str(self.dir)))
        self.assertFalse(pp.default_prove_fail_first({**self.lint, "violationFixture": "clean.txt"}, str(self.dir))["provenFailFirst"])
        self.assertFalse(pp.default_prove_fail_first({k: v for k, v in self.lint.items() if k != "violationFixture"}, str(self.dir))["provenFailFirst"])
        self.assertFalse(pp.default_prove_fail_first({**self.lint, "violationFixture": "no/such/file.cjs"}, str(self.dir))["provenFailFirst"])

    def test_runner_requires_a_clean_lint(self):
        self.assertEqual({"passed": True}, pp._default_run_check(self.lint, str(self.dir)))
        self.assertEqual({"passed": False}, pp._default_run_check({**self.lint, "target": "violation.txt"}, str(self.dir)))
        self.assertEqual({"passed": False}, pp._default_run_check({**self.lint, "target": "missing.txt"}, str(self.dir)), "nothing linted is vacuous")

    def test_eslint_is_found_from_a_subdirectory(self):
        nested = self.dir/"a/b"
        nested.mkdir(parents=True)
        self.assertTrue(pp._resolve_eslint_cli(str(nested)).endswith("eslint.js"))

    def test_missing_eslint_fails_closed(self):
        with tempfile.TemporaryDirectory() as bare:
            with mock.patch.object(pp, "_resolve_eslint_cli", wraps=lambda cwd: None):
                self.assertEqual({"passed": False}, pp._default_run_check(self.lint, bare))
                self.assertEqual({"provenFailFirst": False}, pp.default_prove_fail_first(self.lint, bare))


class SubprocessMachineryTests(unittest.TestCase):
    def test_exec_reaping_returns_stdout_and_raises_with_partial_output(self):
        env = dict(os.environ)
        self.assertEqual("hi\n", pp._exec_reaping(sys.executable, ["-c", "print('hi')"], os.getcwd(), env, 20).replace("\r\n", "\n"))
        with self.assertRaises(pp._ExecError) as caught:
            pp._exec_reaping(sys.executable, ["-c", "import sys; print('partial'); sys.exit(3)"], os.getcwd(), env, 20)
        self.assertIn("partial", caught.exception.stdout)
        with self.assertRaises(pp._ExecError) as caught:
            pp._exec_reaping(sys.executable, ["-c", "import time; print('x', flush=True); time.sleep(30)"], os.getcwd(), env, 1)
        self.assertEqual("", "".join(ch for ch in caught.exception.stdout if ch not in "x\r\n"))
        with self.assertRaises(pp._ExecError):
            pp._exec_reaping(str(Path(tempfile.gettempdir())/"definitely-not-a-binary-xyz"), [], os.getcwd(), env, 5)

    def test_child_env_strips_runner_context(self):
        with mock.patch.dict(os.environ, {"NODE_TEST_CONTEXT": "child-v8", "NODE_OPTIONS": "--x", "KEEP": "1"}):
            env = pp._child_env({"EXTRA": "2"})
        self.assertEqual((None, None, "1", "2"), (env.get("NODE_TEST_CONTEXT"), env.get("NODE_OPTIONS"), env.get("KEEP"), env.get("EXTRA")))

    def test_reap_never_raises_on_bad_pids(self):
        for pid in (None, 0, -4, "x", 4_000_000_000):
            pp._reap_descendants(pid)

    def test_taskkill_path_is_absolute_or_none(self):
        with mock.patch.dict(os.environ, {"SystemRoot": "", "windir": ""}):
            self.assertIsNone(pp._taskkill_path())
        with mock.patch.dict(os.environ, {"SystemRoot": "C:\\Windows"}):
            self.assertTrue(pp._taskkill_path().lower().endswith("taskkill.exe"))

    def test_without_node_the_default_seams_fail_closed(self):
        with mock.patch.object(pp, "_node_executable", return_value=None), tempfile.TemporaryDirectory() as directory:
            self.assertEqual({"passed": False}, pp._default_run_check({"kind": "node-test", "target": "t.cjs"}, directory))
            (Path(directory)/"bad.txt").write_text("FORBIDDEN", encoding="utf-8")
            (Path(directory)/"clean.txt").write_text("ok", encoding="utf-8")
            proof = pp.default_prove_fail_first({"kind": "node-test", "target": "t.cjs", "violationFixture": "bad.txt", "cleanFixture": "clean.txt"}, directory)
            self.assertFalse(proof["provenFailFirst"])
        self.assertEqual({"provenFailFirst": False}, pp.default_prove_fail_first({"kind": "other"}, os.getcwd()))
        self.assertEqual({"provenFailFirst": False}, pp.default_prove_fail_first(None, os.getcwd()))

    def test_resolve_eslint_cli_requires_the_cli_file(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory)/"node_modules/eslint"
            package.mkdir(parents=True)
            (package/"package.json").write_text("{}", encoding="utf-8")
            self.assertIsNone(pp._resolve_eslint_cli(directory))


@unittest.skipUnless(HAS_REAL_NODE, "node is not installed")
class RealNodeTests(unittest.TestCase):
    """Ports of the real-runner end-to-end cases; they run only where a real node exists."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.dir = Path(self.temporary.name)
        (self.dir/"clean-subject.txt").write_text("this subject is clean\n", encoding="utf-8")
        (self.dir/"bad-subject.txt").write_text("this subject contains FORBIDDEN content\n", encoding="utf-8")

    def write(self, name, body):
        path = self.dir/name
        path.write_text(body, encoding="utf-8")
        return str(path)

    HONEST = ("const { test } = require('node:test');\nconst assert = require('node:assert');\nconst fs = require('node:fs');\nconst path = require('node:path');\n"
              "test('rejects the forbidden content (content-dependent)', () => {\n"
              "  const subjectPath = process.env.GSD_PROHIB_SUBJECT || path.join(__dirname, 'clean-subject.txt');\n"
              "  const subject = fs.readFileSync(subjectPath, 'utf-8');\n"
              "  assert.ok(!subject.includes('FORBIDDEN'), 'subject must not contain FORBIDDEN');\n});\n")

    def test_honest_content_dependent_test_greens(self):
        target = self.write("neg.test.cjs", self.HONEST)
        result = pp.run_prohibition_enforcement(TEST_TIER, {"kind": "node-test", "target": target, "violationFixture": str(self.dir/"bad-subject.txt"),
                                                            "cleanFixture": str(self.dir/"clean-subject.txt")}, cwd=str(self.dir))
        self.assertEqual("green", result["status"])
        self.assertEqual("violation-fixture", result["evidence"][0]["failFirstProof"])

    def test_empty_file_does_not_green(self):
        target = self.write("empty.test.cjs", "// intentionally empty\n")
        result = pp.run_prohibition_enforcement(TEST_TIER, {"kind": "node-test", "target": target}, cwd=str(self.dir))
        self.assertNotEqual("green", result["status"])

    def test_deceptive_test_is_not_proven(self):
        target = self.write("deceptive.test.cjs", "const { test } = require('node:test');\nconst assert = require('node:assert');\n"
                            "test('reds whenever a subject is present', () => { assert.ok(!process.env.GSD_PROHIB_SUBJECT); });\n")
        result = pp.run_prohibition_enforcement(TEST_TIER, {"kind": "node-test", "target": target, "violationFixture": str(self.dir/"bad-subject.txt"),
                                                            "cleanFixture": str(self.dir/"clean-subject.txt")}, cwd=str(self.dir), run_check=passing)
        self.assertNotEqual("green", result["status"])

    def test_hanging_test_fails_closed(self):
        target = self.write("hang.test.cjs", "const { test } = require('node:test');\ntest('hangs', () => new Promise((resolve) => { setTimeout(resolve, 10_000); }));\n")
        result = pp.run_prohibition_enforcement(TEST_TIER, {"kind": "node-test", "target": target}, cwd=str(self.dir), timeout_ms=1500)
        self.assertNotEqual("green", result["status"])
        self.assertTrue(result["located"])


if __name__ == "__main__":
    unittest.main()
