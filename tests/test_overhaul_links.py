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

    def test_examples_and_npm_names_do_not_hide_required_prompt_inputs(self):
        text = '''Use `@scope/pkg-name` with these examples:
```markdown
[Illustrative guide](CODE_OF_CONDUCT.md)
@engineer/references/required.md
@.planning/phases/03-example/03-01-SUMMARY.md
```
[Actual guide](../guide.md)
'''
        self.assertEqual(list(tool.targets(text)), [('../guide.md', 7, False), ('engineer/references/required.md', 4, True)])

    def test_relative_include_paths_resolve_from_document(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "agents").mkdir()
            (root / "guide.md").write_text("Guide", encoding="utf-8")
            self.assertTrue(tool.resolve_target(root, root / "agents/a.md", "../guide.md", True))
            self.assertFalse(tool.resolve_target(root, root / "agents/a.md", "../../outside.md", True))
