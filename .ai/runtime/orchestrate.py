#!/usr/bin/env python3
"""Run an approved track schedule with isolated workers and serialized delivery.

Python 3.11+, Git and GitHub CLI. See README.md for the execution contract.
The scheduler is an accident guard, not a sandbox for untrusted programs.
"""

from __future__ import annotations

import argparse
import ast
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import contextmanager
from datetime import date
import hashlib
from functools import wraps
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from urllib.parse import quote, unquote, urlsplit

from markdown_it import MarkdownIt


class Blocked(RuntimeError):
    """Preserve this track for recovery; independent tracks may continue."""


class RetryDelivery(Blocked):
    """A target advance requires fresh integration, without another source review."""


def require(condition, message):
    if not condition:
        raise Blocked(message)


def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def state_locked(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.mutex:
            return method(self, *args, **kwargs)
    return call


def repo_locked(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.repo_mutex:
            return method(self, *args, **kwargs)
    return call


def command(argv, cwd, *, timeout=120, input=None, env=None):
    """No shell interpolation; kill the process tree before releasing resources."""
    options = {'start_new_session': True} if os.name != 'nt' else {
        'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
    process = subprocess.Popen(
        argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
        env=env, **options)
    try:
        output, _ = process.communicate(input, timeout=timeout)
    except BaseException:
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                           capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()
        raise
    require(process.returncode == 0,
            f'{argv[0]} exited {process.returncode}: {output[-6000:]}')
    return output.strip()


def git(root, *args):
    return command(['git', *args], root)


def relative_path(value):
    require(isinstance(value, str) and value and '\\' not in value,
            f'Use a nonempty relative POSIX path: {value!r}')
    path = PurePosixPath(value)
    require(not path.is_absolute() and '..' not in path.parts and
            ':' not in value and not value.startswith('-') and
            not any(c in value for c in '*?[]\n\r\x00') and value in (str(path), str(path) + '/'),
            f'Invalid owned path: {value!r}')
    require(str(path) != '.', 'Repository-wide ownership is not a track boundary')
    return value


def covers(scope, path):
    # Case-fold on all hosts so a Linux schedule also works on Windows.
    scope, path = scope.casefold(), path.casefold()
    return path == scope.rstrip('/') or path.startswith(scope) if scope.endswith('/') else path == scope


def overlaps(left, right):
    return covers(left, right.rstrip('/')) or covers(right, left.rstrip('/'))


DOCUMENT_SUFFIXES = ('.md', '.markdown', '.rst', '.adoc')
DOCUMENT_PHASES = ('document', 'docs-review-1', 'docs-fix', 'docs-review-2')
REVIEW_PHASES = ('review-1', 'review-2', 'docs-review-1', 'docs-review-2')
ID_KINDS = ('FIX', 'INTAKE', 'SPEC', 'ADR', 'AMD')


def documentation_path(path):
    return path.casefold().endswith(DOCUMENT_SUFFIXES)


def rebase_record_links(text, source, target, moves=None):
    moves = moves or {}
    source_dir, target_dir = posixpath.dirname(source), posixpath.dirname(target)
    parser = MarkdownIt('commonmark')

    def snapshot(markdown):
        environment, urls = {}, []

        def tokens_shape(tokens):
            shape = []
            for token in tokens:
                attrs = dict(token.attrs)
                for key in ('href', 'src'):
                    if key in attrs:
                        urls.append(attrs[key])
                        attrs[key] = None
                shape.append((token.type, token.tag, token.nesting, token.hidden, token.markup, token.info, attrs,
                              None if token.type == 'inline' else token.content,
                              tokens_shape(token.children) if token.children else None))
            return shape

        shape = tokens_shape(parser.parse(markdown, environment))
        references = [(('reference', key), value) for key, value in sorted(environment.get('references', {}).items())]
        references += [(('duplicate', index), value) for index, value in enumerate(environment.get('duplicate_refs', []))]
        reference_shape = []
        for key, value in references:
            urls.append(value['href'])
            reference_shape.append((key, {k: v for k, v in value.items() if k not in ('href', 'map')}))
        return (shape, reference_shape), urls

    def destination(link):
        try:
            parts = urlsplit(link)
        except ValueError:
            return None
        if not parts.path or parts.scheme or parts.netloc or parts.path.startswith('/'):
            return None
        resolved = posixpath.normpath(posixpath.join(source_dir, unquote(parts.path)))
        if resolved == '..' or resolved.startswith('../'):
            return None
        rebased = posixpath.relpath(moves.get(resolved, resolved), target_dir)
        if parts.path.endswith('/'):
            rebased += '/'
        rebased = quote(rebased, safe="/@!$&'*+,;=-._~")
        if parts.query:
            rebased += '?' + quote(parts.query, safe="/?:@!$&'*+,;=-._~%")
        if parts.fragment:
            rebased += '#' + quote(parts.fragment, safe="/?:@!$&'*+,;=-._~%")
        return rebased

    current = text
    shape, urls = snapshot(current)
    candidates = list(re.finditer(r'\][(:][ \t\r\n]*', text))
    for match in reversed(candidates):
        start = match.end()
        parsed = parser.helpers.parseLinkDestination(text, start, len(text))
        if not parsed.ok:
            continue
        replacement = destination(parsed.str)
        if replacement is None:
            continue
        old_url, new_url = parser.normalizeLink(parsed.str), parser.normalizeLink(replacement)
        if text[start:parsed.pos].startswith('<'):
            replacement = '<' + replacement + '>'
        candidate = current[:start] + replacement + current[parsed.pos:]
        candidate_shape, candidate_urls = snapshot(candidate)
        if candidate_shape != shape or len(candidate_urls) != len(urls):
            continue
        changed = [(before, after) for before, after in zip(urls, candidate_urls) if before != after]
        if changed and all(before == old_url and after == new_url for before, after in changed):
            current, urls = candidate, candidate_urls
    return current


def json_section(text, heading):
    section = re.search(r'^## ' + re.escape(heading) + r'[ \t]*\r?\n(.*?)(?=^#{1,2}[ \t]|\Z)', text, re.M | re.S)
    match = re.search(r'^```json[ \t]*\r?\n(.*?)\r?\n```[ \t]*$', section[1], re.M | re.S) if section else None
    require(match is not None, f'Record is missing its explicit {heading}')
    return json.loads(match[1])


def execution_contract(text):
    contract = json_section(text, 'Execution contract')
    require(isinstance(contract, dict) and isinstance(contract.get('intent_changes'), list) and
            isinstance(contract.get('steps'), list) and isinstance(contract.get('completed_intake'), list),
            'Execution contract needs intent_changes, steps and completed_intake lists')
    seen, documenting = set(), False
    for step in contract['steps']:
        require(isinstance(step, dict) and re.fullmatch(r'[A-Za-z0-9_-]+', step.get('id', '')) and
                step['id'] not in seen and step.get('phase') in ('build', 'document') and
                isinstance(step.get('title'), str) and step['title'].strip(), 'Invalid or duplicate PLAN step')
        seen.add(step['id'])
        require(not documenting or step['phase'] == 'document',
                'PLAN build steps must precede all documentation steps')
        documenting = documenting or step['phase'] == 'document'
    for change in contract['intent_changes']:
        require(isinstance(change, dict) and isinstance(change.get('request'), str) and change['request'].strip() and
                change.get('decision') in ('pending', 'approved', 'rejected') and
                isinstance(change.get('human_resolution'), str), 'Invalid PLAN intent change')
    for record in contract['completed_intake']:
        relative_path(record)
        require(re.fullmatch(r'\.ai/plans/intake/INTAKE-\d+-[^/]+\.md', record), 'Invalid completed INTAKE path')
    return contract


def python_behavior(text):
    tree = ast.parse(text, type_comments=True)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                node.body.pop(0)
    return ast.dump(tree, include_attributes=False)


def validate(config):
    require(config.get('protocol_version') == 3, 'Use protocol_version 3; preserve older runs with their compatible runtime and receipts')
    require(config.get('worktree_root', '.worktrees') == '.worktrees', 'All worktrees must be immediate children of the primary checkout .worktrees/')
    require(config.get('done_partition', 'quarter') in ('quarter', 'month', 'year'), 'Invalid done_partition')
    require(type(config.get('max_process_attempts', 2)) is int and 1 <= config.get('max_process_attempts', 2) <= 3,
            'max_process_attempts must be between 1 and 3')
    for key, expected in (('forge', 'github'), ('merge_strategy', 'merge'), ('auto_merge', 'auto'), ('cleanup_on_merge', True)):
        require(config.get(key, expected) == expected, f'Unsupported runtime {key}: requires {expected}')
    require(not any(key in config for key in ('paths', 'ids')), 'Custom record paths and ID formats are not supported by this runtime')
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', config['run_id']), 'Invalid run_id')
    for field in ('base_branch', 'remote', 'branch_prefix'):
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', config[field]) and
                '..' not in config[field], f'Invalid {field}')
    require(re.fullmatch(r'[\w.-]+/[\w.-]+', config['github_repo']), 'Expected owner/repository')
    require(type(config['max_parallel_tracks']) is int and config['max_parallel_tracks'] > 0,
            'max_parallel_tracks must be positive')
    require(config['required_commands'], 'Autonomous delivery requires verification commands')
    require(config['required_status_checks'] and
            all(isinstance(x, str) and x for x in config['required_status_checks']),
            'Name the required GitHub status checks; an empty result is not a pass')
    config.setdefault('documentation_model', 'gpt-5.6-luna')
    require(isinstance(config['documentation_model'], str) and config['documentation_model'].strip(),
            'Declare a lightweight documentation_model')
    require('documentation_worker_command' in config,
            'Declare a separate documentation_worker_command; no code-model fallback is permitted')
    for argv in [config['worker_command'], config.get('readiness_worker_command', config['worker_command']),
                 config['documentation_worker_command'], *config['required_commands']]:
        require(isinstance(argv, list) and argv and all(isinstance(x, str) and x for x in argv),
                'Commands must be nonempty argv arrays')
    require(any('{model}' in arg for arg in config['documentation_worker_command']),
            'documentation_worker_command must select the lightweight model with {model}')
    require('residual_findings' not in config, 'Residual policy is owned by RULES.md; remove the obsolete override')
    tracks = config['tracks']
    require(tracks and len({t['id'].casefold() for t in tracks}) == len(tracks), 'Duplicate/empty tracks')
    plans, reservations = set(), {kind: [] for kind in ID_KINDS}
    by_id = {t['id']: t for t in tracks}
    for track in tracks:
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', track['id']), 'Invalid track id')
        require(track['owned_paths'] and track['plans'], 'Declare owned paths and plans for every track')
        require(isinstance(track.get('documentation_paths'), list), 'Declare documentation_paths explicitly (may be empty)')
        require(isinstance(track.get('research_paths', []), list) and isinstance(track.get('source_documentation_paths', []), list),
                'Research and source documentation paths must be lists')
        for path in track['owned_paths'] + track['plans'] + track['code_paths'] + track['documentation_paths'] + track.get('research_paths', []) + track.get('source_documentation_paths', []):
            relative_path(path)
        for path in track['code_paths']:
            require(any((not path.endswith('/') or s.endswith('/')) and covers(s, path.rstrip('/'))
                        for s in track['owned_paths']), 'Code paths must be owned')
        for path in track['documentation_paths']:
            require(any((not path.endswith('/') or s.endswith('/')) and covers(s, path.rstrip('/'))
                        for s in track['owned_paths']), 'Documentation paths must be owned')
            require(path.endswith('/') or documentation_path(path), 'Documentation paths cannot name source files')
            require(not any(overlaps(path, code) for code in track['code_paths']),
                    'Documentation paths and code paths must be disjoint')
        for plan in track['plans']:
            require(re.fullmatch(r'\.ai/plans/(backlog|active|review)/PLAN-\d+-[^/]+\.md', plan),
                    f'PLAN must be in an executable lifecycle stage: {plan}')
            require(plan.casefold() not in plans, f'Plan scheduled twice: {plan}')
            require(any(covers(s, plan) for s in track['owned_paths']), f'Plan not owned: {plan}')
            plans.add(plan.casefold())
        for path in track.get('research_paths', []):
            require(path.startswith('.ai/research/') and documentation_path(path) and not path.endswith('/') and
                    any(covers(s, path) for s in track['owned_paths']) and
                    not any(overlaps(path, s) for s in track['documentation_paths'] + track['code_paths']),
                    'Research notes must be exact, separately owned .ai/research documents')
        for path in track.get('source_documentation_paths', []):
            require(not path.endswith('/') and not documentation_path(path) and
                    any(covers(s, path) for s in track['code_paths']), 'Source documentation must name an owned code file')
            if not path.endswith('.py'):
                argv = track.get('source_documentation_check')
                require(isinstance(argv, list) and argv and all(isinstance(a, str) and a for a in argv) and
                        any('{before}' in a for a in argv) and any('{after}' in a for a in argv),
                        'Non-Python source documentation needs a behavior-equivalence command with {before} and {after}')
        require(all(d in by_id and d != track['id'] for d in track['depends_on']), 'Unknown/self dependency')
        require(isinstance(track['resources'], list) and
                all(isinstance(x, str) and x for x in track['resources']), 'Declare exclusive resources')
        require(all(isinstance(k, str) and isinstance(v, str)
                    for k, v in track.get('environment', {}).items()), 'Environment values must be strings')
        for path in track.get('disposable_paths', []):
            relative_path(path)
            require(path.endswith('/') and not path.casefold().startswith(('.git/', '.worktrees/')),
                    'Disposable paths must be explicit generated directories')
        for kind in reservations:
            start, end = track['ids'][kind]
            require(type(start) is int and type(end) is int and 0 < start and end - start == 19, 'Reserve exactly 20 IDs of each type')
            require(not any(start <= old_end and old_start <= end for old_start, old_end in reservations[kind]),
                    f'Overlapping {kind} reservations')
            reservations[kind].append((start, end))
    visiting, visited = set(), set()
    def visit(key):
        require(key not in visiting, 'Cyclic dependencies')
        if key in visited:
            return
        visiting.add(key)
        for dep in by_id[key]['depends_on']:
            visit(dep)
        visiting.remove(key)
        visited.add(key)
    for key in by_id:
        visit(key)
    return config


@contextmanager
def run_lock(directory):
    """OS-released lock shared by ALL schedules using this Git common directory."""
    path = directory / 'scheduler.lock'
    with path.open('a+b') as handle:
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            if not handle.read(1):
                handle.write(b'0')
                handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                raise Blocked('Another scheduler owns this repository') from exc
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise Blocked('Another scheduler owns this repository') from exc
        try:
            yield
        finally:
            if os.name == 'nt':
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)


FINDING = {
    'type': 'object', 'additionalProperties': False,
    'properties': {k: {'type': 'string'} for k in
                   ('key', 'kind', 'severity', 'title', 'path', 'detail')},
    'required': ['key', 'kind', 'severity', 'title', 'path', 'detail']}
FINDING['properties']['kind']['enum'] = ['code', 'documentation', 'contract', 'question']
FINDING['properties']['severity']['enum'] = ['critical', 'major', 'minor', 'cosmetic']
FINDING['properties']['impact'] = {'type': 'string', 'enum': [
    'missing_code', 'missing_functionality', 'missing_spec_coverage', 'editorial', 'unrelated']}
FINDING['required'].append('impact')
RESULT_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'status': {'type': 'string', 'enum': ['complete', 'blocked']},
        'verdict': {'type': 'string', 'enum': ['approved', 'changes_requested', 'cannot_review', 'not_applicable']},
        'summary': {'type': 'string'},
        'implementation_complete': {'type': 'boolean'},
        'documentation_complete': {'type': 'boolean'},
        'resolved_intake': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'properties': {'path': {'type': 'string'}, 'evidence': {'type': 'string'}}, 'required': ['path', 'evidence']}},
        'spec_coverage': {'type': 'array', 'items': {'type': 'object', 'additionalProperties': False,
            'properties': {key: {'type': 'string'} for key in ('plan', 'spec', 'evidence')},
            'required': ['plan', 'spec', 'evidence']}},
        'findings': {'type': 'array', 'items': FINDING}},
    'required': ['status', 'verdict', 'summary', 'findings', 'implementation_complete', 'documentation_complete', 'resolved_intake', 'spec_coverage']}


class Runner:
    def __init__(self, config):
        self.config = validate(config)
        self.root = Path(config['repository']).resolve()
        require(Path(git(self.root, 'rev-parse', '--show-toplevel')).resolve() == self.root,
                'repository must be the exact base checkout root')
        primary = git(self.root, 'worktree', 'list', '--porcelain').splitlines()[0].removeprefix('worktree ')
        require(Path(primary).resolve() == self.root and (self.root / '.git').is_dir(),
                'repository must be the primary checkout; nested worktrees are forbidden')
        self.common = Path(git(self.root, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
        self.runtime = self.common / 'orchestration'
        self.directory = self.runtime / config['run_id']
        self.directory.mkdir(parents=True, exist_ok=True)
        self.state_path = self.directory / 'state.json'
        self.mutex = threading.RLock()
        self.repo_mutex = threading.RLock()
        fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
        self.fingerprint = fingerprint
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text(encoding='utf-8'))
            require(self.state['config_hash'] == fingerprint, 'Schedule changed; use a new run id')
        else:
            self.state = {'config_hash': fingerprint, 'tracks': {
                t['id']: {'status': 'pending', 'completed_phases': {}, 'findings': {},
                          'plans': t['plans'], 'ids': t['ids']}
                for t in config['tracks']}}
        self.schema = self.directory / 'result-schema.json'
        atomic_json(self.schema, RESULT_SCHEMA)

    def save(self):
        with self.mutex:
            atomic_json(self.state_path, self.state)

    def update(self, state, **values):
        with self.mutex:
            state.update(values)
            self.save()

    def gh(self, *args):
        return command(['gh', *args], self.root)

    def api(self, suffix):
        return json.loads(self.gh('api', f"repos/{self.config['github_repo']}/{suffix}"))

    @repo_locked
    def sync(self):
        cfg = self.config
        require(git(self.root, 'branch', '--show-current') == cfg['base_branch'], 'Base branch changed')
        require(not git(self.root, 'status', '--porcelain'), 'Base checkout is dirty')
        ref = f"refs/remotes/{cfg['remote']}/{cfg['base_branch']}"
        git(self.root, 'fetch', cfg['remote'], f"refs/heads/{cfg['base_branch']}:{ref}")
        git(self.root, 'merge', '--ff-only', ref)
        head = git(self.root, 'rev-parse', 'HEAD')
        require(head == git(self.root, 'rev-parse', ref), 'Base has local commits; not synchronized')
        require(not git(self.root, 'diff', 'HEAD'), 'Base working files differ after sync')
        return head

    def preflight(self):
        self.sync()
        cfg = self.config
        remote_url = git(self.root, 'remote', 'get-url', cfg['remote'])
        require(self.gh('repo', 'view', remote_url, '--json', 'nameWithOwner', '--jq', '.nameWithOwner').casefold()
                == cfg['github_repo'].casefold(), 'GitHub repository does not match checkout')
        for receipt in self.runtime.glob('*/state.json'):
            if receipt == self.state_path:
                continue
            previous = json.loads(receipt.read_text(encoding='utf-8'))
            require(all((s['status'] == 'merged' and s.get('cleaned')) or
                        (s['status'] == 'abandoned' and s.get('released'))
                        for s in previous['tracks'].values()),
                    f'An earlier run still owns worktrees/resources: {receipt.parent.name}')
            for state in previous['tracks'].values():
                for kind, (start, end) in state.get('ids', {}).items():
                    require(not any(start <= t['ids'][kind][1] and t['ids'][kind][0] <= end
                                    for t in cfg['tracks']), f'{kind} reservation reused from {receipt.parent.name}')
        # Strict checks make a target advance reject the merge on the server.
        protection = self.api(f"branches/{quote(cfg['base_branch'], safe='')}/protection")
        checks = protection.get('required_status_checks') or {}
        contexts = set(checks.get('contexts', [])) | {c['context'] for c in checks.get('checks', [])}
        require(checks.get('strict') is True and set(cfg['required_status_checks']) <= contexts and
                protection.get('enforce_admins', {}).get('enabled') is True,
                'Autonomous merge requires strict named checks enforced for administrators too')
        self.protected_checks = contexts

    def worker_environment(self, track):
        # Interpreter caches and temporary files belong to this run, outside Git worktrees.
        directory = self.directory / 'scratch' / track['id']
        directory.mkdir(parents=True, exist_ok=True)
        return {**os.environ, **track.get('environment', {}),
                'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPYCACHEPREFIX': str(directory / 'pycache'),
                'TMPDIR': str(directory), 'TEMP': str(directory), 'TMP': str(directory),
                'XDG_CACHE_HOME': str(directory / 'cache')}

    def discard_generated(self, track):
        """Remove only declared, initially absent, ignored output; preserve everything else."""
        path, _ = self.location(track)
        state = self.state['tracks'][track['id']]
        for name in state.get('disposable_paths', []):
            target = path / name
            require(target.resolve() == target and target.is_relative_to(path), 'Generated path redirected')
            if not target.exists():
                continue
            require(target.is_dir(), 'Generated directory replaced by a file')
            require(not git(path, '--literal-pathspecs', 'ls-files', '--', name), 'Generated directory contains tracked files')
            git(path, 'check-ignore', str(target))
            for child in target.rglob('*'):
                require(child.resolve() == child and not child.is_symlink(), 'Generated output contains a redirected path')
            shutil.rmtree(target)

    def location(self, track):
        path = self.root / '.worktrees' / f"{self.config['run_id']}-{track['id']}"
        require((self.root / '.worktrees').resolve() == self.root / '.worktrees' and
                path.resolve() == path, 'Worktree path escaped or was redirected')
        branch = f"{self.config['branch_prefix']}/{self.config['run_id']}/{track['id']}"
        return path, branch

    def ownership(self, track, path):
        require(path.resolve() == self.location(track)[0].resolve(), 'Worktree ownership changed')
        require(Path(git(path, 'rev-parse', '--show-toplevel')).resolve() == path.resolve(), 'Wrong worktree')
        require(git(path, 'branch', '--show-current') == self.location(track)[1], 'Track branch changed')

    def plan_contracts(self, track, base):
        contracts = {}
        for plan in track['plans']:
            contract = execution_contract(git(self.root, 'show', f'{base}:{plan}'))
            for change in contract['intent_changes']:
                require(change['decision'] == 'approved' and change['human_resolution'].strip(),
                        f"Human intent decision required before implementing {plan}: {change['request']}")
            for record in contract['completed_intake']:
                require(any(covers(s, record) for s in track['owned_paths']), f'Completion INTAKE not owned: {record}')
            contracts[plan] = contract
        return contracts

    def phase_steps(self, track, phase):
        state = self.state['tracks'][track['id']]
        return [{'plan': plan, **step} for plan, contract in state['plan_contracts'].items()
                for step in contract['steps'] if step['phase'] == phase]

    def documentation_only(self, track):
        return not track['code_paths'] and not track.get('source_documentation_paths')

    def required_reviews(self, track):
        return REVIEW_PHASES[2:] if self.documentation_only(track) else REVIEW_PHASES

    def readiness(self, track, base, contracts):
        state = self.state['tracks'][track['id']]
        require(not state.get('inflight_phase'), 'Reconcile the unfinished readiness worker before retrying')
        receipt = state.get('readiness')
        if receipt and receipt['base_sha'] == base:
            require(receipt['result']['status'] == 'complete' and receipt['result']['verdict'] == 'approved' and
                    not receipt['result']['findings'], 'PLAN readiness needs a revised proposal or human resolution')
            return
        if self.documentation_only(track):
            require(not track.get('research_paths') and not any(
                step['phase'] == 'build' for contract in contracts.values() for step in contract['steps']),
                'Documentation-only tracks cannot declare build steps or research writes')
        token = f"{track['id']}-readiness-{time.time_ns()}"
        result_file = self.directory / f'{token}.json'
        mapping = {'worktree': str(self.root), 'phase': 'readiness', 'sandbox': 'read-only',
                   'schema_file': str(self.schema), 'result_file': str(result_file),
                   'model': self.config.get('code_model', 'worker-command-default')}
        context = {'phase': 'readiness', 'worktree': str(self.root), 'base_sha': base,
                   'plan_source_sha': base, 'track': track['id'], 'plans': track['plans'],
                   'plan_contracts': contracts, 'owned_paths': track['owned_paths'],
                   'code_paths': track['code_paths'], 'documentation_paths': track['documentation_paths'],
                   'depends_on': track['depends_on'], 'required_commands': self.config['required_commands']}
        prompt = ('Read AGENTS.md, .ai/RULES.md and .ai/agents/plan-checker.md. Perform only a read-only readiness check. '
                  'Use git show at the immutable base_sha for PLANs, intent, contracts and code. '
                  'Verify acceptance, scope, step ordering and prerequisites against that revision, '
                  'including substantive expected changes; no-change work is not ready for allocation. '
                  'Do not edit, commit, create worktrees or launch agents. Return the supplied result schema: '
                  'approved with no findings means ready; changes_requested or cannot_review parks the PLAN.\n' +
                  json.dumps(context, indent=2))
        argv = [arg.format_map(mapping) for arg in self.config.get('readiness_worker_command', self.config['worker_command'])]
        attempts = state.setdefault('readiness_attempts', {})
        require(attempts.get(base, 0) < self.config.get('max_process_attempts', 2), 'Readiness process retry budget exhausted')
        attempts[base] = attempts.get(base, 0) + 1
        self.update(state, inflight_phase='readiness', worker_stopped=False,
                    inflight={'name': 'readiness', 'before': base, 'result_file': str(result_file),
                              'readonly': True, 'argv': argv})
        try:
            output = command(argv, self.root, input=prompt, timeout=self.config.get('worker_timeout_seconds', 3600),
                             env={**self.worker_environment(track), 'ORCH_CONTEXT': json.dumps(context),
                                  'ORCH_RESULT': str(result_file)})
        finally:
            self.update(state, worker_stopped=True)
        (self.directory / f'{token}.log').write_text(output, encoding='utf-8')
        self.consume_readiness(track)

    def consume_readiness(self, track):
        state = self.state['tracks'][track['id']]
        phase = state['inflight']
        result = json.loads(Path(phase['result_file']).read_text(encoding='utf-8'))
        self.validate_phase_result(result, 'readiness')
        with self.repo_mutex:
            require(not git(self.root, 'status', '--porcelain'), 'Readiness worker changed the primary checkout')
            self.sync()
        receipt = {'base_sha': phase['before'], 'result': result, 'result_file': phase['result_file']}
        with self.mutex:
            state['readiness'] = receipt
            state.setdefault('readiness_history', []).append(receipt)
            state.pop('inflight_phase', None)
            state.pop('inflight', None)
            state.pop('worker_stopped', None)
            self.save()
        require(result['status'] == 'complete' and result['verdict'] == 'approved' and not result['findings'],
                f"PLAN readiness failed: {result['summary']}")

    def documentation_handoff(self, state, readonly):
        allowed = ('build', 'review-1', 'fix', 'review-2')
        if not readonly:
            allowed += ('document', 'docs-review-1')
        return {name: result for name, result in state['completed_phases'].items() if name in allowed}

    def documentation_equivalent(self, track, name, before, after):
        path, _ = self.location(track)
        old = git(path, 'show', f'{before}:{name}')
        new = git(path, 'show', f'{after}:{name}') if after else (path / name).read_text(encoding='utf-8')
        if name.endswith('.py'):
            require(python_behavior(old) == python_behavior(new), f'Documentation changed executable behavior: {name}')
        else:
            scratch = self.directory / 'scratch' / track['id'] / 'documentation-check'
            scratch.mkdir(parents=True, exist_ok=True)
            left, right = scratch / ('before' + Path(name).suffix), scratch / ('after' + Path(name).suffix)
            left.write_text(old, encoding='utf-8')
            right.write_text(new, encoding='utf-8')
            mapping = {'before': str(left), 'after': str(right)}
            command([arg.format_map(mapping) for arg in track['source_documentation_check']], path,
                    env=self.worker_environment(track))

    def created_finding(self, track, name, before, after=None):
        match = re.fullmatch(r'\.ai/(fixes/open/(FIX)|plans/intake/(INTAKE))-(\d+)-[^/]+\.md', name)
        if not match:
            return False
        kind, number = match[2] or match[3], int(match[4])
        start, end = track['ids'][kind]
        require(start <= number <= end, f'Worker finding outside reserved {kind} IDs: {name}')
        path, _ = self.location(track)
        require(not git(path, 'ls-tree', '--name-only', before, '--', name), 'Workers may create findings, not rewrite existing reports')
        content = git(path, 'show', f'{after}:{name}') if after else (path / name).read_text(encoding='utf-8')
        expected = f'{kind}-{number:03d}'
        require(re.search(rf'^id:\s*[\"\']?{re.escape(expected)}[\"\']?\s*$', content, re.M), 'Finding file ID does not match its reserved filename')
        existing = git(path, 'ls-tree', '-r', '--name-only', before, '--', '.ai').splitlines()
        require(not any(Path(p).name.startswith(expected + '-') for p in existing), f'ID already exists: {expected}')
        self.state['tracks'][track['id']].setdefault('worker_records', {})[name] = expected
        return True

    def audit_worker_paths(self, track, phase, names, before, after=None):
        docs = phase in DOCUMENT_PHASES
        scopes = (track['documentation_paths'] + track.get('source_documentation_paths', [])) if docs else track['code_paths']
        for name in names:
            if not docs and self.created_finding(track, name, before, after):
                continue
            if phase == 'build' and name in track.get('research_paths', []):
                continue
            if docs and name in track.get('source_documentation_paths', []):
                self.documentation_equivalent(track, name, before, after)
                continue
            require(not name.casefold().startswith(('.ai/state/', '.ai/fixes/', '.ai/plans/intake/')) and
                    any(covers(s, name) for s in scopes), f'Worker change outside {phase} ownership: {name}')
            if docs:
                require(documentation_path(name), f'Documentation worker cannot change source: {name}')
            else:
                require(not documentation_path(name) and not name.casefold().startswith(('.ai/specs/', '.ai/decisions/')),
                        f'Code worker cannot change docs/contracts: {name}')

    def audit(self, track, path):
        self.ownership(track, path)
        state = self.state['tracks'][track['id']]
        # Imported target commits are owned by the target, not by this track.
        baseline = state.get('integration_base', state['base'])
        paths = git(path, 'diff', '--name-only', '--no-renames', '-z', baseline, 'HEAD').split('\0')
        records = {f['record'] for f in state['findings'].values()}
        records.update(state.get('worker_records', {}))
        records.update(state.get('plan_moves', {}).values())
        for changed in filter(None, paths):
            require(not changed.casefold().startswith(('.ai/state/state.md', '.ai/state/journal/', '.ai/state/orchestration/')),
                    f'Track touched shared coordinator state: {changed}')
            require(changed in records or any(covers(s, changed) for s in track['owned_paths']),
                    f'Change outside declared ownership: {changed}')
        require(not git(path, 'status', '--porcelain'), 'Worker left uncommitted/untracked changes')

    def phase(self, track, name, *, readonly=False, extra=''):
        require(name in ('build', 'fix', *REVIEW_PHASES, 'document', 'docs-fix'), 'Unknown phase')
        require(readonly == (name in REVIEW_PHASES), 'Review phases must be read-only')
        state = self.state['tracks'][track['id']]
        if name in state['completed_phases']:
            result = state['completed_phases'][name]
            require(result['status'] == 'complete', result['summary'])
            return result
        path, _ = self.location(track)
        self.audit(track, path)
        before = git(path, 'rev-parse', 'HEAD')
        require(before == state.get('checkpoint_head', state['base']), 'Phase HEAD changed outside coordinator')
        docs = name in DOCUMENT_PHASES
        model = self.config['documentation_model'] if docs else self.config.get('code_model', 'worker-command-default')
        scopes = (track['documentation_paths'] + track.get('source_documentation_paths', [])) if docs else track['code_paths']
        token = f"{track['id']}-{name}-{time.time_ns()}"
        result_file = self.directory / f'{token}.json'
        mapping = {'worktree': str(path), 'result_file': str(result_file),
                   'schema_file': str(self.schema), 'phase': name,
                   'sandbox': 'read-only' if readonly else 'workspace-write', 'model': model}
        worker_command = self.config['documentation_worker_command'] if docs else self.config['worker_command']
        argv = [arg.format_map(mapping) for arg in worker_command]
        context = {
            'run': self.config['run_id'], 'track': track['id'], 'phase': name,
            'worktree': str(path), 'branch': self.location(track)[1], 'base_sha': state['base'],
            'plan_source_sha': state['base'],
            'plans': track['plans'], 'owned_paths': track['owned_paths'], 'code_paths': track['code_paths'],
            'documentation_paths': track['documentation_paths'], 'phase_paths': scopes,
            'source_documentation_paths': track.get('source_documentation_paths', []),
            'research_paths': track.get('research_paths', []), 'reserved_ids': track['ids'],
            'steps': self.phase_steps(track, name) if name in ('build', 'document') else [],
            'plan_contracts': state['plan_contracts'],
            'documentation_handoff': self.documentation_handoff(state, readonly) if docs else {},
            'model': model, 'documentation_model': self.config['documentation_model'],
            'review_kind': 'documentation' if docs else 'code',
            'code_reviewed_sha': state.get('code_reviewed_sha'),
            'resources': track['resources'], 'required_commands': self.config['required_commands']}
        role = ('track-documentation-reviewer' if docs else 'track-reviewer') if readonly else (
            'track-documentor' if docs else 'track-fixer' if name == 'fix' else 'track-implementor')
        prompt = (f'Follow AGENTS.md and .ai/RULES.md, especially Roles, Runtime worker protocol, '
                  f'Review and documentation, and Definition of done. Your role entry point is .ai/agents/{role}.md. '
                  '\nAssignment:\n' + json.dumps(context, indent=2) + '\n' + extra +
                  '\nReturn the supplied result schema to result_file/ORCH_RESULT.')
        attempts = state.setdefault('process_attempts', {})
        require(attempts.get(name, 0) < self.config.get('max_process_attempts', 2), 'Process retry budget exhausted')
        require(not state.get('inflight_phase'), 'Reconcile the unfinished worker before another process attempt')
        attempts[name] = attempts.get(name, 0) + 1
        self.update(state, inflight_phase=name, worker_stopped=False,
                    inflight={'name': name, 'before': before, 'result_file': str(result_file), 'readonly': readonly,
                              'model': model, 'argv': argv, 'paths': scopes})
        try:
            output = command(argv, path, input=prompt, timeout=self.config.get('worker_timeout_seconds', 3600),
                             env={**self.worker_environment(track), 'ORCH_CONTEXT': json.dumps(context),
                                  'ORCH_RESULT': str(result_file)})
        except Exception as exc:
            # command() waits for termination before returning an error. A process crash
            # of this scheduler leaves this flag absent and requires explicit reconciliation.
            self.update(state, worker_stopped=True)
            if result_file.is_file():
                result = json.loads(result_file.read_text(encoding='utf-8'))
                self.validate_result(result)
                self.record_findings(track, result, self.phase_round(name), publish=False, source_head=before, phase_name=name)
            if docs:
                raise Blocked(f'Lightweight documentation phase {name} ({model}) failed: {exc}') from exc
            raise
        (self.directory / f'{token}.log').write_text(output, encoding='utf-8')
        self.update(state, worker_stopped=True)
        return self.consume_result(track)

    @staticmethod
    def phase_round(name):
        return 2 if name.endswith('review-2') else 0 if name in ('build', 'document') else 1

    @staticmethod
    def validate_result(result):
        require(isinstance(result, dict) and result.get('status') in ('complete', 'blocked') and
                isinstance(result.get('findings'), list) and isinstance(result.get('summary'), str) and
                result.get('verdict') in RESULT_SCHEMA['properties']['verdict']['enum'], 'Malformed worker result')
        require(type(result.get('implementation_complete')) is bool and type(result.get('documentation_complete')) is bool,
                'Worker must explicitly report implementation and SPEC coverage completeness')
        require(isinstance(result.get('resolved_intake'), list) and all(isinstance(item, dict) and
                isinstance(item.get('path'), str) and isinstance(item.get('evidence'), str) and item['evidence'].strip()
                for item in result['resolved_intake']), 'Resolved INTAKE items need paths and completion evidence')
        require(isinstance(result.get('spec_coverage'), list) and all(isinstance(item, dict) and
                all(isinstance(item.get(key), str) and item[key].strip() for key in ('plan', 'spec', 'evidence'))
                for item in result['spec_coverage']), 'SPEC coverage needs PLAN, SPEC and code evidence')
        for finding in result['findings']:
            require(isinstance(finding, dict) and set(FINDING['required']) <= finding.keys() and
                    all(isinstance(finding[k], str) and finding[k].strip() for k in FINDING['required']),
                    'Finding needs a key, kind, severity, title, path and evidence')
            require(finding['kind'] in ('code', 'documentation', 'contract', 'question'), 'Invalid finding kind')
            require(finding['severity'] in ('critical', 'major', 'minor', 'cosmetic'), 'Invalid severity')
            require(finding['impact'] in FINDING['properties']['impact']['enum'], 'Invalid finding impact')
            require(finding['kind'] != 'code' or finding['impact'] in ('missing_code', 'missing_functionality', 'unrelated'),
                    'A code defect cannot be dismissed as editorial')

    @classmethod
    def validate_phase_result(cls, result, name):
        cls.validate_result(result)
        if result['status'] != 'complete' or name not in (*REVIEW_PHASES, 'readiness'):
            return
        require(result['verdict'] in ('approved', 'changes_requested', 'cannot_review'), 'Invalid review verdict')
        if result['verdict'] != 'cannot_review':
            require((result['verdict'] == 'approved') == (len(result['findings']) == 0), 'Inconsistent review verdict')
        if name != 'readiness':
            kinds = ('documentation', 'contract', 'question') if name in DOCUMENT_PHASES else ('code', 'question')
            require(all(f['kind'] in kinds for f in result['findings']), 'Reviewer crossed its code/documentation scope')

    def consume_result(self, track):
        state = self.state['tracks'][track['id']]
        path, _ = self.location(track)
        phase = state['inflight']
        name, before, readonly = phase['name'], phase['before'], phase['readonly']
        result_file = Path(phase['result_file'])
        require(result_file.is_file(), 'Worker did not produce its result')
        result = json.loads(result_file.read_text(encoding='utf-8'))
        self.validate_phase_result(result, name)
        # Queue confirmed findings even if the worker is blocked or its edits fail audit.
        self.record_findings(track, result, self.phase_round(name), publish=False, source_head=before, phase_name=name)
        require(result['status'] == 'complete', result['summary'])
        if name in DOCUMENT_PHASES:
            require(type(result.get('documentation_complete')) is bool,
                    'Documentation phase must explicitly verify original PLAN promises')
        if readonly:
            require(git(path, 'rev-parse', 'HEAD') == before, 'Read-only worker changed HEAD')
        else:
            self.commit_worker_changes(track, name, before)
        self.audit(track, path)
        with self.mutex:
            state.setdefault('phase_heads', {})[name] = before
            state.setdefault('phase_receipts', {})[name] = {
                **phase, 'after': git(path, 'rev-parse', 'HEAD')}
            state['completed_phases'][name] = result
            state.setdefault('phase_attempts', {})[name] = 1
            state.pop('inflight_phase', None)
            state.pop('inflight', None)
            state.pop('worker_stopped', None)
            state['checkpoint_head'] = git(path, 'rev-parse', 'HEAD')
            self.save()
        return result

    def commit_worker_changes(self, track, phase, before):
        path, _ = self.location(track)
        self.ownership(track, path)
        require(not git(path, 'diff', '--cached', '--name-only'), 'Worker left staged files outside a completed step')
        expected = self.phase_steps(track, phase) if phase in ('build', 'document') else []
        head = git(path, 'rev-parse', 'HEAD')
        commits = git(path, 'rev-list', '--reverse', f'{before}..{head}').splitlines()
        previous, matched = before, []
        for commit in commits:
            require(git(path, 'rev-list', '--parents', '-n', '1', commit).split()[1:] == [previous],
                    'Worker history must be linear step commits without merge or rewritten ancestry')
            changed = git(path, 'diff', '--name-only', '--no-renames', previous, commit).splitlines()
            require(changed, 'An empty commit does not complete a PLAN step')
            self.audit_worker_paths(track, phase, changed, previous, commit)
            message = git(path, 'show', '-s', '--format=%B', commit)
            marker = re.findall(r'^PLAN-Step: (.+)$', message, re.M)
            if marker:
                require(len(marker) == 1 and len(matched) < len(expected), 'Unexpected or duplicate PLAN step commit')
                step = expected[len(matched)]
                require(marker[0] == f"{step['plan']}#{step['id']}", 'PLAN step commits are missing or out of order')
                require(any(name not in track.get('research_paths', []) and
                            name not in self.state['tracks'][track['id']].get('worker_records', {}) for name in changed),
                        'A finding or research note cannot stand in for an implementation step')
                matched.append({'plan': step['plan'], 'id': step['id'], 'commit': commit})
            else:
                require(phase == 'build' and all(name in track.get('research_paths', []) or
                        name in self.state['tracks'][track['id']].get('worker_records', {}) for name in changed),
                        'Every PLAN step needs its own commit and PLAN-Step trailer')
            previous = commit
        require(previous == head, 'Worker rewound the checkout')
        require(len(matched) == len(expected), 'Missing PLAN step commits; preserve the target and finish the implementation')
        changed = set(filter(None, git(path, 'diff', '--name-only', '--no-renames', '-z', 'HEAD').split('\0')))
        changed.update(filter(None, git(path, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')))
        self.audit_worker_paths(track, phase, changed, head)
        require(phase not in ('build', 'document') or not changed,
                'Uncommitted PLAN work remains; each step must be committed before handoff')
        if changed:
            git(path, '--literal-pathspecs', 'add', '--', *sorted(changed))
            git(path, 'commit', '-m', f"{phase.capitalize()} planned track {track['id']}")
        if phase in ('build', 'document'):
            self.update(self.state['tracks'][track['id']], **{phase + '_step_commits': matched})

    @state_locked
    def record_findings(self, track, result, round_number, *, publish=True, source_head=None, phase_name='legacy'):
        path, _ = self.location(track)
        state = self.state['tracks'][track['id']]
        self.validate_result(result)
        source_head = source_head or git(path, 'rev-parse', 'HEAD')
        for finding in result['findings']:
            key = finding['key']
            if key in state['findings']:
                item = state['findings'][key]
                require(item['kind'] == finding['kind'], 'Finding changed classification')
                if 'history' not in item:
                    item['history'] = [{k: item[k] for k in (*FINDING['required'], 'round', 'reviewed_sha')}]
            else:
                kind = 'FIX' if finding['kind'] == 'code' else 'INTAKE'
                start, end = track['ids'][kind]
                used = {int(f['id'].split('-')[1]) for f in state['findings'].values() if f['id'].startswith(kind + '-')}
                used.update(int(record.split('-')[1]) for record in state.get('worker_records', {}).values() if record.startswith(kind + '-'))
                number = next((n for n in range(start, end + 1) if n not in used), None)
                require(number is not None, f'{kind} ID block exhausted')
                record_id = f'{kind}-{number:03d}'
                require(not list((path / '.ai').rglob(f'{record_id}-*.md')), f'ID already exists: {record_id}')
                folder = '.ai/fixes/open' if kind == 'FIX' else '.ai/plans/intake'
                item = {'id': record_id, 'record': f'{folder}/{record_id}-review.md',
                        'history': [], 'found': str(date.today())}
                state['findings'][key] = item
            evidence = {**finding, 'round': round_number, 'reviewed_sha': source_head, 'phase': phase_name}
            # Re-entering a completed phase is not a new review observation.
            fields = (*FINDING['required'], 'round', 'phase')
            if not any(all(old.get(k) == evidence[k] for k in fields) for old in item['history']):
                item['history'].append(evidence)
                item.update(finding, round=round_number, reviewed_sha=source_head)
        self.write_reports(track, publish=publish)

    def render_finding(self, track, item):
        kind = 'FIX' if item['kind'] == 'code' else 'INTAKE'
        front = {'tier': 'plan', 'authority': 'agent', 'id': item['id'], 'title': item['title'],
                 'found': item.get('found', str(date.today())), 'found_by': 'orchestration review',
                 'found_while': track['plans'], 'severity': item['severity'],
                  'deferred_until': 'affected-tree-available', 'run': self.config['run_id'], 'links': []}
        front['violates' if kind == 'FIX' else 'kind'] = 'none' if kind == 'FIX' else item['kind']
        text = '---\n' + ''.join(f'{k}: {json.dumps(v)}\n' for k, v in front.items()) + '---\n\n'
        text += f"# {item['id']}: {item['title']}\n\n"
        if kind == 'FIX':
            text += f"## Symptom\n\n{item['detail']}\n\n## Root cause\n\nLocation: {item['path']}. Confirm the mechanism before fixing.\n\n## The change\n\nDeferred for the post-PLAN defect pass.\n\n## Proof\n\nNot yet verified; keep open until a regression check proves the correction.\n\n## Contract\n\nCode only. Any documentation or contract correction requires a separate INTAKE.\n"
        else:
            text += f"## What's wrong\n\n{item['detail']}\n\n## Where\n\n{item['path']}\n\n## Why it wasn't fixed then\n\nSeparate {item['kind']} work after the PLAN queue.\n\n## What it costs to leave\n\nSeverity: {item['severity']}.\n"
        text += '\n## Review evidence\n'
        for evidence in item.get('history', [item]):
            text += (f"\nPhase {evidence.get('phase', 'legacy')}, round {evidence['round']}, source {evidence['reviewed_sha']}, "
                     f"severity {evidence['severity']}, location {evidence['path']}.\n\n{evidence['detail']}\n")
        for attempt in item.get('attempts', []):
            text += ('\n## Attempted correction\n\n' + attempt +
                     '\n\nWorker phase summary only; verify per-FIX proof in the post-PLAN pass before closing.\n')
        return text

    def write_reports(self, track, *, publish):
        path, _ = self.location(track)
        state = self.state['tracks'][track['id']]
        for item in state['findings'].values():
            target = self.directory / 'deferred' / track['id'] / item['record']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.render_finding(track, item), encoding='utf-8')
            item.update(report_file=str(target), source_worktree=str(path))
        # The durable queue exists before any attempt to write into a dirty worktree.
        self.save()
        if not publish or not state['findings']:
            return
        self.audit(track, path)
        for item in state['findings'].values():
            target = path / item['record']
            require(target.resolve() == target, 'Finding record path redirected')
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(self.render_finding(track, item), encoding='utf-8')
        records = [f['record'] for f in state['findings'].values()]
        git(path, '--literal-pathspecs', 'add', '--', *records)
        if git(path, 'diff', '--cached', '--name-only'):
            git(path, 'commit', '-m', f"Record deferred review findings for {track['id']}")
        self.update(state, checkpoint_head=git(path, 'rev-parse', 'HEAD'))

    def checks(self, path, track):
        head = git(path, 'rev-parse', 'HEAD')
        for argv in self.config['required_commands']:
            command(argv, path, timeout=self.config.get('check_timeout_seconds', 900),
                    env=self.worker_environment(track))
        require(git(path, 'rev-parse', 'HEAD') == head and not git(path, 'status', '--porcelain'),
                'Checks modified tracked files or left untracked artifacts')

    def pull_request(self, track):
        path, branch = self.location(track)
        state = self.state['tracks'][track['id']]
        require(git(path, 'diff', '--name-only', state['base'], 'HEAD'),
                'No changes available for a pull request; preserve the track without an empty commit')
        git(path, 'push', '-u', self.config['remote'], f'HEAD:refs/heads/{branch}')
        prs = json.loads(self.gh('pr', 'list', '--repo', self.config['github_repo'], '--head', branch,
                                '--base', self.config['base_branch'], '--state', 'all', '--json', 'number,state'))
        require(len(prs) <= 1, 'Ambiguous PR for track branch')
        if prs:
            require(prs[0]['state'] == 'OPEN', 'Track PR is already closed; recover delivery first')
            self.update(state, pr=prs[0]['number'])
        else:
            body = self.directory / f"{track['id']}-pr.md"
            body.write_text('Build plans:\n\n' + '\n'.join('- ' + p for p in track['plans']) +
                            '\n\nAutonomous review and required checks are pending.\n', encoding='utf-8')
            url = self.gh('pr', 'create', '--repo', self.config['github_repo'], '--head', branch,
                          '--base', self.config['base_branch'], '--title', track.get('title', track['id']),
                          '--body-file', str(body))
            self.update(state, pr=int(url.rstrip('/').split('/')[-1]))

    def build(self, track):
        state = self.state['tracks'][track['id']]
        path, _ = self.location(track)
        last = {'findings': []}
        if self.documentation_only(track):
            self.update(state, pipeline='documentation', code_reviewed_sha=state['base'], code_review_verdict='not_applicable')
        else:
            self.update(state, pipeline='code')
            result = self.phase(track, 'build')
            self.record_findings(track, result, 0, phase_name='build', source_head=state['phase_heads']['build'])
            require(result['implementation_complete'], 'Missing code or functionality; create FIX items or a supporting PLAN and preserve the target')
            if git(path, 'diff', '--name-only', state['base'], 'HEAD'):
                self.pull_request(track)
            first = self.phase(track, 'review-1', readonly=True)
            self.record_findings(track, first, 1, phase_name='review-1', source_head=state['phase_heads']['review-1'])
            require(first['verdict'] != 'cannot_review', 'Reviewer cannot review')
            code = [f for f in first['findings'] if f['kind'] == 'code' and f['impact'] != 'unrelated' and
                    any(covers(scope, f['path']) for scope in track['code_paths'])]
            if code:
                fixed = self.phase(track, 'fix', extra='In-scope code findings to diagnose and attempt once:\n' + json.dumps(code))
                self.record_findings(track, fixed, 1, phase_name='fix', source_head=state['phase_heads']['fix'])
                self.record_attempt(track, fixed)
            last = self.phase(track, 'review-2', readonly=True)
            self.record_findings(track, last, 2, phase_name='review-2', source_head=state['phase_heads']['review-2'])
            require(last['verdict'] != 'cannot_review', 'Reviewer cannot review')
            self.update(state, code_reviewed_sha=state['phase_heads']['review-2'], code_review_verdict=last['verdict'])
            require(last['implementation_complete'] and not any(f['impact'] in ('missing_code', 'missing_functionality')
                    for f in last['findings']), 'Missing code or functionality; preserve the target before documentation')
        documented = self.phase(track, 'document')
        self.record_findings(track, documented, 0, phase_name='document', source_head=state['phase_heads']['document'])
        if not state.get('pr'):
            self.pull_request(track)
        docs_first = self.phase(track, 'docs-review-1', readonly=True)
        self.record_findings(track, docs_first, 1, phase_name='docs-review-1', source_head=state['phase_heads']['docs-review-1'])
        require(docs_first['verdict'] != 'cannot_review', 'Documentation reviewer cannot review')
        docs_findings = [f for f in docs_first['findings'] if f['kind'] in ('documentation', 'contract') and
                        f['impact'] != 'unrelated' and
                        any(covers(s, f['path']) for s in track['documentation_paths'] + track.get('source_documentation_paths', []))]
        require(docs_first.get('documentation_complete') is True or docs_findings,
                'Missing documentation promises require actionable findings within assigned documentation scopes')
        if docs_findings:
            fixed = self.phase(track, 'docs-fix', extra='Documentation findings to attempt once:\n' + json.dumps(docs_findings))
            self.record_findings(track, fixed, 1, phase_name='docs-fix', source_head=state['phase_heads']['docs-fix'])
            self.record_attempt(track, fixed, documentation=True)
            require(fixed.get('documentation_complete') is True, 'Documentation correction is incomplete or unverified')
        docs_last = self.phase(track, 'docs-review-2', readonly=True)
        self.record_findings(track, docs_last, 2, phase_name='docs-review-2', source_head=state['phase_heads']['docs-review-2'])
        require(docs_last['verdict'] != 'cannot_review', 'Documentation reviewer cannot review')
        # Reports remain open until the later defect pass verifies their proof.
        # This avoids silently closing a bug merely because a cold review omitted it.
        self.update(state, reviewed_sha=state['phase_heads']['docs-review-2'],
                    documentation_reviewed_sha=state['phase_heads']['docs-review-2'],
                    documentation_review_verdict=docs_last['verdict'], documentation_model=self.config['documentation_model'])
        self.validate_completion(track)
        self.checks(path, track)
        self.finalize_plans(track)
        self.update(state, prepared_head=git(path, 'rev-parse', 'HEAD'))
        generated = {f['record'] for f in state['findings'].values()}
        generated.update(state.get('plan_moves', {}))
        generated.update(state.get('plan_moves', {}).values())
        changed_after_code = set(filter(None, git(path, 'diff', '--name-only', '--no-renames', '-z',
                                                  state['code_reviewed_sha'], 'HEAD').split('\0')))
        for name in changed_after_code & set(track.get('source_documentation_paths', [])):
            self.documentation_equivalent(track, name, state['code_reviewed_sha'], 'HEAD')
        require(all(name in generated or name in track.get('source_documentation_paths', []) or (documentation_path(name) and
                    any(covers(scope, name) for scope in track['documentation_paths'])) for name in changed_after_code),
                'Code changed after the final code review')
        require(set(filter(None, git(path, 'diff', '--name-only', '--no-renames', '-z',
                                    state['reviewed_sha'], 'HEAD').split('\0'))) <= generated,
                'Source changed after the final review')
        residual = last['findings'] + docs_last['findings']
        verdict = 'changes_requested' if residual else 'approved'
        self.update(state, review_verdict=verdict, residual_findings=residual)
        self.checks(path, track)
        self.audit(track, path)
        self.pull_request(track)
        self.update(state, status='ready_with_followups' if state['findings'] else 'ready')

    def validate_completion(self, track):
        state = self.state['tracks'][track['id']]
        phases = state['completed_phases']
        require(all(name in phases for name in self.required_reviews(track)), 'Missing review evidence for completion')
        code = phases.get('review-2', {'implementation_complete': self.documentation_only(track), 'findings': []})
        docs = phases['docs-review-2']
        require(code['implementation_complete'] and not any(f['impact'] in ('missing_code', 'missing_functionality')
                for f in code['findings'] + docs['findings']),
                'Missing code or functionality; preserve the target and report FIX/supporting PLAN actions')
        require(docs['documentation_complete'] and not any(f['impact'] == 'missing_spec_coverage' for f in docs['findings']),
                'Overall implementation is not documented in SPECs; route coverage to the documentor')
        path, _ = self.location(track)
        covered = set()
        for item in docs['spec_coverage']:
            relative_path(item['spec'])
            require(item['plan'] in track['plans'] and re.fullmatch(r'\.ai/specs/SPEC-\d+-[^/]+\.md', item['spec']),
                    'Invalid implementation SPEC coverage')
            require((path / item['spec']).is_file() and (path / item['spec']).read_text(encoding='utf-8').strip(),
                    f"Overall implementation SPEC is missing: {item['spec']}")
            covered.add(item['plan'])
        require(covered == set(track['plans']), 'Overall implementation lacks evidenced SPEC coverage for every PLAN')

    @state_locked
    def record_attempt(self, track, result, *, documentation=False):
        """Store the fixer's actual proof without treating its claim as closure."""
        state = self.state['tracks'][track['id']]
        marker = 'documentation_attempt_recorded' if documentation else 'attempt_recorded'
        if state.get(marker):
            return
        path, _ = self.location(track)
        review = 'docs-review-1' if documentation else 'review-1'
        kinds = ('documentation', 'contract') if documentation else ('code',)
        scopes = track['documentation_paths'] + track.get('source_documentation_paths', []) if documentation else track['code_paths']
        attempted = {f['key'] for f in state['completed_phases'][review]['findings']
                      if f['kind'] in kinds and f['impact'] != 'unrelated' and any(covers(s, f['path']) for s in scopes)}
        for key in attempted:
            state['findings'][key].setdefault('attempts', []).append(result['summary'])
        self.write_reports(track, publish=True)
        state[marker] = True
        self.save()

    @state_locked
    def finalize_plans(self, track):
        """Mechanical lifecycle moves become visible on the target only at merge."""
        state = self.state['tracks'][track['id']]
        if 'plan_moves' in state:
            return
        self.validate_completion(track)
        path, _ = self.location(track)
        moves = {}
        today = date.today()
        partition = self.config.get('done_partition', 'quarter')
        period = (f'{today.year}-Q{(today.month - 1) // 3 + 1}' if partition == 'quarter' else
                  today.strftime('%Y-%m' if partition == 'month' else '%Y'))
        for source in track['plans']:
            if not re.match(r'^\.ai/plans/(backlog|active|review)/PLAN-', source):
                continue
            target = f'.ai/plans/done/{period}/{PurePosixPath(source).name}'
            moves[source] = target
        eligible = {p for contract in state['plan_contracts'].values() for p in contract['completed_intake']}
        for item in state['completed_phases']['docs-review-2']['resolved_intake']:
            source = item['path']
            require(source in eligible, f'Closeout INTAKE was not declared by the PLAN: {source}')
            if source in moves:
                continue
            target = f'.ai/plans/done/{period}/{PurePosixPath(source).name}'
            moves[source] = target
        require(len(set(moves.values())) == len(moves), 'Lifecycle destinations collide')
        contents = {}
        for source, target in moves.items():
            require((path / source).is_file() and not (path / target).exists(), f'Cannot close record: {source}')
            original = (path / source).read_text(encoding='utf-8')
            contents[target] = (original, rebase_record_links(original, source, target, moves))
        for source, target in moves.items():
            (path / target).parent.mkdir(parents=True, exist_ok=True)
            git(path, 'mv', '--', source, target)
            record = path / target
            original, rebased = contents[target]
            if rebased != original:
                record.write_text(rebased, encoding='utf-8')
                git(path, 'add', '--', target)
        if moves:
            git(path, 'commit', '-m', f"Archive completed plans for {track['id']}")
        state['plan_moves'] = moves
        state['checkpoint_head'] = git(path, 'rev-parse', 'HEAD')
        self.save()

    def wait_checks(self, pr, head):
        required = set(self.config['required_status_checks']) | getattr(self, 'protected_checks', set())
        deadline = time.monotonic() + self.config.get('github_timeout_seconds', 900)
        while True:
            data = json.loads(self.gh('pr', 'view', str(pr), '--repo', self.config['github_repo'],
                                     '--json', 'headRefOid,state,statusCheckRollup,reviewDecision'))
            require(data['headRefOid'] == head and data['state'] == 'OPEN', 'PR head/state changed')
            require(data.get('reviewDecision') != 'CHANGES_REQUESTED', 'GitHub review requests changes')
            checks = data.get('statusCheckRollup') or []
            names, pending = set(), False
            for check in checks:
                name = check.get('name', check.get('context'))
                if name not in required:
                    continue
                names.add(name)
                status = check.get('status', check.get('state'))
                result = check.get('conclusion', check.get('state'))
                if status in ('COMPLETED', 'SUCCESS', 'FAILURE', 'ERROR'):
                    require(result == 'SUCCESS', f'GitHub check did not pass: {name}: {result}')
                else:
                    pending = True
            if required <= names and not pending:
                return
            require(time.monotonic() < deadline, 'Required GitHub checks missing or timed out')
            time.sleep(2)

    def deliver(self, track):
        """One delivery worker; CI waits never occupy the dispatch thread."""
        state = self.state['tracks'][track['id']]
        path, branch = self.location(track)
        require(all(name in state['completed_phases'] for name in self.required_reviews(track)) and
                state.get('documentation_reviewed_sha') == state.get('reviewed_sha') and
                state['completed_phases']['docs-review-2'].get('documentation_complete') is True,
                'Delivery requires every review in the assigned pipeline')
        require(state.get('review_verdict') in ('approved', 'changes_requested'), 'No conclusive review for delivery')
        self.validate_completion(track)
        self.ownership(track, path)
        require(not git(path, 'status', '--porcelain'), 'Dirty track cannot be delivered')
        if state.get('delivery_head'):
            require(git(path, 'rev-parse', 'HEAD') == state.get('integration_head', state['delivery_head']),
                    'Delivery HEAD changed')
        else:
            self.audit(track, path)
            require(git(path, 'rev-parse', 'HEAD') == state.get('integration_head', state['prepared_head']),
                    'Source changed after review')
        self.update(state, delivery_stage='validating')
        base = self.sync()
        # Integration happens in the completed track. No worker is still writing it.
        git(path, 'merge', '--no-edit', base)
        self.update(state, integration_base=base, integration_head=git(path, 'rev-parse', 'HEAD'),
                    checkpoint_head=git(path, 'rev-parse', 'HEAD'))
        self.validate_completion(track)
        self.checks(path, track)
        head = git(path, 'rev-parse', 'HEAD')
        self.update(state, status='delivering', delivery_head=head, tested_base=base,
                    tested_tree=git(path, 'rev-parse', 'HEAD^{tree}'))
        git(path, 'push', self.config['remote'], f'HEAD:refs/heads/{branch}')
        body = self.directory / f"{track['id']}-pr.md"
        body.write_text('Build plans:\n\n' + '\n'.join('- ' + p for p in track['plans']) +
                        f"\n\nReview: {state['review_verdict']}. Required local checks passed.\n"
                        f"Code review: {state['code_review_verdict']}; source: {state['code_reviewed_sha']}\n\n"
                        f"Documentation review: {state['documentation_review_verdict']}; source: {state['documentation_reviewed_sha']}\n\n"
                        f"Documentation model: {state['documentation_model']}\n\nIntegrated head: {head}\n\n"
                        'Follow-ups (open until their affected implementation is verified):\n\n' +
                        ('\n'.join('- ' + f['record'] for f in state['findings'].values()) or 'None.') + '\n', encoding='utf-8')
        self.gh('pr', 'edit', str(state['pr']), '--repo', self.config['github_repo'], '--body-file', str(body))
        self.wait_checks(state['pr'], head)
        with self.repo_mutex:
            if self.sync() != base:
                raise RetryDelivery('Target advanced during validation; retry delivery against latest target')
            self.update(state, delivery_stage='merging')
            self.gh('pr', 'merge', str(state['pr']), '--repo', self.config['github_repo'],
                    '--merge', '--match-head-commit', head)
            self.finish_merge(track)

    @repo_locked
    def finish_merge(self, track):
        state = self.state['tracks'][track['id']]
        data = json.loads(self.gh('pr', 'view', str(state['pr']), '--repo', self.config['github_repo'],
                                 '--json', 'state,headRefOid,mergeCommit'))
        require(data['state'] == 'MERGED', 'Merge has not completed')
        require(data['headRefOid'] == state['delivery_head'], 'Merged unexpected PR head')
        self.sync()
        merge = data['mergeCommit']['oid']
        git(self.root, 'merge-base', '--is-ancestor', merge, 'HEAD')
        git(self.root, 'merge-base', '--is-ancestor', state['delivery_head'], merge)
        require(git(self.root, 'rev-parse', f'{merge}^{{tree}}') == state['tested_tree'],
                'Merged content differs from the tested integration tree')
        self.update(state, status='merged', merge_commit=merge)
        self.cleanup(track)

    @repo_locked
    def cleanup(self, track):
        state = self.state['tracks'][track['id']]
        require(state['status'] == 'merged', 'Only merged tracks may be cleaned')
        self.sync()
        path, branch = self.location(track)
        if path.exists():
            self.ownership(track, path)
            self.discard_generated(track)
            require(not git(path, 'status', '--porcelain', '--ignored'), 'Worktree has local files; preserving it')
            git(self.root, 'merge-base', '--is-ancestor', branch, 'HEAD')
            git(self.root, 'worktree', 'remove', str(path))
        if git(self.root, 'branch', '--list', branch):
            git(self.root, 'merge-base', '--is-ancestor', branch, 'HEAD')
            git(self.root, 'branch', '-d', branch)
        remote = git(self.root, 'ls-remote', '--heads', self.config['remote'], f'refs/heads/{branch}')
        if remote:
            require(remote.split()[0] == state['delivery_head'], 'Remote branch advanced; preserving it')
            ref = f'refs/heads/{branch}'
            git(self.root, 'push', self.config['remote'],
                f"--force-with-lease={ref}:{state['delivery_head']}", f':{ref}')
        self.update(state, cleaned=True)

    def conflict(self, a, b):
        return bool({x.casefold() for x in a['resources']} & {x.casefold() for x in b['resources']}) or any(
            overlaps(x, y) for x in a['owned_paths'] for y in b['owned_paths'])

    def audit_followups(self, queue):
        if not queue['eligible'] or not queue['FIX']:
            return
        head = self.sync()
        fingerprint = hashlib.sha256(json.dumps([head, queue], sort_keys=True).encode()).hexdigest()
        if self.state.get('followup_audit', {}).get('fingerprint') == fingerprint:
            return
        token = f'defect-audit-{time.time_ns()}'
        result_file = self.directory / f'{token}.json'
        mapping = {'worktree': str(self.root), 'phase': 'defect-audit', 'sandbox': 'read-only',
                   'schema_file': str(self.schema), 'result_file': str(result_file),
                   'model': self.config.get('code_model', 'worker-command-default')}
        argv = [arg.format_map(mapping) for arg in self.config['worker_command']]
        context = {'phase': 'defect-audit', 'worktree': str(self.root), 'run': self.config['run_id'],
                    'base_sha': head, 'FIX': [item for item in queue['FIX'] if item['audit_ready']], 'INTAKE': queue['INTAKE'],
                   'parked_tracks': queue['parked_tracks']}
        prompt = (
            'Perform the post-PLAN defect audit, read-only, without launching other agents. '
            'Audit the supplied available defect trees; unrelated PLAN work may remain incomplete. '
            'Read each report_file and its attempted correction proof. Inspect integrated code at base_sha '
            'and, for unmerged defects, the preserved source_worktree read-only. State which tree was tested. '
            'Do not execute checks in a parked worktree whose workers_stopped flag is false; mark it unverified. '
            'Do not assume parked changes are present on the target. For each report, summarize '
            'whether it still reproduces, is a duplicate, appears fixed with proof, or is unverified. '
            'Prioritize remaining code defects. Do not edit code, close records, commit, or change '
            'documentation/contracts. Those corrections remain separate INTAKE items for later. '
            'Do not claim a test passed without running it. Return the structured result, placing '
            'the per-FIX assessment and commands/output in summary. This is an audit of the deferred '
            'queue, not a third review or another fix loop.\n' + json.dumps(context, indent=2))
        output = command(argv, self.root, input=prompt,
                         timeout=self.config.get('worker_timeout_seconds', 3600),
                         env={**self.worker_environment({'id': 'defect-audit'}),
                              'ORCH_CONTEXT': json.dumps(context), 'ORCH_RESULT': str(result_file)})
        (self.directory / f'{token}.log').write_text(output, encoding='utf-8')
        require(git(self.root, 'rev-parse', 'HEAD') == head and not git(self.root, 'status', '--porcelain'),
                'Defect auditor changed the base checkout')
        result = json.loads(result_file.read_text(encoding='utf-8'))
        require(result.get('status') == 'complete' and isinstance(result.get('summary'), str) and
                result['summary'].strip(), 'Post-PLAN defect audit incomplete')
        self.state['followup_audit'] = {'head': head, 'fingerprint': fingerprint, 'result': result}
        self.save()

    def reload(self):
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text(encoding='utf-8'))
            require(self.state['config_hash'] == self.fingerprint, 'Schedule changed before lock acquisition')

    def recover(self, action, track_id, *, expected_head=None, workers_stopped=False):
        """Explicit recovery never resets review counts, rewrites Git or deletes work."""
        with run_lock(self.runtime):
            self.reload()
            track = next((t for t in self.config['tracks'] if t['id'] == track_id), None)
            require(track is not None, 'Unknown recovery track')
            state = self.state['tracks'][track_id]
            require(state['status'] in ('blocked', 'running', 'pending'),
                    'Resume uncertain delivery or merged cleanup with the normal run command')
            if state.get('inflight_phase') == 'readiness':
                require(action in ('reconcile', 'abandon') and workers_stopped,
                        'Reconcile readiness after confirming its worker stopped')
                require(git(self.root, 'rev-parse', 'HEAD') == expected_head,
                        'Supply the exact primary checkout HEAD for readiness recovery')
                if action == 'abandon':
                    self.update(state, status='abandoned', released=True, reason='Readiness abandoned; all evidence preserved')
                    return
                phase = state['inflight']
                require(not git(self.root, 'status', '--porcelain'), 'Readiness left changes in the primary checkout')
                try:
                    result = json.loads(Path(phase['result_file']).read_text(encoding='utf-8'))
                    self.validate_phase_result(result, 'readiness')
                except (OSError, ValueError, TypeError, KeyError, Blocked):
                    require(self.sync() == expected_head, 'Target advanced during recovery; inspect its new HEAD')
                    git(self.root, 'merge-base', '--is-ancestor', phase['before'], expected_head)
                    require(state.get('readiness_attempts', {}).get(expected_head, 0) < self.config.get('max_process_attempts', 2),
                            'Readiness process retry budget exhausted')
                    state.setdefault('failed_processes', []).append(dict(phase))
                    state.pop('inflight_phase', None)
                    state.pop('inflight', None)
                    state.pop('worker_stopped', None)
                    self.update(state, status='pending', reason='Readiness infrastructure failure reconciled without losing prior evidence')
                    return
                self.consume_readiness(track)
                self.update(state, status='pending', reason='Completed readiness result reconciled without replay')
                return
            path, _ = self.location(track)
            if path.exists():
                self.ownership(track, path)
                head = git(path, 'rev-parse', 'HEAD')
            else:
                head = None
            if action in ('reconcile', 'abandon'):
                require(workers_stopped, 'Confirm all track workers and resource users have stopped')
                require(head == expected_head, 'Supply the exact current worktree HEAD for recovery')
            if action == 'abandon':
                self.update(state, status='abandoned', released=True, reason='Explicitly abandoned; all work preserved')
                return
            if head is None:
                require(not state.get('base') and not git(self.root, 'branch', '--list', self.location(track)[1]),
                        'Allocated branch is missing its worktree; inspect and reconcile it before recovery')
                require(action == 'retry', 'Use retry for readiness or preallocation failures')
                receipt = state.get('readiness')
                if receipt and (receipt['result']['status'] != 'complete' or receipt['result']['verdict'] != 'approved' or
                                receipt['result']['findings']):
                    require(self.sync() != receipt['base_sha'],
                            'Completed readiness rejection requires a changed revision; preserve its decision')
                self.update(state, status='pending', reason='Retry readiness against the synchronized target')
                return
            if action == 'reconcile' and state.get('inflight_phase'):
                phase = state.get('inflight')
                require(phase is not None, 'Legacy interrupted phase has no result receipt; preserve and abandon it')
                if phase['readonly'] or phase['name'] not in ('build', 'document'):
                    require(head == phase['before'], 'Phase HEAD changed; reconcile Git against the saved receipt first')
                result_file = Path(phase['result_file'])
                try:
                    result = json.loads(result_file.read_text(encoding='utf-8')) if result_file.is_file() else None
                    if result is not None:
                        self.validate_phase_result(result, phase['name'])
                except (ValueError, TypeError, KeyError, Blocked):
                    result = None
                if result is not None:
                    self.record_findings(track, result, self.phase_round(phase['name']), publish=False,
                                          source_head=phase['before'], phase_name=phase['name'])
                if result is not None and result['status'] == 'complete':
                    self.consume_result(track)
                else:
                    require(result is None, 'A valid blocked worker result needs supporting work, not another review')
                    require(head == phase['before'], 'Partial writer changes require recovery; they cannot be replayed')
                    self.audit(track, path)
                    require(state.get('process_attempts', {}).get(phase['name'], 0) < self.config.get('max_process_attempts', 2),
                            'Process retry budget exhausted')
                    state.setdefault('failed_processes', []).append(dict(phase))
                    state.pop('inflight_phase', None)
                    state.pop('inflight', None)
                    state['checkpoint_head'] = head
            require(not state.get('inflight_phase'), 'Reconcile the interrupted phase before retrying')
            require(all(r['verdict'] != 'cannot_review' for r in state['completed_phases'].values()),
                    'Inconclusive review stays parked; do not reset its review count')
            require(git(path, 'rev-parse', 'HEAD') == state.get('checkpoint_head', state['base']),
                    'Track HEAD differs from the last coordinator checkpoint')
            self.audit(track, path)
            for marker in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
                require(not Path(git(path, 'rev-parse', '--path-format=absolute', '--git-path', marker)).exists(),
                        'Finish or abort the interrupted Git operation before retrying')
            state.pop('worker_stopped', None)
            status = (('ready_with_followups' if state['findings'] else 'ready')
                      if state.get('prepared_head') and state.get('review_verdict') else 'pending')
            self.update(state, status=status, reason='Recovered without replaying completed phases')

    def start(self, track):
        state = self.state['tracks'][track['id']]
        path, branch = self.location(track)
        if 'base' in state:
            self.audit(track, path)
            require(git(path, 'rev-parse', 'HEAD') == state.get('checkpoint_head', state['base']),
                    'Recovery checkpoint changed')
        else:
            for _ in range(3):
                with self.repo_mutex:
                    base = self.sync()
                    contracts = self.plan_contracts(track, base)
                self.readiness(track, base, contracts)
                with self.repo_mutex:
                    if self.sync() != base:
                        continue
                    require(not path.exists(), 'Assigned worktree already exists')
                    git(self.root, 'check-ignore', str(path))
                    git(self.root, 'worktree', 'add', '-b', branch, str(path), base)
                    self.update(state, base=base, checkpoint_head=base, plan_contracts=contracts)
                    break
            else:
                raise Blocked('Target kept advancing during readiness; retry against a stable revision')
            for name in track.get('disposable_paths', []):
                require(not (path / name).exists(), f'Disposable path already exists: {name}')
                require(not git(path, '--literal-pathspecs', 'ls-files', '--', name), 'Disposable path contains tracked files')
            self.update(state, disposable_paths=track.get('disposable_paths', []))
        self.update(state, status='running')

    def start_and_build(self, track):
        self.start(track)
        self.build(track)

    def followup_queue(self):
        states = self.state['tracks']
        # A defect and the PLANs waiting on it cannot be prerequisites for examining that defect.
        parked = {key for key, state in states.items() if state['status'] in ('blocked', 'abandoned')
                  and state['findings']}
        while True:
            owners = [t for t in self.config['tracks'] if t['id'] in parked and
                      states[t['id']]['status'] != 'pending' and not states[t['id']].get('cleaned') and
                      not states[t['id']].get('released')]
            waiting = {t['id'] for t in self.config['tracks'] if states[t['id']]['status'] == 'pending'
                       and (any(dep in parked for dep in t['depends_on']) or
                            any(self.conflict(t, owner) for owner in owners))}
            if waiting <= parked:
                break
            parked.update(waiting)
        complete = all(s['status'] == 'merged' or key in parked for key, s in states.items())
        queue = {'eligible': complete, 'reason': 'Other scheduled PLAN work finished' if complete else 'PLAN queue unfinished',
                 'FIX': [], 'INTAKE': [], 'parked_tracks': [
                     {'track': t['id'], 'plans': t['plans'], 'depends_on': t['depends_on'],
                      'worktree': str(self.location(t)[0]), 'status': states[t['id']]['status'],
                      'workers_stopped': not states[t['id']].get('inflight_phase') or
                                         states[t['id']].get('worker_stopped', False),
                      'reason': states[t['id']].get('reason', 'Waiting on a parked dependency')}
                     for t in self.config['tracks'] if t['id'] in parked]}
        all_states = list(states.values())
        for receipt in self.runtime.glob('*/state.json'):
            if receipt != self.state_path:
                all_states.extend(json.loads(receipt.read_text(encoding='utf-8'))['tracks'].values())
        open_reports = {'-'.join(report.stem.split('-')[:2]): report
                        for kind, folder in (('FIX', '.ai/fixes/open'), ('INTAKE', '.ai/plans/intake'))
                        for report in (self.root / folder).glob(f'{kind}-*.md')}
        closed = {'-'.join(report.stem.split('-')[:2])
                  for kind, folder in (('FIX', '.ai/fixes/done'), ('INTAKE', '.ai/plans/done'), ('INTAKE', '.ai/plans/abandoned'))
                  for report in (self.root / folder).rglob(f'{kind}-*.md')}
        for state in all_states:
            for item in state['findings'].values():
                if item['id'] in closed:
                    continue  # Record lifecycle wins over every receipt, including abandoned tracks.
                report = open_reports.get(item['id'])
                if report is not None:
                    item = {**item, 'record': report.relative_to(self.root).as_posix(),
                            'report_file': str(report), 'source_worktree': str(self.root)}
                elif state['status'] == 'merged':
                    continue
                queue['FIX' if item['kind'] == 'code' else 'INTAKE'].append(dict(item))
        for kind, folder in (('FIX', '.ai/fixes/open'), ('INTAKE', '.ai/plans/intake')):
            known = {item['id'] for item in queue[kind]}
            for report in (self.root / folder).glob(f'{kind}-*.md'):
                record_id = '-'.join(report.stem.split('-')[:2])
                if record_id not in known:
                    queue[kind].append({'id': record_id, 'record': report.relative_to(self.root).as_posix(),
                                        'report_file': str(report), 'kind': 'code' if kind == 'FIX' else 'intake',
                                        'title': report.stem})
        busy_trees = {item.get('source_worktree') for state in all_states
                      if state.get('inflight_phase') and not state.get('worker_stopped') and not state.get('released')
                      for item in state['findings'].values()}
        for item in queue['FIX']:
            item['audit_ready'] = item.get('source_worktree') not in busy_trees
        queue.update(eligible=not queue['FIX'] or any(item['audit_ready'] for item in queue['FIX']),
                     reason='Audit each available defect tree independently of unrelated PLANs',
                     waiting_for=[item['id'] for item in queue['FIX'] if not item['audit_ready']])
        return queue

    def run(self):
        with run_lock(self.runtime):
            self.reload()
            self.preflight()
            for track in self.config['tracks']:
                state = self.state['tracks'][track['id']]
                try:
                    if state['status'] == 'merged' and not state.get('cleaned'):
                        self.cleanup(track)
                    elif state['status'] == 'delivering':
                        data = json.loads(self.gh('pr', 'view', str(state['pr']), '--repo', self.config['github_repo'], '--json', 'state'))
                        if data['state'] == 'MERGED':
                            self.finish_merge(track)
                        else:
                            state['status'] = 'ready_with_followups' if state['findings'] else 'ready'
                    elif state['status'] == 'running':
                        state.update(status='blocked', reason='Interrupted worker: reconcile its process, HEAD and result before recovery')
                except Exception as exc:
                    self.update(state, reason=str(exc))
            self.save()
            with ThreadPoolExecutor(max_workers=self.config['max_parallel_tracks']) as pool, ThreadPoolExecutor(max_workers=1) as delivery:
                active, delivering = {}, {}
                while True:
                    busy = {t['id'] for t in [*active.values(), *delivering.values()]}
                    for track in self.config['tracks']:
                        state = self.state['tracks'][track['id']]
                        if track['id'] in busy:
                            continue
                        if state['status'] in ('ready', 'ready_with_followups'):
                            delivering[delivery.submit(self.deliver, track)] = track
                        if state['status'] != 'pending' or len(active) >= self.config['max_parallel_tracks']:
                            continue
                        if not all(self.state['tracks'][dep]['status'] == 'merged' for dep in track['depends_on']):
                            continue
                        others = [t for t in self.config['tracks'] if t['id'] != track['id'] and
                                  self.state['tracks'][t['id']]['status'] != 'pending' and
                                  not self.state['tracks'][t['id']].get('cleaned') and
                                  not self.state['tracks'][t['id']].get('released')]
                        if any(self.conflict(track, other) for other in others):
                            continue
                        try:
                            self.update(state, status='running')
                            active[pool.submit(self.start_and_build, track)] = track
                        except Exception as exc:
                            self.update(state, status='blocked', reason=str(exc))
                    futures = {*active, *delivering}
                    if not futures:
                        break
                    finished, _ = wait(futures, return_when=FIRST_COMPLETED)
                    for future in finished:
                        is_delivery = future in delivering
                        track = (delivering if is_delivery else active).pop(future)
                        state = self.state['tracks'][track['id']]
                        try:
                            future.result()
                        except Exception as exc:
                            uncertain_merge = is_delivery and state.get('delivery_stage') == 'merging'
                            status = ('merged' if state['status'] == 'merged' else 'delivering'
                                      if uncertain_merge or isinstance(exc, RetryDelivery) else 'blocked')
                            self.update(state, status=status, reason=str(exc))
            queue = self.followup_queue()
            atomic_json(self.directory / 'followups.json', queue)
            self.audit_followups(queue)
            self.save()
            return all(s['status'] == 'merged' and s.get('cleaned') for s in self.state['tracks'].values())


def read_status(config):
    root = Path(config['repository']).resolve()
    common = Path(git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir'))
    receipt = common / 'orchestration' / config['run_id'] / 'state.json'
    if not receipt.is_file():
        return {'run': config['run_id'], 'mode': 'runtime', 'status': 'not_started', 'next_action': 'Validate and run the approved schedule'}
    state = json.loads(receipt.read_text(encoding='utf-8'))
    fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    require(state['config_hash'] == fingerprint, 'Status requires the original execution snapshot')
    tracks = []
    for track in config['tracks']:
        current = state['tracks'][track['id']]
        path = root / '.worktrees' / f"{config['run_id']}-{track['id']}"
        require(path.resolve() == path, 'Worktree path was redirected')
        head = git(path, 'rev-parse', 'HEAD') if path.exists() else None
        dirty = git(path, 'status', '--porcelain') if path.exists() else ''
        if current['status'] == 'abandoned':
            action = 'Preserved and incomplete; delivery still requires a reviewed PR, merge, sync and cleanup'
        elif current.get('inflight_phase'):
            recovery_head = git(root, 'rev-parse', 'HEAD') if current['inflight_phase'] == 'readiness' else head
            action = f"Inspect worker processes and Git, then --reconcile {track['id']} --expected-head {recovery_head} --workers-stopped"
        elif current['status'] == 'blocked':
            content_failure = any(r['status'] != 'complete' or r['verdict'] == 'cannot_review' or
                                  (name in ('build', 'review-2') and not r['implementation_complete']) or
                                  (name == 'docs-review-2' and not r['documentation_complete']) or
                                  (name in ('review-2', 'docs-review-2') and any(f['impact'] in
                                   ('missing_code', 'missing_functionality', 'missing_spec_coverage') for f in r['findings']))
                                  for name, r in current['completed_phases'].items())
            action = ('Preserve and inspect Git drift before recovery' if dirty or
                      (head is not None and head != current.get('checkpoint_head')) else
                      'Resolve the recorded content/decision blocker with supporting work' if content_failure else
                      f"Resolve the recorded blocker, then --retry {track['id']} at the saved checkpoint")
        elif current['status'] == 'merged' and current.get('cleaned'):
            action = 'Complete: PR merged, target synced, worktree and branch cleaned'
        else:
            action = 'Use the original schedule to continue; inspect process liveness before restarting a running scheduler'
        tracks.append({'track': track['id'], 'status': current['status'], 'phase': current.get('inflight_phase'),
                       'pipeline': current.get('pipeline'), 'pr': current.get('pr'), 'worktree': str(path),
                       'observed_head': head, 'checkpoint_head': current.get('checkpoint_head'), 'dirty': dirty,
                       'completed_reviews': [name for name in REVIEW_PHASES if name in current['completed_phases']],
                       'process_attempts': current.get('process_attempts', {}), 'reason': current.get('reason'),
                       'next_action': action})
    return {'run': config['run_id'], 'mode': 'runtime', 'receipt': str(receipt), 'tracks': tracks}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('schedule', type=Path)
    parser.add_argument('--validate', action='store_true', help='Validate JSON without Git/network/writes')
    parser.add_argument('--status', action='store_true', help='Read runtime receipts and actual Git state without writes')
    recovery = parser.add_mutually_exclusive_group()
    recovery.add_argument('--retry', metavar='TRACK', help='Retry a clean blocked track at its saved checkpoint')
    recovery.add_argument('--reconcile', metavar='TRACK', help='Consume an interrupted result after checking its worker and HEAD')
    recovery.add_argument('--abandon', metavar='TRACK', help='Release reservations while preserving all work')
    parser.add_argument('--expected-head', help='Exact worktree HEAD inspected before reconciliation or abandonment')
    parser.add_argument('--workers-stopped', action='store_true', help='Attest that all track processes and resource users stopped')
    args = parser.parse_args()
    try:
        config = validate(json.loads(args.schedule.read_text(encoding='utf-8')))
        if args.validate:
            print('Schedule valid')
            return 0
        if args.status:
            print(json.dumps(read_status(config), indent=2))
            return 0
        runner = Runner(config)
        action = next((name for name in ('retry', 'reconcile', 'abandon') if getattr(args, name)), None)
        if action:
            runner.recover(action, getattr(args, action), expected_head=args.expected_head, workers_stopped=args.workers_stopped)
            print(json.dumps(runner.state, indent=2))
            return 0
        complete = runner.run()
        print(json.dumps(runner.state, indent=2))
        print(f'Follow-up queue: {runner.directory / "followups.json"}')
        return 0 if complete else 1
    except (Blocked, KeyError, TypeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'Blocked: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
