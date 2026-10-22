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

TEMPLATE = ROOT / ".ai/templates/issues"


def bodies(directory=TEMPLATE):
    return {name: re.search(r"^## File Template\n\n```markdown\n(.*?)\n```",
                           (directory / filename).read_text(encoding="utf-8"), re.M | re.S)[1]
            for name, filename in issue_format.TEMPLATES.items()}


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
            runtime = root / ".codex/runtime"
            shutil.copytree(ROOT / ".ai/runtime", runtime)
            templates = root / ".codex/templates/issues"
            shutil.copytree(TEMPLATE, templates)
            source = (templates / "security-risk.md").read_text(encoding="utf-8")
            installed = source.replace("## Risk assessment and lifecycle", "## Installed risk assessment")
            (templates / "security-risk.md").write_text(installed, encoding="utf-8")
            shutil.copytree(TEMPLATE, root / ".ai/templates/issues")
            draft = root / "body.md"
            command = [sys.executable, str(runtime / "phase.py"), "query", "issue.validate",
                       "--variant", "Security risk", "--body-file", str(draft)]
            for body, code in ((bodies()["Security risk"], 1),
                               (bodies()["Security risk"].replace("## Risk assessment and lifecycle",
                                                                "## Installed risk assessment"), 0)):
                draft.write_text(body, encoding="utf-8")
                result = subprocess.run(command, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)

    def test_security_assessment_fields_are_required(self):
        body = bodies()["Security risk"]
        missing = re.sub(r"^- (Threat ID / risk key|Source aliases|Severity|Owner|Status|"
                         r"Mitigation or safe next action|Resolution evidence):.*\n",
                         "", body, flags=re.M)
        self.assert_invalid(missing, "Security risk")
        self.assert_invalid(body.replace("- Owner:", "- Unrequested field:"), "Security risk")

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
        self.assert_invalid(body + "\n```\n## Problem\n```", "Bug")

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

    def test_untemplated_literal_content_is_rejected_and_runtime_marker_preserved(self):
        for variant, body in bodies().items():
            extra = "\n<pre class=\"literal\">\n## Problem\n| Fake | Table |\n</PRE>\n"
            extra += "\n```html\n<pre>\n## Problem\n</pre>\n```\n"
            extra += "\n    ## Problem\n \t## Problem\n"
            extra += "\n- Example with `<pre>` and inline code.\n| Example | `<pre>` |\n"
            extra += "\n<preview>\nExample unrelated tag.\n</preview>\n"
            with self.subTest(variant=variant):
                self.assert_invalid(body + extra, variant)
                self.assert_invalid("<preview>\nExample unrelated tag.\n</preview>\n\n" + body, variant)
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
            path = Path(directory) / "issues"
            shutil.copytree(TEMPLATE, path)
            target = path / "uat.md"
            source = target.read_text(encoding="utf-8")
            malformed = ("", "## Problem\n", source.replace("| Step |", "| Step | Added |"),
                         source.replace("| Step |", "|  |"),
                         source.replace("```markdown", "```text", 1),
                         source + source)
            for text in malformed:
                target.write_text(text, encoding="utf-8")
                with self.assertRaises(VerbError) as caught:
                    issue_format.validate(bodies()["Bug"], "Bug", path)
                self.assertEqual(caught.exception.code, "issue-schema")
            target.unlink()
            with self.assertRaises(VerbError) as caught:
                issue_format.validate(bodies()["Bug"], "Bug", path)
            self.assertEqual(caught.exception.code, "issue-schema")
            target.write_text(source, encoding="utf-8")
            bug = path / "bug.md"
            bug.write_text(bug.read_text(encoding="utf-8").replace(
                "## Expected behavior", "## Expected result"), encoding="utf-8")
            self.assertTrue(issue_format.validate(bodies()["Bug"].replace(
                "## Expected behavior", "## Expected result"), "Bug", path)["valid"])

    def test_each_required_split_template_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "issues"
            shutil.copytree(TEMPLATE, path)
            for filename in issue_format.TEMPLATES.values():
                target = path / filename
                source = target.read_text(encoding="utf-8")
                for replacement in (None, "malformed schema"):
                    with self.subTest(filename=filename, replacement=replacement):
                        if replacement is None:
                            target.unlink()
                        else:
                            target.write_text(replacement, encoding="utf-8")
                        with self.assertRaises(VerbError) as caught:
                            issue_format.validate(bodies()["Bug"], "Bug", path)
                        self.assertEqual(caught.exception.code, "issue-schema")
                target.write_text(source, encoding="utf-8")

    def test_consolidated_file_keeps_security_risk_variant(self):
        text = (TEMPLATE / "security-risk-consolidated.md").read_text(encoding="utf-8")
        body = re.search(r"^## File Template\n\n```markdown\n(.*?)\n```", text, re.M | re.S)[1]
        self.assertTrue(issue_format.validate(body, "Security risk")["valid"])
        self.assertEqual(list(issue_format.schema()), list(bodies()))

    def test_consolidated_filled_rows_columns_identity_and_checkboxes(self):
        text = (TEMPLATE / "security-risk-consolidated.md").read_text(encoding="utf-8")
        body = re.search(r"^## File Template\n\n```markdown\n(.*?)\n```", text, re.M | re.S)[1]
        body = body.replace("[Risk ID]", "R-001")
        body = re.sub(r"\[(?![ xX]\])[^\]\n]+\]", "Safe fixture detail", body)
        row = next(line for line in body.splitlines() if line.startswith("| R-001 |"))
        body = body.replace(row, row + "\n" + row.replace("R-001", "R-002"))
        body = body.replace("- [ ] Remediation verified", "- [ ] Remediation verified\n\n### R-002\n\n- [x] Remediation verified")
        self.assertTrue(issue_format.validate(body, "Security risk")["valid"])
        changes = (
            body.replace("| Owner | Status |", "| Status | Owner |"),
            body.replace("| Owner |", "|", 1),
            body.replace("|---|---|---|---|---|---|---|", "|---|---|---|---|---|---|"),
            body.replace("| R-002 |", "| R-001 |"),
            body.replace("### R-002", "### R-003"),
            body.replace("### R-002", "### R-001"),
            body.replace("- [x] Remediation verified", "Remediation verified"),
            body.replace("- [x] Remediation verified", "- [x] Other task"),
            body.replace("- [x] Remediation verified", "    - [x] Remediation verified"),
            re.sub(r"^(\|.*)$", r"    \1", body, flags=re.M),
            body.replace("- [x] Remediation verified", "- [x] Remediation verified\n- [ ] Remediation verified"),
            body.replace("### R-002\n\n- [x] Remediation verified", ""),
            body + "\n### R-003\n\n- [ ] Remediation verified",
        )
        for changed in changes:
            with self.subTest(changed=changed):
                self.assert_invalid(changed, "Security risk")

        for namespace in (".codex", ".claude"):
            with self.subTest(namespace=namespace), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                runtime = root / namespace / "runtime"
                shutil.copytree(ROOT / ".ai/runtime", runtime)
                templates = runtime.parent / "templates/issues"
                shutil.copytree(TEMPLATE, templates)
                shutil.copytree(TEMPLATE, root / ".ai/templates/issues")
                target = templates / "security-risk-consolidated.md"
                target.write_text(target.read_text(encoding="utf-8").replace(
                    "| Owner |", "| Installed owner |"), encoding="utf-8")
                draft = root / "body.md"
                for content, expected in ((body, 1), (body.replace("| Owner |", "| Installed owner |"), 0)):
                    draft.write_text(content, encoding="utf-8")
                    result = subprocess.run([sys.executable, "-B", str(runtime / "phase.py"),
                                             "query", "issue.validate", "--variant", "Security risk",
                                             "--body-file", str(draft)], cwd=root, capture_output=True, text=True)
                    self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                target.unlink()
                result = subprocess.run([sys.executable, "-B", str(runtime / "phase.py"),
                                         "query", "issue.validate", "--variant", "Security risk",
                                         "--body-file", str(draft)], cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('"issue-schema"', result.stdout)

    def test_consolidated_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "issues"
            shutil.copytree(TEMPLATE, path)
            target = path / "security-risk-consolidated.md"
            source = target.read_text(encoding="utf-8")
            for malformed in (source.replace("| Owner |", "|"),
                              source.replace("| Owner |", "| Status |"),
                              source.replace("### [Risk ID]", "### Other ID", 1),
                              source.replace("- [ ] Remediation verified", "Remediation verified", 1),
                              source + source):
                target.write_text(malformed, encoding="utf-8")
                with self.assertRaises(VerbError) as caught:
                    issue_format.validate(bodies()["Bug"], "Bug", path)
                self.assertEqual(caught.exception.code, "issue-schema")

    def test_examples_outside_file_template_do_not_change_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "issues"
            shutil.copytree(TEMPLATE, path)
            target = path / "bug.md"
            target.write_text(target.read_text(encoding="utf-8") +
                              "\n## Good example\n\n```markdown\n## Different heading\n```\n",
                              encoding="utf-8")
            self.assertEqual(issue_format.schema(), issue_format.schema(path))

    def test_installed_namespace_owns_schema_even_with_sibling_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for namespace in (".codex", ".claude"):
                runtime = root / namespace / "runtime"
                shutil.copytree(ROOT / ".ai/runtime", runtime)
                templates = root / namespace / "templates/issues"
                shutil.copytree(TEMPLATE, templates)
                sibling = root / ".ai/templates/issues"
                shutil.copytree(TEMPLATE, sibling, dirs_exist_ok=True)
                # Neither a complete sibling namespace nor an obsolete bundle
                # supplies a missing file for this running namespace.
                (templates.parent / "issue.md").write_text("obsolete bundle", encoding="utf-8")
                draft = root / "body.md"
                draft.write_text(bodies()["Bug"], encoding="utf-8")
                command = [sys.executable, str(runtime / "phase.py"), "query", "issue.validate",
                           "--variant", "Bug", "--body-file", str(draft)]
                result = subprocess.run(command, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                (templates / "bug.md").unlink()
                result = subprocess.run(command, cwd=root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 1)
                self.assertIn('"issue-schema"', result.stdout)


if __name__ == "__main__":
    unittest.main()
