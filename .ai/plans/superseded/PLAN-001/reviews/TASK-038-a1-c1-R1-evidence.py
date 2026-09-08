"""Independent R1 identity verification and focused configuration probes."""
from __future__ import annotations
import copy
import hashlib
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import FrozenInstanceError
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-038-a1'
STEM = ROOT / '.ai/plans/current/PLAN-001/reviews/TASK-038-a1-c1-R1'
sys.path.insert(0, str(WT / 'src'))
import config
import contracts
from domain_values import DomainException, ErrorCategory

def read(path):
    return json.loads(path.read_bytes())

def git(*args):
    return subprocess.check_output(['git', *args], cwd=WT)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def emit(label, value):
    print(label + ': ' + json.dumps(value, sort_keys=True, default=str))

CREF = '.ai/plans/current/PLAN-001/reviews/candidates/CANDIDATE-TASK-038-a1-5ce39a43fce2.json'
c = read(ROOT / CREF)
assert c['head_oid'] == '5ce39a43fce2449af60ff53b645c212e7558435b'
assert c['base_oid'] == 'ca6fac788dc5273d346d2a671e3e74185da0f757'
assert git('rev-parse', 'HEAD').decode().strip() == c['head_oid']
assert not git('status', '--porcelain=v1').strip()
assert subprocess.run(['git', 'merge-base', '--is-ancestor', c['base_oid'], c['head_oid']], cwd=WT).returncode == 0
assert digest(git('diff', '--binary', c['base_oid'], c['head_oid'])) == c['diff_sha256']
fingerprint = digest(json.dumps({k:v for k,v in c.items() if k != 'fingerprint'}, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode())
assert fingerprint == c['fingerprint'] == 'a4f856e1b67a9dc9205fba35a1986f0ceea3cb1eaa42d9818dfea8ccdb8315f3'
for ref in c['context_refs']:
    assert digest(git('show', f"{c['head_oid']}:{ref['path']}")) == ref['sha256'], ref
for ref in c['validation_refs']:
    assert digest((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref
assert digest((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes()) == c['policy_model_digest']
for rel in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
    assert read(ROOT / rel) == read(WT / rel)
changes = git('diff', '--name-status', c['base_oid'], c['head_oid']).decode().splitlines()
expected = ['.ai/plans/current/PLAN-001/evidence/implementation/TASK-038.md', 'src/config.py', 'tests/unit/config/test_config.py']
assert sorted(line.split('\t')[-1] for line in changes) == expected
assert all(line.startswith('A\t') for line in changes)
assert subprocess.run(['git','diff','--check',c['base_oid'],c['head_oid']],cwd=WT).returncode == 0
bundle = WT / '.ai/plans/current/PLAN-001'
graph = read(bundle / 'graph.json')
tasks = [read(p) for p in sorted((bundle / 'tasks/current').glob('TASK-*.json'))]
iso = read(bundle / 'reviews/r4-isolation-review.json')
task_digest = contracts.structural_task_digest(tasks)
assert len(tasks) == len(graph['nodes']) == 39
assert task_digest == iso['task_set_sha256'] == 'c84fdf4e0affcb8d329e8fc7ce2ae928410b44a21238304b3348b2e7d1b75c9e'
assert graph['revision'] == iso['graph_revision'] == c['graph_revision'] == 4
assert graph['status'] == 'approved' and iso['verdict'] == 'pass'
assert next(n for n in graph['nodes'] if n['task_id']=='TASK-038')['depends_on'] == ['TASK-004']
dep = read(bundle / 'reviews/candidates/CANDIDATE-TASK-004-a2-e3c1177f993e.json')
assert subprocess.run(['git','merge-base','--is-ancestor',dep['head_oid'],c['base_oid']],cwd=WT).returncode == 0
for stage in ('R1','R2'):
    review = read(bundle / f'reviews/TASK-004-a2-c3-{stage}.json')
    assert review['verdict'] == 'pass' and review['candidate_fingerprint'] == dep['fingerprint']
emit('identity', {'head':c['head_oid'], 'base':c['base_oid'], 'fingerprint':fingerprint, 'diff_sha256':c['diff_sha256'], 'context_refs_verified':len(c['context_refs']), 'validation_refs_verified':len(c['validation_refs']), 'policy_model_digest':c['policy_model_digest'], 'task_set_sha256':task_digest, 'accepted_004_ancestor':dep['head_oid'], 'changes':changes, 'clean':True})
emit('runtime', {'python':sys.version, 'config':config.__file__, 'contracts':contracts.__file__, 'load_signature':str(inspect.signature(config.load_project_settings))})
assert Path(config.__file__).resolve() == WT / 'src/config.py'
assert Path(contracts.__file__).resolve() == WT / 'src/contracts.py'

cmd = read(bundle / 'commands/test.TASK-038.json')
argv = [sys.executable] + cmd['argv'][1:]
env = os.environ.copy()
env['PYTHONDONTWRITEBYTECODE'] = '1'
completed = subprocess.run(argv,cwd=WT,env=env,capture_output=True,text=True,timeout=180)
test_output = completed.stdout + completed.stderr
assert completed.returncode == 0 and re.search(r'Ran 27 tests\b',test_output)
print('DECLARED COMMAND: ' + repr(argv))
print(test_output.strip())

registry = contracts.load_contract_registry(WT / 'schemas/v1')
counts = {'positive':0, 'negative':0, 'defects':0}

def expect_error(label, fn, category=None):
    try:
        fn()
    except DomainException as exc:
        if category is not None:
            assert exc.category == category, (label, exc.category)
        assert not exc.retryable
        counts['negative'] += 1
        emit('rejected '+label, {'category':str(exc.category)})
        return exc
    raise AssertionError('Unexpected acceptance: '+label)

def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value),encoding='utf-8')

def fixture(root, ns='.codex'):
    shutil.copytree(WT / 'schemas/v1', root / ns / 'framework/schemas/v1')
    inst = read(WT / 'docs/defaults/FRAMEWORK.json')
    inst = json.loads(json.dumps(inst).replace('.codex',ns))
    models = read(WT / 'docs/defaults/AGENT_MODELS.json')
    models['active_provider'] = 'anthropic' if ns == '.claude' else 'openai'
    policy = read(WT / 'docs/defaults/POLICY.json')
    for p in policy['model_profiles']:
        model = models['providers'][models['active_provider']]['profiles'][models['policy_profile_map'][p['name']]]
        p.update(provider=models['active_provider'], model_id=model['model_id'], capability_rank=model['capability_rank'])
    write(root / ns / 'framework.json',inst)
    write(root / ns / 'project/agent-models.json',models)
    write(root / ns / 'project/policy.json',policy)
    return inst, models, policy

def load(root):
    return config.load_project_settings(root,config.load_installation_record(root))

# Exact live source configuration, without substituting installer defaults.
try:
    load(WT)
except DomainException as exc:
    assert 'local_containers' in str(exc)
    counts['defects'] += 1
    emit('DEFECT R1-TASK-038-001', {'trigger':'load_project_settings(WT, load_installation_record(WT))', 'category':str(exc.category), 'message':str(exc), 'source_action':'local_containers'})
else:
    raise AssertionError('Expected current source-policy reproduction changed')

with tempfile.TemporaryDirectory(prefix='task038-r1-') as temp:
    area = Path(temp)
    root = area / 'project'
    inst, models, policy = fixture(root)
    native = root / '.codex/config.toml'
    native.write_text('model = "unverified-model"\n',encoding='utf-8')
    before = {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    settings = load(root)
    assert settings.configured_model('implementation') is None
    assert settings.model_for_role('implementer').provider == 'openai'
    assert isinstance(settings.policy.model_profiles,tuple)
    detached = settings.policy.to_wire()
    detached['model_profiles'][0]['model_id'] = 'changed'
    assert settings.policy.to_wire() != detached
    try:
        settings.policy.max_parallel = 99
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError('mutable loaded policy')
    assert before == {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
    counts['positive'] += 1
    emit('positive immutable read-only native isolation', True)

    # Tighten every control and prove detached schema-valid positive snapshot.
    overrides = config.RunOverrides(max_parallel=1,max_review_cycles=1,max_rewrites=0,max_agent_invocations=1,required_sandbox=True)
    saved = config.decode_run_settings(json.loads(json.dumps(settings.resolve_run(overrides).to_payload())))
    registry.validate(settings.effective_policy(overrides).to_wire())
    copied_root = area / 'relocated'
    shutil.copytree(root,copied_root)
    changed = copy.deepcopy(policy)
    changed.update(max_parallel=2,max_review_cycles=3,max_rewrites=4,max_agent_invocations=50)
    write(copied_root / '.codex/project/policy.json', changed)
    assert load(copied_root).resolve_run(saved=saved) is saved
    counts['positive'] += 1
    emit('positive portable saved hydration ignores changed project defaults', saved.to_payload())
    expect_error('saved plus overrides', lambda:settings.resolve_run(config.RunOverrides(),saved=saved),ErrorCategory.INVALID_INPUT)
    for key in ('max_parallel','max_review_cycles','max_rewrites','max_agent_invocations'):
        expect_error('broader '+key,lambda key=key:settings.resolve_run(config.RunOverrides(**{key:getattr(settings.policy,key)+1})),ErrorCategory.POLICY_DENIED)
    for key,bad in [('max_parallel',True),('max_review_cycles',0),('max_rewrites',-1),('max_agent_invocations','1'),('required_sandbox',1)]:
        payload=saved.to_payload(); payload[key]=bad
        expect_error('saved malformed '+key,lambda payload=payload:config.decode_run_settings(payload),ErrorCategory.INVALID_INPUT)
    payload=saved.to_payload(); payload.pop('required_sandbox')
    expect_error('saved missing field',lambda:config.decode_run_settings(payload),ErrorCategory.INVALID_INPUT)
    payload=saved.to_payload(); payload['credentials']='none'
    expect_error('saved unknown field',lambda:config.decode_run_settings(payload),ErrorCategory.INVALID_INPUT)

    zero = settings.effective_policy(config.RunOverrides(max_agent_invocations=0))
    try:
        registry.validate(zero.to_wire())
    except DomainException as exc:
        counts['defects'] += 1
        emit('DEFECT R1-TASK-038-002', {'trigger':'effective_policy(RunOverrides(max_agent_invocations=0)).to_wire()', 'category':str(exc.category),'message':str(exc),'returned_value':zero.max_agent_invocations,'schema_minimum':1})
    else:
        raise AssertionError('Expected zero-budget policy-schema reproduction changed')

    for bad in ('../outside/','.codex/../outside/','C:/outside/','.codex/NUL/','.codex/project./'):
        value=copy.deepcopy(inst);value['project_owned_roots'].append(bad)
        expect_error('unsafe root '+bad,lambda value=value:config.decode_installation_record(value,registry),ErrorCategory.INVALID_INPUT)
    value=copy.deepcopy(inst);value['owned_roots'].append('.codex/project/')
    expect_error('ownership overlap',lambda:config.decode_installation_record(value,registry),ErrorCategory.INVALID_INPUT)
    value=copy.deepcopy(inst);value['owned_roots'].append('outside/')
    expect_error('foreign installed root',lambda:config.decode_installation_record(value,registry),ErrorCategory.INVALID_INPUT)

    # Explicit capability and grant failures against copied wire records.
    for action in sorted(config.SENSITIVE_ACTIONS):
        value=copy.deepcopy(policy);value['approval_actions'].remove(action);value['autonomous_actions'].append(action)
        write(root / '.codex/project/policy.json',value)
        expect_error('sensitive autonomous '+action,lambda:load(root),ErrorCategory.POLICY_DENIED)
    write(root / '.codex/project/policy.json',policy)
    for p in policy['model_profiles']:
        p['configured']=True
    write(root / '.codex/project/policy.json',policy)
    assert load(root).configured_model('implementation').model_id == 'gpt-5.6-terra'
    counts['positive'] += 1
    policy['model_profiles'][0]['model_id']='unconfigured-other-model'
    write(root / '.codex/project/policy.json',policy)
    expect_error('configured catalog mismatch',lambda:load(root),ErrorCategory.INVALID_INPUT)

    claude_root=area / 'claude';fixture(claude_root,'.claude')
    assert load(claude_root).models.active_provider == 'anthropic'
    counts['positive'] += 1
    emit('positive Claude namespace',True)
    write(claude_root / '.codex/framework.json',inst)
    expect_error('ambiguous installations',lambda:config.load_installation_record(claude_root),ErrorCategory.INVALID_INPUT)

    # A real Windows junction cannot become a configuration read outside root.
    linked_root=area / 'linked';fixture(linked_root)
    external=area / 'external-project'
    shutil.move(str(linked_root / '.codex/project'), str(external))
    link=linked_root / '.codex/project'
    result=subprocess.run(['cmd','/c','mklink','/J',str(link),str(external)],capture_output=True,text=True)
    assert result.returncode == 0, result.stdout+result.stderr
    assert link.is_junction()
    expect_error('outside-root junction',lambda:load(linked_root),ErrorCategory.POLICY_DENIED)
    link.rmdir()

emit('probe totals',counts)
assert counts['defects'] == 2
assert not git('status','--porcelain=v1').strip()
assert git('rev-parse','HEAD').decode().strip() == c['head_oid']
emit('final source state',{'head':c['head_oid'],'clean':True})
