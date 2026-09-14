"""Check navigable local workflow guidance after the planning/template cutover."""
from pathlib import Path
import posixpath
import re
import unittest
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


def guidance_files():
    for name in ("AGENTS.md", "CLAUDE.md", "README.md"):
        if (ROOT / name).is_file():
            yield ROOT / name
    for directory in (".ai", ".codex", ".claude", ".agents", ".planning", "docs"):
        for path in (ROOT / directory).rglob("*.md"):
            relative = path.relative_to(ROOT).as_posix()
            if any(relative.startswith(root + "/templates/") for root in (".ai", ".codex", ".claude")):
                continue  # Imported source has its own provenance/reference audit.
            yield path


def without_fences(text):
    text = re.sub(r"(?ms)^```[^\n]*\n.*?^```\s*$", "", text)
    return re.sub(r"`+[^`\n]*`+", "", text)  # Literal link syntax in inline examples is not navigation.


class WorkflowNavigationTests(unittest.TestCase):
    def test_literal_link_examples_do_not_hide_real_navigation(self):
        body = without_fences("`[example](missing.md)` and [actual](required.md)\n"
                              "```markdown\n[example](also-missing.md)\n```\n")
        self.assertNotIn("missing.md", body)
        self.assertIn("[actual](required.md)", body)

    def test_local_guidance_links_resolve_with_portable_case(self):
        failures = []
        for source in guidance_files():
            text = without_fences(source.read_text(encoding="utf-8-sig"))
            for match in re.finditer(r"\[[^\]\n]+\]\(([^)\n]+)\)", text):
                target = match[1].strip().strip("<>")
                if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target):
                    continue
                file_part = unquote(target.split("#", 1)[0])
                if not file_part:
                    continue
                relative_text = posixpath.normpath(source.parent.relative_to(ROOT).as_posix() + "/" + file_part)
                destination = (ROOT / relative_text).resolve()
                label = f"{source.relative_to(ROOT)} -> {target}"
                if not destination.is_relative_to(ROOT) or not destination.exists():
                    failures.append(label + " (missing or outside repository)")
                    continue
                # resolve() can correct filename casing on Windows. Audit the
                # spelling in the link, not the filesystem's corrected result.
                relative = Path(relative_text)
                cursor = ROOT
                for part in relative.parts:
                    if part not in {child.name for child in cursor.iterdir()}:
                        failures.append(label + " (case does not match tracked path)")
                        break
                    cursor /= part
        self.assertEqual([], failures, "\n".join(failures))


if __name__ == "__main__":
    unittest.main()
