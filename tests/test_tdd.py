import json
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class TddChecks(RuntimeCase):
    def evidence(self, **overrides):
        record = {"command": "python -m unittest tests.test_app", "exitCode": 1,
                  "output": "FAIL: test_behavior (tests.test_app.App.test_behavior)\nAssertionError: 1 != 2\nRan 1 test in 0.1s\nFAILED (failures=1)\n",
                  "targetTest": "tests.test_app.App.test_behavior", "targetFile": "tests/test_app.py", "expected": 2, "actual": 1}
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
