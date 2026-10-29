"""Owned isolated worktrees, durable worker identities, and serialized integration."""
from __future__ import annotations
import contextlib
import ctypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import uuid

from . import config, records
from .core import Failure, load_json, now, root, run, slug, write_json
from .locking import acquire
from .text import split_frontmatter


def git(*args, cwd=None, check=True):
    return run(['git', *map(str, args)], cwd or root(), check=check, timeout=120)


def common():
    return Path(git('rev-parse', '--path-format=absolute', '--git-common-dir').stdout.strip()).resolve()


@contextlib.contextmanager
def lifecycle_lock():
    try:
        with acquire(common() / 'engineer/lifecycle.lock', 10):
            yield
    except TimeoutError as exc:
        raise Failure('lifecycle-owned', str(exc)) from exc


def registry_path():
    return common() / 'engineer/worktree-ownership.json'


def registry():
    data = load_json(registry_path(), {'schema': 1, 'entries': []})
    if not isinstance(data, dict) or data.get('schema') != 1 or not isinstance(data.get('entries'), list):
        raise Failure('ownership-registry-invalid', str(registry_path()))
    return data


def save_registry(data):
    write_json(registry_path(), data)


def normalized(value):
    return os.path.normcase(str(Path(value).resolve()))


def no_links(path):
    path = Path(path).absolute()
    for candidate in (path, *path.parents):
        if candidate.is_symlink() or (candidate.exists() and getattr(candidate.lstat(), 'st_file_attributes', 0) & 0x400):
            raise Failure('linked-path-refused', str(candidate))
    return path.resolve()


def list_worktrees():
    output = git('worktree', 'list', '--porcelain', '-z').stdout
    result = []
    item = {}
    for line in output.split('\0'):
        if not line:
            if item:
                result.append(item)
                item = {}
            continue
        key, _, value = line.partition(' ')
        if key == 'worktree':
            item['path'] = str(Path(value).resolve())
        elif key == 'branch':
            item['branch'] = value.removeprefix('refs/heads/')
        elif key == 'HEAD':
            item['head'] = value
        elif key in ('locked', 'prunable', 'bare', 'detached'):
            item[key] = value or True
    if item:
        result.append(item)
    return result


def registered(path):
    matches = [item for item in list_worktrees() if normalized(item['path']) == normalized(path)]
    if len(matches) != 1:
        raise Failure('worktree-unregistered', str(path))
    return matches[0]


def primary():
    items = list_worktrees()
    if not items:
        raise Failure('worktree-missing', 'Git reported no checkouts')
    return Path(items[0]['path']).resolve()


def managed_target(path, owner_root):
    target = no_links(path)
    owner = no_links(owner_root)
    registered(owner)
    settings = config.load()
    configured = str(config.lookup(settings, 'worktree.directory', '.worktrees'))
    relatives = [configured, '.worktrees', '.claude/worktrees', '.codex/worktrees']
    allowed = []
    for value in relatives:
        candidate = Path(value)
        if candidate.is_absolute() or '..' in candidate.parts:
            continue
        allowed.append((owner / candidate).resolve())
    if target == owner or not any(target.is_relative_to(base) and target != base for base in allowed):
        raise Failure('worktree-path-outside-managed-root', str(target), owner_root=str(owner))
    return target


def identity(path, branch=None):
    path = no_links(path)
    item = registered(path)
    actual = Path(git('rev-parse', '--show-toplevel', cwd=path).stdout.strip()).resolve()
    if actual != path or Path(git('rev-parse', '--path-format=absolute', '--git-common-dir', cwd=path).stdout.strip()).resolve() != common():
        raise Failure('worktree-repository-mismatch', str(path))
    if not item.get('branch') or item.get('locked') or item.get('prunable'):
        raise Failure('worktree-unusable', 'Detached, locked or prunable checkout preserved', worktree=item)
    if branch is not None and item['branch'] != branch:
        raise Failure('worktree-branch-drift', str(path), expected=branch, actual=item['branch'])
    return item


def head(path=None):
    return git('rev-parse', 'HEAD', cwd=path).stdout.strip()


def ancestor(first, second, cwd=None):
    result = git('merge-base', '--is-ancestor', first, second, cwd=cwd, check=False)
    if result.returncode not in (0, 1):
        raise Failure('ancestry-unavailable', result.stderr.strip())
    return result.returncode == 0


def dirty(path, allow=()):
    fields = git('status', '--porcelain=v1', '-z', '--untracked-files=all', cwd=path).stdout.split('\0')
    index = 0
    allowed = set(allow)
    while index < len(fields):
        entry = fields[index]
        index += 1
        if not entry:
            continue
        names = [entry[3:]]
        if entry[:2].strip().startswith(('R', 'C')) and index < len(fields):
            names.append(fields[index])
            index += 1
        if any(name not in allowed for name in names):
            return True
    return False


def protected(branch):
    return branch in config.lookup(config.load(), 'git.protected_branches', ['main', 'master'])


def scope_path(value):
    value = str(value).replace('\\', '/')
    while value.startswith('./'):
        value = value[2:]
    path = PurePosixPath(value)
    if not value or path.is_absolute() or '..' in path.parts or any(':' in p for p in path.parts) or any(c in value for c in '*?['):
        raise Failure('worker-scope-invalid', 'Declare exact relative files, not globs or outside paths', path=value)
    if path.parts[0] == '.git':
        raise Failure('worker-scope-invalid', value)
    return path.as_posix()


def scope_values(args, key):
    values = args.all(key + '-json') or args.all(key)
    if len(values) == 1:
        value = values[0]
        if value.strip().startswith('['):
            try:
                values = json.loads(value)
            except ValueError as exc:
                raise Failure('worker-scope-invalid', str(exc)) from exc
        elif '\n' in value:
            values = [line for line in value.splitlines() if line]
        elif ' ' in value:
            # Retained shell callers send PLAN_FILES as one whitespace-separated value.
            # JSON is the unambiguous route for actual filenames containing spaces.
            values = shlex.split(value)
    if not isinstance(values, list) or any(not isinstance(v, str) for v in values):
        raise Failure('worker-scope-invalid', key)
    return list(dict.fromkeys(scope_path(v) for v in values))


def manifest(phase):
    return records.planning() / 'worktrees' / (slug(str(phase or 'session')) + '.json')


def manifest_path(args):
    value = args.get('manifest')
    if value is None:
        return no_links(manifest(args.get('phase', 'session')))
    path = no_links(Path(value) if Path(value).is_absolute() else root() / value)
    if path.suffix.lower() != '.json':
        raise Failure('manifest-path-invalid', 'Explicit manifest must be an exact JSON file')
    return path


def read_manifest(path, missing=False):
    data = load_json(path)
    if data is None and missing:
        return {'schema': 1, 'orchestrator_root': str(root()), 'worktrees': []}
    if not isinstance(data, dict):
        raise Failure('manifest-invalid', 'Missing or invalid manifest', path=str(path))
    entries = data.get('worktrees', data.get('workers', data.get('entries')))
    if not isinstance(entries, list) or any(not isinstance(e, dict) for e in entries):
        raise Failure('manifest-invalid', 'Manifest needs worktrees[], workers[] or entries[]', path=str(path))
    owner = data.get('orchestrator_root')
    if not owner:
        raise Failure('manifest-owner-missing', 'Capture the exact orchestrator root before dispatch', path=str(path))
    data['worktrees'] = entries
    return data


def manifest_command(args):
    path = manifest_path(args)
    operation = args.arg(0, args.get('action', 'read'))
    with lifecycle_lock():
        if operation == 'init':
            owner = no_links(args.get('root', root()))
            identity(owner)
            if path.exists() and path.stat().st_size:
                data = read_manifest(path)
                if normalized(data['orchestrator_root']) != normalized(owner):
                    raise Failure('manifest-owner-drift', str(path))
            else:
                data = {'schema': 1, 'orchestrator_root': str(owner), 'worktrees': []}
                write_json(path, data)
        else:
            data = read_manifest(path)
        if operation == 'paths':
            paths = [e.get('worktree_path', e.get('path')) for e in data['worktrees']]
            return '\n'.join(paths) if args.has('lines') else {'paths': paths}
        if operation == 'root':
            return {'orchestrator_root': data['orchestrator_root']}
        if operation not in ('init', 'read'):
            raise Failure('manifest-action-invalid', operation)
        return {**data, 'manifest': str(path)}


def owned(path, data=None):
    items = (data or registry())['entries']
    matches = [entry for entry in items if normalized(entry['path']) == normalized(path) and not entry.get('removed')]
    if len(matches) != 1:
        raise Failure('worktree-not-owned', 'No unique durable ownership record', path=str(path))
    return matches[0]


def process_state(pid):
    """Return alive/creation identity; lack of permissions remains unknown, not dead."""
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return None, None
    if os.name == 'nt':
        api = ctypes.WinDLL('kernel32', use_last_error=True)
        api.OpenProcess.restype = ctypes.c_void_p
        handle = api.OpenProcess(0x1000, False, pid)
        if not handle:
            return (False, None) if ctypes.get_last_error() == 87 else (None, None)
        try:
            code = ctypes.c_ulong()
            times = [ctypes.c_ulonglong() for _ in range(4)]
            if not api.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code)):
                return None, None
            birth = None
            if api.GetProcessTimes(ctypes.c_void_p(handle), *(ctypes.byref(v) for v in times)):
                birth = str(times[0].value)
            return code.value == 259, birth
        finally:
            api.CloseHandle(ctypes.c_void_p(handle))
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False, None
    except PermissionError:
        return None, None
    statfile = Path('/proc') / str(pid) / 'stat'
    try:
        fields = statfile.read_text().rsplit(')', 1)[1].split()
        boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        return fields[0] != 'Z', boot + ':' + fields[19]
    except (OSError, IndexError):
        return True, None


def liveness(entry):
    worker = entry.get('worker')
    if not worker:
        return {'pidAlive': None, 'needsReconciliation': True, 'reason': 'No process or terminal harness receipt is recorded'}
    if worker.get('source') == 'native-host' and worker.get('terminal_receipt_sha256'):
        return {'pidAlive': False, 'needsReconciliation': worker.get('status') != 'complete', 'source': 'native-host-terminal-receipt'}
    if worker.get('status') == 'complete':
        alive, birth = process_state(worker.get('pid'))
        if alive and birth == worker.get('process_identity'):
            return {'pidAlive': True, 'needsReconciliation': True, 'reason': 'Recorded terminal worker is still alive'}
        if alive is None:
            return {'pidAlive': None, 'needsReconciliation': True, 'reason': 'Worker liveness unavailable'}
        return {'pidAlive': False, 'needsReconciliation': False}
    alive, birth = process_state(worker.get('pid'))
    if alive and (not birth or not worker.get('process_identity')):
        return {'pidAlive': None, 'needsReconciliation': True, 'reason': 'Process creation identity unavailable'}
    if alive and birth != worker.get('process_identity'):
        return {'pidAlive': False, 'needsReconciliation': True, 'pid_reused': True}
    return {'pidAlive': alive, 'needsReconciliation': alive is not True}


def assert_stopped(entry, allow_unrecorded=False):
    if not entry.get('worker') and allow_unrecorded:
        return
    live = liveness(entry)
    if live['pidAlive'] is not False:
        raise Failure('worker-live-or-uncertain', 'Preserve worker and do not redispatch, integrate or remove it', worker=entry, **live)


def unresolved(entry):
    return entry.get('worker', {}).get('status') != 'complete' or liveness(entry)['pidAlive'] is not False


def _canonical_entry(entry):
    path = entry.get('worktree_path', entry.get('worktree', entry.get('path')))
    branch = entry.get('branch', entry.get('expected_branch'))
    base = entry.get('expected_base', entry.get('base'))
    if not all(isinstance(v, str) and v for v in (path, branch, base)):
        raise Failure('manifest-entry-invalid', 'Exact path, branch and expected_base are required', entry=entry)
    return path, branch.removeprefix('refs/heads/'), base


def _summary(entry, target, revision):
    name = entry.get('summary_path') or entry.get('worker', {}).get('summary_path')
    if not name:
        plan = str(entry.get('plan', ''))
        tracked = git('ls-tree', '-r', '--name-only', revision, '--', '.planning/phases', '.planning/quick', cwd=target).stdout.splitlines()
        candidates = [p for p in tracked if p.endswith('-SUMMARY.md') and PurePosixPath(p).name == plan + '-SUMMARY.md']
        if len(candidates) != 1:
            raise Failure('worker-summary-unresolved', 'Record the exact SUMMARY path; no guessed broad match', plan=plan)
        name = candidates[0]
    name = scope_path(name)
    content = git('show', revision + ':' + name, cwd=target, check=False)
    if content.returncode:
        raise Failure('worker-summary-uncommitted', name)
    metadata, _ = split_frontmatter(content.stdout)
    if metadata.get('status') != 'complete':
        raise Failure('worker-summary-incomplete', name, status=metadata.get('status'))
    if not git('log', '--format=%H', entry['base'] + '..' + revision, '--', name, cwd=target).stdout.strip():
        raise Failure('worker-summary-stale', 'SUMMARY must be committed in this attempt', path=name)
    return name


def validate_worker(entry):
    target = managed_target(entry['path'], entry['orchestrator_root'])
    item = identity(target, entry['branch'])
    assert_stopped(entry)
    if dirty(target):
        raise Failure('worker-dirty', 'Preserve uncommitted or untracked work', path=str(target))
    revision = head(target)
    bases = entry.get('allowed_bases', [entry['base']])
    if entry['base'] not in bases or not ancestor(entry['base'], revision, target):
        raise Failure('worker-base-drift', entry['plan'])
    if not ancestor(entry['base'], head()):
        raise Failure('integration-base-diverged', 'Integrator must contain the captured worker base')
    if revision == entry['base']:
        raise Failure('worker-no-commits', entry['plan'])
    summary = _summary(entry, target, revision)
    changed = git('diff', '--name-status', '--no-renames', '-z', entry['base'], revision, cwd=target).stdout.split('\0')
    files, deletions = set(entry.get('files', [])), set(entry.get('deletions', []))
    violations = []
    for i in range(0, len(changed) - 1, 2):
        status, name = changed[i:i+2]
        if status.startswith('D'):
            if name not in deletions:
                violations.append({'path': name, 'reason': 'undeclared deletion'})
        elif name not in files and name != summary:
            violations.append({'path': name, 'reason': 'outside exact declared file ownership'})
        if name.startswith('.git/'):
            violations.append({'path': name, 'reason': 'Git administrative path'})
        if name in ('.planning/STATE.md', '.planning/ROADMAP.md', '.planning/PROJECT.md',
                    '.planning/REQUIREMENTS.md', '.planning/config.yaml'):
            violations.append({'path': name, 'reason': 'coordinator-owned shared record'})
    if violations:
        raise Failure('worker-scope-violation', entry['plan'], violations=violations)
    return revision, summary


def deletion_guards(entry, expected_head, require_ancestry=True):
    if entry.get('cleanup_owned') is False:
        raise Failure('external-host-worktree-preserved', 'This adopted checkout belongs to the host cleanup lifecycle')
    target = managed_target(entry['path'], entry['orchestrator_root'])
    item = identity(target, entry['branch'])
    if target == root() or Path.cwd().resolve().is_relative_to(target):
        raise Failure('current-worktree-preserved', str(target))
    if protected(entry['branch']):
        raise Failure('protected-branch', entry['branch'])
    for other in list_worktrees():
        path = Path(other['path'])
        if path != target and path.is_relative_to(target):
            raise Failure('nested-worktrees-preserved', str(target))
    if entry.get('kind') == 'worker':
        assert_stopped(entry)
    else:
        for worker in registry()['entries']:
            if worker.get('kind') == 'worker' and not worker.get('removed') and normalized(worker.get('orchestrator_root', '')) == normalized(target):
                assert_stopped(worker)
    if dirty(target):
        raise Failure('dirty-worktree-preserved', str(target))
    ignored = git('ls-files', '--others', '--ignored', '--exclude-standard', '--directory', '-z', cwd=target).stdout
    ignored_paths = [name for name in ignored.split('\0') if name]
    if ignored_paths:
        raise Failure('ignored-data-preserved', 'Ignored local data has no disposal authority or verified backup', path=str(target), files=ignored_paths)
    actual = head(target)
    if actual != expected_head or item['head'] != expected_head:
        raise Failure('worktree-head-drift', str(target))
    if require_ancestry and not ancestor(actual, head()):
        raise Failure('unmerged-worktree-preserved', str(target))
    return target


def remove_owned(entry, expected_head, require_ancestry=True):
    target = deletion_guards(entry, expected_head, require_ancestry)
    git('worktree', 'remove', str(target))
    entry.update(removed=True, removedAt=now(), removed_head=expected_head)
    # Compare-and-delete this exact ref. There is never a force branch reset.
    current = git('rev-parse', '--verify', 'refs/heads/' + entry['branch'], check=False)
    if current.returncode == 0:
        if current.stdout.strip() != expected_head:
            raise Failure('removed-worktree-branch-drift', entry['branch'], worktree_removed=True)
        if any(w.get('branch') == entry['branch'] for w in list_worktrees()):
            raise Failure('branch-in-use-preserved', entry['branch'], worktree_removed=True)
        git('update-ref', '-d', 'refs/heads/' + entry['branch'], expected_head)
    return entry


def _create_or_record(args, action):
    path = manifest_path(args)
    with lifecycle_lock():
        manifest_data = read_manifest(path, missing=True)
        owner = no_links(args.get('root', manifest_data['orchestrator_root']))
        identity(owner)
        if normalized(owner) != normalized(manifest_data['orchestrator_root']):
            raise Failure('manifest-owner-drift', str(path))
        plan = str(args.arg(0, args.get('plan', args.get('agent-id', ''))))
        agent = str(args.get('agent-id', plan))
        if not agent or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,159}', agent):
            raise Failure('worker-agent-id-required', 'Supply the actual bounded agent ID or plan ID')
        prefix = config.lookup(config.load(), 'worktree.branch_prefix', 'codex/')
        branch = str(args.get('branch', prefix + slug(str(args.get('phase', 'session')) + '-' + agent)))
        git('check-ref-format', '--branch', branch)
        if protected(branch):
            raise Failure('protected-branch', branch)
        target = managed_target(args.get('path', owner / str(config.lookup(config.load(), 'worktree.directory', '.worktrees')) / slug(branch)), owner)
        base = git('rev-parse', '--verify', str(args.get('base', 'HEAD')) + '^{commit}', cwd=owner).stdout.strip()
        allowed = args.json('allowed-bases', [base])
        if not isinstance(allowed, list) or not allowed:
            raise Failure('allowed-bases-invalid', str(allowed))
        allowed = list(dict.fromkeys(git('rev-parse', '--verify', str(v) + '^{commit}', cwd=owner).stdout.strip() for v in allowed))
        if base not in allowed:
            raise Failure('expected-base-not-allowed', base)
        files, deletions = scope_values(args, 'files'), scope_values(args, 'deletions')
        ownership = registry()
        duplicates = [e for e in ownership['entries'] if not e.get('removed') and
                      (normalized(e['path']) == normalized(target) or e.get('branch') == branch or
                       e.get('kind') == 'worker' and e.get('orchestrator_root') == str(owner)
                       and (e.get('agent_id') == agent or e.get('plan') == plan and unresolved(e)))]
        if duplicates:
            existing = duplicates[0]
            if action == 'record-agent' and len(duplicates) == 1 and all(existing.get(k) == v for k, v in
                    {'path': str(target), 'branch': branch, 'base': base, 'files': files, 'deletions': deletions}.items()):
                identity(target, branch)
                if existing.get('worker'):
                    if not args.has('terminal-receipt') or existing['worker'].get('terminal_receipt_sha256') != hashlib.sha256(no_links(args.get('terminal-receipt')).read_bytes()).hexdigest():
                        raise Failure('worker-already-dispatched', 'Do not redispatch a durable worker', worker=existing)
                return {**existing, 'worktree_path': str(target), 'worktree': str(target), 'reused': True}
            raise Failure('worker-already-owned', 'Reconcile existing ownership instead of redispatch', entries=duplicates)
        entry = {'id': uuid.uuid4().hex, 'kind': 'worker', 'agent_id': agent, 'plan': plan, 'path': str(target),
                 'worktree_path': str(target), 'branch': branch, 'base': base, 'expected_base': base,
                 'allowed_bases': allowed, 'files': files, 'deletions': deletions, 'orchestrator_root': str(owner),
                 'created': now(), 'status': 'creating' if action == 'create' else 'recorded', 'merged': False}
        if args.has('summary-path'):
            entry['summary_path'] = scope_path(args.get('summary-path'))
        if action == 'create':
            if target.exists() or git('show-ref', '--verify', '--quiet', 'refs/heads/' + branch, check=False).returncode == 0:
                raise Failure('worktree-target-exists', str(target))
            if git('check-ignore', '--quiet', '--', str(target), cwd=owner, check=False).returncode:
                raise Failure('worktree-root-not-ignored', str(target))
            ownership['entries'].append(entry)
            save_registry(ownership)  # Intent survives a crash during Git creation.
            try:
                git('worktree', 'add', '-b', branch, str(target), base, cwd=owner)
            except BaseException:
                entry['status'] = 'creation-interrupted'
                save_registry(ownership)
                raise
        else:
            actual = identity(target, branch)
            if not ancestor(base, actual['head'], target):
                raise Failure('worker-base-drift', str(target))
            fork = git('merge-base', head(owner), actual['head'], cwd=target).stdout.strip()
            if fork not in allowed:
                raise Failure('worker-fork-base-unapproved', 'Actual branch fork is outside the captured allowed bases', actual_base=fork, allowed_bases=allowed)
            if args.has('terminal-receipt'):
                receipt_path = no_links(args.get('terminal-receipt'))
                raw = receipt_path.read_bytes()
                receipt = json.loads(raw)
                expected = {'agent_id': agent, 'branch': branch, 'head': actual['head']}
                if (not isinstance(receipt, dict) or receipt.get('host') not in ('claude', 'codex')
                        or receipt.get('source') != 'native-host'
                        or receipt.get('status') not in ('complete', 'completed', 'stopped')
                        or any(receipt.get(k) != v for k, v in expected.items())
                        or normalized(receipt.get('worktree_path', '')) != normalized(target)):
                    raise Failure('native-terminal-receipt-invalid', 'Supply actual terminal host metadata bound to this exact worker')
                entry['worker'] = {'source': 'native-host', 'status': 'complete', 'completedAt': now(),
                                   'terminal_receipt': receipt, 'terminal_receipt_sha256': hashlib.sha256(raw).hexdigest()}
                if receipt.get('summary_path'):
                    entry['summary_path'] = scope_path(receipt['summary_path'])
            elif args.has('completed'):
                raise Failure('native-terminal-receipt-required', '--completed alone does not prove worker termination')
            ownership['entries'].append(entry)
        entry['status'] = 'recorded'
        save_registry(ownership)
        manifest_data['worktrees'].append({**entry})
        write_json(path, manifest_data)
        return {**entry, 'worktree': str(target), 'manifest': str(path), 'created': action == 'create'}


def wave(args, action):
    path = manifest_path(args)
    with lifecycle_lock():
        data = read_manifest(path)
        owner = no_links(data['orchestrator_root'])
        if owner != root():
            raise Failure('integration-root-mismatch', 'Run integration from the captured orchestrator checkout', expected=str(owner))
        actual = identity(owner)
        if protected(actual['branch']):
            raise Failure('protected-integration-branch', actual['branch'])
        ownership = registry()
        results = []
        for item in data['worktrees']:
            entry = None
            try:
                target, branch, expected = _canonical_entry(item)
                active = [e for e in ownership['entries'] if normalized(e['path']) == normalized(target) and not e.get('removed')]
                removed = [e for e in ownership['entries'] if normalized(e['path']) == normalized(target)
                           and e.get('branch') == branch and e.get('base') == expected
                           and e.get('removed') and e.get('merged') and e.get('removed_head') == e.get('head')]
                if not active and len(removed) == 1 and not Path(target).exists():
                    results.append({**item, 'status': 'merged_removed', 'already_removed': True,
                                    'head': removed[0]['head'], 'cleaned': True})
                    continue
                entry = owned(target, ownership)
                if entry.get('kind') != 'worker' or entry['branch'] != branch or entry['base'] != expected or normalized(entry['orchestrator_root']) != normalized(owner):
                    raise Failure('manifest-ownership-drift', str(target))
                permitted = [path.relative_to(owner).as_posix()] if path.is_relative_to(owner) else []
                if dirty(owner, permitted):
                    raise Failure('dirty-integration-worktree', str(owner))
                revision, summary = validate_worker(entry)
                integration_head = head()
                if not ancestor(revision, integration_head):
                    entry.update(status='integrating', pending_head=revision, integration_before=integration_head)
                    save_registry(ownership)
                    # Fast-forward is sufficient for linear workers; divergent waves use a normal merge.
                    merged = git('merge', '--no-edit', revision, check=False)
                    if merged.returncode:
                        entry.update(status='merge-blocked', merge_error=merged.stderr[-12000:])
                        save_registry(ownership)
                        raise Failure('worker-merge-conflict', 'Preserve the real merge state for recovery', path=entry['path'])
                if not ancestor(revision, head()):
                    raise Failure('worker-merge-unproven', entry['path'])
                if identity(owner)['branch'] != actual['branch'] or dirty(owner, permitted):
                    raise Failure('integration-state-changed', 'Preserve integrated commits and reconcile unexpected branch or working changes')
                entry.update(merged=True, head=revision, integrated_head=head(), status='merged', summary_path=summary)
                save_registry(ownership)
                status = 'merged'
                if action == 'cleanup-wave':
                    remove_owned(entry, revision)
                    status = 'merged_removed'
                    save_registry(ownership)
                item.update(merged=True, head=revision, status=status, cleaned=bool(entry.get('removed')))
                result = {**item, 'status': status}
            except (Failure, OSError, subprocess.TimeoutExpired) as exc:
                code = exc.code if isinstance(exc, Failure) else 'git-operation-uncertain'
                message = exc.message if isinstance(exc, Failure) else str(exc)
                result = {**item, 'status': 'preserved', 'preserved': True, 'reason': message, 'error': code}
                if entry is not None:
                    result['worktree_removed'] = bool(entry.get('removed'))
                    entry['last_error'] = {'code': code, 'message': message, 'at': now()}
                    save_registry(ownership)
                results.append(result)
                write_json(path, data)
                # Never continue another merge while Git retains an unresolved merge state.
                if not isinstance(exc, Failure) or git('rev-parse', '--verify', 'MERGE_HEAD', check=False).returncode == 0:
                    break
                continue
            results.append(result)
            write_json(path, data)
        packet = {'workers': results, 'entries': results, 'action': action,
                'merged': [e for e in results if e['status'] in ('merged', 'merged_removed')],
                'removed': [e for e in results if e['status'] == 'merged_removed'],
                'preserved': [e for e in results if e.get('preserved')],
                'wave_clean': len(results) == len(data['worktrees']) and all(not e.get('preserved') for e in results)}
        return packet if packet['wave_clean'] else (packet, 1)


def base_check(args):
    mode = args.get('mode', 'orchestrator-worktree')
    if mode not in ('harness-worktree', 'orchestrator-worktree'):
        raise Failure('isolation-required', 'Only isolated worker modes are supported')
    actual = head()
    observation = args.get('observed-fork-base')
    expected = observation or args.get('base')
    if not expected:
        expected = actual if mode == 'orchestrator-worktree' else 'origin/HEAD'
    resolved = git('rev-parse', '--verify', str(expected) + '^{commit}', check=False)
    ready = resolved.returncode == 0 and resolved.stdout.strip() == actual
    return {'shouldDegrade': False, 'ready': ready, 'blocked': not ready, 'mode': mode, 'head': actual,
            'expectedBase': resolved.stdout.strip() if resolved.returncode == 0 else None,
            'message': 'Captured worker base matches orchestrator HEAD.' if ready else
                       'Worker fork base is unproven or differs from HEAD. Establish an isolated checkout at the captured revision; never degrade to primary-checkout execution.'}


def command(args, action):
    if action == 'manifest':
        return manifest_command(args)
    if action == 'base-check':
        return base_check(args)
    if action in ('create', 'record-agent'):
        return _create_or_record(args, action)
    if action in ('merge-wave', 'cleanup-wave'):
        return wave(args, action)
    if action == 'list':
        items = list_worktrees()
        return {'worktrees': items, 'count': len(items)}
    if action == 'health':
        directory = root() / str(config.lookup(config.load(), 'worktree.directory', '.worktrees'))
        ignored = git('check-ignore', '--quiet', '--', str(directory / '__ignored_candidate__'), check=False).returncode == 0
        return {'root_ignored': ignored, 'warnings': [] if ignored else ['Ignore the configured worktree root before dispatch']}
    if action == 'reap-orphans':
        # Metadata-only prune never unlocks, resets, or removes an existing checkout.
        with lifecycle_lock():
            result = git('worktree', 'prune', '--verbose')
        return {'pruned': result.stdout.splitlines(), 'diagnostic': result.stderr}
    raise Failure('unknown-worktree-action', action, 2)


def isolation(args):
    # Compatibility import; the coordinator-owned host adapter supplies actual spawn descriptors.
    from . import models
    identity(root())
    return 'harness-worktree' if models.resolve_host() == 'claude' else 'orchestrator-worktree'
