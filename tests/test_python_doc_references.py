"""Keep active helper instructions on the Python runtime interfaces."""
from pathlib import Path
import importlib.util
import re
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DOCS = (
    "engineer/workflows/code-review.md",
    "engineer/workflows/spec-phase.md",
    "engineer/workflows/ui-phase.md",
    "engineer/workflows/health.md",
    "engineer/workflows/fast.md",
    "engineer/workflows/new-project.md",
    "engineer/workflows/quick.md",
    "engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md",
    "engineer/references/specless-probe-fallback.md",
    "engineer/references/response-language-directive.md",
    "engineer/references/dispatch-isolation-gate.md",
    "engineer/templates/README.md",
    "engineer/templates/state.md",
)
LEGACY_CALL = re.compile(
    r"(?im)^\s*(?:node\s+(?:-e|-p|[^\s]*\.cjs)|npm\s+[^\n]*build:lib)\b"
)
FENCE = re.compile(r"```[^\n]*\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)
MIRRORS = (
    ("commands/code-review.md", "skills/code-review/SKILL.md"),
    ("commands/spec-phase.md", "skills/spec-phase/SKILL.md"),
    ("commands/ui-phase.md", "skills/ui-phase/SKILL.md"),
    ("commands/fast.md", "skills/fast/SKILL.md"),
    ("commands/health.md", "skills/health/SKILL.md"),
    ("commands/new-project.md", "skills/new-project/SKILL.md"),
    ("commands/quick.md", "skills/quick/SKILL.md"),
    ("commands/execute-phase.md", "skills/execute-phase/SKILL.md"),
)


class PythonDocReferences(unittest.TestCase):
    def test_spec_section_runtime_distinguishes_heading_from_supplied_rows(self):
        module_path = ROOT / "engineer/bin/lib/spec_section.py"
        spec = importlib.util.spec_from_file_location("spec_section_under_test", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing-SPEC.md"
            self.assertEqual(module.spec_section_status(missing, "edges"),
                             {"key": "edges", "present": False, "dataRows": 0, "supplied": False})
            empty = Path(directory) / "empty-SPEC.md"
            empty.write_text("# Spec\n\n## Edge Coverage\n", encoding="utf-8")
            self.assertEqual(module.spec_section_status(empty, "edges")["supplied"], False)
            no_rows = Path(directory) / "header-only-SPEC.md"
            no_rows.write_text("## Prohibitions\n| Kind | Rule |\n|---|---|\n", encoding="utf-8")
            header_status = module.spec_section_status(no_rows, "prohibitions")
            self.assertTrue(header_status["present"])
            self.assertEqual(header_status["dataRows"], 0)
            self.assertFalse(header_status["supplied"])
            populated = Path(directory) / "populated-SPEC.md"
            populated.write_text("## Edge Coverage\n| A | B |\n|---|---|\n| x | y |\n", encoding="utf-8")
            populated_status = module.spec_section_status(populated, "edges")
            self.assertEqual(populated_status["dataRows"], 1)
            self.assertTrue(populated_status["supplied"])

    def test_full_workflow_tree_has_no_live_node_helper_invocations(self):
        invocation = re.compile(r"(?im)^\s*node\s+(?:-e|-p|[^\s]*\.cjs)\b")
        for path in sorted((ROOT / "engineer/workflows").rglob("*.md")):
            relative = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8")
            self.assertEqual(len(re.findall(r"(?m)^```", text)) % 2, 0, relative)
            for block in FENCE.findall(text):
                self.assertIsNone(invocation.search(block), relative)

    def test_specless_fallback_requires_supplied_data_rows(self):
        text = (ROOT / "engineer/references/specless-probe-fallback.md").read_text(encoding="utf-8")
        self.assertIn("--pick supplied", text)
        self.assertNotRegex(text, r"spec\.section[^\n]*--pick present")
        self.assertIn("Empty headings and header/separator-only tables", text)

    def test_active_helper_examples_do_not_execute_legacy_node_scripts(self):
        for relative in ACTIVE_DOCS:
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                fences = re.findall(r"(?m)^```", text)
                self.assertEqual(len(fences) % 2, 0, relative)
                for block in FENCE.findall(text):
                    self.assertIsNone(LEGACY_CALL.search(block), relative)

    def test_replaced_interfaces_are_named_in_the_live_docs(self):
        expected = {
            "engineer/workflows/code-review.md": ("review.flags", "review.depth", "review.normalize-fallow"),
            "engineer/workflows/spec-phase.md": ("spec.edge-probe",),
            "engineer/workflows/ui-phase.md": ("spec.ui-probe",),
            "engineer/references/specless-probe-fallback.md": ("spec.section", "spec.edge-probe"),
            "engineer/workflows/health.md": ("gen-health-docs", "lint-health-diagnostic-rule-table"),
            "engineer/references/response-language-directive.md": ("lint-response-language-coverage",),
        }
        for relative, interfaces in expected.items():
            with self.subTest(path=relative):
                text = (ROOT / relative).read_text(encoding="utf-8")
                for interface in interfaces:
                    self.assertIn(interface, text)

    def test_commands_and_skills_mirrors_are_identical(self):
        for command, skill in MIRRORS:
            with self.subTest(command=command, skill=skill):
                self.assertEqual(
                    (ROOT / command).read_bytes(),
                    (ROOT / skill).read_bytes(),
                )


if __name__ == "__main__":
    unittest.main()
