"""Behavioral integration tests for phase execution in real Git worktrees."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import yaml


SOURCE = Path(__file__).resolve().parents[1]
PHASE = "01-example"
PHASE_PATH = Path(".planning/phases") / PHASE


def read_fixture_event(path: Path) -> dict:
    # Windows can briefly deny opening a destination during atomic replacement.
    # Retry that sharing race only; persistent errors must still fail the test.
    for attempt in range(40):
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except PermissionError:
            if attempt == 39:
                raise
            time.sleep(0.025)


class FixtureEventTests(unittest.TestCase):
    def test_transient_sharing_error_retries_and_reads_complete_event(self) -> None:
        with patch.object(Path, "read_text", side_effect=[PermissionError("sharing"), "kind: code\nfinished: 12\n"]) as read, patch("time.sleep") as sleep:
            self.assertEqual(read_fixture_event(Path("event.yaml")), {"kind": "code", "finished": 12})
        self.assertEqual(read.call_count, 2)
        sleep.assert_called_once_with(0.025)

    def test_persistent_permission_error_is_not_hidden(self) -> None:
        with patch.object(Path, "read_text", side_effect=PermissionError("denied")) as read, patch("time.sleep"):
            with self.assertRaises(PermissionError):
                read_fixture_event(Path("event.yaml"))
        self.assertEqual(read.call_count, 40)


class PhaseRuntimeTests(unittest.TestCase):
    """A coordinator and every subprocess worker use genuine isolated branches."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="phase runtime ")
        self.addCleanup(self.temporary.cleanup)
        # Windows CI may expose TEMP through an 8.3 alias (for example RUNNER~1).
        # Compare the same physical paths that Git and the runtime resolve.
        self.directory = Path(self.temporary.name).resolve()
        self.primary = self.directory / "project"
        self.primary.mkdir()
        self.environment = os.environ.copy()
        self.environment.update(
            GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0", PYTHONDONTWRITEBYTECODE="1"
        )
        self.git(self.primary, "init", "-b", "main")
        self.git(self.primary, "config", "user.name", "Phase Test")
        self.git(self.primary, "config", "user.email", "phase-test@example.invalid")
        self.git(self.primary, "config", "core.autocrlf", "false")
        self.git(self.primary, "config", "commit.gpgsign", "false")
        shutil.copytree(
            SOURCE / ".ai/runtime", self.primary / ".ai/runtime",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        templates = Path(os.environ.get("TEMPLATE_TEST_SOURCE", str(SOURCE / ".ai/templates")))
        shutil.copytree(templates, self.primary / ".ai/templates")
        (self.primary / "tests").mkdir()
        shutil.copy2(SOURCE / "tests/phase_worker_fixture.py", self.primary / "tests/phase_worker_fixture.py")
        self.write(self.primary, ".gitignore", ".worktrees/\n__pycache__/\n*.pyc\n")
        self.write(self.primary, "README.md", "Fixture project\n")
        self.write(self.primary, "AGENTS.md", "Follow the approved phase assignment and commit scoped changes.\n")
        self.write(self.primary, ".ai/RULES.md", "Preserve approved scope and use assigned worktrees.\n")
        # Dispatch must hand off real, shipped methods, including specialists.
        shutil.copytree(SOURCE / ".ai/agents", self.primary / ".ai/agents")
        shutil.copytree(SOURCE / ".ai/references", self.primary / ".ai/references")
        self.write(self.primary, ".planning/PROJECT.md", "# Fixture project\n\nExercise phase execution.\n")
        self.write(self.primary, ".planning/REQUIREMENTS.md", "# Requirements\n\n- R1: Components integrate correctly.\n")
        self.write(self.primary, ".planning/ROADMAP.md", "# Roadmap\n\n- 01: Exercise phase execution.\n")
        self.write(self.primary, ".planning/STATE.md", "# State\n\nNo phase has run.\n")
        self.config = {
            "execution": {
                "max_parallel": 2,
                "worker_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "documentor_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "verifier_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "environment": {"PHASE_FIXTURE_EVENTS": str(self.directory / "events")},
            },
            "verification": {
                "commands": [[sys.executable, "-c", "from pathlib import Path; assert Path('README.md').read_text(encoding='utf-8') == 'Fixture project\\n'"]],
            },
            "publication": {"remote": "origin"},
        }
        self.write(self.primary, ".planning/config.yaml", yaml.safe_dump(self.config, sort_keys=False))
        self.git(self.primary, "add", "--all")
        self.git(self.primary, "commit", "-m", "Seed phase runtime fixture")
        self.main_revision = self.git(self.primary, "rev-parse", "HEAD")
        self.checkout = self.primary / ".worktrees" / "phase"
        self.git(self.primary, "worktree", "add", "-b", "codex/phase-test", str(self.checkout))
        self.context()
        self.component("01-01")
        self.commit("Prepare approved phase")

    def git(self, root: Path, *arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments], env=self.environment,
            text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    @staticmethod
    def write(root: Path, relative: str | Path, body: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def record(self, relative: str | Path, metadata: dict, body: str) -> Path:
        return self.write(
            self.checkout, relative,
            "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body,
        )

    def context(self, *, approval: str = "approved", uat: bool = False) -> None:
        self.record(
            PHASE_PATH / "01-CONTEXT.md",
            {"phase": "01", "title": "Example", "approval": approval, "discussion": "complete", "depends_on": [], "uat": uat},
            "# Example phase\n\n## Goal\n\nDeliver integrated fixture components.\n\n"
            "## Scope\n\nOnly the assigned components.\n\n"
            "## Acceptance\n\n- [ ] A1: Every component is present and works with its prerequisites.\n\n"
            "## Decisions\n\nUse independent component worktrees.\n\n"
            "## Authorization\n\nThe user approved implementing and verifying this phase in worktrees.\n\n"
            "## Open questions\n\nNone.\n\n## Deferred\n\nNone.\n",
        )
        self.write(
            self.checkout, PHASE_PATH / "01-DISCUSSION-LOG.md",
            "# Example discussion\n\nThe fixture user chose independent component worktrees "
            "and agreed that every assigned output must work with its prerequisites.\n",
        )
        self.write(
            self.checkout, PHASE_PATH / "01-VALIDATION.md",
            "# Validation\n\nCheck every assigned output and run configured integration checks.\n",
        )

    def component(
        self, identifier: str, *, files: list[str] | None = None,
        depends_on: list[str] | None = None, resources: list[str] | None = None,
        kind: str = "code", documentation: list[str] | None = None,
        checks: list[list[str]] | None = None,
    ) -> None:
        paths = files or [f"src/{identifier}.txt"]
        self.record(
            PHASE_PATH / f"{identifier}-PLAN.md",
            {
                "phase": PHASE, "plan": identifier.split("-")[-1], "type": "execute", "autonomous": True, "wave": 1, "must_haves": {"truths": ["Fixture output works"], "artifacts": paths, "key_links": []},
                "kind": kind, "depends_on": depends_on or [], "files_modified": paths, "requirements": ["R1"],
                "resources": resources or [], "acceptance": ["A1"],
                "documentation": documentation or [],
                "checks": checks or [[sys.executable, "-c", "from pathlib import Path; assert Path(" + repr(paths[0]) + ").exists()"]],
            },
            "<objective>Implement the assigned fixture component.</objective>\n"
            "<execution_context>@.ai/runtime/TEMPLATE-CONTRACT.md</execution_context>\n"
            "<context>Read phase CONTEXT and summaries of prerequisites.</context>\n"
            "<tasks><task type=\"auto\"><name>Implement output</name>"
            "<files>Assigned paths</files><read_first>Phase CONTEXT</read_first>"
            "<action>Write assigned paths without editing other components.</action>"
            "<verify>Run component checks.</verify><done>Assigned outputs work.</done>"
            "</task></tasks>\n<verification>Run component and integration checks.</verification>\n"
            "<success_criteria>Checks pass and output works.</success_criteria>\n"
            "<output>Commit assigned SUMMARY.</output>\n"
            "## Documentation\n\nUpdate every declared documentation path.\n",
        )

    def configure(self, **environment: str) -> None:
        self.config["execution"]["environment"].update(environment)
        self.write(self.checkout, ".planning/config.yaml", yaml.safe_dump(self.config, sort_keys=False))

    def commit(self, message: str) -> None:
        self.git(self.checkout, "add", "--all")
        self.git(self.checkout, "commit", "-m", message)

    def cli(
        self, *arguments: str, succeeds: bool = True, root: Path | None = None,
        timeout: int = 60,
    ) -> subprocess.CompletedProcess[str]:
        directory = root or self.checkout
        result = subprocess.run(
            [sys.executable, str(directory / ".ai/runtime/phase.py"), *arguments],
            cwd=directory, env=self.environment, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
        )
        output = result.stdout + result.stderr
        if succeeds:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        return result

    def events(self, *, include_verifier: bool = False) -> list[dict]:
        directory = self.directory / "events"
        events = [read_fixture_event(path) for path in directory.glob("*.yaml")]
        return [event for event in events if include_verifier or event["kind"] not in ("verifier", "code-reviewer")]

    def summary(self, identifier: str) -> Path:
        return self.checkout / PHASE_PATH / f"{identifier}-SUMMARY.md"

    def assert_primary_untouched(self) -> None:
        self.assertEqual(self.git(self.primary, "rev-parse", "HEAD"), self.main_revision)
        self.assertEqual(self.git(self.primary, "status", "--porcelain"), "")

    def state_snapshot(self) -> dict[str, str]:
        root = self.primary / ".git" / "ai"
        return {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()
        }

    def prepare_remote(self) -> None:
        self.remote = self.directory / "origin.git"
        self.git(self.primary, "init", "--bare", str(self.remote))
        self.git(self.primary, "remote", "add", "origin", str(self.remote))
        self.git(self.primary, "push", "-u", "origin", "main")

    def publish(self, *, succeeds: bool = True, authorized: bool = True) -> subprocess.CompletedProcess[str]:
        self.environment["PHASE_FIXTURE_FORGE_LOG"] = str(self.directory / "forge.jsonl")
        command = [
            sys.executable, str(self.checkout / "tests/phase_worker_fixture.py"),
            "forge-cli", "publish", PHASE, "--base", "main",
        ]
        if authorized:
            command.append("--authorized")
        result = subprocess.run(
            command, cwd=self.checkout, env=self.environment, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        )
        if succeeds:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def forge_calls(self) -> list[list[str]]:
        log = self.directory / "forge.jsonl"
        return [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()] if log.exists() else []

    @contextmanager
    def live_worker_after_coordinator_interruption(self, *, crash_before_pid_save: bool = False, mode="commit-then-wait"):
        release = self.directory / "release-worker"
        self.configure(PHASE_FIXTURE_MODE=mode, PHASE_FIXTURE_RELEASE=str(release))
        self.commit("Prepare interrupted coordinator")
        command = [sys.executable, str(self.checkout / ".ai/runtime/phase.py"), "run", PHASE]
        if crash_before_pid_save:
            launcher = (
                "import os,sys\n"
                "sys.path.insert(0,'.ai/runtime')\n"
                "import phase_runner,phase\n"
                "original=phase_runner.save\n"
                "def lose_pid_checkpoint(p,state):\n"
                "    if any(e.get('status')=='running' for e in state['components'].values()):\n"
                "        os._exit(81)\n"
                "    return original(p,state)\n"
                "phase_runner.save=lose_pid_checkpoint\n"
                f"phase.main(['run',{PHASE!r}])\n"
            )
            command = [sys.executable, "-c", launcher]
        process = subprocess.Popen(
            command,
            cwd=self.checkout, env=self.environment, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                events = self.events()
                if events and events[0].get("committed"):
                    break
                if process.poll() is not None and not crash_before_pid_save:
                    self.fail("Coordinator exited before interruption: " + str(process.communicate()))
                time.sleep(0.025)
            else:
                self.fail("Worker did not commit before interruption timeout")
            if not crash_before_pid_save:
                process.terminate()
            process.communicate(timeout=10)
            if crash_before_pid_save:
                self.assertEqual(process.returncode, 81, "Fault injection did not reach the PID checkpoint")
            yield release
        finally:
            release.touch()
            deadline = time.monotonic() + 10
            while self.events() and not self.events()[0].get("finished") and time.monotonic() < deadline:
                time.sleep(0.025)
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)

    def release_worker(self, release: Path, *, kind: str = "code") -> None:
        release.touch()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            matching = [event for event in self.events(include_verifier=True) if event["kind"] == kind]
            if matching and matching[0].get("finished"):
                return
            time.sleep(0.025)
        self.fail(f"The {kind} worker did not finish")

    def test_check_and_status_are_read_only(self) -> None:
        before = self.git(self.checkout, "rev-parse", "HEAD")
        state_before = self.state_snapshot()
        self.cli("check", PHASE)
        self.cli("status", PHASE)
        self.cli("status")
        self.assertEqual(self.git(self.checkout, "rev-parse", "HEAD"), before)
        self.assertEqual(self.git(self.checkout, "status", "--porcelain"), "")
        self.assertEqual(self.state_snapshot(), state_before)
        self.assertEqual(self.events(), [])
        self.assert_primary_untouched()

    def test_runs_component_commits_summary_and_verifies_phase(self) -> None:
        review_base = self.git(self.checkout, "rev-parse", "HEAD")
        self.cli("run", PHASE)
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(encoding='utf-8'), "01-01 implemented\n")
        self.assertTrue(self.summary("01-01").is_file())
        self.cli("verify", PHASE)
        review = next(event for event in self.events(include_verifier=True) if event["kind"] == "verifier")
        self.assertEqual(review["review_scope"]["diff_base"], review_base)
        self.assertEqual(set(review["review_scope"]["files"]),
                         {"src/01-01.txt", (PHASE_PATH / "01-01-SUMMARY.md").as_posix()})
        self.assertTrue((self.checkout / PHASE_PATH / "01-VERIFICATION.md").is_file())
        self.assertEqual(len(self.events()), 1)
        self.assertEqual(self.git(self.checkout, "status", "--porcelain"), "")
        self.assert_primary_untouched()

    def test_independent_review_uses_worker_revision_without_editing_checkout(self) -> None:
        self.cli("run", PHASE)
        author = self.events()[0]
        review = next(event for event in self.events(include_verifier=True) if event["kind"] == "code-reviewer")
        self.assertNotEqual(review["worktree"], author["worktree"])
        self.assertEqual(review["revision"], author["committed"])
        self.assertEqual(self.git(Path(review["worktree"]), "rev-parse", "HEAD"), author["committed"])
        self.assertEqual(self.git(Path(review["worktree"]), "status", "--porcelain"), "")
        self.assertFalse(Path(review["report_written"]).is_relative_to(Path(review["worktree"])))
        self.assertLessEqual(author["finished"], review["started"])

    def test_skipped_review_retries_same_revision_and_preserves_original_report(self) -> None:
        self.environment["PHASE_FIXTURE_REVIEW_MODE"] = "skipped"
        self.cli("run", PHASE, succeeds=False)
        first = next(event for event in self.events(include_verifier=True) if event["kind"] == "code-reviewer")
        report = Path(first["report_written"])
        original = report.read_bytes()
        self.assertFalse((self.checkout / "src/01-01.txt").exists())
        self.environment["PHASE_FIXTURE_REVIEW_MODE"] = "clean"
        self.cli("resume", PHASE, "--workers-stopped")
        reviews = [event for event in self.events(include_verifier=True) if event["kind"] == "code-reviewer"]
        self.assertEqual(len(reviews), 2)
        self.assertEqual({event["revision"] for event in reviews}, {first["revision"]})
        self.assertEqual(report.read_bytes(), original)
        self.assertEqual(len(self.events()), 1, "Review retry must not replay the coder")
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(encoding="utf-8"), "01-01 implemented\n")
        self.cli("verify", PHASE)

    def test_critical_review_cannot_retry_unchanged_code(self) -> None:
        self.environment["PHASE_FIXTURE_REVIEW_MODE"] = "critical"
        self.cli("run", PHASE, succeeds=False)
        self.environment["PHASE_FIXTURE_REVIEW_MODE"] = "clean"
        self.cli("resume", PHASE, "--workers-stopped", succeeds=False)
        reviews = [event for event in self.events(include_verifier=True) if event["kind"] == "code-reviewer"]
        self.assertEqual(len(reviews), 1)
        self.assertFalse((self.checkout / "src/01-01.txt").exists())

    def test_historical_skipped_review_is_reconciled_before_verification(self) -> None:
        self.cli("run", PHASE)
        # Reproduce a persisted historical review without changing source history.
        checkpoint = next((self.primary / ".git/ai").rglob("state.yaml"))
        state = yaml.safe_load(checkpoint.read_text(encoding="utf-8"))
        attempt = state["components"]["01-01"]["review_attempt"]
        report = Path(attempt["result"])
        report.write_text(report.read_text(encoding="utf-8").replace("status: clean", "status: skipped"), encoding="utf-8")
        attempt.update(verdict="skipped", report_hash=hashlib.sha256(report.read_bytes()).hexdigest())
        checkpoint.write_text(yaml.safe_dump(state), encoding="utf-8")
        original = report.read_bytes()
        self.cli("verify", PHASE, succeeds=False)
        self.cli("verify", PHASE, "--workers-stopped")
        reviews = [event for event in self.events(include_verifier=True) if event["kind"] == "code-reviewer"]
        self.assertEqual(len(reviews), 2)
        self.assertEqual({event["revision"] for event in reviews}, {attempt["revision"]})
        self.assertEqual(report.read_bytes(), original)
        self.assertEqual(len(self.events()), 1)

    def test_review_warning_requires_revision_bound_coordinator_disposition(self) -> None:
        self.environment["PHASE_FIXTURE_REVIEW_MODE"] = "warning"
        self.cli("run", PHASE)
        rejected = self.cli("verify", PHASE, succeeds=False)
        self.assertIn("record one warning_dispositions item", rejected.stderr)
        review = next(event for event in self.events(include_verifier=True) if event["kind"] == "code-reviewer")
        self.record(PHASE_PATH / "01-VERIFICATION.md", {"warning_dispositions": [{
            "component": "01-01", "revision": review["revision"], "finding": "WR-01",
            "disposition": "accepted", "reason": "Fixture advisory does not affect assigned acceptance.",
        }]}, "# Coordinator warning decision\n")
        self.commit("Record coordinator decision for advisory finding")
        self.cli("verify", PHASE)
        data = yaml.safe_load((self.checkout / PHASE_PATH / "01-VERIFICATION.md").read_text(encoding="utf-8").split("---", 2)[1])
        self.assertEqual(data["warning_dispositions"][0]["revision"], review["revision"])
        self.assertEqual(data["status"], "passed")

    def test_skipped_review_retry_rejects_modified_original_report(self) -> None:
        self.environment["PHASE_FIXTURE_REVIEW_MODE"] = "skipped"
        self.cli("run", PHASE, succeeds=False)
        first = next(event for event in self.events(include_verifier=True) if event["kind"] == "code-reviewer")
        report = Path(first["report_written"])
        report.write_text(report.read_text(encoding="utf-8") + "\nTampered evidence.\n", encoding="utf-8")
        self.environment["PHASE_FIXTURE_REVIEW_MODE"] = "clean"
        self.cli("resume", PHASE, "--workers-stopped", succeeds=False)
        self.assertEqual(len([event for event in self.events(include_verifier=True) if event["kind"] == "code-reviewer"]), 1)
        self.assertFalse((self.checkout / "src/01-01.txt").exists())

    def test_bounded_bug_has_failing_reproduction_and_passing_regression(self) -> None:
        self.write(self.checkout, "src/total.py", "def total(values):\n    return len(values)\n")
        self.component("01-01", files=["src/total.py"], checks=[[
            sys.executable, "-c", "from src.total import total; assert total([2, 3]) == 5",
        ]])
        self.configure(PHASE_FIXTURE_MODE="repair-bug")
        self.commit("Prepare reproducible arithmetic defect")
        self.cli("run", PHASE)
        self.assertIn("Regression before repair: [1]", self.summary("01-01").read_text(encoding='utf-8'))
        self.assertIn("Regression after repair: [0]", self.summary("01-01").read_text(encoding='utf-8'))
        self.cli("verify", PHASE)

    def test_independent_components_overlap_and_use_sibling_worktrees(self) -> None:
        self.component("01-02")
        self.configure(PHASE_FIXTURE_DELAY="1")
        self.commit("Prepare independent components")
        self.cli("run", PHASE)
        events = {event["component"]: event for event in self.events()}
        self.assertEqual(set(events), {"01-01", "01-02"})
        self.assertLess(max(event["started"] for event in events.values()), min(event["finished"] for event in events.values()))
        for event in events.values():
            self.assertEqual(Path(event["worktree"]).parent, self.primary / ".worktrees")
            self.assertNotEqual(Path(event["worktree"]), self.checkout)
        self.assertNotEqual(events["01-01"]["worktree"], events["01-02"]["worktree"])
        self.assertTrue(self.summary("01-01").is_file())
        self.assertTrue(self.summary("01-02").is_file())

    def test_shared_resource_serializes_otherwise_independent_components(self) -> None:
        self.component("01-01", resources=["fixture-service"])
        self.component("01-02", resources=["fixture-service"])
        self.configure(PHASE_FIXTURE_DELAY="0.2")
        self.commit("Declare exclusive fixture resource")
        self.cli("run", PHASE)
        events = sorted(self.events(), key=lambda event: event["started"])
        self.assertEqual(len(events), 2)
        self.assertGreaterEqual(events[1]["started"], events[0]["finished"])

    def test_shared_path_serializes_and_preserves_both_changes(self) -> None:
        self.component("01-01", files=["src/shared.txt"])
        self.component("01-02", files=["src/shared.txt"])
        self.configure(PHASE_FIXTURE_DELAY="0.2")
        self.commit("Declare overlapping file ownership")
        self.cli("run", PHASE)
        events = sorted(self.events(), key=lambda event: event["started"])
        self.assertEqual(len(events), 2)
        self.assertGreaterEqual(events[1]["started"], events[0]["finished"])
        self.assertEqual((self.checkout / "src/shared.txt").read_text(encoding='utf-8').splitlines(), [
            f"{events[0]['component']} implemented", f"{events[1]['component']} implemented",
        ])

    def test_case_variants_of_owned_paths_serialize_conservatively(self) -> None:
        self.component("01-01", files=["src/shared.txt"])
        self.component("01-02", files=["src/Shared.txt"])
        self.configure(PHASE_FIXTURE_DELAY="0.2")
        self.commit("Prepare case-variant ownership")
        probe = self.directory / "CaseSensitivityProbe"
        probe.touch()
        case_sensitive = not (self.directory / "casesensitivityprobe").exists()
        # On Windows, the second write retains the first file's Git spelling;
        # serialization remains required, but its exact ownership audit must fail.
        self.cli("run", PHASE, succeeds=case_sensitive)
        events = sorted(self.events(), key=lambda event: event["started"])
        self.assertEqual(len(events), 2)
        self.assertGreaterEqual(events[1]["started"], events[0]["finished"])
        self.assertTrue(self.summary("01-01").exists())
        self.assertEqual(self.summary("01-02").exists(), case_sensitive)

    def test_dependency_sees_committed_prerequisite(self) -> None:
        self.component("01-02", depends_on=["01-01"])
        self.commit("Prepare dependent component")
        self.cli("run", PHASE)
        events = {event["component"]: event for event in self.events()}
        self.assertGreaterEqual(events["01-02"]["started"], events["01-01"]["finished"])
        self.assertTrue(self.summary("01-02").is_file())
        self.assertTrue((self.checkout / "src/01-02.txt").is_file())

    def test_delivered_phase_is_available_from_a_fresh_phase_worktree(self) -> None:
        self.prepare_remote()
        self.cli("run", PHASE)
        self.cli("verify", PHASE)
        # This local bare fixture simulates the user merging the first phase PR.
        self.git(self.checkout, "push", "origin", "HEAD:main")
        next_checkout = self.primary / ".worktrees" / "second-phase"
        self.git(self.primary, "worktree", "add", "-b", "codex/second-phase", str(next_checkout), "origin/main")
        self.checkout = next_checkout
        self.cli("new", "dependent", "--title", "Use the delivered first phase")
        next_phase = Path(".planning/phases/02-dependent")
        source_context = (self.checkout / PHASE_PATH / "01-CONTEXT.md").read_text(encoding='utf-8').split("---", 2)[2]
        self.record(
            next_phase / "02-CONTEXT.md",
            {"phase": "02", "approval": "approved", "discussion": "complete", "depends_on": [PHASE], "uat": False},
            source_context,
        )
        self.write(self.checkout, next_phase / "02-DISCUSSION-LOG.md",
                   "# Follow-up discussion\n\nThe fixture user agreed to consume the delivered prerequisite.\n")
        source_instruction = (self.checkout / PHASE_PATH / "01-01-PLAN.md").read_text(encoding='utf-8').split("---", 2)
        metadata = yaml.safe_load(source_instruction[1])
        metadata.update(phase="02-dependent", plan="01", files_modified=["src/02-01.txt"], checks=[[
            sys.executable, "-c", "from pathlib import Path; assert Path('src/01-01.txt').exists() and Path('src/02-01.txt').exists()",
        ]])
        self.record(next_phase / "02-01-PLAN.md", metadata, source_instruction[2])
        self.commit("Prepare phase depending on delivered behavior")
        self.cli("check", "02-dependent")
        self.cli("run", "02-dependent")
        self.assertTrue((self.checkout / "src/01-01.txt").is_file())
        self.assertTrue((self.checkout / "src/02-01.txt").is_file())
        self.assertEqual({event["component"] for event in self.events()}, {"01-01", "02-01"})

    def test_failed_component_parks_dependents_and_preserves_independent_work(self) -> None:
        self.component("01-02", depends_on=["01-01"])
        self.component("01-03")
        self.configure(PHASE_FIXTURE_FAIL_COMPONENT="01-01")
        self.commit("Prepare isolated component failure")
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual({event["component"] for event in self.events()}, {"01-01", "01-03"})
        self.assertFalse(self.summary("01-02").exists())
        self.assertTrue(self.summary("01-03").is_file())
        self.assertTrue((self.checkout / "src/01-03.txt").is_file())

    def test_documentation_phase_uses_documentation_worker(self) -> None:
        self.component("01-01", kind="documentation", files=["docs/guide.md"], documentation=["docs/guide.md"])
        self.commit("Prepare documentation-only phase")
        self.cli("run", PHASE)
        self.assertEqual([event["kind"] for event in self.events()], ["documentation"])
        self.assertIn(".ai/agents/doc-writer.md", self.events()[0]["methods"])
        self.cli("verify", "01")
        review = next(event for event in self.events(include_verifier=True) if event["kind"] == "verifier")
        self.assertTrue({".ai/agents/doc-verifier.md", ".ai/agents/integration-checker.md"}.issubset(review["methods"]))
        self.assertFalse(Path(review["report_written"]).is_relative_to(Path(review["worktree"])))
        self.assertTrue((self.checkout / "docs/guide.md").is_file())
        self.assertFalse((self.checkout / "src").exists())

    def test_missing_documentation_is_not_accepted(self) -> None:
        self.component("01-01", files=["src/01-01.txt", "docs/guide.md"], documentation=["docs/guide.md"])
        self.configure(PHASE_FIXTURE_MODE="missing-documentation")
        self.commit("Prepare missing required documentation")
        self.cli("run", PHASE, succeeds=False)
        self.assertFalse(self.summary("01-01").exists())
        self.assertFalse((self.checkout / "src/01-01.txt").exists())
        workers = self.events()
        self.assertEqual(len(workers), 1)
        self.assertTrue((Path(workers[0]["worktree"]) / "src/01-01.txt").is_file())

    def test_outside_ownership_is_preserved_but_not_integrated(self) -> None:
        self.component("01-01", checks=[[sys.executable, "-c", "pass"]])
        self.configure(PHASE_FIXTURE_MODE="outside")
        self.commit("Prepare out-of-scope worker")
        self.cli("run", PHASE, succeeds=False)
        self.assertFalse((self.checkout / "outside-ownership.txt").exists())
        self.assertFalse(self.summary("01-01").exists())
        self.assertTrue((Path(self.events()[0]["worktree"]) / "outside-ownership.txt").is_file())

    def test_exact_ownership_rejects_a_different_git_path_case(self) -> None:
        self.component("01-01", files=["src/Allowed.txt"], checks=[[sys.executable, "-c", "pass"]])
        self.configure(PHASE_FIXTURE_MODE="case-outside")
        self.commit("Prepare a worker writing a differently spelled Git path")
        self.cli("run", PHASE, succeeds=False)
        worker = Path(self.events()[0]["worktree"])
        self.assertEqual(self.git(worker, "ls-files", "src/allowed.txt"), "src/allowed.txt")
        self.assertFalse((self.checkout / "src/allowed.txt").exists())
        self.assertFalse(self.summary("01-01").exists())

    def test_leading_space_path_is_rejected_without_trimming_git_output(self) -> None:
        self.component("01-01", files=["safe.txt"], checks=[[sys.executable, "-c", "pass"]])
        self.configure(PHASE_FIXTURE_MODE="leading-space-outside")
        self.commit("Prepare an unowned path with leading whitespace")
        self.cli("run", PHASE, succeeds=False)
        worker = Path(self.events()[0]["worktree"])
        self.assertTrue((worker / " safe.txt").is_file())
        self.assertFalse((self.checkout / " safe.txt").exists())
        self.assertFalse(self.summary("01-01").exists())

    def test_reverted_leading_space_path_is_rejected_from_commit_history(self) -> None:
        self.component("01-01", files=["safe.txt"], checks=[[sys.executable, "-c", "pass"]])
        self.configure(PHASE_FIXTURE_MODE="leading-space-reverted")
        self.commit("Prepare a reverted unowned path in worker history")
        self.cli("run", PHASE, succeeds=False)
        worker = Path(self.events()[0]["worktree"])
        self.assertFalse((worker / " safe.txt").exists())
        self.assertTrue(self.git(worker, "log", "--format=%s", "--", " safe.txt"))
        self.assertFalse((self.checkout / "safe.txt").exists())
        self.assertFalse(self.summary("01-01").exists())

    def test_uncommitted_work_is_preserved_but_not_integrated(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="uncommitted")
        self.commit("Prepare uncommitted worker")
        self.cli("run", PHASE, succeeds=False)
        self.assertFalse((self.checkout / "src/01-01.txt").exists())
        worker = Path(self.events()[0]["worktree"])
        self.assertTrue((worker / "src/01-01.txt").is_file())
        self.assertTrue(self.git(worker, "status", "--porcelain"))

    def test_unapproved_phase_cannot_dispatch(self) -> None:
        self.context(approval="pending")
        self.commit("Leave phase awaiting approval")
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual(self.events(), [])

    def test_unknown_dependency_is_rejected_before_dispatch(self) -> None:
        self.component("01-01", depends_on=["01-99"])
        self.commit("Prepare unavailable dependency")
        self.cli("check", PHASE, succeeds=False)
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual(self.events(), [])

    def test_dependency_cycle_is_rejected_before_dispatch(self) -> None:
        self.component("01-01", depends_on=["01-02"])
        self.component("01-02", depends_on=["01-01"])
        self.commit("Prepare dependency cycle")
        self.cli("check", PHASE, succeeds=False)
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual(self.events(), [])

    def test_path_escape_is_rejected_before_dispatch(self) -> None:
        self.component("01-01", files=["../outside.txt"])
        self.commit("Prepare invalid ownership path")
        self.cli("check", PHASE, succeeds=False)
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual(self.events(), [])

    def test_component_check_failure_prevents_dependent_dispatch(self) -> None:
        self.component("01-01", checks=[[sys.executable, "-c", "raise SystemExit(9)"]])
        self.component("01-02", depends_on=["01-01"])
        self.commit("Prepare failing component check")
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual([event["component"] for event in self.events()], ["01-01"])
        self.assertFalse(self.summary("01-02").exists())

    def test_component_check_timeout_allows_independent_work_and_explicit_replan(self) -> None:
        self.component("01-01", checks=[[sys.executable, "-c", "import time; time.sleep(2)"]])
        self.component("01-02")
        self.config["execution"].update(check_timeout_seconds=1, max_parallel=1)
        self.configure()
        self.commit("Prepare a timed out component check")
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual({event["component"] for event in self.events()}, {"01-01", "01-02"})
        self.assertFalse(self.summary("01-01").exists())
        self.assertTrue(self.summary("01-02").exists())
        self.component("01-01")
        self.commit("Correct the timed out verification instructions")
        self.cli("run", PHASE, "--replan", "--workers-stopped")
        components = [event["component"] for event in self.events()]
        self.assertEqual(components.count("01-01"), 2)
        self.assertEqual(components.count("01-02"), 1)
        self.assertTrue(self.summary("01-01").exists())

    def assert_check_commit_rejected(self, *, fails_after_commit: bool) -> None:
        command = (
            "from pathlib import Path; import subprocess; p=Path('check-created.txt'); "
            "apply=Path.cwd().name == 'phase' and not p.exists(); "
            "p.write_text('outside component ownership', encoding='utf-8') if apply else None; "
            "subprocess.run(['git','add','check-created.txt'],check=True) if apply else None; "
            "subprocess.run(['git','commit','-m','Check changed source'],check=True) if apply else None"
        )
        if fails_after_commit:
            command += "; raise SystemExit(7 if apply else 0)"
        self.config["verification"]["commands"] = [[sys.executable, "-c", command]]
        self.configure()
        self.commit("Prepare an improperly committing integration check")
        self.cli("run", PHASE, succeeds=False)
        self.cli("verify", PHASE, succeeds=False)
        self.assertTrue((self.checkout / "check-created.txt").is_file(), "Unexpected changes must remain available for inspection")
        worker = Path(self.events()[0]["worktree"])
        self.assertFalse((worker / "check-created.txt").exists())
        self.assertFalse((self.checkout / PHASE_PATH / "01-VERIFICATION.md").exists())

    def test_verification_command_cannot_hide_changes_in_a_commit(self) -> None:
        self.assert_check_commit_rejected(fails_after_commit=False)

    def test_failing_verification_command_cannot_hide_changes_in_a_commit(self) -> None:
        self.assert_check_commit_rejected(fails_after_commit=True)

    def test_failed_integration_prevents_dependency_release_and_preserves_result(self) -> None:
        self.component("01-02", depends_on=["01-01"])
        self.config["verification"]["commands"] = [[
            sys.executable, "-c",
            "from pathlib import Path; assert Path.cwd().name != 'phase' or not Path('src/01-01.txt').exists()",
        ]]
        self.configure()
        self.commit("Prepare coordinator-only integration failure")
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual([event["component"] for event in self.events()], ["01-01"])
        self.assertFalse(self.summary("01-02").exists())
        worker = Path(self.events()[0]["worktree"])
        self.assertTrue((worker / PHASE_PATH / "01-01-SUMMARY.md").is_file())
        self.assertTrue((worker / "src/01-01.txt").is_file())

    def test_resume_rechecks_failed_integration_without_replaying_committed_work(self) -> None:
        self.component("01-02", depends_on=["01-01"])
        service_down = self.directory / "integration-service-down"
        service_down.touch()
        self.config["verification"]["commands"] = [[
            sys.executable, "-c", "from pathlib import Path; "
            f"assert Path.cwd().name != 'phase' or not Path({str(service_down)!r}).exists()",
        ]]
        self.configure()
        self.commit("Prepare transient integration failure")
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual([event["component"] for event in self.events()], ["01-01"])
        service_down.unlink()
        self.cli("resume", PHASE, "--workers-stopped")
        events = self.events()
        self.assertEqual(len(events), 2)
        self.assertEqual({event["component"] for event in events}, {"01-01", "01-02"})
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(encoding='utf-8'), "01-01 implemented\n")
        self.assertTrue(self.summary("01-02").exists())

    def test_summary_only_commit_is_not_implementation(self) -> None:
        self.write(self.checkout, "src/01-01.txt", "Existing behavior\n")
        self.configure(PHASE_FIXTURE_MODE="summary-only")
        self.commit("Prepare summary-only worker")
        self.cli("run", PHASE, succeeds=False)
        self.assertFalse(self.summary("01-01").exists())
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(encoding='utf-8'), "Existing behavior\n")

    def test_blocked_summary_cannot_claim_component_completion(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="blocked")
        self.commit("Prepare blocked committed output")
        self.cli("run", PHASE, succeeds=False)
        self.assertFalse(self.summary("01-01").exists())
        self.assertFalse((self.checkout / "src/01-01.txt").exists())

    def test_primary_checkout_cannot_start_mutating_execution(self) -> None:
        self.git(self.primary, "merge", "--ff-only", "codex/phase-test")
        self.main_revision = self.git(self.primary, "rev-parse", "HEAD")
        self.cli("run", PHASE, succeeds=False, root=self.primary)
        self.assertEqual(self.events(), [])
        self.assert_primary_untouched()

    def test_changed_inputs_do_not_reuse_completed_assignments(self) -> None:
        self.cli("run", PHASE)
        instruction = self.checkout / PHASE_PATH / "01-01-PLAN.md"
        instruction.write_text(instruction.read_text(encoding='utf-8') + "\nA newly changed implementation requirement.\n", encoding="utf-8")
        self.commit("Change execution target after completion")
        self.cli("resume", PHASE, "--workers-stopped", succeeds=False)
        self.assertEqual(len(self.events()), 1)

    def test_verifier_cannot_change_tracked_files(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="verifier-dirty")
        self.commit("Prepare mutating verifier")
        self.cli("run", PHASE)
        self.cli("verify", PHASE, succeeds=False)
        self.assertFalse((self.checkout / PHASE_PATH / "01-VERIFICATION.md").exists())

    def test_verifier_cannot_attest_to_an_earlier_revision(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="verifier-stale")
        self.commit("Prepare stale verifier report")
        self.cli("run", PHASE)
        self.cli("verify", PHASE, succeeds=False)

    def test_verifier_findings_prevent_publication(self) -> None:
        self.prepare_remote()
        self.configure(PHASE_FIXTURE_MODE="verifier-fail")
        self.commit("Prepare a failed verification")
        self.cli("run", PHASE)
        self.cli("verify", PHASE, succeeds=False)
        self.publish(succeeds=False)
        self.assertEqual(self.forge_calls(), [])
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), self.main_revision)

    def test_publishing_creates_pr_without_merging_or_moving_primary(self) -> None:
        self.prepare_remote()
        self.cli("run", PHASE)
        self.cli("verify", PHASE)
        self.publish()
        calls = self.forge_calls()
        self.assertTrue(any(call[1:3] == ["pr", "create"] for call in calls))
        self.assertFalse(any("merge" in call for call in calls))
        self.assertEqual(self.git(self.remote, "rev-parse", "main"), self.main_revision)
        self.assertEqual(self.git(self.remote, "rev-parse", "codex/phase-test"), self.git(self.checkout, "rev-parse", "HEAD"))
        self.assert_primary_untouched()

    def test_merged_observation_does_not_mark_newer_branch_work_delivered(self) -> None:
        self.prepare_remote()
        self.cli("run", PHASE)
        self.cli("verify", PHASE)
        # Simulate a human merge observed by the forge; the CLI still never merges.
        self.environment["PHASE_FIXTURE_PR_STATE"] = "MERGED"
        self.publish()
        delivered = self.cli("status", PHASE)
        self.assertIn("delivered (observed merge)", delivered.stdout)
        self.write(self.checkout, "later-change.txt", "A commit not covered by the observed PR\n")
        self.commit("Add new work after the observed merge")
        before = self.state_snapshot()
        current = self.cli("status", PHASE)
        self.assertNotIn("delivered (observed merge)", current.stdout)
        self.assertIn("https://github.com/example/fixture/pull/7", current.stdout)
        self.assertEqual(self.state_snapshot(), before, "Status must retain observations without rewriting state")

    def test_publication_requires_explicit_authorization(self) -> None:
        self.prepare_remote()
        self.cli("run", PHASE)
        self.cli("verify", PHASE)
        self.publish(succeeds=False, authorized=False)
        self.assertEqual(self.forge_calls(), [])

    def test_source_change_invalidates_verification_before_publication(self) -> None:
        self.prepare_remote()
        self.cli("run", PHASE)
        self.cli("verify", PHASE)
        self.write(self.checkout, "src/01-01.txt", "Changed after independent verification\n")
        self.commit("Change source after verification")
        self.publish(succeeds=False)
        self.assertEqual(self.forge_calls(), [])

    def test_required_uat_preserves_results_and_blocks_publication_until_passed(self) -> None:
        self.prepare_remote()
        self.context(uat=True)
        self.commit("Require acceptance testing for this phase")
        self.cli("run", PHASE)
        self.cli("verify", PHASE)
        self.cli("uat", PHASE)
        uat = self.checkout / PHASE_PATH / "01-UAT.md"
        self.assertTrue(uat.is_file())
        self.publish(succeeds=False)
        self.cli("uat", PHASE, "--case", "1", "--result", "blocked", "--note", "External fixture unavailable")
        self.assertIn("External fixture unavailable", uat.read_text(encoding='utf-8'))
        self.cli("uat", PHASE)
        self.assertIn("External fixture unavailable", uat.read_text(encoding='utf-8'))
        self.publish(succeeds=False)
        self.cli("uat", PHASE, "--case", "1", "--result", "fail", "--note", "Observed missing behavior")
        self.publish(succeeds=False)
        self.cli("uat", PHASE, "--case", "1", "--result", "skipped", "--note", "Scenario has not been exercised")
        self.publish(succeeds=False)
        self.cli("uat", PHASE, "--case", "1", "--result", "pass", "--note", "The complete acceptance scenario passed")
        self.assertIn("The complete acceptance scenario passed", uat.read_text(encoding='utf-8'))
        self.publish()
        self.assertFalse(any("merge" in call for call in self.forge_calls()))

    def test_resume_consumes_committed_worker_without_replaying_it(self) -> None:
        with self.live_worker_after_coordinator_interruption() as release:
            self.release_worker(release)
            self.cli("resume", PHASE, "--workers-stopped")
            self.assertTrue(self.summary("01-01").is_file())
            self.assertEqual(len(self.events()), 1)

    def test_capacity_handoffs_preserve_commits_and_dirty_work_without_another_command(self) -> None:
        self.component("01-02", depends_on=["01-01"])
        self.configure(PHASE_FIXTURE_MODE="handoff-context")
        self.commit("Prepare explicit context handoff")
        self.cli("run", PHASE)
        attempts = sorted([e for e in self.events() if e["component"] == "01-01"], key=lambda e: e["started"])
        self.assertEqual(len(attempts), 2)
        self.assertNotEqual(attempts[0]["pid"], attempts[1]["pid"])
        self.assertEqual(attempts[0]["worktree"], attempts[1]["worktree"])
        self.assertGreaterEqual(attempts[1]["started"], attempts[0]["finished"])
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(encoding="utf-8"),
                         "preserved commit\npreserved dirty work\n01-01 implemented\n")
        self.assertTrue(self.summary("01-02").exists())
        self.cli("verify", PHASE)

    def test_worker_timeout_dispatches_fresh_worker_and_retains_attempt_evidence(self) -> None:
        self.config["execution"]["worker_timeout_seconds"] = 8
        self.configure(PHASE_FIXTURE_MODE="handoff-timeout")
        self.commit("Prepare timed-out partial worker")
        self.cli("run", PHASE)
        attempts = sorted(self.events(), key=lambda e: e["started"])
        self.assertEqual(len(attempts), 2)
        self.assertTrue(attempts[1]["continued"])
        checkpoint = next((self.primary / ".git/ai").rglob("state.yaml"))
        entry = yaml.safe_load(checkpoint.read_text(encoding="utf-8"))["components"]["01-01"]
        self.assertEqual(entry["status"], "integrated")
        self.assertEqual(entry["attempt_history"][0]["reason"], "timeout")
        self.assertNotEqual(entry["log"], entry["attempt_history"][0]["log"])
        self.assertTrue(Path(entry["attempt_history"][0]["receipt"]).exists())
        self.assertIn("preserved dirty work", (self.checkout / "src/01-01.txt").read_text(encoding="utf-8"))

    def test_repeated_capacity_handoffs_without_source_edits_still_continue(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="handoff-research")
        self.commit("Prepare consecutive research handoffs")
        self.cli("run", PHASE)
        self.assertEqual(len(self.events()), 3)
        self.assertTrue(self.summary("01-01").exists())

    def test_capacity_exit_with_complete_committed_result_does_not_replay(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="complete-then-handoff")
        self.commit("Prepare complete result at capacity boundary")
        self.cli("run", PHASE)
        self.assertEqual(len(self.events()), 1)
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(encoding="utf-8"), "01-01 implemented\n")

    def test_resume_hands_partial_work_to_a_fresh_worker_in_the_same_tree(self) -> None:
        with self.live_worker_after_coordinator_interruption(mode="handoff-wait") as release:
            self.cli("resume", PHASE, "--workers-stopped", succeeds=False)
            self.assertEqual(len(self.events()), 1)
            self.release_worker(release)
            self.cli("resume", PHASE, "--workers-stopped")
            attempts = sorted(self.events(), key=lambda e: e["started"])
            self.assertEqual(len(attempts), 2)
            self.assertEqual(attempts[0]["worktree"], attempts[1]["worktree"])
            self.assertEqual((self.checkout / "src/01-01.txt").read_text(encoding="utf-8"),
                             "preserved commit\npreserved dirty work\n01-01 implemented\n")

    def test_handoff_keeps_overlapping_components_serialized(self) -> None:
        self.component("01-01", files=["src/shared.txt"], resources=["shared-service"])
        self.component("01-02", files=["src/shared.txt"], resources=["shared-service"])
        self.configure(PHASE_FIXTURE_MODE="handoff-context")
        self.commit("Prepare shared-path handoff")
        self.cli("run", PHASE)
        events = sorted(self.events(), key=lambda e: e["started"])
        self.assertEqual([e["component"] for e in events], ["01-01", "01-01", "01-02"])
        self.assertGreaterEqual(events[2]["started"], events[1]["finished"])
        self.assertEqual((self.checkout / "src/shared.txt").read_text(encoding="utf-8"),
                         "preserved commit\npreserved dirty work\n01-01 implemented\n01-02 implemented\n")

    def test_peer_timeout_during_independent_review_still_dispatches_replacement(self) -> None:
        self.component("01-02")
        self.configure(PHASE_FIXTURE_MODE="handoff-timeout")
        self.commit("Prepare peer interrupted during independent review")
        # Advance only the first worker's deadline when its peer reaches review.
        # The real review polling loop must kill it and record timed_out.
        launcher = (
            "import sys,time\nsys.path.insert(0,'.ai/runtime')\nimport phase_runner,phase\n"
            "original=phase_runner.capture_component_review\n"
            "def review(p,c,e,s,h,peers=None,**kw):\n"
            "    if c.id=='01-02' and peers and '01-01' in peers:\n"
            "        s['components']['01-01']['started']=time.time()-4000\n"
            "    return original(p,c,e,s,h,peers,**kw)\n"
            "phase_runner.capture_component_review=review\n"
            f"raise SystemExit(phase.main(['run',{PHASE!r}]))\n"
        )
        result = subprocess.run([sys.executable, "-c", launcher], cwd=self.checkout, env=self.environment,
                                capture_output=True, text=True, encoding="utf-8", timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        attempts = [e for e in self.events() if e["component"] == "01-01"]
        self.assertEqual(len(attempts), 2)
        self.assertTrue(self.summary("01-01").exists())
        self.assertTrue(self.summary("01-02").exists())

    def test_capacity_handoff_rejects_unowned_dirty_work(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="handoff-outside")
        self.commit("Prepare out-of-scope partial worker")
        result = self.cli("run", PHASE, succeeds=False)
        self.assertIn("out-of-scope unfinished change: outside.txt", result.stdout)
        self.assertEqual(len(self.events()), 1)
        self.assertTrue((Path(self.events()[0]["worktree"]) / "outside.txt").exists())

    def test_resume_does_not_reuse_stale_handoff_after_replacement_permission_failure(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="handoff-permission")
        self.commit("Prepare handoff followed by permission failure")
        self.cli("run", PHASE, succeeds=False)
        self.assertEqual(len(self.events()), 2)
        self.cli("resume", PHASE, "--workers-stopped", succeeds=False)
        self.assertEqual(len(self.events()), 2)
        self.assertFalse(self.summary("01-01").exists())

    def test_timeout_preserves_truncated_utf8_summary_and_independent_work(self) -> None:
        self.component("01-02")
        self.config["execution"]["worker_timeout_seconds"] = 8
        self.configure(PHASE_FIXTURE_MODE="handoff-truncated")
        self.commit("Prepare interruption during multibyte summary write")
        self.cli("run", PHASE)
        self.assertEqual(len([e for e in self.events() if e["component"] == "01-01"]), 2)
        self.assertTrue(self.summary("01-01").exists())
        self.assertTrue(self.summary("01-02").exists())

    def test_capacity_handoff_rejects_undeclared_dirty_deletion(self) -> None:
        self.configure(PHASE_FIXTURE_MODE="handoff-delete")
        self.commit("Prepare undeclared partial deletion")
        result = self.cli("run", PHASE, succeeds=False)
        self.assertIn("undeclared unfinished deletion", result.stdout)
        self.assertEqual(len(self.events()), 1)

    def test_resume_refuses_to_integrate_a_still_running_worker(self) -> None:
        with self.live_worker_after_coordinator_interruption() as release:
            self.assertFalse(self.events()[0].get("finished"))
            self.cli("resume", PHASE, "--workers-stopped", succeeds=False)
            self.assertFalse(self.summary("01-01").exists())
            self.assertFalse((self.checkout / "src/01-01.txt").exists())
            self.release_worker(release)
            self.cli("resume", PHASE, "--workers-stopped")
            self.assertTrue(self.summary("01-01").is_file())
            self.assertEqual(len(self.events()), 1)

    def test_resume_uses_launch_receipt_when_pid_checkpoint_was_lost(self) -> None:
        with self.live_worker_after_coordinator_interruption(crash_before_pid_save=True) as release:
            self.assertFalse(self.events()[0].get("finished"))
            self.cli("resume", PHASE, "--workers-stopped", succeeds=False)
            self.assertFalse(self.summary("01-01").exists())
            self.release_worker(release)
            self.cli("resume", PHASE, "--workers-stopped")
            self.assertTrue(self.summary("01-01").exists())
            self.assertEqual(len(self.events()), 1)

    def test_interrupted_verifier_reuses_its_finished_report_without_relaunch(self) -> None:
        release = self.directory / "release-verifier"
        self.configure(PHASE_FIXTURE_MODE="verifier-report-then-wait", PHASE_FIXTURE_RELEASE=str(release))
        self.commit("Prepare interrupted independent verification")
        self.cli("run", PHASE)
        verified_revision = self.git(self.checkout, "rev-parse", "HEAD")
        process = subprocess.Popen(
            [sys.executable, str(self.checkout / ".ai/runtime/phase.py"), "verify", PHASE],
            cwd=self.checkout, env=self.environment, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                verifier_events = [event for event in self.events(include_verifier=True) if event["kind"] == "verifier"]
                if verifier_events and verifier_events[0].get("report_written"):
                    break
                if process.poll() is not None:
                    self.fail("Verifier coordinator exited before interruption: " + str(process.communicate()))
                time.sleep(0.025)
            else:
                self.fail("Verifier did not write its report before timeout")
            process.terminate()
            process.communicate(timeout=10)
            self.cli("verify", PHASE, succeeds=False)
            self.assertFalse((self.checkout / PHASE_PATH / "01-VERIFICATION.md").exists())
            self.release_worker(release, kind="verifier")
            self.cli("verify", PHASE)
            report = (self.checkout / PHASE_PATH / "01-VERIFICATION.md").read_text(encoding='utf-8').split("---", 2)
            self.assertEqual(yaml.safe_load(report[1])["revision"], verified_revision)
            self.assertEqual(len([event for event in self.events(include_verifier=True) if event["kind"] == "verifier"]), 1)
        finally:
            release.touch()
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                pending = [event for event in self.events(include_verifier=True) if event["kind"] == "verifier" and not event.get("finished")]
                if not pending:
                    break
                time.sleep(0.025)
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)


if __name__ == "__main__":
    unittest.main()
