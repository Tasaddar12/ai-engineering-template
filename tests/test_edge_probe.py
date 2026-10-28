"""Port of upstream tests/edge-probe.test.cjs for engineer/bin/lib/edge_probe.py."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT/"engineer/bin"
sys.path.insert(0, str(BIN))
from lib import edge_probe as ep  # noqa: E402

FIXTURES = ROOT/"engineer/references/edge-probe-fixtures"
ZERO_COVERAGE_2 = {"applicable": 2, "resolved": 0, "unresolved": 2, "unclassified": 0, "byVerification": {"explicit": 0, "backstop": 0}}


def categories(edges):
    return sorted(edge["category"] for edge in edges)


def resolution(category, status, **fields):
    return {"requirement_id": "R1", "category": category, "status": status, **fields}


class ClassifyShapeTests(unittest.TestCase):
    def test_numeric_range(self):
        self.assertEqual(["numeric-range"], sorted(ep.classify_shape("Round a number to N decimal places")))

    def test_collection(self):
        self.assertIn("collection", ep.classify_shape("Merge a list of overlapping intervals"))

    def test_text(self):
        self.assertIn("text", ep.classify_shape("Truncate a string to a maximum length"))

    def test_no_cue(self):
        self.assertEqual([], ep.classify_shape("Display the company logo"))

    def test_none_and_non_string_input(self):
        self.assertEqual([], ep.classify_shape(None))
        self.assertEqual([], ep.classify_shape(42))

    def test_ascii_word_boundaries(self):
        self.assertEqual(["numeric-range"], ep.classify_shape("cafélimit"), "non-ASCII letters are non-word characters, as in JavaScript")
        self.assertEqual(["numeric-range"], ep.classify_shape("LIMIT"))


class TaxonomyTests(unittest.TestCase):
    def test_eight_categories_in_order(self):
        self.assertEqual(["boundary", "adjacency", "empty", "encoding", "ordering", "precision", "idempotency", "concurrency"],
                         [entry["id"] for entry in ep.TAXONOMY])

    def test_entry_shape(self):
        for entry in ep.TAXONOMY:
            self.assertIsInstance(entry["name"], str)
            self.assertTrue(isinstance(entry["shapes"], list) and len(entry["shapes"]) >= 1)
            self.assertIsInstance(entry["probe"], str)

    def test_applicable_categories(self):
        self.assertEqual(["boundary", "precision"], sorted(ep.applicable_categories(["numeric-range"])))
        self.assertEqual(["adjacency", "empty", "ordering"], sorted(ep.applicable_categories(["collection"])))
        self.assertEqual(["empty", "encoding"], sorted(ep.applicable_categories(["text"])))
        self.assertEqual(["concurrency", "idempotency"], sorted(ep.applicable_categories(["stateful"])))
        self.assertEqual(["concurrency"], ep.applicable_categories(["io"]))
        self.assertEqual([], ep.applicable_categories([]))

    def test_vocabulary_is_single_sourced(self):
        locked = ["numeric-range", "collection", "text", "stateful", "io"]
        self.assertEqual(sorted(locked), sorted(ep.SHAPE_CUES))
        self.assertEqual(sorted(locked), sorted(ep.VALID_SHAPES))

    def test_unclassified_is_a_category_but_not_taxonomy(self):
        self.assertEqual("unclassified", ep.UNCLASSIFIED_CATEGORY)
        self.assertIn("unclassified", ep.EDGE_VALIDATORS["categories"])
        self.assertFalse(any(entry["id"] == "unclassified" for entry in ep.TAXONOMY))
        self.assertEqual(["explicit", "backstop"], ep.EDGE_VALIDATORS["verification"])


class ProposeEdgesTests(unittest.TestCase):
    def test_rounding_requirement(self):
        edges = ep.propose_edges({"id": "R1", "text": "Round a number to N decimal places"})
        self.assertEqual(["boundary", "precision"], categories(edges))
        for edge in edges:
            self.assertEqual(("R1", "unresolved", None, None, None), (edge["requirement_id"], edge["status"], edge["verification"], edge["resolution"], edge["reason"]))
            self.assertIsInstance(edge["probe"], str)
        self.assertEqual(ep.TAXONOMY[0]["probe"], edges[0]["probe"])

    def test_authored_shapes_override(self):
        self.assertEqual(["adjacency", "empty", "ordering"], categories(ep.propose_edges({"id": "R9", "text": "opaque label", "shapes": ["collection"]})))
        self.assertEqual(["boundary", "precision"], categories(ep.propose_edges({"id": "R1", "text": "opaque", "shapes": ["numeric-range"]})))

    def test_empty_shapes_override(self):
        self.assertEqual([], ep.propose_edges({"id": "R1", "text": "merge intervals", "shapes": []}))
        self.assertEqual([], ep.propose_edges({"id": "R1", "text": "Display the company logo", "shapes": []}))
        self.assertEqual([], ep.propose_edges({"id": "R1", "shapes": []}))
        self.assertTrue(ep.propose_edges({"id": "R1", "shapes": ["numeric-range"]}))
        self.assertTrue(ep.propose_edges({"id": "R1", "text": "merge intervals"}))

    def test_unclassified_candidate(self):
        edges = ep.propose_edges({"id": "R1", "text": "Display the company logo"})
        self.assertEqual([{"requirement_id": "R1", "category": "unclassified", "status": "unresolved", "verification": None,
                           "resolution": None, "reason": None, "probe": "unclassified — review manually"}], edges)
        self.assertFalse(any(edge["category"] == "unclassified" for edge in ep.propose_edges({"id": "R1", "text": "Round a number to N decimal places"})))

    def test_invalid_authored_shapes_fail_closed(self):
        for shapes in (["numeric"], ["numeric-range", "bogus"], [42]):
            with self.assertRaisesRegex(ValueError, "(?i)invalid shape"):
                ep.propose_edges({"id": "R1", "text": "Round a number", "shapes": shapes})
        with self.assertRaises(ValueError) as caught:
            ep.propose_edges({"id": "R1", "text": "x", "shapes": ["numeric"]})
        self.assertEqual('invalid shape "numeric" for requirement R1 — must be one of: numeric-range, collection, text, stateful, io', str(caught.exception))
        with self.assertRaisesRegex(ValueError, "invalid shape 42"):
            ep.propose_edges({"id": "R1", "text": "x", "shapes": [42]})

    def test_input_validation(self):
        with self.assertRaisesRegex(ValueError, "(?i)shapes must be an array"):
            ep.propose_edges({"id": "R1", "text": "x", "shapes": "numeric-range"})
        with self.assertRaisesRegex(ValueError, "(?i)requirement id must be a non-empty string"):
            ep.propose_edges({"text": "x"})
        with self.assertRaisesRegex(ValueError, "(?i)requirement id must be a non-empty string"):
            ep.propose_edges({"id": "   ", "text": "x"})
        with self.assertRaisesRegex(ValueError, "(?i)text must be a string"):
            ep.propose_edges({"id": "R1", "text": 42})
        for requirement in ({"id": "R1"}, {"id": "R1", "text": ""}, {"id": "R1", "text": "   "}):
            with self.assertRaisesRegex(ValueError, "(?i)text must be a non-empty string when no shapes override"):
                ep.propose_edges(requirement)


class ValidateResolutionTests(unittest.TestCase):
    def rejects(self, pattern, value):
        with self.assertRaisesRegex(ValueError, pattern):
            ep.validate_resolution(value)

    def test_status_rules(self):
        self.rejects("(?i)invalid status", resolution("boundary", "maybe"))
        self.rejects("(?i)invalid status", resolution("boundary", "covered", resolution="x"))
        self.rejects("(?i)dismissed requires a reason", resolution("boundary", "dismissed", reason=""))
        self.assertIs(True, ep.validate_resolution(resolution("boundary", "dismissed", reason="bounded enum")))

    def test_verification_rules(self):
        self.rejects("(?i)verification", resolution("boundary", "resolved", resolution="AC"))
        self.rejects("(?i)invalid verification", resolution("boundary", "resolved", verification="judgment", resolution="AC"))

    def test_explicit_needs_resolution(self):
        for fields in ({"resolution": ""}, {"resolution": "   "}, {}):
            self.rejects("(?i)explicit requires a resolution", resolution("boundary", "resolved", verification="explicit", **fields))
        self.assertIs(True, ep.validate_resolution(resolution("boundary", "resolved", verification="explicit", resolution="AC#3: boundary tested in suite")))

    def test_backstop_needs_resolution(self):
        for fields in ({"resolution": ""}, {"resolution": "   "}, {}):
            self.rejects("(?i)backstop requires a resolution", resolution("boundary", "resolved", verification="backstop", **fields))
        self.assertIs(True, ep.validate_resolution(resolution("boundary", "resolved", verification="backstop", resolution="held-out: covered by integration fuzz suite")))


class AnalyzeCoverageTests(unittest.TestCase):
    REQS = [{"id": "R1", "text": "Merge a list of overlapping intervals"}]

    def test_no_resolutions(self):
        self.assertEqual({"applicable": 3, "resolved": 0, "unresolved": 3, "unclassified": 0, "byVerification": {"explicit": 0, "backstop": 0}},
                         ep.analyze_coverage(self.REQS, [])["coverage"])
        self.assertEqual(3, ep.analyze_coverage(self.REQS)["coverage"]["applicable"])

    def test_merges_resolved_explicit(self):
        report = ep.analyze_coverage(self.REQS, [resolution("adjacency", "resolved", verification="explicit", resolution="AC#6: touching intervals merge")])
        adjacency = next(i for i in report["items"] if i["category"] == "adjacency")
        self.assertEqual(("resolved", "explicit", "AC#6: touching intervals merge"), (adjacency["status"], adjacency["verification"], adjacency["resolution"]))
        self.assertEqual((1, 2, {"explicit": 1, "backstop": 0}),
                         (report["coverage"]["resolved"], report["coverage"]["unresolved"], report["coverage"]["byVerification"]))

    def test_invalid_resolution_throws(self):
        with self.assertRaisesRegex(ValueError, "(?i)dismissed requires a reason"):
            ep.analyze_coverage(self.REQS, [resolution("empty", "dismissed")])

    def test_duplicate_resolution_and_distinct_pairs(self):
        with self.assertRaisesRegex(ValueError, "(?i)duplicate resolution"):
            ep.analyze_coverage(self.REQS, [resolution("adjacency", "resolved", verification="explicit", resolution="AC#1"),
                                            resolution("adjacency", "resolved", verification="explicit", resolution="AC#2")])
        ep.analyze_coverage(self.REQS, [resolution("adjacency", "resolved", verification="explicit", resolution="AC#6: touching intervals merge"),
                                        resolution("ordering", "dismissed", resolution=None, reason="output is canonically sorted; no tie possible")])

    def test_unclassified_flow(self):
        reqs = [{"id": "R1", "text": "Display the company logo"}]
        report = ep.analyze_coverage(reqs)
        self.assertEqual((1, 1, 1, "unclassified"), (report["coverage"]["applicable"], report["coverage"]["unresolved"], report["coverage"]["unclassified"], report["items"][0]["category"]))
        dismissed = ep.analyze_coverage(reqs, [resolution("unclassified", "dismissed", reason="genuinely edge-free — static asset")])
        self.assertEqual("dismissed", dismissed["items"][0]["status"])

    def test_orphan_resolutions_are_rejected(self):
        reqs = [{"id": "R1", "text": "Round a number to N decimal places"}]
        for category in ("precison", "encoding"):
            with self.assertRaisesRegex(ValueError, "(?i)unknown resolution|no matching proposed"):
                ep.analyze_coverage(reqs, [resolution(category, "resolved", verification="explicit", resolution="AC")])
        report = ep.analyze_coverage(reqs, [resolution("precision", "resolved", verification="explicit", resolution="AC: precision tested")])
        self.assertEqual(1, report["coverage"]["resolved"])

    def test_requirement_list_validation(self):
        with self.assertRaisesRegex(ValueError, "(?i)requirements must be an array"):
            ep.analyze_coverage("nope")
        with self.assertRaisesRegex(ValueError, "(?i)duplicate requirement"):
            ep.analyze_coverage([{"id": "R1", "text": "a"}, {"id": "R1", "text": "b"}])
        with self.assertRaisesRegex(ValueError, "(?i)text must be a non-empty string when no shapes override"):
            ep.analyze_coverage([{"id": "R1"}])
        with self.assertRaisesRegex(ValueError, "(?i)invalid shape"):
            ep.analyze_coverage([{"id": "R1", "text": "Round a number", "shapes": ["numeric"]}])

    def test_explicit_empty_shapes_produce_no_items(self):
        report = ep.analyze_coverage([{"id": "R1", "text": "merge intervals", "shapes": []}])
        self.assertEqual(([], 0), (report["items"], report["coverage"]["applicable"]))


class TextEnTests(unittest.TestCase):
    PT = "O sistema mescla intervalos sobrepostos em uma lista ordenada"
    EN = "The system merges overlapping intervals in a sorted list"

    def test_fallback_to_text(self):
        self.assertEqual(["boundary", "precision"], categories(ep.propose_edges({"id": "R1", "text": "Round a number to N decimal places"})))
        self.assertEqual(["boundary", "precision"], categories(ep.propose_edges({"id": "R1", "text": "Round a number to N decimal places", "text_en": None})))

    def test_text_en_drives_classification(self):
        self.assertEqual(["unclassified"], [edge["category"] for edge in ep.propose_edges({"id": "R1", "text": self.PT})])
        self.assertEqual(["adjacency", "empty", "ordering"], categories(ep.propose_edges({"id": "R1", "text": self.PT, "text_en": self.EN})))
        self.assertEqual(categories(ep.propose_edges({"id": "R1", "text": self.EN})),
                         categories(ep.propose_edges({"id": "R1", "text": self.PT, "text_en": self.EN})))

    def test_text_en_validation(self):
        ep.validate_requirement({"id": "R1", "text": "Round a number", "text_en": None})
        for bad in ("", "   ", 42, ["x"], {}):
            with self.assertRaisesRegex(ValueError, "(?i)text_en must be a non-empty string when present"):
                ep.validate_requirement({"id": "R1", "text": "Round a number", "text_en": bad})
        with self.assertRaisesRegex(ValueError, "(?i)text_en must be a non-empty string when present"):
            ep.validate_requirement({"id": "R1", "text": "x", "text_en": "", "shapes": ["collection"]})

    def test_shapes_override_wins_over_text_en(self):
        self.assertEqual(["boundary", "precision"], categories(ep.propose_edges({"id": "R9", "text": self.PT, "text_en": self.EN, "shapes": ["numeric-range"]})))


class GoldenFixtureTests(unittest.TestCase):
    def test_at_least_six_fixtures(self):
        self.assertGreaterEqual(len([d for d in FIXTURES.iterdir() if d.is_dir()]), 6)

    def test_fixtures_match_golden_coverage(self):
        for directory in sorted(d for d in FIXTURES.iterdir() if d.is_dir()):
            with self.subTest(fixture=directory.name):
                requirements = json.loads((directory/"requirements.json").read_text(encoding="utf-8"))
                resolutions_path = directory/"resolutions.json"
                resolutions = json.loads(resolutions_path.read_text(encoding="utf-8")) if resolutions_path.exists() else []
                expected = json.loads((directory/"expected-coverage.json").read_text(encoding="utf-8"))
                self.assertEqual(expected, ep.analyze_coverage(requirements, resolutions))


class EdgeProbeCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.dir = Path(self.temporary.name)

    def write(self, name, content):
        path = self.dir/name
        path.write_text(content if isinstance(content, str) else json.dumps(content), encoding="utf-8")
        return path

    def run_module(self, *args):
        return subprocess.run([sys.executable, "-m", "lib.edge_probe", *map(str, args)], cwd=BIN, capture_output=True, text=True)

    def test_prints_coverage_report(self):
        process = self.run_module(self.write("requirements.json", [{"id": "R1", "text": "Round a number to N decimal places"}]))
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual(ZERO_COVERAGE_2, json.loads(process.stdout)["coverage"])
        self.assertTrue(process.stdout.endswith("}\n"))

    def test_no_args_exits_2_with_usage(self):
        process = self.run_module()
        self.assertEqual(2, process.returncode)
        self.assertIn("usage: edge_probe.py <requirements.json> [resolutions.json]", process.stderr)

    def test_invalid_json_exits_2(self):
        bad = self.write("bad.json", "not valid json {{{")
        self.assertEqual(2, self.run_module(bad).returncode)
        good = self.write("req.json", [{"id": "R1", "text": "Round a number to N decimal places"}])
        process = self.run_module(good, bad)
        self.assertEqual(2, process.returncode)
        self.assertIn("cannot parse JSON from", process.stderr)

    def test_missing_file_exits_2(self):
        self.assertEqual(2, self.run_module(self.dir/"missing.json").returncode)

    def test_invalid_shape_and_resolution_exit_2(self):
        process = self.run_module(self.write("req.json", [{"id": "R1", "text": "Round a number", "shapes": ["numeric"]}]))
        self.assertEqual(2, process.returncode)
        self.assertIn("error: invalid shape", process.stderr)
        good = self.write("good.json", [{"id": "R1", "text": "Round a number to N decimal places"}])
        process = self.run_module(good, self.write("res.json", [resolution("precision", "dismissed")]))
        self.assertEqual(2, process.returncode)
        self.assertIn("dismissed requires a reason", process.stderr)

    def test_resolutions_file_is_applied(self):
        good = self.write("good.json", [{"id": "R1", "text": "Round a number to N decimal places"}])
        res = self.write("res.json", [resolution("precision", "resolved", verification="explicit", resolution="AC#1")])
        process = self.run_module(good, res)
        self.assertEqual(0, process.returncode, process.stderr)
        self.assertEqual(1, json.loads(process.stdout)["coverage"]["resolved"])

    def test_main_returns_exit_code_in_process(self):
        good = self.write("good.json", [{"id": "R1", "text": "Round a number to N decimal places"}])
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(2, ep.main([]))
            self.assertEqual(0, ep.main([str(good)]))
        self.assertEqual(ZERO_COVERAGE_2, json.loads(out.getvalue())["coverage"])


if __name__ == "__main__":
    unittest.main()
