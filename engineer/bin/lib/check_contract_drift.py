"""Agent-contract drift check: keeps agent-contracts.md in sync with the agent, workflow and command files.

Port of ``scripts/check-contract-drift.cjs`` from gsd-core (MIT, Copyright (c) 2026 Open GSD),
pinned at commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79. The parsers and violation
models it shares with ``scripts/command-contract-helpers.cjs`` are inlined here, together
with the one containment predicate it takes from ``src/security.cts`` (``tryWithinRoot``)
and the exit handling of ``scripts/lib/cli-exit.cjs`` (``runMain``).

Enforces that the ``## Agent Registry`` table of ``engineer/references/agent-contracts.md``
stays in sync with reality: the table parses cleanly; every agent file closes its code
fences; declared and emitted markers agree; every ``sentinel-match`` marker has an
exact-case consumer; the roster is covered; no ``<files_to_read>`` survives and every
``<required_reading>`` consumer's agent carries the gate; no consumer matches a phantom
``## TOKEN``; every ``@.../references/*.md`` pointer an agent carries resolves.

Usage: ``python -m lib.check_contract_drift [--root DIR] [--json]`` from ``engineer/bin``.
Exit 0 = clean, exit 1 = violations (diagnostics on stderr).

Deviations:
- Path mapping: upstream ``gsd-core/references/`` -> ``engineer/references/``, ``gsd-core/workflows/``
  -> ``engineer/workflows/``, ``agents/`` -> ``agents/``, ``commands/gsd/`` -> ``commands/``.
  Reference pointers are therefore ``@(~|$HOME)/.claude/engineer/references/...`` or the bare
  ``@engineer/references/...``. Agent names carry no ``gsd-`` prefix in this repo.
- ``unmatched_consumer_tokens`` scans ``engineer/workflows/`` and ``commands/`` (upstream
  ``gsd-core/workflows/`` and ``commands/``). Retired GRAPHIFY completion markers
  have no exemption from contract checks.
- The ``read_tag_gate_missing`` remedy points to the surviving ``AGENTS.md``
  entry point and the assigned role's instructions.
- Helpers of ``command-contract-helpers.cjs`` this script never calls (``parseFrontmatter``,
  ``executionContextRefs``, ``workflowPathRefs``, ``unreachableWorkflows``, ``CANONICAL_TOOLS``)
  are not ported; they belong to the command-contract lint.
- ``tryWithinRoot`` is inlined as ``_try_within_root`` with only the relative-only policy this
  script uses; ``terminateNow``, JSON-error mode and exit-contract versions of ``cli-exit.cjs``
  are not ported. ``main`` returns the exit code; an unexpected exception propagates and Python
  exits 1 with a traceback, as ``runMain`` does with a stack trace.
- A missing ``--root`` value is reported on stderr with exit 1 instead of an uncaught ``Error``.
- The registry/marker/consumer parsers are public module functions here (upstream exports them
  from the helpers module) so tests can drive them directly.
- JavaScript regex semantics are kept explicit: ``\\s``/``trim`` use the JavaScript whitespace set
  (so U+0085 is not whitespace and U+FEFF is), ``\\w``/``\\b`` are ASCII, ``.`` excludes line
  terminators. ``sanitize_echo`` caps by code points rather than UTF-16 units.
- The ambiguity check of ``reference_includes`` asks whether the unstripped token is an exact
  directory entry (``os.listdir``) rather than ``existsSync``, because Windows aliases a trailing
  dot or space to the stripped name and would otherwise report a false ambiguity.
- Agent files are visited in sorted order for deterministic output.
- stdout/stderr writes fall back to replacement characters when the console encoding cannot
  represent a marker (for example ``## ⚠ Source Audit`` on a cp1252 console).
"""
from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import re
import stat
import sys

# ─── JavaScript regex compatibility ────────────────────────────────────────────

_JS_WS_CHARS = "\t\n\v\f\r   " + "".join(chr(c) for c in range(0x2000, 0x200B)) + "    　﻿"
_WS_BODY = "".join(re.escape(c) for c in _JS_WS_CHARS)
_WS = f"[{_WS_BODY}]"
_NOT_WS = f"[^{_WS_BODY}]"
_DOT = "[^\n\r  ]"


def _js_trim(value):
    return value.strip(_JS_WS_CHARS)


# ─── paths of this repository layout ───────────────────────────────────────────

_DEFAULT_ROOT = Path(__file__).resolve().parents[3]
CONTRACTS_RELATIVE = "engineer/references/agent-contracts.md"
REFERENCES_RELATIVE = "engineer/references"
WORKFLOWS_RELATIVE = "engineer/workflows"
COMMANDS_RELATIVE = "commands"
AGENTS_RELATIVE = "agents"

# ─── registry / marker parsing (command-contract-helpers.cjs) ──────────────────


def _split_outside_delimiter(text, delimiter):
    """Split on ``delimiter`` outside backtick spans and parentheticals."""
    parts, current = [], []
    in_backtick, paren_depth = False, 0
    for char in text:
        if char == "`":
            in_backtick = not in_backtick
        if not in_backtick:
            if char == "(":
                paren_depth += 1
            elif char == ")" and paren_depth > 0:
                paren_depth -= 1
        if char == delimiter and not in_backtick and paren_depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts


def _split_table_row(line):
    text = _js_trim(line)
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]
    return [_js_trim(cell) for cell in _split_outside_delimiter(text, "|")]


def _is_separator_row(line):
    text = _js_trim(line)
    return len(text) > 0 and re.fullmatch(r"[|:\- ]+", text) is not None and "-" in text


_NOTE_RE = re.compile(rf"({_DOT}*?){_WS}*\(([^)]*)\){_WS}*")
_UNCONSUMED_RE = re.compile(r"unconsumed\b", re.I | re.A)


def parse_completion_markers_cell(value):
    """Parse one ``Completion Markers`` cell into ``{markers, notes, unconsumedMarkers}``."""
    markers, notes, unconsumed = [], [], []
    if not value:
        return {"markers": markers, "notes": notes, "unconsumedMarkers": unconsumed}
    for raw_entry in _split_outside_delimiter(value, ","):
        entry = _js_trim(raw_entry)
        if entry == "":
            continue
        marker_portion = entry
        annotation = None
        note = _NOTE_RE.fullmatch(entry)
        if note:
            marker_portion = _js_trim(note.group(1))
            annotation = _js_trim(note.group(2))
            notes.append(annotation)
        marker_portion = _js_trim(marker_portion.replace("`", ""))
        marker_portion = _js_trim(re.sub(rf"^#{{1,6}}{_WS}+", "", marker_portion))
        if marker_portion == "" or marker_portion == "No marker":
            continue
        if annotation is not None and _UNCONSUMED_RE.match(annotation):
            unconsumed.append(marker_portion)
            continue
        markers.append(marker_portion)
    return {"markers": markers, "notes": notes, "unconsumedMarkers": unconsumed}


_HEADING_RE = re.compile(rf"(#{{1,6}}){_WS}+({_NOT_WS}{_DOT}*?){_WS}*")
_CANDIDATE_SHAPE_RE = re.compile(r"[A-Z][A-Z0-9 _:'/-]*")
_FENCE_RE = re.compile(r"(`{3,}|~{3,})")


def extract_markers(content, known_markers=None):
    """Find H1-H6 headings and whether each sits in a fenced block.

    Returns ``{"markers", "candidates", "unclosedFence"}``. A heading is a marker only when its
    text exactly matches ``known_markers``; marker-shaped in-fence headings that do not match are
    reported as ``candidates``.
    """
    markers, candidates = [], []
    if content is None or not isinstance(content, str) or _js_trim(content) == "":
        return {"markers": markers, "candidates": candidates, "unclosedFence": False}
    known = set(known_markers or [])
    in_fence, fence_char, fence_len = False, None, 0
    for index, line in enumerate(re.split(r"\r?\n", content)):
        state_for_line = in_fence
        fence = _FENCE_RE.match(_js_trim(line))
        if fence:
            run_char, run_len = fence.group(1)[0], len(fence.group(1))
            if not in_fence:
                in_fence, fence_char, fence_len = True, run_char, run_len
            elif run_char == fence_char and run_len >= fence_len:
                in_fence, fence_char, fence_len = False, None, 0
        heading = _HEADING_RE.fullmatch(line)
        if heading:
            text = _js_trim(heading.group(2))
            if text in known:
                markers.append({"marker": text, "inFence": state_for_line, "line": index + 1})
            elif state_for_line and len(text) <= 60 and _CANDIDATE_SHAPE_RE.fullmatch(text):
                candidates.append({"marker": text, "inFence": state_for_line, "line": index + 1})
    return {"markers": markers, "candidates": candidates, "unclosedFence": in_fence}


def parse_agent_contracts(markdown):
    """Parse the ``## Agent Registry`` pipe table into ``{"rows", "errors"}``."""
    rows, errors = [], []
    if markdown is None or not isinstance(markdown, str):
        return {"rows": rows, "errors": errors}
    lines = re.split(r"\r?\n", markdown)
    registry_index = next((i for i, line in enumerate(lines)
                           if re.fullmatch(rf"##{_WS}+Agent Registry{_WS}*", _js_trim(line))), -1)
    if registry_index == -1:
        return {"rows": rows, "errors": errors}
    i = registry_index + 1
    while i < len(lines) and _js_trim(lines[i]) == "":
        i += 1
    if i >= len(lines) or not _js_trim(lines[i]).startswith("|"):
        return {"rows": rows, "errors": errors}
    column_keys = [re.sub(rf"{_WS}+", "_", _js_trim(header).lower()) for header in _split_table_row(lines[i])]
    i += 1
    if i < len(lines) and _is_separator_row(lines[i]):
        i += 1
    while i < len(lines):
        raw = lines[i]
        if not _js_trim(raw).startswith("|"):
            break
        line_number = i + 1
        cells = _split_table_row(raw)
        if len(cells) != len(column_keys):
            errors.append({"line": line_number,
                           "reason": f"column count mismatch: expected {len(column_keys)}, got {len(cells)}"})
            i += 1
            continue
        row = {}
        for key, value in zip(column_keys, cells):
            if key == "completion_markers":
                parsed = parse_completion_markers_cell(value)
                row["completion_markers"] = parsed["markers"]
                row["notes"] = parsed["notes"]
                row["unconsumed_markers"] = parsed["unconsumedMarkers"]
            else:
                row[key] = value
        if not row.get("agent"):
            errors.append({"line": line_number, "reason": "empty agent name"})
            i += 1
            continue
        rows.append(row)
        i += 1
    return {"rows": rows, "errors": errors}


def parse_consumed_by_cell(value):
    """Extract every file-shaped markdown path from a ``Consumed by`` cell."""
    if not value or not isinstance(value, str):
        return []
    paths = []
    for match in re.finditer(r"`([^`]+)`", value):
        token = _js_trim(match.group(1))
        if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./-]*\.md", token) or "*" in token:
            continue
        if ".." in token.split("/"):
            continue
        paths.append(token)
    return paths


CONTRACT_KINDS = frozenset(("sentinel-match", "artifact+query", "structured-return"))

# Tokens that look like completion markers but are tool output, not agent contracts.
NON_AGENT_TOKENS = frozenset((
))

VIOLATION_KINDS = {
    "PARSE_ERROR": "parse_error",
    "UNCLOSED_FENCE": "unclosed_fence",
    "DECLARED_MARKER_NOT_EMITTED": "declared_marker_not_emitted",
    "EMITTED_MARKER_NOT_DECLARED": "emitted_marker_not_declared",
    "CASE_COLLISION": "case_collision",
    "CASE_ONLY_MATCH": "case_only_match",
    "NO_CONSUMER": "no_consumer",
    "DECLARED_CONSUMER_NO_MATCH": "declared_consumer_no_match",
    "UNKNOWN_KIND": "unknown_kind",
    "VESTIGIAL_MARKER": "vestigial_marker",
    "AGENT_WITHOUT_CONTRACT": "agent_without_contract",
    "DUPLICATE_REGISTRY_ROW": "duplicate_registry_row",
    "UNKNOWN_PRODUCER": "unknown_producer",
    "UNKNOWN_CONSUMER": "unknown_consumer",
    "LEGACY_READ_TAG": "legacy_read_tag",
    "READ_TAG_GATE_MISSING": "read_tag_gate_missing",
    "UNMATCHED_CONSUMER_TOKEN": "unmatched_consumer_token",
    "UNRESOLVED_REFERENCE_INCLUDE": "unresolved_reference_include",
}

REMEDIES = {
    "parse_error": "fix the malformed row in engineer/references/agent-contracts.md",
    "unclosed_fence": "close the unterminated code fence in this agent file",
    "declared_marker_not_emitted":
        "remove the marker from the registry row, or emit it as an in-fence example in the agent file",
    "emitted_marker_not_declared":
        "add this marker to the agent's Completion Markers cell in the registry table",
    "case_collision": "rename one of the colliding markers so they no longer differ only by case",
    "case_only_match":
        "fix the consumer file to match this marker exact-case, or update the marker/registry to match the consumer",
    "no_consumer":
        "add an exact-case consumer for this marker, or reclassify the row Kind to artifact+query/structured-return",
    "declared_consumer_no_match":
        "the marker is consumed, but not by any file the row's Consumed by cell names — fix the cell to name a real consumer",
    "unknown_kind": "set the Kind column to one of sentinel-match, artifact+query, structured-return",
    "vestigial_marker":
        "remove this marker heading from the agent file, since the row's Kind says no marker is expected",
    "agent_without_contract": "add a registry row for this agent in agent-contracts.md",
    "duplicate_registry_row": "merge the two rows for this agent into one",
    "unknown_producer": "remove the row, or create the agents/<name>.md file it names",
    "unknown_consumer":
        "fix the path in the Consumed by cell, or drop it — only real files the check can open belong there",
    "legacy_read_tag":
        "replace <files_to_read> with <required_reading> (#3423 standardized on the gate tag)",
    "read_tag_gate_missing":
        "add the <required_reading> MUST-Read gate clause to this agent's instructions (see AGENTS.md and the assigned role's required-reading instructions)",
    "unmatched_consumer_token":
        "declare the producing agent and marker in the registry, or remove the dispatch — nothing emits this token",
    "unresolved_reference_include":
        "fix the engineer/references/ pointer so it names an existing reference file whole and ends at the name (whitespace, end of line, or closing punctuation)",
}


def sanitize_echo(text):
    """Strip control characters from file-derived text and cap it at 200 characters."""
    out = "".join(ch for ch in str(text) if ord(ch) > 0x1F and ord(ch) != 0x7F)
    return out[:200] if len(out) > 200 else out


def contract_violations(registry=None, producer_markers=None, candidate_markers=None, consumer_texts=None):
    """Cross-check the registry against emitted markers and consumer texts.

    ``producer_markers`` / ``candidate_markers`` map agent -> marker list; ``consumer_texts`` maps
    repo-relative path -> text. Missing inputs default to empty so a partial call never raises.
    """
    violations = []
    try:
        rows = registry if isinstance(registry, list) else []
        producers = producer_markers if isinstance(producer_markers, dict) else {}
        candidates_by_agent = candidate_markers if isinstance(candidate_markers, dict) else {}
        consumers = consumer_texts if isinstance(consumer_texts, dict) else {}

        def declared_of(row):
            return [*(row.get("completion_markers") or []), *(row.get("unconsumed_markers") or [])]

        by_lower = {}
        for row in rows:
            for marker in declared_of(row):
                by_lower.setdefault(marker.lower(), {})[marker] = None
        for row in rows:
            for marker in declared_of(row):
                variants = by_lower.get(marker.lower())
                if variants and len(variants) > 1:
                    others = [v for v in variants if v != marker]
                    violations.append({"kind": "case_collision", "agent": row.get("agent"), "marker": marker,
                                       "detail": f"case-insensitive collision with: {', '.join(others)}"})

        seen_agents = set()
        for row in rows:
            agent = row.get("agent")
            if agent in seen_agents:
                violations.append({"kind": "duplicate_registry_row", "agent": agent, "marker": None,
                                   "detail": f'agent "{agent}" has more than one registry row'})
            seen_agents.add(agent)
            if len(producers) > 0 and agent not in producers:
                violations.append({"kind": "unknown_producer", "agent": agent, "marker": None,
                                   "detail": f'registry row for "{agent}" but no agents/{agent}.md exists'})
        for agent in producers:
            if agent not in seen_agents:
                violations.append({"kind": "agent_without_contract", "agent": agent, "marker": None,
                                   "detail": f"agents/{agent}.md exists but has no registry row in agent-contracts.md"})

        for row in rows:
            agent = row.get("agent")
            declared = row.get("completion_markers") or []
            unconsumed = row.get("unconsumed_markers") or []
            declared_all = [*declared, *unconsumed]
            produced = list(dict.fromkeys(producers.get(agent) or []))
            kind = row.get("kind")
            kind_provided = kind is not None and kind != ""

            if len(producers) > 0 and agent not in producers:
                continue

            for path in parse_consumed_by_cell(row.get("consumed_by")):
                if len(consumers) > 0 and path not in consumers:
                    violations.append({"kind": "unknown_consumer", "agent": agent, "marker": None,
                                       "detail": f'Consumed by names "{path}" but no such file exists'})

            if kind_provided and kind not in CONTRACT_KINDS:
                violations.append({"kind": "unknown_kind", "agent": agent, "marker": None,
                                   "detail": f'row declares unknown kind "{kind}"'})

            is_artifact_or_structured = kind_provided and kind in ("artifact+query", "structured-return")

            for marker in declared_all:
                if marker not in produced:
                    violations.append({"kind": "declared_marker_not_emitted", "agent": agent, "marker": marker,
                                       "detail": f"declared in registry but not emitted in-fence by {agent}"})

            if is_artifact_or_structured:
                unconsumed_set = set(unconsumed)
                for marker in produced:
                    if marker in unconsumed_set:
                        continue
                    violations.append({"kind": "vestigial_marker", "agent": agent, "marker": marker,
                                       "detail": f'row kind "{kind}" expects no marker, but agent still emits "{marker}" in-fence'})
                continue

            for marker in dict.fromkeys(candidates_by_agent.get(agent) or []):
                if marker not in declared_all:
                    violations.append({"kind": "emitted_marker_not_declared", "agent": agent, "marker": marker,
                                       "detail": f"emitted in-fence by {agent} but absent from its registry row"})

            if not kind_provided or kind == "sentinel-match":
                declared_consumer_paths = parse_consumed_by_cell(row.get("consumed_by"))
                for marker in declared:
                    if marker not in produced:
                        continue
                    exact = case_insensitive = declared_match = False
                    for consumer_id, text in consumers.items():
                        if consumer_id == f"agents/{agent}.md":
                            continue
                        if not isinstance(text, str):
                            continue
                        if marker in text:
                            exact = True
                            if consumer_id in declared_consumer_paths:
                                declared_match = True
                        elif marker.lower() in text.lower():
                            case_insensitive = True
                    if not exact:
                        if case_insensitive:
                            violations.append({"kind": "case_only_match", "agent": agent, "marker": marker,
                                               "detail": f'no exact-case consumer for "{marker}"; case-insensitive match found only'})
                        else:
                            violations.append({"kind": "no_consumer", "agent": agent, "marker": marker,
                                               "detail": f'no consumer text contains "{marker}" (exact case)'})
                    elif len(declared_consumer_paths) > 0 and not declared_match:
                        violations.append({"kind": "declared_consumer_no_match", "agent": agent, "marker": marker,
                                           "detail": f"consumed somewhere, but none of the row's Consumed by entries ( {', '.join(declared_consumer_paths)} ) contain \"{marker}\""})
    except Exception as error:
        # A drift gate must fail RED, never green.
        raise RuntimeError(f"contract_violations (internal failure — failing red): {error}") from error
    return violations


def read_tag_violations(registry=None, agent_texts=None, consumer_texts=None):
    """The read-tag arm: legacy ``<files_to_read>`` and a missing ``<required_reading>`` gate."""
    violations = []
    try:
        rows = registry if isinstance(registry, list) else []
        agents = agent_texts if isinstance(agent_texts, dict) else {}
        consumers = consumer_texts if isinstance(consumer_texts, dict) else {}

        for file, text in consumers.items():
            if isinstance(text, str) and "<files_to_read>" in text:
                violations.append({"kind": "legacy_read_tag", "agent": None, "marker": None,
                                   "detail": f"{file} still contains the retired <files_to_read> tag"})

        for row in rows:
            agent = row.get("agent")
            agent_text = agents.get(agent)
            if not isinstance(agent_text, str):
                continue
            if "<required_reading>" in agent_text:
                continue
            for path in parse_consumed_by_cell(row.get("consumed_by")):
                text = consumers.get(path)
                if isinstance(text, str) and "<required_reading>" in text:
                    violations.append({"kind": "read_tag_gate_missing", "agent": agent, "marker": None,
                                       "detail": f"consumer {path} emits <required_reading> but agents/{agent}.md never references the gate"})
                    break
    except Exception as error:
        raise RuntimeError(f"read_tag_violations (internal failure — failing red): {error}") from error
    return violations


_QUOTED_TOKEN_RE = re.compile(r"""[`'"]## ([^`'"\n]+)[`'"]""")


def unmatched_consumer_tokens(consumer_texts=None, vocabulary=None):
    """The reverse direction: a workflow/command matching a quoted ``## TOKEN`` no agent declares."""
    violations = []
    try:
        consumers = consumer_texts if isinstance(consumer_texts, dict) else {}
        if isinstance(vocabulary, (set, frozenset)):
            known = vocabulary
        elif isinstance(vocabulary, (list, tuple)):
            known = set(vocabulary)
        else:
            known = set()
        reported = set()
        for file, text in consumers.items():
            if not file.startswith(f"{WORKFLOWS_RELATIVE}/") and not file.startswith(f"{COMMANDS_RELATIVE}/"):
                continue
            if not isinstance(text, str):
                continue
            for match in _QUOTED_TOKEN_RE.finditer(text):
                token = _js_trim(match.group(1))
                if token in known or token in NON_AGENT_TOKENS:
                    continue
                if len(token) > 60 or not _CANDIDATE_SHAPE_RE.fullmatch(token):
                    continue
                key = (file, token)
                if key in reported:
                    continue
                reported.add(key)
                violations.append({"kind": "unmatched_consumer_token", "agent": None, "marker": token,
                                   "detail": f"{file} matches `## {token}` but no agent declares or emits it"})
    except Exception as error:
        raise RuntimeError(f"unmatched_consumer_tokens (internal failure — failing red): {error}") from error
    return violations


# ─── containment (security.cts tryWithinRoot, relative-only policy) ────────────


def _is_contained_in(resolved_target, resolved_root):
    if resolved_target == resolved_root:
        return True
    return (resolved_target + os.sep).startswith(resolved_root + os.sep)


def _try_within_root(candidate, root):
    """Return the realpath of ``candidate`` under ``root``, or ``None`` when it escapes or is unsafe."""
    if not candidate or not isinstance(candidate, str) or not root or not isinstance(root, str):
        return None
    if "\0" in candidate:
        return None
    try:
        resolved_base = os.path.realpath(os.path.abspath(root), strict=True)
    except (OSError, ValueError):
        resolved_base = os.path.abspath(root)
    if os.path.isabs(candidate) or candidate.startswith(("/", "\\")):
        return None
    resolved = os.path.abspath(os.path.join(root, candidate))
    try:
        resolved = os.path.realpath(resolved, strict=True)
    except (OSError, ValueError):
        # A dangling symlink has no realpath yet exists as a link: refuse it, as an existence
        # oracle for outside paths would otherwise be left open.
        if os.path.islink(resolved):
            return None
        ancestor = os.path.dirname(resolved)
        remainder = [os.path.basename(resolved)]
        while True:
            try:
                real_ancestor = os.path.realpath(ancestor, strict=True)
                resolved = os.path.join(real_ancestor, *remainder)
                break
            except (OSError, ValueError):
                parent = os.path.dirname(ancestor)
                if parent == ancestor:
                    break
                remainder.insert(0, os.path.basename(ancestor))
                ancestor = parent
    if not _is_contained_in(resolved, resolved_base):
        return None
    return resolved


# ─── driver (check-contract-drift.cjs) ─────────────────────────────────────────

_REFERENCE_POINTER_RE = re.compile(
    r"@(?:(?:~|\$HOME)/\.claude/|(?:(?!\.\.?/)[A-Za-z0-9._-]+/)+)?engineer/references/(" + _NOT_WS + "+)"
)
_REFERENCE_NAME_RE = re.compile(r"(?:[A-Za-z0-9_-][A-Za-z0-9._-]*/)*[A-Za-z0-9_-][A-Za-z0-9._-]*\.md")
_TRAILING_PROSE_RE = re.compile(r"""[.,;:!?)\]}>"'`*]+""")


def resolve_root(argv):
    """The ``--root DIR`` value, or this checkout's root. Raises ``ValueError`` without a value."""
    if "--root" not in argv:
        return _DEFAULT_ROOT
    index = argv.index("--root")
    value = argv[index + 1] if index + 1 < len(argv) else None
    if not value:
        raise ValueError("check-contract-drift: --root requires a directory argument")
    return Path(os.path.abspath(value))


def walk_markdown_files(directory, acc=None):
    """Every ``*.md`` under ``directory``, symlinks not followed; unreadable directories are skipped."""
    acc = [] if acc is None else acc
    try:
        entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
    except OSError:
        return acc
    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            walk_markdown_files(entry.path, acc)
        elif entry.is_file(follow_symlinks=False) and entry.name.endswith(".md"):
            acc.append(entry.path)
    return acc


def to_repo_relative(absolute, root):
    return os.path.relpath(absolute, root).replace(os.sep, "/")


def _read_text(path):
    return Path(path).read_bytes().decode("utf-8", errors="replace")


def _names_directory_entry(directory, relative):
    """Does ``relative`` name an existing entry of ``directory`` under exactly that spelling?"""
    target = os.path.join(directory, relative)
    parent, leaf = os.path.split(target)
    try:
        return os.path.exists(target) and leaf in os.listdir(parent)
    except (OSError, ValueError):
        return False


def reference_includes(content, root):
    """Follow ``@.../references/*.md`` pointers in an agent file.

    Returns ``{"includes": [ROOT-relative paths], "declined": [{"pointer", "reason"}]}``. A token is
    captured whole and must satisfy the name grammar end to end; a pointer that does not parse whole,
    or is ambiguous with its prose-stripped reading, is declined and reported, never truncated.
    """
    seen = {}
    declined = {}
    refs_dir = os.path.join(str(root), *REFERENCES_RELATIVE.split("/"))
    for match in _REFERENCE_POINTER_RE.finditer(content):
        raw = match.group(1)
        candidate = None
        for cut in range(len(raw) + 1):
            probe = raw[:len(raw) - cut]
            if cut > 0 and not _TRAILING_PROSE_RE.fullmatch(raw[len(raw) - cut:]):
                break
            if _REFERENCE_NAME_RE.fullmatch(probe):
                candidate = probe
                break
        if candidate is None:
            declined[match.group(0)] = "does not name a reference whole — the text continues past the name, so nothing is followed"
            continue
        if candidate != raw and _names_directory_entry(refs_dir, raw):
            declined[match.group(0)] = (
                f"is ambiguous — `{raw}` itself names something on disk, so stripping it to `{candidate}` "
                "would pick one of two readings; neither is followed"
            )
            continue
        seen[f"{REFERENCES_RELATIVE}/{candidate}"] = None
    return {"includes": list(seen), "declined": [{"pointer": p, "reason": r} for p, r in declined.items()]}


def remedy_for(kind):
    return REMEDIES.get(kind) or "review the registry row and agent file for drift"


def collect_violations(root):
    """Run every check under ``root``.

    Returns ``None`` when the contracts file is missing, else
    ``{"violations": [...], "agents": N, "markers": N}``.
    """
    root = str(root)
    contracts_file = os.path.join(root, *CONTRACTS_RELATIVE.split("/"))
    agents_dir = os.path.join(root, AGENTS_RELATIVE)
    workflows_dir = os.path.join(root, *WORKFLOWS_RELATIVE.split("/"))
    commands_dir = os.path.join(root, COMMANDS_RELATIVE)
    refs_dir = os.path.join(root, *REFERENCES_RELATIVE.split("/"))
    if not os.path.exists(contracts_file):
        return None

    parsed = parse_agent_contracts(_read_text(contracts_file))
    registry, parse_errors = parsed["rows"], parsed["errors"]

    known_markers = set()
    for row in registry:
        known_markers.update(row.get("completion_markers") or [])
        known_markers.update(row.get("unconsumed_markers") or [])

    producer_markers, candidate_markers, agent_texts = {}, {}, {}
    unclosed_fence_violations, include_violations = [], []

    # .compact.md variants render their canonical agent's SAME contract and need no row of their own.
    agent_files = sorted(
        name for name in (os.listdir(agents_dir) if os.path.exists(agents_dir) else [])
        if name.endswith(".md") and not name.endswith(".compact.md")
    )
    for file in agent_files:
        agent = file[:-3]
        absolute = os.path.join(agents_dir, file)
        content = _read_text(absolute)
        include_texts = []

        def report_include(pointer, reason, agent=agent, absolute=absolute):
            include_violations.append({"kind": "unresolved_reference_include", "agent": agent, "marker": None,
                                       "detail": f"{to_repo_relative(absolute, root)}: {pointer} {reason}"})

        followed = reference_includes(content, root)
        for item in followed["declined"]:
            report_include(item["pointer"], item["reason"])
        for reference_path in followed["includes"]:
            contained = _try_within_root(reference_path[len(REFERENCES_RELATIVE) + 1:], refs_dir)
            if contained is None:
                report_include(reference_path, f"does not resolve inside {REFERENCES_RELATIVE}/")
                continue
            try:
                if not stat.S_ISREG(os.lstat(contained).st_mode):
                    report_include(reference_path, "is not a regular file")
                    continue
                include_texts.append(_read_text(contained))
            except OSError as error:
                code = errno.errorcode.get(error.errno)
                report_include(reference_path, "does not exist" if isinstance(error, FileNotFoundError)
                               else f"could not be read ({code})")
        agent_texts[agent] = "\n".join([content, *include_texts])
        extracted = extract_markers(agent_texts[agent], known_markers)
        producer_markers[agent] = [m["marker"] for m in extracted["markers"] if m["inFence"]]
        candidate_markers[agent] = list(dict.fromkeys(m["marker"] for m in extracted["candidates"] if m["inFence"]))
        if extracted["unclosedFence"]:
            unclosed_fence_violations.append({"kind": "unclosed_fence", "agent": agent, "marker": None,
                                              "detail": f"{to_repo_relative(absolute, root)} has an unterminated code fence"})

    # Consumer corpus: every *.md under workflows/, commands/, agents/, plus each file-shaped
    # `Consumed by` entry that resolves on disk.
    consumer_texts = {}
    for directory in (workflows_dir, commands_dir, agents_dir):
        for absolute in walk_markdown_files(directory):
            consumer_texts[to_repo_relative(absolute, root)] = _read_text(absolute)
    for row in registry:
        for relative in parse_consumed_by_cell(row.get("consumed_by")):
            if relative in consumer_texts:
                continue
            try:
                consumer_texts[relative] = _read_text(os.path.join(root, relative))
            except (OSError, ValueError):
                pass  # absent: contract_violations reports it as unknown_consumer

    parse_violations = [{"kind": "parse_error", "agent": None, "marker": None,
                         "detail": f"agent-contracts.md:{e['line']} — {e['reason']}"} for e in parse_errors]
    violations = [
        *parse_violations,
        *unclosed_fence_violations,
        *include_violations,
        *contract_violations(registry=registry, producer_markers=producer_markers,
                             candidate_markers=candidate_markers, consumer_texts=consumer_texts),
        *read_tag_violations(registry=registry, agent_texts=agent_texts, consumer_texts=consumer_texts),
        *unmatched_consumer_tokens(consumer_texts=consumer_texts, vocabulary=known_markers),
    ]
    marker_count = sum(len(row.get("completion_markers") or []) for row in registry)
    return {"violations": violations, "agents": len(registry), "markers": marker_count}


def _write(stream, text):
    try:
        stream.write(text)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "ascii"
        stream.write(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))
    stream.flush()


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        root = resolve_root(argv)
    except ValueError as error:
        _write(sys.stderr, f"{error}\n")
        return 1

    result = collect_violations(root)
    if result is None:
        contracts = to_repo_relative(os.path.join(str(root), *CONTRACTS_RELATIVE.split("/")), root)
        _write(sys.stderr, f"\nERROR check-contract-drift: contracts file not found at {contracts}\n\n")
        return 1
    violations, agent_count, marker_count = result["violations"], result["agents"], result["markers"]

    if "--json" in argv:
        report = {
            "check": "check-contract-drift",
            "status": "ok" if not violations else "violations",
            "agents": agent_count,
            "markers": marker_count,
            "violations": [{"kind": v["kind"], "agent": v.get("agent"), "marker": v.get("marker"),
                            "detail": sanitize_echo(v["detail"])} for v in violations],
        }
        _write(sys.stdout, json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n")
        return 0 if not violations else 1

    if not violations:
        _write(sys.stdout, f"ok check-contract-drift: {agent_count} agents, {marker_count} markers, 0 violations\n")
        return 0

    by_kind = {}
    for violation in violations:
        by_kind.setdefault(violation["kind"], []).append(violation)
    _write(sys.stderr, f"\nERROR check-contract-drift: {len(violations)} violation(s) across {len(by_kind)} kind(s)\n\n")
    for kind, items in by_kind.items():
        _write(sys.stderr, f"  {kind} ({len(items)}):\n")
        for violation in items:
            agent_label = sanitize_echo(violation["agent"]) if violation.get("agent") else "(registry)"
            marker_label = f' marker "{sanitize_echo(violation["marker"])}"' if violation.get("marker") else ""
            _write(sys.stderr, f"    - {agent_label}{marker_label}: {sanitize_echo(violation['detail'])}\n")
            _write(sys.stderr, f"      remedy: {remedy_for(kind)}\n")
        _write(sys.stderr, "\n")
    _write(sys.stderr, "See engineer/references/agent-contracts.md for the registry contract spec.\n\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
