"""Fresh R2 exact-candidate and accepted-contract verification; read-only source."""
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-006-a3'
P = '.ai/plans/current/PLAN-001/'
STEM = P + 'reviews/TASK-006-a3-c3-R2'
BASE = '10e27db6472bbf6d9a5a5023233ede12fae5d52d'
HEAD = 'b41b37ac6b15ecbdfb55ed26bdc086686f4e9416'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / 'src'))
from contracts import ContractRegistry, structural_task_digest

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args, root=TREE):
    return subprocess.check_output(['git', '-C', str(root), *args])

def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

manifest_path = P + 'reviews/candidates/CANDIDATE-TASK-006-a3-b41b37ac6b15.json'
manifest = json.loads((ROOT / manifest_path).read_bytes())
registry = ContractRegistry(TREE / 'schemas/v1')
registry.validate(manifest)
assert git('rev-parse', 'HEAD').decode().strip() == HEAD == manifest['head_oid']
assert git('rev-parse', 'HEAD', root=ROOT).decode().strip() == BASE == manifest['base_oid']
assert git('merge-base', BASE, HEAD).decode().strip() == BASE
assert not git('status', '--porcelain=v1', '--untracked-files=all')
rawdiff = git('diff', '--binary', BASE, HEAD)
assert sha(rawdiff) == manifest['diff_sha256']
(ROOT / (STEM + '-candidate.diff')).write_bytes(rawdiff)
git('diff', '--check', BASE, HEAD)
paths = git('diff', '--name-only', BASE, HEAD).decode().splitlines()
assert set(paths) == {'src/commands.py', 'tests/unit/commands/test_commands.py', P + 'evidence/implementation/TASK-006.md'}
print('IDENTITY', BASE, HEAD, 'clean=true', 'diff_bytes=' + str(len(rawdiff)), 'sha256=' + sha(rawdiff))
print('CHANGED', paths)
for ref in manifest['context_refs']:
    assert sha(git('show', HEAD + ':' + ref['path'])) == ref['sha256'], ref['path']
    print('CONTEXT', ref['path'], ref['sha256'])
for ref in manifest['validation_refs']:
    raw = (ROOT / ref['path']).read_bytes()
    assert sha(raw) == ref['sha256'], ref['path']
    log = raw.decode('utf-8-sig')
    assert 'Head: ' + HEAD in log and 'Exit code: 0' in log and 'Runtime/origin probe exit: 0' in log
    assert 'jsonschema: 4.26.0' in log and 'Ran 22 tests' in log and 'OK (skipped=1)' in log
    origins = ast.literal_eval(next(x[9:] for x in log.splitlines() if x.startswith('Origins: ')))
    normalized = [(name, path.replace('\\', '/')) for name, path in origins]
    origin_prefix = '/mnt/d' if 'linux' in ref['path'] else 'D:'
    assert normalized == [('commands', origin_prefix + '/Codex Projects/ai-engineering-template/.worktrees/TASK-006-a3/src/commands.py')]
    phases = [json.loads(x.split('TASK-006-FIXTURE ', 1)[1]) for x in log.splitlines() if x.startswith('TASK-006-FIXTURE ')]
    assert len(phases) == 4
    assert {(x['phase'], x['mode']) for x in phases} == {(phase, mode) for phase in ('detached_while_parent_live', 'inherited_after_parent_exit') for mode in ('timeout', 'cancellation')}
    for phase in phases:
        assert phase['parent_pid'] > 0 and phase['child_pid'] > 0
        assert phase['parent_gone'] and phase['child_gone'] and phase['reader_threads_settled']
        assert phase['native_termination_calls'] == 1 and not phase['watchdog_intervened']
        assert 0 <= phase['startup_seconds'] < 3 and 0 <= phase['overall_seconds'] < 4
        assert phase['cancellation_observed'] == (phase['mode'] == 'cancellation')
        if phase['mode'] == 'cancellation':
            assert 0 <= phase['cancellation_response_seconds'] < 3
        else:
            assert phase['cancellation_response_seconds'] is None
        if 'linux' in ref['path']:
            if phase['phase'] == 'inherited_after_parent_exit':
                assert phase['child_process_group'] == phase['parent_process_group']
            else:
                assert phase['child_process_group'] != phase['parent_process_group']
                assert phase['child_session'] != phase['parent_session']
    print('VALIDATION', ref['path'], ref['sha256'], '22 discovered/21 non-skipped/1 skip; four phases verified')
    print('\n'.join(x for x in log.splitlines() if x.startswith(('Python:', 'Executable:', 'Platform:', 'Origins:'))))
policy_raw = (ROOT / '.ai/project/policy.json').read_bytes()
model_raw = (ROOT / '.ai/project/agent-models.json').read_bytes()
assert sha(policy_raw + model_raw) == manifest['policy_model_digest']
for path in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
    assert json.loads((ROOT / path).read_bytes()) == json.loads((TREE / path).read_bytes())
    assert git('show', BASE + ':' + path) == git('show', HEAD + ':' + path)
identity = {k: v for k, v in manifest.items() if k != 'fingerprint'}
assert sha(canon(identity)) == manifest['fingerprint'] == '3df5453edcaf80c6237f35c5ca1c5adb81adfb9682cae3af95e25091d2435e80'
print('POLICY_MODEL', manifest['policy_model_digest'], 'FINGERPRINT', manifest['fingerprint'])
frozen = [('src/commands.py', '39828108eb7d198d81d810c8fd9e136e3f64f8f0', '700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0'), ('tests/unit/commands/test_commands.py', '7bf8228bb4105e72b9f711d9f4e4bf1fc3c2377a', 'c77171fefa9d43be13c4f06fe11dd49bc741caae267d6232578161248ff9952a')]
for path, blob, digest in frozen:
    assert git('rev-parse', HEAD + ':' + path).decode().strip() == blob
    assert sha((TREE / path).read_bytes()) == digest
    print('FROZEN', path, blob, digest)
a2 = '4fe9e7a30378e13b43dc51745593adae2bb8b051'
for path in paths:
    assert git('show', '2488fc3f63f34154f037e81690b719b28745308c:' + path) == git('show', a2 + ':' + path)
assert git('show', a2 + ':src/commands.py') == git('show', HEAD + ':src/commands.py')
patch = git('diff', '--binary', a2, HEAD, '--', 'tests/unit/commands/test_commands.py')
assert len(patch) == 2100 and sha(patch) == 'dd19ecadc3cac20102165a206d94b6d8bea4db64eb0e06f91c455af7303f1c6e'
print('ASSERTION_PATCH', patch.decode())
tasks = [json.loads(p.read_bytes()) for p in (TREE / (P + 'tasks/current')).glob('TASK-*.json')]
graph = json.loads((TREE / (P + 'graph.json')).read_bytes())
isolation = json.loads((TREE / (P + 'reviews/r4-isolation-review.json')).read_bytes())
digest = structural_task_digest(tasks)
assert len(tasks) == 39 and graph['revision'] == isolation['graph_revision'] == 4
assert graph['status'] == 'approved' and isolation['verdict'] == 'pass'
assert digest == graph['task_set_sha256'] == isolation['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
projection = {k: graph[k] for k in ('schema_version', 'kind', 'id', 'plan_id', 'revision', 'nodes', 'task_set_sha256')}
assert sha(canon(projection)) == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
for task, oid, source in [('TASK-002', '460ab567d01912167557f2f671ed07c63f0a31e7', 'src/local_ports.py'), ('TASK-004', 'e3c1177f993ee74815639a83ef3333faa4ba3957', 'src/contracts.py'), ('TASK-038', '6f2b12c3283ed7d6e3d4876020fe690c6e0061a3', 'src/config.py')]:
    git('merge-base', '--is-ancestor', oid, BASE)
    assert next(t for t in tasks if t['id'] == task)['status'] == 'accepted'
    for path in (source, P + 'evidence/implementation/' + task + '.md'):
        assert git('show', oid + ':' + path) == git('show', HEAD + ':' + path)
    print('ACCEPTED', task, oid, 'source and handoff unchanged')
print('R4', digest, sha(canon(projection)))
r1path = P + 'reviews/TASK-006-a3-c3-R1.json'
r1raw = (ROOT / r1path).read_bytes()
r1 = json.loads(r1raw)
registry.validate(r1)
assert r1['verdict'] == 'pass' and r1['candidate_ref'] == manifest_path
assert r1['candidate_fingerprint'] == manifest['fingerprint']
assert [c['id'] for c in r1['checks']] == [f'R1-{i:02}' for i in range(1, 12)]
assert all(c['status'] == 'pass' for c in r1['checks']) and not r1['findings']
assert r1['independent_session_id'] == '/root/review_006_c3_r1'
assert r1['reviewer']['invocation_id'] == 'call_eKfxZnJLmAT6jx3rB5YZ0I9w'
assert r1['implementation_session_id'] == '/root/implement_006_a3'
print('R1', r1path, sha(r1raw), 'same fingerprint; all11 pass; distinct implementation/R1/R2 sessions')
for file in sorted((ROOT / (P + 'reviews')).glob('TASK-006-a3-c3-R1*')):
    if file.is_file():
        print('R1_COMPANION', file.name, sha(file.read_bytes()))
print('PASS: exact candidate, all context/evidence, accepted dependencies, r4 and same-candidate R1 verified')
