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
import signal
import subprocess
import sys
import threading
import time
from urllib.parse import quote


class Blocked(RuntimeError):
    """Preserve this track for recovery; independent tracks may continue."""


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
        fingerprint = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
        self.fingerprint = fingerprint
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text(encoding='utf-8'))
            require(self.state['config_hash'] == fingerprint, 'Schedule changed; use a new run id')
        else:
            self.state = {'config_hash': fingerprint, 'tracks': {
                t['id']: {'status': 'pending', 'completed_phases': {}, 'findings': {}}
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

    def sync(self):
        cfg = self.config
        require(git(self.root, 'branch', '--show-current') == cfg['base_branch'], 'Base branch changed')
        require(not git(self.root, 'status', '--porcelain'), 'Base checkout is dirty')
        git(self.root, 'fetch', cfg['remote'], cfg['base_branch'])
        ref = f"refs/remotes/{cfg['remote']}/{cfg['base_branch']}"
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
            require(all(s['status'] == 'merged' and s.get('cleaned') for s in previous['tracks'].values()),
                    f'An earlier run still owns worktrees/resources: {receipt.parent.name}')
        # Strict checks make a target advance reject the merge on the server.
        protection = self.api(f"branches/{quote(cfg['base_branch'], safe='')}/protection")
        checks = protection.get('required_status_checks') or {}
        contexts = set(checks.get('contexts', [])) | {c['context'] for c in checks.get('checks', [])}
        require(checks.get('strict') is True and set(cfg['required_status_checks']) <= contexts and
                protection.get('enforce_admins', {}).get('enabled') is True,
                'Autonomous merge requires strict named checks enforced for administrators too')

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
        paths = git(path, 'diff', '--name-only', '--no-renames', '-z', state['base'], 'HEAD').split('\0')
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
            return state['completed_phases'][name]
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
        self.update(state, inflight_phase=name)
        output = command(argv, path, input=prompt, timeout=self.config.get('worker_timeout_seconds', 3600),
                         env={**os.environ, **track.get('environment', {}), 'ORCH_CONTEXT': json.dumps(context),
                              'ORCH_RESULT': str(result_file)})
        (self.directory / f'{token}.log').write_text(output, encoding='utf-8')
        require(result_file.is_file(), 'Worker did not produce its result')
        result = json.loads(result_file.read_text(encoding='utf-8'))
        require(result.get('status') == 'complete', result.get('summary', 'Worker blocked'))
        require(isinstance(result.get('findings'), list) and isinstance(result.get('summary'), str), 'Malformed worker result')
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
    def record_findings(self, track, result, round_number):
        path, _ = self.location(track)
        state = self.state['tracks'][track['id']]
        additions = []
        for finding in result['findings']:
            require(set(FINDING['required']) <= finding.keys() and
                    all(isinstance(finding[k], str) and finding[k].strip() for k in FINDING['required']),
                    'Finding needs a key, kind, severity, title, path and evidence')
            require(finding['kind'] in ('code', 'documentation', 'contract', 'question'), 'Invalid finding kind')
            require(finding['severity'] in ('critical', 'major', 'minor', 'cosmetic'), 'Invalid severity')
            key = finding['key']
            if key in state['findings']:
                require(state['findings'][key]['kind'] == finding['kind'], 'Finding changed classification')
                continue
            kind = 'FIX' if finding['kind'] == 'code' else 'INTAKE'
            start, end = track['ids'][kind]
            used = {int(f['id'].split('-')[1]) for f in state['findings'].values() if f['id'].startswith(kind + '-')}
            number = next((n for n in range(start, end + 1) if n not in used), None)
            require(number is not None, f'{kind} ID block exhausted')
            record_id = f'{kind}-{number:03d}'
            require(not list((path / '.ai').rglob(f'{record_id}-*.md')), f'ID already exists: {record_id}')
            folder = '.ai/fixes/open' if kind == 'FIX' else '.ai/plans/intake'
            record = f'{folder}/{record_id}-review.md'
            item = {**finding, 'id': record_id, 'record': record, 'round': round_number,
                    'reviewed_sha': git(path, 'rev-parse', 'HEAD')}
            state['findings'][key] = item
            # JSON quoting is also valid YAML scalar quoting.
            front = {'tier': 'plan', 'authority': 'agent', 'id': record_id, 'title': finding['title'],
                     'found': str(date.today()), 'found_by': 'orchestration review',
                     'found_while': track['plans'], 'severity': finding['severity'],
                     'deferred_until': 'all-other-plans-complete', 'run': self.config['run_id'],
                     'links': []}
            front['violates' if kind == 'FIX' else 'kind'] = 'none' if kind == 'FIX' else finding['kind']
            text = '---\n' + ''.join(f'{k}: {json.dumps(v)}\n' for k, v in front.items()) + '---\n\n'
            text += f"# {record_id}: {finding['title']}\n\n"
            if kind == 'FIX':
                text += f"## Symptom\n\n{finding['detail']}\n\n## Root cause\n\nLocation: {finding['path']}. Confirm the mechanism before fixing.\n\n## The change\n\nDeferred for the post-PLAN defect pass.\n\n## Proof\n\nNot yet verified; keep open until a regression check proves the correction.\n\n## Contract\n\nCode only. Any documentation or contract correction requires a separate INTAKE.\n"
            else:
                text += f"## What's wrong\n\n{finding['detail']}\n\n## Where\n\n{finding['path']}\n\n## Why it wasn't fixed then\n\nSeparate {finding['kind']} work after the PLAN queue.\n\n## What it costs to leave\n\nSeverity: {finding['severity']}.\n"
            text += f"\n## Review evidence\n\nRun {self.config['run_id']}, track {track['id']}, round {round_number}, source {item['reviewed_sha']}.\n"
            target = path / record
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding='utf-8')
            additions.append(record)
        if additions:
            git(path, 'add', '--', *additions)
            git(path, 'commit', '-m', f"Record deferred review findings for {track['id']}")
        self.save()

    def checks(self, path, track):
        head = git(path, 'rev-parse', 'HEAD')
        for argv in self.config['required_commands']:
            command(argv, path, timeout=self.config.get('check_timeout_seconds', 900),
                    env={**os.environ, **track.get('environment', {})})
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
        records = [f['record'] for f in state['findings'].values() if f['kind'] == 'code']
        for record in records:
            target = path / record
            with target.open('a', encoding='utf-8') as handle:
                handle.write('\n## Attempted correction\n\n' + result['summary'] +
                             '\n\nCoordinator has not closed this report; verify the proof in the post-PLAN pass.\n')
        if records:
            git(path, 'add', '--', *records)
            git(path, 'commit', '-m', f"Record attempted code corrections for {track['id']}")
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
        self.save()

    def wait_checks(self, pr, head):
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
                names.add(name)
                status = check.get('status', check.get('state'))
                result = check.get('conclusion', check.get('state'))
                if status in ('COMPLETED', 'SUCCESS', 'FAILURE', 'ERROR'):
                    require(result == 'SUCCESS', f'GitHub check did not pass: {name}: {result}')
                else:
                    pending = True
            if set(self.config['required_status_checks']) <= names and not pending:
                return
            require(time.monotonic() < deadline, 'Required GitHub checks missing or timed out')
            time.sleep(2)

    def deliver(self, track):
        """Only called by the scheduler thread, never by concurrent build workers."""
        state = self.state['tracks'][track['id']]
        path, branch = self.location(track)
        self.ownership(track, path)
        require(not git(path, 'status', '--porcelain'), 'Dirty track cannot be delivered')
        if state.get('delivery_head'):
            require(git(path, 'rev-parse', 'HEAD') == state['delivery_head'], 'Delivery HEAD changed')
        else:
            self.audit(track, path)
            require(git(path, 'rev-parse', 'HEAD') == state['prepared_head'], 'Source changed after review')
        base = self.sync()
        # Integration happens in the completed track. No worker is still writing it.
        git(path, 'merge', '--no-edit', base)
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
        require(self.sync() == base, 'Target advanced during validation; retry delivery against latest target')
        self.gh('pr', 'merge', str(state['pr']), '--repo', self.config['github_repo'],
                '--merge', '--match-head-commit', head)
        self.finish_merge(track)

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

    def cleanup(self, track):
        state = self.state['tracks'][track['id']]
        require(state['status'] == 'merged', 'Only merged tracks may be cleaned')
        self.sync()
        path, branch = self.location(track)
        if path.exists():
            self.ownership(track, path)
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
        if not queue['eligible'] or not queue['FIX'] or self.state.get('followup_audit'):
            return
        head = self.sync()
        token = f'defect-audit-{time.time_ns()}'
        result_file = self.directory / f'{token}.json'
        mapping = {'worktree': str(self.root), 'phase': 'defect-audit', 'sandbox': 'read-only',
                   'schema_file': str(self.schema), 'result_file': str(result_file)}
        argv = [arg.format_map(mapping) for arg in self.config['worker_command']]
        context = {'phase': 'defect-audit', 'worktree': str(self.root), 'run': self.config['run_id'],
                   'base_sha': head, 'FIX': queue['FIX'], 'INTAKE': queue['INTAKE']}
        prompt = (
            'Perform the post-PLAN defect audit, read-only, without launching other agents. '
            'All scheduled plans and the other project PLANs are complete. Read the listed code FIX '
            'reports and their attempted correction proof against current code. For each, summarize '
            'whether it still reproduces, is a duplicate, appears fixed with proof, or is unverified. '
            'Prioritize remaining code defects. Do not edit code, close records, commit, or change '
            'documentation/contracts. Those corrections remain separate INTAKE items for later. '
            'Do not claim a test passed without running it. Return the structured result, placing '
            'the per-FIX assessment and commands/output in summary. This is an audit of the deferred '
            'queue, not a third review or another fix loop.\n' + json.dumps(context, indent=2))
        output = command(argv, self.root, input=prompt,
                         timeout=self.config.get('worker_timeout_seconds', 3600),
                         env={**os.environ, 'ORCH_CONTEXT': json.dumps(context), 'ORCH_RESULT': str(result_file)})
        (self.directory / f'{token}.log').write_text(output, encoding='utf-8')
        require(git(self.root, 'rev-parse', 'HEAD') == head and not git(self.root, 'status', '--porcelain'),
                'Defect auditor changed the base checkout')
        result = json.loads(result_file.read_text(encoding='utf-8'))
        require(result.get('status') == 'complete' and isinstance(result.get('summary'), str) and
                result['summary'].strip(), 'Post-PLAN defect audit incomplete')
        self.state['followup_audit'] = {'head': head, 'result': result}
        self.save()

    def run(self):
        with run_lock(self.runtime):
            # Another scheduler may have completed between construction and locking.
            if self.state_path.exists():
                self.state = json.loads(self.state_path.read_text(encoding='utf-8'))
                require(self.state['config_hash'] == self.fingerprint, 'Schedule changed before lock acquisition')
            self.preflight()
            # Never replay an interrupted writer or consume a third review round.
            # Completed phase receipts survive; uncertain worker outcomes are parked.
            for track in self.config['tracks']:
                state = self.state['tracks'][track['id']]
                if state['status'] == 'merged' and not state.get('cleaned'):
                    try:
                        self.cleanup(track)
                    except Exception as exc:
                        self.update(state, reason=str(exc))
                elif state['status'] == 'delivering':
                    data = json.loads(self.gh('pr', 'view', str(state['pr']), '--repo', self.config['github_repo'], '--json', 'state'))
                    if data['state'] == 'MERGED':
                        self.finish_merge(track)
                    else:
                        state['status'] = 'ready_with_followups' if state['findings'] else 'ready'
                elif state['status'] == 'running':
                    state.update(status='blocked', reason='Interrupted worker: reconcile its process, HEAD and result before recovery')
            self.save()
            with ThreadPoolExecutor(max_workers=self.config['max_parallel_tracks']) as pool:
                active = {}
                while True:
                    for track in self.config['tracks']:
                        state = self.state['tracks'][track['id']]
                        if state['status'] in ('ready', 'ready_with_followups'):
                            try:
                                self.deliver(track)
                            except Exception as exc:
                                # Retain delivery receipt if the remote merge outcome is uncertain.
                                self.update(state, status='merged' if state['status'] == 'merged' else
                                            'delivering' if state.get('delivery_head') else 'blocked', reason=str(exc))
                        if state['status'] != 'pending' or len(active) >= self.config['max_parallel_tracks']:
                            continue
                        if not all(self.state['tracks'][dep]['status'] == 'merged' for dep in track['depends_on']):
                            continue
                        # Parked tracks retain their resources; don't reuse an uncertain service/port.
                        others = [t for t in self.config['tracks'] if t['id'] != track['id'] and
                                  self.state['tracks'][t['id']]['status'] != 'pending' and
                                  not self.state['tracks'][t['id']].get('cleaned')]
                        if any(self.conflict(track, other) for other in others):
                            continue
                        try:
                            base = self.sync()
                            path, branch = self.location(track)
                            require(not path.exists(), 'Assigned worktree already exists')
                            git(self.root, 'check-ignore', str(path))
                            git(self.root, 'worktree', 'add', '-b', branch, str(path), base)
                            self.update(state, status='running', base=base)
                            active[pool.submit(self.build, track)] = track
                        except Exception as exc:
                            self.update(state, status='blocked', reason=str(exc))
                    if not active:
                        break
                    finished, _ = wait(active, return_when=FIRST_COMPLETED)
                    for future in finished:
                        track = active.pop(future)
                        try:
                            future.result()
                        except Exception as exc:
                            self.update(self.state['tracks'][track['id']], status='blocked', reason=str(exc))
            complete = all(s['status'] == 'merged' for s in self.state['tracks'].values())
            queue = {'eligible': complete, 'reason': 'All scheduled PLANs merged' if complete else 'PLAN queue unfinished',
                     'FIX': [], 'INTAKE': []}
            for state in self.state['tracks'].values():
                for item in state['findings'].values():
                    queue['FIX' if item['kind'] == 'code' else 'INTAKE'].append(item)
            # Earlier completed runs may have deferred their audit while other
            # PLANs were still waiting. Include the project's open reports too.
            for kind, folder in (('FIX', '.ai/fixes/open'), ('INTAKE', '.ai/plans/intake')):
                known = {item['record'] for item in queue[kind]}
                for report in (self.root / folder).glob(f'{kind}-*.md'):
                    relative = report.relative_to(self.root).as_posix()
                    if relative not in known:
                        queue[kind].append({'id': '-'.join(report.stem.split('-')[:2]),
                                            'record': relative, 'kind': 'code' if kind == 'FIX' else 'intake',
                                            'title': report.stem})
            other_plans = [str(p.relative_to(self.root)) for stage in ('backlog', 'active', 'review', 'blocked')
                           for p in (self.root / '.ai/plans' / stage).glob('PLAN-*.md')]
            if other_plans:
                queue.update(eligible=False, reason='Other project PLANs remain', waiting_for=other_plans)
            atomic_json(self.directory / 'followups.json', queue)
            self.audit_followups(queue)
            self.save()
            return complete and all(s.get('cleaned') for s in self.state['tracks'].values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('schedule', type=Path)
    parser.add_argument('--validate', action='store_true', help='Validate JSON without Git/network/writes')
    args = parser.parse_args()
    try:
        config = validate(json.loads(args.schedule.read_text(encoding='utf-8')))
        if args.validate:
            print('Schedule valid')
            return 0
        runner = Runner(config)
        complete = runner.run()
        print(json.dumps(runner.state, indent=2))
        print(f'Follow-up queue: {runner.directory / "followups.json"}')
        return 0 if complete else 1
    except (Blocked, KeyError, TypeError, ValueError, OSError, subprocess.TimeoutExpired) as exc:
        print(f'Blocked: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
