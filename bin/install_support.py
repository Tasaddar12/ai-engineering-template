"""Pinned, byte-preserving host exports and journaled installation transactions."""
from __future__ import annotations
import argparse
import base64
import contextlib
import hashlib
import io
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
import tomllib
import uuid

PREFIXES = ('agents/', 'commands/', 'engineer/', 'hooks/', 'scripts/', 'skills/', 'bin/')
BEGIN = '# BEGIN ENGINEER MANAGED'
END = '# END ENGINEER MANAGED'
MANIFEST = 'engineer-install/manifest.json'


class Refusal(Exception):
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code, self.details = code, details


def sha(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return base64.b64encode(value).decode('ascii')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def command(argv, cwd=None):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=120, shell=False)
    if result.returncode:
        raise Refusal('command-failed', result.stderr.decode('utf-8', 'replace')[-12000:], argv=argv)
    return result.stdout


def relative(value):
    path = PurePosixPath(value)
    if not value or path.is_absolute() or '..' in path.parts or any(':' in p or '\\' in p for p in path.parts):
        raise Refusal('unsafe-path', value)
    return path.as_posix()


def safe(root, name):
    path = root.joinpath(*PurePosixPath(relative(name)).parts)
    current = path
    while True:
        if current.is_symlink() or (current.exists() and getattr(current.lstat(), 'st_file_attributes', 0) & 0x400):
            raise Refusal('symlink-refused', str(current))
        if current == root:
            break
        current = current.parent
    if path.exists() and not path.is_file():
        raise Refusal('not-regular-file', str(path))
    return path


def target_root(value):
    candidate = Path(value).expanduser().absolute()
    for part in (candidate, *candidate.parents):
        if part.is_symlink() or (part.exists() and getattr(part.lstat(), 'st_file_attributes', 0) & 0x400):
            raise Refusal('symlink-refused', str(part))
    if candidate.exists() and not candidate.is_dir():
        raise Refusal('invalid-target', str(candidate))
    return candidate.resolve()


def current(root, name):
    path = safe(root, name)
    if not path.exists():
        return {'sha256': None, 'mode': None}
    return {'sha256': sha(path.read_bytes()), 'mode': stat.S_IMODE(path.stat().st_mode)}


def atomic(path, content, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.engineer-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def json_write(path, value):
    atomic(path, json.dumps(value, indent=2, ensure_ascii=False).encode('utf-8') + b'\n')


def snapshot(source, revision):
    repo = Path(source).expanduser().resolve(strict=True)
    if not repo.is_dir():
        raise Refusal('source-not-repository', str(repo))
    pin = command(['git', '-C', str(repo), 'rev-parse', '--verify', revision + '^{commit}']).decode().strip()
    archive = command(['git', '-C', str(repo), 'archive', '--format=tar', pin])
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode='r:') as tree:
        for member in tree:
            if not member.name.startswith(PREFIXES):
                continue
            name = relative(member.name)
            if member.isdir():
                continue
            if not member.isfile():
                raise Refusal('source-link-refused', name)
            if name == 'engineer/RULES.md' or '__pycache__' in PurePosixPath(name).parts or name.endswith(('.pyc', '.pyo')):
                continue
            files[name] = (tree.extractfile(member).read(), 0o755 if member.mode & 0o111 else 0o644)
    if not files.get('engineer/bin/engineer.py', (b'',))[0]:
        raise Refusal('source-runtime-missing', 'Pinned source needs a populated engineer/bin/engineer.py')
    return repo, pin, files


def namespace(host):
    if host not in ('claude', 'codex'):
        raise Refusal('unsupported-host', str(host))
    return '.' + host


def metadata(text, key, fallback):
    match = re.search(r'(?m)^' + re.escape(key) + r':\s*([^\n]+)', text.split('---', 2)[1] if text.startswith('---') else '')
    return match.group(1).strip().strip('\"\'') if match else fallback


def managed_block(original, block, begin=BEGIN, end=END):
    start, stop = begin.encode(), end.encode()
    if original.count(start) != original.count(stop) or original.count(start) > 1:
        raise Refusal('managed-block-drift', 'Ambiguous managed markers; preserve file for manual review')
    if start in original:
        first = original.index(start)
        last = original.index(stop, first) + len(stop)
        return original[:first] + block + original[last:]
    return original + (b'\n' if original and not original.endswith(b'\n') else b'') + block + b'\n'


def adapt(content, host, ns, source_name, findings):
    if not source_name.endswith(('.md', '.sh', '.txt', '.yaml', '.yml', '.toml')):
        return content
    text = content.decode('utf-8')
    # Replace the complete obsolete bootstrap, preserving every surrounding method.
    launcher = ('ENGINEER_RUN=' + json.dumps(str(ns / 'engineer/bin/engineer_run')) + '\n'
                'engineer_run() { sh "$ENGINEER_RUN" "$@"; }\nexport ENGINEER_RUN')
    text = re.sub(r'(?m)^_ENGINEER_SHIM_NAME=.*$', lambda _: launcher, text)
    for directory in ('references', 'templates', 'workflows'):
        text = text.replace('@~/.claude/' + directory + '/', '@' + str(ns / 'engineer' / directory).replace('\\', '/') + '/')
    text = text.replace('@~/.claude/', '@' + str(ns).replace('\\', '/') + '/')
    text = text.replace('~/.claude/engineer/', str(ns / 'engineer').replace('\\', '/') + '/')
    if host == 'codex':
        text = text.replace('.claude/CLAUDE.md', '.codex/AGENTS.md').replace('CLAUDE.md', 'AGENTS.md')
    field_function = ('_engineer_field() { python -I ' + json.dumps(str(ns / 'bin/install_support.py'))
                      + ' json-field "$1" "$2"; }')
    text = re.sub(r'_engineer_field\(\) \{ node -e [^\n]*?; \}', lambda _: field_function, text)
    transforms = Path(__file__).with_name('export_transforms.py')
    if transforms.is_file():
        spec = importlib.util.spec_from_file_location('_engineer_export_transforms', transforms)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        text = module.transform(text, source_name, str(ns / 'engineer/bin/engineer.py'))
    # Dynamic JavaScript and .cjs helpers have no safe general mechanical translation.
    # Keep their complete methods and report exact locations, never fabricate an equivalent.
    fence_marker = None
    shell = False
    for index, line in enumerate(text.splitlines(), 1):
        fence = re.match(r'^\s*(`{3,}|~{3,})(.*)$', line)
        if fence:
            marker, info = fence.groups()
            if fence_marker is None:
                fence_marker = marker
                shell = info.strip() in ('bash', 'sh', 'shell', 'zsh')
            elif marker[0] == fence_marker[0] and len(marker) >= len(fence_marker) and not info.strip():
                fence_marker = None
                shell = False
            continue
        if shell and not line.lstrip().startswith('#') and re.search(r'(?:\bnode\s+(?:-[ep]|["\'])|\.cjs\b)', line):
            # Application-specific examples may legitimately inspect a Node application.
            if source_name.startswith(('commands/', 'skills/', 'engineer/workflows/')):
                findings.append({'path': source_name, 'line': index, 'code': 'unported-runtime-javascript', 'text': line[:400]})
    return text.encode('utf-8')


def exports(source, pin, target, host, scope, no_hooks=False):
    repo, resolved, files = snapshot(source, pin)
    nsname = namespace(host)
    ns = target / nsname
    payload, origins, findings, shared, portable_names = {}, {}, [], set(), {}
    def add(name, data, mode=0o644, origin=None):
        name = relative(name)
        # Windows chmod represents only the read-only attribute. Compare the
        # mode that the filesystem can actually retain, so refreshes are stable.
        if os.name == 'nt':
            mode = 0o666 if mode & stat.S_IWUSR else 0o444
        folded = name.casefold()
        if folded in portable_names and portable_names[folded] != name:
            raise Refusal('export-case-collision', name, other=portable_names[folded])
        portable_names[folded] = name
        if name in payload and payload[name] != (data, mode):
            raise Refusal('export-collision', name)
        payload[name] = (data, mode)
        origins[name] = origin
    for name, (data, mode) in files.items():
        # Canonical skills are rebuilt from the complete matching command when available.
        if name.startswith('skills/') and name.endswith('/SKILL.md'):
            role = PurePosixPath(name).parts[1]
            if 'commands/' + role + '.md' in files:
                continue
        transformed = adapt(data, host, ns, name, findings)
        if host == 'claude' and name.startswith('agents/') and name.endswith('.md') and PurePosixPath(name).name != 'AGENT.md':
            text = transformed.decode('utf-8')
            if text.startswith('---'):
                pieces = text.split('---', 2)
                header = re.sub(r'(?m)^(?:model|effort):[^\n]*\n?', '', pieces[1])
                role = PurePosixPath(name).stem
                defaults = {'scout': 'haiku', 'targeted-fixer': 'haiku', 'executor': 'sonnet', 'planner': 'opus'}
                if role in defaults:
                    header += '\nmodel: ' + defaults[role] + '\n'
                if role == 'planner':
                    header += 'effort: medium\n'
                transformed = ('---' + header + '---' + pieces[2]).encode('utf-8')
        add(nsname + '/' + name, transformed, mode, name)
        if name.startswith('commands/') and name.endswith('.md') and PurePosixPath(name).name != 'COMMAND.md':
            role = PurePosixPath(name).stem
            add(nsname + '/skills/' + role + '/SKILL.md', transformed, 0o644, name)
        if host == 'codex' and name.startswith('agents/') and name.endswith('.md') and PurePosixPath(name).name != 'AGENT.md':
            role = PurePosixPath(name).stem
            text = transformed.decode('utf-8')
            values = {'name': role, 'description': metadata(text, 'description', role), 'developer_instructions': text}
            native = '\n'.join(k + ' = ' + json.dumps(v, ensure_ascii=False) for k, v in values.items()) + '\n'
            tomllib.loads(native)
            add(nsname + '/agents/' + role + '.toml', native.encode(), origin=name)
    entry = (nsname + '/AGENTS.md' if host == 'codex' else nsname + '/CLAUDE.md') if scope == 'global' else ('AGENTS.md' if host == 'codex' else 'CLAUDE.md')
    entry_path = safe(target, entry)
    prior = entry_path.read_bytes() if entry_path.exists() else b''
    block = ('<!-- ENGINEER MANAGED BEGIN -->\nRead the complete installed command catalog at '
             + str(ns / 'commands/COMMAND.md') + ', workflow catalog at ' + str(ns / 'engineer/workflows/WORKFLOW.md')
             + ', and role catalog at ' + str(ns / 'agents/AGENT.md') + '.\nRuntime: '
             + str(ns / 'engineer/bin/engineer_run') + '. Preserve project instructions and explicit phase authority.\n'
             '<!-- ENGINEER MANAGED END -->').encode()
    add(entry, managed_block(prior, block, '<!-- ENGINEER MANAGED BEGIN -->', '<!-- ENGINEER MANAGED END -->'), origin='generated:entry')
    shared.add(entry)
    hook_command = '"' + sys.executable + '" -I "' + str(ns / 'hooks/worktree-path-guard.py') + '" --host ' + host
    if host == 'codex':
        name = nsname + '/config.toml'
        path = safe(target, name)
        original = path.read_bytes() if path.exists() else b''
        tomllib.loads(original.decode('utf-8-sig'))
        lines = [BEGIN]
        for name_ in sorted(p for p in payload if p.endswith('/SKILL.md')):
            lines.extend(['[[skills.config]]', 'path = ' + json.dumps(str(target / name_)), 'enabled = true'])
        if not no_hooks:
            lines.extend(['[[hooks.PreToolUse]]', 'matcher = "Agent|Task|Write|Edit|MultiEdit|NotebookEdit|apply_patch"',
                          '[[hooks.PreToolUse.hooks]]', 'type = "command"', 'command = ' + json.dumps(hook_command), 'timeout = 10'])
        lines.append(END)
        result = managed_block(original, '\n'.join(lines).encode())
        tomllib.loads(result.decode('utf-8-sig'))
        add(name, result, origin='generated:codex-config')
        shared.add(name)
    elif not no_hooks:
        name = nsname + '/settings.json'
        path = safe(target, name)
        settings = json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else {}
        hooks = settings.setdefault('hooks', {})
        entries = hooks.setdefault('PreToolUse', [])
        # Remove only this install's own exact guard registration, never other hooks.
        entries[:] = [e for e in entries if not any(h.get('command') == hook_command for h in e.get('hooks', []))]
        entries.append({'matcher': 'Agent|Task|Write|Edit|MultiEdit|NotebookEdit|apply_patch',
                        'hooks': [{'type': 'command', 'command': hook_command, 'timeout': 10}]})
        add(name, json.dumps(settings, indent=2, ensure_ascii=False).encode() + b'\n', origin='generated:claude-settings')
        shared.add(name)
    return {'source': str(repo), 'revision': resolved, 'payload': payload, 'origins': origins,
            'findings': findings, 'shared': shared}


def inventory(root, mode='installed'):
    """Inventory regular files; preserve unmanaged additions instead of deleting them."""
    root = Path(root)
    result = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob('*')):
        if path.is_symlink():
            raise Refusal('inventory-symlink', str(path))
        if path.is_file() and 'engineer-install' not in path.relative_to(root).parts:
            result[path.relative_to(root).as_posix()] = {'sha256': sha(path.read_bytes()), 'mode': stat.S_IMODE(path.stat().st_mode)}
    return result


def legacy_cache(name):
    path = PurePosixPath(name)
    return '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo')


def legacy_inventory(root, host):
    """Capture retained legacy sources independently of the active runtime."""
    result = {}
    for name in ('.ai', namespace(host) + '/runtime'):
        directory = root / name
        if directory.is_symlink():
            raise Refusal('migration-symlink', str(directory))
        if not directory.exists():
            continue
        for path in sorted(directory.rglob('*')):
            if path.is_symlink():
                raise Refusal('migration-symlink', str(path))
            if path.is_file():
                relative_name = path.relative_to(root).as_posix()
                if legacy_cache(relative_name):
                    continue
                result[relative_name] = current(root, relative_name)
    return result


def plan_update(source, ref, target, host, scope='local', no_hooks=False, kind='update'):
    target = target_root(target)
    ns = namespace(host)
    manifest_name = ns + '/' + MANIFEST
    manifest_path = safe(target, manifest_name)
    old = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'files': {}}
    export = exports(source, ref, target, host, scope, no_hooks)
    entries = []
    for name, (data, mode) in sorted(export['payload'].items()):
        before = current(target, name)
        owned = old.get('files', {}).get(name, {})
        after = sha(data)
        conflict = before['sha256'] is not None and before['sha256'] != after and before['sha256'] != owned.get('sha256') and name not in export['shared']
        entries.append({'path': name, 'before': before, 'sha256': after, 'mode': mode,
                        'content': encoded(data), 'source_path': export['origins'][name],
                        'action': 'unchanged' if before['sha256'] == after and before['mode'] == mode else 'conflict' if conflict else 'write',
                        'resolution': 'preserve' if conflict else 'apply'})
    legacy = legacy_inventory(target, host)
    reviewed_legacy = old.get('migration', {})
    if kind != 'migrate' and legacy and (not reviewed_legacy.get('complete') or reviewed_legacy.get('sources') != legacy):
        export['findings'].append({'code': 'migration-required', 'path': str(target), 'message': 'Preview migration before altering a legacy installation'})
    result = {'schema': 1, 'kind': kind, 'source': export['source'], 'revision': export['revision'],
              'target': str(target), 'host': host, 'scope': scope, 'no_hooks': no_hooks,
              'manifest_before': current(target, manifest_name), 'entries': entries,
              'retired_preserved': sorted(set(old.get('files', {})) - {e['path'] for e in entries}),
              'findings': export['findings'], 'complete': not export['findings']}
    result['exporter'] = {'install_support_sha256': sha(Path(__file__).read_bytes())}
    transforms = Path(__file__).with_name('export_transforms.py')
    if transforms.is_file():
        result['exporter']['export_transforms_sha256'] = sha(transforms.read_bytes())
    result['snapshot_token'] = sha(canonical(result))
    return result


def migration_plan(source, ref, target, host, scope='local', no_hooks=False):
    plan = plan_update(source, ref, target, host, scope, no_hooks, 'migrate')
    root = Path(plan['target'])
    ns = namespace(host)
    destinations = {e['path'] for e in plan['entries']}
    # Keep the complete older runtime and its sibling hooks together. Mixing
    # its lib package into the active engine can silently select incompatible
    # modules; moving hooks alone also breaks their sibling-runtime imports.
    mapping = [('.ai/runtime', ns + '/legacy/runtime'), (ns + '/runtime', ns + '/legacy/runtime'),
               ('.ai/templates', ns + '/engineer/templates'), ('.ai/workflows', ns + '/engineer/workflows'),
               ('.ai/references', ns + '/engineer/references'), ('.ai/agents', ns + '/agents'),
               ('.ai/commands', ns + '/commands'), ('.ai/hooks', ns + '/legacy/hooks'), ('.ai/skills', ns + '/skills'),
               ('.ai', ns)]
    legacy_seen = set()
    for old_root, new_root in mapping:
        directory = root / old_root
        if directory.is_symlink():
            raise Refusal('migration-symlink', str(directory))
        if not directory.exists():
            continue
        for path in sorted(directory.rglob('*')):
            if path.is_symlink():
                raise Refusal('migration-symlink', str(path))
            if not path.is_file():
                continue
            old_name = path.relative_to(root).as_posix()
            if legacy_cache(old_name):
                continue
            # Specific relocations win over the catch-all for custom .ai assets.
            if old_name in legacy_seen:
                continue
            legacy_seen.add(old_name)
            name = new_root + '/' + path.relative_to(directory).as_posix()
            data = path.read_bytes()
            disposition = 'no-text-transform'
            disposition_reason = 'non-text-suffix'
            # Preserve exact original bytes in backup; only textual path references change in destination.
            if path.suffix in ('.md', '.sh', '.py', '.yaml', '.toml', '.json', '.txt'):
                try:
                    text = data.decode('utf-8')
                except UnicodeDecodeError:
                    # A text-like extension does not establish an encoding.
                    # The reviewed mapping explicitly exposes this exact copy.
                    disposition_reason = 'non-utf8-bytes'
                else:
                    for old_prefix, new_prefix in sorted(mapping, key=lambda pair: -len(pair[0])):
                        text = text.replace(old_prefix + '/', str(root / new_prefix).replace('\\', '/') + '/')
                    text = text.replace('phase_run', 'engineer_run')
                    data = text.encode('utf-8')
                    disposition = 'utf8-reference-relocation'
                    disposition_reason = 'utf8-text'
            before = current(root, name)
            backup_only = name in destinations
            mode = stat.S_IMODE(path.stat().st_mode)
            identical = before == {'sha256': sha(data), 'mode': mode}
            plan['entries'].append({'path': name, 'legacy_path': old_name, 'legacy_before': current(root, old_name),
                                    'before': before, 'sha256': sha(data), 'content': encoded(data),
                                    'mode': mode, 'source_path': old_name,
                                    'text_transform': disposition, 'text_transform_reason': disposition_reason,
                                    'action': 'backup-only' if backup_only else 'unchanged' if identical else 'conflict' if before['sha256'] else 'write',
                                    'resolution': 'backup' if backup_only else 'apply' if identical else 'preserve' if before['sha256'] else 'apply'})
            destinations.add(name)
    plan.pop('snapshot_token', None)
    plan['snapshot_token'] = sha(canonical(plan))
    return plan


@contextlib.contextmanager
def install_lock(root, host):
    directory = root / namespace(host) / 'engineer-install'
    path = safe(root, str(directory.relative_to(root) / 'install.lock').replace('\\', '/'))
    directory.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        handle.write(b'0')
        handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Refusal('install-locked', str(directory)) from exc
        try:
            yield directory
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def rollback(root, transaction):
    journal = json.loads((transaction / 'journal.json').read_text(encoding='utf-8'))
    # Validate the whole rollback before restoring its first file.
    for entry in journal['changes']:
        actual = current(root, entry['path'])['sha256']
        if actual not in (entry['after'], entry['before']['sha256']):
            raise Refusal('rollback-drift', entry['path'], transaction=str(transaction))
        if entry['before']['sha256'] is not None:
            if sha((transaction / entry['backup']).read_bytes()) != entry['before']['sha256']:
                raise Refusal('backup-corrupt', entry['path'])
    for entry in reversed(journal['changes']):
        path = safe(root, entry['path'])
        actual = current(root, entry['path'])['sha256']
        if actual not in (entry['after'], entry['before']['sha256']):
            raise Refusal('rollback-drift', entry['path'], transaction=str(transaction))
        if current(root, entry['path']) == entry['before']:
            continue
        if entry['before']['sha256'] is None:
            path.unlink(missing_ok=True)
        else:
            backup = transaction / entry['backup']
            content = backup.read_bytes()
            if sha(content) != entry['before']['sha256']:
                raise Refusal('backup-corrupt', str(backup))
            atomic(path, content, entry['before']['mode'])
    journal['status'] = 'rolled-back'
    json_write(transaction / 'journal.json', journal)
    return {'rolled_back': True, 'transaction': str(transaction)}


def apply(plan, selected=None):
    if plan.get('schema') != 1 or plan.get('kind') not in ('install', 'update', 'migrate'):
        raise Refusal('invalid-plan', 'Unsupported plan schema or kind')
    if plan['kind'] == 'migrate' and not selected:
        raise Refusal('migration-selection-required', 'Migration requires explicit --select paths from the reviewed mapping')
    root = target_root(plan['target'])
    host = plan['host']
    # Re-resolve the captured immutable revision and regenerate complete exports from it.
    fresh = (migration_plan if plan['kind'] == 'migrate' else plan_update)(
        plan['source'], plan['revision'], root, host, plan['scope'], plan['no_hooks'])
    if fresh['findings']:
        raise Refusal('export-blocked', 'Resolve unsupported runtime exports before applying', findings=fresh['findings'])
    if fresh['exporter'] != plan.get('exporter'):
        raise Refusal('exporter-drift', 'Preview again with this exact exporter version')
    expected = { (e['path'], e.get('legacy_path', '')): e for e in fresh['entries'] }
    if len(expected) != len(plan['entries']):
        raise Refusal('plan-drift', 'Entry set changed')
    for entry in plan['entries']:
        actual = expected.get((entry['path'], entry.get('legacy_path', '')))
        if not actual or any(entry.get(k) != actual.get(k) for k in ('sha256', 'mode', 'content', 'before', 'legacy_before', 'action', 'text_transform', 'text_transform_reason')):
            raise Refusal('plan-drift', entry['path'])
    if fresh['manifest_before'] != plan['manifest_before']:
        raise Refusal('manifest-drift', 'Installed ownership manifest changed')
    requested = set(selected) if selected else {e['path'] for e in plan['entries'] if e['action'] != 'conflict'}
    unknown = requested - {e['path'] for e in plan['entries']}
    if unknown:
        raise Refusal('unknown-selection', str(sorted(unknown)))
    entries = [e for e in plan['entries'] if e['path'] in requested]
    if any(e['action'] == 'conflict' and e.get('resolution') != 'backup-and-replace' for e in entries):
        raise Refusal('customization-conflict', 'Select an explicit backup-and-replace resolution in the reviewed plan, or preserve the path')
    with install_lock(root, host) as state:
        # Revalidate under ownership; no stale preview can write.
        for entry in plan['entries']:
            if current(root, entry['path']) != entry['before']:
                raise Refusal('target-drift', entry['path'])
            if entry.get('legacy_path') and current(root, entry['legacy_path']) != entry['legacy_before']:
                raise Refusal('legacy-drift', entry['legacy_path'])
        manifest_name = namespace(host) + '/' + MANIFEST
        if current(root, manifest_name) != plan['manifest_before']:
            raise Refusal('manifest-drift', manifest_name)
        for journal_path in state.glob('backups/*/journal.json'):
            if json.loads(journal_path.read_text(encoding='utf-8'))['status'] not in ('committed', 'rolled-back'):
                raise Refusal('transaction-recovery-required', str(journal_path.parent))
        transaction = state / 'backups' / uuid.uuid4().hex
        safe(root, str((transaction / 'journal.json').relative_to(root)).replace('\\', '/'))
        transaction.mkdir(parents=True)
        json_write(transaction / 'reviewed-plan.json', plan)
        journal = {'schema': 1, 'target': str(root), 'status': 'preparing', 'changes': [], 'legacy_backups': []}
        manifest_path = safe(root, manifest_name)
        manifest = json.loads(manifest_path.read_text(encoding='utf-8')) if manifest_path.exists() else {'files': {}}
        manifest.update(schema=1, source=plan['source'], revision=plan['revision'], host=host,
                        scope=plan['scope'], exporter=plan['exporter'])
        writes = {}
        for index, entry in enumerate(entries):
            if entry.get('legacy_path'):
                original = safe(root, entry['legacy_path']).read_bytes()
                atomic(transaction / ('legacy-' + str(index)), original, entry['legacy_before']['mode'])
                journal['legacy_backups'].append({'path': entry['legacy_path'], 'backup': 'legacy-' + str(index),
                                                  'before': entry['legacy_before'], 'destination': entry['path']})
            if entry['action'] == 'backup-only' or entry.get('resolution') == 'preserve':
                continue
            content = base64.b64decode(entry['content'], validate=True)
            if sha(content) != entry['sha256']:
                raise Refusal('plan-content-corrupt', entry['path'])
            writes[entry['path']] = (content, entry['mode'])
            manifest['files'][entry['path']] = {'sha256': entry['sha256'], 'mode': entry['mode'], 'source_path': entry['source_path']}
        manifest['complete'] = not any(e['action'] not in ('unchanged', 'backup-only') and e['path'] not in writes for e in plan['entries'])
        if plan['kind'] == 'migrate':
            legacy_entries = [e for e in plan['entries'] if e.get('legacy_path')]
            manifest['migration'] = {
                'complete': all(e['path'] in requested and (e['action'] == 'backup-only' or e['path'] in writes)
                                for e in legacy_entries),
                'sources': {e['legacy_path']: e['legacy_before'] for e in legacy_entries},
                'runtime_layout': 'isolated-legacy-runtime-and-hooks',
            }
        writes[manifest_name] = (json.dumps(manifest, indent=2, ensure_ascii=False).encode() + b'\n', 0o644)
        for index, (name, (content, mode)) in enumerate(writes.items()):
            before = current(root, name)
            backup = 'file-' + str(index)
            if before['sha256'] is not None:
                atomic(transaction / backup, safe(root, name).read_bytes(), before['mode'])
            journal['changes'].append({'path': name, 'before': before, 'after': sha(content), 'backup': backup, 'mode': mode})
        journal['status'] = 'applying'
        json_write(transaction / 'journal.json', journal)
        try:
            for name, (content, mode) in writes.items():
                expected_before = next(e['before'] for e in journal['changes'] if e['path'] == name)
                if current(root, name) != expected_before:
                    raise Refusal('target-drift-during-apply', name, transaction=str(transaction))
                atomic(safe(root, name), content, mode)
            journal['status'] = 'committed'
            json_write(transaction / 'journal.json', journal)
        except BaseException:
            rollback(root, transaction)
            raise
        return {'applied': True, 'complete': manifest['complete'], 'source': plan['source'], 'revision': plan['revision'],
                'host': host, 'target': str(root), 'files': list(writes), 'backup': str(transaction), 'legacy_preserved': True,
                'verification': 'not-executed'}


def parser(description):
    result = argparse.ArgumentParser(description=description)
    result.add_argument('--source', help='Local Git source repository; never fetched implicitly')
    result.add_argument('--ref', help='Required Git revision, captured as an immutable commit')
    result.add_argument('--target', help='Explicit project root (--local) or home root (--global)')
    result.add_argument('--host', choices=('claude', 'codex'))
    scope = result.add_mutually_exclusive_group()
    scope.add_argument('--local', action='store_const', dest='scope', const='local')
    scope.add_argument('--global', action='store_const', dest='scope', const='global')
    result.add_argument('--no-hooks', action='store_true')
    result.add_argument('--skip-deps', action='store_true', help='Compatibility flag: runtime uses only Python standard library')
    result.add_argument('--dry-run', action='store_true')
    result.add_argument('--plan', help='Write complete preview JSON to this explicit file')
    result.add_argument('--apply', metavar='PLAN', help='Apply a previously reviewed plan')
    result.add_argument('--reviewed-plan-sha256', help='SHA-256 of the exact reviewed plan file bytes')
    selection = result.add_mutually_exclusive_group()
    selection.add_argument('--select', action='append', help='Exact target-relative path; repeat for selected paths')
    selection.add_argument('--select-all', action='store_true', help='Explicitly select every path in the exact reviewed plan')
    result.add_argument('--rollback', help='Exact prior transaction backup directory')
    return result


def cli(kind, argv=None):
    # Plans are a UTF-8 interchange format even on Windows consoles whose
    # default code page cannot represent the target's path or source prose.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    args_parser = parser('Pinned Engineer ' + kind + ': full exports, guarded backups and no destructive cleanup')
    if kind == 'install':
        args_parser.add_argument('--update', action='store_true')
        args_parser.add_argument('--migrate-existing', action='store_true')
    args = args_parser.parse_args(argv)
    try:
        if args.apply:
            if args.dry_run or args.rollback:
                raise Refusal('incompatible-options', '--apply cannot combine with --dry-run or --rollback')
            raw = Path(args.apply).read_bytes()
            if not args.reviewed_plan_sha256 or sha(raw) != args.reviewed_plan_sha256:
                raise Refusal('review-token-mismatch', 'Supply the SHA-256 of the exact reviewed plan file bytes')
            reviewed = json.loads(raw)
            selected = [e['path'] for e in reviewed['entries']] if args.select_all else args.select
            result = apply(reviewed, selected)
        elif args.rollback:
            if not args.target or not args.host:
                raise Refusal('rollback-target-required', 'Specify --target and --host')
            target = target_root(args.target)
            transaction = Path(args.rollback).resolve()
            allowed = target / namespace(args.host) / 'engineer-install/backups'
            if transaction.parent != allowed or not transaction.is_dir() or transaction.is_symlink():
                raise Refusal('rollback-path-refused', str(transaction))
            with install_lock(target, args.host):
                journal = json.loads((transaction / 'journal.json').read_text(encoding='utf-8'))
                if journal.get('target') != str(target):
                    raise Refusal('rollback-target-mismatch', str(transaction))
                result = rollback(target, transaction)
        else:
            if not all((args.source, args.ref, args.target, args.host, args.scope)):
                raise Refusal('explicit-install-context-required', 'Specify --source, --ref, --target, --host and --local or --global')
            operation = 'migrate' if kind == 'migrate' or getattr(args, 'migrate_existing', False) else 'update' if kind == 'update' or getattr(args, 'update', False) else 'install'
            maker = migration_plan if operation == 'migrate' else plan_update
            result = maker(args.source, args.ref, args.target, args.host, args.scope, args.no_hooks)
            result['kind'] = operation
            result.pop('snapshot_token', None)
            result['snapshot_token'] = sha(canonical(result))
            if args.plan:
                json_write(Path(args.plan), result)
                result['plan_file'] = str(Path(args.plan).absolute())
                result['reviewed_plan_sha256'] = sha(Path(args.plan).read_bytes())
            if operation == 'install' and not args.dry_run and not args.plan:
                result = apply(result, args.select)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({'error': exc.code if isinstance(exc, Refusal) else 'operation-failed',
                          'message': str(exc), **(exc.details if isinstance(exc, Refusal) else {})}), file=sys.stderr)
        return 2


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'json-field':
        value = json.loads(sys.argv[2]).get(sys.argv[3])
        def js_string(item):
            if item is None:
                return ''
            if isinstance(item, bool):
                return str(item).lower()
            if isinstance(item, list):
                return ','.join(js_string(x) for x in item)
            if isinstance(item, dict):
                return '[object Object]'
            return str(item)
        print(js_string(value), end='')
    else:
        raise SystemExit(cli('update'))
