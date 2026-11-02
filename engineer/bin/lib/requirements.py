"""Evidence-gated requirement status transitions preserving exact authored wording."""
from __future__ import annotations
import base64
import hashlib
import json
import re

from . import config, issues, phase_issues, records, security_tracking, verification
from .core import Args, Failure, digest, now, planning_lock, read, root, run, write, write_json

STATUSES = {'Pending', 'In Progress', 'Complete', 'Deferred', 'Blocked'}
IDENTIFIER = r'[A-Z][A-Z0-9_-]*-\d+(?:\.\d+)*'
ROW = re.compile(r'^(\|\s*(' + IDENTIFIER + r')\s*\|\s*([^|]+?)\s*\|)(\s*)([^|]+?)(\s*\|.*)$')


def rows(text):
    result, in_table, offset = [], False, 0
    for line in text.splitlines(keepends=True):
        cells = [c.strip().lower() for c in line.strip().strip('|').split('|')] if line.lstrip().startswith('|') else []
        if cells[:3] == ['requirement', 'phase', 'status']:
            in_table = True
        elif not cells:
            in_table = False
        elif in_table and (match := ROW.match(line.rstrip('\r\n'))):
            phase = re.search(r'\bPhase\s+([0-9]+[A-Za-z]?(?:\.\d+)*)\b', match[3], re.I)
            result.append({'id': match[2], 'phase_text': match[3].strip(), 'phase': records.number(phase[1]) if phase else None,
                           'status': match[5].strip(), 'start': offset + match.start(5), 'end': offset + match.end(5)})
        offset += len(line)
    identifiers = [r['id'] for r in result]
    if len(identifiers) != len(set(identifiers)):
        raise Failure('requirements-traceability-ambiguous', 'Each requirement must have exactly one traceability owner')
    return result


def _selected(args):
    values = args.all('requirements') or args.all('ids') or args.pos
    return list(dict.fromkeys(v for item in values for v in re.split(r'[,\s]+', str(item).strip('[]')) if v))


def _coverage(phase, selected):
    report = verification.resolve_file(phase)
    text = read(report)
    satisfied = set()
    for row in security_tracking.table_rows(text, ('requirement', 'status')):
        match = re.search(IDENTIFIER, row['requirement'])
        state = re.sub(r'[^a-z ]', '', row['status'].lower()).strip()
        blocking = row.get('blocking_issue', '').strip()
        if match and state in ('satisfied', 'passed', 'verified', 'complete') and blocking.lower() in ('', '-', 'none', 'n/a'):
            satisfied.add(match[0])
    missing = set(selected) - satisfied
    if missing:
        raise Failure('requirement-coverage-pending', 'Actual current verification must explicitly satisfy each requirement', requirements=sorted(missing), report=str(report))
    return report


def _gate(phase, selected, merged=False, pr=None):
    status = verification.status(Args([phase]))
    current = verification.current_evidence(phase)
    if status.get('status') != 'passed' or not current.get('current'):
        raise Failure('requirements-verification-pending', 'Task or SUMMARY completion cannot close requirements', phase=phase, evidence=current)
    handoff = phase_issues.handoff(Args([phase]))
    if not handoff['ready']:
        raise Failure('requirements-findings-pending', phase, errors=handoff['errors'])
    for finding in handoff['findings']:
        if finding.get('blocking') is True and str(finding.get('state', '')).lower() not in phase_issues.CLOSED:
            raise Failure('requirements-blocking-finding', str(finding['id']))
    directory = records.phase_dir(phase)
    enforce = config.lookup(config.load(), 'workflow.security_enforcement', True)
    if list(directory.glob('*-SECURITY.md')) or enforce and security_tracking.plan_threats(directory):
        security = security_tracking.command(Args([phase]), 'status')
        if not security.get('ready'):
            raise Failure('requirements-security-pending', phase, evidence=security)
    report = _coverage(phase, selected)
    evidence = {'phase': phase, 'verification': str(report), 'snapshot_digest': digest([report]),
                'verified_revision': current.get('verified_revision'), 'fingerprint': current.get('fingerprint')}
    if merged:
        if not pr:
            raise Failure('requirements-merged-pr-required', 'Closing phase requirements requires the actual merged canonical PR')
        pull = phase_issues.merged_pr(pr)
        phase_issues.audit_pr(phase, pull.get('body', ''))
        evidence['merged_pr'] = {'url': pull['url'], 'head': pull['headRefOid'], 'merge_commit': pull.get('mergeCommit'), 'merged_at': pull['mergedAt']}
    return evidence


def command(args, action):
    if action not in ('outstanding', 'set-status', 'mark-complete', 'complete', 'close-phase', 'reopen'):
        raise Failure('unsupported-requirements-action', action, 2)
    path = records.planning() / 'REQUIREMENTS.md'
    text = read(path)
    if not text:
        raise Failure('requirements-missing', str(path))
    trace = rows(text)
    if action == 'outstanding':
        pending = [{'Requirement': r['id'], 'Phase': r['phase_text'], 'Status': r['status']} for r in trace if r['status'] not in ('Complete', 'Deferred')]
        definitions = re.findall(r'(?m)^\s*[-*]\s*\[[ xX]\]\s*\*\*(' + IDENTIFIER + r')\*\*', text)
        missing = sorted(set(definitions) - {r['id'] for r in trace})
        return {'outstanding': pending, 'count': len(pending), 'unmapped': missing, 'wording_preserved': True}
    if action == 'set-status':
        selected, status = [args.need()], args.need(1)
        if status not in STATUSES:
            raise Failure('requirements-status-invalid', status, 2)
    elif action == 'close-phase':
        phase = records.number(args.need())
        selected = args.all('requirements') or [r['id'] for r in trace if r['phase'] == phase]
        if any(r['id'] in selected and r['phase'] != phase for r in trace):
            raise Failure('requirements-owner-mismatch', phase)
        status = 'Complete'
    else:
        selected = _selected(args)
        status = 'Pending' if action == 'reopen' else 'Complete'
    if not selected:
        raise Failure('requirements-selection-required', 'Select exact requirement IDs or a phase with traceability rows', 2)
    by_id = {r['id']: r for r in trace}
    unknown = set(selected) - set(by_id)
    if unknown:
        raise Failure('requirements-not-found', 'Requirements must retain their actual traceability owner', ids=sorted(unknown))
    if any(not re.fullmatch(IDENTIFIER, name) for name in selected):
        raise Failure('requirements-id-invalid', str(selected), 2)
    reason = str(args.get('reason', '')).strip()
    if (action == 'reopen' or status in ('Blocked', 'Deferred') or any(by_id[i]['status'] == 'Complete' and status != 'Complete' for i in selected)) and not reason:
        raise Failure('requirements-reason-required', 'Retain the actual reopening/blocking/deferral reason without rewriting requirement wording')
    groups = {}
    for identifier in selected:
        phase = by_id[identifier]['phase']
        if status == 'Complete' and not phase:
            raise Failure('requirement-phase-unresolved', identifier)
        groups.setdefault(phase, []).append(identifier)
    evidence = []
    if status == 'Complete':
        with issues.budget(180):
            for phase, identifiers in groups.items():
                evidence.append(_gate(phase, identifiers, action == 'close-phase', args.get('pr')))
    changed = [identifier for identifier in selected if by_id[identifier]['status'] != status]
    if not changed:
        return {'changed': [], 'updated': [], 'status': status, 'idempotent': True, 'evidence': evidence}
    updated = text
    for row in sorted((by_id[i] for i in changed), key=lambda item: -item['start']):
        updated = updated[:row['start']] + status + updated[row['end']:]
    # Change only the check mark. The authored requirement sentence remains byte-for-byte intact.
    for identifier in selected:
        pattern = r'(?m)^(\s*[-*]\s*\[)[ xX](\]\s*\*\*' + re.escape(identifier) + r'\*\*)'
        updated = re.sub(pattern, lambda m: m[1] + ('x' if status == 'Complete' else ' ') + m[2], updated)
    snapshot = digest([path])
    with planning_lock():
        if read(path) != text or digest([path]) != snapshot:
            raise Failure('requirements-source-drift', 'Requirements changed before the status-only transition')
        for item in evidence:
            if digest([item['verification']]) != item['snapshot_digest']:
                raise Failure('requirements-verification-drift', item['phase'])
        token = hashlib.sha256((snapshot + json.dumps(selected) + status).encode()).hexdigest()
        journal = security_tracking._runtime_dir().parent / 'requirements-transitions' / (token + '.json')
        record = {'ids': selected, 'before': {i: by_id[i]['status'] for i in selected}, 'status': status,
                  'reason': reason, 'evidence': evidence, 'created': now(), 'source_digest': snapshot,
                  'original': base64.b64encode(path.read_bytes()).decode(), 'state': 'applying'}
        write_json(journal, record)
        write(path, updated)
        record.update(state='complete', completed=now(), result_digest=digest([path]))
        write_json(journal, record)
    result = {'changed': changed, 'updated': changed, 'unknown': [], 'status': status, 'evidence': evidence,
              'wording_preserved': True, 'traceability_preserved': True, 'phase_closed': False}
    if action == 'set-status':
        result.update(id=selected[0], previous=by_id[selected[0]]['status'])
    return result
