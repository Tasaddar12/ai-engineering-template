"""Bound the common text-decoder defect without repeating prior suites."""
from pathlib import Path
import copy
import importlib.util
import json
import sys
import tempfile
from dataclasses import replace

helper_path=Path(__file__).with_name('TASK-017-a2-c3-R2-probes.py')
spec=importlib.util.spec_from_file_location('r2_own_probes',helper_path)
probe=importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
from agents import FakeAgentProviderState
from domain_values import ScopeClaim, EvidenceRef, DomainException, ErrorCategory, DomainError
from workflow_ports import AcceptanceCriterion

def outcome(action):
    try:
        value=action()
        return {'outcome':'admitted','status':getattr(getattr(value,'status',None),'value',None)}
    except DomainException as exc:
        return {'outcome':'rejected','category':exc.category.value,'message':str(exc)}

def main():
    results={}
    with tempfile.TemporaryDirectory(prefix='r2-payload-audit-') as temporary:
        root=Path(temporary)
        for case in ('leading_scope_path','leading_evidence_path','metadata_payload','future_model_provenance'):
            project=root/case
            probe.fixture(project)
            if case=='future_model_provenance':
                models_path=project/'.ai/project/agent-models.json'
                models=json.loads(models_path.read_bytes())
                models['providers']['openai']['profiles']['r2_selected_review']['model_id']='r2-review-caf\u00e9'
                models_path.write_bytes(probe.encoded(models))
                policy_path=project/'.ai/project/policy.json'
                policy=json.loads(policy_path.read_bytes())
                for profile in policy['model_profiles']:
                    if profile['name']=='review_high': profile['model_id']='r2-review-caf\u00e9'
                policy_path.write_bytes(probe.encoded(policy))
            settings=probe.load(project)
            request=probe.request()
            if case=='leading_scope_path':
                request=replace(request,scope=ScopeClaim(write_paths=(' leading-file.txt',)))
            probe.contracts.ContractRegistry(probe.TREE/'schemas/v1').validate(probe.wire(request))
            path=project/'private-state.json'
            store=FakeAgentProviderState(path)
            api=probe.adapter(settings,store)
            handle=api.start(request,request.idempotency_key)
            row={'request_schema_valid':True,'start_admitted':True}
            original_metadata={' note\nkey ':'  exact\nCafe\u0301\t  ','nested':{'value':' trailing '}}
            if case!='leading_scope_path':
                model=api.expected_model(handle)
                if case=='future_model_provenance':
                    bad=replace(model,model_id='r2-review-cafe\u0301')
                    assert bad!=model
                    observation=probe.observation(handle,bad,'baseline')
                else:
                    observation=probe.observation(handle,model,'baseline')
                    reference=EvidenceRef(' leading-evidence.json' if case=='leading_evidence_path' else '.ai/evidence/payload.json','8'*64,metadata=original_metadata)
                    observation=replace(observation,evidence_refs=(reference,))
                store.script(handle,polls=(observation,))
                before_poll=path.read_bytes()
                row['first_poll']=outcome(lambda:api.poll(handle))
                if case=='future_model_provenance':
                    assert row['first_poll']['category']=='validation_failed'
                    assert path.read_bytes()==before_poll
                    row['invalid_model_script_bytes_unchanged_before_restart']=True
            saved=path.read_bytes()
            del api,store
            try:
                restored=FakeAgentProviderState(path)
                restarted=probe.adapter(settings,restored)
                retry=restarted.start(request,request.idempotency_key)
                row['same_handle']=retry==handle
                actual=restarted.poll(handle)
                row['after_restart']={'outcome':'admitted','status':actual.status.value}
                if case=='metadata_payload':
                    row['exact_metadata_roundtrip']=actual.evidence_refs[0].metadata.to_dict()==original_metadata
                    assert row['exact_metadata_roundtrip']
                if case=='future_model_provenance':
                    row['restored_model_id']=actual.run.actual_model.model_id
                    assert actual.run.actual_model==restarted.expected_model(handle)
            except DomainException as exc:
                row['after_restart']={'outcome':'rejected','category':exc.category.value,'message':str(exc),'saved_bytes_unchanged':path.read_bytes()==saved}
            results[case]=row
        rejected=[]
        for label,construct in [('leading criterion whitespace',lambda:AcceptanceCriterion('AC-04',' leading','verify')),('trailing output-like text whitespace',lambda:AcceptanceCriterion('AC-04','trailing ','verify')),('DomainError internal newline',lambda:DomainError(ErrorCategory.INVALID_INPUT,'first\nsecond')),('trailing scope-path whitespace',lambda:ScopeClaim(write_paths=('file.txt ',)))]:
            try: construct()
            except ValueError: rejected.append(label)
            else: raise AssertionError(label+' was unexpectedly admitted upstream')
        results['upstream_rejects_not_requirements']=rejected
    print(json.dumps(results,indent=2,ensure_ascii=True))

if __name__=='__main__': main()
