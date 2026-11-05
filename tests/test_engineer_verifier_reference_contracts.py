"""Execute verifier reference calls against disposable native runtime fixtures."""
import importlib.util
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE, RUNTIME
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE, RUNTIME


REFERENCE = "engineer/references/verifier-phase-gates.md"
TEMPLATE = "engineer/templates/verification-report.md"


def source(path):
    return (SOURCE / path).read_text(encoding="utf-8")


class VerifierReferenceContracts(RuntimeCase):
    def setUp(self):
        super().setUp()
        self.directory = Path(self.phase())
        self.context = self.directory / "01-CONTEXT.md"
        self.report = self.directory / "01-VERIFICATION.md"
        self.section = source(REFERENCE).split('<step name="verify_decisions">', 1)[1].split("</step>", 1)[0]

    def decision_args(self):
        command = re.search(r"\$\((engineer_run query check\.decision-coverage-verify [^\n]+?)\)", self.section)[1]
        values = {"${PHASE_NUM}": "01", "${PHASE_DIR}": str(self.directory),
                  "${CONTEXT_PATH}": str(self.context)}
        return [values.get(token, token) for token in shlex.split(command)[2:]]

    def test_documented_call_requires_report_then_matches_native_output(self):
        self.context.write_text("D-01: Preserve limits\nD-02: Expose failure\n", encoding="utf-8")
        # Plans and source containing the IDs do not satisfy verification coverage.
        self.plan(self.directory, "D-01 D-02 implemented")
        self.put("src/app.py", "# D-01 D-02\n")
        args = self.decision_args()
        self.assertEqual({"passed": False, "block": True, "structuralOnly": True,
                          "decisions": ["D-01", "D-02"], "uncovered": ["D-01", "D-02"], "files": []},
                         self.cli(*args, status=1))
        self.report.write_text('---\nphase: "01"\nstatus: gaps_found\n---\n'
                               'D-01: Limits test failed.\nD-02: Failure handling is unverified.\n', encoding="utf-8")
        before = self.report.read_bytes()
        packet = self.cli(*args)
        self.assertEqual({"passed": True, "block": False, "structuralOnly": True,
                          "decisions": ["D-01", "D-02"], "uncovered": [], "files": [str(self.report)]}, packet)
        self.assertEqual(before, self.report.read_bytes())
        self.assertEqual(["check.decision-coverage-verify", "01", "--dir", str(self.directory)], args)
        sample = re.search(r"```json\n(.*?)\n```", self.section, re.S)[1]
        sample = sample.replace("${PHASE_DIR}", self.directory.as_posix()).replace("${PHASE_NUM}", "01")
        expected = json.loads(sample)
        expected["files"] = [str(Path(name)) for name in expected["files"]]
        self.assertEqual(packet, expected)

    def test_uncovered_and_missing_context_remain_blocking(self):
        self.assertEqual({"passed": False, "block": True, "uncovered": [],
                          "reason": "Decision context is missing", "structuralOnly": True},
                         self.cli(*self.decision_args(), status=1))
        self.context.write_text("D-01\nD-02\n", encoding="utf-8")
        self.report.write_text("Only D-01 was checked.\n", encoding="utf-8")
        packet = self.cli(*self.decision_args(), status=1)
        self.assertEqual(["D-02"], packet["uncovered"])
        self.assertTrue(packet["block"])
        self.assertFalse(packet["passed"])

    def test_zero_ids_still_require_a_report_and_disabled_gate_skips(self):
        self.context.write_text("<decisions>Keep behavior; no explicit IDs.</decisions>\n", encoding="utf-8")
        missing = self.cli(*self.decision_args(), status=1)
        self.assertEqual([], missing["decisions"])
        self.assertTrue(missing["block"])
        self.report.write_text("No tracked decision IDs to cite.\n", encoding="utf-8")
        present = self.cli(*self.decision_args())
        self.assertEqual([], present["decisions"])
        self.assertFalse(present["block"])
        self.cli("config-set", "workflow.context_coverage_gate", "false")
        self.context.unlink()
        self.report.unlink()
        self.assertEqual({"passed": True, "skipped": True, "uncovered": []}, self.cli(*self.decision_args()))

    def test_caller_error_is_nonzero_with_no_fabricated_coverage_counts(self):
        # An explicit directory outside the fixture is rejected before coverage.
        args = ["check.decision-coverage-verify", "01", "--dir", str(self.root.parent)]
        result = subprocess.run([sys.executable, "-I", str(RUNTIME), "query", *args],
                                cwd=self.root, env=self.env, text=True, encoding="utf-8", capture_output=True)
        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        packet = json.loads(result.stderr)
        self.assertEqual("path-outside-repository", packet["error"])
        self.assertNotIn("decisions", packet)
        self.assertNotIn("honored", packet)
        self.assertNotIn("total", packet)


class VerificationTemplateContracts(RuntimeCase):
    def test_template_shell_sample_runs_native_producer(self):
        spec = importlib.util.spec_from_file_location("_verifier_reference_shell", SOURCE / "engineer/bin/lib/posix_shell.py")
        helper = importlib.util.module_from_spec(spec)
        previous = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            spec.loader.exec_module(helper)
        finally:
            sys.dont_write_bytecode = previous
        shell = helper.find_posix_shell()
        if not shell:
            self.skipTest("POSIX shell required for complete documented shell sample")
        directory = Path(self.phase())
        files = ["src/first file.py", "src/second.py"]
        for path in files:
            self.put(path, "VALUE = 1\n")
        report = directory / "01-VERIFICATION.md"
        self.put(str(report.relative_to(self.root)), '---\nphase: "01"\nstatus: human_needed\n---\nActual observations retained.\n')
        # Capture the native producer's bytes as the oracle for shell argument
        # expansion. This avoids a platform-specific newline serialization guess.
        before = report.read_bytes()
        native = self.cli("verification.fingerprint", directory, "--files", files[0], "--files", files[1])
        native_bytes = report.read_bytes()
        report.write_bytes(before)
        command = next(block for block in re.findall(r"```bash\n(.*?)\n```", source(TEMPLATE), re.S)
                       if "engineer_run query verification.fingerprint" in block)
        preamble = "\n".join(("set -e", "engineer_run() { " + shlex.quote(Path(sys.executable).as_posix()) +
                               " -I " + shlex.quote(RUNTIME.as_posix()) + ' "$@"; }',
                               "PHASE_DIR=" + shlex.quote(directory.as_posix()),
                               "COVERED_FILES=(" + " ".join(map(shlex.quote, files)) + ")"))
        result = subprocess.run([shell, "-c", preamble + "\n" + command], cwd=self.root, env=self.env,
                                text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(0, result.returncode, result.stderr or result.stdout)
        self.assertEqual(native, json.loads(result.stdout))
        self.assertEqual(native_bytes, report.read_bytes())

    def test_template_native_producer_preserves_truthful_status_and_covers_spaced_paths(self):
        template = source(TEMPLATE)
        file_template = re.search(r"```markdown\n(.*?)\n```", template, re.S)[1]
        metadata_text = file_template.split("---", 2)[1]
        self.assertNotIn("covered_digest:", metadata_text)
        self.assertRegex(metadata_text, r"(?m)^revision:")
        self.assertRegex(metadata_text, r"(?m)^fingerprint:")
        directory = Path(self.phase())
        report = directory / "01-VERIFICATION.md"
        files = ["src/first file.py", "src/second.py"]
        for path in files:
            self.put(path, "VALUE = 1\n")
        commands = re.findall(r"```bash\n(.*?)\n```", template, re.S)
        command = next(block for block in commands if "engineer_run query verification.fingerprint" in block)
        # Expand only the documented literal command/array operands; execute the
        # resulting argv through the native CLI on every supported platform.
        self.assertIn('FINGERPRINT_ARGS+=(--files "$file")', command)
        call = next(line for line in command.splitlines() if line.startswith("engineer_run query verification.fingerprint"))
        args = []
        for token in shlex.split(call)[2:]:
            if token == "${FINGERPRINT_ARGS[@]}":
                args.extend(value for path in files for value in ("--files", path))
            else:
                args.append(str(directory) if token == "${PHASE_DIR}" else token)
        self.assertEqual(["verification.fingerprint", str(directory), "--files", files[0], "--files", files[1]], args)
        for status in ("passed", "gaps_found", "human_needed"):
            with self.subTest(status=status):
                rendered = metadata_text.replace("phase: XX-name", 'phase: "01"')
                rendered = rendered.replace("YYYY-MM-DDTHH:MM:SSZ", "2026-01-01T00:00:00Z")
                rendered = rendered.replace("passed | gaps_found | human_needed", status).replace("N/M must-haves verified", "1/1 must-haves verified")
                rendered = re.sub(r"(?m)^covered_files:.*\n(?:  - .*\n)+", "covered_files: " + json.dumps(files) + "\n", rendered)
                rendered = re.sub(r"(?m)^revision:.*$", 'revision: "' + self.git("rev-parse", "HEAD") + '"', rendered)
                rendered = re.sub(r"(?m)^fingerprint:.*\n", "", rendered)
                # Optional example items are omitted when their triggering
                # conditions do not apply to this fixture.
                rendered = rendered.split("behavior_unverified_items:", 1)[0]
                report.write_text("---" + rendered + "---\nActual observations retained.\n", encoding="utf-8")
                self.assertTrue(self.cli("frontmatter.validate", report, "--schema", "verification")["valid"])
                result = self.cli(*args)
                metadata = self.cli("frontmatter.get", report)
                self.assertEqual({"fingerprint", "path"}, set(result))
                self.assertEqual(str(report), result["path"])
                self.assertRegex(result["fingerprint"], r"^[a-f0-9]{64}$")
                self.assertEqual(result["fingerprint"], metadata["fingerprint"])
                self.assertEqual(files, metadata["covered_files"])
                self.assertEqual(self.git("rev-parse", "HEAD"), metadata["revision"])
                self.assertEqual(status, metadata["status"])
                self.assertNotIn("covered_digest", metadata)
                self.assertIn("Actual observations retained.", report.read_text(encoding="utf-8"))
                self.assertTrue(self.cli("frontmatter.validate", report, "--schema", "verification")["valid"])
                self.put(files[0], "VALUE = 2\n")
                changed = self.cli(*args)["fingerprint"]
                self.assertNotEqual(result["fingerprint"], changed)
                self.put(files[0], "VALUE = 1\n")
