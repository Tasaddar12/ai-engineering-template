from pathlib import Path
import tempfile
import unittest
from tests.test_overhaul_scripts import load_tool


tool = load_tool("no_node")


class NoNodeWorkflowHelpers(unittest.TestCase):
    def test_workflow_helpers_are_rejected_but_project_syntax_examples_are_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "engineer/bin").mkdir(parents=True)
            (root / "engineer/bin/probe.cjs").write_text("module.exports = {}", encoding="utf-8")
            (root / "engineer/method.md").write_text('node -e "JSON.parse(input)"\nnode --print version\n', encoding="utf-8")
            self.assertEqual(list(tool.findings(root)), [
                ("engineer/bin/probe.cjs", 1, "CommonJS helper file"),
                ("engineer/method.md", 1, "inline Node helper"),
                ("engineer/method.md", 2, "inline Node helper"),
            ])

    def test_generic_javascript_extensions_and_optional_project_checker_are_not_dependencies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "agents").mkdir()
            (root / "agents/method.md").write_text('Inspect app.cjs as project source.\nUse configured project syntax tool: node --check app.js\n', encoding="utf-8")
            self.assertEqual([], list(tool.findings(root)))
