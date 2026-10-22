"""Mechanical evidence packets through the real CLI, without model dispatch."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


RUNTIME = Path(__file__).resolve().parents[1] / ".ai/runtime/phase.py"


class EvidenceExtractionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Evidence Test")
        self.git("config", "user.email", "evidence@example.invalid")
        self.write("old name.txt", "original")
        self.write("gone.txt", "removed later")
        self.git("add", "--", ".")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD").strip()
        (self.root / "old name.txt").rename(self.root / "new café.txt")
        (self.root / "gone.txt").unlink()
        self.git("add", "-A")
        self.git("commit", "-qm", "rename and remove")
        self.first = self.git("rev-parse", "HEAD").strip()
        self.write("added.txt", "committed")
        self.git("add", "--", "added.txt")
        self.git("commit", "-qm", "add")
        self.head = self.git("rev-parse", "HEAD").strip()

    def write(self, name, value):
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                              check=True, encoding="utf-8").stdout

    def query(self, *args, succeeds=True):
        process = subprocess.run([sys.executable, str(RUNTIME), "query", *args],
                                 cwd=self.root, capture_output=True, encoding="utf-8",
                                 env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(process.returncode, 0 if succeeds else 1, process.stderr + process.stdout)
        return json.loads(process.stdout)

    def extract(self, *args, **kwargs):
        return self.query("evidence.extract", "--base", self.base, *args, **kwargs)

    def test_committed_range_resolves_ids_and_preserves_paths_without_dirty_state(self):
        self.write("added.txt", "dirty")
        self.write("untracked.txt", "not in diff")
        status = self.git("status", "--porcelain")
        result = self.extract()
        self.assertEqual(result["base_revision"], self.base)
        self.assertEqual(result["head_revision"], self.head)
        self.assertEqual(result["commit_ids"], [self.first, self.head])
        self.assertEqual(result["changed_paths"],
                         ["added.txt", "gone.txt", "new café.txt", "old name.txt"])
        self.assertIsNone(result["check_evidence"])
        self.assertEqual(self.git("status", "--porcelain"), status)
        self.assertFalse((self.root / ".planning").exists())
        earlier = self.extract("--head", self.first)
        self.assertEqual(earlier["commit_ids"], [self.first])
        self.assertNotIn("added.txt", earlier["changed_paths"])

    def test_identical_endpoints_are_empty(self):
        result = self.extract("--head", self.base)
        self.assertEqual(result["commit_ids"], [])
        self.assertEqual(result["changed_paths"], [])

    def test_recorded_counts_preserve_partial_failures_unknowns_and_revisions(self):
        evidence = {"configured": True, "passed": False, "partial": True,
                    "selected_indices": [1, 3, 4], "tested_revision": self.head,
                    "checks": [
                        {"full_index": 1, "passed": True, "exit_code": 0,
                         "receipt": "private/receipt.json", "reused": True,
                         "tested_revision": self.base, "stdout_tail": "x" * 2500},
                        {"full_index": 3, "passed": False, "exit_code": 7,
                         "error": "failed", "stderr_log": "private/failure.log"},
                        {"full_index": 4, "passed": "true", "exit_code": 0}]}
        self.write("evidence.json", json.dumps(evidence))
        original = (self.root / "evidence.json").read_bytes()
        result = self.extract("--evidence-file", "evidence.json")["check_evidence"]
        self.assertEqual(result["validation"], "recorded-only")
        self.assertEqual(result["counts"], {"total": 3, "passed": 1, "failed": 1,
                                            "unknown": 1, "reused": 1, "receipts": 1})
        self.assertTrue(result["batch"]["partial"])
        self.assertFalse(result["batch"]["passed"])
        self.assertEqual(result["checks"][0]["tested_revision"], self.base)
        self.assertEqual(len(result["checks"][0]["stdout_tail"]), 2000)
        self.assertEqual(result["checks"][1]["exit_code"], 7)
        self.assertEqual(result["checks"][2]["result_index"], 2)
        self.assertEqual((self.root / "evidence.json").read_bytes(), original)

    def test_consumes_existing_runtime_result_without_rerunning_check(self):
        self.write(".gitignore", ".generated/\n.planning/verification-receipts/\n")
        (self.root / ".generated").mkdir()
        command = [sys.executable, "-c", "from pathlib import Path; Path('.generated/ran').write_text('once'); print('check-output')"]
        self.write(".planning/config.yaml", "verification:\n  commands:\n    - " + json.dumps(command) + "\n")
        run = self.query("verification.run-checks")
        self.assertTrue(run["passed"], run)
        self.write("checks.json", json.dumps(run))
        (self.root / ".generated/ran").unlink()
        result = self.extract("--evidence-file", "checks.json")["check_evidence"]
        self.assertEqual(result["counts"]["passed"], 1)
        self.assertEqual(result["checks"][0]["receipt"], run["checks"][0]["receipt"])
        self.assertIn("check-output", result["checks"][0]["stdout_tail"])
        self.assertFalse((self.root / ".generated/ran").exists())

    def test_invalid_evidence_fails_without_silent_pass(self):
        for contents in ('{"checks": [], "checks": []}', '{"checks": [true]}',
                         '{"passed": true}', 'not json'):
            with self.subTest(contents=contents):
                self.write("bad.json", contents)
                result = self.extract("--evidence-file", "bad.json", succeeds=False)
                self.assertEqual(result["code"], "bad-evidence")
        result = self.extract("--evidence-file", "missing.json", succeeds=False)
        self.assertEqual(result["code"], "bad-evidence")

    def test_bad_references_and_missing_option_fail(self):
        for args in (("--base",), ("--base", "--help"), ("--base", "missing-ref")):
            result = self.query("evidence.extract", *args, succeeds=False)
            self.assertFalse(result["ok"])

    def test_explicit_empty_or_blank_evidence_fails_while_omission_is_allowed(self):
        for filename in ("", " ", "\t\n"):
            with self.subTest(filename=repr(filename)):
                result = self.extract("--evidence-file", filename, succeeds=False)
                self.assertEqual(result["code"], "missing-argument")
                self.assertNotIn("check_evidence", result)
        omitted = self.extract()
        self.assertTrue(omitted["ok"])
        self.assertIsNone(omitted["check_evidence"])

    def test_core_rejects_blank_evidence_before_git_access(self):
        script = '''import sys
sys.path.insert(0, sys.argv[1])
from lib.evidence import extract
from lib.results import VerbError
for filename in ("", " ", "\\t\\n"):
    try:
        extract(None, "unused", evidence_file=filename)
    except VerbError as error:
        assert error.code == "missing-argument", error
    else:
        raise AssertionError("blank evidence was accepted")
'''
        process = subprocess.run([sys.executable, "-c", script, str(RUNTIME.parent)],
                                 cwd=self.root, capture_output=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stderr + process.stdout)


if __name__ == "__main__":
    unittest.main()
