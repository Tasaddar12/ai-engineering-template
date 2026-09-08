"""Independent R2 cross-contract probes; all fixtures are temporary projects."""
import dataclasses
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

sys.dont_write_bytecode = True
TREE = Path.cwd().resolve()
sys.path.insert(0, str(TREE / 'src'))
from commands import LocalCommandRunner, FileCommandLogStore
from config import RunSettings, decode_run_settings, load_installation_record, load_project_settings
from contracts import ContractRegistry
from domain_values import CommandStatus, EntityId, PlanId, Revision, Sha256Digest, EvidenceRef
from local_ports import CommandDefinition, CommandRequest, CommandRootBindings, LocalProjectBinding, LocalWorktreeBinding, LocalControlBinding, CommandRunner, EnvironmentBinding
from workflow_ports import ValidationCheck

def wire(value):
    if isinstance(value, (EntityId, PlanId, Revision, Sha256Digest)):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if dataclasses.is_dataclass(value):
        return {field.name: wire(getattr(value, field.name)) for field in dataclasses.fields(value)}
    if isinstance(value, tuple):
        return [wire(x) for x in value]
    return value

class Clock:
    def now(self):
        return datetime.now(timezone.utc)

class Ids:
    def __init__(self):
        self.count = 0
    def new(self, kind, plan_id=None):
        self.count += 1
        return EntityId(f'{kind}-{self.count}')

class ConsistencyProbes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_settings = load_project_settings(TREE, load_installation_record(TREE))
        cls.registry = ContractRegistry(TREE / 'schemas/v1')

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='task006-r2-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.worktree = self.root / '.worktrees/task'
        self.control = self.root / '.worktrees/control'
        for path in (self.root, self.worktree, self.control):
            (path / 'nested').mkdir(parents=True, exist_ok=True)
        self.settings = dataclasses.replace(self.source_settings, project_root=self.root)
        self.roots = CommandRootBindings(LocalProjectBinding('project', self.root), LocalWorktreeBinding('project', 'WT-TASK', self.worktree), LocalControlBinding('project', 'WT-CONTROL', self.control))
        self.ids = Ids()
        self.store = FileCommandLogStore(self.root, 'evidence/logs')

    def definition(self, argv, **options):
        values = dict(id='test.independent', argv=argv, cwd_rule='worktree', timeout_seconds=10, max_output_bytes=1048576, permission_class='local_execute', environment_bindings=(), platforms=('windows', 'linux'), success_rule='exit_zero')
        values.update(options)
        return CommandDefinition(**values)

    def request(self, definition, **options):
        values = dict(project_id='project', plan_id=None, run_id='RUN-001', operation_id='OP-001', definition=definition, roots=self.roots, cwd_relative='.')
        values.update(options)
        return CommandRequest(**values)

    def runner(self, **options):
        base = {'SystemRoot': os.environ['SystemRoot']} if os.name == 'nt' else {}
        values = dict(project_settings=self.settings, run_settings=RunSettings(), allowed_permissions=('local_execute',), id_factory=self.ids, clock=Clock(), log_store=self.store, base_environment=base)
        values.update(options)
        runner = LocalCommandRunner(**values)
        self.assertIsInstance(runner, CommandRunner)
        return runner

    def content(self, ref, root=None):
        self.assertIsNotNone(ref)
        content = ((self.root if root is None else root) / ref.path).read_bytes()
        self.assertEqual(hashlib.sha256(content).hexdigest(), ref.sha256.value)
        return content

    def validate(self, evidence):
        payload = wire(evidence)
        self.registry.validate(payload)
        self.assertEqual(set(payload), set(self.registry.schema('command-evidence')['properties']))

    def test_all_cwd_bindings_preserve_literal_argv_and_zero_plan(self):
        literals = (' leading ', 'line\none', 'tab\tvalue', 'repeat', 'repeat', '; $(echo unsafe)', '--option-as-data')
        code = 'import json,os,sys; print(json.dumps([os.getcwd(),sys.argv[1:]],ensure_ascii=False))'
        for rule, path, identity in [('project', self.root, 'project'), ('worktree', self.worktree, 'WT-TASK'), ('control', self.control, 'WT-CONTROL')]:
            with self.subTest(rule=rule):
                definition = self.definition((sys.executable, '-c', code, *literals), cwd_rule=rule)
                evidence = self.runner().execute(self.request(definition, cwd_relative='nested'))
                self.assertEqual((evidence.status, evidence.exit_code), (CommandStatus.EXITED, 0))
                cwd, observed = json.loads(self.content(evidence.stdout_ref))
                self.assertEqual(Path(cwd), path / 'nested')
                self.assertEqual(observed, list(literals))
                self.assertEqual(evidence.argv_redacted, definition.argv)
                self.assertEqual(evidence.cwd_worktree_id.value, identity)
                self.validate(evidence)
        print('PROBE literal argv / project-worktree-control cwd / zero-plan: pass')

    def test_saved_settings_permissions_and_environment_remain_distinct(self):
        payload = RunSettings(required_sandbox=True, max_parallel=1).to_payload()
        saved = decode_run_settings(payload)
        payload['required_sandbox'] = False
        resolved = self.settings.resolve_run(saved=saved)
        self.assertIs(resolved, saved)
        self.assertTrue(resolved.required_sandbox)
        marker = self.worktree / 'launched'
        definition = self.definition((sys.executable, '-c', 'from pathlib import Path; Path("launched").write_text("yes")'))
        sandbox = self.runner(run_settings=resolved).execute(self.request(definition))
        denied = self.runner(allowed_permissions=()).execute(self.request(definition))
        self.assertEqual((sandbox.status, sandbox.error_category), (CommandStatus.LAUNCH_FAILED, 'unsupported_capability'))
        self.assertEqual((denied.status, denied.error_category), (CommandStatus.LAUNCH_FAILED, 'policy_denied'))
        self.assertFalse(marker.exists())
        self.validate(sandbox)
        self.validate(denied)
        ambient_name = 'TASK006_R2_AMBIENT_ONLY'
        old = os.environ.get(ambient_name)
        os.environ[ambient_name] = 'ambient-private'
        self.addCleanup(lambda: os.environ.pop(ambient_name, None) if old is None else os.environ.__setitem__(ambient_name, old))
        base = {'BASE_VALUE': 'original'}
        if os.name == 'nt':
            base['SystemRoot'] = os.environ['SystemRoot']
        runner = self.runner(base_environment=base)
        base['BASE_VALUE'] = 'changed'
        code = 'import json,os; print(json.dumps([os.getenv("BASE_VALUE"),os.getenv("EMPTY"),os.getenv("TASK006_R2_AMBIENT_ONLY")]))'
        definition = self.definition((sys.executable, '-c', code), environment_bindings=('EMPTY',))
        evidence = runner.execute(self.request(definition, environment=(EnvironmentBinding('EMPTY', ''),)))
        self.assertEqual(json.loads(self.content(evidence.stdout_ref)), ['original', '', None])
        self.assertEqual(evidence.environment_binding_names, ('EMPTY',))
        self.validate(evidence)
        print('PROBE saved snapshot / deny-all / required sandbox / detached explicit environment: pass')

    def test_process_facts_leave_nonzero_count_to_validation_owner(self):
        code = 'import unittest; result=unittest.TextTestRunner().run(unittest.TestSuite()); raise SystemExit(not result.wasSuccessful())'
        definition = self.definition((sys.executable, '-c', code), success_rule='unittest_nonzero_count')
        evidence = self.runner().execute(self.request(definition))
        self.assertEqual((evidence.status, evidence.exit_code), (CommandStatus.EXITED, 0))
        self.assertIn(b'Ran 0 tests', self.content(evidence.stderr_ref))
        self.validate(evidence)
        actual_ref = EvidenceRef(evidence.stderr_ref.path, evidence.stderr_ref.sha256)
        with self.assertRaisesRegex(ValueError, 'positive test count'):
            ValidationCheck(evidence.command_id, 'unittest_nonzero_count', 'passed', actual_ref, observed_test_count=0)
        nonzero = self.runner().execute(self.request(self.definition((sys.executable, '-c', 'raise SystemExit(9)'))))
        self.assertEqual((nonzero.status, nonzero.exit_code), (CommandStatus.EXITED, 9))
        self.validate(nonzero)
        print('PROBE actual zero-test exit / observed exit9 / accepted ValidationCheck rejection: pass')

    def test_trusted_git_argv_is_consumable_without_git_service_duplication(self):
        git = shutil.which('git')
        self.assertIsNotNone(git)
        runner = self.runner()
        init = runner.execute(self.request(self.definition((git, 'init', '--quiet'))))
        self.assertEqual((init.status, init.exit_code), (CommandStatus.EXITED, 0))
        literal = ' --literal ; $(ignored).txt'
        (self.worktree / literal).write_text('data', encoding='utf-8')
        request = self.request(self.definition((git, 'ls-files', '-z', '--others', '--exclude-standard', '--', literal)))
        observed = runner.execute(request)
        self.assertEqual((observed.status, observed.exit_code), (CommandStatus.EXITED, 0))
        self.assertEqual(self.content(observed.stdout_ref), literal.encode() + b'\x00')
        self.assertEqual(observed.argv_redacted, request.definition.argv)
        missing = runner.execute(self.request(self.definition((git, 'rev-parse', '--verify', 'refs/heads/absent'))))
        self.assertEqual((missing.status, missing.exit_code), (CommandStatus.EXITED, 128))
        for evidence in (init, observed, missing):
            self.validate(evidence)
        print('PROBE real Git consumer with literal path / missing ref exit128: pass')

    def test_sanitized_shared_budget_hashes_relocation_and_partial_storage(self):
        secret = 'r2-Private-Value'
        code = 'import os,sys; value=os.environ["SECRET"]; sys.stdout.write(value+"X"*10000); sys.stdout.flush(); sys.stderr.write(value+"Y"*10000)'
        definition = self.definition((sys.executable, '-c', code, secret), environment_bindings=('SECRET',), max_output_bytes=73)
        evidence = self.runner().execute(self.request(definition, environment=(EnvironmentBinding('SECRET', secret),)))
        self.assertEqual((evidence.status, evidence.exit_code), (CommandStatus.EXITED, 0))
        combined = self.content(evidence.stdout_ref) + self.content(evidence.stderr_ref)
        self.assertLessEqual(len(combined), 73)
        self.assertNotIn(secret.encode(), combined)
        self.assertNotIn(secret, json.dumps(wire(evidence)))
        self.assertTrue(evidence.redactions_applied)
        self.assertTrue(evidence.output_truncated)
        self.validate(evidence)
        relocated = self.root / 'relocated'
        shutil.copytree(self.root / 'evidence', relocated / 'evidence')
        self.assertEqual(self.content(evidence.stdout_ref, relocated) + self.content(evidence.stderr_ref, relocated), combined)
        store = self.store
        class PartialStore:
            def write(self, evidence_id, stream, content):
                if stream == 'stderr':
                    raise OSError('independent second-stream failure')
                return store.write(evidence_id, stream, content)
        partial = self.runner(log_store=PartialStore()).execute(self.request(self.definition((sys.executable, '-c', 'print("persisted")'))))
        self.assertEqual((partial.status, partial.exit_code, partial.error_category), (CommandStatus.UNKNOWN, None, 'internal_error'))
        self.assertIsNone(partial.stderr_ref)
        self.assertEqual(self.content(partial.stdout_ref).strip(), b'persisted')
        self.validate(partial)
        print('PROBE shared redacted budget / durable relocated hashes / honest partial storage: pass')

if __name__ == '__main__':
    print('Python:', sys.version, 'Executable:', sys.executable, 'Platform:', platform.platform(), flush=True)
    print('jsonschema:', importlib.metadata.version('jsonschema'), flush=True)
    for name in ('commands', 'config', 'contracts', 'domain_values', 'local_ports', 'workflow_ports'):
        module = importlib.import_module(name)
        assert Path(module.__file__).resolve() == TREE / 'src' / (name + '.py')
        print('Origin:', name, module.__file__, flush=True)
    unittest.main(verbosity=2)
