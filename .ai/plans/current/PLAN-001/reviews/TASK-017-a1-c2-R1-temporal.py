"""Independent finite-state exploration of poll/cancel ordering and restore admission."""
from __future__ import annotations
import copy
import itertools
import json
import os
from pathlib import Path
import sys
import tempfile
sys.dont_write_bytecode=True
os.environ['PYTHONDONTWRITEBYTECODE']='1'
ROOT=Path(__file__).resolve().parents[5]
CANDIDATE=ROOT/'.worktrees/TASK-017-a1'
REPORT=Path(__file__).with_suffix('.txt')
sys.path.insert(0,str(CANDIDATE/'src'))
sys.path.insert(1,str(CANDIDATE/'tests/unit/agents'))
from agents import FakeAgentProviderState
from domain_values import AgentRunStatus, DomainError, DomainException, ErrorCategory
from workflow_ports import CancelObservation, CancelStatus
from test_agents import adapter_values, evidence, observation, output, request

PS=AgentRunStatus; CS=CancelStatus
poll_options=((),(PS.UNKNOWN,PS.RUNNING),(PS.RUNNING,PS.SUCCEEDED),(PS.SUCCEEDED,PS.RUNNING),(PS.FAILED,PS.RUNNING),(PS.CANCELLED,PS.SUCCEEDED),(PS.SUCCEEDED,PS.SUCCEEDED))
cancel_options=((),(CS.PENDING,CS.CANCELLED),(CS.CANCELLED,CS.PENDING),(CS.UNKNOWN,CS.PENDING),(CS.FAILED,CS.ALREADY_TERMINAL))
terminal={PS.SUCCEEDED,PS.FAILED,PS.CANCELLED}
confirmed={CS.CANCELLED,CS.ALREADY_TERMINAL}

def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'))
def state_key(value):
    e=value['effects'][0]
    return canonical({k:e[k] for k in ('poll_position','cancel_position','last_observation','quiesced')})

transitions=0; reachable_count=0; admitted=0; rejected=0
with tempfile.TemporaryDirectory(prefix='TASK-017-a1-c2-R1-temporal-',dir=REPORT.parent) as directory:
    state=Path(directory)/'state.json'
    for pstates,cstates in itertools.product(poll_options,cancel_options):
        initials=[]; variants={}
        for late in (False,True):
            state.unlink(missing_ok=True)
            p=FakeAgentProviderState(state); a,_=adapter_values(provider=p); r=request(); h=a.start(r,r.idempotency_key); m=a.expected_model(h)
            if late: assert a.poll(h).status is PS.QUEUED
            polls=tuple(observation(h,s,model=m,structured_output=output(h,m,f'output-{i}') if s is PS.SUCCEEDED else None) for i,s in enumerate(pstates))
            cancels=tuple(CancelObservation(s,h,s in confirmed,(evidence(f'c-{i}'),),DomainError(ErrorCategory.TRANSIENT_PROVIDER,'scripted unresolved cancel',True) if s in (CS.UNKNOWN,CS.FAILED) else None) for i,s in enumerate(cstates))
            p.script(h,polls=polls,cancellations=cancels)
            initials.append(json.loads(state.read_text()))
            del a,p
        pending=initials[:]; reachable={state_key(v):v for v in initials}
        # Explore every finite public poll/cancel sequence; exact repeats reach existing nodes.
        while pending:
            previous=pending.pop()
            e=previous['effects'][0]
            variants[canonical(e['last_observation'])]=e['last_observation']
            for action in ('poll','cancel'):
                state.write_text(canonical(previous),encoding='utf-8')
                p=FakeAgentProviderState(state); a,_=adapter_values(provider=p)
                assert a.start(r,r.idempotency_key)==h and p.effect_count==1
                poll_terminal=e['last_observation'] is not None and PS(e['last_observation']['status']) in terminal
                blocked=action=='poll' and e['quiesced'] and not poll_terminal
                try:
                    result=getattr(a,action)(h)
                except DomainException as exc:
                    assert blocked and exc.category is ErrorCategory.STATE_CONFLICT
                    assert json.loads(state.read_text())==previous
                else:
                    assert not blocked
                    if action=='poll':
                        expected=PS(e['last_observation']['status']) if poll_terminal else (pstates[min(e['poll_position'],len(pstates)-1)] if pstates else PS.QUEUED)
                        assert result.status is expected
                        if poll_terminal:
                            from agents import _wire
                            assert _wire(result)==e['last_observation']
                    else:
                        expected=CS.ALREADY_TERMINAL if poll_terminal else (CS(e['cancel_script'][e['cancel_position']-1]['status']) if e['quiesced'] else (cstates[min(e['cancel_position'],len(cstates)-1)] if cstates else CS.PENDING))
                        assert result.status is expected and result.quiesced==(expected in confirmed)
                after=json.loads(state.read_text()); key=state_key(after)
                if key not in reachable:
                    reachable[key]=after; pending.append(after)
                del a,p
                transitions+=1
        reachable_count+=len(reachable)
        # Enumerate candidate-derived cursor/last/quiescence combinations, compare file admission
        # against states reached by some real public ordering (including default queued before script).
        for pp,cp,last,q in itertools.product(range(len(pstates)+1),range(len(cstates)+1),variants.values(),(False,True)):
            value=copy.deepcopy(initials[0]); e=value['effects'][0]
            e.update(poll_position=pp,cancel_position=cp,last_observation=last,quiesced=q)
            expected=state_key(value) in reachable
            state.write_text(canonical(value),encoding='utf-8')
            try:
                restored=FakeAgentProviderState(state)
            except DomainException as exc:
                assert not expected and exc.category is ErrorCategory.VALIDATION_FAILED,(pstates,cstates,pp,cp,q,last,exc)
                rejected+=1
            else:
                assert expected,(pstates,cstates,pp,cp,q,last)
                admitted+=1; del restored
report=f'PASS: {len(poll_options)*len(cancel_options)} poll/cancel script combinations; {reachable_count} reachable saved states; {transitions} public transitions checked against independent status/terminal expectations.\nPASS: finite admission matrix: {admitted} reachable combinations admitted, {rejected} unreachable cursor/last/quiescence combinations rejected with validation_failed. Included every poll status, every cancel status, changed successful output, empty/exhausted/partial scripts, both terminal orderings, and default queued before script.\n'
REPORT.write_text(report,encoding='utf-8'); print(report)
