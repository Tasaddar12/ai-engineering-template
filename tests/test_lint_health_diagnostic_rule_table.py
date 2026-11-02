import contextlib
import importlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "engineer/bin/lib"


def _load(name):
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module("engineer_bin_lib." + name)


guard = _load("lint_health_diagnostic_rule_table")
hd = _load("health_diagnostic")

FAKE_SEVERITY = {"ERROR": "error", "WARNING": "warning", "INFO": "info"}


class TempFiles(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="lint-hd-rt-")
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, name, content):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path


class OneToOneInvariant(unittest.TestCase):
    def test_flags_a_duplicated_code(self):
        rules = [{"code": "W001", "severity": "warning"}, {"code": "W002", "severity": "warning"}, {"code": "W001", "severity": "warning"}]
        self.assertEqual({"duplicates": [{"code": "W001", "count": 2}], "badSeverities": []},
                         guard.check_one_to_one_invariant(rules, FAKE_SEVERITY))

    def test_passes_when_every_code_is_unique(self):
        rules = [{"code": "W001", "severity": "warning"}, {"code": "W002", "severity": "error"}, {"code": "W003", "severity": "info"}]
        self.assertEqual({"duplicates": [], "badSeverities": []}, guard.check_one_to_one_invariant(rules, FAKE_SEVERITY))

    def test_flags_a_severity_outside_the_enum(self):
        rules = [{"code": "W001", "severity": "critical"}, {"code": "W002", "severity": "warning"}]
        self.assertEqual({"duplicates": [], "badSeverities": [{"code": "W001", "severity": "critical"}]},
                         guard.check_one_to_one_invariant(rules, FAKE_SEVERITY))

    def test_real_rule_table_satisfies_the_invariant(self):
        self.assertEqual({"duplicates": [], "badSeverities": []}, guard.check_one_to_one_invariant(hd.RULES, hd.SEVERITY))
        self.assertEqual({"duplicates": [], "badSeverities": []}, guard.check_one_to_one_invariant(hd.CONSISTENCY_RULES, hd.SEVERITY))


class FixtureProofInvariant(TempFiles):
    def test_flags_a_code_with_zero_mentions(self):
        file = self.write("fake.test.cjs", "describe('W001 \u2014 something', () => { test('fires', () => {}); });\n")
        found = guard.check_fixture_proof_invariant([{"code": "W001"}, {"code": "W999"}], [file])
        self.assertEqual(["W999"], found["uncovered"])
        self.assertEqual([file], found["testFilesScanned"])

    def test_flags_a_code_mentioned_only_outside_a_titled_block(self):
        file = self.write("fake.test.cjs", "\n".join([
            "// W002 is handled elsewhere, see notes",
            "const message = 'refers to W002 in a plain string, not a block title';",
            "describe('unrelated block', () => { test('does something', () => {}); });", ""]))
        self.assertEqual(["W002"], guard.check_fixture_proof_invariant([{"code": "W002"}], [file])["uncovered"])

    def test_passes_a_code_named_in_a_describe_title(self):
        file = self.write("fake.test.cjs", "describe('W003 \u2014 some finding', () => { test('fires when absent', () => {}); });\n")
        self.assertEqual([], guard.check_fixture_proof_invariant([{"code": "W003"}], [file])["uncovered"])

    def test_passes_a_code_named_in_a_test_only_title(self):
        file = self.write("fake.test.cjs", "test('W010 fires on incomplete agent install', () => {});\n")
        self.assertEqual([], guard.check_fixture_proof_invariant([{"code": "W010"}], [file])["uncovered"])

    def test_python_test_names_and_class_names_count_as_titles(self):
        file = self.write("test_fake.py", "class W020_Degraded(unittest.TestCase):\n    def test_w017_orphans(self):\n        pass\n"
                                           "    async def test_w027_stale(self):\n        pass\n")
        found = guard.check_fixture_proof_invariant([{"code": c} for c in ("W020", "W017", "W027", "W021")], [file])
        self.assertEqual(["W021"], found["uncovered"])

    def test_python_comments_strings_and_helper_names_do_not_count(self):
        file = self.write("test_fake.py", "# W004 is covered elsewhere\nSOME = 'W004'\ndef helper_w004():\n    pass\n"
                                           "class Unrelated:\n    def test_other(self):\n        'W004 in a docstring'\n")
        self.assertEqual(["W004"], guard.check_fixture_proof_invariant([{"code": "W004"}], [file])["uncovered"])

    def test_code_must_be_a_whole_token(self):
        file = self.write("test_fake.py", "class T:\n    def test_w0011_long(self):\n        pass\n    def test_xw001y(self):\n        pass\n")
        self.assertEqual(["W001"], guard.check_fixture_proof_invariant([{"code": "W001"}], [file])["uncovered"])

    def test_passes_for_a_real_code_against_the_real_tests_tree(self):
        files = guard.find_health_diagnostic_test_files()
        self.assertTrue(files, "expected at least one health-diagnostic test file on disk")
        self.assertEqual([], guard.check_fixture_proof_invariant([{"code": "W001"}], files)["uncovered"])

    def test_extract_titled_blocks(self):
        text = "describe('A \u2014 x', () => {\n  test(\"B\", () => {});\n  it(`C`, () => {});\n});\nclass Foo(Bar):\n    def test_baz(self):\n        pass\n    def helper(self):\n        pass\n"
        self.assertEqual(["A \u2014 x", "B", "C", "Foo", "test_baz"], guard.extract_titled_blocks(text))
        # The raw (still escaped) literal is kept, as upstream.
        self.assertEqual(["it\\'s"], guard.extract_titled_blocks("test('it\\'s', () => {})"))

    def test_code_appears_in_title(self):
        self.assertTrue(guard.code_appears_in_title("W001", ["fires: W001 (x)"]))
        self.assertTrue(guard.code_appears_in_title("W001", ["test_w001_fires"]))
        self.assertFalse(guard.code_appears_in_title("W001", ["W0011"]))
        self.assertFalse(guard.code_appears_in_title("W001", []))


class InertCodeExemption(TempFiles):
    def test_exempted_code_with_zero_coverage_is_not_uncovered(self):
        file = self.write("fake.test.cjs", "describe('unrelated', () => {});\n")
        found = guard.check_fixture_proof_invariant([{"code": "W024"}], [file], {"W024": "permanent no-op"})
        self.assertEqual(([], ["W024"]), (found["uncovered"], found["exempted"]))

    def test_non_exempted_code_still_fails(self):
        file = self.write("fake.test.cjs", "describe('unrelated', () => {});\n")
        found = guard.check_fixture_proof_invariant([{"code": "W998"}], [file], {"W024": "permanent no-op"})
        self.assertEqual((["W998"], []), (found["uncovered"], found["exempted"]))

    def test_exempted_code_is_reported_even_when_a_title_mentions_it(self):
        file = self.write("fake.test.cjs", "test('exports exactly 1 rule: W024', () => {});\n")
        found = guard.check_fixture_proof_invariant([{"code": "W024"}], [file], {"W024": "permanent no-op"})
        self.assertEqual(([], ["W024"]), (found["uncovered"], found["exempted"]))

    def test_w024_is_exempted_against_the_real_tests_tree(self):
        found = guard.check_fixture_proof_invariant([{"code": "W024"}], guard.find_health_diagnostic_test_files())
        self.assertEqual(([], ["W024"]), (found["uncovered"], found["exempted"]))

    def test_permanently_inert_codes_lock_exactly_w024(self):
        self.assertEqual(["W024"], list(guard.PERMANENTLY_INERT_CODES))
        reason = guard.PERMANENTLY_INERT_CODES["W024"]
        self.assertRegex(reason, r"ambient I/O|\u00a78\.1")

    def test_w024_rule_is_actually_a_permanent_no_op(self):
        rule = next(r for r in hd.RULES if r["code"] == "W024")
        self.assertEqual([], rule["check"]({}))


class StateValidatePass(TempFiles):
    def test_flags_a_code_with_zero_mentions(self):
        file = self.write("fake-state.test.cjs", "describe('S001: something', () => { test('fires', () => {}); });\n")
        self.assertEqual(["S999"], guard.check_fixture_proof_invariant([{"code": "S001"}, {"code": "S999"}], [file])["uncovered"])

    def test_passes_a_code_named_in_a_test_title(self):
        file = self.write("fake-state.test.cjs", "test('S001: STATE.md corrupt (NUL byte) fires with the verbatim message', () => {});\n")
        self.assertEqual([], guard.check_fixture_proof_invariant([{"code": "S001"}], [file])["uncovered"])

    def test_discovery_reads_codes_off_state_diagnostic_call_sites(self):
        fixture = "\n".join([
            "warnings.push(stateDiagnostic('S002', SEVERITY.WARNING, 'a', 'b'));",
            "warnings.push(stateDiagnostic(", "  'S001',", "  SEVERITY.ERROR,", "));",
            'warnings.push(stateDiagnostic(`S002`, SEVERITY.WARNING, "dup", "b"));',
            "# stateDiagnostic('S404', ...) in a comment still counts: over-inclusion only demands more coverage.",
            "warnings.push(stateDiagnostic ('S010', SEVERITY.WARNING, 'spaced', 'b'));"])
        self.assertEqual(["S001", "S002", "S010", "S404"], guard.discover_state_validate_codes(fixture, "fixture"))

    def test_discovery_fails_closed_when_the_call_shape_changes(self):
        with self.assertRaises(guard._ExitError) as ctx:
            guard.discover_state_validate_codes('renamedHelper("S001", SEVERITY.WARNING);', "fixture")
        self.assertEqual(1, ctx.exception.code)
        self.assertIn("found no stateDiagnostic() call sites in fixture", str(ctx.exception))

    def test_load_state_validate_codes_reads_a_source_file(self):
        source = self.write("state_validate.py", "diagnostics.append(stateDiagnostic('S003', 'error', 'x'))\n")
        self.assertEqual(["S003"], guard.load_state_validate_codes(source))
        empty = self.write("empty.py", "nothing here\n")
        with self.assertRaises(guard._ExitError):
            guard.load_state_validate_codes(empty)

    def test_load_state_validate_codes_is_none_when_the_source_is_absent(self):
        self.assertIsNone(guard.load_state_validate_codes(self.dir / "missing.py"))

    def test_the_fixture_proof_pass_can_actually_fail(self):
        file = self.write("fake-state.test.cjs", "test('S001 fires', () => {});\n")
        found = guard.check_fixture_proof_invariant([{"code": "S001"}, {"code": "S999"}], [file], {})
        self.assertEqual(["S999"], found["uncovered"])


class FindTestFiles(TempFiles):
    def test_finds_health_diagnostic_test_files_only(self):
        self.write("tests/test_health_diagnostic.py", "")
        self.write("tests/test_health_diagnostic_extra.py", "")
        self.write("tests/test_other.py", "")
        names = [p.name for p in guard.find_health_diagnostic_test_files(self.dir)]
        self.assertEqual(["test_health_diagnostic.py", "test_health_diagnostic_extra.py"], names)
        self.assertEqual([], guard.find_health_diagnostic_test_files(self.dir / "nope"))

    def test_real_tree_includes_the_health_diagnostic_test_file(self):
        self.assertIn("test_health_diagnostic.py", [p.name for p in guard.find_health_diagnostic_test_files()])


class RunAndCli(TempFiles):
    def run_gate(self, **kwargs):
        return guard.run(**kwargs)

    def test_real_repo_passes(self):
        lines = guard.run()
        self.assertTrue(lines[0].startswith("lint-health-diagnostic-rule-table: PASS \u2014 33 rule code(s): 32 covered by a titled test, 1 exempted across"))
        self.assertIn("Exempted: W024 (", lines[0])
        self.assertIn("PASS (C0NN namespace) \u2014 4 new rule code(s) (C001, C002, C003, C004)", lines[1])
        self.assertIn("SKIP (S0NN namespace)", lines[2])

    def test_duplicate_code_and_bad_severity_fail_with_remedies(self):
        file = self.write("test_health_diagnostic_fake.py", "class T:\n    def test_w001(self):\n        pass\n")
        rules = [{"code": "W001", "severity": "warning"}, {"code": "W001", "severity": "critical"}]
        with self.assertRaises(guard._ExitError) as ctx:
            self.run_gate(rules=rules, consistency_rules=[], test_files=[file], state_codes=None)
        message = str(ctx.exception)
        self.assertEqual(1, ctx.exception.code)
        self.assertIn("\u00a78.2 rule 1 violated: 1 duplicated rule code(s) in RULES", message)
        self.assertIn("W001 (2 occurrences)", message)
        self.assertIn('\u00a78.2 rule 3 violated: 1 rule(s) with a severity not in SEVERITY\'s values', message)
        self.assertIn('W001: severity="critical"', message)

    def test_uncovered_code_fails_and_names_the_searched_files(self):
        file = self.write("test_health_diagnostic_fake.py", "class T:\n    def test_other(self):\n        pass\n")
        rules = [{"code": "W777", "severity": "warning"}]
        with self.assertRaises(guard._ExitError) as ctx:
            self.run_gate(rules=rules, consistency_rules=[], test_files=[file], state_codes=None)
        message = str(ctx.exception)
        self.assertIn("\u00a78.5 violated: 1 rule code(s) with no test block naming them", message)
        self.assertIn("W777", message)
        self.assertIn("def test_w777_fires", message)

    def test_consistency_namespace_is_checked_separately(self):
        file = self.write("test_health_diagnostic_fake.py", "class T:\n    def test_c001(self):\n        pass\n")
        consistency = [{"code": "C001", "severity": "warning"}, {"code": "C001", "severity": "warning"}, {"code": "W006", "severity": "warning"}]
        with self.assertRaises(guard._ExitError) as ctx:
            self.run_gate(rules=[], consistency_rules=consistency, test_files=[file], state_codes=None)
        self.assertIn("(C0NN namespace): 1 duplicated rule code(s) in CONSISTENCY_RULES", str(ctx.exception))

    def test_state_validate_namespace_failure_and_pass(self):
        rules = [{"code": "W001", "severity": "warning"}]
        file = self.write("test_health_diagnostic_fake.py", "class T:\n    def test_w001(self):\n        pass\n")
        with self.assertRaises(guard._ExitError) as ctx:
            self.run_gate(rules=rules, consistency_rules=[], test_files=[file], state_codes=["S404"])
        self.assertIn("\u00a78.5 violated (S0NN namespace): 1 code(s) with no test block naming them", str(ctx.exception))

    def test_pass_output_lists_exempted_codes_separately(self):
        file = self.write("test_health_diagnostic_fake.py", "class T:\n    def test_w001(self):\n        pass\n")
        rules = [{"code": "W001", "severity": "warning"}, {"code": "W024", "severity": "warning"}]
        lines = self.run_gate(rules=rules, consistency_rules=[], test_files=[file], state_codes=None)
        self.assertIn("2 rule code(s): 1 covered by a titled test, 1 exempted across 1 test file(s).", lines[0])

    def test_main_prints_pass_lines_and_returns_zero(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = guard.main([])
        self.assertEqual(0, code, err.getvalue())
        self.assertIn("lint-health-diagnostic-rule-table: PASS", out.getvalue())

    def test_main_returns_one_and_prints_the_violation(self):
        original = guard.run
        try:
            def failing(*args, **kwargs):
                raise guard._ExitError(1, "boom\n")
            guard.run = failing
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = guard.main([])
        finally:
            guard.run = original
        self.assertEqual(1, code)
        self.assertIn("boom", err.getvalue())
        self.assertEqual("", out.getvalue())

    def test_module_runs_as_a_script(self):
        done = subprocess.run([sys.executable, "-m", "lib.lint_health_diagnostic_rule_table"], cwd=ROOT / "engineer/bin",
                              capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("PASS", done.stdout)


if __name__ == "__main__":
    unittest.main()
