"""Portable, read-only proof of an exact workflow report-only Git successor.

This module knows no receipt/profile schema. Its caller remains responsible for
independent check contracts, original receipt authentication and input equality.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess


class ProofError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True).encode()).hexdigest()


def git(root, *args, input=None):
    return subprocess.run(['git', *args], cwd=root, input=input, capture_output=True,
                          check=True, timeout=30).stdout


def literal_path(name):
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name
            or any(c in name for c in '\0\r\n*?[]')
            or PurePosixPath(name).is_absolute()
            or any(p in ('', '.', '..', '.git') for p in name.split('/'))):
        raise ProofError('expected an exact repository-relative literal path')
    return name


def safe_path(root, name):
    literal_path(name)
    root = Path(root)
    current = root
    for part in name.split('/'):
        current = current / part
        try:
            info = current.lstat()
        except FileNotFoundError:
            continue
        if (stat.S_ISLNK(info.st_mode)
                or getattr(info, 'st_file_attributes', 0) & 0x400):
            raise ProofError('link or reparse point: ' + name)
    current.resolve().relative_to(root.resolve())
    return current


def plain_history(root):
    # Replacement refs and legacy grafts alter traversal without changing the
    # named commit's bytes. Such a graph cannot prove every actual commit.
    if os.environ.get("GIT_REPLACE_REF_BASE") is not None or os.environ.get("GIT_GRAFT_FILE") is not None:
        raise ProofError("overridden Git history is unsupported")
    if git(root, "for-each-ref", "--format=%(refname)", "refs/replace").strip():
        raise ProofError("Git replacement refs make ancestry proof unavailable")
    graft_path = Path(os.fsdecode(git(root, "rev-parse", "--git-path", "info/grafts").strip()))
    if not graft_path.is_absolute():
        graft_path = Path(root) / graft_path
    if graft_path.exists() and graft_path.read_bytes().strip():
        raise ProofError("Git grafts make ancestry proof unavailable")


def worktree_guard(root):
    raw = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
    names = sorted({os.fsdecode(name) for name in raw.split(b"\0") if name})
    content = manifest(root, names)
    metadata = []
    for name in names:
        path = safe_path(root, name)
        info = path.lstat()
        metadata.append([name, info.st_mtime_ns, info.st_ctime_ns, info.st_ino])
    return digest([content, metadata])


def commit_id(root, value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', value):
        raise ProofError('expected a full commit object ID')
    if git(root, 'cat-file', '-t', value).strip() != b'commit':
        raise ProofError('object is not a commit')
    return value


def tree_entry(root, revision, name):
    raw = git(root, 'ls-tree', '-z', revision, '--', literal_path(name))
    if not raw:
        return None
    rows = raw.rstrip(b'\0').split(b'\0')
    if len(rows) != 1:
        raise ProofError('ambiguous Git object')
    meta, actual = rows[0].split(b'\t', 1)
    mode, kind, oid = meta.decode('ascii').split()
    if os.fsdecode(actual) != name or kind != 'blob' or mode not in ('100644', '100755'):
        raise ProofError('unsupported Git mode: ' + name)
    git(root, 'cat-file', '-e', oid)
    return {'mode': mode, 'blob': oid}


def regular_report(root, revision, name):
    entry = tree_entry(root, revision, name)
    path = safe_path(root, name)
    if entry is None:
        if path.exists():
            raise ProofError("report exists without its Git object: " + name)
    elif (not path.is_file()
          or hashlib.sha256(path.read_bytes()).digest()
          != hashlib.sha256(git(root, "cat-file", "--filters", revision + ":" + name)).digest()):
        raise ProofError("report differs from its Git object: " + name)
    return entry


def report_paths(root, paths, revision=None):
    if not isinstance(paths, list) or not paths or len(set(paths)) != len(paths):
        raise ProofError('report paths must be a nonempty list without duplicates')
    for name in paths:
        literal_path(name)
        match = re.fullmatch(r'\.planning/phases/([0-9]+(?:\.[0-9]+)*)(?:-[^/]+)?/([0-9]+(?:\.[0-9]+)*)-VERIFICATION\.md', name)
        if not match or match[1] != match[2]:
            raise ProofError('unsupported generated report owner: ' + name)
        # A suffix is not authority: require the actual canonical phase owner.
        owner = name.rsplit('/', 1)[0] + '/' + match[1] + '-CONTEXT.md'
        safe_path(root, owner)
        if revision:
            if tree_entry(root, revision, owner) is None:
                raise ProofError('missing tracked phase owner: ' + owner)
        elif not (Path(root) / owner).is_file():
            raise ProofError('missing phase owner: ' + owner)
        safe_path(root, name)
    return list(paths)


def clean(root):
    if git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all'):
        raise ProofError('worktree/index/untracked state is dirty')


def manifest(root, paths):
    rows = []
    for name in sorted(set(paths)):
        path = safe_path(root, name)
        try:
            info = path.lstat()
        except FileNotFoundError:
            rows.append([name, 'missing'])
            continue
        if not stat.S_ISREG(info.st_mode):
            raise ProofError('unsupported input mode: ' + name)
        rows.append([name, stat.S_IMODE(info.st_mode), hashlib.sha256(path.read_bytes()).hexdigest()])
    return rows


def validate_manifest(root, revision, rows):
    if not isinstance(rows, list):
        raise ProofError('invalid input manifest')
    names = []
    for row in rows:
        if not isinstance(row, list) or len(row) not in (2, 3):
            raise ProofError('invalid input manifest row')
        name = literal_path(row[0]); names.append(name)
        safe_path(root, name)
        entry = tree_entry(root, revision, name)
        if entry is not None:
            # Ask Git for the baseline worktree representation; this respects
            # the unchanged tracked attributes/EOL rules without modifying files.
            content = git(root, 'cat-file', '--filters', revision + ':' + name)
            if len(row) != 3 or hashlib.sha256(content).hexdigest() != row[2]:
                raise ProofError('manifest disagrees with baseline Git object: ' + name)
        elif len(row) == 2 and row[1] != 'missing':
            raise ProofError('invalid absent marker')
    if names != sorted(set(names)):
        raise ProofError('unordered or duplicate manifest rows')


def capture_bundle(root, revision, contract, all_paths, source_paths, configuration, order, index):
    clean(root)
    plain_history(root)
    commit_id(root, revision)
    paths = report_paths(root, contract['report_paths'], revision)
    source = manifest(root, source_paths)
    protected = manifest(root, set(all_paths) | set(source_paths))
    protected = [row for row in protected if row[0] not in paths]
    validate_manifest(root, revision, source)
    validate_manifest(root, revision, protected)
    reports = {name: regular_report(root, revision, name) for name in paths}
    return {'schema': 1, 'contract': contract, 'source_manifest': source,
            'protected_manifest': protected, 'reports': reports,
            'configuration_sha256': configuration, 'order_sha256': order, 'index': index,
            'source_sha256': digest(source), 'protected_sha256': digest(protected)}


def prove_report_only_successor(root, tested_revision, current_revision, approved_paths):
    """Return proof or a fail-closed reason; never execute checks or write files."""
    result = {'qualified': False, 'tested_revision': tested_revision,
              'qualified_revision': current_revision, 'approved_paths': approved_paths,
              'checked_commits': []}
    try:
        root = Path(root).resolve()
        plain_history(root)
        commit_id(root, tested_revision); commit_id(root, current_revision)
        paths = report_paths(root, approved_paths, tested_revision)
        clean(root)
        if git(root, 'rev-parse', 'HEAD').decode().strip() != current_revision:
            raise ProofError('expected head is not current HEAD')
        source_guard = worktree_guard(root)
        if git(root, 'rev-parse', '--is-shallow-repository').strip() != b'false':
            raise ProofError('complete ancestry is unavailable')
        git(root, 'merge-base', '--is-ancestor', tested_revision, current_revision)
        commits = git(root, 'rev-list', '--reverse', '--topo-order',
                      tested_revision + '..' + current_revision).decode().splitlines()
        for commit in commits:
            parents = git(root, 'rev-list', '--parents', '-n', '1', commit).decode().split()[1:]
            if not parents:
                raise ProofError('missing parent history')
            for parent in parents:
                commit_id(root, parent)
                raw = git(root, 'diff-tree', '-r', '--no-renames', '--raw', '-z',
                          '--no-commit-id', parent, commit).split(b'\0')
                for i in range(0, len(raw) - 1, 2):
                    metadata, name = raw[i], os.fsdecode(raw[i + 1])
                    oldmode, newmode, oldoid, newoid, status = metadata[1:].decode().split()
                    if name not in paths:
                        raise ProofError('nonreport touched in intervening history: ' + name)
                    safe_path(root, name)
                    if (status not in ('A', 'M') or newmode not in ('100644', '100755')
                            or (status == 'M' and oldmode != newmode)
                            or (status == 'A' and oldmode != '000000')):
                        raise ProofError('report deletion, rename or unsupported mode change')
                    git(root, 'cat-file', '-e', newoid)
                    if status == 'M':
                        git(root, 'cat-file', '-e', oldoid)
            result['checked_commits'].append(commit)
        for name in paths:
            regular_report(root, current_revision, name)
        clean(root)
        if git(root, 'rev-parse', 'HEAD').decode().strip() != current_revision:
            raise ProofError('HEAD moved during history validation')
        plain_history(root)
        if worktree_guard(root) != source_guard:
            raise ProofError('source/worktree changed during history validation')
        result.update(qualified=True, reason='complete report-only history proved')
    except (OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        result['reason'] = str(exc)
    return result
