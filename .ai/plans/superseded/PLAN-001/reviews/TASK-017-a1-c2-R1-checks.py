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
REPORT = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-017-a1-c2-R1-checks.txt'
BASE = 'e2faa2b8f3ce8f63119227edd35fa837b82d5ee8'
HEAD = 'e79df3b8d071a7e3a3c7874cf0cacb6e704c0205'
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
manifest_path = ROOT / '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-017-a1-e79df3b8d071.json'
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
assert actual_fp == manifest['fingerprint'] == 'b1d15eb23f6efe4625c3489e708c0c5cf6708b479698277a7b0d55f849cbf488'
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
assert completed.returncode == 0 and 'Ran 27 tests' in completed.stderr

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


# Fresh review: independently replay the exact prior failures with fixed expectations.
for status in (AgentRunStatus.SUCCEEDED, AgentRunStatus.FAILED, AgentRunStatus.CANCELLED):
    a,p=adapter_values(); h=a.start(r,r.idempotency_key); m=a.expected_model(h)
    terminal=observation(h,status,model=m,structured_output=output(h,m,'first') if status is AgentRunStatus.SUCCEEDED else None)
    p.script(h,polls=(terminal,observation(h,AgentRunStatus.RUNNING,model=m),observation(h,AgentRunStatus.SUCCEEDED,model=m,structured_output=output(h,m,'second'))),cancellations=(CancelObservation(CancelStatus.CANCELLED,h,True,(evidence('stop'),)),))
    first=a.poll(h)
    for _ in range(3):
        assert a.poll(h)==first
        assert a.cancel(h).status is CancelStatus.ALREADY_TERMINAL
    e=p._by_external_handle[h.external_handle]
    assert (e.poll_position,e.cancel_position,e.quiesced)==(1,0,True)
emit('Fixed terminal poll cases','succeeded/failed/cancelled stable across repeated poll/cancel; output retained; cursors 1/0')
for status in (CancelStatus.CANCELLED,CancelStatus.ALREADY_TERMINAL):
    a,p=adapter_values(); h=a.start(r,r.idempotency_key)
    p.script(h,cancellations=(CancelObservation(status,h,True,(evidence('stop'),)),CancelObservation(CancelStatus.PENDING,h,False,())))
    first=a.cancel(h)
    for _ in range(3):
        assert a.cancel(h)==first
        assert category(lambda:a.poll(h))=='state_conflict'
    e=p._by_external_handle[h.external_handle]
    assert (e.poll_position,e.cancel_position,e.quiesced)==(0,1,True)
emit('Fixed terminal cancellation cases','cancelled/already_terminal stable; later poll rejected; cursors 0/1')

# Corrupt saved history through the actual file admission boundary, without live concurrent owners.
with tempfile.TemporaryDirectory(prefix='TASK-017-a1-c2-R1-corruption-',dir=REPORT.parent) as directory:
    state=Path(directory)/'state.json'
    p=agents.FakeAgentProviderState(state); a,_=adapter_values(provider=p); h=a.start(r,r.idempotency_key); m=a.expected_model(h)
    started=json.loads(state.read_text())
    p.script(h,polls=(observation(h,AgentRunStatus.RUNNING,model=m),observation(h,AgentRunStatus.SUCCEEDED,model=m,structured_output=output(h,m))),cancellations=(CancelObservation(CancelStatus.PENDING,h,False,()),CancelObservation(CancelStatus.CANCELLED,h,True,(evidence('stop'),))))
    scripted=json.loads(state.read_text())
    a.poll(h); running=json.loads(state.read_text())
    a.poll(h); terminal=json.loads(state.read_text())
    del a,p
    cases=[]
    def case(label,payload,mutate):
        value=copy.deepcopy(payload); mutate(value['effects'][0]); cases.append((label,value))
    case('prior forged quiescence',started,lambda e:e.update(quiesced=True))
    case('prior cursor without last observation',scripted,lambda e:e.update(poll_position=1))
    case('prior unknown request.scope field',started,lambda e:e['request']['scope'].update(unknown=True))
    case('unknown criterion field',started,lambda e:e['request']['acceptance_criteria'][0].update(unknown=True))
    case('missing scope field',started,lambda e:e['request']['scope'].pop('resources'))
    case('nonboolean script committed',started,lambda e:e.update(script_committed=1))
    case('noninteger poll cursor',scripted,lambda e:e.update(poll_position=True))
    case('uncommitted installed script',scripted,lambda e:e.update(script_committed=False))
    case('terminal quiescence lost',terminal,lambda e:e.update(quiesced=False))
    case('last observation lost',running,lambda e:e.update(last_observation=None))
    case('last observation future value',running,lambda e:e.update(last_observation=terminal['effects'][0]['last_observation']))
    case('last evidence digest changed',running,lambda e:e['last_observation']['evidence_refs'][-1].update(sha256='e'*64))
    case('last simulation effort changed',running,lambda e:e['last_observation']['evidence_refs'][-1]['metadata'].update(submitted_reasoning_effort='xhigh'))
    case('both poll and cancel terminals',terminal,lambda e:e.update(cancel_position=2))
    case('consumed cancel other identity',running,lambda e:(e.update(cancel_position=1),e['cancel_script'][0]['handle'].update(request_id='other')))
    case('expected model invocation changed',started,lambda e:e['expected_model'].update(invocation_id='other'))
    case('configured profile mismatch',started,lambda e:e['configured_model'].update(name='other'))
    # Mutate both saved last and consumed script to defeat mere last-value equality checks.
    for field,value in {'profile':'other','provider':'other','model_id':'other','capability_rank':9,'invocation_id':'other'}.items():
        case('consumed model '+field,running,lambda e,f=field,v=value:[o['run']['actual_model'].update({f:v}) for o in (e['poll_script'][0],e['last_observation'])])
    case('consumed request_ref mismatch',running,lambda e:[o['run'].update(request_ref='agent-request:PLAN-099:other') for o in (e['poll_script'][0],e['last_observation'])])
    case('consumed output_ref mismatch',terminal,lambda e:[o['run'].update(output_ref='agent-output:PLAN-001:other') for o in (e['poll_script'][1],e['last_observation'])])
    for label,payload in cases:
        state.write_text(json.dumps(payload),encoding='utf-8')
        assert category(lambda:agents.FakeAgentProviderState(state))=='validation_failed', label
    emit('Fresh saved-state corruption cases',f'{len(cases)} rejected with validation_failed, including all three prior restoration failures')

assert git('rev-parse','HEAD').decode().strip()==HEAD and not git('status','--porcelain=v1')
emit('Post-check candidate',f'{HEAD}; clean')
REPORT.write_text('\n'.join(LOG)+'\n',encoding='utf-8')
