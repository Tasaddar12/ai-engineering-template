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
