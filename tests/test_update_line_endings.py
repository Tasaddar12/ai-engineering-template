"""Conservative comparison metadata must never weaken reviewed-byte guards."""
import base64
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_install_update import git, load, seed_source

ROOT = Path(__file__).resolve().parents[1]
update = load("line_ending_update", ROOT / ".ai/update.py")
legacy = load("line_ending_legacy", ROOT / ".ai/install_update.py")
installer = update.installer


class ComparisonTests(unittest.TestCase):
    def test_conservative_comparison_matrix(self):
        cases = [
            (b"same\xff\x00\r", b"same\xff\x00\r", "unchanged"),
            (b"a\nb\n", b"a\r\nb\r\n", "line-ending-only"),
            (b"a\r\nb\n", b"a\nb\r\n", "line-ending-only"),
            ("caf\u00e9\r\n".encode(), "caf\u00e9\n".encode(), "line-ending-only"),
            (b"a\r\nb\r", b"a\nb\r", "substantive"),
            (b"\xff\r\n", b"\xff\n", "substantive"),
            (b"\x00\r\n", b"\x00\n", "substantive"),
            (b"a\n", b"b\n", "substantive"),
            (b"a\n", b"a", "substantive"),
            (b"a \n", b"a\n", "substantive"),
            (b"\xef\xbb\xbfa\r\n", b"a\n", "substantive"),
            (None, b"", "added"), (b"", None, "retired"),
            (b"", b"", "unchanged"), (None, None, "unchanged"),
        ]
        for current, candidate, expected in cases:
            with self.subTest(current=current, candidate=candidate):
                self.assertEqual(expected, legacy.compare_content(current, candidate))
                if current is not None and candidate is not None:
                    self.assertEqual(expected in ("unchanged", "line-ending-only"),
                                     legacy.same_text(current, candidate))

    def test_shell_and_nginx_attributes_apply_at_every_depth(self):
        with tempfile.TemporaryDirectory(prefix="line-ending-attrs-") as temporary:
            root = Path(temporary)
            git("init", "--quiet", cwd=root)
            shutil.copyfile(ROOT / ".gitattributes", root / ".gitattributes")
            names = ("run.sh", "nested/tools/run.sh", "nginx.conf",
                     "deep/config/nginx.conf", "nginx.conf.template",
                     "deep/templates/nginx.conf.template")
            output = git("check-attr", "text", "eol", "--", *names, cwd=root)
            actual = {}
            for line in output.splitlines():
                name, attribute, value = line.split(": ")
                actual[name, attribute] = value
            for name in names:
                self.assertEqual("set", actual[name, "text"], name)
                self.assertEqual("lf", actual[name, "eol"], name)


class ReviewedLineEndings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory(prefix="line-ending-source-")
        cls.source = Path(cls.fixture.name) / "source"
        cls.source.mkdir()
        seed_source(cls.source)
        git("config", "core.autocrlf", "false", cwd=cls.source)
        shutil.copyfile(ROOT / ".gitattributes", cls.source / ".gitattributes")
        (cls.source / ".ai/workflows/newlines.md").write_bytes(b"first\nsecond\n")
        (cls.source / ".ai/workflows/retired.md").write_bytes(b"retired\n")
        cls.lf_assets = {"hooks/line-ending-fixture.sh": b"#!/bin/sh\nprintf fixture\\n\n",
                         "fixtures/nginx.conf": b"events {}\nhttp {}\n",
                         "fixtures/nginx.conf.template": b"events {}\n# template\n"}
        for name, content in cls.lf_assets.items():
            path = cls.source / ".ai" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        cls.commit("baseline")
        cls.first = git("rev-parse", "HEAD", cwd=cls.source)
        cls.baseline = Path(cls.fixture.name) / "baseline"
        update.fetch(str(cls.source), cls.first, cls.baseline)
        rules = cls.source / ".ai/RULES.md"
        rules.write_bytes(rules.read_bytes() + b"\nSubstantive upstream fixture change.\n")
        (cls.source / ".ai/workflows/retired.md").unlink()
        (cls.source / ".ai/workflows/added.md").write_bytes(b"added\n")
        for name, content in cls.lf_assets.items():
            (cls.source / ".ai" / name).write_bytes(content + b"# reviewed LF update\n")
        cls.commit("upstream")
        cls.second = git("rev-parse", "HEAD", cwd=cls.source)

    @classmethod
    def commit(cls, message):
        git("add", ".", cwd=cls.source)
        git("-c", "user.name=Fixture", "-c", "user.email=test@example.invalid",
            "commit", "--quiet", "-m", message, cwd=cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="line-ending-target-")
        self.addCleanup(self.temporary.cleanup)
        self.target = Path(self.temporary.name) / "project"

    def install(self, host="codex"):
        result = subprocess.run([sys.executable, str(ROOT / ".ai/install.py"),
                                 "--source", str(self.source), "--ref", self.first,
                                 "--target", str(self.target), "--host", host,
                                 "--skip-deps", "--no-hooks"], capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        return self.target / ("." + host) / "update.py"

    def write(self, name, data):
        path = self.target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def snapshot(self):
        return {p.relative_to(self.target).as_posix(): p.read_bytes()
                for p in self.target.rglob("*") if p.is_file() and ".git" not in p.parts}

    def plan(self, host="codex", baseline=None):
        return update.build_plan(self.source, self.target, host, False, str(self.source),
                                 self.second, baseline or self.baseline)

    def row(self, plan, name):
        return next(e for e in plan["entries"] if e["path"] == name)

    def cli(self, entry, *arguments):
        return subprocess.run([sys.executable, "-X", "utf8", str(entry), *map(str, arguments)],
                              capture_output=True, text=True, encoding="utf-8")

    def test_installed_review_preview_is_read_only_and_distinguishes_changes(self):
        entry = self.install()
        self.write(".codex/workflows/newlines.md", b"first\r\nsecond\n")
        before = self.snapshot()
        saved = Path(self.temporary.name) / "review.json"
        result = self.cli(entry, "--target", self.target, "--source", self.source,
                          "--ref", self.second, "--no-hooks", "--plan", saved)
        self.assertEqual(0, result.returncode, result.stderr)
        plan = json.loads(saved.read_bytes())
        self.assertEqual(before, self.snapshot())
        self.assertIn("line-ending-only", result.stdout)
        self.assertIn("substantive", result.stdout)
        self.assertIn("Substantive upstream fixture change", result.stdout)
        row = self.row(plan, ".codex/workflows/newlines.md")
        self.assertEqual("line-ending-only", row["comparison"])
        self.assertEqual("customized", row["classification"])
        self.assertTrue(row["conflict"])
        self.assertEqual("added", self.row(plan, ".codex/workflows/added.md")["comparison"])
        self.assertEqual("retired", self.row(plan, ".codex/workflows/retired.md")["comparison"])

    def resolve(self, plan, replace_rules=False):
        for row in plan["entries"]:
            if row["conflict"]:
                replace = replace_rules and row["path"].endswith("/RULES.md")
                classification = ("upstream-managed" if replace else
                                  "customized" if row["classification"] == "unproven" else
                                  row["classification"])
                plan["resolutions"][row["path"]] = {
                    "action": "write" if replace else "keep", "classification": classification}
        return plan

    def assert_refused_without_mutation(self, plan, message="stale"):
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, message):
            update.apply_plan(plan, self.source, self.baseline)
        self.assertEqual(before, self.snapshot())

    def test_saved_metadata_and_schema_cannot_bypass_fresh_review(self):
        self.install()
        plan = self.resolve(self.plan())
        for field, value in (("comparison", "line-ending-only"),
                             ("candidate_comparison", "unchanged"),
                             ("candidate_base64", "dGFtcGVyZWQ="),
                             ("candidate_sha256", "0" * 64),
                             ("before_sha256", "0" * 64),
                             ("upstream_sha256", "0" * 64)):
            with self.subTest(field=field):
                forged = copy.deepcopy(plan)
                self.row(forged, ".codex/RULES.md")[field] = value
                self.assert_refused_without_mutation(forged)
        old = copy.deepcopy(plan)
        old["schema"] = 1
        self.assert_refused_without_mutation(old, "schema.*new plan")
        missing = copy.deepcopy(plan)
        del self.row(missing, ".codex/RULES.md")["comparison"]
        self.assert_refused_without_mutation(missing)

    def test_crlf_only_changes_to_each_reviewed_input_are_stale(self):
        self.install()
        paths = [self.target / ".codex/workflows/newlines.md",
                 self.source / ".ai/workflows/newlines.md",
                 self.baseline / ".ai/workflows/newlines.md",
                 self.target / ".codex/workflow-ownership.json"]
        for path in paths:
            with self.subTest(path=path.name):
                plan = self.resolve(self.plan())
                original = path.read_bytes()
                changed = original.replace(b"\r\n", b"\n")
                if changed == original:
                    changed = original.replace(b"\n", b"\r\n")
                self.assertNotEqual(original, changed)
                path.write_bytes(changed)
                try:
                    self.assert_refused_without_mutation(plan)
                finally:
                    path.write_bytes(original)

    def test_comparison_matrix_keeps_raw_candidates_and_ownership(self):
        self.install()
        name = ".codex/workflows/newlines.md"
        incoming = b"first\nsecond\n"
        for current, expected in ((incoming, "unchanged"),
                                  (b"first\r\nsecond\r\n", "line-ending-only"),
                                  (b"first\r\nsecond\n", "line-ending-only"),
                                  (b"first\nsecond", "substantive"),
                                  (b"first \nsecond\n", "substantive"),
                                  (b"first\rsecond\n", "substantive"),
                                  (b"\xfffirst\r\nsecond\n", "substantive"),
                                  (b"\x00first\r\nsecond\n", "substantive"),
                                  (b"", "substantive"), (None, "added")):
            with self.subTest(current=current):
                path = self.target / name
                if current is None:
                    path.unlink()
                else:
                    path.write_bytes(current)
                row = self.row(self.plan(), name)
                self.assertEqual(expected, row["comparison"])
                self.assertEqual(update.digest(current), row["before_sha256"])
                self.assertEqual(update.digest(incoming), row["candidate_sha256"])
                self.assertEqual(incoming, base64.b64decode(row["candidate_base64"]))
                if expected in ("line-ending-only", "substantive"):
                    self.assertEqual("customized", row["classification"])
                    self.assertTrue(row["conflict"])
        row = self.row(self.plan(), ".codex/workflows/retired.md")
        self.assertEqual("retired", row["comparison"])
        self.assertEqual("keep", row["action"])
        self.assertTrue(row["conflict"])
        retired = self.target / row["path"]
        retired.unlink()
        missing = self.row(self.plan(), row["path"])
        self.assertEqual("unchanged", missing["comparison"])
        self.assertIsNone(missing["before_sha256"])
        self.assertIsNone(missing["candidate_sha256"])
        # A restored retirement still requires an explicit eligible resolution.
        retired.write_bytes(b"retired\n")
        removal = self.resolve(self.plan())
        removal["resolutions"][row["path"]] = {
            "action": "remove", "classification": "upstream-managed"}
        update.apply_plan(removal, self.source, self.baseline)
        self.assertFalse(retired.exists())
        backup = list((self.target / ".workflow-backups").glob("*/files/.codex/workflows/retired.md"))
        self.assertEqual(1, len(backup))
        self.assertEqual(b"retired\n", backup[0].read_bytes())

    def test_legacy_skip_and_substantive_refresh_use_strict_helper(self):
        self.install()
        name = ".codex/workflows/newlines.md"
        for current, skipped in ((b"first\r\nsecond\n", True),
                                 (b"\x00first\r\nsecond\n", False),
                                 (b"\xfffirst\r\nsecond\n", False),
                                 (b"first\r\nsecond\r", False)):
            self.write(name, current)
            changes, backups, notes = legacy.plan_update(
                self.source, self.target, "codex", False, installer, previous=self.baseline)
            self.assertEqual(skipped, self.target / name not in dict(changes))
            if skipped:
                self.assertTrue(any("Line-ending-only" in note and name in note for note in notes))
            else:
                self.assertIn(self.target / name, backups)

    def test_normalized_equality_does_not_prove_missing_or_invalid_ownership(self):
        self.install()
        self.write(".codex/workflows/newlines.md", b"first\r\nsecond\n")
        manifest_path = self.target / ".codex/workflow-ownership.json"
        original = manifest_path.read_bytes()
        manifest_path.unlink()
        plan = self.plan()
        row = self.row(plan, ".codex/workflows/newlines.md")
        self.assertEqual("line-ending-only", row["comparison"])
        self.assertEqual("unproven", row["classification"])
        self.assert_refused_without_mutation(plan, "Unresolved conflict")
        manifest = json.loads(original)
        manifest["files"][row["path"]]["classification"] = "line-ending-only"
        manifest_path.write_bytes(installer.json_bytes(manifest))
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "Invalid ownership"):
            self.plan()
        self.assertEqual(before, self.snapshot())

    def test_project_and_generated_comparison_does_not_hide_protection(self):
        self.install()
        project = ".planning/PROJECT.md"
        raw = installer.payload(self.source, "codex", False)[project]
        self.write(project, raw.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
        entry = self.target / "AGENTS.md"
        content = entry.read_bytes()
        self.write("AGENTS.md", content.replace(installer.AGENT_END.encode(),
                                              b"Local instruction.\n" + installer.AGENT_END.encode()))
        plan = self.plan()
        row = self.row(plan, project)
        self.assertEqual("line-ending-only", row["comparison"])
        self.assertEqual("unchanged", row["candidate_comparison"])
        self.assertEqual("project", row["classification"])
        self.assertEqual("keep", row["action"])
        self.assertTrue(self.row(plan, "AGENTS.md")["conflict"])
        self.resolve(plan)
        plan["resolutions"]["AGENTS.md"]["action"] = "write"
        self.assert_refused_without_mutation(plan, "generated-file conflict")
        self.write(".planning/config.yaml", b"workflow:\n  isolation: invalid\n")
        invalid = self.resolve(self.plan())
        self.assert_refused_without_mutation(invalid, "invalid project configuration")

    def test_raw_concurrent_change_after_backup_is_refused(self):
        self.install()
        plan = self.resolve(self.plan())
        untouched = self.snapshot()
        real_backup = installer.backup_migration
        original = b"first\nsecond\n"
        changed = b"first\r\nsecond\n"
        def concurrent(target, paths):
            result = real_backup(target, paths)
            self.write(".codex/workflows/newlines.md", changed)
            return result
        with patch.object(installer, "backup_migration", side_effect=concurrent):
            with self.assertRaisesRegex(ValueError, "changed during backup"):
                update.apply_plan(plan, self.source, self.baseline)
        after = self.snapshot()
        for name, content in untouched.items():
            self.assertEqual(changed if name == ".codex/workflows/newlines.md" else content,
                             after[name], name)
        self.assertEqual(original, untouched[".codex/workflows/newlines.md"])
        self.assertTrue(any(name.startswith(".workflow-backups/") for name in after))

    def test_raw_source_change_after_backup_is_refused(self):
        self.install()
        plan = self.resolve(self.plan())
        before = self.snapshot()
        path = self.source / ".ai/workflows/newlines.md"
        original = path.read_bytes()
        real_backup = installer.backup_migration
        def concurrent(target, paths):
            result = real_backup(target, paths)
            path.write_bytes(original.replace(b"\n", b"\r\n"))
            return result
        try:
            with patch.object(installer, "backup_migration", side_effect=concurrent):
                with self.assertRaisesRegex(ValueError, "Source inputs changed during backup"):
                    update.apply_plan(plan, self.source, self.baseline)
        finally:
            path.write_bytes(original)
        after = self.snapshot()
        for name, content in before.items():
            self.assertEqual(content, after[name], name)
        self.assertTrue(any(name.startswith(".workflow-backups/") for name in after))

    def test_installed_both_hosts_apply_preserve_and_require_fresh_noop_review(self):
        for host in ("codex", "claude"):
            with self.subTest(host=host):
                self.target = Path(self.temporary.name) / host
                entry = self.install(host)
                root = "." + host
                preserved = {}
                for name in ("PROJECT", "STATE", "REQUIREMENTS", "ROADMAP"):
                    preserved[f".planning/{name}.md"] = f"# Authored {name}\r\nKeep bytes.\n".encode()
                for name in ("PLAN", "SUMMARY", "CONTEXT"):
                    preserved[f".planning/phases/01-project/01-{name}.md"] = b"authored\r\nmixed\n"
                preserved[root + "/rules/project-local.md"] = b"custom rule\r\n"
                preserved[".workflow-backups/prior/keep.bin"] = b"\x00\xffkeep\r\n"
                config = (self.target / ".planning/config.yaml").read_bytes()
                preserved[".planning/config.yaml"] = config + b"\nproject_value: authoritative\r\n"
                for name, content in preserved.items():
                    self.write(name, content)
                original_rules = (self.target / root / "RULES.md").read_bytes()
                original_rules = original_rules.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n") + b"local\n"
                self.write(root + "/RULES.md", original_rules)
                self.write(root + "/workflows/newlines.md", b"first\r\nsecond\n")
                saved = Path(self.temporary.name) / (host + "-review.json")
                result = self.cli(entry, "--target", self.target, "--source", self.source,
                                  "--ref", self.second, "--host", host, "--no-hooks", "--plan", saved)
                self.assertEqual(0, result.returncode, result.stderr)
                plan = self.resolve(json.loads(saved.read_bytes()), replace_rules=True)
                for name, content in self.lf_assets.items():
                    candidate = content + b"# reviewed LF update\n"
                    row = self.row(plan, root + "/" + name)
                    self.assertEqual(candidate, base64.b64decode(row["candidate_base64"]))
                    self.assertNotIn(b"\r", candidate)
                    self.assertEqual(update.digest(candidate), row["candidate_sha256"])
                saved.write_bytes(installer.json_bytes(plan))
                reviewed_raw = saved.read_bytes()
                reviewed_hash = update.digest(reviewed_raw)
                # Exact digest covers JSON newlines, metadata, candidate and resolutions.
                variants = [reviewed_raw.replace(b"\n", b"\r\n")]
                for mutation in ("comparison", "candidate_base64", "resolution"):
                    forged = copy.deepcopy(plan)
                    if mutation == "resolution":
                        forged["resolutions"][root + "/RULES.md"]["action"] = "keep"
                    else:
                        self.row(forged, root + "/RULES.md")[mutation] = "tampered"
                    variants.append(installer.json_bytes(forged))
                before = self.snapshot()
                for raw in variants:
                    saved.write_bytes(raw)
                    rejected = self.cli(entry, "--apply", saved, "--reviewed-plan-sha256", reviewed_hash)
                    self.assertNotEqual(0, rejected.returncode)
                    self.assertIn("exact --reviewed-plan-sha256", rejected.stderr)
                    self.assertEqual(before, self.snapshot())
                saved.write_bytes(reviewed_raw)
                applied = self.cli(entry, "--apply", saved, "--reviewed-plan-sha256", reviewed_hash)
                self.assertEqual(0, applied.returncode, applied.stderr)
                self.assertIn(root + "/RULES.md", json.loads(applied.stdout)["changed"])
                for name, content in preserved.items():
                    self.assertEqual(content, (self.target / name).read_bytes(), name)
                self.assertEqual(b"retired\n", (self.target / root / "workflows/retired.md").read_bytes())
                backups = list((self.target / ".workflow-backups").glob("*/files/" + root + "/RULES.md"))
                self.assertEqual(1, len(backups))
                self.assertEqual(original_rules, backups[0].read_bytes())
                manifest = update.load_manifest(self.target, host)
                self.assertEqual(self.second, manifest["current"]["revision"])
                self.assertEqual(self.first, manifest["previous"]["revision"])
                for name, record in manifest["files"].items():
                    self.assertEqual(update.digest((self.target / name).read_bytes()), record["installed_sha256"])
                for name, content in self.lf_assets.items():
                    candidate = content + b"# reviewed LF update\n"
                    self.assertEqual(candidate, (self.target / root / name).read_bytes())
                    self.assertEqual(update.digest(candidate), manifest["files"][root + "/" + name]["installed_sha256"])
                self.assertNotEqual(plan["manifest_sha256"], update.digest(
                    (self.target / root / "workflow-ownership.json").read_bytes()))
                after_apply = self.snapshot()
                stale = self.cli(entry, "--apply", saved, "--reviewed-plan-sha256", reviewed_hash)
                self.assertNotEqual(0, stale.returncode)
                self.assertIn("stale", stale.stderr)
                self.assertEqual(after_apply, self.snapshot())
                fresh = self.cli(entry, "--target", self.target, "--source", self.source,
                                 "--ref", self.second, "--host", host, "--no-hooks", "--plan", saved)
                self.assertEqual(0, fresh.returncode, fresh.stderr)
                fresh_plan = self.resolve(json.loads(saved.read_bytes()))
                saved.write_bytes(installer.json_bytes(fresh_plan))
                fresh_hash = update.digest(saved.read_bytes())
                self.assertNotEqual(reviewed_hash, fresh_hash)
                noop = self.cli(entry, "--apply", saved, "--reviewed-plan-sha256", fresh_hash)
                self.assertEqual(0, noop.returncode, noop.stderr)
                self.assertEqual([], json.loads(noop.stdout)["changed"])
                self.assertEqual(after_apply, self.snapshot())


if __name__ == "__main__":
    unittest.main()
