"""Independent R1 probes; candidate source is read-only and all expectations are public."""
from __future__ import annotations

import ast
import builtins
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
WT = ROOT / '.worktrees/TASK-008-a1'
PLAN = '.ai/plans/current/PLAN-001/'
CANDIDATE = PLAN + 'reviews/candidates/CANDIDATE-TASK-008-a1-fcb01a93f0e1.json'
sys.path.insert(0, str(WT / 'src'))
import transitions as t
import domain_values as d
import contracts
import local_ports as lp


def git(*args, cwd=WT):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True).stdout


def identity():
    c = json.loads((ROOT / CANDIDATE).read_bytes())
    assert git('rev-parse', 'HEAD').decode().strip() == c['head_oid']
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == c['base_oid']
    assert not git('status', '--porcelain=v1').strip()
    git('merge-base', '--is-ancestor', c['base_oid'], c['head_oid'])
    assert hashlib.sha256(git('diff', '--binary', c['base_oid'], c['head_oid'])).hexdigest() == c['diff_sha256']
    for ref in c['context_refs']:
        assert hashlib.sha256(git('show', c['head_oid'] + ':' + ref['path'])).hexdigest() == ref['sha256'], ref
    for ref in c['validation_refs']:
        assert hashlib.sha256((ROOT / ref['path']).read_bytes()).hexdigest() == ref['sha256'], ref
    pm = b''.join((ROOT / p).read_bytes() for p in ['.ai/project/policy.json', '.ai/project/agent-models.json'])
    assert hashlib.sha256(pm).hexdigest() == c['policy_model_digest']
    body = {k: v for k, v in c.items() if k != 'fingerprint'}
    assert hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest() == c['fingerprint']
    paths = git('diff', '--name-status', c['base_oid'], c['head_oid']).decode().splitlines()
    assert set(paths) == {'A\tsrc/transitions.py', 'A\ttests/unit/domain_transitions/test_transitions.py', 'A\t' + PLAN + 'evidence/implementation/TASK-008.md'}
    graph = json.loads((WT / PLAN / 'graph.json').read_bytes())
    iso = json.loads((WT / PLAN / 'reviews/r4-isolation-review.json').read_bytes())
    tasks = [json.loads(p.read_bytes()) for p in (WT / PLAN / 'tasks/current').glob('*.json')]
    assert len(tasks) == 39
    digest = contracts.structural_task_digest(tasks)
    assert digest == graph['task_set_sha256'] == iso['task_set_sha256']
    assert graph['revision'] == c['graph_revision'] == iso['graph_revision'] == 4
    assert graph['status'] == 'approved' and iso['verdict'] == 'pass'
    assert all(x['status'] in {'pass', 'not_applicable'} for x in iso['checks'])
    task = next(x for x in tasks if x['id'] == 'TASK-008')
    assert task['depends_on'] == ['TASK-001', 'TASK-004'] == next(x for x in graph['nodes'] if x['task_id'] == 'TASK-008')['depends_on']
    for dep, oid, source in [('TASK-001', 'd1fc917466410febc6238479e65816dd39591a4f', 'src/domain_values.py'), ('TASK-004', 'e3c1177f993ee74815639a83ef3333faa4ba3957', 'src/contracts.py'), ('TASK-002', '460ab567d01912167557f2f671ed07c63f0a31e7', 'src/local_ports.py')]:
        assert next(x for x in tasks if x['id'] == dep)['status'] == 'accepted'
        git('merge-base', '--is-ancestor', oid, c['base_oid'])
        assert git('show', oid + ':' + source) == git('show', c['head_oid'] + ':' + source)
    for module in [t, d, contracts, lp]:
        assert Path(module.__file__).resolve().parent == WT / 'src'
    git('diff', '--check', c['base_oid'], c['head_oid'])
    print('IDENTITY PASS:', c['base_oid'], '->', c['head_oid'])
    print('Fingerprint:', c['fingerprint'], '; raw diff/context/validation/policy digests verified')
    print('Graph r4 digest:', digest, '; 39 tasks; accepted 001/004 source exact; accepted002 translation source exact')
    print('Changed paths:', paths)
    print('Source SHA256:', hashlib.sha256(git('show', c['head_oid'] + ':src/transitions.py')).hexdigest())
    print('Imports:', {m.__name__: str(m.__file__) for m in [t, d, contracts, lp]})
    definition = json.loads((WT / PLAN / 'commands/test.TASK-008.json').read_bytes())
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    argv = [str(ROOT / '.ai/local/full-plan-venv/Scripts/python.exe'), *definition['argv'][1:]]
    result = subprocess.run(argv, cwd=WT, env=env, capture_output=True, text=True)
    print('DECLARED:', repr(argv), 'cwd=', WT, 'exit=', result.returncode)
    print(result.stdout + result.stderr)
    assert result.returncode == 0 and 'Ran 19 tests' in result.stderr


def ref(name):
    return d.EvidenceRef(d.ScopePath.exact_file('.ai/evidence/' + name + '.json'), d.Sha256Digest(hashlib.sha256(name.encode()).hexdigest()))


# These guard/edge expectations are transcribed from the published lifecycle requirements,
# not imported from private reducer tables. The matrix checks every status pair.
EDGES = {}
def edge(kind, a, b, names='', **metadata):
    EDGES[kind, a, b] = (set(names.split()) | {'state_observed'}, metadata)

for a, b, guards in [
    ('draft','isolation',''), ('isolation','approved','graph_approval_current'),
    ('approved','running','graph_approval_current'), ('running','integration_review','live_tasks_accepted'),
    ('integration_review','delivery_ready','live_tasks_accepted integrated_validation_current integration_review_current'),
    ('delivery_ready','delivering','delivery_authorized'),
    ('delivering','completed','live_tasks_accepted integrated_validation_current integration_review_current current_head_ci_passed merge_observed'),
    ('running','replanning','recovery_proposal_recorded'), ('integration_review','replanning','recovery_proposal_recorded'),
    ('replanning','isolation','recovery_rewrite_committed acceptance_preserved recovery_constraints_preserved')]:
    edge('plan',a,b,guards,**({'payload_ref': ref('recovery')} if b == 'replanning' else {}))

for a, b, guards in [
    ('backlog','ready','dependencies_accepted_integrated'),
    ('ready','running','dependencies_accepted_integrated scope_lease_active'),
    ('running','validating','scope_lease_active candidate_recorded_current'),
    ('validating','review_1','validation_current'), ('review_1','review_2','validation_current review_1_current'),
    ('review_2','accepted','validation_current review_1_current review_2_current'),
    ('accepted','completed','integrated_validation_current integration_review_current current_head_ci_passed merge_observed'),
    ('repairing','validating','scope_lease_active candidate_recorded_current'),
    ('replanning','backlog','graph_approval_current acceptance_preserved recovery_constraints_preserved'),
    ('replanning','superseded','graph_approval_current acceptance_preserved recovery_constraints_preserved successor_lineage_valid'),
    ('accepted','ready','candidate_invalidation_recorded dependencies_accepted_integrated')]:
    meta = {}
    if b == 'superseded': meta = {'successor_ids': ('TASK-101', 'TASK-100'), 'payload_ref': ref('successors')}
    if (a,b) == ('accepted','ready'): meta = {'invalidated_evidence_refs': (ref('stale'),), 'payload_ref': ref('invalidation')}
    edge('task',a,b,guards,**meta)
for a in ['validating','review_1','review_2']:
    edge('task',a,'repairing','repair_trigger_recorded prior_approvals_invalidated', invalidated_evidence_refs=(ref('old-approval'),), payload_ref=ref('repair'))
for a in ['backlog','ready','running','validating','review_1','review_2','repairing','accepted']:
    edge('task',a,'replanning','recovery_proposal_recorded',payload_ref=ref('recovery'))

PLAN_ENTRY = {'draft':'', 'isolation':'', 'approved':'graph_approval_current', 'running':'graph_approval_current', 'integration_review':'live_tasks_accepted', 'delivery_ready':'live_tasks_accepted integrated_validation_current integration_review_current', 'delivering':'delivery_authorized', 'replanning':'recovery_proposal_recorded'}
TASK_ENTRY = {'backlog':'', 'ready':'dependencies_accepted_integrated', 'running':'dependencies_accepted_integrated scope_lease_active', 'validating':'scope_lease_active candidate_recorded_current', 'review_1':'validation_current', 'review_2':'validation_current review_1_current', 'accepted':'validation_current review_1_current review_2_current', 'repairing':'repair_trigger_recorded prior_approvals_invalidated', 'replanning':'recovery_proposal_recorded'}
for kind, entries in [('plan',PLAN_ENTRY),('task',TASK_ENTRY)]:
    block = 'block_reason_recorded recovery_action_recorded' if kind == 'plan' else 'block_reason_recorded scope_lease_quiescent inputs_reconciled'
    for state, guards in entries.items():
        edge(kind,state,'blocked',block,resume_state=state,payload_ref=ref('block'))
        edge(kind,'blocked',state,guards+' inputs_reconciled',resume_state=state,**({'payload_ref':ref('recovery')} if state == 'replanning' else {}))
for a,b,g in [('queued','running','run_started'),('running','paused','pause_reason_recorded recovery_action_recorded'),('paused','running','inputs_reconciled'),('running','succeeded','workflow_success_confirmed'),('running','failed','terminal_failure_confirmed'),('running','cancelled','cancellation_explicit cancellation_observed')]:
    edge('workflow-run',a,b,g,**({'payload_ref':ref('pause')} if b == 'paused' else {}))
for a, targets in [('queued',['running']),('running',['succeeded','failed','cancelled','unknown']),('unknown',['queued','running','succeeded','failed','cancelled'])]:
    for b in targets: edge('agent-run',a,b,'provider_observation_current'+(' agent_output_valid' if b == 'succeeded' else ''))
for a,b,g in [('planned','active','git_identity_registered'),('active','retained','retention_recorded'),('active','cleanup_pending','cleanup_guards_satisfied'),('retained','cleanup_pending','cleanup_guards_satisfied'),('retained','removed','cleanup_guards_satisfied'),('cleanup_pending','removed','cleanup_guards_satisfied')]:
    edge('worktree',a,b,g)
for a,b,g in [('prepared','open','remote_state_observed'),('open','checks_pending','remote_state_observed'),('checks_pending','ready','exact_remote_head_checks_passed'),('ready','merged','exact_remote_head_checks_passed delivery_authorized merge_observed'),('open','closed','close_observed'),('checks_pending','closed','close_observed'),('ready','closed','close_observed')]:
    edge('pr-state',a,b,g)


def make(key, names=None, **override):
    expected, metadata = EDGES.get(key, ({'state_observed'}, {}))
    guards = [t.GuardEvidence(t.TransitionGuard(n), True, [ref(n)], 'subject-1') for n in (expected if names is None else names)]
    args = dict(lifecycle=key[0], entity_id='TASK-008' if key[0]=='task' else 'ENTITY-1', current_state=key[1], target_state=key[2], event_id='EVENT-1', operation_id='OP-1', generation=7, created_at=datetime(2026,9,8,9,0,tzinfo=timezone(timedelta(hours=-4))), guards=guards, **metadata)
    args.update(override)
    return t.TransitionRequest(**args)


class IndependentBehavior(unittest.TestCase):
    def test_every_status_pair_against_documented_edges(self):
        total = accepted = 0
        for kind, statuses in [('plan',d.PlanStatus),('task',d.TaskStatus),('workflow-run',d.WorkflowRunStatus),('agent-run',d.AgentRunStatus),('worktree',d.WorktreeStatus),('pr-state',d.PullRequestStatus)]:
            for a in statuses:
                for b in statuses:
                    key = (kind,a.value,b.value)
                    with self.subTest(edge=key):
                        decision = t.decide_transition(make(key))
                        self.assertEqual(decision.accepted, key in EDGES)
                        if key not in EDGES: self.assertEqual(decision.error.category, d.ErrorCategory.STATE_CONFLICT)
                    total += 1
                    accepted += key in EDGES
        print('MATRIX:', total, 'pairs;', accepted, 'accepted;', total-accepted, 'forbidden including all terminal departures/self edges')

    def test_remove_fail_and_add_guards_on_every_legal_edge(self):
        removals = failures = extras = 0
        for key, (required, _) in EDGES.items():
            req = make(key)
            for name in required:
                with self.subTest(edge=key, guard=name):
                    missing = t.decide_transition(make(key, required-{name}))
                    self.assertEqual(missing.error.category, d.ErrorCategory.VALIDATION_FAILED)
                    self.assertIn(name, missing.error.details['missing_guards'])
                    bad = dataclasses.replace(req, guards=[dataclasses.replace(g,satisfied=False) if g.guard.value==name else g for g in req.guards])
                    failed = t.decide_transition(bad)
                    self.assertEqual(failed.error.category, d.ErrorCategory.VALIDATION_FAILED)
                    self.assertIn(name, failed.error.details['failed_guards'])
                removals += 1; failures += 1
            extra = next(g.value for g in t.TransitionGuard if g.value not in required)
            self.assertEqual(t.decide_transition(make(key,required|{extra})).error.category,d.ErrorCategory.INVALID_INPUT)
            extras += 1
        print('GUARDS:', removals, 'missing;', failures, 'failed;', extras, 'unrelated guard rejection cases')

    def test_subject_mismatches_across_all_joint_current_gates(self):
        bound = {'candidate_recorded_current','validation_current','review_1_current','review_2_current','integrated_validation_current','integration_review_current','current_head_ci_passed','merge_observed','exact_remote_head_checks_passed'}
        count = 0
        for key, (names, _) in EDGES.items():
            if len(names & bound)<2: continue
            req = make(key)
            chosen = sorted(names & bound)[-1]
            bad = dataclasses.replace(req,guards=[dataclasses.replace(g,subject='different-subject') if g.guard.value==chosen else g for g in req.guards])
            self.assertEqual(t.decide_transition(bad).error.category,d.ErrorCategory.STATE_CONFLICT)
            count += 1
        for name in bound:
            with self.assertRaises(ValueError): t.GuardEvidence(name,True,[ref('x')])
        print('SUBJECTS:', count, 'joint candidate/head mismatch cases; all',len(bound),'subject-required guard names checked')

    def test_all_block_resume_metadata_and_rechecks(self):
        for kind, entries in [('plan',PLAN_ENTRY),('task',TASK_ENTRY)]:
            for state in entries:
                blocked = t.decide_transition(make((kind,state,'blocked')))
                self.assertEqual(blocked.changes.resume_state,state)
                wrong = make((kind,state,'blocked'),resume_state='running' if state!='running' else 'backlog' if kind=='task' else 'draft')
                self.assertFalse(t.decide_transition(wrong).accepted)
                resume = t.decide_transition(make((kind,'blocked',state)))
                self.assertTrue(resume.accepted)
                self.assertTrue(resume.changes.clear_resume_state)
                self.assertIsNone(resume.changes.resume_state)
                wrong = make((kind,'blocked',state),resume_state='running' if state!='running' else 'backlog' if kind=='task' else 'draft')
                self.assertFalse(t.decide_transition(wrong).accepted)
        print('BLOCK/RESUME: all 17 prior states preserved; mismatched prior states rejected; every fresh entry guard tested above')

    def test_metadata_is_consumed_and_payload_is_required(self):
        ordinary = make(('task','backlog','ready'))
        for extra in [dict(resume_state='backlog'),dict(successor_ids=('TASK-100',)),dict(invalidated_evidence_refs=(ref('stale'),))]:
            self.assertEqual(t.decide_transition(dataclasses.replace(ordinary,**extra)).error.category,d.ErrorCategory.INVALID_INPUT)
        for key, (_,meta) in EDGES.items():
            if 'payload_ref' in meta:
                self.assertEqual(t.decide_transition(make(key,payload_ref=None)).error.category,d.ErrorCategory.VALIDATION_FAILED)
            if 'invalidated_evidence_refs' in meta:
                self.assertFalse(t.decide_transition(make(key,invalidated_evidence_refs=())).accepted)
                self.assertEqual(t.decide_transition(make(key)).changes.invalidated_evidence_refs,meta['invalidated_evidence_refs'])
            if 'successor_ids' in meta:
                self.assertFalse(t.decide_transition(make(key,successor_ids=())).accepted)
                self.assertEqual(tuple(x.value for x in t.decide_transition(make(key)).changes.superseded_by),tuple(sorted(meta['successor_ids'])))

    def test_purity_determinism_and_immutable_snapshots(self):
        source = ast.parse((WT/'src/transitions.py').read_text())
        modules = {n.module if isinstance(n,ast.ImportFrom) else alias.name for n in ast.walk(source) if isinstance(n,(ast.Import,ast.ImportFrom)) for alias in (n.names[:1] if isinstance(n,ast.ImportFrom) else n.names)}
        self.assertLessEqual(modules,{'__future__','collections.abc','dataclasses','datetime','enum','typing','domain_values'})
        for key in EDGES:
            req = make(key)
            reverse = dataclasses.replace(req,guards=list(reversed(req.guards)))
            with patch.object(builtins,'open',side_effect=AssertionError('file IO')), patch.object(subprocess,'run',side_effect=AssertionError('process IO')), patch.object(socket,'create_connection',side_effect=AssertionError('network IO')), patch.object(time,'time',side_effect=AssertionError('clock IO')):
                first = t.decide_transition(req)
                self.assertEqual(first,t.decide_transition(reverse))
                self.assertEqual(first,t.decide_transition(req))
            self.assertEqual(first.event.created_at.utcoffset(),timedelta(0))
            for obj, field in [(req,'generation'),(req.guards[0],'satisfied'),(first,'event'),(first.event,'to_state'),(first.changes,'clear_resume_state')]:
                with self.assertRaises(dataclasses.FrozenInstanceError): setattr(obj,field,None)
        refs=[ref('shared')]; g=t.GuardEvidence('state_observed',True,refs)
        mutable=[g]; req=make(('plan','draft','isolation'),guards=mutable)
        refs.clear(); mutable.clear()
        self.assertTrue(t.decide_transition(req).accepted)
        shared=ref('shared'); req=make(('plan','isolation','approved'),guards=[t.GuardEvidence(n,True,[shared]) for n in ['state_observed','graph_approval_current']])
        self.assertEqual(t.decide_transition(req).event.evidence_refs,(shared,))

    def test_accepted002_event_projection_transaction_mapping(self):
        registry=contracts.ContractRegistry(WT/'schemas/v1')
        # Every decision event maps to accepted002 without adding plan_id to state-event.
        for key in EDGES:
            decision=t.decide_transition(make(key)); event=decision.event
            mapped=lp.StateEvent(event.id,event.operation_id,event.generation,event.entity_id,event.event_type,event.from_state,event.to_state,tuple(x.path.as_wire() for x in event.evidence_refs),event.created_at,None if event.payload_ref is None else lp.ContentRef(event.payload_ref.path.as_wire(),event.payload_ref.sha256))
            wire={f.name:getattr(mapped,f.name) for f in dataclasses.fields(mapped)}
            for name in ['id','operation_id','generation','entity_id']: wire[name]=wire[name].value
            wire['evidence_refs']=list(wire['evidence_refs']); wire['created_at']=wire['created_at'].isoformat()
            if mapped.payload_ref is not None: wire['payload_ref']={'path':mapped.payload_ref.path,'sha256':mapped.payload_ref.sha256.value}
            self.assertNotIn('plan_id',wire); registry.validate(wire)
            if key[0] != 'task': continue
            record=json.loads((WT/PLAN/'tasks/current/TASK-008.json').read_bytes())
            record['status']=event.to_state
            changes=decision.changes
            if changes.resume_state is not None: record['resume_state']=changes.resume_state
            if changes.clear_resume_state: record['resume_state']=None
            if changes.superseded_by: record['superseded_by']=[x.value for x in changes.superseded_by]
            registry.validate(record)
            projection=lp.ProjectionUpdate(d.RecordRef('task',d.EntityId('TASK-008'),d.PlanId('PLAN-001')),record)
            transaction=lp.TransactionRequest('PROJECT-1','RUN-1',6,event.operation_id,[mapped],[projection])
            self.assertEqual(transaction.events[0].generation.value,transaction.expected_generation.value+1)
        print('MAPPING:',len(EDGES),'events schema-valid through accepted002; task metadata projections and generation-7 transactions construct without plan_id event field')

    def test_malformed_inputs_fail_before_decisions(self):
        normal=make(('plan','draft','isolation'))
        for changes in [dict(guards='state_observed'),dict(guards=[normal.guards[0],normal.guards[0]]),dict(created_at=datetime(2026,9,8)),dict(generation=True),dict(generation=-1),dict(successor_ids='TASK-100'),dict(successor_ids=('TASK-100','TASK-100')),dict(invalidated_evidence_refs=(ref('old'),ref('old'))),dict(payload_ref='not-evidence')]:
            with self.assertRaises((TypeError,ValueError)): dataclasses.replace(normal,**changes)
        for satisfied, refs in [(1,[ref('x')]),(True,[]),(True,['plain-ref'])]:
            with self.assertRaises((TypeError,ValueError)): t.GuardEvidence('state_observed',satisfied,refs)


if __name__=='__main__':
    identity()
    outcome=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(IndependentBehavior))
    assert not git('status','--porcelain=v1').strip()
    assert git('rev-parse','HEAD').decode().strip()=='fcb01a93f0e1022c70fa296f7342ced71bbf3250'
    print('FINAL CANDIDATE CHECK: frozen head and clean worktree unchanged')
    raise SystemExit(not outcome.wasSuccessful())
