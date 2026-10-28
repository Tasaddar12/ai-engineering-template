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

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from .posix_shell import find_posix_shell

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

def bash_path() -> str | None:
    """Absolute path of a real bash (Git Bash on Windows, never the System32 WSL launcher), or None."""
    return find_posix_shell("bash")


def shell_available() -> bool:
    return bash_path() is not None


def posix(path) -> str:
    return Path(path).as_posix()


def run_bash(script: str, args=(), env: dict | None = None, cwd=None, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run the script under bash with `args` in "$@" from $1.

    The script travels through a temporary file rather than `bash -c`: a Windows command line is re-encoded
    through the ANSI code page, which corrupts non-ASCII characters in the shipped fences and breaks quoting.
    """
    with tempfile.TemporaryDirectory(prefix="engineer-crp-") as directory:
        path = Path(directory) / "fixture.sh"
        path.write_bytes(script.encode("utf-8"))
        return subprocess.run([bash_path(), posix(path), *map(str, args)], env=env, cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=timeout)


def bash_syntax_error(script: str) -> str:
    """`bash -n` stderr for the script, empty when it parses."""
    with tempfile.TemporaryDirectory(prefix="engineer-crp-") as directory:
        path = Path(directory) / "syntax.sh"
        path.write_bytes(script.encode("utf-8"))
        result = subprocess.run([bash_path(), "-n", posix(path)], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
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


# --- Gate counts (block 1 of the disposition step) --------------------------------

# POSIX [[:space:]] as the C locale defines it; the shipped reads pin LC_ALL=C so unicode spaces are NOT trimmed.
SPACE = "[ \t\n\v\f\r]"
TRIM = re.compile(f"^{SPACE}+|{SPACE}+$")
GATE_UNPARSED = ("Code review status unparsed: REVIEW.md is present but its frontmatter has no parseable "
                 "status; severity counts unavailable.\n")


def _first(lines: list[str], pattern: str) -> str:
    compiled = re.compile(pattern)
    for line in lines:
        if compiled.match(line):
            return TRIM.sub("", line[line.index(":") + 1:])
    return ""


def parse_gate_counts(review_text: str) -> dict:
    """Mirror of the gate's frontmatter scalar reads: first closed `---` block only, counts scoped to `findings:`."""
    lines = str(review_text).replace("\r", "").split("\n")
    frontmatter: list[str] = []
    if lines and lines[0] == "---":
        buffer, closed = [], False
        for line in lines[1:]:
            if line == "---":
                closed = True
                break
            buffer.append(line)
        if closed:
            frontmatter = buffer
    block, inside = [], False
    for line in frontmatter:
        if re.match(f"^findings:{SPACE}*$", line):
            inside = True
            continue
        if inside and re.match(f"^[^ \t\n\v\f\r]", line):
            break
        if inside:
            block.append(line)
    return {
        "status": _first(frontmatter, r"^status:(.*)$"),
        "critical": _first(block, f"^{SPACE}*(?:critical|blocker):(.*)$"),
        "warning": _first(block, f"^{SPACE}*warning:(.*)$"),
        "info": _first(block, f"^{SPACE}*info:(.*)$"),
        "total": _first(block, f"^{SPACE}*total:(.*)$"),
    }


def render_gate_message(counts: dict, phase_number) -> str:
    """The message the shipped fence prints for parsed counts; gated on digit-only, <=8 digit, consistent sums."""
    def numeric(value):
        return value != "" and re.fullmatch("[0-9]+", value) is not None and len(value) <= 8
    values = [counts["total"], counts["critical"], counts["warning"], counts["info"]]
    consistent = all(numeric(value) for value in values)
    if consistent and int(counts["critical"]) + int(counts["warning"]) + int(counts["info"]) != int(counts["total"]):
        consistent = False
    if counts["status"] == "":
        return GATE_UNPARSED
    if counts["status"] in ("clean", "skipped"):
        return ""
    head = (f"Code review: {counts['total']} findings \u2014 {counts['critical']} critical, "
            f"{counts['warning']} warning, {counts['info']} info." if consistent else "Code review found issues.")
    return f"{head}\nConsider running: /code-review {phase_number} --fix\n"


def read_gate_message(stdout: str) -> dict:
    """Read the operator-visible message back into the facts it asserts."""
    full = re.search(r"^Code review: (\d+) findings \u2014 (\d+) critical, (\d+) warning, (\d+) info\.$", stdout, re.M)
    if full:
        return {"reported": True, "countsOk": "1", "total": full.group(1), "critical": full.group(2),
                "warning": full.group(3), "info": full.group(4)}
    if re.search(r"^Code review found issues\.$", stdout, re.M):
        return {"reported": True, "countsOk": "0"}
    if re.search(r"^Code review status unparsed: ", stdout, re.M):
        return {"reported": True, "countsOk": "0", "unparsed": True}
    return {"reported": False}


def _derived_phase_number(padded: str) -> str:
    """PHASE_NUMBER as a caller's parsed phase_number would carry it: no leading zero on the integer part."""
    return re.sub(r"^0+(?=\d)", "", padded) if re.fullmatch(r"\d+(\.\d+)?", padded) else padded


def run_gate_batch(cases: list[dict], extra_env: dict | None = None, step_path=None) -> list[dict]:
    """Run the step's FIRST shell fence (the frontmatter reads) once per case, inside ONE bash process.

    Each case runs in its own subshell under `set -euo pipefail` with its own PHASE_DIR. A case may carry
    `text` (REVIEW.md content), `write_review` (default True), `plant_dir` (a directory stands at the review
    path), `padded` (default "01") and `phase_number` (default derived from `padded`). Returns one
    {"exitCode", "stdout", "stderr"} per case, in order. Batching keeps the matrix affordable where a bash
    start-up and its grep/sed/awk children cost seconds.
    """
    fence = bash_fences(read_text(step_path or DISPOSITION_STEP_PATH))[0]
    if "REVIEW_COUNTS_OK" not in fence:
        raise ValueError("the counts block must still be the first fence")
    with tempfile.TemporaryDirectory(prefix="engineer-crp-") as root:
        args = []
        for index, case in enumerate(cases):
            directory = Path(root) / str(index)
            directory.mkdir()
            padded = case.get("padded", "01")
            review_path = directory / f"{padded}-REVIEW.md"
            if case.get("plant_dir"):
                review_path.mkdir()
            elif case.get("write_review", True):
                review_path.write_bytes(case.get("text", "").encode("utf-8"))
            phase = case.get("phase_number")
            args += [posix(directory), _derived_phase_number(padded) if phase is None else phase]
        script = "\n".join([
            'while [ "$#" -gt 0 ]; do',
            '  _d=$1; _p=$2; shift 2',
            '  ( PHASE_DIR="$_d"; PHASE_NUMBER="$_p"; export PHASE_DIR PHASE_NUMBER; set -euo pipefail',
            fence,
            '  ) 2>"$_d/.stderr"; echo "@@RC:$?@@"',
            "done",
        ])
        out = run_bash(script, args, env={**os.environ, **(extra_env or {})}, timeout=600).stdout
        parts = re.split(r"@@RC:(\d+)@@\n?", out)
        results = []
        for index in range(len(cases)):
            stderr_path = Path(root) / str(index) / ".stderr"
            results.append({"exitCode": int(parts[2 * index + 1]) if 2 * index + 1 < len(parts) else -1,
                            "stdout": parts[2 * index] if 2 * index < len(parts) else "",
                            "stderr": stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""})
        return results


def run_gate_counts(text: str = "", step_path=None, extra_env: dict | None = None, **case) -> dict:
    """One case through `run_gate_batch`."""
    return run_gate_batch([{"text": text, **case}], extra_env=extra_env, step_path=step_path)[0]


def normalize_phase_name(value: str) -> str:
    """Reference padding for a phase id: the integer part is left-padded to two digits; a letter and dot segments carry verbatim."""
    match = re.fullmatch(r"([0-9]+)([A-Z]?)((?:\.[0-9]+)*)", value)
    if not match:
        return value
    return match.group(1).rjust(2, "0") + match.group(2) + match.group(3)


# --- Disposition step: embedded script text, id census, derivations -------------------------

NODE_SCRIPT_OPEN = 'node -e "'
NODE_SCRIPT_CLOSE = '\n" || echo '
ID_ALTERNATION = re.compile(r"\(\?:((?:[A-Z]{2}\|)+[A-Z]{2})\)-")


def disposition_script(src: str) -> str:
    """The `node -e "..."` body of the disposition step, with the surrounding double-quote escapes undone.

    Text extraction only: the script is never executed. Inside "..." a backslash is special only before
    `$`, a backtick, `"` or `\\`, so one left-to-right pass undoes exactly what the shell string required.
    """
    text = src.replace("\r\n", "\n")
    start = text.find(NODE_SCRIPT_OPEN)
    if start == -1:
        raise ValueError("the disposition step must still embed a node -e script")
    body = text[start + len(NODE_SCRIPT_OPEN):]
    end = body.find(NODE_SCRIPT_CLOSE)
    if end == -1:
        raise ValueError("the node -e script must still be closed by its || echo fallback")
    return re.sub(r"\\([\\$`\"])", r"\1", body[:end])


def id_alternations(script: str) -> list[str]:
    """Every finding-id prefix enumeration in the script, each as a sorted `A|B|C` string."""
    return ["|".join(sorted(match.group(1).split("|"))) for match in ID_ALTERNATION.finditer(script)]


def severity_map_keys(script: str) -> list[str]:
    """Keys of the inline severity map indexed by the id prefix."""
    match = re.search(r"\{([^}]*?)\}\[id\.split", script)
    if not match:
        raise ValueError("the severity map must still be an inline object literal indexed by the id prefix")
    return re.findall(r"([A-Z]{2}):", match.group(1))


def emitted_id_prefixes(agent_text: str) -> set[str]:
    """Prefixes the reviewer agent declares: template headings, `X- IDs/prefix` prose and `IDs beginning with X-`."""
    found = set(re.findall(r"^###\s+([A-Z]+)-\d+:", agent_text, re.M))
    found |= set(re.findall(r"\b([A-Z]+)-\s*(?:IDs?|prefix)", agent_text))
    found |= set(re.findall(r"IDs? beginning with\s+`?([A-Z]+)-", agent_text))
    return found


def anchored_line_indexes(lines: list[str], anchor: str, expected: int) -> list[int]:
    """Indexes of every line containing `anchor`; ValueError unless exactly `expected` exist."""
    found = [index for index, line in enumerate(lines) if anchor in line]
    if len(found) != expected:
        raise ValueError(f"expected {expected} line(s) containing {anchor!r}, found {len(found)}")
    return found


def run_derivations(derivations: list[str], phase_ids: list[str], directory) -> list[list[str]]:
    """PADDED computed by each derivation for each phase id, from one bash process (a subshell per pair)."""
    script = "\n".join([
        'for _id in "$@"; do',
        *[f'  ( set -e; PHASE_NUMBER="$_id"; export PHASE_NUMBER\n{d}\n  printf "%s" "$PADDED" ) 2>&1; printf "@@END@@"' for d in derivations],
        "done",
    ])
    out = run_bash(script, phase_ids, env={**os.environ, "PHASE_DIR": posix(directory)}, timeout=300).stdout
    cells = out.split("@@END@@")
    width = len(derivations)
    return [cells[index * width:(index + 1) * width] for index in range(len(phase_ids))]


# --- Installed-runtime helper resolver blocks (#5640) ----------------------------------------

RESOLVER_BEGIN = "# engineer-resolve-lib begin "
RESOLVER_END = "# engineer-resolve-lib end"


def resolver_blocks(src: str) -> list[dict]:
    """Every resolver block of a file, in order: {"module", "text"}."""
    blocks, start = [], src.find(RESOLVER_BEGIN)
    while start != -1:
        line_end = src.index("\n", start)
        module = src[start + len(RESOLVER_BEGIN):line_end].split(" ")[0].rstrip(":")
        end = src.index(RESOLVER_END, line_end)
        blocks.append({"module": module, "text": src[start:end + len(RESOLVER_END)]})
        start = src.find(RESOLVER_BEGIN, end)
    return blocks


def run_resolver_block(block_text: str, env: dict, cwd, prefix: str = "") -> subprocess.CompletedProcess:
    """Run a resolver block, then print the directory it exported, in `cwd` with exactly `env`."""
    script = prefix + block_text.lstrip() + '\nprintf "%s" "$ENGINEER_LIB_DIR"\n'
    return run_bash(script, env=env, cwd=cwd)


def resolver_shape(block_text: str, module: str) -> str:
    """The block with its module name, indentation and the PATH-launcher candidate normalized away."""
    lines = []
    for line in block_text.replace(module, "<module>").split("\n"):
        line = line.strip()
        if line.startswith('if [ -z "$ENGINEER_LIB_DIR" ]'):
            continue
        if re.match(r'^(_engineer_gr=|case "\$_engineer_gr"|\[ -n "\$_engineer_gr" \])', line):
            continue
        lines.append(line.replace(' "$_engineer_gr"', ""))
    return "\n".join(lines)


# --- Disposition ledger through the Python runtime verb ---------------------------------------

ENGINE_PATH = SOURCE / "engineer" / "bin" / "engineer.py"


class ReconcileFixture:
    """A temp git repo holding one phase's review artifacts; `run` drives `engineer.py query review.reconcile`.

    The upstream tests execute the step's `node -e` ledger script. The installer rewrites that exact
    script to `review.reconcile` (bin/export_transforms.py), so the same behaviours are asserted against
    the verb's JSON result and the ledger file it writes.
    """

    def __init__(self, directory, phase: str = "01"):
        self.directory, self.phase = Path(directory), phase
        subprocess.run(["git", "init", "-q", "."], cwd=self.directory, capture_output=True, check=True)

    @property
    def ledger_path(self) -> Path:
        return self.directory / f"{self.phase}-REVIEW-DISPOSITION.md"

    def _put(self, name: str, text) -> None:
        if text is not None:
            (self.directory / name).write_bytes(text.encode("utf-8"))

    def run(self, review=None, prior=None, fix=None, iterations: dict | None = None, review_total=None) -> dict:
        phase = self.phase
        self._put(f"{phase}-REVIEW.md", review)
        self._put(f"{phase}-REVIEW-DISPOSITION.md", prior)
        self._put(f"{phase}-REVIEW-FIX.md", fix)
        for number, text in (iterations or {}).items():
            self._put(f"{phase}-REVIEW-FIX.iter{number}.md", text)
        args = [sys.executable, "-I", str(ENGINE_PATH), "query", "review.reconcile", "--phase", phase,
                "--review-file", f"{phase}-REVIEW.md", "--disposition-file", f"{phase}-REVIEW-DISPOSITION.md",
                "--fix-report-file", f"{phase}-REVIEW-FIX.md"]
        if review_total is not None:
            args += ["--review-total", str(review_total)]
        process = subprocess.run(args, cwd=self.directory, capture_output=True, text=True, encoding="utf-8", errors="replace",
                                 env={**os.environ, "ENGINEER_ROOT": str(self.directory)})
        try:
            result = json.loads(process.stdout)
        except ValueError:
            result = {}
        ledger = self.ledger_path.read_text(encoding="utf-8") if self.ledger_path.exists() else None
        rows = [{key: finding.get(key) for key in ("id", "severity", "disposition", "source", "carried")}
                for finding in result.get("findings", [])]
        return {"returncode": process.returncode, "result": result, "rows": rows, "ledger": ledger,
                "written": bool(result.get("written")), "stderr": process.stderr}
