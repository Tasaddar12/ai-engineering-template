"""Regression checks for firm publication fields, without provider mutations."""
import json
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
from publication_fixtures import issue_body, pr_body

# Observed in graphalyx PR452; its generation/publication route is unknown.
MALFORMED = "Focused author checks passed offline53 and host146."


class PublicationFormat(unittest.TestCase):
    def invalid_pr(self, content):
        with self.assertRaises(VerbError) as caught:
            issue_format.validate_pr(content)
        self.assertEqual(caught.exception.code, "pr-format")

    def invalid_issue(self, content, variant="Bug"):
        with self.assertRaises(VerbError) as caught:
            issue_format.validate(content, variant)
        self.assertEqual(caught.exception.code, "issue-format")

    def test_valid_pr_optional_sections_and_legitimate_text(self):
        for body in (pr_body(), pr_body("https://github.com/acme/project/issues/1"), pr_body(stack=True)):
            self.assertTrue(issue_format.validate_pr(body)["valid"])
        body = pr_body().replace("Safe fixture detail", "Users can search: commas, numbers 53 and 146, and ordinary text.")
        self.assertTrue(issue_format.validate_pr(body)["valid"])

    def test_pr_rejects_actual_malformed_verification_paragraph(self):
        self.invalid_pr(pr_body().replace("## Verification\n", "## Verification\n\n" + MALFORMED + "\n"))
        self.invalid_pr(pr_body() + "\n" + MALFORMED)
        self.invalid_pr(MALFORMED + "\n\n" + pr_body())

    def test_pr_rejects_extra_sections_headings_and_empty_fields(self):
        for body in ("", None, pr_body() + "\n## Review follow-up\nExtra data.",
                     pr_body() + "\n<!-- todo-id: Unrequested instruction -->\n",
                     pr_body().replace("## Known gaps", "### Record health\nExtra data.\n\n## Known gaps"),
                     re.sub(r"(## Goal\n).*?(?=\n## Changes)", r"\1", pr_body(), flags=re.S),
                     pr_body().replace("| Candidate | " + "a" * 40, "| Candidate | short"),
                     pr_body().replace("| Safe fixture detail |", "|  |", 1)):
            with self.subTest(body=str(body)[:60]):
                self.invalid_pr(body)

    def test_issue_rejects_intro_extra_paragraph_and_empty_section(self):
        for variant in ("Bug", "Enhancement", "Decision required", "Security risk", "UAT"):
            body = issue_body(variant)
            self.assertTrue(issue_format.validate(body, variant)["valid"])
            for changed in (MALFORMED + "\n\n" + body, body + "\n\n" + MALFORMED,
                            body + "\n\n### Unrequested narrative\n" + MALFORMED,
                            re.sub(r"(^## [^\n]+\n).*?(?=\n## )", r"\1", body, count=1, flags=re.M | re.S)):
                with self.subTest(variant=variant, changed=changed[:55]):
                    self.invalid_issue(changed, variant)

    def test_documented_security_entries_remain_scoped_and_nonempty(self):
        body = issue_body("Security risk")
        self.assertTrue(issue_format.validate(body, "Security risk")["valid"])
        self.invalid_issue(body.replace("## Risk assessment and lifecycle\n",
                                       "## Risk assessment and lifecycle\n\n### R-001\n"), "Security risk")
        self.invalid_issue(body.replace("## Impact\n", "## Impact\n\n### R-002\n"), "Security risk")
        self.invalid_issue(body.replace("## Safe evidence", "### R-002\n\n## Safe evidence"), "Security risk")
        missing = re.sub(r"^- Owner:.*\n", "", body, flags=re.M)
        self.invalid_issue(missing, "Security risk")
        unknown = re.sub(r"(## Risk assessment and lifecycle\n).*?(?=\n## Safe evidence)",
                         r"\1\n- Unrequested field: arbitrary text\n", body, flags=re.S)
        self.invalid_issue(unknown, "Security risk")
        linked = body.replace("- Severity: Safe fixture detail", "- Severity: [PLAN assessment](https://example.test/plan#assessment)")
        linked = linked.replace("- Mitigation or safe next action: Safe fixture detail",
                                "- Mitigation or safe next action: [PLAN mitigation](https://example.test/plan#mitigation)")
        self.assertTrue(issue_format.validate(linked, "Security risk")["valid"])

    def test_hidden_instruction_blocks_cannot_supply_fields(self):
        for hidden in ("<!-- Unrequested instruction -->", "<div>Hidden data</div>"):
            self.invalid_pr(re.sub(r"(## Goal\n).*?(?=\n## Changes)",
                                   r"\1\n" + hidden + "\n", pr_body(), flags=re.S))
            self.invalid_issue(issue_body().replace("Blank search fails for signed-in users.", hidden))
        self.invalid_issue(None)

    def test_markdown_autolinks_remain_valid_field_content(self):
        body = re.sub(r"(## Safe evidence\n).*?(?=\n## Impact)",
                      r"\1<https://example.test/evidence>\n", issue_body(), flags=re.S)
        self.assertTrue(issue_format.validate(body, "Bug")["valid"])
        for reference in ("<https://example.test/issues/1>", "<reviewer@example.test>"):
            self.assertTrue(issue_format.validate_pr(pr_body(reference))["valid"])

    def test_soft_wrapped_human_acceptance_values_remain_valid(self):
        body = issue_body("UAT").replace("Decision: Safe fixture detail",
                                        "Decision: Pending until the reviewer completes the prepared checkout\n"
                                        "flow and records the actual decision.")
        body = body.replace("Evidence: Safe fixture detail",
                            "Evidence: Pending until the reviewer records\n"
                            "the actual matching decision reference.")
        self.assertTrue(issue_format.validate(body, "UAT")["valid"])
        body = body.replace("Evidence: Pending until the reviewer records\nthe actual matching decision reference.",
                            "Evidence: Matching reviewer decision is recorded at\nhttps://example.test/decision")
        self.assertTrue(issue_format.validate(body, "UAT")["valid"])
        self.invalid_issue(body.replace("Evidence:", "Bogus:"), "UAT")
        self.invalid_issue(body + "\nBogus: value", "UAT")

    def test_setext_headings_cannot_replace_paragraph_fields(self):
        for delimiter in ("=====", "-----"):
            body = issue_body().replace("Blank search fails for signed-in users.", "Unrequested title\n" + delimiter)
            self.invalid_issue(body)
            self.invalid_pr(pr_body().replace("## Goal\n\nSafe fixture detail", "## Goal\n\nUnrequested title\n" + delimiter))

    def test_malformed_pr_source_fails_with_schema_diagnostic(self):
        source = (ROOT / ".ai/templates/pull-request.md").read_text(encoding="utf-8")
        one_column = re.sub(r"\| Revision status \| SHA \|\n\|---\|---\|\n\| Candidate \|[^\n]*\n\| Tested \|[^\n]*",
                            "| Revision status |\n|---|\n| Candidate |\n| Tested |", source)
        self.assertNotEqual(one_column, source)
        malformed = (source.replace("## Verification", "## Missing verification"),
                     source.replace("[Use None identified", "[Other instruction"),
                     source + "\n" + source,
                     source.replace("## Risks or rollback", "## Missing risks"), one_column)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pull-request.md"
            for content in malformed:
                path.write_text(content, encoding="utf-8")
                with self.assertRaises(VerbError) as caught:
                    issue_format.validate_pr(pr_body(), path)
                self.assertEqual(caught.exception.code, "pr-schema")

    def test_installed_pr_validate_uses_own_template_and_never_publishes(self):
        source = (ROOT / ".ai/templates/pull-request.md").read_text(encoding="utf-8")
        for host in ("codex", "claude"):
            with self.subTest(host=host), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                runtime = root / ("." + host) / "runtime"
                shutil.copytree(ROOT / ".ai/runtime", runtime)
                templates = runtime.parent / "templates"
                templates.mkdir()
                (templates / "pull-request.md").write_text(source.replace("## Goal", "## Installed goal"), encoding="utf-8")
                sibling = root / ".ai/templates"
                sibling.mkdir(parents=True)
                (sibling / "pull-request.md").write_text(source, encoding="utf-8")
                draft = root / "body.md"
                for body, code in ((pr_body(), 1),
                                   (pr_body().replace("## Goal", "## Installed goal"), 0)):
                    draft.write_text(body, encoding="utf-8")
                    before = {str(path.relative_to(root)): path.read_bytes()
                              for path in root.rglob("*") if path.is_file()}
                    result = subprocess.run([sys.executable, "-B", str(runtime / "phase.py"),
                                             "query", "pr.validate", "--body-file", str(draft)],
                                            cwd=root, capture_output=True, text=True)
                    self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                    self.assertEqual(json.loads(result.stdout)["ok"], code == 0)
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(before, {str(path.relative_to(root)): path.read_bytes()
                                              for path in root.rglob("*") if path.is_file()})

    def test_issue_preserves_wrapped_prose_actions_pending_uat_and_retry_marker(self):
        body = re.sub(r"(## Problem\n).*?(?=\n\n## )", r"\1A normal wrapped sentence\ncontinues on the next source line.", issue_body(), count=1, flags=re.S)
        self.assertTrue(issue_format.validate(body + "\n<!-- todo-id: fixture -->\n", "Bug")["valid"])
        self.assertTrue(issue_format.validate(issue_body("UAT"), "UAT")["valid"])


if __name__ == "__main__":
    unittest.main()
