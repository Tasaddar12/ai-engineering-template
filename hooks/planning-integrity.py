"""Strict planning integrity preflight for prospective commit commands."""
import shlex
from pathlib import Path
import subprocess
import sys
import tempfile
from hook_common import read_event, root_for, query


def commit_arguments(command):
    try:
        if isinstance(command, list):
            words = command
        elif isinstance(command, str):
            lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
            lexer.whitespace_split = True
            words = list(lexer)
        else:
            return None
    except (ValueError, TypeError):
        return None
    for index, word in enumerate(words):
        if isinstance(word, str) and Path(word).name.lower() in ("git", "git.exe") and (index == 0 or words[index - 1] in (";", "&&", "||", "|")):
            remaining = words[index + 1:]
            cursor = 0
            while cursor < len(remaining):
                token = remaining[cursor]
                if token in ("-C", "-c", "--git-dir", "--work-tree"):
                    cursor += 2
                elif token.startswith("-"):
                    cursor += 1
                else:
                    if token != "commit":
                        break
                    tail = remaining[cursor + 1:]
                    end = next((i for i, item in enumerate(tail) if item in (";", "&&", "||", "|")), len(tail))
                    return remaining[:cursor], tail[:end]
    return None


def prospective_commit(command):
    return commit_arguments(command) is not None


def commit_selection(arguments):
    only, include, all_tracked, paths = False, False, False, []
    takes_value = {"-m", "--message", "-F", "--file", "-C", "--reuse-message", "-c", "--reedit-message", "--author", "--date", "--cleanup", "--fixup", "--squash", "--trailer"}
    cursor = 0
    while cursor < len(arguments):
        item = arguments[cursor]
        if item == "--":
            paths.extend(arguments[cursor + 1:])
            break
        if item.startswith("--pathspec-from-file"):
            raise ValueError("prospective pathspec files require an explicit validated path list")
        if item in ("--only", "-o"):
            only = True
        elif item in ("--include", "-i"):
            include = True
        elif item in ("--all", "-a") or item.startswith(("-am", "-av", "-aq")):
            all_tracked = True
            if item == "-am":
                cursor += 1
        elif item in takes_value:
            cursor += 1
        elif not item.startswith("-"):
            paths.append(item)
        cursor += 1
    return only or bool(paths) and not include, include, all_tracked, paths


def snapshot(root, event, invocation, temporary):
    prefix, arguments = invocation
    cwd = Path(event.get("cwd") or root)
    git = ["git", *prefix]
    original_git = list(git)
    def run(*args):
        return subprocess.run([*git, *args], cwd=cwd, check=True, capture_output=True, timeout=5).stdout
    actual = Path(run("rev-parse", "--show-toplevel").decode().strip()).resolve()
    if actual != root.resolve():
        raise ValueError("prospective commit targets a different repository")
    git = ["git", "-C", str(actual)]
    names = set(run("ls-files", "-z", "--", ".planning").decode().split("\0"))
    only, include, all_tracked, pathspec = commit_selection(arguments)
    selected = set()
    if pathspec:
        selected = set(subprocess.run([*original_git, "ls-files", "--full-name", "-z", "--", *pathspec], cwd=cwd,
                                      check=True, capture_output=True, timeout=5).stdout.decode().split("\0"))
    if only and not selected:
        raise ValueError("cannot establish --only prospective paths without an explicit -- path list")
    if only:
        head = subprocess.run([*git, "ls-tree", "-r", "--name-only", "-z", "HEAD", "--", ".planning"], cwd=cwd,
                              capture_output=True, timeout=5)
        if head.returncode == 0:
            names.update(head.stdout.decode().split("\0"))
    for name in filter(None, names):
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not name.startswith(".planning/"):
            raise ValueError("unsafe prospective planning path")
        if only and name not in selected:
            # Unrelated staged records do not enter a --only commit.
            result = subprocess.run([*git, "show", "HEAD:" + name], cwd=cwd, capture_output=True, timeout=5)
            if result.returncode:
                continue
            data = result.stdout
        elif all_tracked or only or include and name in selected:
            current = actual / path
            if not current.exists():
                continue
            data = current.read_bytes()
        else:
            data = run("show", ":" + name)
        target = Path(temporary) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def main():
    try:
        event = read_event()
        data = event.get("tool_input") or {}
        command = data.get("command") or data.get("cmd") or ""
        invocation = commit_arguments(command)
        if event.get("tool_name") not in ("Bash", "exec_command", "shell_command", "shell") or invocation is None:
            return 0
        root = root_for(event)
        try:
            with tempfile.TemporaryDirectory(prefix="engineer-prospective-") as temporary:
                snapshot(root, event, invocation, temporary)
                result = query(root, "planning.integrity", snapshot=temporary)
        except Exception as exc:
            print("Planning integrity could not be established before commit: " + str(exc), file=sys.stderr)
            return 2
        if not isinstance(result, dict) or result.get("ok") is False or result.get("valid") is not True or result.get("errors"):
            print("Planning integrity refused prospective commit: " + str(result), file=sys.stderr)
            return 2
        # Warn-only structural drift is useful context, not a second blocking gate.
        try:
            warning = query(root, "planning.validate")
            if warning.get("warnings"):
                print("NOTICE: " + str(warning["warnings"]), file=sys.stderr)
        except Exception:
            pass
    except Exception as exc:
        print("NOTICE: planning hook input unavailable: " + str(exc), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
