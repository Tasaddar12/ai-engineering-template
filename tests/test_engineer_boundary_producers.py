"""Offline checks for summary state and verification fingerprint producers."""
import importlib.util
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import unittest

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE, RUNTIME
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE, RUNTIME


VERIFIER = "agents/verifier.md"


def source(path):
    return (SOURCE / path).read_text(encoding="utf-8")


class SummaryStateProducer(RuntimeCase):
    def test_documented_summary_statuses_are_supported(self):
        guidance = source("engineer/templates/summary.md").split("**Status:**", 1)[1].split("</frontmatter_guidance>", 1)[0]
        statuses = re.findall(r"`(?:status: )?(\w+)`", guidance.split("Dependencies", 1)[0])
        self.assertTrue(statuses)
        for status in statuses:
            with self.subTest(status=status):
                report = self.put("01-01-SUMMARY.md", '---\nphase: "01"\nplan: "01"\nstatus: ' + status + '\n---\n')
                self.assertTrue(self.cli("frontmatter.validate", report, "--schema", "summary")["valid"])
        self.assertNotIn("machine-read", guidance)
        self.assertNotIn("blocked_by", guidance)

    def test_partial_and_blocked_remain_incomplete_until_complete(self):
        directory = Path(self.phase())
        first = self.plan(directory)
        self.put(str(directory.relative_to(self.root) / "01-02-PLAN.md"),
                 first.read_text().replace('plan: "01"', 'plan: "02"').replace("depends_on: []", 'depends_on: ["01-01"]'))
        for status in ("blocked", "partial", "complete"):
            with self.subTest(status=status):
                self.put(str(directory.relative_to(self.root) / "01-01-SUMMARY.md"),
                         '---\nphase: "01"\nplan: "01"\nstatus: ' + status + '\n---\n')
                index = self.cli("phase-plan-index", "1")
                self.assertEqual(status == "complete", "01-01" in index["completed_plans"])
                self.assertEqual(status == "complete", "01-02" in index["ready_plans"])

    def test_unsupported_state_fields_and_types_still_fail(self):
        for fields in ("status: halted", "status: []", "status: partial\nblocked_by: [01-00]"):
            with self.subTest(fields=fields):
                report = self.put("01-01-SUMMARY.md", '---\nphase: "01"\nplan: "01"\n' + fields + '\n---\n')
                before = report.read_bytes()
                self.assertFalse(self.cli("frontmatter.validate", report, "--schema", "summary", status=1)["valid"])
                self.assertEqual(before, report.read_bytes())


class VerificationFingerprintProducers(RuntimeCase):
    def test_verifier_creates_report_before_fingerprint(self):
        output = source(VERIFIER).split("## Create VERIFICATION.md", 1)[1]
        self.assertGreater(output.index("engineer_run query verification.fingerprint"),
                           output.index("# Phase {X}: {Name} Verification Report"))

    def check_documented_fingerprint(self, path):
        spec = importlib.util.spec_from_file_location("_boundary_posix_shell", SOURCE / "engineer/bin/lib/posix_shell.py")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        shell = helper.find_posix_shell()
        if not shell:
            self.skipTest("POSIX shell required for documented producer fixture")
        directory = Path(self.phase())
        files = ["src/first file.py", "src/second.py"]
        for name in files:
            self.put(name, "VALUE = 1\n")
        report = directory / "01-VERIFICATION.md"
        for status in ("passed", "gaps_found", "human_needed"):
            with self.subTest(path=path, status=status):
                self.put(str(report.relative_to(self.root)), '---\nphase: "01"\nstatus: ' + status +
                         '\ncovered_files: ' + json.dumps(files) + '\nrevision: "' + self.git("rev-parse", "HEAD") + '"\n---\nActual observations retained.\n')
                blocks = re.findall(r"```bash\n(.*?)\n```", source(path), re.S)
                candidates = [block for block in blocks if "engineer_run query verification.fingerprint" in block]
                if candidates:
                    command = candidates[0]
                else:
                    command = re.search(r"`(engineer_run query verification.fingerprint [^`]+)`", source(path))[1]
                    command = command.replace("{phaseDir}", '"${PHASE_DIR}"').replace("{file}...", '"${COVERED_FILES[@]}"')
                preamble = '\n'.join(("set -e", "engineer_run() { " + shlex.quote(Path(sys.executable).as_posix()) +
                                      " -I " + shlex.quote(RUNTIME.as_posix()) + ' "$@"; }',
                                      "PHASE_DIR=" + shlex.quote(directory.as_posix()),
                                      "COVERED_FILES=(" + " ".join(map(shlex.quote, files)) + ")"))
                result = subprocess.run([shell, "-c", preamble + "\n" + command], cwd=self.root, env=self.env,
                                        text=True, encoding="utf-8", capture_output=True, timeout=30)
                self.assertEqual(0, result.returncode, result.stderr or result.stdout)
                packet = json.loads(result.stdout)
                metadata = self.cli("frontmatter.get", report)
                self.assertEqual(files, metadata["covered_files"])
                self.assertEqual(packet["fingerprint"], metadata["fingerprint"])
                self.assertEqual(status, metadata["status"])
                self.assertIn("Actual observations retained.", report.read_text())
                self.assertTrue(self.cli("frontmatter.validate", report, "--schema", "verification")["valid"])

    def test_verifier_fingerprint_covers_all_explicit_files(self):
        self.check_documented_fingerprint(VERIFIER)

    def test_unknown_verification_fields_and_types_still_fail(self):
        for fields in ("status: not_started", "status: []", "status: gaps_found\ncovered_files: bad", "status: gaps_found\nunknown: true"):
            with self.subTest(fields=fields):
                report = self.put("01-VERIFICATION.md", '---\nphase: "01"\n' + fields + '\n---\n')
                before = report.read_bytes()
                self.assertFalse(self.cli("frontmatter.validate", report, "--schema", "verification", status=1)["valid"])
                self.assertEqual(before, report.read_bytes())


if __name__ == "__main__":
    unittest.main()
