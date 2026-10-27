import unittest
from tests.test_overhaul_scripts import load_tool

common = load_tool("common")


class ProgressTests(unittest.TestCase):
    def test_only_terminal_exact_rows_trailers_count(self):
        messages = "feat: first\n\nRows: R-AG-001, V-24\n\x1eNotes mention Rows: R-AG-002\n\x1efix: next\n\nRows: R-WF-003\n\nmore prose\n\x1echore: final\n\nRows: C-01\nSigned-off-by: Name <name@example.com>\n"
        self.assertEqual(common.completed_rows(messages), {"R-AG-001", "V-24", "C-01"})

    def test_row_catalog_excludes_feature_tables_and_handles_numeric_width(self):
        text = "## 4. Features\n| R-AG-001 | ignored |\n## 11. Agents\n| R-AG-001 | keep |\n## 14. Runtime\n| V-24 | keep |\n| C-01 | keep |\n"
        self.assertEqual(set(common.rows(text)), {"R-AG-001", "V-24", "C-01"})

    def test_feature_rows_follow_workflow_heading(self):
        text = "## 12. Workflows\n### engineer/workflows/secure-phase.md\n| R-WF-001 | future |\n### engineer/workflows/execute-phase.md\n| R-WF-002 | now |\n"
        self.assertEqual(common.deferred_workflow_rows(text), {"R-WF-001"})
