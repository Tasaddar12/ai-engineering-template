"""Subprocess contracts for the Python Engineer install/update/migrate scripts.

The legacy .ai installer suites intentionally exercise the previous layout.
These tests pin real copies of the current source layout and execute both the
source scripts and their installed copies without importing implementation code.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def run(*argv, cwd=None, input_text=None):
    return subprocess.run(list(map(str, argv)), cwd=cwd, capture_output=True,
                          text=True, encoding="utf-8", input=input_text, timeout=120)


def git(root, *args):
    result = run("git", "-C", root, *args)
    if result.returncode:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


def commit(root):
    git(root, "add", "--all")
    git(root, "-c", "user.name=Installer tests", "-c", "user.email=test@example.invalid",
        "commit", "--quiet", "-m", "Pinned fixture")
    return git(root, "rev-parse", "HEAD")


class PythonInstallScripts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory(prefix="engineer-source-")
        cls.source = Path(cls.fixture.name).resolve()
        for name in ("agents", "commands", "engineer", "hooks", "scripts", "skills", "bin"):
            shutil.copytree(ROOT / name, cls.source / name,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        git(cls.source, "init", "--quiet")
        cls.pin = commit(cls.source)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="engineer-cli-")
        self.addCleanup(self.temporary.cleanup)
        # Match canonical installer paths for expectations and fault injection.
        self.base = Path(self.temporary.name).resolve()
        self.target = self.base / "project caf\u00e9 with spaces"

    def cli(self, script="install", *args, installed=False, host="codex", source=None, pin=None):
        directory = self.target / ("." + host) / "bin" if installed else ROOT / "bin"
        return run(sys.executable, "-I", directory / (script + ".py"), *args)

    def context(self, host="codex", source=None, pin=None):
        return ["--source", source or self.source, "--ref", pin or self.pin,
                "--target", self.target, "--host", host, "--local"]

    def success(self, result):
        self.assertEqual(0, result.returncode, result.stderr[-4000:])
        return json.loads(result.stdout)

    def preview(self, script="update", host="codex", installed=False, **context):
        path = self.base / (script + "-" + host + ".json")
        packet = self.success(self.cli(script, *self.context(host, **context), "--plan", path,
                                       installed=installed, host=host))
        self.assertEqual([], packet["findings"])
        return path, json.loads(path.read_bytes())

    def apply(self, path, script="update", installed=False, host="codex", *args):
        token = hashlib.sha256(path.read_bytes()).hexdigest()
        return self.cli(script, "--apply", path, "--reviewed-plan-sha256", token, *args,
                        installed=installed, host=host)

    def test_source_and_installed_clis_export_complete_runnable_hosts(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.target = self.base / (host + " caf\u00e9 with spaces")
                self.target.mkdir()
                entry = self.target / ("CLAUDE.md" if host == "claude" else "AGENTS.md")
                entry.write_bytes(b"Keep customer instructions\r\n")
                settings = self.target / ("." + host) / ("settings.json" if host == "claude" else "config.toml")
                settings.parent.mkdir()
                settings.write_text('{"permissions":{"allow":["Read"]}}' if host == "claude"
                                    else 'model = "customer-model"\n', encoding="utf-8")
                installed = self.success(self.cli("install", *self.context(host), host=host))
                self.assertTrue(installed["complete"])
                self.assertTrue(entry.read_bytes().startswith(b"Keep customer instructions\r\n"))
                ns = self.target / ("." + host)
                identity = run(sys.executable, "-I", ns / "engineer/bin/engineer.py",
                               "query", "runtime-identity", "--pick", "packageName", "--raw", cwd=self.target)
                self.assertEqual(0, identity.returncode, identity.stderr)
                self.assertEqual("engineer-runtime", identity.stdout.strip())
                config = json.loads(settings.read_bytes()) if host == "claude" else tomllib.loads(settings.read_text())
                if host == "claude":
                    self.assertEqual(["Read"], config["permissions"]["allow"])
                else:
                    self.assertEqual("customer-model", config["model"])
                    role = tomllib.loads((ns / "agents/executor.toml").read_text(encoding="utf-8"))
                    self.assertIn("developer_instructions", role)
                hook = config["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
                self.assertIn("worktree-path-guard.py", hook)
                _, plan = self.preview(host=host, installed=True)
                self.assertTrue(all(e["action"] == "unchanged" for e in plan["entries"]))
                self.success(self.cli("install", *self.context(host), "--dry-run", installed=True, host=host))

    def test_actual_git_source_pin_installs_without_fixture_rewrites(self):
        pin = git(ROOT, "rev-parse", "HEAD")
        packet = self.success(self.cli("install", *self.context(source=ROOT, pin=pin)))
        self.assertEqual(pin, packet["revision"])
        self.assertTrue(packet["complete"])

    def test_reviewed_update_uses_immutable_pin_and_preserves_customizations(self):
        self.success(self.cli("install", *self.context()))
        source = self.base / "next source"
        git(self.base, "clone", "--quiet", "--local", self.source, source)
        command = source / "commands/progress.md"
        command.write_bytes(command.read_bytes() + b"\nPinned update evidence\n")
        pin = commit(source)
        custom = self.target / ".codex/commands/next.md"
        custom.write_bytes(b"Customer customization\r\n")
        path, plan = self.preview(installed=True, source=source, pin=pin)
        conflict = next(e for e in plan["entries"] if e["path"] == ".codex/commands/next.md")
        self.assertEqual("conflict", conflict["action"])
        command.write_bytes(b"Later source head must not leak\n")
        commit(source)
        applied = self.success(self.apply(path, installed=True))
        self.assertFalse(applied["complete"])
        self.assertEqual(pin, applied["revision"])
        self.assertEqual(b"Customer customization\r\n", custom.read_bytes())
        self.assertIn(b"Pinned update evidence", (self.target / ".codex/commands/progress.md").read_bytes())

    def test_preview_and_review_token_refuse_stale_target(self):
        self.success(self.cli("install", *self.context()))
        path, _ = self.preview()
        entry = self.target / "AGENTS.md"
        entry.write_bytes(entry.read_bytes() + b"User edit after review\n")
        result = self.apply(path)
        self.assertEqual(2, result.returncode)
        self.assertEqual("plan-drift", json.loads(result.stderr)["error"])
        self.assertTrue(entry.read_bytes().endswith(b"User edit after review\n"))
        result = self.cli("update", "--apply", path, "--reviewed-plan-sha256", "invalid")
        self.assertEqual("review-token-mismatch", json.loads(result.stderr)["error"])

    def test_selected_conflict_replacement_is_backed_up_and_rollback_restores(self):
        self.success(self.cli("install", *self.context()))
        custom = self.target / ".codex/commands/progress.md"
        custom.write_bytes(b"Customer bytes\r\n")
        path, plan = self.preview()
        name = ".codex/commands/progress.md"
        next(e for e in plan["entries"] if e["path"] == name)["resolution"] = "backup-and-replace"
        path.write_text(json.dumps(plan), encoding="utf-8")
        result = self.success(self.apply(path, "update", False, "codex", "--select", name))
        self.assertNotEqual(b"Customer bytes\r\n", custom.read_bytes())
        restored = self.success(self.cli("update", "--target", self.target, "--host", "codex",
                                          "--rollback", result["backup"]))
        self.assertTrue(restored["rolled_back"])
        self.assertEqual(b"Customer bytes\r\n", custom.read_bytes())

    def test_migration_copies_selected_custom_assets_and_preserves_originals(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.target = self.base / host
                originals = {".ai/RULES.md": b"Customer rules\r\n", ".ai/assets/data.bin": b"\x00\xffdata",
                             ".ai/runtime/custom.py": b"print('custom')\n",
                             ".ai/rules/local.md": b"See .ai/runtime/custom.py\n"}
                for name, data in originals.items():
                    path = self.target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                # A fresh installation must require deliberate migration first.
                blocked = self.cli("install", *self.context(host), host=host)
                self.assertEqual("export-blocked", json.loads(blocked.stderr)["error"])
                path, plan = self.preview("migrate", host)
                self.assertFalse((self.target / ("." + host)).exists())
                self.assertEqual("migration-selection-required", json.loads(self.apply(path, "migrate").stderr)["error"])
                selected = [value for e in plan["entries"] for value in ("--select", e["path"])]
                packet = self.success(self.apply(path, "migrate", False, host, *selected))
                ns = self.target / ("." + host)
                self.assertEqual(originals[".ai/RULES.md"], (ns / "RULES.md").read_bytes())
                self.assertEqual(originals[".ai/assets/data.bin"], (ns / "assets/data.bin").read_bytes())
                self.assertEqual(originals[".ai/runtime/custom.py"], (ns / "legacy/runtime/custom.py").read_bytes())
                self.assertIn(str(ns / "legacy/runtime").replace("\\", "/").encode(), (ns / "rules/local.md").read_bytes())
                for name, data in originals.items():
                    self.assertEqual(data, (self.target / name).read_bytes())
                journal = json.loads((Path(packet["backup"]) / "journal.json").read_bytes())
                self.assertEqual(set(originals), {e["path"] for e in journal["legacy_backups"]})
                # Installed migration is still runnable and previews the same originals.
                self.preview("migrate", host, installed=True)

    def test_non_utf8_legacy_text_is_reviewed_as_exact_bytes_and_rolls_back(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.target = self.base / host
                originals = {".ai/RULES.md": b"Customer rules: \x80\r\n",
                             ".ai/notes.txt": b"Customer notes: \xff\r\n",
                             ".ai/data.json": b'{"custom":"\x81"}\r\n'}
                for name, content in originals.items():
                    path = self.target / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(content)
                path, plan = self.preview("migrate", host)
                mapped = [e for e in plan["entries"] if e.get("legacy_path") in originals]
                self.assertEqual(len(originals), len(mapped))
                for entry in mapped:
                    self.assertEqual("no-text-transform", entry["text_transform"])
                    self.assertEqual("non-utf8-bytes", entry["text_transform_reason"])
                selected = [arg for e in mapped for arg in ("--select", e["path"])]
                applied = self.success(self.apply(path, "migrate", False, host, *selected))
                journal = json.loads((Path(applied["backup"]) / "journal.json").read_bytes())
                for entry in mapped:
                    expected = originals[entry["legacy_path"]]
                    self.assertEqual(expected, (self.target / entry["path"]).read_bytes())
                    self.assertEqual(expected, (self.target / entry["legacy_path"]).read_bytes())
                    saved = next(e for e in journal["legacy_backups"] if e["path"] == entry["legacy_path"])
                    self.assertEqual(expected, (Path(applied["backup"]) / saved["backup"]).read_bytes())
                self.success(self.cli("migrate", "--target", self.target, "--host", host,
                                      "--rollback", applied["backup"], host=host))
                for entry in mapped:
                    self.assertFalse((self.target / entry["path"]).exists())
                    self.assertEqual(originals[entry["legacy_path"]], (self.target / entry["legacy_path"]).read_bytes())

    def test_full_legacy_tree_migrates_then_updates_with_isolated_runnable_runtime(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                self.target = self.base / host
                shutil.copytree(ROOT / ".ai", self.target / ".ai",
                                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                originals = {p.relative_to(self.target).as_posix(): p.read_bytes()
                             for p in (self.target / ".ai").rglob("*") if p.is_file()}
                git(self.target, "init", "--quiet")
                path, plan = self.preview("migrate", host)
                legacy = [e for e in plan["entries"] if e.get("legacy_path")]
                self.assertEqual(set(originals), {e["legacy_path"] for e in legacy})
                runtime_entries = [e for e in legacy if e["legacy_path"].startswith(".ai/runtime/")]
                self.assertTrue(runtime_entries)
                self.assertTrue(all(e["path"].startswith("." + host + "/legacy/runtime/") for e in runtime_entries))
                migrated = self.success(self.apply(path, "migrate", False, host, "--select-all"))
                ns = self.target / ("." + host)
                self.assertTrue(migrated["complete"])
                manifest = json.loads((ns / "engineer-install/manifest.json").read_bytes())
                self.assertTrue(manifest["migration"]["complete"])
                journal = json.loads((Path(migrated["backup"]) / "journal.json").read_bytes())
                for saved in journal["legacy_backups"]:
                    self.assertEqual(originals[saved["path"]], (Path(migrated["backup"]) / saved["backup"]).read_bytes())
                for name, content in originals.items():
                    self.assertEqual(content, (self.target / name).read_bytes())
                # Old runtime modules absent from the new engine stay isolated.
                self.assertFalse((ns / "engineer/bin/lib/results.py").exists())
                for runtime in (ns / "engineer/bin/engineer.py", ns / "legacy/runtime/phase.py"):
                    # The old runtime retains its existing PyYAML dependency;
                    # only the new engine promises isolated standard-library use.
                    isolation = ["-I"] if runtime.name == "engineer.py" else []
                    result = self.success(run(sys.executable, *isolation, runtime, "query", "phases.list", cwd=self.target))
                    self.assertEqual([], result["phases"])
                cleanup = run(sys.executable, ns / "legacy/hooks/cleanup.py", "--help", cwd=self.target)
                self.assertEqual(0, cleanup.returncode, cleanup.stderr)
                self.assertIn("cleanup-preview", cleanup.stdout)
                for hook in (ns / "legacy/hooks/planning-integrity.py", ns / "hooks/worktree-path-guard.py"):
                    event = json.dumps({"cwd": str(self.target), "tool_name": "Read", "tool_input": {}})
                    hook_result = run(sys.executable, hook, cwd=self.target, input_text=event)
                    self.assertEqual(0, hook_result.returncode, hook_result.stderr)
                # Running retained source hooks may generate Python caches.
                # Disposable bytecode must neither migrate nor invalidate the
                # reviewed original source snapshot on a later pinned update.
                retained = run(sys.executable, self.target / ".ai/hooks/cleanup.py", "--help", cwd=self.target)
                self.assertEqual(0, retained.returncode, retained.stderr)
                cache = self.target / ".ai/runtime/__pycache__/custom.cpython-313.pyc"
                cache.parent.mkdir(parents=True, exist_ok=True)
                cache.write_bytes(b"Disposable generated bytes")
                extra_bytecode = self.target / ".ai/runtime/custom.pyo"
                extra_bytecode.write_bytes(b"Disposable bytecode outside cache directory")
                update_path, update = self.preview("update", host, installed=True)
                self.assertFalse(update["findings"])
                self.success(self.apply(update_path, "update", True, host))
                updated_manifest = json.loads((ns / "engineer-install/manifest.json").read_bytes())
                self.assertEqual(manifest["migration"], updated_manifest["migration"])
                _, repeated_migration = self.preview("migrate", host, installed=True)
                self.assertTrue(all(not e.get("legacy_path", "").endswith((".pyc", ".pyo"))
                                    for e in repeated_migration["entries"]))
                self.assertTrue(all(e["action"] in ("unchanged", "backup-only")
                                    for e in repeated_migration["entries"] if e.get("legacy_path")))
                # New edits to retained legacy files demand another reviewed migration.
                rules = self.target / ".ai/RULES.md"
                rules.write_bytes(rules.read_bytes() + b"\nUnreviewed legacy edit\n")
                refusal = self.success(self.cli("update", *self.context(host), "--dry-run", installed=True, host=host))
                self.assertIn("migration-required", [e["code"] for e in refusal["findings"]])

    def test_no_hooks_omits_registration_for_both_hosts(self):
        for host in ("claude", "codex"):
            self.target = self.base / host
            self.success(self.cli("install", *self.context(host), "--no-hooks", host=host))
            ns = self.target / ("." + host)
            if host == "claude":
                self.assertFalse((ns / "settings.json").exists())
            else:
                self.assertNotIn("hooks", tomllib.loads((ns / "config.toml").read_text()))

    def test_failed_write_rolls_back_selected_files_and_ownership(self):
        spec = importlib.util.spec_from_file_location("python_install_transaction", ROOT / "bin/install_support.py")
        support = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(support)
        plan = support.plan_update(self.source, self.pin, self.target, "codex")
        first = ".codex/commands/next.md"
        second = ".codex/commands/progress.md"
        original_atomic = support.atomic
        failed = False

        def fail_once(path, content, mode=0o644):
            nonlocal failed
            if path == self.target / second and not failed:
                failed = True
                raise OSError("Injected disk failure")
            return original_atomic(path, content, mode)

        with patch.object(support, "atomic", side_effect=fail_once):
            with self.assertRaisesRegex(OSError, "Injected disk failure"):
                support.apply(plan, [first, second])
        self.assertTrue(failed)
        self.assertFalse((self.target / first).exists())
        self.assertFalse((self.target / second).exists())
        self.assertFalse((self.target / ".codex/engineer-install/manifest.json").exists())
        journal = next((self.target / ".codex/engineer-install/backups").glob("*/journal.json"))
        self.assertEqual("rolled-back", json.loads(journal.read_bytes())["status"])

    def test_export_transform_preserves_non_shell_text_and_crlf(self):
        spec = importlib.util.spec_from_file_location("install_export_transform", ROOT / "bin/export_transforms.py")
        transforms = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(transforms)
        prose = "# Method\r\n\r\n```json\r\nnode -e 'JSON.parse(x).coverage.applicable'\r\n```\r\n"
        shell = '```bash\r\nnode "$UI_PROBE_JS" "$ELEMENTS_JSON"\r\n```\r\n'
        unknown = "```sh\r\nnode -e 'require(\"fs\").unlinkSync(\"customer-file\")'\r\n```\r\n"
        runtime = str(ROOT / "engineer/bin/engineer.py")
        exported = transforms.transform(prose + shell + unknown, "engineer/workflows/ui-phase.md", runtime)
        self.assertTrue(exported.startswith(prose))
        self.assertTrue(exported.endswith(unknown))
        self.assertIn('query spec.ui-probe --input "$ELEMENTS_JSON"', exported)
        self.assertNotIn('node "$UI_PROBE_JS"', exported)
        self.assertEqual(exported.count("\n"), exported.count("\r\n"))

    def test_export_transform_json_reader_generated_command_executes(self):
        spec = importlib.util.spec_from_file_location("install_export_json", ROOT / "bin/export_transforms.py")
        transforms = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(transforms)
        source = '''node -e "const v=JSON.parse(require('fs').readFileSync(0,'utf8')); console.log(v.coverage.applicable)"'''
        exported = transforms.transform(source, "scripts/coverage.sh", str(ROOT / "engineer/bin/engineer.py"))
        self.assertNotIn("node -e", exported)
        arguments = shlex.split(exported)
        arguments[0] = sys.executable
        result = run(*arguments, input_text='{"coverage":{"applicable":7}}')
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("7", result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
