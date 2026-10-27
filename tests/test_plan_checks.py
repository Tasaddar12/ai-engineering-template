from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class PlanChecks(RuntimeCase):
    def test_structured_plan_and_multiline_frontmatter(self):
        path = self.plan(self.phase(), extra="purpose: |\n  First line\n  Second line\n")
        self.assertTrue(self.cli("verify.plan-structure", path)["valid"])
        self.assertEqual("Add behavior", self.cli("plan.task-structure", path)["tasks"][0]["name"])
        self.assertIn("Second line", self.cli("frontmatter.get", path, "--field", "purpose"))
        self.cli("frontmatter.set", path, "--field", "wave", "--value", "2")
        self.assertEqual(2, self.cli("frontmatter.get", path, "--field", "wave"))

    def test_invalid_task_and_schema_report_errors(self):
        path = self.plan(self.phase(), "<task><name>Incomplete</name></task>")
        self.assertFalse(self.cli("verify.plan-structure", path, status=1)["valid"])
        self.cli("frontmatter.set", path, "--field", "wave", "--value", "wrong", status=1, raw=True)
        path.write_text(path.read_text().replace("wave: 1", "wave: wrong"), encoding="utf-8")
        self.assertFalse(self.cli("frontmatter.validate", path, "--schema", "plan", status=1)["valid"])

    def test_frontmatter_write_cannot_escape_repository(self):
        outside = self.root.parent/"outside-engineer-test.md"
        self.cli("frontmatter.set", outside, "--field", "x", "--value", "true", status=1, raw=True)

    def test_verification_commands_must_have_a_failure_direction(self):
        directory = self.phase()
        self.plan(directory, '<task><name>bad</name><files>src/app.py</files><verify>echo okay || true</verify></task>')
        result = self.cli("check.verify-failure-directions", "1", status=1)
        self.assertEqual(1, len(result["findings"]))

    def test_verify_paths_allow_current_and_earlier_task_files(self):
        directory = self.phase()
        self.plan(directory, '<task><name>create</name><files>src/app.py</files><verify>python src/app.py</verify></task>')
        self.assertTrue(self.cli("check.verify-command-paths", "1")["valid"])
        self.plan(directory, '<task><name>missing</name><files>src/app.py</files><verify>python tests/missing.py</verify></task>')
        self.assertFalse(self.cli("check.verify-command-paths", "1", status=1)["valid"])
