"""Regenerate project instructions through real offline installed runtimes."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    from . import test_installer_runtime as fixtures
except ImportError:
    import test_installer_runtime as fixtures


START = "<!-- engineer:managed:start -->"
END = "<!-- engineer:managed:end -->"


class InstalledInstructionRoots(unittest.TestCase):
    # Reuse the pinned, disposable source fixture, without inheriting its tests.
    setUpClass = classmethod(fixtures.CurrentInstallerTests.setUpClass.__func__)
    tearDownClass = classmethod(fixtures.CurrentInstallerTests.tearDownClass.__func__)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="engineer-instructions-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()

    def install(self, host, scope, external=False):
        target = self.base / (host + "-" + scope + " installed home")
        process = subprocess.run(
            [sys.executable, "-I", str(fixtures.CLI), "--source", str(self.source),
             "--ref", self.pin, "--target", str(target), "--host", host, "--" + scope],
            capture_output=True, text=True, encoding="utf-8", timeout=120)
        self.assertEqual(0, process.returncode, process.stderr or process.stdout)
        self.assertTrue(json.loads(process.stdout)["complete"])
        namespace = target / ("." + host)
        # A global runtime is used by a separate adopting checkout.
        project = target if scope == "local" and not external else self.base / (host + " adopting project")
        project.mkdir(exist_ok=True)
        fixtures.git(project, "init", "-b", "main")
        runtime = namespace / "engineer/bin/engineer.py"
        self.assertTrue(runtime.is_file())
        self.assertFalse((namespace / "bin/install-assets/agent-entry.txt").exists())
        env = {key: value for key, value in os.environ.items()
               if key not in ("ENGINEER_ROOT", "ENGINEER_HOST", "CODEX_HOME", "CLAUDE_CONFIG_DIR")}
        env["CODEX_HOME" if host == "codex" else "CLAUDE_CONFIG_DIR"] = str(namespace)

        def query(*args, expected=0):
            result = subprocess.run(
                [sys.executable, "-I", str(runtime), "query", *map(str, args)],
                cwd=project, env=env, capture_output=True, text=True,
                encoding="utf-8", timeout=30)
            self.assertEqual(expected, result.returncode, result.stderr or result.stdout)
            return json.loads(result.stdout if expected == 0 else result.stderr)

        identity = query("runtime-identity")
        self.assertEqual(host, identity["host"])
        self.assertEqual(str(namespace), identity["namespace"])
        query("project.init", "--name", "Fixture", "--description", "Instruction fixture",
              "--core-value", "Installed references resolve")
        return namespace, project, query

    def assert_references(self, content, host, scope, namespace, project):
        # Derived oracle: the installer's reference contract plus actual files.
        prefix = fixtures.installer.reference_namespace(host, scope).as_posix()
        role = prefix + "/agents/AGENT.md"
        command = prefix + "/commands/<command>.md"
        self.assertIn(role, content)
        self.assertIn(command, content)
        selected = "debug"
        for reference in (role, command.replace("<command>", selected)):
            relative = reference.removeprefix(prefix + "/")
            resolved = project / reference if scope == "local" else namespace / relative
            self.assertTrue(resolved.is_file(), reference)
        self.assertIn(".planning/PROJECT.md and STATE.md before working.", content)

    def test_absent_template_both_hosts_and_scopes(self):
        for host in ("claude", "codex"):
            for scope in ("local", "global"):
                with self.subTest(host=host, scope=scope):
                    namespace, project, query = self.install(host, scope)
                    entry = project / ("CLAUDE.md" if host == "claude" else "AGENTS.md")
                    original = entry.read_text(encoding="utf-8") if entry.exists() else ""
                    entry.write_text("Custom project instructions\n" + original, encoding="utf-8")
                    result = query("generate-claude-md")
                    self.assertEqual(str(entry), result["path"])
                    first = entry.read_bytes()
                    self.assertTrue(first.startswith(b"Custom project instructions\n"))
                    self.assertIn(original, first.decode())
                    self.assert_references(first.decode(), host, scope, namespace, project)
                    query("generate-claude-md")
                    self.assertEqual(first, entry.read_bytes())

                    explicit = project / "custom-entry.md"
                    before, after = "Custom before\n\n", "\nCustom after\n"
                    explicit.write_text(before + START + "\nStale generated instructions\n" + END + after,
                                        encoding="utf-8")
                    query("generate-claude-md", "--output", explicit.name)
                    generated = explicit.read_text(encoding="utf-8")
                    self.assertTrue(generated.startswith(before))
                    self.assertTrue(generated.endswith(after))
                    self.assertNotIn("Stale generated instructions", generated)
                    self.assertEqual(1, generated.count(START))
                    self.assert_references(generated, host, scope, namespace, project)
                    query("generate-claude-md", "--output", explicit.name)
                    self.assertEqual(generated, explicit.read_text(encoding="utf-8"))

    def test_present_templates_qualify_legacy_paths_once(self):
        for host in ("claude", "codex"):
            for scope in ("local", "global"):
                with self.subTest(host=host, scope=scope):
                    namespace, project, query = self.install(host, scope)
                    template = namespace / "bin/install-assets/agent-entry.txt"
                    template.parent.mkdir(parents=True, exist_ok=True)
                    prefix = fixtures.installer.reference_namespace(host, scope).as_posix()
                    cases = (
                        ("Read engineer/RULES.md and commands/<command>.md. Keep this prose.",
                         f"Read {prefix}/agents/AGENT.md and {prefix}/commands/<command>.md. Keep this prose."),
                        (f"Read {prefix}/engineer/RULES.md and {prefix}/commands/<command>.md.",
                         f"Read {prefix}/agents/AGENT.md and {prefix}/commands/<command>.md."),
                        (f"Read {prefix}/agents/AGENT.md and {prefix}/commands/<command>.md.",
                         f"Read {prefix}/agents/AGENT.md and {prefix}/commands/<command>.md."),
                        ("Custom template without catalog references.",
                         "Custom template without catalog references."),
                    )
                    for source, expected in cases:
                        with self.subTest(template=source):
                            template.write_text(source + "\n", encoding="utf-8")
                            query("generate-claude-md", "--output", "template-entry.md")
                            entry = project / "template-entry.md"
                            expected_block = START + "\n# Fixture\n\n" + expected + "\n" + END
                            self.assertEqual(expected_block + "\n", entry.read_text(encoding="utf-8"))
                            original = entry.read_bytes()
                            query("generate-claude-md", "--output", entry.name)
                            self.assertEqual(original, entry.read_bytes())

    def test_external_local_runtime_uses_its_actual_namespace(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                namespace, project, query = self.install(host, "local", external=True)
                query("generate-claude-md")
                entry = project / ("CLAUDE.md" if host == "claude" else "AGENTS.md")
                content = entry.read_text(encoding="utf-8")
                for relative in ("agents/AGENT.md", "commands/<command>.md"):
                    reference = namespace.as_posix() + "/" + relative
                    self.assertIn(reference, content)
                    self.assertTrue(Path(reference.replace("<command>", "debug")).is_file())
                original = entry.read_bytes()
                query("generate-claude-md")
                self.assertEqual(original, entry.read_bytes())

    def test_invalid_markers_preserve_bytes(self):
        for host in ("claude", "codex"):
            with self.subTest(host=host):
                _, project, query = self.install(host, "local")
                entry = project / "invalid-entry.md"
                for markers in (START, END, START + END + START + END):
                    with self.subTest(markers=markers):
                        original = ("Custom café\r\n" + markers + "\r\nKeep bytes\r\n").encode()
                        entry.write_bytes(original)
                        failure = query("generate-claude-md", "--output", entry.name, expected=1)
                        self.assertEqual("ambiguous-instruction-block", failure["error"])
                        self.assertEqual(original, entry.read_bytes())


if __name__ == "__main__":
    unittest.main()
