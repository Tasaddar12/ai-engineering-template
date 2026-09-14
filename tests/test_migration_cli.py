"""Exercise migration through the downloaded-script CLI and recoverable backups."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

import test_install as support


class MigrationCliTests(unittest.TestCase):
    setUpClass = classmethod(support.InstallerTests.setUpClass.__func__)
    tearDownClass = classmethod(support.InstallerTests.tearDownClass.__func__)
    setUp = support.InstallerTests.setUp
    install = support.InstallerTests.install
    snapshot = support.InstallerTests.snapshot

    def seed_project(self):
        files = {
            ".ai/RULES.md": b"# Product engineering rules\nKeep the billing invariants.\n",
            ".ai/runtime/phase.py": b"# Previous installed runtime\n",
            ".ai/runtime/custom.py": b"print('custom worker')\n",
            ".ai/workers/worker.py": b"print('migrated custom worker')\n",
            ".ai/check.py": b"print('migrated custom check')\n",
            ".ai/custom-tool.sh": b"#!/bin/sh\necho migrated\n",
            ".ai/guides/local.md": b"# Product guide\nSee [rules](../RULES.md).\n",
            ".ai/assets/data.bin": b"\x00\xff\x80immutable custom data\r\n",
            ".planning/PROJECT.md": "# Cafe project\r\nApproved customer scope: café.\r\n".encode(),
            ".planning/STATE.md": b"# State\r\nActual delivery history.\r\n",
            ".planning/specs/SPEC-billing.md": b"# Billing\nNever lose invoice history.\n",
            ".planning/decisions/ADR-001.md": b"# Decision\nApproved payment provider.\n",
            ".planning/archive/01-SUMMARY.md": b"# Prior evidence\nOriginal .ai/runtime/phase.py revision abc123.\n",
            ".planning/config.yaml": b"# Keep this comment\nexecution:\n  worker_command: [python, .ai/workers/worker.py]\nverification:\n  commands: [[python, .ai/check.py]]\n",
            "AGENTS.md": b"# Product instructions\nKeep this customer rule.\n\n<!-- ai-engineering-template -->\nOld workflow entry\n<!-- /ai-engineering-template -->\n\nKeep this later note.\n",
            "README.md": b"# Existing product\n",
            ".gitignore": b"private-cache/\n.ai/private/\n.ai/agents\n.ai/commands\n",
        }
        for relative, content in files.items():
            path = self.target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return files

    def test_cli_migrates_both_hosts_and_verifies_recoverable_originals(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = self.base / host
                originals = self.seed_project()
                (self.target / ".ai/custom-tool.sh").chmod(0o755)
                before = self.snapshot()
                preview = self.install("--host", host, "--migrate-existing", "--dry-run")
                self.assertEqual(0, preview.returncode, preview.stderr)
                self.assertEqual(before, self.snapshot())
                self.assertFalse((self.target / ".workflow-backups").exists())
                result = self.install("--host", host, "--migrate-existing")
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertFalse((self.target / ".ai").exists())
                namespace = "." + host
                self.assertEqual(originals[".ai/assets/data.bin"], (self.target / namespace / "assets/data.bin").read_bytes())
                self.assertEqual(originals[".ai/runtime/custom.py"], (self.target / namespace / "runtime/custom.py").read_bytes())
                for relative, content in originals.items():
                    if relative.startswith(".planning/") and not relative.endswith("config.yaml"):
                        self.assertEqual(content, (self.target / relative).read_bytes(), relative)
                config = (self.target / ".planning/config.yaml").read_text(encoding="utf-8")
                self.assertIn("# Keep this comment", config)
                self.assertIn(namespace + "/workers/worker.py", config)
                import yaml
                routes = yaml.safe_load(config)
                self.assertIn("migrated custom worker", support.command(*routes["execution"]["worker_command"], cwd=self.target))
                self.assertIn("migrated custom check", support.command(*routes["verification"]["commands"][0], cwd=self.target))
                entry = (self.target / ("CLAUDE.md" if host == "claude" else "AGENTS.md")).read_text(encoding="utf-8")
                self.assertIn("Keep this customer rule.", entry)
                self.assertIn("Keep this later note.", entry)
                self.assertNotIn("Old workflow entry", entry)
                backups = list((self.target / ".workflow-backups").iterdir())
                self.assertEqual(1, len(backups))
                self.assertEqual((self.target / namespace / "custom-tool.sh").stat().st_mode & 0o777,
                                 (backups[0] / "files/.ai/custom-tool.sh").stat().st_mode & 0o777)
                manifest = json.loads((backups[0] / "MANIFEST.json").read_text(encoding="utf-8"))["sha256"]
                for relative, digest in manifest.items():
                    saved = (backups[0] / "files" / relative).read_bytes()
                    self.assertEqual(hashlib.sha256(saved).hexdigest(), digest)
                    self.assertEqual(originals[relative], saved)
                for relative in originals:
                    if relative != "README.md":
                        self.assertIn(relative, manifest)
                ignored = support.command("git", "check-ignore", ".workflow-backups/", cwd=self.target)
                self.assertIn(".workflow-backups/", ignored)
                self.assertIn(namespace + "/private/example", support.command(
                    "git", "check-ignore", namespace + "/private/example", cwd=self.target))
                for directory in ("roles", "workflows"):
                    expected = namespace + "/" + directory + "/private/example"
                    self.assertIn(expected, support.command("git", "check-ignore", expected, cwd=self.target))
                status = support.command(sys.executable, namespace + "/runtime/phase.py", "status", cwd=self.target)
                self.assertIn("No phases yet", status)

    def test_native_collision_leaves_all_originals_and_no_backup(self):
        self.seed_project()
        native = self.target / ".claude/RULES.md"
        native.parent.mkdir()
        native.write_bytes(b"An existing second workflow must not be overwritten.\n")
        before = self.snapshot()
        result = self.install("--host", "claude", "--migrate-existing")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.target / ".workflow-backups").exists())

    def test_failed_backup_never_changes_originals(self):
        originals = self.seed_project()
        obstruction = self.target / ".workflow-backups"
        obstruction.write_bytes(b"User-owned file\n")
        before = self.snapshot()
        result = self.install("--host", "codex", "--migrate-existing")
        self.assertNotEqual(0, result.returncode)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(originals[".ai/runtime/phase.py"], (self.target / ".ai/runtime/phase.py").read_bytes())


if __name__ == "__main__":
    unittest.main()
