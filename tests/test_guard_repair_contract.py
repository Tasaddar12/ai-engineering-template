"""Removal protection for repair guidance, not runtime security evidence."""
import re
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ".ai/references/guard-repair-workflow.md"
ENTRY_POINTS = (
    "AGENTS.md",
    ".ai/RULES.md",
    ".ai/agents/phase-preparer.md",
    ".ai/agents/coder.md",
    ".ai/agents/code-reviewer.md",
)
LINK = re.compile(r"\[[^\]\n]+\]\((<[^>\n]+>|[^\s)\n]+)\s*\)")


def repair_links(root, source):
    """Resolve direct inline Markdown links inside the fixture's boundary."""
    path = root / source
    text = path.read_text(encoding="utf-8")
    # Examples and comments do not make guidance reachable from instructions.
    text = re.sub(r"^(`{3,}|~{3,}).*?^\1[^\n]*$", "", text,
                  flags=re.M | re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    found = []
    for match in LINK.finditer(text):
        target = urlsplit(match.group(1).strip("<>"))
        if target.scheme or target.netloc or not target.path or target.query:
            continue
        resolved = (path.parent / unquote(target.path)).resolve()
        if resolved != (root / CANONICAL).resolve() or not resolved.is_file():
            continue
        if target.fragment:
            headings = re.findall(r"^#{1,6}\s+(.+?)\s*#*\s*$",
                                  resolved.read_text(encoding="utf-8"), re.M)
            anchors = {re.sub(r"[^\w -]", "", heading.lower()).replace(" ", "-")
                       for heading in headings}
            if unquote(target.fragment) not in anchors:
                continue
        found.append(match.group(0))
    return found


def contract_errors(root):
    errors = []
    if not (root / CANONICAL).is_file():
        errors.append(CANONICAL + ": missing canonical repair reference")
    for source in ENTRY_POINTS:
        if not (root / source).is_file() or not repair_links(root, source):
            errors.append(source + ": missing direct repair guidance")
    return errors


class GuardRepairContract(unittest.TestCase):
    def fixture(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for source in ENTRY_POINTS:
            path = root / source
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text((ROOT / source).read_text(encoding="utf-8"), encoding="utf-8")
        canonical = root / CANONICAL
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text((ROOT / CANONICAL).read_text(encoding="utf-8")
                             if (ROOT / CANONICAL).is_file()
                             else "# Guard repair workflow\n", encoding="utf-8")
        # Complete the pre-implementation fixture; the real-tree assertion below
        # independently requires the actual instructions to supply these links.
        for source in ENTRY_POINTS:
            if not repair_links(root, source):
                target = {"AGENTS.md": ".ai/references/guard-repair-workflow.md",
                          ".ai/RULES.md": "references/guard-repair-workflow.md"}.get(
                              source, "../references/guard-repair-workflow.md")
                with (root / source).open("a", encoding="utf-8") as stream:
                    stream.write("\n[Guard repair](" + target + ")\n")
        return root

    def replace_links(self, root, source, replacement):
        path = root / source
        text = path.read_text(encoding="utf-8")
        links = repair_links(root, source)
        self.assertTrue(links, source)
        for link in links:
            text = text.replace(link, replacement)
        path.write_text(text, encoding="utf-8")

    def test_real_entry_points_have_direct_repair_guidance(self):
        self.assertEqual([], contract_errors(ROOT))

    def test_complete_fixture_passes(self):
        self.assertEqual([], contract_errors(self.fixture()))

    def test_each_removed_or_broken_entry_link_reports_its_source(self):
        for source in ENTRY_POINTS:
            for replacement in ("Removed guidance", "[Repair](missing.md)"):
                with self.subTest(source=source, replacement=replacement):
                    root = self.fixture()
                    self.replace_links(root, source, replacement)
                    self.assertEqual([source + ": missing direct repair guidance"],
                                     contract_errors(root))

    def test_missing_canonical_reference_is_reported(self):
        root = self.fixture()
        (root / CANONICAL).unlink()
        self.assertIn(CANONICAL + ": missing canonical repair reference",
                      contract_errors(root))

    def test_unrelated_or_indirect_links_do_not_replace_direct_guidance(self):
        for replacement in ("[Rules](.ai/RULES.md)",
                            "[Other](.ai/references/unrelated.md)",
                            "`guard-repair-workflow.md`",
                            "<!-- [Repair](.ai/references/guard-repair-workflow.md) -->",
                            "```markdown\n[Repair](.ai/references/guard-repair-workflow.md)\n```"):
            with self.subTest(replacement=replacement):
                root = self.fixture()
                (root / ".ai/references/unrelated.md").write_text("# Other\n", encoding="utf-8")
                self.replace_links(root, "AGENTS.md", replacement)
                self.assertIn("AGENTS.md: missing direct repair guidance", contract_errors(root))

    def test_targets_resolve_encoded_paths_and_existing_fragments(self):
        root = self.fixture()
        canonical = root / CANONICAL
        with canonical.open("a", encoding="utf-8") as stream:
            stream.write("\n## Fixture section\n")
        self.replace_links(root, "AGENTS.md",
                           "[Repair](<.ai/references/guard%2Drepair-workflow.md#fixture-section>)")
        self.assertEqual([], contract_errors(root))

    def test_missing_fragment_does_not_count_as_reachable_guidance(self):
        root = self.fixture()
        self.replace_links(root, "AGENTS.md",
                           "[Repair](.ai/references/guard-repair-workflow.md#missing-section)")
        self.assertIn("AGENTS.md: missing direct repair guidance", contract_errors(root))


if __name__ == "__main__":
    unittest.main()
