"""Prohibition probe: the deterministic test-tier enforcement producer and its gate.

Ported from upstream ``src/prohibition-enforcement.cts`` and
``src/gate-prohibition-enforcement.cts`` of gsd-core (MIT, Copyright (c) 2026 Open GSD)
at pinned commit d37ff11b47258b560f0cf8f1132b42ecd90e0c79.

Engine identification: ``engineer/references/prohibition-probe.md`` names a
``prohibition-probe.cjs`` engine, but upstream ships no such file and its reference doc
states there is none ("the recall stage is an LLM prose pass, and only the
schema/projection layer is real code"). The real code behind the doc is:
  - the schema / projection layer, already ported in ``probe_core``
    (``PROHIBITION_VALIDATORS``, ``validate_prohibition_resolution``,
    ``project_prohibitions``, ``disposition_for_prohibition``), re-exported below;
  - the producer in this module: locate the wired mechanical check, machine-prove it
    fails first, run it, build ``enforcementEvidence`` and deliver the
    ``disposition_for_prohibition`` verdict (``run_prohibition_enforcement``);
  - the ``check prohibition-enforcement`` gate (``evaluate_prohibition_enforcement_gate``).

Wired-check kinds: ``node-test`` (a ``node --test`` negative test) and ``lint-rule``
(an eslint rule). Fail-first is machine-proven, never attested: green requires the
prover to observe the check go red on a known-bad fixture AND the runner to observe a
non-vacuous clean pass. Dicts keep the upstream JSON field names (``failFirst``,
``violationFixture``, ``cleanFixture``, ``failFirstProof``, ``provenFailFirst``).

Deviations:
  - The subject-injection convention is exported under both ``ENGINEER_PROHIB_SUBJECT``
    (the name ``engineer/references/prohibition-probe.md`` documents) and upstream's
    ``GSD_PROHIB_SUBJECT``, with the same value.
  - Options are keyword arguments (``run_check``, ``prove_fail_first``, ``mode``,
    ``cwd``, ``timeout_ms``) instead of an options object.
  - The real runners spawn ``node`` (resolved from PATH) and the project's eslint
    (``node_modules/eslint`` found from ``cwd`` upward); a missing tool is the same
    fail-closed, non-passing result as upstream. Child output is decoded as UTF-8 and
    the 16 MiB output cap is checked after the child exits rather than enforced by the
    pipe.
  - Process-tree reaping on timeout uses ``killpg`` on POSIX (the child starts in its
    own session) and an absolute-path ``taskkill /T /F`` on Windows, as upstream.
  - The gate returns the GateResult shape (``{outcome, block, payload}`` or
    ``{failure: {code, message}}``) built by private helpers because this repository
    has no ``gate-verdict`` module at the base commit; the payload is a read-only dict.
  - Upstream ``routeCheckCommand`` (the ``check`` CLI router that formats the gate
    result and maps it to an exit status) is not ported, so there is no ``main``.
  - ``validate_prohibition_resolution`` and friends are re-exported from
    ``probe_core`` rather than defined here.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

from . import probe_core
from .probe_core import (  # noqa: F401  (re-exported schema/projection layer)
    PROHIBITION_VALIDATORS,
    project_prohibitions,
    validate_prohibition_resolution,
)

NODE_TEST_TIMEOUT_MS = 30_000
ESLINT_TIMEOUT_MS = 60_000
CHECK_MAX_BUFFER = 16 * 1024 * 1024

_GATE_USAGE_CODE = "sdk_missing_arg"
_GATE_USAGE_MESSAGE = ("prohibition-enforcement requires a JSON request: check prohibition-enforcement "
                       "<request.json> | --json '{\"prohibition\":{...},\"check\":{...}}'")


# ---------------------------------------------------------------------------------------------
# Descriptor read-back
# ---------------------------------------------------------------------------------------------

def descriptor_from_projection(projected):
    """Rebuild a CheckDescriptor from the flat ``check_*`` scalars ``project_prohibitions`` emits.

    None for a non-object or an item without ``check_kind``. Otherwise
    ``{kind, target}`` plus ``rule`` (lint-rule only, non-blank), ``violationFixture`` and
    ``cleanFixture`` (non-blank). ``failFirst`` is never sourced from the projection. The
    adapter does not validate kind/target/rule: the producer's locate guard rejects an
    under-specified descriptor. Pure and no-throw.
    """
    if not isinstance(projected, dict) or "check_kind" not in projected:
        return None

    def scalar(value):
        # string|number scalars only (the frontmatter parser coerces /^\d+$/ to numbers);
        # anything else is '' so it fails the locate guard instead of stringifying.
        if isinstance(value, str):
            return value
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return str(value)
        return ""

    kind = scalar(projected.get("check_kind"))
    descriptor = {"kind": kind, "target": scalar(projected.get("check_target"))}
    if kind == "lint-rule":
        rule = scalar(projected.get("check_rule"))
        if rule.strip():
            descriptor["rule"] = rule
    fixture = scalar(projected.get("check_violation_fixture"))
    if fixture.strip():
        descriptor["violationFixture"] = fixture
    clean = scalar(projected.get("check_clean_fixture"))
    if clean.strip():
        descriptor["cleanFixture"] = clean
    return descriptor


# ---------------------------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------------------------

def build_node_test_args(check):
    """``node --test`` argv: TAP reporter, ``--`` before the target (option-injection guard)."""
    return ["--test", "--test-reporter=tap", "--", check["target"]]


def build_lint_args(check):
    """eslint argv (after the CLI path): JSON over the target, ignored targets lint to ``[]``."""
    return ["--no-warn-ignored", "--format", "json", "--", check["target"]]


def _base_of(path):
    return re.split(r"[\\/]", path)[-1] if isinstance(path, str) else ""


def parse_node_test_summary(out):
    """Parse the TAP summary counts; a missing line counts as 0."""
    def num(pattern):
        match = re.search(pattern, out, re.M) if isinstance(out, str) else None
        return int(match.group(1)) if match else 0
    return {"tests": num(r"^# tests (\d+)"), "pass": num(r"^# pass (\d+)"),
            "fail": num(r"^# fail (\d+)"), "cancelled": num(r"^# cancelled (\d+)")}


def is_node_test_red(out):
    """True iff the TAP summary reports at least one failure."""
    return parse_node_test_summary(out)["fail"] >= 1


def _tap_names(out, pattern):
    if not isinstance(out, str):
        return []
    names = []
    for match in re.finditer(pattern, out, re.M):
        rest = match.group(1)
        if re.search(r"\s#\s*(?:SKIP|TODO)\b", rest, re.I):
            continue  # skipped/todo never ran
        names.append(re.sub(r"\s+#\s.*$", "", rest).strip())
    return names


def tap_test_names(out):
    """Names of tests that actually ran (``ok N - x`` / ``not ok N - x``), minus SKIP/TODO."""
    return _tap_names(out, r"^(?:not )?ok \d+ - (.+)$")


def tap_failed_test_names(out):
    """Names of failing tests (``not ok N - x``), minus SKIP/TODO."""
    return _tap_names(out, r"^not ok \d+ - (.+)$")


def is_non_vacuous_node_test_pass(out, target):
    """A pass with >=1 test, >=1 pass, 0 failures, 0 cancelled and a test not named after the file."""
    summary = parse_node_test_summary(out)
    if not (summary["tests"] >= 1 and summary["pass"] >= 1 and summary["fail"] == 0 and summary["cancelled"] == 0):
        return False
    target_base = _base_of(target)
    return any(_base_of(name) != target_base for name in tap_test_names(out))


def is_non_vacuous_node_test_red(out, target):
    """A red with ``# fail >= 1`` and a failing test not named after the file (not a load crash)."""
    if not is_node_test_red(out):
        return False
    target_base = _base_of(target)
    return any(_base_of(name) != target_base for name in tap_failed_test_names(out))


def eslint_file_result_count(json_text):
    """Number of file results in an eslint JSON report; 0 when unparseable or not a list."""
    try:
        parsed = json.loads(json_text)
    except (ValueError, TypeError):
        return 0
    return len(parsed) if isinstance(parsed, list) else 0


def _eslint_messages(file, key):
    value = file.get(key) if isinstance(file, dict) else None
    return value if isinstance(value, list) else []


def _parse_report(json_text):
    try:
        parsed = json.loads(json_text)
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, list) else None


def eslint_has_fatal_error(json_text):
    """True when the report has a fatal/parse error or is unreadable (the rule never ran)."""
    parsed = _parse_report(json_text)
    if parsed is None:
        return True
    for file in parsed:
        count = file.get("fatalErrorCount") if isinstance(file, dict) else None
        if isinstance(count, (int, float)) and not isinstance(count, bool) and count > 0:
            return True
        if any(isinstance(message, dict) and message.get("fatal") is True for message in _eslint_messages(file, "messages")):
            return True
    return False


def eslint_json_has_rule(json_text, rule):
    """True when any message (including suppressed ones) names ``rule``; unreadable -> True."""
    parsed = _parse_report(json_text)
    if parsed is None:
        return True
    for file in parsed:
        for key in ("messages", "suppressedMessages"):
            for message in _eslint_messages(file, key):
                if isinstance(message, dict) and message.get("ruleId") == rule:
                    return True
    return False


# ---------------------------------------------------------------------------------------------
# Bounded subprocess machinery
# ---------------------------------------------------------------------------------------------

class _ExecError(Exception):
    def __init__(self, stdout=""):
        super().__init__("check subprocess failed")
        self.stdout = stdout


def _child_env(extra=None):
    """Env for spawned checks: strip an ambient test-runner context and NODE_OPTIONS."""
    env = {key: value for key, value in os.environ.items() if key not in ("NODE_TEST_CONTEXT", "NODE_OPTIONS")}
    if extra:
        env.update(extra)
    return env


def _taskkill_path():
    root = os.environ.get("SystemRoot") or os.environ.get("windir")
    return os.path.join(root, "System32", "taskkill.exe") if root else None


def _reap_descendants(pid):
    """Reap the process tree rooted at ``pid`` after its own timeout killed it. Never raises."""
    if not isinstance(pid, int) or pid <= 0:
        return
    if sys.platform == "win32":
        exe = _taskkill_path()
        if not exe:
            return
        try:
            subprocess.run([exe, "/PID", str(pid), "/T", "/F"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=5, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:  # noqa: BLE001 - best effort
            pass
        return
    try:
        import signal
        os.killpg(pid, signal.SIGKILL)
    except Exception:  # noqa: BLE001 - group already gone or not permitted
        pass


def _exec_reaping(file, args, cwd, env, timeout_seconds):
    """Run ``file args`` bounded by a timeout; return stdout or raise ``_ExecError(stdout)``.

    Like ``execFileSync`` plus descendant reaping when, and only when, this call's own
    timeout killed the child. Arg list, no shell.
    """
    options = {"cwd": cwd, "env": env, "stdin": subprocess.DEVNULL, "stdout": subprocess.PIPE, "stderr": subprocess.PIPE}
    if sys.platform == "win32":
        options["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    else:
        options["start_new_session"] = True
    try:
        process = subprocess.Popen([file, *args], **options)
    except (OSError, ValueError) as error:
        raise _ExecError("") from error
    try:
        out, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        _reap_descendants(process.pid)
        process.kill()
        try:
            out, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:  # a surviving descendant still holds the pipe
            out = b""
        raise _ExecError(out.decode("utf-8", "replace"))
    text = out.decode("utf-8", "replace")
    if len(out) > CHECK_MAX_BUFFER or process.returncode != 0:
        raise _ExecError(text)
    return text


def _pos_timeout(timeout_ms, default):
    """Only a positive override is honored, so the subprocess is always bounded."""
    if isinstance(timeout_ms, (int, float)) and not isinstance(timeout_ms, bool) and timeout_ms > 0:
        return timeout_ms
    return default


def _node_executable():
    return shutil.which("node")


def _resolve_eslint_cli(cwd):
    """eslint's ``bin/eslint.js`` from ``cwd`` upward through ``node_modules``; None if absent."""
    directory = os.path.abspath(cwd)
    while True:
        package = os.path.join(directory, "node_modules", "eslint", "package.json")
        if os.path.isfile(package):
            cli = os.path.join(os.path.dirname(package), "bin", "eslint.js")
            return cli if os.path.exists(cli) else None
        parent = os.path.dirname(directory)
        if parent == directory:
            return None
        directory = parent


def _run_capturing(args, cwd, timeout_ms, default_ms, env=None):
    """Spawn node with ``args``; return stdout, recovering partial stdout from a failed run."""
    node = _node_executable()
    if node is None:
        return ""
    try:
        return _exec_reaping(node, args, cwd, env if env is not None else _child_env(), _pos_timeout(timeout_ms, default_ms) / 1000)
    except _ExecError as error:
        return error.stdout if isinstance(error.stdout, str) else ""


def _run_node_test_with_subject(check, cwd, subject, timeout_ms=None):
    return _run_capturing(build_node_test_args(check), cwd, timeout_ms, NODE_TEST_TIMEOUT_MS,
                          env=_child_env({"ENGINEER_PROHIB_SUBJECT": subject, "GSD_PROHIB_SUBJECT": subject}))


def _default_run_check(check, cwd, timeout_ms=None):
    """The default real runner: report only an observed, non-vacuous pass. Never raises."""
    try:
        if check.get("kind") == "node-test":
            out = _run_capturing(build_node_test_args(check), cwd, timeout_ms, NODE_TEST_TIMEOUT_MS)
            return {"passed": is_non_vacuous_node_test_pass(out, check["target"])}
        if check.get("kind") == "lint-rule":
            eslint_cli = _resolve_eslint_cli(cwd)
            if not eslint_cli:
                return {"passed": False}
            report = _run_capturing([eslint_cli, *build_lint_args(check)], cwd, timeout_ms, ESLINT_TIMEOUT_MS)
            return {"passed": eslint_file_result_count(report) >= 1 and not eslint_has_fatal_error(report)
                    and not eslint_json_has_rule(report, check["rule"])}
        return {"passed": False}
    except Exception:  # noqa: BLE001 - no-throw contract
        return {"passed": False}


def default_prove_fail_first(check, cwd, timeout_ms=None):
    """The default real fail-first prover. Never raises; every un-provable path is False.

    lint-rule: lint the ``violationFixture`` and require >=1 file result, no fatal error and
    the rule id in the report. node-test: the fixture must exist (resolved against ``cwd``),
    the test must go non-vacuously RED with ``ENGINEER_PROHIB_SUBJECT``/``GSD_PROHIB_SUBJECT`` set to it, and the
    mandatory ``cleanFixture`` control must exist and stay non-vacuously GREEN.
    """
    try:
        if check.get("kind") == "lint-rule":
            fixture = check.get("violationFixture")
            if not fixture:
                return {"provenFailFirst": False}
            eslint_cli = _resolve_eslint_cli(cwd)
            if not eslint_cli:
                return {"provenFailFirst": False}
            report = _run_capturing([eslint_cli, *build_lint_args({**check, "target": fixture})], cwd, timeout_ms, ESLINT_TIMEOUT_MS)
            proven = (eslint_file_result_count(report) >= 1 and not eslint_has_fatal_error(report)
                      and eslint_json_has_rule(report, check["rule"]))
            return {"provenFailFirst": proven, "method": "violation-fixture"}
        if check.get("kind") == "node-test":
            fixture = check.get("violationFixture")
            if not fixture or not os.path.exists(os.path.abspath(os.path.join(cwd, fixture))):
                return {"provenFailFirst": False}
            red = _run_node_test_with_subject(check, cwd, fixture, timeout_ms)
            if not is_non_vacuous_node_test_red(red, check["target"]):
                return {"provenFailFirst": False, "method": "violation-fixture"}
            clean = check.get("cleanFixture")
            if not clean:
                return {"provenFailFirst": False, "method": "violation-fixture"}
            if not os.path.exists(os.path.abspath(os.path.join(cwd, clean))):
                return {"provenFailFirst": False, "method": "violation-fixture"}
            green = _run_node_test_with_subject(check, cwd, clean, timeout_ms)
            if not is_non_vacuous_node_test_pass(green, check["target"]):
                return {"provenFailFirst": False, "method": "violation-fixture"}
            return {"provenFailFirst": True, "method": "violation-fixture"}
        return {"provenFailFirst": False}
    except Exception:  # noqa: BLE001 - no-throw contract
        return {"provenFailFirst": False}


# ---------------------------------------------------------------------------------------------
# The producer
# ---------------------------------------------------------------------------------------------

def run_prohibition_enforcement(prohibition, check, run_check=None, prove_fail_first=None, mode=None, cwd=None, timeout_ms=None):
    """LOCATE -> PROVE fail-first -> RUN -> build evidence -> ``disposition_for_prohibition``.

    Returns the disposition (``status``, ``flagged``, ``tier``, ``reason``) plus ``located``,
    ``kind``, ``evidence`` and, when given, ``mode``. A descriptor that is not a well-formed
    wired check is not located (fail-closed). A located check is green only when
    ``prove_fail_first(check)["provenFailFirst"] is True`` AND ``run_check(check)["passed"]
    is True``; a throwing seam counts as not proven / not passed. Caller attestation
    (``failFirst``) is never consulted. ``mode`` is echoed; the hard gate applies in every mode.
    """
    c = check if isinstance(check, dict) else None
    valid_kind = c is not None and c.get("kind") in ("node-test", "lint-rule")
    valid_target = c is not None and isinstance(c.get("target"), str) and c["target"].strip() != ""
    valid_rule = c is not None and (c.get("kind") != "lint-rule" or (isinstance(c.get("rule"), str) and c["rule"].strip() != ""))
    mode_part = {"mode": mode} if mode else {}
    if c is None or not valid_kind or not valid_target or not valid_rule:
        disposition = probe_core.disposition_for_prohibition(prohibition, {"enforcementEvidence": []})
        return {**disposition, "located": False, "kind": None, "evidence": [], **mode_part}

    root = cwd if cwd is not None else os.getcwd()
    run_check = run_check or (lambda to_run: _default_run_check(to_run, root, timeout_ms))
    prove_fail_first = prove_fail_first or (lambda to_prove: default_prove_fail_first(to_prove, root, timeout_ms))
    try:
        proof = prove_fail_first(c)
    except Exception:  # noqa: BLE001 - a throwing prover fails closed
        proof = {"provenFailFirst": False}
    try:
        run = run_check(c)
    except Exception:  # noqa: BLE001 - a throwing runner fails closed
        run = {"passed": False}
    proven = isinstance(proof, dict) and proof.get("provenFailFirst") is True
    passed = proven and isinstance(run, dict) and run.get("passed") is True
    if not passed:
        disposition = probe_core.disposition_for_prohibition(prohibition, {"enforcementEvidence": []})
        return {**disposition, "located": True, "kind": c["kind"], "evidence": [], **mode_part}
    evidence_item = {"kind": c["kind"], "target": c["target"]}
    if isinstance(c.get("rule"), str):
        evidence_item["rule"] = c["rule"]
    evidence_item.update({"failFirst": True, "passed": True})
    if proof.get("method"):
        evidence_item["failFirstProof"] = proof["method"]
    disposition = probe_core.disposition_for_prohibition(prohibition, {"enforcementEvidence": [evidence_item]})
    return {**disposition, "located": True, "kind": c["kind"], "evidence": [evidence_item], **mode_part}


# ---------------------------------------------------------------------------------------------
# The `check prohibition-enforcement` gate
# ---------------------------------------------------------------------------------------------

class _FrozenDict(dict):
    """A dict that rejects mutation (the analogue of ``Object.freeze``) yet still serializes."""

    def _blocked(self, *args, **kwargs):
        raise TypeError("a gate verdict payload is frozen")

    __setitem__ = __delitem__ = update = pop = popitem = clear = setdefault = __ior__ = _blocked


def _gate_verdict(outcome, block, payload):
    return {"outcome": outcome, "block": block, "payload": _FrozenDict(payload)}


def _gate_usage_failure(code, message):
    return {"failure": {"code": code, "message": message}}


def _reject_constant(name):
    raise ValueError(f"invalid JSON constant {name}")


def _parse_request(args):
    """Parse ``{prohibition, check, mode}`` from ``--json <inline>`` or a request file path."""
    args = list(args)
    flag_index = args.index("--json") if "--json" in args else -1
    inline = args[flag_index + 1] if 0 <= flag_index and flag_index + 1 < len(args) else None
    if flag_index != -1 and isinstance(inline, str):
        payload = inline
    elif args and isinstance(args[0], str) and args[0]:
        try:
            with open(args[0], encoding="utf-8", errors="replace") as stream:
                payload = stream.read()
        except OSError:
            return None
    else:
        return None
    try:
        document = json.loads(payload, parse_constant=_reject_constant)
    except ValueError:
        return None
    if document is None:
        return None
    parsed = document if isinstance(document, dict) else {}
    check_raw = parsed.get("check")
    mode_raw = parsed.get("mode")
    request = {"prohibition": parsed.get("prohibition"), "check": check_raw if isinstance(check_raw, dict) else None}
    if isinstance(mode_raw, str) and mode_raw:
        request["mode"] = mode_raw
    return request


def evaluate_prohibition_enforcement_gate(project_dir=None, args=(), env=None):
    """Evaluate ``check prohibition-enforcement`` and return a GateResult.

    ``{"outcome": "advisory", "block": False, "payload": <producer result>}`` for a parsed
    request (the disposition is a delivered answer, never a block); the ``unreadable``
    verdict carries the producer's fail-closed disposition when something throws; a request
    that is absent or does not parse is ``{"failure": {"code", "message"}}``. Writes nothing
    to stdout or stderr. ``project_dir`` and ``env`` are accepted for the gate signature and
    unused, as upstream.
    """
    request = _parse_request(args)
    if request is None:
        return _gate_usage_failure(_GATE_USAGE_CODE, _GATE_USAGE_MESSAGE)
    mode = request.get("mode")
    try:
        result = run_prohibition_enforcement(request["prohibition"], request["check"], mode=mode)
        return _gate_verdict("advisory", False, result)
    except Exception as error:  # noqa: BLE001 - a throw is a fail-closed unreadable verdict
        failed_closed = {"status": "unverified", "flagged": True, "tier": None, "reason": "exception: " + str(error),
                         "located": False, "kind": None, "evidence": [], **({"mode": mode} if mode else {})}
        return _gate_verdict("unreadable", False, failed_closed)
