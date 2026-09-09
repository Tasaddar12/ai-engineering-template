"""Independent R1 identity/evidence verification; candidate is read-only."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('D:/Codex Projects/ai-engineering-template')
CANDIDATE = ROOT / '.worktrees/TASK-006-a3'
PLAN = '.ai/plans/current/PLAN-001/'
BASE = '10e27db6472bbf6d9a5a5023233ede12fae5d52d'
HEAD = 'b41b37ac6b15ecbdfb55ed26bdc086686f4e9416'
A2 = '4fe9e7a30378e13b43dc51745593adae2bb8b051'
sys.dont_write_bytecode = True
sys.path.insert(0, str(CANDIDATE / 'src'))
from contracts import ContractRegistry, structural_task_digest

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(CANDIDATE), *args])

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

candidate_path = PLAN + 'reviews/candidates/CANDIDATE-TASK-006-a3-b41b37ac6b15.json'
manifest = json.loads((ROOT / candidate_path).read_bytes())
ContractRegistry(CANDIDATE / 'schemas/v1').validate(manifest)
assert git('rev-parse', 'HEAD').decode().strip() == HEAD == manifest['head_oid']
assert manifest['base_oid'] == BASE
assert not git('status', '--porcelain=v1', '--untracked-files=all')
assert git('merge-base', BASE, HEAD).decode().strip() == BASE
assert subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD']).decode().strip() == BASE
diff = git('diff', '--binary', BASE, HEAD)
assert sha(diff) == manifest['diff_sha256']
git('diff', '--check', BASE, HEAD)
changed = git('diff', '--name-only', BASE, HEAD).decode().splitlines()
assert sorted(changed) == sorted([PLAN + 'evidence/implementation/TASK-006.md', 'src/commands.py', 'tests/unit/commands/test_commands.py'])
print(json.dumps({'base': BASE, 'head': HEAD, 'clean': True, 'diff_bytes': len(diff), 'diff_sha256': sha(diff), 'changed_paths': changed}, sort_keys=True))
for ref in manifest['context_refs']:
    actual = sha(git('show', HEAD + ':' + ref['path']))
    assert actual == ref['sha256'], ref['path']
    print('CONTEXT ' + ref['path'] + ' ' + actual)
for ref in manifest['validation_refs']:
    raw = (ROOT / ref['path']).read_bytes()
    assert sha(raw) == ref['sha256'], ref['path']
    log = raw.decode('utf-8-sig')
    assert 'Head: ' + HEAD in log
    assert 'Exit code: 0' in log and 'Runtime/origin probe exit: 0' in log
    assert 'jsonschema: 4.26.0' in log and 'TASK-006-a3/src/commands.py' in log
    assert 'Ran 22 tests' in log and 'OK (skipped=1)' in log
    phases = [json.loads(line.split('TASK-006-FIXTURE ', 1)[1]) for line in log.splitlines() if line.startswith('TASK-006-FIXTURE ')]
    assert len(phases) == 4
    assert {(p['phase'], p['mode']) for p in phases} == {(p, m) for p in ('detached_while_parent_live', 'inherited_after_parent_exit') for m in ('timeout', 'cancellation')}
    for p in phases:
        assert p['parent_pid'] > 0 and p['child_pid'] > 0
        assert p['parent_gone'] and p['child_gone'] and p['reader_threads_settled']
        assert not p['watchdog_intervened'] and p['native_termination_calls'] == 1
        assert 0 <= p['startup_seconds'] < 3 and 0 <= p['overall_seconds'] < 4
        assert p['cancellation_observed'] == (p['mode'] == 'cancellation')
        if p['mode'] == 'cancellation':
            assert 0 <= p['cancellation_response_seconds'] < 3
        if 'linux' in ref['path']:
            if p['phase'] == 'inherited_after_parent_exit':
                assert p['child_process_group'] == p['parent_process_group']
            else:
                assert p['child_process_group'] != p['parent_process_group']
                assert p['child_session'] != p['parent_session']
    print('VALIDATION ' + ref['path'] + ' ' + sha(raw))
    print('\n'.join(line for line in log.splitlines() if line.startswith(('Python:', 'Executable:', 'Platform:', 'Origins:', 'Ran '))))
    print('PHASES ' + json.dumps(phases, sort_keys=True))
policy = (ROOT / '.ai/project/policy.json').read_bytes()
models = (ROOT / '.ai/project/agent-models.json').read_bytes()
assert sha(policy + models) == manifest['policy_model_digest']
for p in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
    assert json.loads((ROOT / p).read_bytes()) == json.loads((CANDIDATE / p).read_bytes())
    assert subprocess.check_output(['git', '-C', str(ROOT), 'show', BASE + ':' + p]) == git('show', HEAD + ':' + p)
identity = dict(manifest)
identity.pop('fingerprint')
assert sha(canonical(identity)) == manifest['fingerprint'] == '3df5453edcaf80c6237f35c5ca1c5adb81adfb9682cae3af95e25091d2435e80'
print('POLICY_MODEL ' + manifest['policy_model_digest'])
print('FINGERPRINT ' + manifest['fingerprint'])
for path, blob, digest in [('src/commands.py', '39828108eb7d198d81d810c8fd9e136e3f64f8f0', '700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0'), ('tests/unit/commands/test_commands.py', '7bf8228bb4105e72b9f711d9f4e4bf1fc3c2377a', 'c77171fefa9d43be13c4f06fe11dd49bc741caae267d6232578161248ff9952a')]:
    assert git('rev-parse', HEAD + ':' + path).decode().strip() == blob
    assert sha((CANDIDATE / path).read_bytes()) == digest
    print('FROZEN ' + path + ' ' + blob + ' ' + digest)
patch = git('diff', '--binary', A2, HEAD, '--', 'tests/unit/commands/test_commands.py')
assert len(patch) == 2100 and sha(patch) == 'dd19ecadc3cac20102165a206d94b6d8bea4db64eb0e06f91c455af7303f1c6e'
assert git('rev-parse', A2 + ':src/commands.py') == git('rev-parse', HEAD + ':src/commands.py')
for path in changed:
    assert git('show', '2488fc3f63f34154f037e81690b719b28745308c:' + path) == git('show', A2 + ':' + path)
print('A2_ASSERTION_DIFF bytes=2100 sha256=' + sha(patch) + '; post-salvage three paths equal a2')
graph = json.loads((CANDIDATE / (PLAN + 'graph.json')).read_bytes())
isolation = json.loads((CANDIDATE / (PLAN + 'reviews/r4-isolation-review.json')).read_bytes())
tasks = [json.loads(p.read_bytes()) for p in (CANDIDATE / (PLAN + 'tasks/current')).glob('TASK-*.json')]
digest = structural_task_digest(tasks)
assert len(tasks) == 39 and graph['revision'] == isolation['graph_revision'] == 4
assert graph['status'] == 'approved' and isolation['verdict'] == 'pass'
assert digest == graph['task_set_sha256'] == isolation['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
projection = {key: graph[key] for key in ('schema_version', 'kind', 'id', 'plan_id', 'revision', 'nodes', 'task_set_sha256')}
assert sha(canonical(projection)) == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
for task, oid in [('TASK-002', '460ab567d01912167557f2f671ed07c63f0a31e7'), ('TASK-004', 'e3c1177f993ee74815639a83ef3333faa4ba3957'), ('TASK-038', '6f2b12c3283ed7d6e3d4876020fe690c6e0061a3')]:
    subprocess.run(['git', '-C', str(CANDIDATE), 'merge-base', '--is-ancestor', oid, BASE], check=True)
    assert next(t for t in tasks if t['id'] == task)['status'] == 'accepted'
    print('DEPENDENCY ' + task + ' accepted ancestor ' + oid)
print('ISOLATION task_digest=' + digest + ' structural_graph=' + sha(canonical(projection)))
print('PASS: all identity, scope, salvage, context, validation, policy/model and approval checks')
