from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class UatChecks(RuntimeCase):
    def test_pending_failures_and_checkpoint(self):
        directory = self.phase()
        path = Path(directory)/"01-UAT.md"
        path.write_text('---\nstatus: testing\n---\n### 1. Login\nexpected: Signed in\nresult: pending\n', encoding="utf-8")
        self.assertFalse(self.cli("phase.uat-passed", "1", "--uat-only", status=1)["passed"])
        self.assertEqual("1", self.cli("uat.render-checkpoint", path)["test"]["id"])
        self.assertEqual(1, self.cli("audit-uat")["count"])
        self.assertEqual(1, self.cli("audit-open")["counts"]["uat"])
        self.cli("uat.complete-session", path, status=1, raw=True)
        path.write_text(path.read_text().replace("pending", "passed"), encoding="utf-8")
        self.assertTrue(self.cli("phase.uat-passed", "1", "--uat-only")["passed"])
        self.assertTrue(self.cli("uat.complete-session", path, "--message", "docs: finish UAT")["completed"])

    def test_coverage_classification(self):
        path = self.put("SUMMARY.md", '---\nmust_haves:\n  truths: ["API responds", "Visual appearance", "Documentation rationale"]\n---\n')
        result = self.cli("uat.classify-coverage", path)
        self.assertEqual(1, len(result["automated"]))
        self.assertEqual(1, len(result["human"]))
        self.assertEqual(1, len(result["not-testable"]))
