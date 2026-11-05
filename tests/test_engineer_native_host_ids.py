"""Offline real-Git contracts through both supported installed host runtimes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

try:
    from .test_engineer_runtime import RuntimeCase, SOURCE
    from . import test_installer_runtime as installer_tests
except ImportError:
    from test_engineer_runtime import RuntimeCase, SOURCE
    import test_installer_runtime as installer_tests


CANONICAL = "/root/acme_manager/acme_debugger"
SUMMARY = ".planning/phases/01-behavior/01-01-SUMMARY.md"


class InstalledHostContracts:
    """Pin current source using the same disposable snapshot as installer tests."""

    @classmethod
    def setUpClass(cls):
        installer_tests.CurrentInstallerTests.setUpClass.__func__(cls)
        cls.addClassCleanup(cls.source_temp.cleanup)

    def setUp(self):
        super().setUp()
        # Each test gets a real installation in its own adopting Git repository.
        result = subprocess.run([sys.executable, "-I", str(SOURCE/"bin/install.py"),
                                 "--source", str(self.source), "--ref", self.pin,
                                 "--target", str(self.root), "--host", self.host,
                                 "--local", "--no-hooks"], capture_output=True,
                                text=True, encoding="utf-8", timeout=120)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["complete"])
        self.runtime = self.root/("."+self.host)/"engineer/bin/engineer.py"
        self.env.pop("ENGINEER_HOST", None)  # Infer the host from the installed module.
        self.assertTrue(self.runtime.is_file())
        self.assertTrue((self.runtime.parent/"lib/worktrees.py").is_file())
        identity = self.cli("runtime-identity")
        self.assertEqual(self.host, identity["host"])
        self.assertEqual(self.root/("."+self.host), Path(identity["namespace"]))
        # Exports are fixture inputs, committed before capturing worker bases.
        self.git("add", ".")
        self.git("commit", "-m", "Install fixture runtime")

    def cli(self, *args, status=0, raw=False, stdin=None):
        result = subprocess.run([sys.executable, "-I", str(self.runtime), "query",
                                 *map(str, args)], cwd=self.root, env=self.env,
                                input=stdin, text=True, encoding="utf-8",
                                capture_output=True, timeout=30)
        self.assertEqual(status, result.returncode, result.stderr or result.stdout)
        output = result.stdout or result.stderr
        return output.strip() if raw else json.loads(output)

    def git(self, *args):
        return subprocess.run(["git", *map(str, args)], cwd=self.root, check=True,
                              text=True, encoding="utf-8", capture_output=True,
                              timeout=30).stdout.strip()

    def prepare(self, agent=CANONICAL):
        self.init_records()
        self.put(".gitignore", ".worktrees/\n")
        self.git("add", ".gitignore", ".planning")
        self.git("commit", "-m", "Capture coordinator inputs")
        self.git("switch", "-c", "integration/acme")
        worker = self.cli("worktree.create", "01-01", "--phase", "1",
                          "--base", "HEAD", "--files", "src/app.py")
        target = Path(worker["path"])
        (target/"src").mkdir()
        (target/"src/app.py").write_text("VALUE = 1\n", encoding="utf-8")
        document = target/SUMMARY
        document.parent.mkdir(parents=True)
        document.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\n---\nAcme result.\n',
                            encoding="utf-8")
        self.git("-C", target, "add", "src/app.py", SUMMARY)
        self.git("-C", target, "commit", "-m", "Implement fixture behavior")
        receipt = {"host": self.host, "source": "native-host", "status": "completed",
                   "agent_id": agent, "branch": worker["branch"],
                   "head": self.git("-C", target, "rev-parse", "HEAD"),
                   "worktree_path": worker["path"], "summary_path": SUMMARY}
        source = self.put(".git/host-receipts/acme.json", json.dumps(receipt)+"\n")
        args = ["01-01", "--phase", "1", "--base", worker["base"],
                "--branch", worker["branch"], "--path", worker["path"],
                "--files", "src/app.py", "--agent-id", agent,
                "--terminal-receipt", source]
        return worker, receipt, source, args

    def ownership_bytes(self, worker):
        return ((self.root/".git/engineer/worktree-ownership.json").read_bytes(),
                Path(worker["manifest"]).read_bytes())

    def assert_rejected(self, args, code):
        result = self.cli("worktree.record-agent", *args, status=1)
        self.assertEqual(code, result["error"])

    def test_canonical_receipt_is_unchanged_idempotent_and_mergeable(self):
        worker, receipt, source, args = self.prepare()
        raw = source.read_bytes()
        attached = self.cli("worktree.record-agent", *args)
        self.assertEqual(CANONICAL, attached["agent_id"])
        self.assertEqual(receipt, attached["worker"]["terminal_receipt"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         attached["worker"]["terminal_receipt_sha256"])
        captured = self.ownership_bytes(worker)
        repeated = self.cli("worktree.record-agent", *args)
        self.assertEqual(attached["worker"], repeated["worker"])
        self.assertEqual(captured, self.ownership_bytes(worker))
        self.assertEqual(raw, source.read_bytes())
        merged = self.cli("worktree.merge-wave", "--phase", "1")
        self.assertTrue(merged["wave_clean"])
        self.assertEqual(receipt["head"], self.git("rev-parse", "HEAD"))
        self.assertEqual("VALUE = 1\n", (self.root/"src/app.py").read_text())

    def test_mismatched_receipts_preserve_unbound_ownership(self):
        worker, receipt, source, args = self.prepare()
        before = self.ownership_bytes(worker)
        for field, value in (("agent_id", "acme_debugger"),
                             ("agent_id", "/root/other_manager/acme_debugger"),
                             ("branch", "integration/wrong"), ("head", worker["base"]),
                             ("worktree_path", str(self.root)), ("source", "summary"),
                             ("host", "unknown"), ("status", "running")):
            with self.subTest(field=field, value=value):
                source.write_text(json.dumps({**receipt, field: value}), encoding="utf-8")
                self.assert_rejected(args, "native-terminal-receipt-invalid")
                self.assertEqual(before, self.ownership_bytes(worker))
        source.write_text(json.dumps(receipt), encoding="utf-8")
        self.assert_rejected([*args, "--summary-path", "other-SUMMARY.md"],
                             "worker-summary-drift")
        self.assertEqual(before, self.ownership_bytes(worker))

    def test_exact_checkout_scope_and_manifest_ownership_remain_required(self):
        worker, receipt, source, args = self.prepare()
        before = self.ownership_bytes(worker)
        for option, value in (("--branch", "integration/wrong"),
                              ("--path", str(Path(worker["path"]).with_name("other"))),
                              ("--base", "HEAD~1"), ("--files", "src/other.py")):
            changed = list(args)
            changed[changed.index(option)+1] = value
            with self.subTest(option=option):
                self.assert_rejected(changed, "worker-already-owned")
                self.assertEqual(before, self.ownership_bytes(worker))
        path = Path(worker["manifest"])
        manifest = json.loads(path.read_bytes())
        manifest["worktrees"][0]["agent_id"] = "/root/other_manager/acme_debugger"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        conflicting = self.ownership_bytes(worker)
        self.assert_rejected(args, "manifest-ownership-drift")
        self.assertEqual(conflicting, self.ownership_bytes(worker))

    def test_bound_identity_and_receipt_cannot_be_replaced(self):
        worker, receipt, source, args = self.prepare()
        self.cli("worktree.record-agent", *args)
        before = self.ownership_bytes(worker)
        for agent in ("acme_debugger", "/root/other_manager/acme_debugger"):
            changed = list(args)
            changed[changed.index("--agent-id")+1] = agent
            source.write_text(json.dumps({**receipt, "agent_id": agent}), encoding="utf-8")
            self.assert_rejected(changed, "worker-already-owned")
            self.assertEqual(before, self.ownership_bytes(worker))
        source.write_text(json.dumps({**receipt, "status": "stopped"}), encoding="utf-8")
        self.assert_rejected(args, "worker-already-dispatched")
        self.assertEqual(before, self.ownership_bytes(worker))

    def test_stale_head_and_uncommitted_summary_still_block_integration(self):
        worker, receipt, source, args = self.prepare()
        self.cli("worktree.record-agent", *args)
        target = Path(worker["path"])
        self.git("-C", target, "rm", SUMMARY)
        self.git("-C", target, "commit", "-m", "Remove fixture summary after receipt")
        self.assert_rejected(args, "native-terminal-receipt-invalid")
        blocked = self.cli("worktree.merge-wave", "--phase", "1", status=1)
        self.assertEqual("native-terminal-receipt-stale", blocked["preserved"][0]["error"])
        self.assertFalse((self.root/"src/app.py").exists())

    def test_legacy_receipt_remains_supported(self):
        worker, receipt, source, args = self.prepare("acme-worker.42")
        attached = self.cli("worktree.record-agent", *args)
        self.assertEqual(receipt, attached["worker"]["terminal_receipt"])
        self.assertTrue(self.cli("worktree.merge-wave", "--phase", "1")["wave_clean"])

    def test_canonical_id_without_terminal_evidence_cannot_unlock_merge(self):
        worker, receipt, source, args = self.prepare()
        unproven = args[:-2]
        self.cli("worktree.record-agent", *unproven)
        self.assert_rejected([*unproven, "--completed"], "native-terminal-receipt-required")
        blocked = self.cli("worktree.merge-wave", "--phase", "1", status=1)
        self.assertEqual("worker-live-or-uncertain", blocked["preserved"][0]["error"])
        self.assertFalse((self.root/"src/app.py").exists())

    def test_missing_committed_summary_still_blocks(self):
        worker, receipt, source, args = self.prepare()
        target = Path(worker["path"])
        self.git("-C", target, "rm", SUMMARY)
        self.git("-C", target, "commit", "-m", "Remove required fixture summary")
        receipt["head"] = self.git("-C", target, "rev-parse", "HEAD")
        source.write_text(json.dumps(receipt), encoding="utf-8")
        self.cli("worktree.record-agent", *args)
        blocked = self.cli("worktree.merge-wave", "--phase", "1", status=1)
        self.assertEqual("worker-summary-uncommitted", blocked["preserved"][0]["error"])
        self.assertFalse((self.root/"src/app.py").exists())

    def test_out_of_scope_changes_still_block(self):
        worker, receipt, source, args = self.prepare()
        target = Path(worker["path"])
        (target/"src/unowned.py").write_text("VALUE = 2\n", encoding="utf-8")
        self.git("-C", target, "add", "src/unowned.py")
        self.git("-C", target, "commit", "-m", "Write outside assigned fixture scope")
        receipt["head"] = self.git("-C", target, "rev-parse", "HEAD")
        source.write_text(json.dumps(receipt), encoding="utf-8")
        self.cli("worktree.record-agent", *args)
        blocked = self.cli("worktree.merge-wave", "--phase", "1", status=1)
        self.assertEqual("worker-scope-violation", blocked["preserved"][0]["error"])
        self.assertFalse((self.root/"src/app.py").exists())

    def test_unapproved_actual_fork_base_is_rejected(self):
        worker, receipt, source, args = self.prepare()
        self.put("README.md", "# Acme coordinator advanced\n")
        self.git("add", "README.md")
        self.git("commit", "-m", "Advance coordinator after worker fork")
        self.git("-C", worker["path"], "merge", "--no-edit", self.git("rev-parse", "HEAD"))
        receipt["head"] = self.git("-C", worker["path"], "rev-parse", "HEAD")
        source.write_text(json.dumps(receipt), encoding="utf-8")
        before = self.ownership_bytes(worker)
        self.assert_rejected(args, "worker-fork-base-unapproved")
        self.assertEqual(before, self.ownership_bytes(worker))

    def test_unsafe_or_oversized_ids_are_rejected_without_mutation(self):
        worker, receipt, source, args = self.prepare()
        before = self.ownership_bytes(worker)
        invalid = ("", "/", "//root/acme", "/root//acme", "/root/acme/", "/root/./acme",
                   "/root/../acme", "/root/.acme", "root/acme", "root\\acme", "/root/acme name",
                   "/root/acme\n", "/root/acme\t", "/root/äcme", "/root/acme:worker",
                   "/root/acme%2Fworker", "/root/acme;worker", "/root/$(acme)",
                   "/root/"+"a"*155, "a"*161)
        for agent in invalid:
            changed = list(args)
            changed[changed.index("--agent-id")+1] = agent
            with self.subTest(agent=agent):
                self.assert_rejected(changed, "worker-agent-id-required")
                self.assertEqual(before, self.ownership_bytes(worker))

    def test_legacy_and_canonical_owners_remain_exact_despite_slug_collisions(self):
        self.put(".gitignore", ".worktrees/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "Ignore isolated fixture worktrees")
        agents = ("acme-worker.42", "A"+"a"*159, "/root/"+"a"*154,
                  CANONICAL, "root-acme-manager-acme-debugger",
                  "/root/acme-manager/acme_debugger")
        for index, agent in enumerate(agents):
            entry = self.cli("worktree.create", f"01-{index+1:02d}", "--phase", "1",
                             "--agent-id", agent, "--branch", f"isolation/acme-{index}")
            self.assertEqual(agent, entry["agent_id"])
        worker = self.cli("worktree.create", "02-01", "--phase", "2", "--agent-id", "/root/acme_one")
        failure = self.cli("worktree.create", "02-02", "--phase", "2", "--agent-id", "/root/acme-one", status=1)
        self.assertEqual("worker-already-owned", failure["error"])
        registry = json.loads((self.root/".git/engineer/worktree-ownership.json").read_bytes())
        self.assertEqual("/root/acme_one", registry["entries"][-1]["agent_id"])
        self.assertEqual(worker["path"], registry["entries"][-1]["path"])
        self.assert_rejected(["03-01", "--phase", "3", "--agent-id", CANONICAL,
                              "--branch", "isolation/duplicate"], "worker-already-owned")


class CodexNativeHostIds(InstalledHostContracts, RuntimeCase):
    host = "codex"


class ClaudeNativeHostIds(InstalledHostContracts, RuntimeCase):
    host = "claude"
