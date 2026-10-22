"""Saved provider body behavior and trusted workflow boundary regressions."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import yaml
from publication_fixtures import pr_body

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github/scripts/validate_saved_pr.py"
spec = importlib.util.spec_from_file_location("validate_saved_pr", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def environment():
    return {"PHASE_PR_REPOSITORY": "owner/repository", "PHASE_PR_NUMBER": "42",
            "PHASE_PR_API_URL": "https://api.github.com", "PHASE_PR_TOKEN": "secret-token"}


def saved(body=None):
    return {"number": 42, "body": pr_body() if body is None else body,
            "updated_at": "2026-10-22T12:00:00Z",
            "head": {"sha": "a" * 40, "ref": "feature", "repo": {"id": 2}},
            "base": {"sha": "b" * 40, "ref": "main",
                     "repo": {"id": 1, "full_name": "owner/repository"}}}


class SavedBodyGate(unittest.TestCase):
    def validate(self, first, second=None, env=None):
        snapshots = iter([first, first if second is None else second])
        calls = []

        def reader(url, token):
            calls.append((url, token))
            return next(snapshots)

        result = gate.validate_saved(env or environment(), reader)
        self.assertEqual(calls, [("https://api.github.com/repos/owner/repository/pulls/42",
                                  "secret-token")] * 2)
        return result

    def test_saved_body_ignores_different_event_body(self):
        env = environment()
        env["GITHUB_EVENT_PATH"] = "unread-event-with-invalid-body.json"
        self.assertIn("passes", self.validate(saved(), env=env))

    def test_invalid_saved_body_fails_despite_valid_event_body(self):
        env = environment()
        env["GITHUB_EVENT_BODY"] = pr_body()
        with self.assertRaisesRegex(gate.GateError, "fails canonical"):
            self.validate(saved("invalid saved body"), env=env)

    def test_null_body_is_invalid(self):
        snapshot = saved()
        snapshot["body"] = None
        with self.assertRaisesRegex(gate.GateError, "fails canonical"):
            self.validate(snapshot)

    def test_shell_looking_body_only_reaches_parser_as_data(self):
        payload = pr_body().replace("Safe fixture detail", "$(touch /tmp/unsafe); `id`; ::error::data")
        with patch.object(gate, "validate_pr", wraps=gate.validate_pr) as parser:
            self.assertIn("passes", self.validate(saved(payload)))
        parser.assert_called_once_with(payload)

    def test_recheck_rejects_each_changed_snapshot_field(self):
        for field in ("body", "updated_at", "head-sha", "base-sha", "base-ref", "head-repo"):
            before = saved()
            after = copy.deepcopy(before)
            if field == "body":
                after[field] += "\nchanged"
            elif field == "updated_at":
                after[field] = "2026-10-22T12:00:01Z"
            else:
                side, key = field.split("-")
                after[side][key] = ({"id": 3} if key == "repo" else
                                    "c" * 40 if key == "sha" else "release")
            with self.subTest(field=field), self.assertRaisesRegex(gate.GateError, "changed during"):
                self.validate(before, after)

    def test_identity_and_malformed_snapshots_rejected(self):
        for path, value in ((["number"], 43), (["number"], True),
                            (["base", "repo", "full_name"], "other/repo"),
                            (["head", "sha"], "bad"), (["body"], {})):
            snapshot = saved()
            target = snapshot
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(gate.GateError):
                self.validate(snapshot)

    def test_bad_configuration_never_fetches(self):
        for key, value in (("PHASE_PR_NUMBER", "42/../issues"),
                           ("PHASE_PR_REPOSITORY", "owner/repo?access_token=x"),
                           ("PHASE_PR_REPOSITORY", "../repo"),
                           ("PHASE_PR_API_URL", "http://api.github.com"),
                           ("PHASE_PR_API_URL", "https://user:pass@api.github.com"),
                           ("PHASE_PR_API_URL", "https://api.github.com?token=x"),
                           ("PHASE_PR_TOKEN", "")):
            env = environment()
            env[key] = value
            with self.subTest(key=key), patch.object(gate, "fetch") as fetch:
                with self.assertRaises(gate.GateError):
                    gate.validate_saved(env, fetch)
                fetch.assert_not_called()

    def test_enterprise_api_path(self):
        env = environment()
        env["PHASE_PR_API_URL"] = "https://github.example/api/v3"
        self.assertEqual(gate.configuration(env)[0],
                         "https://github.example/api/v3/repos/owner/repository/pulls/42")

    def test_http_reads_are_bounded_authenticated_gets(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(saved()).encode()
        with patch.object(gate.request, "build_opener") as opener:
            opener.return_value.open.return_value = response
            self.assertEqual(gate.fetch("https://api.github.com/repos/o/r/pulls/1", "secret"), saved())
            req = opener.return_value.open.call_args.args[0]
            self.assertEqual(req.get_method(), "GET")
            self.assertEqual(req.get_header("Authorization"), "Bearer secret")
            self.assertEqual(opener.return_value.open.call_args.kwargs, {"timeout": 20})
            response.__enter__.return_value.read.assert_called_once_with(gate.MAX_RESPONSE + 1)
            self.assertIs(opener.call_args.args[0], gate.NoRedirect)

    def test_http_and_decoding_errors_exclude_response_and_token(self):
        for failure in (HTTPError("https://secret", 403, "private-body", {}, None),
                        URLError("secret-token private-body"), ValueError("private-body")):
            with self.subTest(failure=type(failure).__name__), patch.object(gate.request, "build_opener") as opener:
                opener.return_value.open.side_effect = failure
                with self.assertRaisesRegex(gate.GateError, "Provider read failed") as caught:
                    gate.fetch("https://api.github.com", "secret-token")
                self.assertNotIn("private-body", str(caught.exception))
                self.assertNotIn("secret-token", str(caught.exception))

    def test_oversized_response_fails_and_redirect_is_refused(self):
        response = unittest.mock.MagicMock()
        response.__enter__.return_value.read.return_value = b"x" * (gate.MAX_RESPONSE + 1)
        with patch.object(gate.request, "build_opener") as opener:
            opener.return_value.open.return_value = response
            with self.assertRaisesRegex(gate.GateError, "size limit"):
                gate.fetch("https://api.github.com", "secret")
        self.assertIsNone(gate.NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil"))

    def test_unexpected_exception_is_not_logged(self):
        output = io.StringIO()
        with patch.object(gate, "validate_saved", side_effect=RuntimeError("private-body secret-token")):
            with contextlib.redirect_stderr(output):
                self.assertEqual(gate.main(), 1)
        self.assertNotIn("private-body", output.getvalue())
        self.assertNotIn("secret-token", output.getvalue())

    def test_isolated_script_imports_without_dependencies(self):
        env = dict(os.environ)
        for key in environment():
            env.pop(key, None)
        result = subprocess.run([sys.executable, "-I", str(SCRIPT)], env=env,
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.strip(), "Invalid repository identity.")
        self.assertNotIn("Traceback", result.stderr)


class TrustedWorkflow(unittest.TestCase):
    def test_read_only_trusted_revision_and_environment_data_boundary(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/validate-saved-pr.yml").read_text(encoding="utf-8-sig"))
        events = workflow.get("on", workflow.get(True))
        self.assertEqual(events, {"pull_request_target": {"types": ["opened", "edited", "reopened",
                                                                  "synchronize", "ready_for_review"]}})
        self.assertEqual(workflow["permissions"], {"contents": "read", "pull-requests": "read"})
        self.assertEqual(list(workflow["jobs"]), ["saved-pr-body"])
        job = workflow["jobs"]["saved-pr-body"]
        self.assertNotIn("permissions", job)
        checkout, validate = job["steps"]
        self.assertEqual(checkout["uses"], "actions/checkout@v4")
        self.assertEqual(checkout["with"], {"ref": "${{ github.workflow_sha }}", "persist-credentials": False})
        self.assertEqual(validate["run"], "python3 -I .github/scripts/validate_saved_pr.py")
        self.assertEqual(validate["env"], {
            "PHASE_PR_TOKEN": "${{ github.token }}", "PHASE_PR_API_URL": "${{ github.api_url }}",
            "PHASE_PR_REPOSITORY": "${{ github.repository }}",
            "PHASE_PR_NUMBER": "${{ github.event.pull_request.number }}"})
        self.assertNotIn("env", workflow)
        self.assertNotIn("env", job)


if __name__ == "__main__":
    unittest.main()
