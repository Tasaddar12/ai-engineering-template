"""Exact approval snapshots and fresh guarded removal of runtime-owned resources."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import uuid

from . import worktrees
from .core import Failure, load_json, now, root, write_json


def _collect():
    eligible, preserved = [], []
    ownership = worktrees.registry()
    for entry in ownership['entries']:
        if entry.get('removed'):
            continue
        try:
            revision = worktrees.identity(entry['path'], entry['branch'])['head']
            proof = None
            if entry.get('kind') == 'session':
                from . import sessions
                match = [s for s in load_json(sessions.store(), {'sessions': []})['sessions'] if s.get('id') == entry.get('session_id') and s.get('status') != 'closed']
                if len(match) != 1:
                    raise Failure('cleanup-session-unowned', entry['path'])
                proof = sessions.close_evidence(match[0])
            worktrees.deletion_guards(entry, revision, require_ancestry=proof is None or proof['mapping'] == 'ancestry')
            # Worker cleanup must have actual prior integration evidence, not merely a shared base.
            if entry.get('kind') == 'worker' and (not entry.get('merged') or entry.get('head') != revision):
                raise Failure('cleanup-worker-not-integrated', entry['path'])
            packet = {'id': entry['id'], 'path': entry['path'], 'branch': entry['branch'], 'head': revision,
                      'kind': entry['kind'], 'owner_root': entry['orchestrator_root']}
            if proof:
                packet['integration_provenance'] = proof
            eligible.append(packet)
        except Exception as exc:
            preserved.append({'path': entry['path'], 'branch': entry['branch'],
                              'reason': str(exc), 'error': exc.code if isinstance(exc, Failure) else 'evidence-unavailable'})
    return eligible, preserved


def snapshot():
    with worktrees.lifecycle_lock():
        return _collect()[0]


def command(args, action):
    if action not in ('preview', 'apply'):
        raise Failure('unknown-cleanup-action', action, 2)
    with worktrees.lifecycle_lock():
        directory = worktrees.common() / 'engineer/cleanup-approvals'
        if action == 'preview':
            entries, preserved = _collect()
            packet = {'schema': 1, 'created': now(), 'nonce': uuid.uuid4().hex, 'entries': entries,
                      'caller_root': str(root()), 'caller_head': worktrees.head(), 'repository': str(worktrees.common()),
                      'consumed': False, 'removed': []}
            token = hashlib.sha256(json.dumps(packet, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            write_json(directory / (token + '.json'), packet)
            return {'approval_token': token, 'entries': entries, 'count': len(entries), 'preserved': preserved,
                    'requires_exact_approval': True}
        if not args.has('confirm'):
            raise Failure('cleanup-exact-approval-required', 'Show the exact preview list, obtain its approval, then supply its token and --confirm')
        token = str(args.get('approval-token', args.arg(0, '')))
        if not re.fullmatch(r'[0-9a-f]{64}', token):
            raise Failure('cleanup-token-invalid', 'Supply the exact preview token')
        path = directory / (token + '.json')
        if path.is_symlink():
            raise Failure('cleanup-token-invalid', 'Approval record is linked')
        approved = load_json(path)
        if not approved or approved.get('consumed'):
            raise Failure('cleanup-preview-expired', 'Create and approve a new exact snapshot')
        if hashlib.sha256(json.dumps(approved, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != token:
            raise Failure('cleanup-approval-drift', 'The exact approved snapshot was modified')
        if approved['caller_root'] != str(root()) or approved['caller_head'] != worktrees.head() or approved['repository'] != str(worktrees.common()):
            raise Failure('cleanup-caller-drift', 'Approval is bound to the captured checkout and revision')
        # Consume before any destructive action: interrupted partial runs require fresh approval.
        approved.update(consumed=True, started=now())
        write_json(path, approved)
        ownership = worktrees.registry()
        try:
            for expected in approved['entries']:
                current, _ = _collect()
                if expected not in current:
                    raise Failure('cleanup-resource-drift', 'Preserve changed or no-longer-eligible approved resource', entry=expected, removed=approved['removed'])
                entry = next((e for e in ownership['entries'] if e['id'] == expected['id'] and not e.get('removed')), None)
                if entry is None:
                    raise Failure('cleanup-ownership-drift', expected['path'])
                proof = expected.get('integration_provenance')
                if proof:
                    entry['integration_provenance'] = proof
                try:
                    worktrees.remove_owned(entry, expected['head'], require_ancestry=proof is None or proof['mapping'] == 'ancestry')
                finally:
                    worktrees.save_registry(ownership)
                if entry['kind'] == 'session':
                    from . import sessions
                    state = load_json(sessions.store(), {'sessions': []})
                    matched = next(s for s in state['sessions'] if s['id'] == entry['session_id'])
                    matched.update(status='closed', closed=now(), closed_head=expected['head'], integration_provenance=proof)
                    write_json(sessions.store(), state)
                approved['removed'].append(expected)
                write_json(path, approved)
        except BaseException as exc:
            approved.update(status='partial-preserved', error=str(exc), finished=now())
            write_json(path, approved)
            raise
        approved.update(status='completed', finished=now())
        write_json(path, approved)
        return {'removed': approved['removed'], 'count': len(approved['removed']), 'approval_token': token}
