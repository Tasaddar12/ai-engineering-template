"""Independent R1 evidence for the exact TASK-014 a1 c1 candidate; no candidate writes."""
from __future__ import annotations

import contextlib
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback
import unicodedata

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-014-a1'
STEM = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-014-a1-c1-R1'
CANDIDATE_REF = '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-014-a1-4bfad8611177.json'
BASE = 'a0c6b0c2f8691e1280c1d1272c8124d6a98edaeb'
HEAD = '4bfad8611177959fb99eda01dd3c18077ff55f37'
FINGERPRINT = '4d8084b230013e6688039c87c6925cab747b7eab61e4754481449add3e5eee33'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / 'src'))


def git(*args: str, cwd: Path = TREE) -> bytes:
    result = subprocess.run(['git', *args], cwd=cwd, capture_output=True, check=True)
    return result.stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def reject(label, call, expected=(TypeError, ValueError)):
    try:
        call()
    except expected:
        return
    raise AssertionError('invalid input was accepted: ' + label)


def verify_identity():
    candidate = json.loads((ROOT / CANDIDATE_REF).read_text(encoding='utf-8'))
    assert candidate['base_oid'] == BASE and candidate['head_oid'] == HEAD
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert not git('status', '--porcelain=v1', '--untracked-files=all')
    git('merge-base', '--is-ancestor', BASE, HEAD)
    for accepted in ('d1fc917466410febc6238479e65816dd39591a4f', 'e3c1177f993ee74815639a83ef3333faa4ba3957'):
        git('merge-base', '--is-ancestor', accepted, BASE)
    raw_diff = git('diff', '--binary', BASE, HEAD)
    assert digest(raw_diff) == candidate['diff_sha256']
    print('Verified raw binary diff:', digest(raw_diff), len(raw_diff), 'bytes')
    for entry in candidate['context_refs']:
        actual = digest(git('show', HEAD + ':' + entry['path']))
        assert actual == entry['sha256'], entry['path']
        print('Committed context verified:', entry['path'], actual)
    for entry in candidate['validation_refs']:
        contents = (ROOT / entry['path']).read_bytes()
        assert digest(contents) == entry['sha256'], entry['path']
        print('Bound validation verified:', entry['path'], digest(contents))
        print(contents.decode('utf-8'))
    policy_paths = ('.ai/project/policy.json', '.ai/project/agent-models.json')
    policy_model = digest(b''.join((ROOT / path).read_bytes() for path in policy_paths))
    assert policy_model == candidate['policy_model_digest']
    for path in policy_paths:
        assert git('show', HEAD + ':' + path) == git('show', BASE + ':' + path)
        assert json.loads((ROOT / path).read_bytes()) == json.loads((TREE / path).read_bytes())
    candidate_no_fp = {key: value for key, value in candidate.items() if key != 'fingerprint'}
    assert digest(canonical(candidate_no_fp)) == FINGERPRINT == candidate['fingerprint']
    print('Verified root/head/base, clean worktree, accepted ancestry, policy/model digest and fingerprint:', FINGERPRINT)
    changes = git('diff', '--find-renames', '--name-status', BASE, HEAD).decode().splitlines()
    expected = [
        'A\t.ai/plans/current/PLAN-001/evidence/implementation/TASK-014.md',
        'A\tsrc/scope.py',
        'A\ttests/unit/planning_ownership/test_scope.py',
    ]
    assert changes == expected, changes
    print('Verified exact changed paths:', changes)
    from contracts import ContractRegistry, structural_task_digest
    registry = ContractRegistry(TREE / 'schemas/v1')
    registry.validate(candidate, source=CANDIDATE_REF)
    plan_dir = TREE / '.ai/plans/current/PLAN-001'
    graph = json.loads((plan_dir / 'graph.json').read_bytes())
    iso = json.loads((plan_dir / 'reviews/r4-isolation-review.json').read_bytes())
    tasks = [json.loads(path.read_bytes()) for path in (plan_dir / 'tasks/current').glob('TASK-*.json')]
    task_digest = structural_task_digest(tasks)
    assert task_digest == graph['task_set_sha256'] == iso['task_set_sha256']
    assert graph['revision'] == iso['graph_revision'] == candidate['graph_revision'] == 4
    assert graph['status'] == 'approved' and iso['verdict'] == 'pass'
    structural_graph = {key: graph[key] for key in ('schema_version', 'kind', 'id', 'plan_id', 'revision', 'nodes', 'task_set_sha256')}
    assert digest(canonical(structural_graph)) == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
    selected = next(task for task in tasks if task['id'] == 'TASK-014')
    node = next(node for node in graph['nodes'] if node['task_id'] == 'TASK-014')
    assert selected['depends_on'] == node['depends_on'] == ['TASK-001', 'TASK-004']
    for task_id in selected['depends_on']:
        assert next(task for task in tasks if task['id'] == task_id)['status'] == 'accepted'
    from domain_values import ScopeClaim
    own_scope = ScopeClaim(**selected['scope'])
    assert all(own_scope.permits_write(line.split('\t')[1]) for line in changes)
    git('diff', '--check', BASE, HEAD)
    print('Verified candidate schema; approved structural graph/task digests:', task_digest)


def run_declared():
    command_path = TREE / '.ai/plans/current/PLAN-001/commands/test.TASK-014.json'
    command = json.loads(command_path.read_bytes())
    argv = [str(ROOT / '.ai/local/full-plan-venv/Scripts/python.exe'), *command['argv'][1:]]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    result = subprocess.run(argv, cwd=TREE, env=env, capture_output=True, text=True, timeout=180)
    print('Independent declared command:', argv)
    print('Working directory:', TREE)
    print('Exit:', result.returncode)
    print(result.stdout)
    print(result.stderr)
    assert result.returncode == 0
    assert re.search(r'Ran 17 tests', result.stderr) and '\nOK' in result.stderr


def run_probes():
    import domain_values
    import scope
    from domain_values import DomainException, ErrorCategory, ScopeClaim, ScopePath
    from scope import (AccessMode, ChangeEndpoint, ChangeScopeReport, ChangeScopeViolation,
                       PathChange, ScopeConflict, ScopeConflictKind, ScopeConflictReport,
                       check_change_scope, detect_scope_conflicts, enforce_change_scope)
    for module in (domain_values, scope):
        assert Path(module.__file__).resolve().parent == (TREE / 'src').resolve()
        print('Verified import origin:', module.__file__)

    paths = ('pkg', 'PKG/', 'pkg/file.py', 'PKG\\FILE.PY', 'pkg/sub/', 'pkg/sub/a.py',
             'pkgs/file.py', 'pkg2/', 'caf\u00e9.py', 'cafe\u0301.py', 'Stra\u00dfe.py',
             'STRASSE.PY', '\uff30\uff2b\uff27/file.py', 'pkg/\u212a.py', 'pkg/k.py', 'z/file.py')

    def key(path):
        return tuple(unicodedata.normalize('NFKC', part).casefold()
                     for part in path.replace('\\', '/').rstrip('/').split('/'))

    def overlaps(a, b):
        ka, kb = key(a), key(b)
        return ka[:len(kb)] == kb or kb[:len(ka)] == ka

    conflict_cases = 0
    for a, b, left_mode, right_mode, sequenced in itertools.product(paths, paths, ('read', 'write'), ('read', 'write'), (False, True)):
        left = ScopeClaim(**{left_mode + '_paths': (a,)})
        right = ScopeClaim(**{right_mode + '_paths': (b,)})
        expected = overlaps(a, b) and (left_mode == 'write' or right_mode == 'write')
        report = detect_scope_conflicts(left, right, sequenced=sequenced)
        assert bool(report.conflicts) == expected == left.conflicts_with(right), (a, b, left_mode, right_mode)
        assert report.blocks_concurrency == expected and report.can_run_concurrently == (not expected)
        assert report.has_unsequenced_conflict == (expected and not sequenced)
        assert report.sequencing_satisfied == (not expected or sequenced)
        if expected:
            assert len(report.conflicts) == 1
            item = report.conflicts[0]
            assert item.left_access == left_mode and item.right_access == right_mode
            assert item.kind.value == ('write_write' if left_mode == right_mode else 'write_read')
        conflict_cases += 1
    print('PASS independent path/access/sequencing matrix:', conflict_cases, 'cases; exact, prefix, component boundary, case, separators, NFC/NFKC, bidirectional readers')

    resources = ('schema:alpha', 'SCHEMA:ALPHA', 'schema:alpha/x', 'schema:alphabeta',
                 'component:\u212aelvin', 'component:kelvin', 'component:\uff26\uff2f\uff2f',
                 'component:foo', 'component:cafe\u0301', 'component:caf\u00e9')
    resource_cases = 0
    for a, b, sequenced in itertools.product(resources, resources, (False, True)):
        left = ScopeClaim(write_paths=('left.py',), resources=(a,))
        right = ScopeClaim(write_paths=('right.py',), resources=(b,))
        expected = unicodedata.normalize('NFKC', a).casefold() == unicodedata.normalize('NFKC', b).casefold()
        report = detect_scope_conflicts(left, right, sequenced=sequenced)
        assert bool(report.conflicts) == expected == left.conflicts_with(right), (a, b)
        if expected:
            assert len(report.conflicts) == 1 and report.conflicts[0].kind is ScopeConflictKind.SEMANTIC_RESOURCE
        resource_cases += 1
    print('PASS independent semantic-resource equivalence matrix:', resource_cases, 'cases; exact equivalence without prefix inference')

    first = ScopeClaim(write_paths=('z/', 'a/', 'nested', 'nested/child'), read_paths=('r/',), resources=('resource:Z', 'resource:A'))
    second = ScopeClaim(write_paths=('R/file', 'Z/file', 'nested/child/file'), read_paths=('A/file',), resources=('RESOURCE:a', 'RESOURCE:z'))
    expected = detect_scope_conflicts(first, second, sequenced=False).conflicts
    def reverse(claim):
        return ScopeClaim(**{name: tuple(reversed(values)) for name, values in claim.to_wire().items()})
    assert detect_scope_conflicts(reverse(first), reverse(second), sequenced=False).conflicts == expected
    assert len(expected) == 7, expected
    print('PASS mixed 7-collision completeness and declaration-order independence')

    scope_data = [
        {}, {'write_paths': ('pkg/',)}, {'write_paths': ('pkg',)},
        {'write_paths': ('pkg/file.py',)}, {'read_paths': ('pkg/',)},
        {'write_paths': ('pkg/',), 'prohibited_paths': ('pkg/sub/',)},
        {'write_paths': ('pkg/',), 'prohibited_paths': ('PKG\\FILE.PY',)},
        {'write_paths': ('caf\u00e9.py', 'pkg/'), 'prohibited_paths': ('pkg/\u212a.py',)},
    ]
    changed = ('pkg', 'pkg/file.py', 'PKG\\FILE.PY', 'pkg/sub', 'pkg/sub/a.py', 'pkgs/file.py',
               'pkg/file.py/child', 'outside.py', 'caf\u00e9.py', 'cafe\u0301.py',
               '\uff30\uff2b\uff27/file.py', 'pkg/\u212a.py', 'pkg/k.py')
    def contains(claim, candidate):
        if claim.replace('\\', '/').endswith('/'):
            return len(key(candidate)) > len(key(claim)) and key(candidate)[:len(key(claim))] == key(claim)
        return key(claim) == key(candidate)
    def allowed(data, candidate):
        return any(contains(p, candidate) for p in data.get('write_paths', ())) and not any(contains(p, candidate) for p in data.get('prohibited_paths', ()))
    endpoint_cases = 0
    for data in scope_data:
        owner = ScopeClaim(**data)
        for path, kind in itertools.product(changed, ('added', 'modified', 'deleted')):
            change = PathChange(path, kind)
            report = check_change_scope(owner, (change,))
            assert report.permitted == allowed(data, path) == owner.permits_write(path)
            assert [item.endpoint for item in report.violations] == ([] if allowed(data, path) else [ChangeEndpoint.PATH])
            endpoint_cases += 1
        for path, old in itertools.product(changed, changed):
            change = PathChange(path, 'renamed', old)
            expected_endpoints = ([] if allowed(data, path) else [ChangeEndpoint.PATH]) + ([] if allowed(data, old) else [ChangeEndpoint.PREVIOUS_PATH])
            report = check_change_scope(owner, iter((change,)))
            assert [item.endpoint for item in report.violations] == expected_endpoints, (data, path, old)
            assert report.permitted == (not expected_endpoints)
            endpoint_cases += 1
    print('PASS independent change-scope matrix:', endpoint_cases, 'cases; all four kinds, both rename endpoints, read-only, exact/prefix permissions, Unicode, prohibited overrides')

    rejects = [
        ('wrong scope', lambda: check_change_scope({}, ())),
        ('wrong left claim', lambda: detect_scope_conflicts({}, ScopeClaim(), sequenced=False)),
        ('wrong right claim', lambda: detect_scope_conflicts(ScopeClaim(), {}, sequenced=False)),
    ]
    for bad in (0, 1, None, 'false', [], {}):
        rejects.append(('nonboolean sequencing', lambda bad=bad: detect_scope_conflicts(ScopeClaim(), ScopeClaim(), sequenced=bad)))
    for bad in ('x', b'x', bytearray(b'x'), None, 42, ({'path': 'pkg/x'},)):
        rejects.append(('invalid changes collection', lambda bad=bad: check_change_scope(ScopeClaim(), bad)))
    for bad in ('', '../outside', 'pkg/../outside', '/outside', 'C:\\outside', '//host/share', 'pkg//x', 'pkg/*.py', 'pkg/file:stream', 'pkg/NUL.txt', 'pkg/x\x00', 'pkg/'):
        rejects.append(('invalid change path', lambda bad=bad: PathChange(bad, 'deleted')))
        rejects.append(('invalid previous path', lambda bad=bad: PathChange('pkg/x', 'renamed', bad)))
    rejects.extend([
        ('missing rename origin', lambda: PathChange('pkg/new', 'renamed')),
        ('unowned kind', lambda: PathChange('pkg/new', 'copied')),
        ('ambiguous nonrename origin', lambda: PathChange('pkg/new', 'modified', 'pkg/old')),
        ('directory value', lambda: PathChange(ScopePath.directory('pkg/'), 'deleted')),
        ('directory old value', lambda: PathChange('pkg/x', 'renamed', ScopePath.directory('pkg/'))),
        ('read/read conflict value', lambda: ScopeConflict('write_read', ScopePath('x'), ScopePath('x'), 'read', 'read')),
        ('wrong conflict kind', lambda: ScopeConflict('write_write', ScopePath('x'), ScopePath('x'), 'write', 'read')),
        ('non-overlapping conflict', lambda: ScopeConflict('write_write', ScopePath('x'), ScopePath('y'), 'write', 'write')),
        ('invalid conflict members', lambda: ScopeConflictReport(False, ['x'])),
        ('scalar conflict members', lambda: ScopeConflictReport(False, 'x')),
        ('invalid report sequenced', lambda: ScopeConflictReport(1, [])),
        ('invalid report changes', lambda: ChangeScopeReport(['x'])),
        ('invalid report violations', lambda: ChangeScopeReport([], ['x'])),
        ('wrong violation endpoint path', lambda: ChangeScopeViolation(PathChange('x', 'deleted'), 'path', ScopePath('y'))),
        ('nonrename previous violation', lambda: ChangeScopeViolation(PathChange('x', 'deleted'), 'previous_path', ScopePath('x'))),
        ('unreported violation change', lambda: ChangeScopeReport([], [ChangeScopeViolation(PathChange('x', 'deleted'), 'path', ScopePath('x'))])),
        ('mixed resource and path', lambda: ScopeConflict('semantic_resource', ScopePath('x'), left_resource='r', right_resource='r')),
        ('missing resource', lambda: ScopeConflict('semantic_resource', left_resource='r')),
        ('nonmatching resource', lambda: ScopeConflict('semantic_resource', left_resource='r1', right_resource='r2')),
    ])
    for label, call in rejects:
        reject(label, call)
    print('PASS invalid-input checks:', len(rejects), 'cases')

    changes = [PathChange('pkg/new', 'renamed', 'outside/old')]
    denied = check_change_scope(ScopeClaim(write_paths=('pkg/',)), changes)
    changes.clear()
    assert len(denied.changes) == 1 and len(denied.violations) == 1
    for obj, attr, value in ((denied, 'changes', ()), (denied.changes[0], 'path', ScopePath('x')), (denied.violations[0], 'endpoint', ChangeEndpoint.PATH)):
        reject('immutable report/value', lambda obj=obj, attr=attr, value=value: setattr(obj, attr, value), (AttributeError,))
    try:
        enforce_change_scope(ScopeClaim(write_paths=('pkg/',)), denied.changes)
    except DomainException as exc:
        assert exc.error.category is ErrorCategory.SCOPE_CONFLICT and exc.error.retryable is False
        details = exc.error.details.to_dict()
        assert details == {'violations': [{'change': 'renamed', 'endpoint': 'previous_path', 'path': 'outside/old'}]}
        details['violations'].clear()
        assert len(exc.error.details.to_dict()['violations']) == 1
    else:
        raise AssertionError('scope enforcement did not reject rename from outside')
    assert enforce_change_scope(ScopeClaim(write_paths=('pkg/',)), [PathChange('pkg/new', 'added')]).permitted
    assert check_change_scope(ScopeClaim(), []).permitted
    print('PASS detached/immutable reports and error details; structured nonretryable enforcement; empty and permitted inputs')


def main():
    print('TASK-014-a1-c1-R1 independent evidence')
    print('Python:', sys.version)
    print('Reviewer: /root/review_014_c1_r1; native submission OpenAI gpt-6-astra/xhigh, review_high rank 4; no separately provider-confirmed effective model/effort/UUID')
    verify_identity()
    run_declared()
    run_probes()
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert not git('status', '--porcelain=v1', '--untracked-files=all')
    print('PASS final root/base/head freeze and candidate cleanliness')


if __name__ == '__main__':
    log = Path(str(STEM) + '-evidence.txt')
    code = 0
    with log.open('w', encoding='utf-8', newline='\n') as stream, contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        try:
            main()
        except BaseException:
            traceback.print_exc()
            code = 1
    print(log.read_text(encoding='utf-8'))
    sys.exit(code)
