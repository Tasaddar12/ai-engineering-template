"""Focused independent correction verification; never a product dependency."""
from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import io
import json
import pathlib
import platform
import sys
import unittest
from dataclasses import replace

TREE = pathlib.Path.cwd().resolve()
spec = importlib.util.spec_from_file_location(
    "task018_current_fixture", TREE / "tests/unit/validation/test_validation.py"
)
fixture = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fixture)
import commands
import validation
import workflow_ports

origins = {module.__name__: str(pathlib.Path(module.__file__).resolve())
           for module in (commands, validation, workflow_ports)}
assert all(pathlib.Path(path).parent == TREE / "src" for path in origins.values())
selected = (
    "test_actual_suite_runs_configured_argv_and_persists_bound_identity",
    "test_actual_zero_test_discovery_and_nonzero_exit_fail",
    "test_actual_zero_test_summaries_do_not_borrow_unrelated_counts",
    "test_actual_oversized_count_fails_and_later_command_is_collected",
    "test_sensitive_configured_argv_is_sanitized_from_all_receipts",
)
stream = io.StringIO()
test_result = unittest.TextTestRunner(stream=stream, verbosity=2).run(
    unittest.TestSuite(fixture.ValidationTests(name) for name in selected)
)
rows = []


def actual(name, code, expected, count, bindings=(), arguments=(), reject=False):
    case = fixture.ValidationTests()
    case.setUp()
    try:
        rule = (fixture.CommandSuccessRule.EXIT_ZERO if bindings
                else fixture.CommandSuccessRule.UNITTEST_NONZERO_COUNT)
        definition = replace(
            case.definition("check." + name, (sys.executable, "-c", code, *arguments), rule),
            environment_bindings=tuple(binding.name for binding in bindings),
        )
        command = fixture.ConfiguredCommand(definition, environment=bindings)
        request = case.request((command,), suffix=name)
        if reject:
            request = replace(request, revision_oid="f" * 40)
        result = case.validator((command,)).run(request)
        assert result.status.value == expected, (name, result.status)
        assert result.checks[0].observed_test_count == count, (name, result.checks)
        receipts = [case.read_receipt(ref) for ref in result.evidence_refs]
        assert len(receipts) == 2
        check, suite = receipts
        assert check["status"] != "passed" or expected == "passed"
        assert suite["status"] == expected
        row = {"case": name, "status": expected, "count": count,
               "receipt_hashes_verified": True, "check_status": check["status"],
               "before_oid": check["observed_before_revision_oid"],
               "after_oid": check["observed_after_revision_oid"]}
        observed = check["command_evidence"]
        row["command_observed"] = observed is not None
        if observed is not None:
            row["exit_code"] = observed["exit_code"]
            for key in ("stdout", "stderr"):
                reference = observed[key + "_ref"]
                content = (case.project / reference["path"]).read_bytes()
                assert hashlib.sha256(content).hexdigest() == reference["sha256"]
                row[key + "_bytes"] = len(content)
                row[key] = content.decode("utf-8") if len(content) < 1000 else "[long count omitted]"
        if bindings:
            expected_argv = [sys.executable, "-c", code, "public \t\n value", "x[REDACTED]y", "repeat", "repeat"]
            assert check["configured_command"]["argv"] == expected_argv
            if observed is not None:
                assert observed["argv_redacted"] == expected_argv
                assert observed["redactions_applied"]
            for reference in result.evidence_refs:
                content = case.receipt_store.read(reference, 1_048_576)
                for binding in bindings:
                    if binding.sensitive and binding.value:
                        assert binding.value.encode() not in content
            row["all_receipts_sanitized_and_public_argv_exact"] = True
        rows.append(row)
    finally:
        case.doCleanups()


actual("positive-stdout-skipped-status",
       "import sys, unittest; case=unittest.FunctionTestCase(lambda: None); "
       "skip=unittest.FunctionTestCase(lambda: (_ for _ in ()).throw(unittest.SkipTest('skip'))); "
       "result=unittest.TextTestRunner(stream=sys.stdout).run(unittest.TestSuite((case,skip))); "
       "raise SystemExit(not result.wasSuccessful())", "passed", 2)
actual("cross-stream-conflicting-complete-blocks",
       "import sys, unittest; unittest.TextTestRunner().run(unittest.TestSuite()); "
       "unittest.TextTestRunner(stream=sys.stdout).run(unittest.TestSuite((unittest.FunctionTestCase(lambda: None),)))",
       "failed", None)
actual("split-summary-status",
       "import sys; print('-'*70); print('Ran 1 test in 0.001s'); sys.stderr.write('\\nOK\\n')",
       "failed", None)
actual("count-above-explicit-bound",
       "print('-'*70); print('Ran 1000000001 tests in 0.001s'); print(); print('OK')",
       "failed", None)
actual("original-bare-5000-digit-count",
       "print('Ran '+'9'*5000+' tests in 0.001s')", "failed", None)
marker = "REVIEW018_SYNTHETIC_OVERLAP"
bindings = (
    fixture.EnvironmentBinding("LONG_SECRET", marker, sensitive=True),
    fixture.EnvironmentBinding("SHORT_SECRET", "SYNTHETIC_OVERLAP", sensitive=True),
    fixture.EnvironmentBinding("EMPTY_SECRET", "", sensitive=True),
    fixture.EnvironmentBinding("PUBLIC_VALUE", "public", sensitive=False),
)
arguments = ("public \t\n value", "x" + marker + "y", "repeat", "repeat")
actual("overlap-redacted-executed", "pass", "failed", None, bindings, arguments)
actual("overlap-redacted-stale-before", "pass", "failed", None, bindings, arguments, True)
output = {
    "purpose": "Focused verification of 001/002/003 with unchanged controls reused from retained c1 review",
    "candidate_head": "41a8cd578b81981e6cda42c88f9377aaec5b1bdd",
    "cwd": str(TREE), "python": sys.version, "executable": sys.executable,
    "platform": platform.platform(), "jsonschema": importlib.metadata.version("jsonschema"),
    "origins": origins, "tracked_tests_run": test_result.testsRun,
    "tracked_skips": test_result.skipped,
    "tracked_tests_passed": test_result.wasSuccessful(),
    "tracked_transcript": stream.getvalue(), "independent_actual_cases": rows,
    "integer_conversion_limit": sys.get_int_max_str_digits(),
}
print(json.dumps(output, indent=2))
assert test_result.testsRun == 5 and not test_result.skipped and test_result.wasSuccessful()
