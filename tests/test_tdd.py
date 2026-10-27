import json
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class TddChecks(RuntimeCase):
    def setUp(self):
        super().setUp()
        self.put("tests/test_app.py", "# failing behavior test\n")
        self.git("add", "tests/test_app.py")
        self.git("commit", "-m", "test(01-01): RED behavior fixture")
        self.red_commit = self.git("rev-parse", "HEAD")

    def evidence(self, **overrides):
        record = {"command": "python -m unittest tests.test_app", "exitCode": 1,
                  "output": "FAIL: test_behavior (tests.test_app.App.test_behavior)\nAssertionError: 1 != 2\nRan 1 test in 0.1s\nFAILED (failures=1)\n",
                  "targetTest": "tests.test_app.App.test_behavior", "targetFile": "tests/test_app.py", "expected": 2, "actual": 1, "testCommit": self.red_commit}
        record.update(overrides)
        return self.put("red.json", json.dumps(record))

    def test_target_assertion_is_required(self):
        path = self.evidence()
        self.assertEqual("RED_EVIDENCE_OK", self.cli("check.tdd-red-evidence", path, "--raw", raw=True))
        path = self.evidence(targetTest="test_other")
        self.assertEqual("INVALID_RED:no_target_test_failure", self.cli("check.tdd-red-evidence", path, "--raw", status=1, raw=True))

    def test_unreadable_green_build_and_import_errors(self):
        self.cli("check.tdd-red-evidence", "missing.json", status=69, raw=True)
        cases = [(dict(exitCode=0), "unexpected_green"),
                 (dict(output="FAIL\tpkg [build failed]"), "build_failure"),
                 (dict(output="ImportError: cannot import target"), "fixture_or_load_failure"),
                 (dict(output="not a supported report"), "invalid_record")]
        for changes, reason in cases:
            with self.subTest(reason=reason):
                path = self.evidence(**changes)
                self.assertEqual("INVALID_RED:"+reason, self.cli("check.tdd-red-evidence", path, "--raw", status=1, raw=True))

    def test_config_and_task_determine_tdd_applicability(self):
        path = self.plan(self.phase(), '<task tdd="true"><name>behavior</name></task>')
        self.assertFalse(self.cli("phase.tdd-applicable", path)["applicable"])
        self.cli("config-set", "workflow.tdd_mode", "true")
        self.assertTrue(self.cli("phase.tdd-applicable", path)["applicable"])
        self.assertFalse(self.cli("task.is-behavior-adding", '{"files":["docs/guide.md"],"action":"Document existing behavior"}')["is_behavior_adding"])

    def test_zero_tests_nonzero_without_failure_and_tap(self):
        path = self.evidence(output="Ran 0 tests in 0.1s\nFAILED (failures=0)\n")
        self.assertEqual("INVALID_RED:zero_tests_discovered", self.cli("check.tdd-red-evidence", path, "--raw", status=1, raw=True))
        path = self.evidence(output="Ran 1 test in 0.1s\nFAILED (failures=0)\n")
        self.assertEqual("INVALID_RED:nonzero_exit_without_test_failure", self.cli("check.tdd-red-evidence", path, "--raw", status=1, raw=True))
        path = self.evidence(output="TAP version 13\nnot ok 1 - rejects invalid input\n1..1\n", targetTest="rejects invalid input")
        self.assertEqual("RED_EVIDENCE_OK", self.cli("check.tdd-red-evidence", path, "--raw", raw=True))

    def test_red_commit_must_precede_implementation(self):
        self.put("tests/test_app.py", "# failing behavior test\n")
        self.git("add", "tests/test_app.py")
        red = self.red_commit
        self.put("src/app.py", "def app(): return 2\n")
        self.git("add", "src/app.py")
        self.git("commit", "-m", "feat(01-01): GREEN")
        green = self.git("rev-parse", "HEAD")
        path = self.evidence(testCommit=red, implementationCommit=green)
        self.assertEqual("RED_EVIDENCE_OK", self.cli("check.tdd-red-evidence", path, "--raw", raw=True))
        path = self.evidence(testCommit=green, implementationCommit=red)
        self.cli("check.tdd-red-evidence", path, status=1, raw=True)

    def test_pre_green_requires_committed_red_target_without_future_implementation(self):
        path = self.evidence()
        result = self.cli("check.tdd-red-evidence", path)
        self.assertEqual("RED_EVIDENCE_OK", result["verdict"])
        self.assertEqual(self.red_commit, result["evidence"]["testCommit"])
        self.assertEqual(self.red_commit, result["evidence"]["checkedRevision"])
        self.assertIsNone(result["evidence"]["implementationCommit"])
        for changes in ({"testCommit": None}, {"testCommit": "HEAD"}, {"testCommit": "0"*40},
                        {"testCommit": self.red_commit, "implementationCommit": self.red_commit}):
            path = self.evidence(**changes)
            self.cli("check.tdd-red-evidence", path, status=1, raw=True)

    def test_uncommitted_or_unrelated_test_cannot_borrow_red_commit(self):
        self.put("tests/test_app.py", "# changed assertion after RED\n")
        self.cli("check.tdd-red-evidence", self.evidence(), status=1, raw=True)
        self.put("tests/test_other.py", "# unrelated test\n")
        self.cli("check.tdd-red-evidence", self.evidence(targetFile="tests/test_other.py"), status=1, raw=True)

    def test_red_commit_on_unrelated_branch_cannot_authorize_green(self):
        self.git("switch", "-c", "sibling", "HEAD~1")
        self.put("tests/test_app.py", "# failing behavior test\n")
        self.git("add", "tests/test_app.py")
        self.git("commit", "-m", "test(02-01): unrelated RED")
        sibling = self.git("rev-parse", "HEAD")
        self.git("switch", "main")
        self.cli("check.tdd-red-evidence", self.evidence(testCommit=sibling), status=1, raw=True)
