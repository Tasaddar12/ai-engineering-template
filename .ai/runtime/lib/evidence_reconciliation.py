"""Read-only SHA/result reconciliation; never publish logs or rewrite evidence."""
import re
import subprocess

from . import verification_checks as checks
from . import verification_successors as successors


def sha(value):
    return isinstance(value, str) and re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", value) is not None


def local_rows(root, evidence):
    """Authenticate successful or failed observations without relaxing reuse rules."""
    rows = evidence.get("checks")
    if (evidence.get("configured") is not True or evidence.get("snapshot_valid") is not True
            or evidence.get("partial", False) is not False or not isinstance(rows, list) or not rows):
        raise ValueError("complete stable configured check evidence required")
    observations, inputs = [], []
    for index, row in enumerate(rows):
        reference = row["receipt"]
        if (not isinstance(reference, str) or not reference.startswith(checks.STORE + "/")
                or len(reference.split("/")) != 3):
            raise ValueError("invalid receipt reference")
        path = successors.safe_path(root, reference)
        envelope = checks.strict_json(path.read_text(encoding="utf-8"))
        receipt = envelope["receipt"]
        original = receipt["result"]
        captured = receipt["inputs"]
        key = checks.digest(captured)
        if (type(receipt.get("schema")) is not int or receipt["schema"] != checks.SCHEMA
                or receipt.get("key") != key or path.name != key + ".json"
                or envelope.get("sha256") != checks.digest(receipt)
                or checks.digest(dict(row, reused=False)) != checks.digest(original)
                or type(row.get("reused")) is not bool or original.get("reused") is not False
                or original.get("snapshot_valid") is not True
                or original.get("command") != captured.get("command")
                or type(original.get("full_index")) is not int or original["full_index"] != index
                or type(captured.get("index")) is not int or captured["index"] != index
                or not sha(original.get("tested_revision"))
                or type(original.get("exit_code")) is not int
                or type(original.get("passed")) is not bool
                or original["passed"] != (original["exit_code"] == 0)
                or original.get("error")):
            raise ValueError("receipt/result identity or terminal result mismatch")
        for stream in ("stdout", "stderr"):
            record = receipt[stream]
            name = record["file"]
            if (not isinstance(name, str) or "/" in name or "\\" in name
                    or not name.endswith("." + stream + ".log")):
                raise ValueError("invalid private log reference")
            log_ref = checks.STORE + "/" + name
            log = successors.safe_path(root, log_ref)
            if (original.get(stream + "_log") != log_ref
                    or checks.file_digest(log) != record["sha256"]
                    or original.get(stream + "_tail") != checks.tail(log)):
                raise ValueError("private log integrity mismatch")
        inputs.append(captured)
        observations.append({"actual_revision": original["tested_revision"],
                             "terminal_result": "Passed" if original["passed"] else "Failed",
                             "evidence_ref": reference})
    passed = all(row["terminal_result"] == "Passed" for row in observations)
    if evidence.get("passed") is not passed:
        raise ValueError("aggregate result contradicts receipts")
    return observations, inputs


def provider_row(evidence, kind):
    """Use the run's SHA, never a PR head SHA or a caller's claimed revision."""
    if kind == "github":
        revision, status, conclusion = evidence.get("head_sha"), evidence.get("status"), evidence.get("conclusion")
        event = evidence.get("event")
        if status in {"queued", "in_progress", "waiting", "pending", "requested"}:
            terminal = "Pending"
        elif status == "completed":
            terminal = ("Passed" if conclusion == "success" else "Failed" if conclusion in
                        {"failure", "cancelled", "timed_out", "action_required", "startup_failure"} else "Unverified")
        else:
            terminal = "Unverified"
    else:
        revision, status = evidence.get("sha"), evidence.get("status")
        event = evidence.get("source")
        terminal = ("Passed" if status == "success" else "Failed" if status in {"failed", "canceled"}
                    else "Pending" if status in {"created", "waiting_for_resource", "preparing", "pending", "running", "scheduled", "manual"}
                    else "Unverified")
    if not sha(revision) or not evidence.get("id"):
        raise ValueError("provider run requires its own full SHA and run id")
    # A PR workflow/pipeline can execute a merge checkout or trusted base code.
    # Keep that provenance distinct; never label its workflow SHA as the PR test.
    direct_events = {"push", "workflow_dispatch", "schedule"} if kind == "github" else {"push", "web", "schedule", "api"}
    actual = revision if event in direct_events else None
    return {"actual_revision": actual if sha(actual) else None, "provider_run_revision": revision,
            "provider_event": event, "terminal_result": terminal, "run_id": evidence["id"]}


def reconcile(workspace, evidence_file, claimed_revision, expected_head, kind="local",
              report_only_paths=None, fresh_evidence_file=None, provider_run=None, repository=None):
    result = {"classification": "Unverified", "claimed_revision": claimed_revision,
              "candidate_revision": expected_head, "kind": kind,
              "evidence_ref": str(evidence_file) if evidence_file is not None else None,
              "observations": [], "terminal_result": "Unverified", "current": False}
    try:
        if not sha(claimed_revision) or not sha(expected_head):
            raise ValueError("claimed revision and candidate must be full lowercase commit SHAs")
        root = workspace.root.resolve()
        if checks.git(root, "rev-parse", "HEAD").decode().strip() != expected_head:
            raise ValueError("candidate differs from current HEAD")
        if checks.git(root, "status", "--porcelain", "--untracked-files=all").strip():
            raise ValueError("candidate worktree is dirty")
        live = provider_run is not None
        if live:
            if (kind != "github" or not isinstance(provider_run, str) or not provider_run.isascii()
                    or not provider_run.isdigit() or not isinstance(repository, str)
                    or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
                    or any(part in {".", ".."} for part in repository.split("/"))):
                raise ValueError("live provider read requires kind github, numeric provider-run and owner/repository")
            from .delivery import gh
            from .results import VerbError
            try:
                response = gh(workspace, "api", "repos/" + repository + "/actions/runs/" + provider_run, check=True)
            except VerbError as exc:
                raise ValueError("provider read unavailable: " + str(exc)) from None
            evidence = checks.strict_json(response.stdout)
            if not isinstance(evidence, dict) or str(evidence.get("id")) != provider_run:
                raise ValueError("provider returned a different run identity")
            result["evidence_ref"] = "github:" + repository + "/actions/runs/" + provider_run
        else:
            evidence = checks.read_evidence(evidence_file)
        if evidence.get("ok", True) is not True:
            raise ValueError("evidence reports an unsuccessful runtime operation")
        if kind == "local":
            rows, original_inputs = local_rows(root, evidence)
        elif kind in {"github", "gitlab"}:
            rows = [provider_row(evidence, kind)]
        else:
            raise ValueError("kind must be local, github or gitlab")
        result["observations"] = rows
        terminals = {row["terminal_result"] for row in rows}
        result["terminal_result"] = next((s for s in ("Failed", "Unverified", "Pending", "Passed") if s in terminals))
        if kind != "local" and not live:
            raise ValueError("caller-supplied provider snapshot provenance is Unverified; live provider read required")
        if any(not sha(row["actual_revision"]) for row in rows):
            raise ValueError("provider workflow SHA does not establish actual PR/merge checkout tested_revision")
        if any(row["actual_revision"] != claimed_revision for row in rows):
            raise ValueError("claimed tested SHA differs from actual run SHA")
        if kind == "local" and evidence.get("tested_revision") != claimed_revision:
            raise ValueError("aggregate tested SHA differs from actual receipt SHA")
        if claimed_revision != expected_head:
            if kind != "local" or not report_only_paths:
                raise ValueError("actual run SHA does not cover current candidate; fresh evidence required")
            from .verification import qualify_successor
            qualification = qualify_successor(workspace, evidence_file, report_only_paths,
                                              expected_head, fresh_evidence_file)
            result["successor"] = {key: qualification[key] for key in
                                   ("qualified", "tested_revision", "qualified_revision", "reason",
                                    "fresh_required", "qualifications", "original_receipts")}
            if qualification["qualified"] is not True:
                raise ValueError(qualification["reason"])
        elif kind == "local":
            from .verification import configured_checks, CHECK_TIMEOUT
            from .config import get
            import os
            commands = configured_checks(workspace)
            _, current_inputs = checks.capture_inputs(root, commands, get(workspace, "verification", {}),
                                                      CHECK_TIMEOUT, expected_head, os.environ.copy())
            if checks.digest(original_inputs) != checks.digest(current_inputs):
                raise ValueError("receipt inputs do not match current configured checks")
        if checks.git(root, "rev-parse", "HEAD").decode().strip() != expected_head or checks.git(
                root, "status", "--porcelain", "--untracked-files=all").strip():
            raise ValueError("candidate moved during reconciliation")
        result.update(current=True, classification=result["terminal_result"], reason="run SHA and candidate reconciled")
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RecursionError, subprocess.SubprocessError) as exc:
        result["reason"] = str(exc)
    return result
