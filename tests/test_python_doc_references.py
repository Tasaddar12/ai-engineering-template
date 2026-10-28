"""Keep active helper instructions on the Python runtime interfaces."""
from pathlib import Path
import re
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
