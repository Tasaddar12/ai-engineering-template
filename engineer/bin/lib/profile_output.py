"""Profile output: profile rendering, questionnaire, and artifact generation.

Ported from open-gsd/gsd-core src/profile-output.cts
(commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79, MIT, Copyright (c) 2026 Open GSD).

Commands (upstream name -> Python name, same ``(cwd, options, raw)`` argument shapes; ``options``
is a dict with the upstream keys):
    cmdWriteProfile -> cmd_write_profile          USER-PROFILE.md from analysis JSON
    cmdProfileQuestionnaire -> cmd_profile_questionnaire   fallback when no sessions exist
    cmdGenerateDevPreferences -> cmd_generate_dev_preferences   dev-preferences skill artifact
    cmdGenerateClaudeProfile -> cmd_generate_claude_profile     Developer Profile section
    cmdGenerateClaudeMd -> cmd_generate_claude_md          full CLAUDE.md with managed sections
    PROFILING_QUESTIONS, CLAUDE_INSTRUCTIONS               data tables, verbatim

Upstream has no CLI entry point in this module (the gsd-tools dispatcher calls it), so no
``main`` is exposed. Results go through ``output`` to stdout; fatal conditions go through
``error`` which writes ``Error: <message>`` to stderr and raises ``ExitError(1)``.

Deviations (upstream dependencies are bound to existing repo modules or ported as private
``_`` helpers, because the sibling ports do not exist at this base):
    - io.cts output/error: ``output``/``error`` are private-style helpers here (also exported);
      the pending-outcome, JSON-error-mode and exit-contract-v2 machinery of cli-exit.cts is not
      ported: ``error`` always raises ``ExitError(1)`` and ``output`` never records a DEGRADED
      outcome. Output of more than 50000 characters is redirected to ``<tmp>/gsd/gsd-<ms>.json``
      and ``@file:<path>`` is printed, as upstream.
    - config-loader.cts loadConfig: ``_load_config`` reads ``<cwd>/.planning/config.json`` (the
      upstream file) and falls back to this repository's ``<cwd>/.planning/config.yaml`` via
      ``text.yaml_load``; it fills an empty ``runtime`` from GSD_RUNTIME / the install marker
      (upstream fillRuntimeIdentity, project-config rung) and defaults ``runtime``,
      ``claude_md_path`` and ``claude_md_assembly`` to None. Federated/workstream/global-defaults
      (~/.gsd/defaults.json) resolution, key validation and the legacy-key write-back are not ported.
    - shell-command-projection.cts platformReadSync/platformWriteSync/platformEnsureDir:
      ``_platform_read``/``_platform_write``/``_ensure_dir`` implement UTF-8 read (None on ENOENT),
      atomic tmp+replace write with bounded retry on transient Windows lock errors, and the
      Markdown normalization (blank lines around headings and fences, list-to-prose separation,
      frontmatter passthrough, blank-run collapse, single trailing newline) including the scoped
      #5165 mode backed by markdown-line-diff.cts (``_match_lines``/``_write_scope``).
      ``preserveFencedMarkdownStructure`` (not used by this module) is not ported.
    - runtime-homes.cts getGlobalConfigDir/getGlobalSkillDir and their descriptor resolver are
      ported as private helpers over the ``capability_registry`` port.
    - runtime-slash.cts formatGsdSlash/resolveRuntime/readInstallRuntimeMarker are ported as private
      helpers. The install marker is read from ``engineer/.gsd-runtime`` (upstream
      ``gsd-core/.gsd-runtime``), which this repository does not create.
    - frontmatter-fence.cts locateFrontmatterFence is ported as ``_locate_frontmatter_fence``
      (this repository's ``frontmatter.py`` has no equivalent).
    - Templates: ``templates/user-profile.md`` and ``templates/dev-preferences.md`` are resolved
      under ``TEMPLATES_DIR`` (``engineer/templates``, upstream ``gsd-core/templates``). Neither
      template exists in this repository, so those two commands report ``Template not found``
      until the templates are added.
    - Placeholder substitution is literal. Upstream passes the replacement string to
      ``String.replace``, which interprets ``$&``, ``$1``, ``$$`` and similar sequences found in
      user-supplied evidence text; this port does not reproduce that JS artifact.
    - Project skill directories are scanned in sorted order (upstream uses unspecified readdir order).
    - Generated text still names GSD paths and commands (``/gsd-*``, ``GSD:`` section markers,
      ``gsd-core``, ``gsd-dev-preferences``) because the artifacts are upstream data.
"""
import datetime as dt
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

from .capability_registry import RUNTIMES as _REGISTRY_RUNTIMES
from .runtime_name_policy import (
    LEGACY_NON_REGISTRY_RUNTIME_HOMES,
    assert_known_runtime,
    canonicalize_runtime_name,
    get_project_instruction_file,
    resolve_runtime_name_from_candidates,
)
from .text import yaml_load

__all__ = [
    "PROFILING_QUESTIONS", "CLAUDE_INSTRUCTIONS", "ExitError", "TEMPLATES_DIR", "output", "error",
    "cmd_write_profile", "cmd_profile_questionnaire", "cmd_generate_dev_preferences",
    "cmd_generate_claude_profile", "cmd_generate_claude_md",
]

# Where templates/user-profile.md and templates/dev-preferences.md live (mutable for tests).
TEMPLATES_DIR = Path(__file__).resolve().parents[2]/"templates"

DIMENSION_KEYS = [
    "communication_style", "decision_speed", "explanation_depth",
    "debugging_approach", "ux_philosophy", "vendor_philosophy",
    "frustration_triggers", "learning_style",
]



# --- JavaScript-semantics helpers -----------------------------------------------------------------

_LINE_TERMINATORS = "\r\n  "


def _truthy(value):
    """JavaScript truthiness (empty arrays and objects are truthy; 0, '', null are not)."""
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0 and value == value
    if isinstance(value, str):
        return value != ""
    return True


def _or(*values):
    """JavaScript ``a || b || ...`` (the last operand is returned when none is truthy)."""
    for value in values[:-1]:
        if _truthy(value):
            return value
    return values[-1]


def _js_string(value):
    """JavaScript ``String(value)`` for JSON-derived values."""
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _iso_now():
    now = dt.datetime.now(dt.timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def _join(*parts):
    """Node ``path.join``: join with the separator and normalize."""
    joined = "/".join(part for part in parts if part)
    return os.path.normpath(joined) if joined else "."


def _is_absolute(value):
    return os.path.isabs(value) or (os.name == "nt" and value[:1] in ("/", "\\"))


def _homedir():
    return str(Path.home())


def _expand_tilde(value, home=None):
    home = _homedir() if home is None else home
    if not value:
        return value
    if value.startswith("~/") or value == "~":
        return _join(home, value[1:])
    return value


# --- io.cts: output / error ------------------------------------------------------------------------

GSD_TEMP_DIR = os.path.join(tempfile.gettempdir(), "gsd")


class ExitError(Exception):
    """Raised by ``error``: the command failed and the process should exit with ``exit_code``."""

    def __init__(self, exit_code=1, message=""):
        super().__init__(message)
        self.exit_code = exit_code


def _write_stream(stream, data):
    buffer = getattr(stream, "buffer", None)
    if buffer is not None:
        stream.flush()
        buffer.write(data.encode("utf-8"))
        buffer.flush()
    else:
        stream.write(data)
        stream.flush()


def _reap_stale_temp_files(prefix="gsd-", max_age_ms=5*60*1000, dirs_only=False):
    """Remove stale ``gsd-*`` temp files older than ``max_age_ms``; never raises."""
    try:
        os.makedirs(GSD_TEMP_DIR, exist_ok=True)
        now = time.time()*1000
        for entry in os.listdir(GSD_TEMP_DIR):
            if not entry.startswith(prefix):
                continue
            full = os.path.join(GSD_TEMP_DIR, entry)
            try:
                if now - os.stat(full).st_mtime*1000 > max_age_ms:
                    if os.path.isdir(full):
                        import shutil
                        shutil.rmtree(full, ignore_errors=True)
                    elif not dirs_only:
                        os.unlink(full)
            except OSError:
                pass
    except OSError:
        pass


def output(result, raw=False, raw_value=None):
    """Emit ``result`` as 2-space JSON (no trailing newline), or ``raw_value`` when raw.

    A payload over 50000 characters is written to a temp file and ``@file:<path>`` is printed.
    """
    if raw and raw_value is not None:
        data = str(raw_value)
    else:
        text = json.dumps(result, indent=2, ensure_ascii=False)
        if len(text) > 50000:
            _reap_stale_temp_files()
            os.makedirs(GSD_TEMP_DIR, exist_ok=True)
            temp_path = os.path.join(GSD_TEMP_DIR, f"gsd-{int(time.time()*1000)}.json")
            _platform_write(temp_path, text)
            data = "@file:" + temp_path
        else:
            data = text
    _write_stream(sys.stdout, data)


def error(message):
    """Write ``Error: <message>`` to stderr and raise ``ExitError(1)`` (upstream exits 1)."""
    _write_stream(sys.stderr, "Error: " + message + "\n")
    raise ExitError(1, message)


# --- frontmatter-fence.cts -------------------------------------------------------------------------

class _Fence:
    __slots__ = ("bom", "eol", "open_end", "closed", "closing_start", "closing_fence_end", "body_end")

    def __init__(self, bom, eol, open_end, closed, closing_start, closing_fence_end, body_end):
        self.bom, self.eol, self.open_end, self.closed = bom, eol, open_end, closed
        self.closing_start, self.closing_fence_end, self.body_end = closing_start, closing_fence_end, body_end


def _locate_frontmatter_fence(text, allow_preamble=False):
    """Where a document's frontmatter block starts and stops (a closed/unclosed fence), or None."""
    if not isinstance(text, str):
        raise TypeError(f"locateFrontmatterFence: expected a string, got {type(text).__name__}")
    bom = "﻿" if text[:1] == "﻿" else ""

    def opening_eol_at(at):
        if text.startswith("---\r\n", at):
            return "\r\n"
        if text.startswith("---\n", at):
            return "\n"
        return None

    start = len(bom)
    found = opening_eol_at(start)
    if found is None and allow_preamble:
        newline = text.find("\n", start)
        while newline != -1:
            found = opening_eol_at(newline + 1)
            if found is not None:
                start = newline + 1
                break
            newline = text.find("\n", newline + 1)
    if found is None:
        return None
    eol = found
    open_end = start + 3 + len(eol)

    def closed_at(line_start, line_end):
        body_end = open_end
        if line_start > open_end:
            body_end = line_start - 1
            if body_end > open_end and text[body_end - 1] == "\r":
                body_end -= 1
        return _Fence(bom, eol, open_end, True, line_start, line_end, body_end)

    lenient = None
    line_start = open_end
    while line_start <= len(text):
        newline = text.find("\n", line_start)
        if newline == -1:
            line_end = len(text)
        elif newline > line_start and text[newline - 1] == "\r":
            line_end = newline - 1
        else:
            line_end = newline
        line = text[line_start:line_end]
        if re.fullmatch(r"---[ \t]*", line):
            return closed_at(line_start, line_end)
        if lenient is None and re.fullmatch(r"-{4,}[ \t]*", line):
            lenient = (line_start, line_end)
        if newline == -1:
            break
        line_start = newline + 1
    if lenient is not None:
        return closed_at(*lenient)
    return _Fence(bom, eol, open_end, False, -1, -1, len(text))


# --- markdown-line-diff.cts ------------------------------------------------------------------------

_MAX_SCOPED_EDIT_DISTANCE = 400


def _match_lines(prev, nxt):
    """Align ``nxt`` against ``prev``: per ``nxt`` line the matching ``prev`` index, or -1.

    Myers' O(ND) diff after trimming the common prefix and suffix; None when the documents
    differ by more than the scoped edit distance.
    """
    match = [-1]*len(nxt)
    common = min(len(prev), len(nxt))
    lo = 0
    while lo < common and prev[lo] == nxt[lo]:
        match[lo] = lo
        lo += 1
    prev_end, next_end = len(prev), len(nxt)
    while prev_end > lo and next_end > lo and prev[prev_end - 1] == nxt[next_end - 1]:
        prev_end -= 1
        next_end -= 1
        match[next_end] = prev_end
    a, b = prev[lo:prev_end], nxt[lo:next_end]
    n, m = len(a), len(b)
    if n == 0 or m == 0:
        return match
    limit = min(n + m, _MAX_SCOPED_EDIT_DISTANCE)
    off = limit + 1
    v = [0]*(2*limit + 3)
    trace = []
    found = -1
    d = 0
    while d <= limit and found < 0:
        trace.append(v[:])
        for k in range(-d, d + 1, 2):
            if k == -d or (k != d and v[off + k - 1] < v[off + k + 1]):
                x = v[off + k + 1]
            else:
                x = v[off + k - 1] + 1
            y = x - k
            while x < n and y < m and a[x] == b[y]:
                x += 1
                y += 1
            v[off + k] = x
            if x >= n and y >= m:
                found = d
                break
        d += 1
    if found < 0:
        return None
    x, y = n, m
    for d in range(found, 0, -1):
        before = trace[d]
        k = x - y
        prev_k = k + 1 if (k == -d or (k != d and before[off + k - 1] < before[off + k + 1])) else k - 1
        prev_x = before[off + prev_k]
        prev_y = prev_x - prev_k
        while x > prev_x and y > prev_y:
            x -= 1
            y -= 1
            match[lo + y] = lo + x
        x, y = prev_x, prev_y
    while x > 0 and y > 0:
        x -= 1
        y -= 1
        match[lo + y] = lo + x
    return match


class _WriteScope:
    """What a write left alone, per line junction (i is between line i and line i + 1)."""

    def __init__(self, match, prev_length):
        self.match = match
        self.replaced = [0]*len(match)
        self.prior_index = [-1]*len(match)
        i = 0
        while i < len(match):
            if match[i] >= 0:
                i += 1
                continue
            end = i
            while end + 1 < len(match) and match[end + 1] < 0:
                end += 1
            before = match[i - 1] if i > 0 else -1
            after = match[end + 1] if end + 1 < len(match) else prev_length
            dropped = after - before - 1
            for j in range(i, end + 1):
                self.replaced[j] = dropped
                if j - i < dropped:
                    self.prior_index[j] = before + 1 + (j - i)
            i = end + 1

    def _at(self, values, i):
        return values[i] if 0 <= i < len(values) else None

    def junction_kept(self, i):
        left_value, right_value = self._at(self.match, i), self._at(self.match, i + 1)
        left = left_value is not None and left_value >= 0
        right = right_value is not None and right_value >= 0
        if left and right:
            return right_value - left_value == 1
        if left:
            return (self._at(self.replaced, i + 1) or 0) >= 1
        if right:
            return (self._at(self.replaced, i) or 0) >= 1
        return False

    def line_written(self, i):
        return self.match[i] < 0

    def replaced_prior_index(self, i):
        value = self._at(self.prior_index, i)
        return -1 if value is None else value


def _write_scope(match, prev_length):
    return _WriteScope(match, prev_length)


# --- shell-command-projection.cts: platform file I/O -----------------------------------------------

def _leading_frontmatter_line_count(text):
    fence = _locate_frontmatter_fence(text)
    if fence is None or not fence.closed:
        return 0
    return len(text[:fence.closing_start].split("\n"))


def _without_bom(line):
    return line[1:] if line[:1] == "﻿" else (line or "")


def _is_structural(text):
    stripped = text.rstrip()
    return re.match(r"#{1,6}\s", stripped) is not None or stripped.startswith("```")


_LIST_ITEM = re.compile(r"(\s*[-*+]\s|\s*\d+\.\s)")


def _normalize_md(content, prior=None):
    if not content or not isinstance(content, str):
        return content
    text = content.replace("\r\n", "\n")
    lines = text.split("\n")
    scope = None
    prior_lines = []
    if isinstance(prior, str) and prior != "":
        prior_lines = prior.replace("\r\n", "\n").split("\n")
        align_prior = [_without_bom(prior_lines[0]), *prior_lines[1:]]
        align_next = [_without_bom(lines[0]), *lines[1:]]
        match = _match_lines(align_prior, align_next)
        if match is not None:
            scope = _write_scope(match, len(prior_lines))
    frontmatter_lines = _leading_frontmatter_line_count(text)
    result = []

    def blank():
        if scope is None or not (result and result[-1] == ""):
            result.append("")

    inside_fence = [False]*len(lines)
    fence_open = False
    for i in range(len(lines)):
        if i < frontmatter_lines:
            inside_fence[i] = False
            continue
        if lines[i].rstrip().startswith("```"):
            inside_fence[i] = False
            fence_open = not fence_open
        else:
            inside_fence[i] = fence_open
    for i, line in enumerate(lines):
        if i < frontmatter_lines:
            result.append(line)
            continue
        prev = lines[i - 1] if i > 0 else ""
        prev_trimmed = prev.rstrip()
        trimmed = line.rstrip()
        is_fence_line = trimmed.startswith("```")
        heading = re.match(r"#{1,6}\s", trimmed) is not None
        replaced_prior = scope.replaced_prior_index(i) if scope is not None else -1
        authored_structure = (scope is not None and scope.line_written(i) and _is_structural(line)
                              and not (replaced_prior >= 0 and _is_structural(prior_lines[replaced_prior] if replaced_prior < len(prior_lines) else "")))
        kept_before = scope is not None and not authored_structure and i > 0 and scope.junction_kept(i - 1)
        kept_after = scope is not None and not authored_structure and i < len(lines) - 1 and scope.junction_kept(i)
        if scope is not None and line == "" and result and result[-1] == "" and not kept_before:
            continue
        if heading and i > 0 and prev_trimmed != "" and prev_trimmed != "---" and not kept_before:
            blank()
        if is_fence_line and i > 0 and prev_trimmed != "" and not inside_fence[i] and (not inside_fence[i - 1] or is_fence_line) and not kept_before:
            if not inside_fence[i - 1]:
                blank()
        result.append(line)
        following = lines[i + 1].rstrip() if i < len(lines) - 1 else ""
        if heading and i < len(lines) - 1 and following != "" and not kept_after:
            blank()
        if re.fullmatch(r"```\s*", trimmed) and i > 0 and inside_fence[i - 1] and i < len(lines) - 1 and following != "" and not kept_after:
            blank()
        if _LIST_ITEM.match(line) and i < len(lines) - 1 and not kept_after:
            following_line = lines[i + 1]
            if following_line.rstrip() != "" and not _LIST_ITEM.match(following_line) and not re.match(r"\s", following_line):
                blank()
    head = "\n".join(result[:frontmatter_lines])
    text = "\n".join(result)
    if scope is None:
        text = head + re.sub(r"\n{3,}", "\n\n", text[len(head):])
    return text.rstrip("\n") + "\n"


_MAX_PRIOR_BYTES = 2*1024*1024


def _read_prior_markdown(file_path):
    try:
        if not os.path.isfile(file_path) or os.path.getsize(file_path) > _MAX_PRIOR_BYTES:
            return None
        with open(file_path, "rb") as handle:
            data = handle.read(_MAX_PRIOR_BYTES + 1)
        return None if len(data) > _MAX_PRIOR_BYTES else data.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _normalize_content(file_path, content):
    if os.path.splitext(file_path)[1].lower() == ".md":
        return _normalize_md(content, _read_prior_markdown(file_path))
    return (content or "").replace("\r\n", "\n").rstrip("\n") + "\n"


def _atomic_replace(tmp_path, file_path):
    """os.replace with bounded retry on transient Windows lock errors; returns the final error or None."""
    last = None
    for attempt in range(1, 4):
        try:
            os.replace(tmp_path, file_path)
            return None
        except PermissionError as exc:
            last = exc
            if attempt < 3:
                time.sleep(0.05)
                continue
            break
        except OSError as exc:
            last = exc
            break
    return last


def _platform_write(file_path, content):
    """Normalize and atomically write ``content`` (UTF-8, LF)."""
    normalized = _normalize_content(file_path, content)
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    tmp_path = f"{file_path}.tmp.{os.getpid()}"
    data = normalized.encode("utf-8")
    try:
        with open(tmp_path, "wb") as handle:
            handle.write(data)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        with open(file_path, "wb") as handle:
            handle.write(data)
        return
    failure = _atomic_replace(tmp_path, file_path)
    if failure is None:
        return
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    if isinstance(failure, PermissionError):
        raise failure
    with open(file_path, "wb") as handle:
        handle.write(data)


def _platform_read(file_path):
    """UTF-8 text of ``file_path``, or None when it does not exist."""
    try:
        with open(file_path, "rb") as handle:
            return handle.read().decode("utf-8")
    except FileNotFoundError:
        return None


def _ensure_dir(directory):
    os.makedirs(directory, exist_ok=True)


# --- runtime-homes.cts (the parts profile-output calls) --------------------------------------------

def _non_blank(value):
    return isinstance(value, str) and value.strip() != ""


def _descriptor_env(descriptor, index, env):
    names = descriptor.get("env") or []
    name = names[index] if index < len(names) else None
    value = env.get(name) if name else None
    return value if _non_blank(value) else None


def _resolve_config_home_from_descriptor(config_home, env=None, home=None, exists=None):
    env = os.environ if env is None else env
    home = _homedir() if home is None else home
    exists = os.path.exists if exists is None else exists
    kind = config_home["kind"]
    if kind == "dot-home":
        for name in config_home.get("env") or []:
            value = env.get(name)
            if _non_blank(value):
                return _expand_tilde(value, home)
        return _join(home, config_home["name"])
    if kind == "dot-home-nested":
        override = _descriptor_env(config_home, 0, env)
        if override is not None:
            return _expand_tilde(override, home)
        base = _join(home, config_home["parent"])
        probe = config_home.get("probe")
        if probe:
            if config_home.get("probeExists"):
                for candidate in probe:
                    resolved = _join(base, candidate)
                    if exists(_join(resolved, config_home["probeExists"])):
                        return resolved
            for candidate in probe:
                resolved = _join(base, candidate)
                if exists(resolved):
                    return resolved
            return _join(base, probe[0])
        return _join(base, config_home["name"])
    if kind == "xdg":
        override = _descriptor_env(config_home, 0, env)
        if override is not None:
            return _expand_tilde(override, home)
        file_path = _descriptor_env(config_home, 1, env)
        if file_path is not None:
            return os.path.dirname(_expand_tilde(file_path, home))
        xdg = _descriptor_env(config_home, 2, env)
        if xdg is not None:
            return _join(_expand_tilde(xdg, home), config_home["name"])
        return _join(home, ".config", config_home["name"])
    if kind == "generic-agents-root":
        override = _descriptor_env(config_home, 0, env)
        if override is not None:
            return _expand_tilde(override, home)
        for candidate in config_home["probe"]:
            resolved = _expand_tilde(candidate, home)
            if exists(_join(resolved, config_home["probeExists"])):
                return resolved
        return _expand_tilde(config_home["probe"][0], home)
    if kind == "none":
        raise RuntimeError(f'Runtime "{config_home["name"]}" has no config-home directory (configHome.kind === "none")')
    raise RuntimeError(f"Unknown configHome kind: {kind!r}")


def _runtime_descriptor(runtime):
    entry = _REGISTRY_RUNTIMES.get(runtime) if isinstance(runtime, str) else None
    return (entry or {}).get("runtime") if isinstance(entry, dict) else None


def _get_global_config_dir(runtime, explicit_dir=None):
    assert_known_runtime(runtime)
    if explicit_dir:
        return _expand_tilde(explicit_dir)
    if runtime in LEGACY_NON_REGISTRY_RUNTIME_HOMES:
        legacy = LEGACY_NON_REGISTRY_RUNTIME_HOMES[runtime]
        override = os.environ.get(legacy["env"])
        return _expand_tilde(override) if override else _join(_homedir(), *legacy["dir"])
    descriptor = _runtime_descriptor(runtime)
    if descriptor and descriptor.get("configHome"):
        return _resolve_config_home_from_descriptor(descriptor["configHome"])
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    return _expand_tilde(override) if override else _join(_homedir(), ".claude")


def _get_global_skills_base(runtime):
    assert_known_runtime(runtime)
    descriptor = _runtime_descriptor(runtime)
    if descriptor and (descriptor.get("configHome") or {}).get("kind") == "none":
        return None
    layout = (descriptor or {}).get("artifactLayout") or {}
    skills_kind = next((entry for entry in layout.get("global") or [] if entry.get("kind") == "skills"), None)
    if skills_kind and skills_kind.get("home") and skills_kind.get("destSubpath"):
        return _join(_homedir(), skills_kind["home"], skills_kind["destSubpath"])
    if descriptor and descriptor.get("configHome") and skills_kind and skills_kind.get("destSubpath"):
        config_home = descriptor["configHome"]
        base = _resolve_config_home_from_descriptor(config_home.get("skillsHome") or config_home)
        return _join(base, skills_kind["destSubpath"])
    return _join(_get_global_config_dir(runtime), "skills")


def _get_global_skill_dir(runtime, skill_name):
    base = _get_global_skills_base(runtime)
    return None if base is None else _join(base, skill_name)


# --- runtime-slash.cts (the parts profile-output calls) --------------------------------------------

_INSTALL_MARKER_UNSET = object()
_install_marker_cache = _INSTALL_MARKER_UNSET


def _read_install_runtime_marker():
    """The per-install ``.gsd-runtime`` marker (cached; never raises; None when absent)."""
    global _install_marker_cache
    if _install_marker_cache is not _INSTALL_MARKER_UNSET:
        return _install_marker_cache
    try:
        raw = (Path(__file__).resolve().parents[2]/".gsd-runtime").read_text(encoding="utf-8").strip()
        _install_marker_cache = raw or None
    except (OSError, UnicodeDecodeError):
        _install_marker_cache = None
    return _install_marker_cache


def _read_project_config(project_dir):
    """``<project>/.planning/config.json`` (or this repository's config.yaml) as a dict, else None."""
    if not project_dir:
        return None
    try:
        for name in ("config.json", "config.yaml"):
            config_path = Path(project_dir)/".planning"/name
            if not config_path.exists():
                continue
            raw = config_path.read_text(encoding="utf-8")
            parsed = json.loads(raw) if name.endswith(".json") else yaml_load(raw)
            return parsed if isinstance(parsed, dict) else None
        return None
    except Exception:
        return None


def _resolve_active_runtime(config, env=None):
    env = os.environ if env is None else env
    return resolve_runtime_name_from_candidates(
        env.get("GSD_RUNTIME"),
        config.get("runtime") if config else None,
        _read_install_runtime_marker(),
    ) or "claude"


def _resolve_runtime(project_dir):
    """env.GSD_RUNTIME > config.runtime > install marker > 'claude'."""
    return _resolve_active_runtime(_read_project_config(project_dir))


def _format_gsd_slash(command_name, runtime):
    if not isinstance(command_name, str):
        return command_name
    if command_name == "":
        return command_name
    stripped = re.sub(r"^[/$]?gsd[-:]", "", command_name, count=1, flags=re.I)
    bare = command_name if stripped == command_name else stripped
    if bare == "" or bare.strip() == "":
        return ""
    ws_match = re.match(r"(\S+)(\s[\s\S]*)?\Z", bare)
    token = ws_match.group(1) if ws_match else bare
    tail = ws_match.group(2) if ws_match and ws_match.group(2) else ""
    runtime_text = (runtime if isinstance(runtime, str) and runtime else "claude").lower()
    resolved = canonicalize_runtime_name(runtime_text) or runtime_text
    style = ((_REGISTRY_RUNTIMES.get(resolved) or {}).get("runtime") or {}).get("commandStyle")
    if style == "shell-var":
        return f"$gsd-{token.lower()}{tail}"
    return f"/gsd-{token}{tail}"


# --- config-loader.cts loadConfig (project-config subset) ------------------------------------------

def _load_config(cwd):
    """Project config as a dict with ``runtime``/``claude_md_path``/``claude_md_assembly`` defaulted."""
    parsed = _read_project_config(cwd) or {}
    config = {
        **parsed,
        "runtime": parsed.get("runtime") or None,
        "claude_md_path": parsed.get("claude_md_path") or None,
        "claude_md_assembly": parsed.get("claude_md_assembly") or None,
    }
    install_runtime = resolve_runtime_name_from_candidates(os.environ.get("GSD_RUNTIME"), _read_install_runtime_marker())
    canonical = canonicalize_runtime_name(install_runtime) if install_runtime else None
    if canonical and not config["runtime"]:
        config["runtime"] = canonical
    return config


PROFILING_QUESTIONS = [
  {
    "dimension": 'communication_style',
    "header": 'Communication Style',
    "context": 'Think about the last few times you asked Claude to build or change something. How did you frame the request?',
    "question": 'When you ask Claude to build something, how much context do you typically provide?',
    "options": [
      { "label": 'Minimal -- "fix the bug", "add dark mode", just say what\'s needed', "value": 'a', "rating": 'terse-direct' },
      { "label": 'Some context -- explain what and why in a paragraph or two', "value": 'b', "rating": 'conversational' },
      { "label": 'Detailed specs -- headers, numbered lists, problem analysis, constraints', "value": 'c', "rating": 'detailed-structured' },
      { "label": 'It depends on the task -- simple tasks get short prompts, complex ones get detailed specs', "value": 'd', "rating": 'mixed' },
    ],
  },
  {
    "dimension": 'decision_speed',
    "header": 'Decision Making',
    "context": 'Think about times when Claude presented you with multiple options -- like choosing a library, picking an architecture, or selecting an approach.',
    "question": 'When Claude presents you with options, how do you typically decide?',
    "options": [
      { "label": 'Pick quickly based on gut feeling or past experience', "value": 'a', "rating": 'fast-intuitive' },
      { "label": 'Ask for a comparison table or pros/cons, then decide', "value": 'b', "rating": 'deliberate-informed' },
      { "label": 'Research independently (read docs, check GitHub stars) before deciding', "value": 'c', "rating": 'research-first' },
      { "label": 'Let Claude recommend -- I generally trust the suggestion', "value": 'd', "rating": 'delegator' },
    ],
  },
  {
    "dimension": 'explanation_depth',
    "header": 'Explanation Preferences',
    "context": 'Think about when Claude explains code it wrote or an approach it took. How much detail feels right?',
    "question": 'When Claude explains something, how much detail do you want?',
    "options": [
      { "label": 'Just the code -- I\'ll read it and figure it out myself', "value": 'a', "rating": 'code-only' },
      { "label": 'Brief explanation with the code -- a sentence or two about the approach', "value": 'b', "rating": 'concise' },
      { "label": 'Detailed walkthrough -- explain the approach, trade-offs, and code structure', "value": 'c', "rating": 'detailed' },
      { "label": 'Deep dive -- teach me the concepts behind it so I understand the fundamentals', "value": 'd', "rating": 'educational' },
    ],
  },
  {
    "dimension": 'debugging_approach',
    "header": 'Debugging Style',
    "context": 'Think about the last few times something broke in your code. How did you approach it with Claude?',
    "question": 'When something breaks, how do you typically approach debugging with Claude?',
    "options": [
      { "label": 'Paste the error and say "fix it" -- get it working fast', "value": 'a', "rating": 'fix-first' },
      { "label": 'Share the error plus context, ask Claude to diagnose what went wrong', "value": 'b', "rating": 'diagnostic' },
      { "label": 'Investigate myself first, then ask Claude about my specific theories', "value": 'c', "rating": 'hypothesis-driven' },
      { "label": 'Walk through the code together step by step to understand the issue', "value": 'd', "rating": 'collaborative' },
    ],
  },
  {
    "dimension": 'ux_philosophy',
    "header": 'UX Philosophy',
    "context": 'Think about user-facing features you have built recently. How did you balance functionality with design?',
    "question": 'When building user-facing features, what do you prioritize?',
    "options": [
      { "label": 'Get it working first, polish the UI later (or never)', "value": 'a', "rating": 'function-first' },
      { "label": 'Basic usability from the start -- nothing ugly, but no pixel-perfection', "value": 'b', "rating": 'pragmatic' },
      { "label": 'Design and UX are as important as functionality -- I care about the experience', "value": 'c', "rating": 'design-conscious' },
      { "label": 'I mostly build backend, CLI, or infrastructure -- UX is minimal', "value": 'd', "rating": 'backend-focused' },
    ],
  },
  {
    "dimension": 'vendor_philosophy',
    "header": 'Library & Vendor Choices',
    "context": 'Think about the last time you needed a library or service for a project. How did you go about choosing it?',
    "question": 'When choosing libraries or services, what is your typical approach?',
    "options": [
      { "label": 'Use whatever Claude suggests -- speed matters more than the perfect choice', "value": 'a', "rating": 'pragmatic-fast' },
      { "label": 'Prefer well-known, battle-tested options (React, PostgreSQL, Express)', "value": 'b', "rating": 'conservative' },
      { "label": 'Research alternatives, read docs, compare benchmarks before committing', "value": 'c', "rating": 'thorough-evaluator' },
      { "label": 'Strong opinions -- I already know what I like and I stick with it', "value": 'd', "rating": 'opinionated' },
    ],
  },
  {
    "dimension": 'frustration_triggers',
    "header": 'Frustration Triggers',
    "context": 'Think about moments when working with AI coding assistants that made you frustrated or annoyed.',
    "question": 'What frustrates you most when working with AI coding assistants?',
    "options": [
      { "label": 'Doing things I didn\'t ask for -- adding features, refactoring code, scope creep', "value": 'a', "rating": 'scope-creep' },
      { "label": 'Not following instructions precisely -- ignoring constraints or requirements I stated', "value": 'b', "rating": 'instruction-adherence' },
      { "label": 'Over-explaining or being too verbose -- just give me the code and move on', "value": 'c', "rating": 'verbosity' },
      { "label": 'Breaking working code while fixing something else -- regressions', "value": 'd', "rating": 'regression' },
    ],
  },
  {
    "dimension": 'learning_style',
    "header": 'Learning Preferences',
    "context": 'Think about encountering something new -- an unfamiliar library, a codebase you inherited, a concept you hadn\'t used before.',
    "question": 'When you encounter something new in your codebase, how do you prefer to learn about it?',
    "options": [
      { "label": 'Read the code directly -- I figure things out by reading and experimenting', "value": 'a', "rating": 'self-directed' },
      { "label": 'Ask Claude to explain the relevant parts to me', "value": 'b', "rating": 'guided' },
      { "label": 'Read official docs and tutorials first, then try things', "value": 'c', "rating": 'documentation-first' },
      { "label": 'See a working example, then modify it to understand how it works', "value": 'd', "rating": 'example-driven' },
    ],
  },
]

CLAUDE_INSTRUCTIONS = {
  "communication_style": {
    "terse-direct": 'Keep responses concise and action-oriented. Skip lengthy preambles. Match this developer\'s direct style.',
    "conversational": 'Use a natural conversational tone. Explain reasoning briefly alongside code. Engage with the developer\'s questions.',
    "detailed-structured": 'Match this developer\'s structured communication: use headers for sections, numbered lists for steps, and acknowledge provided context before responding.',
    "mixed": 'Adapt response detail to match the complexity of each request. Brief for simple tasks, detailed for complex ones.',
  },
  "decision_speed": {
    "fast-intuitive": 'Present a single strong recommendation with brief justification. Skip lengthy comparisons unless asked.',
    "deliberate-informed": 'Present options in a structured comparison table with pros/cons. Let the developer make the final call.',
    "research-first": 'Include links to docs, GitHub repos, or benchmarks when recommending tools. Support the developer\'s research process.',
    "delegator": 'Make clear recommendations with confidence. Explain your reasoning briefly, but own the suggestion.',
  },
  "explanation_depth": {
    "code-only": 'Prioritize code output. Add comments inline rather than prose explanations. Skip walkthroughs unless asked.',
    "concise": 'Pair code with a brief explanation (1-2 sentences) of the approach. Keep prose minimal.',
    "detailed": 'Explain the approach, key trade-offs, and code structure alongside the implementation. Use headers to organize.',
    "educational": 'Teach the underlying concepts and principles, not just the implementation. Relate new patterns to fundamentals.',
  },
  "debugging_approach": {
    "fix-first": 'Prioritize the fix. Show the corrected code first, then optionally explain what was wrong. Minimize diagnostic preamble.',
    "diagnostic": 'Diagnose the root cause before presenting the fix. Explain what went wrong and why the fix addresses it.',
    "hypothesis-driven": 'Engage with the developer\'s theories. Validate or refine their hypotheses before jumping to solutions.',
    "collaborative": 'Walk through the debugging process step by step. Explain the investigation approach, not just the conclusion.',
  },
  "ux_philosophy": {
    "function-first": 'Focus on functionality and correctness. Keep UI minimal and functional. Skip design polish unless requested.',
    "pragmatic": 'Build clean, usable interfaces without over-engineering. Apply basic design principles (spacing, alignment, contrast).',
    "design-conscious": 'Invest in UX quality: thoughtful spacing, smooth transitions, responsive layouts. Treat design as a first-class concern.',
    "backend-focused": 'Optimize for developer experience (clear APIs, good error messages, helpful CLI output) over visual design.',
  },
  "vendor_philosophy": {
    "pragmatic-fast": 'Suggest libraries quickly based on popularity and reliability. Don\'t over-analyze choices for non-critical dependencies.',
    "conservative": 'Recommend well-established, widely-adopted tools with strong community support. Avoid bleeding-edge options.',
    "thorough-evaluator": 'Compare alternatives with specific metrics (bundle size, GitHub stars, maintenance activity). Support informed decisions.',
    "opinionated": 'Respect the developer\'s existing tool preferences. Ask before suggesting alternatives to their preferred stack.',
  },
  "frustration_triggers": {
    "scope-creep": 'Do exactly what is asked -- nothing more. Never add unrequested features, refactoring, or "improvements". Ask before expanding scope.',
    "instruction-adherence": 'Follow instructions precisely. Re-read constraints before responding. If requirements conflict, flag the conflict rather than silently choosing.',
    "verbosity": 'Be concise. Lead with code, follow with brief explanation only if needed. Avoid restating the problem or unnecessary context.',
    "regression": 'Before modifying working code, verify the change is safe. Run existing tests mentally. Flag potential regression risks explicitly.',
  },
  "learning_style": {
    "self-directed": 'Point to relevant code sections and let the developer explore. Add signposts (file paths, function names) rather than full explanations.',
    "guided": 'Explain concepts in context of the developer\'s codebase. Use their actual code as examples when teaching.',
    "documentation-first": 'Link to official documentation and relevant sections. Structure explanations like reference material.',
    "example-driven": 'Lead with working code examples. Show a minimal example first, then explain how to extend or modify it.',
  },
}



# CLAUDE.md fallback / placeholder text, runtime-aware so emitted slash commands route correctly.
def _build_claude_md_fallbacks(runtime):
    return {
        "project": f"Project not yet initialized. Run {_format_gsd_slash('new-project', runtime)} to set up.",
        "stack": "Technology stack not yet documented. Will populate after codebase mapping or first phase.",
        "conventions": "Conventions not yet established. Will populate as patterns emerge during development.",
        "architecture": "Architecture not yet mapped. Follow existing patterns found in the codebase.",
        "skills": "No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.",
    }


# Directories where project skills may live (checked in order)
SKILL_SEARCH_DIRS = [".claude/skills", ".agents/skills", ".cursor/skills", ".github/skills", ".codex/skills"]


def _build_claude_md_workflow_enforcement(runtime):
    return "\n".join([
        "Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.",
        "",
        "Use these entry points:",
        f"- `{_format_gsd_slash('fast', runtime)}` for a trivial task inline, with no subagents and no PLAN.md",
        f"- `{_format_gsd_slash('quick', runtime)}` for small fixes, doc updates, and ad-hoc tasks",
        f"- `{_format_gsd_slash('debug', runtime)}` for investigation and bug fixing",
        f"- `{_format_gsd_slash('execute-phase', runtime)}` for planned phase work",
        "",
        "Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.",
    ])


def _build_claude_md_profile_placeholder(runtime):
    return "\n".join([
        "<!-- GSD:profile-start -->",
        "## Developer Profile",
        "",
        f"> Profile not yet configured. Run `{_format_gsd_slash('profile-user', runtime)}` to generate your developer profile.",
        "> This section is managed by `generate-claude-profile` -- do not edit manually.",
        "<!-- GSD:profile-end -->",
    ])


# --- Helper functions --------------------------------------------------------------------------------

def _is_ambiguous_answer(dimension, value):
    if dimension == "communication_style" and value == "d":
        return True
    question = next((q for q in PROFILING_QUESTIONS if q["dimension"] == dimension), None)
    if question is None:
        return False
    option = next((o for o in question["options"] if o["value"] == value), None)
    if option is None:
        return False
    return option["rating"] == "mixed"


def _generate_claude_instruction(dimension, rating):
    dim_instructions = CLAUDE_INSTRUCTIONS.get(dimension)
    if dim_instructions and dim_instructions.get(rating):
        return dim_instructions[rating]
    return f"Adapt to this developer's {dimension.replace('_', ' ')} preference: {rating}."


def _extract_section_content(file_content, section_name):
    start_marker = f"<!-- GSD:{section_name}-start"
    end_marker = f"<!-- GSD:{section_name}-end -->"
    start = file_content.find(start_marker)
    end = file_content.find(end_marker)
    if start == -1 or end == -1:
        return None
    start_tag_end = file_content.find("-->", start)
    if start_tag_end == -1:
        return None
    return file_content[start_tag_end + 3:end]


def _build_section(section_name, source_file, content):
    return "\n".join([f"<!-- GSD:{section_name}-start source:{source_file} -->", content, f"<!-- GSD:{section_name}-end -->"])


def _update_section(file_content, section_name, new_content):
    start_marker = f"<!-- GSD:{section_name}-start"
    end_marker = f"<!-- GSD:{section_name}-end -->"
    start = file_content.find(start_marker)
    end = file_content.find(end_marker)
    if start != -1 and end != -1:
        return {"content": file_content[:start] + new_content + file_content[end + len(end_marker):], "action": "replaced"}
    return {"content": file_content.rstrip() + "\n\n" + new_content + "\n", "action": "appended"}


def _detect_manual_edit(file_content, section_name, expected_content):
    current = _extract_section_content(file_content, section_name)
    if current is None:
        return False

    def normalize(value):
        return re.sub(r"\n{3,}", "\n\n", value.strip())

    return normalize(current) != normalize(expected_content)


def _extract_markdown_section(content, section_name):
    if not content:
        return None
    capturing = False
    result = []
    heading_pattern = re.compile(rf"## {section_name}\s*\Z")
    for line in content.split("\n"):
        if heading_pattern.match(line):
            capturing = True
            result.append(line)
            continue
        if capturing and line.startswith("## "):
            break
        if capturing:
            result.append(line)
    return "\n".join(result).strip() if result else None


_H1 = re.compile(r"(?:^|(?<=[\r\n\u2028\u2029]))# ([^\r\n\u2028\u2029]+)(?=[\r\n\u2028\u2029]|\Z)")


# --- CLAUDE.md section generators --------------------------------------------------------------------

def _generate_project_section(cwd):
    fallbacks = _build_claude_md_fallbacks(_resolve_runtime(cwd))
    content = _platform_read(_join(cwd, ".planning", "PROJECT.md"))
    if not content:
        return {"content": fallbacks["project"], "source": "PROJECT.md", "linkPath": None, "hasFallback": True}
    parts = []
    h1 = _H1.search(content)
    if h1:
        parts.append(f"**{h1.group(1)}**")
    what_this_is = _extract_markdown_section(content, "What This Is")
    if what_this_is:
        body = re.sub(r"^## What This Is\s*", "", what_this_is, count=1, flags=re.I).strip()
        if body:
            parts.append(body)
    core_value = _extract_markdown_section(content, "Core Value")
    if core_value:
        body = re.sub(r"^## Core Value\s*", "", core_value, count=1, flags=re.I).strip()
        if body:
            parts.append(f"**Core Value:** {body}")
    constraints = _extract_markdown_section(content, "Constraints")
    if constraints:
        body = re.sub(r"^## Constraints\s*", "", constraints, count=1, flags=re.I).strip()
        if body:
            parts.append(f"### Constraints\n\n{body}")
    if not parts:
        return {"content": fallbacks["project"], "source": "PROJECT.md", "linkPath": None, "hasFallback": True}
    return {"content": "\n\n".join(parts), "source": "PROJECT.md", "linkPath": ".planning/PROJECT.md", "hasFallback": False}


def _generate_stack_section(cwd):
    fallbacks = _build_claude_md_fallbacks(_resolve_runtime(cwd))
    content = _platform_read(_join(cwd, ".planning", "codebase", "STACK.md"))
    source = "codebase/STACK.md"
    link_path = ".planning/codebase/STACK.md"
    if not content:
        content = _platform_read(_join(cwd, ".planning", "research", "STACK.md"))
        source = "research/STACK.md"
        link_path = ".planning/research/STACK.md"
    if not content:
        return {"content": fallbacks["stack"], "source": "STACK.md", "linkPath": None, "hasFallback": True}
    summary_lines = []
    in_table = False
    for line in content.split("\n"):
        if line.startswith("#"):
            if not line.startswith("# ") or summary_lines:
                summary_lines.append(line)
            continue
        if line.startswith("|"):
            in_table = True
            summary_lines.append(line)
            continue
        if in_table and line.strip() == "":
            in_table = False
        if line.startswith("- ") or line.startswith("* "):
            summary_lines.append(line)
    summary = "\n".join(summary_lines) if summary_lines else content.strip()
    return {"content": summary, "source": source, "linkPath": link_path, "hasFallback": False}


def _generate_conventions_section(cwd):
    fallbacks = _build_claude_md_fallbacks(_resolve_runtime(cwd))
    content = _platform_read(_join(cwd, ".planning", "codebase", "CONVENTIONS.md"))
    if not content:
        return {"content": fallbacks["conventions"], "source": "CONVENTIONS.md", "linkPath": None, "hasFallback": True}
    summary_lines = []
    for line in content.split("\n"):
        if line.startswith("#"):
            if not line.startswith("# "):
                summary_lines.append(line)
            continue
        if line.startswith("- ") or line.startswith("* ") or line.startswith("|"):
            summary_lines.append(line)
    summary = "\n".join(summary_lines) if summary_lines else content.strip()
    return {"content": summary, "source": "CONVENTIONS.md", "linkPath": ".planning/codebase/CONVENTIONS.md", "hasFallback": False}


def _generate_architecture_section(cwd):
    fallbacks = _build_claude_md_fallbacks(_resolve_runtime(cwd))
    content = _platform_read(_join(cwd, ".planning", "codebase", "ARCHITECTURE.md"))
    if not content:
        return {"content": fallbacks["architecture"], "source": "ARCHITECTURE.md", "linkPath": None, "hasFallback": True}
    summary_lines = []
    for line in content.split("\n"):
        if line.startswith("#"):
            if not line.startswith("# "):
                summary_lines.append(line)
            continue
        if line.startswith("- ") or line.startswith("* ") or line.startswith("|") or line.startswith("```"):
            summary_lines.append(line)
    summary = "\n".join(summary_lines) if summary_lines else content.strip()
    return {"content": summary, "source": "ARCHITECTURE.md", "linkPath": ".planning/codebase/ARCHITECTURE.md", "hasFallback": False}


def _generate_workflow_section(cwd):
    return {"content": _build_claude_md_workflow_enforcement(_resolve_runtime(cwd)), "source": "GSD defaults",
            "linkPath": None, "hasFallback": False}


def _extract_skill_frontmatter(content):
    """name and description from a SKILL.md frontmatter block (multi-line descriptions supported)."""
    result = {"name": "", "description": ""}
    fence = _locate_frontmatter_fence(content)
    if fence is None or not fence.closed:
        return result
    current_key = ""
    for line in content[fence.open_end:fence.body_end].split("\n"):
        key_value = re.match(r"([A-Za-z0-9_][A-Za-z0-9_-]*):\s*(.*)", line)
        if key_value:
            current_key = key_value.group(1)
            value = key_value.group(2).strip()
            if current_key == "name":
                result["name"] = value
            if current_key == "description":
                result["description"] = value
            continue
        if current_key == "description" and re.match(r"\s+", line):
            result["description"] += " " + line.strip()
        else:
            current_key = ""
    return result


def _generate_skills_section(cwd):
    """Discover project skills from the standard directories and summarize them as a table."""
    fallbacks = _build_claude_md_fallbacks(_resolve_runtime(cwd))
    discovered = []
    for directory in SKILL_SEARCH_DIRS:
        abs_dir = _join(cwd, directory)
        if not os.path.exists(abs_dir):
            continue
        try:
            entries = sorted(os.scandir(abs_dir), key=lambda entry: entry.name)
        except OSError:
            continue
        for entry in entries:
            if not entry.is_dir(follow_symlinks=False):
                continue
            if entry.name.startswith("gsd-"):
                continue
            skill_md = _join(abs_dir, entry.name, "SKILL.md")
            if not os.path.exists(skill_md):
                continue
            content = _platform_read(skill_md)
            if not content:
                continue
            frontmatter = _extract_skill_frontmatter(content)
            name = frontmatter["name"] or entry.name
            description = frontmatter["description"] or ""
            if any(skill["name"] == name for skill in discovered):
                continue
            discovered.append({"name": name, "description": description, "path": f"{directory}/{entry.name}"})
    if not discovered:
        return {"content": fallbacks["skills"], "source": "skills/", "hasFallback": True}
    lines = ["| Skill | Description | Path |", "|-------|-------------|------|"]
    for skill in discovered:
        description = skill["description"].replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()
        safe_name = skill["name"].replace("\\", "\\\\").replace("|", "\\|")
        lines.append(f"| {safe_name} | {description} | `{skill['path']}/SKILL.md` |")
    return {"content": "\n".join(lines), "source": "skills/", "hasFallback": False}


# --- Commands ----------------------------------------------------------------------------------------

_SENSITIVE_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"Bearer\s+[a-zA-Z0-9._-]+", re.I),
    re.compile(r"password\s*[:=]\s*\S+", re.I),
    re.compile(r"secret\s*[:=]\s*\S+", re.I),
    re.compile(r"token\s*[:=]\s*\S+", re.I),
    re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.I),
    re.compile(r"/Users/[a-zA-Z0-9._-]+/"),
    re.compile(r"/home/[a-zA-Z0-9._-]+/"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"gho_[a-zA-Z0-9]{36}"),
    re.compile(r"xoxb-[a-zA-Z0-9-]+"),
]


def _is_object(value):
    return isinstance(value, (dict, list))


def _load_analysis(cwd, analysis_option):
    """Resolve, read and parse an analysis JSON path the way every analysis-consuming command does."""
    analysis_path = analysis_option if _is_absolute(analysis_option) else _join(cwd, analysis_option)
    if not os.path.exists(analysis_path):
        error(f"Analysis file not found: {analysis_path}")
    analysis_raw = _platform_read(analysis_path)
    try:
        if analysis_raw is None:
            raise ValueError(f"analysis file not found: {analysis_path}")
        analysis = json.loads(analysis_raw)
    except ValueError as exc:
        error(f"Failed to parse analysis JSON: {exc}")
    if not isinstance(analysis, dict) or not _truthy(analysis.get("dimensions")) or not _is_object(analysis.get("dimensions")):
        error('Analysis JSON must contain a "dimensions" object')
    return analysis


def _dimension(analysis, key):
    dimensions = analysis.get("dimensions")
    return dimensions.get(key) if isinstance(dimensions, dict) else None


def _effective_runtime_with_default(cwd):
    """GSD_RUNTIME > config.runtime > 'claude' (config load failures fall back to env/'claude')."""
    try:
        config = _load_config(cwd)
        return resolve_runtime_name_from_candidates(os.environ.get("GSD_RUNTIME"), config.get("runtime"), "claude") or "claude"
    except Exception:
        return resolve_runtime_name_from_candidates(os.environ.get("GSD_RUNTIME"), "claude") or "claude"


def _read_template(file_name):
    template_path = os.path.join(str(TEMPLATES_DIR), file_name)
    if not os.path.exists(template_path):
        error(f"Template not found: {template_path}")
    with open(template_path, "rb") as handle:
        return handle.read().decode("utf-8")


def cmd_write_profile(cwd, options, raw):
    """Write USER-PROFILE.md from an analysis JSON, redacting sensitive evidence text."""
    if not options.get("input"):
        error("--input <analysis-json-path> is required")
    analysis = _load_analysis(cwd, options["input"])
    if not analysis.get("profile_version"):
        error('Analysis JSON must contain "profile_version"')

    redacted_count = 0

    def redact_sensitive(text):
        nonlocal redacted_count
        if not isinstance(text, str):
            return text
        result = text
        for pattern in _SENSITIVE_PATTERNS:
            result, count = pattern.subn("[REDACTED]", result)
            redacted_count += count
        return result

    dimensions = analysis["dimensions"]
    for dim_key in (list(dimensions) if isinstance(dimensions, dict) else []):
        dim = dimensions[dim_key]
        evidence = dim.get("evidence") if isinstance(dim, dict) else None
        if isinstance(evidence, list):
            for item in evidence:
                if not isinstance(item, dict):
                    continue
                if _truthy(item.get("quote")):
                    item["quote"] = redact_sensitive(item["quote"])
                if _truthy(item.get("example")):
                    item["example"] = redact_sensitive(item["example"])
                if _truthy(item.get("signal")):
                    item["signal"] = redact_sensitive(item["signal"])

    if redacted_count > 0:
        _write_stream(sys.stderr, f"Sensitive content redacted: {redacted_count} pattern(s) removed from evidence quotes\n")

    template = _read_template("user-profile.md")

    dimension_labels = {
        "communication_style": "Communication", "decision_speed": "Decisions", "explanation_depth": "Explanations",
        "debugging_approach": "Debugging", "ux_philosophy": "UX Philosophy", "vendor_philosophy": "Vendor Philosophy",
        "frustration_triggers": "Frustration Triggers", "learning_style": "Learning Style",
    }

    summary_lines = []
    high = medium = low = scored = 0
    for dim_key in DIMENSION_KEYS:
        dim = _dimension(analysis, dim_key)
        if not _truthy(dim):
            continue
        confidence = _js_string(_or(dim.get("confidence"), "")).upper()
        if confidence in ("HIGH", "MEDIUM", "LOW"):
            scored += 1
        label = dimension_labels.get(dim_key) or dim_key
        if confidence == "HIGH":
            high += 1
            if _truthy(dim.get("claude_instruction")):
                summary_lines.append(f"- **{label}:** {dim['claude_instruction']} (HIGH)")
        elif confidence == "MEDIUM":
            medium += 1
            if _truthy(dim.get("claude_instruction")):
                summary_lines.append(f"- **{label}:** {dim['claude_instruction']} (MEDIUM)")
        elif confidence == "LOW":
            low += 1

    summary_instructions = "\n".join(summary_lines) if summary_lines else "- No high or medium confidence dimensions scored yet."
    projects = _or(analysis.get("projects_list"), analysis.get("projects_analyzed"), [])
    projects = projects if isinstance(projects, list) else []
    data_source = _js_string(_or(analysis.get("data_source"), "session_analysis"))

    def fill(placeholder, value):
        nonlocal template
        template = template.replace("{{" + placeholder + "}}", value)

    fill("generated_at", _iso_now())
    fill("data_source", data_source)
    fill("projects_list", ", ".join(_js_string(item) for item in projects))
    fill("message_count", _js_string(_or(analysis.get("message_count"), analysis.get("messages_analyzed"), 0)))
    fill("summary_instructions", summary_instructions)
    fill("profile_version", _js_string(analysis["profile_version"]))
    fill("projects_count", str(len(projects)))
    fill("dimensions_scored", str(scored))
    fill("high_confidence_count", str(high))
    fill("medium_confidence_count", str(medium))
    fill("low_confidence_count", str(low))
    fill("sensitive_excluded_summary", f"{redacted_count} pattern(s) redacted" if redacted_count > 0 else "None detected")

    for dim_key in DIMENSION_KEYS:
        dim = _dimension(analysis, dim_key)
        dim = dim if _truthy(dim) and isinstance(dim, dict) else {}
        rating = _or(dim.get("rating"), "UNSCORED")
        confidence = _or(dim.get("confidence"), "UNSCORED")
        instruction = _or(dim.get("claude_instruction"), "No strong preference detected. Ask the developer when this dimension is relevant.")
        summary = _or(dim.get("summary"), "")
        evidence = _or(dim.get("evidence_quotes"), dim.get("evidence"))
        if isinstance(evidence, list) and evidence:
            evidence_lines = []
            for item in evidence:
                item = item if isinstance(item, dict) else {}
                signal = _or(item.get("signal"), item.get("pattern"), "")
                quote = _or(item.get("quote"), item.get("example"), "")
                project = _or(item.get("project"), "unknown")
                evidence_lines.append(f'- **Signal:** {_js_string(signal)} / **Example:** "{_js_string(quote)}" -- project: {_js_string(project)}')
            evidence_block = "\n".join(evidence_lines)
        else:
            evidence_block = "- No evidence collected for this dimension."
        fill(f"{dim_key}.rating", _js_string(rating))
        fill(f"{dim_key}.confidence", _js_string(confidence))
        fill(f"{dim_key}.claude_instruction", _js_string(instruction))
        fill(f"{dim_key}.summary", _js_string(summary))
        fill(f"{dim_key}.evidence", evidence_block)

    output_path = options.get("output")
    if not output_path:
        # #1114: resolve the ACTIVE runtime's config home so the profile lands where that runtime looks.
        effective_runtime = _effective_runtime_with_default(cwd)
        output_path = _join(_get_global_config_dir(effective_runtime), "gsd-core", "USER-PROFILE.md")
    elif not _is_absolute(output_path):
        output_path = _join(cwd, output_path)

    _ensure_dir(os.path.dirname(output_path))
    _platform_write(output_path, template)

    output({
        "profile_path": output_path,
        "dimensions_scored": scored,
        "high_confidence": high,
        "medium_confidence": medium,
        "low_confidence": low,
        "sensitive_redacted": redacted_count,
        "source": data_source,
    }, raw, None)


def cmd_profile_questionnaire(options, raw):
    """Emit the interactive question list, or score comma-separated answers into an analysis."""
    answers = options.get("answers")
    if not answers:
        output({
            "mode": "interactive",
            "questions": [{
                "dimension": q["dimension"], "header": q["header"], "context": q["context"], "question": q["question"],
                "options": [{"label": o["label"], "value": o["value"]} for o in q["options"]],
            } for q in PROFILING_QUESTIONS],
        }, raw, None)
        return

    answer_values = [item.strip() for item in answers.split(",")]
    if len(answer_values) != len(PROFILING_QUESTIONS):
        error(f"Expected {len(PROFILING_QUESTIONS)} answers (comma-separated), got {len(answer_values)}")

    analysis = {
        "profile_version": "1.0",
        "analyzed_at": _iso_now(),
        "data_source": "questionnaire",
        "projects_analyzed": [],
        "messages_analyzed": 0,
        "message_threshold": "questionnaire",
        "sensitive_excluded": [],
        "dimensions": {},
    }
    for question, answer in zip(PROFILING_QUESTIONS, answer_values):
        selected = next((o for o in question["options"] if o["value"] == answer), None)
        if selected is None:
            error(f'Invalid answer "{answer}" for {question["dimension"]}. Valid values: {", ".join(o["value"] for o in question["options"])}')
        ambiguous = _is_ambiguous_answer(question["dimension"], answer)
        analysis["dimensions"][question["dimension"]] = {
            "rating": selected["rating"],
            "confidence": "LOW" if ambiguous else "MEDIUM",
            "evidence_count": 1,
            "cross_project_consistent": None,
            "evidence": [{
                "signal": "Self-reported via questionnaire",
                "quote": selected["label"],
                "project": "N/A (questionnaire)",
            }],
            "summary": f"Developer self-reported as {selected['rating']} for {question['header'].lower()}.",
            "claude_instruction": _generate_claude_instruction(question["dimension"], selected["rating"]),
        }
    output(analysis, raw, None)


def _directive_instruction(dim_key, dim):
    instruction = dim.get("claude_instruction")
    if not _truthy(instruction):
        lookup = CLAUDE_INSTRUCTIONS.get(dim_key)
        if lookup and _truthy(dim.get("rating")) and lookup.get(dim["rating"]):
            instruction = lookup[dim["rating"]]
        else:
            instruction = f"Adapt to this developer's {dim_key.replace('_', ' ')} preference."
    return instruction


def cmd_generate_dev_preferences(cwd, options, raw):
    """Write the dev-preferences skill artifact from an analysis JSON."""
    if not options.get("analysis"):
        error("--analysis <path> is required")
    analysis = _load_analysis(cwd, options["analysis"])

    labels = {
        "communication_style": "Communication", "decision_speed": "Decision Support", "explanation_depth": "Explanations",
        "debugging_approach": "Debugging", "ux_philosophy": "UX Approach", "vendor_philosophy": "Library & Tool Choices",
        "frustration_triggers": "Boundaries", "learning_style": "Learning Support",
    }
    template = _read_template("dev-preferences.md")

    directive_lines = []
    dimensions_included = []
    for dim_key in DIMENSION_KEYS:
        dim = _dimension(analysis, dim_key)
        if not _truthy(dim):
            continue
        label = labels.get(dim_key) or dim_key
        confidence = _or(dim.get("confidence"), "UNSCORED")
        directive_lines.append(f"### {label}\n{_js_string(_directive_instruction(dim_key, dim))} ({_js_string(confidence)} confidence)\n")
        dimensions_included.append(dim_key)

    data_source = _js_string(_or(analysis.get("data_source"), "session_analysis"))
    template = template.replace("{{behavioral_directives}}", "\n".join(directive_lines).strip())
    template = template.replace("{{generated_at}}", _iso_now())
    template = template.replace("{{data_source}}", data_source)

    if analysis.get("data_source") == "questionnaire":
        stack_block = (f"Stack preferences not available (questionnaire-only profile). Run "
                       f"`{_format_gsd_slash('profile-user', _resolve_runtime(cwd))} --refresh` with session data to populate.")
    elif options.get("stack"):
        stack_block = options["stack"]
    else:
        stack_block = "Stack preferences will be populated from session analysis."
    template = template.replace("{{stack_preferences}}", stack_block)

    # #2973: the default target is skills/<skill>/SKILL.md under the runtime's global skills root.
    output_path = options.get("output")
    if not output_path:
        effective_runtime = _effective_runtime_with_default(cwd)
        skill_dir = _get_global_skill_dir(effective_runtime, "gsd-dev-preferences")
        if not skill_dir:
            error(f'Runtime "{effective_runtime}" does not use a skills directory; pass --output to choose a path explicitly.')
        output_path = _join(skill_dir, "SKILL.md")
    elif not _is_absolute(output_path):
        output_path = _join(cwd, output_path)

    _ensure_dir(os.path.dirname(output_path))
    _platform_write(output_path, template)

    output({
        "command_path": output_path,
        "command_name": _format_gsd_slash("dev-preferences", _resolve_runtime(cwd)),
        "dimensions_included": dimensions_included,
        "source": data_source,
    }, raw, None)


def cmd_generate_claude_profile(cwd, options, raw):
    """Write or refresh the Developer Profile section of the runtime's instruction file."""
    if not options.get("analysis"):
        error("--analysis <path> is required")
    analysis = _load_analysis(cwd, options["analysis"])

    labels = {
        "communication_style": "Communication", "decision_speed": "Decisions", "explanation_depth": "Explanations",
        "debugging_approach": "Debugging", "ux_philosophy": "UX Philosophy", "vendor_philosophy": "Vendor Choices",
        "frustration_triggers": "Frustrations", "learning_style": "Learning",
    }
    data_source = _js_string(_or(analysis.get("data_source"), "session_analysis"))
    table_rows = []
    directive_lines = []
    dimensions_included = []
    for dim_key in DIMENSION_KEYS:
        dim = _dimension(analysis, dim_key)
        if not _truthy(dim):
            continue
        label = labels.get(dim_key) or dim_key
        rating = _or(dim.get("rating"), "UNSCORED")
        confidence = _or(dim.get("confidence"), "UNSCORED")
        table_rows.append(f"| {label} | {_js_string(rating)} | {_js_string(confidence)} |")
        directive_lines.append(f"- **{label}:** {_js_string(_directive_instruction(dim_key, dim))}")
        dimensions_included.append(dim_key)

    section_content = "\n".join([
        "<!-- GSD:profile-start -->",
        "## Developer Profile",
        "",
        f"> Generated by GSD from {data_source}. Run `{_format_gsd_slash('profile-user', _resolve_runtime(cwd))}` to update.",
        "",
        "| Dimension | Rating | Confidence |",
        "|-----------|--------|------------|",
        *table_rows,
        "",
        "**Directives:**",
        *directive_lines,
        "<!-- GSD:profile-end -->",
    ])

    # #2565: resolve the target through the effective runtime policy, not a hardcoded CLAUDE.md.
    config = {}
    try:
        config = _load_config(cwd)
    except Exception:
        pass
    effective_runtime = resolve_runtime_name_from_candidates(os.environ.get("GSD_RUNTIME"), config.get("runtime"))
    is_claude_runtime = not effective_runtime or effective_runtime == "claude"

    if options.get("global"):
        if is_claude_runtime:
            target_path = _join(_homedir(), ".claude", "CLAUDE.md")
        else:
            target_path = _join(_get_global_config_dir(effective_runtime),
                                os.path.basename(get_project_instruction_file(effective_runtime)))
    elif options.get("output"):
        target_path = options["output"] if _is_absolute(options["output"]) else _join(cwd, options["output"])
    else:
        config_claude_md_path = ".claude/CLAUDE.md"
        if config.get("claude_md_path"):
            config_claude_md_path = config["claude_md_path"]
        if not is_claude_runtime:
            config_claude_md_path = get_project_instruction_file(effective_runtime)
        target_path = config_claude_md_path if _is_absolute(config_claude_md_path) else _join(cwd, config_claude_md_path)

    existing = _platform_read(target_path)
    if existing is not None:
        start_marker, end_marker = "<!-- GSD:profile-start -->", "<!-- GSD:profile-end -->"
        start, end = existing.find(start_marker), existing.find(end_marker)
        if start != -1 and end != -1:
            existing = existing[:start] + section_content + existing[end + len(end_marker):]
            action = "updated"
        else:
            existing = existing.rstrip() + "\n\n" + section_content + "\n"
            action = "appended"
        _platform_write(target_path, existing)
    else:
        _ensure_dir(os.path.dirname(target_path))
        _platform_write(target_path, section_content + "\n")
        action = "created"

    output({
        "claude_md_path": target_path,
        "action": action,
        "dimensions_included": dimensions_included,
        "is_global": bool(options.get("global")),
    }, raw, None)


_MANAGED_SECTIONS = ["project", "stack", "conventions", "architecture", "skills", "workflow"]
_SECTION_HEADINGS = {
    "project": "## Project",
    "stack": "## Technology Stack",
    "conventions": "## Conventions",
    "architecture": "## Architecture",
    "skills": "## Project Skills",
    "workflow": "## GSD Workflow Enforcement",
}


def cmd_generate_claude_md(cwd, options, raw):
    """Generate or update the full instruction file with GSD-managed sections."""
    generators = {
        "project": _generate_project_section,
        "stack": _generate_stack_section,
        "conventions": _generate_conventions_section,
        "architecture": _generate_architecture_section,
        "skills": _generate_skills_section,
        "workflow": _generate_workflow_section,
    }
    generated = {}
    sections_generated = []
    sections_fallback = []
    sections_skipped = []
    for name in _MANAGED_SECTIONS:
        gen = generators[name](cwd)
        generated[name] = gen
        (sections_fallback if gen["hasFallback"] else sections_generated).append(name)

    assembly_config = {}
    # #1098: default to the project-scoped .claude/CLAUDE.md; --output and claude_md_path still win.
    config_claude_md_path = ".claude/CLAUDE.md"
    try:
        config = _load_config(cwd)
        if config.get("claude_md_path"):
            config_claude_md_path = config["claude_md_path"]
        if config.get("claude_md_assembly"):
            assembly_config = config["claude_md_assembly"]
        # #1529: with no explicit --output, a non-claude runtime always wins over a stale claude_md_path.
        effective_runtime = resolve_runtime_name_from_candidates(os.environ.get("GSD_RUNTIME"), config.get("runtime"))
        if not options.get("output") and effective_runtime and effective_runtime != "claude":
            config_claude_md_path = get_project_instruction_file(effective_runtime)
    except Exception:
        pass  # use default

    output_path = options.get("output")
    if not output_path:
        output_path = config_claude_md_path if _is_absolute(config_claude_md_path) else _join(cwd, config_claude_md_path)
    elif not _is_absolute(output_path):
        output_path = _join(cwd, output_path)

    global_mode = _or(assembly_config.get("mode") if isinstance(assembly_config, dict) else None, "embed")
    block_modes = _or(assembly_config.get("blocks") if isinstance(assembly_config, dict) else None, {})
    block_modes = block_modes if isinstance(block_modes, dict) else {}

    def effective_mode(name):
        return _or(block_modes.get(name), global_mode)

    def build_section_content(name, gen, heading):
        if effective_mode(name) == "link" and gen.get("linkPath") and not gen["hasFallback"]:
            return _build_section(name, gen["source"], f"{heading}\n\n@{gen['linkPath']}")
        return _build_section(name, gen["source"], f"{heading}\n\n{gen['content']}")

    existing_content = _platform_read(output_path)
    if existing_content is None:
        sections = [build_section_content(name, generated[name], _SECTION_HEADINGS[name]) for name in _MANAGED_SECTIONS]
        sections.append("")
        sections.append(_build_claude_md_profile_placeholder(_resolve_runtime(cwd)))
        existing_content = "\n\n".join(sections) + "\n"
        action = "created"
        _ensure_dir(os.path.dirname(output_path))
        _platform_write(output_path, existing_content)
    elif not re.search(r"<!-- GSD:[a-z]+-start", existing_content) and not options.get("force"):
        # #1098: a hand-crafted instruction file with no GSD markers is never clobbered without --force.
        output({
            "claude_md_path": output_path,
            "action": "skipped",
            "reason": "existing instruction file has no GSD markers (hand-crafted); not overwriting. Pass --force to overwrite.",
            "sections_generated": [],
            "sections_fallback": [],
            "sections_skipped": list(_MANAGED_SECTIONS),
            "sections_total": len(_MANAGED_SECTIONS),
            "profile_status": "skipped",
            "message": f"Left existing {os.path.basename(output_path)} untouched (no GSD markers found). Broad project context lives in PROJECT.md / REQUIREMENTS.md; pass --force to overwrite this file with GSD-managed sections.",
        }, raw, None)
        return
    else:
        action = "updated"
        file_content = existing_content
        for name in _MANAGED_SECTIONS:
            gen = generated[name]
            heading = _SECTION_HEADINGS[name]
            full_section = build_section_content(name, gen, heading)
            has_markers = file_content.find(f"<!-- GSD:{name}-start") != -1
            if has_markers and options.get("auto"):
                if effective_mode(name) == "link" and gen.get("linkPath") and not gen["hasFallback"]:
                    expected_body = f"{heading}\n\n@{gen['linkPath']}"
                else:
                    expected_body = f"{heading}\n\n{gen['content']}"
                if _detect_manual_edit(file_content, name, expected_body):
                    sections_skipped.append(name)
                    if name in sections_generated:
                        sections_generated.remove(name)
                    if name in sections_fallback:
                        sections_fallback.remove(name)
                    continue
            file_content = _update_section(file_content, name, full_section)["content"]
        if not options.get("auto") and file_content.find("<!-- GSD:profile-start") == -1:
            file_content = file_content.rstrip() + "\n\n" + _build_claude_md_profile_placeholder(_resolve_runtime(cwd)) + "\n"
        _platform_write(output_path, file_content)

    final_content = _platform_read(output_path)
    if final_content and final_content.find("<!-- GSD:profile-start") != -1:
        if action == "created" or existing_content.find("<!-- GSD:profile-start") == -1:
            profile_status = "placeholder_added"
        else:
            profile_status = "exists"
    else:
        profile_status = "already_present"

    total_managed = len(_MANAGED_SECTIONS)
    message = f"Generated {len(sections_generated)}/{total_managed} sections."
    if sections_fallback:
        message += f" Fallback: {', '.join(sections_fallback)}."
    if sections_skipped:
        message += f" Skipped (manually edited): {', '.join(sections_skipped)}."
    if profile_status == "placeholder_added":
        message += f" Run {_format_gsd_slash('profile-user', _resolve_runtime(cwd))} to unlock Developer Profile."

    output({
        "claude_md_path": output_path,
        "action": action,
        "sections_generated": sections_generated,
        "sections_fallback": sections_fallback,
        "sections_skipped": sections_skipped,
        "sections_total": total_managed,
        "profile_status": profile_status,
        "message": message,
    }, raw, None)
