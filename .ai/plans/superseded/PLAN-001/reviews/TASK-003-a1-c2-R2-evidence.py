"""Independent R2 checks; review evidence only, never a product decoder/adapter."""
from __future__ import annotations

import ast
import dataclasses as dc
from datetime import UTC, datetime
from enum import Enum
import hashlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
import typing
import unittest

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-003-a1'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / 'src'))
import domain_values as dv
import workflow_ports as wp
from jsonschema import Draft202012Validator, FormatChecker

BASE = '3c8092625812b86a1e9bc7c7bfd454c38ee759e0'
HEAD = 'd51b72ce71ea3ac3ad31adf41e3eddc84738ac0b'
DEPENDENCY = 'd1fc917466410febc6238479e65816dd39591a4f'
PREFIX = '.ai/plans/current/PLAN-001/'
CANDIDATE_REF = PREFIX + 'reviews/candidates/CANDIDATE-TASK-003-a1-d51b72ce71ea.json'
R1_REF = PREFIX + 'reviews/TASK-003-a1-c2-R1.json'
CANDIDATE = json.loads((ROOT / CANDIDATE_REF).read_text())
R1 = json.loads((ROOT / R1_REF).read_text())
NOW = datetime(2026, 9, 8, tzinfo=UTC)
SHA = lambda data: hashlib.sha256(data).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.run(['git', *args], cwd=TREE, check=True, capture_output=True).stdout


def wire(value):
    if isinstance(value, dv.ScopeClaim):
        return value.to_wire()
    if isinstance(value, (dv.PlanId, dv.EntityId, dv.Revision, dv.Sha256Digest)):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat().replace('+00:00', 'Z')
    if isinstance(value, Enum):
        return value.value
    if dc.is_dataclass(value):
        return {f.name: wire(getattr(value, f.name)) for f in dc.fields(value)}
    if isinstance(value, (tuple, list)):
        return [wire(v) for v in value]
    if isinstance(value, dict):
        return {k: wire(v) for k, v in value.items()}
    return value


def schema(name):
    return json.loads((TREE / f'schemas/v1/{name}.schema.json').read_text())


def validate(name, value):
    Draft202012Validator(schema(name), format_checker=FormatChecker()).validate(wire(value))


def content(path: str, control=False):
    data = (ROOT / path).read_bytes() if control else git('show', HEAD + ':' + path)
    return wp.ContentRef(path, SHA(data))


def evidence():
    ref = CANDIDATE['validation_refs'][0]
    return dv.EvidenceRef(ref['path'], ref['sha256'])


def review_record(document):
    value = dict(document)
    value.pop('schema_version')
    value.pop('kind')
    value['reviewer'] = wp.ModelIdentity(**value['reviewer'])
    value['checks'] = [wp.ReviewCheck(**check) for check in value['checks']]
    value['findings'] = [wp.ReviewFinding(**finding) for finding in value['findings']]
    value['created_at'] = datetime.fromisoformat(value['created_at'].replace('Z', '+00:00'))
    return wp.ReviewResultRecord(**value)


class IndependentConsistencyTests(unittest.TestCase):
    def test_exact_candidate_r1_and_accepted_dependency(self):
        self.assertEqual(Path.cwd().resolve(), TREE.resolve())
        self.assertEqual(Path(wp.__file__).resolve(), TREE / 'src/workflow_ports.py')
        self.assertEqual(Path(dv.__file__).resolve(), TREE / 'src/domain_values.py')
        self.assertEqual(git('status', '--porcelain=v1'), b'')
        self.assertEqual(git('rev-parse', 'HEAD').decode().strip(), HEAD)
        git('merge-base', '--is-ancestor', BASE, HEAD)
        git('merge-base', '--is-ancestor', DEPENDENCY, BASE)
        self.assertEqual(CANDIDATE['base_oid'], BASE)
        self.assertEqual(CANDIDATE['head_oid'], HEAD)
        self.assertEqual(SHA(git('diff', '--binary', BASE, HEAD)), CANDIDATE['diff_sha256'])
        for ref in CANDIDATE['context_refs']:
            self.assertEqual(SHA(git('show', HEAD + ':' + ref['path'])), ref['sha256'])
        for ref in CANDIDATE['validation_refs']:
            self.assertEqual(SHA((ROOT / ref['path']).read_bytes()), ref['sha256'])
        policy_paths = ['.ai/project/policy.json', '.ai/project/agent-models.json']
        self.assertEqual(SHA(b''.join((ROOT / p).read_bytes() for p in policy_paths)), CANDIDATE['policy_model_digest'])
        for p in policy_paths:
            self.assertEqual(json.loads((ROOT / p).read_bytes()), json.loads(git('show', HEAD + ':' + p)))
        unsigned = {k: v for k, v in CANDIDATE.items() if k != 'fingerprint'}
        self.assertEqual(SHA(json.dumps(unsigned, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()), CANDIDATE['fingerprint'])
        self.assertEqual(CANDIDATE['fingerprint'], '7eed3420cb4bf419205dd2a64d08acfab8cf7d75f7068b7a8b28e7c6ff5f420f')
        validate('candidate', CANDIDATE)
        validate('review-result', R1)
        self.assertEqual((R1['stage'], R1['verdict'], R1['candidate_ref'], R1['candidate_fingerprint']), ('implementation', 'pass', CANDIDATE_REF, CANDIDATE['fingerprint']))
        self.assertEqual(R1['independent_session_id'], '/root/r1_003_c2')
        self.assertEqual(R1['implementation_session_id'], '/root/implement_003')
        self.assertEqual([c['id'] for c in R1['checks']], [f'R1-{i:02d}' for i in range(1, 12)])
        self.assertTrue(all(c['status'] == 'pass' for c in R1['checks']))
        task = json.loads(git('show', HEAD + ':' + PREFIX + 'tasks/current/TASK-001.json'))
        self.assertEqual(task['status'], 'accepted')
        self.assertIn(DEPENDENCY, task['resume_state'])
        for path in ['src/domain_values.py', 'tests/unit/domain_values/test_domain_values.py', PREFIX + 'evidence/implementation/TASK-001.md']:
            self.assertEqual(git('show', DEPENDENCY + ':' + path), git('show', HEAD + ':' + path))

    def test_owned_diff_imports_and_frozen_method_signatures(self):
        expected = ['src/workflow_ports.py', 'tests/unit/domain_workflow_ports/test_workflow_ports.py', PREFIX + 'evidence/implementation/TASK-003.md']
        self.assertEqual(set(git('diff', '--name-only', BASE, HEAD).decode().splitlines()), set(expected))
        self.assertTrue(all(line.startswith('A\t') for line in git('diff', '--name-status', BASE, HEAD).decode().splitlines()))
        git('diff', '--check', BASE, HEAD)
        parsed = ast.parse((TREE / 'src/workflow_ports.py').read_text())
        imports = {node.module for node in ast.walk(parsed) if isinstance(node, ast.ImportFrom)}
        self.assertEqual(imports - {'__future__', 'collections.abc', 'dataclasses', 'datetime', 'enum', 'typing'}, {'domain_values'})
        self.assertEqual({alias.name for node in ast.walk(parsed) if isinstance(node, ast.Import) for alias in node.names}, {'re'})
        expected_signatures = {
            wp.AgentAdapter: {'start': (['self', 'request', 'idempotency_key'], {'request': wp.AgentRequest, 'idempotency_key': str, 'return': wp.AgentHandle}), 'poll': (['self', 'handle'], {'handle': wp.AgentHandle, 'return': wp.AgentObservation}), 'cancel': (['self', 'handle'], {'handle': wp.AgentHandle, 'return': wp.CancelObservation})},
            wp.ContextBuilder: {'build': (['self', 'request'], {'request': wp.ContextRequest, 'return': wp.ContextBundle})},
            wp.Validator: {'run': (['self', 'request'], {'request': wp.ValidationRequest, 'return': wp.ValidationResult})},
            wp.ReviewService: {'evaluate': (['self', 'request'], {'request': wp.ReviewRequest, 'return': wp.ReviewResult})},
            wp.DeliveryAdapter: {'prepare': (['self', 'request'], {'request': wp.DeliveryRequest, 'return': wp.DeliveryDraft}), 'publish': (['self', 'draft', 'authorization'], {'draft': wp.DeliveryDraft, 'authorization': wp.Grant, 'return': wp.DeliveryObservation}), 'observe': (['self', 'handle'], {'handle': wp.DeliveryHandle, 'return': wp.DeliveryObservation})},
        }
        for port, methods in expected_signatures.items():
            self.assertEqual({n for n, obj in vars(port).items() if not n.startswith('_') and inspect.isfunction(obj)}, set(methods))
            for name, (parameters, annotations) in methods.items():
                function = getattr(port, name)
                self.assertEqual(list(inspect.signature(function).parameters), parameters)
                self.assertEqual(typing.get_type_hints(function), annotations)
        values = [getattr(wp, name) for name in wp.__all__ if dc.is_dataclass(getattr(wp, name))]
        self.assertEqual(len(values), 27)
        self.assertTrue(all(v.__dataclass_params__.frozen and hasattr(v, '__slots__') for v in values))

    def test_context_and_agent_request_use_actual_task_contract(self):
        task = json.loads(git('show', HEAD + ':' + PREFIX + 'tasks/current/TASK-003.json'))
        scope = dv.ScopeClaim(**task['scope'])
        refs = [wp.ContentRef(**ref) for ref in CANDIDATE['context_refs']]
        request = wp.ContextRequest('project', 'PLAN-001', 'run', 'context-op', task['id'], 'implementer', scope, task['spec_refs'], [PREFIX + 'evidence/implementation/TASK-001.md'], [], ['.ai/shared/architecture/service-contracts.md'], None, [c['id'] for c in task['acceptance_criteria']], [], 32000)
        bundle = wp.ContextBundle('context', request.task_id, request.role, refs, [content(request.dependency_handoff_refs[0])], [], [content(request.interface_refs[0])], None, request.acceptance_ids, 12000, request.token_budget, SHA(json.dumps(wire(refs), sort_keys=True).encode()), [], True)
        agent = wp.AgentRequest('request', 'workflow', request.run_id, 'TASK-003-a1', task['id'], request.plan_id, task['spec_refs'], request.role, CANDIDATE['graph_revision'], BASE, HEAD, 'TASK-003-a1', scope, 'context:PLAN-001:context', task['validation_commands'], [wp.AcceptanceCriterion(**c) for c in task['acceptance_criteria']], request.dependency_handoff_refs, [], 'implementation', '.ai/project/policy.json', ['local_execute'], 3, 'idempotency')
        validate('context-bundle', bundle)
        validate('agent-request', agent)
        self.assertEqual(agent.plan_id, request.plan_id)
        self.assertIsInstance(agent.scope, dv.ScopeClaim)
        self.assertEqual({r.path for r in bundle.documents}, {r['path'] for r in CANDIDATE['context_refs']})
        self.assertEqual({f.name for f in dc.fields(wp.AgentRequest)}, set(schema('agent-request')['properties']))
        self.assertEqual({f.name for f in dc.fields(wp.ContextBundle)}, set(schema('context-bundle')['properties']))

    def test_validation_precedes_fingerprint_and_r1_roundtrips(self):
        command = json.loads((TREE / (PREFIX + 'commands/test.TASK-003.json')).read_text())
        request = wp.ValidationRequest('project', 'PLAN-001', 'run', 'validate', 'TASK-003', HEAD, 'TASK-003-a1', 'suite-003', [wp.ValidationCommand(command['id'], command['success_rule'])])
        check = wp.ValidationCheck(command['id'], command['success_rule'], dv.ValidationStatus.PASSED, evidence(), 26)
        result = wp.ValidationResult(dv.ValidationStatus.PASSED, request.project_id, request.plan_id, request.run_id, request.operation_id, request.task_id, request.revision_oid, request.command_suite_id, [check], [evidence()])
        self.assertEqual(result.revision_oid, CANDIDATE['head_oid'])
        self.assertEqual(wire(wp.ContentRef(result.evidence_refs[0].path.as_wire(), result.evidence_refs[0].sha256)), CANDIDATE['validation_refs'][0])
        for cls in (wp.ValidationRequest, wp.ValidationResult):
            self.assertFalse({'candidate_ref', 'candidate_fingerprint'} & {f.name for f in dc.fields(cls)})
        record = review_record(R1)
        self.assertEqual(wire(record), R1)
        validate('review-result', record)
        r2 = wp.ReviewRequest('project', 'PLAN-001', 'run', 'review-op', 'R2-request', wp.ReviewStage.CONSISTENCY, 'TASK-003', CANDIDATE_REF, CANDIDATE['fingerprint'], 'PLAN-001-v1', [f'R2-{i:02d}' for i in range(1, 13)], content(CANDIDATE_REF, True), 'review_high', 4, R1['implementation_session_id'], content(R1_REF, True))
        self.assertEqual(r2.review_1_ref.sha256.value, SHA((ROOT / R1_REF).read_bytes()))
        envelope = wp.ReviewResult(dv.ResultStatus.SUCCEEDED, r2.project_id, r2.plan_id, r2.run_id, 'R1-op', record.request_id, record.candidate_fingerprint, record, [evidence()])
        self.assertEqual(envelope.record.verdict, dv.ReviewVerdict.PASS)
        with self.assertRaises(ValueError):
            dc.replace(envelope, candidate_fingerprint='0' * 64)
        with self.assertRaises(ValueError):
            dc.replace(r2, review_1_ref=None)

    def test_agent_observation_discovery_and_cancel_before_start(self):
        handle = wp.AgentHandle('project', 'PLAN-001', 'run', 'request', 'attempt', 3, 'fake-R2', 'dispatch', None)
        model = wp.ModelIdentity('implementation', 'deterministic-review-test', 'fake', 3, 'simulated-invocation')
        output = wp.AgentOutputRecord('output', handle.request_id, handle.attempt_id, dv.AgentOutputStatus.SUCCEEDED, model, [PREFIX + 'evidence/effort-provenance-clarification.md'], [], [], [], None, 'simulated success')
        run = wp.AgentRunRecord('agent-run', 'agent-request:PLAN-001:request', handle.attempt_id, dv.AgentRunStatus.SUCCEEDED, handle.adapter_id, 'discovered', model, NOW, NOW, 'agent-output:PLAN-001:output', None, handle.lease_generation)
        observation = wp.AgentObservation(run.status, handle, run, output, [evidence()])
        self.assertIsNone(observation.handle.external_handle)
        self.assertEqual(observation.run.external_handle, 'discovered')
        validate('agent-run', run)
        validate('agent-output', output)
        with self.assertRaises(ValueError):
            dc.replace(observation, handle=dc.replace(handle, external_handle='different'))
        cancelled = dc.replace(run, status=dv.AgentRunStatus.CANCELLED, actual_model=None, started_at=None, output_ref=None)
        cancelled_observation = wp.AgentObservation(cancelled.status, handle, cancelled, None, [evidence()], dv.DomainError(dv.ErrorCategory.TRANSIENT_PROVIDER, 'cancelled before start'))
        self.assertIsNone(cancelled_observation.run.started_at)
        validate('agent-run', cancelled)
        self.assertFalse(wp.CancelObservation(wp.CancelStatus.PENDING, handle, False, []).quiesced)
        self.assertTrue(wp.CancelObservation(wp.CancelStatus.CANCELLED, handle, True, [evidence()]).quiesced)
        with self.assertRaises(ValueError):
            dc.replace(cancelled_observation, output=output)
        with self.assertRaises(ValueError):
            wp.CancelObservation(wp.CancelStatus.PENDING, handle, True, [])

    def test_delivery_draft_ambiguity_discovery_and_remote_drift(self):
        request = wp.DeliveryRequest('project', 'PLAN-001', 'run', 'publish-op', 'publish-key', 'fixture/repository', 'main', 'ai/PLAN-001/integration', HEAD, 'Fixture draft', 'Reviewable local content', ['unit'], [content(PREFIX + 'tasks/current/TASK-003.json')], [content(R1_REF, True)], [wp.ContentRef(**CANDIDATE['validation_refs'][0])], content('.ai/STATE.json'))
        draft = wp.DeliveryDraft('draft', request, SHA(request.body.encode()), [evidence()])
        grant = wp.Grant('remote_pr_write', request.repository, 'fixture-authority')
        policy = schema('policy')
        Draft202012Validator(policy['properties']['external_grants']['items']).validate(wire(grant))
        handle = wp.DeliveryHandle(request.project_id, request.plan_id, request.run_id, request.operation_id, request.idempotency_key, request.repository, request.base_branch, request.head_branch, request.head_oid)
        ambiguous = wp.DeliveryObservation(wp.DeliveryObservationStatus.AMBIGUOUS, handle, None, [evidence()], dv.DomainError(dv.ErrorCategory.AMBIGUOUS_SIDE_EFFECT, 'simulated uncertain publication'))
        self.assertEqual(ambiguous.handle.idempotency_key, draft.request.idempotency_key)
        state = wp.PullRequestStateRecord('pr-state', handle.plan_id, handle.run_id, handle.repository, 9, 'https://example.invalid/pull/9', dv.PullRequestStatus.CHECKS_PENDING, 'release', handle.head_branch, '1' * 40, '2' * 40, request.required_checks, [wp.RemoteCheck('unit', HEAD, dv.CheckConclusion.SUCCESS, 'fixture-evidence')], dv.PullRequestReviewDecision.CHANGES_REQUESTED, None, [grant.authority_ref], handle.operation_id, NOW)
        observation = wp.DeliveryObservation(wp.DeliveryObservationStatus.OBSERVED, handle, state, [evidence()])
        self.assertIsNone(observation.handle.number)
        self.assertEqual(observation.state.number, 9)
        self.assertNotEqual(state.base_branch, handle.base_branch)
        self.assertNotEqual(state.observed_head_oid, handle.expected_head_oid)
        self.assertNotEqual(state.checks[0].head_oid, state.observed_head_oid)
        validate('pr-state', state)
        with self.assertRaises(ValueError):
            dc.replace(observation, handle=dc.replace(handle, number=10))
        with self.assertRaises(ValueError):
            dc.replace(state, status=dv.PullRequestStatus.MERGED)
        merged = dc.replace(state, status=dv.PullRequestStatus.MERGED, merge_oid='3' * 40)
        validate('pr-state', merged)
        self.assertEqual({f.name for f in dc.fields(wp.PullRequestStateRecord)}, set(schema('pr-state')['properties']))

    def test_v1_model_shape_and_common_types_are_not_duplicated(self):
        for name in ('PlanId', 'EntityId', 'Revision', 'Sha256Digest', 'ScopeClaim', 'EvidenceRef', 'DomainError', 'ResultStatus', 'AgentRunStatus', 'AgentOutputStatus', 'ReviewVerdict', 'ValidationStatus'):
            self.assertIs(getattr(wp, name), getattr(dv, name))
        model_schema = schema('agent-output')['properties']['actual_model']
        self.assertEqual({f.name for f in dc.fields(wp.ModelIdentity)}, set(model_schema['properties']))
        model = wire(wp.ModelIdentity('review_high', 'deterministic-review-test', 'fake', 4, 'simulated-review'))
        model['reasoning_effort'] = 'xhigh'
        self.assertFalse(Draft202012Validator(model_schema).is_valid(model))
        for cls, name in ((wp.AgentRunRecord, 'agent-run'), (wp.AgentOutputRecord, 'agent-output'), (wp.ReviewResultRecord, 'review-result')):
            self.assertEqual({f.name for f in dc.fields(cls)}, set(schema(name)['properties']))


if __name__ == '__main__':
    print('Independent R2 frozen-candidate integration/contract checks', flush=True)
    print('Working directory:', Path.cwd(), flush=True)
    print('Interpreter:', sys.executable, flush=True)
    print('workflow_ports import:', wp.__file__, flush=True)
    print('domain_values import:', dv.__file__, flush=True)
    print('Candidate:', CANDIDATE['fingerprint'], flush=True)
    print('R1 SHA256:', SHA((ROOT / R1_REF).read_bytes()), flush=True)
    unittest.main(verbosity=2)
