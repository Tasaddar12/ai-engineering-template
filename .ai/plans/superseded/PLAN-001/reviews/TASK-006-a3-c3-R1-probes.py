"""Independent focused review probes; imports only the frozen candidate."""
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
import threading
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
CANDIDATE = Path.cwd().resolve()
assert CANDIDATE.name == 'TASK-006-a3'
sys.path.insert(0, str(CANDIDATE / 'src'))
sys.path.insert(0, str(CANDIDATE / 'tests/unit/commands'))
import commands
import config
import contracts
import local_ports
import test_commands as fixture_tests

assert Path(commands.__file__).resolve() == CANDIDATE / 'src/commands.py'
assert hashlib.sha256((CANDIDATE / 'src/commands.py').read_bytes()).hexdigest() == '700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0'
assert hashlib.sha256((CANDIDATE / 'tests/unit/commands/test_commands.py').read_bytes()).hexdigest() == 'c77171fefa9d43be13c4f06fe11dd49bc741caae267d6232578161248ff9952a'
print(json.dumps({'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(), 'jsonschema': importlib.metadata.version('jsonschema'), 'origins': {m.__name__: m.__file__ for m in (commands, config, contracts, local_ports, fixture_tests)}}, sort_keys=True), flush=True)

class ReviewProbes(unittest.TestCase):
    def test_watchdog_cleanup_cannot_manufacture_success(self):
        # A controlled collaborator finishes only when the helper's failure
        # cleanup releases it. Catch the expected watchdog assertion; it must
        # never return a success value after that cleanup.
        release = threading.Event()
        cleanup_calls = []
        class ControlledRunner:
            def execute(self, request):
                release.wait(2)
                return 'controlled result'
        class ControlledFixture:
            watchdog_intervened = False
            def mark_started(self, started):
                self.started_monotonic = started
            def cleanup(self, test):
                cleanup_calls.append(True)
                release.set()
        control = ControlledFixture()
        try:
            with self.assertRaisesRegex(AssertionError, 'overall bound'):
                fixture_tests.CommandRunnerTests._execute_with_watchdog(
                    self, ControlledRunner(), object(), control, overall_seconds=0.02
                )
        finally:
            release.set()
        self.assertTrue(control.watchdog_intervened)
        self.assertEqual(cleanup_calls, [True])
        self.assertFalse(any(t.name == 'task006-fixture-execute' for t in threading.enumerate()))

    def test_missing_phase_and_expired_startup_are_rejected(self):
        # No process is launched. These negative controls verify that cleanup
        # counters or PID-file publication cannot substitute for phase proof.
        with fixture_tests.tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            control = fixture_tests.ObservedFixtureCancellation(
                pid_file=root / 'pid', ready_file=root / 'ready',
                phase='inherited_after_parent_exit', cancel_when_ready=True,
            )
            control.mark_started(fixture_tests.time.monotonic())
            control.native_termination_calls = 1
            with self.assertRaisesRegex(AssertionError, 'phase was not observed'):
                control.assert_ready(self)
            control.startup_expired = True
            with self.assertRaisesRegex(AssertionError, 'startup deadline'):
                control.assert_ready(self)
            control.startup_expired = False
            control.watchdog_intervened = True
            with self.assertRaisesRegex(AssertionError, 'watchdog changed'):
                control.assert_ready(self)

    def test_actual_multiencoding_secret_capture_and_partial_storage_failure(self):
        fixture_tests.CommandRunnerTests.setUpClass()
        case = fixture_tests.CommandRunnerTests()
        case.setUp()
        try:
            secret = 'Review-secret-Delta-2468'
            code = "import os; token=os.environ['TOKEN']; [(os.write(1,token.encode(e)),os.write(2,token.encode(e))) for e in ('utf-8','utf-16-le','utf-16-be')]"
            request = case.request(case.definition((case.python, '-c', code), environment=('TOKEN',)), environment=(local_ports.EnvironmentBinding('TOKEN', secret),))
            evidence = case.runner().execute(request)
            self.assertEqual(evidence.status.value, 'exited')
            combined = case.read_log(evidence.stdout_ref) + case.read_log(evidence.stderr_ref)
            self.assertEqual(combined, b'[REDACTED]' * 6)
            self.assertTrue(evidence.redactions_applied)
            self.assertFalse(evidence.output_truncated)
            case.assert_schema(evidence)
            actual_store = commands.FileCommandLogStore(case.project, 'partial-review-log')
            class SecondWriteFails:
                def write(self, evidence_id, stream, content):
                    if stream == 'stderr':
                        raise OSError('injected second durable write failure')
                    return actual_store.write(evidence_id, stream, content)
            partial = case.runner(log_store=SecondWriteFails()).execute(case.request(case.definition((case.python, '-c', "print('retained stdout')"))))
            self.assertEqual(partial.status.value, 'unknown')
            self.assertEqual(partial.error_category, 'internal_error')
            self.assertIsNone(partial.exit_code)
            self.assertIsNone(partial.stderr_ref)
            self.assertEqual(case.read_log(partial.stdout_ref).strip(), b'retained stdout')
            case.assert_schema(partial)
            self.assertTrue(case._wait_command_readers(2))
        finally:
            case.doCleanups()

if sys.argv[1:] == ['phase']:
    schema_observations = []
    original_schema = fixture_tests.CommandRunnerTests.assert_schema
    def observe_schema(self, evidence):
        original_schema(self, evidence)
        schema_observations.append({'test': self._testMethodName, 'status': evidence.status.value, 'exit_code': evidence.exit_code, 'error': evidence.error_category, 'output_truncated': evidence.output_truncated})
    fixture_tests.CommandRunnerTests.assert_schema = observe_schema
    suite = unittest.TestSuite(fixture_tests.CommandRunnerTests(name) for name in (
        'test_inherited_pipe_descendant_cannot_block_timeout_or_cancellation_return',
        'test_detached_descendant_timeout_and_cancellation_never_overclaim_cleanup',
    ))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print('POST_ASSERTION_SCHEMA ' + json.dumps(schema_observations, sort_keys=True))
    assert len(schema_observations) == 4
    assert result.testsRun == 2 and not result.skipped
else:
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReviewProbes))
    assert result.testsRun == 3 and not result.skipped
assert result.wasSuccessful()
assert not [t for t in threading.enumerate() if t.name.startswith(('command-', 'task006-fixture-execute'))]
print('PASS: focused review probes; no remaining command reader or fixture execution threads')
