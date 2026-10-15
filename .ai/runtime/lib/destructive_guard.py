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


def executable(value):
    return value.replace("\\", "/").rsplit("/", 1)[-1].lower().removesuffix(".exe")


def _tokens(command):
    """Literal shell subset, preserving Windows separators and quoted data."""
    tokens, word = [], []
    quote_char = None
    active = False
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
            elif char == "\\" and quote_char == '"' and index + 1 < len(command) and command[index + 1] in ('"', "\\", "$", "`"):
                index += 1
                word.append(command[index])
            else:
                word.append(char)
        elif char in ("'", '"'):
            quote_char, active = char, True
        elif char == "\\" and index + 1 < len(command) and command[index + 1] in " \t\n'\";|&\\":
            index += 1
            word.append(command[index])
            active = True
        elif char in "$`":
            raise ValueError("dynamic-shell")
        elif char in "<>(){}":
            raise ValueError("unsupported-shell")
        elif char in ";|&\n":
            if active:
                tokens.append("".join(word))
                word, active = [], False
            sep = char
            if char in "|&" and index + 1 < len(command) and command[index + 1] == char:
                index += 1
                sep += char
            if sep == "&":
                raise ValueError("unsupported-shell")
            tokens.append((sep,))
        elif char.isspace():
            if active:
                tokens.append("".join(word))
                word, active = [], False
        else:
            word.append(char)
            active = True
        index += 1
    if quote_char:
        raise ValueError("malformed-shell")
    if active:
        tokens.append("".join(word))
    return tokens


def command_segments(payload):
    """Immutable ordered literal argv/cwd interface for other preflight hooks.

    Git -C is folded into cwd and removed from argv. Other Git options stay in
    argv. Unsupported results must not be used to infer that a commit is safe.
    """
    try:
        if not isinstance(payload, dict) or not isinstance(payload.get("tool_input"), dict):
            raise ValueError("malformed-payload")
        data = payload["tool_input"]
        if "command" in data and "cmd" in data and data["command"] != data["cmd"]:
            raise ValueError("ambiguous-payload")
        command = data.get("command", data.get("cmd"))
        if not isinstance(command, str) or not command.strip():
            raise ValueError("malformed-payload")
        cwd = canonical(payload.get("cwd") or os.getcwd())
        override = data.get("workdir", data.get("cwd"))
        if override is not None:
            if not isinstance(override, str):
                raise ValueError("unknown-cwd")
            cwd = canonical(override, cwd)
        if not Path(cwd).is_dir():
            raise ValueError("unknown-cwd")
        result, argv, previous_separator = [], [], None
        pieces = _tokens(command)
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
            if executable(argv[0]) == "env":
                argv.pop(0)
                if argv and argv[0] == "--":
                    argv.pop(0)
                if argv and argv[0].startswith("-"):
                    raise ValueError("unsupported-environment")
            while argv and ASSIGNMENT.match(argv[0]):
                variable = argv[0].split("=", 1)[0]
                if variable.startswith("GIT_") or variable in ("PATH", "HOME", "XDG_CONFIG_HOME", "BASH_ENV", "ENV", "PWD", "CDPATH"):
                    raise ValueError("unsupported-git-context")
                argv.pop(0)
            if not argv:
                raise ValueError("unsupported-shell")
            while executable(argv[0]) in ("command", "builtin", "exec"):
                argv.pop(0)
                if not argv or argv[0].startswith("-"):
                    raise ValueError("unsupported-wrapper")
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
                cwd = canonical(operands[0], cwd)
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
                            git_cwd = canonical(argv[cursor], git_cwd)
                        else:
                            normalized.append(flag)
                            if flag in ("-c", "--git-dir", "--work-tree", "--namespace", "--config-env"):
                                cursor += 1
                                if cursor >= len(argv):
                                    raise ValueError("unsupported-git-context")
                                normalized.append(argv[cursor])
                        cursor += 1
                    # -C changes Git's cwd only, never later shell segments.
                    result.append(Segment(git_cwd, tuple(normalized + argv[cursor:])))
                else:
                    result.append(Segment(cwd, tuple(argv)))
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
                values = data.get("sessions", data.get("entries"))
                if not isinstance(values, list) or any(not isinstance(x, dict) for x in values):
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


def _backup_removal(segment, evidence):
    operands = []
    skip_option = False
    for arg in segment.argv[1:]:
        if arg == "--":
            skip_option = True
        elif not skip_option and arg.startswith("-"):
            if arg.lower() not in ("-literalpath", "-path", "-recurse", "-force", "-r", "-f", "-rf", "-fr", "-recursive"):
                return _deny("unsupported-removal", "backup-delete")
        else:
            operands.append(arg)
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
    for operand in operands:
        if "," in operand or operand.startswith("~"):
            return _deny("dynamic-removal", "backup-delete", operands)
        target = canonical(operand, segment.cwd)
        if any(char in operand for char in "*?["):
            prefix = re.split(r"[*?\[]", target, maxsplit=1)[0]
            parent = str(Path(prefix).parent)
            if any(root.startswith(parent + os.sep) or fnmatch.fnmatch(root, target) for root in roots):
                return _deny("backup-approval-required", "backup-delete", operands)
        for root in roots:
            if target == root or target.startswith(root + os.sep) or root.startswith(target + os.sep):
                return _deny("backup-approval-required", "backup-delete", operands)
        if ".workflow-backups" in Path(target).parts:
            return _deny("backup-approval-required", "backup-delete", operands)
    return None


def evaluate_payload(payload, evidence_runner=None):
    if isinstance(payload, dict) and payload.get("tool_name") and payload["tool_name"] not in SHELL_TOOLS:
        return Decision(True, "unrelated-tool")
    parsed = command_segments(payload)
    if not parsed.supported:
        return _deny(parsed.reason_code)
    evidence = Evidence(evidence_runner)
    try:
        for segment in parsed.segments:
            argv = segment.argv
            name = executable(argv[0])
            if name in ("rm", "ri", "rmdir", "remove-item"):
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
                destructive = any(a.startswith(("--delete", "--move", "--copy", "--force")) or
                                  (a.startswith("-") and not a.startswith("--") and any(c in a[1:] for c in "dDmMcCf")) for a in args)
                if not destructive:
                    continue
                if any(a.startswith("--") and "=" in a for a in args):
                    return _deny("unsupported-branch-mutation", "branch-delete", args)
                if any(a in ("--move", "--copy", "--force") or
                       (a.startswith("-") and any(c in a[1:] for c in "mMcCf")) for a in args):
                    return _deny("unsupported-branch-mutation", "branch-delete", args)
                branch_targets = [a for a in args if not a.startswith("-")]
            elif verb == "push" and any(a == "-d" or a.startswith("--delete") or a.startswith(":") or a.startswith("+:" ) for a in args):
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
                target = canonical(paths[0], segment.cwd)
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
