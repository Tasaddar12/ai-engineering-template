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
implementation_complete = True


def write(path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')


if phase == 'readiness':
    for plan in context['plans']:
        subprocess.check_output(['git', 'show', f"{context['base_sha']}:{plan}"])
    if mode == 'readiness-reject':
        status = 'blocked'
elif phase == 'build':
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
                         path=f'src/{context["track"]}.txt', detail='Confirmed finding from a blocked worker',
                         impact='missing_functionality' if kind == 'code' else 'editorial')
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
    if mode in ('residual', 'unrelated', 'fix-doc', 'docs-only', 'escalating', 'docs-fix-code', 'docs-corrected'):
        if mode != 'docs-corrected' or phase == 'docs-review-1':
            findings = [dict(key=kind, kind=kind, severity='minor', title=f'{kind} finding',
                             path='docs.md', detail='Documentation evidence for the fixture', impact='editorial')
                        for kind in ('documentation', 'contract')]
    if mode == 'docs-mutating-review':
        write('docs.md', 'documentation reviewer edited\n')
    if mode == 'cold-docs':
        assert not any(name in context['documentation_handoff'] for name in ('document', 'docs-review-1', 'docs-fix', 'docs-review-2'))
    if mode == 'incomplete-docs' or mode == 'missing-docs-review' and phase == 'docs-review-2':
        documentation_complete = False
elif phase.startswith('review'):
    if mode in ('residual', 'unrelated', 'fix-doc', 'escalating'):
        findings = [dict(key=kind, kind=kind, severity='minor', title=f'{kind} finding',
                         path=f'src/{context["track"]}.txt' if kind == 'code' else 'docs.md',
                         detail='Concrete regression evidence for the fixture',
                         impact='unrelated' if mode in ('unrelated', 'escalating') else 'missing_functionality')
                    for kind in ('code',)]
        if mode == 'escalating' and phase == 'review-2':
            findings[0].update(severity='critical', detail='New second-round evidence', path='src/critical.txt')
    if mode == 'mutating-review':
        write('docs.md', 'reviewer changed a document\n')
    if mode == 'out-of-scope' and phase == 'review-1':
        findings = [dict(key='outside', kind='code', severity='minor', title='Outside scope',
                         path='src/other.txt', detail='Known defect outside the owned source', impact='unrelated')]

if phase == 'build' and mode == 'research':
    write(context['research_paths'][0], '# Research\n\nInspected the fixture writer and its callers.\n')
if 'review-' in phase and mode == 'research':
    assert 'Inspected the fixture writer' in (root / context['research_paths'][0]).read_text()
    if phase.startswith('docs-review'):
        assert 'review-2' in context['documentation_handoff']
if phase == 'build' and mode == 'direct-finding':
    record_id = f"FIX-{context['reserved_ids']['FIX'][0]:03d}"
    write(f'.ai/fixes/open/{record_id}-worker.md', f'---\nid: {record_id}\ntier: plan\n---\n# Coding issue\n\nConfirmed fixture defect.\n')
if phase in ('document', 'docs-fix') and mode in ('source-doc', 'source-doc-code'):
    write(context['source_documentation_paths'][0], '\"\"\"Runtime module.\"\"\"\nVALUE = ' + ('2' if mode == 'source-doc-code' else '1') + '\n')
if phase in ('document', 'docs-fix') and mode == 'plan-notes':
    target = root / context['plans'][0]
    target.write_text(target.read_text() + '\n## Notes\n\nImplementation and SPEC coverage verified.\n')

if status == 'complete' and phase in ('build', 'document') and mode != 'staged-outside':
    for index, step in enumerate(context['steps']):
        if index:
            name = 'docs.md' if phase == 'document' else f'src/{context["track"]}.txt'
            target = root / name
            target.write_text(target.read_text() + step['id'] + '\n')
        subprocess.run(['git', 'add', '-A'], check=True)
        changed = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], text=True).strip()
        if changed and mode != 'uncommitted-step':
            subprocess.run(['git', 'commit', '-m', step['title'], '-m',
                            f"PLAN-Step: {step['plan']}#{step['id']}"], check=True)
    if mode == 'uncommitted-step':
        subprocess.run(['git', 'reset'], check=True)

coverage = [dict(plan=plan, spec='.ai/specs/SPEC-001-behavior.md', evidence='Inspected the fixture output behavior')
            for plan in context.get('plans', [])] if phase.startswith('docs-review') else []
if mode == 'no-spec-coverage':
    coverage = []
resolved = [dict(path=record, evidence='The delivered fixture implements this captured request')
            for contract in context.get('plan_contracts', {}).values() for record in contract['completed_intake']]
if phase.startswith('review') and mode == 'incomplete-code':
    implementation_complete = False

verdict = ('cannot_review' if mode == 'cannot-review' or mode == 'docs-cannot-review' and phase.startswith('docs-review') else
           'changes_requested' if findings else 'approved') if 'review-' in phase else 'not_applicable'
if phase == 'readiness':
    verdict = 'approved' if status == 'complete' else 'changes_requested'
Path(os.environ['ORCH_RESULT']).write_text(json.dumps(
    dict(status=status, verdict=verdict, summary=f'Completed {phase}', findings=findings,
         implementation_complete=implementation_complete, documentation_complete=documentation_complete,
         spec_coverage=coverage, resolved_intake=resolved)), encoding='utf-8')
