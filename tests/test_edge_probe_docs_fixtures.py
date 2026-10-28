"""Port of upstream tests/edge-probe-docs-fixtures.test.cjs.

Keeps engineer/references/edge-probe.md's worked-example JSON blocks in sync with the
fixture files under engineer/references/edge-probe-fixtures/ (compared as parsed JSON),
and locks the machine<->SPEC vocabulary mapping.
"""
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"engineer/bin"))
from lib import edge_probe as ep  # noqa: E402

DOC = ROOT/"engineer/references/edge-probe.md"
FIXTURES = ROOT/"engineer/references/edge-probe-fixtures"
ADR = ROOT/"docs/adr/550-spec-phase-probe-contract.md"
SPEC_TEMPLATE = ROOT/"engineer/templates/spec.md"

_DELIMITER = re.compile(r"^( {0,3})(`{3,}|~{3,})(.*)$")


def scan_fenced_blocks(lines):
    """CommonMark fence scanner (private copy of upstream markdown-sectionizer.scanFencedBlocks)."""
    blocks, opened = [], None
    for index, raw in enumerate(lines):
        match = _DELIMITER.match(raw.rstrip("\r") if raw.endswith("\r") else raw)
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
    """Fenced blocks tagged ``json edge-probe:<dir>/<file>``, keyed by ref."""
    lines = re.split(r"\r?\n", markdown)
    found = {}
    for block in scan_fenced_blocks(lines):
        if block["closeLineIdx"] == -1:
            continue
        tag = re.fullmatch(r"json edge-probe:([^\r\n]+)", block["infoString"])
        if tag:
            found[tag.group(1).strip()] = "\n".join(lines[block["openLineIdx"]+1:block["closeLineIdx"]])
    return found


class ScannerTests(unittest.TestCase):
    def test_tagged_blocks_and_unterminated_fences(self):
        markdown = "text\n```json edge-probe:a/b.json\n{\"a\": 1}\n```\n~~~\n```json edge-probe:c/d.json\n~~~\n```json edge-probe:e/f.json\n{}\n"
        self.assertEqual({"a/b.json": '{"a": 1}'}, tagged_json_blocks(markdown))

    def test_crlf_documents(self):
        self.assertEqual({"a/b.json": "[]"}, tagged_json_blocks("```json edge-probe:a/b.json\r\n[]\r\n```\r\n"))


class DocFixtureSyncTests(unittest.TestCase):
    def test_reference_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_doc_embeds_a_block_for_every_expected_coverage_fixture(self):
        blocks = tagged_json_blocks(DOC.read_text(encoding="utf-8"))
        expected = [d for d in FIXTURES.iterdir() if d.is_dir() and (d/"expected-coverage.json").exists()]
        self.assertEqual(len(expected), len(blocks))

    def test_every_tagged_block_equals_its_fixture(self):
        blocks = tagged_json_blocks(DOC.read_text(encoding="utf-8"))
        self.assertTrue(blocks)
        for ref, body in blocks.items():
            with self.subTest(ref=ref):
                self.assertEqual(json.loads((FIXTURES/ref).read_text(encoding="utf-8")), json.loads(body))

    def test_documented_blocks_are_what_the_engine_produces(self):
        for ref, body in tagged_json_blocks(DOC.read_text(encoding="utf-8")).items():
            directory = (FIXTURES/ref).parent
            requirements = json.loads((directory/"requirements.json").read_text(encoding="utf-8"))
            resolutions_path = directory/"resolutions.json"
            resolutions = json.loads(resolutions_path.read_text(encoding="utf-8")) if resolutions_path.exists() else []
            with self.subTest(ref=ref):
                self.assertEqual(json.loads(body), ep.analyze_coverage(requirements, resolutions))


class VocabularyMappingTests(unittest.TestCase):
    MACHINE_TO_DISPLAY = [
        {"status": "resolved", "verification": "explicit", "display": "covered"},
        {"status": "resolved", "verification": "backstop", "display": "backstop"},
        {"status": "dismissed", "verification": None, "display": "dismissed"},
        {"status": "unresolved", "verification": None, "display": "unresolved"},
    ]

    @staticmethod
    def key(status, verification):
        return f"{status}|{verification if verification is not None else '∅'}"

    def test_mapping_is_a_bijection(self):
        to_display = {self.key(m["status"], m["verification"]): m["display"] for m in self.MACHINE_TO_DISPLAY}
        from_display = {m["display"]: self.key(m["status"], m["verification"]) for m in self.MACHINE_TO_DISPLAY}
        self.assertEqual(len(self.MACHINE_TO_DISPLAY), len(to_display))
        self.assertEqual(len(self.MACHINE_TO_DISPLAY), len(from_display))
        for m in self.MACHINE_TO_DISPLAY:
            key = self.key(m["status"], m["verification"])
            self.assertEqual(key, from_display[to_display[key]])

    def test_mapping_agrees_with_the_edge_validators(self):
        tiers = {m["verification"] for m in self.MACHINE_TO_DISPLAY if m["status"] == "resolved"}
        self.assertEqual(set(ep.EDGE_VALIDATORS["verification"]), tiers)

    @unittest.skipUnless(ADR.exists(), "docs/adr/550-spec-phase-probe-contract.md is not part of this repository")
    def test_adr_documents_the_migration(self):
        adr = ADR.read_text(encoding="utf-8")
        self.assertRegex(adr, r"(?i)covered\b[^.]*resolved[^.]*explicit")
        self.assertRegex(adr, r"(?i)backstop\b[^.]*resolved[^.]*backstop")
        self.assertRegex(adr, r"(?i)count-for-count|count-preserved")

    def test_spec_template_legend_renders_all_four_labels(self):
        template = SPEC_TEMPLATE.read_text(encoding="utf-8")
        for mapping in self.MACHINE_TO_DISPLAY:
            self.assertRegex(template, r"(?i)\b" + mapping["display"] + r"\b", mapping["display"])

    def test_reference_distinguishes_the_two_resolved_tiers(self):
        markdown = DOC.read_text(encoding="utf-8")
        self.assertRegex(markdown, r"(?i)resolved`?/`?explicit")
        self.assertRegex(markdown, r"(?i)resolved`?/`?backstop")


if __name__ == "__main__":
    unittest.main()
