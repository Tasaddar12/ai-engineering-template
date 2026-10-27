import json
from pathlib import Path
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class VerifyChecks(RuntimeCase):
    def test_artifacts_links_and_commits(self):
        directory = self.phase()
        path = self.plan(directory)
        self.cli("frontmatter.set", path, "--field", "must_haves.artifacts", "--value", '[{"path":"src/app.py","min_lines":2,"contains":"return 2"}]')
        self.assertFalse(self.cli("verify.artifacts", path, status=1)["valid"])
        self.put("src/app.py", "def app():\n    return 2\n")
        self.assertTrue(self.cli("verify.artifacts", path)["valid"])
        self.cli("frontmatter.set", path, "--field", "must_haves.key_links", "--value", '[{"from":"src/app.py","to":"value","pattern":"return 2"}]')
        self.assertTrue(self.cli("verify.key-links", path)["valid"])
        self.assertTrue(self.cli("verify.commits", self.git("rev-parse", "HEAD"))["valid"])
        self.assertFalse(self.cli("verify.commits", "deadbeef", status=1)["valid"])

    def test_report_is_excluded_from_fingerprint_and_audit_dedupes(self):
        directory = self.phase()
        self.plan(directory)
        report = self.put(str(Path(directory).relative_to(self.root)/"01-VERIFICATION.md"), '---\nphase: "01"\nstatus: passed\n---\nEvidence\n')
        first = self.cli("verification.fingerprint", "1")["fingerprint"]
        self.cli("frontmatter.set", report, "--field", "note", "--value", "changed")
        self.assertEqual(first, self.cli("verification.fingerprint", "1")["fingerprint"])
        self.assertEqual("ship", self.cli("verification.status", directory)["route"])
        audit = Path(directory)/"01-SECURITY.md"
        self.assertTrue(self.cli("verification.append-audit", audit, "--heading", "Audit", "--body", "passed")["appended"])
        self.assertFalse(self.cli("verification.append-audit", audit, "--heading", "Audit", "--body", "passed")["appended"])
