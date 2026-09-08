"""Independent read-only candidate audit and bounded behavioral reproductions."""
from __future__ import annotations
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from dataclasses import replace

ROOT = Path(r'D:/Codex Projects/ai-engineering-template')
CANDIDATE = ROOT / '.worktrees/TASK-017-a1'
REPORT = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-017-a1-c1-R1-checks.txt'
BASE = '759819dedf2dda010530e124c284f0c63f261d15'
HEAD = 'd8930f07ca90cd0dc95ccd452a38d8fcfde8e0c4'
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, str(CANDIDATE / 'src'))
sys.path.insert(1, str(CANDIDATE / 'tests/unit/agents'))
LOG = []
def emit(label, value):
    line = f'{label}: {value}'
    LOG.append(line)
    print(line, flush=True)
def sha(data):
    return hashlib.sha256(data).hexdigest()
def git(*args, cwd=CANDIDATE):
    result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, check=True)
    return result.stdout
def category(action):
    try:
        value = action()
    except DomainException as exc:
        return exc.category.value
    return f'ACCEPTED {value}'

import agents, config, contracts, workflow_ports, domain_values
from domain_values import AgentRunStatus, DomainException, EntityId, Revision, ScopeClaim
from workflow_ports import AcceptanceCriterion, CancelObservation, CancelStatus
from test_agents import adapter_values, capabilities, evidence, observation, output, request, settings

emit('Runtime', f'{sys.version}; executable={sys.executable}; platform={platform.platform()}; jsonschema={importlib.metadata.version("jsonschema")}')
for module in (agents, config, contracts, workflow_ports, domain_values):
    assert Path(module.__file__).resolve().parent == (CANDIDATE / 'src').resolve()
    emit('Origin', f'{module.__name__}={module.__file__}')
assert git('rev-parse', 'HEAD').decode().strip() == HEAD
assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
assert not git('status', '--porcelain=v1')
assert git('merge-base', BASE, HEAD).decode().strip() == BASE
emit('Git identity', f'root={BASE}; candidate={HEAD}; clean; base is merge-base')
manifest_path = ROOT / '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-017-a1-d8930f07ca90.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
assert manifest['base_oid'] == BASE and manifest['head_oid'] == HEAD
assert sha(git('diff', '--binary', BASE, HEAD)) == manifest['diff_sha256']
emit('Raw diff SHA256', manifest['diff_sha256'])
paths = git('diff', '--name-status', '--find-renames', BASE, HEAD).decode().splitlines()
assert paths == [
    'A\t.ai/plans/current/PLAN-001/evidence/implementation/TASK-017.md',
    'A\tsrc/agents.py',
    'A\ttests/unit/agents/test_agents.py',
]
emit('Changed scope', paths)
assert not git('diff', '--check', BASE, HEAD)
for ref in manifest['context_refs']:
    assert sha(git('show', f'{HEAD}:{ref["path"]}')) == ref['sha256'], ref
emit('Context hashes', f'{len(manifest["context_refs"])} / {len(manifest["context_refs"])} match committed bytes')
for ref in manifest['validation_refs']:
    assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref
emit('Validation hashes', f'{len(manifest["validation_refs"])} / {len(manifest["validation_refs"])} match ROOT evidence bytes')
assert sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()) == manifest['policy_model_digest']
for name in ('policy.json', 'agent-models.json'):
    path = '.ai/project/' + name
    assert git('show', f'{BASE}:{path}', cwd=ROOT) == git('show', f'{HEAD}:{path}')
    assert json.loads((ROOT / path).read_text()) == json.loads((CANDIDATE / path).read_text())
emit('Policy/model digest', manifest['policy_model_digest'] + '; committed bytes and semantic worktree values agree')
fingerprint_payload = {key: value for key, value in manifest.items() if key != 'fingerprint'}
actual_fp = sha(json.dumps(fingerprint_payload, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
assert actual_fp == manifest['fingerprint'] == '982055aa72918305c0c44e310bb7daacfc9c3339e8eaacd474a30f3a7f2f7753'
emit('Fingerprint', actual_fp)
bundle = CANDIDATE / '.ai/plans/current/PLAN-001'
graph = json.loads((bundle / 'graph.json').read_text())
isolation = json.loads((bundle / 'reviews/r4-isolation-review.json').read_text())
tasks = [json.loads(path.read_text()) for path in (bundle / 'tasks').glob('*/*.json')]
digest = contracts.structural_task_digest(tasks)
assert digest == graph['task_set_sha256'] == isolation['task_set_sha256']
assert graph['revision'] == isolation['graph_revision'] == 4 and isolation['verdict'] == 'pass'
selected = next(item for item in tasks if item['id'] == 'TASK-017')
assert selected['depends_on'] == next(item for item in graph['nodes'] if item['task_id'] == 'TASK-017')['depends_on'] == ['TASK-003', 'TASK-004', 'TASK-038']
for task in tasks:
    if task['id'] in selected['depends_on']:
        assert task['status'] == 'accepted', task
        emit('Accepted dependency', task['id'] + '=' + task['status'])
emit('Isolation', f'{len(tasks)} tasks; r4 approved structural digest={digest}')
command = json.loads((bundle / 'commands/test.TASK-017.json').read_text())
completed = subprocess.run([sys.executable, *command['argv'][1:]], cwd=CANDIDATE, capture_output=True, text=True, shell=False)
emit('Declared argv', [sys.executable, *command['argv'][1:]])
emit('Declared result', f'exit={completed.returncode}\n{completed.stdout}{completed.stderr}')
assert completed.returncode == 0 and 'Ran 20 tests' in completed.stderr

# Every mutable request identity/content field under one already committed key.
a, p = adapter_values()
r = request()
h = a.start(r, r.idempotency_key)
changes = {
    'id': EntityId('request-other'), 'workflow_id': EntityId('workflow-other'),
    'run_id': EntityId('run-other'), 'attempt_id': EntityId('attempt-other'),
    'task_id': EntityId('TASK-099'), 'plan_id': 'PLAN-099',
    'spec_refs': ('.ai/spec-other.json',), 'role': 'implementation-reviewer',
    'graph_revision': Revision(5), 'base_oid': 'c' * 40, 'current_oid': 'c' * 40,
    'worktree_id': EntityId('worktree-other'), 'scope': ScopeClaim(write_paths=('src/other.py',)),
    'context_ref': '.ai/context-other.json', 'allowed_command_ids': (),
    'acceptance_criteria': (AcceptanceCriterion('AC-OTHER', 'other', 'check'),),
    'dependency_handoffs': (), 'checklist_ids': ('R1-01',), 'model_profile': 'review_high',
    'policy_ref': '.ai/policy-other.json', 'permission_subset': (), 'lease_generation': Revision(8),
}
for field, value in changes.items():
    result = category(lambda: a.start(replace(r, **{field: value}), r.idempotency_key))
    assert result == 'state_conflict', (field, result)
assert p.effect_count == 1
emit('Independent request conflicts', f'{len(changes)} changed fields rejected; one effect retained')

# All immutable handle fences on both methods.
handle_changes = {'project_id': EntityId('other'), 'plan_id': 'PLAN-099', 'run_id': EntityId('other'),
    'request_id': EntityId('other'), 'attempt_id': EntityId('other'), 'lease_generation': Revision(8),
    'adapter_id': 'other', 'idempotency_key': 'other', 'external_handle': 'other'}
for field, value in handle_changes.items():
    changed = replace(h, **{field: value})
    assert category(lambda: a.poll(changed)) == 'state_conflict'
    assert category(lambda: a.cancel(changed)) == 'state_conflict'
emit('Independent handle fences', f'{len(handle_changes) * 2} poll/cancel identity mismatches rejected')

# Invalid observed model variants must not consume the script.
for field, value in {'profile': 'other', 'provider': 'anthropic', 'model_id': 'other', 'capability_rank': 9, 'invocation_id': 'other'}.items():
    a, p = adapter_values(); h = a.start(r, r.idempotency_key)
    model = replace(a.expected_model(h), **{field: value})
    p.script(h, polls=(observation(h, AgentRunStatus.SUCCEEDED, model=model, structured_output=output(h, model)),))
    assert category(lambda: a.poll(h)) == category(lambda: a.poll(h)) == 'validation_failed'
emit('Independent model fences', '5 mismatches rejected twice each without cursor advance')

# Counterexample A: terminal observations do not freeze the effect.
a, p = adapter_values(); h = a.start(r, r.idempotency_key); m = a.expected_model(h)
p.script(h, polls=(observation(h, AgentRunStatus.SUCCEEDED, model=m, structured_output=output(h,m)), observation(h, AgentRunStatus.RUNNING, model=m)))
first = a.poll(h); second = a.poll(h); cancelled = a.cancel(h)
emit('COUNTEREXAMPLE terminal regression', f'poll={first.status.value} -> {second.status.value}; cancel={cancelled.status.value}, quiesced={cancelled.quiesced}')
assert first.status is AgentRunStatus.SUCCEEDED and second.status is AgentRunStatus.RUNNING and cancelled.quiesced
a, p = adapter_values(); h = a.start(r, r.idempotency_key); m = a.expected_model(h)
p.script(h, polls=(observation(h, AgentRunStatus.SUCCEEDED, model=m, structured_output=output(h,m,'output-first')), observation(h, AgentRunStatus.SUCCEEDED, model=m, structured_output=output(h,m,'output-second'))))
emit('COUNTEREXAMPLE terminal result rewrite', f'{a.poll(h).output.id.value} -> {a.poll(h).output.id.value}')
a, p = adapter_values(); h = a.start(r, r.idempotency_key)
p.script(h, cancellations=(CancelObservation(CancelStatus.CANCELLED,h,True,(evidence('stopped'),)),))
stopped = a.cancel(h); subsequent = a.poll(h)
emit('COUNTEREXAMPLE cancel/poll inconsistency', f'cancel={stopped.status.value}, quiesced={stopped.quiesced}; poll={subsequent.status.value}')

# Counterexample B: internally inconsistent saved facts are accepted on restart.
with tempfile.TemporaryDirectory(prefix='TASK-017-a1-c1-R1-fixture-', dir=REPORT.parent) as directory:
    state_path = Path(directory) / 'state.json'
    p = agents.FakeAgentProviderState(state_path); a, _ = adapter_values(provider=p)
    h = a.start(r, r.idempotency_key)
    payload = json.loads(state_path.read_text())
    del a, p
    corrupted = copy.deepcopy(payload); corrupted['effects'][0]['quiesced'] = True
    state_path.write_text(json.dumps(corrupted))
    restored = agents.FakeAgentProviderState(state_path); a, _ = adapter_values(provider=restored)
    recovered = a.start(r, r.idempotency_key); result = a.cancel(recovered)
    emit('COUNTEREXAMPLE unobserved saved quiescence', f'no polls or cancellation observations; modified quiesced=true restored; cancel={result.status.value}, quiesced={result.quiesced}')
    assert result.status is CancelStatus.ALREADY_TERMINAL and result.quiesced
    del a, restored
    corrupted = copy.deepcopy(payload); corrupted['effects'][0]['request']['scope']['unknown_field'] = 'should-reject'
    state_path.write_text(json.dumps(corrupted))
    restored = agents.FakeAgentProviderState(state_path)
    emit('COUNTEREXAMPLE nested unknown saved field', f'request.scope.unknown_field accepted; effect_count={restored.effect_count}')
    del restored
    state_path.write_text(json.dumps(payload))
    p = agents.FakeAgentProviderState(state_path); a, _ = adapter_values(provider=p)
    h = a.start(r, r.idempotency_key); m = a.expected_model(h)
    p.script(h, polls=(observation(h, AgentRunStatus.RUNNING, model=m), observation(h, AgentRunStatus.SUCCEEDED, model=m, structured_output=output(h,m))))
    saved = json.loads(state_path.read_text()); del a, p
    saved['effects'][0]['poll_position'] = 1
    state_path.write_text(json.dumps(saved))
    restored = agents.FakeAgentProviderState(state_path); a, _ = adapter_values(provider=restored)
    result = a.poll(a.start(r,r.idempotency_key))
    emit('COUNTEREXAMPLE cursor without last observation', f'poll_position=1, last_observation=null accepted; first observed poll={result.status.value}')
    del a, restored

assert git('rev-parse', 'HEAD').decode().strip() == HEAD and not git('status', '--porcelain=v1')
emit('Post-check candidate', f'{HEAD}; clean')
REPORT.write_text('\n'.join(LOG) + '\n', encoding='utf-8')
