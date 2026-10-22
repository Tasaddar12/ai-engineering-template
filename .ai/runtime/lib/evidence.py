"""Read-only mechanical evidence extraction; never an acceptance verdict."""
import os
import subprocess

from .results import VerbError, require
from .verification_checks import git as raw_git, read_evidence


def git(workspace, *args):
    try:
        return raw_git(workspace.root, *args)
    except (OSError, subprocess.SubprocessError) as exc:
        raise VerbError("cannot extract Git evidence: " + str(exc), "git-failed") from None


CHECK_FIELDS = ("full_index", "command", "exit_code", "passed", "tested_revision",
                "snapshot_valid", "reused", "receipt", "stdout_log", "stderr_log", "error")
BATCH_FIELDS = ("ok", "configured", "passed", "snapshot_valid", "tested_revision",
                "partial", "selected_indices", "selected_passed",
                "full_configuration_sha256", "full_order_sha256")


def revision(workspace, value):
    require(isinstance(value, str) and value and not value.startswith("-"),
            "a Git commit reference is required", "bad-revision")
    return git(workspace, "rev-parse", "--verify", "--end-of-options",
               value + "^{commit}").decode("ascii").strip()


def check_summary(path):
    """Project recorded fields without authenticating or requalifying receipts."""
    try:
        evidence = read_evidence(path)
    except (OSError, ValueError, TypeError, RecursionError) as exc:
        raise VerbError("cannot read check evidence: " + str(exc), "bad-evidence") from None
    checks = evidence.get("checks")
    require(isinstance(checks, list) and all(isinstance(row, dict) for row in checks),
            "check evidence requires a checks list of objects", "bad-evidence")
    counts = {"total": len(checks), "passed": 0, "failed": 0, "unknown": 0,
              "reused": 0, "receipts": 0}
    rows = []
    for index, check in enumerate(checks):
        passed = check.get("passed")
        counts["passed" if passed is True else "failed" if passed is False else "unknown"] += 1
        counts["reused"] += check.get("reused") is True
        counts["receipts"] += isinstance(check.get("receipt"), str) and bool(check["receipt"])
        row = {key: check[key] for key in CHECK_FIELDS if key in check}
        row["result_index"] = index
        for stream in ("stdout", "stderr"):
            tail = check.get(stream + "_tail")
            if isinstance(tail, str):
                row[stream + "_tail"] = tail[-2000:]
        rows.append(row)
    return {"source": str(path), "validation": "recorded-only",
            "batch": {key: evidence[key] for key in BATCH_FIELDS if key in evidence},
            "counts": counts, "checks": rows}


def extract(workspace, base, head="HEAD", evidence_file=None):
    """Extract an explicit committed range and optionally existing check JSON."""
    require(evidence_file is None or (isinstance(evidence_file, (str, os.PathLike))
                                     and str(os.fspath(evidence_file)).strip()),
            "evidence_file requires a nonblank path", "missing-argument")
    base_sha, head_sha = revision(workspace, base), revision(workspace, head)
    # --no-renames accounts for both removed and added paths; -z preserves
    # whitespace/newlines and avoids Git's quoted display-path format.
    changed = git(workspace, "diff", "--no-ext-diff", "--no-textconv",
                  "--name-only", "--no-renames", "-z",
                  base_sha, head_sha, "--")
    commits = git(workspace, "rev-list", "--reverse", base_sha + ".." + head_sha,
                  "--").decode("ascii").splitlines()
    return {"base_revision": base_sha, "head_revision": head_sha,
            "scope": "committed-endpoint-diff",
            "changed_paths": sorted(os.fsdecode(path) for path in changed.split(b"\0") if path),
            "commit_ids": commits,
            "check_evidence": check_summary(evidence_file) if evidence_file is not None else None}
