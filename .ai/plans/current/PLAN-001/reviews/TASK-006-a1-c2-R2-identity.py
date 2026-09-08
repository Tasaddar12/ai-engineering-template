"""Read-only exact-candidate verification; Windows Git preserves worktree binding."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-006-a1'
PREFIX = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-006-a1-c2-R2'
REF = '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-006-a1-ce4c8edb86b0.json'
R1REF = '.ai/plans/current/PLAN-001/reviews/TASK-006-a1-c2-R1.json'
BASE = '3acfcb0d700b05fbf78233b575e77db556cd9bcc'
HEAD = 'ce4c8edb86b02268a856a5f870932ade0e7e9b91'
sys.path.insert(0, str(TREE / 'src'))
from contracts import ContractRegistry, structural_task_digest

def git(*args, cwd=TREE):
    return subprocess.check_output(['git', *args], cwd=cwd, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})

def sha(value):
    return hashlib.sha256(value).hexdigest()

def main():
    candidate = json.loads((ROOT / REF).read_bytes())
    registry = ContractRegistry(TREE / 'schemas/v1')
    registry.validate(candidate)
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert candidate['base_oid'] == BASE and candidate['head_oid'] == HEAD
    assert git('merge-base', BASE, HEAD).decode().strip() == BASE
    assert not git('status', '--porcelain=v1', '--untracked-files=all')
    print('PASS exact ROOT head/base, candidate HEAD, merge-base and clean worktree:', BASE, HEAD)
    diff = git('diff', '--binary', BASE, HEAD)
    assert sha(diff) == candidate['diff_sha256']
    Path(str(PREFIX) + '-candidate.diff').write_bytes(diff)
    paths = git('diff', '--name-only', BASE, HEAD).decode().splitlines()
    assert set(paths) == {'src/commands.py', 'tests/unit/commands/test_commands.py', '.ai/plans/current/PLAN-001/evidence/implementation/TASK-006.md'}
    print('PASS raw binary diff:', sha(diff), '; paths:', paths)
    for ref in candidate['context_refs']:
        raw = git('show', HEAD + ':' + ref['path'])
        assert sha(raw) == ref['sha256'], ref
        print('PASS context', ref['path'], sha(raw))
    for ref in candidate['validation_refs']:
        raw = (ROOT / ref['path']).read_bytes()
        assert sha(raw) == ref['sha256'], ref
        assert HEAD.encode() in raw and b'Ran 22 tests' in raw and b'OK (skipped=1)' in raw
        print('PASS validation', ref['path'], sha(raw), '22 discovered / 21 executed / 1 skip')
    policy = (ROOT / '.ai/project/policy.json').read_bytes()
    models = (ROOT / '.ai/project/agent-models.json').read_bytes()
    assert sha(policy + models) == candidate['policy_model_digest']
    for path in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
        assert git('show', BASE + ':' + path) == git('show', HEAD + ':' + path)
        assert json.loads((ROOT / path).read_bytes()) == json.loads((TREE / path).read_bytes())
    print('PASS policy/model digest and unchanged committed/equivalent working values:', sha(policy + models))
    digest_input = {k: v for k, v in candidate.items() if k != 'fingerprint'}
    digest = sha(json.dumps(digest_input, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
    assert digest == candidate['fingerprint'] == '7578a4d2cd986e5b69e7a6e0a6938d279aef2056be4f6130d7e17dccbb89cae4'
    print('PASS canonical fingerprint:', digest)
    graph = json.loads((TREE / '.ai/plans/current/PLAN-001/graph.json').read_bytes())
    tasks = [json.loads(p.read_bytes()) for p in sorted((TREE / '.ai/plans/current/PLAN-001/tasks/current').glob('TASK-*.json'))]
    isolation = json.loads((TREE / '.ai/plans/current/PLAN-001/reviews/r4-isolation-review.json').read_bytes())
    structural = structural_task_digest(tasks)
    assert graph['revision'] == candidate['graph_revision'] == isolation['graph_revision'] == 4
    assert graph['status'] == 'approved' and isolation['verdict'] == 'pass'
    assert structural == graph['task_set_sha256'] == isolation['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
    print('PASS approved graph revision/39-task digest:', structural, '; graph keys:', list(graph))
    task_map = {x['id']: x for x in tasks}
    for task_id, oid, source in (
        ('TASK-002', '460ab567d01912167557f2f671ed07c63f0a31e7', 'src/local_ports.py'),
        ('TASK-004', 'e3c1177f993ee74815639a83ef3333faa4ba3957', 'src/contracts.py'),
        ('TASK-038', '6f2b12c3283ed7d6e3d4876020fe690c6e0061a3', 'src/config.py'),
    ):
        assert task_map[task_id]['status'] == 'accepted'
        git('merge-base', '--is-ancestor', oid, BASE)
        assert git('show', oid + ':' + source) == git('show', HEAD + ':' + source)
        handoff = '.ai/plans/current/PLAN-001/evidence/implementation/' + task_id + '.md'
        assert git('show', oid + ':' + handoff) == git('show', HEAD + ':' + handoff)
        print('PASS accepted dependency source/handoff unchanged:', task_id, oid, source)
    assert not git('diff', '--name-only', BASE, HEAD, '--', 'schemas/v1', 'src/domain_values.py', 'src/local_ports.py', 'src/config.py', 'src/contracts.py', 'src/workflow_ports.py')
    r1 = json.loads((ROOT / R1REF).read_bytes())
    registry.validate(r1)
    assert r1['verdict'] == 'pass' and r1['stage'] == 'implementation'
    assert r1['candidate_ref'] == REF and r1['candidate_fingerprint'] == digest
    assert {c['id'] for c in r1['checks']} == {f'R1-{i:02}' for i in range(1, 12)}
    assert all(c['status'] == 'pass' for c in r1['checks'])
    assert all(f['resolved'] for f in r1['findings'])
    assert r1['independent_session_id'] == '/root/r1_006_c2'
    assert r1['implementation_session_id'] == '/root/implement_006'
    for check in r1['checks']:
        for ref in check['evidence']:
            assert (ROOT / ref).is_file() or (TREE / ref).is_file(), ref
    print('PASS same-candidate R1 exact reference:', R1REF, '; JSON sha256:', sha((ROOT / R1REF).read_bytes()))
    print('PASS distinct R2 /root/r2_006_c2; native submitted Astra/xhigh rank4; provider confirmation unavailable; implementer Sol/xhigh rank3')
    print('PASS final candidate clean:', not git('status', '--porcelain=v1', '--untracked-files=all'))

if __name__ == '__main__':
    main()
