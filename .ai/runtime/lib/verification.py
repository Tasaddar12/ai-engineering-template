"""Phase verification records and configured project checks."""
import subprocess

from .config import get as config_get
from .paths import read_text
from .phases import find_directory
from .results import VerbError, require
from .roadmap import display_number, pad
from .text import split_frontmatter

STATUSES = ("passed", "gaps_found", "human_needed")
CHECK_TIMEOUT = 600


def report_path(workspace, number):
    directory = find_directory(workspace, number)
    if directory is None:
        return None
    candidate = directory / (pad(number) + "-VERIFICATION.md")
    return candidate if candidate.is_file() else None


def status(workspace, number):
    """Whether a phase has a verification report, and what it concluded."""
    path = report_path(workspace, number)
    if path is None:
        return {"phase": display_number(number), "exists": False, "status": None,
                "file": None}
    frontmatter, body = split_frontmatter(read_text(path, ""))
    declared = str(frontmatter.get("status") or "").strip() or None
    return {
        "phase": display_number(number),
        "exists": True,
        "file": workspace.relative(path),
        "status": declared,
        "known_status": declared in STATUSES,
        "revision": frontmatter.get("revision"),
        "verified_at": str(frontmatter.get("verified_at") or ""),
        "findings": frontmatter.get("findings") or {},
        "has_body": bool(body.strip()),
    }


def resolve_file(workspace, number):
    """Path a verifier should write, whether or not it exists yet."""
    directory = find_directory(workspace, number)
    require(directory is not None, "no phase directory for " + str(number), "no-phase-dir")
    return {"file": workspace.relative(directory / (pad(number) + "-VERIFICATION.md")),
            "exists": report_path(workspace, number) is not None}


def configured_checks(workspace):
    commands = config_get(workspace, "verification.commands", []) or []
    normalised = []
    for command in commands:
        if isinstance(command, str):
            normalised.append(command.split())
        elif isinstance(command, (list, tuple)):
            normalised.append([str(part) for part in command])
        else:
            raise VerbError("verification.commands entries must be strings or lists",
                            "bad-config")
    return normalised


def run_checks(workspace):
    """Run the project's configured verification commands."""
    commands = configured_checks(workspace)
    if not commands:
        return {"configured": False, "checks": [],
                "note": "verification.commands is empty in .planning/config.yaml"}
    results = []
    for command in commands:
        try:
            completed = subprocess.run(command, cwd=str(workspace.root), capture_output=True,
                                       text=True, timeout=CHECK_TIMEOUT)
            results.append({
                "command": command,
                "exit_code": completed.returncode,
                "passed": completed.returncode == 0,
                "stdout_tail": completed.stdout[-2000:],
                "stderr_tail": completed.stderr[-2000:],
            })
        except (OSError, subprocess.TimeoutExpired) as exc:
            results.append({"command": command, "exit_code": None, "passed": False,
                            "error": str(exc)})
    return {"configured": True, "checks": results,
            "passed": all(item["passed"] for item in results)}
