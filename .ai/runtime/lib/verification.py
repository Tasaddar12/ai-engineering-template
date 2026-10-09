"""Phase verification records, bounded acceptance currentness and checks."""

from datetime import datetime
import re
import subprocess

from . import verification_evidence as evidence

from .config import get as config_get
from .paths import read_text
from .phases import find_directory
from .results import VerbError, require
from .roadmap import Roadmap, as_number, display_number, pad, PLAN_ITEM, CHECKLIST_ITEM, FIELD
from .text import (split_frontmatter, FRONTMATTER, section_body, replace_section,
                   split_row, render_row, is_divider_row)
from .verification_checks import normalise, run

STATUSES = ("passed", "gaps_found", "human_needed")
CHECK_TIMEOUT = 600


def report_path(workspace, number):
    directory = find_directory(workspace, number)
    if directory is None:
        return None
    candidate = directory / (pad(number) + "-VERIFICATION.md")
    return candidate if candidate.is_file() else None


def status(workspace, number):
    """Whether a phase has a verification report, and what it concluded."""
    path = report_path(workspace, number)
    if path is None:
        return {"phase": display_number(number), "exists": False, "status": None,
                "file": None}
    frontmatter, body = split_frontmatter(read_text(path, ""))
    declared = str(frontmatter.get("status") or "").strip() or None
    return {
        "phase": display_number(number),
        "exists": True,
        "file": workspace.relative(path),
        "status": declared,
        "known_status": declared in STATUSES,
        "revision": frontmatter.get("revision"),
        "verified_at": str(frontmatter.get("verified_at") or ""),
        "findings": frontmatter.get("findings") or {},
        "has_body": bool(body.strip()),
    }


def resolve_file(workspace, number):
    """Path a verifier should write, whether or not it exists yet."""
    directory = find_directory(workspace, number)
    require(directory is not None, "no phase directory for " + str(number), "no-phase-dir")
    return {"file": workspace.relative(directory / (pad(number) + "-VERIFICATION.md")),
            "exists": report_path(workspace, number) is not None}


def configured_checks(workspace):
    commands = config_get(workspace, "verification.commands", []) or []
    return normalise(commands, CHECK_TIMEOUT)


def run_checks(workspace):
    """Run configured checks, reusing only matching, intact passing evidence."""
    commands = configured_checks(workspace)
    if not commands:
        return {"configured": False, "checks": [],
                "note": "verification.commands is empty in .planning/config.yaml"}
    return run(workspace, commands, config_get(workspace, "verification", {}), CHECK_TIMEOUT)

# Currentness and completion receipts intentionally fail closed outside the
# bounded transition language below. They never attest to source behavior.
BOOKKEEPING = {'.planning/STATE.md', '.planning/ROADMAP.md', '.planning/REQUIREMENTS.md'}


def committed_text(root, commit, path):
    return evidence.git(root, 'show', commit + ':' + path).decode('utf-8').replace('\r\n', '\n')


def report_metadata(root, path, commit):
    content = committed_text(root, commit, path)
    evidence.check(FRONTMATTER.match(content), 'verification report needs frontmatter')
    data, body = evidence.strict_frontmatter(content)
    evidence.check(type(data.get('schema')) is int and data['schema'] == 1, 'unsupported report schema')
    evidence.check(isinstance(data.get('phase'), str) and data['phase'] == path.split('/')[-2],
                   'report phase/path mismatch')
    evidence.check(isinstance(data.get('status'), str) and data['status'] in STATUSES, 'invalid verification status')
    evidence.revision(root, data.get('revision'))
    timestamp = data.get('verified_at')
    evidence.check(isinstance(timestamp, str) and datetime.fromisoformat(timestamp.replace('Z', '+00:00')).tzinfo
                   is not None, 'verified_at must be an ISO timestamp with timezone')
    clear = evidence.findings(data.get('findings'))
    evidence.check(body.strip(), 'verification report body missing')
    unverified = data.get('behavior_unverified', 0)
    evidence.check(type(unverified) is int and unverified >= 0, 'invalid behavior_unverified count')
    evidence.check(data['status'] == 'passed' and clear and unverified == 0,
                   'acceptance is failed, unresolved or requires human evidence')
    return data


def commit_delta(root, commit):
    parts = evidence.git(root, 'rev-list', '--parents', '-n', '1', commit).decode().split()
    evidence.check(len(parts) == 2, 'completion history must have exactly one parent per commit')
    paths = evidence.git(root, 'diff-tree', '--no-commit-id', '--name-only', '--no-renames',
                         '-r', '-z', parts[1], commit).split(b'\0')
    return parts[1], {p.decode('utf-8') for p in paths if p}


def current_report(root, path, target, allow_bookkeeping=True):
    data = report_metadata(root, path, target)
    source = data['revision']
    ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', source, target],
                              cwd=root, capture_output=True, timeout=30)
    evidence.check(ancestor.returncode == 0, 'tested revision is not an ancestor')
    entries = evidence.tree(root, target)
    report_blob = entries[path]
    commits = evidence.git(root, 'rev-list', '--reverse', source + '..' + target).decode().split()
    for commit in commits:
        before, paths = commit_delta(root, commit)
        if paths <= {path}:
            continue
        evidence.check(allow_bookkeeping and paths <= BOOKKEEPING, 'non-report source/config/history change')
        key = evidence.digest({'kind': 'bookkeeping', 'schema': 1, 'before': before, 'after': commit})
        receipt = evidence.load(root, key)
        evidence.check(isinstance(receipt, dict) and set(receipt) ==
                       {'schema', 'kind', 'before', 'after', 'report_path', 'report_blob',
                        'source_revision', 'delta', 'validator', 'validated_at'},
                       'missing or malformed bounded bookkeeping receipt')
        evidence.check(receipt['schema'] == 1 and receipt['kind'] == 'bookkeeping' and
                       receipt['before'] == before and receipt['after'] == commit and
                       receipt['report_path'] == path and receipt['report_blob'] == report_blob and
                       receipt['source_revision'] == source and receipt['validator'] == validator_digest(),
                       'bookkeeping provenance mismatch')
        # Replay schema and transition validation; a hand-written allowlist
        # receipt cannot substitute for the deterministic proof.
        evidence.check(receipt['delta'] == completion_delta(root, before, commit, path),
                       'bookkeeping delta validation mismatch')
    return data


def currentness(workspace, number):
    path = report_path(workspace, number)
    output = {'phase': display_number(number), 'current': False, 'status': 'never_run',
              'reason': 'missing_report', 'file': workspace.relative(path) if path else None}
    if path is None:
        return output
    root = workspace.root
    try:
        evidence.check(evidence.clean(root), 'dirty worktree')
        target = evidence.head(root)
        data = current_report(root, workspace.relative(path), target)
        evidence.check(evidence.clean(root) and evidence.head(root) == target, 'snapshot changed')
        return dict(output, current=True, status='passed', reason='validated',
                    revision=data['revision'], head=target, verified_at=data['verified_at'])
    except (VerbError, OSError, ValueError, TypeError, KeyError, RecursionError, subprocess.SubprocessError) as exc:
        return dict(output, status='stale_or_invalid', reason=str(exc))


def validator_digest():
    from pathlib import Path
    from .verification_checks import file_digest
    return evidence.digest([file_digest(Path(__file__)), file_digest(Path(evidence.__file__))])


def roadmap_at(root, commit):
    roadmap = Roadmap(type('Snapshot', (), {'roadmap': root / '.planning/ROADMAP.md'})())
    roadmap.content = committed_text(root, commit, '.planning/ROADMAP.md')
    phases = roadmap.phases()
    evidence.check(phases and len({as_number(p.number) for p in phases}) == len(phases),
                   'roadmap requires unique phase records')
    checklist = [as_number(m.group(4)) for m in CHECKLIST_ITEM.finditer(roadmap.content)]
    evidence.check(len(checklist) == len(set(checklist)) and set(checklist) == {as_number(p.number) for p in phases},
                   'roadmap requires one phase checklist item per phase')
    all_plans = [v['id'] for p in phases for v in p.plans]
    evidence.check(len(all_plans) == len(set(all_plans)), 'plan IDs must be unique across roadmap')
    for phase in phases:
        evidence.check(all(p['id'].startswith(phase.padded + '-') and re.fullmatch(r'[0-9]+(?:\.[0-9]+)?-[0-9]{2}', p['id'])
                           for p in phase.plans), 'plan ID must belong to phase')
        fields = [name.lower() for name, value in FIELD.findall(phase.body)]
        evidence.check(len(fields) == len(set(fields)), 'duplicate roadmap phase fields')
        evidence.check(phase.goal and phase.plans and len({p['id'] for p in phase.plans}) == len(phase.plans),
                       'phase needs a goal and unique plan checklist')
        # Reject malformed checklist lines which the tolerant reader ignores.
        for line in phase.body.splitlines():
            if re.match(r'^\s*-\s*\[', line):
                evidence.check(PLAN_ITEM.fullmatch(line), 'malformed phase plan checklist')
    return roadmap


def requirements_transition(before, after, phase, completed_requirements):
    old = section_body(before, 'Traceability', 2)
    new = section_body(after, 'Traceability', 2)
    evidence.check(old and new, 'requirements Traceability table required')
    a, b = old.splitlines(), new.splitlines()
    headers = [index for index, line in enumerate(a) if split_row(line) == ['Requirement', 'Phase', 'Status']]
    evidence.check(len(headers) == 1 and headers[0] + 1 < len(a) and is_divider_row(a[headers[0] + 1])
                   and len(split_row(a[headers[0] + 1])) == 3, 'requirements needs a valid three-column table header')
    evidence.check(len(a) == len(b), 'requirements rows added or removed')
    seen = set()
    updated = []
    for prior, current in zip(a, b):
        cells, changed = split_row(prior), split_row(current)
        if prior == current:
            updated.append(prior)
            if cells and cells[0] not in {'Requirement', 'ID'} and not re.fullmatch(r'[-: ]+', cells[0]):
                evidence.check(len(cells) == 3 and cells[2] in {'Pending', 'In progress', 'Complete', 'Deferred', 'Dropped'},
                               'malformed requirements row')
                evidence.check(cells[0] not in seen, 'duplicate requirement')
                seen.add(cells[0])
            continue
        evidence.check(cells and changed and len(cells) == len(changed) == 3,
                       'malformed requirements transition')
        evidence.check(cells[0] in phase.requirements and cells[0] in completed_requirements and cells[0] not in seen and
                       cells[:2] == changed[:2] and as_number(cells[1].removeprefix('Phase ')) == as_number(phase.number)
                       and cells[2] in {'Pending', 'In progress'} and changed[2] == 'Complete',
                       'only accepted phase requirements may advance to Complete')
        seen.add(cells[0])
        updated.append(render_row(changed))
    expected = replace_section(before, 'Traceability', '\n'.join(updated), 2)
    evidence.check(after == expected or (before == after), 'requirements narrative or formatting changed')


def state_schema(content, roadmap):
    evidence.check(FRONTMATTER.match(content), 'STATE needs frontmatter')
    metadata, body = evidence.strict_frontmatter(content)
    evidence.check(metadata.get('workflow_state_version') == '1.0' and
                   isinstance(metadata.get('status'), str) and metadata['status'] in {'planning', 'executing', 'complete', 'paused'}, 'invalid STATE schema/status')
    phases = roadmap.phases()
    total = sum(len(p.plans) for p in phases)
    done = sum(sum(v['done'] for v in p.plans) for p in phases)
    expected = dict(total_phases=len(phases), completed_phases=sum(p.status == 'Complete' for p in phases),
                    total_plans=total, completed_plans=done, percent=round(done * 100 / total) if total else 0)
    evidence.check(metadata.get('progress') == expected and
                   all(type(v) is int for v in metadata['progress'].values()), 'STATE progress is not derived from roadmap')
    for field in ('Phase', 'Plan', 'Status', 'Last activity', 'Last session', 'Stopped at', 'Resume file'):
        values = re.findall(r'^' + field + r':[^\n]+$', body, re.MULTILINE)
        evidence.check(len(values) == 1, 'STATE requires one nonempty ' + field)
    return metadata, body


def summary_coverage(root, commit, path, phase, report):
    """Only structured, automated passing coverage supports this bounded path.

    Legacy prose and human judgment need a specialist delta review instead.
    """
    accepted = evidence.strings(report.get('acceptance'), 'report acceptance', True)
    accepted_requirements = evidence.strings(report.get('requirements_completed'), 'report requirements_completed')
    completed = set()
    for plan in phase.plans:
        name = path.rsplit('/', 1)[0] + '/' + plan['id'] + '-SUMMARY.md'
        data, body = evidence.strict_frontmatter(committed_text(root, commit, name))
        evidence.check(data.get('phase') == path.split('/')[-2] and str(data.get('plan')).zfill(2) ==
                       plan['id'].rsplit('-', 1)[-1] and data.get('status') == 'complete' and body.strip(),
                       'SUMMARY phase/plan/status/body mismatch')
        acceptance = evidence.strings(data.get('acceptance'), 'SUMMARY acceptance', True)
        requirements = evidence.strings(data.get('requirements-completed'), 'SUMMARY requirements-completed')
        evidence.strings(data.get('documentation'), 'SUMMARY documentation')
        evidence.check(set(acceptance) <= set(accepted) and set(requirements) <= set(phase.requirements)
                       and set(requirements) <= set(accepted_requirements), 'SUMMARY exceeds accepted scope')
        coverage = data.get('coverage')
        evidence.check(isinstance(coverage, list) and coverage, 'SUMMARY structured coverage required')
        covered_requirements = set()
        identifiers = set()
        for item in coverage:
            evidence.check(isinstance(item, dict) and isinstance(item.get('id'), str) and item['id'].strip()
                           and item['id'] not in identifiers and isinstance(item.get('description'), str)
                           and item['description'].strip() and item.get('human_judgment') is False,
                           'SUMMARY coverage must be unique and automated; human judgment needs fresh review')
            identifiers.add(item['id'])
            checks = item.get('verification')
            evidence.check(isinstance(checks, list) and checks, 'SUMMARY verification evidence required')
            for entry in checks:
                evidence.check(isinstance(entry, dict) and entry.get('status') == 'pass'
                               and entry.get('kind') in {'unit', 'integration', 'e2e', 'automated_ui', 'other'}
                               and isinstance(entry.get('ref'), str) and entry['ref'].strip(),
                               'SUMMARY verification must be automated passing evidence')
            if 'requirement' in item:
                evidence.check(item['requirement'] in requirements, 'coverage requirement is not completed')
                covered_requirements.add(item['requirement'])
        evidence.check(set(requirements) <= covered_requirements, 'completed requirement lacks deliverable coverage')
        completed.update(requirements)
    return completed


def completion_delta(root, before, after, path):
    parent, paths = commit_delta(root, after)
    evidence.check(parent == before and paths and paths <= BOOKKEEPING, 'bookkeeping must be one bounded direct-child commit')
    data = report_metadata(root, path, before)
    evidence.check(evidence.tree(root, before)[path] == evidence.tree(root, after)[path], 'acceptance report changed')
    old_map, new_map = roadmap_at(root, before), roadmap_at(root, after)
    number = path.rsplit('/', 1)[-1].removesuffix('-VERIFICATION.md')
    phase = old_map.require_phase(number)
    expected = old_map.content
    for plan in phase.plans:
        old_map.content = old_map.set_plan(plan['id'], True)
    old_map.content = old_map.set_checklist(number, True)
    # Completion dates are validated as ISO dates, preserving other table cells.
    table = section_body(new_map.content, 'Progress', 2)
    expected_table = section_body(old_map.update_progress_table(), 'Progress', 2)
    if table or expected_table:
        date_mask = lambda value: re.sub(r'\d{4}-\d{2}-\d{2}(?=\s*\|)', '<date>', value)
        actual_rows, expected_rows = table.splitlines(), expected_table.splitlines()
        evidence.check(len(actual_rows) == len(expected_rows), 'roadmap progress rows added or removed')
        for actual_row, expected_row in zip(actual_rows, expected_rows):
            selected = re.match(r'^\|\s*' + re.escape(display_number(number)) + r'\.\s', actual_row)
            evidence.check(actual_row == expected_row or (selected and date_mask(actual_row) == date_mask(expected_row)),
                           'roadmap progress rows are not derived or another phase changed')
        for date in re.findall(r'\d{4}-\d{2}-\d{2}(?=\s*\|)', table):
            datetime.strptime(date, '%Y-%m-%d')
        old_map.content = replace_section(old_map.content, 'Progress', table, 2)
    evidence.check(new_map.content in {expected, old_map.content}, 'roadmap changed beyond accepted completion')
    old_req = committed_text(root, before, '.planning/REQUIREMENTS.md')
    new_req = committed_text(root, after, '.planning/REQUIREMENTS.md')
    completed = summary_coverage(root, before, path, phase, data)
    requirements_transition(old_req, new_req, phase, completed)
    old_state = committed_text(root, before, '.planning/STATE.md')
    new_state = committed_text(root, after, '.planning/STATE.md')
    # Use unmodified before roadmap for its original counters.
    a, old_body = state_schema(old_state, roadmap_at(root, before))
    b, new_body = state_schema(new_state, new_map)
    evidence.check({k: v for k, v in a.items() if k != 'progress'} ==
                   {k: v for k, v in b.items() if k != 'progress'}, 'STATE frontmatter changed beyond counters')
    variable = ('Plan', 'Status', 'Last activity', 'Last session', 'Stopped at', 'Resume file', 'Progress')
    mask = lambda body: re.sub(r'^(?:' + '|'.join(variable) + r'):[^\n]*$', '<session-field>', body, flags=re.MULTILINE)
    evidence.check(mask(old_body) == mask(new_body), 'STATE narrative or phase changed')
    final_phase = new_map.require_phase(number)
    evidence.check(final_phase.status == 'Complete', 'accepted phase must be complete after bookkeeping')
    for field in ('Phase',):
        value = re.search(r'^' + field + r':\s*(.*)$', new_body, re.MULTILINE).group(1)
        evidence.check(re.match(r'0*' + re.escape(display_number(number)) + r'(?:\s|$)', value), 'STATE is not on accepted phase')
    old_plan = re.search(r'^Plan:\s*(.*)$', old_body, re.MULTILINE).group(1)
    new_plan = re.search(r'^Plan:\s*(.*)$', new_body, re.MULTILINE).group(1)
    count = len(final_phase.plans)
    evidence.check(old_plan == new_plan or new_plan == f'{count} of {count} in current phase', 'invalid STATE plan counter')
    for field, pattern in (('Last activity', r'\d{4}-\d{2}-\d{2} [-—] .+'), ('Last session', r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}')):
        value = re.search(r'^' + field + r':\s*(.*)$', new_body, re.MULTILINE).group(1)
        evidence.check(re.fullmatch(pattern, value), 'invalid STATE ' + field)
    resume = re.search(r'^Resume file:\s*(.*)$', new_body, re.MULTILINE).group(1)
    evidence.literal(resume)
    if re.search(r'^Progress:', new_body, re.MULTILINE):
        progress = re.search(r'^Progress:.*?([0-9]+)%[ \t]*$', new_body, re.MULTILINE)
        evidence.check(progress and int(progress.group(1)) == b['progress']['percent'], 'invalid STATE progress display')
    status_line = re.search(r'^Status:\s*(.*)$', new_body, re.MULTILINE).group(1)
    if old_body != new_body:
        evidence.check(final_phase.status == 'Complete' and status_line in {'Complete', 'Phase complete', 'Ready for next phase', 'Preparing publication'},
                       'invalid STATE completion transition')
    delta = {name: {'before': evidence.tree(root, before)[name], 'after': evidence.tree(root, after)[name]}
             for name in sorted(paths)}
    return delta


def validate_bookkeeping(workspace, before, after):
    root = workspace.root
    evidence.revision(root, before)
    evidence.revision(root, after)
    evidence.check(evidence.clean(root) and evidence.head(root) == after, 'validator requires clean after HEAD')
    errors = []
    for path in evidence.tree(root, before):
        if not re.fullmatch(r'\.planning/phases/[^/]+/[0-9]+(?:\.[0-9]+)?-VERIFICATION\.md', path):
            continue
        try:
            data = current_report(root, path, before)
            delta = completion_delta(root, before, after, path)
            key = evidence.digest({'kind': 'bookkeeping', 'schema': 1, 'before': before, 'after': after})
            receipt = dict(schema=1, kind='bookkeeping', before=before, after=after, report_path=path,
                           report_blob=evidence.tree(root, before)[path], source_revision=data['revision'],
                           delta=delta, validator=validator_digest(), validated_at=datetime.now().astimezone().isoformat())
            evidence.check(evidence.clean(root) and evidence.head(root) == after, 'validation snapshot changed')
            return dict(valid=True, before=before, after=after, report_path=path,
                        receipt=evidence.save(root, key, receipt), delta=delta)
        except (VerbError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
            errors.append(str(exc))
    raise VerbError('bookkeeping rejected: ' + '; '.join(errors or ['no current passed acceptance report']), 'invalid-bookkeeping')
