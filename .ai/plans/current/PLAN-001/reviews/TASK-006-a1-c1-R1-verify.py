"""Independent R1 identity and declared-suite reproduction; candidate stays read-only."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-006-a1'
STEM = Path(__file__).with_name('TASK-006-a1-c1-R1')
MODE = sys.argv[1]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args, cwd=TREE):
    return subprocess.check_output(['git', *args], cwd=cwd)

if MODE == 'identity':
    candidate = json.loads((ROOT / '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-006-a1-64a48f6bde98.json').read_bytes())
    lines = []
    def record(name, value):
        lines.append(f'{name}: {value}')
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == candidate['base_oid']
    assert git('rev-parse', 'HEAD').decode().strip() == candidate['head_oid']
    assert git('status', '--porcelain', '--untracked-files=all') == b''
    assert git('merge-base', candidate['base_oid'], candidate['head_oid']).decode().strip() == candidate['base_oid']
    record('root_head', candidate['base_oid'])
    record('candidate_head_clean', candidate['head_oid'])
    diff = git('diff', '--binary', candidate['base_oid'], candidate['head_oid'])
    assert sha(diff) == candidate['diff_sha256']
    record('diff_sha256', sha(diff))
    STEM.with_name(STEM.name + '-candidate.diff').write_bytes(diff)
    changes = git('diff', '--name-status', candidate['base_oid'], candidate['head_oid']).decode()
    record('changed_paths', '\n' + changes.strip())
    allowed = {'src/commands.py', 'tests/unit/commands/test_commands.py', '.ai/plans/current/PLAN-001/evidence/implementation/TASK-006.md'}
    assert set(git('diff', '--name-only', candidate['base_oid'], candidate['head_oid']).decode().splitlines()) == allowed
    assert git('diff', '--check', candidate['base_oid'], candidate['head_oid']) == b''
    for ref in candidate['context_refs']:
        actual = sha(git('show', f"{candidate['head_oid']}:{ref['path']}"))
        assert actual == ref['sha256'], ref
        record('context_verified', ref['path'] + ' ' + actual)
    for ref in candidate['validation_refs']:
        data = (ROOT / ref['path']).read_bytes()
        assert sha(data) == ref['sha256']
        record('validation_verified', ref['path'] + ' ' + sha(data))
    digest = sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes())
    assert digest == candidate['policy_model_digest']
    record('policy_model_digest', digest)
    fingerprint = candidate.pop('fingerprint')
    assert sha(json.dumps(candidate, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == fingerprint
    record('candidate_fingerprint', fingerprint)
    sys.path.insert(0, str(TREE / 'src'))
    from contracts import structural_task_digest
    plan = TREE / '.ai/plans/current/PLAN-001'
    tasks = [json.loads(p.read_bytes()) for p in (plan / 'tasks/current').glob('*.json')]
    graph = json.loads((plan / 'graph.json').read_bytes())
    isolation = json.loads((ROOT / '.ai/plans/current/PLAN-001/reviews/r4-isolation-review.json').read_bytes())
    task_digest = structural_task_digest(tasks)
    assert task_digest == graph['task_set_sha256'] == isolation['task_set_sha256']
    assert isolation['verdict'] == 'pass' and isolation['graph_revision'] == 4
    record('graph_and_isolation', f'39 tasks; r4; {task_digest}; pass')
    for dependency, oid in [('TASK-002','460ab567d01912167557f2f671ed07c63f0a31e7'), ('TASK-004','e3c1177f993ee74815639a83ef3333faa4ba3957'), ('TASK-038','6f2b12c3283ed7d6e3d4876020fe690c6e0061a3')]:
        assert subprocess.run(['git','merge-base','--is-ancestor',oid,candidate['base_oid']],cwd=TREE).returncode == 0
        task = json.loads((plan / f'tasks/current/{dependency}.json').read_bytes())
        record('dependency', f'{dependency} {oid} is ancestor of current base; status={task["status"]}')
    output = '\n'.join(lines) + '\nIDENTITY PASS\n'
    STEM.with_name(STEM.name + '-identity.txt').write_text(output, encoding='utf-8')
    print(output)
elif MODE == 'suite':
    platform = 'windows' if os.name == 'nt' else 'linux'
    definition = json.loads((TREE / '.ai/plans/current/PLAN-001/commands/test.TASK-006.json').read_bytes())
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    args = [sys.executable, *definition['argv'][1:]]
    result = subprocess.run(args, cwd=TREE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
    sys.path.insert(0, str(TREE / 'src'))
    import commands, config, contracts, local_ports
    origins = '\n'.join(f'{m.__name__}: {m.__file__}' for m in [commands, config, contracts, local_ports])
    header = f'platform={sys.platform}\ninterpreter={sys.executable}\ncwd={TREE}\nargv={args!r}\n{origins}\nexit_code={result.returncode}\n'
    STEM.with_name(STEM.name + f'-suite-{platform}.txt').write_bytes(header.encode() + result.stdout)
    print(header + result.stdout.decode(errors='replace'))
    raise SystemExit(result.returncode)
else:
    raise ValueError(MODE)
