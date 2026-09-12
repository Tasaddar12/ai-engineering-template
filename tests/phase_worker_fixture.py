"""Deterministic, committing worker for phase-runtime integration tests only."""

from __future__ import annotations

import os
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
        assert assignment.read_text(encoding="utf-8").strip(), "The assignment is empty"
        if kind == "verifier":
            revision = git(root, "rev-parse", "HEAD")
            if mode == "verifier-stale":
                revision = git(root, "rev-parse", "HEAD~1")
            if mode == "verifier-dirty":
                (root / "README.md").write_text("Unauthorized reviewer edit\n", encoding="utf-8")
            verdict = "gaps_found" if mode == "verifier-fail" else "passed"
            write_record(
                result,
                {"status": verdict, "revision": revision},
                "# Phase verification\n\n## Acceptance\n\n"
                "Inspected all component outputs and committed summaries.\n\n"
                "## Integration\n\nThe configured integration check passed.\n\n"
                "## Documentation\n\nRequired guide paths exist and match the output.\n\n"
                "## Findings\n\n"
                + ("The requested behavior is missing.\n" if verdict != "passed" else "None.\n"),
            )
            event["report_written"] = str(result)
            save_event()
            if mode == "verifier-report-then-wait":
                await_fixture_release()
            return 0

        matches = list((root / ".ai/phases").glob(f"*/{component}-IMPLEMENT.md"))
        assert len(matches) == 1, f"No unique instructions for {component}: {matches}"
        instructions = matches[0]
        metadata = frontmatter(instructions)
        for dependency in metadata.get("depends_on", []):
            dependency_instruction = instructions.with_name(f"{dependency}-IMPLEMENT.md")
            dependency_summary = instructions.with_name(f"{dependency}-SUMMARY.md")
            assert dependency_summary.is_file(), f"Dependency summary is not integrated: {dependency}"
            for name in frontmatter(dependency_instruction)["files"]:
                assert (root / name).exists(), f"Dependency output is not integrated: {name}"

        time.sleep(float(os.environ.get("PHASE_FIXTURE_DELAY", "0")))
        if component == os.environ.get("PHASE_FIXTURE_FAIL_COMPONENT"):
            print("Deliberate component failure", file=sys.stderr)
            return 7

        if mode == "repair-bug":
            before = [subprocess.run(argv, cwd=root, capture_output=True).returncode for argv in metadata["checks"]]
            assert any(before), "The regression must fail before repair"

        owned = metadata["files"]
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
        if mode == "summary-only":
            owned = []
        for name in owned:
            if mode == "missing-documentation" and name in documentation:
                continue
            target = root / name
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
                "documentation": [] if mode == "missing-documentation" else documentation,
            },
            f"# Component {component}\n\n## Changes\n\n"
            f"Implemented the owned paths for {component}.\n\n"
            f"## Checks\n\n{check_evidence}\n\n"
            "## Deviations\n\nNone.\n\n## Remaining\n\n"
            + ("The component needs a decision.\n" if mode == "blocked" else "None.\n"),
        )
        if result.resolve() != summary.resolve():
            result.parent.mkdir(parents=True, exist_ok=True)
            result.write_text(summary.read_text(encoding="utf-8"), encoding="utf-8")
        if mode != "uncommitted":
            git(root, "add", "--all")
            git(root, "commit", "-m", f"Implement fixture component {component}")
            event["committed"] = git(root, "rev-parse", "HEAD")
            save_event()
        if mode == "commit-then-wait":
            await_fixture_release()
        return 0
    finally:
        event["finished"] = time.monotonic()
        save_event()


if __name__ == "__main__":
    raise SystemExit(forge_cli() if sys.argv[1:2] == ["forge-cli"] else main())
