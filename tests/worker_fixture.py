"""Deterministic subprocess worker used only by the runtime integration tests."""
import json
import os
from pathlib import Path
import subprocess
import time

context = json.loads(os.environ['ORCH_CONTEXT'])
root = Path(context['worktree'])
phase = context['phase']
mode = os.environ.get('WORKER_MODE', '')
findings = []
status = 'complete'


def write(path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')


if phase == 'build':
    for required in json.loads(os.environ.get('REQUIRE_FILES', '[]')):
        assert (root / required).is_file(), required
    time.sleep(float(os.environ.get('WORKER_DELAY', '0')))
    write('foreign.txt' if mode == 'outside' else f'src/{context["track"]}.txt', 'built\n')
    if mode == 'staged-outside':
        write('foreign.txt', 'must not commit\n')
        subprocess.run(['git', 'add', 'foreign.txt'], check=True)
        (root / 'foreign.txt').unlink()
    if mode == 'blocked-findings':
        status = 'blocked'
        findings = [dict(key=kind, kind=kind, severity='major', title=f'{kind} failure',
                         path=f'src/{context["track"]}.txt', detail='Confirmed finding from a blocked worker')
                    for kind in ('code', 'documentation')]
elif phase == 'fix':
    write('docs.md' if mode == 'fix-doc' else f'src/{context["track"]}.txt', 'fixed\n')
elif phase.startswith('review'):
    if mode in ('residual', 'fix-doc', 'docs-only', 'escalating'):
        findings = [dict(key=kind, kind=kind, severity='minor', title=f'{kind} finding',
                         path=f'src/{context["track"]}.txt' if kind == 'code' else 'docs.md',
                         detail='Concrete regression evidence for the fixture')
                    for kind in ('code', 'documentation', 'contract')]
        if mode == 'docs-only':
            findings = [f for f in findings if f['kind'] != 'code']
        if mode == 'escalating' and phase == 'review-2':
            findings[0].update(severity='critical', detail='New second-round evidence', path='src/critical.txt')
    if mode == 'mutating-review':
        write('docs.md', 'reviewer changed a document\n')

verdict = ('cannot_review' if mode == 'cannot-review' else
           'changes_requested' if findings else 'approved') if phase.startswith('review') else 'not_applicable'
Path(os.environ['ORCH_RESULT']).write_text(json.dumps(
    dict(status=status, verdict=verdict, summary=f'Completed {phase}', findings=findings)), encoding='utf-8')
