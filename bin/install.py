"""Install the repository-root workflow into Claude or Codex using Python 3.11+."""
from __future__ import annotations
import argparse
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import tomllib

# Preview and migration imports must never write into the installed tree.
sys.dont_write_bytecode = True

PREFIXES = ("agents", "commands", "engineer", "hooks", "scripts", "skills", "bin")
HOSTS = ("claude", "codex")
AGENT_MARKER = "<!-- ai-engineering-template -->"
AGENT_END = "<!-- /ai-engineering-template -->"
IGNORE_BLOCK = "\n# Engineering workflow local state\n.workflow-backups/\n.worktrees/\n.planning/handoffs/\n"
STALE_SCRIPTS = {"worktree-guard.sh", "destructive-git-guard.py", "gsd-check-update.js", "gsd-agent-isolation-guard.js", "isolation-sentinel.js"}
MANAGED_HOOKS = {
    "PreToolUse": [(r"^(Bash|exec_command|shell_command|shell)$", "planning-integrity.sh", 10),
                   (r"^(Agent|Task|Write|Edit|MultiEdit|NotebookEdit|apply_patch)$", "worktree-path-guard.py", 10)],
    "PostToolUse": [(r"^(Bash|Write|Edit|MultiEdit|NotebookEdit|apply_patch)$", "ai-tier-notice.sh", 10),
                    (r"^(Bash|Write|Edit|MultiEdit|NotebookEdit|apply_patch|Agent|Task)$", "context-handoff.sh", 10)],
    "SubagentStop": [("", "context-handoff.sh", 10)],
    "Stop": [("", "context-handoff.sh", 10)],
}
HOST_HOOKS = {"codex": {"SessionStart": [("", "context-handoff.sh", 10)]}, "claude": {
    "WorktreeCreate": [("", "worktree-location.sh", 180)], "WorktreeRemove": [("", "worktree-location.sh", 60)]}}


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def load_module(name):
    path = Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location("engineer_install_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def skill_root(host):
    if host not in HOSTS:
        raise ValueError("host must be claude or codex")
    return ".claude/skills" if host == "claude" else ".agents/skills"


def linked(path):
    try:
        return path.is_symlink() or bool(path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except AttributeError:
        return path.is_symlink()
    except FileNotFoundError:
        return False


def destination(root, relative):
    """Resolve portable owned paths without following links or accepting drive aliases."""
    root = Path(root).resolve()
    if not isinstance(relative, str) or not relative or "\\" in relative or ":" in relative or any(part in ("", ".", "..") for part in relative.split("/")):
        raise ValueError("unsafe destination path: " + str(relative))
    parts = PurePosixPath(relative).parts
    if PurePosixPath(relative).is_absolute() or any(p in (".", "..", "") for p in parts):
        raise ValueError("unsafe destination path: " + relative)
    path = root
    for part in parts:
        path = path / part
        if linked(path):
            raise ValueError("linked path refused: " + str(path))
        if path != root / relative and path.exists() and not path.is_dir():
            raise ValueError("file used as parent: " + str(path))
    return path


def utf8(data, label):
    try:
        text = data.decode("utf-8-sig")
        if "\x00" in text:
            raise UnicodeError("NUL in text")
        return text
    except UnicodeError as exc:
        raise ValueError(label + " must be UTF-8") from exc


def same_text(a, b):
    if a == b:
        return True
    try:
        if a is None or b is None or b"\0" in a or b"\0" in b:
            return False
        left, right = a.decode("utf-8"), b.decode("utf-8")
        if re.search(r"\r(?!\n)", left) or re.search(r"\r(?!\n)", right):
            return False
        return left.replace("\r\n", "\n") == right.replace("\r\n", "\n")
    except UnicodeError:
        return False


def render_asset(relative, data, host):
    """Render full methods, replacing only host paths and generated metadata."""
    skill_root(host)
    if Path(relative).suffix not in (".md", ".toml", ".yaml", ".yml", ".sh", ".txt"):
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeError:
        return data
    if "\x00" in text:
        return data
    namespace = "." + host
    if "skills/" in relative:
        skill_namespace = "../../" if host == "claude" else "../../../.codex/"
        def skill_link(match):
            suffix = match[1]
            if suffix.split("/", 1)[0] in ("templates", "workflows", "references", "guides", "rules", "RULES.md"):
                suffix = "engineer/" + suffix
            elif suffix.startswith("runtime/"):
                suffix = "engineer/bin/" + suffix[len("runtime/"):]
            return skill_namespace + suffix
        text = re.sub(r"(?:\.\./)+\.ai/([\w./-]+)", skill_link, text)
    for prefix in ("engineer", "agents", "commands", "hooks", "scripts", "bin"):
        text = re.sub(r"(?<![\w./-])" + prefix + r"/", namespace + "/" + prefix + "/", text)
    text = text.replace(".agents/skills/", skill_root(host) + "/").replace(".claude/skills/", skill_root(host) + "/")
    if host == "claude":
        text = text.replace("AGENTS.md", "CLAUDE.md")
        text = text.replace(".claude/agents/code-fixer.md", ".claude/engineer/references/code-fixer.md")
        if relative.startswith("agents/"):
            text = text.replace("](code-fixer.md)", "](../engineer/references/code-fixer.md)")
        if relative == "agents/code-fixer.md":
            text = text.replace("../engineer/", "../")
    if re.search(r"(?:^|/)agents/[^/]+\.md$", relative) and text.startswith("---"):
        bits = text.split("---", 2)
        if len(bits) == 3:
            header = re.sub(r"^(?:model|effort|maxTurns|model_reasoning_effort):[^\r\n]*(?:\r?\n|$)", "", bits[1], flags=re.M)
            role = Path(relative).stem
            header = re.sub(r"^name: (?:coder|phase-preparer|phase-checker|researcher)[ \t]*$", "name: " + role, header, flags=re.M)
            if host == "claude":
                defaults = {"scout": ("haiku", None), "targeted-fixer": ("haiku", None), "executor": ("sonnet", None), "planner": ("opus", "medium")}
                model, effort = defaults.get(role, (None, None))
                if model:
                    header += "model: " + model + "\n"
                if effort:
                    header += "effort: " + effort + "\n"
            text = "---" + header + "---" + bits[2]
    return text.encode("utf-8")


def agent_native(role, description="Engineering workflow role", method=""):
    model = "gpt-6-luna" if role in ("scout", "targeted-fixer") else "gpt-6.1-sol"
    effort = "medium" if role in ("executor", "doc-verifier", "integration-checker") else "high"
    lines = ["name = " + json.dumps(role), "description = " + json.dumps(description),
             "model = " + json.dumps(model), "model_reasoning_effort = " + json.dumps(effort),
             "developer_instructions = " + json.dumps("Follow the complete method at .codex/agents/" + role + ".md.\n\n" + method)]
    if role == "scout":
        lines.append('sandbox_mode = "read-only"')
    return ("\n".join(lines) + "\n").encode()


def hook_settings(host):
    events = {}
    for event, records in {**MANAGED_HOOKS, **HOST_HOOKS[host]}.items():
        groups = []
        for matcher, script, timeout in records:
            root = '"$(git rev-parse --show-toplevel)/.' + host + '/hooks/'
            command = 'bash ' + root + ("python-hook.sh\" " + script if script.endswith(".py") else script + '"')
            handler = {"type": "command", "command": command, "timeout": timeout}
            if host == "codex":
                handler["commandWindows"] = "python (Join-Path (git rev-parse --show-toplevel) '.codex/hooks/" + script.removesuffix(".sh").removesuffix(".py") + ".py'); exit $LASTEXITCODE"
            group = {"hooks": [handler]}
            if matcher:
                group["matcher"] = matcher
            groups.append(group)
        events[event] = groups
    return {"hooks": events}


def managed_scripts():
    return {row[1] for rows in MANAGED_HOOKS.values() for row in rows} | {"worktree-location.sh"} | STALE_SCRIPTS


def managed_command(command):
    return any(re.search(r"(?:/|\\)hooks(?:/|\\)" + re.escape(name) + r"(?:[\s\"']|$)", command) for name in managed_scripts()) or ("python-hook.sh" in command and "worktree-path-guard.py" in command)


def merge_events(existing, incoming):
    validate_events(existing)
    validate_events(incoming)
    result = {}
    for event in sorted(existing.keys() | incoming.keys()):
        keep = []
        for group in existing.get(event, []):
            handlers = group.get("hooks", [])
            managed = [h for h in handlers if managed_command(h.get("command", ""))]
            if managed and len(managed) != len(handlers):
                raise ValueError("managed registration shares a group with a user hook: " + event)
            if not managed:
                keep.append(group)
        result[event] = keep + incoming.get(event, [])
    return {event: groups for event, groups in result.items() if groups}


def validate_events(events):
    if not isinstance(events, dict):
        raise ValueError("host settings hooks must be a mapping")
    for event, groups in sorted(events.items()):
        if not isinstance(groups, list):
            raise ValueError("host settings event groups must be arrays: " + event)
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                raise ValueError("host settings hook group must contain a hooks array")
            for handler in group["hooks"]:
                if not isinstance(handler, dict) or not isinstance(handler.get("type"), str):
                    raise ValueError("host settings hook handler must have a type")
                if handler["type"] == "command" and (not isinstance(handler.get("command"), str) or not handler["command"]):
                    raise ValueError("host settings command hook must have a command")


def unique_json(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError("host settings duplicate key: " + key)
        value[key] = child
    return value


def settings_json(raw):
    value = json.loads(raw, object_pairs_hook=unique_json,
                       parse_constant=lambda word: (_ for _ in ()).throw(ValueError("host settings invalid constant: " + word)))
    if not isinstance(value, dict):
        raise ValueError("host settings must be an object")
    validate_events(value.get("hooks", {}))
    return value


def hooks_toml(events):
    lines = []
    for event, groups in sorted(events.items()):
        for group in groups:
            lines.append("[[hooks." + event + "]]")
            if "matcher" in group:
                lines.append("matcher = " + json.dumps(group["matcher"]))
            for hook in group.get("hooks", []):
                lines.append("[[hooks." + event + ".hooks]]")
                for key, value in hook.items():
                    lines.append(key + " = " + (str(value) if isinstance(value, int) else json.dumps(value)))
            lines.append("")
    return ("\n".join(lines) + "\n").encode()


def toml_lines(text):
    """Yield real statement lines, excluding comments and multiline string contents."""
    state = None
    for index, line in enumerate(text.splitlines(keepends=True)):
        inside = state in ('"""', "'''")
        yield index, line, inside
        pos = 0
        while pos < len(line):
            if state in ('"""', "'''"):
                if state == '"""' and line[pos] == "\\":
                    pos += 2
                elif line.startswith(state, pos):
                    quote = state[0]
                    while pos < len(line) and line[pos] == quote:
                        pos += 1
                    state = None
                else:
                    pos += 1
            elif state in ('"', "'"):
                if state == '"' and line[pos] == "\\":
                    pos += 2
                elif line[pos] == state:
                    state = None
                    pos += 1
                else:
                    pos += 1
            elif line[pos] == "#":
                break
            elif line.startswith('"""', pos) or line.startswith("'''", pos):
                state = line[pos:pos + 3]
                pos += 3
            elif line[pos] in "\"'":
                state = line[pos]
                pos += 1
            else:
                pos += 1


def remove_toml_groups(text, events):
    """Remove only exact or recognizable managed hook groups, preserving other text."""
    lines = text.splitlines(keepends=True)
    headers = [(i, re.match(r"\s*\[\[hooks\.([\w-]+)\]\]", line))
               for i, line, inside in toml_lines(text) if not inside]
    headers = [(i, m[1]) for i, m in headers if m]
    remove = set()
    for start, event in headers:
        end = len(lines)
        for i, line, inside in toml_lines(text):
            if i > start and not inside and re.match(r"\s*\[", line) and not re.match(r"\s*\[\[hooks\." + re.escape(event) + r"\.hooks\]\]", line):
                end = i
                break
        fragment = "".join(lines[start:end])
        parsed = tomllib.loads(fragment).get("hooks", {}).get(event, [])
        if parsed and any(group in events.get(event, []) for group in parsed):
            remove.update(range(start, end))
    return "".join(line for i, line in enumerate(lines) if i not in remove)


def merge_codex_config(original, incoming, label="config.toml"):
    text = utf8(original, label)
    try:
        current = tomllib.loads(text)
        desired = tomllib.loads(incoming.decode())
    except tomllib.TOMLDecodeError as exc:
        raise ValueError("host settings " + label + " invalid TOML: " + str(exc)) from exc
    validate_events(current.get("hooks", {}))
    if not isinstance(current.get("agents", {}), dict):
        raise ValueError(label + " agents must be a table; nothing was installed")
    for _, line, inside in toml_lines(text):
        if not inside and re.match(r'\s*agents\s*=\s*\{', line):
            raise ValueError(label + " inline agents table is unsupported; nothing was installed")
    for key_name in ("max_threads", "max_concurrent_threads_per_session"):
        value = current.get("agents", {}).get(key_name)
        if value is not None and (type(value) is not int or value < 1):
            raise ValueError(label + " concurrency must be a positive integer; nothing was installed")
    lines = text.splitlines(keepends=True)
    remove, replace = set(), {}
    group = ""
    cap_done = False
    key = r'(?:"max_concurrent_threads_per_session"|\'max_concurrent_threads_per_session\'|max_concurrent_threads_per_session|"max_threads"|\'max_threads\'|max_threads)'
    for i, line, inside in toml_lines(text):
        if inside:
            continue
        header = re.match(r'\s*\[([^\]]+)\]', line)
        if header:
            group = header[1].strip().strip('"\'')
        match = re.match(r'^(\s*)(?:(?:agents|"agents"|\'agents\')\.)?' + key + r'\s*=\s*([^#\r\n]*)(.*)$', line.rstrip('\r\n'))
        is_dotted = re.match(r'\s*(?:agents|"agents"|\'agents\')\.', line)
        if match and (group == "agents" or is_dotted):
            if not cap_done:
                prefix = "agents." if is_dotted else ""
                replace[i] = match[1] + prefix + "max_concurrent_threads_per_session = 12" + re.search(r"[ \t]*$", match[2])[0] + match[3] + ("\r\n" if line.endswith("\r\n") else "\n")
                cap_done = True
            else:
                remove.add(i)
    text = "".join(replace.get(i, line) for i, line in enumerate(lines) if i not in remove)
    if not cap_done:
        newline = "\r\n" if "\r\n" in text else "\n"
        headers = [(i, line) for i, line, inside in toml_lines(text) if not inside and re.match(r'\s*\[(?:agents|"agents"|\'agents\')\]\s*(?:#.*)?$', line.rstrip())]
        if headers:
            lines = text.splitlines(keepends=True)
            index = headers[0][0] + 1
            if index and not lines[index - 1].endswith(("\n", "\r")):
                lines[index - 1] += newline
            lines.insert(index, "max_concurrent_threads_per_session = 12" + newline)
            text = "".join(lines)
        else:
            statements = [(i, line) for i, line, inside in toml_lines(text) if not inside]
            first_table = next((i for i, line in statements if re.match(r"\s*\[", line)), len(text.splitlines()))
            root_dotted = any(i < first_table and re.match(r"\s*(?:agents|\"agents\"|'agents')\.", line)
                              for i, line in statements)
            if root_dotted:
                lines = text.splitlines(keepends=True)
                if first_table and not lines[first_table - 1].endswith(("\n", "\r")):
                    lines[first_table - 1] += newline
                lines.insert(first_table, "agents.max_concurrent_threads_per_session = 12" + newline)
                text = "".join(lines)
            else:
                text += ("" if text.endswith("\n") or not text else newline) + "[agents]" + newline + "max_concurrent_threads_per_session = 12" + newline
    if "hooks" in desired:
        old_hooks = current.get("hooks", {})
        merged = merge_events(old_hooks, desired["hooks"])
        if merged == old_hooks:
            bom = b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b""
            return bom + text.encode()
        removable = {}
        for event, groups in old_hooks.items():
            removable[event] = [g for g in groups if any(managed_command(h.get("command", "")) for h in g.get("hooks", []))]
        text = remove_toml_groups(text, removable)
        added = {event: [g for g in groups if g not in old_hooks.get(event, []) or g in desired["hooks"].get(event, [])]
                 for event, groups in merged.items()}
        if any(added.values()):
            text = text + ("\n" if text.endswith("\n") else "\n\n") + hooks_toml(added).decode()
    tomllib.loads(text)
    bom = b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b""
    return bom + text.encode()


def managed_block(text):
    if text.count(AGENT_MARKER) != text.count(AGENT_END) or text.count(AGENT_MARKER) > 1:
        raise ValueError("ambiguous managed entry block")
    if AGENT_MARKER not in text:
        return None
    a, b = text.index(AGENT_MARKER), text.index(AGENT_END) + len(AGENT_END)
    if b < a:
        raise ValueError("ambiguous managed entry block")
    return text[a:b]


def merge_entry(original, incoming):
    before, new = utf8(original, "agent entry"), utf8(incoming, "incoming entry")
    block = managed_block(before)
    new_block = managed_block(new)
    if not new_block:
        raise ValueError("incoming managed entry block missing")
    if block:
        result = before.replace(block, new_block, 1)
    else:
        separator = "" if before.endswith("\n\n") else "\n" if before.endswith("\n") else "\n\n"
        result = before + separator + new_block + "\n"
    bom = b"\xef\xbb\xbf" if original.startswith(b"\xef\xbb\xbf") else b""
    return bom + result.encode()


def host_payload(host, hooks=True):
    ns = "." + host
    entry = "CLAUDE.md" if host == "claude" else "AGENTS.md"
    block = (AGENT_MARKER + "\nRead " + ns + "/engineer/RULES.md, the assigned command and " + ns + "/agents/AGENT.md.\n"
             "The coordinator owns shared planning records through engineer_run query; phase implementation requires explicit authorization.\n" + AGENT_END + "\n")
    result = {entry: block.encode(), ".gitignore": IGNORE_BLOCK.encode()}
    if host == "codex":
        result[ns + "/config.toml"] = b"[agents]\nmax_concurrent_threads_per_session = 12\n" + (hooks_toml(hook_settings(host)["hooks"]) if hooks else b"")
    elif hooks:
        result[ns + "/settings.json"] = json_bytes(hook_settings(host))
    return result


def inventory(root, mode="source"):
    root = Path(root)
    prefixes = PREFIXES if mode == "source" else (".claude", ".codex", ".agents/skills")
    result = {}
    for prefix in prefixes:
        folder = root / prefix
        if linked(folder):
            raise ValueError("linked path refused: " + str(folder))
        if not folder.exists():
            continue
        for path in folder.rglob("*"):
            if linked(path):
                raise ValueError("linked path refused: " + str(path))
            if path.is_file() and not any(p in {"__pycache__", ".git", "node_modules"} for p in path.parts) and path.suffix != ".pyc":
                result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def payload(source, host, hooks=True):
    source = Path(source)
    if not (source / "engineer/bin/engineer.py").is_file():
        raise ValueError("source requires engineer/bin/engineer.py")
    result = {}
    for relative, data in inventory(source).items():
        if relative.startswith("bin/install-assets/") or relative in {"skills/SKILL", "bin/generate-assets.py"} or (relative.startswith("agents/") and Path(relative).stem.startswith("gsd-")):
            continue
        dest = skill_root(host) + relative[len("skills"):] if relative.startswith("skills/") else "." + host + "/" + relative
        if host == "claude" and relative == "agents/code-fixer.md":
            dest = ".claude/engineer/references/code-fixer.md"
        result[dest] = render_asset(relative, data, host)
        if host == "codex" and relative.startswith("agents/") and relative.endswith(".md") and Path(relative).stem not in {"AGENT", "code-fixer"}:
            role = Path(relative).stem
            description = re.search(r"^description: (.+)$", data.decode("utf-8"), flags=re.M)
            result[".codex/agents/" + role + ".toml"] = agent_native(role, description[1] if description else role, result[dest].decode("utf-8"))
    # A copied source can omit native skills or carry only its placeholder. Every
    # command still exports its complete method, never a shortened redirect.
    for command in sorted((source / "commands").glob("*.md")):
        key = skill_root(host) + "/" + command.stem + "/SKILL.md"
        if key not in result:
            result[key] = render_asset("commands/" + command.name, command.read_bytes(), host)
    result.update(host_payload(host, hooks))
    entry_asset = source / "bin/install-assets/agent-entry.txt"
    if entry_asset.is_file():
        text = render_asset("agent-entry.txt", entry_asset.read_bytes(), host)
        entry_name = "CLAUDE.md" if host == "claude" else "AGENTS.md"
        result[entry_name] = AGENT_MARKER.encode() + b"\n" + text.rstrip() + b"\n" + AGENT_END.encode() + b"\n"
    for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE"):
        path = source / "bin/install-assets" / (name + ".txt")
        if path.is_file():
            result[".planning/" + name + ".md"] = path.read_bytes()
    config = source / "engineer/templates/config.yaml"
    if config.is_file():
        result[".planning/config.yaml"] = config.read_bytes().replace(b"  isolation: worktree", b"  isolation: auto")
    for name in ("todos/pending/.gitkeep", "todos/completed/.gitkeep", "milestones/.gitkeep"):
        result[".planning/" + name] = b""
    result[".planning/todos/README.md"] = b"# Project todos\n\nCapture actual project ideas through engineer_run query todo.add.\n"
    return result


def merge_file(name, before, candidate, host, hooks=True):
    if name in ("AGENTS.md", "CLAUDE.md"):
        return merge_entry(before, candidate)
    if name == ".gitignore":
        text = utf8(before, name)
        missing = [line for line in candidate.decode().splitlines() if line and not line.startswith("#") and line not in text.splitlines()]
        return before if not missing else before + (b"" if before.endswith(b"\n") else b"\n") + ("\n".join(missing) + "\n").encode()
    if name == ".codex/config.toml":
        return merge_codex_config(before, candidate, name)
    if name == ".claude/settings.json":
        try:
            old = settings_json(utf8(before, name))
        except (ValueError, TypeError) as exc:
            raise ValueError("invalid host settings for Claude: " + str(exc)) from exc
        old["hooks"] = merge_events(old.get("hooks", {}), json.loads(candidate).get("hooks", {}))
        return json_bytes(old)
    return candidate


def plan_install(source, target, host="codex", hooks=True, **kwargs):
    target = Path(target).resolve()
    if linked(target / ".ai"):
        raise ValueError("linked path refused: .ai")
    if (target / ".ai").exists():
        raise ValueError("legacy .ai requires explicit migration first")
    other = ".claude" if host == "codex" else ".codex"
    if (target / other / "engineer/bin/engineer.py").exists():
        raise ValueError("second host installation conflicts")
    changes, originals = [], {}
    ownership = load_module("update").load_manifest(target, host)["files"]
    for name, candidate in payload(source, host, hooks).items():
        path = destination(target, name)
        if path.exists() and not path.is_file():
            raise ValueError("directory occupies installed file: " + name)
        before = path.read_bytes() if path.is_file() else None
        if before is not None:
            if name.startswith(".planning/"):
                continue
            if name in ("AGENTS.md", "CLAUDE.md", ".gitignore", ".codex/config.toml", ".claude/settings.json"):
                candidate = merge_file(name, before, candidate, host, hooks)
                record = ownership.get(name)
                if record and digest(before) != record.get("installed_sha256") and not same_text(before, candidate):
                    raise ValueError("customized managed entry or host registration; reconcile with reviewed update: " + name)
            elif not same_text(before, candidate):
                raise ValueError("conflict at " + name + "; use reviewed update")
        if before is None or not same_text(before, candidate):
            changes.append((path, candidate))
            if before is not None:
                originals[path] = before
    return changes, originals, {"host": host, "target": str(target)}


def backup_migration(target, originals):
    target = Path(target).resolve()
    backup = destination(target, ".workflow-backups/" + time.strftime("%Y%m%d-%H%M%S") + "-" + str(time.time_ns()))
    backup.mkdir(parents=True)
    manifest = {}
    for original, data in originals.items():
        path = Path(original)
        relative = path.relative_to(target).as_posix()
        saved = destination(backup, "files/" + relative)
        saved.parent.mkdir(parents=True, exist_ok=True)
        saved.write_bytes(data)
        if path.exists():
            shutil.copymode(path, saved)
        manifest[relative] = digest(data)
    (backup / "MANIFEST.json").write_bytes(json_bytes({"sha256": manifest}))
    for name, expected in manifest.items():
        if digest((backup / "files" / name).read_bytes()) != expected:
            raise ValueError("backup verification failed: " + name)
    return backup


def write_changes(target, changes):
    # Validate the entire batch before creating a parent or writing the first file.
    for path, data in changes:
        checked = destination(target, path.relative_to(Path(target).resolve()).as_posix())
        if checked.exists() and not checked.is_file():
            raise ValueError("directory occupies installed file: " + str(checked))
    for path, data in changes:
        relative = path.relative_to(Path(target).resolve()).as_posix()
        checked = destination(target, relative)
        checked.parent.mkdir(parents=True, exist_ok=True)
        if data is None:
            if checked.exists():
                checked.unlink()
        else:
            checked.write_bytes(data)
            if checked.suffix == ".sh":
                checked.chmod(checked.stat().st_mode | 0o111)


def fetch(source, revision, destination_root):
    if not revision:
        raise ValueError("a pinned --ref is required")
    subprocess.run(["git", "clone", "--quiet", "--no-checkout", "--config", "core.autocrlf=false", "--config", "core.eol=lf", "--", str(source), str(destination_root)], check=True, capture_output=True)
    resolved = subprocess.run(["git", "rev-parse", "--verify", revision + "^{commit}"], cwd=destination_root, check=True, capture_output=True, text=True).stdout.strip()
    subprocess.run(["git", "checkout", "--quiet", "--detach", resolved], cwd=destination_root, check=True, capture_output=True)
    return resolved


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--ref", required=True)
    parser.add_argument("--target", required=True)
    detected = Path(__file__).resolve().parents[1].name.removeprefix(".")
    parser.add_argument("--host", choices=HOSTS, default=detected if detected in HOSTS else "codex")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-hooks", action="store_true")
    parser.add_argument("--skip-deps", action="store_true", help="compatibility flag; payload is standard-library only")
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--migrate-existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        target = Path(args.target).resolve()
        if target.exists() and not target.is_dir():
            raise ValueError("target is not a directory")
        if args.update:
            arguments = ["--source", args.source, "--ref", args.ref, "--target", str(target), "--host", args.host]
            if args.no_hooks:
                arguments.append("--no-hooks")
            if args.plan:
                arguments.extend(["--plan", str(args.plan)])
            return load_module("update").main(arguments)
        # Refuse a nested installation before any target or backup is created.
        ancestor = target
        while not ancestor.exists() and ancestor != ancestor.parent:
            ancestor = ancestor.parent
        probe = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=ancestor, capture_output=True, text=True)
        if probe.returncode == 0 and Path(probe.stdout.strip()).resolve() != target:
            raise ValueError("target is inside another repository; install at its root")
        with tempfile.TemporaryDirectory(prefix="engineer-install-") as temp:
            source = Path(temp) / "source"
            revision = fetch(args.source, args.ref, source)
            module = load_module("migrate") if args.migrate_existing else None
            changes, originals, report = (module.plan_migration(source, target, args.host, not args.no_hooks, None) if module else plan_install(source, target, args.host, not args.no_hooks))
            preexisting = {name for name in payload(source, args.host, not args.no_hooks) if (target / name).is_file()}
            if args.dry_run:
                print("Would change " + str(len(changes)) + " paths")
                for path, _ in changes:
                    print("write " + path.relative_to(target).as_posix())
                return 0
            if originals:
                backup_migration(target, originals)
            write_changes(target, changes)
            if module:
                module.finish_migration(target, args.host)
            updater = load_module("update")
            updater.record_install(target, args.host, args.source, revision, payload(source, args.host, not args.no_hooks), preexisting)
            if not (target / ".git").exists():
                subprocess.run(["git", "init", "--quiet", str(target)], check=True, capture_output=True)
            if not args.skip_deps:
                entry = target / ("." + args.host) / "engineer/bin/engineer.py"
                subprocess.run([sys.executable, str(entry), "query", "runtime-identity"], cwd=target, check=True, capture_output=True)
            print("Installed " + args.host + " workflow at " + str(target) + " from " + revision + "; human must review and commit")
        return 0
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(str(exc) + "; nothing was installed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
