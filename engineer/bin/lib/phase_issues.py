"""Evidence-bound phase findings, human acceptance and merged-todo reconciliation."""
from __future__ import annotations
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from . import delivery, issue_format, issues, records, repository
from .core import Args, Failure, digest, load_json, now, planning_lock, read, root, run, safe_path, write, write_json
from .text import join_frontmatter, split_frontmatter

SUFFIXES = ('-SUMMARY.md', '-REVIEW.md', '-VERIFICATION.md', '-SECURITY.md', '-VALIDATION.md', '-UAT.md')
CLOSED = {'resolved', 'fixed', 'dismissed'}


def artifacts(directory):
    return sorted(p for p in directory.rglob('*.md') if p.is_file() and not p.is_symlink() and p.name.endswith(SUFFIXES))


def _refs(entries):
    if not isinstance(entries, list):
        raise Failure('invalid-finding-declarations', 'An explicit issue_refs array is required')
    ids = set()
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get('id'), str) or not entry['id'].strip() or entry['id'] in ids:
            raise Failure('invalid-finding-declarations', 'Finding IDs must be unique nonempty strings')
        ids.add(entry['id'])
        state = str(entry.get('state', entry.get('status', 'unresolved'))).lower()
        if state in CLOSED and (not entry.get('evidence') or not entry.get('reason')):
            raise Failure('finding-resolution-unproved', 'Resolved entries require both actual evidence and reason', id=entry['id'])
        url = entry.get('url', entry.get('issue_url'))
        if url:
            repository.require_url(str(url).split('#')[0], 'issues')
        elif state not in CLOSED:
            raise Failure('finding-canonical-target-pending', 'Unresolved findings need a canonical published issue URL', id=entry['id'])
    return entries


def declare(args):
    directory = records.phase_dir(args.need())
    path = safe_path(directory / args.need(1))
    if not path.is_relative_to(directory) or not path.is_file() or not path.name.endswith(SUFFIXES):
        raise Failure('invalid-phase-artifact', str(path))
    metadata, _ = split_frontmatter(read(path))
    snapshot = digest([path])
    if not args.has('entries-file'):
        return {'snapshotDigest': snapshot, 'entries': metadata.get('issue_refs', []), 'declared': 'issue_refs' in metadata, 'path': str(path)}
    entries = json.loads(read(safe_path(args.get('entries-file'))))
    # Pending entries may be authored before publication; handoff, not declaration, owns readiness.
    if not isinstance(entries, list) or any(not isinstance(e, dict) or not isinstance(e.get('id'), str) or not e['id'].strip() for e in entries):
        raise Failure('invalid-finding-declarations', 'Supply complete identified finding objects')
    if len({e['id'] for e in entries}) != len(entries):
        raise Failure('duplicate-finding-id', str(path))
    with planning_lock():
        if args.get('expect-digest') != snapshot or digest([path]) != snapshot:
            raise Failure('phase-artifact-drift', 'Declaration snapshot changed')
        metadata, body = split_frontmatter(read(path))
        previous = {e['id']: e for e in metadata.get('issue_refs', []) if isinstance(e, dict) and e.get('id')}
        for entry in entries:
            old = previous.get(entry['id'], {})
            prior = old.get('url', old.get('issue_url'))
            target = entry.get('url', entry.get('issue_url'))
            if prior and prior != target:
                raise Failure('canonical-relationship-drift', 'Preserve the established finding relationship', id=entry['id'], existing=prior)
            if target:
                repository.require_url(str(target).split('#')[0], 'issues')
        if set(previous) - {e['id'] for e in entries}:
            raise Failure('finding-history-removal-refused', 'Retain prior findings with a resolved evidence-backed disposition')
        metadata['issue_refs'] = entries
        write(path, join_frontmatter(metadata, body))
    return {'updated': True, 'entries': entries, 'path': str(path), 'snapshotDigest': digest([path])}


def _handoff(args):
    directory = records.phase_dir(args.need())
    errors, findings = [], []
    plans = sorted(directory.glob('*-PLAN.md'))
    revision = run(['git', 'rev-parse', 'HEAD'], root(), timeout=30).stdout.strip()
    if not plans:
        errors.append({'reason': 'Phase has no actual plans'})
    for plan in plans:
        summary = plan.with_name(plan.name[:-len('-PLAN.md')] + '-SUMMARY.md')
        metadata, _ = split_frontmatter(read(summary))
        if not summary.exists() or metadata.get('status') != 'complete':
            errors.append({'file': str(summary), 'reason': 'Actual complete SUMMARY is required'})
            continue
        committed = run(['git', 'show', revision + ':' + str(summary.relative_to(root()))], root(), check=False, timeout=30)
        if committed.returncode or committed.stdout != read(summary):
            errors.append({'file': str(summary), 'reason': 'Complete SUMMARY must match committed evidence at captured HEAD'})
    provider_cache = {}
    for path in artifacts(directory):
        metadata, body = split_frontmatter(read(path))
        try:
            entries = _refs(metadata.get('issue_refs'))
        except Failure as exc:
            errors.append({'file': str(path), 'reason': exc.message, 'error': exc.code, **exc.details})
            continue
        declared = {e['id'] for e in entries}
        for entry in entries:
            url = entry.get('url', entry.get('issue_url'))
            if url:
                base = str(url).split('#')[0]
                try:
                    if base not in provider_cache:
                        provider_cache[base] = issues.issue_get(base, repository.identity())
                    if provider_cache[base].get('state', '').upper() == 'CLOSED' and str(entry.get('state', '')).lower() not in CLOSED:
                        errors.append({'file': str(path), 'id': entry['id'], 'reason': 'Closed unresolved match needs explicit reconciliation; do not duplicate it'})
                except Failure as exc:
                    errors.append({'file': str(path), 'id': entry['id'], 'reason': exc.message, 'error': exc.code})
            if str(entry.get('state', '')).lower() in CLOSED:
                evidence = entry.get('evidence')
                citations = evidence if isinstance(evidence, list) else evidence.get('citations', []) if isinstance(evidence, dict) else []
                from .security_tracking import _citation
                if not citations or not all(_citation(c, revision) for c in citations):
                    errors.append({'file': str(path), 'id': entry['id'], 'reason': 'Resolution needs actual cited commits and paths, not completion narration'})
        # Read only explicit finding headers, never turn narrative tone into an outcome.
        visible = '\n'.join(issue_format.visible_lines(body))
        actual = set(re.findall(r'(?m)^#{2,4}\s+((?:F|SEC|UAT|GAP|BUG)-[A-Za-z0-9_.-]+)\b', visible))
        if actual - declared:
            errors.append({'file': str(path), 'reason': 'Actual finding headings are missing declarations', 'ids': sorted(actual - declared)})
        if isinstance(metadata.get('findings'), list):
            for finding in metadata['findings']:
                if isinstance(finding, dict) and finding.get('id') not in declared:
                    errors.append({'file': str(path), 'reason': 'Structured finding is undeclared', 'id': finding.get('id')})
        findings.extend({'file': str(path), **e} for e in entries)
    from . import security_tracking
    threats = security_tracking.plan_threats(directory)
    if threats:
        with issues.budget(120):
            audit = security_tracking.threat_audit(security_tracking.scope(args))
        errors.extend({'reason': 'Canonical threat target is pending', **e} for e in audit['errors'])
    return {'ready': not errors, 'errors': errors, 'findings': findings, 'phase': directory.name.split('-')[0],
            'revision': revision, 'snapshotDigest': digest(plans + artifacts(directory)), 'structuralOnly': True}


def handoff(args):
    with issues.budget(180):
        return _handoff(args)


def _acceptance_fields(body):
    fields = {}
    for field in ('Status', 'Reviewer', 'Date', 'Decision', 'Evidence'):
        matches = [m[1].strip() for line in issue_format.visible_lines(body)
                   if (m := re.match(r'^ {0,3}(?:- )?' + field + r':\s*(.+)$', line.replace('**', ''), re.I))]
        if len(matches) != 1 or not matches[0] or re.search(r'\b(?:pending|TBD|unknown|placeholder)\b|\[replace', matches[0], re.I):
            return None
        fields[field.lower()] = matches[0]
    return fields


def accepted_human(body):
    """Accept only a real provider-read-back human decision, never a CLI assertion."""
    fields = _acceptance_fields(body)
    if not fields or fields['status'].upper() != 'ACCEPTED':
        return False
    try:
        dt.date.fromisoformat(fields['date'][:10])
    except ValueError:
        return False
    if not re.fullmatch(r'@?[A-Za-z0-9][A-Za-z0-9-]{0,38}', fields['reviewer']) or '#issuecomment-' not in fields['evidence']:
        return False
    try:
        with issues.budget(60):
            human_evidence(fields)
            if '## Human acceptance' in body:
                _uat_steps(body)
        return True
    except Exception:
        return False


def human_evidence(fields, issue_url=None, scope_reference=None):
    """Verify actual non-bot authored acceptance in the canonical issue comment."""
    if not isinstance(fields, dict) or not all(fields.get(k) for k in ('reviewer', 'date', 'decision', 'evidence')):
        raise Failure('human-acceptance-pending', 'Actual reviewer/date/decision/evidence are required')
    urls = re.findall(r'https://[^\s)\]>]+', str(fields['evidence']))
    candidates = [u for u in urls if re.search(r'#issuecomment-\d+$', u)]
    if len(candidates) != 1:
        raise Failure('human-acceptance-pending', 'One actual canonical human comment permalink is required')
    url = candidates[0]
    base = url.split('#')[0]
    repository.require_url(base, 'issues')
    if issue_url and base != str(issue_url).split('#')[0]:
        raise Failure('human-acceptance-scope-mismatch', 'Acceptance belongs to a different issue')
    reviewer = str(fields['reviewer']).lstrip('@')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', reviewer):
        raise Failure('human-reviewer-invalid', reviewer)
    origin = repository.identity()
    comment_id = url.rsplit('-', 1)[1]
    endpoint = 'repos/' + origin['owner'] + '/' + origin['repository'] + '/issues/comments/' + comment_id
    packet = json.loads(issues.provider(['api', '--hostname', origin['hostname'], endpoint], origin).stdout)
    author = packet.get('user') or {}
    body = packet.get('body', '')
    if (packet.get('html_url') != url or author.get('type') != 'User' or author.get('login', '').lower() != reviewer.lower()
            or not str(packet.get('created_at', '')).startswith(str(fields['date'])[:10])
            or str(fields['decision']).strip().lower() not in body.lower()
            or not re.search(r'(?i)\b(?:accepted|approved|i accept|i approve)\b', body)
            or re.search(r'(?i)\b(?:pending|rejected)\b|\bnot\s+(?:accepted|approved)\b|\bdo not\b', body)):
        raise Failure('human-acceptance-unverified', 'Provider did not confirm the named human accepted this exact recorded decision')
    if scope_reference and str(scope_reference) not in body:
        raise Failure('human-acceptance-scope-pending', 'Human reply does not identify this individual risk')
    return {'accepted': True, 'reviewer': reviewer, 'url': url, 'comment_id': comment_id,
            'body_sha256': hashlib.sha256(body.encode()).hexdigest()}


def _uat_steps(body):
    from .security_tracking import table_rows
    rows = table_rows(body, ('step', 'action', 'expected_outcome', 'actual_outcome_evidence'))
    actual = [r for r in rows if re.fullmatch(r'\d+\.?', r['step'])]
    if not actual or any(not r['actual_outcome_evidence'].strip() or re.search(
            r'(?i)\b(?:pending|blocked|failed|unknown|TBD)\b|\{[^}]*\}|<replace', r['actual_outcome_evidence']) for r in actual):
        raise Failure('uat-observations-pending', 'Every actual UAT step needs its real outcome/evidence before acceptance closes scope')


def audit_pr(phase, body):
    packet = handoff(Args([str(phase)]))
    if not packet['ready']:
        raise Failure('phase-issues', 'Findings are not reconciled', errors=packet['errors'])
    failures = []
    origin = repository.identity() if packet['findings'] else None
    with issues.budget(120):
        for item in packet['findings']:
            url = item.get('url', item.get('issue_url'))
            if not url:
                continue
            base = str(url).split('#')[0]
            number = repository.require_url(base, 'issues')
            issue = issues.issue_get(base, origin)
            forms = '(?:' + re.escape(base) + '|' + re.escape(origin['owner'] + '/' + origin['repository']) + '#' + str(number) + '|#' + str(number) + r')(?!\d)'
            closes = bool(re.search(r'(?i)\b(?:closes?|closed|fix(?:es|ed)?|resolves?|resolved)\s+' + forms, body))
            relationship = item.get('relationship', 'followup')
            if str(url) not in body:
                failures.append({'id': item['id'], 'reason': 'Exact canonical finding URL missing from PR body'})
            if relationship == 'followup' and closes:
                failures.append({'id': item['id'], 'reason': 'Follow-up must not be closed by this PR'})
            if relationship in ('closes', 'close', 'fixes', 'resolving'):
                if not closes or str(item.get('state', '')).lower() not in CLOSED:
                    failures.append({'id': item['id'], 'reason': 'Closing relationship requires complete resolved scope and actual evidence'})
                if str(item.get('variant', '')).upper() == 'UAT' or '## Human acceptance' in issue.get('body', ''):
                    if not accepted_human(issue['body']):
                        failures.append({'id': item['id'], 'reason': 'UAT lacks an explicit accepted receipt'})
                    else:
                        try:
                            _uat_steps(issue['body'])
                            human_evidence(_acceptance_fields(issue['body']), base)
                        except Failure as exc:
                            failures.append({'id': item['id'], 'reason': exc.message})
    if failures:
        raise Failure('phase-issue-links', 'PR relationships or actual acceptance are pending', errors=failures)
    return packet


def merged_pr(url):
    repository.require_url(url, 'pull')
    origin = repository.identity()
    packet = json.loads(issues.provider(['pr', 'view', url, '--json', 'url,state,body,headRefName,headRefOid,mergeCommit,mergedAt'], origin).stdout)
    branch = run(['git', 'branch', '--show-current'], root(), timeout=30).stdout.strip()
    revision = run(['git', 'rev-parse', 'HEAD'], root(), timeout=30).stdout.strip()
    if (packet.get('url') != url or packet.get('state') != 'MERGED' or not packet.get('mergedAt')
            or packet.get('headRefName') != branch or packet.get('headRefOid') != revision):
        raise Failure('phase-pr-not-current-merged', 'Readback must identify this exact phase branch HEAD as actually merged')
    return packet


def reconcile_todos(args):
    from . import verification
    directory = records.phase_dir(args.need())
    context_paths = sorted(directory.glob('*-CONTEXT.md'))
    context_digest = digest(context_paths)
    contexts = '\n'.join(read(p) for p in context_paths)
    folded = re.search(r'(?ms)^### Folded Todos\s*\n(.*?)(?=^###|^## |\Z)', contexts)
    selected = args.all('todos')
    if not folded or not selected:
        raise Failure('no-folded-todos', 'Select exact pending filenames from the actual Folded Todos section')
    for name in selected:
        if Path(name).name != name or not re.search(r'`' + re.escape(name) + r'`', folded[1]):
            raise Failure('todo-not-folded', name)
    verified = verification.current_evidence(args.need())
    if not verified.get('current'):
        raise Failure('todo-verification-pending', 'Actual current passed phase verification is required', evidence=verified)
    results = []
    with issues.budget(120):
        pull = merged_pr(str(args.get('pr', '')))
        for name in selected:
            source = safe_path(records.planning() / 'todos/pending' / name)
            destination = safe_path(records.planning() / 'todos/completed' / name)
            try:
                existing = not source.exists() and destination.is_file()
                record = destination if existing else source
                if not record.is_file():
                    raise Failure('todo-record-missing', name)
                snapshot = digest([record])
                metadata, body = split_frontmatter(read(record))
                target = metadata.get('issue_url', metadata.get('issueURL', metadata.get('issue')))
                if not target:
                    raise Failure('todo-not-published', name)
                target = str(target).split('#')[0]
                repository.require_url(target, 'issues')
                if target not in pull.get('body', ''):
                    raise Failure('todo-pr-relationship-missing', 'Merged phase PR does not relate this canonical todo issue')
                first = issues.issue_get(target, repository.identity())
                final = issues.issue_get(target, repository.identity())
                if first != final or final.get('state', '').upper() != 'CLOSED':
                    raise Failure('todo-issue-not-stably-closed', name)
                if '## Human acceptance' in final.get('body', ''):
                    if not accepted_human(final['body']):
                        raise Failure('todo-human-acceptance-pending', name)
                    _uat_steps(final['body'])
                    human_evidence(_acceptance_fields(final['body']), target)
                if existing:
                    if metadata.get('completed_pr') != pull['url']:
                        raise Failure('todo-archive-provenance-mismatch', name)
                    results.append({'todo': name, 'state': 'already-completed', 'path': str(destination)})
                    continue
                with planning_lock():
                    if digest([source]) != snapshot or digest(context_paths) != context_digest:
                        raise Failure('todo-source-drift', name)
                    from .security_tracking import _runtime_dir
                    ledger_key = hashlib.sha256((name + snapshot + pull['url']).encode()).hexdigest()
                    ledger_path = _runtime_dir().parent / 'todo-reconciliation' / (ledger_key + '.json')
                    intent = load_json(ledger_path)
                    if destination.exists() and not (intent and intent.get('source_digest') == snapshot and intent.get('pr') == pull['url']):
                        raise Failure('todo-destination-exists', str(destination))
                    if not intent:
                        intent = {'todo': name, 'source_digest': snapshot, 'original': base64.b64encode(source.read_bytes()).decode(),
                                  'pr': pull['url'], 'issue': target, 'status': 'archiving', 'created': now()}
                        write_json(ledger_path, intent)
                    updated = dict(metadata, status='complete', completed=now(), completed_pr=pull['url'], issue_url=target,
                                   reconciled_source_digest=snapshot)
                    if destination.exists():
                        prior, _ = split_frontmatter(read(destination))
                        if prior.get('reconciled_source_digest') != snapshot or prior.get('completed_pr') != pull['url']:
                            raise Failure('todo-archive-drift', name)
                    else:
                        write(destination, join_frontmatter(updated, body))
                    if digest([source]) != snapshot:
                        raise Failure('todo-source-drift', name)
                    source.unlink()
                    intent.update(status='complete', completed=now())
                    write_json(ledger_path, intent)
                results.append({'todo': name, 'state': 'completed', 'path': str(destination)})
            except (Failure, OSError, ValueError) as exc:
                results.append({'todo': name, 'state': 'pending', 'reason': str(exc), 'error': exc.code if isinstance(exc, Failure) else 'evidence-unavailable'})
    return {'items': results, 'pr': pull['url'], 'issues_closed': False}
