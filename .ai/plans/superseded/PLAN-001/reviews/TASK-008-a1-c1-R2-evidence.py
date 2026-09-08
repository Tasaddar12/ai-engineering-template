"""Independent R2 consistency probes; reads the frozen candidate, writes no source."""
from __future__ import annotations

import ast
import builtins
import copy
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-008-a1'
P = '.ai/plans/current/PLAN-001/'
REVIEW = P + 'reviews/TASK-008-a1-c1-R2'
CREF = P + 'reviews/candidates/CANDIDATE-TASK-008-a1-fcb01a93f0e1.json'
R1REF = P + 'reviews/TASK-008-a1-c1-R1.json'
BASE = 'ecbc4b70cd54e55c22311e9a656be0b73bb6291f'
HEAD = 'fcb01a93f0e1022c70fa296f7342ced71bbf3250'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'src'))
import transitions as tr
import domain_values as dv
import contracts as co
import local_ports as lp

def read(path, root=WT):
    return json.loads((root / path).read_bytes())

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args, root=WT):
    return subprocess.check_output(['git', '-C', str(root), *args], shell=False)

def identity():
    c = read(CREF, ROOT)
    assert c['base_oid'] == BASE and c['head_oid'] == HEAD
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('rev-parse', 'HEAD', root=ROOT).decode().strip() == BASE
    assert not git('status', '--porcelain')
    git('merge-base', '--is-ancestor', BASE, HEAD)
    assert sha(git('diff', '--binary', BASE, HEAD)) == c['diff_sha256']
    for ref in c['context_refs']:
        assert sha(git('show', HEAD + ':' + ref['path'])) == ref['sha256'], ref
        assert git('show', BASE + ':' + ref['path']) == git('show', HEAD + ':' + ref['path'])
    for ref in c['validation_refs']:
        assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref
    assert sha((ROOT / '.ai/project/policy.json').read_bytes() +
               (ROOT / '.ai/project/agent-models.json').read_bytes()) == c['policy_model_digest']
    body = {k: v for k, v in c.items() if k != 'fingerprint'}
    assert sha(json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == c['fingerprint']
    for f in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
        assert read(f, ROOT) == read(f)
        assert git('show', BASE + ':' + f) == git('show', HEAD + ':' + f)
    registry.validate(c, source=CREF)
    r1 = read(R1REF, ROOT)
    registry.validate(r1, source=R1REF)
    assert r1['verdict'] == 'pass' and r1['stage'] == 'implementation'
    assert r1['candidate_ref'] == CREF and r1['candidate_fingerprint'] == c['fingerprint']
    assert r1['checklist_version'] == c['checklist_version'] == 'PLAN-001-v1'
    assert [x['id'] for x in r1['checks']] == [f'R1-{n:02}' for n in range(1, 12)]
    assert all(x['status'] == 'pass' for x in r1['checks']) and not r1['findings']
    assert r1['independent_session_id'] == '/root/r1_008_c1'
    assert r1['implementation_session_id'] == '/root/implement_008'
    graph = read(P + 'graph.json')
    tasks = [read(P + 'tasks/current/' + name + '.json') for name in read(P + 'plan.json')['task_ids']]
    digest = co.structural_task_digest(tasks)
    iso = read(P + 'reviews/r4-isolation-review.json')
    assert graph['revision'] == iso['graph_revision'] == c['graph_revision'] == 4
    assert graph['status'] == 'approved' and iso['verdict'] == 'pass'
    assert digest == graph['task_set_sha256'] == iso['task_set_sha256']
    assert len(tasks) == 39
    assert {t['id']: t['depends_on'] for t in tasks} == {n['task_id']: n['depends_on'] for n in graph['nodes']}
    accepted = {'001': ('d1fc917466410febc6238479e65816dd39591a4f', ['src/domain_values.py']),
                '004': ('e3c1177f993ee74815639a83ef3333faa4ba3957', ['src/contracts.py', 'src/install.py', 'src/validate_foundation.py']),
                '002': ('460ab567d01912167557f2f671ed07c63f0a31e7', ['src/local_ports.py'])}
    for number, (oid, sources) in accepted.items():
        task = read(P + f'tasks/current/TASK-{number}.json')
        assert task['status'] == 'accepted' and oid in task['resume_state']
        git('merge-base', '--is-ancestor', oid, BASE)
        for path in sources + [P + f'evidence/implementation/TASK-{number}.md']:
            assert git('show', oid + ':' + path) == git('show', HEAD + ':' + path), path
    changed = git('diff', '--name-status', BASE, HEAD).decode().splitlines()
    assert set(changed) == {'A\tsrc/transitions.py', 'A\ttests/unit/domain_transitions/test_transitions.py',
                            'A\t' + P + 'evidence/implementation/TASK-008.md'}
    git('diff', '--check', BASE, HEAD)
    assert read(P + 'tasks/current/TASK-008.json')['depends_on'] == ['TASK-001', 'TASK-004']
    assert 'TASK-008' in read(P + 'tasks/current/TASK-009.json')['depends_on']
    for module in (tr, dv, co, lp):
        assert Path(module.__file__).resolve().parent == (WT / 'src').resolve()
    print('IDENTITY PASS:', BASE, '->', HEAD, flush=True)
    print('Fingerprint:', c['fingerprint'], '; raw diff, 13 context refs, validation, policy/model verified', flush=True)
    print('R1 exact binding:', R1REF, '; SHA256', sha((ROOT / R1REF).read_bytes()), flush=True)
    print('Graph r4:', digest, '; 39 tasks; accepted001/004 and relevant002 exact source/handoff ancestry', flush=True)
    print('Owned additions:', changed, '; task-local imports:', [m.__file__ for m in (tr, dv, co, lp)], flush=True)

registry = co.ContractRegistry(WT / 'schemas/v1')
G = tr.TransitionGuard
K = tr.LifecycleKind
NOW = datetime(2026, 9, 8, 6, 0, tzinfo=timezone.utc)
SUBJECT_GUARDS = {G.CANDIDATE_RECORDED_CURRENT, G.VALIDATION_CURRENT, G.REVIEW_1_CURRENT,
                  G.REVIEW_2_CURRENT, G.INTEGRATED_VALIDATION_CURRENT, G.INTEGRATION_REVIEW_CURRENT,
                  G.CURRENT_HEAD_CI_PASSED, G.MERGE_OBSERVED, G.EXACT_REMOTE_HEAD_CHECKS_PASSED}

def ev(name):
    return dv.EvidenceRef(dv.ScopePath.exact_file(P + 'evidence/' + name + '.json'), dv.Sha256Digest(sha(name.encode())))

def request(kind, before, after, guards=(), **kw):
    identity = 'PLAN-001' if kind == K.PLAN else 'TASK-008' if kind == K.TASK else 'entity-008'
    values = dict(lifecycle=kind, entity_id=identity, current_state=before, target_state=after,
                  event_id='event-' + kind.value + '-' + before + '-' + after,
                  operation_id='operation-r2', generation=8, created_at=NOW,
                  guards=tuple(tr.GuardEvidence(g, True, (ev(g.value),), 'subject-current' if g in SUBJECT_GUARDS else None)
                               for g in (G.STATE_OBSERVED, *guards)))
    values.update(kw)
    return tr.TransitionRequest(**values)

def port_event(event):
    return lp.StateEvent(event.id, event.operation_id, event.generation, event.entity_id,
                         event.event_type, event.from_state, event.to_state,
                         tuple(e.path.as_wire() for e in event.evidence_refs), event.created_at,
                         None if event.payload_ref is None else lp.ContentRef(event.payload_ref.path.as_wire(), event.payload_ref.sha256))

def wire(event):
    return dict(schema_version=event.schema_version, kind=event.kind, id=event.id.value,
                operation_id=event.operation_id.value, generation=event.generation.value,
                entity_id=event.entity_id.value, event_type=event.event_type,
                from_state=event.from_state, to_state=event.to_state,
                evidence_refs=list(event.evidence_refs), created_at=event.created_at.isoformat(),
                payload_ref=None if event.payload_ref is None else
                dict(path=event.payload_ref.path, sha256=event.payload_ref.sha256.value))

def projected(decision, kind, before=None):
    record = copy.deepcopy(before if before is not None else
                           read(P + ('plan.json' if kind == K.PLAN else 'tasks/current/TASK-008.json')))
    record['status'] = decision.event.to_state
    if decision.changes.resume_state is not None:
        record['resume_state'] = decision.changes.resume_state
    if decision.changes.clear_resume_state:
        record['resume_state'] = None
    if decision.changes.superseded_by:
        record['superseded_by'] = [e.value for e in decision.changes.superseded_by]
    registry.validate(record)
    ref = dv.RecordRef('plan', 'PLAN-001') if kind == K.PLAN else dv.RecordRef('task', 'TASK-008', 'PLAN-001')
    return lp.ProjectionUpdate(ref, dv.FrozenJsonObject(record))

def mapped(decision, kind, before=None):
    assert decision.accepted, decision.error
    event = port_event(decision.event)
    registry.validate(wire(event))
    projection = projected(decision, kind, before)
    tx = lp.TransactionRequest('project-1', 'run-1', 7, 'operation-r2', (event,), (projection,))
    assert tx.events[0].generation.value == 8 and tx.expected_generation.value == 7
    return projection.record.to_dict()

class Consistency(unittest.TestCase):
    def test_six_vocabularies_and_exact_v1_event_mapping(self):
        cases = [(K.PLAN, dv.PlanStatus, 'draft', 'isolation', ()),
                 (K.TASK, dv.TaskStatus, 'backlog', 'ready', (G.DEPENDENCIES_ACCEPTED_INTEGRATED,)),
                 (K.WORKFLOW_RUN, dv.WorkflowRunStatus, 'queued', 'running', (G.RUN_STARTED,)),
                 (K.AGENT_RUN, dv.AgentRunStatus, 'unknown', 'succeeded', (G.PROVIDER_OBSERVATION_CURRENT, G.AGENT_OUTPUT_VALID)),
                 (K.WORKTREE, dv.WorktreeStatus, 'planned', 'active', (G.GIT_IDENTITY_REGISTERED,)),
                 (K.PULL_REQUEST, dv.PullRequestStatus, 'checks_pending', 'ready', (G.EXACT_REMOTE_HEAD_CHECKS_PASSED,))]
        for kind, enum, before, after, guards in cases:
            self.assertEqual({s.value for s in enum}, set(registry.schema(kind.value)['properties']['status']['enum']))
            dec = tr.decide_transition(request(kind, before, after, guards))
            self.assertTrue(dec.accepted)
            event = port_event(dec.event)
            artifact = wire(event)
            registry.validate(artifact)
            self.assertEqual(set(artifact), set(registry.schema('state-event')['required']))
            self.assertNotIn('plan_id', artifact)
            for mutation in ({'plan_id': 'PLAN-001'}, {'schema_version': '2.0'}):
                with self.assertRaises(dv.DomainException):
                    registry.validate(artifact | mutation)
        print('VOCABULARY/EVENTS: 6 enums match schema; 6 exact v1 port mappings; 12 version/extra-field rejections')

    def test_task_accept_invalidate_repair_without_overwriting_history(self):
        reviews = (G.VALIDATION_CURRENT, G.REVIEW_1_CURRENT, G.REVIEW_2_CURRENT)
        req = request(K.TASK, 'review_2', 'accepted', reviews)
        accepted = tr.decide_transition(req)
        accepted_record = mapped(accepted, K.TASK)
        self.assertEqual(accepted_record['status'], 'accepted')
        old_snapshot = wire(port_event(accepted.event))
        missing = tr.decide_transition(request(K.TASK, 'accepted', 'completed'))
        self.assertEqual(missing.error.category, dv.ErrorCategory.VALIDATION_FAILED)
        stale = dataclasses.replace(req, guards=tuple(dataclasses.replace(g, subject='stale-candidate')
                                   if g.guard == G.REVIEW_2_CURRENT else g for g in req.guards))
        self.assertEqual(tr.decide_transition(stale).error.category, dv.ErrorCategory.STATE_CONFLICT)
        invalidated = ev('prior-accepted-review')
        bad = request(K.TASK, 'accepted', 'ready', (G.CANDIDATE_INVALIDATION_RECORDED, G.DEPENDENCIES_ACCEPTED_INTEGRATED), payload_ref=ev('why-invalidated'))
        self.assertFalse(tr.decide_transition(bad).accepted)
        ready = tr.decide_transition(dataclasses.replace(bad, invalidated_evidence_refs=(invalidated,)))
        self.assertEqual(ready.changes.invalidated_evidence_refs, (invalidated,))
        self.assertEqual(mapped(ready, K.TASK, accepted_record)['status'], 'ready')
        for before in ('validating', 'review_1', 'review_2'):
            repair = tr.decide_transition(request(K.TASK, before, 'repairing',
                 (G.REPAIR_TRIGGER_RECORDED, G.PRIOR_APPROVALS_INVALIDATED),
                 invalidated_evidence_refs=(invalidated,), payload_ref=ev('repair-history')))
            self.assertEqual(repair.changes.invalidated_evidence_refs, (invalidated,))
            mapped(repair, K.TASK)
        fresh = request(K.TASK, 'repairing', 'validating', (G.SCOPE_LEASE_ACTIVE, G.CANDIDATE_RECORDED_CURRENT))
        mapped(tr.decide_transition(fresh), K.TASK)
        self.assertFalse(tr.decide_transition(dataclasses.replace(fresh, guards=fresh.guards[:-1])).accepted)
        self.assertEqual(wire(port_event(accepted.event)), old_snapshot)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            accepted.event.to_state = 'ready'
        print('HISTORY: acceptance distinct from completion; stale R2 rejected; explicit invalidation; 3 repair origins; fresh candidate required; prior event unchanged')

    def test_all_block_resume_projections_and_fresh_entry_guards(self):
        plan = {'draft': (), 'isolation': (), 'approved': (G.GRAPH_APPROVAL_CURRENT,),
                'running': (G.GRAPH_APPROVAL_CURRENT,), 'integration_review': (G.LIVE_TASKS_ACCEPTED,),
                'replanning': (G.RECOVERY_PROPOSAL_RECORDED,),
                'delivery_ready': (G.LIVE_TASKS_ACCEPTED, G.INTEGRATED_VALIDATION_CURRENT, G.INTEGRATION_REVIEW_CURRENT),
                'delivering': (G.DELIVERY_AUTHORIZED,)}
        task = {'backlog': (), 'ready': (G.DEPENDENCIES_ACCEPTED_INTEGRATED,),
                'running': (G.DEPENDENCIES_ACCEPTED_INTEGRATED, G.SCOPE_LEASE_ACTIVE),
                'validating': (G.SCOPE_LEASE_ACTIVE, G.CANDIDATE_RECORDED_CURRENT),
                'review_1': (G.VALIDATION_CURRENT,), 'review_2': (G.VALIDATION_CURRENT, G.REVIEW_1_CURRENT),
                'accepted': (G.VALIDATION_CURRENT, G.REVIEW_1_CURRENT, G.REVIEW_2_CURRENT),
                'repairing': (G.REPAIR_TRIGGER_RECORDED, G.PRIOR_APPROVALS_INVALIDATED),
                'replanning': (G.RECOVERY_PROPOSAL_RECORDED,)}
        omitted = 0
        for kind, entries in ((K.PLAN, plan), (K.TASK, task)):
            blockers = (G.BLOCK_REASON_RECORDED, G.RECOVERY_ACTION_RECORDED) if kind == K.PLAN else (G.BLOCK_REASON_RECORDED, G.SCOPE_LEASE_QUIESCENT, G.INPUTS_RECONCILED)
            for before, gates in entries.items():
                block = tr.decide_transition(request(kind, before, 'blocked', blockers, resume_state=before, payload_ref=ev('block-' + before)))
                state = mapped(block, kind)
                self.assertEqual(state['resume_state'], before)
                resume_req = request(kind, 'blocked', before, (G.INPUTS_RECONCILED, *gates), resume_state=state['resume_state'], payload_ref=ev('resume-' + before))
                resume = tr.decide_transition(resume_req)
                resumed = mapped(resume, kind, state)
                self.assertEqual(resumed['status'], before)
                self.assertIsNone(resumed['resume_state'])
                self.assertTrue(resume.changes.clear_resume_state)
                wrong = dataclasses.replace(resume_req, resume_state='approved' if kind == K.PLAN and before != 'approved' else 'draft' if kind == K.PLAN else 'ready' if before != 'ready' else 'backlog')
                self.assertEqual(tr.decide_transition(wrong).error.category, dv.ErrorCategory.STATE_CONFLICT)
                for gate in resume_req.guards:
                    result = tr.decide_transition(dataclasses.replace(resume_req, guards=tuple(x for x in resume_req.guards if x.guard != gate.guard)))
                    self.assertEqual(result.error.category, dv.ErrorCategory.VALIDATION_FAILED)
                    omitted += 1
        print('BLOCK/RESUME: 17 prior states; 34 schema-valid projections/transactions; explicit null clearing; 17 wrong-state and', omitted, 'fresh-guard omission rejections')

    def test_same_generation_completion_relocation_and_plan_identity(self):
        gates = (G.INTEGRATED_VALIDATION_CURRENT, G.INTEGRATION_REVIEW_CURRENT, G.CURRENT_HEAD_CI_PASSED, G.MERGE_OBSERVED)
        task = tr.decide_transition(request(K.TASK, 'accepted', 'completed', gates))
        plan = tr.decide_transition(request(K.PLAN, 'delivering', 'completed', (G.LIVE_TASKS_ACCEPTED, *gates)))
        task_projection = projected(task, K.TASK)
        plan_projection = projected(plan, K.PLAN)
        old = dv.ScopePath(P)
        new = dv.ScopePath('.ai/plans/completed/PLAN-001/')
        reference = lp.ReferenceUpdate(dv.RecordRef('project-state', 'project-1'), ('active_plans',), ['PLAN-001'], [])
        retain = lp.ManifestEffect(dv.RecordRef('archive-manifest', 'archive-1', 'PLAN-001'), lp.ManifestEffectKind.RETAIN,
                                   dv.ScopePath.exact_file('reviews/old-review.json'), dv.Sha256Digest('a' * 64))
        relocation = dataclasses.replace(plan_projection, old_location=old, new_location=new,
                                        reference_updates=(reference,), manifest_effects=(retain,))
        events = tuple(port_event(d.event) for d in (plan, task))
        for event in events:
            registry.validate(wire(event))
        tx = lp.TransactionRequest('project-1', 'run-1', 7, 'operation-r2', events, (relocation, task_projection))
        self.assertTrue(tx.projection_updates[0].is_relocation)
        self.assertFalse(task_projection.record['archived'])
        self.assertEqual(tx.projection_updates[0].manifest_effects[0].artifact_path.as_wire(), 'reviews/old-review.json')
        with self.assertRaises(ValueError):
            dataclasses.replace(tx, expected_generation=8)
        with self.assertRaises(ValueError):
            dataclasses.replace(tx, operation_id='wrong-operation')
        other_record = task_projection.record.to_dict() | {'plan_id': 'PLAN-002'}
        registry.validate(other_record)
        other = lp.ProjectionUpdate(dv.RecordRef('task', 'TASK-008', 'PLAN-002'), dv.FrozenJsonObject(other_record))
        qualified = dataclasses.replace(tx, projection_updates=(task_projection, other))
        self.assertNotEqual(qualified.projection_updates[0].ref, qualified.projection_updates[1].ref)
        print('COMPLETION: task+plan events share generation 8 over expected 7; relocation/reference/retained manifest grouped; archive independent; plan-qualified duplicate local IDs remain distinct')

    def test_recovery_lineage_guards_terminal_history_and_head_binding(self):
        guards = (G.GRAPH_APPROVAL_CURRENT, G.ACCEPTANCE_PRESERVED, G.RECOVERY_CONSTRAINTS_PRESERVED, G.SUCCESSOR_LINEAGE_VALID)
        req = request(K.TASK, 'replanning', 'superseded', guards, successor_ids=('TASK-101', 'TASK-100'), payload_ref=ev('successor-map'))
        result = tr.decide_transition(req)
        record = mapped(result, K.TASK)
        self.assertEqual(record['superseded_by'], ['TASK-100', 'TASK-101'])
        for omitted in guards:
            for failed in (False, True):
                altered = tuple(dataclasses.replace(g, satisfied=False) if failed and g.guard == omitted else g
                                for g in req.guards if failed or g.guard != omitted)
                self.assertFalse(tr.decide_transition(dataclasses.replace(req, guards=altered)).accepted)
        self.assertFalse(tr.decide_transition(dataclasses.replace(req, successor_ids=())).accepted)
        self.assertFalse(tr.decide_transition(dataclasses.replace(req, payload_ref=None)).accepted)
        terminals = 0
        for kind, before, states in ((K.PLAN, 'completed', dv.PlanStatus), (K.TASK, 'completed', dv.TaskStatus), (K.TASK, 'superseded', dv.TaskStatus)):
            for target in states:
                self.assertEqual(tr.decide_transition(request(kind, before, target.value)).error.category, dv.ErrorCategory.STATE_CONFLICT)
                terminals += 1
        pr = request(K.PULL_REQUEST, 'ready', 'merged', (G.EXACT_REMOTE_HEAD_CHECKS_PASSED, G.DELIVERY_AUTHORIZED, G.MERGE_OBSERVED))
        self.assertTrue(tr.decide_transition(pr).accepted)
        mismatched = dataclasses.replace(pr, guards=tuple(dataclasses.replace(g, subject='old-head') if g.guard == G.MERGE_OBSERVED else g for g in pr.guards))
        self.assertEqual(tr.decide_transition(mismatched).error.category, dv.ErrorCategory.STATE_CONFLICT)
        print('RECOVERY/DELIVERY:', terminals, 'terminal reopenings rejected; 8 lineage guard omission/failure cases; successor/payload required; stale merge head rejected')

    def test_pure_boundary_and_deterministic_snapshot(self):
        tree = ast.parse((WT / 'src/transitions.py').read_text(encoding='utf-8'))
        imports = {n.module.split('.')[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertLessEqual(imports, {'__future__', 'collections', 'dataclasses', 'datetime', 'enum', 'typing', 'domain_values'})
        self.assertFalse(any(isinstance(n, ast.Import) for n in ast.walk(tree)))
        req = request(K.TASK, 'review_2', 'accepted', (G.VALIDATION_CURRENT, G.REVIEW_1_CURRENT, G.REVIEW_2_CURRENT))
        with patch.object(builtins, 'open', side_effect=AssertionError('IO')), patch.object(subprocess, 'run', side_effect=AssertionError('IO')), patch.object(socket, 'create_connection', side_effect=AssertionError('IO')), patch.object(time, 'time', side_effect=AssertionError('IO')):
            first = tr.decide_transition(req)
            reverse = tr.decide_transition(dataclasses.replace(req, guards=tuple(reversed(req.guards))))
            self.assertEqual(first, reverse)
        self.assertIsInstance(first.event.generation, dv.Revision)
        self.assertIsInstance(first.event.entity_id, dv.EntityId)
        self.assertFalse(any(hasattr(tr, name) for name in ('StateStore', 'TransactionRequest', 'ContractRegistry')))
        print('BOUNDARY: explicit pure imports only; immutable equal decisions with reversed guards under IO traps; no persistence or schema-registry replacement')

if __name__ == '__main__':
    identity()
    command = read(P + 'commands/test.TASK-008.json')
    argv = [str(ROOT / '.ai/local/full-plan-venv/Scripts/python.exe'), *command['argv'][1:]]
    run = subprocess.run(argv, cwd=WT, shell=False, capture_output=True, text=True,
                         env=os.environ | {'PYTHONDONTWRITEBYTECODE': '1'}, timeout=command['timeout_seconds'])
    print('DECLARED:', argv, '; cwd=', WT, '; exit=', run.returncode, flush=True)
    print(run.stdout + run.stderr, flush=True)
    count = re.search(r'Ran (\d+) tests?', run.stdout + run.stderr)
    assert run.returncode == 0 and count and int(count[1]) == 19
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Consistency)
    result = unittest.TextTestRunner(verbosity=2, stream=sys.stdout).run(suite)
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD and not git('status', '--porcelain')
    print('FINAL CANDIDATE CHECK: unchanged frozen head and clean worktree', flush=True)
    sys.exit(0 if result.wasSuccessful() else 1)
