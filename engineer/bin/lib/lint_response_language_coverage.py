"""Response-language coverage lint: every workflow must carry the response-language contract.

Port of ``scripts/lint-response-language-coverage.cjs`` from gsd-core (MIT, Copyright (c) 2026 Open GSD),
pinned at commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79.

A workflow file passes when it contains EITHER an ``@``-import of a shared directive reference
(``references/response-language-directive.md``, whose own text must still carry an actionable
directive) OR its own inline ``response_language`` directive: one line with the config field, an
action verb, a user-output term and a narration-class token (``narration`` or ``between tool calls``).
A workflow fragment (``<workflow>/<modes|steps|templates|detail>/<name>.md``) additionally passes
when its parent workflow dispatches that exact fragment from a read/execute/run line and is itself
covered. Exit 0 only when workflows were found AND every one is covered; a run that inspected
nothing is a failure.

Usage: ``python -m lib.lint_response_language_coverage`` from ``engineer/bin``.

Deviations:
- Path mapping: upstream ``gsd-core/workflows/`` -> ``engineer/workflows/`` (``WORKFLOWS_DIR``) and
  upstream ``gsd-core/`` -> ``engineer/`` (``REFERENCE_ROOT``, so ``references/...`` resolves to
  ``engineer/references/...``). Import lines are ``@~/.claude/engineer/references/...``; the dispatch
  needle is ``engineer/workflows/<path>``.
- ``EXACT_INLINE_DIRECTIVE_WORKFLOWS`` keeps only the upstream entries that exist in
  ``engineer/workflows/``; upstream lists ``discuss-phase/modes/{advisor,analyze,batch,chain,default,power}.md``,
  ``help/modes/*.md``, ``plan-phase/steps/prd-express-path.md`` and ``settings-advanced.md``, which this
  repo does not have. ``DIRECTIVE_REFS`` keeps both upstream references although
  ``engineer/references/execute-phase-response-language.md`` does not exist here; it is consulted only
  if a workflow imports it.
- The upstream ``main(workflowsDir, io, refRoot)`` is ``run(workflows_dir, io, ref_root)`` here; ``main(argv)``
  is the CLI wrapper, takes no options (extra arguments are ignored, as upstream ignores them) and returns
  the exit code. ``io`` is any object with ``log(message)`` and ``error(message)``.
- The default root is derived from this file's location (``engineer/bin/lib`` -> repository root).
- JavaScript regex semantics are kept explicit: whitespace is the JavaScript set (U+0085 excluded,
  U+FEFF included), ``\\w``/``\\b`` are ASCII, ``.`` excludes line terminators.
- The directory walk follows symlinks and junctions with a visited set of real paths, as upstream does
  for symlinks; a link whose target cannot be stat-ed is skipped.
"""
from __future__ import annotations

import errno
import os
from pathlib import Path
import re
import stat
import sys

_JS_WS_CHARS = "\t\n\v\f\r   " + "".join(chr(c) for c in range(0x2000, 0x200B)) + "    　﻿"
_NOT_WS = "[^" + "".join(re.escape(c) for c in _JS_WS_CHARS) + "]"
_DOT = "[^\n\r  ]"

_DEFAULT_ROOT = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = str(_DEFAULT_ROOT / "engineer" / "workflows")
# A reference resolves as a sibling of the workflow catalog, so a fixture tree and the real one
# resolve by one rule.
REFERENCE_ROOT = str(_DEFAULT_ROOT / "engineer")
WORKFLOWS_PREFIX = "engineer/workflows/"

DIRECTIVE_REFS = (
    "references/response-language-directive.md",
    "references/execute-phase-response-language.md",
)

# Names the narration class explicitly: "user-facing prose" alone reads, in practice, as the
# question/answer surface, which is the half of the output the contract was never about.
INLINE_RESPONSE_LANGUAGE_DIRECTIVE = (
    "Apply response_language to all user-facing prose — narration between tool calls, status updates, "
    "progress notes, and findings included; preserve code, paths, and identifiers."
)

# A lazy-loaded mode/step/template carries its own directive only when it cannot PROVE inheritance
# (no parent dispatches it from a read/execute context, or the parent is itself uncovered). The exact
# sentence is pinned because these files cannot take the eager @-reference.
EXACT_INLINE_DIRECTIVE_WORKFLOWS = frozenset((
    "discuss-phase/modes/all.md",
    "discuss-phase/modes/auto.md",
    "discuss-phase/modes/text.md",
    "discuss-phase/templates/context.md",
    "discuss-phase/templates/discussion-log.md",
    "execute-phase/steps/code-review-disposition.md",
    "execute-phase/steps/codebase-drift-gate.md",
    "execute-phase/steps/gap-closure-artifacts.md",
    "execute-phase/steps/regression-gate.md",
    "execute-phase/steps/regression-gate-run.md",
    "execute-phase/steps/worktree-recovery-policy.md",
    "quick-batch/steps/plan-checker-loop.md",
))

# Fragment directories: a file under one is a SECTION of its parent workflow, reached by a
# `read and execute engineer/workflows/<path>` stub that fires with the parent's directive loaded.
FRAGMENT_DIRS = frozenset(("modes", "steps", "templates", "detail"))

_ASCII_I = re.I | re.A
DIRECTIVE_ACTION_RE = re.compile(r"\b(?:apply|present|render|respond|translate|use|write|must|should)\b", _ASCII_I)
USER_OUTPUT_RE = re.compile(r"\b(?:explanations?|language|narration|outputs?|prompts?|prose|questions?|templates?|user-facing)\b", _ASCII_I)
# The defect is NARRATION, not the question/answer surface: coverage requires the word "narration"
# or output described as running "between tool calls". Bare status/progress/findings do not name it.
NARRATION_CLASS_RE = re.compile(r"\bnarration\b|\bbetween tool calls\b", _ASCII_I)
_RESPONSE_LANGUAGE_RE = re.compile(r"\bresponse_language\b", _ASCII_I)

# The catalog's extensions, matched case-insensitively and by whole extension, so SETTINGS.MD is
# discovered (and judged) on every platform rather than exempted on case-sensitive ones.
WORKFLOW_EXTENSIONS = frozenset((".md",))

# How far a read/execute verb may sit from the fragment path it governs on the same line.
ENTRY_POINT_VERB_WINDOW = 40
ENTRY_POINT_VERB_RE = re.compile(rf"\b(?:read|execute|run)\b{_DOT}{{0,{ENTRY_POINT_VERB_WINDOW}}}\Z", _ASCII_I)

DIRECTIVE_IMPORT_RES = tuple(
    re.compile(rf"@(?:~|\$HOME)/{_NOT_WS}*{re.escape(ref)}") for ref in DIRECTIVE_REFS
)


def _js_trim(value):
    return value.strip(_JS_WS_CHARS)


def _read_text(path):
    return Path(path).read_bytes().decode("utf-8", errors="replace")


def _lines(content):
    return re.split(r"\r?\n", content)


def _relative(file, directory):
    return os.path.relpath(file, directory).replace(os.sep, "/")


def is_workflow_file(name):
    return os.path.splitext(name)[1].lower() in WORKFLOW_EXTENSIONS


def find_markdown_files_recursive(directory, seen=None):
    """Walk the catalog, FOLLOWING symlinked subtrees.

    A symlinked directory is resolved and entered once (cycles are bounded by ``seen``, the set of real
    paths already entered); a broken link contributes nothing. Raises ``OSError`` when ``directory``
    itself cannot be listed.
    """
    seen = set() if seen is None else seen
    files = []
    try:
        real = os.path.realpath(directory)
    except (OSError, ValueError):
        real = directory
    if real in seen:
        return files
    seen.add(real)
    for entry in os.scandir(directory):
        full = os.path.join(directory, entry.name)
        is_dir = entry.is_dir(follow_symlinks=False)
        is_file = entry.is_file(follow_symlinks=False)
        if entry.is_symlink() or (not is_dir and not is_file):
            try:
                mode = os.stat(full).st_mode
            except OSError:
                continue
            is_dir, is_file = stat.S_ISDIR(mode), stat.S_ISREG(mode)
        if is_dir:
            files.extend(find_markdown_files_recursive(full, seen))
        elif is_file and is_workflow_file(entry.name):
            files.append(full)
    files.sort()
    return files


def imported_directive_reference(content):
    """Which known reference does this file import, if any?

    Only a real ``@``-import occupying a whole line counts; prose naming the path loads nothing.
    """
    lines = [_js_trim(line) for line in _lines(content)]
    for ref, pattern in zip(DIRECTIVE_REFS, DIRECTIVE_IMPORT_RES):
        if any(pattern.fullmatch(line) for line in lines):
            return ref
    return None


def imports_directive_reference(content):
    return imported_directive_reference(content) is not None


def carries_inline_directive(content):
    """One line carrying all four signals: the config field, an action verb, a user-output term, narration.

    LIMITATION (text, not AST): the four hits are independent, so polarity is not read; a line that
    negates the instruction still satisfies them.
    """
    return any(
        _RESPONSE_LANGUAGE_RE.search(line) and DIRECTIVE_ACTION_RE.search(line)
        and USER_OUTPUT_RE.search(line) and NARRATION_CLASS_RE.search(line)
        for line in _lines(content)
    )


# Keyed by identity AND version (size + mtime), so a caller that rewrites a reference and re-asks
# gets the fresh verdict rather than a permanent one.
_reference_directive_cache = {}


def reference_carries_directive(ref, ref_root=None):
    """Does the SHARED FILE a workflow imports itself carry an actionable directive?"""
    ref_root = REFERENCE_ROOT if ref_root is None else ref_root
    file = os.path.join(str(ref_root), ref)
    stamp = "missing"
    try:
        info = os.stat(file)
        stamp = f"{info.st_size}:{info.st_mtime_ns}"
    except (OSError, ValueError):
        pass  # keep the missing stamp; the read below decides the verdict
    key = "\0".join([str(ref_root), ref, stamp])
    if key not in _reference_directive_cache:
        try:
            verdict = carries_inline_directive(_read_text(file))
        except (OSError, ValueError):
            verdict = False
        _reference_directive_cache[key] = verdict
    return _reference_directive_cache[key]


def find_broken_directive_references(files, ref_root=None):
    """Of the references these files actually import, which are missing, unreadable or no longer actionable?"""
    ref_root = REFERENCE_ROOT if ref_root is None else ref_root
    imported = set()
    for file in files:
        try:
            content = _read_text(file)
        except OSError:
            continue
        ref = imported_directive_reference(content)
        if ref is not None:
            imported.add(ref)
    return sorted(ref for ref in imported if not reference_carries_directive(ref, ref_root))


def has_response_language_coverage(content, ref_root=None):
    ref_root = REFERENCE_ROOT if ref_root is None else ref_root
    ref = imported_directive_reference(content)
    if ref is not None:
        return reference_carries_directive(ref, ref_root)
    return carries_inline_directive(content)


def names_fragment_as_entry_point(parent, relative):
    """Does the parent name this fragment as a live ENTRY POINT, rather than merely mention its path?

    The path must follow a read/execute/run verb within ``ENTRY_POINT_VERB_WINDOW`` characters on the
    same line, in the catalog-rooted spelling (``engineer/workflows/<relative>``) or the catalog-relative
    one, and must not be the tail of a longer path.

    LIMITATION: Markdown is read as text; a stub commented out or quoted in a fenced example still matches.
    """
    for line in _lines(parent):
        for needle in (f"{WORKFLOWS_PREFIX}{relative}", relative):
            at = line.find(needle)
            if at == -1 or (at > 0 and re.fullmatch(r"[A-Za-z0-9_/.-]", line[at - 1])):
                continue
            if ENTRY_POINT_VERB_RE.search(line[:at]):
                return True
    return False


def inherits_parent_coverage(workflows_dir, relative, ref_root=None):
    """A fragment inherits its parent workflow's coverage only when that is PROVEN per file.

    1. the path is ``<workflow>/<fragment-dir>/<name>.md``; 2. ``<workflow>.md`` exists and dispatches
    this exact fragment from a read/execute context; 3. the parent is itself covered.
    """
    ref_root = REFERENCE_ROOT if ref_root is None else ref_root
    segments = relative.split("/")
    if len(segments) != 3 or segments[1] not in FRAGMENT_DIRS:
        return False
    parent_path = os.path.join(str(workflows_dir), f"{segments[0]}.md")
    if not os.path.exists(parent_path):
        return False
    parent = _read_text(parent_path)
    if not names_fragment_as_entry_point(parent, relative):
        return False
    return has_response_language_coverage(parent, ref_root)


def find_violations(workflows_dir=None, ref_root=None):
    """Paths of workflow files with no response-language coverage."""
    workflows_dir = WORKFLOWS_DIR if workflows_dir is None else workflows_dir
    ref_root = REFERENCE_ROOT if ref_root is None else ref_root
    violations = []
    for file in find_markdown_files_recursive(workflows_dir):
        relative = _relative(file, workflows_dir)
        content = _read_text(file)
        if relative in EXACT_INLINE_DIRECTIVE_WORKFLOWS:
            if INLINE_RESPONSE_LANGUAGE_DIRECTIVE in _lines(content):
                continue
            # Only the reference form is admitted in place of the pin: its wording is validated in
            # turn by find_broken_directive_references. A reworded inline line stays a violation.
            if imports_directive_reference(content) and has_response_language_coverage(content, ref_root):
                continue
            violations.append(file)
            continue
        if has_response_language_coverage(content, ref_root):
            continue
        if not inherits_parent_coverage(workflows_dir, relative, ref_root):
            violations.append(file)
    return violations


class _Console:
    @staticmethod
    def log(message):
        _write(sys.stdout, f"{message}\n")

    @staticmethod
    def error(message):
        _write(sys.stderr, f"{message}\n")


def _write(stream, text):
    try:
        stream.write(text)
    except UnicodeEncodeError:
        encoding = getattr(stream, "encoding", None) or "ascii"
        stream.write(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))
    stream.flush()


def run(workflows_dir=None, io=None, ref_root=None):
    """Lint ``workflows_dir``; returns the exit code (0 only when every discovered workflow is covered)."""
    workflows_dir = WORKFLOWS_DIR if workflows_dir is None else workflows_dir
    ref_root = REFERENCE_ROOT if ref_root is None else ref_root
    io = _Console if io is None else io
    # The catalog is discovered, not declared, so an unreadable or empty directory yields an empty
    # violation list, indistinguishable from full coverage if "no violations" were the only success
    # condition. Both discovery failures are therefore lint failures in their own right.
    try:
        files = find_markdown_files_recursive(workflows_dir)
    except (FileNotFoundError, NotADirectoryError) as error:
        code = "ENOENT" if isinstance(error, FileNotFoundError) else "ENOTDIR"
        io.error(
            f"lint-response-language-coverage: cannot read the workflow directory {workflows_dir} ({code}).\n"
            "Coverage cannot be established, so this is a failure and not a pass (#2529)."
        )
        return 1
    except OSError as error:
        if error.errno in (errno.ENOENT, errno.ENOTDIR):
            io.error(
                f"lint-response-language-coverage: cannot read the workflow directory {workflows_dir} "
                f"({errno.errorcode[error.errno]}).\nCoverage cannot be established, so this is a failure and not a pass (#2529)."
            )
            return 1
        raise

    if len(files) == 0:
        io.error(
            f"lint-response-language-coverage: no workflow files found under {workflows_dir}.\n"
            "A run that inspected zero workflows cannot establish coverage (#2529)."
        )
        return 1

    # Shared references are checked ONCE, before the per-file pass: a reference that has gone missing
    # or been reworded back to the weak sentence is one systemic failure, not one per importer.
    broken = find_broken_directive_references(files, ref_root)
    if broken:
        io.error(
            f"lint-response-language-coverage: {len(broken)} shared directive reference(s) no longer carry an actionable directive (#2529, REQ-LANG-04).\n"
            "Workflows that @-import a reference take ALL of their coverage from it, so a missing,\n"
            "unreadable, or reworded reference silently uncovers every one of them:\n\n"
            + "\n".join(f"  - {ref}" for ref in broken) + "\n\n"
            "The file must itself name the narration class on the same line as response_language\n"
            "— the same rule an inline directive must satisfy."
        )
        return 1

    violations = find_violations(workflows_dir, ref_root)
    if violations:
        io.error(
            f"lint-response-language-coverage: {len(violations)} workflow(s) have no response-language coverage (#2529).\n"
            "Each workflow must either @-reference a recognized response-language directive\n"
            "or carry its own inline `response_language` directive (unless its parent dispatches it).\n"
            'An inline directive names the narration class with the word "narration" or the phrase\n'
            '"between tool calls" (REQ-LANG-04); enumerating status updates, progress notes or\n'
            "findings without naming the class does not satisfy it:\n\n"
            + "\n".join(f"  - {_relative(file, workflows_dir)}" for file in violations)
        )
        return 1

    io.log(f"lint-response-language-coverage: OK ({len(files)} workflows covered)")
    return 0


def main(argv=None):
    """CLI entry point: lint this checkout's ``engineer/workflows`` tree."""
    return run()


if __name__ == "__main__":
    raise SystemExit(main())
