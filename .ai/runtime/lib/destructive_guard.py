"""Bounded shell preflight and a separate exact-approved cleanup entrypoint.

The runner contract is runner(argv: list[str], cwd: str) -> CompletedProcess.
Preflight subprocesses only collect evidence; no payload command is executed,
expanded or passed to a shell. Cleanup mutations use explicitly constructed argv.
"""
from dataclasses import dataclass
import fnmatch
import hashlib
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

# Standalone cleanup shares the guard's evidence policy; it never evaluates a
# shell payload and never writes runtime-owned sessions/waves/planning records.
def _json_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value):
    return hashlib.sha256(_json_bytes(value)).hexdigest()


def _safe_path(value):
    """Reject aliases, including Windows junctions, before canonicalization."""
    path = Path(os.path.abspath(value))
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise EvidenceError("symlink-or-junction")
    if os.path.normcase(str(path)) != os.path.normcase(canonical(path)):
        raise EvidenceError("path-alias")
    return str(path)


def _contains(parent, child):
    return Path(child).is_relative_to(Path(parent))


def _backup_digest(path):
    _safe_path(path)
    rows, total = [], 0
    pending = [Path(path)]
    while pending:
        item = pending.pop()
        _safe_path(item)
        info = item.lstat()
        relative = item.relative_to(path).as_posix()
        if stat.S_ISDIR(info.st_mode):
            rows.append([relative, "directory", stat.S_IMODE(info.st_mode)])
            pending.extend(sorted(item.iterdir(), reverse=True))
        elif stat.S_ISREG(info.st_mode):
            total += info.st_size
            if total > 100 * 1024 * 1024:
                raise EvidenceError("backup-evidence-limit")
            rows.append([relative, "file", stat.S_IMODE(info.st_mode),
                         hashlib.sha256(item.read_bytes()).hexdigest()])
        else:
            raise EvidenceError("backup-special-file")
        if len(rows) + len(pending) > 10000:
            raise EvidenceError("backup-evidence-limit")
    return _digest(rows)


class CleanupEvidence(Evidence):
    def __init__(self, runner=None):
        super().__init__(runner)
        self.provider_reads = []

    def repository(self, cwd):
        # Inspect Git's original path spelling before shared evidence resolves it.
        # A junction registration must not disappear behind its canonical target.
        raw = self.git(cwd, "worktree", "list", "--porcelain", "-z")
        for field in raw.split("\0"):
            if field.startswith("worktree "):
                _safe_path(field[9:])
        return super().repository(cwd)

    def output(self, argv, cwd):
        if argv[0] == "git":
            # status may refresh the index unless optional writes are disabled.
            argv = ["git", "--no-optional-locks", *argv[1:]]
        value = super().output(argv, cwd)
        if argv[0] in ("gh", "glab"):
            self.provider_reads.append({"argv": list(argv), "response": json.loads(value)})
        return value


def _cleanup_provider(evidence, repo, branch):
    records = []
    remote = evidence.git(repo["root"], "remote", "get-url", "origin")
    for read in evidence.provider_reads:
        github = read["argv"][0] == "gh"
        response = read["response"]
        if github:
            values = [item for page in response for item in page]
        elif "/merge_requests" in read["argv"][-1]:
            values = response
        else:
            continue
        for item in values:
            if (item.get("head", {}).get("ref") if github else item.get("source_branch")) != branch:
                continue
            number = item.get("number" if github else "iid")
            if type(number) is not int or number <= 0:
                raise EvidenceError("provider-record-identity-unknown")
            records.append({"provider": "github" if github else "gitlab", "record": number,
                "project": item["base"]["repo"]["full_name"] if github else item["target_project_id"],
                "state": item["state"], "head": item["head"]["sha"] if github else item["sha"]})
    if not records:
        raise EvidenceError("provider-record-identity-unknown")
    return {"remote": remote, "records": records, "reads": list(evidence.provider_reads)}


def _cleanup_storage(repo):
    return Path(_safe_path(Path(repo["common_dir"]) / "ai-cleanup"))


def _cleanup_generation(repo):
    root = _cleanup_storage(repo)
    if not root.exists():
        return _digest([])
    receipts = root / "receipts"
    _safe_path(receipts)
    rows = []
    if receipts.exists():
        for path in sorted(receipts.iterdir()):
            if not re.fullmatch(r"[0-9a-f]{64}\.json", path.name) or len(rows) >= 10000:
                raise EvidenceError("cleanup-receipt-invalid")
            _safe_path(path)
            if not path.is_file() or path.stat().st_size > 1024 * 1024:
                raise EvidenceError("cleanup-receipt-invalid")
            rows.append([path.name, hashlib.sha256(path.read_bytes()).hexdigest()])
    return _digest(rows)


def _cleanup_ref_identity(evidence, repo_path, ref):
    """Read the exact named ref, including symbolic refs with missing targets."""
    try:
        if time.monotonic() >= evidence.deadline:
            raise EvidenceError("evidence-time-budget")
        probe = evidence.runner(["git", "--no-optional-locks", "symbolic-ref", "--quiet",
                                 "--no-recurse", ref], str(repo_path))
        if not isinstance(probe.stdout, str) or probe.returncode not in (0, 1):
            raise EvidenceError("ref-identity-unknown")
        if probe.returncode == 0:
            target = probe.stdout.strip()
            if not target.startswith("refs/") or any(c in target for c in "\0\r\n"):
                raise EvidenceError("ref-identity-unknown")
            return {"kind": "symbolic", "ref": ref, "target": target}
        # Exit 1 is Git's explicit "not symbolic" result, not evidence failure.
        raw = evidence.git(repo_path, "for-each-ref", "--format=%(refname)%00%(objectname)%00%(symref)", ref)
        rows = [line.split("\0") for line in raw.splitlines() if line.split("\0")[0] == ref]
        if not rows:
            return {"kind": "missing", "ref": ref}
        if len(rows) != 1 or len(rows[0]) != 3:
            raise EvidenceError("ref-identity-unknown")
        _, oid, target = rows[0]
        if target:
            # A concurrent direct-to-symbolic change between the two reads.
            return {"kind": "symbolic", "ref": ref, "target": target}
        if not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", oid):
            raise EvidenceError("ref-identity-unknown")
        return {"kind": "direct", "ref": ref, "oid": oid}
    except (OSError, subprocess.SubprocessError) as exc:
        raise EvidenceError("ref-identity-unknown") from exc


def cleanup_preview(repo_path, evidence_runner=None):
    """Read-only, deterministic snapshot. Unknown evidence preserves targets."""
    evidence = CleanupEvidence(evidence_runner)
    repo = evidence.repository(_safe_path(repo_path))
    for path in (repo["root"], repo["common_dir"], repo["primary"]):
        _safe_path(path)
    identity = {key: repo[key] for key in ("root", "common_dir", "primary")}
    identity["head"] = evidence.git(repo["root"], "rev-parse", "HEAD")
    identity["current_branch"] = evidence.git(repo["root"], "symbolic-ref", "--short", "HEAD")
    preserved, operations, backups = [], [], []
    trees = {tree.get("branch"): tree for tree in repo["worktrees"] if tree.get("branch")}
    branches = evidence.git(repo["root"], "for-each-ref", "--format=%(refname:short)", "refs/heads/").splitlines()
    for tree in repo["worktrees"]:
        if not tree.get("branch"):
            preserved.append({"kind": "worktree", "target": tree["path"], "reason": "detached-worktree"})
    for branch in sorted(branches):
        tree = trees.get(branch)
        target = tree["path"] if tree else None
        try:
            if target:
                _safe_path(target)
                # Distinct registered trees sharing a branch are ambiguous.
                if sum(t.get("branch") == branch for t in repo["worktrees"]) != 1:
                    raise EvidenceError("worktree-ambiguous")
            evidence.provider_reads = []
            decision = deletion_decision(evidence, repo, branch, target)
            if not decision.allowed:
                raise EvidenceError(decision.reason_code)
            owner = _ownership(repo, branch, target)
            if not owner:
                raise EvidenceError("target-unowned")
            recorded_path = owner.get("worktree", owner.get("path"))
            if not tree and recorded_path and os.path.lexists(recorded_path):
                raise EvidenceError("ownership-worktree-unregistered")
            ref_identity = _cleanup_ref_identity(evidence, repo["root"], "refs/heads/" + branch)
            if ref_identity["kind"] != "direct":
                raise EvidenceError("symbolic-ref-candidate" if ref_identity["kind"] == "symbolic" else "ref-identity-unknown")
            oid = ref_identity["oid"]
            provider = _cleanup_provider(evidence, repo, branch)
            if any(record["head"] != oid for record in provider["records"]):
                raise EvidenceError("provider-identity-mismatch")
            base_oid = evidence.git(repo["root"], "rev-parse", "--verify", "refs/heads/" + owner["base_branch"])
            common = {"branch": branch, "ref": "refs/heads/" + branch, "oid": oid,
                      "ref_identity": ref_identity, "base_oid": base_oid,
                      "ownership": owner, "cleanliness": "clean", "provider": provider}
            if target:
                operations.append(dict(common, kind="worktree_remove", target=target))
            operations.append(dict(common, kind="branch_delete", target="refs/heads/" + branch))
            paths = owner.get("backups", [])
            if not isinstance(paths, list) or any(not isinstance(p, str) for p in paths):
                preserved.append({"kind": "backup", "target": branch, "reason": "backup-ownership-invalid"})
            else:
                backups.extend((p, common) for p in paths)
        except (EvidenceError, OSError, ValueError, TypeError) as exc:
            preserved.append({"kind": "worktree" if target else "branch", "target": target or branch,
                              "reason": str(exc) or "evidence-unknown"})
    backup_ops = []
    roots = [str(Path(repo[p]) / ".workflow-backups") for p in ("root", "primary")]
    for value, common in sorted(backups, key=lambda item: item[0]):
        try:
            if not Path(value).is_absolute() or any(c in value for c in "*?["):
                raise EvidenceError("backup-path-invalid")
            path = _safe_path(value)
            if not any(path != root and _contains(root, path) for root in roots):
                raise EvidenceError("backup-root-unowned")
            if sum(canonical(p) == path for p, _ in backups) != 1:
                raise EvidenceError("backup-ownership-ambiguous")
            protected = [repo["root"], repo["common_dir"], *[t["path"] for t in repo["worktrees"]]]
            if any(_contains(path, p) for p in protected):
                raise EvidenceError("backup-protected-ancestor")
            if any(canonical(other) != path and (_contains(path, canonical(other)) or _contains(canonical(other), path))
                   for other, _ in backups):
                raise EvidenceError("backup-overlapping-targets")
            if Path(path).exists():
                backup_ops.append(dict(common, kind="backup_remove", target=path, digest=_backup_digest(path)))
        except (EvidenceError, OSError, ValueError, TypeError) as exc:
            preserved.append({"kind": "backup", "target": value, "reason": str(exc)})
    # Backups precede ref removal so every refresh can still prove their owner,
    # provider head and integration. Worktree removal always precedes its branch.
    operations = backup_ops + operations
    for root in sorted(set(roots)):
        try:
            _safe_path(root)
            if Path(root).exists():
                for child in sorted(Path(root).iterdir()):
                    # Owning a nested target does not authorize its container.
                    # Keep that ancestor visible before and after our own ref
                    # deletion, so genuine unrelated preserved drift still fails.
                    if not any(child == Path(canonical(value)) for value, _ in backups):
                        preserved.append({"kind": "backup", "target": str(child), "reason": "backup-unowned-or-ineligible"})
        except (EvidenceError, OSError) as exc:
            preserved.append({"kind": "backup", "target": root, "reason": str(exc)})
    body = {"schema_version": 1, "repository": identity, "generation": _cleanup_generation(repo),
            "operations": operations, "preserved": sorted(preserved, key=lambda row: (row["kind"], row["target"]))}
    return dict(body, snapshot_id=_digest(body))


def _read_approval(path):
    path = Path(_safe_path(path))
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise EvidenceError("approval-file-invalid")
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate-approval-key")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_pairs)


def _validate_approval(envelope, preview, approval_path):
    if not isinstance(envelope, dict) or set(envelope) != {"schema_version", "repository", "snapshot_id", "operations", "approval"}:
        raise EvidenceError("approval-envelope-invalid")
    if (type(envelope["schema_version"]) is not int or envelope["schema_version"] != 1 or
            envelope["repository"] != preview["repository"] or envelope["snapshot_id"] != preview["snapshot_id"] or
            envelope["operations"] != preview["operations"] or not preview["operations"]):
        raise EvidenceError("approval-list-or-snapshot-stale")
    approval = envelope["approval"]
    expected_text = "Approve exact cleanup snapshot " + preview["snapshot_id"]
    if (not isinstance(approval, dict) or set(approval) != {"text", "reference", "snapshot_id"} or
            approval["text"] != expected_text or approval["snapshot_id"] != preview["snapshot_id"] or
            not isinstance(approval["reference"], str) or not approval["reference"].strip() or
            len(approval["reference"]) > 4096):
        raise EvidenceError("exact-human-approval-required")
    targets = [(op["kind"], op["target"]) for op in preview["operations"]]
    if len(set(targets)) != len(targets):
        raise EvidenceError("duplicate-approval-operation")
    for op in preview["operations"]:
        if op["kind"] == "backup_remove" and _contains(op["target"], approval_path):
            raise EvidenceError("approval-file-within-target")


def _remove_backup(path):
    # Do not follow links or delegate deletion to a shell or forceful rmtree.
    _safe_path(path)
    item = Path(path)
    if item.is_dir():
        for child in sorted(item.iterdir()):
            _remove_backup(child)
        item.rmdir()
    else:
        item.unlink()


def _final_operation(evidence, repo_path, op):
    try:
        if op["kind"] == "branch_delete":
            identity = _cleanup_ref_identity(evidence, repo_path, op["ref"])
            refs = (op["ref"] + " " + identity["oid"] if identity["kind"] == "direct" else
                    "ref: " + identity["target"] if identity["kind"] == "symbolic" else "")
            return {"kind": op["kind"], "target": op["target"], "exists": identity["kind"] != "missing",
                    "identity": identity, "refs": refs}
        path = op["target"]
        row = {"kind": op["kind"], "target": path, "exists": os.path.lexists(path)}
        if op["kind"] == "worktree_remove":
            row["registered"] = any(tree["path"] == path for tree in evidence.repository(repo_path)["worktrees"])
        return row
    except (EvidenceError, OSError, ValueError):
        return {"kind": op["kind"], "target": op["target"], "exists": None, "reason": "final-state-unknown"}


def _final_preserved(evidence, repo_path, rows):
    result = []
    for row in rows:
        if "operation" in row:
            op = row["operation"]
        elif row["kind"] == "branch":
            op = {"kind": "branch_delete", "ref": "refs/heads/" + row["target"], "target": row["target"]}
        elif Path(row["target"]).is_absolute():
            op = {"kind": "worktree_remove" if row["kind"] == "worktree" else "backup_remove", "target": row["target"]}
        else:
            result.append({"target": row["target"], "exists": None, "reason": "final-state-unknown"})
            continue
        result.append(_final_operation(evidence, repo_path, op))
    return result


def cleanup_apply(repo_path, approval_path, evidence_runner=None, mutation_runner=None):
    """Consume exact approval under a common-dir lock; stop on partial failure."""
    result = {"schema_version": 1, "status": "refused", "removed": [], "failed": [], "preserved": [], "final_state": []}
    lock_fd, lock, receipt = None, None, None
    receipt_stream = None
    envelope, initial = None, None
    operations = []
    try:
        approval_path = _safe_path(approval_path)
        envelope = _read_approval(approval_path)
        initial = cleanup_preview(repo_path, evidence_runner)
        _validate_approval(envelope, initial, approval_path)
        operations = initial["operations"]
        storage = _cleanup_storage(initial["repository"])
        storage.mkdir(exist_ok=True)
        lock = storage / "lock"
        _safe_path(lock)
        lock_fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        fresh = cleanup_preview(repo_path, evidence_runner)
        _validate_approval(envelope, fresh, approval_path)
        # Approval payload itself is pinned, including provenance reference.
        if _read_approval(approval_path) != envelope:
            raise EvidenceError("approval-file-changed")
        receipts = storage / "receipts"
        _safe_path(receipts)
        receipts.mkdir(exist_ok=True)
        receipt_path = receipts / (initial["snapshot_id"] + ".json")
        _safe_path(receipt_path)
        receipt_stream = receipt_path.open("x+", encoding="utf-8")
        receipt = receipt_path
        json.dump({"schema_version": 1, "snapshot_id": initial["snapshot_id"],
                   "approval_digest": _digest(envelope), "status": "consumed"}, receipt_stream)
        receipt_stream.flush()
        os.fsync(receipt_stream.fileno())
        result["preserved"] = initial["preserved"]
        runner = mutation_runner or run_evidence
        for index, op in enumerate(operations):
            try:
                current = cleanup_preview(repo_path, evidence_runner)
                if (current["repository"] != initial["repository"] or current["operations"] != operations[index:] or
                        current["preserved"] != initial["preserved"] or
                        _read_approval(approval_path) != envelope):
                    raise EvidenceError("cleanup-state-stale")
                evidence = Evidence(evidence_runner)
                if op["kind"] == "worktree_remove":
                    argv = ["git", "worktree", "remove", "--", op["target"]]
                elif op["kind"] == "branch_delete":
                    if any(tree.get("branch") == op["branch"] for tree in evidence.repository(repo_path)["worktrees"]):
                        raise EvidenceError("branch-still-checked-out")
                    if _cleanup_ref_identity(evidence, repo_path, op["ref"]) != op["ref_identity"]:
                        raise EvidenceError("ref-identity-stale")
                    # --no-deref binds the mutation to the approved name even
                    # if an uncooperative writer aliases it after inspection.
                    argv = ["git", "update-ref", "-d", "--no-deref", op["ref"], op["oid"]]
                elif op["kind"] == "backup_remove":
                    if _backup_digest(op["target"]) != op["digest"]:
                        raise EvidenceError("backup-content-stale")
                    _remove_backup(op["target"])
                    argv = None
                else:
                    raise EvidenceError("cleanup-operation-unsupported")
                if argv:
                    outcome = runner(argv, str(repo_path))
                    if outcome.returncode:
                        raise EvidenceError("cleanup-command-failed")
                state = _final_operation(Evidence(evidence_runner), repo_path, op)
                if state["exists"] is not False or state.get("registered", False):
                    raise EvidenceError("cleanup-readback-failed")
                result["removed"].append(op)
            except (EvidenceError, OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
                result["failed"].append({"operation": op, "reason": str(exc) or "cleanup-failed"})
                result["preserved"].extend({"operation": pending, "reason": "stopped-after-failure"} for pending in operations[index + 1:])
                break
        result["status"] = "complete" if not result["failed"] else "partial"
    except (EvidenceError, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        result["reason"] = str(exc) or "cleanup-refused"
        if initial:
            result["preserved"] = initial["preserved"] + [{"operation": op, "reason": "apply-refused"} for op in operations]
    finally:
        if operations:
            result["final_state"] = [_final_operation(Evidence(evidence_runner), repo_path, op) for op in operations]
        result["final_preserved"] = _final_preserved(Evidence(evidence_runner), repo_path, result["preserved"])
        if receipt:
            try:
                # A consumed receipt survives failure/crash; retry needs a new
                # preview including its changed receipt generation and approval.
                receipt_stream.seek(0)
                receipt_stream.truncate()
                receipt_stream.write(_json_bytes({"schema_version": 1, "snapshot_id": initial["snapshot_id"],
                    "approval_digest": _digest(envelope), "outcome": result}).decode("utf-8"))
                receipt_stream.flush()
                os.fsync(receipt_stream.fileno())
            except OSError:
                result["status"] = "partial"
                result["receipt_error"] = "outcome-write-failed; approval-remains-consumed"
        if receipt_stream is not None:
            try:
                receipt_stream.close()
            except OSError:
                result["status"] = "partial"
                result["receipt_error"] = "receipt-close-failed; approval-remains-consumed"
        if lock_fd is not None:
            os.close(lock_fd)
            try:
                lock.unlink()
            except OSError:
                result["lock_error"] = "lock-release-failed"
    return result
