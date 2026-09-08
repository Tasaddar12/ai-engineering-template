"""Final schema, report consistency and candidate freeze verification."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path('D:/Codex Projects/ai-engineering-template')
CANDIDATE = ROOT / '.worktrees/TASK-006-a3'
REVIEW = ROOT / '.ai/plans/current/PLAN-001/reviews'
STEM = 'TASK-006-a3-c3-R1'
sys.dont_write_bytecode = True
sys.path.insert(0, str(CANDIDATE / 'src'))
from contracts import ContractRegistry
registry = ContractRegistry(CANDIDATE / 'schemas/v1')
report = json.loads((REVIEW / (STEM + '.json')).read_bytes())
registry.validate(report, source=STEM)
assert [c['id'] for c in report['checks']] == ['R1-%02d' % n for n in range(1, 12)]
assert all(c['status'] == 'pass' for c in report['checks'])
assert report['verdict'] == 'pass' and not report['findings']
assert report['reviewer']['invocation_id'] == 'call_eKfxZnJLmAT6jx3rB5YZ0I9w'
assert report['independent_session_id'] != report['implementation_session_id']
for check in report['checks']:
    assert check['rationale'] and check['evidence']
    for ref in check['evidence']:
        assert (ROOT / ref).is_file(), ref
manifest = json.loads((ROOT / report['candidate_ref']).read_bytes())
assert report['candidate_fingerprint'] == manifest['fingerprint']
assert subprocess.check_output(['git', '-C', str(CANDIDATE), 'rev-parse', 'HEAD']).decode().strip() == manifest['head_oid']
assert not subprocess.check_output(['git', '-C', str(CANDIDATE), 'status', '--porcelain=v1', '--untracked-files=all'])
diff = subprocess.check_output(['git', '-C', str(CANDIDATE), 'diff', '--binary', manifest['base_oid'], manifest['head_oid']])
assert hashlib.sha256(diff).hexdigest() == manifest['diff_sha256']
for ref in manifest['validation_refs']:
    assert hashlib.sha256((ROOT / ref['path']).read_bytes()).hexdigest() == ref['sha256']
for path, digest in [('src/commands.py', '700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0'), ('tests/unit/commands/test_commands.py', 'c77171fefa9d43be13c4f06fe11dd49bc741caae267d6232578161248ff9952a')]:
    assert hashlib.sha256((CANDIDATE / path).read_bytes()).hexdigest() == digest
print('PASS: frozen-v1 review-result schema; 11 unique passing R1 checks; all evidence paths present; distinct submitted native invocation/session; no findings.')
print('PASS: exact candidate head, clean tree, frozen production/test bytes, raw diff and all bound validation bytes remain unchanged.')
for path in sorted(REVIEW.glob(STEM + '*')):
    if path.name == STEM + '-report-validation.txt':
        continue
    print(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + path.name)
print('PASS: review finalized; candidate access ends before FINAL.')
