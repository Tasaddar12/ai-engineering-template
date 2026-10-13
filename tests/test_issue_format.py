"""Template-derived structural gate, including installed namespace resolution."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".ai/runtime"))
from lib import issue_format
from lib.results import VerbError

TEMPLATE = ROOT / ".ai/templates/issue.md"


def bodies():
    text = TEMPLATE.read_text(encoding="utf-8")
    return dict(re.findall(r"^### ([^\n]+)\n\n```markdown\n(.*?)\n```", text, re.M | re.S))


class IssueFormat(unittest.TestCase):
    def assert_invalid(self, body, variant="UAT", code="issue-format"):
        with self.assertRaises(VerbError) as caught:
            issue_format.validate(body, variant)
        self.assertEqual(caught.exception.code, code)

    def test_all_canonical_variants(self):
        self.assertEqual(list(issue_format.schema()),
                         ["Bug", "Enhancement", "Decision required", "Security risk", "UAT"])
        for variant, body in bodies().items():
            with self.subTest(variant=variant):
                self.assertTrue(issue_format.validate(body, variant)["valid"])

    def test_missing_unknown_or_noncanonical_variant(self):
        for variant in (None, "", "bug", "expected-behavior", True):
            self.assert_invalid(bodies()["Bug"], variant, "issue-variant")

    def test_missing_out_of_order_duplicate_headings_all_variants(self):
        for variant, body in bodies().items():
            headings = re.findall(r"^## .+$", body, re.M)
            changes = (body.replace(headings[0], "", 1),
                       body.replace(headings[0], "SWAP", 1).replace(
                           headings[1], headings[0], 1).replace("SWAP", headings[1], 1),
                       body.replace(headings[0], headings[1], 1),
                       body + "\n" + headings[0],
                       body.replace(headings[0], "## Unexpected", 1))
            for changed in changes:
                with self.subTest(variant=variant, changed=changed[:60]):
                    self.assert_invalid(changed, variant)

    def test_literal_headings_do_not_satisfy_shape(self):
        body = bodies()["Bug"]
        for fake in ("```markdown\n## Problem\n```", "~~~\n## Problem\n~~~",
                     "    ## Problem", "> ## Problem", "| ## Problem |",
                     "<!--\n## Problem\n-->"):
            self.assert_invalid(body.replace("## Problem", fake, 1), "Bug")
        self.assertTrue(issue_format.validate(body + "\n```\n## Problem\n```", "Bug")["valid"])

    def test_uat_header_columns_separator_and_numbered_rows(self):
        body = bodies()["UAT"]
        for changed in (body.replace("| Step |", "| Case |"),
                        body.replace("|---|---|---|---|", "|---|---|---|"),
                        body.replace("| 1 |", "| one |"),
                        body.replace("| 2 |", "| 3 |"),
                        body.replace("| 2 |", "| 1 |"),
                        body.replace("| 1 |", "| 1 | extra |"),
                        body.replace("| 1 |", "| 1 |\n")):
            with self.subTest(changed=changed[:80]):
                self.assert_invalid(changed)

    def test_html_literal_blocks_do_not_supply_headings_or_tables(self):
        for variant in ("Bug", "UAT"):
            body = bodies()[variant]
            for tag in ("pre", "script", "style", "textarea"):
                for opening in ("<" + tag + ">", "<" + tag.upper() + " class=\"literal\">",
                                "<" + tag + "\n>", "<" + tag + "\n class=\"literal\">"):
                    with self.subTest(variant=variant, opening=opening):
                        self.assert_invalid(opening + "\n" + body + "\n</" + tag + ">", variant)
            with self.subTest(variant=variant, unclosed=True):
                self.assert_invalid("<pre>\n" + body, variant)

    def test_mixed_indent_does_not_supply_uat_table(self):
        body = bodies()["UAT"]
        for prefix in (" \t", "  \t", "   \t", "\t "):
            with self.subTest(prefix=repr(prefix)):
                self.assert_invalid(re.sub(r"^(\|.*)$", lambda match: prefix + match[1], body, flags=re.M))

    def test_raw_html_tables_do_not_supply_markdown_table(self):
        body = bodies()["UAT"]
        table = re.search(r"^\| Step .*?(?=\n\n)", body, re.M | re.S).group()
        for tag in ("div", "table"):
            for opening in ("<" + tag + ">", "<" + tag + "\n>",
                            "<" + tag + "\n class=\"literal\">", "<" + tag + "> leading prose"):
                with self.subTest(tag=tag, opening=opening):
                    self.assert_invalid(body.replace(table, opening + "\n" + table + "\n</" + tag + ">"))

    def test_comment_prefixes_and_raw_instructions_do_not_supply_structure(self):
        bug = bodies()["Bug"]
        for prefix in ("<!--x-->", "<!-- literal\n-->"):
            with self.subTest(prefix=prefix):
                self.assert_invalid(bug.replace("## Problem", prefix + "## Problem", 1), "Bug")
        uat = bodies()["UAT"]
        with self.subTest(prefix="table comments"):
            self.assert_invalid(re.sub(r"^(\|.*)$", lambda match: "<!--x-->" + match[1], uat, flags=re.M))
        table = re.search(r"^\| Step .*?(?=\n\n)", uat, re.M | re.S).group()
        for opening, closing in (("<?literal", "?>"), ("<!DOCTYPE literal", ">"),
                                 ("<![CDATA[", "]]>")):
            with self.subTest(opening=opening):
                self.assert_invalid(uat.replace(table, opening + "\n" + table + "\n" + closing))

    def test_literal_examples_and_shallow_tables_preserve_real_structure(self):
        for variant, body in bodies().items():
            extra = "\n<pre class=\"literal\">\n## Problem\n| Fake | Table |\n</PRE>\n"
            extra += "\n```html\n<pre>\n## Problem\n</pre>\n```\n"
            extra += "\n    ## Problem\n \t## Problem\n"
            extra += "\n- Example with `<pre>` and inline code.\n| Example | `<pre>` |\n"
            extra += "\n<preview>\nExample unrelated tag.\n</preview>\n"
            with self.subTest(variant=variant):
                self.assertTrue(issue_format.validate(body + extra, variant)["valid"])
                self.assertTrue(issue_format.validate(
                    "<preview>\nExample unrelated tag.\n</preview>\n\n" + body, variant)["valid"])
                self.assertTrue(issue_format.validate(body + "\n<!-- todo-id: fixture -->\n", variant)["valid"])
        for spaces in (1, 2, 3):
            padded = re.sub(r"^(\|.*)$", lambda match: " " * spaces + match[1], bodies()["UAT"], flags=re.M)
            self.assertTrue(issue_format.validate(padded, "UAT")["valid"])

    def test_literal_tables_and_acceptance_fields_do_not_satisfy_shape(self):
        body = bodies()["UAT"]
        table = re.search(r"^\| Step .*?(?=\n\n)", body, re.M | re.S).group()
        for fake in ("```\n" + table + "\n```", "<!--\n" + table + "\n-->",
                     "\n".join("    " + line for line in table.splitlines())):
            self.assert_invalid(body.replace(table, fake))
        for changed in (body.replace("Reviewer:", "Observer:"),
                        body + "\nReviewer: Duplicate",
                        re.sub(r"^Date:.*$", "Date:", body, flags=re.M),
                        body.replace("Status:", "    Status:")):
            self.assert_invalid(changed)

    def test_schema_missing_malformed_and_derived(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "issue.md"
            malformed = ("", "## Problem\n", TEMPLATE.read_text(encoding="utf-8").replace(
                "| Step |", "| Step | Added |"),
                TEMPLATE.read_text(encoding="utf-8").replace("| Step |", "|  |"),
                TEMPLATE.read_text(encoding="utf-8").replace("### Bug", "### Removed", 1),
                TEMPLATE.read_text(encoding="utf-8").replace("```markdown", "```text", 1))
            for text in malformed:
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(VerbError) as caught:
                    issue_format.validate(bodies()["Bug"], "Bug", path)
                self.assertEqual(caught.exception.code, "issue-schema")
            path.unlink()
            with self.assertRaises(VerbError) as caught:
                issue_format.validate(bodies()["Bug"], "Bug", path)
            self.assertEqual(caught.exception.code, "issue-schema")
            path.write_text(TEMPLATE.read_text(encoding="utf-8").replace(
                "## Expected behavior", "## Expected result"), encoding="utf-8")
            self.assertTrue(issue_format.validate(bodies()["Bug"].replace(
                "## Expected behavior", "## Expected result"), "Bug", path)["valid"])

    def test_installed_namespace_owns_schema_even_with_sibling_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for namespace in (".codex", ".claude"):
                runtime = root / namespace / "runtime"
                shutil.copytree(ROOT / ".ai/runtime", runtime)
                templates = root / namespace / "templates"
                templates.mkdir()
                shutil.copyfile(TEMPLATE, templates / "issue.md")
                sibling = root / ".ai/templates"
                sibling.mkdir(parents=True, exist_ok=True)
                (sibling / "issue.md").write_text("malformed sibling", encoding="utf-8")
                draft = root / "body.md"
                draft.write_text(bodies()["Bug"], encoding="utf-8")
                command = [sys.executable, str(runtime / "phase.py"), "query", "issue.validate",
                           "--variant", "Bug", "--body-file", str(draft)]
                result = subprocess.run(command, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                (templates / "issue.md").unlink()
                result = subprocess.run(command, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('"issue-schema"', result.stdout)


if __name__ == "__main__":
    unittest.main()
