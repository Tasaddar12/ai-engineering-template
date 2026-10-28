"""Origin-bound canonical security tracking, guarded publication and report evidence."""
from __future__ import annotations
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
import uuid

from . import config, issue_format, issues, records, repository, verification
from .core import Args, Failure, digest, load_json, now, planning_lock, read, root, run, safe_path, write, write_json
from .text import join_frontmatter, split_frontmatter
from .locking import acquire

RANK = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
FIELDS = ('key', 'id', 'heading', 'plan', 'threat_id', 'owner', 'scope_acceptance',
          'assessment_uncertainty', 'lifecycle_outcome', 'next_action', 'revision_check_evidence', 'aliases_occurrences')
RESOLVED = {'resolved', 'mitigated', 'fixed'}


def _runtime_dir():
    common = Path(run(['git', 'rev-parse', '--path-format=absolute', '--git-common-dir'], root(), timeout=30).stdout.strip()).resolve()
    return common / 'engineer/security-tracking'


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def _head():
    return run(['git', 'rev-parse', 'HEAD'], root(), timeout=30).stdout.strip()


def _enabled(args, key):
    return args.has(key) and str(args.get(key)).lower() in ('true', '1', 'yes')


def scope(args, provider=True):
    if args.has('quick'):
        packet = records.quick(Args([str(args.get('quick'))]), 'get')
        directory = safe_path(packet['directory'])
        identifier, kind = str(packet['id']), 'quick'
    else:
        directory = records.phase_dir(args.need())
        identifier, kind = directory.name.split('-', 1)[0], 'phase'
    origin = repository.identity() if provider else {'local_repository': str(root())}
    anchors = sorted(directory.glob('*-CONTEXT.md')) or sorted(directory.glob('*-PLAN.md'))
    stable = args.get('scope-key')
    if not stable and anchors:
        history = run(['git', 'log', '--follow', '--diff-filter=A', '--format=%H', '--name-only', '--',
                       str(anchors[0].relative_to(root()))], root(), timeout=30).stdout.splitlines()
        creation = next((i for i, line in enumerate(history) if re.fullmatch(r'[a-f0-9]{40,64}', line)), None)
        if creation is not None:
            original = next((v for v in history[creation+1:] if v.strip() and not re.fullmatch(r'[a-f0-9]{40,64}', v)), '')
            stable = history[creation] + ':' + original
    if not stable:
        stable = kind + ':' + identifier
        stable_pending = 'Commit the source CONTEXT/PLAN or supply a reviewed stable --scope-key before publication'
    else:
        stable_pending = None
    key = _hash({'origin': origin, 'kind': kind, 'identity': stable})
    return {'kind': kind, 'id': identifier, 'directory': directory, 'origin': origin, 'key': key,
            'stable_identity': stable, 'identity_pending': stable_pending}


def table_rows(body, required):
    lines = issue_format.visible_lines(body)
    rows, columns = [], None
    for line in lines:
        if not line.lstrip().startswith('|'):
            columns = None
            continue
        cells = [v.strip().replace('**', '') for v in line.strip().strip('|').split('|')]
        normalized = [re.sub(r'[^a-z0-9]+', '_', c.lower()).strip('_') for c in cells]
        if all(name in normalized for name in required):
            columns = normalized
            continue
        if columns and len(cells) == len(columns) and not all(re.fullmatch(r':?-+:?', c.replace(' ', '')) for c in cells):
            rows.append(dict(zip(columns, cells)))
    return rows


def plan_threats(directory):
    result = []
    for path in sorted(directory.glob('*-PLAN.md')):
        text = read(path)
        blocks = re.findall(r'<threat_model\b[^>]*>([\s\S]*?)</threat_model>', text)
        for block in blocks:
            for row in table_rows(block, ('threat_id', 'category', 'component', 'severity', 'disposition')):
                identifier = row['threat_id'].strip('` ')
                if not identifier or any(c in identifier for c in '{}<>'):
                    raise Failure('invalid-plan-threat', str(path), row=row)
                result.append({**row, 'threat_id': identifier, 'plan': path.name})
    return result


def _text(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)


def _lifecycle(entry):
    value = entry.get('lifecycle_outcome', '')
    if isinstance(value, dict):
        return str(value.get('state', '')).lower()
    return re.split(r'[\s:;,]+', str(value).strip().lower(), 1)[0]


def _inputs(args, ctx):
    path = safe_path(args.get('entries-file'))
    raw = json.loads(read(path))
    if not isinstance(raw, list) or not raw or len(raw) > 50:
        raise Failure('security-entries-invalid', 'Supply 1-50 fully authored risk entries')
    threats = plan_threats(ctx['directory'])
    found, identifiers = set(), set()
    for entry in raw:
        if not isinstance(entry, dict) or any(entry.get(k) is None or not _text(entry.get(k, '')).strip() for k in FIELDS):
            raise Failure('security-entry-incomplete', 'Every canonical risk field needs actual content', fields=FIELDS)
        if not isinstance(entry.get('planned'), bool) or entry['key'] in found or entry['id'] in identifiers:
            raise Failure('security-identity-invalid', 'Keys and entry identities must be unique; planned is boolean')
        if not isinstance(entry['key'], str) or not isinstance(entry['id'], str) or not isinstance(entry['heading'], str) or '\n' in entry['heading'] or entry['heading'].startswith('#'):
            raise Failure('security-identity-invalid', 'Use plain stable key/id/heading strings')
        found.add(entry['key'])
        identifiers.add(entry['id'])
        plan = safe_path(ctx['directory'] / entry['plan'])
        if plan.parent != ctx['directory'] or not plan.name.endswith('-PLAN.md') or not plan.is_file():
            raise Failure('security-plan-invalid', str(plan))
        matches = [r for r in threats if r['plan'] == entry['plan'] and r['threat_id'] == entry['threat_id']]
        if entry['planned'] and len(matches) != 1:
            raise Failure('security-threat-not-declared', str(entry['threat_id']), plan=entry['plan'])
        if not entry['planned']:
            body = entry.get('standalone_body')
            if not isinstance(body, str):
                raise Failure('security-standalone-body-required', entry['id'])
            issues.validate(str(entry.get('title', entry['heading'])), body, 'Security risk')
        review = entry.get('match_review')
        if not isinstance(review, dict) or review.get('disposition') not in ('existing', 'no-match', 'pending') or not review.get('evidence'):
            raise Failure('security-match-review-required', entry['id'])
        if not all(isinstance(review.get(k), list) for k in ('reviewed_issue_urls', 'reviewed_pr_urls')):
            raise Failure('security-match-review-required', 'Include complete reviewed issue and PR URL lists')
        for url in review['reviewed_issue_urls']:
            repository.require_url(str(url).split('#')[0], 'issues')
        for url in review['reviewed_pr_urls']:
            repository.require_url(str(url).split('#')[0], 'pull')
    source = sorted(ctx['directory'].glob('*-PLAN.md')) + sorted(ctx['directory'].glob('*-CONTEXT.md'))
    source += [p for p in ctx['directory'].iterdir() if p.is_file() and p.name.endswith(('-SUMMARY.md', '-SECURITY.md', '-REVIEW.md'))]
    source.append(path)
    return raw, source, threats


def _state(ctx):
    path = _runtime_dir() / (_hash(ctx['origin']) + '.json')
    return path, load_json(path, {'schema': 1, 'risks': {}, 'scopes': {}})


def _issue_digest(issue):
    return _hash({k: issue.get(k) for k in ('url', 'title', 'body', 'state', 'labels')})


def _lookup(ctx, state):
    established = state['scopes'].get(ctx['key'])
    title = established['title'] if established else 'chore(security): ' + ctx['kind'] + ' ' + ctx['id'] + ' security checklist'
    label = ctx['kind'] + '-security-checklist'
    result = json.loads(issues.provider(['issue', 'list', '--state', 'all', '--label', label, '--search', '"' + title + '"',
                                        '--limit', '200', '--json', issues.FIELDS], ctx['origin']).stdout)
    exact = [i for i in result if i.get('title') == title and label in {v['name'] if isinstance(v, dict) else v for v in i.get('labels', [])}]
    marker = '<!-- engineer-security-intent:' + _hash({'origin': ctx['origin'], 'key': 'container:' + ctx['key']}) + ' -->'
    historical = json.loads(issues.provider(['issue', 'list', '--state', 'all', '--label', label,
                                             '--search', marker, '--limit', '200', '--json', issues.FIELDS], ctx['origin']).stdout)
    for candidate in historical:
        if marker in candidate.get('body', '') and all(i['url'] != candidate['url'] for i in exact):
            exact.append(candidate)
    if not established and len(exact) == 1 and marker in exact[0].get('body', ''):
        title = exact[0]['title']  # Renumbering/cloning never changes an established identity.
    if established and established.get('url'):
        known = issues.issue_get(established['url'], ctx['origin'])
        if known.get('title') != title:
            raise Failure('security-checklist-identity-drift', 'Established container title changed; reconcile its references')
        if all(i['url'] != known['url'] for i in exact):
            exact.append(known)
    return title, label, exact, len(result) >= 200 or len(historical) >= 200


def _entry_block(entry, canonical_url=None):
    marker = _hash(entry['key'])
    fields = [('Entry identity', entry['id']), ('Canonical risk key', entry['key']),
              ('Aliases/occurrences', entry['aliases_occurrences']), ('PLAN/Threat ID', entry['plan'] + '/' + entry['threat_id']),
              ('Owner', entry['owner']), ('Scope/acceptance', entry['scope_acceptance']),
              ('Assessment/uncertainty', entry['assessment_uncertainty']), ('Lifecycle/outcome', entry['lifecycle_outcome']),
              ('Next action', entry['next_action']), ('Revision/check evidence', entry['revision_check_evidence']),
              ('Canonical reference', canonical_url or 'This reviewed checklist entry; actual provider-rendered target is pending readback.')]
    return '<!-- engineer-risk:' + marker + ':begin -->\n### ' + entry['heading'] + '\n\n' + '\n'.join(
        '**' + name + ':** ' + _text(value) for name, value in fields) + '\n<!-- engineer-risk:' + marker + ':end -->'


def _container_body(entries):
    parts = {'Security concern': 'Canonical planned risk tracking. Each authored entry preserves its own control/surface/failure/remediation identity.',
             'Affected surface and behavior': '\n'.join(_text(e['scope_acceptance']) for e in entries),
             'Impact': '\n'.join(_text(e['assessment_uncertainty']) for e in entries),
             'Risk assessment and lifecycle': '\n\n'.join(_entry_block(e, e.get('canonical_url')) for e in entries),
             'Safe evidence': '\n'.join(_text(e['revision_check_evidence']) for e in entries),
             'Requested remediation': '\n'.join(_text(e['next_action']) for e in entries),
             'Scope and acceptance': '\n'.join(_text(e['scope_acceptance']) for e in entries),
             'Related links': '\n'.join(e.get('canonical_url') or e['plan'] + '/' + e['threat_id'] for e in entries)}
    return '\n\n'.join('## ' + name + '\n\n' + parts[name] for name in issue_format.FALLBACK_HEADINGS['Security risk']) + '\n'


def _merge_container(body, entries):
    issues.validate('Canonical security checklist', body, 'Security risk')
    for entry in entries:
        marker = _hash(entry['key'])
        start = '<!-- engineer-risk:' + marker + ':begin -->'
        stop = '<!-- engineer-risk:' + marker + ':end -->'
        if body.count(start) != body.count(stop) or body.count(start) > 1:
            raise Failure('security-entry-marker-drift', entry['key'])
        block = _entry_block(entry, entry.get('canonical_url'))
        if start in body:
            body = body[:body.index(start)] + block + body[body.index(stop) + len(stop):]
        else:
            match = re.search(r'(?m)^## Safe evidence\s*$', body)
            if not match:
                raise Failure('security-container-schema', 'Lifecycle section boundary unavailable')
            body = body[:match.start()].rstrip() + '\n\n' + block + '\n\n' + body[match.start():]
    return body


def _review(args, ctx):
    entries, sources, threats = _inputs(args, ctx)
    _, state = _state(ctx)
    title, label, containers, truncated = _lookup(ctx, state)
    pending = []
    if ctx['identity_pending']:
        pending.append(ctx['identity_pending'])
    if truncated or len(containers) > 1:
        pending.append('Checklist lookup was truncated or ambiguous')
    container = containers[0] if len(containers) == 1 else None
    if container and container.get('state', '').upper() == 'CLOSED':
        pending.append('Established checklist is closed; reopening needs separate actual authority')
    evidence, rendered = [], []
    for item in entries:
        entry = dict(item)
        review = entry['match_review']
        context = issues.candidates(entry['key'], ctx['origin'], limit=200)
        if context['possibly_truncated']:
            pending.append(entry['id'] + ': candidate lookup truncated')
        reviewed_issues, reviewed_prs = set(review['reviewed_issue_urls']), set(review['reviewed_pr_urls'])
        if any(i['url'] not in reviewed_issues for i in context['issues']) or any(i['url'] not in reviewed_prs for i in context['pull_requests']):
            pending.append(entry['id'] + ': every issue/current-linked PR candidate needs explicit match review')
        prior = state['risks'].get(entry['key'])
        if prior and prior.get('scope') == ctx['key'] and prior.get('heading') != entry['heading']:
            pending.append(entry['id'] + ': preserve the established heading; renames need explicit reference repair')
        existing = review.get('url') or (prior or {}).get('canonical_url')
        if prior and review.get('url') and prior['canonical_url'] != review['url']:
            pending.append(entry['id'] + ': canonical identity may not be replaced')
        if existing:
            issue = issues.issue_get(str(existing).split('#')[0], ctx['origin'])
            if review['disposition'] != 'existing' or not review.get('url'):
                pending.append(entry['id'] + ': established canonical match must be retained explicitly')
            resolution = entry.get('revision_check_evidence')
            citations = resolution.get('citations', []) if isinstance(resolution, dict) else []
            resolved = _lifecycle(entry) in RESOLVED and bool(citations) and all(_citation(c, _head()) for c in citations)
            if issue.get('state', '').upper() == 'CLOSED' and not resolved:
                pending.append(entry['id'] + ': closed unresolved canonical match requires separate human decision; no duplicate')
            entry['canonical_url'] = str(existing)
            if issue['url'] not in reviewed_issues:
                pending.append(entry['id'] + ': selected existing issue must appear in the explicit reviewed list')
            evidence.append(issue)
        elif review['disposition'] != 'no-match':
            pending.append(entry['id'] + ': canonical match review pending')
        elif any(entry['key'] in i.get('body', '') for i in context['issues']):
            pending.append(entry['id'] + ': canonical source-scope key already has a tracker')
        rendered.append(entry)
        evidence.append({'risk': entry['key'], 'candidates': context})
    planned = [e for e in rendered if e['planned']]
    operations = []
    if planned:
        body = _merge_container(container['body'], planned) if container else _container_body(planned)
        issues.validate(title, body, 'Security risk')
        operations.append({'key': 'container:' + ctx['key'], 'title': title, 'body': body, 'labels': [label],
                           'url': container['url'] if container else None, 'before': _issue_digest(container) if container else None,
                           'action': 'edit' if container else 'create'})
    for entry in rendered:
        if entry['planned'] or entry.get('canonical_url'):
            continue
        operations.append({'key': 'risk:' + _hash(entry['key']), 'title': str(entry.get('title', entry['heading'])),
                           'body': _merge_container(entry['standalone_body'], [entry]), 'labels': ['security-risk'], 'action': 'create', 'url': None,
                           'before': None, 'risk_key': entry['key']})
    return {'ready': not pending, 'pending': pending, 'entries': rendered, 'operations': operations,
            'title': title, 'label': label, 'container': container, 'candidates': evidence,
            'source_digest': digest(sources), 'source_files': [str(p.relative_to(root())) for p in sources],
            'revision': _head(), 'scope': {k: str(v) if isinstance(v, Path) else v for k, v in ctx.items()}}


class _Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.heading = None
        self.items = {}
    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'h3':
            self.heading = {'text': [], 'anchors': []}
        if self.heading is not None:
            if attrs.get('href', '').startswith('#'):
                self.heading['anchors'].append(attrs['href'][1:])
            elif attrs.get('id'):
                self.heading['anchors'].append(attrs['id'])
    def handle_data(self, data):
        if self.heading is not None:
            self.heading['text'].append(data)
    def handle_endtag(self, tag):
        if tag == 'h3' and self.heading is not None:
            text = ''.join(self.heading['text']).strip()
            self.items[text] = self.heading['anchors']
            self.heading = None


def rendered_targets(issue_url, entries, origin):
    number = repository.require_url(issue_url, 'issues')
    endpoint = 'repos/' + origin['owner'] + '/' + origin['repository'] + '/issues/' + str(number)
    response = issues.provider(['api', '--hostname', origin['hostname'], endpoint,
                                '--header', 'Accept: application/vnd.github.html+json'], origin)
    packet = json.loads(response.stdout)
    parser = _Anchors()
    parser.feed(packet.get('body_html', ''))
    targets, pending = {}, []
    for entry in entries:
        anchors = parser.items.get(entry['heading'], [])
        if len(set(anchors)) != 1:
            pending.append(entry['id'] + ': actual rendered heading anchor unavailable or ambiguous')
        else:
            targets[entry['key']] = issue_url + '#' + anchors[0]
    return targets, pending


def _mutate(operation, ctx, preview_path, preview):
    intent_key = _hash({'origin': ctx['origin'], 'key': operation['key']})
    intent_path = _runtime_dir() / 'intents' / (intent_key + '.json')
    marker = '<!-- engineer-security-intent:' + intent_key + ' -->'
    body = operation['body'] if marker in operation['body'] else operation['body'].rstrip() + '\n\n' + marker + '\n'
    with planning_lock():
        intent = load_json(intent_path)
        retry = bool(intent)
        if (intent and intent.get('state') == 'complete' and operation.get('action') == 'edit'
                and intent.get('url') == operation.get('url') and intent.get('operation') != {**operation, 'body': body}):
            retry = False  # A fresh explicitly reviewed edit of the established identity.
        if retry and intent.get('operation') != {**operation, 'body': body}:
            raise Failure('security-publication-uncertain', 'Reconcile the existing exact create/edit intent before changing input', intent=intent)
        if not retry:
            intent = {'origin': ctx['origin'], 'marker': marker, 'operation': {**operation, 'body': body},
                      'state': 'attempting', 'attempted': now(), 'source_digest': preview['source_digest']}
            write_json(intent_path, intent)  # Never repeat an unknown create.
        preview['consumed'] = True
        write_json(preview_path, preview)
    if retry:
        if intent.get('url') or operation.get('url'):
            result = issues.issue_get(intent.get('url') or operation['url'], ctx['origin'])
        else:
            result = issues.reconcile(intent, ctx['origin'])
    if not retry or (operation.get('url') and result.get('body', '').strip() != body.strip()
                     and _issue_digest(result) == operation['before']):
        if operation.get('url'):
            current = issues.issue_get(operation['url'], ctx['origin'])
            if _issue_digest(current) != operation['before'] or current.get('state', '').upper() == 'CLOSED':
                raise Failure('security-provider-drift', operation['url'])
        with tempfile.TemporaryDirectory(prefix='engineer-security-') as directory:
            path = Path(directory) / 'body.md'
            path.write_text(body, encoding='utf-8')
            argv = (['issue', 'edit', operation['url']] if operation.get('url') else ['issue', 'create'])
            argv += ['--title', operation['title'], '--body-file', str(path)]
            for label in operation['labels']:
                argv += ['--add-label' if operation.get('url') else '--label', label]
            response = issues.provider(argv, ctx['origin'])
        urls = re.findall(r'https://[^\s]+/issues/\d+', response.stdout)
        url = operation.get('url') or (urls[-1] if urls else None)
        result = issues.issue_get(url, ctx['origin']) if url else issues.reconcile(intent, ctx['origin'])
    with planning_lock():
        intent['url'] = result['url']
        write_json(intent_path, intent)
    if result.get('title') != operation['title'] or result.get('body', '').strip() != body.strip():
        raise Failure('security-readback-mismatch', 'Provider content differs from exact reviewed content', url=result['url'])
    if not set(operation['labels']) <= {x['name'] if isinstance(x, dict) else x for x in result.get('labels', [])}:
        raise Failure('security-label-readback-mismatch', result['url'])
    with planning_lock():
        intent.update(state='complete', completed=now())
        write_json(intent_path, intent)
    return result


def _tracking(args, action):
    ctx = scope(args)
    if action == 'threat-audit':
        return threat_audit(ctx)
    resume = None
    supplied = str(args.get('preview-token', ''))
    if action == 'threat-publish' and re.fullmatch(r'[a-f0-9]{64}', supplied):
        resume = load_json(_runtime_dir() / 'previews' / (supplied + '.json'))
    if resume and resume.get('consumed'):
        if (resume.get('scope', {}).get('key') != ctx['key'] or resume.get('scope', {}).get('origin') != ctx['origin']
                or resume.get('revision') != _head()
                or digest([safe_path(p) for p in resume['source_files']]) != resume['source_digest']):
            raise Failure('security-recovery-source-drift', 'Preserve prior published URLs and reconcile changed source before any new mutation')
        review = resume  # Own provider writes must not invalidate their recovery token.
    else:
        review = _review(args, ctx)
    if action == 'threat-review':
        return review
    identity = {k: review[k] for k in ('scope', 'entries', 'operations', 'source_digest', 'revision')}
    token = _hash(identity)
    path = _runtime_dir() / 'previews' / (token + '.json')
    if action == 'threat-preview':
        with planning_lock():
            previous = load_json(path, {})
            packet = {**review, 'token': token, 'consumed': previous.get('consumed', False),
                      'results': previous.get('results', []), 'created': previous.get('created', now())}
            write_json(path, packet)
        return {**review, 'preview_token': token, 'previewToken': token}
    if action != 'threat-publish' or not _enabled(args, 'publish'):
        raise Failure('security-publication-not-authorized', 'Provider writes require explicit --publish and an exact reviewed preview token')
    if args.get('preview-token') != token or not review['ready']:
        raise Failure('security-preview-stale-or-pending', 'Review exact current source/provider inputs before publishing', pending=review['pending'])
    saved = load_json(path)
    if not saved or saved.get('token') != token:
        raise Failure('security-preview-missing', token)
    state_path, state = _state(ctx)
    with acquire(_runtime_dir() / 'risk-index.lock', 10):
        state = load_json(state_path, {'schema': 1, 'risks': {}, 'scopes': {}})
        reservations = state.setdefault('risk_intents', {})
        for entry in review['entries']:
            known = state['risks'].get(entry['key'], {}).get('canonical_url')
            own_readback = bool(resume and resume.get('consumed') and any(r['url'] == str(known).split('#')[0] for r in saved.get('results', [])))
            if known and entry.get('canonical_url') != known and not own_readback:
                raise Failure('security-canonical-match-arrived', 'Refresh match review against the established canonical identity', key=entry['key'], url=known)
            prior = reservations.get(entry['key'])
            if prior and prior != {'scope': ctx['key'], 'token': token}:
                raise Failure('security-risk-publication-owned', 'Reconcile the existing risk publication before another source creates a tracker', key=entry['key'], intent=prior)
            if not known:
                reservations[entry['key']] = {'scope': ctx['key'], 'token': token}
        write_json(state_path, state)
    results = list(saved.get('results', []))
    for operation in review['operations']:
        prior = next((r for r in results if r['key'] == operation['key']), None)
        if digest([safe_path(p) for p in review['source_files']]) != review['source_digest'] or _head() != review['revision']:
            raise Failure('security-source-drift', 'Source changed during publication', published=results)
        result = _mutate(operation, ctx, path, saved)
        if not prior:
            results.append({'key': operation['key'], 'url': result['url']})
        with planning_lock():
            saved['results'] = results
            write_json(path, saved)
    container = next((r['url'] for r in results if r['key'].startswith('container:')), None)
    targets, pending = ({}, [])
    if container:
        targets, pending = rendered_targets(container, [e for e in review['entries'] if e['planned']], ctx['origin'])
    state_path, state = _state(ctx)
    with acquire(_runtime_dir() / 'risk-index.lock', 10):
        state = load_json(state_path, {'schema': 1, 'risks': {}, 'scopes': {}})
        if container:
            state['scopes'][ctx['key']] = {'url': container, 'title': review['title'], 'label': review['label'], 'identity': ctx['stable_identity']}
        for entry in review['entries']:
            standalone = next((r['url'] for r in results if r['key'] == 'risk:' + _hash(entry['key'])), None)
            canonical = entry.get('canonical_url') or standalone or targets.get(entry['key'])
            prior = state['risks'].get(entry['key'], {})
            if prior.get('canonical_url') and canonical and prior['canonical_url'] != canonical:
                raise Failure('security-canonical-identity-drift', entry['key'], existing=prior['canonical_url'])
            state['risks'][entry['key']] = {**prior, 'canonical_url': canonical or prior.get('canonical_url'),
                                          'entry_id': entry['id'], 'heading': entry['heading'], 'plan': entry['plan'],
                                          'threat_id': entry['threat_id'], 'scope': ctx['key'], 'container_url': container,
                                          'target': targets.get(entry['key'], standalone or entry.get('canonical_url')),
                                          'aliases_occurrences': entry['aliases_occurrences'], 'updated': now()}
            occurrence = {'scope': ctx['key'], 'entry_id': entry['id'], 'heading': entry['heading'], 'plan': entry['plan'],
                          'threat_id': entry['threat_id'], 'target': targets.get(entry['key'], standalone or entry.get('canonical_url')),
                          'container_url': container}
            history = prior.get('occurrences', [])
            history = [v for v in history if (v.get('scope'), v.get('plan'), v.get('threat_id')) != (ctx['key'], entry['plan'], entry['threat_id'])]
            history.append(occurrence)
            state['risks'][entry['key']]['occurrences'] = history
            aliases = prior.get('aliases_history', [])
            if prior.get('aliases_occurrences') is not None and prior['aliases_occurrences'] not in aliases:
                aliases.append(prior['aliases_occurrences'])
            if entry['aliases_occurrences'] not in aliases:
                aliases.append(entry['aliases_occurrences'])
            state['risks'][entry['key']]['aliases_history'] = aliases
            if prior.get('canonical_url'):
                for field in ('scope', 'entry_id', 'heading', 'plan', 'threat_id', 'target', 'container_url'):
                    if field in prior:
                        state['risks'][entry['key']][field] = prior[field]
            if state['risks'][entry['key']].get('canonical_url'):
                state.get('risk_intents', {}).pop(entry['key'], None)
        write_json(state_path, state)
        saved.update(results=results, complete=not pending, pending=pending)
        write_json(path, saved)
    return {'published': True, 'ready': not pending, 'pending': pending, 'results': results, 'targets': targets,
            'container_url': container, 'source_digest': review['source_digest'], 'issues_closed': False}


def threat_audit(ctx):
    _, state = _state(ctx)
    errors, findings = [], []
    threats = plan_threats(ctx['directory'])
    seen = set()
    for threat in threats:
        if threat['threat_id'] in seen:
            errors.append({'id': threat['threat_id'], 'reason': 'Duplicate phase threat ID'})
        seen.add(threat['threat_id'])
        matches = [(key, {**r, **occurrence}) for key, r in state['risks'].items() for occurrence in r.get('occurrences', [r])
                   if occurrence.get('scope') == ctx['key'] and occurrence.get('threat_id') == threat['threat_id'] and occurrence.get('plan') == threat['plan']]
        if len(matches) != 1 or not matches[0][1].get('target'):
            errors.append({'id': threat['threat_id'], 'reason': 'No unique read-back canonical target'})
            continue
        key, entry = matches[0]
        target = entry['target']
        issue = issues.issue_get(target.split('#')[0], ctx['origin'])
        if '#' in target:
            anchors, pending = rendered_targets(issue['url'], [{'id': entry['entry_id'], 'key': key, 'heading': entry['heading']}], ctx['origin'])
            if pending or target not in anchors.values():
                errors.append({'id': threat['threat_id'], 'reason': 'Actual provider heading target drifted'})
        if target not in read(ctx['directory'] / threat['plan']):
            errors.append({'id': threat['threat_id'], 'reason': 'PLAN register lacks its exact actual canonical target'})
        findings.append({'id': threat['threat_id'], 'target': target, 'issue': issue['url']})
    return {'ready': not errors, 'errors': errors, 'findings': findings, 'phase': ctx['id'], 'structuralOnly': True}


def _citation(value, revision):
    if not isinstance(value, dict) or not value.get('commit') or not value.get('path'):
        return False
    commit = str(value['commit']).lower()
    if not re.fullmatch(r'[a-f0-9]{40,64}', commit):
        return False
    path = safe_path(value['path']).relative_to(root()).as_posix()
    if run(['git', 'merge-base', '--is-ancestor', commit, revision], root(), check=False, timeout=30).returncode:
        return False
    result = run(['git', 'show', commit + ':' + path], root(), check=False, timeout=30)
    return result.returncode == 0 and (not value.get('quote') or str(value['quote']) in result.stdout)


def security_fingerprint(ctx, covered=()):
    sources = sorted(ctx['directory'].glob('*-PLAN.md')) + sorted(ctx['directory'].glob('*-CONTEXT.md')) + sorted(ctx['directory'].glob('*-SUMMARY.md'))
    sources += [safe_path(p) for p in covered]
    settings = config.load()
    return _hash({'inputs': digest(sources), 'asvs': config.lookup(settings, 'workflow.security_asvs_level', 1),
                  'blocking': config.lookup(settings, 'workflow.security_block_on', 'high')})


def security_status(args, proposed=None):
    ctx = scope(args, provider=False)
    reports = sorted(ctx['directory'].glob('*-SECURITY.md'))
    if len(reports) != 1:
        return {'ready': False, 'status': 'pending', 'threats_open': None, 'reasons': ['One actual SECURITY report is required'], 'behaviorVerified': False}
    path = reports[0]
    metadata, body = split_frontmatter(read(path))
    if proposed:
        metadata.update(proposed)
    revision = _head()
    reasons = []
    from .worktrees import dirty
    if dirty(root(), [str(path.relative_to(root()))]):
        reasons.append('Working source changed during the frozen audit')
    if proposed is None:
        committed = run(['git', 'show', revision + ':' + str(path.relative_to(root()))], root(), check=False, timeout=30)
        if committed.returncode or committed.stdout != read(path):
            reasons.append('Actual complete security report must be committed before readiness')
    frozen = metadata.get('revision', metadata.get('audit_revision'))
    valid_revision = isinstance(frozen, str) and bool(re.fullmatch(r'[a-f0-9]{40,64}', frozen))
    if not valid_revision or run(['git', 'merge-base', '--is-ancestor', str(frozen), revision], root(), check=False, timeout=30).returncode:
        reasons.append('Security evidence is not bound to an actual current-history frozen revision')
    elif frozen != revision:
        changed = run(['git', 'log', '--format=', '--name-only', '--full-history', '-m', frozen + '..' + revision], root(), timeout=30).stdout.splitlines()
        allowed = {str(path.relative_to(root())), '.planning/STATE.md', '.planning/ROADMAP.md', '.planning/REQUIREMENTS.md'}
        allowed.update(str(p.relative_to(root())) for p in ctx['directory'].glob('*-VERIFICATION.md'))
        if any(p.strip() and p not in allowed for p in changed):
            reasons.append('Source changed after the frozen security audit')
    covered = metadata.get('covered_files', [])
    if not isinstance(covered, list) or not covered or not all(isinstance(p, str) for p in covered):
        covered = []
        reasons.append('Explicit covered_files must be a path array')
    expected_fingerprint = security_fingerprint(ctx, covered)
    if metadata.get('fingerprint') != expected_fingerprint:
        reasons.append('Security source/configuration fingerprint is absent or stale')
    if metadata.get('audit_completed') is not True or not metadata.get('auditor'):
        reasons.append('Actual completed auditor evidence is absent')
    try:
        if ctx['kind'] == 'phase' and records.number(str(metadata.get('phase', ''))) != records.number(ctx['id']):
            reasons.append('Report phase identity does not match its actual scope')
        if ctx['kind'] == 'quick' and str(metadata.get('quick', '')).zfill(3) != str(ctx['id']).zfill(3):
            reasons.append('Report quick identity does not match its actual scope')
    except (ValueError, Failure):
        reasons.append('Report scope identity is missing or malformed')
    required_level = config.lookup(config.load(), 'workflow.security_asvs_level', 1)
    if not isinstance(metadata.get('asvs_level'), int) or metadata['asvs_level'] < required_level:
        reasons.append('Recorded ASVS depth does not meet configured policy')
    rows = table_rows(body, ('threat_id', 'severity', 'disposition', 'status'))
    declared = metadata.get('threat_evidence', [])
    if not isinstance(declared, list):
        declared = []
    plans = plan_threats(ctx['directory'])
    if not rows and not (metadata.get('no_applicable_threats') is True and metadata.get('coverage_rationale') and declared):
        reasons.append('Empty or missing threat observations cannot prove security')
    if not rows:
        coverage = [c for e in declared if isinstance(e, dict) for c in e.get('citations', [])]
        if not valid_revision or not coverage or not all(_citation(c, frozen) for c in coverage):
            reasons.append('No-applicable-threat conclusion lacks actual current cited coverage evidence')
    ids = [r['threat_id'].strip('` ') for r in rows]
    if len(ids) != len(set(ids)):
        reasons.append('Duplicate security threat rows')
    if any(t['threat_id'] not in ids for t in plans):
        reasons.append('Report omits a planned threat')
    threshold = RANK.get(str(config.lookup(config.load(), 'workflow.security_block_on', 'high')).lower(), 3)
    blocking = 0
    for row in rows:
        identifier = row['threat_id'].strip('` ')
        evidence = [e for e in declared if isinstance(e, dict) and e.get('id', e.get('threat_id')) == identifier]
        citations = evidence[0].get('citations', []) if len(evidence) == 1 else []
        supported = valid_revision and bool(citations) and all(_citation(c, frozen) for c in citations)
        closed = row['status'].strip().lower() in ('closed', 'resolved', 'mitigated')
        if row['severity'].lower() not in RANK:
            reasons.append(identifier + ': unknown severity cannot be silently downgraded')
        if closed and row['disposition'].lower().startswith(('accept', 'transfer')):
            acceptance = evidence[0].get('acceptance', {}) if evidence else {}
            supported = supported and all(acceptance.get(k) for k in ('reviewer', 'date', 'decision', 'evidence')) and _citation(acceptance.get('source'), frozen)
            if supported:
                try:
                    from .phase_issues import human_evidence
                    human_evidence(acceptance, acceptance.get('issue_url'), identifier)
                except Failure as exc:
                    supported = False
                    reasons.append(identifier + ': ' + exc.message)
        if closed and not supported:
            reasons.append(identifier + ': closed status has no current cited resolution/actual acceptance evidence')
        if RANK.get(row['severity'].lower(), 4) >= threshold and (not closed or not supported):
            blocking += 1
    if metadata.get('threats_open') != blocking:
        reasons.append('Recorded threats_open does not match actual blocking rows')
    if metadata.get('status') != 'verified' or blocking:
        reasons.append('Security report is not verified with zero blocking threats')
    return {'ready': not reasons, 'status': 'verified' if not reasons else 'pending', 'threats_open': blocking,
            'path': str(path), 'revision': revision, 'snapshotDigest': digest([path]), 'reasons': reasons,
            'fingerprint': expected_fingerprint, 'verified_revision': frozen,
            'behaviorVerified': False, 'evidence_scope': 'cited security audit; independent checks/acceptance retain their own gates'}


def command(args, action):
    if args.has('variant') and args.get('variant') != 'Security risk':
        raise Failure('security-variant-invalid', 'Security publication retains the canonical Security risk variant')
    with issues.budget(min(300, max(1, float(args.get('budget-seconds', 120))))):
        if action in ('threat-review', 'threat-preview', 'threat-publish', 'threat-audit'):
            if action == 'threat-publish':
                with acquire(_runtime_dir() / (scope(args)['key'] + '.lock'), 10):
                    return _tracking(args, action)
            return _tracking(args, action)
        if action == 'status':
            return security_status(args)
        if action == 'fingerprint':
            ctx = scope(args, provider=False)
            return {'fingerprint': security_fingerprint(ctx, args.all('files') + args.all('covered-files')), 'revision': _head()}
        if action == 'resolve':
            ctx = scope(args, provider=False)
            reports = sorted(ctx['directory'].glob('*-SECURITY.md'))
            if len(reports) != 1:
                raise Failure('security-report-missing', 'Author the complete actual SECURITY report before resolving its metadata')
            path = reports[0]
            proposed = json.loads(read(safe_path(args.get('entries-file'))))
            allowed = {'revision', 'audit_revision', 'audit_completed', 'auditor', 'asvs_level', 'threat_evidence', 'fingerprint', 'covered_files',
                       'threats_open', 'status', 'issue_refs', 'no_applicable_threats', 'coverage_rationale'}
            if not isinstance(proposed, dict) or set(proposed) - allowed:
                raise Failure('security-resolution-invalid', 'Only actual audit/report metadata fields may be supplied')
            snapshot = digest([path])
            if not _enabled(args, 'apply'):
                return {'path': str(path), 'snapshotDigest': snapshot, 'proposed': proposed, 'applied': False}
            evaluated = security_status(args, proposed)
            existing_metadata, _ = split_frontmatter(read(path))
            if proposed.get('status', existing_metadata.get('status')) == 'verified' and not evaluated['ready']:
                raise Failure('security-resolution-unproved', 'Real audit evidence is required before setting verified', reasons=evaluated.get('reasons'))
            with planning_lock():
                if args.get('expect-digest') != snapshot or digest([path]) != snapshot:
                    raise Failure('security-report-drift', 'Review exact current metadata before applying')
                metadata, body = split_frontmatter(read(path))
                metadata.update(proposed)
                write(path, join_frontmatter(metadata, body))
            result = security_status(args)
            return {**result, 'applied': True, 'acceptance_invented': False}
    raise Failure('unsupported-security-action', action, 2)
