import unittest
from unittest.mock import patch
from tests.test_overhaul_scripts import load_tool

tool = load_tool("anchor")


class AnchorTests(unittest.TestCase):
    def test_multiple_disjoint_line_ranges(self):
        self.assertEqual(list(tool.citations("after agents/executor.md:3-4, 7; .ai/agents/coder.md:2")), [("agents/executor.md", 3, 4), ("agents/executor.md", 7, 7), (".ai/agents/coder.md", 2, 2)])
        with patch.object(tool, "git", return_value="one\ntwo\nthree\nfour\n") as read:
            result = tool.anchor_lines(None, "agents/executor.md:2,4")
        self.assertEqual(read.call_count, 1)
        self.assertEqual(result, ["agents/executor.md:2-2", "    2: two", "agents/executor.md:4-4", "    4: four"])

    def test_invalid_ranges_and_rows_fail(self):
        with self.assertRaises(ValueError):
            list(tool.citations("agents/executor.md:9-2"))
        with patch.object(tool, "git", return_value="one\n"):
            with self.assertRaises(ValueError):
                tool.anchor_lines(None, "agents/executor.md:1-3")
        with self.assertRaises(ValueError):
            tool.row_cells("## 11. Agents\n", "R-AG-999")
