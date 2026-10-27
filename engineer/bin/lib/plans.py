"""Read task XML fragments without executing their commands."""
from pathlib import Path
import re
import json
import shlex
from .core import Failure, read, root, safe_path
from .text import split_frontmatter
from . import frontmatter, records


def tasks(content):
    result = []
    for match in re.finditer(r"<task\b([^>]*)>(.*?)</task>", content, re.S):
        attrs = dict(re.findall(r'([\w-]+)=["\']([^"\']*)["\']', match.group(1)))
        task = {"type": attrs.get("type", "auto"), "tdd": attrs.get("tdd", "false").lower() == "true",
                "gate": attrs.get("gate"), "auto_select": attrs.get("auto_select"),
                "options": [{"id": item[1], "body": item[2].strip()} for item in re.finditer(r"<option\b[^>]*\bid=[\"']([^\"']+)[\"'][^>]*>(.*?)</option>", match.group(2), re.S)]}
        for name in ("name", "files", "read_first", "action", "verify", "done", "decision", "resume-signal", "how-to-verify"):
            child = re.search(rf"<{name}\b[^>]*>(.*?)</{name}>", match.group(2), re.S)
            task[name] = child.group(1).strip() if child else ""
        result.append(task)
    return result


def structure(args):
    path = safe_path(args.need())
    if not path.is_file():
        raise Failure("file-not-found", str(path))
    return {"tasks": tasks(read(path)), "count": len(tasks(read(path)))}


def validate(args):
    path = safe_path(args.need())
    if not path.is_file():
        raise Failure("file-not-found", str(path))
    metadata, body = split_frontmatter(read(path))
    findings = frontmatter.errors(metadata, "plan")+frontmatter.path_errors(path, metadata, "plan")
    parsed = tasks(body)
    if not parsed:
        findings.append("Plan has no tasks")
    for index, task in enumerate(parsed, 1):
        if task["type"].startswith("checkpoint:"):
            if task["type"] == "checkpoint:decision":
                ids = [option["id"] for option in task["options"]]
                if not ids or len(ids) != len(set(ids)):
                    findings.append(f"Task {index}: decision options require unique declared IDs")
                if task["auto_select"] is not None and task["auto_select"] not in ids:
                    findings.append(f"Task {index}: auto_select must name an actual declared option ID")
            elif task["auto_select"] is not None:
                findings.append(f"Task {index}: auto_select requires checkpoint:decision")
            continue
        for key in ("files", "action", "verify", "done"):
            if not task[key]:
                findings.append(f"Task {index}: missing {key}")
    return {"valid": not findings, "errors": findings, "task_count": len(parsed)}, int(bool(findings))


def plan_paths(args):
    if args.has("plan"):
        return [safe_path(args.get("plan"))]
    if args.has("dir"):
        return sorted(safe_path(args.get("dir")).glob("*-PLAN.md"))
    candidate = args.arg(0, args.get("phase"))
    if candidate and str(candidate).endswith(".md"):
        return [safe_path(candidate)]
    return sorted(records.phase_dir(candidate).glob("*-PLAN.md"))


def check(args, kind):
    findings, known, commands = [], set(), []
    paths = plan_paths(args)
    if not paths:
        raise Failure("plans-not-found", "No PLAN files found")
    for path in paths:
        for index, task in enumerate(tasks(read(path)), 1):
            verify = task["verify"]
            automated = re.findall(r"<automated\b[^>]*>(.*?)</automated>", verify, re.S)
            command = "\n".join(value.strip() for value in automated) if automated else verify
            if kind == "failure-directions" and (automated or "<fails_when" in verify):
                rows = failing_directions(verify)
                for row in rows:
                    entry = {"plan": str(path), "task": index, **row}
                    commands.append(entry)
                    if entry["severity"] != "none":
                        findings.append(entry)
            created = set(re.split(r"[,\s]+", task["files"].strip())) - {""}
            if kind == "failure-directions":
                reasons = []
                if re.search(r"\|\|\s*(?:true|:)(?:\s|$)", command):
                    reasons.append("failure is swallowed")
                if re.match(r"^\s*(?:echo|printf)\b", command):
                    reasons.append("command only prints text")
                if re.search(r"(?:^|[;\n])\s*grep\b", command) and not re.search(r"\bgrep\s+(?:-[^\s]*q\b|--quiet\b)", command):
                    reasons.append("grep must use a quiet assertion with explicit failure direction")
                if reasons:
                    findings.append({"plan": str(path), "task": index, "command": command, "reasons": reasons, "reason": "; ".join(reasons), "severity": "blocker", "status": "unsafe_failure_direction"})
            else:
                for candidate in automated or [command]:
                    for row in command_paths(candidate.strip(), known, created):
                        entry = {"plan": str(path), "task": index, **row}
                        commands.append(entry)
                        if entry["severity"] != "none":
                            findings.append(entry)
            known.update(created)
    blocking = any(item.get("severity", "blocker") == "blocker" for item in findings)
    return {"valid": not blocking, "findings": findings, "commands": commands, "readError": None}, int(blocking)


def failing_directions(verify):
    """Bind the first fails_when to the nearest preceding automated command."""
    rows, current = [], None
    for match in re.finditer(r"<(automated|fails_when)\b[^>]*>(.*?)</\1>", verify, re.S):
        value = match[2].strip()
        if match[1] == "automated":
            sentinel = bool(re.match(r"MISSING\s*[—–-]\s*Wave\s+0\b", value, re.I))
            current = {"command": value, "fails_when": None, "status": "sentinel" if sentinel else "missing", "severity": "none" if sentinel else "blocker", "reason": "non-runnable Wave 0 placeholder" if sentinel else "No stated failing direction"}
            rows.append(current)
        elif current is None:
            rows.append({"command": None, "fails_when": value, "status": "orphan", "severity": "warning", "reason": "No preceding automated command"})
        elif current["fails_when"] is None:
            current["fails_when"] = value
            if current["status"] == "sentinel":
                continue
            placeholder = re.fullmatch(r"(?i)(?:TBD|TODO|FIXME|N/?A|\[.*\]|\.\.\.)[.!]?", value)
            status = "empty" if not value else "placeholder" if placeholder else "ok"
            current.update(status=status, severity="none" if status == "ok" else "blocker", reason="Stated failing direction" if status == "ok" else "Blank failing direction" if status == "empty" else "Placeholder failing direction")
    return rows


def command_paths(command, known, created):
    """Inspect literal cwd/prefix and file targets without executing PLAN text."""
    def row(target, status, severity="none", reason=None):
        return {"command": command, "path": target, "target": target, "status": status, "severity": severity, "reason": reason or status}
    if re.match(r"MISSING\b", command):
        return [row(None, "sentinel")]
    try:
        tokens = shlex.split(command)
    except ValueError as exc:
        return [row(None, "unresolvable", "warning", str(exc))]
    targets, directory, npm = [], None, False
    if tokens[:1] == ["cd"] and len(tokens) > 1:
        directory = tokens[1]
    elif tokens[:1] == ["npm"] and "--prefix" in tokens:
        index = tokens.index("--prefix")
        directory = tokens[index+1] if len(tokens) > index+1 else ""
        npm = True
    pending = set(known)
    # Only earlier task outputs justify a directory being created before this command.
    if directory is not None:
        if not directory or re.search(r"[$*?`~]", directory):
            return [row(directory, "unresolvable", "warning", "dynamic_path")]
        try:
            target = safe_path(directory)
        except Failure:
            return [row(directory, "unresolvable", "warning", "outside_root")]
        if not target.is_dir():
            prefix = directory.removeprefix("./").rstrip("/")+"/"
            if any(value.startswith(prefix) for value in pending):
                return [row(directory, "pending_creation")]
            return [row(directory, "missing", "blocker", "directory_missing")]
        targets.append(row(directory, "resolved"))
        if npm:
            manifest = target/"package.json"
            try:
                package = json.loads(read(manifest))
                if not isinstance(package, dict):
                    raise ValueError("manifest must be an object")
            except (ValueError, OSError):
                return [row(directory, "unresolvable", "warning", "manifest_unreadable")]
            tail = tokens[tokens.index("--prefix")+2:]
            if tail:
                script = tail[1] if tail[0] == "run" and len(tail)>1 else tail[0]
                if script not in ("install", "ci", "exec") and script not in package.get("scripts", {}):
                    return [row(directory, "unresolvable", "warning", "script_missing")]
        return targets
    for token in tokens:
        token = token.rstrip(";,")
        if token.startswith(("-", "$", "http:", "https:")) or re.search(r"[|><*?]", token):
            continue
        if not re.search(r"[/\\]|\.(?:py|sh|js|ts|json|ya?ml|toml|md|go|rs|xml)$", token):
            continue
        normalized = token.removeprefix("./")
        if normalized in known or normalized in created:
            targets.append(row(token, "pending_creation"))
            continue
        try:
            target = safe_path(normalized)
        except Failure:
            targets.append(row(token, "unresolvable", "warning", "outside_root"))
            continue
        targets.append(row(token, "resolved") if target.exists() else row(token, "missing", "blocker", "unresolvable-path"))
    return targets or [row(None, "unrecognized")]
