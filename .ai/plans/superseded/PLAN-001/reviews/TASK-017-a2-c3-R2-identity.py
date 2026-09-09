"""R2-owned read-only identity audit; never invokes finalized review programs."""
from pathlib import Path
from datetime import datetime, UTC
import hashlib
import json
import os
import platform
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
TREE = ROOT / '.worktrees/TASK-017-a2'
PLAN = '.ai/plans/current/PLAN-001/'
REVIEWS = ROOT / (PLAN + 'reviews')
STEM = 'TASK-017-a2-c3-R2'
BASE = 'b90556d92e0f37e664d685b4af85c43fc8143d81'
HEAD = 'b7593f11961aa6f5c3a927f3c49af32c4fa93971'
OWNED = [PLAN+'evidence/implementation/TASK-017.md', 'src/agents.py', 'tests/unit/agents/test_agents.py']
sys.path.insert(0, str(TREE/'src'))
import agents, config, contracts, domain_values, workflow_ports

def sha(value):
    return hashlib.sha256(value).hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def git(*args, root=TREE):
    return subprocess.check_output(['git', '-C', str(root), *args])

def verify():
    manifest_path = PLAN+'reviews/candidates/CANDIDATE-TASK-017-a2-b7593f11961a.json'
    candidate = json.loads((ROOT/manifest_path).read_bytes())
    assert git('rev-parse', 'HEAD', root=ROOT).decode().strip() == BASE
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert not git('status', '--porcelain', '--untracked-files=all')
    assert git('merge-base', BASE, HEAD).decode().strip() == BASE
    assert candidate['base_oid'] == BASE and candidate['head_oid'] == HEAD
    diff = git('diff', '--binary', BASE, HEAD)
    assert sha(diff) == candidate['diff_sha256']
    assert git('diff', '--name-status', BASE, HEAD).decode().splitlines() == ['A\t'+p for p in OWNED]
    assert not git('diff', '--check', BASE, HEAD)
    # Each raw diff addition is exactly its committed source/test/handoff blob.
    for section, path in zip(diff.split(b'diff --git ')[1:], OWNED):
        body = section.split(b'@@', 2)[2].split(b'\n', 1)[1]
        restored = b''.join(line[1:] for line in body.splitlines(keepends=True) if line.startswith(b'+'))
        assert restored == git('show', HEAD+':'+path)
    for ref in candidate['context_refs']:
        assert sha(git('show', HEAD+':'+ref['path'])) == ref['sha256']
    validations = []
    for ref in candidate['validation_refs']:
        raw = (ROOT/ref['path']).read_bytes()
        assert sha(raw) == ref['sha256']
        assert HEAD in raw.decode() and 'Ran 29 tests' in raw.decode() and 'Exit code: 0' in raw.decode()
        validations.append(ref)
    settings = ['.ai/project/policy.json', '.ai/project/agent-models.json']
    assert sha(b''.join((ROOT/p).read_bytes() for p in settings)) == candidate['policy_model_digest']
    for p in settings:
        assert git('show', BASE+':'+p) == git('show', HEAD+':'+p)
        assert json.loads((ROOT/p).read_bytes()) == json.loads((TREE/p).read_bytes())
    assert sha(canonical({k:v for k,v in candidate.items() if k != 'fingerprint'})) == candidate['fingerprint'] == 'f2f7e852b8eb99345c66a959f15c842f5a2b046631f0b7d349377d3353fec5ac'
    tasks = [json.loads(p.read_bytes()) for p in (TREE/(PLAN+'tasks/current')).glob('TASK-*.json')]
    graph = json.loads((TREE/(PLAN+'graph.json')).read_bytes())
    isolation = json.loads((TREE/(PLAN+'reviews/r4-isolation-review.json')).read_bytes())
    task_digest = contracts.structural_task_digest(tasks)
    graph_digest = sha(canonical({k:graph[k] for k in ('schema_version','kind','id','plan_id','revision','nodes','task_set_sha256')}))
    assert task_digest == graph['task_set_sha256'] == isolation['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
    assert graph_digest == '5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
    assert isolation['verdict'] == 'pass' and isolation['graph_revision'] == graph['revision'] == 4
    by_id = {t['id']:t for t in tasks}
    assert len(tasks) == len(graph['nodes']) == 39
    for node in graph['nodes']:
        assert node['depends_on'] == by_id[node['task_id']]['depends_on']
    dependencies = {'TASK-003':('d51b72ce71ea3ac3ad31adf41e3eddc84738ac0b','src/workflow_ports.py'), 'TASK-004':('e3c1177f993ee74815639a83ef3333faa4ba3957','src/contracts.py'), 'TASK-038':('6f2b12c3283ed7d6e3d4876020fe690c6e0061a3','src/config.py')}
    for task,(oid,path) in dependencies.items():
        assert by_id[task]['status'] == 'accepted'
        assert git('show', oid+':'+path) == git('show', HEAD+':'+path) == git('show', BASE+':'+path)
        handoff = PLAN+'evidence/implementation/'+task+'.md'
        assert git('show', oid+':'+handoff) == git('show', HEAD+':'+handoff)
    assert not git('diff', BASE, HEAD, '--', 'schemas', '.ai/shared', '.ai/project', 'src/config.py', 'src/contracts.py', 'src/workflow_ports.py', 'src/domain_values.py')
    recovery = json.loads((ROOT/(PLAN+'evidence/recovery/TASK-017-recovery-assessment-verification.json.txt')).read_bytes())
    history = recovery['historical_files_unchanged']
    assert len(history) == 20
    for p,digest in history.items():
        checkpoint = '10e27db6472bbf6d9a5a5023233ede12fae5d52d' if '-c1-' in p else '8ebe9629f0eb7870933623af87cd10e93677dd4b'
        assert sha((ROOT/p).read_bytes()) == sha(git('show', checkpoint+':'+p)) == sha(git('show', BASE+':'+p)) == digest
    for name,digest in [('TASK-017-recovery-assessment.md.txt','64f3b3bfb6a0949efcd9a37741f8f84fc743d24ab751fec3c0c0a01139a83605'), ('TASK-017-recovery-assessment-verification.json.txt','814e4c7c567cba5477b9a91479b34dc3826a57c5df78126dd2ab946f0db0c3f0')]:
        assert sha((ROOT/(PLAN+'evidence/recovery/'+name)).read_bytes()) == digest
    pairs = [('71e0ccf697c132082bb17f7f3814ffb6abee5df6','ce1776adb42a06b5a02c7c7e7047e03c8a7f30c2'),('7e5bd5fd5d1b36a14cbee6ae911b68a4ec9ffbf8','3cdb41e5698f2cb0c7fc08c36c08d57a28ea1d16')]
    for original,salvage in pairs:
        assert git('diff', '--binary', original+'^', original) == git('diff', '--binary', salvage+'^', salvage)
        assert git('diff-tree', '--no-commit-id', '--name-only', '-r', salvage).decode().splitlines() == OWNED
    for p in OWNED:
        assert git('show', pairs[-1][1]+':'+p) == git('show', 'e79df3b8d071a7e3a3c7874cf0cacb6e704c0205:'+p)
        assert git('show', 'f5e21518f50e96b421ed68175d51acf253053a18:'+p) == git('show', HEAD+':'+p)
    r1 = json.loads((REVIEWS/'TASK-017-a2-c3-R1.json').read_bytes())
    registry = contracts.ContractRegistry(TREE/'schemas/v1')
    registry.validate(candidate)
    registry.validate(r1)
    assert r1['candidate_ref'] == manifest_path and r1['candidate_fingerprint'] == candidate['fingerprint']
    assert r1['verdict'] == 'pass' and not r1['findings']
    assert [c['id'] for c in r1['checks']] == [f'R1-{i:02}' for i in range(1,12)]
    assert all(c['status']=='pass' and c['evidence'] for c in r1['checks'])
    assert r1['reviewer']['capability_rank'] == 4 and r1['reviewer']['invocation_id']=='call_mI6rXNxVx2oywJ9qKRH8tyx7'
    assert r1['independent_session_id'] == '/root/review_017_c3_r1' and r1['implementation_session_id'] == '/root/implement_017_a2'
    r1_hashes = {p.name:sha(p.read_bytes()) for p in REVIEWS.glob('TASK-017-a2-c3-R1*')}
    for name,digest in re.findall(r'SHA256 (\S+): ([a-f0-9]{64})', (REVIEWS/'TASK-017-a2-c3-R1-final.txt').read_text()):
        assert r1_hashes[name] == digest
    for module in (agents,config,contracts,domain_values,workflow_ports):
        assert Path(module.__file__).resolve().parent == (TREE/'src').resolve()
    result = {'utc':datetime.now(UTC).isoformat(), 'runtime':sys.version, 'executable':sys.executable, 'platform':platform.platform(), 'root_head':BASE,'candidate_head':HEAD,'clean':True,'fingerprint':candidate['fingerprint'],'raw_diff_sha256':sha(diff),'raw_diff_lines':len(diff.splitlines()),'owned_paths':OWNED,'context_hashes_verified':len(candidate['context_refs']),'validation_refs':validations,'policy_model_digest':candidate['policy_model_digest'],'task_digest':task_digest,'graph_digest':graph_digest,'accepted_dependencies':dependencies,'salvage_pairs':pairs,'history_hashes':history,'r1_hashes':r1_hashes,'origins':{m.__name__:m.__file__ for m in (agents,config,contracts,domain_values,workflow_ports)}}
    (REVIEWS/(STEM+'-identity.json.txt')).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    argv = [sys.executable,'-B',*json.loads((TREE/(PLAN+'commands/test.TASK-017.json')).read_bytes())['argv'][1:]]
    run = subprocess.run(argv,cwd=TREE,env=dict(os.environ,PYTHONPATH=str(TREE/'src'),PYTHONDONTWRITEBYTECODE='1'),text=True,capture_output=True,shell=False)
    (REVIEWS/(STEM+'-declared.txt')).write_text(f'R2 independent declared suite: {argv}\nCwd: {TREE}\nRuntime: {sys.version}\nExit: {run.returncode}\n'+run.stdout+run.stderr,encoding='utf-8')
    assert run.returncode == 0 and 'Ran 29 tests' in run.stderr
    print('PASS identity, 14 contexts, 3 validation files, policy/fingerprint, 39-task/r4 digests, accepted dependency bytes, salvage, 20 history files, 9 immutable R1 files; declared suite 29 tests exit 0.')

if __name__ == '__main__':
    verify()
