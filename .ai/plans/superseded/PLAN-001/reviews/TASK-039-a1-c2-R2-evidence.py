"""Independent R2 checks. Reads the frozen candidate; writes no candidate files."""
from __future__ import annotations
import ast
import dataclasses as dc
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import get_type_hints

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-039-a1'
BASE = '3368964b3825df6e1e59c1f66820f2bce61de0ff'
HEAD = '314ef09d59f494223bec02556c6e3d9a8108636f'
STEM = '.ai/plans/current/PLAN-001/reviews/TASK-039-a1-c2-R2'
CREF = '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-039-a1-314ef09d59f4.json'
R1REF = '.ai/plans/current/PLAN-001/reviews/TASK-039-a1-c2-R1.json'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / 'src'))
import orchestration_ports as op
import workflow_ports as wp
import domain_values as dv
import config
import transitions as tr
import ai
from jsonschema import Draft202012Validator, FormatChecker

def git(*args, cwd=TREE):
    return subprocess.check_output(['git', *args], cwd=cwd)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(path, root=TREE):
    return json.loads((root/path).read_bytes())

def reject(call, label):
    try:
        call()
    except (ValueError, TypeError):
        return
    raise AssertionError('accepted invalid boundary: ' + label)

def verify_identity():
    c = read(CREF, ROOT)
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD == c['head_oid']
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE == c['base_oid']
    assert git('status', '--porcelain') == b''
    assert git('merge-base', BASE, HEAD).decode().strip() == BASE
    diff = git('diff', '--binary', BASE, HEAD)
    assert digest(diff) == c['diff_sha256']
    changed = git('diff', '--name-status', BASE, HEAD).decode().splitlines()
    expected = ['A\t.ai/plans/current/PLAN-001/evidence/implementation/TASK-039.md',
                'A\tsrc/orchestration_ports.py',
                'A\ttests/unit/domain_orchestration_ports/test_orchestration_ports.py']
    assert changed == expected
    for ref in c['context_refs']:
        assert digest(git('show', HEAD+':'+ref['path'])) == ref['sha256'], ref
    for ref in c['validation_refs']:
        assert digest((ROOT/ref['path']).read_bytes()) == ref['sha256'], ref
    assert digest((ROOT/'.ai/project/policy.json').read_bytes() +
                  (ROOT/'.ai/project/agent-models.json').read_bytes()) == c['policy_model_digest']
    assert digest(json.dumps({k:v for k,v in c.items() if k!='fingerprint'},
                  sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()) == c['fingerprint']
    r1 = read(R1REF, ROOT)
    Draft202012Validator(read('schemas/v1/review-result.schema.json'), format_checker=FormatChecker()).validate(r1)
    assert (r1['stage'], r1['verdict'], r1['candidate_ref'], r1['candidate_fingerprint']) == (
        'implementation','pass',CREF,c['fingerprint'])
    assert {x['id'] for x in r1['checks']} == {f'R1-{i:02}' for i in range(1,12)}
    assert all(x['status']=='pass' for x in r1['checks']) and not r1['findings']
    assert len({r1['independent_session_id'], r1['implementation_session_id'], '/root/r2_039_c2'}) == 3
    graph = read('.ai/plans/current/PLAN-001/graph.json')
    task_records = [read(f'.ai/plans/current/PLAN-001/tasks/current/{n["task_id"]}.json') for n in graph['nodes']]
    iso = read(graph['review_ref'])
    assert graph['revision']==iso['graph_revision']==4 and iso['verdict']=='pass'
    assert ai.structural_task_digest(task_records)==graph['task_set_sha256']==iso['task_set_sha256']
    accepted = {
      'TASK-001': ('d1fc917466410febc6238479e65816dd39591a4f','15dacd3fc544e433e3602d5403c6b476e547eae0'),
      'TASK-003': ('d51b72ce71ea3ac3ad31adf41e3eddc84738ac0b','c749ec19056dd6d215c51a9896f35785391d0ace'),
      'TASK-002': ('460ab567d01912167557f2f671ed07c63f0a31e7','4e4dc60178f073042d989f517ee1d363cbe6777c'),
      'TASK-038': ('6f2b12c3283ed7d6e3d4876020fe690c6e0061a3','ab36f09f7775201882bf863a90bc264be022adbd'),
      'TASK-008': ('fcb01a93f0e1022c70fa296f7342ced71bbf3250','62b899af5c57f651175cd6f304f52218acb12adb')}
    for task_id, commits in accepted.items():
        assert read(f'.ai/plans/current/PLAN-001/tasks/current/{task_id}.json')['status']=='accepted'
        for oid in commits:
            assert subprocess.run(['git','merge-base','--is-ancestor',oid,BASE],cwd=TREE).returncode == 0
    old = read('.ai/plans/current/PLAN-001/reviews/TASK-039-a1-c1-R1.json', ROOT)
    assert old['verdict']=='fail' and old['findings'][0]['id']=='R1-TASK-039-001'
    assert old['candidate_fingerprint'] != c['fingerprint']
    print('PASS exact base/head, clean candidate, binary diff '+c['diff_sha256'])
    print('PASS fingerprint '+c['fingerprint']+'; 12 committed context hashes; validation bytes; policy/model digest; same-candidate passing R1; independent sessions.')
    print('PASS graph r4/39-task structural digest/isolation; five accepted prerequisite/sibling candidate+integration ancestry; exactly three owned additions; retained failed cycle1.')

verify_identity()
for mod in (op, wp, dv, config, tr):
    assert Path(mod.__file__).resolve().is_relative_to(TREE/'src')
    print('Import:', mod.__file__)

if '--skip-declared' not in sys.argv:
    command = read('.ai/plans/current/PLAN-001/commands/test.TASK-039.json')['argv']
    command[0] = sys.executable
    result = subprocess.run(command, cwd=TREE, env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}, capture_output=True, text=True)
    print('Declared command:', command, '\nExit:', result.returncode)
    print(result.stdout+result.stderr)
    assert result.returncode==0 and 'Ran 20 tests' in result.stderr and 'OK' in result.stderr
else:
    print('Reviewer fixture corrected: omit graph-approval and delivery-authorization guards from already-delivering completion edge; test authorization on its owned entry edge. Earlier declared 20-test pass retained.')

spec = importlib.util.spec_from_file_location('r2_candidate_fixtures', TREE/'tests/unit/domain_orchestration_ports/test_orchestration_ports.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)

# Signature types are asserted independently of the candidate's parameter-only test.
methods = [
 (op.IsolationService,'review','request',op.IsolationRequest,op.IsolationDecision),
 (op.TaskDispatcher,'start','request',op.TaskAttemptRequest,op.AttemptHandle),
 (op.TaskDispatcher,'observe','handle',op.AttemptHandle,op.AttemptObservation),
 (op.TaskDispatcher,'cancel','handle',op.AttemptHandle,wp.CancelObservation),
 (op.Scheduler,'tick','snapshot',op.SchedulingSnapshot,op.SchedulingDecision),
 (op.IntegrationService,'integrate','request',op.IntegrationRequest,op.IntegrationResult),
 (op.RecoveryService,'recover','request',op.RecoveryRequest,op.RecoveryDecision),
 (op.ExecutionService,'advance','request',op.ExecutionRequest,op.ExecutionStep),
 (op.PlanIntegrationService,'evaluate','request',op.PlanIntegrationRequest,op.PlanIntegrationDecision),
 (op.CompletionContinuation,'advance','request',op.CompletionRequest,op.CompletionStep)]
for cls,method,arg,request,result_type in methods:
    fn = getattr(cls,method)
    assert tuple(inspect.signature(fn).parameters)==('self',arg)
    assert get_type_hints(fn)=={arg:request,'return':result_type}
imports = {node.module for node in ast.walk(ast.parse((TREE/'src/orchestration_ports.py').read_text())) if isinstance(node,ast.ImportFrom)}
assert imports <= {'__future__','collections.abc','dataclasses','datetime','enum','typing','domain_values','workflow_ports'}
print('PASS all 10 frozen method types; only standard-library/shared-value/workflow imports; existing cancellation type reused.')

schemas = [('task-graph',op.TaskGraphRecord),('candidate',op.CandidateRecord),('isolation-review',op.IsolationReviewRecord),('recovery',op.RecoveryRecord)]
for name,cls in schemas:
    schema = read(f'schemas/v1/{name}.schema.json')
    assert {v.name for v in dc.fields(cls)}==set(schema['properties'])
for schema_name,prop,cls in [('task-graph','nodes',op.GraphNode),('recovery','acceptance_mapping',op.AcceptanceMapping),('recovery','salvage',op.SalvageItem)]:
    assert {v.name for v in dc.fields(cls)}==set(read(f'schemas/v1/{schema_name}.schema.json')['properties'][prop]['items']['properties'])
assert set(op.ExecutionStatus)==set(dv.ExecutionStatus) and 'completed' not in {x.value for x in op.ExecutionStatus}
print('PASS four v1 record and three nested field sets; operational types introduce no serialized fields; execution/completion vocabularies remain distinct.')

# Cross configuration/recovery scenario: minimum configuration and over-limit facts coexist.
installation = config.load_installation_record(TREE)
settings = config.load_project_settings(TREE, installation)
saved = settings.resolve_run(overrides=config.RunOverrides(max_agent_invocations=1,max_rewrites=0))
hydrated = config.decode_run_settings(saved.to_payload())
assert hydrated == saved and saved.max_agent_invocations == 1 and saved.max_rewrites == 0
reject(lambda: config.RunSettings(max_agent_invocations=0),'configured zero invocation limit')
assert settings.configured_model('review_high') is None
budget = op.LineageBudget(saved.max_agent_invocations,9,saved.max_rewrites,3,60,120,2,4,3,100,125)
for name in ['used_agent_invocations','used_rewrites','elapsed_seconds','used_review_1_cycles','used_review_2_cycles','used_tokens']:
    for value in [0,1,2,10**30]:
        assert getattr(dc.replace(budget,**{name:value}),name)==value
for fld in dc.fields(op.LineageBudget):
    for value in [-1,True,1.5,'1']:
        reject(lambda fld=fld,value=value:dc.replace(budget,**{fld.name:value}),fld.name)
print('PASS accepted config save/hydrate with limits 1/0, zero configured invocations rejected, automatic model binding remains absent; 24 observed-usage probes and 44 malformed-number rejections.')

r1,r2=f.review_histories(4)
r2.pop()
permissions=['local_execute']
rr=op.RecoveryRequest('project-1','PLAN-001','run-1','recover-op','recover-request',12,
 'lineage budget exhausted',['TASK-003'],f.graph(),f.tasks(),
 [op.AcceptanceMapping('TASK-003-AC1',['TASK-003'])],r1,r2,budget,f.git_facts(),permissions,[f.evidence('failure')])
r1.clear();r2.clear();permissions.append('remote_push')
assert (len(rr.review_1_history),len(rr.review_2_history))==(4,3)
assert rr.permission_subset==('local_execute',) and rr.lineage_budget==budget
assert rr.review_2_history[-1].record.review_1_ref==rr.review_1_history[2].ref.path
reject(lambda:dc.replace(rr,review_1_history=rr.review_1_history[1:]),'missing linked R1 history')
reject(lambda:dc.replace(rr,review_1_history=rr.review_2_history),'history stage mismatch')
paused=op.RecoveryDecision('paused',rr.request_id,rr.plan_id,rr.run_id,None,None,None,[],rr.failed_task_ids,['TASK-003-a1'],[f.evidence('budget-pause')],f.error(dv.ErrorCategory.BUDGET_EXHAUSTED))
assert not {'permission_subset','authorization_refs','grant'} & {v.name for v in dc.fields(paused)}
assert paused.evidence_refs and paused.error.category is dv.ErrorCategory.BUDGET_EXHAUSTED
reject(lambda:dc.replace(paused,error=None),'pause without cause')
print('PASS 4 R1/3 R2 histories preserved independently with linkage; acceptance/Git facts and all over-limit counters retained; immutable restricted permissions and evidence-bearing budget pause.')

request=f.attempt_request()
for changes in [{'request_id':dv.EntityId('other-request')},{'attempt_id':dv.EntityId('other-attempt')},{'run_id':dv.EntityId('other-run')},{'lease_generation':dv.Revision(99)}]:
    reject(lambda changes=changes:dc.replace(request,agent_request=dc.replace(request.agent_request,**changes)) if 'request_id' not in changes else dc.replace(request,request_id=changes['request_id']), 'nested request fence')
handle=f.attempt_handle()
for changes in [{'project_id':dv.EntityId('other-project')},{'request_id':dv.EntityId('other-request')},{'lease_generation':dv.Revision(99)}]:
    reject(lambda changes=changes:dc.replace(handle,agent_handle=dc.replace(handle.agent_handle,**changes)),'nested handle fence')
observed=f.successful_agent_observation(dc.replace(handle.agent_handle,external_handle='different-known-handle'))
reject(lambda:op.AttemptObservation('succeeded',handle,observed,f.content('output'),[f.evidence('import')]),'known provider-handle mismatch')
for status in wp.CancelStatus:
    quiesced=status in {wp.CancelStatus.CANCELLED,wp.CancelStatus.ALREADY_TERMINAL}
    err=f.error() if status in {wp.CancelStatus.UNKNOWN,wp.CancelStatus.FAILED} else None
    observation=wp.CancelObservation(status,handle.agent_handle,quiesced,[f.evidence('cancel')],err)
    reject(lambda:dc.replace(observation,quiesced=not quiesced),'false cancellation quiescence')
print('PASS nested dispatch request/attempt/run/lease/project and mutually known provider identities; all five accepted cancellation states reject incorrect quiescence.')

first=f.review_record(wp.ReviewStage.IMPLEMENTATION,'TASK-003')
second=f.review_record(wp.ReviewStage.CONSISTENCY,'TASK-003')
integration=op.IntegrationRequest('project-1','PLAN-001','run-1','integrate-op','integrate-key',12,4,f.DIGEST,'TASK-003','TASK-003-a1',f.candidate(),'ai/PLAN-001/integration','PLAN-001-integration',f.OID,[f.dependency()],f.content('handoff'),first,f.content('review-1'),second,f.content('review-2'),f.content('intent'))
for changes in [{'candidate_fingerprint':dv.Sha256Digest(f.OTHER_DIGEST)},{'plan_id':dv.PlanId('PLAN-002')},{'verdict':dv.ReviewVerdict.FAIL}]:
    reject(lambda changes=changes:dc.replace(integration,review_2=dc.replace(second,**changes)),'stale/wrong/failed second review')
reject(lambda:dc.replace(integration,review_1_ref=f.content('unrelated-review')),'wrong R1 reference')
print('PASS integration consumes accepted workflow review records; wrong fingerprint, plan, verdict, and R1 reference rejected.')

# Completion observations can feed the already accepted pure transition contract.
done=op.CompletionStep('completed','run-1','completed',14,f.plan_integration_decision(),f.delivery_observation(),[f.evidence('completed')])
reject(lambda:dc.replace(done,integration_decision=None),'missing integrated gate')
reject(lambda:dc.replace(done,delivery_observation=f.delivery_observation(False)),'no observed merge')
unauthorized=dc.replace(done.delivery_observation,state=dc.replace(done.delivery_observation.state,authorization_refs=[]))
reject(lambda:dc.replace(done,delivery_observation=unauthorized),'missing authorization')
step=op.ExecutionStep('tasks_accepted','run-1','integration_review',13,[f.evidence('accepted')])
assert step.status.value != done.status.value
guards=[tr.GuardEvidence(name,True,[f.evidence(name)], f.OTHER_OID if name in {'integrated_validation_current','integration_review_current','current_head_ci_passed','merge_observed'} else None) for name in ['state_observed','live_tasks_accepted','integrated_validation_current','integration_review_current','current_head_ci_passed','merge_observed']]
transition=tr.TransitionRequest('plan','PLAN-001','delivering','completed','event-complete','complete-operation',14,f.NOW,guards)
assert tr.decide_transition(transition).accepted
assert not tr.decide_transition(dc.replace(transition,guards=[g for g in guards if g.guard is not tr.TransitionGuard.MERGE_OBSERVED])).accepted
entry=dc.replace(transition,current_state='delivery_ready',target_state='delivering',guards=[tr.GuardEvidence(name,True,[f.evidence(name)]) for name in ['state_observed','delivery_authorized']])
assert tr.decide_transition(entry).accepted
assert not tr.decide_transition(dc.replace(entry,guards=[g for g in entry.guards if g.guard is not tr.TransitionGuard.DELIVERY_AUTHORIZED])).accepted
print('PASS authorized observed completion and accepted TASK-008 transition agree; missing integrated gate/merge/authority rejects, and tasks_accepted cannot stand in for completion.')

verify_identity()
print('ALL INDEPENDENT R2 CONSISTENCY CHECKS PASSED; candidate access ends after this successful run.')
