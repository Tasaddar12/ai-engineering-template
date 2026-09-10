#!/usr/bin/env python3
"""Run an approved track schedule with isolated workers and serialized delivery.

Python 3.11+, Git and GitHub CLI. See README.md for the execution contract.
The scheduler is an accident guard, not a sandbox for untrusted programs.
"""

from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from contextlib import contextmanager
from datetime import date
import hashlib
from functools import wraps
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from urllib.parse import quote


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


def validate(config):
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
    for argv in [config['worker_command'], *config['required_commands']]:
        require(isinstance(argv, list) and argv and all(isinstance(x, str) and x for x in argv),
                'Commands must be nonempty argv arrays')
    require(config.get('residual_findings', 'merge') in ('merge', 'park'), 'Invalid residual policy')
    tracks = config['tracks']
    require(tracks and len({t['id'].casefold() for t in tracks}) == len(tracks), 'Duplicate/empty tracks')
    plans, reservations = set(), {'FIX': [], 'INTAKE': []}
    by_id = {t['id']: t for t in tracks}
    for track in tracks:
        require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', track['id']), 'Invalid track id')
        require(track['owned_paths'] and track['plans'], 'Declare owned paths and plans for every track')
        for path in track['owned_paths'] + track['plans'] + track['code_paths']:
            relative_path(path)
        for path in track['code_paths']:
            require(any((not path.endswith('/') or s.endswith('/')) and covers(s, path.rstrip('/'))
                        for s in track['owned_paths']), 'Code paths must be owned')
        for plan in track['plans']:
            require(plan.casefold() not in plans, f'Plan scheduled twice: {plan}')
            require(any(covers(s, plan) for s in track['owned_paths']), f'Plan not owned: {plan}')
            plans.add(plan.casefold())
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
            require(type(start) is int and type(end) is int and 0 < start <= end, 'Invalid ID range')
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
RESULT_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'status': {'type': 'string', 'enum': ['complete', 'blocked']},
        'verdict': {'type': 'string', 'enum': ['approved', 'changes_requested', 'cannot_review', 'not_applicable']},
        'summary': {'type': 'string'},
        'findings': {'type': 'array', 'items': FINDING}},
    'required': ['status', 'verdict', 'summary', 'findings']}


class Runner:
    def __init__(self, config):
        self.config = validate(config)
        self.root = Path(config['repository']).resolve()
        require(Path(git(self.root, 'rev-parse', '--show-toplevel')).resolve() == self.root,
                'repository must be the exact base checkout root')
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

    def audit(self, track, path):
        self.ownership(track, path)
        state = self.state['tracks'][track['id']]
        # Imported target commits are owned by the target, not by this track.
        baseline = state.get('integration_base', state['base'])
        paths = git(path, 'diff', '--name-only', '--no-renames', '-z', baseline, 'HEAD').split('\0')
        records = {f['record'] for f in state['findings'].values()}
        records.update(state.get('plan_moves', {}).values())
        for changed in filter(None, paths):
            require(not changed.casefold().startswith(('.ai/state/state.md', '.ai/state/journal/', '.ai/state/orchestration/')),
                    f'Track touched shared coordinator state: {changed}')
            require(changed in records or any(covers(s, changed) for s in track['owned_paths']),
                    f'Change outside declared ownership: {changed}')
        require(not git(path, 'status', '--porcelain'), 'Worker left uncommitted/untracked changes')

    def phase(self, track, name, *, readonly=False, extra=''):
        state = self.state['tracks'][track['id']]
        if name in state['completed_phases']:
            result = state['completed_phases'][name]
            require(result['status'] == 'complete', result['summary'])
            return result
        path, _ = self.location(track)
        self.audit(track, path)
        before = git(path, 'rev-parse', 'HEAD')
        token = f"{track['id']}-{name}-{time.time_ns()}"
        result_file = self.directory / f'{token}.json'
        mapping = {'worktree': str(path), 'result_file': str(result_file),
                   'schema_file': str(self.schema), 'phase': name,
                   'sandbox': 'read-only' if readonly else 'workspace-write'}
        argv = [arg.format_map(mapping) for arg in self.config['worker_command']]
        context = {
            'run': self.config['run_id'], 'track': track['id'], 'phase': name,
            'worktree': str(path), 'branch': self.location(track)[1], 'base_sha': state['base'],
            'plans': track['plans'], 'owned_paths': track['owned_paths'], 'code_paths': track['code_paths'],
            'resources': track['resources'], 'required_commands': self.config['required_commands']}
        prompt = (
            'Execute only this assigned phase. Read AGENTS.md and .ai/RULES.md. '
            'The coordinator owns commits, publication, shared state and FIX/INTAKE allocation. '
            'Do not commit or stage files; the coordinator audits and commits your edits after this phase. '
            'Never launch other agents, change branches, merge, rebase, push or edit sibling worktrees. '
            'Do not ask for approval. Return blocked with a reason if execution is impossible. '
            'Do not modify documentation/contracts to repair incidental review findings; return those '
            'as documentation/contract findings for INTAKE. Confirmed code defects are code findings '
            'for FIX, at every severity and regardless of scope. Use a stable key for each root cause. '
            'Record concrete evidence and location. Questions are question findings. '
            'Workers do not create FIX or INTAKE files. '
            + ('This is a cold, read-only review. Follow .ai/agents/track-reviewer.md. '
               'Do not read previous phase output, research, review logs or FIX/INTAKE reports. '
               'Review the plans, acceptance, contracts and actual diff from base_sha. Exclude '
               '.ai/fixes/ and .ai/plans/intake/ from the diff; the coordinator audits those records. '
               'Use approved only with no findings; changes_requested requires findings. '
               'Use cannot_review if evidence is insufficient. Do not make commits or edits. '
               if readonly else
               'Follow the applicable track role with coordinator-owned commits. '
               'Build phase: research, implement the plans in order, then document all original '
               'PLAN promises using track-researcher, track-implementor and track-documentor guidance. '
               'Keep research in the response, not shared orchestration files. '
               'Keep plans in their existing paths; report completion to the coordinator. '
               'Fix phase: follow track-fixer, correct only supplied code findings inside ownership, '
               'run a regression check and report before/after proof. Never repair docs/contracts '
               'in this phase. Return any unresolved or out-of-scope code defects as findings. ')
            + '\nAssignment:\n' + json.dumps(context, indent=2) + '\n' + extra
            + '\nReturn JSON matching the supplied schema in the configured result file.')
        attempts = state.setdefault('phase_attempts', {})
        require(name == 'build' or not attempts.get(name), 'Cannot repeat a fix or review attempt')
        attempts[name] = attempts.get(name, 0) + 1
        self.update(state, inflight_phase=name, worker_stopped=False,
                    inflight={'name': name, 'before': before, 'result_file': str(result_file), 'readonly': readonly})
        try:
            output = command(argv, path, input=prompt, timeout=self.config.get('worker_timeout_seconds', 3600),
                             env={**self.worker_environment(track), 'ORCH_CONTEXT': json.dumps(context),
                                  'ORCH_RESULT': str(result_file)})
        except Exception:
            # command() waits for termination before returning an error. A process crash
            # of this scheduler leaves this flag absent and requires explicit reconciliation.
            self.update(state, worker_stopped=True)
            if result_file.is_file():
                result = json.loads(result_file.read_text(encoding='utf-8'))
                self.validate_result(result)
                self.record_findings(track, result, self.phase_round(name), publish=False, source_head=before)
            raise
        (self.directory / f'{token}.log').write_text(output, encoding='utf-8')
        self.update(state, worker_stopped=True)
        return self.consume_result(track)

    @staticmethod
    def phase_round(name):
        return 2 if name == 'review-2' else 0 if name == 'build' else 1

    @staticmethod
    def validate_result(result):
        require(isinstance(result, dict) and result.get('status') in ('complete', 'blocked') and
                isinstance(result.get('findings'), list) and isinstance(result.get('summary'), str) and
                result.get('verdict') in RESULT_SCHEMA['properties']['verdict']['enum'], 'Malformed worker result')
        for finding in result['findings']:
            require(isinstance(finding, dict) and set(FINDING['required']) <= finding.keys() and
                    all(isinstance(finding[k], str) and finding[k].strip() for k in FINDING['required']),
                    'Finding needs a key, kind, severity, title, path and evidence')
            require(finding['kind'] in ('code', 'documentation', 'contract', 'question'), 'Invalid finding kind')
            require(finding['severity'] in ('critical', 'major', 'minor', 'cosmetic'), 'Invalid severity')

    def consume_result(self, track):
        state = self.state['tracks'][track['id']]
        path, _ = self.location(track)
        phase = state['inflight']
        name, before, readonly = phase['name'], phase['before'], phase['readonly']
        result_file = Path(phase['result_file'])
        require(result_file.is_file(), 'Worker did not produce its result')
        result = json.loads(result_file.read_text(encoding='utf-8'))
        self.validate_result(result)
        # Queue confirmed findings even if the worker is blocked or its edits fail audit.
        self.record_findings(track, result, self.phase_round(name), publish=False, source_head=before)
        require(result['status'] == 'complete', result['summary'])
        require(git(path, 'rev-parse', 'HEAD') == before, 'Worker changed HEAD; coordinator owns commits')
        if readonly:
            require(result.get('verdict') in ('approved', 'changes_requested', 'cannot_review'), 'Invalid review verdict')
            if result['verdict'] != 'cannot_review':
                require((result['verdict'] == 'approved') == (len(result['findings']) == 0), 'Inconsistent review verdict')
        else:
            self.commit_worker_changes(track, name)
        self.audit(track, path)
        with self.mutex:
            state.setdefault('phase_heads', {})[name] = before
            state['completed_phases'][name] = result
            state.pop('inflight_phase', None)
            state.pop('inflight', None)
            state.pop('worker_stopped', None)
            state['checkpoint_head'] = git(path, 'rev-parse', 'HEAD')
            self.save()
        return result

    def commit_worker_changes(self, track, phase):
        path, _ = self.location(track)
        self.ownership(track, path)
        require(not git(path, 'diff', '--cached', '--name-only'), 'Worker staged files; coordinator owns the index')
        changed = set(filter(None, git(path, 'diff', '--name-only', '--no-renames', '-z', 'HEAD').split('\0')))
        changed.update(filter(None, git(path, 'ls-files', '--others', '--exclude-standard', '-z').split('\0')))
        scopes = track['code_paths'] if phase == 'fix' else track['owned_paths']
        for name in changed:
            require(not name.casefold().startswith(('.ai/state/', '.ai/fixes/', '.ai/plans/intake/')) and
                    any(covers(s, name) for s in scopes), f'Worker change outside {phase} ownership: {name}')
            if phase == 'fix':
                require(not name.casefold().endswith(('.md', '.rst', '.adoc')) and
                        not name.casefold().startswith(('.ai/specs/', '.ai/decisions/')), f'Fix cannot change docs/contracts: {name}')
        if changed:
            git(path, '--literal-pathspecs', 'add', '--', *sorted(changed))
            git(path, 'commit', '-m', f"{phase.capitalize()} planned track {track['id']}")

    @state_locked
    def record_findings(self, track, result, round_number, *, publish=True, source_head=None):
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
                number = next((n for n in range(start, end + 1) if n not in used), None)
                require(number is not None, f'{kind} ID block exhausted')
                record_id = f'{kind}-{number:03d}'
                require(not list((path / '.ai').rglob(f'{record_id}-*.md')), f'ID already exists: {record_id}')
                folder = '.ai/fixes/open' if kind == 'FIX' else '.ai/plans/intake'
                item = {'id': record_id, 'record': f'{folder}/{record_id}-review.md',
                        'history': [], 'found': str(date.today())}
                state['findings'][key] = item
            evidence = {**finding, 'round': round_number, 'reviewed_sha': source_head}
            # Re-entering a completed phase is not a new review observation.
            fields = (*FINDING['required'], 'round')
            if not any(all(old[k] == evidence[k] for k in fields) for old in item['history']):
                item['history'].append(evidence)
                item.update(finding, round=round_number, reviewed_sha=source_head)
        self.write_reports(track, publish=publish)

    def render_finding(self, track, item):
        kind = 'FIX' if item['kind'] == 'code' else 'INTAKE'
        front = {'tier': 'plan', 'authority': 'agent', 'id': item['id'], 'title': item['title'],
                 'found': item.get('found', str(date.today())), 'found_by': 'orchestration review',
                 'found_while': track['plans'], 'severity': item['severity'],
                 'deferred_until': 'all-other-plans-complete', 'run': self.config['run_id'], 'links': []}
        front['violates' if kind == 'FIX' else 'kind'] = 'none' if kind == 'FIX' else item['kind']
        text = '---\n' + ''.join(f'{k}: {json.dumps(v)}\n' for k, v in front.items()) + '---\n\n'
        text += f"# {item['id']}: {item['title']}\n\n"
        if kind == 'FIX':
            text += f"## Symptom\n\n{item['detail']}\n\n## Root cause\n\nLocation: {item['path']}. Confirm the mechanism before fixing.\n\n## The change\n\nDeferred for the post-PLAN defect pass.\n\n## Proof\n\nNot yet verified; keep open until a regression check proves the correction.\n\n## Contract\n\nCode only. Any documentation or contract correction requires a separate INTAKE.\n"
        else:
            text += f"## What's wrong\n\n{item['detail']}\n\n## Where\n\n{item['path']}\n\n## Why it wasn't fixed then\n\nSeparate {item['kind']} work after the PLAN queue.\n\n## What it costs to leave\n\nSeverity: {item['severity']}.\n"
        text += '\n## Review evidence\n'
        for evidence in item.get('history', [item]):
            text += (f"\nRound {evidence['round']}, source {evidence['reviewed_sha']}, "
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
        result = self.phase(track, 'build')
        self.record_findings(track, result, 0)
        self.pull_request(track)
        first = self.phase(track, 'review-1', readonly=True)
        self.record_findings(track, first, 1)
        require(first['verdict'] != 'cannot_review', 'Reviewer cannot review')
        code = [f for f in first['findings'] if f['kind'] == 'code']
        if code:
            fixed = self.phase(track, 'fix', extra='Code findings to attempt once:\n' + json.dumps(code))
            self.record_findings(track, fixed, 1)
            self.record_attempt(track, fixed)
            last = self.phase(track, 'review-2', readonly=True)
            self.record_findings(track, last, 2)
            require(last['verdict'] != 'cannot_review', 'Reviewer cannot review')
        else:
            last = first
        # Reports remain open until the later defect pass verifies their proof.
        # This avoids silently closing a bug merely because a cold review omitted it.
        self.update(state, reviewed_sha=state['phase_heads']['review-2' if code else 'review-1'])
        self.finalize_plans(track)
        self.update(state, prepared_head=git(path, 'rev-parse', 'HEAD'))
        generated = {f['record'] for f in state['findings'].values()}
        generated.update(state.get('plan_moves', {}))
        generated.update(state.get('plan_moves', {}).values())
        require(set(filter(None, git(path, 'diff', '--name-only', '--no-renames', '-z',
                                    state['reviewed_sha'], 'HEAD').split('\0'))) <= generated,
                'Source changed after the final review')
        self.update(state, review_verdict=last['verdict'], residual_findings=last['findings'])
        self.checks(path, track)
        self.audit(track, path)
        self.pull_request(track)
        require(not last['findings'] or self.config.get('residual_findings', 'merge') == 'merge',
                'Residual findings parked until the post-PLAN pass')
        self.update(state, status='ready_with_followups' if state['findings'] else 'ready')

    @state_locked
    def record_attempt(self, track, result):
        """Store the fixer's actual proof without treating its claim as closure."""
        state = self.state['tracks'][track['id']]
        if state.get('attempt_recorded'):
            return
        path, _ = self.location(track)
        attempted = {f['key'] for f in state['completed_phases']['review-1']['findings']
                     if f['kind'] == 'code' and any(covers(s, f['path']) for s in track['code_paths'])}
        for key in attempted:
            state['findings'][key].setdefault('attempts', []).append(result['summary'])
        self.write_reports(track, publish=True)
        state['attempt_recorded'] = True
        self.save()

    @state_locked
    def finalize_plans(self, track):
        """Mechanical lifecycle moves become visible on the target only at merge."""
        state = self.state['tracks'][track['id']]
        if 'plan_moves' in state:
            return
        path, _ = self.location(track)
        moves = {}
        today = date.today()
        period = f'{today.year}-Q{(today.month - 1) // 3 + 1}'
        for source in track['plans']:
            if not re.match(r'^\.ai/plans/(backlog|active|review)/PLAN-', source):
                continue
            target = f'.ai/plans/done/{period}/{PurePosixPath(source).name}'
            require(not (path / target).exists(), f'Completed PLAN already exists: {target}')
            (path / target).parent.mkdir(parents=True, exist_ok=True)
            git(path, 'mv', '--', source, target)
            moves[source] = target
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
        require(state.get('review_verdict') in ('approved', 'changes_requested'), 'No conclusive review for delivery')
        require(not state.get('residual_findings') or self.config.get('residual_findings', 'merge') == 'merge',
                'Residual findings parked until the post-PLAN pass')
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
        self.checks(path, track)
        head = git(path, 'rev-parse', 'HEAD')
        self.update(state, status='delivering', delivery_head=head, tested_base=base,
                    tested_tree=git(path, 'rev-parse', 'HEAD^{tree}'))
        git(path, 'push', self.config['remote'], f'HEAD:refs/heads/{branch}')
        body = self.directory / f"{track['id']}-pr.md"
        body.write_text('Build plans:\n\n' + '\n'.join('- ' + p for p in track['plans']) +
                        f"\n\nReview: {state['review_verdict']}. Required local checks passed.\n"
                        f"Reviewed source: {state['reviewed_sha']}\n\nIntegrated head: {head}\n\n"
                        'Follow-ups (open until verified after all other PLANs):\n\n' +
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
        """Look through deferred bugs once the project's other PLAN work is done."""
        if not queue['eligible'] or not queue['FIX']:
            return
        head = self.sync()
        fingerprint = hashlib.sha256(json.dumps([head, queue], sort_keys=True).encode()).hexdigest()
        if self.state.get('followup_audit', {}).get('fingerprint') == fingerprint:
            return
        token = f'defect-audit-{time.time_ns()}'
        result_file = self.directory / f'{token}.json'
        mapping = {'worktree': str(self.root), 'phase': 'defect-audit', 'sandbox': 'read-only',
                   'schema_file': str(self.schema), 'result_file': str(result_file)}
        argv = [arg.format_map(mapping) for arg in self.config['worker_command']]
        context = {'phase': 'defect-audit', 'worktree': str(self.root), 'run': self.config['run_id'],
                   'base_sha': head, 'FIX': queue['FIX'], 'INTAKE': queue['INTAKE'],
                   'parked_tracks': queue['parked_tracks']}
        prompt = (
            'Perform the post-PLAN defect audit, read-only, without launching other agents. '
            'Other runnable PLAN work is finished; listed parked tracks and their dependencies remain incomplete. '
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
            require(head is not None, 'No worktree to retry; abandon this allocation and use a new run')
            if action == 'reconcile' and state.get('inflight_phase'):
                phase = state.get('inflight')
                require(phase is not None, 'Legacy interrupted phase has no result receipt; preserve and abandon it')
                require(head == phase['before'], 'Phase HEAD changed; reconcile Git against the saved receipt first')
                result_file = Path(phase['result_file'])
                result = json.loads(result_file.read_text(encoding='utf-8')) if result_file.is_file() else None
                if result is not None:
                    self.validate_result(result)
                    self.record_findings(track, result, self.phase_round(phase['name']), publish=False,
                                         source_head=phase['before'])
                if result is not None and result['status'] == 'complete':
                    self.consume_result(track)
                else:
                    require(phase['name'] == 'build', 'Failed fix/review attempt stays parked for the deferred pass')
                    self.audit(track, path)
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

    @repo_locked
    def start(self, track):
        state = self.state['tracks'][track['id']]
        path, branch = self.location(track)
        if 'base' in state:
            self.audit(track, path)
            require(git(path, 'rev-parse', 'HEAD') == state.get('checkpoint_head', state['base']),
                    'Recovery checkpoint changed')
        else:
            base = self.sync()
            require(not path.exists(), 'Assigned worktree already exists')
            git(self.root, 'check-ignore', str(path))
            git(self.root, 'worktree', 'add', '-b', branch, str(path), base)
            # Save ownership even if artifact registration fails after worktree creation.
            self.update(state, base=base, checkpoint_head=base)
            for name in track.get('disposable_paths', []):
                require(not (path / name).exists(), f'Disposable path already exists: {name}')
                require(not git(path, '--literal-pathspecs', 'ls-files', '--', name), 'Disposable path contains tracked files')
            self.update(state, disposable_paths=track.get('disposable_paths', []))
        self.update(state, status='running')

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
                  for kind, folder in (('FIX', '.ai/fixes/done'), ('INTAKE', '.ai/plans/abandoned'))
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
        excluded = {p for t in self.config['tracks'] if t['id'] in parked for p in t['plans']}
        other_plans = [p.relative_to(self.root).as_posix() for stage in ('backlog', 'active', 'review', 'blocked')
                       for p in (self.root / '.ai/plans' / stage).glob('PLAN-*.md')
                       if p.relative_to(self.root).as_posix() not in excluded]
        if other_plans:
            queue.update(eligible=False, reason='Other project PLANs remain', waiting_for=other_plans)
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
                            self.start(track)
                            active[pool.submit(self.build, track)] = track
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('schedule', type=Path)
    parser.add_argument('--validate', action='store_true', help='Validate JSON without Git/network/writes')
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
