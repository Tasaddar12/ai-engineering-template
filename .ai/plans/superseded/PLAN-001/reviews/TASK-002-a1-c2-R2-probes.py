"""Independent R2 identity and cross-contract probes; candidate source is read-only."""
from __future__ import annotations

import ast
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
import unittest
from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-002-a1'
PLAN = Path('.ai/plans/current/PLAN-001')
STEM = ROOT / PLAN / 'reviews/TASK-002-a1-c2-R2'
BASE = '43c8004c7313105f63d3b8d21726f8a056b96842'
HEAD = '460ab567d01912167557f2f671ed07c63f0a31e7'
CANDIDATE = PLAN / 'reviews/candidates/CANDIDATE-TASK-002-a1-460ab567d019.json'
R1 = PLAN / 'reviews/TASK-002-a1-c2-R1.json'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'src'))
import contracts
import domain_values as dv
import local_ports as lp
import workflow_ports as wp

def git(*args: str) -> bytes:
    return subprocess.run(['git', *args], cwd=WT, check=True, capture_output=True, shell=False).stdout

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def read_json(path: Path) -> dict:
    return json.loads(path.read_bytes())

def wire(value: object) -> object:
    if isinstance(value, (dv.EntityId, dv.PlanId, dv.Revision, dv.Sha256Digest)):
        return value.value
    if isinstance(value, dv.ScopePath):
        return value.as_wire()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if dataclasses.is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {k: wire(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [wire(v) for v in value]
    return value

REG = contracts.ContractRegistry(WT / 'schemas/v1')
NOW = datetime(2026, 9, 8, 5, 30, tzinfo=timezone.utc)
A, B = 'a' * 40, 'b' * 40
EVID = dv.EvidenceRef(dv.ScopePath.exact_file('evidence/observation.json'), dv.Sha256Digest('d' * 64))
PROJECT = lp.LocalProjectBinding('project', WT)
CONTROL = lp.LocalControlBinding('project', 'WT-CONTROL', WT / '.worktrees/control')

def verify_identity() -> None:
    candidate = read_json(ROOT / CANDIDATE)
    REG.validate(candidate)
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD == candidate['head_oid']
    assert git('merge-base', BASE, HEAD).decode().strip() == BASE == candidate['base_oid']
    assert git('status', '--porcelain=v1') == b''
    assert sha(git('diff', '--binary', BASE, HEAD)) == candidate['diff_sha256']
    refs = []
    for ref in candidate['context_refs']:
        raw = git('show', HEAD + ':' + ref['path'])
        assert sha(raw) == ref['sha256'], ref['path']
        refs.append(ref['path'])
    for ref in candidate['validation_refs']:
        assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256']
    policy_paths = ['.ai/project/policy.json', '.ai/project/agent-models.json']
    policy_digest = sha(b''.join((ROOT / p).read_bytes() for p in policy_paths))
    assert policy_digest == candidate['policy_model_digest']
    for p in policy_paths:
        assert json.loads(git('show', HEAD + ':' + p)) == read_json(ROOT / p)
    assert sha(canonical({k: v for k, v in candidate.items() if k != 'fingerprint'})) == candidate['fingerprint']
    r1 = read_json(ROOT / R1)
    REG.validate(r1)
    assert r1['candidate_fingerprint'] == candidate['fingerprint'] and r1['verdict'] == 'pass'
    assert r1['candidate_ref'] == CANDIDATE.as_posix()
    assert r1['independent_session_id'] == '/root/r1_002_c2'
    assert r1['implementation_session_id'] == '/root/implement_002'
    assert len(r1['checks']) == 11 and all(c['status'] == 'pass' for c in r1['checks'])
    assert not any(not f['resolved'] and f['severity'] in ('major', 'blocking') for f in r1['findings'])
    graph = read_json(WT / PLAN / 'graph.json')
    tasks = [read_json(WT / PLAN / f"tasks/current/{n['task_id']}.json") for n in graph['nodes']]
    iso = read_json(WT / PLAN / 'reviews/r4-isolation-review.json')
    task_digest = contracts.structural_task_digest(tasks)
    assert graph['status'] == 'approved' and graph['revision'] == 4
    assert iso['verdict'] == 'pass' and iso['graph_revision'] == 4
    assert task_digest == graph['task_set_sha256'] == iso['task_set_sha256']
    assert all(n['depends_on'] == next(t for t in tasks if t['id'] == n['task_id'])['depends_on'] for n in graph['nodes'])
    graph_digest = sha(canonical({k: graph[k] for k in ('schema_version','kind','id','plan_id','revision','nodes','task_set_sha256')}))
    assert graph_digest == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
    scope = next(t['scope'] for t in tasks if t['id'] == 'TASK-002')
    changed = git('diff', '--name-only', BASE, HEAD).decode().splitlines()
    assert set(changed) == {str(PLAN / 'evidence/implementation/TASK-002.md').replace('\\','/'), 'src/local_ports.py', 'tests/unit/domain_local_ports/test_local_ports.py'}
    assert all(any(dv.ScopePath(p).contains(dv.ScopePath.exact_file(c)) for p in scope['write_paths']) for c in changed)
    deps = []
    for task, commit, review, source in (
        ('TASK-001', 'd1fc917466410febc6238479e65816dd39591a4f', 'TASK-001-a2-c2-R2.json', ['src/domain_values.py']),
        ('TASK-004', 'e3c1177f993ee74815639a83ef3333faa4ba3957', 'TASK-004-a2-c3-R2.json', ['src/contracts.py','src/validate_foundation.py','src/install.py']),
        ('TASK-003', 'd51b72ce71ea3ac3ad31adf41e3eddc84738ac0b', 'TASK-003-a1-c2-R2.json', ['src/workflow_ports.py']),
    ):
        assert next(t for t in tasks if t['id'] == task)['status'] == 'accepted'
        git('merge-base', '--is-ancestor', commit, BASE)
        r2 = read_json(WT / PLAN / 'reviews' / review)
        prior_r1 = read_json(WT / r2['review_1_ref'])
        dep_candidate = read_json(WT / r2['candidate_ref'])
        assert r2['verdict'] == prior_r1['verdict'] == 'pass'
        assert r2['candidate_fingerprint'] == prior_r1['candidate_fingerprint'] == dep_candidate['fingerprint']
        assert dep_candidate['head_oid'] == commit
        for p in source:
            assert git('show', commit + ':' + p) == git('show', HEAD + ':' + p)
        deps.append({'task':task, 'accepted_candidate':commit, 'unchanged_source':source, 'passing_r2':review})
    git('merge-base', '--is-ancestor', '1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518', BASE)
    for module in (contracts, dv, lp, wp):
        assert Path(module.__file__).parent == WT / 'src'
    local_ast = ast.parse((WT / 'src/local_ports.py').read_text())
    imports = {node.module.split('.')[0] for node in ast.walk(local_ast) if isinstance(node, ast.ImportFrom) and node.module}
    imports |= {a.name.split('.')[0] for node in ast.walk(local_ast) if isinstance(node, ast.Import) for a in node.names}
    assert imports == {'__future__','re','collections','dataclasses','datetime','enum','pathlib','typing','domain_values'}
    git('diff', '--check', BASE, HEAD)
    for suffix in ('.json', '.md'):
        p = (PLAN / ('reviews/TASK-002-a1-c1-R1' + suffix)).as_posix()
        assert (ROOT / p).read_bytes().replace(b'\r\n',b'\n') == git('show', '8446225b832db582e49598670ef1f0f3345be415:' + p).replace(b'\r\n',b'\n')
    print(json.dumps({'candidate':candidate['id'], 'base':BASE, 'head':HEAD,
        'fingerprint':candidate['fingerprint'], 'binary_diff_sha256':candidate['diff_sha256'],
        'context_hashes_verified':len(refs), 'validation_hashes_verified':len(candidate['validation_refs']),
        'policy_model_digest':policy_digest, 'graph_digest':graph_digest, 'task_set_sha256':task_digest,
        'r1_sha256':sha((ROOT/R1).read_bytes()), 'accepted_dependencies_and_sibling':deps,
        'changed_paths':changed, 'imports':[m.__file__ for m in (contracts,dv,lp,wp)],
        'source_state':'clean; exact base/head; allowed diff; historical failed R1 preserved'}, indent=2), flush=True)

class ConsistencyScenarios(unittest.TestCase):
    def test_zero_plan_initialization_and_qualified_record_boundary(self):
        state = read_json(WT / '.ai/STATE.json')
        state.update(generation=1, active_plans=[], completed_plans=[], archived_plans=[], active_runs=[])
        event = lp.StateEvent('EV-INIT','OP-INIT',1,state['project_id'],'project_initialized',None,'foundation',(),NOW,None)
        REG.validate(wire(event)); REG.validate(state)
        tx = lp.TransactionRequest(state['project_id'],'RUN-INIT',0,'OP-INIT',(event,),(
            lp.ProjectionUpdate(dv.RecordRef('project-state',state['project_id']),state),))
        self.assertEqual(tx.projection_updates[0].ref.plan_id, None)
        refs = [contracts.parse_record_ref(f'task:{plan}:TASK-001') for plan in ('PLAN-001','PLAN-002')]
        values = [lp.VersionedRecord(ref,'missing',1,None) for ref in refs]
        self.assertEqual(len({v.ref for v in values}), 2)
        with self.assertRaises((TypeError,ValueError)):
            dv.RecordRef('task','TASK-001')

    def test_lifecycle_projection_groups_registry_references_and_manifest(self):
        task = read_json(WT / PLAN / 'tasks/current/TASK-002.json')
        before = contracts.structural_task_digest([task])
        old_task = (PLAN / 'tasks/current/TASK-002.json').as_posix()
        new_task = old_task.replace('/plans/current/', '/plans/completed/').replace('/tasks/current/','/tasks/completed/')
        task['status'] = 'completed'
        for key in ('spec_refs','adr_refs','research_refs','input_contracts','output_contracts'):
            task[key] = [v.replace('/plans/current/','/plans/completed/') for v in task[key]]
        for key in ('write_paths','read_paths','prohibited_paths'):
            task['scope'][key] = [v.replace('/plans/current/','/plans/completed/') for v in task['scope'][key]]
        self.assertEqual(before, contracts.structural_task_digest([task]))
        plan = read_json(WT/PLAN/'plan.json'); plan['status'] = 'completed'
        old_graph_ref = plan['graph_ref']
        for key in ('graph_ref','document_ref','isolation_review_ref'):
            plan[key] = plan[key].replace('/plans/current/','/plans/completed/')
        plan['spec_refs'] = [v.replace('/plans/current/','/plans/completed/') for v in plan['spec_refs']]
        state = read_json(WT/'.ai/STATE.json')
        state.update(generation=23,active_plans=[],completed_plans=['PLAN-001'])
        manifest = {'schema_version':'1.0','kind':'archive-manifest','id':'ARCHIVE-1','plan_id':'PLAN-001',
            'reason':'completed snapshot','merge_evidence_ref':'evidence:PLAN-001:MERGE-1',
            'artifacts':[{'path':'tasks/current/TASK-002.json','sha256':sha(git('show',HEAD+':'+old_task))}],
            'retained_commit_oids':[HEAD],'created_at':NOW.isoformat()}
        for record in (task,plan,state,manifest): REG.validate(record)
        mr = dv.RecordRef('archive-manifest','ARCHIVE-1','PLAN-001')
        updates = (
            lp.ProjectionUpdate(dv.RecordRef('task','TASK-002','PLAN-001'),task,old_task,new_task,
                (lp.ReferenceUpdate(dv.RecordRef('plan','PLAN-001'),('graph_ref',),old_graph_ref,plan['graph_ref']),),
                (lp.ManifestEffect(mr,'retain','tasks/current/TASK-002.json',manifest['artifacts'][0]['sha256']),)),
            lp.ProjectionUpdate(dv.RecordRef('plan','PLAN-001'),plan,PLAN.as_posix()+'/',PLAN.as_posix().replace('/plans/current/','/plans/completed/')+'/'),
            lp.ProjectionUpdate(dv.RecordRef('project-state',state['project_id']),state),
            lp.ProjectionUpdate(mr,manifest),
        )
        tx = lp.TransactionRequest(state['project_id'],'RUN-1',22,'OP-MOVE',(
            lp.StateEvent('EV-MOVE','OP-MOVE',23,'PLAN-001','plan_completed','running','completed',(),NOW,None),),updates)
        self.assertEqual(len(tx.projection_updates),4)
        self.assertEqual(tx.projection_updates[0].manifest_effects[0].artifact_path.value,'tasks/current/TASK-002.json')
        manifest['artifacts'][0]['path']='mutated.json'
        self.assertEqual(tx.projection_updates[3].record['artifacts'][0]['path'],'tasks/current/TASK-002.json')
        intent = lp.OperationIntent('OP-MOVE','relocate','relocate-once','plan:PLAN-001','intent',())
        self.assertEqual(set(wire(intent)),set(REG.schema('workflow-run')['properties']['pending_operations']['items']['properties']))

    def test_control_command_evidence_does_not_override_validation_success_rule(self):
        definition = lp.CommandDefinition('test.zero',('python','-m','unittest'),'control',10,4096,'local_execute',(),('windows','linux'),'unittest_nonzero_count')
        request = lp.CommandRequest('project',None,'RUN-INIT','OP-CMD',definition,lp.CommandRootBindings(PROJECT,control=CONTROL),'.')
        self.assertEqual(request.cwd_binding,CONTROL)
        observed = lp.CommandEvidence('CE-0',definition.id,definition.argv,CONTROL.worktree_id,'.',NOW,NOW,0,'exited',lp.ContentRef('evidence/zero.log','e'*64),None,False,False,(),None)
        REG.validate(wire(definition)); REG.validate(wire(observed))
        command = wp.ValidationCommand(definition.id,definition.success_rule.value)
        failed = wp.ValidationCheck(command.command_id,command.success_rule,'failed',EVID,0,dv.DomainError(dv.ErrorCategory.VALIDATION_FAILED,'zero observed tests'))
        self.assertEqual(observed.exit_code,0); self.assertEqual(failed.observed_test_count,0)
        with self.assertRaisesRegex(ValueError,'positive test count'):
            wp.ValidationCheck(command.command_id,command.success_rule,'passed',EVID,0)
        with self.assertRaisesRegex(ValueError,'requires exit_code'):
            dataclasses.replace(observed,exit_code=None)
        unresolved = dataclasses.replace(observed,status='unknown',exit_code=None,finished_at=None,error_category='process_state_unknown')
        REG.validate(wire(unresolved))

    def test_git_expected_observed_and_unavailable_facts_remain_distinct(self):
        branch = git('symbolic-ref','HEAD').decode().strip()
        actual = git('rev-parse','HEAD').decode().strip()
        query = lp.GitRefQuery(branch,lp.GitRefExpectation(branch,'present',BASE))
        ancestry = lp.AncestryQuery(BASE,HEAD)
        request = lp.GitInspectRequest('project','RUN-1',PROJECT,(query,),(ancestry,))
        result = lp.GitSnapshot('succeeded','project','RUN-1',PROJECT,lp.GitHead('attached',branch,actual),
            (lp.GitRefObservation(branch,'present',actual),lp.GitRefObservation('refs/heads/absent','missing',None)),
            (lp.AncestryObservation(ancestry,'ancestor'),),(),lp.GitStatus(),NOW,(EVID,))
        self.assertNotEqual(request.refs[0].expected.oid,result.refs[0].oid)
        self.assertEqual(result.head.oid,HEAD)
        for head in (lp.GitHead('unborn','main',None),lp.GitHead('missing',None,None)):
            unknown = dataclasses.replace(result,status='unknown',head=head,working_tree=None,
                ancestry=(lp.AncestryObservation(ancestry,'unknown'),),error=dv.DomainError(dv.ErrorCategory.INTERNAL_ERROR,'partial inspection'))
            self.assertIsNone(unknown.working_tree)
        op = lp.GitOperationResult('unknown','OP-GIT','same-intent',None,None,(),(),(EVID,),dv.DomainError(dv.ErrorCategory.AMBIGUOUS_SIDE_EFFECT,'ref update not observed'))
        with self.assertRaisesRegex(ValueError,'cannot claim'):
            dataclasses.replace(op,changed=False)
        merge = lp.MergeRequest('project','PLAN-001','RUN-1','OP-MERGE','merge-once',PROJECT,'ai/PLAN-001/integration',BASE,branch,HEAD)
        self.assertEqual((merge.expected_integration_head_oid,merge.candidate_oid),(BASE,HEAD))

    def test_cleanup_fencing_and_retention_information_survives_handoff(self):
        record = lp.WorktreeRecord('WT-1','TASK-002','RUN-1','TASK-002-a1','task','ai/PLAN-001/TASK-002/a1','.worktrees/WT-1',BASE,HEAD,'cleanup_pending','LEASE-1',NOW,())
        binding = lp.LocalWorktreeBinding('project','WT-1',WT/'.worktrees/WT-1')
        guard = lp.CleanupGuard(record.branch,HEAD,'LEASE-1',(HEAD,))
        request = lp.CleanupRequest('project','PLAN-001','RUN-1','OP-CLEAN','cleanup-once',PROJECT,record,binding,guard)
        for lease in (lp.LeaseObservation('LEASE-1','RUN-1','TASK-002-a1',9,'unknown',None),lp.LeaseObservation('LEASE-1','RUN-1','TASK-002-a1',9,'expired',True)):
            observation = lp.WorktreeObservation('WT-1',binding.root,True,True,True,record.branch,HEAD,BASE,lp.GitStatus(untracked_paths=('unaccepted.txt',)),lease,True,False,'retain_required',False)
            reconcile = lp.ReconcileRequest('project','RUN-1',PROJECT,(record,),(binding,),(lease,),(HEAD,))
            proposals = tuple(lp.ReconcileAction(kind,'WT-1',binding.root,'needs coordinator reconciliation',False) for kind in ('fence_output','observe_process','retain_dirty','invalidate_approvals'))
            report = lp.ReconcileReport('succeeded','project','RUN-1',(observation,),proposals,(EVID,))
            self.assertEqual(reconcile.leases[0].generation,dv.Revision(9))
            self.assertFalse(report.observations[0].merged)
            self.assertTrue(report.observations[0].dirty.is_dirty)
            self.assertTrue(all(not p.safe_to_apply for p in report.proposed_actions))
        self.assertEqual(request.guard.retained_commit_oids,(HEAD,))
        for field in ('require_managed','require_clean','require_no_live_lease','require_merged_or_retained'):
            self.assertTrue(getattr(guard,field))
            with self.assertRaises(ValueError): dataclasses.replace(guard,**{field:False})
        self.assertNotIn('force',{f.name for f in dataclasses.fields(request)}|{f.name for f in dataclasses.fields(guard)})
        for field,value in (('expected_head_oid',BASE),('expected_lease_id','STALE-LEASE')):
            with self.assertRaises(ValueError): dataclasses.replace(request,guard=dataclasses.replace(guard,**{field:value}))
        REG.validate(wire(record))

if __name__ == '__main__':
    verify_identity()
    result = unittest.TextTestRunner(stream=sys.stdout,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ConsistencyScenarios))
    sys.exit(0 if result.wasSuccessful() else 1)
