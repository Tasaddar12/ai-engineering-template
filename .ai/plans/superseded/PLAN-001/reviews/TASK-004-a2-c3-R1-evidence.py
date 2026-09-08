"""Independent read-only candidate probes; only temporary fixtures are mutated."""
from __future__ import annotations
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-004-a2'
PLAN = Path('.ai/plans/current/PLAN-001')
STEM = ROOT / PLAN / 'reviews/TASK-004-a2-c3-R1'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / 'src'))
import ai
import contracts
import domain_values as dv
import install
import validate_foundation as vf

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def git(*args):
    return subprocess.check_output(['git', *args], cwd=TREE)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def typed_error(fn, category):
    try:
        fn()
    except dv.DomainException as exc:
        assert exc.category == category, (exc.category, category)
        assert exc.error.retryable is False
        return
    raise AssertionError('expected typed error')

def replace(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: replace(item, old, new) for key, item in value.items()}
    return value

candidate = read(ROOT / PLAN / 'reviews/candidates/CANDIDATE-TASK-004-a2-e3c1177f993e.json')
assert git('rev-parse', 'HEAD').decode().strip() == candidate['head_oid']
assert not git('status', '--porcelain')
git('merge-base', '--is-ancestor', candidate['base_oid'], candidate['head_oid'])
git('merge-base', '--is-ancestor', 'd1fc917466410febc6238479e65816dd39591a4f', candidate['base_oid'])
assert sha(git('diff', '--binary', candidate['base_oid'], candidate['head_oid'])) == candidate['diff_sha256']
for ref in candidate['context_refs']:
    committed = git('show', f"{candidate['head_oid']}:{ref['path']}")
    assert sha(committed) == ref['sha256'], ref
    # Checkout transformations are permitted only when Git confirms unchanged files.
    assert (TREE / ref['path']).read_bytes().replace(b'\r\n', b'\n') == committed.replace(b'\r\n', b'\n')
for ref in candidate['validation_refs']:
    assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256']
assert sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()) == candidate['policy_model_digest']
unsigned = {key: value for key, value in candidate.items() if key != 'fingerprint'}
assert sha(json.dumps(unsigned, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == candidate['fingerprint']
expected_paths = {'src/contracts.py', 'src/install.py', 'src/validate_foundation.py', 'tests/unit/schemas/test_contracts.py', '.ai/plans/current/PLAN-001/evidence/implementation/TASK-004.md'}
assert set(git('diff', '--name-only', candidate['base_oid'], candidate['head_oid']).decode().splitlines()) == expected_paths
git('diff', '--check', candidate['base_oid'], candidate['head_oid'])
print('PASS candidate identity: clean exact head/base, accepted TASK-001 ancestor, binary diff, 12 context hashes, validation hash, policy/model hash, fingerprint and five owned paths', flush=True)
for module in (ai, contracts, dv, install, vf):
    assert Path(module.__file__).resolve().parent == (TREE / 'src').resolve()
print('PASS module origins:', ', '.join(str(Path(m.__file__)) for m in (ai, contracts, dv, install, vf)), flush=True)

registry = contracts.load_contract_registry(TREE / 'schemas/v1')
examples = [read(path) for path in (TREE / 'schemas/examples').glob('*.json')]
examples.append(read(TREE / '.ai/project/agent-models.json'))
assert len(examples) == 27 and {item['kind'] for item in examples} == set(registry.kinds)
for artifact in examples:
    original = copy.deepcopy(artifact)
    registry.validate(dv.FrozenJsonObject(artifact))
    assert artifact == original
    bad = dict(artifact, independently_unknown=True)
    typed_error(lambda: registry.validate(bad), dv.ErrorCategory.VALIDATION_FAILED)
    bad = dict(artifact, schema_version='3.0')
    typed_error(lambda: registry.validate(bad), dv.ErrorCategory.UNSUPPORTED_CAPABILITY)
detached = registry.schema('spec')
detached['properties']['title']['type'] = 'integer'
registry.validate(read(TREE / 'schemas/examples/spec.json'))
typed_error(lambda: registry.validate(dict(read(TREE / 'schemas/examples/spec.json'), title=3)), dv.ErrorCategory.VALIDATION_FAILED)
print('PASS all 27 kinds: immutable valid inputs, unknown fields and unsupported versions; schema views cannot mutate validators', flush=True)

valid_refs = ['task:PLAN-101:TASK-001', 'command:PLAN-101:test.TASK-001', 'review:PLAN-101:R1', 'evidence:PLAN-101:E1', 'spec:PLAN-101:SPEC-001', 'plan:PLAN-101', 'policy:P1', 'future-kind:PLAN-101:X']
for text in valid_refs:
    parts = text.split(':')
    expected = dv.RecordRef(parts[0], dv.EntityId(parts[-1]), dv.PlanId(parts[1]) if len(parts) == 3 else None)
    assert contracts.parse_record_ref(text) == expected
for text in ['task:TASK-001', 'command:test.TASK-001', 'review:R1', 'evidence:E1', 'task:PLAN-1:TASK-001', 'task:PLAN-101:TASK-1', 'task:PLAN-101:TASK-001:x', 'plan:PLAN-101:PLAN-101', 'TASK:PLAN-101:TASK-001', '', None]:
    typed_error(lambda: contracts.parse_record_ref(text), dv.ErrorCategory.INVALID_INPUT)
typed_error(lambda: contracts.parse_record_ref(valid_refs[0], expected_plan_id='PLAN-102'), dv.ErrorCategory.INVALID_INPUT)
typed_error(lambda: contracts.parse_record_ref(valid_refs[0], expected_kind='review'), dv.ErrorCategory.INVALID_INPUT)
assert contracts.parse_record_ref('task:PLAN-101:TASK-001').key != contracts.parse_record_ref('task:PLAN-102:TASK-001').key
with tempfile.TemporaryDirectory(prefix='r1-offline-') as tmp:
    schemas = Path(tmp) / 'v1'
    shutil.copytree(TREE / 'schemas/v1', schemas)
    target = schemas / 'spec.schema.json'
    original = read(target)
    for keyword in ('$ref', '$dynamicRef'):
        changed = copy.deepcopy(original)
        changed['allOf'] = [{keyword: 'https://unavailable.invalid/missing.json'}]
        write(target, changed)
        with patch('socket.create_connection') as socket_call:
            typed_error(lambda: contracts.load_contract_registry(schemas), dv.ErrorCategory.UNSUPPORTED_CAPABILITY)
        socket_call.assert_not_called()
        changed['allOf'] = [{keyword: '#/$defs/missing'}]
        write(target, changed)
        local_registry = contracts.load_contract_registry(schemas)
        typed_error(lambda: local_registry.validate(read(TREE / 'schemas/examples/spec.json')), dv.ErrorCategory.VALIDATION_FAILED)
print('PASS logical reference constructor/error parity and qualified keys; remote/local $ref and $dynamicRef errors are typed and offline', flush=True)

tasks = [read(path) for path in (TREE / PLAN / 'tasks/current').glob('TASK-*.json')]
graph = read(TREE / PLAN / 'graph.json')
approval = read(TREE / PLAN / 'reviews/r4-isolation-review.json')
assert len(tasks) == 39
assert contracts.STRUCTURAL_TASK_FIELDS == ai.STRUCTURAL_TASK_FIELDS
digest = contracts.structural_task_digest(tasks)
assert digest == ai.structural_task_digest(tasks) == graph['task_set_sha256'] == approval['task_set_sha256']
assert graph['revision'] == approval['graph_revision'] == 4 and approval['verdict'] == 'pass'
assert contracts.structural_task_digest(list(reversed(tasks))) == digest
print('PASS 39-task bootstrap/new/approved graph identity:', digest, flush=True)
sample = read(TREE / 'schemas/examples/task.json')
known_tails = ['plan.json', 'plan.md', 'spec.json', 'spec.md', 'graph.json', '', 'tasks/current/TASK-001.json', 'tasks/current/']
cases = 0
with tempfile.TemporaryDirectory(prefix='r1-relocation-matrix-') as tmp:
    for namespace in ('.ai', '.codex', '.claude'):
        for separator in ('/', '\\'):
            base = copy.deepcopy(sample)
            refs = [(f'{namespace}/plans/current/PLAN-101/' + tail).replace('/', separator) for tail in known_tails]
            base['input_contracts'] = refs[:]
            base['output_contracts'] = refs[:]
            base['scope']['read_paths'] = [f'{namespace}/plans/current/PLAN-101/tasks/current/'.replace('/', separator)]
            expected = ai.structural_task_digest([base])
            assert contracts.structural_task_digest([base]) == expected
            for pb in ('current', 'completed', 'archived'):
                for tb in ('current', 'completed', 'archived'):
                    moved = replace(base, f'{separator}plans{separator}current{separator}', f'{separator}plans{separator}{pb}{separator}')
                    moved = replace(moved, f'{separator}tasks{separator}current{separator}', f'{separator}tasks{separator}{tb}{separator}')
                    location = Path(tmp) / namespace / 'plans' / pb / 'PLAN-101/tasks' / tb / 'TASK-001.json'
                    write(location, moved)
                    observed = read(location)
                    assert contracts.structural_task_digest([observed]) == expected
                    observed['scope']['write_paths'][0] = 'src/changed.py'
                    assert contracts.structural_task_digest([observed]) != expected
                    cases += 1
assert cases == 54
print('PASS 54 disk-written/read provider/separator/plan/task bucket combinations: both mixed arrays, eight closed forms, task bucket scope, real scope invalidation', flush=True)

negative = ['spec.json: required shape comes from docs/contract.md', 'spec.json requires review.md', 'spec.json.', 'spec.json/', 'spec.json\\', 'notes.json', 'reviews/REVIEW-001.json', 'spec.json — révision nécessaire.md', 'tasks/current/TASK-001.json requires review.md', 'spec.json\n', 'spec.json ']
prose_cases = 0
for field in ('input_contracts', 'output_contracts'):
    for text in ['.codex/plans/current/PLAN-101/' + tail for tail in negative] + ['See .codex/plans/current/PLAN-101/spec.json', 'https://example.invalid/.codex/plans/current/PLAN-101/spec.json', 'config/plans/current/PLAN-101/spec.json']:
        before = copy.deepcopy(sample)
        before[field] = [text]
        after = copy.deepcopy(before)
        after[field] = [text.replace('/current/', '/completed/')]
        assert contracts._canonicalize_task_projection(before)[field] == before[field]
        assert contracts._canonicalize_task_projection(after)[field] == after[field]
        assert contracts.structural_task_digest([before]) != contracts.structural_task_digest([after])
        prose_cases += 1
dv.ScopePath('.codex/plans/current/PLAN-101/spec.json requires review.md')
for field in ('input_contracts', 'output_contracts'):
    before = copy.deepcopy(sample)
    before[field] = ['task:PLAN-101:TASK-001']
    after = copy.deepcopy(before)
    after[field] = ['task:PLAN-102:TASK-001']
    assert contracts.structural_task_digest([before]) != contracts.structural_task_digest([after])
print(f'PASS {prose_cases} unmatched prose/suffix cases byte-exact in both arrays, including ScopePath-valid sentence; logical identity changes invalidate', flush=True)

with tempfile.TemporaryDirectory(prefix='r1-closure-') as tmp:
    source = Path(tmp)
    src = source / 'src'
    src.mkdir()
    fixture = {'ai.py': 'import install\n', 'validate_foundation.py': 'import contracts\n', 'contracts.py': 'import domain_values\n', 'domain_values.py': 'VALUE=1\n', 'install.py': 'import helper_a\n', 'helper_a.py': 'from helper_b import VALUE\n', 'helper_b.py': 'import helper_a\nVALUE=2\n', 'unrelated.py': "raise RuntimeError('not reachable')\n"}
    for name, content in fixture.items():
        (src / name).write_text(content, encoding='utf-8')
    assert {path.name for path in install._tool_sources(source)} == set(fixture) - {'unrelated.py'}
    (src / 'domain_values.py').unlink()
    try:
        install._tool_sources(source)
    except install.InstallError as exc:
        assert 'missing required' in str(exc)
    else:
        raise AssertionError('missing helper was accepted')
print('PASS transitive helper closure includes reachable install.py and two extra modules with cycle, excludes unrelated source, rejects missing required helper', flush=True)

environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
environment.pop('PYTHONPATH', None)
definition = read(TREE / PLAN / 'commands/test.TASK-004.json')
commands = [('declared', [sys.executable, *definition['argv'][1:]]), ('bootstrap', [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_*.py']), ('foundation', [sys.executable, 'src/validate_foundation.py'])]
for label, argv in commands:
    result = subprocess.run(argv, cwd=TREE, env=environment, capture_output=True, text=True, timeout=180, shell=False)
    output = 'argv=' + repr(argv) + '\ncwd=' + str(TREE) + '\nexit=' + str(result.returncode) + '\n' + result.stdout + result.stderr
    Path(str(STEM) + '-' + label + '.txt').write_text(output, encoding='utf-8')
    assert result.returncode == 0, output
    if label in ('declared', 'bootstrap'):
        count = re.search(r'Ran (\d+) tests?', result.stderr)
        assert count and int(count.group(1)) == (21 if label == 'declared' else 24), output
        print(f'PASS {label}: {count.group(1)} tests, exact candidate, exit 0', flush=True)
    else:
        print('PASS foundation:', result.stdout.strip(), flush=True)
assert not git('status', '--porcelain')
assert git('rev-parse', 'HEAD').decode().strip() == candidate['head_oid']
print('PASS final candidate remains clean and unchanged; temporary probes cleaned up', flush=True)
