"""Independent error rollback and real process recovery checks."""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(r'D:/Codex Projects/ai-engineering-template')
CANDIDATE = ROOT / '.worktrees/TASK-017-a1'
REPORT = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-017-a1-c1-R1-recovery.txt'
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, str(CANDIDATE / 'src'))
sys.path.insert(1, str(CANDIDATE / 'tests/unit/agents'))
from agents import FakeAgentProviderState
from domain_values import AgentRunStatus, DomainException, ErrorCategory
from workflow_ports import CancelObservation, CancelStatus
from test_agents import adapter_values, evidence, observation, output, request
lines = []
def emit(value):
    print(value, flush=True)
    lines.append(value)
def assert_write_failure(action, directory, before):
    with patch('agents.os.replace', side_effect=OSError('independent atomic replace failure')):
        try:
            action()
        except DomainException as exc:
            assert exc.category is ErrorCategory.INTERNAL_ERROR
        else:
            raise AssertionError('expected typed persistence failure')
    after = {file.name: file.read_bytes() for file in directory.iterdir()}
    assert after == before, 'file bytes changed or temporary file leaked'

with tempfile.TemporaryDirectory(prefix='TASK-017-a1-c1-R1-io-', dir=REPORT.parent) as temp:
    directory = Path(temp); backing = directory / 'state.json'
    provider = FakeAgentProviderState(backing); adapter, _ = adapter_values(provider=provider)
    r = request()
    assert_write_failure(lambda: adapter.start(r, r.idempotency_key), directory, {})
    assert provider.effect_count == 0
    h = adapter.start(r, r.idempotency_key); m = adapter.expected_model(h)
    emit('PASS: failed start replacement rolls back effect count, leaves no file or temporary file, and normal retry succeeds')
    polls = (observation(h, AgentRunStatus.RUNNING, model=m), observation(h, AgentRunStatus.SUCCEEDED, model=m, structured_output=output(h,m)))
    cancellations = (CancelObservation(CancelStatus.PENDING, h, False, ()), CancelObservation(CancelStatus.CANCELLED,h,True,(evidence('cancelled'),)))
    script = lambda: provider.script(h, polls=polls, cancellations=cancellations)
    assert_write_failure(script, directory, {'state.json': backing.read_bytes()})
    script()
    emit('PASS: failed script replacement rolls back immutable-script commit and permits one successful retry')
    assert_write_failure(lambda: adapter.poll(h), directory, {'state.json': backing.read_bytes()})
    assert adapter.poll(h).status is AgentRunStatus.RUNNING
    emit('PASS: failed poll replacement rolls back cursor and last observation; retry still returns running')
    assert adapter.cancel(h).status is CancelStatus.PENDING
    assert_write_failure(lambda: adapter.cancel(h), directory, {'state.json': backing.read_bytes()})
    state = json.loads(backing.read_text())['effects'][0]
    assert state['cancel_position'] == 1 and not state['quiesced']
    assert adapter.cancel(h).status is CancelStatus.CANCELLED
    emit('PASS: failed cancellation replacement rolls back cancellation cursor and quiescence; retry returns confirmed cancellation')
    del adapter, provider

PROCESS = r'''
import sys
from pathlib import Path
root, backing, action = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
sys.path.insert(0, str(root/'src')); sys.path.insert(1, str(root/'tests/unit/agents'))
from agents import FakeAgentProviderState
from domain_values import AgentRunStatus
from test_agents import adapter_values, observation, output, request
p = FakeAgentProviderState(backing); a, _ = adapter_values(provider=p)
r = request(); h = a.start(r,r.idempotency_key)
if action == 'start':
    m = a.expected_model(h)
    p.script(h, polls=(observation(h,AgentRunStatus.UNKNOWN), observation(h,AgentRunStatus.SUCCEEDED,model=m,structured_output=output(h,m))))
    print(h.external_handle, p.effect_count, 'started')
else:
    observed = a.poll(h)
    print(h.external_handle, p.effect_count, observed.status.value, a.cancel(h).status.value)
'''
with tempfile.TemporaryDirectory(prefix='TASK-017-a1-c1-R1-process-', dir=REPORT.parent) as temp:
    backing = Path(temp)/'state.json'; results=[]
    for action in ('start','poll','poll','poll'):
        result=subprocess.run([sys.executable,'-B','-c',PROCESS,str(CANDIDATE),str(backing),action],cwd=CANDIDATE,capture_output=True,text=True,shell=False)
        assert result.returncode == 0, result.stderr
        results.append(result.stdout.strip().split())
    assert len({item[0] for item in results}) == 1 and all(item[1]=='1' for item in results)
    assert [item[2:] for item in results] == [['started'], ['unknown','pending'], ['succeeded','already_terminal'], ['succeeded','already_terminal']]
    emit('PASS: four separate Python processes recover exactly one handle/effect: start -> unknown/pending -> succeeded/already_terminal -> stable succeeded/already_terminal')
REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8')
