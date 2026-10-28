"""Port of upstream tests/prohibition-probe.docs-fixtures.test.cjs.

Keeps engineer/references/prohibition-probe.md's worked-example JSON blocks in sync with the
fixtures under engineer/references/prohibition-probe-fixtures/ (compared as parsed JSON), and
runs the fixtures through the ported schema layer.
"""
import importlib
import importlib.util
import json
from pathlib import Path
import re
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


pp = _load("prohibition_probe")
pc = _load("probe_core")

DOC = ROOT/"engineer/references/prohibition-probe.md"
FIXTURES = ROOT/"engineer/references/prohibition-probe-fixtures"
_DELIMITER = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")


def scan_fenced_blocks(lines):
    """CommonMark fence scanner (private copy of upstream markdown-sectionizer.scanFencedBlocks)."""
    blocks, opened = [], None
    for index, raw in enumerate(lines):
        match = _DELIMITER.match(raw[:-1] if raw.endswith("\r") else raw)
        if not match:
            continue
        char, length, trailing = match.group(2)[0], len(match.group(2)), match.group(3)
        if opened is None:
            if char == "`" and "`" in trailing:
                continue
            opened = {"char": char, "len": length, "infoString": trailing.strip(), "openLineIdx": index}
        elif char == opened["char"] and length >= opened["len"] and not trailing.strip():
            blocks.append({**opened, "closeLineIdx": index})
            opened = None
    if opened is not None:
        blocks.append({**opened, "closeLineIdx": -1})
    return blocks


def tagged_json_blocks(markdown):
    """Fenced blocks tagged ``json prohibition-probe:<dir>/<file>``, keyed by ref."""
    lines = re.split(r"\r?\n", markdown)
    found = {}
    for block in scan_fenced_blocks(lines):
        if block["closeLineIdx"] == -1:
            continue
        tag = re.fullmatch(r"json prohibition-probe:([^\r\n]+)", block["infoString"])
        if tag:
            found[tag.group(1).strip()] = "\n".join(lines[block["openLineIdx"]+1:block["closeLineIdx"]])
    return found


class DocFixtureSyncTests(unittest.TestCase):
    def test_reference_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_doc_embeds_a_block_for_every_expected_fixture(self):
        blocks = tagged_json_blocks(DOC.read_text(encoding="utf-8"))
        expected = [d for d in FIXTURES.iterdir() if d.is_dir() and (d/"expected.json").exists()]
        self.assertEqual(3, len(expected))
        self.assertEqual(len(expected), len(blocks))

    def test_every_tagged_block_equals_its_fixture(self):
        blocks = tagged_json_blocks(DOC.read_text(encoding="utf-8"))
        self.assertTrue(blocks)
        for ref, body in blocks.items():
            with self.subTest(ref=ref):
                self.assertEqual(json.loads((FIXTURES/ref).read_text(encoding="utf-8")), json.loads(body))

    def test_scanner_handles_unterminated_and_crlf_fences(self):
        markdown = "```json prohibition-probe:a/b.json\r\n[]\r\n```\r\n```json prohibition-probe:c/d.json\r\n{}\r\n"
        self.assertEqual({"a/b.json": "[]"}, tagged_json_blocks(markdown))


class FixtureSchemaTests(unittest.TestCase):
    """The fixtures are the canonical corpus the schema layer must accept (CR-01 regression)."""

    def items(self):
        found = []
        for directory in sorted(d for d in FIXTURES.iterdir() if d.is_dir()):
            expected = directory/"expected.json"
            if expected.exists():
                data = json.loads(expected.read_text(encoding="utf-8"))
                self.assertTrue("items" not in data or isinstance(data["items"], list), directory.name)
                found.extend((directory.name, item) for item in data.get("items", []))
        return found

    def test_validator_accepts_every_fixture_item(self):
        found = self.items()
        self.assertGreaterEqual(len(found), 4)
        for name, item in found:
            with self.subTest(fixture=name, item=f"{item['requirement_id']}::{item['category']}"):
                self.assertIs(True, pp.validate_prohibition_resolution(item))

    def test_fixture_coverage_rollups_are_consistent(self):
        for directory in sorted(d for d in FIXTURES.iterdir() if d.is_dir()):
            data = json.loads((directory/"expected.json").read_text(encoding="utf-8"))
            coverage = data["coverage"]
            with self.subTest(fixture=directory.name):
                self.assertEqual(len(data["items"]), coverage["applicable"])
                self.assertEqual(coverage["applicable"], coverage["resolved"] + coverage["unresolved"])
                for tier in ("test", "judgment"):
                    self.assertEqual(sum(1 for i in data["items"] if i["status"] == "resolved" and i["verification"] == tier),
                                     coverage["byVerification"][tier])

    def test_fixture_items_project_deterministically(self):
        for name, item in self.items():
            projected = pp.project_prohibitions([item])
            self.assertEqual(projected, pp.project_prohibitions([item]))
            self.assertEqual(item["statement"], projected[0]["statement"], name)

    def test_schema_layer_is_reexported(self):
        self.assertIs(pc.project_prohibitions, pp.project_prohibitions)
        self.assertIs(pc.validate_prohibition_resolution, pp.validate_prohibition_resolution)
        self.assertIs(pc.PROHIBITION_VALIDATORS, pp.PROHIBITION_VALIDATORS)


if __name__ == "__main__":
    unittest.main()
