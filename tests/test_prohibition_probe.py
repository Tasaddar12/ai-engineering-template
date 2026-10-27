"""Real temporary-project controls; no proof is accepted from caller flags."""
import json
import os
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SOURCE / "engineer/bin"))
from lib.core import Args, Failure
from lib.probes import prohibition_project, prohibition_proof


class ProhibitionProbe(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        environment = patch.dict(os.environ, {"ENGINEER_ROOT": str(self.root)})
        environment.start()
        self.addCleanup(environment.stop)

    def put(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def project(self, items):
        path = self.put("selected.json", json.dumps(items))
        return prohibition_project(Args([str(path)]))

    def test_all_reference_projection_oracles(self):
        fixtures = SOURCE / "engineer/references/prohibition-probe-fixtures"
        for path in sorted(fixtures.rglob("expected.json")):
            with self.subTest(fixture=path.parent.name):
                oracle = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(oracle, self.project(oracle["items"]))

    def test_projection_is_selected_only_and_tiers_are_orthogonal(self):
        base = {"requirement_id": "R", "category": "bespoke", "statement": "MUST NOT expose secrets"}
        result = self.project([
            {**base, "status": "resolved", "verification": "test"},
            {**base, "status": "resolved", "verification": "judgment"},
            {**base, "status": "dismissed", "reason": "No such data", "verification": "test"},
            {**base, "status": "unresolved", "verification": "judgment"},
        ])
        self.assertEqual({"applicable": 4, "resolved": 3, "unresolved": 1,
                          "byVerification": {"test": 1, "judgment": 1}}, result["coverage"])
        self.assertIsNone(result["items"][2]["verification"])
        self.assertIsNone(result["items"][3]["verification"])
        self.assertEqual([], self.project([])["items"])
        with self.assertRaises(Failure):
            self.project([{"id": "R", "text": "Send a reminder"}])

    def test_flat_projection_preserves_wired_descriptors_without_inventing_proof(self):
        row = {"requirement_id": "R", "category": "privacy", "statement": "MUST NOT expose secrets",
               "status": "resolved", "verification": "test", "check_kind": "lint-rule",
               "check_target": "source.py", "check_rule": "local/no-secret",
               "check_violation_fixture": "bad.py", "check_clean_fixture": "clean.py"}
        result = self.project([row])["items"][0]
        for key in row:
            self.assertEqual(row[key], result[key])
        self.assertNotIn("proved", result)
        for partial in ({"check_kind": "lint-rule", "check_target": "x"},
                        {"check_kind": "unknown", "check_target": "x"}, {}):
            candidate = {key: value for key, value in row.items() if not key.startswith("check_")}
            projected = self.project([{**candidate, **partial}])["items"][0]
            self.assertFalse(any(key.startswith("check_") for key in projected))
            self.assertEqual("test", projected["verification"])
        for invalid in ({"check": {"kind": "test-command"}}, {"check_target": []},
                        {"status": "dismissed", "reason": " "}, {"verification": "backstop"}):
            with self.subTest(invalid=invalid), self.assertRaises(Failure):
                self.project([{**row, **invalid}])

    def descriptor(self, body=None, legacy=False):
        variable = "GSD_PROHIB_SUBJECT" if legacy else "ENGINEER_PROHIB_SUBJECT"
        body = body or f"self.assertNotIn('secret', Path(os.environ[{variable!r}]).read_text())"
        script = self.put("negative_check.py", textwrap.dedent(f"""\
            import os
            from pathlib import Path
            import unittest
            class Privacy(unittest.TestCase):
                def test_no_raw_secret(self):
                    {body}
            if __name__ == '__main__':
                unittest.main()
            """))
        self.put("bad.txt", "raw secret")
        self.put("clean.txt", "redacted")
        self.put("real.txt", "safe real output")
        return {"kind": "test-command", "target": str(script), "violationFixture": "bad.txt",
                "cleanFixture": "clean.txt", "argv": [sys.executable, "{target}"], "failFirst": True}

    def proof(self, descriptor, timeout=None):
        path = self.put("descriptor.json", json.dumps(descriptor))
        values = [str(path), "--subject", str(self.root / "real.txt")]
        if timeout:
            values += ["--timeout", str(timeout)]
        return prohibition_proof(Args(values))

    def rejected(self, descriptor, reason=None, timeout=None):
        with self.assertRaises(Failure) as caught:
            self.proof(descriptor, timeout)
        self.assertEqual(2, caught.exception.status)
        self.assertFalse(caught.exception.details["proved"])
        self.assertEqual("flagged", caught.exception.details["disposition"])
        if reason:
            self.assertIn(reason, caught.exception.message)
        return caught.exception.details

    def test_actual_negative_clean_and_subject_proof_with_both_environment_names(self):
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                result = self.proof(self.descriptor(legacy=legacy))
                self.assertTrue(result["located"] and result["proved"] and result["valid"])
                self.assertEqual("green", result["disposition"])
                self.assertEqual(["violation", "clean", "subject"], [o["stage"] for o in result["observations"]])
                self.assertEqual([1, 0, 0], [o["exit_code"] for o in result["observations"]])
                self.assertEqual([1, 1, 1], [o["asserted"] for o in result["observations"]])

    def test_flat_aliases_translate_without_nested_plan_objects(self):
        descriptor = self.descriptor()
        for name, flat in (("kind", "check_kind"), ("target", "check_target"),
                           ("violationFixture", "check_violation_fixture"), ("cleanFixture", "check_clean_fixture")):
            descriptor[flat] = descriptor.pop(name)
        self.assertTrue(self.proof(descriptor)["proved"])

    def test_attestation_cannot_replace_bad_control(self):
        self.rejected(self.descriptor("self.assertTrue(True)"), "violation")
        details = self.rejected(self.descriptor("self.fail('content-independent failure')"), "clean")
        self.assertEqual(2, len(details["observations"]))

    def test_real_subject_must_also_pass(self):
        descriptor = self.descriptor()
        self.put("real.txt", "a different secret")
        details = self.rejected(descriptor, "subject")
        self.assertEqual(3, len(details["observations"]))

    def test_errors_zero_skipped_and_timeouts_are_unprovable(self):
        for body in ("raise RuntimeError('not an assertion')", "self.skipTest('nothing checked')"):
            with self.subTest(body=body):
                self.rejected(self.descriptor(body))
        descriptor = self.descriptor()
        self.put("negative_check.py", "import unittest\nunittest.main()\n")
        self.rejected(descriptor, "non-vacuous")
        descriptor = self.descriptor("__import__('time').sleep(2)")
        details = self.rejected(descriptor, "timed out", timeout=0.01)
        self.assertTrue(details["observations"][0]["timed_out"])

    def test_missing_controls_target_argv_and_unknown_reports_fail_closed(self):
        for key in ("violationFixture", "cleanFixture", "target", "argv"):
            descriptor = self.descriptor()
            descriptor.pop(key)
            with self.subTest(missing=key):
                self.rejected(descriptor)
        descriptor = self.descriptor()
        descriptor["argv"] = [sys.executable, "-c", "pass"]
        self.rejected(descriptor, "name the check target")
        descriptor = self.descriptor()
        descriptor["reportFormat"] = "caller-says-green"
        self.rejected(descriptor, "Unrecognized")

    def lint_descriptor(self):
        target = self.put("lint_check.py", textwrap.dedent("""\
            import ast
            import json
            from pathlib import Path
            import sys
            subject = Path(sys.argv[1]).resolve()
            nodes = ast.walk(ast.parse(subject.read_text()))
            messages = [{'ruleId': 'local/no-eval', 'severity': 2, 'message': 'eval is forbidden'}
                        for node in nodes if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Name) and node.func.id == 'eval']
            print(json.dumps([{'filePath': str(subject), 'messages': messages,
                               'errorCount': len(messages), 'warningCount': 0, 'fatalErrorCount': 0}]))
            sys.exit(1 if messages else 0)
            """))
        self.put("bad.py", "eval('1')")
        self.put("clean.py", "value = 1")
        self.put("real.txt", "value = 2")
        return {"kind": "lint-rule", "target": str(target), "rule": "local/no-eval",
                "violationFixture": "bad.py", "cleanFixture": "clean.py",
                "argv": [sys.executable, "{target}", "{subject}"]}

    def test_lint_requires_selected_rule_and_each_actual_processed_subject(self):
        result = self.proof(self.lint_descriptor())
        self.assertEqual([1, 0, 0], [o["rule_hits"] for o in result["observations"]])
        descriptor = self.lint_descriptor()
        descriptor["rule"] = "different/rule"
        self.rejected(descriptor, "violation")
        descriptor = self.lint_descriptor()
        content = (self.root / "lint_check.py").read_text()
        self.put("lint_check.py", content.replace("str(subject)", "str(subject.parent / 'other.py')"))
        self.rejected(descriptor, "actual injected subject")

    def test_lint_missing_clean_control_and_fatal_report_are_unprovable(self):
        descriptor = self.lint_descriptor()
        descriptor.pop("cleanFixture")
        self.rejected(descriptor)
        descriptor = self.lint_descriptor()
        content = (self.root / "lint_check.py").read_text()
        self.put("lint_check.py", content.replace("'fatalErrorCount': 0", "'fatalErrorCount': 1"))
        self.rejected(descriptor, "fatal")

    def test_junit_requires_fresh_nonzero_asserted_cases(self):
        descriptor = self.descriptor()
        descriptor.update({"reportFormat": "junit", "reportFile": "result.xml",
                           "argv": [sys.executable, "{target}", "{report}"]})
        self.put("negative_check.py", textwrap.dedent("""\
            import os
            from pathlib import Path
            import sys
            import xml.etree.ElementTree as ET
            bad = 'secret' in Path(os.environ['ENGINEER_PROHIB_SUBJECT']).read_text()
            suite = ET.Element('testsuite', tests='1', failures=str(int(bad)), errors='0', skipped='0')
            case = ET.SubElement(suite, 'testcase', name='privacy')
            if bad:
                ET.SubElement(case, 'failure', type='AssertionError', message='raw secret forbidden')
            ET.ElementTree(suite).write(sys.argv[1], encoding='unicode')
            sys.exit(int(bad))
            """))
        self.assertTrue(self.proof(descriptor)["proved"])
        self.put("negative_check.py", "import sys\nsys.exit(0)\n")
        self.rejected(descriptor, "stale report")

    def test_junit_rejects_zero_skipped_errors_and_inconsistent_counts(self):
        reports = (
            '<testsuite tests="0"/>',
            '<testsuite tests="1"><testcase name="privacy"><skipped/></testcase></testsuite>',
            '<testsuite tests="1"><testcase name="privacy"><error type="RuntimeError"/></testcase></testsuite>',
            '<testsuite tests="5"><testcase name="privacy"/></testsuite>',
            '<testsuite tests="1"><testcase name="privacy"><failure type="RuntimeError"/></testcase></testsuite>',
            '<testsuites tests="9"><testsuite tests="1"><testcase name="privacy"/></testsuite></testsuites>',
        )
        for report in reports:
            with self.subTest(report=report):
                descriptor = self.descriptor()
                descriptor.update({"reportFormat": "junit", "reportFile": "result.xml",
                                   "argv": [sys.executable, "{target}", "{report}"]})
                self.put("negative_check.py", "from pathlib import Path\nimport sys\n"
                         + f"Path(sys.argv[1]).write_text({report!r})\nsys.exit(1)\n")
                self.rejected(descriptor)

    def test_lint_report_counts_and_empty_results_are_not_proof(self):
        for replacement in ("'errorCount': 0", "'errorCount': 100"):
            descriptor = self.lint_descriptor()
            content = (self.root / "lint_check.py").read_text()
            self.put("lint_check.py", content.replace("'errorCount': len(messages)", replacement))
            with self.subTest(replacement=replacement):
                self.rejected(descriptor, "Inconsistent lint counters")

    def test_cli_arguments_remain_individual_tokens(self):
        descriptor = self.descriptor()
        spaced = self.root / "a check with spaces.py"
        (self.root / "negative_check.py").rename(spaced)
        descriptor["target"] = str(spaced)
        self.assertTrue(self.proof(descriptor)["proved"])
        descriptor["argv"][0] = "must-not-execute.cmd"
        self.rejected(descriptor, "shell evaluation")

    def test_malformed_or_missing_machine_report_never_greens(self):
        descriptor = self.descriptor()
        self.put("negative_check.py", "print('passed: true, failFirst: true')\n")
        self.rejected(descriptor, "summary")
        descriptor = self.lint_descriptor()
        self.put("lint_check.py", "print('[]')\n")
        self.rejected(descriptor, "processed files")
