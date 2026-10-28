"""Code-review pipeline regression checks: scope parsing, severity labels, evidence consolidation.

Ported from upstream gsd-core `tests/code-review-pipeline-regression.test.cjs`
(Open GSD, MIT, Copyright (c) 2026 Open GSD; pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79).

The module holds pure mirrors of the parsers the workflow text embeds (SUMMARY
key-files, severity frontmatter, gate counts), the extractors that slice steps and
shell fences out of workflow/agent markdown, and a bash harness that executes the
shipped fences. `tests/test_code_review_pipeline_regression.py` asserts them
against this repo.

Deviations:
- `gsd-core/workflows/` -> `engineer/workflows/`; `agents/gsd-code-fixer.md` ->
  `agents/code-fixer.md`; `agents/gsd-code-reviewer.md` -> `agents/code-reviewer.md`;
  `gsd_run` / `gsd-tools` -> `engineer_run`; `gsd-core/workflows/...` read/execute
  pointers -> `engineer/workflows/...`.
- Upstream runs the embedded `node -e` / `node -` scripts. This repo's tests never
  execute Node: those scripts are not run, and the cases that need their output
  are skipped. The mirrors below stand in only for the pure parsing shapes.
- Upstream skips bash fixtures on win32 (`HAS_BASH`); here they run wherever a
  `bash` is found, with CRLF normalized exactly as `readFileNormalized` does.
- `structural-pre-pass.md` (the fallow step) is absent here, so its diff-base
  derivation cannot be extracted.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess

SOURCE = Path(__file__).resolve().parents[3]
WORKFLOW_PATH = SOURCE / "engineer" / "workflows" / "code-review.md"
FIX_WORKFLOW_PATH = SOURCE / "engineer" / "workflows" / "code-review-fix.md"
PRE_PASS_STEP_PATH = SOURCE / "engineer" / "workflows" / "code-review" / "steps" / "structural-pre-pass.md"
FIXER_PATH = SOURCE / "agents" / "code-fixer.md"
REVIEWER_PATH = SOURCE / "agents" / "code-reviewer.md"
SHARED_VERIFY_STEP_PATH = SOURCE / "engineer" / "workflows" / "execute-phase" / "steps" / "verify-phase-goal.md"
DISPOSITION_STEP_PATH = SOURCE / "engineer" / "workflows" / "execute-phase" / "steps" / "code-review-disposition.md"

KNOWN_EXTENSIONLESS_BUILD_FILES = frozenset({"dockerfile", "containerfile", "makefile", "justfile", "procfile"})


def read_text(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def read_normalized(path) -> str:
    """UTF-8 text with CRLF folded to LF, as the upstream `readFileNormalized` helper does."""
    return read_text(path).replace("\r\n", "\n")


# --- Pure mirrors ---------------------------------------------------------------

def is_acceptable_path(raw: str) -> bool:
    """Root-level and extensionless build files qualify, not only nested paths with an extension."""
    if re.search(r"\.[A-Za-z0-9]+$", raw):
        return True
    return raw.split("/")[-1].lower() in KNOWN_EXTENSIONLESS_BUILD_FILES


def parse_key_files(yaml: str) -> list[str]:
    """Mirror of the SUMMARY key-files extractor: only `created:` / `modified:` bullets, narrative stripped."""
    files, section = [], None
    for line in yaml.split("\n"):
        if re.match(r"^\s+created:", line):
            section = "created"
            continue
        if re.match(r"^\s+modified:", line):
            section = "modified"
            continue
        if re.match(r"^\s*[\w-]+:", line) and not re.match(r"^\s*-", line):
            section = None
            continue
        bullet = re.match(r"^\s+-\s+(.+)", line)
        if section and bullet:
            raw = bullet.group(1).strip()
            raw = re.sub(r"^['\"]|['\"]$", "", raw)
            raw = re.sub(r"\s+\([^)]*\)\s*$", "", raw)
            raw = re.split(r"\s+—\s", raw)[0].strip()
            if is_acceptable_path(raw):
                files.append(raw)
    return files


def parse_frontmatter_critical(frontmatter: str) -> int:
    """Mirror of `grep -E "^\\s*(critical|blocker):" | head -1 | cut -d: -f2 | xargs`."""
    for line in frontmatter.split("\n"):
        if re.match(r"^\s*(critical|blocker):", line):
            value = ":".join(line.split(":")[1:]).strip()
            match = re.match(r"^[+-]?\d+", value)
            return int(match.group(0)) if match else 0
    return 0


# --- Markdown slicing -------------------------------------------------------------

def step_section(src: str, name: str, closer: str = "</step>") -> str | None:
    """The `<step name="...">` body up to its closer, or None when the step is absent."""
    start = src.find(f'<step name="{name}">')
    if start == -1:
        return None
    return src[start:src.find(closer, start)]


def tag_section(src: str, tag: str) -> str | None:
    start = src.find(f"<{tag}>")
    if start == -1:
        return None
    return src[start:src.find(f"</{tag}>", start)]


def between(src: str, start_marker: str, end_marker: str, offset: int = 0) -> str | None:
    start = src.find(start_marker, offset)
    if start == -1:
        return None
    end = src.find(end_marker, start)
    return None if end == -1 else src[start:end]


def bash_fences(src: str) -> list[str]:
    """Every ```bash fence in a step file, in order (column-0 fences only)."""
    out, start, lines = [], -1, src.replace("\r\n", "\n").split("\n")
    for index, line in enumerate(lines):
        if start == -1 and re.match(r"^```bash\s*$", line):
            start = index + 1
        elif start != -1 and re.match(r"^```\s*$", line):
            out.append("\n".join(lines[start:index]))
            start = -1
    return out


def fence_containing(src: str, marker: str, from_index: int = 0) -> str:
    """The ```bash fence holding `marker` after `from_index`; ValueError when absent."""
    marker_index = src.find(marker, from_index)
    if marker_index == -1:
        raise ValueError(f'expected to find "{marker}" in workflow source')
    fence_start = src.rfind("```bash", 0, marker_index)
    if fence_start == -1:
        raise ValueError(f'no ```bash fence before "{marker}"')
    body_start = src.index("\n", fence_start) + 1
    fence_end = src.find("\n```", body_start)
    if fence_end == -1:
        raise ValueError(f'unterminated ```bash fence containing "{marker}"')
    return src[body_start:fence_end]


# --- Bash harness -----------------------------------------------------------------

def shell_available() -> bool:
    return shutil.which("bash") is not None


def posix(path) -> str:
    return Path(path).as_posix()


def run_bash(script: str, args=(), env: dict | None = None, cwd=None, timeout: int = 60) -> subprocess.CompletedProcess:
    """`bash -c <script> bash <args...>`; `bash` is $0 so the arguments land in "$@" from $1."""
    return subprocess.run(["bash", "-c", script, "bash", *map(str, args)], env=env, cwd=cwd, capture_output=True,
                          text=True, timeout=timeout)


def bash_syntax_error(script: str) -> str:
    """`bash -n` stderr for the script, empty when it parses."""
    result = subprocess.run(["bash", "-n", "-c", script], capture_output=True, text=True, timeout=60)
    return result.stderr if result.returncode else ""


def post_processing_script(src: str) -> str:
    """The tilde-expansion and deleted-file fences of the post-processing section, glued behind a REVIEW_FILES seed."""
    section = src.find("**Post-processing (all tiers):**")
    if section == -1:
        raise ValueError('code-review.md must have a "Post-processing (all tiers)" section')
    return "\n".join([
        'REVIEW_FILES=("$@")',
        fence_containing(src, "EXPANDED_FILES=()", section),
        fence_containing(src, "DELETED_COUNT=0", section),
        'printf "%s\\n" "${REVIEW_FILES[@]}"',
        'echo "REVIEW_FILES_COUNT=${#REVIEW_FILES[@]}"',
        'echo "DELETED_COUNT=$DELETED_COUNT"',
    ])


# --- Shell-doc scan (upstream tests/helpers/shell-doc-scan.cjs) ---------------------

def fold_shell_continuations(src: str) -> str:
    """Fold unquoted backslash-newline continuations into logical lines (text heuristic, not a shell parser)."""
    return re.sub(r"(^|[^\\])((?:\\\\)*)\\\n[ \t]*", lambda m: f"{m.group(1)}{m.group(2)} ", src, flags=re.M)


def closed_shell_fences(src: str) -> list[str]:
    """Bodies of closed ```bash / ```sh fences (info string compared case-insensitively)."""
    lines, out, start, info = src.replace("\r\n", "\n").split("\n"), [], -1, ""
    for index, line in enumerate(lines):
        if start == -1:
            opened = re.match(r"^ {0,3}(`{3,})([^`]*)$", line)
            if opened:
                start, info = index, opened.group(2).strip().lower()
        elif re.match(r"^ {0,3}`{3,}\s*$", line):
            if info in ("bash", "sh"):
                out.append("\n".join(lines[start + 1:index]))
            start = -1
    return out


def find_shell_fenced_matches(src: str, pattern) -> list[str]:
    """Regex matches (full match text) from logical lines inside closed bash/sh fences."""
    compiled = re.compile(pattern, re.M) if isinstance(pattern, str) else pattern
    return [match.group(0) for body in closed_shell_fences(src) for match in compiled.finditer(fold_shell_continuations(body))]


GREP_SITE = re.compile(r"^\s*[A-Z_]+=\$\(git log[^\n]*--grep=[^\n]*$", re.M)


def find_grep_sites(src: str) -> list[str]:
    return find_shell_fenced_matches(src, GREP_SITE)
