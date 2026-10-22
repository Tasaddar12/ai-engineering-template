"""Real Git/CLI packet behavior, including installed runtime namespace."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

RUNTIME = Path(__file__).resolve().parents[1] / ".ai/runtime/phase.py"


class WorkPacketTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.runtime = RUNTIME
        self.git("init", "-q")
        self.git("config", "user.name", "Packet Test")
        self.git("config", "user.email", "packet@example.invalid")
        self.write("constraints.md", "Acceptance: preserve every byte.\nSecurity: deny unauthenticated access.\n")
        self.git("add", "constraints.md")
        self.git("commit", "-qm", "input")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.bind()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.root, capture_output=True,
                              text=True, check=True).stdout

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def query(self, *args, ok=True):
        process = subprocess.run([sys.executable, str(self.runtime), "query", *args],
                                 cwd=self.root, capture_output=True, encoding="utf-8",
                                 env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertNotIn("Traceback", process.stderr)
        self.assertEqual(process.returncode, 0 if ok else 1, process.stdout + process.stderr)
        return json.loads(process.stdout)

    def bind(self):
        return self.query("handoff.write", "worker", "--reason", "turn-limit",
                          "--findings", "constraints.md:1 must preserve acceptance",
                          "--files-read", "constraints.md", "--remaining", "implement denial")

    def packet(self, *args, **kwargs):
        return self.query("handoff.packet", "worker", "--base", self.base,
                          "--sources", "constraints.md", *args, **kwargs)

    def test_valid_packet_preserves_full_security_sources_and_single_owner(self):
        handoff = self.root / ".planning/handoffs/worker.json"
        original = handoff.read_bytes()
        packet = self.packet()
        self.assertTrue(packet["dispatchable"])
        self.assertTrue(packet["reusable_context"])
        self.assertEqual(packet["input_revision"], self.base)
        source = packet["required_sources"][0]
        data = (self.root / "constraints.md").read_bytes()
        self.assertEqual(source["content"], data.decode())
        self.assertEqual(source["sha256"], hashlib.sha256(data).hexdigest())
        self.assertEqual(packet["remaining"], ["implement denial"])
        self.assertEqual(packet["unresolved_findings"][0]["status"], "context-only")
        self.assertEqual(handoff.read_bytes(), original)
        self.assertEqual(list((self.root / ".planning/handoffs").glob("*.json")), [handoff])

    def test_size_bound_counts_pretty_printed_utf8_success_envelope(self):
        self.write("constraints.md", "Acceptance: preserve caf\u00e9.\nSecurity: deny unauthenticated access.\n")
        command = [sys.executable, str(self.runtime), "query", "handoff.packet", "worker",
                   "--base", self.base, "--sources", "constraints.md"]
        def capture(*extra):
            # Keep binary stdout: text mode hides Windows CRLF expansion.
            return subprocess.run(command + list(extra), cwd=self.root, capture_output=True,
                                  env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        initial = capture()
        self.assertEqual(initial.returncode, 0, initial.stderr)
        packet = json.loads(initial.stdout)
        size = len(initial.stdout)
        expected = (json.dumps(packet, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        self.assertEqual(initial.stdout, expected)
        self.assertNotIn(b"\r\n", initial.stdout)
        accepted = capture("--max-bytes", str(size))
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertLessEqual(len(accepted.stdout), size)
        self.assertEqual(json.loads(accepted.stdout)["required_sources"], packet["required_sources"])
        rejected = capture("--max-bytes", str(size - 1))
        self.assertEqual(rejected.returncode, 1, rejected.stderr)
        self.assertEqual(json.loads(rejected.stdout)["code"], "packet-too-large")

    def test_oversized_packet_explicitly_fails_without_trimming_constraints(self):
        self.write("constraints.md", "Acceptance\n" + "S" * 70000 + "\nSecurity: deny access")
        result = self.packet(ok=False)
        self.assertEqual(result["code"], "packet-too-large")
        self.assertIn("constraints.md", result["error"])
        packet = self.packet("--max-bytes", "200000")
        self.assertTrue(packet["required_sources"][0]["content"].endswith("Security: deny access"))

    def test_missing_source_is_nondispatchable_and_keeps_required_refs(self):
        (self.root / "constraints.md").unlink()
        result = self.packet()
        self.assertFalse(result["dispatchable"])
        self.assertEqual(result["missing_inputs"], ["constraints.md"])
        self.assertFalse(result["reusable_context"])

    def test_dirty_input_invalidates_findings_and_rereads_full_content(self):
        self.write("constraints.md", "Security: require admin in addition to authentication")
        packet = self.packet()
        self.assertFalse(packet["reusable_context"])
        self.assertEqual(packet["unresolved_findings"][0]["status"], "unverified")
        self.assertIn("require admin", packet["required_sources"][0]["content"])

    def test_previously_read_dependency_is_included_even_when_not_relisted(self):
        self.write("dependency.md", "old dependency")
        self.query("handoff.write", "worker", "--findings", "dependency.md:1 old dependency",
                   "--files-read", "constraints.md", "dependency.md")
        self.write("dependency.md", "Security: dependency now requires a signed request")
        self.query("handoff.write", "worker", "--notes", "continuation remains pending")
        packet = self.packet()
        self.assertFalse(packet["reusable_context"])
        dependency = next(row for row in packet["required_sources"] if row["path"] == "dependency.md")
        self.assertIn("requires a signed request", dependency["content"])

    def test_new_revision_invalidates_reuse_and_reuses_mechanical_extractor(self):
        self.write("code.py", "deny = True")
        self.git("add", "code.py")
        self.git("commit", "-qm", "implementation")
        self.write("checks.json", json.dumps({"tested_revision": self.base,
                   "checks": [{"passed": False, "exit_code": 1, "receipt": "private/check.json"}]}))
        packet = self.packet("--evidence-file", "checks.json")
        self.assertFalse(packet["reusable_context"])
        self.assertEqual(packet["changes"]["changed_paths"], ["code.py"])
        fields = packet["reusable_evidence"]["fields"]
        self.assertEqual(fields["validation"], "recorded-only")
        self.assertEqual(fields["counts"]["failed"], 1)
        self.assertEqual(fields["checks"][0]["receipt"], "private/check.json")
        self.assertEqual(fields["batch"]["tested_revision"], self.base)
        self.assertEqual(packet["reusable_evidence"]["source_sha256"],
                         hashlib.sha256((self.root / "checks.json").read_bytes()).hexdigest())

    def test_legacy_or_partially_rebound_digest_never_blesses_saved_findings(self):
        path = self.root / ".planning/handoffs/worker.json"
        record = json.loads(path.read_text())
        del record["input_snapshot"]
        path.write_text(json.dumps(record))
        self.assertFalse(self.packet()["reusable_context"])
        self.bind()
        self.query("handoff.write", "worker", "--files-read", "constraints.md")
        self.assertFalse(self.packet()["reusable_context"])
        self.bind()
        self.query("handoff.write", "worker", "--findings", "--files-read", "constraints.md")
        self.assertFalse(self.packet()["reusable_context"])

    def test_invalid_arguments_and_path_escape_fail_closed(self):
        for args in (("--max-bytes", "0"), ("--max-bytes", "nope")):
            self.assertEqual(self.packet(*args, ok=False)["code"], "bad-packet-limit")
        result = self.query("handoff.packet", "worker", "--base", self.base,
                            "--sources", "../outside", ok=False)
        self.assertEqual(result["code"], "path-escape")
        result = self.query("handoff.packet", "worker", "--base", self.base, ok=False)
        self.assertEqual(result["code"], "missing-sources")

    def test_installed_namespace_supports_same_packet_contract(self):
        target = self.root / ".claude/runtime"
        shutil.copytree(RUNTIME.parent, target)
        self.runtime = target / "phase.py"
        self.bind()
        self.assertTrue(self.packet()["reusable_context"])


class ResultEmissionTests(unittest.TestCase):
    def test_emitter_overrides_crlf_translation_and_preserves_fallback_streams(self):
        specification = importlib.util.spec_from_file_location("packet_results", RUNTIME.parent / "lib/results.py")
        results = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(results)
        payload = {"ok": True, "constraint": "caf\u00e9\nSecurity: deny access"}
        expected = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        buffer = io.BytesIO()
        stream = io.TextIOWrapper(buffer, encoding="ascii", newline="\r\n")
        results.emit(payload, stream=stream)
        stream.flush()
        self.assertEqual(buffer.getvalue(), expected)
        fallback = io.StringIO()
        results.emit(payload, stream=fallback)
        self.assertEqual(fallback.getvalue().encode("utf-8"), expected)
        class Unconfigurable(io.StringIO):
            def reconfigure(self, **kwargs):
                raise ValueError("stream already read")
        fallback = Unconfigurable()
        results.emit(payload, stream=fallback)
        self.assertEqual(fallback.getvalue().encode("utf-8"), expected)


if __name__ == "__main__":
    unittest.main()
