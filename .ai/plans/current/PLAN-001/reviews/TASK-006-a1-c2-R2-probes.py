"""Fresh R2 cross-contract fixtures, isolated from all candidate files."""
import dataclasses
import hashlib
import importlib
import json
import os
import platform
import shutil
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-006-a1'
sys.path.insert(0, str(TREE / 'src'))
from commands import FileCommandLogStore, LocalCommandRunner
from config import RunOverrides, decode_run_settings, load_installation_record, load_project_settings
from contracts import ContractRegistry
from domain_values import CommandStatus, EntityId, EvidenceRef, PlanId, Revision, Sha256Digest
from local_ports import (CommandCwdRule, CommandDefinition, CommandPlatform, CommandRequest,
    CommandRootBindings, CommandRunner, CommandSuccessRule, ContentRef, EnvironmentBinding,
    LocalControlBinding, LocalProjectBinding, LocalWorktreeBinding, PermissionClass)
from workflow_ports import ValidationCheck, ValidationStatus, ValidationSuccessRule


def wire(value):
    if isinstance(value, (EntityId, PlanId, Revision, Sha256Digest)):
        return value.value
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if dataclasses.is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [wire(x) for x in value]
    return value


class Clock:
    def __init__(self):
        self.value = datetime(2026, 9, 8, 13, 0, tzinfo=timezone.utc)

    def now(self):
        self.value += timedelta(milliseconds=1)
        return self.value


class Ids:
    def __init__(self):
        self.plans = []

    def new(self, kind, plan_id=None):
        self.plans.append(plan_id)
        return EntityId('R2-C2-' + str(len(self.plans)))


class CrossContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ContractRegistry(TREE / 'schemas/v1')
        cls.source = load_project_settings(TREE, load_installation_record(TREE))
        for name in ('commands', 'config', 'contracts', 'domain_values', 'local_ports', 'workflow_ports'):
            origin = Path(importlib.import_module(name).__file__).resolve()
            assert origin.parent == TREE / 'src', origin
        print(json.dumps({'case': 'runtime', 'python': platform.python_version(), 'platform': sys.platform,
                          'candidate_src': str(TREE / 'src'), 'all_six_origins_verified': True}), flush=True)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='task006-r2-')
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve()
        self.task = self.project / '.worktrees/task'
        self.control = self.project / '.worktrees/control'
        for directory in (self.project, self.task, self.control):
            (directory / 'nested space').mkdir(parents=True)
        self.settings = dataclasses.replace(self.source, project_root=self.project)
        self.roots = CommandRootBindings(LocalProjectBinding('R2-PROJECT', self.project),
            LocalWorktreeBinding('R2-PROJECT', 'R2-TASK', self.task),
            LocalControlBinding('R2-PROJECT', 'R2-CONTROL', self.control))
        self.ids = Ids()
        self.store = FileCommandLogStore(self.project, 'portable/logs')
        self.base = {'PATH': str(Path(sys.executable).parent)}
        if os.name == 'nt':
            self.base['SystemRoot'] = os.environ['SystemRoot']

    def runner(self, **changes):
        values = dict(project_settings=self.settings, run_settings=self.settings.resolve_run(),
            allowed_permissions=[PermissionClass.LOCAL_EXECUTE], id_factory=self.ids,
            clock=Clock(), log_store=self.store, base_environment=self.base)
        values.update(changes)
        runner = LocalCommandRunner(**values)
        self.assertIsInstance(runner, CommandRunner)
        return runner

    def request(self, code, *, arguments=(), rule=CommandCwdRule.PROJECT, plan=None,
                relative='.', environment=(), permission=PermissionClass.LOCAL_EXECUTE,
                success=CommandSuccessRule.EXIT_ZERO, cap=65536, timeout=10):
        definition = CommandDefinition('test.r2', (str(sys.executable), '-B', '-c', code, *arguments),
            rule, timeout, cap, permission, tuple(b.name for b in environment),
            (CommandPlatform.LINUX, CommandPlatform.WINDOWS), success)
        self.registry.validate(wire(definition))
        return CommandRequest('R2-PROJECT', plan, 'R2-RUN', 'R2-OP', definition,
                              self.roots, relative, environment)

    def log(self, ref):
        self.assertIsInstance(ref, ContentRef)
        value = (self.project / ref.path).read_bytes()
        self.assertEqual(hashlib.sha256(value).hexdigest(), ref.sha256.value)
        return value

    def evidence(self, value):
        payload = wire(value)
        self.registry.validate(payload, source='R2 observed command evidence')
        self.assertEqual(set(payload), set(self.registry.schema('command-evidence')['required']))
        with self.assertRaises(Exception):
            self.registry.validate({**payload, 'assumed_success': True})
        return payload

    def test_01_saved_snapshot_and_permission_authority_remain_separate(self):
        overrides = RunOverrides(max_agent_invocations=1, max_rewrites=0, required_sandbox=True)
        payload = json.loads(json.dumps(self.settings.resolve_run(overrides).to_payload()))
        saved = decode_run_settings(payload)
        self.registry.validate(self.settings.effective_policy(overrides).to_wire())
        payload['required_sandbox'] = False
        changed = dataclasses.replace(self.settings, policy=dataclasses.replace(
            self.settings.policy, required_sandbox=False, max_agent_invocations=299))
        self.assertIs(changed.resolve_run(saved=saved), saved)
        self.assertTrue(saved.required_sandbox)
        self.assertEqual(saved.max_agent_invocations, 1)
        self.assertEqual(saved.max_rewrites, 0)
        self.assertIsNone(changed.configured_model('review_high'))
        with self.assertRaises(Exception):
            changed.resolve_run(RunOverrides(), saved=saved)
        marker = self.project / 'should-not-launch'
        request = self.request("from pathlib import Path; Path('should-not-launch').touch()")
        sandbox = self.runner(project_settings=changed, run_settings=changed.resolve_run(saved=saved)).execute(request)
        self.assertEqual((sandbox.status, sandbox.error_category), (CommandStatus.LAUNCH_FAILED, 'unsupported_capability'))
        permissions = []
        deny_runner = self.runner(allowed_permissions=permissions)
        permissions.append(PermissionClass.LOCAL_EXECUTE)
        denied = deny_runner.execute(request)
        self.assertEqual((denied.status, denied.error_category), (CommandStatus.LAUNCH_FAILED, 'policy_denied'))
        self.assertFalse(marker.exists())
        self.evidence(sandbox); self.evidence(denied)
        print(json.dumps({'case': 'saved_snapshot_and_permissions', 'saved_sandbox': True,
            'policy_change_did_not_replace_saved': True, 'caller_permission_mutation_did_not_grant': True,
            'automatic_profile_still_unconfigured': True}), flush=True)

    def test_02_payload_argv_zero_plan_and_three_nested_cwd_bindings(self):
        arguments = (' leading ', 'line1\nline2', 'tab\tvalue', 'same', 'same', '&& echo literal', '$(literal)')
        code = 'import json,sys; from pathlib import Path; print(json.dumps([sys.argv[1:], Path.cwd().parent.name]))'
        records = []
        for rule, binding, parent, plan in ((CommandCwdRule.PROJECT, 'R2-PROJECT', self.project.name, None),
            (CommandCwdRule.WORKTREE, 'R2-TASK', 'task', 'PLAN-001'),
            (CommandCwdRule.CONTROL, 'R2-CONTROL', 'control', None)):
            request = self.request(code, arguments=arguments, rule=rule, plan=plan, relative='nested space/')
            value = self.runner().execute(request)
            self.assertEqual((value.status, value.exit_code), (CommandStatus.EXITED, 0))
            self.assertEqual(value.argv_redacted, request.definition.argv)
            self.assertEqual(json.loads(self.log(value.stdout_ref)), [list(arguments), parent])
            self.assertEqual(value.cwd_worktree_id, EntityId(binding))
            self.assertEqual(value.cwd_relative, 'nested space')
            self.evidence(value)
            records.append([rule.value, wire(self.ids.plans[-1]), binding])
        print(json.dumps({'case': 'argv_and_cwd', 'significant_arguments': len(arguments), 'bindings': records}), flush=True)

    def test_03_environment_detached_and_bounded_sanitized_logs_relocatable(self):
        self.base['APPROVED'] = 'before'
        runner = self.runner()
        self.base['APPROVED'] = 'after'
        secret = 'R2-Secret-654321'
        host_key = 'R2_UNAPPROVED_AMBIENT'
        previous = os.environ.get(host_key)
        os.environ[host_key] = 'must-not-enter-child'
        def restore():
            if previous is None:
                os.environ.pop(host_key, None)
            else:
                os.environ[host_key] = previous
        self.addCleanup(restore)
        code = "import os; print(os.environ['APPROVED'],os.environ.get('R2_UNAPPROVED_AMBIENT','absent'),repr(os.environ['EMPTY']),flush=True); os.write(1,os.environ['TOKEN'].encode()*2000); os.write(2,b'err'*5000)"
        value = runner.execute(self.request(code, cap=180, environment=(EnvironmentBinding('TOKEN', secret), EnvironmentBinding('EMPTY', ''))))
        self.assertEqual((value.status, value.exit_code), (CommandStatus.EXITED, 0))
        logs = [self.log(value.stdout_ref), self.log(value.stderr_ref)]
        self.assertIn(b"before absent ''", logs[0])
        self.assertNotIn(secret.encode(), b''.join(logs))
        self.assertLessEqual(sum(map(len, logs)), 180)
        self.assertTrue(value.redactions_applied and value.output_truncated)
        payload = self.evidence(value)
        self.assertEqual(payload['environment_binding_names'], ['TOKEN', 'EMPTY'])
        with tempfile.TemporaryDirectory(prefix='r2-relocated-') as destination:
            for ref in (value.stdout_ref, value.stderr_ref):
                target = Path(destination) / ref.path
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(self.project / ref.path, target)
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), ref.sha256.value)
        print(json.dumps({'case': 'detached_environment_and_portable_logs', 'bytes': list(map(len, logs)),
            'redacted': value.redactions_applied, 'truncated': value.output_truncated,
            'relocated_refs_hash_verified': True}), flush=True)

    def test_04_partial_durable_failure_retains_only_proven_reference(self):
        store = self.store
        class PartialStore:
            def write(self, evidence_id, stream, content):
                if stream == 'stderr':
                    raise OSError('synthetic durable stderr failure')
                return store.write(evidence_id, stream, content)
        value = self.runner(log_store=PartialStore()).execute(self.request("print('retained-before-storage-failure')"))
        self.assertEqual((value.status, value.exit_code, value.error_category), (CommandStatus.UNKNOWN, None, 'internal_error'))
        self.assertEqual(self.log(value.stdout_ref).strip(), b'retained-before-storage-failure')
        self.assertIsNone(value.stderr_ref)
        self.evidence(value)
        print(json.dumps({'case': 'partial_durable_failure', 'status': value.status.value,
            'stdout_sha256': value.stdout_ref.sha256.value, 'stderr_ref': None, 'exit_code': None}), flush=True)

    def test_05_real_zero_test_run_is_process_fact_not_validation_pass(self):
        code = 'import unittest; unittest.TextTestRunner().run(unittest.TestSuite())'
        value = self.runner().execute(self.request(code, success=CommandSuccessRule.UNITTEST_NONZERO_COUNT))
        self.assertEqual((value.status, value.exit_code), (CommandStatus.EXITED, 0))
        self.assertIn(b'Ran 0 tests', self.log(value.stderr_ref))
        payload = self.evidence(value)
        reference = EvidenceRef('evidence/observed-command.json', hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest())
        with self.assertRaisesRegex(ValueError, 'positive test count'):
            ValidationCheck('test.r2', ValidationSuccessRule.UNITTEST_NONZERO_COUNT, ValidationStatus.PASSED, reference, 0)
        nonzero = self.runner().execute(self.request('raise SystemExit(9)'))
        self.assertEqual((nonzero.status, nonzero.exit_code, nonzero.error_category), (CommandStatus.EXITED, 9, None))
        self.evidence(nonzero)
        print(json.dumps({'case': 'success_rule_owner_boundary', 'real_empty_suite_exit': value.exit_code,
            'real_observed_tests': 0, 'accepted_validation_dto_rejects_zero_count_pass': True,
            'nonzero_exit_preserved': nonzero.exit_code, 'TASK018_service_not_claimed': True}), flush=True)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CrossContractTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    active = [t.name for t in threading.enumerate() if t.name.startswith('command-')]
    print(json.dumps({'case': 'completion', 'tests': result.testsRun, 'skips': len(result.skipped),
        'successful': result.wasSuccessful(), 'active_command_reader_threads': active}), flush=True)
    raise SystemExit(0 if result.wasSuccessful() and not active else 1)
