"""Template-derived structural gate, including installed namespace resolution."""
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engineer/bin"))
from lib import issue_format, delivery
from lib.core import Failure

TEMPLATE = ROOT / ".github/ISSUE_TEMPLATE"


def bodies():
    return {variant: issue_format.form_body(issue_format.template_path(variant, TEMPLATE))[1]
            for variant in issue_format.VARIANTS}


class IssueFormat(unittest.TestCase):
    def assert_invalid(self, body, variant="UAT", code="issue-format"):
        with self.assertRaises(Failure) as caught:
            issue_format.validate(body, variant)
        self.assertEqual(caught.exception.code, code)

    def test_all_canonical_variants(self):
        self.assertEqual(list(issue_format.schema()),
                         ["Bug", "Enhancement", "Decision required", "Security risk", "UAT",
                          "Docs issue", "Chore", "Feature request"])
        for variant, body in bodies().items():
            with self.subTest(variant=variant):
                self.assertTrue(issue_format.validate(body, variant)["valid"])

    def test_security_risk_heading_required_and_ordered(self):
        body = bodies()["Security risk"]
        heading = "## Risk assessment and lifecycle"
        self.assertIn(heading[3:], issue_format.schema()["Security risk"]["headings"])
        self.assert_invalid(body.replace(heading, "", 1), "Security risk")
        section = re.search(r"## Risk assessment and lifecycle\n.*?(?=\n## )",
                            body, re.S).group()
        moved = body.replace(section, "").replace(
            "## Requested remediation", section + "\n## Requested remediation")
        self.assert_invalid(moved, "Security risk")

    def test_safe_filled_security_risks_at_different_states(self):
        body = bodies()["Security risk"]
        for severity, status, evidence in (
                ("low", "unresolved", "Pending owner inspection"),
                ("medium", "deferred", "Maintainer; scoped follow-up; next: inspect control"),
                ("high", "accepted", "Maintainer acceptance rationale: limited residual risk"),
                ("critical", "mitigated", "Revision fixture-sha; isolated secure check passed")):
            filled = re.sub(r"\[[^\n]*?\]", "Safe fixture assessment", body)
            filled = re.sub(r"^- Severity:.*$", "- Severity: " + severity +
                            "; impact/likelihood assessed; uncertainty recorded", filled, flags=re.M)
            filled = re.sub(r"^- Status:.*$", "- Status: " + status, filled, flags=re.M)
            filled = re.sub(r"^- Resolution evidence:.*$", "- Resolution evidence: " +
                            evidence, filled, flags=re.M)
            with self.subTest(severity=severity, status=status):
                result = issue_format.validate(filled, "Security risk")
                self.assertTrue(result["valid"])
                self.assertTrue(result["structuralOnly"])

    def test_installed_security_schema_owns_its_heading(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / ".codex/engineer/bin"
            shutil.copytree(ROOT / "engineer/bin", runtime)
            templates = root / ".codex/.github/ISSUE_TEMPLATE"
            shutil.copytree(TEMPLATE, templates)
            form = templates / "security-risk.yml"
            source = form.read_text(encoding="utf-8")
            installed = source.replace("## Risk assessment and lifecycle", "## Installed risk assessment")
            form.write_text(installed, encoding="utf-8")
            sibling = root / ".ai/templates"
            sibling.mkdir(parents=True)
            (sibling / "issue.md").write_text(source, encoding="utf-8")
            draft = root / "body.md"
            command = [sys.executable, str(runtime / "engineer.py"), "query", "issue.validate",
                       "--variant", "Security risk", "--body-file", str(draft)]
            for body, code in ((bodies()["Security risk"], 1),
                               (bodies()["Security risk"].replace("## Risk assessment and lifecycle",
                                                                "## Installed risk assessment"), 0)):
                draft.write_text(re.sub(r"\[[^\]\n]+\]", "Observed fixture fact", body), encoding="utf-8")
                result = subprocess.run(command, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def test_security_assessment_values_remain_structural_only(self):
        body = bodies()["Security risk"]
        # Correct shape with absent/incorrect risk facts still passes today.
        # This is negative evidence: semantic review is required after validation.
        missing = re.sub(r"^- (Threat ID / risk key|Source aliases|Severity|Owner|Status|"
                         r"Mitigation or safe next action|Resolution evidence):.*\n",
                         "", body, flags=re.M)
        wrong = re.sub(r"^- Severity:.*$", "- Severity: banana", body, flags=re.M)
        wrong = re.sub(r"^- Status:.*$", "- Status: merged-means-secure", wrong, flags=re.M)
        wrong = re.sub(r"^- Resolution evidence:.*$", "- Resolution evidence: unknown",
                       wrong, flags=re.M)
        for changed in (missing, wrong):
            with self.subTest(body=changed):
                result = issue_format.validate(changed, "Security risk")
                self.assertTrue(result["valid"])
                self.assertTrue(result["structuralOnly"])

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
            directory = Path(directory) / "ISSUE_TEMPLATE"
            shutil.copytree(TEMPLATE, directory)
            path = directory / "uat.yml"
            source = path.read_text(encoding="utf-8")
            malformed = ("", "## Problem\n", source.replace("| Step |", "| Step | Added |"),
                         source.replace("| Step |", "|  |"), source.replace('name: "UAT"', 'name: "Removed"'),
                         source.replace("value: |", "value: >"))
            for text in malformed:
                path.write_text(text, encoding="utf-8")
                with self.assertRaises(Failure) as caught:
                    issue_format.validate(bodies()["Bug"], "Bug", directory)
                self.assertEqual(caught.exception.code, "issue-schema")
            path.unlink()
            with self.assertRaises(Failure) as caught:
                issue_format.validate(bodies()["Bug"], "Bug", directory)
            self.assertEqual(caught.exception.code, "issue-schema")
            path.write_text(source, encoding="utf-8")
            bug = directory / "bug.yml"
            bug.write_text(bug.read_text(encoding="utf-8").replace(
                "## Expected behavior", "## Expected result"), encoding="utf-8")
            self.assertTrue(issue_format.validate(bodies()["Bug"].replace(
                "## Expected behavior", "## Expected result"), "Bug", directory)["valid"])

    def test_installed_namespace_owns_schema_even_with_sibling_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for namespace in (".codex", ".claude"):
                runtime = root / namespace / "engineer/bin"
                shutil.copytree(ROOT / "engineer/bin", runtime)
                templates = root / namespace / ".github/ISSUE_TEMPLATE"
                shutil.copytree(TEMPLATE, templates)
                sibling = root / ".ai/templates"
                sibling.mkdir(parents=True, exist_ok=True)
                (sibling / "issue.md").write_text("malformed sibling", encoding="utf-8")
                draft = root / "body.md"
                draft.write_text(re.sub(r"\[[^\]\n]+\]", "Observed fixture fact", bodies()["Bug"]), encoding="utf-8")
                command = [sys.executable, str(runtime / "engineer.py"), "query", "issue.validate",
                           "--variant", "Bug", "--body-file", str(draft)]
                result = subprocess.run(command, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                (templates / "bug.yml").unlink()
                result = subprocess.run(command, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('"issue-schema"', result.stderr)


class PullRequestFormat(unittest.TestCase):
    def test_malformed_template_cannot_disable_required_sections(self):
        for template in ('<!-- instructions only -->', '# Incomplete template',
                         '## Requirements or Issues\nOptional\n\n## Stack\nOptional'):
            with self.subTest(template=template), patch.object(delivery, 'read', return_value=template):
                with self.assertRaises(Failure) as caught:
                    delivery.validate_body('Unstructured public body')
                self.assertEqual('invalid-pr-body', caught.exception.code)

    def test_template_instructions_do_not_become_public_sections(self):
        template = '<!--\n## Instructions\nOnly authoring guidance\n-->\n\n## Goal\nOutcome\n'
        with patch.object(delivery, 'read', return_value=template):
            delivery.validate_body('## Goal\nObserved outcome\n')
            with self.assertRaises(Failure):
                delivery.validate_body('## Instructions\nMissing goal\n')


if __name__ == "__main__":
    unittest.main()
