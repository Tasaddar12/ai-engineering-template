"""Read-only candidate verification and independent R2 boundary checks."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from dataclasses import FrozenInstanceError

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-013-a1'
PREFIX = '.ai/plans/current/PLAN-001/'
STEM = PREFIX + 'reviews/TASK-013-a1-c1-R2'
BASE = '24f7c768f996c4abf66ed37a5ea1e89b459dd74b'
HEAD = '51a94cd050ad6c7cb525c6d26c9c7e38e0943c13'
CREF = PREFIX + 'reviews/candidates/CANDIDATE-TASK-013-a1-51a94cd050ad.json'
R1REF = PREFIX + 'reviews/TASK-013-a1-c1-R1.json'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / 'src'))
import contracts
import domain_values
import plan_graph
import orchestration_ports as ports
from contracts import ContractRegistry, structural_task_digest, parse_record_ref
from domain_values import DomainException, ErrorCategory, EntityId, PlanId, RecordRef, Revision, Sha256Digest, ScopeClaim, freeze_json
from plan_graph import AcceptedDependency, build_dependency_graph
from workflow_ports import ContentRef


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def git(*args, cwd=TREE):
    return subprocess.check_output(['git', '-C', str(cwd), *args])


def read(path, root=TREE):
    return json.loads((root / path).read_bytes())


REGISTRY = ContractRegistry(TREE / 'schemas/v1')
PLAN = read(PREFIX + 'plan.json')
GRAPH = read(PREFIX + 'graph.json')
TASKS = [read(PREFIX + 'tasks/' + bucket + '/' + p.name)
         for bucket in ('current', 'completed')
         for p in sorted((TREE / PREFIX / 'tasks' / bucket).glob('TASK-*.json'))]


def verify_identity(label):
    candidate = read(CREF, ROOT)
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert git('merge-base', BASE, HEAD).decode().strip() == BASE
    assert git('status', '--porcelain', '--untracked-files=all') == b''
    assert git('diff', '--name-only', cwd=ROOT) == b''
    assert git('diff', '--cached', '--name-only', cwd=ROOT) == b''
    assert candidate['base_oid'] == BASE and candidate['head_oid'] == HEAD
    raw_diff = git('diff', '--binary', BASE, HEAD)
    assert digest(raw_diff) == candidate['diff_sha256']
    changed = git('diff', '--name-status', BASE, HEAD).decode().splitlines()
    assert set(changed) == {'A\tsrc/plan_graph.py',
        'A\ttests/unit/planning_dag/test_plan_graph.py',
        'A\t' + PREFIX + 'evidence/implementation/TASK-013.md'}
    for ref in candidate['context_refs']:
        assert digest(git('show', HEAD + ':' + ref['path'])) == ref['sha256'], ref
    for ref in candidate['validation_refs']:
        assert digest((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref
    policy_bytes = (ROOT / '.ai/project/policy.json').read_bytes()
    model_bytes = (ROOT / '.ai/project/agent-models.json').read_bytes()
    assert digest(policy_bytes + model_bytes) == candidate['policy_model_digest']
    for p in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
        assert git('show', HEAD + ':' + p) == git('show', BASE + ':' + p)
        assert read(p) == read(p, ROOT)
    unhashed = {k: v for k, v in candidate.items() if k != 'fingerprint'}
    assert digest(json.dumps(unhashed, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == candidate['fingerprint']
    assert candidate['fingerprint'] == '9c7b3139798b22e6f1bb30a9d5e5bf9230db0c75a348cdedbc30f472201bd9ae'
    r1 = read(R1REF, ROOT)
    for record in (candidate, r1):
        REGISTRY.validate(record)
    assert r1['candidate_ref'] == CREF and r1['candidate_fingerprint'] == candidate['fingerprint']
    assert r1['verdict'] == 'pass' and r1['stage'] == 'implementation'
    assert [c['id'] for c in r1['checks']] == [f'R1-{n:02d}' for n in range(1, 12)]
    assert all(c['status'] == 'pass' for c in r1['checks']) and not r1['findings']
    assert r1['independent_session_id'] == '/root/r1_013_c1'
    assert r1['implementation_session_id'] == '/root/implement_013'
    assert r1['checklist_version'] == candidate['checklist_version'] == 'PLAN-001-v1'
    iso = read(PREFIX + 'reviews/r4-isolation-review.json')
    assert iso['verdict'] == 'pass' and iso['graph_revision'] == candidate['graph_revision'] == GRAPH['revision'] == 4
    assert structural_task_digest(TASKS) == GRAPH['task_set_sha256'] == iso['task_set_sha256']
    assert len(TASKS) == 39 and all(c['status'] == 'pass' for c in iso['checks'])
    assert all(f['resolved'] for f in iso['findings'])
    for tid, accepted, source in (
        ('TASK-001', 'd1fc917466410febc6238479e65816dd39591a4f', 'src/domain_values.py'),
        ('TASK-004', 'e3c1177f993ee74815639a83ef3333faa4ba3957', 'src/contracts.py'),
        ('TASK-039', '314ef09d59f494223bec02556c6e3d9a8108636f', 'src/orchestration_ports.py')):
        assert next(t for t in TASKS if t['id'] == tid)['status'] == 'accepted'
        assert subprocess.run(['git', '-C', str(TREE), 'merge-base', '--is-ancestor', accepted, BASE]).returncode == 0
        assert git('show', accepted + ':' + source) == git('show', HEAD + ':' + source)
    for module in (contracts, domain_values, plan_graph, ports):
        assert Path(module.__file__).resolve().parent == (TREE / 'src').resolve()
    print(label + ': identity PASS; clean exact head/base; 13 context hashes; validation hash; raw diff/policy/model/fingerprint; passing same-candidate R1; r4 digest; unchanged accepted 001/004/039 code.')
    print('Changed paths:', changed)
    print('Candidate imports:', {m.__name__: m.__file__ for m in (contracts, domain_values, plan_graph, ports)})
    return candidate


def build(plan=PLAN, graph=GRAPH, tasks=TASKS):
    return build_dependency_graph(plan, graph, tasks, registry=REGISTRY)


def qualified(task_id, plan_id='PLAN-001'):
    return parse_record_ref(f'task:{plan_id}:{task_id}', expected_plan_id=plan_id, expected_kind='task')


def recast(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [recast(v, old, new) for v in value]
    if isinstance(value, dict):
        return {k: recast(v, old, new) for k, v in value.items()}
    return value


class ConsistencyChecks(unittest.TestCase):
    def test_01_real_plan_through_accepted_port_values(self):
        dag = build()
        self.assertEqual(len(dag.nodes), 39)
        self.assertEqual(len(dag.acceptance_coverage), 9)
        port_graph = ports.TaskGraphRecord(
            GRAPH['id'], GRAPH['plan_id'], GRAPH['revision'], GRAPH['status'],
            tuple(ports.GraphNode(n['task_id'], tuple(n['depends_on'])) for n in GRAPH['nodes']),
            GRAPH['task_set_sha256'], GRAPH['review_ref'])
        self.assertEqual((dag.plan_id, dag.graph_id, dag.revision, dag.status, dag.task_set_digest),
                         (port_graph.plan_id, port_graph.id, port_graph.revision, port_graph.status, port_graph.task_set_sha256))
        self.assertEqual({n.task.local_id: set(d.local_id for d in n.dependencies) for n in dag.nodes},
                         {n.task_id: set(n.depends_on) for n in port_graph.nodes})
        snapshots = tuple(ports.TaskContractSnapshot(t['id'], tuple(t['depends_on']), ScopeClaim(**t['scope']),
            tuple(a['id'] for a in t['acceptance_criteria']), tuple(t['plan_acceptance_ids']),
            tuple(t['input_contracts']), tuple(t['output_contracts']), t['estimated_production_files'],
            ContentRef(PREFIX + 'tasks/current/' + t['id'] + '.json', digest(git('show', HEAD + ':' + PREFIX + 'tasks/current/' + t['id'] + '.json')))) for t in TASKS)
        # Synthetic attestations exercise representation only; these are not repository acceptance claims.
        commits = tuple(ports.AcceptedDependencyCommit(t['id'], 'a'*40, 'b'*40, 'c'*64,
            (ContentRef('evidence/fake-acceptance.json', 'd'*64),)) for t in TASKS if t['status'] == 'accepted')
        snapshot = ports.SchedulingSnapshot('project', 'PLAN-001', 'RUN-001', 28, port_graph,
            snapshots, commits, (), (), (), 0, {'max_parallel': 4})
        facts = tuple(AcceptedDependency(qualified(c.task_id.value, snapshot.plan_id.value), c.integration_oid)
                      for c in snapshot.accepted_dependency_commits)
        self.assertEqual(dag.ready_frontier(facts), ())
        # Real eligible tasks are already active. Simulate one permitted ready state;
        # this lifecycle change must leave the structural digest unchanged.
        dispatch_tasks = copy.deepcopy(TASKS)
        next(t for t in dispatch_tasks if t['id'] == 'TASK-013')['status'] = 'ready'
        dag = build(tasks=dispatch_tasks)
        frontier = dag.ready_frontier(facts)
        satisfied = {c.task_id.value for c in commits}
        expected = sorted(t['id'] for t in dispatch_tasks if t['status'] in ('backlog', 'ready')
                          and t['id'] not in satisfied and set(t['depends_on']) <= satisfied)
        self.assertEqual([r.task.local_id.value for r in frontier], expected)
        self.assertTrue(expected)  # Capacity zero remains scheduler policy, not a DAG filter.
        self.assertEqual(dag.ready_frontier(), ())
        for r in frontier:
            task = next(t for t in TASKS if t['id'] == r.task.local_id.value)
            self.assertEqual([f.task.local_id.value for f in r.dependency_facts], sorted(task['depends_on']))
            self.assertTrue(all(f.integration_commit == 'b'*40 for f in r.dependency_facts))
        print('Real plan -> accepted scheduling DTO: 39 nodes, 9 criteria,', len(commits), 'synthetic facts; frontier', expected)

    def test_02_lifecycle_neutral_digest_and_structural_prose(self):
        before = build()
        tasks = recast(copy.deepcopy(TASKS), '/plans/current/PLAN-001/', '/plans/completed/PLAN-001/')
        for t in tasks:
            t['attempt_ids'].append(t['id'] + '-review-simulation')
        graph = copy.deepcopy(GRAPH)
        self.assertEqual(structural_task_digest(tasks), GRAPH['task_set_sha256'])
        self.assertEqual(build(tasks=tasks), before)
        tasks[0]['output_contracts'].append('Keep current evidence at .ai/plans/current/PLAN-001/spec.json')
        with self.assertRaises(DomainException) as caught:
            build(tasks=tasks)
        self.assertEqual(caught.exception.category, ErrorCategory.VALIDATION_FAILED)
        self.assertIn('stale', str(caught.exception))
        self.assertNotEqual(structural_task_digest(tasks), GRAPH['task_set_sha256'])
        print('Lifecycle-only path/attempt movement preserves full DAG; structural mixed-field prose rejects prior digest.')

    def test_03_proposed_split_coverage_and_excluded_history(self):
        plan, tasks = copy.deepcopy(PLAN), copy.deepcopy(TASKS)
        old = next(t for t in tasks if t['id'] == 'TASK-013')
        history = copy.deepcopy(old)
        history.update(status='superseded', superseded_by=['TASK-040', 'TASK-041'])
        history_bytes = json.dumps(history, sort_keys=True)
        tasks.remove(old)
        for number in (40, 41):
            replacement = recast(copy.deepcopy(old), 'TASK-013', f'TASK-{number:03d}')
            replacement.update(status='backlog', attempt_ids=[], superseded_by=[])
            if number == 41:
                replacement['depends_on'].append('TASK-040')
            tasks.append(replacement)
        for task in tasks:
            task['depends_on'] = ['TASK-041' if d == 'TASK-013' else d for d in task['depends_on']]
        plan['task_ids'] = [t['id'] for t in tasks]
        graph = copy.deepcopy(GRAPH)
        graph.update(id='PLAN-001-r5', revision=5, status='proposed', review_ref=None,
            nodes=[{'task_id': t['id'], 'depends_on': t['depends_on']} for t in tasks],
            task_set_sha256=structural_task_digest(tasks))
        dag = build(plan, graph, tasks)
        self.assertEqual(len(dag.nodes), 40)
        coverage = next(c for c in dag.acceptance_coverage if c.acceptance_id.value == 'AC-03')
        self.assertTrue({qualified('TASK-040'), qualified('TASK-041')} <= set(coverage.tasks))
        self.assertNotIn(qualified('TASK-013'), dag.topological_order)
        self.assertEqual(json.dumps(history, sort_keys=True), history_bytes)
        self.assertEqual(next(t for t in tasks if t['id'] == 'TASK-001'), next(t for t in TASKS if t['id'] == 'TASK-001'))
        with self.assertRaises(DomainException):
            build(plan, graph, tasks + [history])
        with self.assertRaises(DomainException):
            dag.ready_frontier([AcceptedDependency(qualified('TASK-013'), 'a'*40)])
        # A proposal losing an original criterion fails even with a recomputed digest.
        lost = copy.deepcopy(tasks)
        for t in lost:
            t['plan_acceptance_ids'] = [a for a in t['plan_acceptance_ids'] if a != 'AC-03'] or ['AC-01']
        graph['task_set_sha256'] = structural_task_digest(lost)
        with self.assertRaises(DomainException) as caught:
            build(plan, graph, lost)
        self.assertEqual(caught.exception.error.details['missing_acceptance_ids'], ('AC-03',))
        print('40-node proposed split preserves original coverage and prerequisite bytes; excluded history/facts and dropped original AC reject.')

    def test_04_registry_error_and_frozen_input_compatibility(self):
        self.assertEqual(build(freeze_json(PLAN), freeze_json(GRAPH), freeze_json(TASKS)), build())
        for record_index in range(3):
            for field, value in (('schema_version', '9.0'), ('kind', 'future-kind'), ('unknown', 1)):
                plan, graph, tasks = copy.deepcopy(PLAN), copy.deepcopy(GRAPH), copy.deepcopy(TASKS)
                target = (plan, graph, tasks[0])[record_index]
                target[field] = value
                with self.assertRaises(DomainException) as expected:
                    REGISTRY.validate(target)
                with self.assertRaises(DomainException) as actual:
                    build(plan, graph, tasks)
                self.assertEqual(actual.exception.category, expected.exception.category)
                self.assertEqual(actual.exception.error.details, expected.exception.error.details)
                self.assertFalse(actual.exception.retryable)
                with self.assertRaises(TypeError):
                    actual.exception.error.details['bad'] = True
        print('Immutable accepted JSON builds; nine version/kind/shape failures preserve accepted registry category/details/retryability.')

    def test_05_plan_qualified_namespace_across_port_roundtrip(self):
        left = build()
        plan, graph, tasks = (recast(copy.deepcopy(v), 'PLAN-001', 'PLAN-902') for v in (PLAN, GRAPH, TASKS))
        graph['task_set_sha256'] = structural_task_digest(tasks)
        right = build(plan, graph, tasks)
        self.assertEqual([r.local_id for r in left.topological_order], [r.local_id for r in right.topological_order])
        self.assertTrue(set(left.topological_order).isdisjoint(right.topological_order))
        for ref in left.topological_order:
            self.assertEqual(left.node(parse_record_ref(str(ref))).task, ref)
        with self.assertRaises(DomainException):
            right.node(left.nodes[0].task)
        with self.assertRaises(DomainException):
            right.ready_frontier([AcceptedDependency(left.nodes[0].task, 'a'*40)])
        print('Two complete 39-task plans share local IDs but all lookup/frontier identities stay disjoint.')

    def test_06_detached_values_and_stable_direct_fact_order(self):
        baseline = copy.deepcopy(TASKS)
        next(t for t in baseline if t['id'] == 'TASK-013')['status'] = 'ready'
        plan, graph, tasks = copy.deepcopy(PLAN), copy.deepcopy(GRAPH), copy.deepcopy(baseline)
        before = build(plan, graph, tasks)
        facts = [AcceptedDependency(n.task, '1'*64) for n in before.nodes if n.status.value == 'accepted']
        frontier = before.ready_frontier(facts)
        self.assertEqual(before.ready_frontier(iter(reversed(facts))), frontier)
        tasks.reverse()
        graph['nodes'].reverse()
        self.assertEqual(build(plan, graph, iter(tasks)), before)
        tasks[0]['plan_acceptance_ids'].clear()
        graph['nodes'].clear()
        plan['acceptance_criteria'].clear()
        facts.clear()
        self.assertEqual(before, build(tasks=baseline))
        self.assertTrue(frontier)
        for value, field in ((before, 'nodes'), (before.nodes[0], 'dependencies'),
                             (before.acceptance_coverage[0], 'tasks'), (frontier[0], 'dependency_facts'),
                             (frontier[0].dependency_facts[0], 'integration_commit')):
            with self.assertRaises(FrozenInstanceError):
                setattr(value, field, None)
        print('Builder/port-derived outputs remain detached, immutable, deterministic; full SHA-256 integration facts preserved.')


if __name__ == '__main__':
    verify_identity('PRE')
    if '--checks-only' not in sys.argv:
        command = read(PREFIX + 'commands/test.TASK-013.json')
        argv = [sys.executable] + command['argv'][1:]
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(TREE / 'src'))
        result = subprocess.run(argv, cwd=TREE, env=env, capture_output=True, text=True, timeout=command['timeout_seconds'])
        print('Declared argv:', argv, '; cwd:', TREE, '; exit:', result.returncode)
        print(result.stdout + result.stderr)
        assert result.returncode == 0 and 'Ran 13 tests' in result.stderr
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ConsistencyChecks)
    result = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
    verify_identity('POST')
    assert result.testsRun == 6
    raise SystemExit(0 if result.wasSuccessful() else 1)
