"""Run the real coordinator after installing its resources in either host root."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml

import test_phase_runtime as source_tests


SOURCE = Path(__file__).resolve().parents[1]
PHASE = source_tests.PHASE
PHASE_PATH = source_tests.PHASE_PATH


class HostRuntimeTests(unittest.TestCase):
    # Reuse fixture record builders and Git assertions, without inheriting the
    # source-only tests or constructing their .ai installation first.
    git = source_tests.PhaseRuntimeTests.git
    write = staticmethod(source_tests.PhaseRuntimeTests.write)
    record = source_tests.PhaseRuntimeTests.record
    context = source_tests.PhaseRuntimeTests.context
    component = source_tests.PhaseRuntimeTests.component
    commit = source_tests.PhaseRuntimeTests.commit
    events = source_tests.PhaseRuntimeTests.events
    assert_primary_untouched = source_tests.PhaseRuntimeTests.assert_primary_untouched

    def create_installation(self, host):
        self.host = host
        temporary = tempfile.TemporaryDirectory(prefix=f"{host[1:]} runtime ")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name).resolve()
        self.primary = self.directory / "project"
        self.primary.mkdir()
        self.environment = os.environ.copy()
        self.environment.update(GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
                                PYTHONDONTWRITEBYTECODE="1", PHASE_RUNTIME_ROOT=host)
        self.git(self.primary, "init", "-b", "main")
        for name, value in (("user.name", "Host Runtime Test"),
                            ("user.email", "test@example.invalid"),
                            ("core.autocrlf", "false"), ("commit.gpgsign", "false")):
            self.git(self.primary, "config", name, value)
        for source, destination in (("runtime", "runtime"), ("templates", "templates"),
                                    ("agents", "roles"), ("references", "references")):
            shutil.copytree(SOURCE / ".ai" / source, self.primary / host / destination,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copytree(SOURCE / ".agents/skills", self.primary / host / "skills")
        # Match the installer's prose relocation; Python is copied byte-for-byte.
        for path in (self.primary / host).rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            path.write_text(self.relocate(text), encoding="utf-8")
        self.write(self.primary, ".gitignore", ".worktrees/\n__pycache__/\n*.pyc\n")
        self.write(self.primary, "README.md", "Fixture project\n")
        entry = "CLAUDE.md" if host == ".claude" else "AGENTS.md"
        self.write(self.primary, entry, "Follow the scoped phase assignment.\n")
        self.write(self.primary, f"{host}/RULES.md", "Use assigned worktrees.\n")
        for name in ("PROJECT", "REQUIREMENTS", "ROADMAP", "STATE"):
            self.write(self.primary, f".planning/{name}.md", f"# Fixture {name}\n")
        (self.primary / "tests").mkdir()
        shutil.copy2(SOURCE / "tests/phase_worker_fixture.py", self.primary / "tests/phase_worker_fixture.py")
        self.config = {
            "execution": {
                "max_parallel": 2,
                "worker_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "documentor_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "verifier_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "environment": {"PHASE_FIXTURE_EVENTS": str(self.directory / "events"),
                                "PHASE_FIXTURE_MODE": "full-templates",
                                "PHASE_RUNTIME_ROOT": host},
            },
            "verification": {"commands": [[sys.executable, "-c",
                "from pathlib import Path; assert Path('src/01-01.txt').read_text().strip()"]]},
            "publication": {"remote": "origin"},
        }
        self.write(self.primary, ".planning/config.yaml", yaml.safe_dump(self.config))
        self.git(self.primary, "add", "--all")
        self.git(self.primary, "commit", "-m", "Install host-only runtime fixture")
        self.main_revision = self.git(self.primary, "rev-parse", "HEAD")
        self.checkout = self.primary / ".worktrees" / "phase"
        self.git(self.primary, "worktree", "add", "-b", "codex/host-runtime-test", str(self.checkout))

    def relocate(self, text):
        return (text.replace(".ai/agents/", f"{self.host}/roles/")
                    .replace(".ai/commands/", f"{self.host}/workflows/")
                    .replace(".agents/skills/", f"{self.host}/skills/")
                    .replace(".ai/", f"{self.host}/"))

    def cli(self, *args, succeeds=True):
        result = subprocess.run([sys.executable, str(self.checkout / self.host / "runtime/phase.py"), *args],
                                cwd=self.checkout, env=self.environment, text=True, encoding="utf-8",
                                capture_output=True, timeout=60)
        output = result.stdout + result.stderr
        self.assertEqual(result.returncode == 0, succeeds, output)
        return output

    def probe(self, code):
        prefix = f"import sys; sys.path.insert(0, {str(self.checkout / self.host / 'runtime')!r}); "
        result = subprocess.run([sys.executable, "-c", prefix + code], cwd=self.checkout,
                                env=self.environment, text=True, encoding="utf-8", capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def exercise_host(self, host):
        self.create_installation(host)
        self.cli("new", "example", "--title", "Exercise installed host")
        created_context = self.checkout / PHASE_PATH / "01-CONTEXT.md"
        self.assertIn("<domain>", created_context.read_text(encoding="utf-8"))
        self.context()
        self.component("01-01")
        self.component("01-02", files=["docs/result.md"], kind="documentation",
                       depends_on=["01-01"], documentation=["docs/result.md"])
        for plan in (self.checkout / PHASE_PATH).glob("*-PLAN.md"):
            plan.write_text(self.relocate(plan.read_text(encoding="utf-8")), encoding="utf-8")
        self.commit("Prepare installed-host components")
        self.cli("check", PHASE)

        # Changing the active namespace's rules must invalidate phase inputs.
        fingerprint_code = ("from pathlib import Path; from phase_records import load_phase; "
                            f"print(load_phase(Path.cwd(), {PHASE!r}).fingerprint())")
        before = self.probe(fingerprint_code)
        rules = self.checkout / host / "RULES.md"
        original_rules = rules.read_bytes()
        rules.write_bytes(original_rules + b"Changed input.\n")
        self.assertNotEqual(before, self.probe(fingerprint_code))
        rules.write_bytes(original_rules)
        self.assertEqual(before, self.probe(fingerprint_code))

        # A worker cannot claim the installed rules through a file or directory.
        plan = self.checkout / PHASE_PATH / "01-01-PLAN.md"
        original_plan = plan.read_text(encoding="utf-8")
        for ownership in (f"{host}/RULES.md", f"{host}/"):
            changed = original_plan.replace("- src/01-01.txt", f"- {ownership}")
            plan.write_text(changed, encoding="utf-8")
            self.assertIn("coordinator-owned", self.cli("check", PHASE, succeeds=False))
        plan.write_text(original_plan, encoding="utf-8")

        self.cli("run", PHASE)
        self.assertTrue((self.checkout / "src/01-01.txt").is_file())
        self.assertTrue((self.checkout / "docs/result.md").is_file())
        self.cli("verify", PHASE)
        report = (self.checkout / PHASE_PATH / "01-VERIFICATION.md").read_text(encoding="utf-8")
        self.assertIn("status: passed", report)
        events = self.events(include_verifier=True)
        self.assertEqual({event["kind"] for event in events}, {"code", "documentation", "verifier"})
        self.assertTrue(all(event["methods"] for event in events))
        self.assertTrue(all(method.startswith(host + "/") for event in events for method in event["methods"]))

        prompts = list((self.primary / ".git/ai").rglob("*-assignment.md"))
        self.assertEqual(len(prompts), 3)
        for path in prompts:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(".ai/", text)
            self.assertIn(f"{host}/RULES.md", text)
            self.assertIn(f"{host}/runtime/TEMPLATE-CONTRACT.md", text)
            self.assertIn("Read CLAUDE.md" if host == ".claude" else "Read AGENTS.md", text)

        # TDD prompts use the same installed skill namespace without executing
        # a second phase merely to inspect the additional instruction branch.
        tdd_prompt = self.probe("from pathlib import Path; from phase_records import load_phase; "
            "from phase_runner import assignment; "
            f"p=load_phase(Path.cwd(), {PHASE!r}); c=p.components['01-01']; c.data['type']='tdd'; "
            "print(assignment(p,c,p.root,'code',c.summary,'a'*40))")
        self.assertIn(f"{host}/skills/regression-design/SKILL.md", tdd_prompt)
        self.assertNotIn(".agents/skills", tdd_prompt)
        self.assertNotIn(".ai/", tdd_prompt)
        self.assertFalse((self.primary / ".ai").exists())
        self.assertFalse((self.checkout / ".ai").exists())
        for event in events:
            self.assertFalse((Path(event["worktree"]) / ".ai").exists())
        self.assert_primary_untouched()

    def test_codex_runtime_without_ai_directory(self):
        self.exercise_host(".codex")

    def test_claude_runtime_without_ai_directory(self):
        self.exercise_host(".claude")


if __name__ == "__main__":
    unittest.main()
