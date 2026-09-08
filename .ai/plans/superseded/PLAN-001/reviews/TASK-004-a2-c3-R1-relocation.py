"""Independent physical installed-bundle relocation and approval probes."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path('D:/Codex Projects/ai-engineering-template')
TREE = ROOT / '.worktrees/TASK-004-a2'
sys.dont_write_bytecode = True
sys.path.insert(0, str(TREE / 'src'))
import ai
import contracts
import install
import validate_foundation as vf

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def recursive(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [recursive(item, old, new) for item in value]
    if isinstance(value, dict):
        return {key: recursive(item, old, new) for key, item in value.items()}
    return value

def stale(project):
    try:
        vf.validate(project)
    except vf.ValidationFailure as exc:
        assert 'stale structural task digest' in str(exc), str(exc)
        return
    raise AssertionError('stale graph unexpectedly passed')

count = 0
for provider in ('codex', 'claude'):
    namespace = '.' + provider
    for separator in ('/', '\\'):
        with tempfile.TemporaryDirectory(prefix='r1-physical-') as tmp:
            project = Path(tmp) / 'project with spaces'
            other = Path(tmp) / 'unrelated cwd'
            other.mkdir()
            install.install(str(project), provider)
            toolroot = project / namespace / 'tools'
            probe = f"import pathlib,sys;sys.path.insert(0,{str(toolroot)!r});import ai,contracts,domain_values,validate_foundation;assert all(pathlib.Path(m.__file__).resolve().parent == pathlib.Path({str(toolroot)!r}).resolve() for m in (ai,contracts,domain_values,validate_foundation));assert validate_foundation.validate(pathlib.Path({str(project)!r}))['plans']==0"
            environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
            environment.pop('PYTHONPATH', None)
            result = subprocess.run([sys.executable, '-I', '-B', '-c', probe], cwd=other, env=environment, text=True, capture_output=True, shell=False)
            assert result.returncode == 0, result.stderr
            with contextlib.redirect_stdout(io.StringIO()):
                assert ai.main(['--project', str(project), 'plan', 'create', 'PLAN-101', '--title', 'Independent physical relocation']) == 0
            records = project / namespace
            bundle = records / 'plans/current/PLAN-101'
            task_path = bundle / 'tasks/current/TASK-001.json'
            task = read(task_path)
            base_ref = f'{namespace}/plans/current/PLAN-101/'
            task['input_contracts'] = [(base_ref + 'tasks/current/TASK-001.json').replace('/', separator)]
            task['output_contracts'] = [(base_ref + 'spec.json').replace('/', separator)]
            task['scope']['read_paths'] = [(base_ref + 'tasks/current/').replace('/', separator)]
            write(task_path, task)
            graph_path = bundle / 'graph.json'
            graph = read(graph_path)
            graph.update(status='approved', task_set_sha256=contracts.structural_task_digest([task]), review_ref=base_ref + 'reviews/isolation-review.json')
            write(graph_path, graph)
            review = read(TREE / 'schemas/examples/isolation-review.json')
            review.update(plan_id='PLAN-101', graph_revision=graph['revision'], task_set_sha256=graph['task_set_sha256'], verdict='pass')
            write(project / graph['review_ref'], review)
            plan = read(bundle / 'plan.json')
            plan['isolation_review_ref'] = graph['review_ref']
            write(bundle / 'plan.json', plan)
            assert vf.validate(project)['tasks'] == 1
            count += 1
            previous_bucket = 'current'
            for bucket in ('completed', 'archived'):
                target = records / 'plans' / bucket / 'PLAN-101'
                bundle.rename(target)
                bundle = target
                for path in bundle.rglob('*.json'):
                    value = read(path)
                    for sep in ('/', '\\'):
                        value = recursive(value, f'{namespace}/plans/{previous_bucket}/PLAN-101'.replace('/', sep), f'{namespace}/plans/{bucket}/PLAN-101'.replace('/', sep))
                        value = recursive(value, '/tasks/current/'.replace('/', sep), '/tasks/completed/'.replace('/', sep))
                    write(path, value)
                old_task = bundle / 'tasks/current/TASK-001.json'
                task_path = bundle / 'tasks/completed/TASK-001.json'
                if old_task.exists():
                    old_task.rename(task_path)
                task = read(task_path)
                task['status'] = 'completed'
                write(task_path, task)
                plan = read(bundle / 'plan.json')
                plan.update(status='completed', archived=bucket == 'archived')
                write(bundle / 'plan.json', plan)
                state = read(records / 'STATE.json')
                state.update(active_plans=[], completed_plans=['PLAN-101'] if bucket == 'completed' else [], archived_plans=['PLAN-101'] if bucket == 'archived' else [])
                write(records / 'STATE.json', state)
                assert vf.validate(project)['tasks'] == 1
                assert contracts.structural_task_digest([task]) == graph['task_set_sha256']
                count += 1
                mutated = copy.deepcopy(task)
                mutated['scope']['write_paths'][0] = 'src/reviewer_structure_change.py'
                write(task_path, mutated)
                stale(project)
                write(task_path, task)
                previous_bucket = bucket
            # Fresh fixture approval for each exact prior prose reproduction; then mutate only prose.
            for field, text in [('objective', '.codex/plans/current/PLAN-101/spec.json must remain the selected active specification.'), *[(field, text) for field in ('input_contracts', 'output_contracts') for text in ('.codex/plans/current/PLAN-101/spec.json: required shape comes from docs/contract.md', '.codex/plans/current/PLAN-101/spec.json requires review.md')]]:
                updated = copy.deepcopy(task)
                updated[field] = text if field == 'objective' else [text]
                write(task_path, updated)
                graph_path = bundle / 'graph.json'
                approved = read(graph_path)
                approved['task_set_sha256'] = contracts.structural_task_digest([updated])
                write(graph_path, approved)
                report_path = project / approved['review_ref']
                report = read(report_path)
                report['task_set_sha256'] = approved['task_set_sha256']
                write(report_path, report)
                vf.validate(project)
                changed_text = text.replace('/current/', '/completed/')
                updated[field] = changed_text if field == 'objective' else [changed_text]
                write(task_path, updated)
                stale(project)
        print(f'PASS {provider}, separator={separator!r}: installed origins isolated; current->completed->archived plan physically moved, task completed and both contract references/scope directory updated; scope and all five prior prose mutations reject unchanged approvals', flush=True)
assert count == 12
print('PASS 12 physical installed plan lifecycle states and 20 independent approved-graph prose rejection cases; all temporary projects removed', flush=True)
