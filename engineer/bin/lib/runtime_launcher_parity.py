"""Runtime launcher parity checks for the `engineer_run` preamble.

Ported from upstream gsd-core `tests/runtime-launcher-parity.test.cjs`
(Open GSD, MIT, Copyright (c) 2026 Open GSD; pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79).

The module holds the reusable logic: fenced shell block extraction, preamble
counting and ordering scans, snippet structure probes, and a small harness that
runs the canonical launcher snippet under POSIX shell against fixtures. The test
file `tests/test_runtime_launcher_parity.py` asserts the results against this
repo.

Deviations:
- `gsd-core/workflows/` -> `engineer/workflows/`; `gsd-core/references/gsd-run-resolver.md`
  -> `engineer/references/run-resolver.md`; `agents/` -> `agents/` (no `gsd-` prefix);
  `gsd_run` / `gsd-tools.cjs` -> `engineer_run` (a POSIX shell script resolved as
  `<home>/engineer/bin/engineer_run`); `_GSD_SHIM_NAME=` marker ->
  `_engineer_identity_ok() {` marker.
- This repo's snippet selects an `ENGINEER_RUN` path through one ordered candidate
  list (`_engineer_select`), identity-gating every candidate, instead of upstream's
  `_gsd_homes` / `_gsd_at` / `GSD_TOOLS` chain; the arm-order probes read that
  candidate list. The repo-local `.claude` and `.codex` arms hang off the git
  root (or cwd), not `RUNTIME_DIR`; `RUNTIME_DIR` feeds only the second candidate.
- The launcher is a shell script run with `sh`, so no `node` binary is linked
  into the isolated PATH.
- Only the Claude and Codex runtime homes exist here; upstream's other runtime
  home probes have no counterpart.
- The resolver reference delegates by sourcing the snippet file rather than
  repeating it, so the byte-equality probe accepts either form.
"""
from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parents[3]
WORKFLOWS_DIR = SOURCE / "engineer" / "workflows"
AGENTS_DIR = SOURCE / "agents"
SNIPPET_FILE = WORKFLOWS_DIR / "_runtime-launcher.snippet.sh"
RESOLVER_REFERENCE = SOURCE / "engineer" / "references" / "run-resolver.md"
RESOLVER_MARKER = "references/run-resolver.md"
LAUNCHER = "engineer_run"
PREAMBLE_MARKER = "_engineer_identity_ok() {"
SHELL_LANGS = ("bash", "sh", "shell", "zsh", "")
FENCE_OPEN = re.compile(r"^(\s*)```(\w+)?\s*$")
LAUNCHER_WORD = re.compile(r"\bengineer_run\b")
DEFAULT_VAR = re.compile(r"\$\{([A-Z_][A-Z0-9_]*):-")
HARD_ERROR = "ERROR: No engineer-runtime launcher was found"
EXPECTED_IDENTITY = "engineer-runtime"
# Variables that decide where the launcher resolves from; a fixture that does
# not scrub them lets the developer's real install win.
SNIPPET_SCRUB = {"CLAUDE_ENV_FILE": "", "BASH_ENV": "", "ENGINEER_RUN": "",
                 "CLAUDE_CONFIG_DIR": "", "CODEX_HOME": "", "RUNTIME_DIR": ""}
# Read by the snippet but supplied by the fixture itself.
CALLER_OR_SELF_ASSIGNED = {"RUNTIME_DIR", "ENGINEER_RUN"}


def read_text(path) -> str:
    return Path(path).read_text(encoding="utf-8")


def expected_preamble(snippet_text: str) -> list[str]:
    """Canonical preamble lines: every snippet line, without the trailing newline."""
    lines = re.split(r"\r?\n", snippet_text)
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if not lines:
        raise ValueError("_runtime-launcher.snippet.sh must not be empty")
    return lines


def extract_shell_blocks(content: str) -> list[dict]:
    """Shell fenced blocks with their lines; indented fences are supported."""
    blocks, in_block, lang, lines, indent = [], False, "", [], ""
    for line in re.split(r"\r?\n", content):
        if not in_block:
            opened = FENCE_OPEN.match(line)
            if opened:
                in_block, indent, lang, lines = True, opened.group(1), (opened.group(2) or "").lower(), []
            continue
        if re.match("^" + re.escape(indent) + r"```\s*$", line):
            if lang in SHELL_LANGS:
                blocks.append({"index": len(blocks), "lang": lang, "lines": lines})
            in_block, lang, lines, indent = False, "", [], ""
            continue
        lines.append(line)
    return blocks


def collect_markdown(directory) -> list[Path]:
    return sorted(Path(directory).rglob("*.md"))


def delegates_to_resolver_reference(content: str) -> bool:
    return RESOLVER_MARKER in content


def shell_text(content: str) -> str:
    """All shell block lines of a document joined in document order."""
    return "\n".join(line for block in extract_shell_blocks(content) for line in block["lines"])


def uses_launcher(content: str) -> bool:
    return any(LAUNCHER_WORD.search(line) for block in extract_shell_blocks(content) for line in block["lines"])


def count_occurrences(haystack: str, needle: str) -> int:
    count, position = 0, 0
    while True:
        index = haystack.find(needle, position)
        if index == -1:
            return count
        count += 1
        position = index + len(needle)


def preamble_violations(files, base, preamble: list[str]) -> list[str]:
    """Files using the launcher must hold exactly one canonical preamble before the first use."""
    needle = "\n".join(preamble)
    violations = []
    for path in files:
        relative = Path(path).relative_to(base).as_posix()
        content = read_text(path)
        if delegates_to_resolver_reference(content) or not uses_launcher(content):
            continue
        text = shell_text(content)
        found = count_occurrences(text, needle)
        if found != 1:
            violations.append(f"{relative}: expected exactly 1 canonical preamble occurrence in bash blocks, found {found}.")
            continue
        first_use = LAUNCHER_WORD.search(text)
        if text.index(needle) > first_use.start():
            violations.append(f"{relative}: preamble appears AFTER the first {LAUNCHER} reference - it must precede all {LAUNCHER} calls.")
    return violations


def token_offenders(files, base, token: str) -> list[str]:
    return [Path(path).relative_to(base).as_posix() for path in files if token in read_text(path)]


def files_missing_probe(files, base, probe: str) -> list[str]:
    """Inline-preamble files that use the launcher but lack `probe` in their shell blocks."""
    missing = []
    for path in files:
        content = read_text(path)
        if delegates_to_resolver_reference(content) or not uses_launcher(content):
            continue
        if probe not in shell_text(content):
            missing.append(Path(path).relative_to(base).as_posix())
    return missing


def default_arm_vars(snippet_text: str) -> list[str]:
    """Distinct names read through a `${NAME:-default}` arm, in first-seen order."""
    seen = []
    for match in DEFAULT_VAR.finditer(snippet_text):
        if match.group(1) not in seen:
            seen.append(match.group(1))
    return seen


def uncovered_default_vars(snippet_text: str, covered) -> list[str]:
    return [name for name in default_arm_vars(snippet_text) if name not in set(covered)]


def brace_depth(text: str) -> tuple[int, int]:
    """(final depth, minimum depth) of raw `{`/`}` counting, as downstream text scanners do."""
    depth = lowest = 0
    for char in text:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        lowest = min(lowest, depth)
    return depth, lowest


def select_candidates(snippet_text: str) -> list[str]:
    """Ordered candidate expressions passed to `_engineer_select` in the snippet."""
    match = re.search(r"^\s*_engineer_select \\\n((?:\s+\S.*\\\n)*\s+\S.*?)\s*\|\| \{", snippet_text, re.M)
    if not match:
        return []
    return [part.strip().rstrip("\\").strip() for part in match.group(1).splitlines() if part.strip()]


def candidate_index(candidates: list[str], fragment: str) -> int:
    for index, candidate in enumerate(candidates):
        if fragment in candidate:
            return index
    return -1


def resolver_reference_violations(reference_text: str, snippet_text: str, snippet_relative: str) -> list[str]:
    """The resolver reference must carry the canonical preamble or source the snippet file."""
    block_text = "\n".join("\n".join(block["lines"]) for block in extract_shell_blocks(reference_text)).strip()
    if block_text == "\n".join(expected_preamble(snippet_text)):
        return []
    sources = re.fullmatch(r"\.\s+(\S+)", block_text)
    if sources and sources.group(1).strip("\"'").endswith(snippet_relative):
        return []
    return [f"resolver reference block is neither byte-equal to the snippet nor sourcing {snippet_relative}: {block_text!r}"]


def roster_violations(roster: dict[str, Path]) -> list[str]:
    """Delegating files must load the shared resolver by @-include and not inline the preamble."""
    problems = []
    for name, path in roster.items():
        content = read_text(path)
        if RESOLVER_MARKER not in content:
            problems.append(f"{name}: missing the run-resolver.md @-include")
        if PREAMBLE_MARKER in content:
            problems.append(f"{name}: carries an inline preamble")
    return problems


# --- Behavioral harness -------------------------------------------------------

def shell_available() -> bool:
    return shutil.which("bash") is not None and shutil.which("sh") is not None


def posix(path) -> str:
    return Path(path).as_posix()


def quote(value) -> str:
    return "'" + str(value).replace("'", "'\"'\"'") + "'"


def snippet_env(overrides: dict | None = None, base: dict | None = None) -> dict:
    """Process env with every resolution-steering variable scrubbed, then overrides applied.

    Windows env names are case-insensitive, so any other casing of a key set here is dropped.
    """
    env = {**(os.environ if base is None else base), **SNIPPET_SCRUB, **(overrides or {})}
    owned = {key.upper(): key for key in [*SNIPPET_SCRUB, *(overrides or {})]}
    for key in list(env):
        owner = owned.get(key.upper())
        if owner is not None and owner != key:
            del env[key]
    return env


def has_launcher(directory) -> bool:
    return any(os.access(Path(directory) / name, os.X_OK) and (Path(directory) / name).is_file()
               for name in (LAUNCHER, LAUNCHER + ".exe"))


def build_isolated_path(base_path: str | None = None) -> str:
    """A PATH `command -v engineer_run` cannot resolve from.

    Only absolute directories survive (an empty element or a relative one puts the child's cwd on PATH),
    and any directory holding a resolvable `engineer_run` is dropped.
    """
    entries = (os.environ.get("PATH", "") if base_path is None else base_path).split(os.pathsep)
    return os.pathsep.join(entry for entry in entries if os.path.isabs(entry) and not has_launcher(entry))


def write_launcher_stub(directory, marker: str, identity: bool = True) -> Path:
    """An `engineer_run` stub: proves identity (optionally) and prints `<marker>:<args>`."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    identity_branch = (
        'if [ "$1" = "query" ] && [ "$2" = "runtime-identity" ]; then echo ' + EXPECTED_IDENTITY + '; exit 0; fi\n'
        if identity else ""
    )
    stub = directory / LAUNCHER
    stub.write_bytes((f'#!/bin/sh\n{identity_branch}echo "{marker}:$*"\n').encode("utf-8"))
    stub.chmod(0o755)
    return stub


def write_runtime_stub(root, marker: str, kind: str = "runtime", identity: bool = True) -> Path:
    """Install a stub under `<root>/<kind>/engineer/bin/engineer_run` (`kind` may be '' or '.claude' ...)."""
    base = Path(root) / kind if kind else Path(root)
    return write_launcher_stub(base / "engineer" / "bin", marker, identity)


def snippet_script(snippet_text: str, body: str = "", exports: dict | None = None, unset: tuple = ("ENGINEER_RUN",)) -> str:
    lines = []
    if unset:
        lines.append("unset " + " ".join(unset))
    for key, value in (exports or {}).items():
        lines.append(f"export {key}={quote(value)}")
    return "\n".join(lines) + "\n" + snippet_text + "\n" + body + "\n"


def run_script(script_text: str, workdir, env: dict, name: str = "fixture.sh") -> subprocess.CompletedProcess:
    """Write `script_text` beside the fixture and run it under bash from a non-git working directory."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    script = workdir / name
    script.write_bytes(script_text.encode("utf-8"))
    return subprocess.run(["bash", str(script)], cwd=workdir, env=env, capture_output=True, text=True)


def make_temp(prefix: str) -> str:
    return tempfile.mkdtemp(prefix=prefix)


# --- Standalone executable and env-file persistence --------------------------

def python_wrapper_dir(directory, interpreter) -> Path:
    """A directory whose `python3` and `python` exec `interpreter`, for hosts where the bare names are stubs."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name in ("python3", "python"):
        wrapper = directory / name
        wrapper.write_bytes(f'#!/bin/sh\nexec {quote(posix(interpreter))} "$@"\n'.encode("utf-8"))
        wrapper.chmod(0o755)
    return directory


def run_launcher_executable(launcher, args, env: dict) -> subprocess.CompletedProcess:
    """Run the shipped `engineer_run` script with `sh`, as the snippet does."""
    return subprocess.run(["sh", posix(launcher), *args], env=env, capture_output=True, text=True)


def env_file_path_line(env_file_text: str) -> str:
    """The `export PATH=` line the preamble persisted, or an empty string."""
    for line in env_file_text.splitlines():
        if line.startswith("export PATH="):
            return line
    return ""


def run_shell_text(command: str, env: dict, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", command], env=env, cwd=cwd, capture_output=True, text=True)


# --- Resolver extraction from a workflow ----------------------------------------

def extract_resolver_snippet(content: str) -> str:
    """The inline resolver block of a workflow, from the identity helper through the env-file `fi`."""
    lines = shell_text(content).split("\n")
    start = next((index for index, line in enumerate(lines) if line.strip() == PREAMBLE_MARKER), -1)
    if start == -1:
        raise ValueError("workflow does not contain the canonical runtime preamble")
    function_end = next((index for index in range(start, len(lines)) if lines[index].startswith("engineer_run() {")), -1)
    if function_end == -1:
        raise ValueError("runtime preamble does not define engineer_run")
    end = next((index for index in range(function_end, len(lines)) if lines[index] == "fi"), -1)
    if end == -1:
        raise ValueError("runtime preamble must end with a closing `fi`")
    return "\n".join(lines[start:end + 1])
