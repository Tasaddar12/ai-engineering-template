"""Port of upstream tests/responsive-separators.test.cjs (gsd-core d37ff11)."""
import importlib
import importlib.util
from pathlib import Path
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


rs = _load("responsive_separators")

HEAVY, LIGHT, DOUBLE = rs.HEAVY, rs.LIGHT, rs.DOUBLE
LIMIT = rs.MIN_RULE_RUN


class RepoScan(unittest.TestCase):
    def test_shipped_content_walk_finds_files(self):
        files = rs.shipped_markdown_files(SOURCE)
        self.assertGreater(len(files), 100)
        for root in rs.SHIPPED_ROOTS:
            self.assertTrue(any((SOURCE/root) in f.parents for f in files), "no markdown under %s" % root)

    def test_no_fixed_width_rule_lines(self):
        violations = rs.scan(rs.shipped_markdown_files(SOURCE), rs.is_fixed_width_rule_line, SOURCE)
        self.assertEqual([], violations, "Fixed-width rule lines found:\n" + "\n".join(violations) + rs.REMEDY)

    def test_no_panel_characters(self):
        violations = rs.scan(rs.shipped_markdown_files(SOURCE), rs.has_panel_character, SOURCE)
        self.assertEqual([], violations, "Box-panel characters found:\n" + "\n".join(violations) + rs.REMEDY)


class CheckModule(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def temp_file(self, name, content):
        path = self.root/name
        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        return path

    def test_limit_boundaries(self):
        for glyph in (HEAVY, LIGHT, DOUBLE):
            self.assertFalse(rs.is_fixed_width_rule_line(glyph*(LIMIT - 1)))
            self.assertTrue(rs.is_fixed_width_rule_line(glyph*LIMIT))
        self.assertTrue(rs.is_fixed_width_rule_line(HEAVY*(LIMIT + 1)))
        self.assertFalse(rs.is_fixed_width_rule_line(HEAVY))

    def test_lines_containing_glyphs_are_not_rules(self):
        for line in ["└── file.md", "├── dir/", "├────┼────┤",
                     "Progress: ████░░ 80%", "| --- | --- |", "---",
                     "### Engineer ► EXECUTING WAVE 8", "", "   \t  ", "a" + HEAVY*3, HEAVY*3 + "a"]:
            self.assertFalse(rs.is_fixed_width_rule_line(line), repr(line))

    def test_indented_and_mixed_rules(self):
        self.assertTrue(rs.is_fixed_width_rule_line("   " + HEAVY*4 + "  "))
        self.assertTrue(rs.is_fixed_width_rule_line("\t" + LIGHT*3 + "\t"))
        self.assertTrue(rs.is_fixed_width_rule_line(LIGHT*3 + HEAVY*2 + DOUBLE))

    def test_panel_characters(self):
        for line in ["╔══╗", "║  CHECKPOINT: Verification Required   ║", "╚══╝", "╠══╣"]:
            self.assertTrue(rs.has_panel_character(line), repr(line))
        for line in ["├──┤", "│  tree", "### CHECKPOINT: Verification Required", "└── file.md"]:
            self.assertFalse(rs.has_panel_character(line), repr(line))

    def test_scan_flags_rule_line_with_path_and_line_number(self):
        path = self.temp_file("banner.md", "\n".join(["Display banner:", "", HEAVY*53, " Engineer ► PLANNING", ""]))
        violations = rs.scan([path], rs.is_fixed_width_rule_line)
        self.assertEqual(1, len(violations))
        self.assertRegex(violations[0], r"banner\.md:3: ")

    def test_scan_flags_panel_characters(self):
        path = self.temp_file("panel.md", "\n".join(["╔══╗", "║ ERROR ║", "╚══╝"]))
        self.assertEqual(3, len(rs.scan([path], rs.has_panel_character)))

    def test_crlf_scanned_like_lf(self):
        path = self.temp_file("crlf.md", "\r\n".join(["Display:", HEAVY*53, "└── file.md", ""]))
        violations = rs.scan([path], rs.is_fixed_width_rule_line)
        self.assertEqual(1, len(violations))
        self.assertRegex(violations[0], r"crlf\.md:2: ")

    def test_clean_and_empty_files(self):
        clean = self.temp_file("clean.md", "\n".join(["# Title", "", "### Engineer ► PLANNING", "", "---", "", "Body."]))
        empty = self.temp_file("empty.md", "")
        for path in (clean, empty):
            self.assertEqual([], rs.scan([path], rs.is_fixed_width_rule_line))
            self.assertEqual([], rs.scan([path], rs.has_panel_character))

    def test_find_markdown_files_handles_missing_directory(self):
        self.assertEqual([], rs.find_markdown_files(self.root/"absent"))
        self.temp_file("a.md", "x")
        self.temp_file("b.txt", "x")
        self.assertEqual(["a.md"], [p.name for p in rs.find_markdown_files(self.root)])

    def test_property_pure_runs_are_flagged(self):
        rng = random.Random(3028)
        for _ in range(300):
            body = "".join(rng.choice((LIGHT, HEAVY, DOUBLE)) for _ in range(rng.randint(LIMIT, 120)))
            line = rng.choice(["", " ", "  ", "\t", " \t "]) + body + rng.choice(["", " ", "  ", "\t", "\r"])
            self.assertTrue(rs.is_fixed_width_rule_line(line), repr(line))

    def test_property_intruder_is_never_flagged(self):
        rng = random.Random(3028)
        alphabet = [c for c in "abcXYZ019!#|.│└"]
        glyphs = (LIGHT, HEAVY, DOUBLE)
        for _ in range(300):
            intruder = rng.choice(alphabet)
            line = "".join(rng.choice(glyphs) for _ in range(rng.randint(0, 60))) + intruder + \
                "".join(rng.choice(glyphs) for _ in range(rng.randint(0, 60)))
            self.assertFalse(rs.is_fixed_width_rule_line(line), repr(line))


if __name__ == "__main__":
    unittest.main()
