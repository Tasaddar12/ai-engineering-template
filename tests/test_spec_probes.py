import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE


class SpecProbes(RuntimeCase):
    def test_upstream_oracle_fixtures(self):
        fixture_root = SOURCE/"engineer/references/edge-probe-fixtures"
        for fixture in sorted(fixture_root.iterdir()):
            if not fixture.is_dir():
                continue
            with self.subTest(fixture=fixture.name):
                requirements = self.put("requirements.json", (fixture/"requirements.json").read_text(encoding="utf-8"))
                arguments = ["spec.edge-probe", requirements]
                resolutions = fixture/"resolutions.json"
                if resolutions.exists():
                    arguments += ["--resolutions", self.put("resolutions.json", resolutions.read_text(encoding="utf-8"))]
                self.assertEqual(json.loads((fixture/"expected-coverage.json").read_text(encoding="utf-8")), self.cli(*arguments))

    def test_invalid_shape_and_sections(self):
        path = self.put("bad.json", '{"not":"array"}')
        self.cli("spec.edge-probe", path, status=2, raw=True)
        spec = self.put("SPEC.md", "# Specification\n## Edge cases\n- Empty input\n- Maximum size\n## Prohibitions\n- Must not erase data\n")
        self.assertEqual(["Empty input", "Maximum size"], self.cli("spec.section", spec, "edges")["items"])
        self.assertEqual(["Must not erase data"], self.cli("spec.section", spec, "prohibitions")["items"])

    def probe(self, requirements, resolutions=None):
        arguments = ["spec.edge-probe", self.put("requirements.json", json.dumps(requirements))]
        if resolutions is not None:
            arguments += ["--resolutions", self.put("resolutions.json", json.dumps(resolutions))]
        return self.cli(*arguments)

    def test_all_shapes_and_relevance_filter(self):
        expected = {
            "numeric-range": ["boundary", "precision"],
            "collection": ["adjacency", "empty", "ordering"],
            "text": ["empty", "encoding"],
            "stateful": ["idempotency", "concurrency"],
            "io": ["concurrency"],
        }
        for shape, categories in expected.items():
            with self.subTest(shape=shape):
                result = self.probe([{"id": "R", "text": "Opaque", "shapes": [shape]}])
                self.assertEqual(categories, [row["category"] for row in result["items"]])
                self.assertEqual(len(categories), result["coverage"]["unresolved"])
        combined = self.probe([{"id": "R", "text": "Opaque", "shapes": list(expected)}])
        self.assertEqual(8, combined["coverage"]["applicable"])
        self.assertEqual(8, len({row["category"] for row in combined["items"]}))

    def test_translation_override_optout_and_uncued_prose(self):
        result = self.probe([
            {"id": "translated", "text": "顧客情報", "text_en": "Update a session"},
            {"id": "preferred", "text": "Round numbers", "text_en": "A string"},
            {"id": "override", "text": "Round numbers", "shapes": ["io"]},
            {"id": "optout", "text": "Round numbers", "shapes": []},
            {"id": "uncued", "text": "Display the company emblem"},
            {"id": "foreign", "text": "顧客情報"},
            {"id": "empty", "text": " "},
        ])
        by_id = {}
        for row in result["items"]:
            by_id.setdefault(row["requirement_id"], []).append(row["category"])
        self.assertEqual({"translated": ["idempotency", "concurrency"],
                          "preferred": ["empty", "encoding"], "override": ["concurrency"],
                          "uncued": ["unclassified"], "foreign": ["unclassified"]}, by_id)
        self.assertEqual(2, result["coverage"]["unclassified"])

    def test_word_boundaries_do_not_classify_embedded_cues(self):
        result = self.probe([{"id": "R", "text": "Adopt a maximally streamlined outlook"}])
        self.assertEqual(["unclassified"], [row["category"] for row in result["items"]])

    def test_backstop_dismissed_and_unclassified_lifecycle(self):
        result = self.probe([{"id": "R", "text": "An opaque promise"},
                             {"id": "N", "text": "A number"}], [
            {"requirement_id": "R", "category": "unclassified", "status": "dismissed",
             "reason": "Static asset only", "verification": "explicit"},
            {"requirement_id": "N", "category": "boundary", "status": "resolved",
             "verification": "backstop", "resolution": "Held-out checks around each bound"},
        ])
        self.assertIsNone(result["items"][0]["verification"])
        self.assertEqual({"applicable": 3, "resolved": 2, "unresolved": 1,
                          "unclassified": 1, "byVerification": {"explicit": 0, "backstop": 1}},
                         result["coverage"])

    def test_invalid_authored_shapes_and_translations_fail_closed(self):
        for fields in ({"shapes": ["unknown"]}, {"shapes": "text"}, {"shapes": None},
                       {"shapes": [1]}, {"text_en": []}):
            with self.subTest(fields=fields):
                path = self.put("requirements.json", json.dumps([{"id": "R", "text": "List", **fields}]))
                self.cli("spec.edge-probe", path, status=2, raw=True)
        self.cli("spec.edge-probe", self.put("broken.json", "[invalid"), status=2, raw=True)

    def test_invalid_resolution_never_counts_as_closed(self):
        requirement = self.put("requirements.json", '[{"id":"R","text":"A number"}]')
        for fields in ({"status": "resolved", "verification": "explicit", "resolution": " "},
                       {"status": "resolved", "verification": "test", "resolution": "AC"},
                       {"status": "dismissed", "reason": " "}, {"status": "covered"}):
            with self.subTest(fields=fields):
                resolution = self.put("resolutions.json", json.dumps([
                    {"requirement_id": "R", "category": "boundary", **fields}]))
                self.cli("spec.edge-probe", requirement, "--resolutions", resolution, status=2, raw=True)
