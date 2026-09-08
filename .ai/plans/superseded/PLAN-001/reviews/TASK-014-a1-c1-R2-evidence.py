"""Read-only exact-candidate R2 cross-contract checks; writes only stdout."""
from __future__ import annotations

import ast
import copy
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-014-a1'
PLAN = '.ai/plans/current/PLAN-001'
STEM = f'{PLAN}/reviews/TASK-014-a1-c1-R2'
CANDIDATE = f'{PLAN}/reviews/candidates/CANDIDATE-TASK-014-a1-4bfad8611177.json'
R1 = f'{PLAN}/reviews/TASK-014-a1-c1-R1.json'
BASE = 'a0c6b0c2f8691e1280c1d1272c8124d6a98edaeb'
HEAD = '4bfad8611177959fb99eda01dd3c18077ff55f37'
FP = '4d8084b230013e6688039c87c6925cab747b7eab61e4754481449add3e5eee33'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / 'src'))
import contracts
import domain_values
import scope
from contracts import ContractRegistry, structural_task_digest
from domain_values import DomainException, ErrorCategory, ResultEnvelope, ResultStatus, ScopeClaim
from scope import PathChange, PathChangeKind, ScopeConflictKind, check_change_scope, detect_scope_conflicts, enforce_change_scope


def read(path: str, root: Path = TREE):
    return json.loads((root / path).read_text(encoding='utf-8'))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(data) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def git(*args: str, cwd: Path = TREE) -> bytes:
    return subprocess.run(['git', *args], cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True, shell=False).stdout


def identity():
    c = read(CANDIDATE, ROOT)
    assert c['base_oid'] == BASE and c['head_oid'] == HEAD and c['fingerprint'] == FP
    assert sha(canonical({k: v for k, v in c.items() if k != 'fingerprint'})) == FP
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert not git('status', '--porcelain=v1', '--untracked-files=all')
    assert not git('diff', 'HEAD', '--name-only', cwd=ROOT)
    git('merge-base', '--is-ancestor', BASE, HEAD)
    raw = git('diff', '--binary', BASE, HEAD)
    assert sha(raw) == c['diff_sha256']
    print('PASS frozen root/base/head; clean candidate and root tracked tree; raw binary diff', len(raw), sha(raw))
    for ref in c['context_refs']:
        assert sha(git('show', f"{HEAD}:{ref['path']}")) == ref['sha256'], ref
        assert git('hash-object', ref['path']).strip() == git('rev-parse', f"{HEAD}:{ref['path']}").strip()
    for ref in c['validation_refs']:
        data = (ROOT / ref['path']).read_bytes()
        assert sha(data) == ref['sha256']
        log = data.decode()
        assert HEAD in log and 'Exit code: 0' in log and 'Ran 17 tests' in log and 'OK' in log
    policy_paths = ['.ai/project/policy.json', '.ai/project/agent-models.json']
    assert sha(b''.join((ROOT / p).read_bytes() for p in policy_paths)) == c['policy_model_digest']
    for p in policy_paths:
        assert read(p, ROOT) == read(p)
        assert git('show', f'{BASE}:{p}') == git('show', f'{HEAD}:{p}')
    for oid in ['d1fc917466410febc6238479e65816dd39591a4f', 'e3c1177f993ee74815639a83ef3333faa4ba3957']:
        git('merge-base', '--is-ancestor', oid, BASE)
    for task_id in ['TASK-001', 'TASK-004']:
        assert read(f'{PLAN}/tasks/current/{task_id}.json')['status'] == 'accepted'
    for mod in [scope, domain_values, contracts]:
        assert Path(mod.__file__).resolve().parent == (TREE / 'src').resolve()
        print('Import origin:', mod.__file__)
    registry.validate(c)
    r1 = read(R1, ROOT)
    registry.validate(r1)
    assert r1['candidate_ref'] == CANDIDATE and r1['candidate_fingerprint'] == FP
    assert r1['stage'] == 'implementation' and r1['verdict'] == 'pass' and not r1['findings']
    assert [x['id'] for x in r1['checks']] == [f'R1-{i:02d}' for i in range(1, 12)]
    assert all(x['status'] == 'pass' for x in r1['checks'])
    assert r1['independent_session_id'] == '/root/review_014_c1_r1'
    assert r1['implementation_session_id'] == '/root/implement_014'
    assert sha((ROOT / R1).read_bytes()) == '2c5accc3c826a68861c3145df8becfdbfec5c998496192dd971d87c27cd3612a'
    print('PASS 13 committed context refs, 2 bound validation logs, policy/model digest, accepted ancestry, candidate schema, exact unchanged passing R1 and fingerprint', FP)
    return c


print('TASK-014-a1-c1-R2 independent cross-contract evidence')
print('Python:', sys.version)
print('Native submission: /root/review_014_c1_r2, OpenAI gpt-6-astra/xhigh, review_high rank 4; no separately provider-confirmed effective configuration')
registry = ContractRegistry(TREE / 'schemas/v1')
c = identity()
tasks = [read(f'{PLAN}/tasks/current/TASK-{i:03d}.json') for i in range(1, 40)]
task_by_id = {t['id']: t for t in tasks}
graph = read(f'{PLAN}/graph.json')
iso = read(f'{PLAN}/reviews/r4-isolation-review.json')
assert structural_task_digest(tasks) == graph['task_set_sha256'] == iso['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
gstruct = {k: graph[k] for k in ['schema_version', 'kind', 'id', 'plan_id', 'revision', 'nodes', 'task_set_sha256']}
assert sha(canonical(gstruct)) == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
assert graph['status'] == 'approved' and iso['verdict'] == 'pass' and graph['revision'] == iso['graph_revision'] == 4
claims = {}
for t in tasks:
    registry.validate(t)
    claims[t['id']] = ScopeClaim(**t['scope'])
    assert claims[t['id']].to_wire() == t['scope']
print('PASS approved r4 structural graph/task identities and all 39 registry-valid task scope wire roundtrips')

# Caller-side ordering observation is independently derived only for this probe.
edges = {n['task_id']: set(n['depends_on']) for n in graph['nodes']}
def ancestors(task_id: str) -> set[str]:
    reached, pending = set(), list(edges[task_id])
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node)
            pending.extend(edges[node])
    return reached

reach = {k: ancestors(k) for k in edges}
unordered = ordered_conflicts = total = 0
for a, b in itertools.combinations(sorted(claims), 2):
    ordered = a in reach[b] or b in reach[a]
    report = detect_scope_conflicts(claims[a], claims[b], sequenced=ordered)
    assert report.requires_sequencing == claims[a].conflicts_with(claims[b])
    assert report.can_run_concurrently == (not report.conflicts)
    assert report.sequencing_satisfied
    if not ordered:
        unordered += 1
        assert not report.conflicts, (a, b)
    elif report.conflicts:
        ordered_conflicts += 1
        assert report.blocks_concurrency and not report.has_unsequenced_conflict
    total += 1
assert total == 741 and unordered == 280
print(f'PASS actual graph: {total} pairs; {unordered} unordered pairs remain disjoint; {ordered_conflicts} ordered collisions satisfy sequencing but still block concurrency')

# All three planned consumers have a real read of this module, not a reverse import.
for consumer in ['TASK-015', 'TASK-022', 'TASK-024']:
    t = task_by_id[consumer]
    assert 'TASK-014' in t['depends_on'] and 'src/scope.py' in t['scope']['read_paths']
    before = detect_scope_conflicts(claims['TASK-014'], claims[consumer], sequenced=False)
    after = detect_scope_conflicts(claims['TASK-014'], claims[consumer], sequenced=True)
    assert before.has_unsequenced_conflict and not before.sequencing_satisfied
    assert before.conflicts == after.conflicts and after.sequencing_satisfied and not after.can_run_concurrently
    assert any(x.kind is ScopeConflictKind.WRITE_READ and x.left_path.as_wire() == 'src/scope.py' for x in after.conflicts)
print('PASS 3 actual consumer contract-read relationships; supplied ordering changes satisfaction only')

# A proposed semantic-resource collision needs both a new digest and ordering facts.
mutated = copy.deepcopy(tasks)
edit = next(t for t in mutated if t['id'] == 'TASK-014')
edit['scope']['resources'].append(task_by_id['TASK-013']['scope']['resources'][0])
registry.validate(edit)
assert structural_task_digest(mutated) != graph['task_set_sha256']
new_claim = ScopeClaim(**edit['scope'])
assert not detect_scope_conflicts(claims['TASK-013'], claims['TASK-014'], sequenced=False).conflicts
collision = detect_scope_conflicts(claims['TASK-013'], new_claim, sequenced=False)
ordered_collision = detect_scope_conflicts(claims['TASK-013'], new_claim, sequenced=True)
assert [x.kind for x in collision.conflicts] == [ScopeConflictKind.SEMANTIC_RESOURCE]
assert collision.has_unsequenced_conflict and not ordered_collision.has_unsequenced_conflict
assert ordered_collision.blocks_concurrency and ordered_collision.conflicts == collision.conflicts
print('PASS recovery/isolation probe: schema-valid scope mutation invalidates digest; shared resource needs ordering, never grants concurrency')

changed = git('diff', '--name-status', BASE, HEAD).decode().splitlines()
expected_paths = {f'{PLAN}/evidence/implementation/TASK-014.md', 'src/scope.py', 'tests/unit/planning_ownership/test_scope.py'}
assert {line.split('\t')[1] for line in changed} == expected_paths and all(line.startswith('A\t') for line in changed)
actual_changes = tuple(PathChange(line.split('\t')[1], 'added') for line in changed)
assert enforce_change_scope(claims['TASK-014'], iter(actual_changes)).permitted
for path in ['src/domain_values.py', 'src/contracts.py', f'{PLAN}/graph.json', '.ai/STATE.json']:
    assert not claims['TASK-014'].permits_write(path)
bad_changes = [PathChange('src/contracts.py', 'renamed', 'src/scope.py'), PathChange('src/domain_values.py', 'deleted'), PathChange('src/scope.py', 'renamed', '.ai/STATE.json')]
denied = check_change_scope(claims['TASK-014'], iter(bad_changes))
assert [(v.endpoint.value, v.path.as_wire()) for v in denied.violations] == [('path', 'src/contracts.py'), ('path', 'src/domain_values.py'), ('previous_path', '.ai/STATE.json')]
try:
    enforce_change_scope(claims['TASK-014'], bad_changes)
except DomainException as exc:
    assert exc.category is ErrorCategory.SCOPE_CONFLICT and not exc.retryable
    outcome = ResultEnvelope(ResultStatus.BLOCKED, (), exc.error, {'violations': exc.error.details.to_dict()['violations']})
    payload = outcome.payload.to_dict()
    assert len(payload['violations']) == 3
    payload['violations'].clear()
    assert len(outcome.payload.to_dict()['violations']) == 3
    assert len(outcome.error.details.to_dict()['violations']) == 3
else:
    raise AssertionError('out-of-scope endpoints did not raise')
print('PASS exact 3-file candidate scope; prerequisite delete and both canonical/other-owner rename boundaries; accepted error-to-result propagation')

wire_changes = [PathChange('src/owned/new.py', 'added'), PathChange('src/owned/current.py', 'modified'), PathChange('src/owned/old.py', 'deleted'), PathChange('src/owned/Caf\u00e9.py', 'renamed', 'src/owned/Cafe\u0301-old.py')]
assert {x.change.value for x in wire_changes} == set(registry.schema('handoff')['properties']['files_changed']['items']['properties']['change']['enum'])
handoff = dict(schema_version='1.0', kind='handoff', id='R2-synthetic-handoff', task_id='TASK-014', attempt_id='TASK-014-a1', branch='ai/PLAN-001/TASK-014/a1', base_oid=BASE, commit_oid=HEAD, files_changed=[x.to_wire() for x in wire_changes], validation=[], assumptions=[], remaining_risks=[], deviations=[], interfaces_changed=[], dependency_notes=[], reviewer_notes=[], command_evidence_refs=[], context_digest=FP)
registry.validate(handoff)
roundtrip = tuple(PathChange(**item) for item in json.loads(json.dumps(handoff))['files_changed'])
assert roundtrip == tuple(wire_changes)
assert enforce_change_scope(ScopeClaim(write_paths=['src/owned/']), roundtrip).permitted
assert all(set(x.to_wire()) == {'path', 'change', 'previous_path'} for x in roundtrip)
bad_wire = copy.deepcopy(handoff)
bad_wire['files_changed'][-1]['previous_path'] = None
registry.validate(bad_wire)  # Schema shape intentionally delegates endpoint coherence to typed semantics.
try:
    PathChange(**bad_wire['files_changed'][-1])
except ValueError:
    pass
else:
    raise AssertionError('ambiguous schema-valid rename accepted')
print('PASS frozen handoff vocabulary/keys, full registry validation and 4-kind JSON-to-typed roundtrip; semantic rename coherence rejects incomplete schema-valid facts')

tree_ast = ast.parse((TREE / 'src/scope.py').read_text(encoding='utf-8'))
imports = {node.module for node in ast.walk(tree_ast) if isinstance(node, ast.ImportFrom)} | {alias.name for node in ast.walk(tree_ast) if isinstance(node, ast.Import) for alias in node.names}
assert imports == {'__future__', 'collections.abc', 'dataclasses', 'enum', 'typing', 'domain_values'}
assert not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {'open', 'exec', 'eval', '__import__'} for node in ast.walk(tree_ast))
print('PASS explicit flat import closure; no graph, scheduler, Git, persistence, provider, schema mutation or dynamic IO calls')

command = read(f'{PLAN}/commands/test.TASK-014.json')
argv = [str(ROOT / '.ai/local/full-plan-venv/Scripts/python.exe'), *command['argv'][1:]]
environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
run = subprocess.run(argv, cwd=TREE, env=environment, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=False, timeout=command['timeout_seconds'])
output = run.stdout.decode('utf-8')
print('Declared command:', argv, '\nCandidate cwd:', TREE, '\nExit:', run.returncode)
print(output)
assert run.returncode == 0 and re.search(r'Ran 17 tests\b', output) and 'OK' in output.splitlines()
identity()
print('PASS all independent R2 cross-contract checks; exact candidate remains unchanged')
