"""Additional independent corruption, unconsumed fault and provenance boundary checks."""
from __future__ import annotations
from dataclasses import replace
from pathlib import Path
import hashlib
import json
import os
import sys
import tempfile
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
ROOT=Path(__file__).resolve().parents[5]; CANDIDATE=ROOT/'.worktrees/TASK-017-a1'
REPORT=Path(__file__).with_suffix('.txt')
sys.path.insert(0,str(CANDIDATE/'src')); sys.path.insert(1,str(CANDIDATE/'tests/unit/agents'))
from agents import FakeAgentProviderState
from domain_values import AgentRunStatus, DomainException, ErrorCategory
from test_agents import adapter_values, request, observation, output
lines=[]
graph=json.loads((CANDIDATE/'.ai/plans/current/PLAN-001/graph.json').read_text())
projection={k:graph[k] for k in ('schema_version','kind','id','plan_id','revision','nodes','task_set_sha256')}
digest=hashlib.sha256(json.dumps(projection,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
assert digest=='5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
lines.append('PASS: approved r4 structural graph digest '+digest)
with tempfile.TemporaryDirectory(prefix='TASK-017-a1-c2-R1-edges-',dir=REPORT.parent) as temp:
    path=Path(temp)/'state.json'
    for field,value in {'profile':'other','provider':'other','model_id':'other','capability_rank':9,'invocation_id':'other'}.items():
        path.unlink(missing_ok=True)
        p=FakeAgentProviderState(path); a,_=adapter_values(provider=p); r=request(); h=a.start(r,r.idempotency_key); model=replace(a.expected_model(h),**{field:value})
        # Install a future fault after a valid default queued result, then consume unknown.
        assert a.poll(h).status is AgentRunStatus.QUEUED
        p.script(h,polls=(observation(h,AgentRunStatus.UNKNOWN),observation(h,AgentRunStatus.SUCCEEDED,model=model,structured_output=output(h,model))))
        assert a.poll(h).status is AgentRunStatus.UNKNOWN
        before=path.read_bytes(); del a,p
        for _ in range(2):
            p=FakeAgentProviderState(path); a,_=adapter_values(provider=p)
            assert a.start(r,r.idempotency_key)==h
            try: a.poll(h)
            except DomainException as exc: assert exc.category is ErrorCategory.VALIDATION_FAILED
            else: raise AssertionError('future invalid model accepted')
            assert path.read_bytes()==before and json.loads(before)['effects'][0]['poll_position']==1
            del a,p
lines.append('PASS: five unconsumed model-identity mutations survive restore after queued/late-script/unknown; every invalid poll rejected twice across sequential provider recreation, with byte-identical backing state and cursor 1.')
REPORT.write_text('\n'.join(lines)+'\n',encoding='utf-8'); print('\n'.join(lines))
