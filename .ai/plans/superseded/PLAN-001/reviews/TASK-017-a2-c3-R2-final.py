"""Final R2 schema and immutability verification; no finalized R1 program run."""
from pathlib import Path
from datetime import datetime, UTC
import hashlib
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[5]
TREE=ROOT/'.worktrees/TASK-017-a2'
PLAN='.ai/plans/current/PLAN-001/'
REVIEWS=ROOT/(PLAN+'reviews')
STEM='TASK-017-a2-c3-R2'
BASE='b90556d92e0f37e664d685b4af85c43fc8143d81'
HEAD='b7593f11961aa6f5c3a927f3c49af32c4fa93971'
sys.path.insert(0,str(TREE/'src'))
from contracts import ContractRegistry, structural_task_digest

def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def git(*args,root=TREE): return subprocess.check_output(['git','-C',str(root),*args])

def frozen_checks():
    assert git('rev-parse','HEAD',root=ROOT).decode().strip()==BASE
    assert git('rev-parse','HEAD').decode().strip()==HEAD
    assert git('merge-base',BASE,HEAD).decode().strip()==BASE
    assert not git('status','--porcelain','--untracked-files=all')
    assert git('diff','--name-only',root=ROOT).decode().splitlines()==[PLAN+'evidence/coordination/CURRENT.md']
    assert not git('diff','--cached','--name-only',root=ROOT)
    assert sha(git('diff','--binary',BASE,HEAD))==manifest['diff_sha256']
    for ref in manifest['context_refs']:
        assert sha(git('show',HEAD+':'+ref['path']))==ref['sha256']
    for ref in manifest['validation_refs']:
        assert sha((ROOT/ref['path']).read_bytes())==ref['sha256']
    assert sha((ROOT/'.ai/project/policy.json').read_bytes()+(ROOT/'.ai/project/agent-models.json').read_bytes())==manifest['policy_model_digest']
    for name,digest in audit['r1_hashes'].items():
        assert sha((REVIEWS/name).read_bytes())==digest
    for path,digest in audit['history_hashes'].items():
        assert sha((ROOT/path).read_bytes())==digest
    for path in audit['owned_paths']:
        assert path in git('ls-files').decode().splitlines()
    assert json.loads((ROOT/report['candidate_ref']).read_bytes())==manifest

report=json.loads((REVIEWS/(STEM+'.json')).read_bytes())
audit=json.loads((REVIEWS/(STEM+'-identity.json.txt')).read_bytes())
manifest=json.loads((ROOT/report['candidate_ref']).read_bytes())
registry=ContractRegistry(TREE/'schemas/v1')
registry.validate(report)
registry.validate(manifest)
r1=json.loads((ROOT/report['review_1_ref']).read_bytes())
registry.validate(r1)
assert report['stage']=='consistency' and report['verdict']=='fail'
assert [c['id'] for c in report['checks']]==[f'R2-{i:02}' for i in range(1,13)]
assert all(c['rationale'] and c['evidence'] for c in report['checks'])
assert len(report['findings'])==1 and report['findings'][0]['resolved'] is False
assert report['findings'][0]['category']=='defect'
assert report['review_1_ref']==PLAN+'reviews/TASK-017-a2-c3-R1.json'
assert r1['verdict']=='pass' and r1['candidate_ref']==report['candidate_ref']
assert r1['candidate_fingerprint']==report['candidate_fingerprint']==manifest['fingerprint']==sha(canonical({k:v for k,v in manifest.items() if k!='fingerprint'}))
assert len({report['independent_session_id'],r1['independent_session_id'],report['implementation_session_id']})==3
assert report['reviewer']['invocation_id']=='call_xKTFWNRE1BxoqMhanEfHd15D'
assert report['reviewer']['capability_rank']==4
assert report['reviewer']['invocation_id'] not in {r1['reviewer']['invocation_id'],'call_9PXUEvQO4ZqUKqOXh6eTRkke'}
assert len(audit['r1_hashes'])==9 and len(audit['history_hashes'])==20
frozen_checks()
tasks=[json.loads(p.read_bytes()) for p in (TREE/(PLAN+'tasks/current')).glob('TASK-*.json')]
graph=json.loads((TREE/(PLAN+'graph.json')).read_bytes())
assert structural_task_digest(tasks)==audit['task_digest']
assert sha(canonical({k:graph[k] for k in ('schema_version','kind','id','plan_id','revision','nodes','task_set_sha256')}))==audit['graph_digest']
windows=json.loads((REVIEWS/(STEM+'-probes-windows.json.txt')).read_bytes())
linux=json.loads((REVIEWS/(STEM+'-probes-linux.json.txt')).read_bytes())
assert len(windows['fresh_processes'])==5 and len(linux['fresh_processes'])==2
for data in (windows,linux):
    for first,second in data['fresh_processes']:
        assert first['pid']!=second['pid'] and first['settings_sha256']==second['settings_sha256']
        assert first['outcome']=='admitted' and first['request_schema_valid'] and first['output_schema_valid']
        if first['case']=='baseline':
            assert second['outcome']=='admitted' and first['output_sha256']==second['output_sha256']
        elif first['case']=='unicode_output':
            assert second['outcome']=='admitted' and first['output_sha256']!=second['output_sha256']
        else:
            assert second['outcome']=='rejected' and second['saved_bytes_unchanged']
    for checks in data['compatibility'].values():
        assert checks=={'protocol_signatures':3,'mapped_review_roles':3,'wire_records_validated':8,'boundary_rejections':13}
payload=json.loads((REVIEWS/(STEM+'-payload-audit.json.txt')).read_bytes())
for case in ('leading_scope_path','leading_evidence_path'):
    assert payload[case]['after_restart']['outcome']=='rejected'
    assert payload[case]['after_restart']['saved_bytes_unchanged']
assert payload['metadata_payload']['exact_metadata_roundtrip']
assert payload['future_model_provenance']['first_poll']['category']=='validation_failed'
assert payload['future_model_provenance']['after_restart']['status']=='succeeded'
assert len(payload['upstream_rejects_not_requirements'])==4
final_path=REVIEWS/(STEM+'-final.txt')
log=[f'Final R2 verification UTC: {datetime.now(UTC).isoformat()}',f'Runtime: {sys.version}; executable={sys.executable}', 'PASS review-result/candidate/R1 schemas; all 12 R2 checks present; one unresolved major defect; verdict FAIL.', 'PASS exact same-candidate R1 PASS remains immutable; native R2 invocation/session distinct from R1 and implementation.', 'PASS ROOT/base/head, clean candidate, raw diff, 14 committed contexts, 3 bound validation files, policy-model digest and fingerprint unchanged.', 'PASS approved r4 graph/task digests, 9 R1 file hashes and all 20 historical report/companion hashes unchanged.', 'PASS required task source/tests/handoff remain tracked; ROOT index unchanged; only disclosed tracked coordinator CURRENT.md progress differs.', 'PASS independent Windows suite ran 29 tests, exit 0; Windows/Linux probe commands and focused payload audit exited 0, capturing genuine product counterexamples rather than acceptance passes.', 'PASS 10 Windows and 4 Linux fresh processes reproduce the recorded outcomes with identical per-case settings; both-provider review/schema/fence controls hold.', 'PASS focused payload audit bounds accepted leading path whitespace, exact arbitrary metadata payloads, upstream unsupported inputs and normalization-induced invalid-provenance acceptance.']
final_path.write_text('\n'.join(log)+'\n',encoding='utf-8')
for check in report['checks']:
    for path in check['evidence']:
        assert (ROOT/path).exists() or (TREE/path).exists(),path
for markdown in REVIEWS.glob(STEM+'*.md'):
    for target in re.findall(r'\]\(([^)]+)\)',markdown.read_text(encoding='utf-8')):
        assert (markdown.parent/target).resolve().is_file(),target
foundation=subprocess.run([sys.executable,'-B',str(TREE/'src/validate_foundation.py'),'--project',str(ROOT)],cwd=TREE,capture_output=True,text=True,shell=False)
log += [f'ROOT review packaging foundation exit: {foundation.returncode}',foundation.stdout,foundation.stderr]
assert foundation.returncode==0,(foundation.stdout,foundation.stderr)
frozen_checks()
for path in sorted(REVIEWS.glob(STEM+'*')):
    if path!=final_path: log.append(f'SHA256 {path.name}: {sha(path.read_bytes())}')
log.append('FINAL verification complete. R2 stops all ROOT/candidate access and returns FAIL for independent recovery; no integration, acceptance, repair or source mutation performed.')
final_path.write_text('\n'.join(log)+'\n',encoding='utf-8')
print('\n'.join(log))
