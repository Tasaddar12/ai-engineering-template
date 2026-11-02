"""Ports of upstream tests/ui-consideration-probe.test.cjs and ui-consideration-probe-docs-fixtures.test.cjs."""
import contextlib
import io
import importlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT/"engineer/bin"
LIB = ROOT/"engineer/bin/lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package (another ``lib`` package exists under .ai/runtime)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib."+name)


core = _load("probe_core")
uc = _load("ui_consideration_probe")

TAXONOMY_IDS = ["empty", "loading", "error", "populated", "partial", "overflow", "zero-one-many", "long-text"]
LIST_ELEMENT = {"id": "C1", "text": "A table listing all rows of results"}
ZERO_CUE_ELEMENT = {"id": "Z", "text": "xyzzy plugh frobnicate"}
PARTIAL_CUE_ELEMENT = {"id": "P", "text": "A signup form with input fields and validation"}
COVERED = 'Empty state for the results table renders the documented "No results" copy.'
BACKSTOP = {"statement": "Overflowing long labels truncate with an ellipsis without shifting layout.", "verification": "backstop"}
COVERED_2 = "Loading state shows a skeleton for the results table."
DA_LIST = "En liste over projektorer med knapper til at forbinde og afbryde."
DA_FORM = "En formular hvor brugeren indtaster IP-adresse og adgangskode."
EN_LIST = "A list of projectors with buttons to connect and disconnect."
EN_FORM = "A form where the user enters IP address and password."


def cats(items):
    return [item["category"] for item in items]


class ClassifyElementTests(unittest.TestCase):
    def test_cues(self):
        self.assertIn("form", uc.classify_element("A signup form with input fields and validation"))
        self.assertIn("list-collection", uc.classify_element("A table listing all rows of results"))
        self.assertIn("static-content", uc.classify_element("A heading and a paragraph of body copy"))
        self.assertIn("nav", uc.classify_element("Sidebar navigation menu"))
        self.assertIn("media", uc.classify_element("Avatar image gallery"))
        self.assertIn("interactive-control", uc.classify_element("A toggle switch"))

    def test_zero_cue_and_null_safe(self):
        self.assertEqual([], uc.classify_element("xyzzy plugh frobnicate wibble"))
        self.assertEqual([], uc.classify_element(None))


class TaxonomyTests(unittest.TestCase):
    def test_taxonomy_ids_and_shape(self):
        self.assertEqual(TAXONOMY_IDS, [entry["id"] for entry in uc.UI_TAXONOMY])
        for entry in uc.UI_TAXONOMY:
            self.assertIsInstance(entry["name"], str)
            self.assertTrue(isinstance(entry["elements"], list) and entry["elements"])
            self.assertTrue(isinstance(entry["consideration"], str) and entry["consideration"])

    def test_unclassified_is_outside_the_taxonomy(self):
        self.assertEqual("unclassified", uc.UNCLASSIFIED_CATEGORY)
        self.assertNotIn("unclassified", [entry["id"] for entry in uc.UI_TAXONOMY])

    def test_validators(self):
        self.assertEqual([*TAXONOMY_IDS, "unclassified"], uc.UI_VALIDATORS["categories"])
        self.assertEqual(["explicit", "backstop"], uc.UI_VALIDATORS["verification"])
        self.assertNotIn("verifications", uc.UI_VALIDATORS)

    def test_valid_element_kinds_single_sourced(self):
        self.assertEqual(sorted(uc.UI_CUES), sorted(uc.VALID_ELEMENT_KINDS))

    def test_applicable_categories(self):
        self.assertEqual(["long-text", "overflow"], sorted(uc.applicable_categories(["static-content"])))
        self.assertEqual(["empty", "error", "loading", "overflow", "partial", "populated", "zero-one-many"], sorted(uc.applicable_categories(["list-collection"])))
        self.assertEqual(["error", "loading", "long-text"], sorted(uc.applicable_categories(["interactive-control"])))
        self.assertEqual([], uc.applicable_categories([]))
        everything = uc.applicable_categories(["form", "list-collection", "nav", "media", "interactive-control", "static-content"])
        self.assertTrue(set(everything) <= set(TAXONOMY_IDS))
        for kind in uc.UI_CUES:
            self.assertGreaterEqual(len(uc.applicable_categories([kind])), 1, kind)


class ProposeConsiderationsTests(unittest.TestCase):
    def test_one_unresolved_item_per_category(self):
        items = uc.propose_considerations(LIST_ELEMENT)
        expected = uc.applicable_categories(uc.classify_element(LIST_ELEMENT["text"]))
        self.assertEqual(sorted(expected), sorted(cats(items)))
        for item in items:
            self.assertEqual(("C1", "unresolved", None, None, None), (item["requirement_id"], item["status"], item["verification"], item["resolution"], item["reason"]))
            self.assertTrue(isinstance(item["probe"], str) and item["probe"])

    def test_zero_cue_yields_one_unclassified(self):
        items = uc.propose_considerations({"id": "Z", "text": "xyzzy plugh frobnicate"})
        self.assertEqual([{"requirement_id": "Z", "category": "unclassified", "status": "unresolved", "verification": None,
                           "resolution": None, "reason": None, "probe": "unclassified — review manually"}], items)

    def test_explicit_empty_override_is_silent(self):
        self.assertEqual([], uc.propose_considerations({"id": "O", "text": "anything", "elements": []}))
        self.assertEqual([], uc.propose_considerations({"id": "O", "elements": []}))

    def test_invalid_authored_kind_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "invalid element kind"):
            uc.propose_considerations({"id": "B", "text": "x", "elements": ["not-a-kind"]})
        with self.assertRaises(ValueError) as caught:
            uc.propose_considerations({"id": "B", "text": "x", "elements": ["not-a-kind"]})
        self.assertEqual('invalid element kind "not-a-kind" for element B — must be one of: form, list-collection, nav, media, interactive-control, static-content', str(caught.exception))
        with self.assertRaisesRegex(ValueError, "invalid element kind 5"):
            uc.propose_considerations({"id": "B", "text": "x", "elements": [5]})

    def test_authored_override_bypasses_prose(self):
        self.assertEqual(["long-text", "overflow"], sorted(cats(uc.propose_considerations({"id": "A", "text": "no cues here at all", "elements": ["static-content"]}))))

    def test_requirement_validation(self):
        with self.assertRaisesRegex(ValueError, "elements must be an array"):
            uc.propose_considerations({"id": "A", "text": "x", "elements": "form"})
        with self.assertRaisesRegex(ValueError, "text must be a non-empty string when no elements override"):
            uc.propose_considerations({"id": "A"})
        with self.assertRaisesRegex(ValueError, "requirement id must be a non-empty string"):
            uc.propose_considerations({"text": "x"})


class DelegatedValidationTests(unittest.TestCase):
    def test_blank_dismissal_reason_rejected(self):
        with self.assertRaises(ValueError):
            uc.validate_resolution({"requirement_id": "C1", "category": "empty", "status": "dismissed", "verification": None, "resolution": None, "reason": "   "})
        self.assertIs(True, uc.validate_resolution({"requirement_id": "C1", "category": "empty", "status": "resolved", "verification": "explicit", "resolution": "x"}))

    def test_orphan_rejected(self):
        with self.assertRaises(ValueError):
            uc.analyze_coverage([LIST_ELEMENT], [{"requirement_id": "C1", "category": "nonexistent-category", "status": "resolved",
                                                  "verification": "explicit", "resolution": "x", "reason": None}])

    def test_clean_merge(self):
        report = uc.analyze_coverage([LIST_ELEMENT], [])
        self.assertIsInstance(report["coverage"]["applicable"], int)
        self.assertGreaterEqual(len(report["items"]), 1)

    def test_list_validation(self):
        with self.assertRaisesRegex(ValueError, "elements must be an array"):
            uc.analyze_coverage("nope")
        with self.assertRaisesRegex(ValueError, "duplicate element id"):
            uc.analyze_coverage([LIST_ELEMENT, {"id": "C1", "text": "other"}])


class Lift01Tests(unittest.TestCase):
    def test_project_truths(self):
        out = core.project_truths([COVERED, BACKSTOP])
        self.assertEqual(COVERED, out[0])
        self.assertEqual({"statement": BACKSTOP["statement"], "verification": "backstop"}, out[1])
        self.assertEqual([COVERED, COVERED_2, {"statement": BACKSTOP["statement"], "verification": "backstop"}], core.project_truths([COVERED, COVERED_2, BACKSTOP]))

    def test_disposition(self):
        no_evidence = core.disposition_for_unverifiable_truth(BACKSTOP, {"evidence": []})
        self.assertEqual(("unverified", True, "backstop", core.INSUFFICIENT_SPEC), (no_evidence["status"], no_evidence["flagged"], no_evidence["tier"], no_evidence["reason"]))
        with_evidence = core.disposition_for_unverifiable_truth(BACKSTOP, {"evidence": [{"kind": "wired-test", "passed": True}]})
        self.assertEqual(("green", False), (with_evidence["status"], with_evidence["flagged"]))
        covered = core.disposition_for_unverifiable_truth(COVERED, {"evidence": []})
        self.assertEqual(("green", False), (covered["status"], covered["flagged"]))

    def test_backward_compat_and_format(self):
        self.assertEqual([], core.project_truths(None))
        self.assertEqual([], core.project_truths([]))
        mixed = ['Empty state renders the documented "No results" copy.', {"statement": "Overflowing long labels truncate with an ellipsis.", "verification": "backstop"}, "Loading shows a skeleton for the results table."]
        self.assertEqual([mixed[0], {"statement": mixed[1]["statement"], "verification": "backstop"}, mixed[2]], core.project_truths(mixed))


class ProposeElementsTests(unittest.TestCase):
    def test_classified_element(self):
        (proposal,) = uc.propose_elements([LIST_ELEMENT])
        self.assertEqual("C1", proposal["id"])
        self.assertIn("list-collection", proposal["kinds"])
        self.assertEqual(sorted(uc.applicable_categories(uc.classify_element(LIST_ELEMENT["text"]))), sorted(proposal["categories"]))
        self.assertEqual(sorted(proposal["categories"]), sorted(cats(proposal["considerations"])))
        self.assertFalse(proposal["unclassified"])

    def test_zero_cue_element(self):
        (proposal,) = uc.propose_elements([ZERO_CUE_ELEMENT])
        self.assertEqual(([], [], True, 1, uc.UNCLASSIFIED_CATEGORY),
                         (proposal["kinds"], proposal["categories"], proposal["unclassified"], len(proposal["considerations"]), proposal["considerations"][0]["category"]))

    def test_deterministic(self):
        self.assertEqual(uc.propose_elements([LIST_ELEMENT, ZERO_CUE_ELEMENT]), uc.propose_elements([LIST_ELEMENT, ZERO_CUE_ELEMENT]))

    def test_authored_override(self):
        (proposal,) = uc.propose_elements([{"id": "A", "text": "no cues here at all", "elements": ["static-content"]}])
        self.assertEqual((["static-content"], ["long-text", "overflow"], False), (proposal["kinds"], sorted(proposal["categories"]), proposal["unclassified"]))

    def test_explicit_empty_override_is_not_unclassified(self):
        (proposal,) = uc.propose_elements([{"id": "A", "text": "x", "elements": []}])
        self.assertEqual(([], [], [], False), (proposal["kinds"], proposal["categories"], proposal["considerations"], proposal["unclassified"]))

    def test_partial_cue_recall_gap(self):
        (heuristic,) = uc.propose_elements([PARTIAL_CUE_ELEMENT])
        (confirmed,) = uc.propose_elements([{**PARTIAL_CUE_ELEMENT, "elements": ["form", "list-collection"]}])
        self.assertEqual(["form"], heuristic["kinds"])
        self.assertTrue(set(heuristic["categories"]) < set(confirmed["categories"]))

    def test_invalid_element_is_rejected(self):
        with self.assertRaises(ValueError):
            uc.propose_elements([{"id": "A"}])


class AutoResolveTests(unittest.TestCase):
    def test_applicable_items_backstop_never_dismissed(self):
        items = uc.propose_considerations(LIST_ELEMENT)
        resolutions = uc.auto_resolve(items)
        self.assertEqual(len(items), len(resolutions))
        for resolution in resolutions:
            self.assertEqual(("resolved", "backstop"), (resolution["status"], resolution["verification"]))
            self.assertTrue(resolution["resolution"])

    def test_unclassified_stays_unresolved(self):
        (resolution,) = uc.auto_resolve(uc.propose_considerations(ZERO_CUE_ELEMENT))
        self.assertEqual(("unresolved", None, None, None), (resolution["status"], resolution["verification"], resolution["resolution"], resolution["reason"]))

    def test_output_merges_through_probe_core(self):
        report = uc.analyze_coverage([LIST_ELEMENT], uc.auto_resolve(uc.propose_considerations(LIST_ELEMENT)))
        self.assertTrue(all(item["status"] != "dismissed" for item in report["items"]))
        self.assertEqual(report["coverage"]["applicable"], report["coverage"]["resolved"])
        self.assertEqual(report["coverage"]["applicable"], report["coverage"]["byVerification"]["backstop"])


class TextEnTests(unittest.TestCase):
    def test_text_en_drives_classification(self):
        self.assertEqual(["unclassified"], cats(uc.propose_considerations({"id": "U1", "text": DA_LIST})))
        self.assertEqual(["empty", "loading", "error", "populated", "partial", "overflow", "zero-one-many", "long-text"],
                         cats(uc.propose_considerations({"id": "U1", "text": DA_LIST, "text_en": EN_LIST})))

    def test_translated_matches_english(self):
        for danish, english in ((DA_LIST, EN_LIST), (DA_FORM, EN_FORM)):
            self.assertEqual(cats(uc.propose_considerations({"id": "U1", "text": english})),
                             cats(uc.propose_considerations({"id": "U1", "text": danish, "text_en": english})))

    def test_absent_and_null_fall_back_to_text(self):
        expected = ["empty", "loading", "error", "partial", "long-text"]
        self.assertEqual(expected, cats(uc.propose_considerations({"id": "U1", "text": EN_FORM})))
        self.assertEqual(expected, cats(uc.propose_considerations({"id": "U1", "text": EN_FORM, "text_en": None})))
        uc.validate_requirement({"id": "U1", "text": "A results table", "text_en": None})

    def test_text_en_validation(self):
        for bad in ("", "   ", 42, ["x"], {}):
            with self.assertRaisesRegex(ValueError, "(?i)text_en must be a non-empty string when present"):
                uc.validate_requirement({"id": "U1", "text": DA_LIST, "text_en": bad})
        with self.assertRaisesRegex(ValueError, "(?i)text_en must be a non-empty string when present"):
            uc.validate_requirement({"id": "U1", "text": DA_LIST, "text_en": "", "elements": ["form"]})

    def test_override_wins_and_zero_cue_text_en_is_unclassified(self):
        self.assertEqual(["loading", "error", "overflow", "long-text"],
                         cats(uc.propose_considerations({"id": "U9", "text": DA_LIST, "text_en": EN_LIST, "elements": ["nav"]})))
        self.assertEqual(["unclassified"], cats(uc.propose_considerations({"id": "U1", "text": DA_FORM, "text_en": "Purple elephant dreams."})))

    def test_propose_elements_uses_text_en(self):
        (translated,) = uc.propose_elements([{"id": "U1", "text": DA_LIST, "text_en": EN_LIST}])
        self.assertEqual((["list-collection", "interactive-control"], False), (translated["kinds"], translated["unclassified"]))
        (plain,) = uc.propose_elements([{"id": "U1", "text": DA_LIST}])
        self.assertEqual((True, []), (plain["unclassified"], plain["kinds"]))

    def test_reproduction_pair_report(self):
        english = uc.analyze_coverage([{"id": "U1", "text": EN_LIST}, {"id": "U2", "text": EN_FORM}])
        translated = uc.analyze_coverage([{"id": "U1", "text": DA_LIST, "text_en": EN_LIST}, {"id": "U2", "text": DA_FORM, "text_en": EN_FORM}])
        self.assertEqual(english["coverage"]["applicable"], translated["coverage"]["applicable"])
        self.assertEqual(0, translated["coverage"]["unclassified"])
        self.assertEqual(cats(english["items"]), cats(translated["items"]))


class UiConsiderationCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.dir = Path(self.temporary.name)

    def write(self, name, content):
        path = self.dir/name
        path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        return path

    def run_module(self, *args):
        return subprocess.run([sys.executable, "-m", "lib.ui_consideration_probe", *map(str, args)], cwd=BIN, capture_output=True, text=True, encoding="utf-8")

    def test_text_en_through_the_cli(self):
        path = self.write("elements.json", [{"id": "U1", "text": DA_LIST, "text_en": EN_LIST}, {"id": "U2", "text": DA_FORM, "text_en": EN_FORM}])
        process = self.run_module(path)
        self.assertEqual(0, process.returncode, process.stderr)
        report = json.loads(process.stdout)
        self.assertEqual(0, report["coverage"]["unclassified"])
        self.assertGreater(report["coverage"]["applicable"], 0)
        self.assertIn("—", process.stdout, "UTF-8 output is emitted verbatim")

    def test_resolutions_file_and_failures(self):
        elements = self.write("elements.json", [LIST_ELEMENT])
        resolutions = self.write("resolutions.json", [{"requirement_id": "C1", "category": "empty", "status": "dismissed", "reason": "n/a"}])
        process = self.run_module(elements, resolutions)
        self.assertEqual((0, 1), (process.returncode, json.loads(process.stdout)["coverage"]["resolved"]))
        for args in ((), (self.dir/"missing.json",), (self.write("bad.json", "{{"),)):
            self.assertEqual(2, self.run_module(*args).returncode)
        usage = self.run_module()
        self.assertIn("usage: ui_consideration_probe.py <elements.json> [resolutions.json]", usage.stderr)
        invalid = self.run_module(self.write("invalid.json", [{"id": "X", "text": "t", "elements": ["nope"]}]))
        self.assertEqual(2, invalid.returncode)
        self.assertIn("error: invalid element kind", invalid.stderr)

    def test_main_in_process(self):
        path = self.write("elements.json", [LIST_ELEMENT])
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(0, uc.main([str(path)]))
            self.assertEqual(2, uc.main([]))
        self.assertIn("coverage", json.loads(out.getvalue()))


DOC = ROOT/"engineer/references/ui-consideration-probe.md"
DOMAIN = ROOT/"engineer/references/domain-probes.md"
TEMPLATE = ROOT/"engineer/templates/UI-SPEC.md"


def doc_taxonomy_ids(markdown):
    section = re.split(r"(?m)^## Taxonomy", markdown)[1]
    section = re.split(r"(?m)^## ", section)[0]
    ids = []
    for line in section.split("\n"):
        if line.strip().startswith("|"):
            cell = line.split("|")[1].strip()
            if re.fullmatch(r"[a-z][a-z0-9-]*", cell) and cell != "id":
                ids.append(cell)
    return ids


def headings(markdown):
    return [re.sub(r"^## ", "", line).strip().lower() for line in markdown.split("\n") if re.match(r"^## ", line)]


class DocParityTests(unittest.TestCase):
    def test_reference_doc_exists(self):
        self.assertTrue(DOC.exists())

    def test_doc_taxonomy_ids_equal_code(self):
        self.assertEqual([entry["id"] for entry in uc.UI_TAXONOMY], doc_taxonomy_ids(DOC.read_text(encoding="utf-8")))

    def test_closed_and_open_banks_are_disjoint(self):
        topics = headings(DOMAIN.read_text(encoding="utf-8"))
        for entry in uc.UI_TAXONOMY:
            self.assertNotIn(entry["id"], topics)

    def test_doc_links_the_domain_probes_bank(self):
        self.assertRegex(DOC.read_text(encoding="utf-8"), r"domain-probes\.md")

    def test_inputs_document_text_en(self):
        inputs = re.split(r"(?m)^## ", re.split(r"(?m)^## Inputs", DOC.read_text(encoding="utf-8"))[1])[0]
        self.assertRegex(inputs, "text_en")
        self.assertRegex(inputs, "English")

    def test_template_has_ui_considerations_and_copywriting_sections(self):
        found = headings(TEMPLATE.read_text(encoding="utf-8"))
        self.assertIn("ui considerations", found)
        self.assertIn("copywriting contract", found)


if __name__ == "__main__":
    unittest.main()
