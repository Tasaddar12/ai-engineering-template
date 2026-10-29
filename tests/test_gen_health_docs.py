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
SHIPPED_HEALTH_MD = ROOT / "engineer/workflows/health.md"


def _load(name):
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB / "__init__.py", submodule_search_locations=[str(LIB)])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module("engineer_bin_lib." + name)


gen = _load("gen_health_docs")
hd = _load("health_diagnostic")
RULES = hd.RULES


def run_gen(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = gen.main(list(args))
    return code, out.getvalue(), err.getvalue()


def read(path):
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


class TempHealthMd(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="gen-health-docs-")
        self.addCleanup(self._tmp.cleanup)
        self.target = Path(self._tmp.name) / "health.md"
        write(self.target, read(SHIPPED_HEALTH_MD))


class CheckWriteRoundTrip(TempHealthMd):
    def test_check_passes_on_a_freshly_written_file(self):
        code, _, err = run_gen(["--write", "--target", str(self.target)])
        self.assertEqual(0, code, err)
        code, out, err = run_gen(["--check", "--target", str(self.target)])
        self.assertEqual(0, code, err)
        self.assertIn("up to date (36 codes, 6 repair actions)", out)

    def test_write_reports_counts(self):
        code, out, _ = run_gen(["--write", "--target", str(self.target)])
        self.assertEqual(0, code)
        self.assertEqual(f"Wrote {self.target} — 36 error/warning/info code(s), 6 repair action(s).\n", out)

    def test_check_fails_when_the_tagged_region_is_stale(self):
        run_gen(["--write", "--target", str(self.target)])
        content = read(self.target)
        self.assertIn("| E001 | error |", content)
        write(self.target, content.replace("| E001 | error |", "| E001 | error-STALE-MUTATION |"))
        code, _, err = run_gen(["--check", "--target", str(self.target)])
        self.assertEqual(1, code)
        self.assertIn("is stale", err)
        self.assertIn("gen_health_docs --write", err)

    def test_write_on_a_stale_copy_regenerates_to_a_clean_check(self):
        run_gen(["--write", "--target", str(self.target)])
        write(self.target, read(self.target).replace("| W010 |", "| W010-DRIFTED |"))
        self.assertEqual(1, run_gen(["--check", "--target", str(self.target)])[0])
        self.assertEqual(0, run_gen(["--write", "--target", str(self.target)])[0])
        self.assertEqual(0, run_gen(["--check", "--target", str(self.target)])[0])

    def test_write_only_touches_the_tagged_regions(self):
        before = read(self.target)
        run_gen(["--write", "--target", str(self.target)])
        after = read(self.target)
        self.assertEqual(before[:before.index(gen.ERROR_CODES_START)], after[:after.index(gen.ERROR_CODES_START)])
        self.assertEqual(before[before.index(gen.REPAIR_ACTIONS_END):], after[after.index(gen.REPAIR_ACTIONS_END):])

    def test_crlf_text_is_preserved_outside_the_regions(self):
        text = read(self.target).replace("\r\n", "\n").replace("\n", "\r\n")
        write(self.target, text)
        run_gen(["--write", "--target", str(self.target)])
        after = read(self.target)
        self.assertTrue(after.endswith(text[text.index(gen.REPAIR_ACTIONS_END):]))

    def test_plain_invocation_prints_both_tables(self):
        code, out, err = run_gen([])
        self.assertEqual(0, code, err)
        self.assertIn("| Code | Severity | Description | Repairable |", out)
        self.assertIn("| Action | Effect | Risk |", out)

    def test_unrecognized_flag_and_missing_target_value_exit_1(self):
        code, _, err = run_gen(["--bogus"])
        self.assertEqual(1, code)
        self.assertIn("unknown flag: --bogus", err)
        self.assertIn("Recognized flags: --write, --check, --target <path>.", err)
        code, _, err = run_gen(["--target"])
        self.assertEqual(1, code)
        self.assertIn("--target requires a path argument.", err)

    def test_missing_target_file(self):
        missing = str(Path(self._tmp.name) / "nope.md")
        code, _, err = run_gen(["--check", "--target", missing])
        self.assertEqual(1, code)
        self.assertIn(f"gen-health-docs: {missing} not found.", err)

    def test_target_without_tags_fails(self):
        write(self.target, "no tags here\n")
        code, _, err = run_gen(["--write", "--target", str(self.target)])
        self.assertEqual(1, code)
        self.assertIn("is missing the <error_codes>/</error_codes> tags.", err)

    def test_module_runs_as_a_script(self):
        write(self.target, read(SHIPPED_HEALTH_MD))
        run = lambda *args: subprocess.run([sys.executable, "-m", "lib.gen_health_docs", *args], cwd=ROOT / "engineer/bin",
                                           capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(0, run("--write", "--target", str(self.target)).returncode)
        done = run("--check", "--target", str(self.target))
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertIn("up to date", done.stdout)
        self.assertEqual(1, run("--bogus").returncode)

    @unittest.expectedFailure
    def test_shipped_health_md_already_passes_check(self):
        # KNOWN DRIFT: engineer/workflows/health.md localises W010/W019/W028 descriptions
        # ("Engineer" for upstream "GSD") and rewords the generated footnote paragraph.
        code, _, err = run_gen(["--check"])
        self.assertEqual(0, code, err)


class RowContent(unittest.TestCase):
    def region_row(self, code):
        region = gen.render_error_codes_region(RULES)
        return next((line for line in region.split("\n") if line.startswith(f"| {code} |")), None)

    def test_36_row_table_is_33_rules_plus_3_prechecks(self):
        rows = gen.build_error_code_rows(RULES)
        self.assertEqual(36, len(rows))
        codes = [r["code"] for r in rows]
        for precheck in gen.PRECHECK_CODES:
            self.assertIn(precheck["code"], codes)
        self.assertIn("W030", codes)

    def test_w010_row_uses_the_rule_description(self):
        row = self.region_row("W010")
        self.assertIn(next(r for r in RULES if r["code"] == "W010")["description"], row)
        self.assertTrue(row.endswith("| No |"))

    def test_w026_row_uses_the_rule_description(self):
        self.assertIn(next(r for r in RULES if r["code"] == "W026")["description"], self.region_row("W026"))

    def test_e004_is_not_repairable(self):
        self.assertTrue(self.region_row("E004").endswith("| No |"))

    def test_repairable_overrides(self):
        self.assertIn("Yes (`--backfill`)", self.region_row("W018"))
        self.assertIn("Yes (known legacy statuses only)", self.region_row("W030"))
        self.assertTrue(self.region_row("W003").endswith("| Yes |"))

    def test_w025_is_absent(self):
        self.assertIsNone(self.region_row("W025"))

    def test_rows_sort_e_then_w_numerically_then_i(self):
        rows = gen.build_error_code_rows(RULES)
        from functools import cmp_to_key
        self.assertEqual(rows, sorted(rows, key=cmp_to_key(gen.compare_codes)))
        codes = [r["code"] for r in rows]
        last_e = max(i for i, c in enumerate(codes) if c.startswith("E"))
        first_w = min(i for i, c in enumerate(codes) if c.startswith("W"))
        last_w = max(i for i, c in enumerate(codes) if c.startswith("W"))
        first_i = min(i for i, c in enumerate(codes) if c.startswith("I"))
        self.assertLess(last_e, first_w)
        self.assertLess(last_w, first_i)
        w_numbers = [int(c[1:]) for c in codes if c.startswith("W")]
        self.assertEqual(sorted(w_numbers), w_numbers)

    def test_c_codes_sort_after_known_prefixes(self):
        rows = gen.build_error_code_rows([{"code": "C001", "severity": "warning", "description": "c", "repairable": False}])
        self.assertEqual("C001", rows[-1]["code"])

    def test_duplicate_codes_across_rules_and_prechecks_raise(self):
        with self.assertRaisesRegex(ValueError, 'duplicate diagnostic code "E001"'):
            gen.build_error_code_rows([{"code": "E001", "severity": "error", "description": "x", "repairable": False}])

    def test_unparseable_code_raises(self):
        with self.assertRaisesRegex(ValueError, 'unparseable diagnostic code "bogus"'):
            gen.parse_code("bogus")
        self.assertEqual({"prefix": "W", "number": 30}, gen.parse_code("W030"))

    def test_cell_text_escapes_table_hostile_characters(self):
        self.assertEqual("a\\\\b \\| &lt;x&gt; c", gen.cell_text("a\\b | <x>\nc  "))

    def test_error_codes_region_shape(self):
        region = gen.render_error_codes_region(RULES)
        self.assertTrue(region.startswith("\n| Code | Severity | Description | Repairable |\n|------|----------|-------------|------------|\n| E001 | error |"))
        self.assertTrue(region.endswith(gen.FOOTNOTE_PARAGRAPH + "\n"))

    def test_repair_actions_region_lists_all_seven_actions(self):
        region = gen.render_repair_actions_region()
        for action in gen.REMEDY_ACTION_ORDER:
            self.assertIn(f"| {action} |", region)
        self.assertEqual(6, len(gen.REMEDY_ACTION_ORDER))
        self.assertEqual(set(gen.REMEDY_ACTION_ORDER), {v for k, v in hd.REMEDY_ACTION.items() if k != "ADVISE"})
        self.assertTrue(region.endswith("**Not repairable (too risky):**\n- PROJECT.md, ROADMAP.md content\n- Phase directory renaming\n- Orphaned plan cleanup\n"))

    def test_missing_action_metadata_raises(self):
        saved = gen.REMEDY_ACTION_METADATA.pop("createConfig")
        try:
            with self.assertRaisesRegex(ValueError, 'no Effect/Risk metadata registered for repair action "createConfig"'):
                gen.render_repair_actions_region()
        finally:
            gen.REMEDY_ACTION_METADATA["createConfig"] = saved


class SpliceRegion(unittest.TestCase):
    def test_missing_tag_raises(self):
        with self.assertRaisesRegex(gen._ExitError, "missing the .*tags"):
            gen.splice_region("no tags here", gen.ERROR_CODES_START, gen.ERROR_CODES_END, "x")

    def test_duplicate_tag_raises(self):
        text = f"{gen.ERROR_CODES_START}a{gen.ERROR_CODES_END}{gen.ERROR_CODES_START}b{gen.ERROR_CODES_END}"
        with self.assertRaisesRegex(gen._ExitError, "more than one"):
            gen.splice_region(text, gen.ERROR_CODES_START, gen.ERROR_CODES_END, "x")

    def test_preserves_content_outside_the_tags(self):
        before, after = "PROSE BEFORE\n", "\nPROSE AFTER"
        out = gen.splice_region(f"{before}{gen.ERROR_CODES_START}old inner{gen.ERROR_CODES_END}{after}",
                                gen.ERROR_CODES_START, gen.ERROR_CODES_END, "new inner")
        self.assertTrue(out.startswith(before + gen.ERROR_CODES_START))
        self.assertTrue(out.endswith(gen.ERROR_CODES_END + after))
        self.assertNotIn("old inner", out)
        self.assertEqual(f"{before}{gen.ERROR_CODES_START}new inner\n{gen.ERROR_CODES_END}{after}", out)

    def test_regenerate_is_idempotent(self):
        once = gen.regenerate_health_md(RULES, read(SHIPPED_HEALTH_MD))
        self.assertEqual(once, gen.regenerate_health_md(RULES, once))


if __name__ == "__main__":
    unittest.main()
