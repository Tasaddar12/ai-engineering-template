"""Ported from gsd-core tests/code-review-depth.test.cjs (pinned d37ff11b).

The upstream config-registration tests (CLI config-set/get round trip) exercise
the JavaScript gsd-tools binary and have no counterpart for this pure module.
Property tests use the stdlib ``random`` module with a fixed seed.
"""
import copy
from pathlib import Path
import random
import string
import sys
import unittest

import importlib
import importlib.util

LIB = Path(__file__).resolve().parents[1]/"engineer/bin/lib"


def _load(name):
    # Load engineer/bin/lib as an isolated package: ".ai/runtime/lib" is also named "lib".
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib."+name)

_module = _load("code_review_depth")
DEPTH_TIERS, LARGE_SCOPE_THRESHOLD, REASON = _module.DEPTH_TIERS, _module.LARGE_SCOPE_THRESHOLD, _module.REASON
normalize_rel_path, resolve_code_review_depth, rule_matches_file = _module.normalize_rel_path, _module.resolve_code_review_depth, _module.rule_matches_file


_DEFAULT = object()


def resolve(overrides=_DEFAULT, files=(), flag="", config="", root="/repo", omit_overrides=False):
    payload = {"flagDepth": flag, "configDepth": config, "files": list(files), "repoRoot": root}
    if not omit_overrides:
        payload["overrides"] = [] if overrides is _DEFAULT else overrides
    return resolve_code_review_depth(payload)


def rule(*paths, depth="deep"):
    return {"paths": list(paths), "depth": depth}


class ReasonEnum(unittest.TestCase):
    def test_reason_is_frozen_with_nine_keys(self):
        self.assertEqual(sorted(["GLOB_UNSUPPORTED", "INVALID_DEPTH", "NOT_AN_ARRAY", "PATHS_MALFORMED", "PATH_ABSOLUTE",
                                 "PATH_CONTROL_CHAR", "PATH_EMPTY", "PATH_TRAVERSAL", "RULE_NOT_OBJECT"]), sorted(REASON))
        with self.assertRaises(TypeError):
            REASON["X"] = "x"
        self.assertEqual("not_an_array", REASON["NOT_AN_ARRAY"])

    def test_constants(self):
        self.assertEqual(("quick", "standard", "deep"), DEPTH_TIERS)
        self.assertEqual(50, LARGE_SCOPE_THRESHOLD)


class ResolutionOrder(unittest.TestCase):
    def test_default(self):
        result = resolve(files=["src/lib/a.ts"])
        self.assertEqual((True, "standard", "default"), (result["ok"], result["depth"], result["source"]))

    def test_config(self):
        result = resolve(files=["src/lib/a.ts"], config="deep")
        self.assertEqual((True, "deep", "config"), (result["ok"], result["depth"], result["source"]))

    def test_rule_escalates(self):
        result = resolve([rule("src/auth")], ["src/auth/x.ts"])
        self.assertEqual((True, "deep", "rule"), (result["ok"], result["depth"], result["source"]))
        self.assertEqual({"index": 0, "path": "src/auth", "depth": "deep"}, result["matchedRule"])

    def test_unmatched_rule_ignored(self):
        result = resolve([rule("src/auth")], ["src/billing/x.ts"])
        self.assertEqual(("standard", "default", None), (result["depth"], result["source"], result["matchedRule"]))

    def test_single_matched_file_escalates(self):
        result = resolve([rule("src/auth")], ["src/lib/a.ts", "src/auth/x.ts"])
        self.assertEqual(("deep", "rule"), (result["depth"], result["source"]))

    def test_strongest_tier_wins(self):
        result = resolve([rule("src/lib", depth="quick"), rule("src/auth")], ["src/lib/a.ts", "src/auth/x.ts"])
        self.assertEqual(("deep", "rule", "src/auth"), (result["depth"], result["source"], result["matchedRule"]["path"]))

    def test_first_rule_at_winning_tier(self):
        result = resolve([rule("src/auth"), rule("src/billing")], ["src/auth/x.ts", "src/billing/y.ts"])
        self.assertEqual({"index": 0, "path": "src/auth", "depth": "deep"}, result["matchedRule"])

    def test_matching_rule_replaces_global_even_when_weaker(self):
        result = resolve([rule("src/auth", depth="quick")], ["src/auth/x.ts"], config="deep")
        self.assertEqual(("quick", "rule"), (result["depth"], result["source"]))

    def test_flag_outranks_rules(self):
        result = resolve([rule("src/auth", depth="quick")], ["src/auth/x.ts"], flag="deep")
        self.assertEqual(("deep", "flag"), (result["depth"], result["source"]))

    def test_rules_validated_even_when_flag_wins(self):
        result = resolve([rule("src/auth", depth="not-a-tier")], ["src/auth/x.ts"], flag="deep")
        self.assertFalse(result["ok"])
        self.assertEqual(REASON["INVALID_DEPTH"], result["errors"][0]["reason"])

    def test_invalid_flag_depth_falls_back_to_standard(self):
        result = resolve(files=["a"], flag="bogus", config="deep")
        self.assertEqual(("standard", "flag", True), (result["depth"], result["source"], result["invalidFlagDepth"]))
        self.assertNotIn("invalidConfigDepth", result)

    def test_invalid_config_depth_falls_back_to_standard(self):
        result = resolve(files=["a"], config="bogus")
        self.assertEqual(("standard", "config", True), (result["depth"], result["source"], result["invalidConfigDepth"]))
        self.assertNotIn("invalidFlagDepth", result)

    def test_ok_result_shape(self):
        self.assertEqual({"ok": True, "depth": "standard", "resolvedDepth": "standard", "source": "default",
                          "matchedRule": None, "downgraded": False, "fileCount": 1}, resolve(files=["a"]))

    def test_non_string_flag_and_config_are_ignored(self):
        result = resolve_code_review_depth({"flagDepth": None, "configDepth": None, "files": []})
        self.assertEqual(("standard", "default"), (result["depth"], result["source"]))


class SegmentAwareMatching(unittest.TestCase):
    def test_sibling_prefix_does_not_match(self):
        result = resolve([rule("src/auth")], ["src/authfoo/x.ts"])
        self.assertEqual(("standard", None), (result["depth"], result["matchedRule"]))

    def test_anchored_at_root(self):
        result = resolve([rule("src/auth")], ["docs/src/auth/x.ts"])
        self.assertEqual(("standard", None), (result["depth"], result["matchedRule"]))

    def test_trailing_slash_insignificant(self):
        self.assertEqual(resolve([rule("src/auth/")], ["src/auth/x.ts"]), resolve([rule("src/auth")], ["src/auth/x.ts"]))

    def test_file_shaped_rule_matches_exact_file(self):
        hit = resolve([rule("src/auth.ts")], ["src/auth.ts"])
        self.assertEqual(("deep", "rule"), (hit["depth"], hit["source"]))
        miss = resolve([rule("src/auth.ts")], ["src/auth/x.ts"])
        self.assertEqual(("standard", None), (miss["depth"], miss["matchedRule"]))

    def test_rule_matches_file_function(self):
        self.assertTrue(rule_matches_file("a/b", "a/b"))
        self.assertTrue(rule_matches_file("a/b", "a/b/c"))
        self.assertFalse(rule_matches_file("a/b", "a/bc"))
        self.assertFalse(rule_matches_file("a/b", "x/a/b"))
        self.assertFalse(rule_matches_file("a/b", "A/b"))


class PathNormalization(unittest.TestCase):
    def test_leading_dot_slash(self):
        self.assertEqual("deep", resolve([rule("src/auth")], ["./src/auth/x.ts"])["depth"])

    def test_backslashes_in_file(self):
        self.assertEqual("deep", resolve([rule("src/auth")], ["src\\auth\\x.ts"])["depth"])

    def test_backslashes_in_rule(self):
        self.assertEqual("deep", resolve([rule("src\\auth")], ["src/auth/x.ts"])["depth"])

    def test_absolute_under_root_relativized(self):
        result = resolve([rule("src/auth")], ["/repo/src/auth/x.ts"])
        self.assertEqual(("deep", "rule"), (result["depth"], result["source"]))

    def test_absolute_outside_root_does_not_match(self):
        for outside in ("/home/user/.claude/notes.md", "/src/auth/x.ts"):
            result = resolve([rule("src/auth")], [outside])
            self.assertEqual(("standard", None), (result["depth"], result["matchedRule"]), outside)
        inside = resolve([rule("src/auth")], ["/repo/src/auth/x.ts"])
        self.assertEqual("src/auth", inside["matchedRule"]["path"])
        self.assertEqual("/src/auth/x.ts", normalize_rel_path("/src/auth/x.ts", "/repo"))

    def test_normalize_rel_path_cases(self):
        self.assertEqual("", normalize_rel_path(None))
        self.assertEqual("", normalize_rel_path(42))
        self.assertEqual("a/b", normalize_rel_path("  ./././a//b/\r\n"))
        self.assertEqual("/a/b", normalize_rel_path("/a/b"))
        self.assertEqual("a/b", normalize_rel_path("/repo/a/b", "/repo"))
        self.assertEqual("/", normalize_rel_path("/", "/repo"))
        self.assertEqual("C:/x/y", normalize_rel_path("C:\\x\\y"))
        self.assertEqual("src/a.ts", normalize_rel_path("C:\\repo\\src\\a.ts", "C:\\repo\\"))
        self.assertEqual("a", normalize_rel_path("a/", ""))
        self.assertEqual("a/b", normalize_rel_path("\ufeffa/b\u00a0"))

    def test_normalize_is_idempotent(self):
        for value in ("./a//b/", "/repo/x/y", "C:\\a\\b", "../a", "/a"):
            once = normalize_rel_path(value, "/repo")
            self.assertEqual(once, normalize_rel_path(once, "/repo"), value)


class EmptyInputs(unittest.TestCase):
    def test_empty_file_set(self):
        result = resolve([rule("src/auth")], [])
        self.assertEqual(("standard", "default", 0, None), (result["depth"], result["source"], result["fileCount"], result["matchedRule"]))

    def test_empty_rules_equal_absent_overrides(self):
        empty = resolve([], ["src/lib/a.ts"], config="quick")
        absent = resolve(files=["src/lib/a.ts"], config="quick", omit_overrides=True)
        self.assertEqual(("quick", "config"), (empty["depth"], empty["source"]))
        self.assertEqual(empty, absent)


class MalformedRulePaths(unittest.TestCase):
    def reason(self, bad_path):
        result = resolve([rule(bad_path)])
        self.assertFalse(result["ok"], repr(bad_path))
        return result["errors"][0]["reason"]

    def test_glob(self):
        result = resolve([rule("src/auth/**")], ["src/auth/x.ts"])
        self.assertEqual((False, REASON["GLOB_UNSUPPORTED"], 0), (result["ok"], result["errors"][0]["reason"], result["errors"][0]["ruleIndex"]))
        self.assertEqual("src/auth/**", result["errors"][0]["path"])
        self.assertEqual(REASON["GLOB_UNSUPPORTED"], self.reason("src/*.ts"))
        self.assertEqual(REASON["GLOB_UNSUPPORTED"], self.reason("a?b"))

    def test_traversal(self):
        for bad in ("../etc", "src/../../etc"):
            self.assertEqual(REASON["PATH_TRAVERSAL"], self.reason(bad))

    def test_absolute(self):
        for bad in ("/etc/passwd", "C:\\Windows"):
            self.assertEqual(REASON["PATH_ABSOLUTE"], self.reason(bad))

    def test_empty(self):
        for bad in ("", "   ", "/", ".", "./"):
            self.assertEqual(REASON["PATH_EMPTY"], self.reason(bad))

    def test_trims_whitespace_and_cr(self):
        result = resolve([rule("  src/auth\r\n")], ["src/auth/x.ts"])
        self.assertEqual(("deep", "src/auth"), (result["depth"], result["matchedRule"]["path"]))

    def test_interior_control_characters(self):
        for bad in ("src/au\nth", "src/au\rth", "src/au\tth", "src/au\x7fth"):
            self.assertEqual(REASON["PATH_CONTROL_CHAR"], self.reason(bad), repr(bad))

    def test_glob_precedes_control_char(self):
        self.assertEqual(REASON["GLOB_UNSUPPORTED"], self.reason("src/*\nauth"))

    def test_only_first_bad_path_in_rule_is_reported(self):
        result = resolve([rule("../a", "b/*")])
        self.assertEqual(1, len(result["errors"]))
        self.assertEqual(REASON["PATH_TRAVERSAL"], result["errors"][0]["reason"])


class MalformedRuleShapes(unittest.TestCase):
    def test_invalid_depth(self):
        for bad in ("light", "DEEP", ""):
            result = resolve([rule("src/auth", depth=bad)])
            self.assertFalse(result["ok"], bad)
            self.assertEqual(REASON["INVALID_DEPTH"], result["errors"][0]["reason"])
            self.assertEqual(bad, result["errors"][0]["value"])

    def test_missing_depth(self):
        result = resolve([{"paths": ["src/auth"]}])
        self.assertEqual(REASON["INVALID_DEPTH"], result["errors"][0]["reason"])
        self.assertNotIn("value", result["errors"][0])

    def test_non_string_depth(self):
        self.assertEqual(REASON["INVALID_DEPTH"], resolve([{"paths": ["a"], "depth": 3}])["errors"][0]["reason"])

    def test_paths_absent_empty_or_not_array(self):
        for bad in ({"depth": "deep"}, {"paths": [], "depth": "deep"}, {"paths": "src", "depth": "deep"}):
            result = resolve([bad])
            self.assertFalse(result["ok"], bad)
            self.assertEqual(REASON["PATHS_MALFORMED"], result["errors"][0]["reason"])

    def test_paths_with_non_string(self):
        for bad in (["ok", 42], ["ok", None]):
            result = resolve([{"paths": bad, "depth": "deep"}])
            self.assertEqual(REASON["PATHS_MALFORMED"], result["errors"][0]["reason"])

    def test_overrides_not_array(self):
        for bad in ({}, "deep", 0, True, None):
            result = resolve(bad, [])
            self.assertFalse(result["ok"], repr(bad))
            self.assertEqual([{"reason": REASON["NOT_AN_ARRAY"]}], result["errors"])

    def test_rule_not_object(self):
        for bad in ("src/auth", [], None, 0):
            result = resolve([bad])
            self.assertEqual({"reason": REASON["RULE_NOT_OBJECT"], "ruleIndex": 0}, result["errors"][0], repr(bad))

    def test_reports_every_malformed_rule(self):
        result = resolve([rule("src/auth/**"), rule("src/billing", depth="nonsense")])
        self.assertFalse(result["ok"])
        self.assertEqual([(REASON["GLOB_UNSUPPORTED"], 0), (REASON["INVALID_DEPTH"], 1)],
                         [(e["reason"], e["ruleIndex"]) for e in result["errors"]])


class HostileInput(unittest.TestCase):
    def test_proto_key_is_inert(self):
        hostile = {"__proto__": {"polluted": True}, "paths": ["src/auth"], "depth": "deep"}
        result = resolve([hostile], ["src/auth/x.ts"])
        self.assertIn(result["ok"], (True, False))
        self.assertFalse(hasattr({}, "polluted"))

    def test_unusual_but_well_formed_paths(self):
        rule_path = "caf\u00e9/\u65e5\u672c\u8a9e dir/" + "a"*4096
        result = resolve([rule(rule_path)], [rule_path + "/x.ts"])
        self.assertEqual((True, "deep", "rule"), (result["ok"], result["depth"], result["source"]))


class LargeScopeDowngrade(unittest.TestCase):
    @staticmethod
    def under(path, count):
        return [f"{path}/f{i}.ts" for i in range(count)]

    def test_boundary(self):
        for count, downgraded in ((LARGE_SCOPE_THRESHOLD - 1, False), (LARGE_SCOPE_THRESHOLD, False), (LARGE_SCOPE_THRESHOLD + 1, True)):
            result = resolve([rule("src/auth")], self.under("src/auth", count))
            self.assertEqual("deep", result["resolvedDepth"])
            self.assertEqual(downgraded, result["downgraded"])
            self.assertEqual("standard" if downgraded else "deep", result["depth"])
            self.assertEqual("rule", result["source"])
            self.assertEqual({"index": 0, "path": "src/auth", "depth": "deep"}, result["matchedRule"])

    def test_flag_deep_downgraded_without_rule(self):
        result = resolve(files=self.under("src/misc", LARGE_SCOPE_THRESHOLD + 1), flag="deep")
        self.assertEqual(("standard", "deep", True, "flag", None),
                         (result["depth"], result["resolvedDepth"], result["downgraded"], result["source"], result["matchedRule"]))

    def test_non_deep_left_alone(self):
        result = resolve(files=self.under("src/misc", LARGE_SCOPE_THRESHOLD + 1), config="standard")
        self.assertEqual(("standard", "standard", False), (result["depth"], result["resolvedDepth"], result["downgraded"]))


class Independence(unittest.TestCase):
    def test_does_not_mutate_inputs(self):
        overrides = [rule("src/auth")]
        files = ["src/auth/x.ts", "src/lib/a.ts"]
        snapshot = copy.deepcopy((overrides, files))
        first = resolve(overrides, files)
        second = resolve(overrides, files)
        self.assertEqual(snapshot, (overrides, files))
        self.assertEqual(first, second)


class Properties(unittest.TestCase):
    ALNUM = string.ascii_letters + string.digits

    def setUp(self):
        self.rng = random.Random(25540)

    def segment(self):
        return "".join(self.rng.choice(self.ALNUM) for _ in range(self.rng.randint(1, 8)))

    def path(self, low=1, high=3):
        return "/".join(self.segment() for _ in range(self.rng.randint(low, high)))

    def test_successful_resolution_is_consistent(self):
        for _ in range(200):
            overrides = [{"paths": [self.path() for _ in range(self.rng.randint(1, 2))], "depth": self.rng.choice(DEPTH_TIERS)}
                         for _ in range(self.rng.randint(0, 4))]
            files = [self.path(1, 5) for _ in range(self.rng.randint(0, 10))]
            result = resolve(overrides, files, config=self.rng.choice(DEPTH_TIERS))
            self.assertTrue(result["ok"])
            self.assertIn(result["depth"], DEPTH_TIERS)
            if result["source"] == "rule":
                self.assertIsNotNone(result["matchedRule"])
                self.assertEqual(result["depth"], result["matchedRule"]["depth"])

    def test_prefix_matching_is_segment_aware(self):
        for _ in range(200):
            base, suffix = self.path(), self.segment()
            self.assertTrue(rule_matches_file(base, f"{base}/{suffix}"))
            self.assertFalse(rule_matches_file(base, f"{base}{suffix}"))

    def test_non_array_overrides_rejected(self):
        for _ in range(200):
            bad = self.rng.choice([self.rng.randint(-1000, 1000), self.segment(), self.rng.random() < 0.5, None,
                                   {self.segment(): self.rng.randint(0, 9)}])
            result = resolve(bad, [])
            self.assertFalse(result["ok"])
            self.assertEqual(REASON["NOT_AN_ARRAY"], result["errors"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
