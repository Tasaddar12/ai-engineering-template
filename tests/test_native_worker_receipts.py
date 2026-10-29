"""Real Git lifecycle checks for attaching terminal native-host evidence."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
try:
    from .test_engineer_runtime import RuntimeCase
except ImportError:
    from test_engineer_runtime import RuntimeCase


class NativeWorkerReceipts(RuntimeCase):
    def test_documented_wave_commands_follow_the_owned_manifest(self):
        worker, receipt, source, arguments = self.prepared_worker()
        self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source)
        workflow = (Path(__file__).resolve().parents[1]/"engineer/workflows/execute-phase.md").read_text(encoding="utf-8")
        runtime = Path(__file__).resolve().parents[1]/"engineer/bin/engineer.py"
        sys.path.insert(0, str(runtime.parent))
        from lib.posix_shell import find_posix_shell
        shell = find_posix_shell()
        self.assertIsNotNone(shell)
        preamble = "\n".join([
            "set -e",
            "engineer_run() { "+shlex.quote(Path(sys.executable).as_posix())+" -I "+shlex.quote(runtime.as_posix())+' "$@"; }',
            "PHASE_NUMBER=999",
            "WAVE_WORKTREE_MANIFEST="+shlex.quote(Path(worker["manifest"]).as_posix()),
        ])
        for verb in ("merge-wave", "cleanup-wave"):
            command = next(line for line in workflow.splitlines() if line.startswith("engineer_run query worktree."+verb+" "))
            with tempfile.TemporaryDirectory(prefix="documented-wave-") as directory:
                script = Path(directory)/"fixture.sh"
                script.write_text(preamble+"\n"+command+"\n", encoding="utf-8")
                result = subprocess.run([shell, script.as_posix()], cwd=self.root, env=self.env,
                                        text=True, encoding="utf-8", capture_output=True, timeout=30)
            self.assertEqual(0, result.returncode, result.stderr or result.stdout)
            packet = json.loads(result.stdout)
            if verb == "merge-wave":
                self.assertTrue(packet["wave_clean"])
                self.assertEqual(receipt["head"], self.git("rev-parse", "HEAD"))
        self.assertEqual("VALUE = 1\n", (self.root/"src/app.py").read_text(encoding="utf-8"))
        self.assertFalse(Path(worker["path"]).exists())

    def prepared_worker(self):
        self.init_records()
        self.put(".gitignore", ".worktrees/\n")
        self.git("add", ".gitignore", ".planning")
        self.git("commit", "-m", "record fixture coordinator inputs")
        self.git("switch", "-c", "codex/integration")
        worker = self.cli("worktree.create", "01-01", "--phase", "1", "--base", "HEAD", "--files", "src/app.py")
        target = Path(worker["path"])
        source = target / "src/app.py"
        source.parent.mkdir(parents=True)
        source.write_text("VALUE = 1\n", encoding="utf-8")
        summary = ".planning/phases/01-behavior/01-01-SUMMARY.md"
        document = target / summary
        document.parent.mkdir(parents=True)
        document.write_text('---\nphase: "01"\nplan: "01"\nstatus: complete\n---\nImplemented source.\n', encoding="utf-8")
        self.git("-C", str(target), "add", "src/app.py", summary)
        self.git("-C", str(target), "commit", "-m", "implement worker source and summary")
        revision = self.git("-C", str(target), "rev-parse", "HEAD")
        # Fixture for actual host terminal metadata; branch/head/path come from real Git.
        receipt = {"host": "codex", "source": "native-host", "status": "completed", "agent_id": "native-worker-42",
                   "branch": worker["branch"], "head": revision, "worktree_path": worker["path"], "summary_path": summary}
        receipt_path = self.put(".git/host-receipts/worker.json", json.dumps(receipt))
        arguments = ("01-01", "--phase", "1", "--base", worker["base"], "--branch", worker["branch"],
                     "--path", worker["path"], "--files", "src/app.py", "--agent-id", receipt["agent_id"])
        return worker, receipt, receipt_path, arguments

    def test_create_record_terminal_receipt_and_merge(self):
        worker, receipt, source, arguments = self.prepared_worker()
        self.assertEqual("01-01", worker["agent_id"])
        self.cli("worktree.record-agent", *arguments)
        blocked = json.loads(self.cli("worktree.merge-wave", "--phase", "1", status=1, raw=True))
        self.assertEqual("worker-live-or-uncertain", blocked["preserved"][0]["error"])
        self.cli("worktree.record-agent", *arguments, "--completed", status=1, raw=True)
        attached = self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source)
        self.assertEqual(receipt["agent_id"], attached["agent_id"])
        self.assertEqual(receipt, attached["worker"]["terminal_receipt"])
        repeated = self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source)
        self.assertEqual(attached["worker"], repeated["worker"])
        registry = json.loads((self.root / ".git/engineer/worktree-ownership.json").read_text(encoding="utf-8"))
        manifest = json.loads(Path(attached["manifest"]).read_text(encoding="utf-8"))
        self.assertEqual(registry["entries"][0]["worker"], manifest["worktrees"][0]["worker"])
        self.assertEqual(receipt["agent_id"], manifest["worktrees"][0]["agent_id"])
        self.assertEqual(1, len(manifest["worktrees"]))
        merged = self.cli("worktree.merge-wave", "--phase", "1")
        self.assertTrue(merged["wave_clean"])
        self.assertEqual(1, len(merged["merged"]))
        self.assertEqual("VALUE = 1\n", (self.root / "src/app.py").read_text(encoding="utf-8"))
        self.assertEqual(receipt["head"], self.git("rev-parse", "HEAD"))

    def test_mismatched_receipts_and_ownership_cannot_unlock_worker(self):
        worker, receipt, source, arguments = self.prepared_worker()
        for field, value in (("agent_id", "different-host-worker"), ("branch", "codex/wrong"),
                             ("head", worker["base"]), ("worktree_path", str(self.root)),
                             ("source", "summary"), ("status", "running"), ("host", "unknown")):
            with self.subTest(field=field):
                source.write_text(json.dumps({**receipt, field: value}), encoding="utf-8")
                self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source, status=1, raw=True)
        source.write_text(json.dumps(receipt), encoding="utf-8")
        for option, value in (("--branch", "codex/wrong"), ("--path", str(Path(worker["path"]).with_name("other"))),
                              ("--base", "HEAD~1"), ("--files", "src/other.py")):
            changed = list(arguments)
            changed[changed.index(option)+1] = value
            with self.subTest(option=option):
                self.cli("worktree.record-agent", *changed, "--terminal-receipt", source, status=1, raw=True)
        blocked = json.loads(self.cli("worktree.merge-wave", "--phase", "1", status=1, raw=True))
        self.assertEqual("worker-live-or-uncertain", blocked["preserved"][0]["error"])
        self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source)
        source.write_text(json.dumps({**receipt, "status": "stopped"}), encoding="utf-8")
        self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source, status=1, raw=True)
        source.write_text(json.dumps({**receipt, "agent_id": "another-native-worker"}), encoding="utf-8")
        changed = list(arguments)
        changed[changed.index("--agent-id")+1] = "another-native-worker"
        self.cli("worktree.record-agent", *changed, "--terminal-receipt", source, status=1, raw=True)

    def test_conflicting_manifest_cannot_replace_ownership(self):
        worker, receipt, source, arguments = self.prepared_worker()
        manifest_path = Path(worker["manifest"])
        original = json.loads(manifest_path.read_text(encoding="utf-8"))
        for field, value in (("id", "another-entry"), ("agent_id", "prebound-other-host"),
                             ("files", ["src/other.py"])):
            manifest = json.loads(json.dumps(original))
            manifest["worktrees"][0][field] = value
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.subTest(field=field):
                self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source, status=1, raw=True)
        manifest_path.write_text(json.dumps(original), encoding="utf-8")
        attached = self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source)
        self.assertEqual(receipt["agent_id"], attached["agent_id"])

    def test_new_commits_require_fresh_stop_proof(self):
        worker, receipt, source, arguments = self.prepared_worker()
        self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source)
        target = Path(worker["path"])
        (target / "src/app.py").write_text("VALUE = 2\n", encoding="utf-8")
        self.git("-C", str(target), "add", "src/app.py")
        self.git("-C", str(target), "commit", "-m", "change source after terminal receipt")
        self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source, status=1, raw=True)
        blocked = json.loads(self.cli("worktree.merge-wave", "--phase", "1", status=1, raw=True))
        self.assertEqual("native-terminal-receipt-stale", blocked["preserved"][0]["error"])
        self.assertFalse((self.root / "src/app.py").exists())

    def test_terminal_receipt_does_not_replace_a_committed_summary(self):
        worker, receipt, source, arguments = self.prepared_worker()
        target = Path(worker["path"])
        self.git("-C", str(target), "rm", receipt["summary_path"])
        self.git("-C", str(target), "commit", "-m", "remove required worker summary")
        receipt["head"] = self.git("-C", str(target), "rev-parse", "HEAD")
        source.write_text(json.dumps(receipt), encoding="utf-8")
        self.cli("worktree.record-agent", *arguments, "--terminal-receipt", source)
        blocked = json.loads(self.cli("worktree.merge-wave", "--phase", "1", status=1, raw=True))
        self.assertEqual("worker-summary-uncommitted", blocked["preserved"][0]["error"])
        self.assertFalse((self.root / "src/app.py").exists())
