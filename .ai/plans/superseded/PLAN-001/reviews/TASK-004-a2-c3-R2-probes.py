"""Independent R2 evidence; only temporary fixtures and named review outputs mutate."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-004-a2'
REVIEWS = ROOT / '.ai/plans/current/PLAN-001/reviews'
STEM = 'TASK-004-a2-c3-R2'
EVIDENCE = REVIEWS / (STEM + '-evidence.txt')
CAND_REF = '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-004-a2-e3c1177f993e.json'
PYTHON = ROOT / '.ai/local/full-plan-venv/Scripts/python.exe'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'src'))
import ai
import contracts
import domain_values
import install
import validate_foundation


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def git(*args):
    return subprocess.run(['git', *args], cwd=WT, check=True, capture_output=True).stdout


def log(message):
    with EVIDENCE.open('a', encoding='utf-8') as stream:
        stream.write(message + '\n')
    print(message, flush=True)


def replace_live(value, before, after):
    if isinstance(value, str):
        return value.replace(before, after)
    if isinstance(value, list):
        return [replace_live(item, before, after) for item in value]
    if isinstance(value, dict):
        return {key: replace_live(item, before, after) for key, item in value.items()}
    return value


if '--integration-only' in sys.argv:
    log('HARNESS CORRECTION: initial integration fixture omitted the archived_plans registry update; candidate correctly rejected it. Corrected fixture now updates all three registries. Prior declared 21-test pass is retained; no suite rerun.')
else:
    EVIDENCE.write_text('', encoding='utf-8')
candidate = read(ROOT / CAND_REF)
assert git('rev-parse', 'HEAD').decode().strip() == candidate['head_oid']
assert not git('status', '--porcelain')
git('merge-base', '--is-ancestor', candidate['base_oid'], candidate['head_oid'])
git('merge-base', '--is-ancestor', 'd1fc917466410febc6238479e65816dd39591a4f', candidate['base_oid'])
assert sha(git('diff', '--binary', candidate['base_oid'], candidate['head_oid'])) == candidate['diff_sha256']
for ref in candidate['context_refs']:
    assert sha(git('show', candidate['head_oid'] + ':' + ref['path'])) == ref['sha256'], ref
for ref in candidate['validation_refs']:
    assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref
assert sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()) == candidate['policy_model_digest']
assert sha(json.dumps({key: value for key, value in candidate.items() if key != 'fingerprint'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == candidate['fingerprint']
paths = git('diff', '--name-only', candidate['base_oid'], candidate['head_oid']).decode().splitlines()
assert set(paths) == {'src/contracts.py', 'src/install.py', 'src/validate_foundation.py', 'tests/unit/schemas/test_contracts.py', '.ai/plans/current/PLAN-001/evidence/implementation/TASK-004.md'}
assert git('show', 'd1fc917466410febc6238479e65816dd39591a4f:src/domain_values.py') == git('show', 'HEAD:src/domain_values.py')
assert not git('diff', candidate['base_oid'], candidate['head_oid'], '--', 'schemas', 'src/workflow_ports.py', 'src/ai.py')
registry = contracts.load_contract_registry(WT / 'schemas/v1')
registry.validate(candidate)
r1 = read(REVIEWS / 'TASK-004-a2-c3-R1.json')
registry.validate(r1)
assert r1['verdict'] == 'pass' and r1['candidate_fingerprint'] == candidate['fingerprint'] and r1['candidate_ref'] == CAND_REF
assert [item['id'] for item in r1['checks']] == [f'R1-{number:02}' for number in range(1, 12)]
assert all(item['status'] == 'pass' for item in r1['checks']) and not r1['findings']
for module in (ai, contracts, domain_values, install, validate_foundation):
    assert Path(module.__file__).resolve().parent == (WT / 'src').resolve()
log('PASS identity: exact clean head/base, accepted TASK-001 ancestry and unchanged bytes; binary diff, 12 context refs, validation ref, policy/model hash, fingerprint, five paths; schema-valid same-candidate 11-check R1 pass')
log('PASS origins: every R2 production import is from frozen TASK-004-a2/src; schemas, accepted values/workflow ports, and bootstrap CLI are unchanged')

tasks = [read(path) for path in (WT / '.ai/plans/current/PLAN-001/tasks/current').glob('TASK-*.json')]
graph = read(WT / '.ai/plans/current/PLAN-001/graph.json')
isolation = read(WT / '.ai/plans/current/PLAN-001/reviews/r4-isolation-review.json')
assert ai.STRUCTURAL_TASK_FIELDS == contracts.STRUCTURAL_TASK_FIELDS
assert contracts.structural_task_digest(tasks) == ai.structural_task_digest(tasks) == graph['task_set_sha256'] == isolation['task_set_sha256']
assert graph['revision'] == isolation['graph_revision'] == candidate['graph_revision'] == 4 and isolation['verdict'] == 'pass'
assert contracts.structural_task_digest([domain_values.FrozenJsonObject(item) for item in reversed(tasks)]) == graph['task_set_sha256']
log('PASS common digest: 39 current tasks reproduce bootstrap and approved r4 hash, including immutable task inputs and reordered task collection')

ref_kinds = {'task': 'TASK-001', 'command': 'test.TASK-001', 'review': 'R1', 'evidence': 'E1', 'handoff': 'TASK-001'}
for kind, local in ref_kinds.items():
    first = contracts.parse_record_ref(f'{kind}:PLAN-101:{local}', expected_plan_id='PLAN-101')
    second = contracts.parse_record_ref(f'{kind}:PLAN-102:{local}')
    assert first.key != second.key
    assert first == domain_values.RecordRef(kind=kind, plan_id='PLAN-101', local_id=local)
    for bad, expected in ((f'{kind}:{local}', None), (str(second), 'PLAN-101')):
        try:
            contracts.parse_record_ref(bad, expected_plan_id=expected)
        except domain_values.DomainException as error:
            assert error.category == domain_values.ErrorCategory.INVALID_INPUT and not error.error.retryable
        else:
            raise AssertionError(bad)
assert str(contracts.parse_record_ref('plan:PLAN-101')) == 'plan:PLAN-101'
log('PASS reference compatibility: five plan-local kinds preserve TASK-001 constructors, differ across plans, and reject bare or wrong-plan identities with nonretryable typed errors; project-unique plan reference remains bare')

# Reuse accepted sibling's public wire fixtures, but send them through this candidate's registry.
spec = importlib.util.spec_from_file_location('r2_workflow_fixtures', WT / 'tests/unit/domain_workflow_ports/test_workflow_ports.py')
fixtures = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(fixtures)
seen = []


class RegistryBridge:
    def __init__(self, schema, **kwargs):
        self.kind = schema['properties']['kind']['const']

    def validate(self, record):
        assert record['kind'] == self.kind
        registry.validate(domain_values.FrozenJsonObject(record))
        seen.append(self.kind)


with patch.object(fixtures, 'Draft202012Validator', RegistryBridge):
    fixtures.SchemaShapeTests('test_representative_schema_records_validate_after_test_wire_projection').test_representative_schema_records_validate_after_test_wire_projection()
assert len(seen) == 6 and len(set(seen)) == 6
log('PASS accepted TASK-003 compatibility: immutable wire projections for ' + ', '.join(seen) + ' validate through the new offline registry; no TASK-003 dependency/import added')

environment = dict(os.environ)
environment.pop('PYTHONPATH', None)
environment['PYTHONDONTWRITEBYTECODE'] = '1'
command = read(WT / '.ai/plans/current/PLAN-001/commands/test.TASK-004.json')
if '--integration-only' not in sys.argv:
    run = subprocess.run([str(PYTHON), *command['argv'][1:]], cwd=WT, env=environment, capture_output=True, text=True, timeout=180)
    (REVIEWS / (STEM + '-declared.txt')).write_text(run.stdout + run.stderr, encoding='utf-8')
    assert run.returncode == 0 and 'Ran 21 tests' in run.stderr and '\nOK' in run.stderr
    log('PASS declared task suite: exact command with required root interpreter, 21 tests, exit 0; full output in ' + STEM + '-declared.txt')

with tempfile.TemporaryDirectory(prefix='r2-contract-integration-') as temporary:
    temp = Path(temporary)
    project = temp / 'project with spaces'
    install.install(str(project), 'codex')
    for plan_id in ('PLAN-101', 'PLAN-102'):
        assert ai.main(['--project', str(project), 'plan', 'create', plan_id, '--title', 'R2 integration']) == 0
    bundle = project / '.codex/plans/current/PLAN-101'
    task_path = bundle / 'tasks/current/TASK-001.json'
    task = read(task_path)
    task['input_contracts'] = ['task:PLAN-101:TASK-001', '.codex/plans/current/PLAN-101/tasks/current/']
    task['output_contracts'] = ['.codex/plans/current/PLAN-101/spec.json']
    task['scope']['read_paths'] = ['.codex/plans/current/PLAN-101/tasks/current/']
    write(task_path, task)
    approval = read(bundle / 'graph.json')
    approval.update(status='approved', task_set_sha256=contracts.structural_task_digest([task]), review_ref='.codex/plans/current/PLAN-101/reviews/isolation-review.json')
    write(bundle / 'graph.json', approval)
    report = read(WT / 'schemas/examples/isolation-review.json')
    report.update(plan_id='PLAN-101', graph_revision=approval['revision'], task_set_sha256=approval['task_set_sha256'], verdict='pass')
    write(project / approval['review_ref'], report)
    plan = read(bundle / 'plan.json')
    plan['isolation_review_ref'] = approval['review_ref']
    write(bundle / 'plan.json', plan)

    snapshot = bundle / 'history/r2-snapshot'
    snapshot.mkdir(parents=True)
    retained = {
        'task.json': task_path.read_bytes(),
        'graph.json': (bundle / 'graph.json').read_bytes(),
        'review.json': (project / approval['review_ref']).read_bytes(),
        'legacy.json': b'{"schema_version":"0.1","note":".codex/plans/current/PLAN-101/spec.json"}\r\n',
    }
    for name, content in retained.items():
        (snapshot / name).write_bytes(content)
    manifest = read(WT / 'schemas/examples/archive-manifest.json')
    manifest.update(id='R2-snapshot', plan_id='PLAN-101', artifacts=[{'path': name, 'sha256': sha(content)} for name, content in retained.items()])
    write(snapshot / 'manifest.json', manifest)
    retained['manifest.json'] = (snapshot / 'manifest.json').read_bytes()
    result = validate_foundation.validate(project)
    assert result['plans'] == 2 and result['tasks'] == 2 and result['archive_manifests'] == 1

    # Recursive live validation checks the owning plan without conflating duplicated local task IDs.
    wrong = read(ROOT / CAND_REF)
    wrong['plan_id'] = 'PLAN-102'
    wrong_path = bundle / 'reviews/candidates/wrong-plan.json'
    write(wrong_path, wrong)
    try:
        validate_foundation.validate(project)
    except validate_foundation.ValidationFailure as error:
        assert 'artifact belongs to another plan' in str(error)
    else:
        raise AssertionError('wrong-plan artifact accepted')
    wrong_path.unlink()

    previous_bucket = 'current'
    for next_bucket in ('completed', 'archived'):
        destination = project / f'.codex/plans/{next_bucket}/PLAN-101'
        bundle.rename(destination)
        bundle = destination
        for path in bundle.rglob('*.json'):
            if 'history' not in path.relative_to(bundle).parts:
                value = replace_live(read(path), f'.codex/plans/{previous_bucket}/PLAN-101', f'.codex/plans/{next_bucket}/PLAN-101')
                write(path, value)
        plan = read(bundle / 'plan.json')
        plan.update(status='completed', archived=next_bucket == 'archived')
        write(bundle / 'plan.json', plan)
        if previous_bucket == 'current':
            old_task = bundle / 'tasks/current/TASK-001.json'
            task = replace_live(read(old_task), '/tasks/current/', '/tasks/completed/')
            task['status'] = 'completed'
            task_path = bundle / 'tasks/completed/TASK-001.json'
            write(old_task, task)
            old_task.rename(task_path)
        else:
            task_path = bundle / 'tasks/completed/TASK-001.json'
        state_path = project / '.codex/STATE.json'
        state = read(state_path)
        state['active_plans'] = ['PLAN-102']
        state['completed_plans'] = ['PLAN-101'] if next_bucket == 'completed' else []
        state['archived_plans'] = ['PLAN-101'] if next_bucket == 'archived' else []
        write(state_path, state)
        result = validate_foundation.validate(project)
        assert result['plans'] == 2 and result['tasks'] == 2 and result['archive_manifests'] == 1
        snapshot = bundle / 'history/r2-snapshot'
        assert all((snapshot / name).read_bytes() == content for name, content in retained.items())
        before = task_path.read_bytes()
        for field in ('objective', 'input_contracts', 'output_contracts'):
            changed = read(task_path)
            changed[field] = 'new structural prose' if field == 'objective' else [*changed[field], 'required approval suffix.md']
            write(task_path, changed)
            try:
                validate_foundation.validate(project)
            except validate_foundation.ValidationFailure as error:
                assert 'stale structural task digest' in str(error)
            else:
                raise AssertionError('stale approval retained')
            task_path.write_bytes(before)
        previous_bucket = next_bucket
    (snapshot / 'legacy.json').write_bytes(retained['legacy.json'] + b' ')
    try:
        validate_foundation.validate(project)
    except validate_foundation.ValidationFailure as error:
        assert 'stale hash for legacy.json' in str(error)
    else:
        raise AssertionError('changed snapshot bytes accepted')
    log('PASS physical lifecycle/history integration: two plans reuse TASK-001 safely; wrong-plan nested live artifact rejects; approved current/completed/archived PLAN-101 passes; five snapshot files remain byte-exact; six prose changes reject stale approval; one historical-byte mutation rejects its content hash')

    future_source = temp / 'future source'
    for name in ('src', 'docs', 'schemas'):
        shutil.copytree(WT / name, future_source / name, ignore=shutil.ignore_patterns('__pycache__'))
    with (future_source / 'src/ai.py').open('a', encoding='utf-8') as stream:
        stream.write('\nimport r2_future_a\n')
    (future_source / 'src/r2_future_a.py').write_text('from r2_future_b import VALUE\n', encoding='utf-8')
    (future_source / 'src/r2_future_b.py').write_text('import r2_future_a\nfrom domain_values import PlanId\nVALUE = PlanId("PLAN-101")\n', encoding='utf-8')
    (future_source / 'src/r2_unrelated.py').write_text('raise RuntimeError("unreachable")\n', encoding='utf-8')
    future_target = temp / 'future target'
    with patch.object(install, '_source_root', return_value=future_source):
        install.install(str(future_target), 'claude')
    tool_root = future_target / '.claude/tools'
    assert (tool_root / 'r2_future_a.py').is_file() and (tool_root / 'r2_future_b.py').is_file()
    assert not (tool_root / 'r2_unrelated.py').exists() and not (tool_root / 'workflow_ports.py').exists()
    unrelated_cwd = temp / 'unrelated cwd'
    unrelated_cwd.mkdir()
    probe = ('import pathlib,sys; sys.path.insert(0, ' + repr(str(tool_root)) + '); '
             'import ai,contracts,domain_values,validate_foundation,r2_future_a,r2_future_b; '
             'mods=(ai,contracts,domain_values,validate_foundation,r2_future_a,r2_future_b); '
             'assert all(pathlib.Path(m.__file__).resolve().parent == pathlib.Path(' + repr(str(tool_root)) + ').resolve() for m in mods); '
             'assert str(r2_future_a.VALUE) == "PLAN-101"; '
             'assert validate_foundation.validate(pathlib.Path(' + repr(str(future_target)) + '))["plans"] == 0')
    run = subprocess.run([str(PYTHON), '-I', '-B', '-c', probe], cwd=unrelated_cwd, env=environment, capture_output=True, text=True, timeout=60)
    assert run.returncode == 0, run.stdout + run.stderr
    log('PASS future flat-module integration: installed two new transitive modules with an import cycle into fresh Claude target, excluded unreachable source, and imported/validated only installed origins under isolated Python from an unrelated directory')

assert not git('status', '--porcelain')
assert git('rev-parse', 'HEAD').decode().strip() == candidate['head_oid']
git('diff', '--check', candidate['base_oid'], candidate['head_oid'])
log('PASS final candidate is clean and unchanged; all temporary integration fixtures cleaned up; R2 probes exit 0')
