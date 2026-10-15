#!/usr/bin/env python3
"""Read-only native PreToolUse prospective Git commit checker (denial exit 2)."""
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# Both source .ai/hooks and installed .codex|.claude/hooks have sibling runtime.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'runtime'))
try:
    from lib import planning_integrity as integrity
    from lib.results import VerbError
except ImportError as exc:
    print('planning-integrity: installed sibling runtime and PyYAML are required: ' + str(exc), file=sys.stderr)
    raise SystemExit(2)


def tokens(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|')
    lexer.whitespace_split = True
    lexer.commenters = ''
    return list(lexer)


def segments(command):
    values = tokens(command)
    if values and Path(values[0]).name.lower().removesuffix('.exe') in ('bash', 'sh', 'powershell', 'pwsh', 'cmd'):
        for index, value in enumerate(values[1:], 1):
            if value.lower() in ('-c', '-lc', '-command', '/c'):
                remaining = values[index + 1:]
                return segments(remaining[0] if len(remaining) == 1 else shlex.join(remaining))
    result, current = [], []
    for value in values:
        if value in ('&&', ';', '||', '|', '&'):
            if current:
                result.append(current)
            current = []
        else:
            current.append(value)
    if current:
        result.append(current)
    return result


def git_command(values, cwd):
    if not values or Path(values[0]).name.lower().removesuffix('.exe') != 'git':
        return None
    args, index = [], 1
    while index < len(values):
        value = values[index]
        if value in ('-C', '-c', '--git-dir', '--work-tree'):
            if index + 1 >= len(values):
                return None
            if value == '-C':
                cwd = (Path(cwd) / values[index + 1]).resolve()
            else:
                args.extend(values[index:index + 2])
            index += 2
        elif value.startswith(('--git-dir=', '--work-tree=', '--namespace=')) or value in ('--no-pager', '--no-optional-locks'):
            args.append(value)
            index += 1
        else:
            return cwd, args, value, values[index + 1:]
    return None


def changed_worktree(cwd, globals_, pathspec=(), tracked=False):
    # ls-files matches Git pathspecs and returns index identities. --others is
    # included only for a preceding git add, never commit --all/--only.
    args = ['ls-files', '-z', '--full-name', '--cached']
    if not tracked:
        args += ['--others', '--exclude-standard']
    return set(integrity.names(cwd, *globals_, *args, '--', *pathspec))


def commit_options(args):
    paths, mode, index = [], 'index', 0
    takes_value = {'-m', '--message', '-F', '--file', '-C', '--reuse-message', '-c', '--reedit-message',
                   '--author', '--date', '--cleanup', '--trailer', '--fixup', '--squash', '--pathspec-from-file'}
    unsupported = False
    while index < len(args):
        value = args[index]
        if value == '--':
            paths.extend(args[index + 1:])
            break
        if value in ('--only', '-o'):
            mode = 'only'
        elif value in ('--all', '-a') or (re.fullmatch(r'-[a-zA-Z]+', value) and 'a' in value[1:].split('m', 1)[0] and value not in takes_value):
            mode = 'all'
        elif value in ('--include', '-i', '--interactive', '--patch', '-p') or value.startswith('--pathspec-'):
            unsupported = True
        elif value in takes_value:
            index += 1
        elif value.startswith('-'):
            pass
        else:
            paths.append(value)
        index += 1
    if paths and mode == 'index':
        mode = 'only'
    return mode, paths, unsupported


def inspect(command, cwd):
    additions = []
    ambiguous = False
    for values in segments(command):
        if values and not git_command(values, cwd) and any(Path(value).name.lower().removesuffix('.exe') == 'git' for value in values) and 'commit' in values:
            raise VerbError('Unsupported Git commit prefix or environment; run a separate plain Git commit.', integrity.CODE)
        if values[0].lower() in ('cd', 'set-location') and len(values) == 2:
            cwd = (Path(cwd) / values[1]).resolve()
            continue
        parsed = git_command(values, cwd)
        if not parsed:
            ambiguous = True
            continue
        target, globals_, operation, args = parsed
        if operation == 'add':
            # Exact paths, -A and -u have deterministic working-tree bytes.
            if any(arg.startswith('-') and arg not in ('--', '-A', '--all', '-u', '--update') for arg in args):
                ambiguous = True
            else:
                specs = [arg for arg in args if arg != '--' and not arg.startswith('-')]
                additions.append((target, globals_, specs, '-u' in args or '--update' in args))
            continue
        if operation != 'commit':
            if 'commit' in args:
                raise VerbError('Unsupported Git global options before commit; use explicit supported -C/-c options.', integrity.CODE)
            if operation not in ('status', 'diff', 'log', 'show', 'rev-parse'):
                ambiguous = True
            continue
        if ambiguous:
            raise VerbError('Ambiguous shell mutation before Git commit; separate the commands for safe issue_refs inspection.', integrity.CODE)
        root = Path(integrity.git_read(target, *globals_, 'rev-parse', '--show-toplevel').decode('utf-8').strip())
        mode, specs, unsupported = commit_options(args)
        staged = set(integrity.names(target, *globals_, 'diff', '--cached', '--name-only', '--diff-filter=ACMRT', '-z'))
        work = set()
        if mode == 'only':
            # Paths are relative to native command cwd; queries emit repo paths.
            work = changed_worktree(target, globals_, specs, tracked=True)
            staged = set()
        elif mode == 'all':
            work = set(integrity.names(target, *globals_, 'diff', '--name-only', '--diff-filter=ACDMRT', '-z'))
        for add_cwd, add_globals, add_specs, tracked in additions:
            if Path(integrity.git_read(add_cwd, *add_globals, 'rev-parse', '--show-toplevel').decode().strip()) == root:
                added = changed_worktree(add_cwd, add_globals, add_specs, tracked)
                if mode != 'only':
                    work.update(added)
        relevant = {path for path in staged | work if integrity.record_kind(path)}
        if relevant and (ambiguous or unsupported):
            raise VerbError('Ambiguous prospective planning commit (issue_refs and other metadata cannot be inspected safely). '
                            'Use a separate git add, then a plain commit, --only with explicit paths, or --all.', integrity.CODE)
        for path in sorted(relevant):
            if path in work:
                file = root / path
                if not file.exists():
                    continue  # Intended deletion has no new document to validate.
                # User clean filters can transform YAML arbitrarily. Refuse rather
                # than claim working bytes equal commit bytes without executing it.
                attr = integrity.git_read(root, *globals_, 'check-attr', 'filter', '--', path).decode().strip()
                if not attr.endswith((': unspecified', ': unset')):
                    raise VerbError(path + ': configured clean filter prevents safe prospective-byte inspection; stage separately.', integrity.CODE)
                content = file.read_bytes().decode('utf-8-sig')
                historical = subprocess.run(['git', *globals_, 'show', 'HEAD:' + path], cwd=root, capture_output=True)
                if historical.returncode == 0 and content.replace('\r\n', '\n') == historical.stdout.decode('utf-8-sig').replace('\r\n', '\n'):
                    continue  # Explicit unchanged legacy paths are not a migration sweep.
            else:
                content = integrity.git_read(root, *globals_, 'show', ':' + path).decode('utf-8-sig')
            integrity.validate_record(path, content)


def main():
    try:
        payload = json.load(sys.stdin)
        data = payload.get('tool_input') or {}
        command = data.get('command') or data.get('cmd') or payload.get('command') or payload.get('cmd') or ''
        if isinstance(command, list) and all(isinstance(arg, str) for arg in command):
            command = shlex.join(command)
        if not isinstance(command, str) or not re.search(r'\bgit(?:\.exe)?\b.*\bcommit\b', command, re.S | re.I):
            return 0
        inspect(command, data.get('cwd') or payload.get('cwd') or os.getcwd())
        return 0
    except (VerbError, OSError, ValueError, UnicodeError) as exc:
        print('planning-integrity: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
