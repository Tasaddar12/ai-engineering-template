"""Independent TASK-016 review evidence; not a product dependency or regression suite."""
from __future__ import annotations
import dataclasses
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import traceback
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[5]
CAND = ROOT / '.worktrees/TASK-016-a1'
PREFIX = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-016-a1-c1-R1'
BASE = 'e44eeb2b4197774a57d03918518381962aa37c20'
HEAD = 'e88e7950fb6bce3656d3de8dad54ace21074d252'
OWNER = '0cb81d179b7ffd76012f05f216010ae444f11f98'
MANIFEST = ROOT / '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-016-a1-e88e7950fb6b.json'
sys.path.insert(0, str(CAND / 'src'))
from context import RepositoryContextBuilder
from workflow_ports import ContextRequest, ContextBuilder
from contracts import ContractRegistry, structural_task_digest
from domain_values import DomainException, ScopeClaim

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def sha(value):
    return hashlib.sha256(value).hexdigest()

def git(*args, cwd=CAND):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, check=True).stdout

def record(suffix, value):
    Path(str(PREFIX) + suffix).write_text(json.dumps(value, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')

def identity():
    manifest = json.loads(MANIFEST.read_bytes())
    assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD
    assert not git('status', '--porcelain')
    assert manifest['base_oid'] == BASE and manifest['head_oid'] == HEAD
    assert sha(git('diff', '--binary', BASE, HEAD)) == manifest['diff_sha256']
    context = []
    for ref in manifest['context_refs']:
        committed = git('show', HEAD + ':' + ref['path'])
        assert sha(committed) == ref['sha256'], ref
        assert committed == (CAND / ref['path']).read_bytes(), ref
        assert committed == git('show', BASE + ':' + ref['path'], cwd=ROOT), ref
        context.append(ref)
    for ref in manifest['validation_refs']:
        assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256']
    assert sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()) == manifest['policy_model_digest']
    assert sha(canonical({k:v for k,v in manifest.items() if k != 'fingerprint'})) == manifest['fingerprint']
    ContractRegistry(CAND / 'schemas/v1').validate(manifest)
    paths = git('diff', '--name-only', '--no-renames', '-z', BASE, HEAD).decode().split('\0')[:-1]
    expected = ['.ai/plans/current/PLAN-001/evidence/implementation/TASK-016.md', 'src/context.py', 'tests/unit/context/test_context.py']
    assert sorted(paths) == expected, paths
    owner_changes = git('diff', '--name-status', OWNER, HEAD, '--', 'src', 'tests', 'schemas').decode()
    for entry in owner_changes.splitlines():
        action, path = entry.split('\t')
        assert action == 'A', entry
        assert git('show', BASE + ':' + path, cwd=ROOT) == git('show', HEAD + ':' + path), path
    for path in expected:
        assert git('show', OWNER + ':' + path) == git('show', HEAD + ':' + path), path
    deps = {'TASK-003': ('c749ec19056dd6d215c51a9896f35785391d0ace', ['src/workflow_ports.py']), 'TASK-004': ('1ee6b06c46e4c626ab6d63be52bb11d7bdfeb518', ['src/contracts.py']), 'TASK-038': ('ab36f09f7775201882bf863a90bc264be022adbd', ['src/config.py'])}
    for task, (oid, dep_paths) in deps.items():
        git('merge-base', '--is-ancestor', oid, BASE)
        rel = '.ai/plans/current/PLAN-001/tasks/current/' + task + '.json'
        assert json.loads(git('show', BASE + ':' + rel))['status'] == 'accepted'
        for path in dep_paths + ['.ai/plans/current/PLAN-001/evidence/implementation/' + task + '.md']:
            assert git('show', oid + ':' + path) == git('show', HEAD + ':' + path), path
    graph = json.loads((CAND / '.ai/plans/current/PLAN-001/graph.json').read_bytes())
    plan = json.loads((CAND / '.ai/plans/current/PLAN-001/plan.json').read_bytes())
    tasks = [json.loads((CAND / ('.ai/plans/current/PLAN-001/tasks/current/' + task + '.json')).read_bytes()) for task in plan['task_ids']]
    assert graph['revision'] == 4
    assert structural_task_digest(tasks) == graph['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
    isolation = json.loads((CAND / plan['isolation_review_ref']).read_bytes())
    assert isolation['verdict'] == 'pass' and isolation['task_set_sha256'] == graph['task_set_sha256'] and isolation['graph_revision'] == 4
    return {'base': BASE, 'head': HEAD, 'owner': OWNER, 'fingerprint': manifest['fingerprint'], 'diff_sha256': manifest['diff_sha256'], 'changed': paths, 'context_refs_verified': context, 'validation_refs_verified': manifest['validation_refs'], 'policy_model_digest': manifest['policy_model_digest'], 'candidate_clean': True, 'owner_owned_blobs_identical': True, 'merge_other_source_additions_match_base': owner_changes.splitlines(), 'dependency_acceptance_and_blobs': deps, 'graph_revision': 4, 'task_count': len(tasks), 'structural_digest': graph['task_set_sha256'], 'root_status': git('status', '--porcelain', cwd=ROOT).decode(), 'manifest_sha256': sha(MANIFEST.read_bytes())}

def run_command(label, argv, cwd):
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, shell=False)
    value = {'argv': argv, 'cwd': str(cwd), 'exit_code': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}
    record('-' + label + '.json.txt', value)
    assert proc.returncode == 0, value
    return value

def request(**kw):
    values = dict(project_id='p', plan_id='PLAN-001', run_id='r', operation_id='o', task_id='TASK-016', role='implementer', scope=ScopeClaim(read_paths=['records/', '.ai/plans/', 'src/']), document_refs=['records/task.md'], dependency_handoff_refs=(), sibling_handoff_refs=(), interface_refs=(), review_1_ref=None, acceptance_ids=['TASK-016-AC1', 'TASK-016-AC2'], optional_refs=(), token_budget=100000)
    values.update(kw)
    return ContextRequest(**values)

def wire(bundle):
    def convert(value):
        if isinstance(value, (str, int, bool)) or value is None: return value
        if isinstance(value, (tuple, list)): return [convert(v) for v in value]
        if hasattr(value, 'value'): return str(value)
        return {field.name: convert(getattr(value, field.name)) for field in dataclasses.fields(value)}
    return convert(bundle)

REG = ContractRegistry(CAND / 'schemas/v1')
def handoff(task='TASK-003'):
    return dict(schema_version='1.0', kind='handoff', id='handoff-' + task, task_id=task, attempt_id=task + '-a1', branch='task-branch', base_oid='1'*40, commit_oid='2'*40, files_changed=[], validation=[], assumptions=[], remaining_risks=[], deviations=[], interfaces_changed=[], dependency_notes=[], reviewer_notes=[], command_evidence_refs=[], context_digest='3'*64)

def review():
    return dict(schema_version='1.0', kind='review-result', id='r1', stage='implementation', request_id='request-r1', task_id='TASK-016', plan_id='PLAN-001', candidate_ref='.ai/plans/current/PLAN-001/reviews/candidate.json', candidate_fingerprint='4'*64, verdict='pass', reviewer=dict(profile='review_high',provider='OpenAI',model_id='gpt-6-astra',capability_rank=4,invocation_id='i'), independent_session_id='reviewer', implementation_session_id='implementer', review_1_ref=None, checklist_version='PLAN-001-v1', checks=[dict(id='R1-01',status='pass',rationale='checked',evidence=['records/task.md'])], findings=[], created_at='2026-09-08T00:00:00Z')

def behavior():
    results = []
    with tempfile.TemporaryDirectory(prefix='task016-review-') as temp:
        root = Path(temp)
        def write(path, data):
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data if isinstance(data, bytes) else data.encode('utf-8'))
            return path
        def probe(name, fn):
            try:
                detail = fn()
                results.append(dict(name=name, status='pass', detail=detail))
            except Exception as exc:
                results.append(dict(name=name, status='fail', error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc()))
        def rejects(req, reason=None, builder=None):
            try:
                (builder or RepositoryContextBuilder(root)).build(req)
            except DomainException as exc:
                details = exc.error.details.to_dict()
                if reason: assert details.get('reason') == reason, details
                assert str(root) not in str(exc) + repr(details)
                return {'category': str(exc.category), 'details': details}
            raise AssertionError('build unexpectedly returned a successful complete bundle')
        write('records/task.md', 'required acceptance\r\n')
        dep = write('.ai/plans/current/PLAN-001/evidence/dep.json', canonical(handoff()))
        sib = write('.ai/plans/current/PLAN-001/evidence/sib.json', canonical(handoff('TASK-004')))
        rev = write('.ai/plans/current/PLAN-001/reviews/r1.json', canonical(review()))
        REG.validate(handoff()); REG.validate(review())
        builder = RepositoryContextBuilder(root)
        base = request(dependency_handoff_refs=[dep], sibling_handoff_refs=[sib], review_1_ref=rev)
        def valid_hash():
            bundle = builder.build(base); value = wire(bundle); REG.validate(value)
            assert isinstance(builder, ContextBuilder)
            assert bundle == builder.build(base)
            for ref in [*value['documents'],*value['dependency_handoffs'],*value['sibling_handoffs'],value['review_1_ref']]:
                assert ref['sha256'] == sha((root / ref['path']).read_bytes())
            unsigned = {k:v for k,v in value.items() if k not in {'id','digest'}}
            preimage = dict(estimator='utf8-byte-upper-bound-v1', request=dict(project_id='p',plan_id='PLAN-001',run_id='r',operation_id='o',task_id='TASK-016',role='implementer',scope=base.scope.to_wire()),bundle=unsigned)
            assert sha(canonical(preimage)) == str(bundle.digest)
            assert value['id'] == 'context-' + value['digest'][:16]
            source_size=sum((root / r['path']).stat().st_size for r in [*value['documents'],*value['dependency_handoffs'],*value['sibling_handoffs'],value['review_1_ref']])
            return dict(digest=str(bundle.digest), estimated=bundle.estimated_tokens, selected_raw_bytes=source_size, complete_manifest_preimage_bytes=len(canonical(preimage)), actual_wire_bytes=len(canonical(value)))
        probe('schema_valid_full_records_raw_hash_independent_manifest', valid_hash)
        def budgets():
            measured=builder.build(base)
            exact=builder.build(dataclasses.replace(base,token_budget=measured.estimated_tokens))
            assert exact.estimated_tokens == measured.estimated_tokens
            below=rejects(dataclasses.replace(base,token_budget=measured.estimated_tokens-1),'required_context_over_budget')
            write('records/a-large.md','x'*10000); write('records/z-small.md','small')
            opt=request(optional_refs=['records/z-small.md','records/a-large.md'],token_budget=1500)
            result=builder.build(opt)
            assert result.omitted_optional_refs == ('records/a-large.md',)
            assert builder.build(dataclasses.replace(opt,optional_refs=tuple(reversed(opt.optional_refs)))) == result
            metadata=rejects(request(acceptance_ids=['A'*5000],token_budget=2000),'required_context_over_budget')
            return dict(required_exact=exact.estimated_tokens,below=below,optional_selected=[r.path for r in result.documents],metadata_only=metadata)
        probe('required_multi_file_metadata_and_optional_after_omission',budgets)
        def boundaries():
            outcomes=[]
            for field,path in [('document_refs','records/../task.md'),('optional_refs','/etc/passwd')]:
                outcomes.append(rejects(request(**{field:[path]}),'invalid_portable_path'))
            outcomes.append(rejects(request(optional_refs=['RECORDS/task.md']),'duplicate_of_documents'))
            outcomes.append(rejects(request(document_refs=['records/caf\u00e9.md'],optional_refs=['records/cafe\u0301.md']),'duplicate_of_documents'))
            outcomes.append(rejects(request(optional_refs=['records/task2.md'],scope=ScopeClaim(read_paths=['records/'],prohibited_paths=['records/task2.md'])),'outside_read_scope'))
            outcomes.append(rejects(request(dependency_handoff_refs=['.ai/plans/current/PLAN-002/evidence/dep.json']),'cross_plan_reference'))
            for mutation,reason in [({'task_id':'TASK-099'},'wrong_review_task'),({'stage':'consistency'},'wrong_review_stage')]:
                write(rev,canonical({**review(),**mutation})); outcomes.append(rejects(base,reason))
            write(rev,canonical(review()))
            for mutation,reason in [({'commit_oid':'bad'},'invalid_handoff_commit'),({'task_id':'TASK-016'},'self_handoff')]:
                write(dep,canonical({**handoff(),**mutation})); outcomes.append(rejects(base,reason))
            write(dep,canonical(handoff()))
            return outcomes
        probe('scope_alias_plan_record_identity_boundaries',boundaries)
        def leakage():
            known='opaque-known-review-value'
            checked=RepositoryContextBuilder(root,sensitive_values=[known])
            outcomes=[]
            with patch.object(Path,'open',side_effect=AssertionError('metadata rejection must precede file reads')):
                for kw in [dict(role='r-'+known),dict(acceptance_ids=['A-'+known]),dict(role='C:\\Users\\private-review\\x'),dict(acceptance_ids=['/home/private-review/x']),dict(optional_refs=['records/'+known+'.md'])]:
                    outcomes.append(rejects(request(**kw),builder=checked))
            for payload in [known,'api_key = secret-review-value','path C:\\Users\\private-review\\x','path /home/private-review/x']:
                write('records/leaky.md',payload)
                outcomes.append(rejects(request(document_refs=['records/leaky.md']),builder=checked))
                optional=checked.build(request(optional_refs=['records/leaky.md']))
                assert optional.omitted_optional_refs == ('records/leaky.md',)
                assert known not in repr(optional)
            return outcomes
        probe('known_secrets_host_paths_metadata_before_reads_sanitized_errors',leakage)
        def bounded_reads():
            read=[]; original=Path.open
            def tracked(path,*args,**kw):
                if str(path).startswith(str(root)):
                    assert path == root / 'records/task.md', path
                    assert args == ('rb',), args
                    read.append(path.relative_to(root).as_posix())
                return original(path,*args,**kw)
            with patch.object(Path,'open',tracked):
                builder.build(request())
            assert read == ['records/task.md'], read
            write('records/binary.dat',b'\xff'); write('records/oversize.md','x'*3000)
            binary=rejects(request(document_refs=['records/binary.dat']),'non_utf8_content')
            over=rejects(request(document_refs=['records/oversize.md'],token_budget=1000),'required_context_over_budget')
            write('records/task.md','required acceptance\n')
            changed=builder.build(request())
            assert changed.documents[0].sha256.value == sha(b'required acceptance\n')
            return dict(opened=read,binary=binary,over_budget=over)
        probe('explicit_only_binary_size_and_raw_material_change',bounded_reads)
        def schema_invalid_handoff():
            invalid={k:handoff()[k] for k in ['schema_version','kind','id','task_id','commit_oid']}
            try: REG.validate(invalid)
            except DomainException: pass
            else: raise AssertionError('invalid fixture unexpectedly passed registry')
            write(dep,canonical(invalid))
            return rejects(base)
        probe('schema_invalid_handoff_required_input_rejected',schema_invalid_handoff)
        write(dep,canonical(handoff()))
        def schema_invalid_review():
            invalid={k:review()[k] for k in ['schema_version','kind','plan_id','task_id','stage']}
            try: REG.validate(invalid)
            except DomainException: pass
            else: raise AssertionError('invalid fixture unexpectedly passed registry')
            write(rev,canonical(invalid))
            return rejects(base)
        probe('schema_invalid_review_required_input_rejected',schema_invalid_review)
        write(rev,canonical(review()))
        def nested_json():
            write(dep,'{"schema_version":"1.0","kind":"handoff","deep":' + '['*2000+'0'+']'*2000+'}')
            return rejects(base)
        probe('bounded_deep_json_returns_typed_sanitized_error',nested_json)
        def surrogate_metadata():
            return rejects(request(role='reviewer\ud800'))
        probe('dto_accepted_non_utf8_metadata_returns_typed_error',surrogate_metadata)
    return {'runtime':sys.version,'platform':platform.platform(),'origins':{m:importlib.import_module(m).__file__ for m in ['context','workflow_ports','contracts','domain_values']},'groups':results}

if __name__ == '__main__':
    mode=sys.argv[1]
    if mode == 'identity':
        value=identity(); record('-identity.json.txt',value); print(json.dumps(value,indent=2))
    elif mode == 'behavior':
        value=behavior(); record('-probe.json.txt',value); print(json.dumps(value,indent=2)); sys.exit(1 if any(g['status']=='fail' for g in value['groups']) else 0)
    elif mode == 'declared':
        command=json.loads((CAND / '.ai/plans/current/PLAN-001/commands/test.TASK-016.json').read_bytes())
        value=run_command('declared',[sys.executable,*command['argv'][1:]],CAND)
        assert re.search(r'Ran ([1-9][0-9]*) tests',value['stderr']+value['stdout']); print(json.dumps(value,indent=2))
    elif mode == 'linux-link':
        value=run_command('linux-link',['wsl.exe','-d','Ubuntu-24.04','--cd','/mnt/d/Codex Projects/ai-engineering-template/.worktrees/TASK-016-a1','--exec','/mnt/d/Codex Projects/ai-engineering-template/.ai/local/full-plan-linux-py311-venv/bin/python','-B','-m','unittest','discover','-s','tests/unit/context/','-p','test_*.py','-k','real_file_and_directory_links','-v'],ROOT)
        assert 'Ran 1 test' in value['stderr'] and 'skipped' not in value['stderr']; print(json.dumps(value,indent=2))
    elif mode == 'foundation':
        print(json.dumps(run_command('foundation',[sys.executable,'-B','src/validate_foundation.py'],CAND),indent=2))
    elif mode == 'closing':
        value=identity(); opening=json.loads(Path(str(PREFIX)+'-identity.json.txt').read_bytes())
        for key in opening:
            if key != 'root_status': assert canonical(value[key]) == canonical(opening[key]),key
        report_path=Path(str(PREFIX)+'.json'); report=json.loads(report_path.read_bytes()); REG.validate(report)
        assert len(report['checks']) == 11 and {c['id'] for c in report['checks']} == {f'R1-{i:02}' for i in range(1,12)}
        assert report['candidate_fingerprint'] == value['fingerprint']
        refs=[r for c in report['checks'] for r in c['evidence']]
        assert all((ROOT/r).is_file() or (CAND/r).is_file() for r in refs)
        text=Path(str(PREFIX)+'.md').read_text(encoding='utf-8')
        links=re.findall(r'\]\(([^)]+)\)',text)
        closing_path=Path(str(PREFIX)+'-verification.json.txt')
        assert all((PREFIX.parent/link.split('#')[0]).exists() or (PREFIX.parent/link.split('#')[0]) == closing_path for link in links), links
        value.update(report_schema_valid=True,check_count=11,evidence_links_valid=True,report_sha256=sha(report_path.read_bytes()),markdown_sha256=sha(Path(str(PREFIX)+'.md').read_bytes()),report_finding_ids=[f['id'] for f in report['findings']])
        record('-verification.json.txt',value)
        assert all((PREFIX.parent/link.split('#')[0]).exists() for link in links), links
        print(json.dumps(value,indent=2))
