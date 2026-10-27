from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tests.test_overhaul_scripts import load_tool

tool = load_tool("inventory")


class InventoryTests(unittest.TestCase):
    def test_origins_line_counts_and_gsd_counts_are_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "agents").mkdir()
            (root / "docs").mkdir()
            original = b"one GSD line\n"
            (root / "agents" / "planner.md").write_bytes(original)
            (root / "agents" / "verifier.md").write_bytes(b"changed\nfull content\n")
            (root / "agents" / "local.md").write_bytes(b"new\n")
            (root / "docs" / "INVENTORY.md").write_bytes(b"old inventory\n")
            records = "100644 blob " + tool.blob_id(original) + "\tagents/gsd-planner.md\n100644 blob " + tool.blob_id(b"old\n") + "\tagents/gsd-verifier.md\n"
            with patch.object(tool, "git", return_value=records):
                rendered = tool.render_inventory(root)
                self.assertEqual(rendered, tool.render_inventory(root))
            self.assertIn("| `agents/planner.md` | upstream | 1 | 1 |", rendered)
            self.assertIn("| `agents/verifier.md` | reconciled | 2 | 0 |", rendered)
            self.assertIn("| `agents/local.md` | local-only | 1 | 0 |", rendered)
            self.assertIn("| `docs/INVENTORY.md` | local-only |", rendered)
