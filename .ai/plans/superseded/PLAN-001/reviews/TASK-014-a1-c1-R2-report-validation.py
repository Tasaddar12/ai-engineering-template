"""Final report and freeze verification; no candidate writes."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
root = Path('D:/Codex Projects/ai-engineering-template')
tree = root / '.worktrees/TASK-014-a1'
plan = '.ai/plans/current/PLAN-001'
stem = f'{plan}/reviews/TASK-014-a1-c1-R2'
sys.path.insert(0, str(tree / 'src'))
from contracts import ContractRegistry
from jsonschema import Draft202012Validator, FormatChecker

def git(*args, cwd=tree):
    return subprocess.run(['git', *args], cwd=cwd, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, shell=False, check=True).stdout

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

report = json.loads((root / f'{stem}.json').read_text(encoding='utf-8'))
schema = json.loads((tree / 'schemas/v1/review-result.schema.json').read_text(encoding='utf-8'))
Draft202012Validator(schema, format_checker=FormatChecker()).validate(report)
registry = ContractRegistry(tree / 'schemas/v1')
registry.validate(report)
assert report['stage'] == 'consistency' and report['verdict'] == 'pass' and not report['findings']
assert [check['id'] for check in report['checks']] == [f'R2-{i:02d}' for i in range(1, 13)]
assert all(check['status'] == 'pass' and check['rationale'] and check['evidence'] for check in report['checks'])
assert report['review_1_ref'] == f'{plan}/reviews/TASK-014-a1-c1-R1.json'
r1_bytes = (root / report['review_1_ref']).read_bytes()
r1 = json.loads(r1_bytes)
assert sha(r1_bytes) == '2c5accc3c826a68861c3145df8becfdbfec5c998496192dd971d87c27cd3612a'
assert len({report['independent_session_id'], r1['independent_session_id'], report['implementation_session_id']}) == 3
assert report['reviewer']['invocation_id'] != r1['reviewer']['invocation_id']
assert report['request_id'] != r1['request_id']
assert report['reviewer']['capability_rank'] == 4
assert report['candidate_ref'] == r1['candidate_ref'] and report['candidate_fingerprint'] == r1['candidate_fingerprint']
for check in report['checks']:
    for ref in check['evidence']:
        assert (root / ref).is_file() or (tree / ref).is_file(), ref
candidate = json.loads((root / report['candidate_ref']).read_text(encoding='utf-8'))
canonical = json.dumps({k: v for k, v in candidate.items() if k != 'fingerprint'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
assert sha(canonical) == candidate['fingerprint'] == report['candidate_fingerprint']
for ref in candidate['context_refs']:
    assert sha(git('show', f"{candidate['head_oid']}:{ref['path']}")) == ref['sha256']
for ref in candidate['validation_refs']:
    assert sha((root / ref['path']).read_bytes()) == ref['sha256']
assert sha(b''.join((root / p).read_bytes() for p in ['.ai/project/policy.json', '.ai/project/agent-models.json'])) == candidate['policy_model_digest']
assert git('rev-parse', 'HEAD').decode().strip() == candidate['head_oid'] == '4bfad8611177959fb99eda01dd3c18077ff55f37'
assert git('rev-parse', 'HEAD', cwd=root).decode().strip() == candidate['base_oid'] == 'a0c6b0c2f8691e1280c1d1272c8124d6a98edaeb'
assert not git('status', '--porcelain=v1', '--untracked-files=all')
assert not git('diff', 'HEAD', '--name-only', cwd=root)
assert sha(git('diff', '--binary', candidate['base_oid'], candidate['head_oid'])) == candidate['diff_sha256']
print(datetime.datetime.now(datetime.timezone.utc).isoformat())
print('PASS review-result Draft 2020-12 schema with date-time format validation')
print('PASS accepted ContractRegistry validation')
print('PASS complete ordered R2-01 through R2-12, all pass, no findings')
print('PASS distinct R2/R1/implementation sessions, invocation/request identities and exact R1 binding')
print('PASS every checklist evidence reference exists')
print('PASS all candidate context, validation and policy/model hashes and canonical fingerprint')
print('PASS final unchanged R1, root/base/head freeze, clean candidate, root tracked tree and raw binary diff')
print('Report SHA256:', sha((root / f'{stem}.json').read_bytes()))
print('Review worktree access has ended after this validation; no candidate commands remain running.')
