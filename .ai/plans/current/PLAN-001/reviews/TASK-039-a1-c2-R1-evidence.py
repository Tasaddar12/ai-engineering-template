"""Independent cycle-2 R1 probes; candidate is read-only and imports use its src."""
from __future__ import annotations
import ast
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
from dataclasses import fields, replace
from typing import get_type_hints

ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-039-a1'
BASE = '3368964b3825df6e1e59c1f66820f2bce61de0ff'
HEAD = '314ef09d59f494223bec02556c6e3d9a8108636f'
PLAN = '.ai/plans/current/PLAN-001/'
CANDIDATE = PLAN + 'reviews/candidates/CANDIDATE-TASK-039-a1-314ef09d59f4.json'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'src'))
import orchestration_ports as p
import workflow_ports as w
import domain_values as d
from contracts import structural_task_digest
from jsonschema import Draft202012Validator, FormatChecker

def git(*args, cwd=WT):
    return subprocess.check_output(['git', *args], cwd=cwd, shell=False)

def expect_rejection(label, fn):
    try:
        fn()
    except (TypeError, ValueError):
        return
    raise AssertionError('accepted invalid input: ' + label)

def verify_identity():
    candidate = json.loads((ROOT / CANDIDATE).read_text(encoding='utf-8'))
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('status', '--porcelain', '--untracked-files=all') == b''
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert candidate['base_oid'] == BASE and candidate['head_oid'] == HEAD
    assert hashlib.sha256(git('diff', '--binary', BASE, HEAD)).hexdigest() == candidate['diff_sha256']
    for ref in candidate['context_refs']:
        raw = git('show', HEAD + ':' + ref['path'])
        assert hashlib.sha256(raw).hexdigest() == ref['sha256'], ref['path']
    for ref in candidate['validation_refs']:
        assert hashlib.sha256((ROOT / ref['path']).read_bytes()).hexdigest() == ref['sha256']
    policy_model = (ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()
    assert hashlib.sha256(policy_model).hexdigest() == candidate['policy_model_digest']
    unsigned = {k: v for k, v in candidate.items() if k != 'fingerprint'}
    digest = hashlib.sha256(json.dumps(unsigned, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
    assert digest == candidate['fingerprint'] == '8be5700d160170cda0a2c3570aa7a4858ae79952bd642782bf1b7685bd51d74a'
    expected = {
        'src/orchestration_ports.py',
        'tests/unit/domain_orchestration_ports/test_orchestration_ports.py',
        PLAN + 'evidence/implementation/TASK-039.md',
    }
    changes = git('diff', '--name-status', BASE, HEAD).decode().splitlines()
    assert {line.split('\t', 1)[1] for line in changes} == expected
    assert all(line.startswith('A\t') for line in changes)
    graph = json.loads(git('show', HEAD + ':' + PLAN + 'graph.json'))
    isolation = json.loads(git('show', HEAD + ':' + PLAN + 'reviews/r4-isolation-review.json'))
    task_records = [json.loads(git('show', HEAD + ':' + PLAN + 'tasks/current/' + n['task_id'] + '.json')) for n in graph['nodes']]
    assert structural_task_digest(task_records) == graph['task_set_sha256'] == isolation['task_set_sha256']
    assert graph['status'] == 'approved' and graph['revision'] == isolation['graph_revision'] == 4 and isolation['verdict'] == 'pass'
    for oid in ['d51b72ce71ea3ac3ad31adf41e3eddc84738ac0b', 'c749ec19056dd6d215c51a9896f35785391d0ace', 'd1fc917466410febc6238479e65816dd39591a4f']:
        subprocess.run(['git', 'merge-base', '--is-ancestor', oid, BASE], cwd=WT, check=True, shell=False)
    subprocess.run(['git', 'diff', '--check', BASE, HEAD], cwd=WT, check=True, shell=False)
    print('PASS identity: clean frozen ROOT/base and candidate HEAD; binary diff; 12 committed context hashes; validation hash; policy/model digest; canonical fingerprint; three allowed additions; graph r4 structural digest/isolation; accepted prerequisite ancestry.')

verify_identity()
for module in (p, w, d):
    assert Path(module.__file__).resolve().parent == WT / 'src'
    print('Import:', module.__file__)
if '--probes-only' not in sys.argv:
    command = json.loads((WT / (PLAN + 'commands/test.TASK-039.json')).read_text())['argv']
    run = subprocess.run([sys.executable, '-B', *command[1:]], cwd=WT, shell=False, text=True, capture_output=True,
                         env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    print('Declared command:', [sys.executable, '-B', *command[1:]])
    print('Exit:', run.returncode)
    print(run.stdout + run.stderr)
    assert run.returncode == 0 and 'Ran 20 tests' in run.stderr and 'OK' in run.stderr
else:
    print('Independent probes rerun after correcting review fixture error_category; declared 20-test pass above is retained.')

spec = importlib.util.spec_from_file_location('r1_fixtures', WT / 'tests/unit/domain_orchestration_ports/test_orchestration_ports.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)

expected = [
    (p.IsolationService, 'review', 'request', p.IsolationRequest, p.IsolationDecision),
    (p.TaskDispatcher, 'start', 'request', p.TaskAttemptRequest, p.AttemptHandle),
    (p.TaskDispatcher, 'observe', 'handle', p.AttemptHandle, p.AttemptObservation),
    (p.TaskDispatcher, 'cancel', 'handle', p.AttemptHandle, w.CancelObservation),
    (p.Scheduler, 'tick', 'snapshot', p.SchedulingSnapshot, p.SchedulingDecision),
    (p.IntegrationService, 'integrate', 'request', p.IntegrationRequest, p.IntegrationResult),
    (p.RecoveryService, 'recover', 'request', p.RecoveryRequest, p.RecoveryDecision),
    (p.ExecutionService, 'advance', 'request', p.ExecutionRequest, p.ExecutionStep),
    (p.PlanIntegrationService, 'evaluate', 'request', p.PlanIntegrationRequest, p.PlanIntegrationDecision),
    (p.CompletionContinuation, 'advance', 'request', p.CompletionRequest, p.CompletionStep),
]
for port, method, arg, arg_type, result_type in expected:
    fn = getattr(port, method)
    assert tuple(inspect.signature(fn).parameters) == ('self', arg)
    assert get_type_hints(fn) == {arg: arg_type, 'return': result_type}
print('PASS all ten frozen Protocol signatures, complete parameter and return type identity.')

for cls, name in [(p.TaskGraphRecord, 'task-graph'), (p.CandidateRecord, 'candidate'), (p.IsolationReviewRecord, 'isolation-review'), (p.RecoveryRecord, 'recovery')]:
    schema = json.loads((WT / f'schemas/v1/{name}.schema.json').read_text())
    assert {item.name for item in fields(cls)} == set(schema['properties'])
for cls, name, key in [(p.GraphNode, 'task-graph', 'nodes'), (p.AcceptanceMapping, 'recovery', 'acceptance_mapping'), (p.SalvageItem, 'recovery', 'salvage')]:
    schema = json.loads((WT / f'schemas/v1/{name}.schema.json').read_text())
    assert {item.name for item in fields(cls)} == set(schema['properties'][key]['items']['properties'])
tree = ast.parse((WT / 'src/orchestration_ports.py').read_text())
imports = {node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
imports |= {a.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import) for a in node.names}
assert imports <= {'__future__', 're', 'collections', 'dataclasses', 'datetime', 'enum', 'typing', 'domain_values', 'workflow_ports'}
assert {x.value for x in d.ExecutionStatus} == {'progress', 'waiting', 'tasks_accepted', 'paused', 'failed', 'cancelled'}
assert {x.value for x in d.CompletionStatus} == {'progress', 'waiting', 'delivery_ready', 'completed', 'paused', 'failed'}
print('PASS four schema-backed DTO field sets plus three nested shapes; only accepted/shared and standard-library imports; exact execution/completion vocabulary.')

budget = p.LineageBudget(300, 299, 3, 2, 3600, 3599, 2, 1, 1, 10000, 9999)
pairs = [('used_agent_invocations', 'max_agent_invocations'), ('used_rewrites', 'max_rewrites'), ('elapsed_seconds', 'max_elapsed_seconds'), ('used_review_1_cycles', 'max_review_cycles_per_stage'), ('used_review_2_cycles', 'max_review_cycles_per_stage'), ('used_tokens', 'max_tokens')]
for usage, limit in pairs:
    for value in [0, getattr(budget, limit) - 1, getattr(budget, limit), getattr(budget, limit) + 1, 10**30]:
        actual = replace(budget, **{usage: value})
        assert getattr(actual, usage) == value and getattr(actual, limit) == getattr(budget, limit)
for item in fields(budget):
    for invalid in [-1, True, False, 1.5, '1']:
        expect_rejection(item.name, lambda key=item.name, value=invalid: replace(budget, **{key: value}))
assert replace(budget, max_tokens=None, used_tokens=10**30).used_tokens == 10**30
print('PASS repair: 30 independent usage boundary cases across all six counters; 55 malformed numeric cases rejected; unbounded optional tokens retained.')

r1, r2 = f.review_histories(4)
r2.pop()  # Latest attempt never reached R2; retain earlier R2 evidence.
permissions = ['local_execute']
observed = replace(budget, used_agent_invocations=301, used_rewrites=4, elapsed_seconds=3601, used_review_1_cycles=4, used_review_2_cycles=3, used_tokens=10001)
request = p.RecoveryRequest('project-1', 'PLAN-001', 'run-1', 'operation-recovery', 'request-recovery', 12, 'budget exhausted', ['TASK-003'], f.graph(), f.tasks(), [p.AcceptanceMapping('TASK-003-AC1', ['TASK-003'])], r1, r2, observed, f.git_facts(), permissions, [f.evidence('failure')])
r1.clear(); r2.clear(); permissions.clear()
assert len(request.review_1_history) == 4 and len(request.review_2_history) == 3
assert request.lineage_budget is observed and request.permission_subset == ('local_execute',)
assert request.original_acceptance_mapping[0].original_id == 'TASK-003-AC1'
for history in ['review_1_history', 'review_2_history']:
    opposite = request.review_2_history if history == 'review_1_history' else request.review_1_history
    expect_rejection(history + ' stage mismatch', lambda key=history, values=opposite: replace(request, **{key: values}))
expect_rejection('dangling R2', lambda: replace(request, review_1_history=request.review_1_history[1:]))
expect_rejection('foreign plan history', lambda: replace(request, review_1_history=[replace(request.review_1_history[0], record=replace(request.review_1_history[0].record, plan_id='PLAN-999'))]))
pause = p.RecoveryDecision('paused', request.request_id, request.plan_id, request.run_id, None, None, None, [], request.failed_task_ids, ['TASK-003-a1'], [f.evidence('durable-pause')], f.error(d.ErrorCategory.BUDGET_EXHAUSTED))
assert pause.error.category is d.ErrorCategory.BUDGET_EXHAUSTED and pause.evidence_refs
assert not any('permission' in item.name or 'grant' in item.name for item in fields(pause))
expect_rejection('pause without error', lambda: replace(pause, error=None))
print('PASS cumulative 4 R1 / 3 R2 history retention, immutable permission subset, over-limit usage request and evidence-bearing budget_exhausted pause; stage, plan and R2 linkage guards.')

good = p.AttemptObservation('succeeded', f.attempt_handle(), f.successful_agent_observation(), f.content('imported'), [f.evidence('import')])
expect_rejection('missing import evidence', lambda: replace(good, evidence_refs=[]))
expect_rejection('stale provider lease', lambda: replace(good, agent_observation=f.successful_agent_observation(f.provider_handle(8))))
expect_rejection('known provider handle mismatch', lambda: replace(good, agent_observation=f.successful_agent_observation(replace(f.provider_handle(), external_handle='external-other'))))
expect_rejection('provider request mismatch', lambda: replace(good, agent_observation=f.successful_agent_observation(replace(f.provider_handle(), request_id='request-other'))))
unknown_run = replace(good.agent_observation.run, status=d.AgentRunStatus.UNKNOWN, output_ref=None, error_category=d.ErrorCategory.AMBIGUOUS_SIDE_EFFECT)
unknown_agent = w.AgentObservation(d.AgentRunStatus.UNKNOWN, good.handle.agent_handle, unknown_run, None, [f.evidence('unknown')], f.error(d.ErrorCategory.AMBIGUOUS_SIDE_EFFECT))
unknown = p.AttemptObservation('unknown', good.handle, unknown_agent, None, [f.evidence('unknown')], f.error(d.ErrorCategory.AMBIGUOUS_SIDE_EFFECT))
expect_rejection('unknown output import', lambda: replace(unknown, imported_output_ref=f.content('late')))
for status in [w.CancelStatus.PENDING, w.CancelStatus.UNKNOWN, w.CancelStatus.FAILED]:
    cancel = w.CancelObservation(status, f.provider_handle(), False, [f.evidence('cancel')], f.error() if status != w.CancelStatus.PENDING else None)
    expect_rejection('unresolved cancellation cannot quiesce', lambda c=cancel: replace(c, quiesced=True))
print('PASS dispatch evidence and provider request/lease/handle fences; unknown output cannot import; pending/unknown/failed cancellation cannot release scope.')

integrated = p.IntegrationResult('integrated', 'project-1', 'PLAN-001', 'run-1', 'integrate', 'TASK-003', f.OTHER_OID, f.OID, f.MERGE_OID, f.MERGE_OID, False, [f.evidence('integrated')])
expect_rejection('integration without observed OID', lambda: replace(integrated, observed_integration_oid=None))
expect_rejection('integration without evidence', lambda: replace(integrated, evidence_refs=[]))
expect_rejection('re-review represented as accepted', lambda: replace(integrated, re_review_required=True))
approved = f.plan_integration_decision()
expect_rejection('approval without validation', lambda: replace(approved, validation_result=None))
expect_rejection('approval with candidate-mismatched review', lambda: replace(approved, review=replace(approved.review, candidate_fingerprint=f.OTHER_DIGEST)))
completed = p.CompletionStep('completed', 'run-1', 'completed', 14, approved, f.delivery_observation(), [f.evidence('completed')])
for label, changes in [('no integration', {'integration_decision': None}), ('no observation', {'delivery_observation': None}), ('unmerged observation', {'delivery_observation': f.delivery_observation(False)}), ('no evidence', {'evidence_refs': []})]:
    expect_rejection(label, lambda values=changes: replace(completed, **values))
unauthorized = replace(completed.delivery_observation, state=replace(completed.delivery_observation.state, authorization_refs=[]))
expect_rejection('no authorization', lambda: replace(completed, delivery_observation=unauthorized))
expect_rejection('tasks_accepted cannot be completion', lambda: replace(completed, status='tasks_accepted'))
print('PASS integration requires observed OID/evidence and consistent re-review status; plan approval requires validation/exact review; completion requires approved integration plus authorized observed merge.')
verify_identity()
print('ALL INDEPENDENT CYCLE-2 R1 PROBES PASSED. No candidate source/state mutation or automatic integration performed.')
