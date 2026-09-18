"""Deterministic, committing worker for phase-runtime integration tests only."""

from __future__ import annotations

import os
import re
from pathlib import Path
import subprocess
import sys
import time
import uuid

import yaml


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(root), *args], text=True, encoding="utf-8"
    ).strip()


def write_record(path: Path, metadata: dict, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body,
        encoding="utf-8",
    )


def await_fixture_release() -> None:
    release = Path(os.environ["PHASE_FIXTURE_RELEASE"])
    deadline = time.monotonic() + 25
    while not release.exists():
        if time.monotonic() > deadline:
            raise RuntimeError("Test did not release the worker")
        time.sleep(0.025)


def forge_cli() -> int:
    """Run the real CLI with only the external GitHub response simulated."""
    import json
    import runpy
    import shutil
    from unittest.mock import patch

    original_run = subprocess.run
    original_which = shutil.which
    log = Path(os.environ["PHASE_FIXTURE_FORGE_LOG"])

    def fake_run(argv: list[str], *args, **kwargs):
        if Path(str(argv[0])).name.lower() not in {"gh", "gh.exe"}:
            return original_run(argv, *args, **kwargs)
        with log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(argv) + "\n")
        if "merge" in argv:
            raise AssertionError("Publication attempted a merge")
        head = git(Path(kwargs.get("cwd", Path.cwd())), "rev-parse", "HEAD")
        if argv[1:3] == ["pr", "list"]:
            stdout = "[]\n"
        elif argv[1:3] == ["pr", "create"]:
            stdout = "https://github.com/example/fixture/pull/7\n"
        elif argv[1:3] == ["pr", "view"]:
            state = os.environ.get("PHASE_FIXTURE_PR_STATE", "OPEN")
            stdout = json.dumps({
                "number": 7, "url": "https://github.com/example/fixture/pull/7",
                "state": state, "mergedAt": "2026-09-12T00:00:00Z" if state == "MERGED" else None,
                "headRefOid": head,
                "statusCheckRollup": [],
            })
        else:
            raise AssertionError(f"Unexpected GitHub operation: {argv}")
        return subprocess.CompletedProcess(argv, 0, stdout, "")

    def fake_which(command, *args, **kwargs):
        return "gh" if command == "gh" else original_which(command, *args, **kwargs)

    sys.argv = [str(Path.cwd() / ".ai/runtime/phase.py"), *sys.argv[2:]]
    sys.path.insert(0, str(Path.cwd() / ".ai/runtime"))
    with patch("subprocess.run", side_effect=fake_run), patch("shutil.which", side_effect=fake_which):
        runpy.run_path(sys.argv[0], run_name="__main__")
    return 0


def full_template_result(root, path, template_name):
    """Materialize the entire upstream output block, plus real fixture receipts."""
    sys.path.insert(0, str(root / os.environ.get("PHASE_RUNTIME_ROOT", ".ai") / "runtime"))
    from phase_records import file_template, record
    data, evidence = record(path)
    template = file_template(root, template_name)
    body = re.sub(r"\A---\n.*?\n---\n", "", template, count=1, flags=re.S)
    # These are deterministic test artifacts, not model judgments. Keep every
    # upstream heading and fill instructional placeholders with fixture evidence.
    body = re.sub(r"\[[^\]\n]+\]", "Fixture output verified", body)
    body = body.replace("XX-name", "01-example").replace("{phase}", "01").replace("{plan}", "01")
    data.update(phase="01-example")
    if template_name == "summary.md":
        data.update(plan="01", subsystem="testing", tags=["fixture"], requires=[],
                    provides=["Assigned fixture output"], affects=[], actuals={"tokens": 10, "tasks": 1, "commits": 1},
                    **{"tech-stack": {"added": [], "patterns": []},
                       "key-files": {"created": ["src/01-01.txt"], "modified": []},
                       "key-decisions": ["Follow assigned fixture"], "patterns-established": [],
                       "coverage": [{"id": "D1", "description": "Assigned fixture output", "requirement": "R1",
                                     "verification": [{"kind": "integration", "ref": "fixture check", "status": "pass"}],
                                     "human_judgment": False}], "duration": "1min", "completed": "2026-09-13"})
        # Runtime Checks is additive; upstream sections keep their own names.
        body += "\n## Checks\n\nFixture check asserted assigned output exists; worker verified integrated dependencies.\n"
    else:
        data.update(verified="2026-09-13T00:00:00Z", score="1/1 must-haves verified", behavior_unverified=0,
                    covered_files=["src/01-01.txt"], covered_digest="fixture-only: not an upstream fingerprint")
        body += "\n" + evidence[evidence.index("## Acceptance"):]
    write_record(path, data, body)


def main() -> int:
    root = Path(os.environ["PHASE_WORKTREE"])
    assignment = Path(os.environ["PHASE_ASSIGNMENT"])
    result = Path(os.environ["PHASE_RESULT"])
    component = os.environ["PHASE_COMPONENT"]
    kind = os.environ["PHASE_KIND"]
    mode = os.environ.get("PHASE_FIXTURE_MODE", "normal")
    if mode.startswith("verifier-") and kind != "verifier":
        mode = "normal"
    event_directory = Path(os.environ["PHASE_FIXTURE_EVENTS"])
    event_directory.mkdir(parents=True, exist_ok=True)
    event_path = event_directory / f"{uuid.uuid4().hex}.yaml"
    event = {
        "component": component,
        "kind": kind,
        "worktree": str(root),
        "pid": os.getpid(),
        "started": time.monotonic(),
    }

    def save_event() -> None:
        temporary = event_path.with_suffix(".tmp")
        temporary.write_text(yaml.safe_dump(event), encoding="utf-8")
        temporary.replace(event_path)

    save_event()
    try:
        assert assignment.is_file(), "The worker must receive an assignment file"
        prompt = assignment.read_text(encoding="utf-8")
        assert prompt.strip(), "The assignment is empty"
        namespace = re.escape(os.environ.get("PHASE_RUNTIME_ROOT", ".ai"))
        methods = sorted(set(re.findall(rf"{namespace}/(?:agents|roles|references)/[a-z-]+\.md", prompt)))
        for method in methods:
            assert (root / method).is_file(), f"Assignment requires missing method: {method}"
            assert (root / method).read_text(encoding="utf-8").strip(), f"Assignment method is empty: {method}"
        event["methods"] = methods
        if kind == "code-reviewer":
            scope_match = re.search(r"(?s)<config>\n(.*?)</config>", prompt)
            assert scope_match, "Reviewer must receive an explicit diff scope"
            scope = yaml.safe_load(scope_match[1])
            revision = git(root, "rev-parse", "HEAD")
            assert git(root, "merge-base", scope["diff_base"], revision) == scope["diff_base"]
            changed = git(root, "diff", "--name-only", scope["diff_base"], revision).splitlines()
            assert set(changed) == set(scope["files"]), "Review scope must cover the actual diff"
            review_mode = os.environ.get("PHASE_FIXTURE_REVIEW_MODE", "clean")
            critical = int(review_mode == "critical")
            warning = int(review_mode == "warning")
            write_record(
                result,
                {"status": "issues_found" if critical or warning else review_mode,
                 "revision": revision, "diff_base": scope["diff_base"],
                 "findings": {"critical": critical, "warning": warning}},
                "# Component review\n\n## Summary\n\nInspected the assigned diff.\n\n"
                "## Critical Issues\n\n" + ("CR-01: Fixture defect.\n" if critical else "None.\n")
                + "\n## Warnings\n\n" + ("### WR-01: Fixture advisory\n\nOptional robustness improvement.\n" if warning else "None.\n"),
            )
            event.update(review_scope=scope, revision=revision, report_written=str(result))
            return 0
        if kind == "verifier":
            scope_match = re.search(r"(?s)<config>\n(.*?)</config>", prompt)
            assert scope_match, "Code-reviewer cannot run without a review scope"
            scope = yaml.safe_load(scope_match[1])
            assert isinstance(scope["files"], list), "Review files must be exact paths"
            assert re.fullmatch(r"[0-9a-f]{40}", scope["diff_base"]), "Review base must be an exact revision"
            event["review_scope"] = scope
            revision = git(root, "rev-parse", "HEAD")
            if mode == "verifier-stale":
                revision = git(root, "rev-parse", "HEAD~1")
            if mode == "verifier-dirty":
                (root / "README.md").write_text("Unauthorized reviewer edit\n", encoding="utf-8")
            verdict = "gaps_found" if mode == "verifier-fail" else "passed"
            write_record(
                result,
                {"status": verdict, "revision": revision},
                "# Phase verification\n\n## Goal Achievement\n\nFixture output works.\n\n"
                "## Requirements Coverage\n\nR1 exercised.\n\n## Anti-Patterns Found\n\nNone.\n\n"
                "## Human Verification Required\n\nNone.\n\n## Acceptance\n\n"
                "Inspected all component outputs and committed summaries.\n\n"
                "## Integration\n\nThe configured integration check passed.\n\n"
                "## Documentation\n\nRequired guide paths exist and match the output.\n\n"
                "## Findings\n\n"
                + ("The requested behavior is missing.\n" if verdict != "passed" else "None.\n"),
            )
            if mode == "full-templates":
                full_template_result(root, result, "verification-report.md")
            event["report_written"] = str(result)
            save_event()
            if mode == "verifier-report-then-wait":
                await_fixture_release()
            return 0

        matches = list((root / ".planning/phases").glob(f"*/{component}-PLAN.md"))
        assert len(matches) == 1, f"No unique instructions for {component}: {matches}"
        instructions = matches[0]
        metadata = frontmatter(instructions)
        for dependency in metadata.get("depends_on", []):
            dependency_instruction = instructions.with_name(f"{dependency}-PLAN.md")
            dependency_summary = instructions.with_name(f"{dependency}-SUMMARY.md")
            assert dependency_summary.is_file(), f"Dependency summary is not integrated: {dependency}"
            for name in frontmatter(dependency_instruction)["files_modified"]:
                assert (root / name).exists(), f"Dependency output is not integrated: {name}"

        time.sleep(float(os.environ.get("PHASE_FIXTURE_DELAY", "0")))
        if component == os.environ.get("PHASE_FIXTURE_FAIL_COMPONENT"):
            print("Deliberate component failure", file=sys.stderr)
            return 7

        if mode.startswith("handoff-") and component == "01-01":
            prior_attempts = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in event_directory.glob("*.yaml") if p != event_path]
            prior_attempts = [e for e in prior_attempts if e["component"] == component and e["kind"] == kind]
            if mode == "handoff-research" and len(prior_attempts) < 2:
                return 75
            target = root / metadata["files_modified"][0]
            if not prior_attempts and mode != "handoff-research":
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("preserved commit\n", encoding="utf-8")
                git(root, "add", "--", str(target.relative_to(root)))
                git(root, "commit", "-m", "Preserve partial component work")
                event["partial_commit"] = git(root, "rev-parse", "HEAD")
                target.write_text("preserved commit\npreserved dirty work\n", encoding="utf-8")
                if mode == "handoff-outside":
                    (root / "outside.txt").write_text("Preserve but reject", encoding="utf-8")
                if mode == "handoff-delete":
                    target.unlink()
                if mode in ("handoff-context", "handoff-permission"):
                    write_record(result, {"status": "blocked", "continuation": "context_limit"},
                                 "# Handoff\n\nPreserved first task. Finish the remaining output and checks.\n")
                    return 0
                if mode == "handoff-wait":
                    event["committed"] = event["partial_commit"]
                    save_event()
                    await_fixture_release()
                    return 75
                save_event()
                if mode == "handoff-truncated":
                    result.write_bytes(b"---\nstatus: blocked\n---\nPartial UTF8: \xe6\x9d")
                if mode in ("handoff-timeout", "handoff-truncated"):
                    time.sleep(120)
                return 75
            if mode == "handoff-permission":
                print("Access is denied", file=sys.stderr)
                return 7
            assert "Required continuation from a stopped worker" in prompt
            if mode != "handoff-research":
                assert target.read_text(encoding="utf-8") == "preserved commit\npreserved dirty work\n"
                assert git(root, "merge-base", prior_attempts[0]["partial_commit"], "HEAD") == prior_attempts[0]["partial_commit"]
            event["continued"] = True

        tdd_evidence = ""
        if mode == "native-tdd":
            test = root / "tests/test_total.py"
            test.write_text("import unittest\nfrom src.total import total\n\nclass TotalTests(unittest.TestCase):\n"
                            "    def test_total_nonempty(self):\n        self.assertEqual(total([1, 2, 3]), 6)\n", encoding="utf-8")
            git(root, "add", "--", "tests/test_total.py")
            git(root, "commit", "-m", "test: specify total returns the sum of nonempty inputs")
            red_commit = git(root, "rev-parse", "HEAD")
            red = subprocess.run(metadata["checks"][0], cwd=root, capture_output=True, text=True)
            assert red.returncode == 1 and "FAIL: test_total_nonempty" in red.stderr and "AssertionError: 0 != 6" in red.stderr, red.stderr
            (root / "src/total.py").write_text("def total(values):\n    return sum(values)\n", encoding="utf-8")
            green = subprocess.run(metadata["checks"][0], cwd=root, capture_output=True, text=True)
            assert green.returncode == 0 and "Ran 1 test" in green.stderr, green.stderr
            git(root, "add", "--", "src/total.py")
            git(root, "commit", "-m", "feat: implement total for nonempty inputs")
            green_commit = git(root, "rev-parse", "HEAD")
            tdd_evidence = (f"\n## TDD Evidence\n\nCommand: {metadata['checks'][0]!r}. Target: TotalTests.test_total_nonempty.\n"
                            f"RED at {red_commit}: exit {red.returncode}; expected total([1, 2, 3]) = 6, actual 0; AssertionError: 0 != 6.\n"
                            f"GREEN at {green_commit}: exit {green.returncode}; one named test passed.\n"
                            "REFACTOR: no further change needed; configured integration check reruns the same behavioral assertion.\n")
        if mode == "repair-bug":
            before = [subprocess.run(argv, cwd=root, capture_output=True).returncode for argv in metadata["checks"]]
            assert any(before), "The regression must fail before repair"

        owned = metadata["files_modified"] + metadata.get("files_deleted", [])
        documentation = metadata.get("documentation", [])
        if mode == "outside":
            owned = ["outside-ownership.txt"]
        if mode == "case-outside":
            owned = ["src/allowed.txt"]
        if mode == "leading-space-outside":
            owned = [" safe.txt"]
        if mode == "leading-space-reverted":
            outside = root / " safe.txt"
            outside.write_text("Out-of-scope history\n", encoding="utf-8")
            git(root, "add", "--", " safe.txt")
            git(root, "commit", "-m", "Temporarily change an unowned path")
            outside.unlink()
            git(root, "add", "--", " safe.txt")
            git(root, "commit", "-m", "Revert the unowned change")
        if mode in ("summary-only", "native-tdd"):
            owned = []
        for name in owned:
            if mode == "missing-documentation" and name in documentation:
                continue
            target = root / name
            if mode == "delete":
                target.unlink()
                continue
            if name.endswith("/"):
                target /= f"{component}.txt"
            target.parent.mkdir(parents=True, exist_ok=True)
            prior = target.read_text(encoding="utf-8") if target.exists() else ""
            target.write_text(
                "def total(values):\n    return sum(values)\n" if mode == "repair-bug"
                else prior + f"{component} implemented\n", encoding="utf-8",
            )

        check_evidence = "Verified required dependency files before writing."
        if mode == "repair-bug":
            after = [subprocess.run(argv, cwd=root, capture_output=True).returncode for argv in metadata["checks"]]
            assert not any(after), "The regression must pass after repair"
            check_evidence = f"Regression before repair: {before}. Regression after repair: {after}."

        summary = instructions.with_name(f"{component}-SUMMARY.md")
        write_record(
            summary,
            {
                "status": "blocked" if mode == "blocked" else "complete",
                "acceptance": metadata.get("acceptance", []),
                "requirements-completed": metadata.get("requirements", []),
                "documentation": [] if mode == "missing-documentation" else documentation,
            },
            f"# Component {component}\n\n## Accomplishments\n\n"
            f"Implemented the owned paths for {component}.\n\n"
            "## Task Commits\n\nCommitted fixture output.\n\n## Files Created/Modified\n\nAssigned paths.\n\n"
            "## Decisions Made\n\nFollow assignment.\n\n## Issues Encountered\n\nNone.\n\n"
            "## User Setup Required\n\nNone.\n\n"
            f"## Checks\n\n{check_evidence}\n\n"
            "## Deviations from Plan\n\nNone.\n\n## Next Phase Readiness\n\n"
            + ("The component needs a decision.\n" if mode == "blocked" else "None.\n"),
        )
        if mode in ("full-templates", "native-tdd"):
            full_template_result(root, summary, "summary.md")
        if tdd_evidence:
            summary.write_text(summary.read_text(encoding="utf-8") + tdd_evidence, encoding="utf-8")
        if result.resolve() != summary.resolve():
            result.parent.mkdir(parents=True, exist_ok=True)
            result.write_text(summary.read_text(encoding="utf-8"), encoding="utf-8")
        if mode != "uncommitted":
            git(root, "add", "--all")
            git(root, "commit", "-m", f"Implement fixture component {component}")
            event["committed"] = git(root, "rev-parse", "HEAD")
            save_event()
        if mode == "complete-then-handoff":
            return 75
        if mode == "commit-then-wait":
            await_fixture_release()
        return 0
    finally:
        event["finished"] = time.monotonic()
        save_event()


if __name__ == "__main__":
    raise SystemExit(forge_cli() if sys.argv[1:2] == ["forge-cli"] else main())
