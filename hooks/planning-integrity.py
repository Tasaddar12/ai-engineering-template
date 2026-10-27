"""Strict planning integrity preflight for prospective commit commands."""
import shlex
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
from hook_common import read_event, root_for, query


def shell_words(command, windows=False):
    # Shell comments start at a word boundary. shlex's default comment handling
    # incorrectly discards literal hashes in message arguments.
    cleaned, quote, escaped, boundary = [], None, False, True
    index = 0
    while index < len(command):
        char = command[index]
        if not windows and char == "\\" and index + 1 < len(command) and command[index + 1] == "\n":
            index += 2
            continue
        if escaped:
            cleaned.append(char)
            escaped = False
            boundary = False
        elif char == "\\" and not windows and quote != "'":
            cleaned.append(char)
            escaped = True
        elif char in ("'", '"'):
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            cleaned.append(char)
            boundary = False
        elif char == "#" and quote is None and boundary:
            while index < len(command) and command[index] != "\n":
                index += 1
            continue
        else:
            cleaned.append(";" if char == "\n" and quote is None else char)
            if quote is None:
                boundary = char.isspace() or char in ";&|"
        index += 1
    if windows:
        # Native shells concatenate quoted and unquoted parts of one argument.
        # posix=False shlex splits -am"two words" into fake path arguments;
        # posix=True instead destroys native path separators such as C:\repo.
        words, word, quote, started = [], [], None, False
        for char in cleaned:
            if char in ("'", '"') and (quote is None or quote == char):
                quote = None if quote else char
                started = True
            elif quote is None and (char.isspace() or char in ";&|"):
                if started:
                    words.append("".join(word))
                    word, started = [], False
                if char in ";&|":
                    if words and words[-1] == char and char in "&|":
                        words[-1] += char
                    else:
                        words.append(char)
            else:
                word.append(char)
                started = True
        if quote:
            raise ValueError("unterminated native shell quote")
        if started:
            words.append("".join(word))
        return words
    lexer = shlex.shlex("".join(cleaned), posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def command_segments(command, windows=False, depth=0):
    if depth > 8:
        raise ValueError("inline shell nesting exceeds supported inspection depth")
    words = list(command) if isinstance(command, list) else shell_words(command, windows)
    segments, current = [], []
    for word in [*words, ";"]:
        if word in (";", "&&", "||", "|", "&"):
            if current:
                segments.append(current)
                current = []
        else:
            current.append(word)
    for words in segments:
        while words and (words[0] in ("command", "exec", "env", "time", "!") or
                         re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0])):
            words = words[1:]
        if not words:
            continue
        executable = words[0].replace("\\", "/").rsplit("/", 1)[-1].lower().removesuffix(".exe")
        if executable in ("bash", "sh", "powershell", "pwsh", "cmd"):
            inline = next((i for i, word in enumerate(words[1:], 1)
                           if word.lower() in ("-command", "/c") or
                           executable in ("bash", "sh") and word.startswith("-") and "c" in word[1:]), None)
            if inline is None:
                continue  # --help, --version and interactive launches do not commit.
            if len(words) != inline + 2:
                raise ValueError("unsupported inline shell invocation; provide one complete command string")
            yield from command_segments(words[inline + 1], executable in ("powershell", "pwsh", "cmd"), depth + 1)
        else:
            yield words


def commit_arguments(command, windows=False):
    if not isinstance(command, (str, list)):
        return None
    additions = []
    for words in command_segments(command, windows):
        executable = words[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
        if executable not in ("git", "git.exe"):
            continue
        cursor = 1
        while cursor < len(words):
            token = words[cursor]
            if token in ("-C", "-c", "--git-dir", "--work-tree"):
                cursor += 2
            elif token.startswith("-"):
                cursor += 1
            else:
                break
        if cursor >= len(words):
            continue
        prefix, arguments = words[1:cursor], words[cursor + 1:]
        if words[cursor] == "add":
            additions.append((prefix, arguments))
        elif words[cursor] == "commit":
            return prefix, arguments, additions
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
        elif item.startswith("-") and not item.startswith("--") and len(item) > 2:
            # Short options preceding m/F/C/c consume the rest as their value.
            for position, option in enumerate(item[1:], 1):
                if option == "a":
                    all_tracked = True
                elif option == "o":
                    only = True
                elif option == "i":
                    include = True
                if option in "mFCc":
                    if position == len(item) - 1:
                        cursor += 1
                    break
        elif item in ("--all", "-a"):
            all_tracked = True
        elif item in takes_value:
            cursor += 1
        elif not item.startswith("-"):
            paths.append(item)
        cursor += 1
    return only or bool(paths) and not include, include, all_tracked, paths


def snapshot(root, event, invocation, temporary):
    prefix, arguments, additions = invocation
    cwd = Path(event.get("cwd") or root)
    def execute(prefix, *args, check=True, input=None):
        return subprocess.run(["git", *prefix, *args], cwd=cwd, check=check,
                              capture_output=True, timeout=5, input=input)
    def top(prefix):
        return Path(execute(prefix, "rev-parse", "--show-toplevel").stdout.decode().strip()).resolve()
    actual = top(prefix)
    if actual != root.resolve():
        raise ValueError("prospective commit targets a different repository")
    git = ["-C", str(actual)]
    def names(prefix, paths, others=False):
        options = ["ls-files", "--full-name", "-z", "--cached"]
        if others:
            options += ["--others", "--exclude-standard"]
        return set(filter(None, execute(prefix, *options, "--", *paths).stdout.decode().split("\0")))
    tracked = names(git, [".planning"])
    working = set()
    for add_prefix, add_args in additions:
        if top(add_prefix) != actual:
            raise ValueError("preceding git add targets a different repository")
        add_paths, update, repository_wide = [], False, False
        after_separator = False
        for token in add_args:
            if token == "--":
                after_separator = True
            elif not after_separator and token in ("-u", "--update"):
                update = True
                repository_wide = True
            elif not after_separator and token in ("-A", "--all"):
                repository_wide = True
            elif not after_separator and token.startswith("-"):
                raise ValueError("unsupported prospective git add option: " + token)
            else:
                add_paths.append(token)
        if add_paths or repository_wide:
            selected = names(add_prefix if add_paths else git, add_paths or [".planning"], not update)
            selected = {name for name in selected if name.startswith(".planning/")}
            tracked.update(selected)
            working.update(selected)
    only, include, all_tracked, pathspec = commit_selection(arguments)
    selected = names(prefix, pathspec) & tracked if pathspec else set()
    # Newly added paths are now prospective index members, including glob matches.
    if pathspec and additions:
        selected |= names(prefix, pathspec, True) & working
    if only and not pathspec:
        raise ValueError("cannot establish --only prospective paths without an explicit -- path list")
    for name in sorted(tracked):
        path = Path(name)
        if path.is_absolute() or ".." in path.parts or not name.startswith(".planning/"):
            raise ValueError("unsafe prospective planning path")
        if only and name not in selected:
            continue  # Unrelated staged records do not enter a --only commit.
        from_working = all_tracked or only or name in working or include and name in selected
        if from_working:
            current = actual / path
            if not current.exists():
                continue
            attributes = execute(git, "check-attr", "filter", "--", name).stdout.decode().rstrip().rsplit(": ", 1)[-1]
            if attributes not in ("unspecified", "unset"):
                raise ValueError("Cannot validate a planning record with a clean filter: " + name)
            data = current.read_bytes()
        else:
            staged = execute(git, "show", ":" + name, check=False)
            if staged.returncode:
                continue  # Deletions have no prospective bytes.
            data = staged.stdout
        previous = execute(git, "show", "HEAD:" + name, check=False)
        if previous.returncode == 0:
            if previous.stdout == data:
                continue
            if from_working:
                # Git's built-in conversion honors autocrlf, eol and encoding.
                # The filter guard above is mandatory: never execute a project's
                # clean filter. No -w means neither object store nor index changes.
                prospective = execute(git, "hash-object", "--path=" + name, "--stdin", input=data).stdout.strip()
                historical = execute(git, "rev-parse", "HEAD:" + name).stdout.strip()
                if prospective == historical:
                    continue  # Unchanged Git bytes do not revalidate legacy schema.
        target = Path(temporary) / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def main():
    try:
        event = read_event()
        if event.get("tool_name") not in ("Bash", "exec_command", "shell_command", "shell"):
            return 0
        data = event.get("tool_input") or {}
        command = data.get("command") or data.get("cmd") or ""
        try:
            invocation = commit_arguments(command, os.name == "nt" and event.get("tool_name") != "Bash")
        except (ValueError, TypeError) as exc:
            print("Planning integrity could not inspect shell command: " + str(exc), file=sys.stderr)
            return 2
        if invocation is None:
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
