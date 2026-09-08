"""Independent cycle-2 identity verification and exact declared suite launcher."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-006-a1'
STEM = Path(__file__).with_name('TASK-006-a1-c2-R1')
REF = '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-006-a1-ce4c8edb86b0.json'
EXPECTED = '7578a4d2cd986e5b69e7a6e0a6938d279aef2056be4f6130d7e17dccbb89cae4'

def git(*args, cwd=TREE):
    # The worktree was created by Windows Git; its .git pointer is a Windows path.
    # WSL needs an explicit read-only repository binding, without editing that pointer.
    prefix = ['git']
    if os.name != 'nt' and cwd == TREE:
        prefix.extend(['--git-dir=' + str(ROOT / '.git/worktrees/TASK-006-a1'), '--work-tree=' + str(TREE)])
    return subprocess.check_output([*prefix, *args], cwd=cwd)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify_head():
    c = json.loads((ROOT / REF).read_bytes())
    assert c['fingerprint'] == EXPECTED
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == c['base_oid']
    assert git('rev-parse', 'HEAD').decode().strip() == c['head_oid']
    assert not git('status', '--porcelain', '--untracked-files=all')
    return c

if sys.argv[1] == 'identity':
    c = verify_head()
    facts = {'candidate_ref': REF, 'base': c['base_oid'], 'head': c['head_oid'], 'clean': True}
    assert git('merge-base', c['base_oid'], c['head_oid']).decode().strip() == c['base_oid']
    diff = git('diff', '--binary', c['base_oid'], c['head_oid'])
    assert sha(diff) == c['diff_sha256']
    STEM.with_name(STEM.name + '-candidate.diff').write_bytes(diff)
    facts['diff_sha256'] = sha(diff)
    allowed = {'src/commands.py', 'tests/unit/commands/test_commands.py', '.ai/plans/current/PLAN-001/evidence/implementation/TASK-006.md'}
    assert set(git('diff', '--name-only', c['base_oid'], c['head_oid']).decode().splitlines()) == allowed
    facts['changed_paths'] = git('diff', '--name-status', c['base_oid'], c['head_oid']).decode().splitlines()
    assert not git('diff', '--check', c['base_oid'], c['head_oid'])
    facts['context_refs'] = []
    for ref in c['context_refs']:
        assert sha(git('show', c['head_oid'] + ':' + ref['path'])) == ref['sha256']
        facts['context_refs'].append(ref)
    facts['validation_refs'] = []
    for ref in c['validation_refs']:
        assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256']
        facts['validation_refs'].append(ref)
    policy_digest = sha(b''.join((ROOT / ('.ai/project/' + name)).read_bytes() for name in ['policy.json', 'agent-models.json']))
    assert policy_digest == c['policy_model_digest']
    facts['policy_model_digest'] = policy_digest
    content = {k: v for k, v in c.items() if k != 'fingerprint'}
    assert sha(json.dumps(content, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == EXPECTED
    facts['fingerprint'] = EXPECTED
    sys.path.insert(0, str(TREE / 'src'))
    from contracts import ContractRegistry, structural_task_digest
    plan = TREE / '.ai/plans/current/PLAN-001'
    tasks = [json.loads(p.read_bytes()) for bucket in ('current','completed','archived') for p in (plan / 'tasks' / bucket).glob('*.json')]
    assert len(tasks) == 39
    graph = json.loads((plan / 'graph.json').read_bytes())
    iso = json.loads((plan / 'reviews/r4-isolation-review.json').read_bytes())
    digest = structural_task_digest(tasks)
    assert digest == graph['task_set_sha256'] == iso['task_set_sha256']
    assert iso['verdict'] == 'pass' and graph['revision'] == iso['graph_revision'] == 4
    projection = {k: graph[k] for k in ('schema_version','kind','id','plan_id','revision','nodes','task_set_sha256')}
    graph_digest = sha(json.dumps(projection, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
    assert graph_digest == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
    facts['graph'] = {'revision': 4, 'task_count':len(tasks), 'task_digest':digest, 'structural_graph_digest':graph_digest, 'isolation':'pass'}
    facts['accepted_dependencies'] = []
    for name, oid in [('TASK-002','460ab567d01912167557f2f671ed07c63f0a31e7'),('TASK-004','e3c1177f993ee74815639a83ef3333faa4ba3957'),('TASK-038','6f2b12c3283ed7d6e3d4876020fe690c6e0061a3')]:
        subprocess.run(['git','merge-base','--is-ancestor',oid,c['base_oid']],cwd=TREE,check=True)
        task = next(t for t in tasks if t['id'] == name)
        assert task['status'] == 'accepted'
        facts['accepted_dependencies'].append({'task':name,'candidate':oid,'status':task['status'],'base_ancestor':True})
    registry = ContractRegistry(TREE / 'schemas/v1')
    registry.validate(c)
    facts['result'] = 'PASS'
    output = json.dumps(facts, indent=2) + '\n'
    STEM.with_name(STEM.name + '-identity.txt').write_text(output, encoding='utf-8')
    print(output)
elif sys.argv[1] == 'suite':
    c = verify_head()
    sys.path.insert(0, str(TREE / 'src'))
    import commands, config, contracts, local_ports
    origins = {m.__name__: str(Path(m.__file__).resolve()) for m in (commands, config, contracts, local_ports)}
    assert all(Path(p).parent == TREE / 'src' for p in origins.values())
    definition = json.loads((TREE / '.ai/plans/current/PLAN-001/commands/test.TASK-006.json').read_bytes())
    argv = [sys.executable, *definition['argv'][1:]]
    result = subprocess.run(argv, cwd=TREE, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    body = result.stdout.decode(errors='replace')
    count = re.search(r'Ran (\d+) tests?', body)
    skipped = re.search(r'OK \(skipped=(\d+)\)', body)
    facts = {'head':c['head_oid'], 'platform':sys.platform, 'python':sys.version, 'cwd':str(TREE), 'argv':argv, 'origins':origins, 'exit_code':result.returncode, 'discovered':int(count[1]) if count else 0, 'skipped':int(skipped[1]) if skipped else 0}
    facts['executed'] = facts['discovered'] - facts['skipped']
    output = json.dumps(facts, indent=2) + '\n' + body
    suffix = '-suite-' + ('windows' if os.name == 'nt' else 'linux') + '.txt'
    STEM.with_name(STEM.name + suffix).write_text(output, encoding='utf-8')
    print(output)
    assert result.returncode == 0 and facts['executed'] > 0
    verify_head()
else:
    raise ValueError(sys.argv[1])
