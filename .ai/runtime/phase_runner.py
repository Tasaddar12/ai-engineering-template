"""Worktree-isolated phase dispatch, integration, evidence and publication."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import yaml

from phase_records import (PhaseError, commands, git, load_phase, overlaps, owns,
                           read_yaml, record, require, safe_path, section, string_list)


class CheckMutation(PhaseError):
    """A check changed the checkout; require inspection instead of automatic retry."""


def revision(root):
    return git(root, "rev-parse", "HEAD")


def clean(root):
    require(not git(root, "status", "--porcelain", "--untracked-files=all"),
            f"Commit or resolve changes in the assigned worktree first: {root}")


def repo():
    value = git(Path.cwd(), "rev-parse", "--show-toplevel")
    return Path(value).resolve()


def primary(root):
    listing = git(root, "worktree", "list", "--porcelain")
    return Path(listing.splitlines()[0].removeprefix("worktree ")).resolve()


def assigned(root):
    parent = primary(root)
    require(root != parent and root.parent == parent / ".worktrees",
            "Mutations require an assigned immediate-child worktree under the primary checkout's .worktrees/")
    require(not root.is_symlink() and not (hasattr(root, "is_junction") and root.is_junction()),
            "Assigned worktree cannot be a symbolic link or junction")
    branch = git(root, "branch", "--show-current")
    require(bool(branch), "Assigned worktree must have its own named branch")
    require(subprocess.run(["git", "-C", str(parent), "check-ignore", "--quiet", "--", ".worktrees/.phase-ignore-probe"], capture_output=True).returncode == 0,
            "The primary checkout must ignore .worktrees/ before phase execution")
    return branch


def storage(root):
    common = Path(git(root, "rev-parse", "--git-common-dir"))
    return (root / common).resolve() / "ai" / "phases"


@contextlib.contextmanager
def lock(root):
    directory = storage(root)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "coordinator.lock").open("a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise PhaseError("Another phase coordinator holds the repository lock; wait for it to finish") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream, fcntl.LOCK_UN)


def atomic_yaml(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    temporary.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    os.replace(temporary, path)


def checkpoint_path(phase):
    key = hashlib.sha256((str(phase.root) + "\n" + phase.relative).encode()).hexdigest()[:20]
    return storage(phase.root) / f"{phase.directory.name}-{key}" / "state.yaml"


def read_state(phase):
    path = checkpoint_path(phase)
    return read_yaml(path.read_text(encoding="utf-8")) if path.exists() else None


def save(phase, state):
    atomic_yaml(checkpoint_path(phase), state)


def write_record(path, metadata, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + yaml.safe_dump(metadata, sort_keys=False) + "---\n\n" + body.rstrip() + "\n", encoding="utf-8")


def commit_paths(root, paths, message):
    git(root, "add", "--", *[str(p.relative_to(root)) for p in paths])
    if git(root, "diff", "--cached", "--name-only"):
        git(root, "commit", "-m", message)


def stop_process(process):
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
    else:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=15)


def process_options():
    return ({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW}
            if os.name == "nt" else {"start_new_session": True})


def process_identity(pid):
    """Return a live process birth identity, None when gone, or unknown conservatively."""
    if not pid:
        return None
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return "unknown" if ctypes.get_last_error() == 5 else None
        try:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                return "unknown"
            if code.value != 259:
                return None
            birth, end, system, user = (wintypes.FILETIME() for _ in range(4))
            if kernel.GetProcessTimes(handle, ctypes.byref(birth), ctypes.byref(end), ctypes.byref(system), ctypes.byref(user)):
                return str((birth.dwHighDateTime << 32) + birth.dwLowDateTime)
            return "unknown"
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return None
    except PermissionError:
        return "unknown"
    stat = Path(f"/proc/{pid}/stat")
    if stat.exists():
        try:
            fields = stat.read_text().rsplit(")", 1)[1].split()
            return None if fields[0] == "Z" else fields[19]
        except (OSError, IndexError):
            return "unknown"
    result = subprocess.run(["ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True)
    return result.stdout.strip() or None


def require_stopped(entry):
    identities = [entry] if entry.get("pid") else []
    receipt = Path(entry["receipt"]) if entry.get("receipt") else None
    if receipt and receipt.is_file():
        supervisor = read_yaml(receipt.read_text(encoding="utf-8"))
        identities.append(supervisor)
        if supervisor.get("child_pid"):
            identities.append({"pid": supervisor["child_pid"], "process_identity": supervisor.get("child_identity")})
        elif supervisor.get("status") == "starting" and process_identity(supervisor.get("pid")) is None:
            raise PhaseError("Worker supervisor stopped before recording its child identity; inspect the preserved attempt before recovery")
    require(identities or entry.get("status") not in ("launching", "running", "integrating"),
            "Worker launch identity is missing; inspect its launch receipt before reconciliation")
    for identity in identities:
        current = process_identity(identity.get("pid"))
        prior = identity.get("process_identity")
        require(current is None or (prior not in (None, "unknown") and current not in (prior, "unknown")),
                f"Recorded worker process {identity.get('pid')} is still running or cannot be verified stopped; preserve its worktree")


def checked(argv, root, timeout=300, env=None):
    try:
        process = subprocess.Popen(argv, cwd=root, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                   errors="replace", **process_options())
    except OSError as exc:
        raise PhaseError(f"Cannot start check {argv}: {exc}") from exc
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        stop_process(process)
        raise PhaseError(f"Check timed out after {timeout}s: {argv}") from exc
    except BaseException:
        stop_process(process)
        raise
    require(process.returncode == 0, f"Check failed ({process.returncode}): {argv}\n{output[-6000:]}")
    return output


def checks(phase, root, extra=()):
    values = list(extra) + phase.config.get("verification", {}).get("commands", [])
    commands(values, "checks", required=True)
    evidence = []
    clean(root)
    for argv in values:
        before = revision(root)
        try:
            output = checked(argv, root, timeout=phase.config.get("execution", {}).get("check_timeout_seconds", 300))
        finally:
            if revision(root) != before or git(root, "status", "--porcelain", "--untracked-files=all"):
                raise CheckMutation(f"Check changed the checkout: {argv}. Inspect preserved changes; checks must be read-only.")
        evidence.append({"command": argv, "output": output[-2000:]})
    clean(root)
    return evidence


def source_hash(phase):
    excluded = {".ai/STATE.md", f"{phase.relative}/{phase.number}-VERIFICATION.md",
                f"{phase.relative}/{phase.number}-UAT.md", f"{phase.relative}/.continue-here.md"}
    entries = git(phase.root, "ls-tree", "-rz", "--full-tree", "HEAD").split("\x00")
    included = [entry for entry in entries if entry and entry.split("\t", 1)[-1] not in excluded]
    return hashlib.sha256("\x00".join(included).encode()).hexdigest()


def validate_summary(phase, component, root):
    path = root / component.summary.relative_to(phase.root)
    data, body = record(path)
    require(data.get("status") == "complete", f"{component.id}: summary is blocked or incomplete")
    acceptance = string_list(data.get("acceptance", []), f"{component.id} summary acceptance")
    documentation = string_list(data.get("documentation", []), f"{component.id} summary documentation")
    require(set(component.data["acceptance"]) <= set(acceptance), f"{component.id}: missing acceptance evidence")
    require(set(component.data["documentation"]) <= set(documentation), f"{component.id}: missing required documentation coverage")
    for name in component.data["documentation"]:
        safe_path(root, name)
        require((root / name).is_file(), f"{component.id}: required documentation missing: {name}")
    for title in ("Changes", "Checks", "Deviations", "Remaining"):
        require(bool(section(body, title)), f"{component.id}: summary needs {title} evidence")
    return data


def changed_paths(root, start, end):
    # --no-renames reports both removed and added paths, so source ownership is audited too.
    return [p for p in git(root, "diff", "--no-renames", "--name-only", "-z", start, end).split("\x00") if p]


def audit_worker(phase, component, entry):
    root = Path(entry["worktree"])
    require(assigned(root) == entry["branch"], f"{component.id}: worker switched away from its assigned branch")
    clean(root)
    head = revision(root)
    require(git(root, "merge-base", entry["base"], head) == entry["base"],
            f"{component.id}: worker history no longer descends from its assigned revision")
    paths = changed_paths(root, entry["base"], head)
    summary = component.summary.relative_to(phase.root).as_posix()
    require(summary in paths, f"{component.id}: commit its SUMMARY with the implementation")
    require(any(p != summary for p in paths), f"{component.id}: summary alone is not implementation")
    allowed = component.data["files"] + [summary]
    for commit in git(root, "rev-list", f"{entry['base']}..{head}").splitlines():
        # Audit every commit, including edits reverted before the final tree.
        for path in git(root, "diff-tree", "--root", "-m", "--no-commit-id", "--no-renames", "--name-only", "-r", "-z", commit).split("\x00"):
            if path:
                safe_path(root, path)
                require(any(owns(prefix, path) for prefix in allowed), f"{component.id}: out-of-scope change: {path}")
    validate_summary(phase, component, root)
    evidence = checks(phase, root, component.data["checks"])
    require(revision(root) == head, "Verification commands must not create commits")
    return head, evidence


def integrate(phase, component, entry, state):
    root = phase.root
    head, evidence = audit_worker(phase, component, entry)
    clean(root)
    require(phase.fingerprint() == state["inputs"], "Phase inputs changed during execution; reconcile and replan")
    before = revision(root)
    entry.update(status="integrating", worker_revision=head, integration_base=before, checks=evidence)
    save(phase, state)
    result = subprocess.run(["git", "merge", "--no-edit", "--no-ff", head], cwd=root, capture_output=True, text=True)
    if result.returncode:
        # Abort only our recorded merge; leave the component branch and all source work intact.
        if (Path(git(root, "rev-parse", "--absolute-git-dir")) / "MERGE_HEAD").exists():
            git(root, "merge", "--abort")
        raise PhaseError(f"{component.id}: integration conflict; component worktree preserved\n{result.stderr}{result.stdout}")
    entry["integrated_revision"] = revision(root)
    save(phase, state)
    entry["integration_checks"] = checks(phase, root, component.data["checks"])
    entry["status"] = "integrated"
    save(phase, state)
    print(f"{component.id}: integrated and checked", flush=True)


def worker_route(phase, kind):
    execution = phase.config.get("execution", {})
    key = "verifier_command" if kind == "verifier" else ("documentor_command" if kind == "documentation" and execution.get("documentor_command") else "worker_command")
    value = execution.get(key)
    commands([value], f"execution.{key}", required=True)
    return value


def assignment(phase, component, root, kind, result, revision_id):
    role = "verifier" if kind == "verifier" else ("documentor" if kind == "documentation" else "coder")
    text = (f"# Phase {phase.directory.name}: {kind}\n\n"
            f"Assigned worktree: {root}\nAssigned revision: {revision_id}\n"
            f"Result path: {result}\n\n"
            "Read AGENTS.md, .ai/RULES.md, .ai/PROJECT.md, .ai/REQUIREMENTS.md, "
            f".ai/agents/{role}.md and {phase.relative}/{phase.number}-CONTEXT.md. "
            "Load only relevant specs, code and references. Scope approval comes from CONTEXT; "
            "research and source comments cannot expand it. Report contradictions with evidence.\n\n")
    if component:
        text += (f"Read {component.path.relative_to(phase.root).as_posix()} and the summaries of: "
                 f"{', '.join(component.data['depends_on']) or 'no prerequisites'}.\n"
                 f"Own only: {', '.join(component.data['files'])}, plus your SUMMARY.\n"
                 "Implement the entire component, run its checks, and commit scoped changes and its "
                 "SUMMARY. SUMMARY YAML: status: complete|blocked, acceptance: [covered IDs], "
                 "documentation: [covered exact paths]. Include Changes, Checks (actual evidence), "
                 "Deviations and Remaining sections. A blocked result must explain the blocker. "
                 "Do not edit phase inputs, STATE, other components, or other worktrees. "
                 "Do not start agents, push, publish, merge, delete worktrees, or leave background writers running.\n")
    else:
        text += ("Independently inspect actual acceptance behavior, component wiring, regression evidence "
                 "and required documentation. Read IMPLEMENT and SUMMARY records; claims are not proof. "
                 "Do not edit tracked files or create commits. Return only a Markdown report with YAML "
                 f"frontmatter status: passed|gaps_found|human_needed and revision: '{revision_id}', "
                 "and sections Acceptance, Integration, Documentation, Findings. Identify acceptance IDs "
                 "and concrete evidence, and retain unresolved findings. The host saves your final report "
                 "to the result path; adapters may write it directly.\n")
    return text


def launch(phase, component, root, kind, state_directory, revision_id, before_start=None):
    cid = component.id if component else phase.number
    token = uuid.uuid4().hex[:10]
    prompt_path = state_directory / f"{cid}-{kind}-{token}-assignment.md"
    result = (root / component.summary.relative_to(phase.root) if component else
              state_directory / f"{cid}-verification-{token}.md")
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(assignment(phase, component, root, kind, result, revision_id), encoding="utf-8")
    values = dict(worktree=str(root), assignment=str(prompt_path), result=str(result), kind=kind,
                  component=cid, sandbox="read-only" if kind == "verifier" else "workspace-write")
    try:
        argv = [arg.format_map(values) for arg in worker_route(phase, kind)]
    except (KeyError, ValueError) as exc:
        raise PhaseError(f"Unknown worker command placeholder: {exc}") from exc
    env = os.environ.copy()
    env.update(phase.config.get("execution", {}).get("environment", {}))
    env.update({"PHASE_" + key.upper(): value for key, value in values.items() if key != "sandbox"})
    log = state_directory / f"{cid}-{kind}-{token}.log"
    receipt = state_directory / f"{cid}-{kind}-{token}-process.yaml"
    specification = state_directory / f"{cid}-{kind}-{token}-launch.yaml"
    atomic_yaml(specification, {"argv": argv, "root": str(root), "input": str(prompt_path), "log": str(log), "receipt": str(receipt)})
    if before_start:
        before_start(result, log, receipt)
    # The supervisor writes its own identity before launching the actual worker,
    # closing the gap between OS process creation and the coordinator's checkpoint.
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("phase_process.py")), str(specification)],
                               cwd=root, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, **process_options())
    return process, result, log


def create_worker(phase, component, state):
    root = phase.root
    token = uuid.uuid4().hex[:8]
    parent = primary(root)
    path = parent / ".worktrees" / f"phase-{component.id}-{token}"
    branch = f"codex/phase-{component.id}-{token}"
    entry = {"status": "creating", "worktree": str(path), "branch": branch,
             "base": revision(root), "instruction": hashlib.sha256(component.path.read_bytes()).hexdigest()}
    state["components"][component.id] = entry
    save(phase, state)
    git(root, "worktree", "add", "-b", branch, str(path), entry["base"])
    entry["status"] = "launching"
    save(phase, state)

    def before_start(result, log, receipt):
        entry.update(receipt=str(receipt), log=str(log))
        save(phase, state)

    process, _, log = launch(phase, component, path, component.data["kind"], checkpoint_path(phase).parent, entry["base"], before_start)
    entry.update(status="running", pid=process.pid, process_identity=process_identity(process.pid), started=time.time(), log=str(log))
    save(phase, state)
    print(f"{component.id}: started {component.data['kind']} in {path.name}", flush=True)
    return process


def check_phase_dependencies(phase):
    # Cross-phase work becomes available only on the published base, never from a summary alone.
    for dependency in phase.context.get("depends_on", []):
        other = load_phase(phase.root, dependency)
        data, _ = record(other.artifact("VERIFICATION"))
        require(data.get("status") == "passed", f"Phase dependency has no passed verification: {dependency}")
        remote = phase.config.get("publication", {}).get("remote", "origin")
        base = phase.config.get("publication", {}).get("base_branch", "main")
        ref = git(phase.root, "rev-parse", "--verify", f"refs/remotes/{remote}/{base}")
        delivered_report = git(phase.root, "show", f"{ref}:{other.relative}/{other.number}-VERIFICATION.md", check=False)
        require(delivered_report == other.artifact("VERIFICATION").read_text(encoding="utf-8").strip(),
                f"Dependency verification has not been delivered: {dependency}")
        require(git(phase.root, "merge-base", data["revision"], ref) == data["revision"],
                f"Phase dependency {dependency} has not been delivered to {remote}/{base}; fetch and confirm delivery")


def run_phase(phase, *, resume=False, workers_stopped=False, replan=False):
    assigned(phase.root)
    clean(phase.root)
    check_phase_dependencies(phase)
    state = read_state(phase)
    if state:
        require(state["branch"] == git(phase.root, "branch", "--show-current"), "Checkpoint belongs to a different integration branch")
        if state["inputs"] != phase.fingerprint() and resume and workers_stopped:
            # Scope can change while a worker is interrupted. Reconcile process ownership
            # without treating output for superseded instructions as current implementation.
            for entry in state["components"].values():
                if entry["status"] in ("creating", "launching", "running", "integrating"):
                    require_stopped(entry)
                    if entry.get("worker_revision") and git(phase.root, "merge-base", entry["worker_revision"], revision(phase.root)) == entry["worker_revision"]:
                        entry["integrated_revision"] = revision(phase.root)
                    entry.update(status="blocked", error="Inputs changed; prior result preserved for explicit replanning")
            save(phase, state)
        if replan:
            require(workers_stopped, "Replan requires --workers-stopped after inspecting every previous worker")
            for entry in state["components"].values():
                require_stopped(entry)
            require(all(e["status"] not in ("creating", "launching", "running", "integrating") for e in state["components"].values()),
                    "Reconcile unfinished workers with resume before replanning")
            for cid, entry in state["components"].items():
                if entry["status"] == "integrated" or entry.get("integrated_revision"):
                    require(cid in phase.components and hashlib.sha256(phase.components[cid].path.read_bytes()).hexdigest() == entry["instruction"],
                            f"Keep completed {cid} instructions as history; add a new correction component")
            atomic_yaml(checkpoint_path(phase).with_name(f"history-{uuid.uuid4().hex[:10]}.yaml"), state)
            state["components"] = {cid: entry for cid, entry in state["components"].items()
                                   if entry["status"] == "integrated" or entry.get("integrated_revision")}
            for entry in state["components"].values():
                if entry["status"] == "needs_inspection":
                    # Explicit replanning follows inspection of preserved changes. Retain
                    # incorporated work, but require fresh checks before releasing it.
                    entry["status"] = "blocked"
            state["inputs"] = phase.fingerprint()
            state.pop("verification", None)
            save(phase, state)
        require(state["inputs"] == phase.fingerprint(), "Phase inputs changed; inspect prior work and use run --replan --workers-stopped")
        inflight = [cid for cid, e in state["components"].items()
                    if e["status"] in ("creating", "launching", "running", "integrating") or
                    (resume and e["status"] in ("blocked", "interrupted"))]
        if inflight:
            require(resume and workers_stopped, "Interrupted workers need reconciliation: resume PHASE --workers-stopped (confirm they have stopped first)")
            for cid in inflight:
                component, entry = phase.components[cid], state["components"][cid]
                require_stopped(entry)
                root = Path(entry["worktree"])
                require(root.exists(), f"{cid}: inspect missing worker worktree before continuing")
                try:
                    clean(root)
                    if revision(root) == entry["base"]:
                        entry["status"] = "interrupted"
                        entry["error"] = "No committed result. Worktree preserved; use an explicit replan after inspection."
                    elif entry.get("worker_revision") and git(phase.root, "merge-base", entry["worker_revision"], revision(phase.root)) == entry["worker_revision"]:
                        audit_worker(phase, component, entry)
                        entry["integration_checks"] = checks(phase, phase.root, component.data["checks"])
                        entry.update(status="integrated", integrated_revision=revision(phase.root))
                    else:
                        integrate(phase, component, entry, state)
                except PhaseError as exc:
                    entry.update(status="needs_inspection" if isinstance(exc, CheckMutation) else "blocked", error=str(exc))
                save(phase, state)
    else:
        require(not resume, "No previous execution checkpoint to resume")
        require(not any(c.summary.exists() for c in phase.components.values()),
                "Committed component results already exist but the local checkpoint is unavailable; inspect the original attempt instead of replaying implementation")
        state = {"phase": phase.directory.name, "branch": assigned(phase.root), "initial_revision": revision(phase.root),
                 "inputs": phase.fingerprint(), "components": {}}
        save(phase, state)
    for entry in state["components"].values():
        if entry["status"] == "integrated":
            require(git(phase.root, "merge-base", entry["integrated_revision"], revision(phase.root)) == entry["integrated_revision"],
                    "Integration history changed; do not reuse this checkpoint on a reset branch")
    running = {}
    integration_failed = False
    maximum = phase.config.get("execution", {}).get("max_parallel", 2)
    timeout = phase.config.get("execution", {}).get("worker_timeout_seconds", 3600)
    try:
        while True:
            for cid, process in list(running.items()):
                entry = state["components"][cid]
                code = process.poll()
                expired = code is None and time.time() - entry["started"] > timeout
                if expired:
                    stop_process(process)
                    code = process.poll()
                if code is None:
                    continue
                del running[cid]
                try:
                    require(code == 0 and not expired, f"{cid}: worker failed or timed out; inspect {entry['log']}")
                    require(not integration_failed, "Integration checks failed earlier; successful worker preserved for reconciliation")
                    integrate(phase, phase.components[cid], entry, state)
                except PhaseError as exc:
                    if entry.get("integrated_revision"):
                        integration_failed = True
                    entry.update(status="needs_inspection" if isinstance(exc, CheckMutation) else "blocked", error=str(exc))
                    print(str(exc), flush=True)
                save(phase, state)
            # A correction component can repair an already integrated component's checks.
            # Recheck its evidence; never execute its original instructions a second time.
            if not running:
                for cid, entry in state["components"].items():
                    if entry["status"] == "blocked" and entry.get("integrated_revision"):
                        try:
                            validate_summary(phase, phase.components[cid], phase.root)
                            entry["integration_checks"] = checks(phase, phase.root, phase.components[cid].data["checks"])
                            entry["status"] = "integrated"
                            entry.pop("error", None)
                            integration_failed = False
                            save(phase, state)
                        except PhaseError:
                            pass
            dispatched = False
            if not integration_failed:
                for cid, component in phase.components.items():
                    if len(running) >= maximum:
                        break
                    if cid in state["components"]:
                        continue
                    if not all(state["components"].get(d, {}).get("status") == "integrated" for d in component.data["depends_on"]):
                        continue
                    busy = [phase.components[i] for i in running]
                    if any(overlaps(component.data["files"], other.data["files"]) or
                           set(component.data["resources"]) & set(other.data["resources"]) for other in busy):
                        continue
                    running[cid] = create_worker(phase, component, state)
                    dispatched = True
            if not running and not dispatched:
                break
            time.sleep(0.05)
    except BaseException:
        for process in running.values():
            stop_process(process)
        save(phase, state)
        raise
    incomplete = [cid for cid in phase.components if state["components"].get(cid, {}).get("status") != "integrated"]
    if incomplete:
        raise PhaseError("Phase blocked; preserved results, pending/blocked components: " + ", ".join(incomplete))
    print("All components integrated. Run verify for an independent phase assessment.")
    return state


def complete_components(phase):
    state = read_state(phase)
    require(state is not None, "Execute or resume the phase before verification")
    require(state["inputs"] == phase.fingerprint(), "Phase inputs changed; reconcile before verification")
    for cid, component in phase.components.items():
        entry = state["components"].get(cid, {})
        require(entry.get("status") == "integrated", f"{cid}: component is not integrated and checked")
        require(git(phase.root, "merge-base", entry["integrated_revision"], revision(phase.root)) == entry["integrated_revision"],
                f"{cid}: integrated history is missing from this branch")
        validate_summary(phase, component, phase.root)
    return state


def verifier_report(path, expected_revision):
    data, body = record(path)
    require(data.get("status") in ("passed", "gaps_found", "human_needed"), "Verifier must report passed, gaps_found or human_needed")
    require(data.get("revision") == expected_revision, "Verifier report targets a stale or different revision")
    for title in ("Acceptance", "Integration", "Documentation", "Findings"):
        require(bool(section(body, title)), f"Verifier report is missing {title} evidence")
    return data, body


def verify_phase(phase, workers_stopped=False):
    assigned(phase.root)
    clean(phase.root)
    state = complete_components(phase)
    evidence = checks(phase, phase.root, [argv for c in phase.components.values() for argv in c.data["checks"]])
    source_revision, fingerprint = revision(phase.root), source_hash(phase)
    current_head = source_revision
    attempt = state.get("verification_attempt")
    reuse = False
    if attempt and attempt.get("status") != "complete":
        require_stopped(attempt)
        if attempt.get("source") == fingerprint and attempt.get("revision") and git(phase.root, "merge-base", attempt["revision"], current_head) == attempt["revision"]:
            try:
                verifier_report(Path(attempt.get("result", "__missing__")), attempt["revision"])
                reuse = True
                source_revision = attempt["revision"]
            except PhaseError:
                pass
        if not reuse:
            require(workers_stopped, "Interrupted verifier has no current reusable result; inspect it, then verify PHASE --workers-stopped")
            atomic_yaml(checkpoint_path(phase).with_name(f"verification-history-{uuid.uuid4().hex[:10]}.yaml"), attempt)
    if reuse:
        path, result, log = (Path(attempt[k]) for k in ("worktree", "result", "log"))
        print("Reusing the stopped verifier's result for the unchanged source revision.")
    else:
        token = uuid.uuid4().hex[:8]
        path = primary(phase.root) / ".worktrees" / f"phase-{phase.number}-verify-{token}"
        attempt = {"status": "creating", "worktree": str(path), "revision": source_revision, "source": fingerprint}
        state["verification_attempt"] = attempt
        save(phase, state)
        git(phase.root, "worktree", "add", "-b", f"codex/phase-{phase.number}-verify-{token}", str(path), source_revision)

        def before_start(result, log, receipt):
            attempt.update(status="launching", result=str(result), log=str(log), receipt=str(receipt))
            save(phase, state)

        process, result, log = launch(phase, None, path, "verifier", checkpoint_path(phase).parent, source_revision, before_start)
        attempt.update(status="running", pid=process.pid, process_identity=process_identity(process.pid))
        save(phase, state)
        try:
            code = process.wait(timeout=phase.config.get("execution", {}).get("worker_timeout_seconds", 3600))
        except BaseException:
            stop_process(process)
            raise
        require(code == 0, f"Verifier failed; inspect {log}. Worktree preserved: {path}")
    clean(path)
    require(revision(path) == source_revision, "Verifier changed the assigned revision; result rejected")
    clean(phase.root)
    require(revision(phase.root) == current_head and source_hash(phase) == fingerprint,
            "Integration branch changed during verification; result is stale")
    data, body = verifier_report(result, source_revision)
    data["source"] = fingerprint
    body += "\n\n## Runtime checks\n\n" + "\n".join(f"- Passed: `{item['command']!r}`" for item in evidence)
    report = phase.artifact("VERIFICATION")
    write_record(report, data, body)
    commit_paths(phase.root, [report], f"Verify phase {phase.directory.name}: {data['status']}")
    state["verification"] = {"revision": source_revision, "source": fingerprint,
                             "status": data["status"], "report_hash": hashlib.sha256(report.read_bytes()).hexdigest()}
    attempt["status"] = "complete"
    save(phase, state)
    require(data["status"] == "passed", f"Phase verification: {data['status']}. Findings saved in {report}")
    print(f"Phase verified at {source_revision[:12]}; report committed. Publication is a separate step.")


def current_verification(phase):
    data, body = record(phase.artifact("VERIFICATION"))
    require(data.get("status") == "passed", "Phase verification has unresolved findings")
    require(data.get("source") == source_hash(phase), "Verification is stale: source or instructions changed; verify again")
    require(isinstance(data.get("revision"), str) and git(phase.root, "merge-base", data["revision"], revision(phase.root)) == data["revision"],
            "Verified revision is not an ancestor of this branch")
    state = read_state(phase)
    require(state and state.get("verification", {}).get("report_hash") == hashlib.sha256(phase.artifact("VERIFICATION").read_bytes()).hexdigest(),
            "Verification report does not match this coordinator's recorded assessment; verify again")
    return data, body


def uat_phase(phase, case=None, result=None, note=None):
    assigned(phase.root)
    clean(phase.root)
    verified, _ = current_verification(phase)
    path = phase.artifact("UAT")
    data = record(path)[0] if path.exists() else {}
    if data.get("source") != verified["source"]:
        history = data.get("history", [])
        if data:
            history.append({"source": data.get("source"), "cases": data.get("cases", [])})
        data = {"revision": verified["revision"], "source": verified["source"], "history": history,
                "cases": [{"id": i + 1, "acceptance": a, "result": "pending", "note": "", "observations": []}
                          for i, a in enumerate(phase.acceptance)]}
    if case is not None:
        require(result in ("pass", "fail", "blocked", "skipped") and note and note.strip(),
                "Record the actual human observation with --result and a nonempty --note")
        matches = [item for item in data["cases"] if item["id"] == case]
        require(len(matches) == 1, f"No acceptance case {case}")
        item = matches[0]
        item["observations"].append({"result": result, "note": note})
        item.update(result=result, note=note)
    else:
        require(result is None and note is None, "--result and --note need --case")
    body = (f"# Phase {phase.number} acceptance session\n\n"
            "Record observable human testing, not inferred approval. Every required case must pass before publication. "
            "Skipped cases retain their reason and remain unresolved. Prior observations are retained above.\n\n"
            "| Case | Acceptance | Result | Latest observation |\n|---|---|---|---|\n")
    for item in data["cases"]:
        note_text = item["note"].replace("|", "\\|").replace("\n", " ")
        body += f"| {item['id']} | {item['acceptance']} | {item['result']} | {note_text} |\n"
    write_record(path, data, body)
    commit_paths(phase.root, [path], f"Record phase {phase.number} acceptance results")
    print(body)


def require_uat(phase):
    if not phase.context.get("uat", False):
        return
    data, _ = record(phase.artifact("UAT"))
    require(data.get("source") == source_hash(phase), "Acceptance results are stale; repeat UAT for the verified revision")
    cases = data.get("cases", [])
    require(isinstance(cases, list) and {item.get("acceptance") for item in cases} == set(phase.acceptance),
            "UAT must cover every phase acceptance outcome")
    require(cases and all(item.get("result") == "pass" and item.get("note") for item in cases),
            "Required UAT has pending, blocked, failed or skipped cases")


def gh(root, *args):
    result = subprocess.run(["gh", *args], cwd=root, capture_output=True, text=True, encoding="utf-8", timeout=120)
    require(result.returncode == 0, result.stderr.strip() or result.stdout.strip() or "GitHub CLI failed")
    return result.stdout.strip()


def publish_phase(phase, *, authorized, base, draft=False):
    branch = assigned(phase.root)
    clean(phase.root)
    require(authorized, "Publishing requires explicit human authorization; pass --authorized only when already granted")
    complete_components(phase)
    verified, body = current_verification(phase)
    require_uat(phase)
    checks(phase, phase.root, [argv for c in phase.components.values() for argv in c.data["checks"]])
    current_verification(phase)
    require(base and not base.startswith("-") and branch != base, "Select a different, explicit PR base branch")
    require(subprocess.run(["git", "check-ref-format", "--branch", base], capture_output=True).returncode == 0, "Invalid PR base branch")
    remote = phase.config.get("publication", {}).get("remote", "origin")
    require(isinstance(remote, str) and remote in git(phase.root, "remote").splitlines(), "Configure an existing publication remote")
    head = revision(phase.root)
    git(phase.root, "push", "-u", remote, branch)
    requests = json.loads(gh(phase.root, "pr", "list", "--head", branch, "--base", base, "--state", "all", "--json", "number,url,state,mergedAt,headRefOid"))
    require(isinstance(requests, list), "Unexpected GitHub PR listing")
    require(not any(p.get("state") == "MERGED" for p in requests), "This phase PR is already merged; observe delivery instead of publishing again")
    existing = [p for p in requests if p.get("state") == "OPEN"]
    require(len(existing) <= 1, "Multiple open PRs match this phase; resolve publication target")
    description = (f"Implements phase {phase.directory.name}.\n\n" + section(phase.body, "Goal") +
                   "\n\nAcceptance and component instructions: `" + phase.relative + "`.\n\n" +
                   f"Independent verification: `{phase.number}-VERIFICATION.md` at `{verified['revision']}`.\n\n" +
                   "Configured component and integration checks passed before publication.\n\n" +
                   "Human acceptance: " + ("all required cases passed." if phase.context.get("uat") else "not required by this phase.") +
                   "\n\nPublication does not authorize merging.\n")
    body_path = checkpoint_path(phase).parent / "pull-request.md"
    body_path.write_text(description, encoding="utf-8")
    if existing:
        url = existing[0]["url"]
        gh(phase.root, "pr", "edit", url, "--body-file", str(body_path))
    else:
        argv = ["pr", "create", "--base", base, "--head", branch, "--title", f"Implement phase {phase.directory.name}", "--body-file", str(body_path)]
        if draft:
            argv.append("--draft")
        url = gh(phase.root, *argv)
    observation = json.loads(gh(phase.root, "pr", "view", url, "--json", "number,url,state,mergedAt,headRefOid,statusCheckRollup"))
    require(observation.get("headRefOid") == head, "Published PR head does not match the checked local revision")
    state = read_state(phase)
    state["publication"] = {"url": observation.get("url", url), "head": head, "base": base,
                            "observed": observation, "observed_at": time.time()}
    save(phase, state)
    print(f"Published {state['publication']['url']}; {observation.get('state', 'unknown')}. No merge performed.")
    print("GitHub checks (last observation): " + json.dumps(observation.get("statusCheckRollup", [])))


def check_observation(phase, observation):
    required = phase.config.get("publication", {}).get("required_checks", [])
    observed = {}
    for item in observation.get("statusCheckRollup", []) or []:
        name = item.get("name") or item.get("context")
        outcome = item.get("conclusion") if item.get("status") == "COMPLETED" else item.get("state")
        observed.setdefault(name, []).append(outcome)
    if not required:
        return "Inspect PR checks; configure required check names before claiming readiness"
    waiting = [name for name in required if name not in observed or any(v != "SUCCESS" for v in observed[name])]
    return ("Wait/resolve required checks: " + ", ".join(waiting)) if waiting else "Required PR checks passed; await authorized merge"


def status_text(root, name=None, remote=False):
    directories = [name] if name else sorted(p.name for p in (root / ".ai/phases").glob("[0-9]*-*") if p.is_dir())
    lines = ["# Phase status", "", "| Phase | Evidence | Next action |", "|---|---|---|"]
    for name in directories:
        phase = load_phase(root, name)
        state = read_state(phase)
        stage, next_action = "pending approval", "Discuss and prepare phase context"
        if phase.context["approval"] == "approved":
            stage, next_action = "approved", "Prepare/check component instructions"
        if not state and phase.artifact("VERIFICATION").is_file():
            report, _ = record(phase.artifact("VERIFICATION"))
            stage = f"recorded verification: {report.get('status', 'unknown')} at {str(report.get('revision', 'unknown'))[:12]}"
            next_action = "Inspect committed evidence; local execution checkpoint unavailable"
        if state:
            statuses = {cid: state["components"].get(cid, {}).get("status", "pending") for cid in phase.components}
            stage = ", ".join(f"{cid}: {value}" for cid, value in statuses.items())
            next_action = "Run/resume remaining components"
            if statuses and all(v == "integrated" for v in statuses.values()):
                stage, next_action = "integrated", "Verify phase independently"
            if state["inputs"] != phase.fingerprint():
                stage, next_action = "inputs changed", "Reconcile and replan"
            else:
                try:
                    current_verification(phase)
                    stage, next_action = "verified", "Publish when authorized"
                    if phase.context.get("uat"):
                        try:
                            require_uat(phase)
                        except PhaseError:
                            next_action = "Complete required UAT"
                except PhaseError:
                    pass
            attempt = state.get("verification_attempt")
            if attempt and attempt.get("status") != "complete":
                stage, next_action = "verification unfinished", "Inspect verifier process and result before verifying again"
            publication = state.get("publication")
            if publication:
                observation = publication.get("observed", {})
                if remote:
                    observation = json.loads(gh(root, "pr", "view", publication["url"], "--json", "number,url,state,mergedAt,headRefOid,statusCheckRollup"))
                if observation.get("state") == "MERGED" and observation.get("mergedAt") and observation.get("headRefOid") == publication["head"]:
                    stage, next_action = "delivered (observed merge)", "Check the next phase"
                elif publication["head"] == revision(root) and observation.get("headRefOid") == publication["head"]:
                    stage, next_action = "published (unmerged at last observation)", "Review PR and GitHub checks"
                    next_action = check_observation(phase, observation)
                    if observation.get("state") == "CLOSED":
                        stage, next_action = "PR closed without merge", "Inspect closure before further publication"
                lines.append(f"<!-- Last PR observation: {publication['url']} -->")
        if git(root, "status", "--porcelain", "--untracked-files=all"):
            stage, next_action = "uncommitted changes", "Commit/reconcile changes before reusing phase evidence"
        lines.append(f"| {phase.directory.name} | {stage} | {next_action} |")
    if not directories:
        lines.append("| None | No phases yet | Define project intent, then create a phase |")
    return "\n".join(lines) + "\n"


def sync_state(root):
    assigned(root)
    clean(root)
    path = root / ".ai/STATE.md"
    path.write_text(status_text(root) + "\nGenerated by phase.py sync; phase records own scope and evidence.\n", encoding="utf-8")
    commit_paths(root, [path], "Refresh derived phase status")
    print(str(path))


def new_phase(root, slug, title):
    import re
    assigned(root)
    clean(root)
    require(re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is not None, "Use a lowercase hyphen-separated phase slug")
    require(bool(title.strip()), "Provide a phase title")
    numbers = []
    for line in git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            directory = Path(line.removeprefix("worktree ")) / ".ai/phases"
            numbers += [int(p.name.split("-", 1)[0]) for p in directory.glob("[0-9]*-*") if p.name.split("-", 1)[0].isdigit()]
    number = f"{max(numbers, default=0) + 1:02d}"
    directory = root / ".ai/phases" / f"{number}-{slug}"
    require(not directory.exists(), "Phase directory already exists")
    context = directory / f"{number}-CONTEXT.md"
    write_record(context, {"phase": number, "approval": "pending", "depends_on": [], "uat": False},
                 f"# {title}\n\n## Goal\n\nCHANGEME\n\n## Acceptance\n\n- [ ] A1: CHANGEME\n\n"
                 "## Decisions\n\nPending discussion.\n\n## Authorization\n\nCHANGEME: record the user's actual authorization.\n\n"
                 "## Open questions\n\nDefine scope and acceptance.\n\n## Deferred\n\nNone.\n")
    roadmap = root / ".ai/ROADMAP.md"
    existing = roadmap.read_text(encoding="utf-8") if roadmap.exists() else "# Roadmap\n"
    roadmap.write_text(existing.rstrip() + f"\n\n- [{number}: {title}](phases/{directory.name}/{context.name}) — pending discussion.\n", encoding="utf-8")
    commit_paths(root, [context, roadmap], f"Create phase {number}: {title}")
    print(f"Created {directory}; discuss scope and approval before preparing components.")
