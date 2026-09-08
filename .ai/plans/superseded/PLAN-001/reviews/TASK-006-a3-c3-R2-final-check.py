"""Final immutable report/schema, evidence and source freeze verification."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path('D:/Codex Projects/ai-engineering-template')
tree = root / '.worktrees/TASK-006-a3'
p = '.ai/plans/current/PLAN-001/'
stem = p + 'reviews/TASK-006-a3-c3-R2'
sys.dont_write_bytecode = True
sys.path.insert(0, str(tree / 'src'))
from contracts import ContractRegistry

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def git(*args, cwd=tree):
    return subprocess.check_output(['git', '-C', str(cwd), *args])

record = json.loads((root / (stem + '.json')).read_bytes())
registry = ContractRegistry(tree / 'schemas/v1')
registry.validate(record)
assert record['verdict'] == 'pass' and record['stage'] == 'consistency' and record['findings'] == []
assert [c['id'] for c in record['checks']] == [f'R2-{i:02}' for i in range(1, 13)]
assert all(c['status'] == 'pass' for c in record['checks'])
for check in record['checks']:
    for path in check['evidence']:
        assert (root / path).is_file() or (tree / path).is_file(), path
manifest = json.loads((root / record['candidate_ref']).read_bytes())
assert record['candidate_fingerprint'] == manifest['fingerprint']
assert sha(json.dumps({k: v for k, v in manifest.items() if k != 'fingerprint'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()) == manifest['fingerprint']
assert sha((root / '.ai/project/policy.json').read_bytes() + (root / '.ai/project/agent-models.json').read_bytes()) == manifest['policy_model_digest']
r1raw = (root / record['review_1_ref']).read_bytes()
assert sha(r1raw) == 'd0c2ac84ef47b71fd78972c75686c413b132800e6d02bba9cd7b394968c5db75'
r1 = json.loads(r1raw)
registry.validate(r1)
assert r1['verdict'] == 'pass' and r1['candidate_fingerprint'] == record['candidate_fingerprint']
assert len({record['independent_session_id'], r1['independent_session_id'], record['implementation_session_id']}) == 3
assert record['reviewer']['invocation_id'] == 'call_GbgJkuZJORydnqcmQ4L3Qc4B'
assert record['reviewer']['invocation_id'] != r1['reviewer']['invocation_id']
assert record['reviewer']['capability_rank'] == 4
for line in (root / (stem + '-identity.txt')).read_text(encoding='utf-8-sig').splitlines():
    if line.startswith('R1_COMPANION '):
        _, name, expected = line.split()
        assert sha((root / (p + 'reviews') / name).read_bytes()) == expected, name
assert git('rev-parse', 'HEAD').decode().strip() == manifest['head_oid'] == 'b41b37ac6b15ecbdfb55ed26bdc086686f4e9416'
assert git('rev-parse', 'HEAD', cwd=root).decode().strip() == manifest['base_oid'] == '10e27db6472bbf6d9a5a5023233ede12fae5d52d'
assert not git('status', '--porcelain=v1', '--untracked-files=all')
assert sha(git('diff', '--binary', manifest['base_oid'], manifest['head_oid'])) == manifest['diff_sha256']
assert sha((root / (stem + '-candidate.diff')).read_bytes()) == manifest['diff_sha256']
for ref in manifest['context_refs']:
    assert sha(git('show', manifest['head_oid'] + ':' + ref['path'])) == ref['sha256']
for ref in manifest['validation_refs']:
    assert sha((root / ref['path']).read_bytes()) == ref['sha256']
assert sha((tree / 'src/commands.py').read_bytes()) == '700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0'
assert sha((tree / 'tests/unit/commands/test_commands.py').read_bytes()) == 'c77171fefa9d43be13c4f06fe11dd49bc741caae267d6232578161248ff9952a'
print('PASS: frozen-v1 review-result schema; all12 consistency checks pass, no findings; all references exist.')
print('PASS: distinct R2/R1/implementation sessions and native calls, applicable same-fingerprint R1 and every retained R1 companion unchanged.')
print('PASS: clean exact candidate and frozen ROOT base; source/test bytes, raw diff, every context/validation hash, policy/model digest and fingerprint unchanged.')
for file in sorted((root / (p + 'reviews')).glob('TASK-006-a3-c3-R2*')):
    if file.is_file() and file.name != 'TASK-006-a3-c3-R2-final-check.txt':
        print(sha(file.read_bytes()), file.name)
print('PASS: review finalized. All candidate access stops before FINAL; coordinator owns integration.')
