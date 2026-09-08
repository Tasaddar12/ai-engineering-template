"""Read-only exact-candidate review probes; no production/runtime dependency."""
from __future__ import annotations
import copy
import hashlib
import importlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime

ROOT = Path('D:/Codex Projects/ai-engineering-template')
CANDIDATE = ROOT / '.worktrees/TASK-015-a1'
PREFIX = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-015-a1-c1-R1'
BASE = '060362675e254194a6d76f877cddaa64205b1399'
HEAD = 'd57d1ad29462c44d0156f1b7c74c3256a339b1c7'
OWNER = '9dba72717218d0e7c2bca394da40f5fce2f991b7'
sys.dont_write_bytecode = True
sys.path.insert(0, str(CANDIDATE / 'src'))
sys.path.insert(0, str(CANDIDATE / 'tests/unit/planning_isolation'))
import test_isolation as fixture
from agents import DeterministicFakeAgentAdapter, FakeAgentProviderState, AgentAdapterCapabilities
from contracts import structural_task_digest, load_contract_registry
from domain_values import EvidenceRef

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args, cwd=CANDIDATE):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, check=True, shell=False).stdout

def identity():
    manifest_path = ROOT / '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-015-a1-d57d1ad29462.json'
    manifest = json.loads(manifest_path.read_bytes())
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert not git('status', '--porcelain')
    assert manifest['base_oid'] == BASE and manifest['head_oid'] == HEAD
    raw_diff = git('diff', '--binary', BASE, HEAD)
    assert sha(raw_diff) == manifest['diff_sha256']
    unsigned = {k: v for k, v in manifest.items() if k != 'fingerprint'}
    assert sha(json.dumps(unsigned, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == manifest['fingerprint']
    refs = []
    for ref in manifest['context_refs']:
        committed = git('show', HEAD + ':' + ref['path'])
        assert sha(committed) == ref['sha256'], ref['path']
        assert (CANDIDATE / ref['path']).read_bytes() == committed, ref['path']
        assert git('show', BASE + ':' + ref['path'], cwd=ROOT) == committed, ref['path']
        refs.append(ref)
    for ref in manifest['validation_refs']:
        assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256']
    policy_bytes = (ROOT / '.ai/project/policy.json').read_bytes()
    model_bytes = (ROOT / '.ai/project/agent-models.json').read_bytes()
    assert sha(policy_bytes + model_bytes) == manifest['policy_model_digest']
    dependencies = {
        '003': ('c749ec19056dd6d215c51a9896f35785391d0ace', 'd51b72ce71ea3ac3ad31adf41e3eddc84738ac0b'),
        '013': ('a089594df19d33250a6218126a6a3fea83ce49f8', '51a94cd050ad6c7cb525c6d26c9c7e38e0943c13'),
        '014': ('d6d3e6f94dd355994fb82d8e6a0c1c2546b6c3a3', '4bfad8611177959fb99eda01dd3c18077ff55f37'),
        '017': ('2c0748444f4982118a04b086bfa6d42d418fd1bd', 'eaa80842f695c766dd55ab92e40dcf40874c8471'),
        '039': ('bc8a5f47d8e1a66bc2b8929b099349cb199c0100', '314ef09d59f494223bec02556c6e3d9a8108636f'),
    }
    for dep, oids in dependencies.items():
        task = json.loads(git('show', HEAD + f':.ai/plans/current/PLAN-001/tasks/current/TASK-{dep}.json'))
        assert task['status'] == 'accepted'
        for oid in oids:
            git('merge-base', '--is-ancestor', oid, BASE)
            git('merge-base', '--is-ancestor', oid, HEAD)
    paths = git('diff', '--name-status', '-M', BASE, HEAD).decode().splitlines()
    owned = ['src/isolation.py', 'tests/unit/planning_isolation/test_isolation.py', '.ai/plans/current/PLAN-001/evidence/implementation/TASK-015.md']
    assert {p.split('\t')[-1] for p in paths} == set(owned)
    blobs = {}
    for p in owned:
        value = git('show', HEAD + ':' + p)
        assert value == git('show', OWNER + ':' + p)
        blobs[p] = sha(value)
    graph = json.loads(git('show', HEAD + ':.ai/plans/current/PLAN-001/graph.json'))
    plan = json.loads(git('show', HEAD + ':.ai/plans/current/PLAN-001/plan.json'))
    tasks = [json.loads(git('show', HEAD + f':.ai/plans/current/PLAN-001/tasks/current/{task}.json')) for task in plan['task_ids']]
    assert len(tasks) == 39 and graph['revision'] == 4
    assert structural_task_digest(tasks) == graph['task_set_sha256']
    prior = json.loads(git('show', HEAD + ':' + graph['review_ref']))
    assert prior['verdict'] == 'pass' and prior['task_set_sha256'] == graph['task_set_sha256'] and prior['graph_revision'] == 4
    return dict(root_head=BASE, candidate_head=HEAD, manifest_sha256=sha(manifest_path.read_bytes()), fingerprint=manifest['fingerprint'], diff_sha256=sha(raw_diff), changed_paths=paths, owned_sha256=blobs, owner_byte_identity=True, context_refs=refs, validation_refs=manifest['validation_refs'], policy_model_digest=manifest['policy_model_digest'], dependency_ancestry=dependencies, task_count=len(tasks), task_set_sha256=graph['task_set_sha256'])

class ScriptedAcceptedAdapter(DeterministicFakeAgentAdapter):
    """Use actual TASK-017 start/poll fencing; configure its public fake script API."""
    def __init__(self, f, mutate_review=None, mutate_binding=None, mutate_observation=None, allow_write=True):
        self.f = f
        self.provider = FakeAgentProviderState()
        self.last_request = None
        self.scripted = set()
        self.mutate_review = mutate_review
        self.mutate_binding = mutate_binding
        self.mutate_observation = mutate_observation
        settings = fixture.agent_settings()
        super().__init__(project_id='project-900', settings=settings,
            capabilities=AgentAdapterCapabilities(roles=(fixture.ISOLATION_REVIEW_ROLE,), permissions=('local_read', 'review_write') if allow_write else ('local_read',), command_ids=(), model_profiles=settings.models.provider().profiles), provider_state=self.provider)

    def start(self, request, idempotency_key):
        handle = super().start(request, idempotency_key)
        self.last_request = request
        if handle.external_handle not in self.scripted:
            maker = fixture.ScriptedAgent(self.f.store, model=self.expected_model(handle), mutate_review=self.mutate_review, mutate_binding=self.mutate_binding)
            maker.started, maker.handle = request, handle
            observation = maker.poll(handle)
            if self.mutate_observation:
                observation = self.mutate_observation(observation)
            self.provider.script(handle, polls=(observation,))
            self.scripted.add(handle.external_handle)
        return handle

SPEC_DOC = '.ai/plans/current/PLAN-900/spec.md'
def complete_fixture():
    f = fixture.IsolationFixture()
    spec = json.loads((CANDIDATE / '.ai/plans/current/PLAN-001/spec.json').read_bytes())
    spec['document_ref'] = SPEC_DOC
    spec['adr_refs'] = []
    f.store[fixture.SPEC_PATH] = fixture.encoded(spec)
    f.store[SPEC_DOC] = b'# Actual bounded fixture specification\n'
    f.store[fixture.ROLE_PATH] = (CANDIDATE / fixture.ROLE_PATH).read_bytes()
    f.store[fixture.CHECKLIST_PATH] = (CANDIDATE / fixture.CHECKLIST_PATH).read_bytes()
    return f

def make_request(f, include_doc=True):
    request = f.request()
    if include_doc:
        request = replace(request, context_refs=request.context_refs + (fixture.content_ref(SPEC_DOC, f.store[SPEC_DOC]),))
    return request

def run_case(name, change=None, mutate_review=None, mutate_binding=None, mutate_observation=None, include_doc=True, allow_write=True, repeat=False):
    f = complete_fixture()
    if change:
        change(f)
    adapter = ScriptedAcceptedAdapter(f, mutate_review, mutate_binding, mutate_observation, allow_write)
    f.agent = adapter
    service = f.service()
    request = make_request(f, include_doc)
    decision = service.review(request)
    if repeat:
        second = service.review(request)
        assert second == decision and adapter.provider.effect_count == 1
    return dict(name=name, status=decision.status.value, verdict=None if decision.record is None else decision.record.verdict.value, proposal=decision.proposed_graph is not None, error=None if decision.error is None else decision.error.message, effects=adapter.provider.effect_count, adapter=type(adapter).__mro__[1].__name__, simulation_evidence=any(e.metadata.get('simulated') is True for e in decision.evidence_refs), source_spec_sha256=sha(f.store[fixture.SPEC_PATH]), doc_in_context=any(e.path == SPEC_DOC for e in request.context_refs), review_read_paths=[] if adapter.last_request is None else [p.as_wire() for p in adapter.last_request.scope.read_paths])

def probes():
    def all_na(r):
        for check in r['checks']:
            check.update(status='not_applicable', rationale='No check is applicable', evidence=[])
    def fail(r):
        r['verdict'] = 'fail'
        r['checks'][0]['status'] = 'fail'
    def model_forge(o):
        model = replace(o.run.actual_model, model_id='unconfigured-review-model')
        return replace(o, run=replace(o.run, actual_model=model), output=replace(o.output, actual_model=model))
    def scope_conflict(f):
        tasks = copy.deepcopy(f.tasks)
        tasks[1]['depends_on'] = []
        tasks[1]['input_contracts'] = []
        tasks[1]['scope']['write_paths'] = tasks[0]['scope']['write_paths']
        f.replace_records(tasks)
    def valid_rewrite(f):
        f.tasks[0]['objective'] = 'Rewritten bounded task with current structural digest'
        f.graph = fixture.graph_record(f.tasks)
        f.graph.update(id='PLAN-900-r2', revision=2)
        f.store[fixture.GRAPH_PATH] = fixture.encoded(f.graph)
        f.store[fixture.TASK_1_PATH] = fixture.encoded(f.tasks[0])
    cases = [
        run_case('complete_context_positive_and_exact_retry', repeat=True),
        run_case('malformed_required_spec', change=lambda f: f.store.update({fixture.SPEC_PATH: b'{BROKEN JSON'})),
        run_case('wrong_kind_required_spec', change=lambda f: f.store.update({fixture.SPEC_PATH: b'{"kind":"fixture-spec"}'})),
        run_case('missing_spec_document', include_doc=False),
        run_case('all_twelve_checks_not_applicable', mutate_review=all_na),
        run_case('stale_checklist_evidence', mutate_binding=lambda b: b.update(checklist_version='old')),
        run_case('forged_observed_model', mutate_observation=model_forge),
        run_case('actual_permission_denial', allow_write=False),
        run_case('valid_review_fail_no_proposal', mutate_review=fail),
        run_case('unsequenced_write_conflict', change=scope_conflict),
        run_case('rewritten_current_graph_positive', change=valid_rewrite, mutate_review=lambda r: r.update(graph_revision=2, id='ISO-PLAN-900-r2-runtime')),
    ]
    return cases

def closing():
    from jsonschema import Draft202012Validator, FormatChecker
    record = json.loads(Path(str(PREFIX) + '.json').read_bytes())
    schema = json.loads((CANDIDATE / 'schemas/v1/review-result.schema.json').read_bytes())
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(record)
    checked = []
    for check in record['checks']:
        for link in check['evidence']:
            assert (ROOT / link).is_file() or (CANDIDATE / link).is_file(), link
            checked.append(link)
    assert len(record['checks']) == 11 and {c['id'] for c in record['checks']} == {f'R1-{i:02d}' for i in range(1,12)}
    closing_identity = identity()
    opening = json.loads(Path(str(PREFIX) + '-diagnostic.json.txt').read_bytes())
    assert json.loads(json.dumps(closing_identity)) == opening['identity'], 'frozen inputs changed since opening verification'
    markdown = Path(str(PREFIX) + '.md').read_text(encoding='utf-8')
    markdown_links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', markdown)
    closing_path = Path(str(PREFIX) + '-closing.json.txt')
    for target in markdown_links:
        resolved = (PREFIX.parent / target).resolve()
        assert resolved.is_file() or resolved == closing_path.resolve(), target
    result = dict(created_at=datetime.now(UTC).isoformat(), schema_valid=True, evidence_links=sorted(set(checked)), markdown_links=markdown_links, unchanged_since_opening=True, identity=closing_identity, report_sha256=sha(Path(str(PREFIX) + '.json').read_bytes()), markdown_sha256=sha(Path(str(PREFIX) + '.md').read_bytes()), diagnostic_program_sha256=sha(Path(__file__).read_bytes()))
    closing_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    assert all((PREFIX.parent / target).resolve().is_file() for target in markdown_links)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    if '--closing' in sys.argv:
        closing()
    else:
        result = dict(created_at=datetime.now(UTC).isoformat(), identity=identity(), python=sys.version, origins={name: importlib.import_module(name).__file__ for name in ('isolation','agents','orchestration_ports','workflow_ports','plan_graph','scope','contracts')}, probes=probes())
        assert all(Path(p).is_relative_to(CANDIDATE / 'src') for p in result['origins'].values())
        Path(str(PREFIX) + '-diagnostic.json.txt').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result, indent=2))
