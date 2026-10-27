from pathlib import Path
import tempfile
import unittest
from tests.test_overhaul_scripts import load_tool

tool = load_tool("links")


class LinksTests(unittest.TestCase):
    def test_local_relative_rooted_and_includes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "agents").mkdir()
            (root / "engineer" / "references").mkdir(parents=True)
            target = root / "engineer" / "references" / "file with spaces.md"
            target.write_text("# Heading\n", encoding="utf-8")
            source = root / "agents" / "a.md"
            source.write_text("[ok](../engineer/references/file%20with%20spaces.md#heading)\n[remote](https://example.org/missing)\n@engineer/references/missing.md\n[bad](../outside.md)\n", encoding="utf-8")
            self.assertEqual(list(tool.broken_links(root)), [("agents/a.md", 4, "../outside.md"), ("agents/a.md", 3, "engineer/references/missing.md")])

    def test_dynamic_paths_are_ignored_and_home_paths_are_reported(self):
        root = Path.cwd()
        source = root / "agents/a.md"
        self.assertIsNone(tool.resolve_target(root, source, "engineer/${NAME}.md", True))
        self.assertFalse(tool.resolve_target(root, source, "~/.claude/gsd-core/workflows/old.md", True))
        self.assertIsNone(tool.resolve_target(root, source, "#heading"))
