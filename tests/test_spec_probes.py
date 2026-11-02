import json
import importlib
import importlib.util
from pathlib import Path
import sys
try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE


LIB = SOURCE/"engineer/bin/lib"


def _load(name):
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("engineer_bin_lib."+name)


spec_section = _load("spec_section")
ui_consideration_probe = _load("ui_consideration_probe")


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

    def test_section_status_cli_matches_canonical_helper(self):
        boundary_only = self.put("BOUNDARIES.md", "## Boundaries\n- API input stops at the HTTP boundary.\n\n## Edge Coverage\n")
        expected = spec_section.spec_section_status(str(boundary_only), "edges")
        self.assertEqual({"key": "edges", "present": True, "dataRows": 0, "supplied": False}, expected)
        self.assertEqual(expected, self.cli("spec.section-status", boundary_only, "edges"))

        table = self.put("TABLE.md", "## Edge Coverage\n\n| Category | Requirement |\n|---|---|\n| empty | R1 |\n")
        expected = spec_section.spec_section_status(str(table), "edges")
        self.assertEqual({"key": "edges", "present": True, "dataRows": 1, "supplied": True}, expected)
        self.assertEqual(expected, self.cli("spec.section-status", table, "edges"))
        self.cli("spec.section-status", table, "bogus", status=2, raw=True)

    def test_ui_probe_cli_matches_canonical_adapter_and_preserves_spec_ui(self):
        elements = [{"id": "E1", "text": "A password input with search results"}]
        resolutions = [{"requirement_id": "E1", "category": "error", "status": "resolved",
                        "verification": "explicit", "resolution": "Show a useful failure state"}]
        elements_path = self.put("elements.json", json.dumps(elements))
        resolutions_path = self.put("resolutions.json", json.dumps(resolutions))
        expected = ui_consideration_probe.analyze_coverage(elements, resolutions)
        actual = self.cli("spec.ui-probe", elements_path, "--resolutions", resolutions_path)
        self.assertEqual(expected, actual)
        self.assertEqual(8, len({item["category"] for item in actual["items"]}))
        self.assertTrue(any(item["requirement_id"] == "E1" and item["status"] == "resolved"
                            for item in actual["items"]))

        invalid = self.put("invalid-elements.json", json.dumps([{"id": "E1", "text": "Surface", "elements": ["unknown"]}]))
        self.cli("spec.ui-probe", invalid, status=2, raw=True)
        malformed = self.put("malformed.json", "{")
        self.cli("spec.ui-probe", malformed, status=2, raw=True)
        orphan = self.put("orphan-resolutions.json", json.dumps([{"requirement_id": "wrong", "category": "error",
                                                                   "status": "resolved", "verification": "explicit",
                                                                   "resolution": "Show an error"}]))
        self.cli("spec.ui-probe", elements_path, "--resolutions", orphan, status=2, raw=True)

        legacy = self.cli("spec.ui", elements_path)
        self.assertFalse(legacy["behaviorVerified"])
        self.assertIn("element_id", legacy["items"][0])
