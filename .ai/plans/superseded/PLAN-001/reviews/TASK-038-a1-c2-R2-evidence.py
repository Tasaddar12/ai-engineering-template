"""Independent R2 identity and cross-contract checks; no candidate writes."""
from __future__ import annotations
import ast
import copy
import hashlib
import inspect
import itertools
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from dataclasses import FrozenInstanceError, replace

ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-038-a1'
PLAN = '.ai/plans/current/PLAN-001'
BASE = 'c945928da13cf9081dcf85c32c849cefdf24b97c'
HEAD = '6f2b12c3283ed7d6e3d4876020fe690c6e0061a3'
CREF = f'{PLAN}/reviews/candidates/CANDIDATE-TASK-038-a1-6f2b12c3283e.json'
R1REF = f'{PLAN}/reviews/TASK-038-a1-c2-R1.json'
STEM = f'{PLAN}/reviews/TASK-038-a1-c2-R2'
sys.dont_write_bytecode = True
sys.path.insert(0, str(WT / 'src'))
import config
import contracts
import domain_values
import install
import local_ports
from domain_values import DomainException, ErrorCategory

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(data):
    return hashlib.sha256(data).hexdigest()

def git(*args, cwd=WT):
    return subprocess.check_output(['git', *args], cwd=cwd)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')

def ok(message):
    print('PASS', message, flush=True)

negative_count = 0
def reject(label, operation, category=ErrorCategory.INVALID_INPUT, exception=DomainException):
    global negative_count
    try:
        operation()
    except exception as exc:
        if isinstance(exc, DomainException):
            assert exc.category == category and not exc.retryable, (label, exc)
        negative_count += 1
    else:
        raise AssertionError(f'Unexpected acceptance: {label}')

assert git('rev-parse', 'HEAD').decode().strip() == HEAD
assert git('rev-parse', 'HEAD', cwd=ROOT).decode().strip() == BASE
assert git('status', '--porcelain') == b''
assert git('merge-base', BASE, HEAD).decode().strip() == BASE
candidate = read(ROOT / CREF)
assert candidate['head_oid'] == HEAD and candidate['base_oid'] == BASE
assert candidate['diff_sha256'] == sha(git('diff', '--binary', BASE, HEAD))
assert candidate['fingerprint'] == sha(canonical({k:v for k,v in candidate.items() if k != 'fingerprint'}))
assert candidate['fingerprint'] == 'b19e2958568f1c67da0c70f28d5e50901143bf9baf627449ae96ea5a39345e0b'
for ref in candidate['context_refs']:
    assert sha(git('show', f"{HEAD}:{ref['path']}")) == ref['sha256'], ref
for ref in candidate['validation_refs']:
    assert sha((ROOT / ref['path']).read_bytes()) == ref['sha256'], ref
assert candidate['policy_model_digest'] == sha((ROOT / '.ai/project/policy.json').read_bytes() + (ROOT / '.ai/project/agent-models.json').read_bytes())
for relative in ('.ai/project/policy.json', '.ai/project/agent-models.json'):
    assert read(ROOT / relative) == read(WT / relative)
    assert git('show', f'{BASE}:{relative}') == git('show', f'{HEAD}:{relative}')
print('BASE', BASE, 'HEAD', HEAD)
print('FINGERPRINT', candidate['fingerprint'], 'DIFF', candidate['diff_sha256'])
print('CONTEXT_HASHES', len(candidate['context_refs']), 'VALIDATION_HASHES', len(candidate['validation_refs']))
ok('Exact clean head, current ROOT base, ancestry, raw binary diff, committed context, ROOT validation and policy/model bytes, canonical fingerprint')

paths = git('diff', '--name-only', BASE, HEAD).decode().splitlines()
assert set(paths) == {'src/config.py', 'tests/unit/config/test_config.py', f'{PLAN}/evidence/implementation/TASK-038.md'}
assert not git('diff', '--check', BASE, HEAD)
for path in paths:
    assert git('show', f'{HEAD}:{path}').replace(b'\r\n', b'\n') == (WT / path).read_bytes().replace(b'\r\n', b'\n')
print('CHANGED_PATHS', json.dumps(paths))
registry = contracts.load_contract_registry(WT / 'schemas/v1')
registry.validate(candidate)
r1 = read(ROOT / R1REF)
registry.validate(r1)
assert r1['verdict'] == 'pass' and r1['stage'] == 'implementation'
assert r1['candidate_ref'] == CREF and r1['candidate_fingerprint'] == candidate['fingerprint']
assert [c['id'] for c in r1['checks']] == [f'R1-{n:02}' for n in range(1, 12)]
assert all(c['status'] == 'pass' for c in r1['checks']) and not r1['findings']
assert len({'/root/r2_038_c2', r1['independent_session_id'], r1['implementation_session_id']}) == 3
for suffix in ('.json', '.md', '-evidence.py', '-evidence.txt', '-report-validation.txt'):
    path = ROOT / f'{PLAN}/reviews/TASK-038-a1-c2-R1{suffix}'
    print('R1_BOUND_FILE', path.name, sha(path.read_bytes()))
ok('Same-candidate schema-valid passing R1, complete 11 checks, three distinct sessions; R1 companion bytes recorded')

tasks = [read(path) for path in (WT / PLAN / 'tasks/current').glob('TASK-*.json')]
graph = read(WT / PLAN / 'graph.json')
isolation = read(WT / PLAN / 'reviews/r4-isolation-review.json')
digest = contracts.structural_task_digest(tasks)
assert graph['revision'] == isolation['graph_revision'] == 4
assert graph['status'] == 'approved' and isolation['verdict'] == 'pass'
assert digest == graph['task_set_sha256'] == isolation['task_set_sha256']
assert {t['id']:t['depends_on'] for t in tasks} == {n['task_id']:n['depends_on'] for n in graph['nodes']}
print('STRUCTURAL_DIGEST', digest)
for task, candidate_name, review_stem, source_files in (
    ('004', 'CANDIDATE-TASK-004-a2-e3c1177f993e', 'TASK-004-a2-c3', ['src/contracts.py','src/install.py','src/validate_foundation.py']),
    ('002', 'CANDIDATE-TASK-002-a1-460ab567d019', 'TASK-002-a1-c2', ['src/local_ports.py']),
    ('003', 'CANDIDATE-TASK-003-a1-d51b72ce71ea', 'TASK-003-a1-c2', ['src/workflow_ports.py']),
):
    accepted = read(WT / PLAN / f'reviews/candidates/{candidate_name}.json')
    oid = accepted['head_oid']
    assert git('merge-base', oid, BASE).decode().strip() == oid
    assert read(WT / PLAN / f'tasks/current/TASK-{task}.json')['status'] == 'accepted'
    for stage in ('R1','R2'):
        review = read(WT / PLAN / f'reviews/{review_stem}-{stage}.json')
        assert review['verdict'] == 'pass' and review['candidate_fingerprint'] == accepted['fingerprint']
    for source_file in source_files:
        assert git('show', f'{HEAD}:{source_file}') == git('show', f'{oid}:{source_file}')
    print('ACCEPTED_COMPATIBLE', task, oid, ','.join(source_files))
ok('Approved graph digest/dependencies and accepted prerequisite/sibling ancestry, review fingerprints and unchanged source')

assert str(inspect.signature(config.load_project_settings)) == "(root: 'Path', installation: 'InstallationRecord') -> 'ProjectSettings'"
for module in (config, contracts, domain_values, install, local_ports):
    assert Path(module.__file__).resolve().parent == (WT / 'src').resolve()
    print('IMPORT', module.__name__, module.__file__)
imports = {n.module for n in ast.walk(ast.parse((WT/'src/config.py').read_text())) if isinstance(n,ast.ImportFrom)}
assert {'contracts','domain_values'} <= imports
assert not {'local_ports','workflow_ports','orchestration_ports','ai','install'} & imports
ok('Frozen signature and explicit task-worktree imports; configuration has no runtime/port implementation dependencies')

command = read(WT / PLAN / 'commands/test.TASK-038.json')
argv = [sys.executable, *command['argv'][1:]]
run = subprocess.run(argv, cwd=WT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=180, shell=False)
print('DECLARED_ARGV', json.dumps(argv))
print(run.stdout, end='')
assert run.returncode == 0 and 'Ran 29 tests' in run.stdout and 'OK' in run.stdout
ok('Declared task suite: 29 tests, exit 0')

source_paths = [WT / p for p in ('.ai/framework.json','.ai/project/policy.json','.ai/project/agent-models.json')]
source_bytes = {p:p.read_bytes() for p in source_paths}
source = config.load_project_settings(WT, config.load_installation_record(WT))
assert source.namespace == '.ai'
assert source.policy.action_requirement('local_containers') is config.ActionRequirement.AUTONOMOUS
assert source.configured_model('implementation') is None
assert source.model_for_role('implementer').name == 'implementation_escalated'
ok('Real source .ai loads unchanged local_containers; manual recommendation does not create automatic binding')

snapshot_count = 0
def cross_contract(settings):
    global snapshot_count
    registry.validate(settings.installation.to_wire())
    assert set(settings.installation.to_wire()) == set(registry.schema('framework-installation')['properties'])
    policy_before = settings.policy.to_wire()
    for parallel, cycles, rewrites, invocations, sandbox in itertools.product((1,settings.policy.max_parallel),(1,settings.policy.max_review_cycles),(0,settings.policy.max_rewrites),(1,settings.policy.max_agent_invocations),(True,)):
        override = config.RunOverrides(parallel,cycles,rewrites,invocations,sandbox)
        effective = settings.effective_policy(override)
        wire = effective.to_wire()
        assert set(wire) == set(registry.schema('policy')['properties'])
        registry.validate(wire)
        payload = settings.resolve_run(override).to_payload()
        saved = config.decode_run_settings(json.loads(canonical(payload)))
        assert saved.to_payload() == payload
        assert settings.resolve_run(saved=saved) is saved
        registry.validate(settings.policy.with_run_settings(saved).to_wire())
        snapshot_count += 2
    assert settings.policy.to_wire() == policy_before
    saved = settings.resolve_run()
    changed = replace(settings, policy=settings.effective_policy(config.RunOverrides(1,1,0,1,True)))
    assert changed.resolve_run(saved=saved) is saved and saved.max_agent_invocations == settings.policy.max_agent_invocations
    reject('resume plus override',lambda:changed.resolve_run(config.RunOverrides(),saved=saved))
    reject('saved frozen',lambda:setattr(saved,'max_parallel',5),exception=FrozenInstanceError)
    for name in ('max_parallel','max_review_cycles','max_rewrites','max_agent_invocations'):
        reject(f'broaden {name}',lambda name=name:settings.resolve_run(config.RunOverrides(**{name:getattr(settings.policy,name)+1})),ErrorCategory.POLICY_DENIED)
    reject('sandbox weakening',lambda:changed.resolve_run(config.RunOverrides(required_sandbox=False)),ErrorCategory.POLICY_DENIED)
    for constructor in (config.RunSettings,config.RunOverrides):
        reject('zero configured invocations',lambda constructor=constructor:constructor(max_agent_invocations=0),exception=ValueError)
    for invalid in (0,-1,True,1.5,'1',None):
        reject('invalid saved invocation',lambda invalid=invalid:config.decode_run_settings(dict(saved.to_payload(),max_agent_invocations=invalid)))
    reject('saved unknown',lambda:config.decode_run_settings(dict(saved.to_payload(),invocations_used=0)))
    missing = saved.to_payload(); missing.pop('required_sandbox')
    reject('saved missing',lambda:config.decode_run_settings(missing))
    altered = saved.to_payload(); altered['max_agent_invocations'] = 999
    assert saved.max_agent_invocations != 999
    detached = settings.policy.to_wire(); detached['model_profiles'].clear()
    assert settings.policy.model_profiles

cross_contract(source)
for assistant, namespace in (('codex','.codex'),('claude','.claude')):
    with tempfile.TemporaryDirectory(prefix='r2-config-') as scratch:
        target = Path(scratch) / 'project'
        install.install(str(target),assistant)
        native = target / namespace / ('config.toml' if assistant == 'codex' else 'settings.json')
        native.write_text('deliberately invalid native configuration',encoding='utf-8')
        refs = [target/namespace/'framework.json',target/namespace/'project/policy.json',target/namespace/'project/agent-models.json',native]
        before = {p:p.read_bytes() for p in refs}
        settings = config.load_project_settings(target,config.load_installation_record(target))
        assert settings.namespace == namespace and settings.configured_model('review_high') is None
        cross_contract(settings)
        assert before == {p:p.read_bytes() for p in refs}
        print('FRESH_INSTALL',assistant,'read-only, native ignored, snapshot/resume boundaries passed')
ok(f'{snapshot_count} effective-policy registry validations across source/codex/claude; {negative_count} independent rejection checks')

# Verify existing persistence wire routes; this is representability, not durable IO.
payload = source.resolve_run(config.RunOverrides(1,1,0,1,True)).to_payload()
payload_ref = {'path':f'{PLAN}/evidence/run-settings-test.json','sha256':sha(canonical(payload))}
local_ports.ContentRef(**payload_ref)
event = dict(schema_version='1.0',kind='state-event',id='EVENT-R2',operation_id='OP-R2',generation=0,entity_id='RUN-R2',event_type='settings_saved',from_state=None,to_state='running',evidence_refs=[],created_at='2026-09-08T05:50:00Z',payload_ref=payload_ref)
registry.validate(event)
run_wire = dict(schema_version='1.0',kind='workflow-run',id='RUN-R2',plan_id='PLAN-001',status='running',phase='configured',graph_revision=4,expected_generation=0,policy_ref=f'{PLAN}/evidence/effective-policy-test.json',pending_operations=[],agent_run_ids=[],budgets=dict(max_agent_invocations=1,used_agent_invocations=0,max_rewrites=0,used_rewrites=0,max_elapsed_seconds=0),started_at=None,finished_at=None,pause_reason=None,resume_phase=None)
registry.validate(run_wire)
for key in ('max_parallel','max_review_cycles','required_sandbox'):
    reject('undeclared run field '+key,lambda key=key:registry.validate(dict(run_wire,**{key:payload[key]})),ErrorCategory.VALIDATION_FAILED)
command_value = dict(id='test.R2',argv=('python',' leading ','line\nbreak','tab\targ',' leading '),cwd_rule='worktree',timeout_seconds=1,max_output_bytes=100,permission_class='local_execute',environment_bindings=(),platforms=('windows','linux'),success_rule='exit_zero')
typed_command = local_ports.CommandDefinition(**command_value)
assert typed_command.argv == command_value['argv']
ok('Existing state-event content reference and workflow-run policy_ref are schema-representable; undeclared run fields rejected; accepted command argv semantics preserved')

assert source_bytes == {p:p.read_bytes() for p in source_paths}
assert git('status','--porcelain') == b''
assert git('rev-parse','HEAD').decode().strip() == HEAD
assert git('rev-parse','HEAD',cwd=ROOT).decode().strip() == BASE
ok('Final candidate still clean and frozen; source bytes unchanged')
print('RESULT PASS', 'SNAPSHOTS', snapshot_count,'EXPECTED_REJECTIONS',negative_count,flush=True)
