"""Shared-Git session lineage and provider-proven closeout of owned checkouts."""
from __future__ import annotations
from pathlib import Path
import json
import uuid

from . import config, records, repository, worktrees
from .core import Failure, load_json, now, root, slug, write_json


def store():
    return worktrees.common() / 'engineer/sessions.json'


def _load():
    data = load_json(store(), {'schema': 1, 'sessions': []})
    if not isinstance(data, dict) or not isinstance(data.get('sessions'), list):
        raise Failure('session-registry-invalid', str(store()))
    return data


def _validate(entry):
    actual = worktrees.identity(entry['worktree'], entry['branch'])
    if not worktrees.ancestor(entry['base'], actual['head'], entry['worktree']):
        raise Failure('session-base-drift', entry['branch'])
    return actual


def close_evidence(entry, pr=None):
    """Read current origin-bound provider state; prove squash content before deletion."""
    origin = repository.identity()
    value = str(pr or entry.get('pr_url') or entry['branch'])
    if value.startswith('https://'):
        repository.require_url(value, 'pull')
    fields = 'url,state,mergedAt,headRefOid,headRefName,baseRefName,mergeCommit'
    response = worktrees.run(['gh', 'pr', 'view', value, '--repo', origin['slug'], '--json', fields],
                             root(), timeout=60)
    packet = json.loads(response.stdout)
    repository.require_url(packet.get('url', ''), 'pull')
    actual = _validate(entry)
    revision = actual['head']
    if (packet.get('state') != 'MERGED' or not packet.get('mergedAt')
            or packet.get('headRefName') != entry['branch'] or packet.get('headRefOid') != revision):
        raise Failure('session-pr-not-current-merged', 'Provider evidence must identify this exact branch HEAD as merged', pr=packet)
    merge = (packet.get('mergeCommit') or {}).get('oid')
    if not merge or not worktrees.ancestor(merge, worktrees.head()):
        raise Failure('session-merge-not-local', 'Caller HEAD does not contain the actual provider merge commit')
    direct = worktrees.ancestor(revision, worktrees.head())
    if not direct:
        # A provider's MERGED state alone cannot map unrelated post-merge commits.
        # Every final changed blob/mode must match the actual squash merge tree.
        changed = worktrees.git('diff', '--name-only', '--no-renames', '-z', entry['base'], revision,
                                cwd=entry['worktree']).stdout.split('\0')
        for name in filter(None, changed):
            left = worktrees.git('ls-tree', revision, '--', name, cwd=entry['worktree']).stdout
            right = worktrees.git('ls-tree', merge, '--', name).stdout
            if left != right:
                raise Failure('session-squash-content-unproven', 'Actual merge tree does not preserve this session path', path=name)
    if repository.identity() != origin:
        raise Failure('session-origin-drift', 'Origin changed during provider readback')
    return {'url': packet['url'], 'head': revision, 'branch': entry['branch'], 'base_branch': packet.get('baseRefName'),
            'merge_commit': merge, 'merged_at': packet['mergedAt'], 'origin': origin,
            'mapping': 'ancestry' if direct else 'provider-merged-exact-tree'}


def command(args, action):
    if action not in ('open', 'adopt', 'status', 'close'):
        raise Failure('unknown-session-action', action, 2)
    with worktrees.lifecycle_lock():
        data = _load()
        if action == 'status':
            opened = []
            for entry in data['sessions']:
                if entry.get('status') == 'closed':
                    continue
                packet = {**entry, 'exists': Path(entry['worktree']).is_dir()}
                try:
                    packet.update(head=_validate(entry)['head'], dirty=worktrees.dirty(entry['worktree']), valid=True)
                except Failure as exc:
                    packet.update(valid=False, error=exc.code, reason=exc.message)
                opened.append(packet)
            return {'sessions': data['sessions'], 'count': len(data['sessions']), 'open': opened, 'open_count': len(opened)}
        ownership = worktrees.registry()
        if action == 'close':
            branch = args.need()
            matches = [e for e in data['sessions'] if e['branch'] == branch and e.get('status') != 'closed']
            if len(matches) != 1:
                raise Failure('session-not-found', 'Select one open owned session', branch=branch)
            entry = matches[0]
            actual = _validate(entry)
            owned = worktrees.owned(entry['worktree'], ownership)
            if owned.get('session_id') != entry['id']:
                raise Failure('session-ownership-drift', branch)
            worktrees.deletion_guards(owned, actual['head'], require_ancestry=False)
            proof = close_evidence(entry, args.get('pr'))
            if worktrees.head(entry['worktree']) != proof['head']:
                raise Failure('session-head-drift', branch)
            entry.update(status='closing', integration_provenance=proof, close_requested_at=now())
            owned['integration_provenance'] = proof
            write_json(store(), data)
            worktrees.save_registry(ownership)
            try:
                worktrees.remove_owned(owned, proof['head'], require_ancestry=proof['mapping'] == 'ancestry')
            finally:
                # A failed ref deletion must not lose proof that the checkout was removed.
                worktrees.save_registry(ownership)
            entry.update(status='closed', closed=now(), closed_head=proof['head'])
            write_json(store(), data)
            return {**entry, 'closed': True, 'removed': True, 'merge_authorized': False}
        kind, label = args.need(), args.need(1)
        if kind not in ('phase', 'quick', 'milestone', 'onboard'):
            raise Failure('invalid-session-kind', kind, 2)
        label = records.number(label) if kind == 'phase' else slug(str(label))
        matches = [e for e in data['sessions'] if e['kind'] == kind and e['label'] == label and e.get('status') != 'closed']
        if matches:
            if len(matches) != 1:
                raise Failure('ambiguous-session', kind + ':' + label)
            entry = matches[0]
            actual = _validate(entry)
            recovered = entry.get('status') in ('creating', 'creation-interrupted')
            if recovered:
                resource = worktrees.owned(entry['worktree'], ownership)
                if resource.get('session_id') != entry['id']:
                    raise Failure('session-ownership-drift', entry['branch'])
                entry['status'] = resource['status'] = 'open'
                write_json(store(), data)
                worktrees.save_registry(ownership)
            return {**entry, 'head': actual['head'], 'reused': True, 'recovered': recovered, 'dirty': worktrees.dirty(entry['worktree'])}
        base = worktrees.git('rev-parse', '--verify', str(args.get('base', 'HEAD')) + '^{commit}').stdout.strip()
        main = worktrees.primary()
        if action == 'adopt':
            actual = worktrees.identity(root())
            if root() == main or worktrees.protected(actual['branch']) or worktrees.dirty(root()):
                raise Failure('session-adoption-refused', 'Adopt only a clean named nonprotected isolated checkout')
            if not worktrees.ancestor(base, actual['head']):
                raise Failure('session-base-unrelated', str(base))
            target, branch = root(), actual['branch']
            # External host-owned worktrees can be used, but cannot be deleted by this runtime.
            try:
                worktrees.managed_target(target, main)
                cleanup_owned = True
            except Failure:
                cleanup_owned = False
        else:
            branch = str(config.lookup(config.load(), 'worktree.branch_prefix', 'codex/')) + kind + '-' + label
            worktrees.git('check-ref-format', '--branch', branch)
            target = worktrees.managed_target(main / str(config.lookup(config.load(), 'worktree.directory', '.worktrees')) / slug(branch), main)
            if target.exists() or worktrees.git('show-ref', '--verify', '--quiet', 'refs/heads/' + branch, check=False).returncode == 0:
                raise Failure('session-target-exists', 'Existing resources require explicit clean adoption', path=str(target), branch=branch)
            if worktrees.git('check-ignore', '--quiet', '--', str(target), cwd=main, check=False).returncode:
                raise Failure('session-root-not-ignored', str(target))
            cleanup_owned = True
        if any(not e.get('removed') and (worktrees.normalized(e['path']) == worktrees.normalized(target) or e.get('branch') == branch) for e in ownership['entries']):
            raise Failure('session-already-owned', str(target))
        identifier = uuid.uuid4().hex
        entry = {'id': identifier, 'kind': kind, 'label': label, 'branch': branch, 'worktree': str(target),
                 'base': base, 'status': 'creating' if action == 'open' else 'open', 'created': now(),
                 'adopted': action == 'adopt', 'cleanup_owned': cleanup_owned,
                 'source_worktree': str(root()), 'source_branch': worktrees.identity(root())['branch']}
        resource = {'id': uuid.uuid4().hex, 'kind': 'session', 'session_id': identifier, 'path': str(target),
                    'branch': branch, 'base': base, 'orchestrator_root': str(main), 'created': entry['created'],
                    'cleanup_owned': cleanup_owned, 'status': entry['status']}
        data['sessions'].append(entry)
        ownership['entries'].append(resource)
        write_json(store(), data)
        worktrees.save_registry(ownership)
        if action == 'open':
            try:
                worktrees.git('worktree', 'add', '-b', branch, str(target), base, cwd=main)
            except BaseException:
                entry['status'] = resource['status'] = 'creation-interrupted'
                write_json(store(), data)
                worktrees.save_registry(ownership)
                raise
        actual = worktrees.identity(target, branch)
        entry['status'] = resource['status'] = 'open'
        resource['recorded_head'] = actual['head']
        write_json(store(), data)
        worktrees.save_registry(ownership)
        return {**entry, 'head': actual['head'], 'reused': False, 'created_worktree': action == 'open'}


def locate(args):
    identifier = records.number(args.need())
    with worktrees.lifecycle_lock():
        matches = [e for e in _load()['sessions'] if e.get('kind') == 'phase' and e.get('status') != 'closed' and records.number(e['label']) == identifier]
        if len(matches) > 1:
            raise Failure('ambiguous-phase-session', identifier)
        if matches:
            entry = matches[0]
            actual = _validate(entry)
            target = Path(entry['worktree'])
            candidates = []
            directory = target / '.planning/phases'
            if directory.is_dir():
                for path in directory.iterdir():
                    if path.is_dir() and not path.is_symlink():
                        try:
                            if records.number(path.name.split('-', 1)[0]) == identifier:
                                candidates.append(path)
                        except (ValueError, Failure):
                            continue
            if len(candidates) != 1:
                raise Failure('phase-session-record-missing', identifier)
            return {'found': True, 'source': 'session', 'padded_phase': identifier, 'worktree': str(target),
                    'branch': actual['branch'], 'session': entry, 'phase_dir': str(candidates[0])}
        try:
            directory = records.phase_dir(identifier)
        except Failure:
            return {'found': False, 'source': None, 'padded_phase': identifier, 'worktree': None, 'session': None}
        return {'found': True, 'source': 'current', 'padded_phase': identifier, 'worktree': str(root()),
                'branch': worktrees.identity(root())['branch'], 'phase_dir': str(directory), 'session': None}
