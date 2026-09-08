"""Bounded independent probes of TASK-018's frozen candidate; no product edits."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys
from dataclasses import replace

ROOT = pathlib.Path(r"D:/Codex Projects/ai-engineering-template")
TREE = ROOT / ".worktrees/TASK-018-a1"
spec = importlib.util.spec_from_file_location(
    "task018_review_fixture", TREE / "tests/unit/validation/test_validation.py"
)
fixture = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fixture)
from local_ports import EnvironmentBinding
from domain_values import EntityId, Sha256Digest, ValidationStatus

results = []


def actual_case(name, code, rule=fixture.CommandSuccessRule.UNITTEST_NONZERO_COUNT, sensitive=False):
    case = fixture.ValidationTests()
    case.setUp()
    try:
        argv = (sys.executable, "-c", code)
        marker = "TASK018_REVIEW_SYNTHETIC_TOKEN_52794"
        if sensitive:
            argv += (marker,)
        definition = case.definition("check." + name, argv, rule)
        bindings = ()
        if sensitive:
            definition = replace(definition, environment_bindings=("REVIEW_TOKEN",))
            bindings = (EnvironmentBinding("REVIEW_TOKEN", marker, sensitive=True),)
        command = fixture.ConfiguredCommand(definition, environment=bindings)
        validator = case.validator((command,))
        row = {"case": name, "actual_child_code": code, "requested_oid": case.oid}
        try:
            result = validator.run(case.request((command,), suffix=name))
            row.update(status=result.status.value, observed_count=result.checks[0].observed_test_count)
            receipts = [case.read_receipt(ref) for ref in result.evidence_refs]
            command_receipt = receipts[0]
            observed = command_receipt["command_evidence"]
            row["command_evidence"] = observed
            row["receipt_sha256_verified"] = True
            row["before_oid"] = command_receipt["observed_before_revision_oid"]
            row["after_oid"] = command_receipt["observed_after_revision_oid"]
            for stream in ("stdout", "stderr"):
                ref = observed[stream + "_ref"]
                content = (case.project / ref["path"]).read_bytes()
                assert hashlib.sha256(content).hexdigest() == ref["sha256"]
                row[stream + "_bytes"] = len(content)
                row[stream] = content.decode("utf-8") if len(content) < 2000 else "[bounded long output omitted]"
            if sensitive:
                row["synthetic_token_in_runner_argv"] = marker in json.dumps(observed["argv_redacted"])
                row["synthetic_token_in_receipt_configured_argv"] = marker in json.dumps(command_receipt["configured_command"]["argv"])
        except Exception as exc:
            row.update(raised=type(exc).__name__, error=str(exc), retained_receipts=len(list((case.project / "evidence/validation").glob("*.json"))))
        results.append(row)
    finally:
        case.doCleanups()


actual_case("stdout-zero-stderr-decoy", "import sys, unittest; print('Earlier diagnostic:'); sys.stderr.write('Ran 7 tests in 0.001s\\n'); sys.stderr.flush(); result=unittest.TextTestRunner(stream=sys.stdout).run(unittest.TestSuite()); print('ACTUAL_TESTS_RUN='+str(result.testsRun)); raise SystemExit(not result.wasSuccessful())")
actual_case("stderr-zero-trailing-decoy", "import sys, unittest; result=unittest.TextTestRunner().run(unittest.TestSuite()); sys.stderr.write('Historical output excerpt follows:\\nRan 7 tests in 0.001s\\nEnd excerpt\\n'); print('ACTUAL_TESTS_RUN='+str(result.testsRun)); raise SystemExit(not result.wasSuccessful())")
actual_case("malformed-count-overflow", "print('Ran '+'9'*5000+' tests in 0.001s')")
actual_case("sensitive-argv", "import sys; print(sys.argv[1])", fixture.CommandSuccessRule.EXIT_ZERO, sensitive=True)
git_executable = shutil.which("git")
assert git_executable is not None
actual_case("real-git-drift", f"import pathlib, subprocess; pathlib.Path('changed.txt').write_text('changed'); subprocess.run([{git_executable!r},'add','changed.txt'],check=True); subprocess.run([{git_executable!r},'-c','commit.gpgsign=false','commit','--no-verify','-qm','during-validation'],check=True)", fixture.CommandSuccessRule.EXIT_ZERO)

# Isolated collaborators exercise returned evidence guards while the native Git
# observer still binds the worktree. This supplements the actual process probes.
case = fixture.ValidationTests()
case.setUp()
try:
    command = fixture.ConfiguredCommand(case.definition("check.guards", (sys.executable, "-c", "pass")))
    evidence = case.evidence(command)
    for name, bad in (
        ("wrong-root", replace(evidence, cwd_worktree_id=EntityId("other-root"))),
        ("wrong-env", replace(evidence, environment_binding_names=("OTHER",))),
        ("running", replace(evidence, status=fixture.CommandStatus.RUNNING, exit_code=None, finished_at=None)),
    ):
        result = case.validator((command,), runner=fixture.SequenceRunner(bad)).run(case.request((command,), suffix=name))
        results.append({"case": name, "status": result.status.value})
        assert result.status is not ValidationStatus.PASSED

    class BadStore:
        def __init__(self, mode): self.mode = mode
        def write(self, *args):
            ref = case.receipt_store.write(*args)
            return replace(ref, sha256=Sha256Digest("0" * 64)) if self.mode == "wrong-receipt-digest" else ref
        def read(self, ref, maximum):
            value = case.receipt_store.read(ref, maximum)
            return value + b" " if self.mode == "wrong-receipt-readback" else value

    for mode in ("wrong-receipt-digest", "wrong-receipt-readback"):
        result = case.validator((command,), runner=fixture.SequenceRunner(evidence), evidence_store=BadStore(mode)).run(case.request((command,), suffix=mode))
        results.append({"case": mode, "status": result.status.value})
        assert result.status is ValidationStatus.UNKNOWN
finally:
    case.doCleanups()

output = {"python": sys.version, "candidate_origin": fixture.SOURCE_ROOT.as_posix(), "cases": results}
path = pathlib.Path(__file__).with_suffix(".json.txt")
path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
print(json.dumps(output, indent=2))
