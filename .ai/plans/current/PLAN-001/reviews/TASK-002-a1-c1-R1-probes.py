"""Independent read-only R1 boundary checks; candidate source is never edited."""
import dataclasses as dc
import hashlib
import inspect
import json
import subprocess
import sys
import unittest
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import get_type_hints

ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-002-a1'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'src'))
import contracts
import domain_values as dv
import local_ports as p

NOW = datetime(2026, 9, 8, 12, tzinfo=timezone.utc)
A, B = 'a' * 40, 'b' * 64
E = dv.EvidenceRef(dv.ScopePath.exact_file('evidence/observed.txt'), dv.Sha256Digest('d' * 64))
PROJECT = p.LocalProjectBinding('project', WT)
WORKTREE = p.LocalWorktreeBinding('project', 'WT-1', WT / '.worktrees/WT-1')
CONTROL = p.LocalControlBinding('project', 'CONTROL', WT / '.worktrees/control')
REGISTRY = contracts.ContractRegistry(WT / 'schemas/v1')

def wire(value):
    if isinstance(value, (dv.EntityId, dv.PlanId, dv.Revision, dv.Sha256Digest)):
        return value.value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if dc.is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in dc.fields(value)}
    if isinstance(value, tuple):
        return [wire(v) for v in value]
    return value

def err(category):
    return dv.DomainError(category, 'independently observed failure')

def definition(argv=('python', '-m', 'unittest'), rule='project', names=()):
    return p.CommandDefinition('test.example', argv, rule, 5, 2048, 'local_execute', names, ('windows', 'linux'), 'exit_zero')

def command_evidence(argv=('python',), status='exited', exit_code=0, finish=NOW, category=None):
    return p.CommandEvidence('CMD-1', 'test.example', argv, 'project', '.', NOW, finish, exit_code, status, None, None, False, False, (), category)

def record(**changes):
    base = p.WorktreeRecord('WT-1', 'TASK-002', 'RUN-1', 'TASK-002-a1', 'task', 'ai/PLAN-001/TASK-002/a1', '.worktrees/WT-1', A, None, 'planned', None, None, ())
    return dc.replace(base, **changes)

def git(*args):
    return subprocess.check_output(['git', *args], cwd=WT)

def verify_identity():
    candidate = json.loads((ROOT / '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-002-a1-f38680d2d892.json').read_bytes())
    sha = lambda value: hashlib.sha256(value).hexdigest()
    assert git('rev-parse', 'HEAD').decode().strip() == candidate['head_oid']
    assert git('status', '--porcelain=v1') == b''
    assert sha(git('diff', '--binary', candidate['base_oid'], candidate['head_oid'])) == candidate['diff_sha256']
    for ref in candidate['context_refs']:
        assert sha(git('show', candidate['head_oid'] + ':' + ref['path'])) == ref['sha256'], ref['path']
    for ref in candidate['validation_refs']:
        assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref['path']
    assert sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()) == candidate['policy_model_digest']
    assert sha(json.dumps({k: v for k, v in candidate.items() if k != 'fingerprint'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == candidate['fingerprint']
    plan = WT / '.ai/plans/current/PLAN-001'
    tasks = [json.loads(f.read_bytes()) for bucket in ('current', 'completed', 'archived') for f in (plan / 'tasks' / bucket).glob('TASK-*.json')]
    graph = json.loads((plan / 'graph.json').read_bytes())
    isolation = json.loads((plan / 'reviews/r4-isolation-review.json').read_bytes())
    assert contracts.structural_task_digest(tasks) == graph['task_set_sha256'] == isolation['task_set_sha256']
    assert sha(json.dumps({k: graph[k] for k in ('schema_version', 'kind', 'id', 'plan_id', 'revision', 'nodes', 'task_set_sha256')}, sort_keys=True, separators=(',', ':')).encode()) == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
    for dep, report in [('d1fc917466410febc6238479e65816dd39591a4f', 'TASK-001-a2-c2-R2.json'), ('1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518', 'TASK-004-a2-c3-R2.json')]:
        subprocess.run(['git', 'merge-base', '--is-ancestor', dep, candidate['base_oid']], cwd=WT, check=True)
        assert json.loads((plan / 'reviews' / report).read_bytes())['verdict'] == 'pass'
    assert {task['id']: task['status'] for task in tasks}['TASK-001'] == 'accepted'
    assert {task['id']: task['status'] for task in tasks}['TASK-004'] == 'accepted'
    print(json.dumps({'candidate': candidate['id'], 'head': candidate['head_oid'], 'base': candidate['base_oid'], 'fingerprint': candidate['fingerprint'], 'diff_sha256': candidate['diff_sha256'], 'context_hashes': len(candidate['context_refs']), 'validation_hashes': len(candidate['validation_refs']), 'policy_model_digest': candidate['policy_model_digest'], 'structural_task_digest': graph['task_set_sha256'], 'graph_revision': graph['revision'], 'isolation': isolation['verdict'], 'accepted_dependencies': 'TASK-001 and TASK-004 accepted, passing R2, both integrated into base', 'changed_paths': git('diff', '--name-status', candidate['base_oid'], candidate['head_oid']).decode().splitlines(), 'imports': {m.__name__: m.__file__ for m in (contracts, dv, p)}}, indent=2), flush=True)

class BoundaryTests(unittest.TestCase):
    def test_01_exact_protocol_annotations(self):
        expected = [(p.StateStore, 'read', 'ref', dv.RecordRef, p.VersionedRecord), (p.StateStore, 'transact', 'request', p.TransactionRequest, p.TransactionResult), (p.CommandRunner, 'execute', 'request', p.CommandRequest, p.CommandEvidence), (p.GitRepository, 'inspect', 'request', p.GitInspectRequest, p.GitSnapshot), (p.GitRepository, 'create_branch', 'request', p.BranchRequest, p.GitOperationResult), (p.GitRepository, 'merge', 'request', p.MergeRequest, p.GitOperationResult), (p.WorktreeManager, 'ensure', 'request', p.WorktreeRequest, p.WorktreeResult), (p.WorktreeManager, 'reconcile', 'request', p.ReconcileRequest, p.ReconcileReport), (p.WorktreeManager, 'cleanup', 'request', p.CleanupRequest, p.WorktreeResult)]
        for owner, name, param, request, result in expected:
            method = getattr(owner, name)
            self.assertEqual(list(inspect.signature(method).parameters), ['self', param])
            self.assertEqual(get_type_hints(method), {param: request, 'return': result})
        self.assertEqual(get_type_hints(p.Clock.now), {'return': datetime})
        self.assertEqual(get_type_hints(p.IdFactory.new), {'kind': str, 'plan_id': dv.PlanId | None, 'return': dv.EntityId})
        self.assertIsNone(inspect.signature(p.IdFactory.new).parameters['plan_id'].default)

    def test_02_schema_fieldsets_and_zero_plan_event(self):
        event = p.StateEvent('EVENT-1', 'OP-1', 1, 'project', 'initialized', None, 'foundation', (), NOW, None)
        for value in (event, definition(), command_evidence(), record()):
            payload = wire(value)
            REGISTRY.validate(payload)
            self.assertEqual(set(payload), set(REGISTRY.schema(payload['kind'])['properties']))
        self.assertIsInstance(event.entity_id, dv.EntityId)
        self.assertNotIn('plan_id', wire(event))
        intent = p.OperationIntent('OP-1', 'git_branch', 'idem', 'refs/heads/new', 'intent', ())
        self.assertEqual(set(wire(intent)), set(REGISTRY.schema('workflow-run')['properties']['pending_operations']['items']['properties']))
        with self.assertRaises(dc.FrozenInstanceError):
            event.entity_id = dv.EntityId('changed')

    def test_03_qualified_reads_atomic_relocation_and_detachment(self):
        first = dv.RecordRef('task', 'TASK-002', 'PLAN-001')
        second = dv.RecordRef('task', 'TASK-002', 'PLAN-002')
        self.assertNotEqual(first, second)
        with self.assertRaises(ValueError):
            dv.RecordRef('task', 'TASK-002')
        self.assertIsNone(p.VersionedRecord(first, 'missing', 3, None).record)
        source = {'kind': 'task', 'nested': ['original']}
        ref = p.ReferenceUpdate(dv.RecordRef('project-state', 'project'), ['active_plans', '0'], ['PLAN-001'], [])
        manifest = p.ManifestEffect(dv.RecordRef('archive-manifest', 'ARCHIVE-1', 'PLAN-001'), 'add', 'tasks/completed/TASK-002.json', 'c' * 64)
        projection = p.ProjectionUpdate(first, source, 'plans/current/PLAN-001/', 'plans/completed/PLAN-001/', [ref], [manifest])
        event = p.StateEvent('EVENT-2', 'OP-1', 4, 'TASK-002', 'completed', 'accepted', 'completed', (), NOW, None)
        tx = p.TransactionRequest('project', 'RUN-1', 3, 'OP-1', [event], [projection])
        source['nested'].append('changed')
        self.assertEqual(tx.projection_updates[0].record['nested'], ('original',))
        self.assertEqual(len(tx.projection_updates[0].manifest_effects), 1)
        self.assertEqual(tx.events[0].generation.value, tx.expected_generation.value + 1)
        for changes in ({'expected_generation': 4}, {'operation_id': 'OP-2'}, {'events': [event, event]}, {'projection_updates': [projection, projection]}):
            with self.assertRaises(ValueError):
                dc.replace(tx, **changes)

    def test_04_transaction_evidence_and_errors(self):
        commit = p.TransactionResult('committed', 'OP-1', 4, A, (E,))
        for changes in ({'checkpoint_oid': None}, {'evidence_refs': ()}, {'error': err(dv.ErrorCategory.INTERNAL_ERROR)}):
            with self.assertRaises(ValueError):
                dc.replace(commit, **changes)
        for status, category in [('conflict', dv.ErrorCategory.STATE_CONFLICT), ('unknown', dv.ErrorCategory.AMBIGUOUS_SIDE_EFFECT), ('failed', dv.ErrorCategory.INTERNAL_ERROR)]:
            result = p.TransactionResult(status, 'OP-1', 3, None, (), err(category))
            with self.assertRaises(ValueError):
                dc.replace(result, checkpoint_oid=A)

    def test_05_command_bindings_environment_and_cwd(self):
        roots = p.CommandRootBindings(PROJECT, WORKTREE, CONTROL)
        for rule, binding in [('project', PROJECT), ('worktree', WORKTREE), ('control', CONTROL)]:
            request = p.CommandRequest('project', None, 'RUN-1', 'OP-1', definition(rule=rule, names=('TOKEN',)), roots, '.', (p.EnvironmentBinding('TOKEN', 'private-value'),))
            self.assertEqual(request.cwd_binding, binding)
            self.assertNotIn('private-value', repr(request))
            for relative in ('../outside', '/outside', 'D:/outside'):
                with self.assertRaises(ValueError):
                    dc.replace(request, cwd_relative=relative)
            with self.assertRaises(ValueError):
                dc.replace(request, environment=(p.EnvironmentBinding('UNLISTED', 'x'),))
        with self.assertRaises(ValueError):
            p.CommandRequest('project', None, 'RUN-1', 'OP-1', definition(rule='worktree'), p.CommandRootBindings(PROJECT), '.')

    def test_06_all_command_observation_states(self):
        for status, code, finish, category in [('launch_failed', None, NOW, 'launch_failure'), ('running', None, None, None), ('exited', 1, NOW, None), ('timed_out', 124, NOW, 'timeout'), ('cancelled', -15, NOW, 'cancelled'), ('unknown', None, None, 'process_state_unknown')]:
            result = command_evidence(status=status, exit_code=code, finish=finish, category=category)
            REGISTRY.validate(wire(result))
            self.assertEqual(result.exit_code, code)
        with self.assertRaises(ValueError):
            command_evidence(status='unknown', exit_code=0, finish=None, category='process_state_unknown')

    def test_07_actual_git_facts_and_unborn_representability(self):
        head = git('rev-parse', 'HEAD').decode().strip()
        base = '91bf184a7b65d300996970758ba516917cbc5a77'
        branch = git('symbolic-ref', 'HEAD').decode().strip()
        missing = 'refs/heads/reviewer-TASK-002-c1-nonexistent'
        self.assertNotEqual(subprocess.run(['git', 'show-ref', '--verify', '--quiet', missing], cwd=WT).returncode, 0)
        self.assertEqual(p.GitHead('attached', branch, head).oid, head)
        refs = (p.GitRefObservation(branch, 'present', head), p.GitRefObservation(missing, 'missing', None))
        actual_ancestry = []
        for ancestor, descendant, expected in [(base, head, 'ancestor'), (head, base, 'not_ancestor')]:
            code = subprocess.run(['git', 'merge-base', '--is-ancestor', ancestor, descendant], cwd=WT).returncode
            self.assertIn(code, (0, 1))
            fact = p.AncestryObservation(p.AncestryQuery(ancestor, descendant), 'ancestor' if code == 0 else 'not_ancestor')
            self.assertEqual(fact.status.value, expected)
            actual_ancestry.append(fact)
        snapshot = p.GitSnapshot('succeeded', 'project', 'RUN-1', PROJECT, p.GitHead('attached', branch, head), refs, actual_ancestry, (), p.GitStatus(), NOW, (E,))
        self.assertEqual(snapshot.refs[1].status.value, 'missing')
        for status, name, oid in [('unborn', 'main', None), ('missing', None, None), ('detached', None, head)]:
            self.assertEqual(p.GitHead(status, name, oid).status.value, status)
        for status in ('missing', 'unknown'):
            self.assertEqual(p.AncestryObservation(p.AncestryQuery(A, B), status).status.value, status)

    def test_08_git_effect_expectations_and_ambiguity(self):
        branch = p.BranchRequest('project', None, 'RUN-1', 'OP-1', 'idem', PROJECT, 'new', 'HEAD', A, p.GitRefExpectation('refs/heads/new', 'missing'))
        with self.assertRaises(ValueError):
            dc.replace(branch, branch='--delete')
        with self.assertRaises(ValueError):
            dc.replace(branch, expected_branch=p.GitRefExpectation('refs/heads/other', 'missing'))
        unknown = p.GitOperationResult('unknown', 'OP-1', 'idem', None, None, (), (), (), err(dv.ErrorCategory.AMBIGUOUS_SIDE_EFFECT))
        for changes in ({'changed': False}, {'error': err(dv.ErrorCategory.GIT_CONFLICT)}):
            with self.assertRaises(ValueError):
                dc.replace(unknown, **changes)
        merge = p.MergeRequest('project', 'PLAN-001', 'RUN-1', 'OP-2', 'merge-idem', PROJECT, 'integration', A, 'refs/heads/new', B)
        self.assertEqual(merge.candidate_oid, B)

    def test_09_worktree_ensure_control_and_binding_guards(self):
        task = record()
        request = p.WorktreeRequest('project', 'PLAN-001', 'RUN-1', 'OP-1', 'idem', PROJECT, task, WORKTREE, p.GitRefExpectation('refs/heads/' + task.branch, 'missing'))
        with self.assertRaises(ValueError):
            dc.replace(request, plan_id=None)
        with self.assertRaises(ValueError):
            dc.replace(request, binding=dc.replace(WORKTREE, root=WT / 'different'))
        control = dc.replace(task, id='CONTROL', task_id=None, role='control', branch='ai/state', location_hint='.worktrees/control')
        control_request = p.WorktreeRequest('project', None, 'RUN-1', 'OP-2', 'control-idem', PROJECT, control, CONTROL, p.GitRefExpectation('refs/heads/ai/state', 'present', A))
        self.assertIsNone(control_request.plan_id)

    def test_10_reconciliation_and_cleanup_are_guarded_requests(self):
        unknown_lease = p.LeaseObservation('LEASE-1', 'RUN-1', 'TASK-002-a1', 2, 'unknown', None)
        self.assertIsNone(unknown_lease.process_alive)
        unmanaged = p.WorktreeObservation(None, WT / '.worktrees/unknown', False, False, True, None, None, None, p.GitStatus(untracked_paths=('untracked.txt',)), None, None, None, 'unknown', False)
        missing = p.WorktreeObservation('WT-1', WORKTREE.root, True, True, False, None, None, A, p.GitStatus(), unknown_lease, None, None, 'unknown', True)
        report = p.ReconcileReport('succeeded', 'project', 'RUN-1', (unmanaged, missing), (p.ReconcileAction('report_unmanaged', None, unmanaged.path, 'preserve unknown contents', False),), (E,))
        self.assertTrue(report.observations[0].dirty.is_dirty)
        self.assertIsNone(report.observations[1].lease.process_alive)
        cleanable = record(status='cleanup_pending', observed_head_oid=A, lease_id='LEASE-1')
        guard = p.CleanupGuard(cleanable.branch, A, 'LEASE-1', ())
        request = p.CleanupRequest('project', 'PLAN-001', 'RUN-1', 'OP-3', 'cleanup-idem', PROJECT, cleanable, WORKTREE, guard)
        self.assertTrue(all(getattr(request.guard, name) for name in ('require_managed', 'require_clean', 'require_no_live_lease', 'require_merged_or_retained')))
        self.assertNotIn('force', {f.name for f in dc.fields(guard)})
        with self.assertRaises(ValueError):
            dc.replace(request, guard=dc.replace(guard, expected_lease_id=None))
        with self.assertRaises(dc.FrozenInstanceError):
            guard.require_no_live_lease = False
        # These are requests/proposals: fresh lease, dirtiness, merge and retention
        # observation remains owned by the later adapter; no cleanup is performed.

    def check_argv_roundtrip(self, argv, expected_stdout):
        payload = wire(definition())
        payload['argv'] = argv
        REGISTRY.validate(payload)
        observed = subprocess.run(argv, shell=False, capture_output=True, text=True, timeout=5, cwd=WT)
        self.assertEqual(observed.returncode, 0)
        self.assertEqual(observed.stdout, expected_stdout)
        evidence_payload = wire(command_evidence())
        evidence_payload['argv_redacted'] = argv
        REGISTRY.validate(evidence_payload)
        print('ARGUMENT REPRO: schema-valid argv=' + repr(argv) + '; actual stdout=' + repr(observed.stdout), flush=True)
        with self.subTest(dto='CommandDefinition'):
            self.assertEqual(definition(argv=argv).argv, tuple(argv))
        with self.subTest(dto='CommandEvidence'):
            self.assertEqual(command_evidence(argv=argv).argv_redacted, tuple(argv))

    def test_11_schema_valid_whitespace_argument_must_roundtrip(self):
        self.check_argv_roundtrip([sys.executable, '-c', 'import sys; print(repr(sys.argv[1]))', '  payload  '], "'  payload  '\n")

    def test_12_schema_valid_multiline_argument_must_roundtrip(self):
        self.check_argv_roundtrip([sys.executable, '-c', 'x = 1\nprint(x)'], '1\n')

if __name__ == '__main__':
    verify_identity()
    unittest.main(verbosity=2)
