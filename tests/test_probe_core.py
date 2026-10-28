"""Ports of upstream tests/probe-core.test.cjs and tests/probe-core.property.test.cjs."""
import importlib
import importlib.util
import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

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


pc = _load("probe_core")

VALIDATORS = {
    "categories": ["adjacency", "empty", "ordering"],
    "verification": ["explicit", "backstop"],
    "requiredFieldsByVerification": {"explicit": ["resolution"], "backstop": ["resolution"]},
}


def item(category, **overrides):
    return {"requirement_id": "R1", "category": category, "status": "unresolved", "verification": None,
            "resolution": None, "reason": None, "probe": f"probe-for-{category}", **overrides}


UNRESOLVED = [item("adjacency"), item("empty"), item("ordering")]


def res(category, status, **fields):
    return {"requirement_id": "R1", "category": category, "status": status, **fields}


class ValidStatusTests(unittest.TestCase):
    def test_exposes_exactly_the_recut_lifecycle(self):
        self.assertEqual(["dismissed", "resolved", "unresolved"], sorted(pc.VALID_STATUS))
        self.assertNotIn("covered", pc.VALID_STATUS)
        self.assertNotIn("backstop", pc.VALID_STATUS)


class ValidateResolutionTests(unittest.TestCase):
    def check(self, resolution):
        return pc.validate_resolution(resolution, VALIDATORS)

    def rejects(self, pattern, resolution):
        with self.assertRaisesRegex(ValueError, pattern):
            self.check(resolution)

    def test_rejects_unknown_status(self):
        self.rejects("(?i)invalid status", res("adjacency", "maybe"))

    def test_rejects_former_covered_status(self):
        self.rejects("(?i)invalid status", res("adjacency", "covered", resolution="x"))

    def test_dismissed_needs_reason(self):
        self.rejects("(?i)dismissed requires a reason", res("adjacency", "dismissed", reason=""))
        self.assertIs(True, self.check(res("adjacency", "dismissed", reason="bounded enum")))

    def test_resolved_needs_known_tier(self):
        self.rejects("(?i)verification", res("adjacency", "resolved", resolution="AC"))
        self.rejects("(?i)invalid verification", res("adjacency", "resolved", verification="judgment", resolution="AC"))

    def test_resolved_needs_resolution_text(self):
        self.rejects("(?i)explicit requires a resolution", res("adjacency", "resolved", verification="explicit", resolution="   "))
        self.rejects("(?i)backstop requires a resolution", res("adjacency", "resolved", verification="backstop"))

    def test_accepts_resolved_tiers(self):
        self.assertIs(True, self.check(res("adjacency", "resolved", verification="explicit", resolution="AC#6")))
        self.assertIs(True, self.check(res("adjacency", "resolved", verification="backstop", resolution="held-out PBT suite")))

    def test_verification_must_be_null_unless_resolved(self):
        self.rejects("(?i)verification must be null", res("adjacency", "dismissed", reason="n/a", verification="explicit"))
        self.rejects("(?i)verification must be null", res("adjacency", "unresolved", verification="backstop"))

    def test_unresolved_must_not_carry_payload(self):
        self.rejects("(?i)unresolved must not carry", res("adjacency", "unresolved", resolution="AC#1"))
        self.rejects("(?i)unresolved must not carry", res("adjacency", "unresolved", reason="because"))
        self.assertIs(True, self.check(res("adjacency", "unresolved")))

    def test_messages_match_upstream_text(self):
        with self.assertRaises(ValueError) as caught:
            self.check(res("adjacency", "resolved"))
        self.assertEqual("resolved requires a verification tier (one of: explicit, backstop) for R1::adjacency", str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            self.check(res("adjacency", "resolved", verification="judgment", resolution="AC"))
        self.assertEqual("invalid verification \"judgment\" for R1::adjacency — must be one of: explicit, backstop", str(caught.exception))


class ValidateRequirementTests(unittest.TestCase):
    def test_rejections(self):
        for requirement in ({"text": "x"}, {"id": "   ", "text": "x"}):
            with self.assertRaisesRegex(ValueError, "(?i)requirement id must be a non-empty string"):
                pc.validate_requirement(requirement)
        with self.assertRaisesRegex(ValueError, "(?i)text must be a string"):
            pc.validate_requirement({"id": "R1", "text": 42})

    def test_accepts_valid(self):
        self.assertIsNone(pc.validate_requirement({"id": "R1", "text": "a testable statement"}))


class AnalyzeCoverageTests(unittest.TestCase):
    def test_no_resolutions_zeroed_rollup(self):
        report = pc.analyze_coverage(UNRESOLVED, [], VALIDATORS)
        self.assertEqual({"applicable": 3, "resolved": 0, "unresolved": 3, "unclassified": 0,
                          "byVerification": {"explicit": 0, "backstop": 0}}, report["coverage"])

    def test_merges_resolved_explicit(self):
        report = pc.analyze_coverage(UNRESOLVED, [res("adjacency", "resolved", verification="explicit", resolution="AC#6: touching intervals merge")], VALIDATORS)
        adjacency = next(i for i in report["items"] if i["category"] == "adjacency")
        self.assertEqual(("resolved", "explicit", "AC#6: touching intervals merge"), (adjacency["status"], adjacency["verification"], adjacency["resolution"]))
        self.assertEqual((1, 2, {"explicit": 1, "backstop": 0}),
                         (report["coverage"]["resolved"], report["coverage"]["unresolved"], report["coverage"]["byVerification"]))
        self.assertEqual("unresolved", UNRESOLVED[0]["status"], "inputs are not mutated")

    def test_dismissed_is_closed_but_not_verified(self):
        report = pc.analyze_coverage(UNRESOLVED, [res("ordering", "dismissed", reason="canonically sorted; no tie")], VALIDATORS)
        self.assertEqual(1, report["coverage"]["resolved"])
        self.assertEqual({"explicit": 0, "backstop": 0}, report["coverage"]["byVerification"])
        ordering = next(i for i in report["items"] if i["category"] == "ordering")
        self.assertEqual(("dismissed", None, "canonically sorted; no tie"), (ordering["status"], ordering["verification"], ordering["reason"]))

    def test_mixed_resolutions(self):
        report = pc.analyze_coverage(UNRESOLVED, [
            res("adjacency", "resolved", verification="explicit", resolution="AC#6"),
            res("empty", "resolved", verification="backstop", resolution="held-out empty-input PBT"),
            res("ordering", "dismissed", reason="canonically sorted")], VALIDATORS)
        self.assertEqual((3, 0, 3), (report["coverage"]["applicable"], report["coverage"]["unresolved"], report["coverage"]["resolved"]))
        self.assertEqual({"explicit": 1, "backstop": 1}, report["coverage"]["byVerification"])

    def test_all_dismissed_is_closed_not_covered(self):
        report = pc.analyze_coverage(UNRESOLVED, [res("adjacency", "dismissed", reason="a"), res("empty", "dismissed", reason="b"),
                                                  res("ordering", "dismissed", reason="c")], VALIDATORS)
        self.assertEqual((0, 3), (report["coverage"]["unresolved"], report["coverage"]["resolved"]))
        self.assertEqual({"explicit": 0, "backstop": 0}, report["coverage"]["byVerification"])

    def test_rejects_duplicate_orphan_and_invalid(self):
        one = res("adjacency", "resolved", verification="explicit", resolution="AC#1")
        with self.assertRaisesRegex(ValueError, "(?i)duplicate resolution"):
            pc.analyze_coverage(UNRESOLVED, [one, {**one, "resolution": "AC#2"}], VALIDATORS)
        with self.assertRaisesRegex(ValueError, "(?i)unknown resolution|no matching proposed"):
            pc.analyze_coverage(UNRESOLVED, [res("boundary", "resolved", verification="explicit", resolution="AC")], VALIDATORS)
        with self.assertRaisesRegex(ValueError, "(?i)dismissed requires a reason"):
            pc.analyze_coverage(UNRESOLVED, [res("empty", "dismissed")], VALIDATORS)

    def test_rejects_non_array_items_and_unknown_category(self):
        with self.assertRaisesRegex(ValueError, "(?i)items must be an array"):
            pc.analyze_coverage("nope", [], VALIDATORS)
        with self.assertRaisesRegex(ValueError, "(?i)unknown category"):
            pc.analyze_coverage([item("bogus-category")], [], VALIDATORS)

    def test_verbatim_items_are_validated(self):
        with self.assertRaisesRegex(ValueError, "(?i)invalid status"):
            pc.analyze_coverage([item("adjacency", status="covered")], [], VALIDATORS)
        with self.assertRaisesRegex(ValueError, "(?i)dismissed requires a reason"):
            pc.analyze_coverage([item("adjacency", status="dismissed")], [], VALIDATORS)
        with self.assertRaisesRegex(ValueError, "(?i)requires a verification tier"):
            pc.analyze_coverage([item("adjacency", status="resolved", resolution="AC")], [], VALIDATORS)

    def test_matching_resolution_governs_prepopulated_item(self):
        report = pc.analyze_coverage([item("adjacency", status="covered")], [res("adjacency", "resolved", verification="explicit", resolution="AC#6")], VALIDATORS)
        self.assertEqual(("resolved", "explicit", 1), (report["items"][0]["status"], report["items"][0]["verification"], report["coverage"]["resolved"]))

    def test_unclassified_sibling_count(self):
        validators = {**VALIDATORS, "categories": ["idempotency", "ordering", "unclassified"]}
        report = pc.analyze_coverage([item("unclassified", requirement_id=name) for name in ("CONN-01", "CONN-02", "PJL-01")], [], validators)
        self.assertEqual((3, 3, 0, 3), tuple(report["coverage"][k] for k in ("applicable", "unclassified", "resolved", "unresolved")))
        report = pc.analyze_coverage([item("idempotency", requirement_id="A"), item("ordering", requirement_id="B")], [], validators)
        self.assertEqual((2, 0), (report["coverage"]["applicable"], report["coverage"]["unclassified"]))
        report = pc.analyze_coverage([], [], validators)
        self.assertEqual((0, 0), (report["coverage"]["applicable"], report["coverage"]["unclassified"]))
        report = pc.analyze_coverage([item("idempotency", requirement_id="A"), item("unclassified", requirement_id="B")], [], validators)
        self.assertEqual((2, 1, report["coverage"]["applicable"] - report["coverage"]["unresolved"]),
                         (report["coverage"]["applicable"], report["coverage"]["unclassified"], report["coverage"]["resolved"]))


class RunProbeCliTests(unittest.TestCase):
    REPORT = {"items": [], "coverage": {"applicable": 0, "resolved": 0, "unresolved": 0, "byVerification": {}}}

    def run_cli(self, analyze, argv, read_file=lambda path: "[]"):
        out, err, codes = [], [], []
        pc.run_probe_cli(analyze, "demo-probe.py <requirements.json> [resolutions.json]", argv=argv, read_file=read_file,
                         write=out.append, write_err=err.append, exit=codes.append)
        return "".join(out), "".join(err), codes

    def test_no_path_writes_usage_and_exits_2(self):
        out, err, codes = self.run_cli(lambda r, s: self.REPORT, [])
        self.assertEqual([2], codes)
        self.assertRegex(err, r"usage: demo-probe\.py")
        self.assertEqual("", out)

    def test_valid_path_prints_report(self):
        seen = []
        out, _, codes = self.run_cli(lambda r, s: (seen.append((r, s)), self.REPORT)[1], ["/fake/req.json"], lambda path: '[{"id":"R1","text":"x"}]')
        self.assertEqual([([{"id": "R1", "text": "x"}], [])], seen)
        self.assertEqual(self.REPORT, json.loads(out))
        self.assertTrue(out.endswith("\n"))
        self.assertEqual([], codes)

    def test_reads_optional_resolutions(self):
        seen = []
        self.run_cli(lambda r, s: (seen.append(s), self.REPORT)[1], ["/req.json", "/res.json"],
                     lambda path: '[{"requirement_id":"R1"}]' if path == "/res.json" else '[{"id":"R1"}]')
        self.assertEqual([[{"requirement_id": "R1"}]], seen)

    def test_invalid_json_exits_2(self):
        _, err, codes = self.run_cli(lambda r, s: self.REPORT, ["/req.json"], lambda path: "not json {{{")
        self.assertEqual([2], codes)
        self.assertIn("cannot parse JSON from /req.json", err)
        _, err, codes = self.run_cli(lambda r, s: self.REPORT, ["/req.json", "/res.json"], lambda path: "[]" if path == "/req.json" else "{{")
        self.assertEqual([2], codes)
        self.assertIn("cannot parse JSON from /res.json", err)

    def test_analyze_exception_exits_2(self):
        def boom(r, s):
            raise ValueError("boom")
        _, err, codes = self.run_cli(boom, ["/req.json"])
        self.assertEqual(([2], "error: boom\n"), (codes, err))

    def test_structurally_invalid_reports_exit_2_and_write_nothing(self):
        bad_item = {"items": [{}], "coverage": {"applicable": 0, "resolved": 0, "unresolved": 0, "byVerification": {}}}
        for report in ({"nope": True}, {"items": [], "coverage": {"applicable": "x", "resolved": None, "unresolved": None, "byVerification": {}}}, bad_item):
            out, _, codes = self.run_cli(lambda r, s, report=report: report, ["/req.json"])
            self.assertEqual(([2], ""), (codes, out))

    def test_fully_formed_item_still_writes(self):
        good = {"items": [{"requirement_id": "R1", "category": "empty", "status": "unresolved", "verification": None,
                           "resolution": None, "reason": None, "probe": "edge"}],
                "coverage": {"applicable": 1, "resolved": 0, "unresolved": 1, "byVerification": {}}}
        out, _, codes = self.run_cli(lambda r, s: good, ["/req.json"])
        self.assertEqual((good, []), (json.loads(out), codes))

    def test_default_exit_raises_exit_error(self):
        with self.assertRaises(pc.ExitError) as caught:
            pc.run_probe_cli(lambda r, s: self.REPORT, "demo", argv=[], write_err=lambda text: None)
        self.assertEqual(2, caught.exception.code)

    def test_default_io_reads_real_files(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"req.json"
            path.write_text("[]", encoding="utf-8")
            out = []
            pc.run_probe_cli(lambda r, s: self.REPORT, "demo", argv=[str(path)], write=out.append)
            self.assertEqual(self.REPORT, json.loads("".join(out)))


class ProjectProhibitionsTests(unittest.TestCase):
    def test_descriptor_less_shape_is_byte_stable(self):
        projected = pc.project_prohibitions([
            {"requirement_id": "R1", "category": "values", "status": "resolved", "verification": "judgment", "resolution": None, "reason": None, "statement": "MUST NOT shame the user"},
            {"requirement_id": "R1", "category": "privacy", "status": "dismissed", "verification": "test", "resolution": None, "reason": "out of scope this phase", "statement": "MUST NOT store raw SSN"},
            {"requirement_id": "R2", "category": "safety", "status": "unresolved", "verification": None, "resolution": None, "reason": None, "statement": "MUST NOT auto-execute fetched code"}])
        self.assertEqual([
            {"statement": "MUST NOT shame the user", "status": "resolved", "verification": "judgment"},
            {"statement": "MUST NOT store raw SSN", "status": "dismissed", "verification": "test", "reason": "out of scope this phase"},
            {"statement": "MUST NOT auto-execute fetched code", "status": "unresolved"}], projected)
        for entry in projected:
            self.assertFalse(any(key.startswith("check_") for key in entry))
        self.assertEqual(["statement", "status", "verification", "reason"], list(projected[1]))

    def test_non_list_and_non_object_inputs(self):
        self.assertEqual([], pc.project_prohibitions("nope"))
        self.assertEqual([], pc.project_prohibitions(None))
        self.assertEqual([{"statement": "", "status": "unresolved"}], pc.project_prohibitions([{}, 5, None]))

    def test_node_test_descriptor(self):
        projected = pc.project_prohibitions([{"status": "resolved", "verification": "test", "statement": "S", "check_kind": "node-test",
                                              "check_target": "tests/no-autoexec.test.cjs", "check_rule": "ignored"}])
        self.assertEqual({"check_kind": "node-test", "check_target": "tests/no-autoexec.test.cjs"},
                         {k: v for k, v in projected[0].items() if k.startswith("check_")})

    def test_lint_rule_descriptor(self):
        base = {"status": "resolved", "verification": "test", "statement": "S", "check_kind": "lint-rule", "check_target": "src/"}
        full = pc.project_prohibitions([{**base, "check_rule": "local/no-source-grep"}])[0]
        self.assertEqual(("lint-rule", "src/", "local/no-source-grep"), (full["check_kind"], full["check_target"], full["check_rule"]))
        self.assertNotIn("check_rule", pc.project_prohibitions([base])[0])

    def test_fixtures_ride_both_kinds_when_nonblank(self):
        for kind, extra in (("node-test", {}), ("lint-rule", {"check_rule": "r"})):
            entry = pc.project_prohibitions([{"status": "resolved", "statement": "S", "check_kind": kind, "check_target": "t",
                                              "check_violation_fixture": "bad.txt", "check_clean_fixture": "clean.txt", **extra}])[0]
            self.assertEqual(("bad.txt", "clean.txt"), (entry["check_violation_fixture"], entry["check_clean_fixture"]))
        blank = pc.project_prohibitions([{"status": "resolved", "statement": "S", "check_kind": "node-test", "check_target": "t",
                                          "check_violation_fixture": "   ", "check_clean_fixture": "   "}])[0]
        self.assertFalse({"check_violation_fixture", "check_clean_fixture"} & set(blank))

    def test_fixtures_without_descriptor_do_not_leak(self):
        entry = pc.project_prohibitions([{"status": "resolved", "statement": "S", "check_violation_fixture": "bad", "check_clean_fixture": "clean"}])[0]
        self.assertFalse(any(key.startswith("check_") for key in entry))

    def test_under_specified_descriptor_emits_nothing(self):
        for item_ in ({"check_kind": "node-test", "check_target": "   "}, {"check_kind": "grep-rule", "check_target": "src/"}, {"check_kind": "node-test"}):
            entry = pc.project_prohibitions([{"status": "resolved", "verification": "test", "statement": "S", **item_}])[0]
            self.assertFalse(any(key.startswith("check_") for key in entry))

    def test_validate_prohibition_resolution(self):
        self.assertIs(True, pc.validate_prohibition_resolution(res("values", "resolved", verification="judgment")))
        self.assertIs(True, pc.validate_prohibition_resolution(res("values", "resolved", verification="test", resolution=None)))
        with self.assertRaisesRegex(ValueError, "invalid verification"):
            pc.validate_prohibition_resolution(res("values", "resolved", verification="explicit"))
        with self.assertRaisesRegex(ValueError, "dismissed requires a reason"):
            pc.validate_prohibition_resolution(res("values", "dismissed"))
        self.assertEqual([], pc.PROHIBITION_VALIDATORS["categories"])


class DispositionTests(unittest.TestCase):
    def test_prohibition_without_evidence_is_flagged_unverified(self):
        for evidence in ([], None):
            context = {} if evidence is None else {"enforcementEvidence": evidence}
            disposition = pc.disposition_for_prohibition({"status": "resolved", "verification": "test", "statement": "S"}, context)
            self.assertEqual(("unverified", True, "test"), (disposition["status"], disposition["flagged"], disposition["tier"]))
            self.assertIn("test-tier prohibition has no passing wired enforcement check", disposition["reason"])
        judgment = pc.disposition_for_prohibition({"verification": "judgment"})
        self.assertEqual(("unverified", True, "judgment"), (judgment["status"], judgment["flagged"], judgment["tier"]))
        self.assertTrue(judgment["reason"].startswith("prohibition has no enforcement evidence"))

    def test_prohibition_with_evidence(self):
        evidence = {"enforcementEvidence": [{"passed": True}]}
        green = pc.disposition_for_prohibition({"verification": "test"}, evidence)
        self.assertEqual(("green", False, "test"), (green["status"], green["flagged"], green["tier"]))
        judgment = pc.disposition_for_prohibition({"verification": "judgment"}, evidence)
        self.assertEqual(("unverified", True, "judgment"), (judgment["status"], judgment["flagged"], judgment["tier"]))
        unknown = pc.disposition_for_prohibition({"verification": "weird"}, evidence)
        self.assertEqual(("unverified", True, None), (unknown["status"], unknown["flagged"], unknown["tier"]))
        self.assertEqual("unverified", pc.disposition_for_prohibition(None)["status"])

    def test_truth_normalizers(self):
        self.assertEqual("Overlapping intervals are merged", pc.truth_statement("Overlapping intervals are merged"))
        self.assertEqual("Adjacent intervals merge", pc.truth_statement({"statement": "Adjacent intervals merge", "verification": "backstop"}))
        self.assertEqual("", pc.truth_statement(None))
        self.assertEqual("backstop", pc.truth_verification({"statement": "Adjacent", "verification": "backstop"}))
        self.assertIsNone(pc.truth_verification("plain"))
        self.assertEqual("explicit", pc.truth_verification({"statement": "x", "verification": "explicit"}))

    def test_truth_verification_tolerates_hand_authored_markers(self):
        for raw, expected in (("backstop ", "backstop"), (" backstop", "backstop"), ('"backstop"', "backstop"),
                              ("explicit ", "explicit"), ('back"stop', None), (5, None)):
            self.assertEqual(expected, pc.truth_verification({"statement": "x", "verification": raw}), raw)

    def test_backstop_truth_abstains_without_evidence(self):
        truth = {"statement": "Adjacent/touching intervals [1,2],[2,3] merge", "verification": "backstop"}
        disposition = pc.disposition_for_unverifiable_truth(truth, {"evidence": []})
        self.assertEqual({"status": "unverified", "flagged": True, "tier": "backstop", "reason": "insufficient_spec"}, disposition)
        self.assertEqual("insufficient_spec", pc.INSUFFICIENT_SPEC)
        self.assertEqual("unverified", pc.disposition_for_unverifiable_truth(truth)["status"])

    def test_backstop_truth_with_evidence_is_green(self):
        disposition = pc.disposition_for_unverifiable_truth({"statement": "s", "verification": "backstop"},
                                                            {"evidence": [{"test": "tests/intervals.property.test.cjs", "passed": True}]})
        self.assertEqual(("green", False, "backstop"), (disposition["status"], disposition["flagged"], disposition["tier"]))

    def test_inferable_truths_never_abstain(self):
        self.assertEqual(("green", False), tuple(pc.disposition_for_unverifiable_truth("plain", {"evidence": []})[k] for k in ("status", "flagged")))
        explicit = pc.disposition_for_unverifiable_truth({"statement": "s", "verification": "explicit"}, {"evidence": []})
        self.assertEqual(("green", False), (explicit["status"], explicit["flagged"]))

    def test_whitespace_mangled_backstop_still_abstains(self):
        disposition = pc.disposition_for_unverifiable_truth({"statement": "user data is never logged", "verification": "backstop "}, {"evidence": []})
        self.assertEqual(("unverified", True, "backstop", "insufficient_spec"), tuple(disposition[k] for k in ("status", "flagged", "tier", "reason")))

    def test_project_truths(self):
        self.assertEqual([{"statement": "Adjacent intervals merge", "verification": "backstop"}, "Overlapping intervals are merged", "Symbol X is wired"],
                         pc.project_truths([{"statement": "Adjacent intervals merge", "verification": "backstop"}, "Overlapping intervals are merged",
                                            {"statement": "Symbol X is wired", "verification": "explicit"}, "", {"verification": "backstop"}]))
        self.assertEqual([], pc.project_truths("nope"))


class AnalyzeCoveragePropertyTests(unittest.TestCase):
    """Seeded randomized checks of the algebraic invariants (upstream used fast-check)."""
    DISPOSITIONS = ("none", "resolved-explicit", "resolved-backstop", "dismissed", "unresolved")

    def scenario(self, rng):
        keys = sorted({(rng.choice(["R1", "R2", "R3", "R4", "R5"]), rng.choice(VALIDATORS["categories"])) for _ in range(rng.randint(0, 12))})
        items, resolutions = [], []
        for requirement_id, category in keys:
            items.append(item(category, requirement_id=requirement_id))
            base = {"requirement_id": requirement_id, "category": category}
            choice = rng.choice(self.DISPOSITIONS)
            if choice == "resolved-explicit":
                resolutions.append({**base, "status": "resolved", "verification": "explicit", "resolution": "AC#1"})
            elif choice == "resolved-backstop":
                resolutions.append({**base, "status": "resolved", "verification": "backstop", "resolution": "held-out PBT suite"})
            elif choice == "dismissed":
                resolutions.append({**base, "status": "dismissed", "reason": "bounded enum"})
            elif choice == "unresolved":
                resolutions.append({**base, "status": "unresolved"})
        return items, resolutions

    def test_invariants(self):
        rng = random.Random(550)
        for _ in range(200):
            items, resolutions = self.scenario(rng)
            report = pc.analyze_coverage(items, resolutions, VALIDATORS)
            coverage = report["coverage"]
            self.assertEqual(coverage["applicable"], coverage["resolved"] + coverage["unresolved"])
            self.assertEqual(len(items), coverage["applicable"])
            self.assertLessEqual(sum(coverage["byVerification"].values()), coverage["resolved"])
            for tier in VALIDATORS["verification"]:
                recount = sum(1 for i in report["items"] if i["status"] == "resolved" and i["verification"] == tier)
                self.assertEqual(recount, coverage["byVerification"][tier])
            self.assertEqual(json.dumps(report), json.dumps(pc.analyze_coverage(items, resolutions, VALIDATORS)))

    def test_orphan_always_throws(self):
        rng = random.Random(644)
        for _ in range(100):
            items, _ = self.scenario(rng)
            orphan = {"requirement_id": "Z9", "category": rng.choice(VALIDATORS["categories"]), "status": "unresolved"}
            with self.assertRaisesRegex(ValueError, "(?i)unknown resolution|no matching proposed item"):
                pc.analyze_coverage(items, [orphan], VALIDATORS)


class ModuleTests(unittest.TestCase):
    def test_module_has_no_cli(self):
        process = subprocess.run([sys.executable, "-I", "-c", "import sys; sys.path.insert(0, sys.argv[1]); import lib.probe_core",
                                  str(ROOT/"engineer/bin")], capture_output=True, text=True)
        self.assertEqual(0, process.returncode, process.stderr)


if __name__ == "__main__":
    unittest.main()
