"""R1-owned real-loader probes; imports no candidate test helpers or old probes."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import replace
from datetime import datetime, UTC, timedelta
from importlib.metadata import version
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-017-a2'
sys.path.insert(0, str(TREE/'src'))
import agents, config, contracts, domain_values, workflow_ports
from agents import AgentAdapterCapabilities, DeterministicFakeAgentAdapter, FakeAgentProviderState
from domain_values import AgentRunStatus, AgentOutputStatus, DomainError, DomainException, ErrorCategory, EvidenceRef, ScopeClaim
from workflow_ports import AgentHandle, AgentRequest, AgentObservation, AgentOutputRecord, AgentRunRecord, CancelObservation, CancelStatus, AcceptanceCriterion

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',',':'), ensure_ascii=False).encode()

def fixture(path, mapped, provider='openai'):
    shutil.copytree(TREE/'schemas/v1', path/'schemas/v1')
    (path/'.ai/project').mkdir(parents=True)
    shutil.copyfile(TREE/'.ai/framework.json', path/'.ai/framework.json')
    models=json.loads((TREE/'.ai/project/agent-models.json').read_bytes())
    policy=json.loads((TREE/'.ai/project/policy.json').read_bytes())
    models['active_provider']=provider
    for catalog in models['providers'].values():
        catalog['profiles']['implementation_custom']=copy.deepcopy(catalog['profiles']['implementation'])
        catalog['profiles']['implementation_other']=copy.deepcopy(catalog['profiles']['implementation'])
    selected='implementation_custom' if mapped else 'implementation'
    models['policy_profile_map']['implementation']=selected
    for item in policy['model_profiles']:
        item['configured']=item['name'] in ('implementation','review_high')
        if item['configured']:
            profile=models['providers'][provider]['profiles'][models['policy_profile_map'][item['name']]]
            item.update(provider=provider, model_id=profile['model_id'], capability_rank=profile['capability_rank'])
    (path/'.ai/project/policy.json').write_bytes(encode(policy))
    (path/'.ai/project/agent-models.json').write_bytes(encode(models))
    return path

def load(path):
    return config.load_project_settings(path, config.load_installation_record(path))

def request():
    return AgentRequest(id='r1-request', workflow_id='r1-workflow', run_id='r1-run', attempt_id='TASK-017-a2', task_id='TASK-017', plan_id='PLAN-001', spec_refs=('.ai/plans/current/PLAN-001/spec.json',), role='implementer', graph_revision=4, base_oid='b90556d92e0f37e664d685b4af85c43fc8143d81', current_oid='b7593f11961aa6f5c3a927f3c49af32c4fa93971', worktree_id='TASK-017-a2', scope=ScopeClaim(write_paths=('src/agents.py',)), context_ref='.ai/context/r1.json', allowed_command_ids=('test.TASK-017',), acceptance_criteria=(AcceptanceCriterion('TASK-017-AC1','deterministic execution','R1 independent probe'),), dependency_handoffs=('handoff:TASK-003','handoff:TASK-004','handoff:TASK-038'), checklist_ids=(), model_profile='implementation', policy_ref='.ai/project/policy.json', permission_subset=('tests',), lease_generation=17, idempotency_key='r1-key')

def capabilities(settings):
    return AgentAdapterCapabilities(roles=('implementer','implementation-reviewer'), permissions=('tests',), command_ids=('test.TASK-017',), model_profiles=settings.models.provider().profiles)

def adapter(settings, state, caps=None):
    return DeterministicFakeAgentAdapter(project_id='r1-project', settings=settings, capabilities=capabilities(settings) if caps is None else caps, provider_state=state)

def observation(handle, model, status, name='r1-output'):
    now=datetime(2026,9,8,12,tzinfo=UTC)
    end=now+timedelta(minutes=1)
    terminal=status in (AgentRunStatus.SUCCEEDED,AgentRunStatus.FAILED,AgentRunStatus.CANCELLED)
    error=DomainError(ErrorCategory.TRANSIENT_PROVIDER,'simulated uncertain or unsuccessful result',retryable=status is AgentRunStatus.UNKNOWN) if status in (AgentRunStatus.UNKNOWN,AgentRunStatus.FAILED,AgentRunStatus.CANCELLED) else None
    out=AgentOutputRecord(id=name,request_id=handle.request_id,attempt_id=handle.attempt_id,status=AgentOutputStatus.SUCCEEDED,actual_model=model,artifact_refs=('.ai/evidence/r1-result.md',),command_evidence_refs=(),discoveries=(),scope_change_requests=(),error_category=None,summary='independent deterministic result') if status is AgentRunStatus.SUCCEEDED else None
    run=AgentRunRecord(id='r1-agent-run',request_ref='agent-request:PLAN-001:r1-request',attempt_id=handle.attempt_id,status=status,adapter_id=handle.adapter_id,external_handle=handle.external_handle,actual_model=model,started_at=now if status not in (AgentRunStatus.QUEUED,AgentRunStatus.UNKNOWN,AgentRunStatus.CANCELLED) else None,finished_at=end if terminal else None,output_ref='agent-output:PLAN-001:'+name if out else None,error_category='transient_provider' if status in (AgentRunStatus.FAILED,AgentRunStatus.UNKNOWN) else None,lease_generation=handle.lease_generation)
    return AgentObservation(status,handle,run,out,(EvidenceRef('.ai/evidence/r1-simulation.json','1'*64),),error)

def cancellation(handle,status):
    confirmed=status in (CancelStatus.CANCELLED,CancelStatus.ALREADY_TERMINAL)
    error=DomainError(ErrorCategory.TRANSIENT_PROVIDER,'simulated unresolved cancellation') if status in (CancelStatus.FAILED,CancelStatus.UNKNOWN) else None
    return CancelObservation(status,handle,confirmed,(EvidenceRef('.ai/evidence/r1-cancellation.json','2'*64),),error)

def reject(action, category):
    try:
        action()
    except DomainException as exc:
        assert exc.category == category, (exc.category,category,str(exc))
        return
    raise AssertionError('required rejection did not occur')

def actions(a, handle):
    req=request()
    return (lambda:a.start(req,req.idempotency_key),lambda:a.poll(handle),lambda:a.cancel(handle),lambda:a.expected_model(handle))

def snapshot(path):
    return json.loads(path.read_bytes())['effects'][0]

def fresh_child(project, phase):
    settings=load(project)
    state_path=project/'process-state.json'
    state=FakeAgentProviderState(state_path)
    a=adapter(settings,state)
    req=request()
    if phase == 'start':
        handle=a.start(req,req.idempotency_key)
        assert a.poll(handle).status is AgentRunStatus.QUEUED
        model=a.expected_model(handle)
        state.script(handle,polls=(observation(handle,model,AgentRunStatus.UNKNOWN),observation(handle,model,AgentRunStatus.RUNNING),observation(handle,model,AgentRunStatus.SUCCEEDED),observation(handle,model,AgentRunStatus.SUCCEEDED,'replacement-output')))
        observed=a.poll(handle)
        assert observed.status is AgentRunStatus.UNKNOWN
        assert a.cancel(handle).status is CancelStatus.PENDING
    else:
        # Persisted public handle used before retrying start; exercises admission.
        handle=AgentHandle(**snapshot(state_path)['handle'])
        model=a.expected_model(handle)
        observed=a.poll(handle)
        assert observed.status is (AgentRunStatus.RUNNING if phase == 'continue' else AgentRunStatus.SUCCEEDED)
    assert a.start(req,req.idempotency_key) == handle and state.effect_count == 1
    selected=settings.configured_model(req.model_profile)
    assert model.profile == req.model_profile == 'implementation'
    if phase == 'finish':
        before=state_path.read_bytes()
        assert a.poll(handle) == observed
        assert observed.output.id.value == 'r1-output'
        assert a.cancel(handle).status is CancelStatus.ALREADY_TERMINAL
        assert state_path.read_bytes() == before
    result={'phase':phase,'pid':os.getpid(),'runtime':platform.python_version(),'executable':sys.executable,'origins':{m.__name__:m.__file__ for m in (agents,config,contracts,domain_values,workflow_ports)},'effect_count':state.effect_count,'handle':handle.external_handle,'requested_profile':req.model_profile,'resolved_profile':selected.name,'expected_profile':model.profile,'provider':selected.provider,'reasoning_effort':selected.reasoning_effort,'effort':selected.effort,'poll':observed.status.value,'cursor':snapshot(state_path)['poll_position'],'settings_sha256':sha((project/'.ai/project/policy.json').read_bytes()+(project/'.ai/project/agent-models.json').read_bytes())}
    for origin in result['origins'].values():
        assert Path(origin).resolve().parent == (TREE/'src').resolve()
    print(json.dumps(result,sort_keys=True))

def start_file(settings, path):
    state=FakeAgentProviderState(path)
    a=adapter(settings,state)
    handle=a.start(request(),'r1-key')
    return state,a,handle

def negative_bindings(project):
    settings=load(project)
    seed_path=project/'binding-seed.json'
    state,a,handle=start_file(settings,seed_path)
    seed=json.loads(seed_path.read_bytes())
    del state,a
    count=0
    for field,value in [('name','unrelated-saved-name'),('reasoning_effort','medium'),('effort','high'),('provider','other-provider'),('model_id','other-model'),('capability_rank',77)]:
        payload=copy.deepcopy(seed)
        effect=payload['effects'][0]
        effect['configured_model'][field]=value
        if field in ('provider','model_id','capability_rank'):
            effect['expected_model'][field]=value
        path=project/('bad-binding-'+field+'.json')
        path.write_bytes(encode(payload))
        before=path.read_bytes()
        state=FakeAgentProviderState(path)  # Intrinsic-only layer must hydrate.
        a=adapter(settings,state)
        for action in actions(a,handle):
            for _ in range(2):
                reject(action,ErrorCategory.VALIDATION_FAILED)
                assert path.read_bytes()==before
                internal=state._by_external_handle[handle.external_handle]
                assert (internal.poll_position,internal.cancel_position)==(0,0)
                count+=1
        del action,a,state
    return count

def admission_after_terminal(project):
    settings=load(project)
    path=project/'terminal-admission.json'
    state,a,handle=start_file(settings,path)
    model=a.expected_model(handle)
    state.script(handle,polls=(observation(handle,model,AgentRunStatus.SUCCEEDED),))
    a.poll(handle)
    before=path.read_bytes()
    models_path=project/'.ai/project/agent-models.json'
    original=models_path.read_bytes()
    count=0
    # New mapping, same model/rank/effort, then new effort with matching capabilities.
    for mutation in ('mapping','effort'):
        models=json.loads(original)
        if mutation == 'mapping':
            models['policy_profile_map']['implementation']='implementation_other'
        else:
            models['providers']['openai']['profiles']['implementation_custom']['reasoning_effort']='medium'
        models_path.write_bytes(encode(models))
        changed=load(project)
        other=adapter(changed,state)
        for action in actions(other,handle):
            reject(action,ErrorCategory.VALIDATION_FAILED)
            assert path.read_bytes()==before
            count+=1
    models_path.write_bytes(original)
    for field,value in [('roles',('implementation-reviewer',)),('permissions',()),('command_ids',()),('queryable',False),('cancellable',False),('reports_model_provenance',False)]:
        caps=replace(capabilities(settings),**{field:value})
        other=adapter(settings,state,caps)
        for action in actions(other,handle):
            reject(action,ErrorCategory.UNSUPPORTED_CAPABILITY)
            assert path.read_bytes()==before
            count+=1
    return count

def temporal_and_corruption(project):
    settings=load(project)
    path=project/'history-seed.json'
    state,a,handle=start_file(settings,path)
    model=a.expected_model(handle)
    fresh=json.loads(path.read_bytes())
    assert a.poll(handle).status is AgentRunStatus.QUEUED
    queued=json.loads(path.read_bytes())
    state.script(handle,polls=(observation(handle,model,AgentRunStatus.RUNNING),observation(handle,model,AgentRunStatus.SUCCEEDED),observation(handle,model,AgentRunStatus.RUNNING)),cancellations=(cancellation(handle,CancelStatus.PENDING),cancellation(handle,CancelStatus.CANCELLED)))
    late=json.loads(path.read_bytes())
    a.poll(handle)
    running=json.loads(path.read_bytes())
    assert a.cancel(handle).status is CancelStatus.PENDING
    partial=json.loads(path.read_bytes())
    success=a.poll(handle)
    terminal=json.loads(path.read_bytes())
    assert a.poll(handle)==success and a.cancel(handle).status is CancelStatus.ALREADY_TERMINAL
    assert snapshot(path)['cancel_position']==1 and snapshot(path)['poll_position']==2
    del state,a
    valid=[fresh,queued,late,running,partial,terminal]
    corrupt=[]
    def case(seed, mutate):
        payload=copy.deepcopy(seed)
        mutate(payload['effects'][0])
        corrupt.append(payload)
    case(fresh,lambda e:e.update(quiesced=True))
    case(late,lambda e:e.update(poll_position=1,last_observation=None))
    case(running,lambda e:e.update(poll_position=0))
    case(running,lambda e:e.update(last_observation=None))
    case(running,lambda e:e.update(script_committed=False))
    case(terminal,lambda e:e.update(quiesced=False))
    case(terminal,lambda e:e.update(poll_position=3))
    case(terminal,lambda e:e.update(cancel_position=2))
    case(fresh,lambda e:e['request']['scope'].update(extra=True))
    case(fresh,lambda e:e['request']['acceptance_criteria'][0].update(extra=True))
    case(running,lambda e:e['poll_script'][0]['run'].update(extra=True))
    case(running,lambda e:e['last_observation']['evidence_refs'][0].update(extra=True))
    case(fresh,lambda e:e['expected_model'].update(profile='wrong-policy'))
    case(fresh,lambda e:e['expected_model'].update(invocation_id='wrong-invocation'))
    case(fresh,lambda e:e['handle'].update(external_handle='wrong-handle'))
    case(fresh,lambda e:e['request'].update(lease_generation=18))
    check_path=project/'history-check.json'
    for payload in valid:
        check_path.write_bytes(encode(payload))
        restored=FakeAgentProviderState(check_path)
        ra=adapter(settings,restored)
        assert ra.start(request(),'r1-key')==handle
        del ra,restored
    for payload in corrupt:
        check_path.write_bytes(encode(payload))
        before=check_path.read_bytes()
        reject(lambda:FakeAgentProviderState(check_path),ErrorCategory.VALIDATION_FAILED)
        assert check_path.read_bytes()==before
    # All terminal poll statuses, first result stable, later incompatible poll ignored.
    terminal_cases=0
    for status in (AgentRunStatus.SUCCEEDED,AgentRunStatus.FAILED,AgentRunStatus.CANCELLED):
        p=project/('terminal-'+status.value+'.json')
        state,a,h=start_file(settings,p)
        m=a.expected_model(h)
        state.script(h,polls=(observation(h,m,status),observation(h,m,AgentRunStatus.RUNNING)))
        first=a.poll(h)
        before=p.read_bytes()
        assert a.poll(h)==first and a.cancel(h).quiesced
        assert p.read_bytes()==before
        del a,state
        state=FakeAgentProviderState(p)
        a=adapter(settings,state)
        assert a.poll(h)==first
        terminal_cases+=1
    # Confirmed cancellation stays stable; incompatible future poll never advances.
    for status in (CancelStatus.CANCELLED,CancelStatus.ALREADY_TERMINAL):
        p=project/('cancel-'+status.value+'.json')
        state,a,h=start_file(settings,p)
        state.script(h,polls=(observation(h,a.expected_model(h),AgentRunStatus.RUNNING),),cancellations=(cancellation(h,status),cancellation(h,CancelStatus.PENDING)))
        first=a.cancel(h)
        before=p.read_bytes()
        assert a.cancel(h)==first
        reject(lambda:a.poll(h),ErrorCategory.STATE_CONFLICT)
        assert p.read_bytes()==before
        del a,state
        state=FakeAgentProviderState(p)
        a=adapter(settings,state)
        assert a.cancel(h)==first
        reject(lambda:a.poll(h),ErrorCategory.STATE_CONFLICT)
        assert p.read_bytes()==before
        terminal_cases+=1
    # Empty scripts and exhausted nonterminal scripts restore and continue.
    for empty in (True,False):
        p=project/('exhausted-'+str(empty)+'.json')
        state,a,h=start_file(settings,p)
        polls=() if empty else (observation(h,a.expected_model(h),AgentRunStatus.RUNNING),)
        state.script(h,polls=polls)
        first=a.poll(h)
        del a,state
        state=FakeAgentProviderState(p)
        a=adapter(settings,state)
        assert a.poll(h)==first
    return {'legitimate_history_snapshots':len(valid),'intrinsic_corruptions_rejected':len(corrupt),'terminal_sequences':terminal_cases,'empty_exhausted_controls':2}

def fault_provenance(project):
    settings=load(project)
    count=0
    for field,value in [('profile','wrong-policy'),('provider','other-provider'),('model_id','other-model'),('capability_rank',99),('invocation_id','wrong-invocation')]:
        path=project/('future-'+field+'.json')
        state,a,h=start_file(settings,path)
        good=a.expected_model(h)
        bad=replace(good,**{field:value})
        assert a.poll(h).status is AgentRunStatus.QUEUED
        state.script(h,polls=(observation(h,good,AgentRunStatus.UNKNOWN),observation(h,bad,AgentRunStatus.RUNNING)))
        assert a.poll(h).status is AgentRunStatus.UNKNOWN
        del a,state
        before=path.read_bytes()
        for _ in range(2):
            state=FakeAgentProviderState(path)
            a=adapter(settings,state)
            assert a.start(request(),'r1-key')==h
            reject(lambda:a.poll(h),ErrorCategory.VALIDATION_FAILED)
            assert path.read_bytes()==before and snapshot(path)['poll_position']==1
            del a,state
            count+=1
    return count

def atomic_rollback(project):
    settings=load(project)
    path=project/'atomic.json'
    state=FakeAgentProviderState(path)
    a=adapter(settings,state)
    with patch('agents.os.replace',side_effect=OSError('R1 injected replacement failure')):
        reject(lambda:a.start(request(),'r1-key'),ErrorCategory.INTERNAL_ERROR)
    assert state.effect_count==0 and not path.exists()
    h=a.start(request(),'r1-key')
    m=a.expected_model(h)
    polls=(observation(h,m,AgentRunStatus.RUNNING),)
    cancels=(cancellation(h,CancelStatus.CANCELLED),)
    before=path.read_bytes()
    with patch('agents.os.replace',side_effect=OSError('R1 injected replacement failure')):
        reject(lambda:state.script(h,polls=polls,cancellations=cancels),ErrorCategory.INTERNAL_ERROR)
    assert path.read_bytes()==before
    state.script(h,polls=polls,cancellations=cancels)
    before=path.read_bytes()
    with patch('agents.os.replace',side_effect=OSError('R1 injected replacement failure')):
        reject(lambda:a.poll(h),ErrorCategory.INTERNAL_ERROR)
    assert path.read_bytes()==before
    assert state._by_external_handle[h.external_handle].poll_position==0
    assert a.poll(h).status is AgentRunStatus.RUNNING
    before=path.read_bytes()
    with patch('agents.os.replace',side_effect=OSError('R1 injected replacement failure')):
        reject(lambda:a.cancel(h),ErrorCategory.INTERNAL_ERROR)
    assert path.read_bytes()==before
    assert not state._by_external_handle[h.external_handle].quiesced
    assert a.cancel(h).quiesced
    assert not list(project.glob('.atomic.json.*.tmp'))
    return 4

def main():
    log={'runtime':sys.version,'executable':sys.executable,'platform':platform.platform(),'jsonschema':version('jsonschema'),'fresh_processes':[]}
    with tempfile.TemporaryDirectory(prefix='r1-017-c3-') as temporary:
        base=Path(temporary)
        providers=('openai',) if '--linux-focused' in sys.argv else ('openai','anthropic')
        for provider in providers:
            for mapped in (False,True):
                project=fixture(base/(provider+str(mapped)),mapped,provider)
                results=[]
                for phase in ('start','continue','finish'):
                    run=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(project),phase],cwd=TREE,capture_output=True,text=True,shell=False)
                    assert run.returncode==0,(run.stdout,run.stderr)
                    results.append(json.loads(run.stdout))
                assert len({r['pid'] for r in results})==3
                for key in ('handle','settings_sha256','effect_count','requested_profile','resolved_profile','expected_profile'):
                    assert len({r[key] for r in results})==1,key
                assert results[0]['resolved_profile']==('implementation_custom' if mapped else 'implementation')
                assert [r['cursor'] for r in results]==[1,2,3]
                log['fresh_processes'].append(results)
        project=fixture(base/'boundaries',True)
        log['atomic_replacement_rollback']=atomic_rollback(project)
        if '--linux-focused' not in sys.argv:
            log['binding_rejections']=negative_bindings(project)
            log['terminal_settings_capability_rejections']=admission_after_terminal(project)
            log['temporal']=temporal_and_corruption(project)
            log['unconsumed_provenance_rejections_across_restarts']=fault_provenance(project)
    print(json.dumps(log,indent=2,sort_keys=True))

if __name__=='__main__':
    if '--child' in sys.argv:
        fresh_child(Path(sys.argv[2]),sys.argv[3])
    else:
        main()
