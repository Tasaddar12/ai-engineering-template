"""The delivered complete methods remain attributable to their pinned originals."""
import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AgentSourceTests(unittest.TestCase):
    def test_full_agents_reconstruct_the_pinned_source_without_network(self):
        provenance = json.loads((ROOT / ".ai/agents/PROVENANCE.json").read_text(encoding="utf-8"))
        self.assertRegex(provenance["revision"], r"^[0-9a-f]{40}$")
        self.assertEqual(len(provenance["files"]), 11)
        paths = set()
        for entry in provenance["files"]:
            with self.subTest(agent=entry["path"]):
                self.assertNotIn(entry["path"], paths)
                paths.add(entry["path"])
                self.assertNotIn(".compact.", entry["source"])
                path = ROOT / entry["path"]
                self.assertTrue(path.resolve().is_relative_to(ROOT / ".ai/agents"))
                adapted = path.read_text(encoding="utf-8")
                self.assertEqual(hashlib.sha256(adapted.encode()).hexdigest(), entry["adapted_sha256_lf"])
                original = adapted.splitlines(keepends=True)
                self.assertEqual(len(original), entry["adapted_lines"])
                # Each inverse edit names a range in the delivered full method.
                # Applying from the end preserves earlier range coordinates.
                end = len(original)
                for edit in reversed(entry["inverse_edits"]):
                    self.assertTrue(0 <= edit["start"] <= edit["end"] <= end)
                    original[edit["start"]:edit["end"]] = edit["original"].splitlines(keepends=True)
                    end = edit["start"]
                self.assertEqual(len(original), entry["source_lines"])
                original = "".join(original)
                self.assertEqual(hashlib.sha256(original.encode()).hexdigest(), entry["source_sha256_lf"])
                # Host edits must not delete the method's section structure.
                source_sections = re.findall(r"(?m)^#{1,6} .+|^<[/\w][^>]*>$", original)
                adapted_sections = re.findall(r"(?m)^#{1,6} .+|^<[/\w][^>]*>$", adapted)
                self.assertGreaterEqual(len(adapted_sections), len(source_sections))


if __name__ == "__main__":
    unittest.main()
