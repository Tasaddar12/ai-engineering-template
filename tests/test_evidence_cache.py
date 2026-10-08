"""Source evidence reuse against real Git repositories and linked worktrees."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".ai" / "runtime"
sys.path.insert(0, str(RUNTIME))
from lib import evidence
from lib.results import VerbError


class EvidenceCase(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="source-evidence-"))
        self.repo = self.temp / "repo"
        self.repo.mkdir()
        self.addCleanup(self.cleanup)
        self.git("init", "-q")
        self.git("config", "user.name", "Evidence Test")
        self.git("config", "user.email", "evidence@example.test")
        self.git("config", "core.autocrlf", "false")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "input.txt").write_bytes(b"initial source\n")
        (self.repo / "config.json").write_bytes(b'{"setting":1}\n')
        (self.repo / ".gitignore").write_bytes(b"src/ignored.txt\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "initial")
        self.request = {"schema": evidence.SCHEMA, "task_class": "FACT_EXTRACTION",
                        "question": "What does the source say?", "source_revision": self.head(),
                        "inputs": ["src/input.txt", "config.json"], "scope": ["src/", "config.json"],
                        "acceptance": ["cite the source"],
                        "provenance": {"role": "scout", "model": "luna", "prompt_version": "v1"},
                        "config": {"mode": "strict"}, "status": "complete",
                        "outputs": {"answer": "initial source"},
                        "evidence": [{"claim": "source text", "citation": "src/input.txt:1",
                                      "excerpt": "initial source"}]}

    def cleanup(self):
        subprocess.run(["git", "worktree", "prune"], cwd=self.repo, capture_output=True)
        shutil.rmtree(self.temp, ignore_errors=True)

    def git(self, *args, cwd=None):
        result = subprocess.run(["git", *args], cwd=cwd or self.repo,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def head(self, cwd=None):
        return self.git("rev-parse", "HEAD", cwd=cwd)

    def store(self, request=None, cwd=None):
        return evidence.store(cwd or self.repo, request or self.request)

    def lookup(self, request=None, cwd=None):
        return evidence.lookup(cwd or self.repo, request or self.request)

    def cache(self):
        return self.repo / ".git" / "ai-phase" / "evidence" / "state.json"

    def test_store_revalidate_payload_and_no_working_tree_mutation(self):
        status = self.git("status", "--porcelain")
        original = copy.deepcopy(self.request)
        stored = self.store()
        result = self.lookup()
        self.assertTrue(result["reused"])
        self.assertEqual(result["artifact_id"], stored["artifact_id"])
        self.assertEqual(result["source_revision"], self.head())
        self.assertNotIn("outputs", result)
        rich = self.lookup(dict(self.request, include_payload=True))
        self.assertEqual(rich["outputs"], self.request["outputs"])
        self.assertEqual(rich["evidence"][0]["citation"], "src/input.txt:1")
        self.assertEqual(self.request, original)
        self.assertEqual(self.git("status", "--porcelain"), status)
        state = json.loads(self.cache().read_text())["state"]
        packet = state["packets"][stored["artifact_id"]]
        self.assertIn("sha256", packet["fingerprint"]["files"]["src/input.txt"])
        self.assertFalse(any(self.cache().parent.glob("*.tmp")))

    def test_byte_configuration_and_scope_inventory_invalidation(self):
        self.store()
        source = self.repo / "src" / "input.txt"
        source.write_bytes(b"changed source\n")
        self.assertIn("inputs-or-scope-changed", self.lookup()["reasons"])
        source.write_bytes(b"initial source\n")
        self.assertTrue(self.lookup()["reused"])
        config = self.repo / "config.json"
        config.write_bytes(b'{"setting":2}\n')
        self.assertFalse(self.lookup()["reused"])
        config.write_bytes(b'{"setting":1}\n')
        for name in ("new.txt", "ignored.txt"):
            with self.subTest(name=name):
                path = self.repo / "src" / name
                path.write_bytes(b"new\n")
                self.assertFalse(self.lookup()["reused"])
                path.unlink()
                self.assertTrue(self.lookup()["reused"])
        empty = self.repo / "src" / "empty"
        empty.mkdir()
        self.assertFalse(self.lookup()["reused"])
        empty.rmdir()
        source.unlink()
        result = self.lookup()
        self.assertFalse(result["reused"])
        self.assertIn("stale-evidence-input", result["reasons"])

    def test_ignored_and_untracked_inputs_are_hashed(self):
        for name in ("ignored.txt", "untracked.txt"):
            (self.repo / "src" / name).write_bytes(b"captured\n")
        request = copy.deepcopy(self.request)
        request["inputs"] += ["src/ignored.txt", "src/untracked.txt"]
        self.store(request)
        self.assertTrue(self.lookup(request)["reused"])
        for name in ("ignored.txt", "untracked.txt"):
            path = self.repo / "src" / name
            path.write_bytes(b"modified\n")
            self.assertFalse(self.lookup(request)["reused"])
            path.write_bytes(b"captured\n")
        self.git("add", "src/untracked.txt")
        self.assertTrue(self.lookup(request)["reused"])

    def test_contract_changes_cannot_reuse(self):
        self.store()
        changes = [{"question": "Different question"}, {"task_class": "SUMMARIZATION"},
                   {"acceptance": ["different acceptance"]}, {"config": {"mode": "loose"}},
                   {"provenance": dict(self.request["provenance"], prompt_version="v2")},
                   {"provenance": dict(self.request["provenance"], model="other")},
                   {"scope": ["src/input.txt", "config.json"]},
                   {"inputs": ["src/input.txt"]}]
        for change in changes:
            with self.subTest(change=change):
                self.assertIn("contract-changed", self.lookup(dict(self.request, **change))["reasons"])
        with self.assertRaises(VerbError):
            self.lookup(dict(self.request, schema="source-evidence/v2"))

    def test_revision_bound_default_and_complete_cross_revision_contract(self):
        old_revision = self.head()
        stored = self.store()
        cross = dict(self.request, reuse={"cross_revision": True, "complete_scope": True})
        reusable = self.store(cross)
        (self.repo / "unrelated.txt").write_bytes(b"unrelated\n")
        self.git("add", "unrelated.txt")
        self.git("commit", "-qm", "unrelated revision")
        current = dict(self.request, source_revision=self.head())
        self.assertIn("revision-changed", self.lookup(current)["reasons"])
        result = self.lookup(dict(cross, source_revision=self.head(), include_payload=True))
        self.assertTrue(result["reused"])
        self.assertEqual(result["source_revision"], old_revision)
        self.assertEqual(result["artifact_id"], reusable["artifact_id"])
        self.assertNotEqual(stored["artifact_id"], reusable["artifact_id"])
        with self.assertRaises(VerbError):
            self.lookup(self.request)
        with self.assertRaises(VerbError):
            self.store(dict(current, reuse={"cross_revision": True, "complete_scope": False}))

    def test_linked_worktree_reads_common_cache_but_revalidates_its_bytes(self):
        self.store()
        linked = self.temp / "linked"
        self.git("worktree", "add", "-q", "--detach", str(linked), self.head())
        self.assertTrue(self.lookup(cwd=linked)["reused"])
        (linked / "src" / "input.txt").write_bytes(b"other worktree\n")
        self.assertFalse(self.lookup(cwd=linked)["reused"])
        self.assertTrue(self.lookup()["reused"])

    def test_incomplete_and_failed_packets_are_preserved_not_reused(self):
        for status in ("incomplete", "blocked", "failed"):
            with self.subTest(status=status):
                result = self.store(dict(self.request, status=status))
                self.assertFalse(result["reusable"])
        self.assertEqual(len(json.loads(self.cache().read_text())["state"]["packets"]), 3)
        self.assertIn("packet-not-complete", self.lookup()["reasons"])

    def test_explicit_invalidation_survives_identical_store(self):
        stored = self.store()
        request = {"artifact_id": stored["artifact_id"], "reason": "evidence withdrawn"}
        self.assertTrue(evidence.invalidate(self.repo, request)["invalidated"])
        self.assertIn("explicitly-invalidated", self.lookup()["reasons"])
        self.assertFalse(self.store()["reusable"])
        self.assertFalse(self.lookup()["reused"])
        with self.assertRaises(VerbError):
            evidence.invalidate(self.repo, dict(request, artifact_id="a" * 64))

    def test_missing_or_incomplete_fields_and_invalid_json_reject(self):
        for field in ("schema", "task_class", "question", "source_revision", "inputs", "scope",
                      "acceptance", "provenance", "config", "status", "outputs", "evidence"):
            with self.subTest(field=field):
                request = copy.deepcopy(self.request)
                del request[field]
                with self.assertRaises(VerbError):
                    self.store(request)
        for bad in ('{', '{"schema":1,"schema":2}', '[]', '{"a":NaN}'):
            with self.assertRaises(VerbError):
                self.store(bad)
        for changes in ({"source_revision": "HEAD"}, {"inputs": []}, {"scope": ["src"]},
                        {"evidence": [{}]}, {"provenance": {"role": "scout"}},
                        {"inputs": ["not-in-scope"]}, {"include_payload": "true"}):
            with self.subTest(changes=changes), self.assertRaises(VerbError):
                if "include_payload" in changes:
                    self.lookup(dict(self.request, **changes))
                else:
                    self.store(dict(self.request, **changes))

    def test_corrupt_json_state_and_packet_digests_fail_closed(self):
        self.store()
        original = self.cache().read_bytes()
        self.cache().write_bytes(b"{truncated")
        self.assertIn("corrupt-evidence", self.lookup()["reasons"])
        with self.assertRaises(VerbError):
            self.store()
        self.cache().write_bytes(original)
        envelope = json.loads(original)
        packet = next(iter(envelope["state"]["packets"].values()))
        packet["outputs"]["answer"] = "tampered"
        # Even a recomputed state envelope cannot conceal a corrupt packet digest.
        envelope["digest"] = evidence._digest(envelope["state"])
        self.cache().write_text(json.dumps(envelope))
        self.assertIn("corrupt-evidence", self.lookup()["reasons"])

    def test_rehashed_incomplete_packet_is_rejected(self):
        self.store()
        envelope = json.loads(self.cache().read_bytes())
        packet = next(iter(envelope["state"]["packets"].values()))
        del packet["contract"]["provenance"]["prompt_version"]
        envelope["state"]["packets"] = {evidence._digest(packet): packet}
        envelope["digest"] = evidence._digest(envelope["state"])
        self.cache().write_text(json.dumps(envelope))
        self.assertIn("corrupt-evidence", self.lookup()["reasons"])

    def test_unsafe_paths_and_artifact_ids_reject(self):
        for path in ("../config.json", "/config.json", "C:/config.json", "src\\input.txt",
                     "src/../config.json", ".git/config", "src//input.txt", "src/NUL.txt",
                     "src/input.txt."):
            with self.subTest(path=path), self.assertRaises(VerbError):
                self.store(dict(self.request, inputs=[path]))
        for artifact_id in ("../state", "HEAD", "a" * 63):
            with self.assertRaises(VerbError):
                evidence.invalidate(self.repo, {"artifact_id": artifact_id, "reason": "unsafe"})

    def test_symlinks_in_scope_and_cache_reject(self):
        source = self.repo / "src" / "link.txt"
        try:
            source.symlink_to(self.repo / "config.json")
        except OSError as exc:
            self.skipTest("host cannot create symlinks: " + str(exc))
        with self.assertRaises(VerbError):
            self.store()
        source.unlink()
        cache = self.repo / ".git" / "ai-phase"
        outside = self.temp / "outside"
        outside.mkdir()
        cache.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(VerbError):
            self.store()
        self.assertEqual(list(outside.iterdir()), [])

    def test_concurrent_process_writers_preserve_every_packet_and_invalidation(self):
        stored = self.store()
        evidence.invalidate(self.repo, {"artifact_id": stored["artifact_id"], "reason": "withdrawn"})
        script = ("import json,sys; sys.path.insert(0,sys.argv[1]); from lib import evidence; "
                  "print(json.dumps(evidence.store(sys.argv[2],json.loads(sys.argv[3]))))")
        processes = []
        for index in range(8):
            request = dict(self.request, question="parallel question " + str(index))
            processes.append(subprocess.Popen([sys.executable, "-c", script, str(RUNTIME),
                                               str(self.repo), json.dumps(request)],
                                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
        for process in processes:
            stdout, stderr = process.communicate(timeout=45)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertTrue(json.loads(stdout)["reusable"])
        state = json.loads(self.cache().read_text())["state"]
        self.assertEqual(len(state["packets"]), 9)
        self.assertEqual(state["invalidations"][stored["artifact_id"]], "withdrawn")
        for index in range(8):
            self.assertTrue(self.lookup(dict(self.request, question="parallel question " + str(index)))["reused"])


if __name__ == "__main__":
    unittest.main()
