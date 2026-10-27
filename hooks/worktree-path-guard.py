#!/usr/bin/env python3
"""Advisory PreToolUse isolation/path guard for Claude and Codex JSON events."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

READ_ONLY = {'scout', 'verifier', 'code-reviewer', 'doc-verifier', 'plan-checker',
             'integration-checker', 'security-auditor', 'ui-auditor', 'ui-checker', 'dom-verifier'}
ARTIFACT = {'phase-researcher', 'codebase-mapper', 'planner', 'pattern-mapper', 'ui-researcher'}
WRITE_TOOLS = {'Write', 'Edit', 'MultiEdit', 'NotebookEdit', 'apply_patch'}


def git(cwd, *args):
    result = subprocess.run(['git', '-C', str(cwd), *args], capture_output=True,
                            text=True, encoding='utf-8', errors='replace', timeout=5, shell=False)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Git did not identify this checkout')
    return result.stdout.strip()


def canonical(path):
    return os.path.normcase(str(Path(path).resolve()))


def append_activity(root, payload, role, category, branch, checkout):
    session = str(payload.get('session_id') or payload.get('agent_id') or 'unknown-session')
    slug = re.sub(r'[^A-Za-z0-9_-]+', '-', session).strip('-')[:64] or 'unknown-session'
    slug += '-' + hashlib.sha256(session.encode()).hexdigest()[:8]
    directory = root / '.planning/handoffs'
    if directory.is_symlink() or (root / '.planning').is_symlink():
        return
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / ('.active-' + slug + '.jsonl')
    if path.is_symlink():
        return
    inputs = payload.get('tool_input') or {}
    record = {'event': 'dispatch', 'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(),
              'session_id': session, 'agent_id': payload.get('tool_use_id') or payload.get('agent_id'),
              'role': role, 'agent': role, 'category': category, 'tool_name': payload.get('tool_name'),
              'isolation': inputs.get('isolation'), 'cwd': str(checkout), 'root': str(root), 'branch': branch}
    # A single locked append keeps independent hook invocations from interleaving JSON.
    with path.open('a+b') as handle:
        if os.name == 'nt':
            import msvcrt
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                return
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            handle.seek(0, os.SEEK_END)
            handle.write(json.dumps(record, ensure_ascii=False).encode() + b'\n')
            handle.flush()
            os.fsync(handle.fileno())
        finally:
            if os.name == 'nt':
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def write_paths(inputs):
    values = []
    for key in ('file_path', 'path', 'notebook_path'):
        if isinstance(inputs.get(key), str):
            values.append(inputs[key])
    for edit in inputs.get('edits', []) if isinstance(inputs.get('edits'), list) else []:
        if isinstance(edit, dict):
            values.extend(write_paths(edit))
    patch = inputs.get('patch') or inputs.get('patch_text') or inputs.get('input')
    if isinstance(patch, str):
        values.extend(re.findall(r'^\*\*\* (?:Add|Update|Delete) File: (.+)$', patch, re.M))
    return values


def inspect(payload):
    if not isinstance(payload, dict):
        raise ValueError('Hook input must be a JSON object')
    tool = payload.get('tool_name', '')
    if tool not in WRITE_TOOLS and tool not in ('Agent', 'Task'):
        return []
    inputs = payload.get('tool_input') or {}
    if not isinstance(inputs, dict):
        raise ValueError('tool_input must be a JSON object')
    cwd = Path(payload.get('cwd') or os.getcwd()).resolve()
    root = Path(git(cwd, 'rev-parse', '--show-toplevel')).resolve()
    common = Path(git(cwd, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve()
    gitdir = Path(git(cwd, 'rev-parse', '--absolute-git-dir')).resolve()
    branch = git(cwd, 'branch', '--show-current')
    registered = git(cwd, 'worktree', 'list', '--porcelain')
    registered_roots = [Path(line[9:]).resolve() for line in registered.splitlines() if line.startswith('worktree ')]
    warnings = []
    if root not in registered_roots:
        warnings.append('Git did not register this checkout as an active worktree. Establish its identity before writing.')
    if not branch:
        warnings.append('This checkout has detached HEAD; establish the assigned named session branch before writing.')
    pin = os.environ.get('ENGINEER_WORKTREE_ROOT') or os.environ.get('ENGINEER_ROOT')
    if pin and canonical(pin) != canonical(root):
        warnings.append('The actual Git checkout differs from the supplied root pin. Stop dependent writes and resolve the coordinator-owned worktree identity.')
    if tool in ('Agent', 'Task'):
        role = str(inputs.get('subagent_type') or inputs.get('agent_type') or inputs.get('name') or 'unknown')
        role = role.removeprefix('gsd-')
        role = {'coder': 'executor', 'phase-preparer': 'planner', 'phase-checker': 'plan-checker', 'researcher': 'phase-researcher'}.get(role, role)
        category = 'read-only' if role in READ_ONLY else 'artifact' if role in ARTIFACT else 'write'
        if category != 'read-only' and inputs.get('isolation') != 'worktree':
            warnings.append('Write-capable or artifact dispatch lacks isolation="worktree". Use the runtime-owned isolated worker lifecycle; a sequential schedule does not waive isolation.')
        append_activity(root, payload, role, category, branch, cwd)
        return warnings
    if gitdir == common:
        warnings.append('This write targets the primary checkout. Use the explicitly assigned isolated session; do not silently switch or move work.')
    paths = write_paths(inputs)
    if not paths:
        warnings.append('The guard could not establish every write target from this tool payload. Inspect its exact paths before applying the operation.')
    for value in paths:
        path = Path(value).expanduser()
        path = (cwd / path).resolve() if not path.is_absolute() else path.resolve()
        if not path.is_relative_to(root):
            warnings.append('Write target is outside the actual assigned checkout: ' + str(path))
        if any('scratchpad' in part.lower() for part in path.parts):
            warnings.append('Scratchpad writes do not provide durable project or planning evidence: ' + str(path))
    return warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', choices=('claude', 'codex'), default='claude')
    parser.parse_args()
    try:
        data = json.loads(sys.stdin.read())
        warnings = inspect(data)
    except Exception as exc:
        # Reviewed project policy is advisory: malformed input never denies the host tool.
        print('Engineer worktree guard could not establish safety: ' + str(exc), file=sys.stderr)
        return 0
    if warnings:
        advice = 'Engineer worktree advisory (not an acceptance or authorization):\n' + '\n'.join('- ' + warning for warning in warnings)
        print(advice, file=sys.stderr)
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'additionalContext': advice}}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
