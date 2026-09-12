"""Behavioral integration tests for phase execution in real Git worktrees."""

from __future__ import annotations

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

import yaml


SOURCE = Path(__file__).resolve().parents[1]
PHASE = "01-example"
PHASE_PATH = Path(".ai/phases") / PHASE


class PhaseRuntimeTests(unittest.TestCase):
    """A coordinator and every subprocess worker use genuine isolated branches."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="phase runtime ")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
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
        (self.primary / "tests").mkdir()
        shutil.copy2(SOURCE / "tests/phase_worker_fixture.py", self.primary / "tests/phase_worker_fixture.py")
        self.write(self.primary, ".gitignore", ".worktrees/\n__pycache__/\n*.pyc\n")
        self.write(self.primary, "README.md", "Fixture project\n")
        self.write(self.primary, "AGENTS.md", "Follow the approved phase assignment and commit scoped changes.\n")
        self.write(self.primary, ".ai/RULES.md", "Preserve approved scope and use assigned worktrees.\n")
        for role in ("coder", "documentor", "verifier"):
            self.write(self.primary, f".ai/agents/{role}.md", f"# {role}\n\nFollow the assigned phase responsibility.\n")
        self.write(self.primary, ".ai/PROJECT.md", "# Fixture project\n\nExercise phase execution.\n")
        self.write(self.primary, ".ai/REQUIREMENTS.md", "# Requirements\n\n- R1: Components integrate correctly.\n")
        self.write(self.primary, ".ai/ROADMAP.md", "# Roadmap\n\n- 01: Exercise phase execution.\n")
        self.write(self.primary, ".ai/STATE.md", "# State\n\nNo phase has run.\n")
        self.config = {
            "execution": {
                "max_parallel": 2,
                "worker_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "documentor_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "verifier_command": [sys.executable, "{worktree}/tests/phase_worker_fixture.py"],
                "environment": {"PHASE_FIXTURE_EVENTS": str(self.directory / "events")},
            },
            "verification": {
                "commands": [[sys.executable, "-c", "from pathlib import Path; assert Path('README.md').read_text() == 'Fixture project\\n'"]],
            },
            "publication": {"remote": "origin"},
        }
        self.write(self.primary, ".ai/config.yaml", yaml.safe_dump(self.config, sort_keys=False))
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
            {"phase": "01", "title": "Example", "approval": approval, "depends_on": [], "uat": uat},
            "# Example phase\n\n## Goal\n\nDeliver integrated fixture components.\n\n"
            "## Scope\n\nOnly the assigned components.\n\n"
            "## Acceptance\n\n- [ ] A1: Every component is present and works with its prerequisites.\n\n"
            "## Decisions\n\nUse independent component worktrees.\n\n"
            "## Authorization\n\nThe user approved implementing and verifying this phase in worktrees.\n\n"
            "## Open questions\n\nNone.\n\n## Deferred\n\nNone.\n",
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
            PHASE_PATH / f"{identifier}-IMPLEMENT.md",
            {
                "kind": kind, "depends_on": depends_on or [], "files": paths,
                "resources": resources or [], "acceptance": ["A1"],
                "documentation": documentation or [],
                "checks": checks or [[sys.executable, "-c", "from pathlib import Path; assert Path(" + repr(paths[0]) + ").exists()"]],
            },
            f"# Component {identifier}\n\n## Objective\n\nImplement the assigned fixture component.\n\n"
            "## Read first\n\nRead phase CONTEXT and summaries of prerequisites.\n\n"
            "## Implementation\n\nWrite the assigned paths without editing other components.\n\n"
            "## Verification\n\nRun the component check and configured integration check.\n\n"
            "## Documentation\n\nUpdate every declared documentation path.\n",
        )

    def configure(self, **environment: str) -> None:
        self.config["execution"]["environment"].update(environment)
        self.write(self.checkout, ".ai/config.yaml", yaml.safe_dump(self.config, sort_keys=False))

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
        events = [yaml.safe_load(path.read_text(encoding="utf-8")) for path in directory.glob("*.yaml")]
        return [event for event in events if include_verifier or event["kind"] != "verifier"]

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
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

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
        self.cli("run", PHASE)
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(), "01-01 implemented\n")
        self.assertTrue(self.summary("01-01").is_file())
        self.cli("verify", PHASE)
        self.assertTrue((self.checkout / PHASE_PATH / "01-VERIFICATION.md").is_file())
        self.assertEqual(len(self.events()), 1)
        self.assertEqual(self.git(self.checkout, "status", "--porcelain"), "")
        self.assert_primary_untouched()

    def test_bounded_bug_has_failing_reproduction_and_passing_regression(self) -> None:
        self.write(self.checkout, "src/total.py", "def total(values):\n    return len(values)\n")
        self.component("01-01", files=["src/total.py"], checks=[[
            sys.executable, "-c", "from src.total import total; assert total([2, 3]) == 5",
        ]])
        self.configure(PHASE_FIXTURE_MODE="repair-bug")
        self.commit("Prepare reproducible arithmetic defect")
        self.cli("run", PHASE)
        self.assertIn("Regression before repair: [1]", self.summary("01-01").read_text())
        self.assertIn("Regression after repair: [0]", self.summary("01-01").read_text())
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
        self.assertEqual((self.checkout / "src/shared.txt").read_text().splitlines(), [
            f"{events[0]['component']} implemented", f"{events[1]['component']} implemented",
        ])

    def test_case_variants_of_owned_paths_serialize_conservatively(self) -> None:
        self.component("01-01", files=["src/shared.txt"])
        self.component("01-02", files=["src/Shared.txt"])
        self.configure(PHASE_FIXTURE_DELAY="0.2")
        self.commit("Prepare case-variant ownership")
        self.cli("run", PHASE)
        events = sorted(self.events(), key=lambda event: event["started"])
        self.assertEqual(len(events), 2)
        self.assertGreaterEqual(events[1]["started"], events[0]["finished"])
        self.assertTrue(self.summary("01-01").exists())
        self.assertTrue(self.summary("01-02").exists())

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
        next_phase = Path(".ai/phases/02-dependent")
        source_context = (self.checkout / PHASE_PATH / "01-CONTEXT.md").read_text().split("---", 2)[2]
        self.record(
            next_phase / "02-CONTEXT.md",
            {"phase": "02", "approval": "approved", "depends_on": [PHASE], "uat": False},
            source_context,
        )
        source_instruction = (self.checkout / PHASE_PATH / "01-01-IMPLEMENT.md").read_text().split("---", 2)
        metadata = yaml.safe_load(source_instruction[1])
        metadata.update(files=["src/02-01.txt"], checks=[[
            sys.executable, "-c", "from pathlib import Path; assert Path('src/01-01.txt').exists() and Path('src/02-01.txt').exists()",
        ]])
        self.record(next_phase / "02-01-IMPLEMENT.md", metadata, source_instruction[2])
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
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(), "01-01 implemented\n")
        self.assertTrue(self.summary("01-02").exists())

    def test_summary_only_commit_is_not_implementation(self) -> None:
        self.write(self.checkout, "src/01-01.txt", "Existing behavior\n")
        self.configure(PHASE_FIXTURE_MODE="summary-only")
        self.commit("Prepare summary-only worker")
        self.cli("run", PHASE, succeeds=False)
        self.assertFalse(self.summary("01-01").exists())
        self.assertEqual((self.checkout / "src/01-01.txt").read_text(), "Existing behavior\n")

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
        instruction = self.checkout / PHASE_PATH / "01-01-IMPLEMENT.md"
        instruction.write_text(instruction.read_text() + "\nA newly changed implementation requirement.\n", encoding="utf-8")
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
        self.assertIn("External fixture unavailable", uat.read_text())
        self.cli("uat", PHASE)
        self.assertIn("External fixture unavailable", uat.read_text())
        self.publish(succeeds=False)
        self.cli("uat", PHASE, "--case", "1", "--result", "fail", "--note", "Observed missing behavior")
        self.publish(succeeds=False)
        self.cli("uat", PHASE, "--case", "1", "--result", "skipped", "--note", "Scenario has not been exercised")
        self.publish(succeeds=False)
        self.cli("uat", PHASE, "--case", "1", "--result", "pass", "--note", "The complete acceptance scenario passed")
        self.assertIn("The complete acceptance scenario passed", uat.read_text())
        self.publish()
        self.assertFalse(any("merge" in call for call in self.forge_calls()))

    def test_resume_consumes_committed_worker_without_replaying_it(self) -> None:
        release = self.directory / "release-worker"
        self.configure(PHASE_FIXTURE_MODE="commit-then-wait", PHASE_FIXTURE_RELEASE=str(release))
        self.commit("Prepare interrupted coordinator")
        process = subprocess.Popen(
            [sys.executable, str(self.checkout / ".ai/runtime/phase.py"), "run", PHASE],
            cwd=self.checkout, env=self.environment, text=True, encoding="utf-8",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                events = self.events()
                if events and events[0].get("committed"):
                    break
                if process.poll() is not None:
                    self.fail("Coordinator exited before interruption: " + str(process.communicate()))
                time.sleep(0.025)
            else:
                self.fail("Worker did not commit before interruption timeout")
            process.terminate()
            process.communicate(timeout=10)
            release.touch()
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not self.events()[0].get("finished"):
                time.sleep(0.025)
            self.assertTrue(self.events()[0].get("finished"), "Committed worker did not finish")
            self.cli("resume", PHASE, "--workers-stopped")
            self.assertTrue(self.summary("01-01").is_file())
            self.assertEqual(len(self.events()), 1)
        finally:
            release.touch()
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)


if __name__ == "__main__":
    unittest.main()
