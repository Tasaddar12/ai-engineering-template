"""Ported from gsd-core tests/code-review-flags.test.cjs (pinned d37ff11b)."""
from pathlib import Path
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

_module = _load("code_review_flags")
parse_code_review_flags = _module.parse_code_review_flags
resolve_code_review_workflow = _module.resolve_code_review_workflow

DEFAULTS = {"fix": False, "all": False, "auto": False, "depth": "", "files": ""}


class ParseCodeReviewFlags(unittest.TestCase):
    def test_no_flags_all_defaults(self):
        self.assertEqual(DEFAULTS, parse_code_review_flags([]))

    def test_fix(self):
        flags = parse_code_review_flags(["--fix"])
        self.assertEqual((True, False, False), (flags["fix"], flags["all"], flags["auto"]))

    def test_all_implies_fix(self):
        flags = parse_code_review_flags(["--all"])
        self.assertEqual((True, True, False), (flags["fix"], flags["all"], flags["auto"]))

    def test_auto_implies_fix(self):
        flags = parse_code_review_flags(["--auto"])
        self.assertEqual((True, False, True), (flags["fix"], flags["all"], flags["auto"]))

    def test_depth_and_files(self):
        self.assertEqual("high", parse_code_review_flags(["--depth=high"])["depth"])
        self.assertEqual("src/foo", parse_code_review_flags(["--files=src/foo"])["files"])

    def test_empty_depth_value(self):
        self.assertEqual("", parse_code_review_flags(["--depth="])["depth"])

    def test_phase_positional_ignored(self):
        self.assertEqual({**DEFAULTS, "fix": True}, parse_code_review_flags(["2", "--fix"]))

    def test_unknown_flags_ignored(self):
        self.assertEqual(DEFAULTS, parse_code_review_flags(["--unknown"]))

    def test_combined(self):
        self.assertEqual({"fix": True, "all": True, "auto": False, "depth": "deep", "files": "a.ts"},
                         parse_code_review_flags(["3", "--all", "--depth=deep", "--files=a.ts"]))

    def test_all_three_flags(self):
        flags = parse_code_review_flags(["1", "--fix", "--all", "--auto"])
        self.assertEqual((True, True, True), (flags["fix"], flags["all"], flags["auto"]))
        self.assertEqual("code-review-fix.md", resolve_code_review_workflow(flags))

    def test_depth_and_files_with_fix(self):
        flags = parse_code_review_flags(["2", "--depth=deep", "--files=src/foo.ts,src/bar.ts", "--fix"])
        self.assertEqual((True, "deep", "src/foo.ts,src/bar.ts"), (flags["fix"], flags["depth"], flags["files"]))

    def test_later_value_wins_and_equals_kept(self):
        flags = parse_code_review_flags(["--depth=a", "--depth=b=c"])
        self.assertEqual("b=c", flags["depth"])

    def test_space_separated_value_is_not_parsed(self):
        flags = parse_code_review_flags(["--depth", "deep"])
        self.assertEqual("", flags["depth"])


class ResolveCodeReviewWorkflow(unittest.TestCase):
    def test_fix_true(self):
        self.assertEqual("code-review-fix.md", resolve_code_review_workflow({**DEFAULTS, "fix": True}))

    def test_fix_false(self):
        self.assertEqual("code-review.md", resolve_code_review_workflow(DEFAULTS))

    def test_dispatch_from_argv(self):
        self.assertEqual("code-review-fix.md", resolve_code_review_workflow(parse_code_review_flags(["2", "--fix"])))
        self.assertEqual("code-review.md", resolve_code_review_workflow(parse_code_review_flags(["2"])))
        self.assertEqual("code-review-fix.md", resolve_code_review_workflow(parse_code_review_flags(["3", "--all"])))
        self.assertEqual("code-review-fix.md", resolve_code_review_workflow(parse_code_review_flags(["3", "--auto"])))


if __name__ == "__main__":
    unittest.main()
