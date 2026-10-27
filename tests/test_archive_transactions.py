"""Fresh byte-journal contracts, using actual isolated repositories and I/O."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"engineer/bin"))
from lib import archive
from lib.core import Args, Failure


class ArchiveTransactions(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        environment = patch.dict(os.environ, ENGINEER_ROOT=str(self.root))
        environment.start()
        self.addCleanup(environment.stop)
        self.source = self.root/".planning/quick/261027-001-fix"
        (self.source/"empty").mkdir(parents=True)
        (self.source/"binary.dat").write_bytes(b"\x00\xff\x10")
        (self.source/"QUICK.md").write_text("---\nstatus: complete\ncompleted: reviewed release\n---\n## Verification\n\nChecked the output against the approved acceptance cases.\n", encoding="utf-8")
        (self.root/".planning/reader.md").write_text("[record](quick/261027-001-fix/QUICK.md#verification)\n", encoding="utf-8")
        self.arguments = ["quick", self.source.name]

    def preview(self):
        return archive.archive(Args(self.arguments))

    def apply(self, preview=None):
        preview = preview or self.preview()
        return archive.archive(Args(self.arguments+["--apply", "--expect", preview["digest"]]))

    def recover(self, identifier):
        preview = archive.recover(Args([identifier]))
        return archive.recover(Args([identifier, "--apply", "--expect", preview["recoveryDigest"]]))

    def test_preview_is_read_only_and_apply_requires_exact_reviewed_inventory(self):
        before = archive._snapshot()
        preview = self.preview()
        self.assertEqual(preview, self.preview())
        self.assertEqual(before, archive._snapshot())
        self.assertFalse((self.root/".planning/archive").exists())
        (self.source/"new-empty").mkdir()
        with self.assertRaises(Failure) as caught:
            self.apply(preview)
        self.assertEqual("archive-preview-stale", caught.exception.code)
        self.assertTrue(self.source.exists())

    def test_apply_rebases_links_and_recovery_restores_bytes_and_empty_directory(self):
        before = archive._snapshot()
        packet = self.apply()
        destination = self.root/".planning/archive/quick"/self.source.name
        self.assertEqual(b"\x00\xff\x10", (destination/"binary.dat").read_bytes())
        self.assertTrue((destination/"empty").is_dir())
        self.assertIn("archive/quick/", (self.root/".planning/reader.md").read_text())
        self.recover(packet["recovery_id"])
        self.assertEqual(before, archive._snapshot())
        self.assertTrue((self.source/"empty").is_dir())
        self.assertEqual("already_recovered", archive.recover(Args([packet["recovery_id"], "--apply"]))["state"])

    def test_new_nested_empty_directory_prevents_overwrite_during_recovery(self):
        packet = self.apply()
        destination = self.root/".planning/archive/quick"/self.source.name
        (destination/"user-empty").mkdir()
        before = archive._snapshot()
        with self.assertRaises(Failure) as caught:
            archive.recover(Args([packet["recovery_id"]]))
        self.assertEqual("archive-recovery-conflict", caught.exception.code)
        self.assertEqual(before, archive._snapshot())

    def test_interrupted_byte_write_leaves_recoverable_journal_and_blocks_next_archive(self):
        before = archive._snapshot()
        original = archive.atomic_write
        calls = []
        def interrupted(path, content):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("injected storage interruption")
            return original(path, content)
        with patch.object(archive, "atomic_write", side_effect=interrupted):
            with self.assertRaises(Failure) as caught:
                self.apply()
        self.assertEqual("archive-interrupted", caught.exception.code)
        identifier = caught.exception.details["recovery_id"]
        with self.assertRaises(Failure) as blocked:
            self.preview()
        self.assertEqual("archive-pending", blocked.exception.code)
        self.recover(identifier)
        self.assertEqual(before, archive._snapshot())

    def test_corrupt_journal_is_rejected_before_any_record_write(self):
        packet = self.apply()
        path = self.root/".planning/archive/recovery"/(packet["recovery_id"]+".json")
        journal = json.loads(path.read_text())
        journal["changes"][0]["path"] = ".planning/PROJECT.md"
        path.write_text(json.dumps(journal))
        before = archive._snapshot()
        with self.assertRaises(Failure) as caught:
            archive.recover(Args([packet["recovery_id"], "--apply"]))
        self.assertEqual("bad-recovery-journal", caught.exception.code)
        self.assertEqual(before, archive._snapshot())
