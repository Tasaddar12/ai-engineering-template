"""One bounded independent review diagnostic; never a product dependency."""
from __future__ import annotations
import dataclasses
import hashlib
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
CANDIDATE = ROOT / '.worktrees/TASK-009-a1'
BUNDLE = ROOT / '.ai/plans/current/PLAN-001'
HEAD = '44d9481dc6e65a8ae33e2e472c131852813ba913'
BASE = '1e6477285d37c59a35dee4c9951a3c1bfe4be3f1'
OWNER = 'cee6a8261431876c50fd4a64f0c7884992bf4c8d'
PREFIX = BUNDLE / 'reviews/TASK-009-a1-c1-R1'
sys.path.insert(0, str(CANDIDATE / 'src'))
from contracts import ContractRegistry, structural_task_digest
from commands import LocalCommandRunner, FileCommandLogStore
from config import RunSettings, load_installation_record, load_project_settings
from domain_values import EntityId, PlanId, RecordRef, FrozenJsonObject, ScopePath, Sha256Digest
from git_ops import LocalGitRepository, FileContentReader, GitRuntimeBinding
from local_ports import ProjectionUpdate, ManifestEffect, ManifestEffectKind, PermissionClass, GitInspectRequest, GitRefQuery, TransactionStatus, ContentRef
from state import LocalStateStore

spec = importlib.util.spec_from_file_location('review_state_fixture', CANDIDATE / 'tests/unit/state_checkpoints/test_state.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)
F = fixture_module
REGISTRY = ContractRegistry(CANDIDATE / 'schemas/v1')
RESULTS = {}

def rawgit(*args, cwd=CANDIDATE):
    return subprocess.run(('git', *args), cwd=cwd, capture_output=True, check=True, shell=False).stdout

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()

def identity():
    manifest = json.loads((BUNDLE / 'reviews/candidates/CANDIDATE-TASK-009-a1-44d9481dc6e6.json').read_bytes())
    assert rawgit('rev-parse', 'HEAD').decode().strip() == HEAD
    assert rawgit('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert not rawgit('status', '--porcelain=v1')
    assert hashlib.sha256(rawgit('diff', '--binary', BASE, HEAD)).hexdigest() == manifest['diff_sha256']
    assert digest({k: v for k, v in manifest.items() if k != 'fingerprint'}) == manifest['fingerprint']
    refs = {}
    for group, root in [('context_refs', CANDIDATE), ('validation_refs', ROOT)]:
        for ref in manifest[group]:
            observed = hashlib.sha256((root / ref['path']).read_bytes()).hexdigest()
            assert observed == ref['sha256'], ref['path']
            refs[ref['path']] = observed
    policy = hashlib.sha256((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()).hexdigest()
    assert policy == manifest['policy_model_digest']
    graph = json.loads((CANDIDATE / '.ai/plans/current/PLAN-001/graph.json').read_bytes())
    tasks = [json.loads(p.read_bytes()) for p in (CANDIDATE / '.ai/plans/current/PLAN-001/tasks/current').glob('TASK-*.json')]
    assert len(tasks) == 39
    assert structural_task_digest(tasks) == graph['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
    structural_graph_digest = digest({key: graph[key] for key in ('schema_version', 'kind', 'id', 'plan_id', 'revision', 'nodes', 'task_set_sha256')})
    assert structural_graph_digest == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
    for path in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
        assert (ROOT / path).read_bytes() == (CANDIDATE / path).read_bytes()
    approval = json.loads((CANDIDATE / graph['review_ref']).read_bytes())
    assert graph['revision'] == 4 and graph['status'] == 'approved' and approval['verdict'] == 'pass'
    assert approval['task_set_sha256'] == graph['task_set_sha256'] and approval['graph_revision'] == 4
    assert len(approval['checks']) == 12 and all(x['status'] == 'pass' for x in approval['checks'])
    dependencies = [x for x in tasks if x['id'] in {'TASK-002', 'TASK-004', 'TASK-007', 'TASK-008'}]
    assert len(dependencies) == 4 and all(x['status'] == 'accepted' for x in dependencies)
    paths = rawgit('diff', '--name-only', BASE, HEAD).decode().splitlines()
    assert set(paths) == {'.ai/plans/current/PLAN-001/evidence/implementation/TASK-009.md', 'src/state.py', 'tests/unit/state_checkpoints/test_state.py'}
    blobs = {}
    for path in paths + ['src/local_ports.py', 'src/contracts.py', 'src/domain_values.py', 'src/transitions.py', 'src/git_ops.py', 'src/commands.py', 'src/config.py']:
        ours = rawgit('rev-parse', HEAD + ':' + path).decode().strip()
        owner = rawgit('rev-parse', OWNER + ':' + path).decode().strip()
        assert ours == owner, path
        blobs[path] = ours
    rawgit('merge-base', '--is-ancestor', BASE, HEAD)
    rawgit('merge-base', '--is-ancestor', OWNER, HEAD)
    rawgit('diff', '--check', BASE, HEAD)
    accepted = {}
    for report_name, path in [('TASK-002-a1-c2-R2.json', 'src/local_ports.py'), ('TASK-004-a2-c3-R2.json', 'src/contracts.py'), ('TASK-007-a1-c2-R1.json', 'src/git_ops.py'), ('TASK-008-a1-c1-R2.json', 'src/transitions.py')]:
        report = json.loads((CANDIDATE / '.ai/plans/current/PLAN-001/reviews' / report_name).read_bytes())
        assert report['verdict'] == 'pass'
        REGISTRY.validate(report)
        previous_candidate = json.loads((CANDIDATE / report['candidate_ref']).read_bytes())
        assert previous_candidate['fingerprint'] == report['candidate_fingerprint']
        accepted_head = previous_candidate['head_oid']
        rawgit('merge-base', '--is-ancestor', accepted_head, HEAD)
        assert rawgit('rev-parse', accepted_head+':'+path) == rawgit('rev-parse', HEAD+':'+path)
        accepted[report_name] = {'accepted_head': accepted_head, 'current_dependency_blob_matches': True}
    return {'base': BASE, 'head': HEAD, 'raw_diff_sha256': manifest['diff_sha256'], 'fingerprint': manifest['fingerprint'], 'context_validation_hashes': refs, 'policy_model_digest': policy, 'graph_canonical_sha256': digest(graph), 'graph_structural_sha256': structural_graph_digest, 'task_digest': graph['task_set_sha256'], 'owned_and_dependency_blobs_equal_owner_tested_head': blobs, 'prerequisite_acceptance': accepted, 'candidate_clean': True}

def project_event(op, generation):
    return F.event(op, generation, 'fixture-project', 'project.observed', 'foundation', 'foundation')

def commit_seed(fixture, files):
    for path, value in files.items():
        target = fixture.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value if isinstance(value, bytes) else F.encoded(value))
    fixture.git('add', '--', *files)
    fixture.git('commit', '-m', 'review seed')

def summarize(result):
    return {'status': result.status.value, 'generation': result.generation.value, 'checkpoint_oid': result.checkpoint_oid, 'error': None if result.error is None else result.error.category.value}

class Clock:
    def __init__(self):
        self.value = datetime(2026, 9, 8, tzinfo=timezone.utc)
    def now(self):
        self.value += timedelta(microseconds=1)
        return self.value

class Ids:
    def __init__(self): self.value = 0
    def new(self, kind, plan_id=None):
        self.value += 1
        return EntityId(f'review-command-{self.value}')

def real_ports_and_payload():
    f = F.RepositoryFixture()
    try:
        settings = dataclasses.replace(load_project_settings(CANDIDATE, load_installation_record(CANDIDATE)), project_root=f.root)
        saved = RunSettings(max_parallel=2, max_review_cycles=1, max_rewrites=1, max_agent_invocations=20)
        payload = F.encoded({'saved': saved.to_payload(), 'policy': settings.policy.with_run_settings(saved).to_wire()})
        path = '.codex/evidence/review-saved-settings.json'
        (f.root / path).parent.mkdir(parents=True)
        (f.root / path).write_bytes(payload)
        (f.root / 'developer.txt').write_bytes(b'staged\x00bytes\r\n')
        f.git('add', '--', 'developer.txt')
        (f.root / 'developer.txt').write_bytes(b'unstaged\x00bytes\n')
        (f.root / 'untracked.bin').write_bytes(b'\x00\xffkeep')
        before = (rawgit('rev-parse', 'HEAD', cwd=f.root), (f.root / '.git/index').read_bytes(), (f.root / 'developer.txt').read_bytes(), (f.root / 'untracked.bin').read_bytes())
        clock = Clock()
        environment = {name: os.environ[name] for name in ('PATH', 'SystemRoot', 'TEMP', 'TMP') if name in os.environ}
        runner = LocalCommandRunner(project_settings=settings, run_settings=saved, allowed_permissions=(PermissionClass.LOCAL_EXECUTE, PermissionClass.LOCAL_READ), id_factory=Ids(), clock=clock, log_store=FileCommandLogStore(f.root, '.git/review-logs'), base_environment=environment)
        reader = FileContentReader(f.root)
        op = 'review-real-ports'
        request = F.transaction(op, 0, F.project_state(1), dataclasses.replace(project_event(op, 1), payload_ref=ContentRef(path, Sha256Digest(hashlib.sha256(payload).hexdigest()))))
        with LocalStateStore(project=f.project, command_runner=runner, content_reader=reader, runtime=f.runtime, namespace='.codex') as store:
            first = store.transact(request)
            duplicate = store.transact(request)
            assert first.status == TransactionStatus.COMMITTED and duplicate == first
            assert store.read(F.state_ref()).record['generation'] == 1
        repository = LocalGitRepository(project=f.project, command_runner=runner, clock=clock, content_reader=reader, runtime=GitRuntimeBinding(sys.executable, shutil.which('git'), CANDIDATE / 'src'))
        observed = repository.inspect(GitInspectRequest(project_id=f.project.project_id, run_id=EntityId('review-inspect'), target=f.project, refs=(GitRefQuery('refs/heads/ai/state'),)))
        assert observed.error is None and observed.refs[0].oid == first.checkpoint_oid
        recovered = json.loads(rawgit('show', f'{first.checkpoint_oid}:{path}', cwd=f.root))
        REGISTRY.validate(recovered['policy'])
        assert settings.resolve_run(saved=RunSettings(**recovered['saved'])) == saved
        after = (rawgit('rev-parse', 'HEAD', cwd=f.root), (f.root / '.git/index').read_bytes(), (f.root / 'developer.txt').read_bytes(), (f.root / 'untracked.bin').read_bytes())
        assert before == after
        return {'first': summarize(first), 'dedup_equal': True, 'accepted_006_007_composition': True, 'actual_038_payload_roundtrip': True, 'head_index_tracked_untracked_bytes_preserved': True}
    finally: f.close()

def unguarded_status_change():
    f = F.RepositoryFixture()
    try:
        path = '.codex/plans/current/PLAN-001/tasks/current/TASK-001.json'
        commit_seed(f, {path: F.task_record('PLAN-001', 'backlog')})
        op = 'review-unguarded'
        request = F.transaction(op, 0, F.project_state(1), project_event(op, 1), ProjectionUpdate(RecordRef('task', EntityId('TASK-001'), PlanId('PLAN-001')), FrozenJsonObject(F.task_record('PLAN-001', 'accepted'))))
        with f.store() as store:
            result = store.transact(request)
            observed = store.read(RecordRef('task', EntityId('TASK-001'), PlanId('PLAN-001')))
        return {'result': summarize(result), 'task_status': observed.record['status'], 'event_entity': request.events[0].entity_id.value, 'event_evidence': list(request.events[0].evidence_refs)}
    finally: f.close()

def unrelated_review_gate():
    f = F.RepositoryFixture()
    try:
        review = json.loads((CANDIDATE / 'schemas/examples/review-result.json').read_bytes())
        review.update(id='REVIEW-OTHER', task_id='TASK-999', plan_id='PLAN-002', verdict='pass', stage='implementation')
        review['checks'][0]['status'] = 'pass'
        REGISTRY.validate(review)
        path = '.codex/plans/current/PLAN-001/tasks/current/TASK-001.json'
        gate_path = '.codex/plans/current/PLAN-002/reviews/REVIEW-OTHER.json'
        commit_seed(f, {path: F.task_record('PLAN-001', 'review_2'), gate_path: review})
        op = 'review-wrong-gate'
        request = F.transaction(op, 0, F.project_state(1), F.event(op, 1, 'TASK-001', 'task.transitioned', 'review_2', 'accepted', evidence_refs=(gate_path,)), ProjectionUpdate(RecordRef('task', EntityId('TASK-001'), PlanId('PLAN-001')), FrozenJsonObject(F.task_record('PLAN-001', 'accepted'))))
        with f.store() as store: result = store.transact(request)
        return {'result': summarize(result), 'gate_plan': review['plan_id'], 'gate_task': review['task_id'], 'gate_stage': review['stage'], 'gate_fingerprint': review['candidate_fingerprint']}
    finally: f.close()

def mixed_command_evidence():
    f = F.RepositoryFixture()
    try:
        root = '.codex/plans/current/PLAN-001'
        good = F.command_evidence_record('UNRELATED-PASS', root+'/evidence/empty.out', b'', root+'/evidence/empty.err', b'')
        good['command_id'] = 'other-command'
        good['argv_redacted'] = ['other-command']
        failed = F.command_evidence_record('REQUIRED-FAIL', root+'/evidence/failed.out', b'Ran 2 tests\nFAILED\n', root+'/evidence/empty.err', b'')
        failed['exit_code'] = 1
        files = {root+'/tasks/current/TASK-001.json': F.task_record('PLAN-001', 'validating'), root+'/commands/test.TASK-001.json': F.command_definition(), root+'/evidence/commands/UNRELATED-PASS.json': good, root+'/evidence/commands/REQUIRED-FAIL.json': failed, root+'/evidence/empty.out': b'', root+'/evidence/empty.err': b'', root+'/evidence/failed.out': b'Ran 2 tests\nFAILED\n'}
        commit_seed(f, files)
        op = 'review-mixed-command'
        request = F.transaction(op, 0, F.project_state(1), F.event(op, 1, 'TASK-001', 'task.transitioned', 'validating', 'review_1', evidence_refs=(root+'/evidence/commands/UNRELATED-PASS.json', root+'/evidence/commands/REQUIRED-FAIL.json')), ProjectionUpdate(RecordRef('task', EntityId('TASK-001'), PlanId('PLAN-001')), FrozenJsonObject(F.task_record('PLAN-001', 'review_1'))))
        with f.store() as store: result = store.transact(request)
        return {'result': summarize(result), 'required_command_exit': failed['exit_code'], 'unrelated_command_exit': good['exit_code']}
    finally: f.close()

def incomplete_relocation():
    f = F.RepositoryFixture()
    try:
        root = '.codex/plans/current/PLAN-001'
        plan = F.plan_record('running')
        state = F.project_state(0, active_plans=['PLAN-001'])
        task = F.task_record('PLAN-001', 'accepted')
        specification = json.loads((CANDIDATE / 'schemas/examples/spec.json').read_bytes())
        specification['document_ref'] = root+'/spec.md'
        REGISTRY.validate(specification)
        commit_seed(f, {'.codex/STATE.json': state, root+'/plan.json': plan, root+'/plan.md': b'Fixture plan\n', root+'/spec.json': specification, root+'/spec.md': b'Fixture specification\n', root+'/tasks/current/TASK-001.json': task})
        source_spec_existed = bool(rawgit('ls-tree', '--name-only', 'HEAD', '--', task['spec_refs'][0], cwd=f.root))
        target = '.codex/plans/archived/PLAN-001'
        archived = dict(plan, archived=True)
        op = 'review-incomplete-relocation'
        request = F.transaction(op, 0, F.project_state(1, active_plans=['PLAN-001']), F.event(op, 1, 'PLAN-001', 'plan.archived', 'running', 'running'), ProjectionUpdate(RecordRef('plan', EntityId('PLAN-001')), FrozenJsonObject(archived), old_location=ScopePath.directory(root+'/'), new_location=ScopePath.directory(target+'/')))
        with f.store() as store: result = store.transact(request)
        if result.status != TransactionStatus.COMMITTED: return {'result': summarize(result)}
        moved_task = json.loads(rawgit('show', f'{result.checkpoint_oid}:{target}/tasks/current/TASK-001.json', cwd=f.root))
        committed_state = json.loads(rawgit('show', f'{result.checkpoint_oid}:.codex/STATE.json', cwd=f.root))
        return {'result': summarize(result), 'active_plans': committed_state['active_plans'], 'archived_plans': committed_state['archived_plans'], 'moved_task_spec_ref': moved_task['spec_refs'][0], 'source_spec_existed_before': source_spec_existed, 'source_directory_exists': bool(rawgit('ls-tree', '-r', '--name-only', result.checkpoint_oid, '--', root, cwd=f.root)), 'archived_plan': True}
    finally: f.close()

def unrelated_relocation_source():
    f = F.RepositoryFixture()
    try:
        task_path = '.codex/plans/current/PLAN-001/tasks/current/TASK-001.json'
        unrelated = '.codex/evidence/keep.txt'
        commit_seed(f, {task_path: F.task_record('PLAN-001', 'accepted'), unrelated: b'keep unrelated committed evidence\n'})
        op = 'review-wrong-source'
        target = '.codex/plans/current/PLAN-001/tasks/completed/TASK-001.json'
        request = F.transaction(op, 0, F.project_state(1), F.event(op, 1, 'TASK-001', 'task.transitioned', 'accepted', 'completed'), ProjectionUpdate(RecordRef('task', EntityId('TASK-001'), PlanId('PLAN-001')), FrozenJsonObject(F.task_record('PLAN-001', 'completed')), old_location=ScopePath.exact_file(unrelated), new_location=ScopePath.exact_file(target)))
        with f.store() as store: result = store.transact(request)
        return {'result': summarize(result), 'unrelated_source_exists': bool(rawgit('ls-tree', '--name-only', 'refs/heads/ai/state', '--', unrelated, cwd=f.root)), 'old_task_exists': bool(rawgit('ls-tree', '--name-only', 'refs/heads/ai/state', '--', task_path, cwd=f.root)), 'new_task_exists': bool(rawgit('ls-tree', '--name-only', 'refs/heads/ai/state', '--', target, cwd=f.root))}
    finally: f.close()

def snapshot_relative_manifest():
    f = F.RepositoryFixture()
    try:
        content = b'immutable snapshot bytes\n'
        sha = hashlib.sha256(content).hexdigest()
        root = '.codex/plans/current/PLAN-001/history/manifests'
        artifact = root+'/TASK-001.json'
        target = f.root / artifact
        target.parent.mkdir(parents=True)
        target.write_bytes(content)
        manifest = {'schema_version': '1.0', 'kind': 'archive-manifest', 'id': 'MANIFEST-001', 'plan_id': 'PLAN-001', 'reason': 'review snapshot', 'merge_evidence_ref': None, 'artifacts': [{'path': 'TASK-001.json', 'sha256': sha}], 'retained_commit_oids': [], 'created_at': F.NOW.isoformat()}
        REGISTRY.validate(manifest)
        outcomes = {}
        for label, effect_path in [('root_relative_effect', artifact), ('snapshot_relative_effect', 'TASK-001.json')]:
            op = 'review-manifest-'+label
            ref = RecordRef('archive-manifest', EntityId('MANIFEST-001'), PlanId('PLAN-001'))
            request = F.transaction(op, 0, F.project_state(1), project_event(op, 1), ProjectionUpdate(ref, FrozenJsonObject(manifest), manifest_effects=(ManifestEffect(ref, ManifestEffectKind.ADD, ScopePath.exact_file(effect_path), Sha256Digest(sha)),)))
            with f.store() as store: outcomes[label] = summarize(store.transact(request))
        return {'schema_valid_manifest': True, 'manifest_artifact_path': 'TASK-001.json', 'actual_snapshot_artifact': artifact, **outcomes}
    finally: f.close()

def verify_reports():
    report = json.loads(PREFIX.with_suffix('.json').read_bytes())
    REGISTRY.validate(report)
    assert len(report['checks']) == 11
    assert report['candidate_fingerprint'] == identity()['fingerprint']
    for check in report['checks']:
        for ref in check['evidence']:
            assert (ROOT / ref).exists(), ref
    markdown_path = PREFIX.with_suffix('.md')
    for target in re.findall(r'\]\(([^)]+)\)', markdown_path.read_text(encoding='utf-8')):
        assert (markdown_path.parent / target.split('#', 1)[0]).exists(), target
    return {'report_schema': 'pass', 'evidence_links': 'pass', 'frozen_identity': 'pass', 'candidate_clean': True, 'identity': identity()}

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--verify-reports':
        print(json.dumps(verify_reports(), indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == '--real-ports-only':
        result = {'real_ports_and_payload': real_ports_and_payload(), 'final_identity': identity()}
        Path(str(PREFIX) + '-real-ports.json.txt').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == '--relocation-only':
        result = {'incomplete_relocation': incomplete_relocation(), 'final_identity': identity()}
        Path(str(PREFIX) + '-relocation.json.txt').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(result, indent=2))
    else:
        RESULTS['runtime'] = {'python': sys.version, 'platform': platform.platform(), 'source': str(sys.modules['state'].__file__), 'candidate': str(CANDIDATE)}
        for name, function in [('identity', identity), ('real_ports_and_payload', real_ports_and_payload), ('unguarded_status_change', unguarded_status_change), ('unrelated_review_gate', unrelated_review_gate), ('mixed_command_evidence', mixed_command_evidence), ('incomplete_relocation', incomplete_relocation), ('unrelated_relocation_source', unrelated_relocation_source), ('snapshot_relative_manifest', snapshot_relative_manifest)]:
            try: RESULTS[name] = function()
            except Exception:
                RESULTS[name] = {'diagnostic_error': traceback.format_exc()}
            print(name + ': ' + json.dumps(RESULTS[name], sort_keys=True), flush=True)
        RESULTS['final_identity'] = identity()
        output = Path(str(PREFIX) + '-windows.json.txt')
        output.write_text(json.dumps(RESULTS, indent=2) + '\n', encoding='utf-8')
        if any(isinstance(value, dict) and 'diagnostic_error' in value for value in RESULTS.values()):
            raise SystemExit(1)
