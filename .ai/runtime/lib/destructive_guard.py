"""Bounded, non-evaluating shell preflight. All subprocesses collect evidence.

The runner contract is runner(argv: list[str], cwd: str) -> CompletedProcess.
No payload command is executed, expanded or passed to a shell.
"""
from dataclasses import dataclass
import fnmatch
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
from urllib.parse import quote, urlsplit

SHELL_TOOLS = frozenset(("Bash", "exec_command", "shell_command", "shell"))
WRAPPERS = frozenset(("bash", "sh", "zsh", "dash", "pwsh", "powershell", "cmd",
                      "eval", "source", ".", "invoke-expression", "iex", "sudo", "doas",
                      "start-process", "invoke-command", "call"))
PROTECTED_BRANCH = re.compile(r"^(main|master|develop|trunk|release/.*)$")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SEPARATORS = frozenset((";", "&&", "||", "|", "\n"))


@dataclass(frozen=True)
class Segment:
    cwd: str
    argv: tuple[str, ...]
    shell_dialect: str = "native"
    glob_patterns: tuple[str | None, ...] = ()


@dataclass(frozen=True)
class CommandSegments:
    supported: bool
    reason_code: str
    segments: tuple[Segment, ...] = ()


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason_code: str
    operation: str = "none"
    targets: tuple[str, ...] = ()
    reason: str = ""


def canonical(path, cwd=None):
    value = Path(path)
    return str((value if value.is_absolute() else Path(cwd or os.getcwd()) / value).resolve())


def _shell_path(path, cwd, dialect, *, resolve=True):
    """Translate modeled Windows Bash drive roots; never invent /usr or /tmp."""
    if os.name == "nt" and dialect == "posix" and str(path).startswith("/"):
        drive = re.fullmatch(r"/([A-Za-z])(?:/(.*))?", str(path))
        if not drive:
            raise ValueError("unsupported-posix-root")
        path = drive[1] + ":/" + (drive[2] or "")
    if not resolve:
        value = Path(path)
        return str(value if value.is_absolute() else Path(cwd) / value)
    return canonical(path, cwd)


def executable(value):
    return value.replace("\\", "/").rsplit("/", 1)[-1].lower().removesuffix(".exe")


class _Literal(str):
    """Private lexer word; public segments expose plain strings and metadata."""
    def __new__(cls, value, pattern, active_glob):
        word = super().__new__(cls, value)
        word.glob_pattern = pattern if active_glob else None
        return word


def _tokens(command, posix=False):
    """Literal shell subset; Bash escapes are distinct from native backslashes."""
    tokens, word, pattern = [], [], []
    quote_char = None
    active, active_glob = False, False
    def append(char, unquoted=False):
        nonlocal active_glob
        word.append(char)
        pattern.append(char if unquoted else {"*": "[*]", "?": "[?]", "[": "[[]"}.get(char, char))
        active_glob = active_glob or (unquoted and char in "*?[")

    index = 0
    while index < len(command):
        char = command[index]
        if char == "\x00":
            raise ValueError("malformed-shell")
        if quote_char:
            if char == quote_char:
                quote_char = None
            elif char in ("$", "`") and quote_char == '"':
                raise ValueError("dynamic-shell")
            elif posix and char == "\\" and quote_char == '"' and index + 1 < len(command) and command[index + 1] in ('"', "\\", "$", "`", "\n"):
                index += 1
                if command[index] != "\n":
                    append(command[index])
            else:
                append(char)
        elif char in ("'", '"'):
            quote_char, active = char, True
        elif posix and char == "\\":
            if index + 1 == len(command):
                raise ValueError("malformed-shell")
            index += 1
            if command[index] != "\n":
                append(command[index])
                active = True
        elif char in "$`":
            raise ValueError("dynamic-shell")
        elif char in "<>(){}":
            raise ValueError("unsupported-shell")
        elif char in ";|&\n":
            if active:
                tokens.append(_Literal("".join(word), "".join(pattern), active_glob))
                word, pattern, active, active_glob = [], [], False, False
            sep = char
            if char in "|&" and index + 1 < len(command) and command[index + 1] == char:
                index += 1
                sep += char
            if sep == "&":
                raise ValueError("unsupported-shell")
            tokens.append((sep,))
        elif char.isspace():
            if active:
                tokens.append(_Literal("".join(word), "".join(pattern), active_glob))
                word, pattern, active, active_glob = [], [], False, False
        else:
            append(char, unquoted=True)
            active = True
        index += 1
    if quote_char:
        raise ValueError("malformed-shell")
    if active:
        tokens.append(_Literal("".join(word), "".join(pattern), active_glob))
    return tokens


def _segment(cwd, argv, dialect):
    return Segment(cwd, tuple(str(a) for a in argv), dialect,
                   tuple(getattr(a, "glob_pattern", None) for a in argv))


def _literal_prefixes(argv):
    """Normalize each literal wrapper/assignment layer until the command is fixed.

    No expansion or executable body is evaluated. Context-changing assignment
    checks apply at every layer, including after command/exec/env prefixes.
    """
    cursor = 0
    while cursor < len(argv):
        word = argv[cursor]
        if ASSIGNMENT.match(word):
            variable = word.split("=", 1)[0]
            if os.name == "nt":
                variable = variable.upper()
            if variable.startswith("GIT_") or variable in (
                    "PATH", "HOME", "XDG_CONFIG_HOME", "BASH_ENV", "ENV", "PWD", "CDPATH"):
                raise ValueError("unsupported-git-context")
            cursor += 1
            continue
        name = executable(word)
        if name == "env":
            cursor += 1
            if cursor < len(argv) and argv[cursor] == "--":
                cursor += 1
            if cursor < len(argv) and argv[cursor].startswith("-"):
                raise ValueError("unsupported-environment")
            continue
        if name in ("command", "builtin", "exec", "time", "!"):
            cursor += 1
            if cursor < len(argv) and argv[cursor].startswith("-"):
                raise ValueError("unsupported-wrapper")
            continue
        return argv[cursor:]
    raise ValueError("unsupported-shell")


def command_segments(payload):
    """Immutable ordered literal argv/cwd interface for other preflight hooks.

    Git -C is folded into cwd and removed from argv. Other Git options stay in
    argv. Unsupported results must not be used to infer that a commit is safe.
    """
    try:
        if not isinstance(payload, dict) or not isinstance(payload.get("tool_input"), dict):
            raise ValueError("malformed-payload")
        if not isinstance(payload.get("tool_name"), str) or not payload["tool_name"]:
            raise ValueError("malformed-tool-name")
        data = payload["tool_input"]
        if "command" in data and "cmd" in data and data["command"] != data["cmd"]:
            raise ValueError("ambiguous-payload")
        command = data.get("command", data.get("cmd"))
        if not isinstance(command, str) or not command.strip():
            raise ValueError("malformed-payload")
        shell = data.get("shell")
        shell_name = executable(shell) if isinstance(shell, str) else ""
        posix = (payload.get("tool_name") == "Bash" or shell_name in ("bash", "sh", "zsh", "dash")
                 or (not shell_name and os.name != "nt"))
        dialect = "cmd" if shell_name == "cmd" else "posix" if posix else "native"
        # cmd's caret, percent and delayed expansion need a different grammar.
        # Refuse them as data instead of incorrectly parsing a native argv.
        if dialect == "cmd" and any(char in command for char in "^%!"):
            raise ValueError("unsupported-cmd-syntax")
        cwd = canonical(payload.get("cwd") or os.getcwd())
        override = data.get("workdir", data.get("cwd"))
        if override is not None:
            if not isinstance(override, str):
                raise ValueError("unknown-cwd")
            cwd = _shell_path(override, cwd, dialect)
        if not Path(cwd).is_dir():
            raise ValueError("unknown-cwd")
        result, argv, previous_separator = [], [], None
        pieces = _tokens(command, posix=posix)
        while pieces and pieces[-1] in ((";",), ("\n",)):
            pieces.pop()
        pieces += [(";",)]
        for token in pieces:
            if isinstance(token, str):
                argv.append(token)
                continue
            separator = token[0]
            if not argv:
                if separator == "\n":
                    continue
                raise ValueError("malformed-shell")
            argv = _literal_prefixes(argv)
            name = executable(argv[0])
            if name in WRAPPERS:
                raise ValueError("nested-shell")
            if name in ("for", "while", "if", "function", "do", "foreach", "switch"):
                raise ValueError("unsupported-shell")
            if name in ("cd", "set-location", "chdir"):
                operands = argv[1:]
                if operands[:1] == ["--"]:
                    operands = operands[1:]
                if (len(operands) != 1 or separator in ("||", "|") or
                        previous_separator in ("&&", "||", "|")):
                    raise ValueError("ambiguous-cwd")
                cwd = _shell_path(operands[0], cwd, dialect)
                if not Path(cwd).is_dir():
                    raise ValueError("unknown-cwd")
            else:
                if name == "git":
                    normalized, cursor, git_cwd = [argv[0]], 1, cwd
                    while cursor < len(argv) and argv[cursor].startswith("-"):
                        flag = argv[cursor]
                        if flag == "-C":
                            cursor += 1
                            if cursor >= len(argv):
                                raise ValueError("unsupported-git-context")
                            git_cwd = _shell_path(argv[cursor], git_cwd, dialect)
                        else:
                            normalized.append(flag)
                            if flag in ("-c", "--git-dir", "--work-tree", "--namespace", "--config-env"):
                                cursor += 1
                                if cursor >= len(argv):
                                    raise ValueError("unsupported-git-context")
                                normalized.append(argv[cursor])
                        cursor += 1
                    # -C changes Git's cwd only, never later shell segments.
                    result.append(_segment(git_cwd, normalized + argv[cursor:], dialect))
                else:
                    result.append(_segment(cwd, argv, dialect))
            argv = []
            previous_separator = separator
        return CommandSegments(True, "literal-commands", tuple(result))
    except (ValueError, OSError, TypeError) as exc:
        return CommandSegments(False, str(exc) or "malformed-payload")


def run_evidence(argv, cwd):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", timeout=20, shell=False)


class EvidenceError(Exception):
    pass


class Evidence:
    def __init__(self, runner=None):
        self.runner = runner or run_evidence
        self.deadline = time.monotonic() + 80

    def output(self, argv, cwd):
        try:
            if time.monotonic() >= self.deadline:
                raise EvidenceError("evidence-time-budget")
            result = self.runner(list(argv), str(cwd))
            if result.returncode:
                raise EvidenceError("evidence-unavailable")
            if not isinstance(result.stdout, str):
                raise EvidenceError("evidence-malformed")
            return result.stdout.strip()
        except (OSError, subprocess.SubprocessError) as exc:
            raise EvidenceError("evidence-unavailable") from exc

    def git(self, cwd, *args):
        return self.output(["git", *args], cwd)

    def repository(self, cwd):
        root = canonical(self.git(cwd, "rev-parse", "--show-toplevel"))
        common = canonical(self.git(root, "rev-parse", "--git-common-dir"), root)
        raw = self.git(root, "worktree", "list", "--porcelain", "-z")
        trees, current = [], {}
        for field in raw.split("\0"):
            if field.startswith("worktree "):
                if current:
                    trees.append(current)
                current = {"path": canonical(field[9:])}
            elif field.startswith("branch "):
                current["branch"] = field[7:].removeprefix("refs/heads/")
            elif field.startswith("HEAD "):
                current["head"] = field[5:]
            elif field in ("locked", "prunable", "bare") or field.startswith(("locked ", "prunable ")):
                current[field.split(" ")[0]] = True
        if current:
            trees.append(current)
        if not trees or not any(t["path"] == root for t in trees):
            raise EvidenceError("repository-identity-unknown")
        return {"root": root, "common_dir": common, "primary": trees[0]["path"], "worktrees": trees}


def _deny(code, operation="shell", targets=()):
    return Decision(False, code, operation, tuple(targets),
                    f"{code}: preserve the target; use explicit literal argv or the reviewed cleanup entrypoint. "
                    "For a checkout path restore use git checkout [REF] -- PATH.")


def _git_parts(argv):
    cursor = 1
    while cursor < len(argv) and argv[cursor].startswith("-"):
        flag = argv[cursor]
        # -C has already been folded into the segment cwd. Other context flags
        # cannot prove an ordinary worktree identity and are refused on mutation.
        if flag in ("--no-pager", "--paginate"):
            cursor += 1
            continue
        return None, (), "unsupported-git-context"
    return (argv[cursor], argv[cursor + 1:], None) if cursor < len(argv) else (None, (), None)


def _ownership(repo, branch, target=None):
    state = Path(repo["common_dir"]) / "ai-phase"
    records = []
    try:
        paths = [state / "sessions.json", *sorted((state / "waves").glob("*.json"))]
        for path in paths:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                key = "sessions" if path == state / "sessions.json" else "entries"
                if not isinstance(data, dict):
                    return None
                values = data.get(key)
                if not isinstance(values, list):
                    return None
                for record in values:
                    if not isinstance(record, dict):
                        return None
                    branch_value = record.get("branch")
                    worktree_value = record.get("worktree", record.get("path"))
                    base_value = record.get("base_branch")
                    if (not isinstance(branch_value, str) or not branch_value or
                            not isinstance(worktree_value, str) or not worktree_value or
                            (base_value is not None and not isinstance(base_value, str))):
                        return None
                records.extend(values)
        matches = [r for r in records if r.get("branch") == branch and
                   isinstance(r.get("worktree", r.get("path")), str) and
                   (target is None or canonical(r.get("worktree", r.get("path"))) == target)]
        identities = {(canonical(r.get("worktree", r.get("path"))), r.get("base_branch")) for r in matches}
        return matches[0] if len(identities) == 1 else None
    except (ValueError, OSError, TypeError):
        return None


def provider_evidence(evidence, repo, branch, oid):
    """Complete matching terminal records; no ancestry fallback for unknown/open."""
    try:
        remote = evidence.git(repo["root"], "remote", "get-url", "origin")
        scp = re.fullmatch(r"(?:[^@/]+@)?([^:/]+):(.+)", remote)
        if "://" in remote:
            parsed = urlsplit(remote)
            host, project = parsed.hostname, parsed.path.strip("/")
        elif scp:
            host, project = scp.groups()
        else:
            return "provider-unknown"
        project = project.removesuffix(".git")
        if not host or not project or ".." in project.split("/"):
            return "provider-unknown"
        if host == "github.com" or host.startswith("github."):
            endpoint = f"repos/{project}/pulls?state=all&per_page=100"
            pages = json.loads(evidence.output(["gh", "api", "--hostname", host,
                "--paginate", "--slurp", endpoint], repo["root"]))
            if (not isinstance(pages, list) or not pages or
                    any(not isinstance(p, list) for p in pages) or len(pages[-1]) >= 100 or
                    any(len(p) != 100 for p in pages[:-1])):
                return "provider-incomplete"
            records = [item for page in pages for item in page]
            matches = []
            for item in records:
                if not isinstance(item, dict) or not isinstance(item.get("head"), dict):
                    return "provider-malformed"
                if item["head"].get("ref") != branch:
                    continue
                if (item.get("base", {}).get("repo", {}).get("full_name") != project or
                        (item["head"].get("repo") or {}).get("full_name") != project or
                        item["head"].get("sha") != oid):
                    return "provider-identity-mismatch"
                state = item.get("state")
                if state in ("open", "OPEN"):
                    return "provider-open"
                if state not in ("closed", "CLOSED", "MERGED"):
                    return "provider-unknown"
                matches.append(item)
        elif host == "gitlab.com" or host.startswith("gitlab."):
            args = ["glab", "api", "--hostname", host, "--output", "json", "-X", "GET"]
            project_data = json.loads(evidence.output(args + ["projects/" + quote(project, safe="")], repo["root"]))
            project_id = project_data.get("id")
            if (not isinstance(project_id, int) or isinstance(project_id, bool) or
                    project_data.get("path_with_namespace") != project or
                    project_data.get("web_url", "").rstrip("/") != f"https://{host}/{project}"):
                return "provider-identity-mismatch"
            records = json.loads(evidence.output(args + ["--paginate",
                f"projects/{project_id}/merge_requests?state=all"], repo["root"]))
            if not isinstance(records, list):
                return "provider-incomplete"
            matches = []
            for item in records:
                if not isinstance(item, dict) or "source_branch" not in item:
                    return "provider-malformed"
                if item["source_branch"] != branch:
                    continue
                if (item.get("source_project_id") != project_id or item.get("target_project_id") != project_id
                        or item.get("sha") != oid):
                    return "provider-identity-mismatch"
                if item.get("state") == "opened":
                    return "provider-open"
                if item.get("state") not in ("closed", "merged"):
                    return "provider-unknown"
                matches.append(item)
        else:
            return "provider-unknown"
        return "provider-terminal" if matches else "provider-no-match"
    except (EvidenceError, ValueError, TypeError, AttributeError):
        return "provider-unknown"


def deletion_decision(evidence, repo, branch, target=None):
    operation = "worktree-delete" if target else "branch-delete"
    targets = (target or branch,)
    if not branch or PROTECTED_BRANCH.fullmatch(branch):
        return _deny("protected-branch", operation, targets)
    current = evidence.git(repo["root"], "symbolic-ref", "--short", "HEAD")
    if branch == current or target in (repo["root"], repo["primary"]):
        return _deny("current-or-primary-target", operation, targets)
    ownership = _ownership(repo, branch, target)
    if not ownership:
        return _deny("target-unowned", operation, targets)
    for tree in repo["worktrees"]:
        if tree.get("branch") != branch:
            continue
        if tree.get("locked") or tree.get("prunable") or tree.get("bare"):
            return _deny("worktree-unavailable", operation, targets)
        status = evidence.git(tree["path"], "status", "--porcelain=v1", "--untracked-files=all", "--ignored", "-z")
        if status:
            return _deny("worktree-dirty", operation, targets)
        if not target:
            return _deny("branch-checked-out", operation, targets)
    oid = evidence.git(repo["root"], "rev-parse", "--verify", "refs/heads/" + branch)
    provider = provider_evidence(evidence, repo, branch, oid)
    if provider != "provider-terminal":
        return _deny(provider, operation, targets)
    base = ownership.get("base_branch")
    if not isinstance(base, str) or not base or base.startswith("-"):
        return _deny("integration-unknown", operation, targets)
    # Terminal CLOSED is not integration. Even MERGED may predate new commits.
    # Require the pinned tip to be integrated; squashed unique work stays kept.
    try:
        evidence.git(repo["root"], "merge-base", "--is-ancestor", oid, "refs/heads/" + base)
    except EvidenceError:
        return _deny("integration-unproven", operation, targets)
    return Decision(True, "clean-owned-terminal-integrated", operation, targets)


def _within(path, parent):
    """Component ancestry, including roots, with compatible-drive comparison."""
    path, parent = os.path.normcase(path), os.path.normcase(parent)
    try:
        return os.path.commonpath((path, parent)) == parent
    except ValueError:
        return False


def _glob_overlaps(pattern, protected):
    """A glob can cover a protected ancestor, exact path or descendant.

    Compare components, retaining quoted/escaped metacharacters as literals in
    the lexer-provided fnmatch pattern. A benign sibling prefix is unrelated.
    """
    parts = Path(os.path.normcase(pattern)).parts
    protected_parts = Path(os.path.normcase(protected)).parts
    return all(fnmatch.fnmatchcase(target, candidate)
               for candidate, target in zip(parts, protected_parts))


def _resolved_glob_overlaps(pattern, protected):
    """Resolve bounded read-only matches, including wildcard-selected aliases.

    Unlike shell execution this only enumerates directory components. Errors,
    recursive glob syntax or an exceeded inspection budget preserve the target.
    Literal/quoted operands never enter this function.
    """
    parts = Path(pattern).parts
    if not parts or len(parts) > 64 or "**" in parts:
        raise EvidenceError("glob-evidence-unsupported")
    candidates, inspected = [Path(parts[0])], 0
    try:
        for index, component in enumerate(parts[1:], 1):
            following = []
            magic = any(char in component for char in "*?[")
            for parent in candidates:
                if magic:
                    children = []
                    try:
                        with os.scandir(parent) as entries:
                            for entry in entries:
                                inspected += 1
                                if inspected > 8192:
                                    raise EvidenceError("glob-evidence-budget")
                                if fnmatch.fnmatchcase(os.path.normcase(entry.name), os.path.normcase(component)):
                                    children.append(Path(entry.path))
                    except (FileNotFoundError, NotADirectoryError):
                        continue
                else:
                    children = [parent / component]
                for child in children:
                    inspected += 1
                    if inspected > 8192:
                        raise EvidenceError("glob-evidence-budget")
                    try:
                        child.lstat()
                    except FileNotFoundError:
                        if magic:
                            raise EvidenceError("glob-evidence-changed")
                        continue
                    resolved = canonical(child)
                    final = index == len(parts) - 1
                    if any(_within(resolved, root) or (final and _within(root, resolved)) for root in protected):
                        return True
                    following.append(child)
            candidates = following
            if not candidates:
                return False
        return False
    except (OSError, RuntimeError) as exc:
        raise EvidenceError("glob-evidence-unknown") from exc


def _unsupported_parent_traversal(operand, pattern, cwd, dialect):
    """Preserve raw parent components before canonicalization can erase them."""
    if ".." not in Path(operand).parts:
        return None
    if pattern is not None:
        return "unsupported-glob-parent-traversal"
    raw = Path(_shell_path(operand, cwd, dialect, resolve=False))
    current, alias = Path(raw.anchor), False
    last_parent = max(index for index, component in enumerate(raw.parts) if component == "..")
    for component in raw.parts[1:last_parent + 1]:
        if component == "..":
            if alias:
                return "unsupported-alias-parent-traversal"
            current = current.parent
            continue
        # Active pattern/parent combinations were refused above. A remaining * or ? is
        # literal data and cannot name a Windows component; do not ask native
        # metadata APIs to interpret or reject that impossible literal name.
        if os.name == "nt" and any(char in component for char in "*?"):
            return None
        current = current / component
        try:
            metadata = current.lstat()
        except (FileNotFoundError, NotADirectoryError):
            return None
        except OSError as exc:
            raise EvidenceError("parent-traversal-unknown") from exc
        alias = alias or stat.S_ISLNK(metadata.st_mode) or bool(
            getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    return None


def _git_argument_parts(args, value_longs=(), value_shorts=()):
    """Separate option names from operands/values without expanding shell data.

    Long = values and short-option attached/separate values never become flags.
    `--` ends option parsing. Unknown options remain literal flags for the
    caller's conservative destructive-option classification.
    """
    options, operands, cursor, literal = [], [], 0, False
    while cursor < len(args):
        arg = args[cursor]
        cursor += 1
        if literal or not arg.startswith("-") or arg == "-":
            operands.append(arg)
        elif arg == "--":
            literal = True
        elif arg.startswith("--"):
            name, equals, _ = arg.partition("=")
            options.append(name)
            if not equals and name in value_longs:
                if cursor >= len(args):
                    raise ValueError("malformed-git-option")
                cursor += 1
        else:
            for index, short in enumerate(arg[1:], 1):
                options.append("-" + short)
                if short in value_shorts:
                    if index == len(arg) - 1:
                        if cursor >= len(args):
                            raise ValueError("malformed-git-option")
                        cursor += 1
                    break
    return tuple(options), tuple(operands)


def _long_option(option, complete):
    return option.startswith("--") and len(option) > 2 and complete.startswith(option)


def _backup_removal(segment, evidence):
    operands, patterns = [], []
    skip_option, literal_paths = False, False
    for index, arg in enumerate(segment.argv[1:], 1):
        if arg == "--":
            skip_option = True
        elif not skip_option and arg.startswith("-"):
            if arg.lower() not in ("-literalpath", "-path", "-recurse", "-force", "-r", "-f", "-rf", "-fr", "-recursive"):
                return _deny("unsupported-removal", "backup-delete")
            literal_paths = literal_paths or arg.lower() == "-literalpath"
        else:
            operands.append(arg)
            patterns.append(segment.glob_patterns[index] if len(segment.glob_patterns) == len(segment.argv)
                            else arg if any(char in arg for char in "*?[") else None)
    if not operands:
        return _deny("unresolved-removal", "backup-delete")
    # Filesystem identity is enough for backup protection. Ordinary removals
    # must not depend on Git or a provider being installed/authenticated.
    roots = {canonical(Path(segment.cwd) / ".workflow-backups")}
    for directory in (Path(segment.cwd), *Path(segment.cwd).parents):
        marker = directory / ".git"
        if not marker.exists():
            continue
        roots.add(canonical(directory / ".workflow-backups"))
        try:
            common = marker
            if marker.is_file():
                text = marker.read_text(encoding="utf-8").strip()
                if not text.startswith("gitdir: "):
                    return _deny("repository-identity-unknown", "backup-delete")
                gitdir = Path(canonical(text[8:], directory))
                common = Path(canonical((gitdir / "commondir").read_text(encoding="utf-8").strip(), gitdir))
            if common.name == ".git":
                roots.add(canonical(common.parent / ".workflow-backups"))
        except OSError:
            return _deny("repository-identity-unknown", "backup-delete")
        break
    for operand, pattern in zip(operands, patterns):
        if "," in operand or operand.startswith("~"):
            return _deny("dynamic-removal", "backup-delete", operands)
        try:
            if segment.shell_dialect != "posix":
                # PowerShell -Path expands wildcard characters even in quotes;
                # -LiteralPath explicitly treats every such character as data.
                pattern = None if literal_paths else operand if any(c in operand for c in "*?[") else None
            unsupported = _unsupported_parent_traversal(operand, pattern, segment.cwd, segment.shell_dialect)
            if unsupported:
                return _deny(unsupported, "backup-delete", operands)
            target = _shell_path(operand, segment.cwd, segment.shell_dialect)
            pattern = _shell_path(pattern, segment.cwd, segment.shell_dialect) if pattern is not None else None
        except ValueError as exc:
            return _deny(str(exc), "backup-delete", operands)
        if pattern is not None:
            if any(_glob_overlaps(pattern, root) for root in roots) or _resolved_glob_overlaps(pattern, roots):
                return _deny("backup-approval-required", "backup-delete", operands)
        for root in roots:
            if _within(target, root) or _within(root, target):
                return _deny("backup-approval-required", "backup-delete", operands)
        if ".workflow-backups" in Path(target).parts:
            return _deny("backup-approval-required", "backup-delete", operands)
    return None


def evaluate_payload(payload, evidence_runner=None):
    if not isinstance(payload, dict):
        return _deny("malformed-payload")
    tool = payload.get("tool_name")
    if not isinstance(tool, str) or not tool:
        return _deny("malformed-tool-name")
    if tool not in SHELL_TOOLS:
        return Decision(True, "unrelated-tool")
    parsed = command_segments(payload)
    if not parsed.supported:
        return _deny(parsed.reason_code)
    evidence = Evidence(evidence_runner)
    try:
        for segment in parsed.segments:
            argv = segment.argv
            name = executable(argv[0])
            if name in ("rm", "ri", "rmdir", "remove-item", "del", "rd", "erase"):
                denied = _backup_removal(segment, evidence)
                if denied:
                    return denied
            if name != "git":
                continue
            verb, args, error = _git_parts(argv)
            if error:
                return _deny(error, "git")
            if not verb:
                continue
            known = {"add", "commit", "status", "show", "diff", "log", "rev-parse", "show-ref",
                     "ls-files", "ls-tree", "grep", "fetch", "pull", "push", "branch", "checkout",
                     "switch", "worktree", "update-ref", "merge", "rebase", "restore", "reset",
                     "config", "remote", "tag", "clean", "stash", "help", "version", "describe",
                     "for-each-ref", "merge-base", "symbolic-ref", "cat-file", "check-ignore"}
            if verb not in known:
                # Never execute an alias to find out what it does.
                return _deny("git-alias-or-unknown", "git", (verb,))
            if verb in ("checkout", "switch"):
                if verb == "checkout" and "--" in args:
                    before = args[:args.index("--")]
                    after = args[args.index("--") + 1:]
                    if len(before) <= 1 and not any(a.startswith("-") for a in before) and after:
                        continue
                repo = evidence.repository(segment.cwd)
                if repo["root"] == repo["primary"]:
                    return _deny("primary-branch-switch", "branch-switch", args)
                continue
            branch_targets = None
            if verb == "branch":
                options, operands = _git_argument_parts(args,
                    value_longs=("--format", "--sort", "--set-upstream-to", "--points-at"), value_shorts=("u",))
                destructive = any(a in ("-d", "-D", "-m", "-M", "-c", "-C", "-f") or
                    any(_long_option(a, flag) for flag in ("--delete", "--move", "--copy", "--force"))
                    for a in options)
                if not destructive:
                    continue
                if any(a in ("-m", "-M", "-c", "-C", "-f") or
                       any(_long_option(a, flag) for flag in ("--move", "--copy", "--force")) for a in options):
                    return _deny("unsupported-branch-mutation", "branch-delete", args)
                branch_targets = operands
            elif verb == "push":
                options, operands = _git_argument_parts(args,
                    value_longs=("--push-option", "--repo", "--receive-pack", "--exec"), value_shorts=("o",))
                if (any(a == "-d" or _long_option(a, "--delete") for a in options) or
                        any(a.startswith((":", "+:")) for a in operands)):
                    return _deny("remote-deletion-unsupported", "branch-delete", args)
            elif verb == "update-ref":
                return _deny("ref-mutation-unsupported", "branch-delete", args)
            elif verb == "worktree" and args and args[0] in ("remove", "prune", "move", "repair"):
                if args[0] != "remove":
                    return _deny("worktree-mutation-unsupported", "worktree-delete", args)
                paths = [a for a in args[1:] if not a.startswith("-")]
                if len(paths) != 1:
                    return _deny("unresolved-worktree", "worktree-delete", paths)
                repo = evidence.repository(segment.cwd)
                target = _shell_path(paths[0], segment.cwd, segment.shell_dialect)
                tree = next((t for t in repo["worktrees"] if t["path"] == target), None)
                if not tree:
                    return _deny("target-unregistered", "worktree-delete", (target,))
                decision = deletion_decision(evidence, repo, tree.get("branch"), target)
                if not decision.allowed:
                    return decision
            if branch_targets is not None:
                if not branch_targets:
                    return _deny("unresolved-branch", "branch-delete")
                repo = evidence.repository(segment.cwd)
                for branch in branch_targets:
                    decision = deletion_decision(evidence, repo, branch)
                    if not decision.allowed:
                        return decision
        return Decision(True, "allowed")
    except (EvidenceError, OSError, ValueError, TypeError) as exc:
        return _deny(str(exc) if isinstance(exc, EvidenceError) else "evidence-unknown")
