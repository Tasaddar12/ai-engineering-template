"""Strict local evidence packets bound to immutable Git inputs.

Integrity detects corruption, not authorship: the host verifies independent
reviewer identity and preserves that validation in result provenance.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import uuid

import yaml

from .text import FRONTMATTER

from .results import VerbError, require
from .verification_checks import digest, git

SCHEMA = 1
STORE = '.planning/verification-evidence'
KINDS = {'review', 'scout', 'acceptance'}
STATUSES = {'passed', 'complete', 'failed', 'incomplete'}
SEVERITIES = {'critical', 'high', 'medium', 'low', 'info'}
REQUEST_FIELDS = {'schema', 'kind', 'revision', 'scope', 'inputs', 'configuration',
                  'question', 'requirements', 'requested_fields', 'report_path'}
RESULT_FIELDS = {'status', 'inspected_revision', 'findings', 'provenance',
                 'covered_paths', 'field_results', 'evidence', 'search_scope', 'absence_claims', 'unresolved_questions'}


def check(condition, message):
    require(condition, message, 'bad-evidence')


def strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            check(key not in result, 'duplicate JSON field: ' + key)
            result[key] = value
        return result
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs,
                          parse_constant=lambda value: check(False, 'nonfinite JSON value'))
    except (OSError, ValueError, RecursionError) as exc:
        raise VerbError('invalid evidence JSON: ' + str(exc), 'bad-evidence')


def strict_frontmatter(content):
    match = FRONTMATTER.match(content)
    check(match is not None, 'frontmatter required')

    class Loader(yaml.SafeLoader):
        pass

    def mapping(loader, node):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node)
            check(isinstance(key, str) and key not in result, 'duplicate/invalid YAML field')
            result[key] = loader.construct_object(value_node)
        return result

    Loader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    try:
        metadata = yaml.load(match.group(1), Loader=Loader)
        check(isinstance(metadata, dict), 'frontmatter mapping required')
        return metadata, content[match.end():]
    except (yaml.YAMLError, TypeError, ValueError, RecursionError) as exc:
        raise VerbError('invalid frontmatter: ' + str(exc), 'bad-evidence')


def literal(value):
    check(isinstance(value, str) and bool(value), 'path must be a nonempty string')
    path = PurePosixPath(value)
    check(not path.is_absolute() and path.as_posix() == value and
          not any(part in {'.', '..', '.git', 'verification-evidence', 'verification-receipts'}
                  for part in path.parts) and
          not any(char in value for char in ':\\*?[]\0\n\r'),
          'path must be literal repository-relative: ' + value)
    return value


def strings(value, name, nonempty=False):
    check(isinstance(value, list) and all(isinstance(v, str) and v.strip() for v in value),
          name + ' must be a string list')
    check(len(value) == len(set(value)) and (value or not nonempty), name + ' must be unique/nonempty')
    return value


def revision(root, value):
    check(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', value),
          'revision must be a full committed SHA')
    try:
        check(git(root, 'rev-parse', '--verify', value + '^{commit}').decode().strip() == value,
              'revision is not an exact commit')
    except (OSError, subprocess.SubprocessError):
        raise VerbError('revision is not a committed object', 'bad-evidence')
    return value


def head(root):
    return git(root, 'rev-parse', 'HEAD').decode().strip()


def clean(root):
    return not git(root, 'status', '--porcelain', '--untracked-files=all').strip()


def tree(root, commit):
    entries = {}
    for item in git(root, 'ls-tree', '-rz', '--full-tree', commit).split(b'\0'):
        if not item:
            continue
        metadata, name = item.split(b'\t', 1)
        mode, kind, blob = metadata.decode().split()
        entries[os.fsdecode(name)] = [mode, kind, blob]
    return entries


def manifest(entries, paths):
    result = {}
    for name in paths:
        literal(name)
        matches = [p for p in entries if p == name or p.startswith(name + '/')]
        check(matches, 'missing committed scope/input: ' + name)
        for path in matches:
            mode, kind, blob = entries[path]
            check(kind == 'blob' and mode in {'100644', '100755'}, 'unsupported committed input: ' + path)
            literal(path)
            result[path] = [mode, blob]
    return dict(sorted(result.items()))


def validator_digest():
    directory = Path(__file__).parent
    names = ('verification_evidence.py', 'verification.py', 'verification_checks.py', 'text.py', 'results.py')
    return digest({name: hashlib.sha256((directory / name).read_bytes()).hexdigest() for name in names})


def request_inputs(root, request):
    check(isinstance(request, dict) and not set(request) - REQUEST_FIELDS, 'unknown request field')
    check(type(request.get('schema')) is int and request['schema'] == SCHEMA, 'unsupported evidence schema')
    check(isinstance(request.get('kind'), str) and request['kind'] in KINDS, 'unknown evidence kind')
    check(isinstance(request.get('question'), str) and request['question'].strip(), 'question required')
    check(isinstance(request.get('configuration'), dict), 'configuration object required')
    strings(request.get('scope'), 'scope', True)
    strings(request.get('inputs'), 'inputs')
    commit = revision(root, request.get('revision'))
    kind = request['kind']
    if kind == 'review':
        strings(request.get('requirements'), 'requirements', True)
    if kind == 'scout':
        strings(request.get('requested_fields'), 'requested_fields', True)
    if kind == 'acceptance':
        check('report_path' in request, 'acceptance requires report_path')
    entries = tree(root, commit)
    scope = manifest(entries, request['scope'])
    additional = manifest(entries, request['inputs'])
    selected = {k: v for k, v in request.items() if k != 'revision'}
    if 'report_path' in selected:
        name = literal(selected['report_path'])
        check(re.fullmatch(r'\.planning/phases/[^/]+/[0-9]+(?:\.[0-9]+)?-VERIFICATION\.md', name),
              'report_path must be an exact phase report')
        check(name in entries, 'report_path must be tracked at inspected revision')
        selected['report_blob'] = entries[name]
    if kind == 'acceptance':
        selected['revision'] = commit
    selected.update(scope_manifest=scope, input_manifest=additional,
                    validator=validator_digest())
    return selected


def findings(value):
    check(isinstance(value, list), 'findings must be an array')
    for item in value:
        check(isinstance(item, dict) and not set(item) - {'severity', 'message', 'resolved', 'evidence'},
              'invalid finding schema')
        check(isinstance(item.get('severity'), str) and item['severity'] in SEVERITIES and isinstance(item.get('message'), str)
              and item['message'].strip() and type(item.get('resolved')) is bool,
              'finding requires severity, message and resolved boolean')
        if 'evidence' in item:
            check(isinstance(item['evidence'], str) and item['evidence'].strip(), 'invalid finding evidence')
    return not any(not item['resolved'] for item in value)


def result_valid(request, result, inputs):
    check(isinstance(result, dict) and not set(result) - RESULT_FIELDS, 'unknown result field')
    check(isinstance(result.get('status'), str) and result['status'] in STATUSES, 'invalid result status')
    check(result.get('inspected_revision') == request['revision'], 'inspected_revision mismatch')
    clear = findings(result.get('findings'))
    unresolved = strings(result.get('unresolved_questions', []), 'unresolved_questions')
    check(isinstance(result.get('provenance'), dict) and result['provenance'], 'validation provenance required')
    complete = result['status'] in {'passed', 'complete'}
    scope = sorted(inputs['scope_manifest'])
    if request['kind'] in {'review', 'acceptance'}:
        strings(result.get('covered_paths'), 'covered_paths')
        check(not complete or sorted(result['covered_paths']) == scope, 'incomplete review/acceptance coverage')
    if request['kind'] == 'scout':
        fields = request['requested_fields']
        check(isinstance(result.get('field_results'), dict) and
              set(result['field_results']) == set(fields), 'field_results must cover exactly requested_fields')
        strings(result.get('evidence'), 'evidence', complete)
        strings(result.get('search_scope'), 'search_scope')
        claims = strings(result.get('absence_claims', []), 'absence_claims')
        check(set(claims) <= set(fields), 'absence_claims must name requested fields')
        check(not (complete or claims) or sorted(result['search_scope']) == scope,
              'complete extraction/absence requires complete declared manifest coverage')
        check(not claims or complete, 'incomplete packet cannot claim absence')
        for name, field in result['field_results'].items():
            check(isinstance(field, dict) and not set(field) - {'status', 'value', 'evidence'},
                  'field_results entries require a structured result')
            check(isinstance(field.get('status'), str) and field['status'] in {'found', 'absent', 'incomplete'},
                  'invalid scout field status')
            strings(field.get('evidence'), 'field evidence', field['status'] != 'incomplete')
            check(field['status'] != 'found' or field.get('value') is not None,
                  'found field requires a non-null value')
            check((field['status'] == 'absent') == (name in claims), 'absent fields must match absence_claims')
            if field['status'] == 'incomplete':
                clear = False
        check(not claims or not unresolved, 'unresolved search cannot claim absence')
    return complete and clear and not unresolved


def effective_status(request, result):
    if result['status'] in {'passed', 'complete'} and (result.get('unresolved_questions') or
            (request['kind'] == 'scout' and any(field['status'] == 'incomplete'
                                              for field in result['field_results'].values()))):
        return 'incomplete'
    return result['status']


def storage(root):
    path = root / STORE
    for parent in (root / '.planning', path):
        check(not parent.is_symlink(), 'evidence storage symlink')
    path.mkdir(parents=True, exist_ok=True)
    check(not (path / '.gitignore').is_symlink(), 'evidence ignore file symlink')
    with (path / '.gitignore').open('a', encoding='utf-8') as handle:
        if (path / '.gitignore').stat().st_size == 0:
            handle.write('*\n')
    return path


def save(root, key, receipt):
    path = storage(root)
    temporary = path / (uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps({'receipt': receipt, 'sha256': digest(receipt)},
                                        sort_keys=True), encoding='utf-8')
        os.replace(temporary, path / (key + '.json'))
    finally:
        temporary.unlink(missing_ok=True)
    return STORE + '/' + key + '.json'


def load(root, key):
    try:
        path = root / STORE / (key + '.json')
        check(not any(p.is_symlink() for p in (path, path.parent, root / '.planning')), 'symlink receipt')
        packet = strict_json(path)
        check(set(packet) == {'receipt', 'sha256'} and digest(packet['receipt']) == packet['sha256'],
              'receipt integrity mismatch')
        return packet['receipt']
    except (VerbError, OSError, ValueError, TypeError, KeyError, RecursionError):
        return None


def record(workspace, request_path, result_path):
    root = workspace.root
    request = strict_json(request_path)
    inputs = request_inputs(root, request)
    recorded_head = head(root)
    check(clean(root), 'record requires a clean worktree; inspected inputs come from the committed revision')
    result = strict_json(result_path)
    reusable = result_valid(request, result, inputs)
    if request['kind'] == 'acceptance' and reusable:
        from .verification import current_report
        current_report(root, request['report_path'], request['revision'])
    key = digest(inputs)
    receipt = {'schema': SCHEMA, 'key': key, 'inputs': inputs, 'request': request,
               'result': result, 'validated_at': datetime.now(timezone.utc).isoformat()}
    check(clean(root) and head(root) == recorded_head and request_inputs(root, request) == inputs,
          'snapshot changed while validating')
    path = save(root, key, receipt)
    return dict(key=key, receipt=path, reusable=reusable, status=effective_status(request, result),
                inspected_revision=request['revision'], validated_at=receipt['validated_at'])


def lookup(workspace, request_path):
    root = workspace.root
    request = strict_json(request_path)
    inputs = request_inputs(root, request)
    key = digest(inputs)
    output = dict(key=key, receipt=STORE + '/' + key + '.json', reusable=False,
                  status='never_run', reason='missing_or_invalid')
    if not clean(root) or head(root) != request['revision']:
        return dict(output, reason='dirty_or_wrong_head')
    receipt = load(root, key)
    if receipt is None:
        return output
    try:
        check(set(receipt) == {'schema', 'key', 'inputs', 'request', 'result', 'validated_at'}, 'receipt schema')
        check(receipt['schema'] == SCHEMA and receipt['key'] == key and receipt['inputs'] == inputs,
              'receipt inputs mismatch')
        original = receipt['request']
        check(request_inputs(root, original) == inputs, 'original committed inputs mismatch')
        reusable = result_valid(original, receipt['result'], inputs)
        check(isinstance(receipt['validated_at'], str) and
              datetime.fromisoformat(receipt['validated_at']).tzinfo is not None, 'invalid validation timestamp')
        check(clean(root) and head(root) == request['revision'], 'lookup snapshot changed')
        return dict(output, reusable=reusable, status=effective_status(original, receipt['result']),
                    reason='matching_inputs' if reusable else 'failed_incomplete_or_unresolved',
                    inspected_revision=original['revision'], validated_at=receipt['validated_at'],
                    result=receipt['result'])
    except (VerbError, KeyError, TypeError, ValueError, RecursionError):
        return output
