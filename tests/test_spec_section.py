"""Port of upstream tests/spec-section.test.cjs plus parity checks against spec.section."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT/"engineer/bin"
sys.path.insert(0, str(BIN))
from lib import spec_section as ss  # noqa: E402

PROHIB_SUFFIX_SPEC = "\n".join([
    "## Prohibitions (must-NOT)", "",
    "**Coverage:** 2/2 applicable prohibitions resolved · 0 unresolved", "",
    "| Prohibition | Requirement | Status | Verification |",
    "|-------------|-------------|--------|--------------|",
    "| MUST NOT do X | R1 | resolved | test |",
    "| MUST NOT do Y | R2 | resolved | judgment |", "",
    "## Ambiguity Report",
    "| Dim | Score |",
    "|-----|-------|",
    "| Goal | 0.9 |",
])


class SpecSectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.dir = Path(self.temporary.name)

    def write(self, name, content):
        path = self.dir/name
        path.write_text(content, encoding="utf-8")
        return str(path)

    def test_suffix_tolerant_header(self):
        self.assertEqual({"present": True, "dataRows": 2}, ss.count_section_data_rows(PROHIB_SUFFIX_SPEC, "prohibitions"))

    def test_does_not_bleed_into_next_section(self):
        self.assertEqual(2, ss.count_section_data_rows(PROHIB_SUFFIX_SPEC, "prohibitions")["dataRows"])

    def test_plain_and_parenthetical_headers(self):
        for heading in ("## Prohibitions", "##\tProhibitions", "## Prohibitions (must-NOT)"):
            spec = f"{heading}\n\n| a |\n|---|\n| 1 |\n"
            self.assertEqual({"present": True, "dataRows": 1}, ss.count_section_data_rows(spec, "prohibitions"), heading)
        self.assertFalse(ss.count_section_data_rows("## Prohibitionsx\n| a |\n|--|\n| 1 |", "prohibitions")["present"])
        self.assertFalse(ss.count_section_data_rows("### Prohibitions\n| a |\n|--|\n| 1 |", "prohibitions")["present"])

    def test_edge_coverage_rows(self):
        spec = "\n".join(["## Edge Coverage", "", "| Category | Requirement | Status | Resolution |",
                          "|----------|-------------|--------|------------|", "| empty | R1 | covered | x |",
                          "| ordering | R1 | dismissed | y |", "| adjacency | R2 | backstop | z |"])
        self.assertEqual({"present": True, "dataRows": 3}, ss.count_section_data_rows(spec, "edges"))

    def test_present_but_empty_is_not_supplied(self):
        spec = "\n".join(["## Prohibitions (must-NOT)", "", "**Coverage:** 0/0 applicable", "",
                          "| Prohibition | Requirement | Status | Verification |",
                          "|-------------|-------------|--------|--------------|"])
        status = ss.spec_section_status(self.write("empty.md", spec), "prohibitions")
        self.assertEqual((True, 0, False), (status["present"], status["dataRows"], status["supplied"]))

    def test_absent_section(self):
        status = ss.spec_section_status(self.write("noproh.md", "## Edge Coverage\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"), "prohibitions")
        self.assertEqual((False, False), (status["present"], status["supplied"]))

    def test_missing_file_does_not_throw(self):
        self.assertEqual({"key": "edges", "present": False, "dataRows": 0, "supplied": False},
                         ss.spec_section_status(str(self.dir/"no-such-file-xyz.md"), "edges"))

    def test_directory_is_treated_as_missing(self):
        self.assertFalse(ss.spec_section_status(str(self.dir), "edges")["present"])

    def test_multi_table_section(self):
        spec = "\n".join(["## Edge Coverage", "", "| Category | Status |", "|----------|--------|", "| empty | covered |", "",
                          "Some prose between two tables.", "", "| Category | Status |", "|----------|--------|",
                          "| ordering | covered |", "| adjacency | backstop |"])
        self.assertEqual(3, ss.count_section_data_rows(spec, "edges")["dataRows"])

    def test_crlf_and_separator_variants(self):
        spec = "## Edge Coverage\r\n\r\n| a |\r\n| :---: |\r\n| 1 |\r\n| 2 |\r\n"
        self.assertEqual(2, ss.count_section_data_rows(spec, "edges")["dataRows"])
        self.assertEqual(1, ss.count_section_data_rows("## Edge Coverage\n| a |\n|:--|\n| 1 |\n", "edges")["dataRows"])

    def test_supplied_requires_present_and_rows(self):
        self.assertTrue(ss.spec_section_status(self.write("full.md", PROHIB_SUFFIX_SPEC), "prohibitions")["supplied"])


class SpecSectionCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.spec = Path(self.temporary.name)/"cli.md"
        self.spec.write_text(PROHIB_SUFFIX_SPEC, encoding="utf-8")

    def run_module(self, *args):
        return subprocess.run([sys.executable, "-m", "lib.spec_section", *map(str, args)], cwd=BIN, capture_output=True, text=True)

    def test_prints_json_and_exits_0(self):
        process = self.run_module(self.spec, "prohibitions")
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual({"key": "prohibitions", "present": True, "dataRows": 2, "supplied": True}, json.loads(process.stdout))
        self.assertEqual('{"key":"prohibitions","present":true,"dataRows":2,"supplied":true}\n', process.stdout)

    def test_exits_2_on_bad_key_or_missing_args(self):
        for args in ((self.spec, "bogus"), (self.spec,), ()):
            process = self.run_module(*args)
            self.assertEqual(2, process.returncode)
            self.assertIn("usage: spec-section.py <specFile> <edges|prohibitions>", process.stderr)

    def test_absent_file_still_exits_0(self):
        process = self.run_module(Path(self.temporary.name)/"missing.md", "edges")
        self.assertEqual((0, False), (process.returncode, json.loads(process.stdout)["supplied"]))

    def test_main_returns_codes(self):
        self.assertEqual(2, ss.main(["only-one"]))


if __name__ == "__main__":
    unittest.main()
