"""Deterministic subprocess worker used only by the runtime integration tests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

context = json.loads(os.environ['ORCH_CONTEXT'])
root = Path(context['worktree'])
phase = context['phase']
mode = os.environ.get('WORKER_MODE', '')
findings = []
status = 'complete'
documentation_complete = True


def write(path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')


if phase == 'build':
    for required in json.loads(os.environ.get('REQUIRE_FILES', '[]')):
        assert (root / required).is_file(), required
    time.sleep(float(os.environ.get('WORKER_DELAY', '0')))
    if mode == 'code-documentation-config':
        for config_path in context['code_paths']:
            write(config_path, 'planned configuration\n')
    elif mode != 'no-code':
        write('foreign.txt' if mode == 'outside' else f'src/{context["track"]}.txt', 'built\n')
    if mode == 'staged-outside':
        write('foreign.txt', 'must not commit\n')
        subprocess.run(['git', 'add', 'foreign.txt'], check=True)
        (root / 'foreign.txt').unlink()
    if mode == 'build-doc':
        write('docs.md', 'documentation too early\n')
    if mode == 'blocked-findings':
        status = 'blocked'
        findings = [dict(key=kind, kind=kind, severity='major', title=f'{kind} failure',
                         path=f'src/{context["track"]}.txt', detail='Confirmed finding from a blocked worker')
                    for kind in ('code', 'documentation')]
elif phase == 'fix':
    write('docs.md' if mode == 'fix-doc' else f'src/{context["track"]}.txt', 'fixed\n')
elif phase in ('document', 'docs-fix'):
    assert sys.argv[1] == context['model'] == context['documentation_model']
    if 'docs.md' in context['documentation_paths']:
        write('docs.md', 'documented\n' if phase == 'document' else 'documentation corrected\n')
    if mode == 'document-code' or mode == 'docs-fix-code' and phase == 'docs-fix':
        write(f'src/{context["track"]}.txt', 'late code edit\n')
    if mode == 'document-outside':
        write('other.md', 'outside documentation ownership\n')
    if mode == 'document-source':
        write('docs/code.py', 'print("source under docs")\n')
    if mode == 'document-cmake':
        write('docs/CMakeLists.txt', 'cmake_minimum_required(VERSION 3.20)\n')
    if mode == 'document-requirements':
        write('docs/requirements.txt', 'fixture-dependency==1.0\n')
    if mode == 'incomplete-docs':
        documentation_complete = False
elif phase.startswith('docs-review'):
    assert sys.argv[1] == context['model'] == context['documentation_model']
    if mode == 'docs-corrected' and phase == 'docs-review-1':
        documentation_complete = False
    if mode in ('residual', 'fix-doc', 'docs-only', 'escalating', 'docs-fix-code', 'docs-corrected'):
        if mode != 'docs-corrected' or phase == 'docs-review-1':
            findings = [dict(key=kind, kind=kind, severity='minor', title=f'{kind} finding',
                             path='docs.md', detail='Documentation evidence for the fixture')
                        for kind in ('documentation', 'contract')]
    if mode == 'docs-mutating-review':
        write('docs.md', 'documentation reviewer edited\n')
    if mode == 'missing-docs-review' and phase == 'docs-review-2':
        documentation_complete = False
elif phase.startswith('review'):
    if mode in ('residual', 'fix-doc', 'escalating'):
        findings = [dict(key=kind, kind=kind, severity='minor', title=f'{kind} finding',
                         path=f'src/{context["track"]}.txt' if kind == 'code' else 'docs.md',
                         detail='Concrete regression evidence for the fixture')
                    for kind in ('code',)]
        if mode == 'escalating' and phase == 'review-2':
            findings[0].update(severity='critical', detail='New second-round evidence', path='src/critical.txt')
    if mode == 'mutating-review':
        write('docs.md', 'reviewer changed a document\n')

verdict = ('cannot_review' if mode == 'cannot-review' or mode == 'docs-cannot-review' and phase.startswith('docs-review') else
           'changes_requested' if findings else 'approved') if 'review-' in phase else 'not_applicable'
Path(os.environ['ORCH_RESULT']).write_text(json.dumps(
    dict(status=status, verdict=verdict, summary=f'Completed {phase}', findings=findings,
         documentation_complete=documentation_complete)), encoding='utf-8')
