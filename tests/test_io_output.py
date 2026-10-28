"""Tests for engineer/bin/lib/io_output.py (port of upstream gsd-core src/io.cts)."""
import contextlib
import errno
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

BIN = Path(__file__).resolve().parents[1]/"engineer"/"bin"

import importlib
import importlib.util

LIB = Path(__file__).resolve().parents[1]/"engineer"/"bin"/"lib"


def _load(name):
    """Load engineer/bin/lib as an isolated package (`lib` collides with .ai/runtime/lib)."""
    if "engineer_bin_lib" not in sys.modules:
        spec = importlib.util.spec_from_file_location("engineer_bin_lib", LIB/"__init__.py", submodule_search_locations=[str(LIB)])
        pkg = importlib.util.module_from_spec(spec)
        sys.modules["engineer_bin_lib"] = pkg
        spec.loader.exec_module(pkg)
    return importlib.import_module("engineer_bin_lib."+name)

io_output = _load("io_output")


def run_script(script):
    env = dict(os.environ, PYTHONPATH=str(BIN), PYTHONIOENCODING="utf-8")
    env.pop("GSD_EXIT_CONTRACT", None)
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, env=env, timeout=60)
    return result.returncode, result.stdout.decode("utf-8"), result.stderr.decode("utf-8")


@contextlib.contextmanager
def capture_fd(*fds):
    """Intercept os.write for the given fds, delivering nothing to the real fd."""
    original = os.write
    captured = {fd: [] for fd in fds}

    def patched(fd, data):
        if fd in captured:
            captured[fd].append(bytes(data))
            return len(data)
        return original(fd, data)

    with mock.patch.object(os, "write", patched):
        yield {fd: chunks for fd, chunks in captured.items()}


def text_of(chunks):
    return b"".join(chunks).decode("utf-8")


class IoCase(unittest.TestCase):
    def setUp(self):
        io_output.set_json_error_mode(False)
        io_output._resolve_contract_version(argv=["python", "x"], env={})
        io_output._set_pending_outcome(None)
        self.addCleanup(io_output.set_json_error_mode, False)
        self.addCleanup(io_output._resolve_contract_version, argv=["python", "x"], env={})
        self.addCleanup(io_output._set_pending_outcome, None)

    def use_v2(self):
        io_output._resolve_contract_version(argv=["python", "x", "--exit-contract=v2"], env={})


EXPECTED_REASON_OUTCOME = {
    "config_key_not_found": "NO_INPUT", "config_no_file": "UNAVAILABLE", "config_parse_failed": "UNAVAILABLE",
    "config_invalid_key": "USAGE", "sdk_fail_fast": "INTERNAL", "sdk_unknown_command": "USAGE",
    "sdk_missing_arg": "USAGE", "phase_not_found": "UNAVAILABLE", "phase_id_collision": "USAGE",
    "ambiguous_phase_owner": "USAGE", "phase_naming_not_custom": "USAGE",
    "phase_verification_incomplete": "UNAVAILABLE", "phase_plan_coverage_incomplete": "UNAVAILABLE",
    "summary_no_planning": "NO_INPUT", "workstream_mode_none_active": "NO_INPUT",
    "workstream_mode_marker_unresolved": "UNAVAILABLE", "graphify_no_graph": "UNAVAILABLE",
    "graphify_invalid_query": "USAGE", "estimate_phases_unreadable": "UNAVAILABLE", "hooks_opt_out": "FAIL",
    "commit_docs_guard_not_a_repo": "UNAVAILABLE", "commit_docs_guard_foreign_hook": "UNAVAILABLE",
    "commit_docs_guard_hooks_path_set": "UNAVAILABLE", "security_scan_failed": "INTERNAL",
    "pick_field_absent": "UNAVAILABLE", "pick_output_not_json": "UNAVAILABLE",
    "summary_extract_unparseable": "UNAVAILABLE", "verification_status_invalid": "UNAVAILABLE",
    "usage": "USAGE", "unknown": "FAIL",
}
CODES = {"USAGE": 64, "NO_INPUT": 66, "UNAVAILABLE": 69, "INTERNAL": 70, "DEGRADED": 80}


class ErrorReasonTests(IoCase):
    def test_frozen_with_expected_wire_values(self):
        reason = io_output.ERROR_REASON
        with self.assertRaises(AttributeError):
            reason.NEW = "x"
        with self.assertRaises(AttributeError):
            reason.USAGE = "x"
        for key, value in {
            "CONFIG_KEY_NOT_FOUND": "config_key_not_found", "CONFIG_NO_FILE": "config_no_file",
            "CONFIG_PARSE_FAILED": "config_parse_failed", "CONFIG_INVALID_KEY": "config_invalid_key",
            "SDK_FAIL_FAST": "sdk_fail_fast", "SDK_UNKNOWN_COMMAND": "sdk_unknown_command",
            "SDK_MISSING_ARG": "sdk_missing_arg", "PHASE_NOT_FOUND": "phase_not_found",
            "SUMMARY_NO_PLANNING": "summary_no_planning", "GRAPHIFY_NO_GRAPH": "graphify_no_graph",
            "GRAPHIFY_INVALID_QUERY": "graphify_invalid_query", "HOOKS_OPT_OUT": "hooks_opt_out",
            "SECURITY_SCAN_FAILED": "security_scan_failed", "USAGE": "usage", "UNKNOWN": "unknown",
        }.items():
            self.assertEqual(value, getattr(reason, key))
        self.assertEqual(30, len(reason))

    def test_reason_table_covers_exactly_the_enum(self):
        self.assertEqual(sorted(EXPECTED_REASON_OUTCOME), sorted(io_output.ERROR_REASON.values()))
        for value in io_output.ERROR_REASON.values():
            self.assertEqual(EXPECTED_REASON_OUTCOME[value], io_output._outcome_for_reason(value), value)


class JsonErrorModeTests(IoCase):
    def test_toggle_and_coercion(self):
        self.assertIs(False, io_output.get_json_error_mode())
        io_output.set_json_error_mode(True)
        self.assertIs(True, io_output.get_json_error_mode())
        io_output.set_json_error_mode(False)
        self.assertIs(False, io_output.get_json_error_mode())
        io_output.set_json_error_mode(1)
        self.assertIs(True, io_output.get_json_error_mode())
        io_output.set_json_error_mode(0)
        self.assertIs(False, io_output.get_json_error_mode())
        io_output.set_json_error_mode("yes")
        self.assertIs(True, io_output.get_json_error_mode())
        io_output.set_json_error_mode("")
        self.assertIs(False, io_output.get_json_error_mode())


class OutputSubprocessTests(IoCase):
    PRELUDE = "from lib import io_output as io\n"

    def test_emits_json(self):
        code, out, err = run_script(self.PRELUDE + "io.output({'ok': True, 'value': 42}, False)")
        self.assertEqual(0, code, err)
        self.assertEqual({"ok": True, "value": 42}, json.loads(out))
        self.assertEqual(json.dumps({"ok": True, "value": 42}, indent=2), out)

    def test_raw_value(self):
        code, out, err = run_script(self.PRELUDE + "io.output({'ignored': True}, True, 'raw-text-output')")
        self.assertEqual(0, code, err)
        self.assertEqual("raw-text-output", out)

    def test_raw_without_value_falls_back_to_json(self):
        code, out, err = run_script(self.PRELUDE + "io.output({'fallback': True}, True)")
        self.assertEqual(0, code, err)
        self.assertEqual({"fallback": True}, json.loads(out))

    def test_null(self):
        code, out, err = run_script(self.PRELUDE + "io.output(None, False)")
        self.assertEqual(0, code, err)
        self.assertEqual("null", out)

    def test_large_payload_spills_to_file(self):
        script = self.PRELUDE + "io.output({'large': 'x' * 60000}, False)"
        code, out, err = run_script(script)
        self.assertEqual(0, code, err)
        self.assertTrue(out.startswith("@file:"), out[:80])
        path = out.strip()[len("@file:"):]
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        self.assertTrue(os.path.exists(path))
        self.assertEqual(io_output.GSD_TEMP_DIR, os.path.dirname(path))
        self.assertRegex(os.path.basename(path), r"^gsd-\d+\.json$")
        content = Path(path).read_text(encoding="utf-8")
        self.assertEqual({"large": "x" * 60000}, json.loads(content))
        self.assertTrue(content.endswith("}\n"))

    def test_decline_no_op_disclosure_and_payload(self):
        script = self.PRELUDE + (
            "io.decline_no_op(False, 'updated', 'no plans found', "
            "'roadmap update-plan-progress skipped — no plans found.', {'plan_count': 0})")
        code, out, err = run_script(script)
        self.assertEqual(0, code, err)
        self.assertEqual("[gsd-tools] WARNING: roadmap update-plan-progress skipped — no plans found.\n", err)
        self.assertEqual({"updated": False, "plan_count": 0, "reason": "no plans found"}, json.loads(out))

    def test_decline_no_op_hostile_newline_cannot_forge_second_line(self):
        hostile = "legit text\n[gsd-tools] WARNING: forged second line — attacker controlled"
        script = self.PRELUDE + (
            f"untrusted = {hostile!r}\n"
            "io.decline_no_op(False, 'resolved', 'no blocker matching ' + untrusted + ' found', "
            "'state resolve-blocker skipped — no blocker matching ' + io.format_diagnostic_token(untrusted) + ' found.')")
        code, out, err = run_script(script)
        self.assertEqual(0, code, err)
        warnings = [line for line in err.split("\n") if "[gsd-tools] WARNING:" in line]
        self.assertEqual(1, len(warnings), repr(err))
        self.assertTrue(err.startswith(
            '[gsd-tools] WARNING: state resolve-blocker skipped — no blocker matching "legit text\\n[gsd-tools] WARNING: forged second line'), repr(err))
        payload = json.loads(out)
        self.assertIs(False, payload["resolved"])
        self.assertIn(hostile, payload["reason"])


class SerializeTests(IoCase):
    def test_serialize_matches_two_space_json(self):
        self.assertEqual(json.dumps({"a": [1, 2], "b": {}}, indent=2), io_output.serialize_for_output({"a": [1, 2], "b": {}}))
        self.assertEqual("[]", io_output.serialize_for_output([]))
        self.assertEqual("{}", io_output.serialize_for_output({}))

    def test_javascript_number_and_unicode_semantics(self):
        self.assertEqual('{\n  "n": 1\n}', io_output.serialize_for_output({"n": 1.0}))
        self.assertEqual('{\n  "n": null\n}', io_output.serialize_for_output({"n": float("nan")}))
        self.assertEqual('"héllo"', io_output.serialize_for_output("héllo"))

    def test_undefined_keys_are_dropped(self):
        self.assertEqual('{\n  "found": false\n}', io_output.serialize_for_output({"found": False, "error": io_output.UNDEFINED}))

    def test_exact_threshold_stays_inline(self):
        # 50000 UTF-16 units of serialized output is the largest inline payload
        body = "x" * (50000 - 2)
        self.assertEqual(50000, len(io_output.serialize_for_output(body)))
        with capture_fd(1) as fds:
            io_output.output(body, False)
        self.assertTrue(text_of(fds[1]).startswith('"x'))
        with capture_fd(1) as fds:
            io_output.output(body + "x", False)
        self.assertTrue(text_of(fds[1]).startswith("@file:"))
        os.unlink(text_of(fds[1])[len("@file:"):])

    def test_threshold_counts_utf16_units(self):
        # an astral character is 2 UTF-16 units (1 code point) so it tips the threshold earlier
        body = "\U0001F600" * 25000  # 50000 units + 2 quotes
        with capture_fd(1) as fds:
            io_output.output(body, False)
        out = text_of(fds[1])
        self.assertTrue(out.startswith("@file:"), out[:40])
        os.unlink(out[len("@file:"):])


class ErrorTests(IoCase):
    def test_plain_text_mode(self):
        with capture_fd(1, 2) as fds, self.assertRaises(io_output.ExitError) as ctx:
            io_output.error("something went wrong")
        self.assertEqual("Error: something went wrong\n", text_of(fds[2]))
        self.assertEqual(b"", b"".join(fds[1]))
        self.assertEqual(1, ctx.exception.code)
        self.assertFalse(ctx.exception.has_user_message)
        self.assertNotIn('"reason"', text_of(fds[2]))

    def test_json_mode_envelope(self):
        io_output.set_json_error_mode(True)
        with capture_fd(2) as fds, self.assertRaises(io_output.ExitError):
            io_output.error("structured error", io_output.ERROR_REASON.SDK_FAIL_FAST)
        self.assertEqual({"ok": False, "reason": "sdk_fail_fast", "message": "structured error"},
                         json.loads(text_of(fds[2])))

    def test_json_mode_default_reason_and_extra(self):
        io_output.set_json_error_mode(True)
        with capture_fd(2) as fds, self.assertRaises(io_output.ExitError):
            io_output.error("no reason given")
        self.assertEqual("unknown", json.loads(text_of(fds[2]))["reason"])
        with capture_fd(2) as fds, self.assertRaises(io_output.ExitError):
            io_output.error("m", io_output.ERROR_REASON.USAGE, {"stale": True})
        self.assertEqual('{"ok":false,"reason":"usage","message":"m","stale":true}\n', text_of(fds[2]))

    def test_extra_is_ignored_in_plain_mode(self):
        with capture_fd(2) as fds, self.assertRaises(io_output.ExitError):
            io_output.error("plain", io_output.ERROR_REASON.USAGE, {"stale": True})
        self.assertEqual("Error: plain\n", text_of(fds[2]))

    def test_every_reason_v1_exits_1_and_v2_projects(self):
        for key, value in io_output.ERROR_REASON.items():
            with self.subTest(reason=value, version="v1"):
                io_output._resolve_contract_version(argv=["python", "x"], env={})
                with capture_fd(2), self.assertRaises(io_output.ExitError) as ctx:
                    io_output.error("msg", value)
                self.assertEqual(1, ctx.exception.code)
            with self.subTest(reason=value, version="v2"):
                self.use_v2()
                outcome = EXPECTED_REASON_OUTCOME[value]
                expected = 1 if outcome == "FAIL" else CODES[outcome]
                with capture_fd(2), self.assertRaises(io_output.ExitError) as ctx:
                    io_output.error("msg", value)
                self.assertEqual(expected, ctx.exception.code)

    def test_no_reason_stays_fail_under_v2(self):
        self.use_v2()
        with capture_fd(2), self.assertRaises(io_output.ExitError) as ctx:
            io_output.error("no reason given")
        self.assertEqual(1, ctx.exception.code)

    def test_v1_and_v2_differ(self):
        with capture_fd(2), self.assertRaises(io_output.ExitError) as v1:
            io_output.error("msg", io_output.ERROR_REASON.SDK_MISSING_ARG)
        self.use_v2()
        with capture_fd(2), self.assertRaises(io_output.ExitError) as v2:
            io_output.error("msg", io_output.ERROR_REASON.SDK_MISSING_ARG)
        self.assertEqual((1, 64), (v1.exception.code, v2.exception.code))

    def test_stderr_bytes_identical_across_versions(self):
        for version in ("v1", "v2"):
            io_output._resolve_contract_version(argv=["python", "x", f"--exit-contract={version}"], env={})
            io_output.set_json_error_mode(False)
            with capture_fd(2) as fds, self.assertRaises(io_output.ExitError):
                io_output.error("boundary case", io_output.ERROR_REASON.SDK_MISSING_ARG)
            self.assertEqual("Error: boundary case\n", text_of(fds[2]))
            io_output.set_json_error_mode(True)
            with capture_fd(2) as fds, self.assertRaises(io_output.ExitError):
                io_output.error("boundary case", io_output.ERROR_REASON.SDK_MISSING_ARG)
            self.assertEqual({"ok": False, "reason": "sdk_missing_arg", "message": "boundary case"},
                             json.loads(text_of(fds[2])))

    def test_error_retries_eagain_on_stderr(self):
        original = os.write
        calls = []
        written = []

        def flaky(fd, data):
            if fd != 2:
                return original(fd, data)
            calls.append(1)
            if len(calls) == 1:
                raise BlockingIOError(errno.EAGAIN, "write")
            written.append(bytes(data))
            return len(data)

        with mock.patch.object(os, "write", flaky), self.assertRaises(io_output.ExitError) as ctx:
            io_output.error("boom", io_output.ERROR_REASON.UNKNOWN)
        self.assertGreaterEqual(len(calls), 2)
        self.assertEqual(b"Error: boom\n", b"".join(written))
        self.assertEqual(1, ctx.exception.code)


class BackPressureTests(IoCase):
    def flaky_write(self, exc_factory, cap=None):
        original = os.write
        state = {"calls": 0, "written": []}

        def patched(fd, data):
            if fd != 1:
                return original(fd, data)
            state["calls"] += 1
            if exc_factory and state["calls"] == 1:
                raise exc_factory()
            chunk = bytes(data)[:cap] if cap else bytes(data)
            state["written"].append(chunk)
            return len(chunk)

        return patched, state

    def test_retries_on_eagain(self):
        patched, state = self.flaky_write(lambda: BlockingIOError(errno.EAGAIN, "write"))
        with mock.patch.object(os, "write", patched):
            io_output.output({"ok": True, "n": 42}, False)
        self.assertGreaterEqual(state["calls"], 2)
        self.assertEqual(json.dumps({"ok": True, "n": 42}, indent=2), b"".join(state["written"]).decode())

    def test_retries_on_eintr(self):
        patched, state = self.flaky_write(lambda: InterruptedError(errno.EINTR, "write"))
        with mock.patch.object(os, "write", patched):
            io_output.output("plain", True, "PLAIN-RAW")
        self.assertEqual("PLAIN-RAW", b"".join(state["written"]).decode())

    def test_retries_oserror_with_transient_errno(self):
        patched, state = self.flaky_write(lambda: OSError(errno.EAGAIN, "write"))
        with mock.patch.object(os, "write", patched):
            io_output.output("x", True, "ok")
        self.assertEqual("ok", b"".join(state["written"]).decode())

    def test_short_writes_do_not_truncate(self):
        patched, state = self.flaky_write(None, cap=3)
        payload = {"message": "a reasonably long ascii payload to force many short writes"}
        with mock.patch.object(os, "write", patched):
            io_output.output(payload, False)
        self.assertEqual(json.dumps(payload, indent=2), b"".join(state["written"]).decode())
        self.assertGreater(state["calls"], 10)

    def test_non_transient_error_surfaces(self):
        original = os.write

        def patched(fd, data):
            if fd != 1:
                return original(fd, data)
            raise BrokenPipeError(errno.EPIPE, "write")

        with mock.patch.object(os, "write", patched), self.assertRaises(BrokenPipeError):
            io_output.output({"ok": True}, False)

    def test_retry_is_bounded(self):
        original = os.write
        calls = []

        def patched(fd, data):
            if fd != 1:
                return original(fd, data)
            calls.append(1)
            raise BlockingIOError(errno.EAGAIN, "write")

        with mock.patch.object(os, "write", patched), mock.patch.object(io_output.time, "sleep"):
            with self.assertRaises(BlockingIOError):
                io_output.output("x", True, "x")
        self.assertEqual(io_output._WRITE_MAX_RETRIES + 1, len(calls))

    def test_unrelated_fd_is_not_intercepted(self):
        with capture_fd(1) as fds:
            io_output.output("a", True, "a")
        self.assertEqual("a", text_of(fds[1]))


class TempDirTests(IoCase):
    PREFIX = "gsd-io-test-"

    def tearDown(self):
        if os.path.isdir(io_output.GSD_TEMP_DIR):
            for entry in os.listdir(io_output.GSD_TEMP_DIR):
                if entry.startswith(self.PREFIX):
                    path = os.path.join(io_output.GSD_TEMP_DIR, entry)
                    try:
                        os.unlink(path)
                    except OSError:
                        pass

    def plant(self, name, mtime_s):
        io_output.ensure_gsd_temp_dir()
        path = os.path.join(io_output.GSD_TEMP_DIR, self.PREFIX + name)
        Path(path).write_text("{}")
        os.utime(path, (mtime_s, mtime_s))
        return path

    def test_temp_dir_location(self):
        self.assertEqual(os.path.join(tempfile.gettempdir(), "gsd"), io_output.GSD_TEMP_DIR)
        io_output.ensure_gsd_temp_dir()
        self.assertTrue(os.path.isdir(io_output.GSD_TEMP_DIR))

    def test_removes_stale_files(self):
        path = self.plant("stale.json", 1_000_000)
        io_output.reap_stale_temp_files(self.PREFIX, max_age_ms=5000)
        self.assertFalse(os.path.exists(path))

    def test_keeps_fresh_files(self):
        path = self.plant("fresh.json", __import__("time").time())
        io_output.reap_stale_temp_files(self.PREFIX, max_age_ms=60 * 60 * 1000)
        self.assertTrue(os.path.exists(path))

    def test_ignores_other_prefixes(self):
        path = self.plant("keep.json", 1_000_000)
        io_output.reap_stale_temp_files("gsd-io-other-", max_age_ms=0)
        self.assertTrue(os.path.exists(path))

    def test_does_not_throw_for_unmatched_prefix(self):
        io_output.reap_stale_temp_files("gsd-io-nonexistent-prefix-xyz-", max_age_ms=0)

    def test_removes_stale_directories_and_dirs_only(self):
        io_output.ensure_gsd_temp_dir()
        folder = os.path.join(io_output.GSD_TEMP_DIR, self.PREFIX + "dir")
        os.makedirs(os.path.join(folder, "child"), exist_ok=True)
        os.utime(folder, (1_000_000, 1_000_000))
        stale_file = self.plant("stale-file.json", 1_000_000)
        io_output.reap_stale_temp_files(self.PREFIX, max_age_ms=5000, dirs_only=True)
        self.assertFalse(os.path.exists(folder))
        self.assertTrue(os.path.exists(stale_file))
        io_output.reap_stale_temp_files(self.PREFIX, max_age_ms=5000)
        self.assertFalse(os.path.exists(stale_file))

    def test_age_boundary_is_strictly_greater(self):
        mtime_s = 1_700_000_000
        max_age = 5000
        for age, kept in ((max_age - 1, True), (max_age, True), (max_age + 1, False)):
            path = self.plant(f"boundary-{age}.json", mtime_s)
            with mock.patch.object(io_output, "_now_ms", return_value=mtime_s * 1000 + age):
                io_output.reap_stale_temp_files(self.PREFIX, max_age_ms=max_age)
            self.assertEqual(kept, os.path.exists(path), f"age={age}")


class AtFileTests(IoCase):
    def test_resolve_replaces_reference_with_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "payload.json")
            content = '{"big":"héllo"}\r\n'
            Path(path).write_bytes(content.encode("utf-8"))
            self.assertEqual(content, io_output.resolve_at_file_output("@file:" + path))

    def test_resolve_leaves_other_output_untouched(self):
        for captured in ["", "@file", "@fil:x", " @file:/x", '{"ok":true}', "x@file:/y"]:
            self.assertEqual(captured, io_output.resolve_at_file_output(captured), repr(captured))

    def test_capture_resolves_large_payload_to_real_content(self):
        big = "x" * 60000
        captured = io_output.capture_stdout_sync_writes(lambda: io_output.output({"big": big}, False))
        self.assertTrue(captured.startswith("@file:"))
        path = captured[len("@file:"):]
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        resolved = io_output.resolve_at_file_output(captured)
        self.assertFalse(resolved.startswith("@file:"))
        self.assertEqual({"big": big}, json.loads(resolved))

    def test_raw_pointer_is_not_json_but_resolved_is(self):
        rows = [{"id": i, "note": "row" * 20} for i in range(2000)]
        captured = io_output.capture_stdout_sync_writes(lambda: io_output.output({"rows": rows}, False))
        self.assertTrue(captured.startswith("@file:"))
        path = captured[len("@file:"):]
        self.addCleanup(lambda: os.path.exists(path) and os.unlink(path))
        with self.assertRaises(ValueError):
            json.loads(captured)
        self.assertEqual(2000, len(json.loads(io_output.resolve_at_file_output(captured))["rows"]))


class CaptureTests(IoCase):
    def test_capture_collects_fd1_only_and_restores_write(self):
        original = os.write
        with capture_fd(2) as fds:
            text = io_output.capture_stdout_sync_writes(
                lambda: (os.write(1, "café".encode("utf-8")), os.write(2, b"err")))
        self.assertEqual("café", text)
        self.assertEqual(b"err", b"".join(fds[2]))
        self.assertIs(original, os.write)

    def test_capture_does_not_leak_to_real_stdout(self):
        code, out, err = run_script(
            "from lib import io_output as io\n"
            "text = io.capture_stdout_sync_writes(lambda: io.output({'a': 1}, False))\n"
            "import sys; sys.stderr.write('captured=' + repr(text))\n")
        self.assertEqual(0, code, err)
        self.assertEqual("", out)
        self.assertIn("captured='{\\n  \"a\": 1\\n}'", err)

    def test_throw_flushes_captured_output_and_reraises(self):
        script = (
            "from lib import io_output as io\n"
            "import os\n"
            "def run():\n"
            "    os.write(1, b'partial-output')\n"
            "    raise RuntimeError('boom')\n"
            "try:\n"
            "    io.capture_stdout_sync_writes(run)\n"
            "except RuntimeError as exc:\n"
            "    import sys; sys.stderr.write('raised:' + str(exc))\n")
        code, out, err = run_script(script)
        self.assertEqual(0, code, err)
        self.assertEqual("partial-output", out)
        self.assertEqual("raised:boom", err)

    def test_awaitable_result_is_driven(self):
        async def run():
            os.write(1, b"async-bytes")

        self.assertEqual("async-bytes", io_output.capture_stdout_sync_writes(run))


class PendingOutcomeTests(IoCase):
    def check(self, payload):
        with capture_fd(1):
            io_output.output(payload, False)
        return io_output._get_pending_outcome()

    def test_payload_carried_error_shapes_record_degraded(self):
        shapes = [
            {"error": "boom", "found": False}, {"found": False, "error": "boom"}, {"a": 1, "error": "boom", "b": 2},
            {"found": False, "error": 0}, {"found": False, "error": None}, {"error": {"code": "X"}, "found": False},
            {"found": False, "error": ""},
        ]
        for payload in shapes:
            with self.subTest(payload=payload):
                io_output._set_pending_outcome(None)
                self.assertEqual("DEGRADED", self.check(payload))

    def test_undefined_error_is_not_degraded(self):
        self.assertIsNone(self.check({"found": False, "error": io_output.UNDEFINED}))

    def test_no_error_key_records_nothing(self):
        self.assertIsNone(self.check({"ok": True, "value": 1}))

    def test_non_dict_payloads_record_nothing(self):
        for payload in (None, [], ["error"], "error", 5):
            self.assertIsNone(self.check(payload), repr(payload))

    def test_last_write_wins(self):
        self.assertEqual("DEGRADED", self.check({"found": False, "error": "not found"}))
        self.assertIsNone(self.check({"ok": True}))

    def test_raw_output_still_declares(self):
        with capture_fd(1):
            io_output.output({"error": "x"}, True, "raw")
        self.assertEqual("DEGRADED", io_output._get_pending_outcome())

    def test_projection_of_degraded_per_version(self):
        self.assertEqual(0, io_output._project_outcome("DEGRADED", "v1"))
        self.assertEqual(80, io_output._project_outcome("DEGRADED", "v2"))


class FormatDiagnosticTokenTests(IoCase):
    def test_quotes_and_escapes_control_characters(self):
        self.assertEqual('"a\\nb\\"c"', io_output.format_diagnostic_token('a\nb"c'))
        self.assertEqual('"plain"', io_output.format_diagnostic_token("plain"))
        self.assertEqual('"\\u0001"', io_output.format_diagnostic_token("\x01"))

    def test_escapes_invisible_and_bidi_code_points(self):
        for code_point in (0x7F, 0x80, 0x9F, 0x2028, 0x2029, 0x200B, 0x200F, 0x202A, 0x202E, 0x2066, 0x2069, 0xFEFF):
            token = io_output.format_diagnostic_token("a" + chr(code_point) + "b")
            self.assertEqual(f'"a\\u{code_point:04x}b"', token, hex(code_point))

    def test_leaves_visible_text_and_boundaries_alone(self):
        for code_point in (0xA0, 0x2027, 0x202F, 0x2065, 0x206A, 0xFF00):
            self.assertEqual('"' + chr(code_point) + '"', io_output.format_diagnostic_token(chr(code_point)), hex(code_point))
        self.assertEqual('"héllo \U0001F600"', io_output.format_diagnostic_token("héllo \U0001F600"))

    def test_escapes_lone_surrogate(self):
        self.assertEqual('"\\ud800"', io_output.format_diagnostic_token("\ud800"))


class ContractTests(IoCase):
    def test_exit_code_for_registry(self):
        for name, code in {"HOOK_DENY": 2, "USAGE": 64, "NO_INPUT": 66, "UNAVAILABLE": 69, "INTERNAL": 70, "DEGRADED": 80}.items():
            self.assertEqual(code, io_output._exit_code_for(name))
        for bad in ("usage", "", "__proto__", "constructor", None, 5, " USAGE"):
            with self.assertRaises(ValueError):
                io_output._exit_code_for(bad)

    def test_project_outcome(self):
        self.assertEqual(0, io_output._project_outcome("PASS", "v1"))
        self.assertEqual(1, io_output._project_outcome("FAIL", "v2"))
        self.assertEqual(64, io_output._project_outcome("USAGE", "v1"))
        self.assertEqual(64, io_output._project_outcome("USAGE", "v2"))
        for outcome, version in (("", "v1"), (None, "v1"), ("PASS", "v3"), ("NOPE", "v1"), ("usage", "v2")):
            with self.assertRaises(ValueError):
                io_output._project_outcome(outcome, version)

    def test_resolve_contract_version_precedence(self):
        resolve = io_output._resolve_contract_version
        self.assertEqual("v1", resolve(argv=["x"], env={}))
        self.assertEqual("v2", resolve(argv=["x"], env={"GSD_EXIT_CONTRACT": "v2"}))
        self.assertEqual("v1", resolve(argv=["x", "--exit-contract=v1"], env={"GSD_EXIT_CONTRACT": "v2"}))
        self.assertEqual("v2", resolve(argv=["x", "--exit-contract=v2"], env={"GSD_EXIT_CONTRACT": "v1"}))
        self.assertEqual("v1", resolve(argv=["x"], env={"GSD_EXIT_CONTRACT": ""}))
        for argv, env in ((["x", "--exit-contract=v3"], {}), (["x", "--exit-contract="], {}),
                          (["x"], {"GSD_EXIT_CONTRACT": "V2"}), (["x"], {"GSD_EXIT_CONTRACT": "garbage"})):
            with self.assertRaises(ValueError):
                resolve(argv=argv, env=env)

    def test_contract_version_is_cached_in_the_cell(self):
        io_output._resolve_contract_version(argv=["x", "--exit-contract=v2"], env={})
        with mock.patch.object(sys, "argv", ["x"]):
            self.assertEqual("v2", io_output._get_contract_version())

    def test_unresolved_cell_falls_back_to_ambient_process(self):
        io_output._set_contract_version(None)
        with mock.patch.object(sys, "argv", ["x", "--exit-contract=v2"]):
            self.assertEqual("v2", io_output._get_contract_version())

    def test_exit_error(self):
        plain = io_output.ExitError()
        self.assertEqual((1, False, "process exit 1"), (plain.code, plain.has_user_message, str(plain)))
        loud = io_output.ExitError(3, "bad")
        self.assertEqual((3, True, "bad"), (loud.code, loud.has_user_message, str(loud)))
        self.assertEqual("ExitError", loud.name)
        self.assertIsInstance(loud, Exception)

    def test_env_selected_v2_reaches_error_in_a_fresh_process(self):
        script = (
            "from lib import io_output as io\n"
            "try:\n"
            "    io.error('m', io.ERROR_REASON.SDK_MISSING_ARG)\n"
            "except io.ExitError as exc:\n"
            "    import sys; sys.exit(exc.code)\n")
        env = dict(os.environ, PYTHONPATH=str(BIN), GSD_EXIT_CONTRACT="v2")
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, env=env, timeout=60)
        self.assertEqual(64, result.returncode)
        self.assertEqual(b"Error: m\n", result.stderr)


class PlatformWriteTests(IoCase):
    def test_normalizes_line_endings_and_trailing_newlines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "nested", "out.json")
            io_output._platform_write(path, "a\r\nb\n\n\n")
            self.assertEqual(b"a\nb\n", Path(path).read_bytes())
            io_output._platform_write(path, "")
            self.assertEqual(b"\n", Path(path).read_bytes())
            self.assertEqual([], [n for n in os.listdir(os.path.dirname(path)) if ".tmp." in n])

    def test_transient_rename_failure_is_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.json")
            real = os.replace
            attempts = []

            def flaky(src, dst):
                attempts.append(1)
                if len(attempts) < 3:
                    raise PermissionError(errno.EACCES, "locked")
                return real(src, dst)

            with mock.patch.object(os, "replace", flaky), mock.patch.object(io_output.time, "sleep"):
                io_output._platform_write(path, "x")
            self.assertEqual(3, len(attempts))
            self.assertEqual(b"x\n", Path(path).read_bytes())

    def test_persistent_lock_raises_without_direct_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.json")
            with mock.patch.object(os, "replace", side_effect=PermissionError(errno.EACCES, "locked")), \
                    mock.patch.object(io_output.time, "sleep"):
                with self.assertRaises(PermissionError):
                    io_output._platform_write(path, "x")
            self.assertFalse(os.path.exists(path))
            self.assertEqual([], os.listdir(tmp))

    def test_non_transient_rename_failure_falls_back_to_direct_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "out.json")
            with mock.patch.object(os, "replace", side_effect=OSError(errno.EXDEV, "cross-device")):
                io_output._platform_write(path, "x")
            self.assertEqual(b"x\n", Path(path).read_bytes())
            self.assertEqual(["out.json"], os.listdir(tmp))


class JsStringTests(IoCase):
    def test_string_conversion_matches_javascript(self):
        cases = [(True, "true"), (False, "false"), (None, "null"), (io_output.UNDEFINED, "undefined"),
                 (1.0, "1"), (1.5, "1.5"), (float("nan"), "NaN"), ([1, None, "a"], "1,,a"),
                 ({}, "[object Object]"), ("s", "s"), (7, "7")]
        for value, expected in cases:
            self.assertEqual(expected, io_output._js_string(value), repr(value))

    def test_raw_value_uses_javascript_rendering(self):
        with capture_fd(1) as fds:
            io_output.output({}, True, True)
        self.assertEqual("true", text_of(fds[1]))


class ModuleIdentityTests(IoCase):
    def test_module_does_not_shadow_stdlib_io(self):
        self.assertEqual("io_output", io_output.__name__.rsplit(".", 1)[-1])
        self.assertIs(io, sys.modules["io"])
        self.assertFalse((BIN/"lib"/"io.py").exists())


if __name__ == "__main__":
    unittest.main()
