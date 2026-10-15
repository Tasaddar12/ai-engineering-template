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


def tokens(command, grammar):
    if grammar == 'bash':
        command = command.replace('\\\r\n', '').replace('\\\n', '')
    lexer = shlex.shlex(command, posix=True, punctuation_chars=';&|')
    lexer.escape = '\\' if grammar == 'bash' else ('`' if grammar == 'powershell' else '^')
    lexer.whitespace_split = True
    lexer.commenters = ''
    return list(lexer)


def outer_commands(command, grammar):
    """Split only unquoted outer operators, retaining each command's raw text."""
    if grammar == 'bash':
        command = command.replace('\\\r\n', '').replace('\\\n', '')
    escape = '\\' if grammar == 'bash' else ('`' if grammar == 'powershell' else '^')
    result, start, index, quote = [], 0, 0, None
    while index < len(command):
        char = command[index]
        if char == escape and quote != "'":
            index += 2
            continue
        if quote:
            if char == quote:
                if grammar != 'bash' and index + 1 < len(command) and command[index + 1] == quote:
                    index += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char in ';&|\r\n':
            if command[start:index].strip():
                result.append(command[start:index])
            start = index + 1
        index += 1
    if quote:
        raise ValueError('Unterminated shell quote; cannot inspect prospective commit')
    if command[start:].strip():
        result.append(command[start:])
    return result


def segments(command, grammar, depth=0):
    if depth > 32:
        raise ValueError('Shell wrapper nesting exceeds the supported inspection boundary')
    result = []
    # Outer segmentation precedes wrapper unwrapping: trailing/leading commands
    # are never joined into a wrapper's actual -c script argument.
    for part in outer_commands(command, grammar):
        values = tokens(part, grammar)
        if grammar == 'bash' and values[:2] not in (['command', '-v'], ['command', '-V']):
            while values and values[0] in ('command', 'env', 'exec', 'time', '!'):
                values = values[1:]
                if values and values[0] == '--':
                    values = values[1:]
        if not values:
            continue
        wrapper = Path(values[0]).name.lower().removesuffix('.exe')
        if wrapper in ('bash', 'sh', 'powershell', 'pwsh', 'cmd'):
            if len(values) == 2 and values[1].lower() in ('--version', '--help', '-version', '-help', '-h', '/?'):
                continue  # These diagnostic invocations have no inline script.
            switches = ('/c',) if wrapper == 'cmd' else (('-command', '-c') if wrapper in ('powershell', 'pwsh') else ('-c', '-lc', '-cl'))
            selected = next((i for i, value in enumerate(values[1:], 1) if value.lower() in switches), None)
            if selected is None:
                if any('commit' in value for value in values):
                    raise ValueError('Unsupported inline shell wrapper; use one explicit -c/-Command script argument')
                result.append((grammar, values))
                continue
            if selected + 1 >= len(values):
                raise ValueError('Missing inline shell script; cannot inspect prospective commit')
            if wrapper not in ('bash', 'sh') and selected + 2 != len(values):
                raise ValueError('Unsupported inline shell wrapper arguments; quote one complete script')
            nested = 'bash' if wrapper in ('bash', 'sh') else ('cmd' if wrapper == 'cmd' else 'powershell')
            result.extend(segments(values[selected + 1], nested, depth + 1))
        else:
            result.append((grammar, values))
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
    takes_value = {'--message', '--file', '--reuse-message', '--reedit-message',
                   '--author', '--date', '--cleanup', '--trailer', '--fixup', '--squash'}
    unsupported = False
    while index < len(args):
        value = args[index]
        if value == '--':
            paths.extend(args[index + 1:])
            break
        if value == '--only':
            mode = 'only'
        elif value == '--all':
            mode = 'all'
        elif value in ('--include', '--interactive', '--patch') or value.startswith('--pathspec-'):
            unsupported = True
        elif value in takes_value:
            index += 1
            unsupported = unsupported or index >= len(args)
        elif value.startswith('--'):
            pass  # Attached long-option values remain inside their option token.
        elif value.startswith('-') and len(value) > 1:
            # Scan flags only until the first argument-consuming option. Its
            # remaining characters are an attached argument, including digits,
            # spaces, punctuation and letters that happen to name other flags.
            for offset, flag in enumerate(value[1:], 1):
                if flag == 'a':
                    mode = 'all'
                elif flag == 'o':
                    mode = 'only'
                elif flag in ('i', 'p'):
                    unsupported = True
                elif flag in ('m', 'F', 'C', 'c'):
                    if offset + 1 == len(value):
                        index += 1
                        unsupported = unsupported or index >= len(args)
                    break
                elif flag == 'S':
                    break  # Optional attached signing-key argument consumes the rest.
        else:
            paths.append(value)
        index += 1
    if paths and mode == 'index':
        mode = 'only'
    return mode, paths, unsupported


def inspect(command, cwd, grammar):
    additions = []
    ambiguous = False
    for grammar, values in segments(command, grammar):
        # Harmless diagnostics do not execute their textual git arguments.
        if values[0].lower() in ('echo', 'printf', 'write-output', 'get-command', 'which', 'where'):
            if grammar == 'bash' and ('$' + '(' in command or '`' in command) and 'commit' in command:
                raise VerbError('Unsupported command substitution around commit; use a separate Git command.', integrity.CODE)
            continue
        if grammar == 'bash':
            if values[:2] in (['command', '-v'], ['command', '-V']):
                continue
            while values and values[0] in ('command', 'env', 'exec', 'time', '!'):
                values = values[1:]
                if values and values[0] == '--':
                    values = values[1:]
            if not values:
                continue
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
                if not specs and not any(arg in ('-A', '--all', '-u', '--update') for arg in args):
                    # Bare git add is a no-op, not an implicit add of every path.
                    continue
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
        if unsupported:
            raise VerbError('Unsupported interactive/include/pathspec-file prospective planning commit (issue_refs cannot be inspected safely); stage separately and use a plain commit.', integrity.CODE)
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
                # Since Git 2, -A/-u without a pathspec is repository-wide,
                # including when the native command starts in a subdirectory.
                added = changed_worktree(add_cwd if add_specs else root, add_globals, add_specs, tracked)
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
        shell = str(data.get('shell') or '').lower()
        grammar = ('bash' if payload.get('tool_name') == 'Bash' or 'bash' in shell or shell.endswith('/sh')
                   else ('cmd' if shell.endswith(('cmd', 'cmd.exe')) else ('powershell' if os.name == 'nt' else 'bash')))
        if isinstance(command, list) and all(isinstance(arg, str) for arg in command):
            command = shlex.join(command)
            grammar = 'bash'  # quoting an existing argv, not inferring a shell
        if not isinstance(command, str):
            return 0
        inspect(command, data.get('cwd') or payload.get('cwd') or os.getcwd(), grammar)
        return 0
    except (VerbError, OSError, ValueError, UnicodeError) as exc:
        print('planning-integrity: ' + str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        # Native hosts distinguish deliberate denial (2) from a hook crash (1).
        # Never let an unexpected inspection defect silently allow a commit.
        print('planning-integrity: inspection failed (' + type(exc).__name__
              + '); commit denied. Use planning.integrity to diagnose the selected records.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
