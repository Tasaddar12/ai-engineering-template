"""Existing target proof and provider bytes; no reconciliation API or live provider."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    from .test_artifacts import _load
    from .test_engineer_runtime import RuntimeCase, SOURCE
    from . import test_installer_runtime as installer_tests
except ImportError:
    from test_artifacts import _load
    from test_engineer_runtime import RuntimeCase, SOURCE
    import test_installer_runtime as installer_tests

security = _load("security_tracking")
ORIGIN = {"owner": "acme", "repository": "project", "hostname": "github.com"}
URL = "https://github.com/acme/project/issues/7"
KEY = "acme/project|control|unsafe-reuse"
ENTRY = {"id": "T-01-01", "key": KEY, "heading": "Exact risk",
         "canonical_url": "https://github.com/acme/project/issues/2#original"}
NATIVE = "engineer-risk-" + security._hash(KEY)


def html(*addresses, key=KEY):
    return ("".join('<p><a name="' + address + '"></a></p>' for address in addresses)
            + '<h3>Exact risk</h3><p>Canonical risk key: ' + key + '</p>')


class ExternalCanonicalTargets(unittest.TestCase):
    def render(self, body, entry=None):
        response = subprocess.CompletedProcess([], 0, json.dumps({"body_html": body}), "")
        with patch.object(security.repository, "require_url", return_value=7), \
                patch.object(security.issues, "provider", return_value=response):
            return security.rendered_targets(URL, [dict(ENTRY) if entry is None else entry], ORIGIN)

    def test_external_identity_selects_only_actual_unique_owned_native_address(self):
        for address in (NATIVE, "user-content-" + NATIVE):
            with self.subTest(address=address):
                entry = dict(ENTRY)
                self.assertEqual(({KEY: URL + "#" + address}, []),
                                 self.render(html("old-evidence-alias", address), entry))
                self.assertEqual(ENTRY, entry, "Reading checklist proof must preserve external identity")

    def test_ambiguous_missing_conflicting_and_wrong_key_proof_stays_pending(self):
        for body in (html("one", "two"), html(NATIVE, "user-content-" + NATIVE),
                     html(NATIVE, NATIVE), html(NATIVE, key="wrong-key"),
                     '<a name="' + NATIVE + '"></a><h3>Other owner</h3>' + html("alias", NATIVE)):
            with self.subTest(body=body):
                targets, pending = self.render(body)
                self.assertEqual({}, targets)
                self.assertTrue(pending)

    def test_same_issue_established_address_keeps_precedence(self):
        entry = {**ENTRY, "canonical_url": URL + "#old-evidence-alias"}
        self.assertEqual(({KEY: entry["canonical_url"]}, []),
                         self.render(html("old-evidence-alias", NATIVE), entry))
        self.assertEqual({}, self.render(html(NATIVE), entry)[0])

    def test_new_entry_authors_stable_declaration_without_claiming_provider_proof(self):
        entry = {**ENTRY, "plan": "01-01-PLAN.md", "threat_id": "T-01-01"}
        for field in ("aliases_occurrences", "owner", "scope_acceptance", "assessment_uncertainty",
                      "lifecycle_outcome", "next_action", "revision_check_evidence"):
            entry[field] = "Actual fixture evidence"
        body = security._entry_block(entry)
        self.assertIn('<a name="' + NATIVE + '"></a>\n### Exact risk', body)
        self.assertEqual(body, security._entry_block(entry))
        self.assertNotIn(URL + "#", body)
        self.assertEqual({}, self.render('<h3>Exact risk</h3><p>Canonical risk key: ' + KEY + '</p>')[0])


class ProviderBodyBytes(RuntimeCase):
    def test_ordinary_writer_preserves_reviewed_utf8_and_retry_does_not_repeat_effect(self):
        for index, payload in enumerate(("LF café\nsecond", "CRLF 雪\r\nsecond", "mixed\r\nnext\nlast\rfin")):
            with self.subTest(payload=payload):
                operation = {"key": "container:" + str(index), "body": payload, "title": "Exact title",
                             "labels": ["security-risk"], "action": "create", "url": None}
                preview = {"source_digest": "captured-source"}
                token_path = self.root / ("preview-" + str(index) + ".json")
                captured = []
                marker = '<!-- engineer-security-intent:' + security._hash(
                    {"origin": ORIGIN, "key": operation["key"]}) + ' -->'
                expected = payload.rstrip() + "\n\n" + marker + "\n"
                result = {"url": URL, "body": expected, "title": operation["title"],
                          "labels": operation["labels"], "state": "OPEN"}

                def provider(argv, origin):
                    captured.append(Path(argv[argv.index("--body-file") + 1]).read_bytes())
                    return subprocess.CompletedProcess(argv, 0, URL + "\n", "")

                with patch.dict(os.environ, self.env), \
                        patch.object(security, "_runtime_dir", return_value=self.root / "runtime"), \
                        patch.object(security.issues, "provider", side_effect=provider), \
                        patch.object(security.issues, "issue_get", return_value=result):
                    self.assertEqual(result, security._mutate(operation, {"origin": ORIGIN}, token_path, preview))
                    self.assertEqual(result, security._mutate(operation, {"origin": ORIGIN}, token_path, preview))
                self.assertEqual([expected.encode("utf-8")], captured)
                self.assertTrue(preview["consumed"])


INSTALLED_PROBE = """
import contextlib, importlib.util, json, pathlib, subprocess, sys
from unittest.mock import patch
runtime = pathlib.Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("required_installed_lib", runtime / "lib/__init__.py", submodule_search_locations=[str(runtime / "lib")])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
from required_installed_lib import security_tracking as security, models
packet = json.load(sys.stdin)
response = subprocess.CompletedProcess([], 0, json.dumps({"body_html": packet["html"]}), "")
with patch.object(security.repository, "require_url", return_value=7), patch.object(security.issues, "provider", return_value=response):
    targets, pending = security.rendered_targets(packet["url"], [packet["entry"]], packet["origin"])
fixture = pathlib.Path.cwd() / "ordinary-readback-fixture"
ctx = {"key": "phase:01", "id": "01", "kind": "phase", "origin": packet["origin"], "stable_identity": "fixture"}
entry = {**packet["entry"], "planned": True, "plan": "01-01-PLAN.md", "threat_id": "T-01-01", "aliases_occurrences": ["fixture-owner"]}
operation = {"key": "container:phase:01", "action": "create", "url": None, "body": "Reviewed fixture body", "title": "Fixture checklist", "labels": ["security-risk"]}
revision = "a" * 40
review = {"scope": ctx, "entries": [entry], "operations": [operation], "source_files": [], "source_digest": security.digest([]), "revision": revision, "ready": True, "pending": [], "title": operation["title"], "label": "security-risk"}
token = security._hash({key: review[key] for key in ("scope", "entries", "operations", "source_digest", "revision")})
preview_path = fixture / "previews" / (token + ".json")
saved = {**review, "token": token, "consumed": True, "results": [{"key": operation["key"], "url": packet["url"]}]}
security.write_json(preview_path, saved)
index_path = fixture / "index.json"
security.write_json(index_path, {"schema": 1, "risks": {entry["key"]: {"canonical_url": entry["canonical_url"]}}, "scopes": {}, "risk_intents": {}})
intent_key = security._hash({"origin": ctx["origin"], "key": operation["key"]})
body = operation["body"] + "\\n\\n<!-- engineer-security-intent:" + intent_key + " -->\\n"
security.write_json(fixture / "intents" / (intent_key + ".json"), {"state": "complete", "origin": ctx["origin"], "operation": {**operation, "body": body}, "url": packet["url"], "source_digest": review["source_digest"]})
issue = {"url": packet["url"], "title": operation["title"], "body": body, "state": "OPEN", "labels": operation["labels"]}
provider_calls = []
def provider(argv, origin):
    provider_calls.append(argv[0])
    assert argv[0] == "api", "Consumed ordinary registration must not write a provider"
    return response
with patch.object(security, "scope", return_value=ctx), patch.object(security, "_head", return_value=revision), patch.object(security, "_runtime_dir", return_value=fixture), patch.object(security, "_state", side_effect=lambda ctx: (index_path, security.load_json(index_path))), patch.object(security, "planning_lock", side_effect=contextlib.nullcontext), patch.object(security.repository, "require_url", return_value=7), patch.object(security.issues, "issue_get", return_value=issue), patch.object(security.issues, "provider", side_effect=provider):
    first = security.command(security.Args(["1", "--preview-token", token, "--publish"]), "threat-publish")
    second = security.command(security.Args(["1", "--preview-token", token, "--publish"]), "threat-publish")
risk = security.load_json(index_path)["risks"][entry["key"]]
print(json.dumps({"host": models.resolve_host(), "targets": targets, "pending": pending, "entry": packet["entry"], "registered_targets": second["targets"], "registration_ready": second["ready"], "canonical_url": risk["canonical_url"], "occurrences": len(risk["occurrences"]), "provider_calls": provider_calls, "reconciliation_api": hasattr(security, "_anchor_reconciliation")}))
"""


class InstalledReaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        installer_tests.CurrentInstallerTests.setUpClass.__func__(cls)
        cls.addClassCleanup(cls.source_temp.cleanup)

    def test_actual_claude_and_codex_exports_select_and_refuse_without_reconciliation_api(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host), tempfile.TemporaryDirectory(prefix="required-target-") as temporary:
                target = Path(temporary).resolve()
                install = subprocess.run([sys.executable, "-I", str(SOURCE / "bin/install.py"),
                                          "--source", str(self.source), "--ref", self.pin,
                                          "--target", str(target), "--host", host, "--local", "--no-hooks"],
                                         capture_output=True, text=True, encoding="utf-8", timeout=120)
                self.assertEqual(0, install.returncode, install.stderr)
                self.assertTrue(json.loads(install.stdout)["complete"])
                environment = dict(os.environ)
                environment.pop("ENGINEER_HOST", None)
                for body, expected in ((html("old-alias", NATIVE), {KEY: URL + "#" + NATIVE}),
                                       (html(NATIVE, "user-content-" + NATIVE), {}),
                                       (html(NATIVE, key="wrong-key"), {})):
                    packet = {"html": body, "entry": dict(ENTRY), "url": URL, "origin": ORIGIN}
                    probe = subprocess.run([sys.executable, "-I", "-c", INSTALLED_PROBE,
                                            str(target / ("." + host) / "engineer/bin")],
                                           input=json.dumps(packet), capture_output=True, text=True,
                                           encoding="utf-8", env=environment, cwd=target, timeout=30)
                    self.assertEqual(0, probe.returncode, probe.stderr)
                    actual = json.loads(probe.stdout)
                    self.assertEqual(host, actual["host"])
                    self.assertEqual(expected, actual["targets"])
                    self.assertEqual(not bool(expected), bool(actual["pending"]))
                    self.assertEqual(ENTRY, actual["entry"])
                    self.assertEqual(expected, actual["registered_targets"])
                    self.assertEqual(bool(expected), actual["registration_ready"])
                    self.assertEqual(ENTRY["canonical_url"], actual["canonical_url"])
                    self.assertEqual(1, actual["occurrences"])
                    self.assertEqual(["api", "api"], actual["provider_calls"])
                    self.assertFalse(actual["reconciliation_api"])
