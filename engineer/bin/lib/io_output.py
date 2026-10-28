"""CLI I/O primitives: output(), error(), ERROR_REASON, JSON-error mode and the
temp-file helpers that output() depends on.

Ported from upstream gsd-core ``src/io.cts`` at pinned commit
d37ff11b47258b560f0cf8f1132b42ecd90e0c79 (MIT, Copyright (c) 2026 Open GSD).
The needed pieces of ``src/shell-command-projection.cts`` (``platformWriteSync``,
``platformEnsureDir``) and ``src/cli-exit.cts`` (``ExitError``, the JSON-error-mode,
contract-version and pending-outcome cells, ``projectOutcome``) plus the exit-code
registry (``gsd-core/bin/shared/exit-codes.json``) are inlined as private helpers.

The ``@file:`` overflow protocol: a JSON payload whose serialized form exceeds
50000 characters is written to ``<tmpdir>/gsd/gsd-<epoch-ms>.json`` and the CLI
prints ``@file:<path>`` instead. Callers unwrap it with ``resolve_at_file_output``.

Deviations:
- The module is named ``io_output`` (not ``io``) so it never shadows stdlib ``io``.
- JS ``undefined`` has no Python equivalent: the ``UNDEFINED`` sentinel stands in
  for it (a dict key holding ``UNDEFINED`` is dropped when serialized, as
  ``JSON.stringify`` does, and does not count as a payload-carried error).
  ``raw_value=None`` means "no raw value" (upstream ``undefined``).
- ``output()`` and ``error()`` write with ``os.write`` on fds 1 and 2 (upstream
  ``fs.writeSync``); EAGAIN/EINTR retry and short-write loops are preserved.
- ``capture_stdout_sync_writes`` is synchronous (upstream returns a Promise); an
  awaitable returned by ``run`` is driven with ``asyncio.run``. It intercepts
  ``os.write`` calls on fd 1.
- Only the cli-exit pieces ``io`` consumes are inlined. ``runMain``,
  ``terminateNow`` and ``declareOutcome`` are not ported; the process-global
  cells live in a dict on ``builtins`` so two imports of this module share them.
- ``platformWriteSync`` is reduced to the non-Markdown path (the spill file is
  always ``.json``): CRLF to LF, trailing newlines collapsed to one, atomic
  replace with bounded retry on transient Windows lock errors. Markdown
  normalization is not ported.
- ``process.exitCode`` / ``process.exit`` have no counterpart: ``error()`` raises
  ``ExitError`` and the caller owns termination.
"""
from __future__ import annotations

import asyncio
import builtins
import errno
import inspect
import json
import math
import os
import re
import shutil
import sys
import tempfile
import time

__all__ = [
    "GSD_TEMP_DIR", "UNDEFINED", "ERROR_REASON", "ExitError", "ensure_gsd_temp_dir",
    "reap_stale_temp_files", "output", "decline_no_op", "serialize_for_output",
    "set_json_error_mode", "get_json_error_mode", "error", "format_diagnostic_token",
    "capture_stdout_sync_writes", "resolve_at_file_output",
]


class _Undefined:
    """Sentinel for JS ``undefined``."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "UNDEFINED"

    def __bool__(self):
        return False


UNDEFINED = _Undefined()

# ─── cli-exit pieces (private) ────────────────────────────────────────────────

EXIT_ENVELOPE_REASON = "sdk_fail_fast"

_EXIT_CODES = {"HOOK_DENY": 2, "USAGE": 64, "NO_INPUT": 66, "UNAVAILABLE": 69, "INTERNAL": 70, "DEGRADED": 80}


def _js_json(value):
    """``JSON.stringify`` for diagnostics: ``undefined`` renders as the word."""
    if value is UNDEFINED:
        return "undefined"
    try:
        return json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps(str(value), ensure_ascii=False)


def _exit_code_for(name):
    if not isinstance(name, str) or len(name) == 0:
        raise ValueError(f"exitCodeFor: name must be a non-empty string, received {_js_json(name)}")
    if name not in _EXIT_CODES:
        raise ValueError(f"exitCodeFor: unregistered exit code name: {_js_json(name)}")
    return _EXIT_CODES[name]


def _cells():
    cells = getattr(builtins, "_gsd_exit_cells", None)
    if cells is None:
        cells = {"json_error_mode": False, "contract_version": None, "pending_outcome": None}
        builtins._gsd_exit_cells = cells
    return cells


def set_json_error_mode(value):
    """Process-level flag: when true, error() emits structured JSON to stderr."""
    _cells()["json_error_mode"] = bool(value)


def get_json_error_mode():
    return _cells()["json_error_mode"] is True


def _set_contract_version(version):
    _cells()["contract_version"] = version


def _resolve_contract_version(argv=None, env=None):
    """Resolve the exit-contract version from argv/env and persist it (flag beats env)."""
    argv = sys.argv if argv is None else argv
    env = os.environ if env is None else env
    flag = None
    for arg in argv:
        if isinstance(arg, str) and arg.startswith("--exit-contract="):
            flag = arg[len("--exit-contract="):]
            break
    raw_env = env.get("GSD_EXIT_CONTRACT")
    env_value = None if raw_env is None or raw_env == "" else raw_env
    selected = flag if flag is not None else env_value
    if selected is None:
        resolved = "v1"
    elif selected in ("v1", "v2"):
        resolved = selected
    else:
        raise ValueError(
            f"resolveContractVersion: unrecognized exit-contract version {_js_json(selected)} "
            "(expected 'v1' or 'v2')")
    _set_contract_version(resolved)
    return resolved


def _get_contract_version():
    cached = _cells()["contract_version"]
    if cached in ("v1", "v2"):
        return cached
    return _resolve_contract_version()


def _project_outcome(outcome, version):
    """Project a declared outcome name onto an integer exit code for a contract version."""
    if not isinstance(outcome, str) or len(outcome) == 0:
        raise ValueError(f"projectOutcome: outcome must be a non-empty string, received {_js_json(outcome)}")
    if version not in ("v1", "v2"):
        raise ValueError(f"projectOutcome: version must be 'v1' or 'v2', received {_js_json(version)}")
    if outcome == "PASS":
        return 0
    if outcome == "FAIL":
        return 1
    if outcome == "DEGRADED":
        return 0 if version == "v1" else _exit_code_for("DEGRADED")
    return _exit_code_for(outcome)


def _set_pending_outcome(value):
    _cells()["pending_outcome"] = value


def _get_pending_outcome():
    return _cells()["pending_outcome"]


class ExitError(Exception):
    """Error carrying a process exit code; the entrypoint translates it into an exit status."""

    def __init__(self, code=1, message=None):
        super().__init__(f"process exit {code}" if message is None else message)
        self.name = "ExitError"
        self.code = code
        self.has_user_message = message is not None


# ─── platform write pieces (private) ──────────────────────────────────────────

_RENAME_RETRY_ERRNOS = (errno.EPERM, errno.EBUSY, errno.EACCES)
_RENAME_MAX_ATTEMPTS = 3
_RENAME_RETRY_BACKOFF_S = 0.05


def _atomic_rename_with_retry(tmp_path, file_path):
    """Return None on success, or the final OSError when every attempt failed."""
    rename_err = None
    for attempt in range(1, _RENAME_MAX_ATTEMPTS + 1):
        try:
            os.replace(tmp_path, file_path)
            return None
        except OSError as exc:
            rename_err = exc
            transient = exc.errno in _RENAME_RETRY_ERRNOS or isinstance(exc, PermissionError)
            if attempt < _RENAME_MAX_ATTEMPTS and transient:
                time.sleep(_RENAME_RETRY_BACKOFF_S)
                continue
            break
    return rename_err


def _normalize_non_markdown(content):
    return re.sub(r"\n*\Z", "\n", (content or "").replace("\r\n", "\n"), count=1)


def _write_bytes(path, data):
    with open(path, "wb") as handle:
        handle.write(data)


def _platform_write(file_path, content):
    """Atomic publish of ``content`` at ``file_path`` (non-Markdown normalization)."""
    data = _normalize_non_markdown(content).encode("utf-8")
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    tmp_path = f"{file_path}.tmp.{os.getpid()}"
    try:
        _write_bytes(tmp_path, data)
    except OSError:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        _write_bytes(file_path, data)
        return
    rename_err = _atomic_rename_with_retry(tmp_path, file_path)
    if rename_err is None:
        return
    try:
        os.unlink(tmp_path)
    except OSError:
        pass
    if rename_err.errno in _RENAME_RETRY_ERRNOS or isinstance(rename_err, PermissionError):
        raise rename_err
    _write_bytes(file_path, data)


# ─── Temp-file helpers ────────────────────────────────────────────────────────

GSD_TEMP_DIR = os.path.join(tempfile.gettempdir(), "gsd")


def ensure_gsd_temp_dir():
    os.makedirs(GSD_TEMP_DIR, exist_ok=True)


def _now_ms():
    return time.time() * 1000


def reap_stale_temp_files(prefix="gsd-", max_age_ms=5 * 60 * 1000, dirs_only=False):
    """Remove stale ``<prefix>*`` entries older than ``max_age_ms`` from GSD_TEMP_DIR."""
    try:
        ensure_gsd_temp_dir()
        now = _now_ms()
        for entry in os.listdir(GSD_TEMP_DIR):
            if not entry.startswith(prefix):
                continue
            full_path = os.path.join(GSD_TEMP_DIR, entry)
            try:
                stat = os.stat(full_path)
                if now - stat.st_mtime_ns / 1e6 > max_age_ms:
                    if os.path.isdir(full_path):
                        shutil.rmtree(full_path, ignore_errors=True)
                    elif not dirs_only:
                        os.unlink(full_path)
            except OSError:
                pass  # removed between listdir and stat
    except Exception:
        pass  # non-critical: cleanup failures never break output


# ─── Output helpers ───────────────────────────────────────────────────────────

_WRITE_RETRY_ERRNOS = (errno.EAGAIN, errno.EINTR)
_WRITE_MAX_RETRIES = 1000
_WRITE_RETRY_BACKOFF_S = 0.001


def _write_all_sync(fd, data):
    """Write the entire payload to ``fd``, tolerating non-blocking-pipe back-pressure."""
    buf = data.encode("utf-8")
    offset = 0
    retries = 0
    while offset < len(buf):
        try:
            offset += os.write(fd, buf[offset:])
        except (BlockingIOError, InterruptedError) as exc:
            if retries < _WRITE_MAX_RETRIES:
                retries += 1
                time.sleep(_WRITE_RETRY_BACKOFF_S)
                continue
            raise exc
        except OSError as exc:
            if exc.errno in _WRITE_RETRY_ERRNOS and retries < _WRITE_MAX_RETRIES:
                retries += 1
                time.sleep(_WRITE_RETRY_BACKOFF_S)
                continue
            raise


def capture_stdout_sync_writes(run):
    """Run ``run`` while capturing everything written to fd 1; return the captured text.

    On a raise from ``run`` whatever was captured is flushed to the real stdout and
    the error propagates.
    """
    original_write = os.write
    captured = []

    def patched(fd, data, *rest):
        if fd == 1:
            text = bytes(data).decode("utf-8") if not isinstance(data, str) else data
            captured.append(text)
            return len(bytes(data)) if not isinstance(data, str) else len(data.encode("utf-8"))
        return original_write(fd, data, *rest)

    os.write = patched
    try:
        result = run()
        if inspect.isawaitable(result):
            asyncio.run(_await(result))
    except BaseException:
        os.write = original_write
        text = "".join(captured)
        if text:
            try:
                original_write(1, text.encode("utf-8"))
            except Exception:
                pass  # best-effort flush
        raise
    os.write = original_write
    return "".join(captured)


async def _await(awaitable):
    return await awaitable


def resolve_at_file_output(captured):
    """Resolve ``output()``'s ``@file:<path>`` redirection back to the real content."""
    if not captured.startswith("@file:"):
        return captured
    with open(captured[len("@file:"):], "rb") as handle:
        return handle.read().decode("utf-8")


def _js_number(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        if value == int(value):
            return int(value)
    return value


def _to_jsonable(value):
    if value is UNDEFINED:
        return None  # array slot / top level: JSON.stringify yields null in arrays
    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items() if v is not UNDEFINED}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return _js_number(value)


def serialize_for_output(result):
    """The wire form of a JSON result: the exact bytes ``output()`` emits for it."""
    return json.dumps(_to_jsonable(result), indent=2, ensure_ascii=False)


def _is_payload_carried_error(result):
    return isinstance(result, dict) and "error" in result and result["error"] is not UNDEFINED


def _js_string(value):
    """``String(value)`` as JavaScript renders it."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    if value is UNDEFINED:
        return "undefined"
    if isinstance(value, float):
        number = _js_number(value)
        return "NaN" if number is None else str(number)
    if isinstance(value, (list, tuple)):
        return ",".join("" if v is None or v is UNDEFINED else _js_string(v) for v in value)
    if isinstance(value, dict):
        return "[object Object]"
    return str(value)


def _utf16_length(text):
    return len(text.encode("utf-16-le", "surrogatepass")) // 2


def output(result, raw, raw_value=None):
    """Write a result to stdout as JSON (or ``raw_value`` when ``raw``), spilling >50000 chars to a tempfile."""
    if _is_payload_carried_error(result):
        _set_pending_outcome("DEGRADED")
    else:
        _set_pending_outcome(None)
    if raw and raw_value is not None and raw_value is not UNDEFINED:
        data = _js_string(raw_value)
    else:
        text = serialize_for_output(result)
        if _utf16_length(text) > 50000:
            reap_stale_temp_files()
            ensure_gsd_temp_dir()
            tmp_path = os.path.join(GSD_TEMP_DIR, f"gsd-{int(_now_ms())}.json")
            _platform_write(tmp_path, text)
            data = "@file:" + tmp_path
        else:
            data = text
    _write_all_sync(1, data)


def _write_stderr_text(text):
    """``process.stderr.write``: bytes go out untranslated (no CRLF expansion on Windows)."""
    stream = sys.stderr
    buffer = getattr(stream, "buffer", None)
    if buffer is None:
        stream.write(text)
        stream.flush()
        return
    stream.flush()
    buffer.write(text.encode("utf-8"))
    buffer.flush()


def decline_no_op(raw, flag_key, reason, disclosure, computed=None):
    """Pair a ``[gsd-tools] WARNING:`` stderr disclosure with ``{flag_key: false, ...computed, reason}`` JSON."""
    _write_stderr_text(f"[gsd-tools] WARNING: {disclosure}\n")
    output({flag_key: False, **(computed or {}), "reason": reason}, raw, "false")


class _FrozenNamespace:
    """Immutable attribute namespace (frozen enum of wire values)."""

    def __init__(self, **values):
        object.__setattr__(self, "_values", dict(values))

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, "_values")[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name, value):
        raise AttributeError("ERROR_REASON is frozen")

    def __delattr__(self, name):
        raise AttributeError("ERROR_REASON is frozen")

    def __getitem__(self, name):
        return self._values[name]

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __contains__(self, name):
        return name in self._values

    def keys(self):
        return self._values.keys()

    def values(self):
        return self._values.values()

    def items(self):
        return self._values.items()


ERROR_REASON = _FrozenNamespace(
    CONFIG_KEY_NOT_FOUND="config_key_not_found",
    CONFIG_NO_FILE="config_no_file",
    CONFIG_PARSE_FAILED="config_parse_failed",
    CONFIG_INVALID_KEY="config_invalid_key",
    SDK_FAIL_FAST=EXIT_ENVELOPE_REASON,
    SDK_UNKNOWN_COMMAND="sdk_unknown_command",
    SDK_MISSING_ARG="sdk_missing_arg",
    PHASE_NOT_FOUND="phase_not_found",
    PHASE_ID_COLLISION="phase_id_collision",
    AMBIGUOUS_PHASE_OWNER="ambiguous_phase_owner",
    PHASE_NAMING_NOT_CUSTOM="phase_naming_not_custom",
    PHASE_VERIFICATION_INCOMPLETE="phase_verification_incomplete",
    PHASE_PLAN_COVERAGE_INCOMPLETE="phase_plan_coverage_incomplete",
    SUMMARY_NO_PLANNING="summary_no_planning",
    WORKSTREAM_MODE_NONE_ACTIVE="workstream_mode_none_active",
    WORKSTREAM_MODE_MARKER_UNRESOLVED="workstream_mode_marker_unresolved",
    GRAPHIFY_NO_GRAPH="graphify_no_graph",
    GRAPHIFY_INVALID_QUERY="graphify_invalid_query",
    ESTIMATE_PHASES_UNREADABLE="estimate_phases_unreadable",
    HOOKS_OPT_OUT="hooks_opt_out",
    COMMIT_DOCS_GUARD_NOT_A_REPO="commit_docs_guard_not_a_repo",
    COMMIT_DOCS_GUARD_FOREIGN_HOOK="commit_docs_guard_foreign_hook",
    COMMIT_DOCS_GUARD_HOOKS_PATH_SET="commit_docs_guard_hooks_path_set",
    SECURITY_SCAN_FAILED="security_scan_failed",
    PICK_FIELD_ABSENT="pick_field_absent",
    PICK_OUTPUT_NOT_JSON="pick_output_not_json",
    SUMMARY_EXTRACT_UNPARSEABLE="summary_extract_unparseable",
    VERIFICATION_STATUS_INVALID="verification_status_invalid",
    USAGE="usage",
    UNKNOWN="unknown",
)

# ─── Diagnostics ──────────────────────────────────────────────────────────────

_INVISIBLE_OR_BIDI_RANGES = (
    (0x7F, 0x9F), (0x2028, 0x2029), (0x200B, 0x200F), (0x202A, 0x202E), (0x2066, 0x2069),
    (0xFEFF, 0xFEFF),
    (0xD800, 0xDFFF),  # lone surrogates (JS iterates UTF-16 units; Python holds them only when lone)
)
_INVISIBLE_OR_BIDI_RE = re.compile(
    "[" + "".join(f"\\u{lo:04x}-\\u{hi:04x}" for lo, hi in _INVISIBLE_OR_BIDI_RANGES) + "]")


def _to_unicode_escape(code_point):
    return f"\\u{code_point:04x}"


def format_diagnostic_token(value):
    """Render an untrusted string as one quoted, single-line, invisible-character-free token."""
    return _INVISIBLE_OR_BIDI_RE.sub(lambda m: _to_unicode_escape(ord(m.group(0))),
                                     json.dumps(value, ensure_ascii=False))


_REASON_TO_OUTCOME = {
    ERROR_REASON.CONFIG_INVALID_KEY: "USAGE",
    ERROR_REASON.SDK_UNKNOWN_COMMAND: "USAGE",
    ERROR_REASON.SDK_MISSING_ARG: "USAGE",
    ERROR_REASON.GRAPHIFY_INVALID_QUERY: "USAGE",
    ERROR_REASON.USAGE: "USAGE",
    ERROR_REASON.PHASE_ID_COLLISION: "USAGE",
    ERROR_REASON.AMBIGUOUS_PHASE_OWNER: "USAGE",
    ERROR_REASON.PHASE_NAMING_NOT_CUSTOM: "USAGE",
    ERROR_REASON.CONFIG_KEY_NOT_FOUND: "NO_INPUT",
    ERROR_REASON.SUMMARY_NO_PLANNING: "NO_INPUT",
    ERROR_REASON.WORKSTREAM_MODE_NONE_ACTIVE: "NO_INPUT",
    ERROR_REASON.CONFIG_NO_FILE: "UNAVAILABLE",
    ERROR_REASON.CONFIG_PARSE_FAILED: "UNAVAILABLE",
    ERROR_REASON.PHASE_NOT_FOUND: "UNAVAILABLE",
    ERROR_REASON.PHASE_VERIFICATION_INCOMPLETE: "UNAVAILABLE",
    ERROR_REASON.PHASE_PLAN_COVERAGE_INCOMPLETE: "UNAVAILABLE",
    ERROR_REASON.WORKSTREAM_MODE_MARKER_UNRESOLVED: "UNAVAILABLE",
    ERROR_REASON.GRAPHIFY_NO_GRAPH: "UNAVAILABLE",
    ERROR_REASON.ESTIMATE_PHASES_UNREADABLE: "UNAVAILABLE",
    ERROR_REASON.COMMIT_DOCS_GUARD_NOT_A_REPO: "UNAVAILABLE",
    ERROR_REASON.COMMIT_DOCS_GUARD_FOREIGN_HOOK: "UNAVAILABLE",
    ERROR_REASON.COMMIT_DOCS_GUARD_HOOKS_PATH_SET: "UNAVAILABLE",
    ERROR_REASON.PICK_FIELD_ABSENT: "UNAVAILABLE",
    ERROR_REASON.PICK_OUTPUT_NOT_JSON: "UNAVAILABLE",
    ERROR_REASON.SUMMARY_EXTRACT_UNPARSEABLE: "UNAVAILABLE",
    ERROR_REASON.VERIFICATION_STATUS_INVALID: "UNAVAILABLE",
    ERROR_REASON.SDK_FAIL_FAST: "INTERNAL",
    ERROR_REASON.SECURITY_SCAN_FAILED: "INTERNAL",
    ERROR_REASON.HOOKS_OPT_OUT: "FAIL",
    ERROR_REASON.UNKNOWN: "FAIL",
}


def _outcome_for_reason(reason):
    return _REASON_TO_OUTCOME.get(reason, "FAIL")


def error(message, reason=ERROR_REASON.UNKNOWN, extra=None):
    """Write an error to stderr and raise ``ExitError`` (v1: code 1; v2: the reason's projected outcome)."""
    if get_json_error_mode():
        payload = json.dumps({"ok": False, "reason": reason, "message": message, **(extra or {})},
                             ensure_ascii=False, separators=(",", ":")) + "\n"
        _write_all_sync(2, payload)
    else:
        _write_all_sync(2, "Error: " + message + "\n")
    if _get_contract_version() == "v2":
        raise ExitError(_project_outcome(_outcome_for_reason(reason), "v2"))
    raise ExitError(1)
