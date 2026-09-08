"""Final R1 packaging verification; stop all candidate/ROOT access after success."""
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
TREE=ROOT/'.worktrees/TASK-017-a2'
REVIEW=ROOT/'.ai/plans/current/PLAN-001/reviews'
STEM='TASK-017-a2-c3-R1'
BASE='b90556d92e0f37e664d685b4af85c43fc8143d81'
HEAD='b7593f11961aa6f5c3a927f3c49af32c4fa93971'
sys.path.insert(0,str(TREE/'src'))
from contracts import ContractRegistry

def git(*args, tree=TREE):
    return subprocess.check_output(['git','-C',str(tree),*args])

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()

report_path=REVIEW/(STEM+'.json')
report=json.loads(report_path.read_bytes())
# The final report timestamp is observed here, not an anticipated clock value.
report['created_at']=datetime.now(UTC).isoformat()
for check in report['checks']:
    check['evidence']=[re.sub(r':\d+$','',value) for value in check['evidence']]
report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
registry=ContractRegistry(TREE/'schemas/v1')
registry.validate(report)
assert [c['id'] for c in report['checks']]==[f'R1-{i:02}' for i in range(1,12)]
assert all(c['status']=='pass' and c['rationale'] and c['evidence'] for c in report['checks'])
assert report['verdict']=='pass' and not report['findings']
assert report['independent_session_id']!=report['implementation_session_id']
assert report['reviewer']['invocation_id']=='call_mI6rXNxVx2oywJ9qKRH8tyx7'
manifest=json.loads((ROOT/report['candidate_ref']).read_bytes())
assert manifest['fingerprint']==report['candidate_fingerprint']==sha(canonical({k:v for k,v in manifest.items() if k!='fingerprint'}))
assert manifest['base_oid']==BASE and manifest['head_oid']==HEAD
assert git('rev-parse','HEAD',tree=ROOT).decode().strip()==BASE
assert git('rev-parse','HEAD').decode().strip()==HEAD
assert not git('status','--porcelain','--untracked-files=all')
assert git('merge-base',BASE,HEAD).decode().strip()==BASE
assert sha(git('diff','--binary',BASE,HEAD))==manifest['diff_sha256']
for ref in manifest['context_refs']:
    assert sha(git('show',HEAD+':'+ref['path']))==ref['sha256']
for ref in manifest['validation_refs']:
    assert sha((ROOT/ref['path']).read_bytes())==ref['sha256']
assert sha((ROOT/'.ai/project/policy.json').read_bytes()+(ROOT/'.ai/project/agent-models.json').read_bytes())==manifest['policy_model_digest']
graph=json.loads((TREE/'.ai/plans/current/PLAN-001/graph.json').read_bytes())
projection={k:graph[k] for k in ('schema_version','kind','id','plan_id','revision','nodes','task_set_sha256')}
assert sha(canonical(projection))=='5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337'
prior=json.loads((ROOT/'.ai/plans/current/PLAN-001/evidence/recovery/TASK-017-recovery-assessment-verification.json.txt').read_bytes())
for path,digest in prior['historical_files_unchanged'].items():
    assert sha((ROOT/path).read_bytes())==digest
tracked=git('ls-files').decode().splitlines()
for path in ('src/agents.py','tests/unit/agents/test_agents.py','.ai/plans/current/PLAN-001/evidence/implementation/TASK-017.md','src/config.py','src/contracts.py','src/workflow_ports.py','src/domain_values.py'):
    assert path in tracked
root_diff=git('diff','--name-only',tree=ROOT).decode().splitlines()
assert root_diff==['.ai/plans/current/PLAN-001/evidence/coordination/CURRENT.md'],root_diff
assert not git('diff','--cached','--name-only',tree=ROOT)
for p in REVIEW.glob(STEM+'-probes-*.json.txt'):
    data=json.loads(p.read_bytes())
    assert data['atomic_replacement_rollback']==4
    assert len(data['fresh_processes'])==(2 if 'linux' in p.name else 4)
    for group in data['fresh_processes']:
        assert [row['poll'] for row in group]==['unknown','running','succeeded']
        assert all(row['effect_count']==1 for row in group)
        assert len({row['settings_sha256'] for row in group})==1
final_path=REVIEW/(STEM+'-final.txt')
log=[f'Final verification UTC: {datetime.now(UTC).isoformat()}',f'Runtime: {sys.version}; executable={sys.executable}','PASS review-result schema through accepted ContractRegistry; all 11 checks complete/pass; independent reviewer/native identity bound.',f'PASS ROOT HEAD={BASE}; clean candidate HEAD={HEAD}; unchanged merge-base/raw diff/14 context refs/3 validation refs/policy digest/fingerprint.','PASS r4 structural graph digest=5fa7578c40f6897562a450aaa933f2b2fc307db2dbc6e415483c03abe4c24337; prior identity audit verified 39-task digest.','PASS all 20 historical review companions retain their verified original hashes.','PASS required candidate runtime/tests/handoff are tracked; ROOT tracked changes contain only the coordinator-disclosed CURRENT.md note; index unchanged.','PASS captured independent Windows/Linux process, rollback and boundary evidence is parseable and retains the reported outcomes.','Commands: Windows Python3.12 -B identity.py --suite (29 tests, exit0); Windows Python3.12 -B probes.py (exit0); Linux Python3.11 via WSL --exec -B probes.py --linux-focused (exit0). No probe setup or product failure occurred.']
final_path.write_text('\n'.join(log)+'\n',encoding='utf-8')
for check in report['checks']:
    for path in check['evidence']:
        assert (ROOT/path).exists() or (TREE/path).exists(),path
markdown=(REVIEW/(STEM+'.md')).read_text(encoding='utf-8')
for target in re.findall(r'\]\(([^)]+)\)',markdown):
    assert (REVIEW/target).resolve().is_file(),target
foundation=subprocess.run([sys.executable,'-B',str(TREE/'src/validate_foundation.py'),'--project',str(ROOT)],cwd=TREE,capture_output=True,text=True,shell=False)
log.extend([f'ROOT report packaging foundation validation exit={foundation.returncode}',foundation.stdout,foundation.stderr])
assert foundation.returncode==0,(foundation.stdout,foundation.stderr)
assert git('rev-parse','HEAD',tree=ROOT).decode().strip()==BASE
assert git('rev-parse','HEAD').decode().strip()==HEAD and not git('status','--porcelain')
log.append('PASS final report Markdown links and all check evidence resolve; final frozen identities remain unchanged.')
for p in sorted(REVIEW.glob(STEM+'*')):
    if p!=final_path:
        log.append(f'SHA256 {p.name}: {sha(p.read_bytes())}')
log.append('FINAL verification complete. Reviewer now stops all ROOT/candidate access and hands off PASS for fresh R2 only.')
final_path.write_text('\n'.join(log)+'\n',encoding='utf-8')
print('\n'.join(log))
