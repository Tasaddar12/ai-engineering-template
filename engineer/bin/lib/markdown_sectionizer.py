"""Canonical markdown-structure parsing seam.

Ported from upstream gsd-core ``src/markdown-sectionizer.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
Pure functions over strings, stdlib only, no I/O. Fence handling, ATX heading
tokenisation, section collection, bullet iteration and the bounded splice helpers
(``update_bullet``, ``update_heading``, ``with_section``, ``delete_section``, tagged
block and fence masking) behave exactly as upstream, including CRLF safety and the
"bounded no-op" returns.

Shapes (dicts keep upstream's camelCase field names so JSON output is unchanged):
- ``stripFencedCode`` result: ``{"text", "unterminatedFence"}``
- HeadingToken: ``{"level", "text", "line", "offset"}`` (``line`` is 1-based)
- Section: ``{"heading", "body", "bodyStart", "bodyEnd"}``
- Section options: ``{"levelBounded", "stopAtLevel", "stripFences"}``;
  ``delete_section`` also accepts ``"endOffset"``
- BulletItem: ``{"marker", "text", "indent", "checked"}``
- InlineCodeSpan: ``{"start", "end", "content"}``
- FencedBlockRecord: ``{"char", "len", "infoString", "openLineIdx", "closeLineIdx"}``

Deviations:
- Character offsets (``offset``, ``bodyStart``, ``bodyEnd``, span ``start``/``end``) index the
  Python ``str`` (code points); upstream indexes UTF-16 code units. They are identical for text
  without astral characters and always consistent with Python slicing of the same string.
- JS regex classes are reproduced explicitly: ``\\s`` is the ECMAScript whitespace set (``_WS``),
  ``.`` excludes the four ECMAScript line terminators, ``\\d`` is ``[0-9]``, and ``trim`` /
  ``trimEnd`` strip the ECMAScript whitespace set, not Python's ``str.strip`` default.
- ``mask_fences`` returns a ``FenceMask`` object (``masked`` attribute, ``restore`` method)
  instead of a plain object with a method.
- ``escapeRegex`` (upstream ``./pattern.cjs``) is ``re.escape``; ``text.matchAll`` is ``re.finditer``.
- Case-insensitive tag matching uses Python's Unicode ``re.IGNORECASE`` rather than ECMAScript's
  simple case folding; identical for ASCII tag names.
- ``None`` stands in for JS ``null``/``undefined`` option values and non-string inputs; every
  ``typeof x !== 'string'`` guard becomes ``not isinstance(x, str)``.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Callable, Optional

__all__ = [
    "XML_DECISION_TAG_NAMES", "FenceMask", "strip_fenced_code", "strip_inline_code",
    "scan_inline_code_spans", "scan_fenced_blocks", "extract_fenced_block", "tokenize_headings",
    "collect_sections", "collect_section", "iterate_bullets", "update_bullet", "update_heading",
    "extract_tagged_blocks", "strip_tagged_blocks", "edit_outside_tagged_blocks", "mask_fences",
    "edit_outside_fences", "replace_section", "with_section", "delete_section",
    "extract_xml_tag_bodies",
]

# ECMAScript whitespace / line-terminator set (what JS `\s`, `trim()` and `trimEnd()` use).
_WS_CHARS = "\t\n\v\f\r              " \
            "    　﻿"
_WS = "[" + _WS_CHARS + "]"
# JS `.` (no dotAll flag): anything except \n, \r,  ,  .
_DOT = "[^\n\r  ]"

_DELIM_RE = re.compile("( {0,3})(`{3,}|~{3,})(" + _DOT + "*)\\Z")
_HEADING_RE = re.compile("( {0,3})(#{1,6})([ \t]+" + _DOT + "*|[ \t]*)?\\Z")
_CLOSING_ONLY_WS = re.compile("(?:" + _WS + ")*\\Z")


def _trim(text):
    return text.strip(_WS_CHARS)


def _trim_end(text):
    return text.rstrip(_WS_CHARS)


def _strip_cr(raw_line):
    return raw_line[:-1] if raw_line.endswith("\r") else raw_line


def _is_blank(text):
    return _CLOSING_ONLY_WS.match(text) is not None


def _line_offsets(lines):
    """Character offset of the start of each line, plus the EOF sentinel."""
    offsets = []
    acc = 0
    for line in lines:
        offsets.append(acc)
        acc += len(line) + 1
    return offsets, acc


# ─── stripFencedCode ──────────────────────────────────────────────────────────

def strip_fenced_code(content):
    """CommonMark-correct fenced-code-block stripper.

    Returns ``{"text", "unterminatedFence"}``; delimiter lines and fence bodies are dropped, kept
    lines are returned as-is (CRLF preserved). ``unterminatedFence`` is true when EOF is reached
    inside an open fence. Non-string input yields an empty result.
    """
    if not isinstance(content, str):
        return {"text": "", "unterminatedFence": False}
    kept = []
    open_fence = None
    for raw_line in content.split("\n"):
        line = _strip_cr(raw_line)
        m = _DELIM_RE.match(line)
        if m:
            char = m.group(2)[0]
            length = len(m.group(2))
            trailing = m.group(3)
            if open_fence is None:
                # CommonMark 4.5: a backtick fence's info string must not contain a backtick.
                if char == "`" and "`" in trailing:
                    kept.append(raw_line)
                    continue
                open_fence = (char, length)
            elif char == open_fence[0] and length >= open_fence[1] and _is_blank(trailing):
                open_fence = None
            continue  # every delimiter line is dropped
        if open_fence is None:
            kept.append(raw_line)
    return {"text": "\n".join(kept), "unterminatedFence": open_fence is not None}


# ─── inline code ──────────────────────────────────────────────────────────────

def _scan_spans_in_line(line):
    spans = []
    if "`" not in line:
        return spans
    # Collect maximal backtick runs once, then match openers to closers with a per-length
    # forward cursor: linear on lines of many unmatched increasing-length runs.
    runs = []
    i = 0
    while i < len(line):
        if line[i] == "`":
            n = 1
            while i + n < len(line) and line[i + n] == "`":
                n += 1
            runs.append((i, n))
            i += n
        else:
            i += 1
    runs_by_len = {}
    for k, (_, length) in enumerate(runs):
        runs_by_len.setdefault(length, []).append(k)
    cursor_by_len = {}
    k = 0
    while k < len(runs):
        open_pos, n = runs[k]
        candidates = runs_by_len[n]
        ci = cursor_by_len.get(n, 0)
        while ci < len(candidates) and candidates[ci] <= k:
            ci += 1
        if ci < len(candidates):
            close_k = candidates[ci]
            close_pos = runs[close_k][0]
            spans.append({"start": open_pos, "end": close_pos + n, "content": line[open_pos + n:close_pos]})
            cursor_by_len[n] = ci + 1
            k = close_k + 1  # runs inside the span are code
        else:
            cursor_by_len[n] = ci
            k += 1  # unmatched run is literal text
    return spans


def scan_inline_code_spans(content):
    """Locate every inline code span (``{"start", "end", "content"}``), per line, offsets into the full string."""
    if not isinstance(content, str) or len(content) == 0:
        return []
    out = []
    line_start = 0
    for line in content.split("\n"):
        for span in _scan_spans_in_line(line):
            out.append({"start": line_start + span["start"], "end": line_start + span["end"],
                        "content": span["content"]})
        line_start += len(line) + 1
    return out


def _strip_inline_code_line(line):
    spans = _scan_spans_in_line(line)
    if not spans:
        return line
    out = []
    prev = 0
    for span in spans:
        out.append(line[prev:span["start"]] + " ")
        prev = span["end"]
    return "".join(out) + line[prev:]


def strip_inline_code(content):
    """Remove CommonMark inline code spans line by line, replacing each with one space."""
    if not isinstance(content, str) or len(content) == 0:
        return ""
    return "\n".join(_strip_inline_code_line(line) for line in content.split("\n"))


# ─── fenced block scanning ────────────────────────────────────────────────────

def scan_fenced_blocks(lines):
    """Return every fenced block in ``lines`` as ``{"char","len","infoString","openLineIdx","closeLineIdx"}``.

    ``closeLineIdx`` is ``-1`` for an unterminated fence. Uses the same delimiter rules as
    ``strip_fenced_code``.
    """
    blocks = []
    open_block = None
    for i, raw in enumerate(lines):
        m = _DELIM_RE.match(_strip_cr(raw))
        if not m:
            continue
        char = m.group(2)[0]
        length = len(m.group(2))
        trailing = m.group(3)
        if open_block is None:
            if char == "`" and "`" in trailing:
                continue  # not a valid opener
            open_block = {"char": char, "len": length, "infoString": _trim(trailing), "openLineIdx": i}
        elif char == open_block["char"] and length >= open_block["len"] and _is_blank(trailing):
            blocks.append({"char": open_block["char"], "len": open_block["len"],
                           "infoString": open_block["infoString"], "openLineIdx": open_block["openLineIdx"],
                           "closeLineIdx": i})
            open_block = None
    if open_block is not None:
        blocks.append({"char": open_block["char"], "len": open_block["len"],
                       "infoString": open_block["infoString"], "openLineIdx": open_block["openLineIdx"],
                       "closeLineIdx": -1})
    return blocks


def extract_fenced_block(content, info_string):
    """Inner text of the FIRST terminated fenced block whose (trimmed, case-insensitive) info string matches, else ``None``."""
    if not isinstance(content, str) or len(content) == 0:
        return None
    if not isinstance(info_string, str):
        return None
    target = _trim(info_string).lower()
    lines = content.split("\n")
    for block in scan_fenced_blocks(lines):
        if block["closeLineIdx"] == -1:
            continue
        if _trim(block["infoString"]).lower() != target:
            continue
        return "\n".join(lines[block["openLineIdx"] + 1:block["closeLineIdx"]])
    return None


# ─── tokenizeHeadings ─────────────────────────────────────────────────────────

def tokenize_headings(content):
    """All ATX headings outside fenced code, in document order, as ``{"level","text","line","offset"}``."""
    if not isinstance(content, str) or len(content) == 0:
        return []
    original_lines = content.split("\n")
    tokens = []
    open_fence = None
    char_offset = 0
    for i, raw_line in enumerate(original_lines):
        line = _strip_cr(raw_line)
        dm = _DELIM_RE.match(line)
        if dm:
            char = dm.group(2)[0]
            length = len(dm.group(2))
            trailing = dm.group(3)
            if open_fence is None:
                if char == "`" and "`" in trailing:
                    pass  # not a valid opener: fall through to the heading check
                else:
                    open_fence = (char, length)
                    char_offset += len(raw_line) + 1
                    continue
            elif char == open_fence[0] and length >= open_fence[1] and _is_blank(trailing):
                open_fence = None
                char_offset += len(raw_line) + 1
                continue
            else:
                char_offset += len(raw_line) + 1
                continue
        if open_fence is None:
            hm = _HEADING_RE.match(line)
            if hm:
                hashes = hm.group(2)
                rest = hm.group(3) or ""
                raw_text = re.sub("^[ \t]+", "", rest, count=1)
                raw_text = re.sub("[ \t]+#+[ \t]*\\Z", "", raw_text, count=1)
                raw_text = re.sub("^#+[ \t]*\\Z", "", raw_text, count=1)
                tokens.append({"level": len(hashes), "text": _trim(raw_text), "line": i + 1, "offset": char_offset})
        char_offset += len(raw_line) + 1
    return tokens


# ─── collectSections / collectSection ─────────────────────────────────────────

def collect_sections(content, stop_predicate):
    """Collect one section per heading accepted by ``stop_predicate``; each ends at the next accepted heading or EOF."""
    if not isinstance(content, str) or len(content) == 0:
        return []
    headings = tokenize_headings(content)
    if not headings:
        return []
    lines = content.split("\n")
    sections = []
    headings_by_line = {h["line"]: h for h in headings}
    line_offsets, _ = _line_offsets(lines)
    current_heading = None
    current_body_start = 0
    body_lines = []

    def flush():
        nonlocal current_heading, body_lines
        if current_heading is not None:
            body = _trim_end("\n".join(body_lines))
            # INVARIANT: content[bodyStart:bodyEnd] == body
            sections.append({"heading": current_heading, "body": body, "bodyStart": current_body_start,
                             "bodyEnd": current_body_start + len(body)})
            current_heading = None
            body_lines = []

    for i in range(len(lines)):
        h = headings_by_line.get(i + 1)
        if h is not None and stop_predicate(h):
            flush()
            current_heading = h
            idx = h["line"] - 1
            current_body_start = line_offsets[idx] + len(lines[idx]) + 1
        elif current_heading is not None:
            body_lines.append(lines[i])
    flush()
    return sections


def _find_stop_line(headings, target_idx, target, opts, default):
    level_bounded = opts.get("levelBounded")
    level_bounded = True if level_bounded is None else level_bounded
    stop_at_level = opts.get("stopAtLevel")
    for j in range(target_idx + 1, len(headings)):
        nxt = headings[j]
        if stop_at_level is not None:
            is_stop = nxt["level"] <= stop_at_level
        else:
            is_stop = nxt["level"] <= target["level"] if level_bounded else True
        if is_stop:
            return nxt["line"]
    return default


def _find_heading_index(headings, predicate):
    for idx, heading in enumerate(headings):
        if predicate(heading):
            return idx
    return -1


def collect_section(content, heading_predicate, opts=None):
    """Collect the first section whose heading satisfies ``heading_predicate``; ``None`` when absent.

    Options: ``levelBounded`` (default True), ``stopAtLevel`` (takes precedence), ``stripFences``.
    """
    if not isinstance(content, str) or len(content) == 0:
        return None
    opts = opts or {}
    strip_fences = bool(opts.get("stripFences") or False)
    headings = tokenize_headings(content)
    target_idx = _find_heading_index(headings, heading_predicate)
    if target_idx == -1:
        return None
    target = headings[target_idx]
    lines = content.split("\n")
    body_start_line = target["line"] + 1
    body_end_line = _find_stop_line(headings, target_idx, target, opts, len(lines) + 1)
    line_offsets, eof_offset = _line_offsets(lines)
    body_start_offset = line_offsets[body_start_line - 1] if body_start_line <= len(lines) else eof_offset
    body_raw = _trim_end("\n".join(lines[body_start_line - 1:body_end_line - 1]))
    body = strip_fenced_code(body_raw)["text"] if strip_fences else body_raw
    # INVARIANT: bodyEnd derives from body length so replace_section(content, s, s["body"]) == content.
    return {"heading": target, "body": body, "bodyStart": body_start_offset,
            "bodyEnd": body_start_offset + len(body)}


# ─── iterateBullets ───────────────────────────────────────────────────────────

_CHECKBOX_ITER_RE = re.compile("(" + _WS + "*)- \\[([xX ])\\] (" + _DOT + "*)\\Z")
_DASH_ITER_RE = re.compile("(" + _WS + "*)[-*+] (" + _DOT + "*)\\Z")
_NUMBERED_ITER_RE = re.compile("(" + _WS + "*)[0-9]+\\. (" + _DOT + "*)\\Z")


def iterate_bullets(section_text):
    """Bullet items (``{"marker","text","indent","checked"}``) from ``section_text``.

    Markers: checkbox (``checkbox-unchecked``/``checkbox-checked``), ``dash`` (``-``/``*``/``+``) and
    ``numbered``. Indented non-bullet lines continue the current bullet; blank lines end it.
    """
    if not isinstance(section_text, str) or len(section_text) == 0:
        return []
    items = []
    current = None

    def flush():
        nonlocal current
        if current is not None:
            current["text"] = _trim(current["text"])
            items.append(current)
            current = None

    for raw_line in section_text.split("\n"):
        line = _strip_cr(raw_line)
        trimmed = _trim(line)
        if trimmed == "":
            flush()
            continue
        cbm = _CHECKBOX_ITER_RE.match(line)
        if cbm:
            flush()
            checked = cbm.group(2) in ("x", "X")
            current = {"marker": "checkbox-checked" if checked else "checkbox-unchecked",
                       "text": cbm.group(3), "indent": cbm.group(1), "checked": checked}
            continue
        nm = _NUMBERED_ITER_RE.match(line)
        if nm:
            flush()
            current = {"marker": "numbered", "text": nm.group(2), "indent": nm.group(1), "checked": None}
            continue
        dm = _DASH_ITER_RE.match(line)
        if dm:
            flush()
            current = {"marker": "dash", "text": dm.group(2), "indent": dm.group(1), "checked": None}
            continue
        if current is not None and line[:1] in (" ", "\t"):
            current["text"] += " " + trimmed
            continue
        flush()
    flush()
    return items


# ─── updateBullet / updateHeading ─────────────────────────────────────────────

_CHECKBOX_UPDATE_RE = re.compile("(" + _WS + "*)-[ \t]{1,4}\\[([xX ])\\] (" + _DOT + "*)\\Z")
_DASH_UPDATE_RE = re.compile("(" + _WS + "*)[-*+][ \t]{1,4}(" + _DOT + "*)\\Z")
_NUMBERED_UPDATE_RE = re.compile("(" + _WS + "*)[0-9]+\\.[ \t]{1,4}(" + _DOT + "*)\\Z")


def update_bullet(content, match, transform):
    """Replace the first fence-external bullet-opening line accepted by ``match`` with ``transform(raw_line)``.

    ``match(bullet_text, raw_line, line_index)`` -> bool; ``transform(raw_line)`` -> str. Only that
    physical line changes; a miss or a non-string transform result returns ``content`` unchanged.
    """
    if not isinstance(content, str) or len(content) == 0:
        return content
    lines = content.split("\n")
    open_fence = None
    offset = 0
    for i, raw_line in enumerate(lines):
        line = _strip_cr(raw_line)
        dm = _DELIM_RE.match(line)
        if dm:
            char = dm.group(2)[0]
            length = len(dm.group(2))
            trailing = dm.group(3)
            if open_fence is None:
                if not (char == "`" and "`" in trailing):
                    open_fence = (char, length)
                    offset += len(raw_line) + 1
                    continue
            elif char == open_fence[0] and length >= open_fence[1] and _is_blank(trailing):
                open_fence = None
                offset += len(raw_line) + 1
                continue
            else:
                offset += len(raw_line) + 1
                continue
        if open_fence is not None:
            offset += len(raw_line) + 1
            continue
        bullet_text = None
        cbm = _CHECKBOX_UPDATE_RE.match(line)
        if cbm:
            bullet_text = cbm.group(3)
        else:
            dm2 = _DASH_UPDATE_RE.match(line)
            if dm2:
                bullet_text = dm2.group(2)
            else:
                nm = _NUMBERED_UPDATE_RE.match(line)
                if nm:
                    bullet_text = nm.group(2)
        if bullet_text is not None and match(bullet_text, raw_line, i):
            new_line = transform(raw_line)
            if not isinstance(new_line, str):
                return content
            return content[:offset] + new_line + content[offset + len(raw_line):]
        offset += len(raw_line) + 1
    return content


def update_heading(content, match, transform):
    """Rewrite the physical line of the first ATX heading (outside fences) accepted by ``match``.

    ``match(heading, raw_line, line_index)`` -> bool (``line_index`` is 0-based); ``transform(raw_line)`` -> str.
    """
    if not isinstance(content, str) or len(content) == 0:
        return content
    for heading in tokenize_headings(content):
        newline_at = content.find("\n", heading["offset"])
        line_end = len(content) if newline_at == -1 else newline_at
        raw_line = content[heading["offset"]:line_end]
        if not match(heading, raw_line, heading["line"] - 1):
            continue
        new_line = transform(raw_line)
        if not isinstance(new_line, str):
            return content
        return content[:heading["offset"]] + new_line + content[line_end:]
    return content


# ─── tagged blocks ────────────────────────────────────────────────────────────

def _tagged_block_pattern(tag_name, ignore_case, allow_attributes):
    esc = re.escape(tag_name)
    opener = "<" + esc + "(?:" + _WS + "[^>]{0,1000})?>" if allow_attributes else "<" + esc + ">"
    boundary = "<" + esc + "(?:" + _WS + "|>)" if allow_attributes else "<" + esc + ">"
    return re.compile(opener + "((?:(?!" + boundary + ")[\\s\\S])*?)</" + esc + ">",
                      re.IGNORECASE if ignore_case else 0)


def extract_tagged_blocks(content, tag_name, allow_attributes=False):
    """Inner text of every ``<tag>...</tag>`` block, in document order (no nesting; ReDoS-safe boundary)."""
    if not isinstance(content, str) or len(content) == 0:
        return []
    if not isinstance(tag_name, str) or len(tag_name) == 0:
        return []
    return [m.group(1) for m in _tagged_block_pattern(tag_name, False, allow_attributes).finditer(content)]


def strip_tagged_blocks(content, tag_name, allow_attributes=False, case_sensitive=False):
    """Remove every ``<tag>...</tag>`` block (case-insensitive unless ``case_sensitive``)."""
    if not isinstance(content, str) or len(content) == 0:
        return ""
    if not isinstance(tag_name, str) or len(tag_name) == 0:
        return content
    return _tagged_block_pattern(tag_name, not case_sensitive, allow_attributes).sub("", content)


def _restore_placeholders(text, placeholder, originals):
    restored = text
    for i, original in enumerate(originals):
        marker = placeholder(i)
        at = restored.find(marker)
        if at == -1 or restored.find(marker, at + len(marker)) != -1:
            return None
        restored = restored[:at] + original + restored[at + len(marker):]
    return restored


def edit_outside_tagged_blocks(content, tag_name, edit, allow_attributes=False, case_sensitive=False):
    """Run ``edit`` with every ``<tag>`` block replaced by a placeholder comment, then restore the blocks byte-for-byte.

    A non-string edit result, or a lost/duplicated placeholder, returns ``content`` unchanged.
    """
    if not isinstance(content, str) or len(content) == 0:
        return content
    if not isinstance(tag_name, str) or len(tag_name) == 0:
        return edit(content)
    blocks = []
    nonce = 0
    while f"<!-- gsd-masked-{tag_name}-{nonce}-" in content:
        nonce += 1

    def placeholder(i):
        return f"<!-- gsd-masked-{tag_name}-{nonce}-{i} -->"

    def mask(m):
        blocks.append(m.group(0))
        return placeholder(len(blocks) - 1)

    masked = _tagged_block_pattern(tag_name, not case_sensitive, allow_attributes).sub(mask, content)
    if not blocks:
        return edit(content)
    edited = edit(masked)
    if not isinstance(edited, str):
        return content
    restored = _restore_placeholders(edited, placeholder, blocks)
    return content if restored is None else restored


# ─── maskFences / editOutsideFences ───────────────────────────────────────────

@dataclass(frozen=True)
class FenceMask:
    """Fence-masked view of some content plus the inverse that puts the blocks back."""
    masked: str
    restore: Callable[[str], Optional[str]]


def mask_fences(content):
    """Replace every fenced block with one ``<!-- gsd-masked-fence-... -->`` line; ``restore`` splices them back.

    ``restore(edited)`` returns ``None`` when the edit lost or duplicated a placeholder.
    """
    identity = FenceMask(content, lambda edited: edited)
    if not isinstance(content, str) or len(content) == 0:
        return identity
    lines = content.split("\n")
    blocks = scan_fenced_blocks(lines)
    if not blocks:
        return identity
    nonce = 0
    while f"<!-- gsd-masked-fence-{nonce}-" in content:
        nonce += 1

    def placeholder(i):
        return f"<!-- gsd-masked-fence-{nonce}-{i} -->"

    kept = []
    originals = []
    cursor = 0
    for block in blocks:
        end = len(lines) - 1 if block["closeLineIdx"] == -1 else block["closeLineIdx"]
        while cursor < block["openLineIdx"]:
            kept.append(lines[cursor])
            cursor += 1
        originals.append("\n".join(lines[block["openLineIdx"]:end + 1]))
        kept.append(placeholder(len(originals) - 1))
        cursor = end + 1
    kept.extend(lines[cursor:])

    def restore(edited):
        if not isinstance(edited, str):
            return None
        return _restore_placeholders(edited, placeholder, originals)

    return FenceMask("\n".join(kept), restore)


def edit_outside_fences(content, edit):
    """Run ``edit`` over ``content`` with fenced blocks hidden; a bad edit returns ``content`` unchanged."""
    if not isinstance(content, str) or len(content) == 0:
        return content
    mask = mask_fences(content)
    edited = edit(mask.masked)
    if not isinstance(edited, str):
        return content
    restored = mask.restore(edited)
    return content if restored is None else restored


# ─── replaceSection / withSection / deleteSection ─────────────────────────────

def replace_section(content, section, new_body):
    """Splice ``new_body`` in place of the section's body (``bodyStart``..``bodyEnd``)."""
    if not isinstance(content, str):
        return content
    if not isinstance(new_body, str):
        return content
    return content[:section["bodyStart"]] + new_body + content[section["bodyEnd"]:]


def with_section(content, target, edit, opts=None):
    """Run ``edit`` against ONLY the body of the section matching ``target`` (exact trimmed heading text or predicate).

    A miss, a non-string edit result, or an unchanged result returns ``content`` unchanged.
    """
    if not isinstance(content, str):
        return content
    if callable(target):
        predicate = target
    else:
        wanted = _trim(target)
        predicate = lambda h: _trim(h["text"]) == wanted  # noqa: E731
    section = collect_section(content, predicate, opts or {})
    if not section:
        return content
    new_body = edit(section["body"])
    if not isinstance(new_body, str) or new_body == section["body"]:
        return content
    return replace_section(content, section, new_body)


def delete_section(content, heading_predicate, opts=None):
    """Delete the matching heading line plus its body (level-bounded); a miss returns ``content`` unchanged.

    ``endOffset`` caps the deleted range (the earlier boundary wins). At most one resulting blank-line
    seam is collapsed to a single blank line.
    """
    if not isinstance(content, str):
        return content
    opts = opts or {}
    headings = tokenize_headings(content)
    target_idx = _find_heading_index(headings, heading_predicate)
    if target_idx == -1:
        return content
    target = headings[target_idx]
    lines = content.split("\n")
    stop_line = _find_stop_line(headings, target_idx, target, opts, len(lines) + 1)
    line_offsets, eof_offset = _line_offsets(lines)
    section_start = line_offsets[target["line"] - 1]
    heading_bounded_end = line_offsets[stop_line - 1] if stop_line <= len(lines) else eof_offset
    end_offset = opts.get("endOffset")
    if (isinstance(end_offset, (int, float)) and not isinstance(end_offset, bool)
            and math.isfinite(end_offset)):
        explicit_end = max(0, min(len(content), end_offset))
    else:
        explicit_end = heading_bounded_end
    section_end = min(heading_bounded_end, explicit_end)
    if section_end <= section_start:
        return content
    before = content[:section_start]
    after = content[section_end:]
    collapsed_before = re.sub("(?:\r\n|\n){3,}\\Z",
                              lambda m: "\r\n\r\n" if "\r\n" in m.group(0) else "\n\n", before, count=1)
    return collapsed_before + after


# ─── extractXmlTagBodies ──────────────────────────────────────────────────────

XML_DECISION_TAG_NAMES = ("objective", "tasks", "task", "action", "read_first", "behavior", "verify",
                          "acceptance_criteria", "done")


def _xml_decision_tag_regex(tag_name):
    return re.compile(
        "<" + tag_name + "(?:" + _WS + "[^>]{0,1000})?>((?:(?!<" + tag_name + "(?:" + _WS + "|>))[\\s\\S])*?)</"
        + tag_name + ">", re.IGNORECASE)


def extract_xml_tag_bodies(text):
    """Bodies of every planner-canonical XML tag (``XML_DECISION_TAG_NAMES`` order), joined by newlines.

    Each tag's body ends only at its OWN closing tag, so an inner scanned tag is absorbed into the
    outer body and also matched on its own pass; empty bodies are dropped.
    """
    parts = []
    for tag_name in XML_DECISION_TAG_NAMES:
        for m in _xml_decision_tag_regex(tag_name).finditer(text):
            if m.group(1):
                parts.append(m.group(1))
    return "\n".join(parts)
