from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class UatChecks(RuntimeCase):
    def test_pending_failures_and_checkpoint(self):
        directory = self.phase()
        path = Path(directory)/"01-UAT.md"
        summary = Path(directory)/"01-01-SUMMARY.md"
        summary.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\nrequirements-completed: []\nacceptance: []\ndocumentation: []\nissue_refs: []\n---\nDelivered login fixture.\n', encoding="utf-8")
        self.git("add", str(summary))
        self.git("commit", "-m", "fixture: delivered login summary")
        path.write_text('---\nphase: "01"\nstatus: testing\nsource: [01-01-SUMMARY.md]\n---\n## Tests\n\n### 1. Login\nexpected: Signed in\nresult: pending\n\n## Human acceptance\nstatus: accepted\naccepted_by: Fixture reviewer\naccepted_at: 2026-10-27\ndecision: Fixture acceptance recorded for offline tests\n', encoding="utf-8")
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

    def test_audits_preserve_distinct_same_day_quick_owners(self):
        owners = ["261027-001-first", "261027-002-second"]
        for owner in owners:
            self.put(".planning/quick/"+owner+"/QUICK.md", "---\nstatus: open\n---\n")
            self.put(".planning/quick/"+owner+"/"+owner+"-VERIFICATION.md",
                     "---\nstatus: human_needed\nhuman_verification: [Inspect actual result]\n---\nAwaiting observation.\n")
        self.assertEqual(owners, sorted(item["quick"] for item in self.cli("audit-uat")["items"]))
        audit = self.cli("audit-open")
        self.assertEqual(owners, sorted(item["quick"] for item in audit["uat"]))
        self.assertEqual(owners, sorted(item["quick"] for item in audit["verification"]))
