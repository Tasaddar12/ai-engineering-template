"""Phase verification records and configured project checks."""

from .config import get as config_get
from .paths import read_text
from .phases import find_directory
from .results import VerbError, require
from .roadmap import display_number, pad
from .text import split_frontmatter
from .verification_checks import normalise, run, selected_indices

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
    return normalise(commands, CHECK_TIMEOUT)


def run_checks(workspace, only_checks=None):
    """Run configured checks, reusing only matching, intact passing evidence."""
    commands = configured_checks(workspace)
    if not commands:
        if only_checks is not None:
            selected_indices(only_checks, 0)
        return {"configured": False, "checks": [],
                "note": "verification.commands is empty in .planning/config.yaml"}
    return run(workspace, commands, config_get(workspace, "verification", {}), CHECK_TIMEOUT, only_checks)


def qualify_successor(workspace, evidence_file, report_only_paths, expected_head, fresh_evidence_file=None):
    from .verification_checks import read_evidence, validate_successor
    try:
        evidence = read_evidence(evidence_file)
        fresh = read_evidence(fresh_evidence_file) if fresh_evidence_file else None
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        raise VerbError('cannot read successor evidence: ' + str(exc), 'bad-evidence') from None
    return validate_successor(workspace, evidence, report_only_paths, expected_head,
                              configured_checks(workspace), config_get(workspace, 'verification', {}),
                              CHECK_TIMEOUT, fresh)
