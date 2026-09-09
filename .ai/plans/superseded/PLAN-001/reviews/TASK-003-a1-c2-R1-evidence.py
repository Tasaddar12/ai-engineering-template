"""Independent R1 verification. Writes only this companion evidence transcript."""
from __future__ import annotations

import ast
from dataclasses import fields, is_dataclass, replace
from datetime import UTC, datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('D:/Codex Projects/ai-engineering-template')
WT = ROOT / '.worktrees/TASK-003-a1'
PLAN = '.ai/plans/current/PLAN-001'
CANDIDATE = PLAN + '/reviews/candidates/CANDIDATE-TASK-003-a1-d51b72ce71ea.json'
BASE = '3c8092625812b86a1e9bc7c7bfd454c38ee759e0'
HEAD = 'd51b72ce71ea3ac3ad31adf41e3eddc84738ac0b'
PYTHON = ROOT / '.ai/local/full-plan-venv/Scripts/python.exe'
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
TRANSCRIPT: list[str] = []
COUNTS = {'accepted': 0, 'rejected': 0}


def log(value):
    text = value if isinstance(value, str) else json.dumps(value, sort_keys=True)
    TRANSCRIPT.append(text)
    print(text)


def command(argv, expected=0):
    result = subprocess.run(argv, cwd=WT, env=ENV, shell=False, capture_output=True)
    assert result.returncode == expected, (argv, result.returncode, result.stderr)
    return result


def git(*argv):
    return command(['git', *argv]).stdout


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def accept(label, operation):
    value = operation()
    COUNTS['accepted'] += 1
    log('ACCEPT ' + label)
    return value


def reject(label, operation):
    try:
        operation()
    except (TypeError, ValueError) as exc:
        COUNTS['rejected'] += 1
        log('REJECT ' + label + ': ' + str(exc))
    else:
        raise AssertionError('Unexpectedly accepted: ' + label)


def main():
    log({'invocation': '/root/r1_003_c2', 'started_at': datetime.now(UTC).isoformat(), 'cwd': str(WT)})
    candidate = json.loads((ROOT / CANDIDATE).read_bytes())
    assert git('rev-parse', 'HEAD').decode().strip() == HEAD == candidate['head_oid']
    assert candidate['base_oid'] == BASE
    assert git('status', '--porcelain') == b''
    git('merge-base', '--is-ancestor', BASE, HEAD)
    diff = git('diff', '--binary', BASE, HEAD)
    assert sha(diff) == candidate['diff_sha256']
    changed = git('diff', '--name-status', BASE, HEAD).decode().splitlines()
    paths = ['src/workflow_ports.py', 'tests/unit/domain_workflow_ports/test_workflow_ports.py',
             PLAN + '/evidence/implementation/TASK-003.md']
    assert sorted(changed) == sorted('A\t' + path for path in paths)
    for path in paths:
        assert (WT / path).read_bytes().replace(b'\r\n', b'\n') == git('show', HEAD + ':' + path).replace(b'\r\n', b'\n')
    git('diff', '--check', BASE, HEAD)
    hashes = []
    for group, location in [('context_refs', WT), ('validation_refs', ROOT)]:
        for ref in candidate[group]:
            observed = sha((location / ref['path']).read_bytes())
            assert observed == ref['sha256'], (group, ref['path'], observed)
            hashes.append(dict(group=group, path=ref['path'], sha256=observed))
    policy_paths = ['.ai/project/policy.json', '.ai/project/agent-models.json']
    digest = sha(b''.join((ROOT / path).read_bytes() for path in policy_paths))
    assert digest == candidate['policy_model_digest']
    for path in policy_paths + [ref['path'] for ref in candidate['context_refs']]:
        assert (ROOT / path).read_bytes().replace(b'\r\n', b'\n') == (WT / path).read_bytes().replace(b'\r\n', b'\n'), path
    fingerprint = sha(canonical({key: value for key, value in candidate.items() if key != 'fingerprint'}))
    assert fingerprint == candidate['fingerprint'] == '7eed3420cb4bf419205dd2a64d08acfab8cf7d75f7068b7a8b28e7c6ff5f420f'
    sys.path.insert(0, str(WT / 'src'))
    from ai import structural_task_digest
    graph = json.loads((WT / PLAN / 'graph.json').read_bytes())
    tasks = [json.loads(path.read_bytes()) for bucket in ['current', 'completed']
             for path in (WT / PLAN / 'tasks' / bucket).glob('TASK-*.json')]
    isolation = json.loads((WT / PLAN / 'reviews/r4-isolation-review.json').read_bytes())
    assert len(tasks) == 39
    task_digest = structural_task_digest(tasks)
    assert task_digest == graph['task_set_sha256'] == isolation['task_set_sha256']
    assert graph['revision'] == isolation['graph_revision'] == candidate['graph_revision'] == 4
    assert isolation['verdict'] == 'pass' and all(c['status'] == 'pass' for c in isolation['checks'])
    dependency = next(task for task in tasks if task['id'] == 'TASK-001')
    assert dependency['status'] == 'accepted'
    assert next(task for task in tasks if task['id'] == 'TASK-003')['depends_on'] == ['TASK-001']
    git('merge-base', '--is-ancestor', 'd1fc917466410febc6238479e65816dd39591a4f', BASE)
    assert git('show', BASE + ':src/domain_values.py') == git('show', 'd1fc917466410febc6238479e65816dd39591a4f:src/domain_values.py')
    log({'base_oid': BASE, 'head_oid': HEAD, 'changed': changed, 'diff_sha256': sha(diff),
         'context_and_validation_hashes': hashes, 'policy_model_digest': digest,
         'fingerprint': fingerprint, 'structural_task_digest': task_digest,
         'isolation': isolation['id'], 'accepted_dependency': 'TASK-001',
         'git_diff_check': 'exit 0', 'root_frozen_comparison': 'equal after CRLF-only normalization'})

    definition = json.loads((WT / PLAN / 'commands/test.TASK-003.json').read_bytes())
    argv = [str(PYTHON), *definition['argv'][1:]]
    result = command(argv)
    log({'declared_command': 'test.TASK-003', 'argv': argv, 'exit_code': result.returncode,
         'stdout': result.stdout.decode(), 'stderr': result.stderr.decode()})
    assert b'Ran 26 tests' in result.stderr and b'OK' in result.stderr

    import workflow_ports as p
    import domain_values as v
    module_spec = importlib.util.spec_from_file_location('r1_fixture', WT / 'tests/unit/domain_workflow_ports/test_workflow_ports.py')
    fixture = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(fixture)
    h, success_run, output = fixture.successful_agent_values()
    ev = (fixture.evidence('independent-r1'),)
    err = fixture.error(v.ErrorCategory.TRANSIENT_PROVIDER)
    runs = {
        v.AgentRunStatus.SUCCEEDED: success_run,
        v.AgentRunStatus.QUEUED: replace(success_run, status='queued', started_at=None, finished_at=None, actual_model=None, output_ref=None),
        v.AgentRunStatus.RUNNING: replace(success_run, status='running', finished_at=None, output_ref=None),
        v.AgentRunStatus.FAILED: replace(success_run, status='failed', error_category='transient_provider', output_ref=None),
        v.AgentRunStatus.CANCELLED: replace(success_run, status='cancelled', started_at=None, actual_model=None, output_ref=None),
        v.AgentRunStatus.UNKNOWN: replace(success_run, status='unknown', started_at=None, finished_at=None, actual_model=None, error_category='transient_provider', output_ref=None),
    }
    for status, run in runs.items():
        observation_error = err if status in {v.AgentRunStatus.FAILED, v.AgentRunStatus.CANCELLED, v.AgentRunStatus.UNKNOWN} else None
        good_output = output if status is v.AgentRunStatus.SUCCEEDED else None
        def observe(handle=h, record=run, structured=good_output):
            return p.AgentObservation(status, handle, record, structured, ev, observation_error)
        accept('valid agent status ' + status.value, observe)
        reject('conflicting known external handles at ' + status.value,
               lambda: observe(record=replace(run, external_handle='other-provider-job')))
        for handle_value, run_value in [(None, 'external-1'), ('external-1', None), (None, None)]:
            accept('unknown external handle combinations at ' + status.value,
                   lambda: observe(handle=replace(h, external_handle=handle_value), record=replace(run, external_handle=run_value)))
        if status is not v.AgentRunStatus.SUCCEEDED:
            for output_status in v.AgentOutputStatus:
                reject('non-success poll ' + status.value + ' with output ' + output_status.value,
                       lambda: observe(structured=replace(output, status=output_status)))
    for key, value in [('attempt_id', 'TASK-003-a2'), ('adapter_id', 'other-adapter'), ('lease_generation', 99)]:
        reject('agent identity ' + key, lambda: p.AgentObservation('succeeded', h, replace(success_run, **{key: value}), output, ev))
    for key in ['request_id', 'attempt_id']:
        reject('output identity ' + key, lambda: p.AgentObservation('succeeded', h, success_run, replace(output, **{key: 'other'}), ev))
    for key in ['model_id', 'invocation_id']:
        reject('success output provenance ' + key,
               lambda: p.AgentObservation('succeeded', h, success_run, replace(output, actual_model=replace(output.actual_model, **{key: 'other'})), ev))
    reject('success without evidence', lambda: p.AgentObservation('succeeded', h, success_run, output, ()))
    reject('success without output', lambda: p.AgentObservation('succeeded', h, success_run, None, ev))
    for status in p.CancelStatus:
        confirmed = status in {p.CancelStatus.CANCELLED, p.CancelStatus.ALREADY_TERMINAL}
        cancel_error = err if status in {p.CancelStatus.UNKNOWN, p.CancelStatus.FAILED} else None
        accept('valid cancellation ' + status.value, lambda: p.CancelObservation(status, h, confirmed, ev, cancel_error))
        reject('contradictory cancellation quiesced ' + status.value, lambda: p.CancelObservation(status, h, not confirmed, ev, cancel_error))
        if confirmed:
            reject('confirmed cancellation without evidence ' + status.value, lambda: p.CancelObservation(status, h, True, ()))

    dh, state = fixture.delivery_values()
    for status in p.DeliveryObservationStatus:
        delivery_error = None if status is p.DeliveryObservationStatus.OBSERVED else fixture.error(
            v.ErrorCategory.AMBIGUOUS_SIDE_EFFECT if status is p.DeliveryObservationStatus.AMBIGUOUS else v.ErrorCategory.TRANSIENT_PROVIDER)
        def delivery(handle=dh, record=state):
            return p.DeliveryObservation(status, handle, record, ev, delivery_error)
        accept('matching PR at ' + status.value, delivery)
        reject('conflicting known PR numbers at ' + status.value, lambda: delivery(record=replace(state, number=13)))
        accept('unknown PR discovery and remote drift at ' + status.value,
               lambda: delivery(handle=replace(dh, number=None, url=None), record=replace(state, observed_head_oid='e' * 40, observed_base_oid='d' * 40, base_branch='release')))
    for key, value in [('plan_id', 'PLAN-002'), ('run_id', 'other-run'), ('operation_id', 'other-op'), ('repository', 'other/repo'), ('head_branch', 'other-head')]:
        reject('delivery identity ' + key, lambda: p.DeliveryObservation('observed', dh, replace(state, **{key: value}), ev))
    reject('observed delivery without state', lambda: p.DeliveryObservation('observed', dh, None, ev))
    reject('observed delivery without evidence', lambda: p.DeliveryObservation('observed', dh, state, ()))
    reject('ambiguity without ambiguity category', lambda: p.DeliveryObservation('ambiguous', dh, None, ev, err))

    for count in [None, 0, -1, True]:
        reject('invalid observed unittest count ' + repr(count),
               lambda: p.ValidationCheck('test.TASK-003', 'unittest_nonzero_count', 'passed', ev[0], count))
    for status in [v.ValidationStatus.FAILED, v.ValidationStatus.UNKNOWN, v.ValidationStatus.NOT_RUN]:
        reject('non-passing validation without error ' + status.value,
               lambda: p.ValidationCheck('test.TASK-003', 'exit_zero', status, ev[0]))
    reject('passing validation without evidence', lambda: p.ValidationCheck('test.TASK-003', 'exit_zero', 'passed', None))
    for oid in ['', 'A' * 40, 'a' * 39, 'a' * 41, 'g' * 64, 'a' * 65]:
        reject('invalid revision ' + repr(oid), lambda: replace(fixture.agent_request(), current_oid=oid))
    for path in ['../escape', 'C:/absolute', 'folder/', 'NUL', 'valid/file:stream']:
        reject('unsafe content reference ' + path, lambda: p.ContentRef(path, fixture.DIGEST))

    record = p.ReviewResultRecord('review-result', 'implementation', 'review-request', 'TASK-003', 'PLAN-001',
                                 'candidate:PLAN-001:one', fixture.DIGEST, 'fail', fixture.model(),
                                 'review-session', 'implementation-session', None, 'PLAN-001-v1',
                                 [p.ReviewCheck('R1-01', 'fail', 'missing evidence', [])], [], fixture.NOW)
    review = p.ReviewResult('succeeded', 'project-1', 'PLAN-001', 'run-1', 'review-op', 'review-request',
                          fixture.DIGEST, record, ev)
    accept('transport success with review fail verdict', lambda: review)
    reject('self review', lambda: replace(record, independent_session_id='implementation-session'))
    reject('pass review with failed check', lambda: replace(record, verdict='pass'))
    for key, value in [('request_id', 'other-request'), ('plan_id', 'PLAN-002'), ('candidate_fingerprint', 'f' * 64)]:
        reject('review result binding ' + key, lambda: replace(review, record=replace(record, **{key: value})))
    reject('review result without evidence', lambda: replace(review, evidence_refs=()))
    reject('review result without record', lambda: replace(review, record=None))

    tree = ast.parse((WT / 'src/workflow_ports.py').read_text())
    protocol_methods = {node.name: [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
                        for node in tree.body if isinstance(node, ast.ClassDef)
                        and any(isinstance(base, ast.Name) and base.id == 'Protocol' for base in node.bases)}
    assert protocol_methods == {'AgentAdapter': ['start', 'poll', 'cancel'], 'ContextBuilder': ['build'],
                                'Validator': ['run'], 'ReviewService': ['evaluate'],
                                'DeliveryAdapter': ['prepare', 'publish', 'observe']}
    dataclasses = [getattr(p, node.name) for node in tree.body if isinstance(node, ast.ClassDef)
                   and is_dataclass(getattr(p, node.name))]
    assert len(dataclasses) == 27
    assert all(value.__dataclass_params__.frozen and hasattr(value, '__slots__') for value in dataclasses)
    assert git('status', '--porcelain') == b'' and git('rev-parse', 'HEAD').decode().strip() == HEAD
    log({'independent_boundary_results': COUNTS, 'frozen_dataclasses': len(dataclasses),
         'protocol_methods': protocol_methods, 'final_worktree': 'clean at exact head',
         'completed_at': datetime.now(UTC).isoformat()})


if __name__ == '__main__':
    try:
        main()
    finally:
        Path(__file__).with_suffix('.txt').write_text('\n'.join(TRANSCRIPT) + '\n', encoding='utf-8')
