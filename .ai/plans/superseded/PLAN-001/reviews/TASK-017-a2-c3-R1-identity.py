"""Independent, read-only candidate/salvage verification; writes only R1 evidence."""
from __future__ import annotations
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, UTC
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-017-a2'
OUT = Path(__file__).with_suffix('.txt')
PREFIX = '.ai/plans/current/PLAN-001/'
BASE = 'b90556d92e0f37e664d685b4af85c43fc8143d81'
HEAD = 'b7593f11961aa6f5c3a927f3c49af32c4fa93971'
OWNED = ['.ai/plans/current/PLAN-001/evidence/implementation/TASK-017.md', 'src/agents.py', 'tests/unit/agents/test_agents.py']
sys.path.insert(0, str(TREE / 'src'))
import agents, config, contracts, domain_values, workflow_ports

def git(*args, tree=TREE):
    return subprocess.check_output(['git', '-C', str(tree), *args])

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def verify():
    log = [f'UTC {datetime.now(UTC).isoformat()}', f'Runtime {sys.version}; executable={sys.executable}; platform={platform.platform()}; jsonschema={version("jsonschema")}']
    manifest = json.loads((ROOT / (PREFIX + 'reviews/candidates/CANDIDATE-TASK-017-a2-b7593f11961a.json')).read_bytes())
    assert git('rev-parse', 'HEAD', tree=ROOT).decode().strip() == BASE
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert not git('status', '--porcelain')
    assert git('merge-base', BASE, HEAD).decode().strip() == BASE
    assert manifest['base_oid'] == BASE and manifest['head_oid'] == HEAD
    diff = git('diff', '--binary', BASE, HEAD)
    assert sha(diff) == manifest['diff_sha256']
    changes = git('diff', '--name-status', BASE, HEAD).decode().splitlines()
    assert changes == ['A\t' + path for path in OWNED]
    assert subprocess.run(['git', '-C', str(TREE), 'diff', '--check', BASE, HEAD], capture_output=True).returncode == 0
    log += [f'PASS exact clean head={HEAD}; frozen merge-base={BASE}', f'PASS raw binary diff SHA256={sha(diff)}; changed paths={changes}']
    for group in ('context_refs', 'validation_refs'):
        for ref in manifest[group]:
            raw = git('show', HEAD + ':' + ref['path']) if group == 'context_refs' else (ROOT / ref['path']).read_bytes()
            assert sha(raw) == ref['sha256'], ref
        log.append(f'PASS {len(manifest[group])} {group} raw hashes')
    settings_paths = ['.ai/project/policy.json', '.ai/project/agent-models.json']
    digest = sha(b''.join((ROOT / path).read_bytes() for path in settings_paths))
    assert digest == manifest['policy_model_digest']
    for path in settings_paths:
        assert git('show', BASE + ':' + path) == git('show', HEAD + ':' + path)
        assert json.loads((ROOT / path).read_bytes()) == json.loads((TREE / path).read_bytes())
    content = {k:v for k,v in manifest.items() if k != 'fingerprint'}
    assert sha(canonical(content)) == manifest['fingerprint'] == 'f2f7e852b8eb99345c66a959f15c842f5a2b046631f0b7d349377d3353fec5ac'
    log += [f'PASS raw policy/model digest={digest}', f'PASS canonical fingerprint={manifest["fingerprint"]}']
    task_dir = TREE / (PREFIX + 'tasks/current')
    tasks = [json.loads(p.read_bytes()) for p in task_dir.glob('TASK-*.json')]
    graph = json.loads((TREE / (PREFIX + 'graph.json')).read_bytes())
    isolation = json.loads((TREE / (PREFIX + 'reviews/r4-isolation-review.json')).read_bytes())
    task_digest = contracts.structural_task_digest(tasks)
    assert task_digest == isolation['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
    assert isolation['verdict'] == 'pass' and graph['revision'] == isolation['graph_revision'] == 4
    by_id = {t['id']:t for t in tasks}
    assert len(tasks) == len(graph['nodes']) == 39
    for node in graph['nodes']:
        assert node['depends_on'] == by_id[node['task_id']]['depends_on']
    for dependency in ('TASK-003', 'TASK-004', 'TASK-038'):
        assert by_id[dependency]['status'] == 'accepted'
    for path in ('src/workflow_ports.py', 'src/contracts.py', 'src/config.py', 'src/domain_values.py'):
        assert git('show', BASE + ':' + path) == git('show', HEAD + ':' + path)
    log.append(f'PASS graph r4 / 39-node dependencies / accepted 003,004,038 / unchanged prerequisite sources / task digest={task_digest}')
    recovery = json.loads((ROOT / (PREFIX + 'evidence/recovery/TASK-017-recovery-assessment-verification.json.txt')).read_bytes())
    assert len(recovery['historical_files_unchanged']) == 20
    for path, digest in recovery['historical_files_unchanged'].items():
        checkpoint = '10e27db6472bbf6d9a5a5023233ede12fae5d52d' if '-c1-' in path else '8ebe9629f0eb7870933623af87cd10e93677dd4b'
        assert sha((ROOT / path).read_bytes()) == sha(git('show', BASE + ':' + path)) == sha(git('show', checkpoint + ':' + path)) == digest, path
    for name,digest in [('TASK-017-recovery-assessment.md.txt','64f3b3bfb6a0949efcd9a37741f8f84fc743d24ab751fec3c0c0a01139a83605'),('TASK-017-recovery-assessment-verification.json.txt','814e4c7c567cba5477b9a91479b34dc3826a57c5df78126dd2ab946f0db0c3f0')]:
        assert sha((ROOT / (PREFIX + 'evidence/recovery/' + name)).read_bytes()) == digest
    assert not list((ROOT / (PREFIX+'reviews')).glob('TASK-017*R2.json'))
    log.append('PASS 20 historical review companions byte-identical to original preservation checkpoints and frozen ROOT; packaged original recovery hashes; zero TASK-017 R2')
    pairs = [('71e0ccf697c132082bb17f7f3814ffb6abee5df6','ce1776adb42a06b5a02c7c7e7047e03c8a7f30c2'),('7e5bd5fd5d1b36a14cbee6ae911b68a4ec9ffbf8','3cdb41e5698f2cb0c7fc08c36c08d57a28ea1d16')]
    for original,salvage in pairs:
        for commit in (original,salvage):
            assert len(git('rev-list','--parents','-n','1',commit).split()) == 2
            assert git('diff-tree','--no-commit-id','--name-only','-r',commit).decode().splitlines() == OWNED
        assert git('diff','--binary',original+'^',original) == git('diff','--binary',salvage+'^',salvage)
        log.append(f'PASS exact owned patch salvage {original} -> {salvage}')
    assert git('rev-parse',pairs[0][1]+'^').decode().strip() == '8a4d789090f8a2f51be1be9c947470f82e21ef81'
    assert git('rev-parse',pairs[1][1]+'^').decode().strip() == pairs[0][1]
    for path in OWNED:
        assert git('show',pairs[1][1]+':'+path) == git('show','e79df3b8d071a7e3a3c7874cf0cacb6e704c0205:'+path)
        assert git('show','f5e21518f50e96b421ed68175d51acf253053a18:'+path) == git('show',HEAD+':'+path)
    log.append('PASS all three pre-correction salvage blobs equal frozen unaccepted a1; final owner blobs equal current-base candidate')
    for module in (agents, config, contracts, domain_values, workflow_ports):
        assert Path(module.__file__).resolve().parent == (TREE/'src').resolve()
        log.append(f'Origin {module.__name__}={module.__file__}')
    if '--suite' in sys.argv:
        command = json.loads((TREE / (PREFIX + 'commands/test.TASK-017.json')).read_bytes())
        argv = [sys.executable, '-B', *command['argv'][1:]]
        env = dict(os.environ, PYTHONPATH=str(TREE/'src'), PYTHONDONTWRITEBYTECODE='1')
        run = subprocess.run(argv, cwd=TREE, env=env, capture_output=True, text=True, shell=False)
        log += [f'Declared argv={argv}; cwd={TREE}; exit={run.returncode}', run.stdout, run.stderr]
        assert run.returncode == 0 and 'Ran 29 tests' in run.stderr
    OUT.write_text('\n'.join(log)+'\n', encoding='utf-8')
    print('\n'.join(log))

if __name__ == '__main__':
    verify()
