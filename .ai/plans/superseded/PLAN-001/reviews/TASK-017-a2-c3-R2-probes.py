"""Independent R2 cross-contract probes; no task tests or R1 helpers imported."""
from pathlib import Path
from datetime import datetime, UTC, timedelta
from dataclasses import fields, is_dataclass, replace
from enum import Enum
import copy
import hashlib
import inspect
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT/'.worktrees/TASK-017-a2'
sys.path.insert(0,str(TREE/'src'))
import agents, config, contracts, domain_values, workflow_ports
from agents import AgentAdapterCapabilities, DeterministicFakeAgentAdapter, FakeAgentProviderState
from workflow_ports import AgentRequest, AgentHandle, AgentRunRecord, AgentOutputRecord, AgentObservation, AcceptanceCriterion, CancelObservation, CancelStatus, AgentAdapter
from domain_values import ScopeClaim, ScopePath, EntityId, PlanId, Revision, Sha256Digest, FrozenJsonObject, AgentRunStatus, AgentOutputStatus, EvidenceRef, DomainError, DomainException, ErrorCategory

def wire(value):
    if isinstance(value,ScopePath): return value.as_wire()
    if isinstance(value,ScopeClaim): return value.to_wire()
    if isinstance(value,(EntityId,PlanId,Revision,Sha256Digest)): return value.value
    if isinstance(value,datetime): return value.isoformat()
    if isinstance(value,Enum): return value.value
    if isinstance(value,FrozenJsonObject): return value.to_dict()
    if is_dataclass(value): return {f.name:wire(getattr(value,f.name)) for f in fields(value)}
    if isinstance(value,tuple): return [wire(v) for v in value]
    return value

def encoded(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def sha(value): return hashlib.sha256(value).hexdigest()

def fixture(path,provider='openai'):
    shutil.copytree(TREE/'schemas/v1',path/'schemas/v1')
    (path/'.ai/project').mkdir(parents=True)
    shutil.copyfile(TREE/'.ai/framework.json',path/'.ai/framework.json')
    models=json.loads((TREE/'.ai/project/agent-models.json').read_bytes())
    policy=json.loads((TREE/'.ai/project/policy.json').read_bytes())
    models['active_provider']=provider
    for catalog in models['providers'].values():
        catalog['profiles']['r2_selected_review']=copy.deepcopy(catalog['profiles']['review_high'])
    models['policy_profile_map']['review_high']='r2_selected_review'
    for profile in policy['model_profiles']:
        selected=models['providers'][provider]['profiles'][models['policy_profile_map'][profile['name']]]
        profile.update(configured=True,provider=provider,model_id=selected['model_id'],capability_rank=selected['capability_rank'])
    (path/'.ai/project/policy.json').write_bytes(encoded(policy))
    (path/'.ai/project/agent-models.json').write_bytes(encoded(models))

def load(path):
    return config.load_project_settings(path,config.load_installation_record(path))

def request(case='baseline',role='consistency-reviewer',key='r2-review-key',plan='PLAN-001'):
    description={'multiline_request':'Validate the first result.\nPreserve the second line.', 'unicode_request':'Preserve Cafe\u0301 exactly.'}.get(case,'Validate the result.')
    return AgentRequest(id='r2-request',workflow_id='r2-workflow',run_id='r2-run',attempt_id='TASK-017-a2',task_id=None if role=='task-isolation-reviewer' else 'TASK-017',plan_id=plan,spec_refs=(f'.ai/plans/current/{plan}/spec.json',),role=role,graph_revision=4,base_oid='b90556d92e0f37e664d685b4af85c43fc8143d81',current_oid='b7593f11961aa6f5c3a927f3c49af32c4fa93971',worktree_id='TASK-017-a2',scope=ScopeClaim(write_paths=('.ai/review-outbox/',)),context_ref='.ai/context/r2.json',allowed_command_ids=(),acceptance_criteria=(AcceptanceCriterion('AC-04',description,'ContractRegistry and restart'),),dependency_handoffs=('handoff:TASK-003','handoff:TASK-004','handoff:TASK-038'),checklist_ids=('R2-01','R2-12'),model_profile='review_high',policy_ref='.ai/project/policy.json',permission_subset=('read',),lease_generation=9,idempotency_key=key)

def adapter(settings,state,caps=None,project='r2-project'):
    if caps is None:
        caps=AgentAdapterCapabilities(roles=('consistency-reviewer','implementation-reviewer','task-isolation-reviewer'),permissions=('read',),command_ids=(),model_profiles=settings.models.provider().profiles)
    return DeterministicFakeAgentAdapter(project_id=project,settings=settings,capabilities=caps,provider_state=state)

def observation(handle,model,case,status=AgentRunStatus.SUCCEEDED):
    now=datetime(2026,9,8,12,tzinfo=UTC)
    summary={'multiline_output':'First result.\nSecond result.', 'unicode_output':'Committed Cafe\u0301 exactly.'}.get(case,'Independent contract result.')
    output=AgentOutputRecord(id='r2-output',request_id=handle.request_id,attempt_id=handle.attempt_id,status=AgentOutputStatus.SUCCEEDED,actual_model=model,artifact_refs=('.ai/evidence/r2-invocation.md',),command_evidence_refs=(),discoveries=(),scope_change_requests=(),error_category=None,summary=summary) if status is AgentRunStatus.SUCCEEDED else None
    run=AgentRunRecord(id='r2-observed-run',request_ref=f'agent-request:{handle.plan_id.value}:{handle.request_id.value}',attempt_id=handle.attempt_id,status=status,adapter_id=handle.adapter_id,external_handle=handle.external_handle,actual_model=model,started_at=now,finished_at=now+timedelta(seconds=1) if output else None,output_ref=f'agent-output:{handle.plan_id.value}:r2-output' if output else None,error_category=None,lease_generation=handle.lease_generation)
    return AgentObservation(status,handle,run,output,(EvidenceRef('.ai/evidence/r2-provider.json','7'*64),))

def child(path,case,phase):
    settings=load(path)
    req=request(case)
    registry=contracts.ContractRegistry(TREE/'schemas/v1')
    registry.validate(wire(req))
    state_path=path/'provider-state.json'
    before=state_path.read_bytes() if state_path.exists() else None
    result={'case':case,'phase':phase,'pid':os.getpid(),'runtime':platform.python_version(),'executable':sys.executable,'origins':{m.__name__:m.__file__ for m in (agents,config,contracts,domain_values,workflow_ports)},'request_schema_valid':True,'settings_sha256':sha((path/'.ai/project/policy.json').read_bytes()+(path/'.ai/project/agent-models.json').read_bytes())}
    stage='provider_restore'
    try:
        state=FakeAgentProviderState(state_path)
        api=adapter(settings,state)
        stage='start_retry' if phase=='resume' else 'start'
        handle=api.start(req,req.idempotency_key)
        result.update(handle=handle.external_handle,effect_count=state.effect_count,requested_profile=req.model_profile,resolved_profile=settings.configured_model(req.model_profile).name,expected_profile=api.expected_model(handle).profile)
        if phase=='start':
            scripted=observation(handle,api.expected_model(handle),case)
            registry.validate(wire(scripted.run))
            registry.validate(wire(scripted.output))
            state.script(handle,polls=(scripted,))
        stage='poll'
        observed=api.poll(handle)
        registry.validate(wire(observed.run))
        registry.validate(wire(observed.output))
        result.update(outcome='admitted',poll=observed.status.value,output_schema_valid=True,output_summary=observed.output.summary,output_sha256=sha(encoded(wire(observed.output))),request_description=req.acceptance_criteria[0].description,cancellation=api.cancel(handle).status.value)
    except DomainException as exc:
        result.update(outcome='rejected',stage=stage,category=exc.category.value,message=str(exc),saved_bytes_unchanged=state_path.read_bytes()==before)
    print(json.dumps(result,ensure_ascii=True,sort_keys=True))

def rejected(action,category):
    try: action()
    except DomainException as exc:
        assert exc.category is category,(exc.category,category)
        return 1
    raise AssertionError('Expected rejection did not occur')

def compatibility(path):
    settings=load(path)
    registry=contracts.ContractRegistry(TREE/'schemas/v1')
    store=FakeAgentProviderState(path/'compatibility-state.json')
    api=adapter(settings,store)
    assert isinstance(api,AgentAdapter)
    for name in ('start','poll','cancel'):
        assert inspect.signature(getattr(type(api),name)) == inspect.signature(getattr(AgentAdapter,name))
    checks={'protocol_signatures':3,'mapped_review_roles':0,'wire_records_validated':0,'boundary_rejections':0}
    handles=[]
    for role in ('implementation-reviewer','consistency-reviewer','task-isolation-reviewer'):
        req=request(role=role,key='r2-'+role)
        registry.validate(wire(req)); checks['wire_records_validated']+=1
        handle=api.start(req,req.idempotency_key)
        assert api.start(req,req.idempotency_key)==handle
        queued=api.poll(handle)
        registry.validate(wire(queued.run)); checks['wire_records_validated']+=1
        assert queued.status is AgentRunStatus.QUEUED and queued.run.actual_model is None
        assert api.cancel(handle).status is CancelStatus.PENDING and not api.cancel(handle).quiesced
        model=api.expected_model(handle)
        assert model.profile=='review_high' and settings.configured_model('review_high').name=='r2_selected_review'
        assert model.capability_rank>settings.configured_model('implementation').capability_rank
        handles.append(handle); checks['mapped_review_roles']+=1
    assert len({api.expected_model(h).invocation_id for h in handles})==3
    req=request(role='implementation-reviewer',key='r2-implementation-reviewer')
    before=(path/'compatibility-state.json').read_bytes()
    checks['boundary_rejections']+=rejected(lambda:api.start(replace(req,plan_id='PLAN-002'),req.idempotency_key),ErrorCategory.STATE_CONFLICT)
    for mutated in (replace(handles[0],project_id='other-project'),replace(handles[0],lease_generation=10)):
        for action in (api.poll,api.cancel,api.expected_model):
            checks['boundary_rejections']+=rejected(lambda:action(mutated),ErrorCategory.STATE_CONFLICT)
    for role in ('implementation-reviewer','consistency-reviewer','task-isolation-reviewer'):
        low=replace(request(role=role,key='low-'+role),model_profile='implementation')
        checks['boundary_rejections']+=rejected(lambda:api.start(low,low.idempotency_key),ErrorCategory.UNSUPPORTED_CAPABILITY)
    assert (path/'compatibility-state.json').read_bytes()==before
    forged=wire(req); forged['reasoning_effort']='xhigh'
    checks['boundary_rejections']+=rejected(lambda:registry.validate(forged),ErrorCategory.VALIDATION_FAILED)
    base=load(TREE)
    assert base.configured_model('review_high') is None
    checks['boundary_rejections']+=rejected(lambda:adapter(base,FakeAgentProviderState()).start(req,req.idempotency_key),ErrorCategory.UNSUPPORTED_CAPABILITY)
    model=api.expected_model(handles[0])
    valid=observation(handles[0],model,'baseline')
    registry.validate(wire(valid.run)); registry.validate(wire(valid.output)); checks['wire_records_validated']+=2
    wrong=copy.deepcopy(wire(valid.output)); wrong['actual_model']['reasoning_effort']='xhigh'
    checks['boundary_rejections']+=rejected(lambda:registry.validate(wrong),ErrorCategory.VALIDATION_FAILED)
    return checks

def main():
    result={'utc':datetime.now(UTC).isoformat(),'runtime':sys.version,'platform':platform.platform(),'fresh_processes':[],'compatibility':{}}
    with tempfile.TemporaryDirectory(prefix='r2-017-consistency-') as temporary:
        folder=Path(temporary)
        if '--linux-focused' not in sys.argv:
            for provider in ('openai','anthropic'):
                project=folder/provider; fixture(project,provider)
                result['compatibility'][provider]=compatibility(project)
        cases=('multiline_request','unicode_output') if '--linux-focused' in sys.argv else ('baseline','multiline_request','unicode_request','multiline_output','unicode_output')
        for case in cases:
            project=folder/case; fixture(project)
            rows=[]
            for phase in ('start','resume'):
                run=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--child',str(project),case,phase],cwd=TREE,text=True,capture_output=True,shell=False)
                assert run.returncode==0,(run.stdout,run.stderr)
                rows.append(json.loads(run.stdout))
            assert rows[0]['pid']!=rows[1]['pid'] and rows[0]['settings_sha256']==rows[1]['settings_sha256']
            for row in rows:
                for origin in row['origins'].values(): assert Path(origin).resolve().parent==(TREE/'src').resolve()
            result['fresh_processes'].append(rows)
    print(json.dumps(result,indent=2,ensure_ascii=True))

if __name__=='__main__':
    if '--child' in sys.argv: child(Path(sys.argv[2]),sys.argv[3],sys.argv[4])
    else: main()
