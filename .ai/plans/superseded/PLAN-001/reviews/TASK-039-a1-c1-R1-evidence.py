"""Read-only independent R1 reproduction; writes only its named report companion."""
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
from dataclasses import replace, FrozenInstanceError
from typing import get_type_hints

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-039-a1'
STEM = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-039-a1-c1-R1'
BASE = '6023ffaa9f6e5812dade5dc48e193f256f334a6e'
HEAD = 'b54d39eecb862e6020be6fb5614c773d9cdc4b3b'
FP = '8dcea50b055bf8199939becf8df3c12461e9e7480b877cfdae5dfef99df36b89'
lines = []

def note(value):
    lines.append(str(value))
    print(value)

def git(*args):
    return subprocess.run(['git', *args], cwd=TREE, check=True, capture_output=True).stdout

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def must_reject(label, action):
    try:
        action()
    except (ValueError, TypeError, FrozenInstanceError) as exc:
        note(f'PASS guard {label}: {type(exc).__name__}: {exc}')
    else:
        raise AssertionError(f'{label} unexpectedly accepted')

def main():
    note('Harness history: initial run passed the 19-test suite and identity checks, then stopped on a reviewer fixture TypeError (unknown AgentObservation lacked its mandatory AgentRunRecord). Corrected the review-only fixture; this was not a candidate failure.')
    note(f'R1 request REVIEW-REQUEST-TASK-039-a1-c1-R1; invocation/session /root/r1_039_c1; implementer /root/implement_039')
    note('Coordinator-observed native settings: OpenAI gpt-6-astra/xhigh, review_high rank 4; implementer gpt-5.6-sol/xhigh rank 3. Separate provider-returned identity/effort unavailable.')
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('status', '--porcelain=v1') == b''
    git('merge-base', '--is-ancestor', BASE, HEAD)
    candidate = json.loads((ROOT / '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-039-a1-b54d39eecb86.json').read_text(encoding='utf-8'))
    assert (candidate['base_oid'], candidate['head_oid'], candidate['fingerprint']) == (BASE, HEAD, FP)
    assert sha(git('diff', '--binary', BASE, HEAD)) == candidate['diff_sha256']
    paths = git('diff', '--name-only', BASE, HEAD).decode().splitlines()
    assert set(paths) == {'.ai/plans/current/PLAN-001/evidence/implementation/TASK-039.md', 'src/orchestration_ports.py', 'tests/unit/domain_orchestration_ports/test_orchestration_ports.py'}
    for ref in candidate['context_refs']:
        assert sha(git('show', f'{HEAD}:{ref["path"]}')) == ref['sha256'], ref['path']
    for ref in candidate['validation_refs']:
        assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref['path']
    assert sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()) == candidate['policy_model_digest']
    unsigned = {key: value for key, value in candidate.items() if key != 'fingerprint'}
    assert sha(json.dumps(unsigned, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == FP
    note(f'PASS candidate: clean HEAD={HEAD}; BASE={BASE}; fingerprint={FP}; binary diff, all 12 committed context hashes, ROOT validation hash and policy/model hash match; exactly 3 owned additions')
    for commit in ['d51b72ce71ea3ac3ad31adf41e3eddc84738ac0b', 'c749ec19056dd6d215c51a9896f35785391d0ace', 'd1fc917466410febc6238479e65816dd39591a4f']:
        git('merge-base', '--is-ancestor', commit, BASE)
    note('PASS accepted TASK-003 candidate/integration and shared TASK-001 candidate are ancestors of frozen base')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(TREE / 'src'))
    import contracts
    graph = json.loads((TREE / '.ai/plans/current/PLAN-001/graph.json').read_text())
    tasks = [json.loads(path.read_text()) for path in (TREE / '.ai/plans/current/PLAN-001/tasks/current').glob('TASK-*.json')]
    assert contracts.structural_task_digest(tasks) == graph['task_set_sha256']
    iso = json.loads((TREE / '.ai/plans/current/PLAN-001/reviews/r4-isolation-review.json').read_text())
    assert iso['verdict'] == 'pass' and iso['graph_revision'] == graph['revision'] == 4
    assert iso['task_set_sha256'] == graph['task_set_sha256']
    assert {check['id'] for check in iso['checks']} == {f'ISO-{i:02}' for i in range(1, 13)}
    note(f'PASS approved r4 isolation matches recomputed structural task digest {graph["task_set_sha256"]}')
    command = json.loads((TREE / '.ai/plans/current/PLAN-001/commands/test.TASK-039.json').read_text())
    argv = [sys.executable, *command['argv'][1:]]
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    run = subprocess.run(argv, cwd=TREE, env=env, capture_output=True, text=True, timeout=180)
    note(f'DECLARED SUITE {argv!r}; exit={run.returncode}')
    note(run.stdout + run.stderr)
    assert run.returncode == 0 and 'Ran 19 tests' in run.stderr
    import orchestration_ports as op
    import workflow_ports as wp
    import domain_values as dv
    for module in (op, wp, dv):
        assert Path(module.__file__).resolve().parent == (TREE / 'src').resolve()
    note('PASS imports resolve frozen task-tree src for orchestration_ports, workflow_ports and domain_values')
    expected = [(op.IsolationService, 'review', 'request', op.IsolationRequest, op.IsolationDecision), (op.TaskDispatcher, 'start', 'request', op.TaskAttemptRequest, op.AttemptHandle), (op.TaskDispatcher, 'observe', 'handle', op.AttemptHandle, op.AttemptObservation), (op.TaskDispatcher, 'cancel', 'handle', op.AttemptHandle, wp.CancelObservation), (op.Scheduler, 'tick', 'snapshot', op.SchedulingSnapshot, op.SchedulingDecision), (op.IntegrationService, 'integrate', 'request', op.IntegrationRequest, op.IntegrationResult), (op.RecoveryService, 'recover', 'request', op.RecoveryRequest, op.RecoveryDecision), (op.ExecutionService, 'advance', 'request', op.ExecutionRequest, op.ExecutionStep), (op.PlanIntegrationService, 'evaluate', 'request', op.PlanIntegrationRequest, op.PlanIntegrationDecision), (op.CompletionContinuation, 'advance', 'request', op.CompletionRequest, op.CompletionStep)]
    for protocol, method, arg, incoming, outgoing in expected:
        fn = getattr(protocol, method)
        assert tuple(inspect.signature(fn).parameters) == ('self', arg)
        assert get_type_hints(fn) == {arg: incoming, 'return': outgoing}
    assert {v.value for v in dv.ExecutionStatus} == {'progress', 'waiting', 'tasks_accepted', 'paused', 'failed', 'cancelled'}
    assert {v.value for v in dv.CompletionStatus} == {'progress', 'waiting', 'delivery_ready', 'completed', 'paused', 'failed'}
    imports = set()
    for node in ast.walk(ast.parse((TREE / 'src/orchestration_ports.py').read_text())):
        if isinstance(node, ast.ImportFrom): imports.add(node.module)
        if isinstance(node, ast.Import): imports.update(alias.name for alias in node.names)
    assert imports == {'__future__', 're', 'collections.abc', 'dataclasses', 'datetime', 'enum', 'typing', 'domain_values', 'workflow_ports'}
    note('PASS all 10 exact Protocol method argument/return types, both frozen status vocabularies, accepted-only import surface and no later concrete imports')
    spec = importlib.util.spec_from_file_location('r1_task039_fixture', TREE / 'tests/unit/domain_orchestration_ports/test_orchestration_ports.py')
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    f = fixtures
    good = op.AttemptObservation('succeeded', f.attempt_handle(), f.successful_agent_observation(), f.content('output'), [f.evidence()])
    must_reject('successful import without evidence', lambda: replace(good, evidence_refs=[]))
    must_reject('successful import mismatched external handle', lambda: replace(good, agent_observation=f.successful_agent_observation(replace(f.provider_handle(), external_handle='another-worker'))))
    unknown_run = replace(f.successful_agent_observation().run, status=dv.AgentRunStatus.UNKNOWN, finished_at=None, output_ref=None, error_category='internal_error')
    unknown_agent = wp.AgentObservation(dv.AgentRunStatus.UNKNOWN, f.provider_handle(), unknown_run, None, [f.evidence('unknown')], f.error())
    unknown = op.AttemptObservation('unknown', f.attempt_handle(), unknown_agent, None, [f.evidence('unknown')], f.error())
    must_reject('unknown import forbidden', lambda: replace(unknown, imported_output_ref=f.content('output')))
    must_reject('unknown cancellation cannot release scope', lambda: wp.CancelObservation('unknown', f.provider_handle(), True, [f.evidence()], f.error()))
    must_reject('execution does not admit completed', lambda: op.ExecutionStep('completed', 'run-1', 'completed', 14, [f.evidence()]))
    completed = op.CompletionStep('completed', 'run-1', 'completed', 14, f.plan_integration_decision(), f.delivery_observation(), [f.evidence()])
    unauthorized = replace(f.delivery_observation(), state=replace(f.delivery_observation().state, authorization_refs=[]))
    must_reject('completion without authorization evidence', lambda: replace(completed, delivery_observation=unauthorized))
    must_reject('completion with unknown delivery', lambda: replace(completed, delivery_observation=wp.DeliveryObservation('unknown', f.delivery_observation().handle, None, [f.evidence()], f.error())))
    must_reject('incomplete dispatch context', lambda: replace(f.attempt_request(), context=replace(f.context(), required_context_complete=False)))
    note('PASS 8 additional identity/evidence/unknown/cancellation/completion guards')
    at_limit = replace(f.budget(), elapsed_seconds=3600, used_tokens=10000)
    assert at_limit.elapsed_seconds == 3600 and at_limit.used_tokens == 10000
    for label, changes in [('elapsed after resume', {'elapsed_seconds': 3601}), ('actual token usage after completion', {'used_tokens': 10001}), ('cumulative R1 history after bounded repair', {'used_review_1_cycles': 3}), ('cumulative R2 history after bounded repair', {'used_review_2_cycles': 3})]:
        try:
            replace(at_limit, **changes)
        except ValueError as exc:
            note(f'REPRO R1-TASK-039-001: {label} {changes!r} is rejected before RecoveryRequest can carry actual usage: {exc}')
        else:
            raise AssertionError('budget defect no longer reproduces; revise finding')
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('status', '--porcelain=v1') == b''
    git('diff', '--check', BASE, HEAD)
    note('PASS final worktree clean, HEAD unchanged; exact candidate diff whitespace check exit 0')

try:
    main()
finally:
    STEM.with_name(STEM.name + '-evidence.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
