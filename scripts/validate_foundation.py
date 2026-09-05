"""Validate phase-one artifacts; not a runtime orchestration implementation."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise SystemExit('Install development dependencies: python -m pip install -e ".[dev]"') from exc

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def overlaps(left: str, right: str) -> bool:
    a, b = left.replace('\\', '/').casefold(), right.replace('\\', '/').casefold()
    return a == b or (a.endswith('/') and b.startswith(a)) or (b.endswith('/') and a.startswith(b))


def validate() -> dict[str, int]:
    schemas = {p.stem.removesuffix('.schema'): read(p) for p in (ROOT / 'schemas/v1').glob('*.json')}
    for schema in schemas.values():
        Draft202012Validator.check_schema(schema)
    count = 0
    for base in ['schemas/examples', '.ai']:
        for path in (ROOT / base).rglob('*.json'):
            artifact = read(path)
            Draft202012Validator(schemas[artifact['kind']], format_checker=FormatChecker()).validate(artifact)
            count += 1
    plan = read(ROOT / '.ai/plans/PLAN-001.json')
    graph = read(ROOT / plan['graph_ref'])
    tasks = {p.stem: read(p) for p in (ROOT / '.ai/tasks').glob('*.json')}
    assert set(tasks) == set(plan['task_ids']), 'Plan/task membership mismatch'
    nodes = {n['task_id']: n['depends_on'] for n in graph['nodes']}
    assert len(nodes) == len(graph['nodes']), 'Duplicate graph node'
    assert set(nodes) == set(tasks), 'Graph/task membership mismatch'
    ancestors: dict[str, set[str]] = {}

    def visit(task_id: str, trail: set[str]) -> set[str]:
        assert task_id not in trail, f'Cycle involving {task_id}'
        if task_id in ancestors:
            return ancestors[task_id]
        assert task_id in tasks, f'Missing dependency {task_id}'
        result: set[str] = set()
        for dep in tasks[task_id]['depends_on']:
            result.add(dep)
            result.update(visit(dep, trail | {task_id}))
        ancestors[task_id] = result
        return result

    for task_id, task in tasks.items():
        assert task_id == task['id'] and task['plan_id'] == plan['id']
        assert task['depends_on'] == nodes[task_id], f'{task_id}: mismatched dependencies'
        assert len(task['depends_on']) == len(set(task['depends_on'])), 'Duplicate dependency'
        visit(task_id, set())
        assert len(task['acceptance_criteria']) <= 3, f'{task_id}: needs size review'
        for command in task['validation_commands']:
            assert (ROOT / f'.ai/project/commands/{command}.json').exists(), f'Missing command {command}'
        for path in task['spec_refs'] + task['adr_refs'] + task['research_refs']:
            assert (ROOT / path).is_file(), f'{task_id}: missing reference {path}'
    pairs = 0
    ids = sorted(tasks)
    for i, left in enumerate(ids):
        for right in ids[i + 1:]:
            if left in ancestors[right] or right in ancestors[left]:
                continue
            pairs += 1
            a, b = tasks[left]['scope'], tasks[right]['scope']
            for p in a['write_paths']:
                for q in b['write_paths'] + b['read_paths']:
                    assert not overlaps(p, q), f'Unordered overlap {left}:{p} {right}:{q}'
            for p in b['write_paths']:
                for q in a['read_paths']:
                    assert not overlaps(p, q), f'Unordered overlap {right}:{p} {left}:{q}'
            assert not set(a['resources']) & set(b['resources']), f'Unordered resource overlap {left}/{right}'
    expected = {c['id'] for c in plan['acceptance_criteria']}
    covered = {a for task in tasks.values() for a in task['plan_acceptance_ids']}
    assert expected == covered, f'Acceptance coverage mismatch: {expected ^ covered}'
    digest = hashlib.sha256(json.dumps([tasks[t] for t in ids], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert graph['task_set_sha256'] == digest, 'Stale graph/task digest'
    if graph['status'] == 'approved':
        report = read(ROOT / graph['review_ref'])
        assert report['verdict'] == 'pass' and report['task_set_sha256'] == digest
        assert report['graph_revision'] == graph['revision']
        assert {c['id'] for c in report['checks']} == {f'ISO-{i:02}' for i in range(1, 13)}
        assert all(c['status'] == 'pass' for c in report['checks'])
        assert not any(f['severity'] in ['blocking', 'major'] and not f['resolved'] for f in report['findings'])
        assert plan['isolation_review_ref'] == graph['review_ref']
    links = 0
    for path in ROOT.rglob('*.md'):
        content = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
        for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)', content):
            if '://' in target or target.startswith('#'):
                continue
            destination = target.split('#', 1)[0]
            if destination:
                assert (path.parent / destination).exists(), f'{path.relative_to(ROOT)}: broken link {target}'
                links += 1
    return {'schemas': len(schemas), 'validated_artifacts': count, 'tasks': len(tasks), 'unordered_pairs_checked': pairs, 'local_links': links}


if __name__ == '__main__':
    print(json.dumps(validate(), indent=2))
