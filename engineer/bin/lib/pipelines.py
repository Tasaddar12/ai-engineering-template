"""Serialized, durable host execution with isolated attempts and honest outcomes."""
from __future__ import annotations

import contextlib
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
import uuid

from . import records
from .core import Args, Failure, load_json, now, planning_lock, root, run, write_json

_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z")
_DONE = "implemented_unverified"
_TERMINAL = {_DONE, "failed", "blocked", "cancelled", "interrupted"}


def _identifier(value):
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise Failure("invalid-pipeline-id", "IDs must be 1-80 ASCII letters, digits, underscores or hyphens", 2)
    return value


def _directory(identifier=None):
    base = records.planning() / "pipelines"
    path = base / _identifier(identifier) if identifier is not None else base
    cursor = path
    while cursor != root().parent:
        if cursor.is_symlink():
            raise Failure("pipeline-symlink", str(cursor))
        if cursor == root():
            break
        cursor = cursor.parent
    return path


def _number(value, name, default, minimum=1, maximum=28800):
    try:
        result = float(default if value is None else value)
    except (TypeError, ValueError) as exc:
        raise Failure("invalid-pipeline-option", name, 2) from exc
    if not math.isfinite(result) or not minimum <= result <= maximum:
        raise Failure("invalid-pipeline-option", f"{name} must be between {minimum} and {maximum}", 2)
    return result


@contextlib.contextmanager
def _ownership(directory):
    """Kernel locks survive stale metadata and release on runner death, not on age."""
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "runner.lock"
    if lock.is_symlink():
        raise Failure("pipeline-symlink", str(lock))
    with lock.open("a+b") as handle:
        handle.seek(0)
        handle.write(b"0")
        handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise Failure("pipeline-owned", "Another runner owns this pipeline") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _save(directory, data):
    data["updated"] = now()
    write_json(directory / "state.json", data)


def _load(identifier):
    directory = _directory(identifier)
    data = load_json(directory / "state.json")
    if not isinstance(data, dict) or data.get("schema") != 1:
        raise Failure("pipeline-not-found", identifier)
    if data.get("repository") != str(root()):
        raise Failure("pipeline-root-mismatch", "Run from the recorded repository checkout")
    return directory, data


def _git(*argv, cwd=None, check=True):
    return run(["git", *argv], cwd or root(), check=check, timeout=60)


def _head(cwd):
    return _git("rev-parse", "HEAD", cwd=cwd).stdout.strip()


def _tasks(raw):
    if isinstance(raw, dict):
        raw = raw.get("tasks")
    if not isinstance(raw, list) or not raw or len(raw) > 1000:
        raise Failure("invalid-pipeline-tasks", "Supply a nonempty JSON task array (maximum 1000)", 2)
    result, seen = [], set()
    for item in raw:
        if not isinstance(item, dict):
            raise Failure("invalid-pipeline-task", "Each task must be an object", 2)
        identifier = _identifier(item.get("id"))
        prompt = item.get("prompt")
        instructions = item.get("instructions", "")
        dependencies = item.get("depends_on", [])
        if identifier in seen or not isinstance(prompt, str) or not prompt.strip() or not isinstance(instructions, str):
            raise Failure("invalid-pipeline-task", "Task IDs must be unique and prompts nonempty", 2)
        if not isinstance(dependencies, list) or any(not isinstance(d, str) for d in dependencies):
            raise Failure("invalid-pipeline-dependencies", identifier, 2)
        retries = _number(item.get("max_retries"), "max_retries", 0, 0, 3)
        if not retries.is_integer():
            raise Failure("invalid-pipeline-option", "max_retries must be an integer", 2)
        seen.add(identifier)
        result.append({"id": identifier, "prompt": prompt, "phase": item.get("phase"),
                       "description": item.get("description", ""), "instructions": instructions,
                       "depends_on": list(dict.fromkeys(dependencies)),
                       "timeout_seconds": _number(item.get("timeout_seconds"), "timeout_seconds", 3600),
                       "max_retries": int(retries),
                       "status": "pending", "attempts": []})
    visited = set()
    while len(visited) < len(result):
        ready = [t for t in result if t["id"] not in visited and set(t["depends_on"]) <= visited]
        if not ready:
            raise Failure("invalid-pipeline-dependencies", "Unknown dependency or cycle", 2)
        visited.update(t["id"] for t in ready)
    return result


def _create(args):
    if args.has("tasks") == args.has("file"):
        raise Failure("pipeline-input", "Supply exactly one of --tasks JSON or --file FILE", 2)
    try:
        raw = args.json("tasks") if args.has("tasks") else json.loads(Path(str(args.get("file"))).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise Failure("pipeline-input", str(exc), 2) from exc
    tasks = _tasks(raw)
    identifier = _identifier(args.get("id", "pipeline-" + uuid.uuid4().hex[:12]))
    directory = _directory(identifier)
    base = _git("rev-parse", "--verify", str(args.get("base", "HEAD")) + "^{commit}").stdout.strip()
    intent = {"tasks": tasks, "base_ref": args.get("base"), "instructions": str(args.get("instructions", "")),
              "budget_seconds": _number(args.get("budget-seconds"), "budget-seconds", 28800, 1, 604800)}
    intent_digest = hashlib.sha256(json.dumps(intent, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    with planning_lock():
        if directory.exists():
            existing = load_json(directory / "state.json")
            if isinstance(existing, dict) and existing.get("intent_digest") == intent_digest:
                return {**existing, "reused": True}
            raise Failure("pipeline-exists", "This ID already owns a different task intent", id=identifier)
        directory.mkdir(parents=True)
        data = {"schema": 1, "id": identifier, "token": uuid.uuid4().hex, "repository": str(root()),
                "created": now(), "status": "pending", "base": base, "head": base,
                "branch": "codex/pipeline-" + identifier + "-" + uuid.uuid4().hex[:8],
                "intent_digest": intent_digest, "instructions": intent["instructions"], "budget_seconds": intent["budget_seconds"],
                "spent_seconds": 0, "tasks": tasks, "model": "inherit", "effort": "inherit"}
        _save(directory, data)
    return data


def _host(args, data):
    host = args.get("host", data.get("host"))
    argv = args.json("command-json", data.get("command"))
    if host not in ("claude", "codex") or not isinstance(argv, list) or not argv:
        raise Failure("pipeline-host", "Specify --host claude|codex and --command-json argv", 2)
    if any(not isinstance(v, str) or not v or "\x00" in v for v in argv):
        raise Failure("pipeline-host", "Host argv must contain nonempty strings", 2)
    executable = Path(argv[0]).name.lower()
    if executable not in (host, host + ".exe"):
        raise Failure("pipeline-host", "Use the selected host executable directly; no shells or wrappers", 2)
    if host == "codex" and ("exec" not in argv[1:] or "-" not in argv[1:]):
        raise Failure("pipeline-host", "Codex argv must select exec and stdin prompt '-'", 2)
    if host == "claude" and not any(v in ("-p", "--print") for v in argv[1:]):
        raise Failure("pipeline-host", "Claude argv must select noninteractive --print", 2)
    return host, argv


def _alive(attempt):
    pid = attempt.get("pid")
    if not pid:
        return None  # Launch crash window: never guess that no worker exists.
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return False if ctypes.get_last_error() == 87 else None
        try:
            code = ctypes.c_ulong()
            if not kernel.GetExitCodeProcess(ctypes.c_void_p(handle), ctypes.byref(code)):
                return None
            return code.value == 259
        finally:
            kernel.CloseHandle(ctypes.c_void_p(handle))
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return None


class _WindowsJob:
    """Kill every assigned descendant when this runner's job handle closes."""
    def __init__(self):
        self.handle = None
        if os.name != "nt":
            return
        from ctypes import wintypes as w

        class Basic(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                        ("flags", w.DWORD), ("minimum", ctypes.c_size_t), ("maximum", ctypes.c_size_t),
                        ("active", w.DWORD), ("affinity", ctypes.c_size_t),
                        ("priority", w.DWORD), ("scheduling", w.DWORD)]

        class IO(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in
                        ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]

        class Extended(ctypes.Structure):
            _fields_ = [("basic", Basic), ("io", IO), ("process_memory", ctypes.c_size_t),
                        ("job_memory", ctypes.c_size_t), ("peak_process", ctypes.c_size_t),
                        ("peak_job", ctypes.c_size_t)]

        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.CreateJobObjectW.restype = w.HANDLE
        self.handle = self.api.CreateJobObjectW(None, None)
        limits = Extended()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE; no breakaway.
        if not self.handle or not self.api.SetInformationJobObject(
                w.HANDLE(self.handle), 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise Failure("pipeline-job", "Cannot establish Windows process-tree ownership")

    def assign(self, process):
        if self.handle and not self.api.AssignProcessToJobObject(
                ctypes.c_void_p(self.handle), ctypes.c_void_p(int(process._handle))):
            raise Failure("pipeline-job", "Cannot assign host to the owned Windows job")

    def resume(self, process):
        """Resume the suspended primary thread only after its job owns it."""
        from ctypes import wintypes as w

        class ThreadEntry(ctypes.Structure):
            _fields_ = [("size", w.DWORD), ("usage", w.DWORD), ("thread", w.DWORD),
                        ("owner", w.DWORD), ("priority", w.LONG), ("delta", w.LONG), ("flags", w.DWORD)]

        self.api.CreateToolhelp32Snapshot.argtypes = [w.DWORD, w.DWORD]
        self.api.CreateToolhelp32Snapshot.restype = w.HANDLE
        self.api.Thread32First.argtypes = [w.HANDLE, ctypes.POINTER(ThreadEntry)]
        self.api.Thread32Next.argtypes = [w.HANDLE, ctypes.POINTER(ThreadEntry)]
        self.api.OpenThread.argtypes = [w.DWORD, w.BOOL, w.DWORD]
        self.api.OpenThread.restype = w.HANDLE
        self.api.ResumeThread.argtypes = [w.HANDLE]
        self.api.ResumeThread.restype = w.DWORD
        snapshot = self.api.CreateToolhelp32Snapshot(0x4, 0)
        if not snapshot or snapshot == ctypes.c_void_p(-1).value:
            raise Failure("pipeline-job", "Cannot locate suspended host thread")
        try:
            entry = ThreadEntry()
            entry.size = ctypes.sizeof(entry)
            present = self.api.Thread32First(w.HANDLE(snapshot), ctypes.byref(entry))
            while present:
                if entry.owner == process.pid:
                    thread = self.api.OpenThread(0x2, False, entry.thread)
                    if not thread:
                        raise Failure("pipeline-job", "Cannot open suspended host thread")
                    try:
                        if self.api.ResumeThread(w.HANDLE(thread)) != 1:
                            raise Failure("pipeline-job", "Host thread did not resume from its initial suspension")
                        return
                    finally:
                        self.api.CloseHandle(w.HANDLE(thread))
                present = self.api.Thread32Next(w.HANDLE(snapshot), ctypes.byref(entry))
            raise Failure("pipeline-job", "Suspended host thread was not found")
        finally:
            self.api.CloseHandle(w.HANDLE(snapshot))

    def stop(self):
        if self.handle:
            if not self.api.TerminateJobObject(ctypes.c_void_p(self.handle), 1):
                raise Failure("pipeline-job", "Cannot terminate the owned Windows process tree")
            # Query JobObjectBasicAccountingInformation until ActiveProcesses is zero.
            buffer = ctypes.create_string_buffer(48)
            deadline = time.monotonic() + 30
            while True:
                if not self.api.QueryInformationJobObject(ctypes.c_void_p(self.handle), 1, buffer, 48, None):
                    raise Failure("pipeline-job", "Cannot establish process-tree termination")
                if int.from_bytes(buffer.raw[40:44], "little") == 0:
                    break
                if time.monotonic() >= deadline:
                    raise Failure("pipeline-job", "Owned process tree did not terminate")
                time.sleep(0.1)

    def close(self):
        if self.handle:
            self.api.CloseHandle(ctypes.c_void_p(self.handle))
            self.handle = None


def _stop(process, job=None):
    if os.name == "nt":
        if job and job.handle:
            job.stop()
            process.wait(timeout=30)
            return True
        result = run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, timeout=30)
        process.wait(timeout=30)
        return result.returncode == 0
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=30)
    deadline = time.monotonic() + 30
    while _alive({"pid": process.pid}) is not False:
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.1)
    return True


def _stdout_receipt(attempt, task, data):
    """Accept a bounded final response without expanding worker write access."""
    with Path(attempt["stdout"]).open("rb") as stream:
        stream.seek(0, 2)
        stream.seek(max(0, stream.tell()-4*1024*1024))
        output = stream.read().decode("utf-8", errors="replace")
    found = []

    def inspect(value, depth=0):
        if depth > 12:
            return
        if isinstance(value, dict):
            for child in value.values():
                inspect(child, depth+1)
        elif isinstance(value, list):
            for child in value:
                inspect(child, depth+1)
        elif isinstance(value, str):
            for line in value.splitlines():
                offset = line.find("ENGINEER_OUTCOME:")
                if offset < 0:
                    continue
                try:
                    packet, _ = json.JSONDecoder().raw_decode(line[offset+len("ENGINEER_OUTCOME:"):].strip())
                except ValueError:
                    continue
                if isinstance(packet, dict) and all(packet.get(key) == expected for key, expected in {
                    "pipeline_id": data["id"], "task_id": task["id"], "attempt_token": attempt["token"]}.items()):
                    found.append(packet)

    for line in output.splitlines():
        try:
            inspect(json.loads(line))
        except ValueError:
            inspect(line)
    if not found or any(packet != found[-1] for packet in found):
        raise Failure("pipeline-receipt", "No single consistent token-bound outcome was returned by the host")
    return found[-1]


def _receipt(attempt, task, data):
    path = Path(attempt["path"])
    receipt_path = Path(attempt["receipt"])
    if receipt_path.is_symlink():
        raise Failure("pipeline-receipt", "Receipt may not be a symlink")
    receipt = load_json(receipt_path) if receipt_path.is_file() else _stdout_receipt(attempt, task, data)
    if not isinstance(receipt, dict) or any(receipt.get(k) != v for k, v in {
        "pipeline_id": data["id"], "task_id": task["id"], "attempt_token": attempt["token"]}.items()):
        raise Failure("pipeline-receipt", "Missing or mismatched outcome receipt")
    if receipt.get("status") != "implemented":
        raise Failure("pipeline-receipt", "Worker did not report implemented work", outcome=receipt)
    if not isinstance(receipt.get("reason"), str) or not receipt["reason"].strip():
        raise Failure("pipeline-receipt", "Receipt needs the actual outcome reason")
    head = _head(path)
    if receipt.get("head") != head or head == attempt["base"]:
        raise Failure("pipeline-receipt", "Receipt must identify actual new committed HEAD")
    if _git("merge-base", "--is-ancestor", attempt["base"], head, cwd=path, check=False).returncode:
        raise Failure("pipeline-history", "Worker rewrote prerequisite history")
    if _git("diff", "--quiet", attempt["base"], head, "--", cwd=path, check=False).returncode != 1:
        raise Failure("pipeline-empty-work", "Empty commits do not establish implementation")
    if _git("status", "--porcelain", "--untracked-files=all", cwd=path).stdout:
        raise Failure("pipeline-dirty-worker", "Uncommitted work is preserved, not integrated")
    if _git("branch", "--show-current", cwd=path).stdout.strip() != attempt["branch"]:
        raise Failure("pipeline-branch", "Worker changed its assigned branch")
    write_json(receipt_path, receipt)
    return head, receipt


def _accept(directory, data, task, attempt):
    head, receipt = _receipt(attempt, task, data)
    attempt.update(status="integrating", head=head, outcome=receipt)
    _save(directory, data)
    current = _git("rev-parse", "refs/heads/" + data["branch"]).stdout.strip()
    if current != head:
        if current != attempt["base"]:
            raise Failure("pipeline-branch-drift", "Pipeline branch changed outside this runner")
        _git("update-ref", "refs/heads/" + data["branch"], head, current)
    data["head"] = head
    task["status"] = _DONE
    attempt.update(status=_DONE, finished=now(), verification="unverified")
    task["head"] = head
    _save(directory, data)


def _recover(directory, data):
    for task in data["tasks"]:
        for attempt in task["attempts"]:
            if attempt["status"] == "preparing":
                attempt.update(status="interrupted", retry_safe=True, finished=now())
                task["status"] = "interrupted"
                _save(directory, data)
                continue
            if attempt["status"] not in ("launching", "running", "integrating") and not (
                    attempt["status"] == "interrupted" and not attempt.get("retry_safe")):
                continue
            alive = _alive(attempt)
            if alive is not False:
                raise Failure("pipeline-worker-uncertain", "Live or unidentifiable worker preserved; no duplicate launch", task=task["id"], attempt=attempt)
            # On Windows the leader's death cannot prove its descendants stopped.
            if os.name == "nt" and attempt["status"] != "integrating" and not attempt.get("job_guard"):
                raise Failure("pipeline-worker-uncertain", "Inspect preserved Windows process tree before recovery; leader exit alone is insufficient", attempt=attempt)
            data["spent_seconds"] += max(0, time.time() - attempt.get("accounted_at", time.time()))
            if Path(attempt["receipt"]).is_file() or Path(attempt["stdout"]).is_file():
                try:
                    _accept(directory, data, task, attempt)
                    continue
                except (Failure, OSError, ValueError) as exc:
                    attempt["error"] = str(exc)
            attempt.update(status="interrupted", finished=now(), retry_safe=True)
            task["status"] = "interrupted"
            _save(directory, data)


def _attempt(directory, data, task, argv):
    ordinal = len(task["attempts"]) + 1
    token = uuid.uuid4().hex
    common = Path(_git("rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
    workroot = common / "engineer-pipeline-worktrees" / data["token"]
    path = workroot / (task["id"] + "-" + str(ordinal))
    if workroot.is_symlink() or path.exists():
        raise Failure("pipeline-worktree-exists", str(path))
    branch = data["branch"] + "-" + task["id"] + "-" + str(ordinal)
    logs = directory / "attempts" / (task["id"] + "-" + str(ordinal))
    logs.mkdir(parents=True, exist_ok=False)
    attempt = {"number": ordinal, "token": token, "status": "preparing", "base": data["head"],
               "branch": branch, "path": str(path), "receipt": str(logs / "outcome.json"),
               "stdout": str(logs / "stdout.log"), "stderr": str(logs / "stderr.log"), "started": now()}
    task["attempts"].append(attempt)
    task["status"] = "running"
    _save(directory, data)
    workroot.mkdir(parents=True, exist_ok=True)
    _git("worktree", "add", "-b", branch, str(path), data["head"])
    prompt = ("Implement only this explicitly authorized task in the assigned isolated checkout. "
              "Do not publish, merge, alter other worktrees, or launch detached workers. Preserve prior commits. "
              "Commit actual changes. Report blocked work honestly. Verification may remain unverified; "
              "do not invent passing checks. After committing, return a final single-line response "
              "beginning ENGINEER_OUTCOME: followed by a JSON outcome receipt. The runner persists it; "
              "you do not need permission to write outside this checkout. Receipt schema: "
              '{"pipeline_id": "...", "task_id": "...", "attempt_token": "...", '
              '"status": "implemented|blocked|failed", "head": "actual Git HEAD", '
              '"reason": "actual outcome", "verification": {"status": "unverified|passed", "evidence": []}}.\n'
              + json.dumps({"pipeline_id": data["id"], "task_id": task["id"], "attempt_token": token,
                            "receipt_path": attempt["receipt"], "worktree": str(path), "base": data["head"]})
              + "\n\nUSER CONSTRAINTS (preserve these throughout implementation):\n"
              + data.get("instructions", "") + "\n" + task.get("instructions", "")
              + "\n\nTASK:\n" + task["prompt"] + "\n")
    # Preserve the exact prompt and deliver it only after process-tree ownership exists.
    prompt_path = logs / "prompt.txt"
    prompt_path.write_text(prompt, encoding="utf-8")
    job = _WindowsJob()
    attempt.update(status="launching", accounted_at=time.time())
    _save(directory, data)
    env = dict(os.environ, ENGINEER_ROOT=str(path), ENGINEER_HOST=data["host"], ENGINEER_PIPELINE_ATTEMPT=token)
    started = time.monotonic()
    timed_out = cancelled = False
    with Path(attempt["stdout"]).open("wb") as stdout, Path(attempt["stderr"]).open("wb") as stderr:
        options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | 0x4} if os.name == "nt" else {"start_new_session": True}
        try:
            process = subprocess.Popen(argv, cwd=path, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr, shell=False, **options)
        except OSError as exc:
            job.close()
            attempt.update(status="failed", error=str(exc), finished=now(), retry_safe=True)
            task["status"] = "failed"
            _save(directory, data)
            return
        try:
            attempt["pid"] = process.pid
            job.assign(process)
            attempt.update(pid=process.pid, status="running", job_guard=os.name == "nt")
            _save(directory, data)
            if os.name == "nt":
                job.resume(process)
            def send_prompt():
                try:
                    process.stdin.write(prompt.encode("utf-8"))
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass  # Exit code and required receipt determine the outcome.

            sender = threading.Thread(target=send_prompt, daemon=True)
            sender.start()
            while process.poll() is None:
                elapsed = time.monotonic() - started
                timed_out = elapsed >= task["timeout_seconds"] or data["spent_seconds"] >= data["budget_seconds"]
                cancelled = (directory / "cancel.json").exists()
                if timed_out or cancelled:
                    attempt["retry_safe"] = _stop(process, job)
                    break
                time.sleep(0.5)
                current = time.time()
                data["spent_seconds"] += max(0, current - attempt["accounted_at"])
                attempt["accounted_at"] = current
                _save(directory, data)
            process.wait()
            if os.name == "nt":
                job.stop()
                attempt["retry_safe"] = True
            elif _alive(attempt) is not False:
                attempt["retry_safe"] = _stop(process)
                attempt["orphaned_children"] = True
            sender.join(timeout=5)
        except BaseException:
            # Abrupt process death still leaves launch/running evidence for fail-closed recovery.
            try:
                attempt["retry_safe"] = _stop(process, job if attempt.get("job_guard") else None)
            finally:
                attempt.update(status="interrupted", finished=now())
                task["status"] = "interrupted"
                _save(directory, data)
            raise
        finally:
            job.close()
        attempt["exit_code"] = process.returncode
    current = time.time()
    data["spent_seconds"] += max(0, current - attempt["accounted_at"])
    attempt["accounted_at"] = current
    attempt["finished"] = now()
    if cancelled or timed_out or process.returncode:
        attempt["status"] = "cancelled" if cancelled else "timed_out" if timed_out else "failed"
        task["status"] = "cancelled" if cancelled else "failed"
        # Ordinary Windows host exit does not establish that child processes ended.
        attempt.setdefault("retry_safe", os.name != "nt" and _alive(attempt) is False)
    elif attempt.get("orphaned_children") or _alive(attempt) is not False:
        attempt.update(status="interrupted", error="Host left live descendants; preserve attempt", retry_safe=False)
        task["status"] = "interrupted"
    else:
        try:
            _accept(directory, data, task, attempt)
            return
        except (Failure, OSError, ValueError) as exc:
            outcome = exc.details.get("outcome", {}) if isinstance(exc, Failure) else {}
            status = "blocked" if outcome.get("status") == "blocked" else "failed"
            attempt.update(status=status, error=str(exc), outcome=outcome,
                           retry_safe=attempt.get("retry_safe", _alive(attempt) is False))
            task["status"] = status
    _save(directory, data)


def _publish(directory, data, args):
    remaining = data["budget_seconds"]-data["spent_seconds"]
    if remaining <= 0:
        return {"requested": True, "published": False, "status": "pending", "reason": "Runner budget exhausted; resume with a fresh explicit budget"}
    accepted = [a for t in data["tasks"] for a in t["attempts"]
                if a["status"] == _DONE and a.get("head") == data["head"]]
    if not accepted:
        return {"requested": True, "published": False, "reason": "No accepted committed work"}
    cwd = Path(accepted[-1]["path"])
    if _head(cwd) != data["head"] or _git("status", "--porcelain", cwd=cwd).stdout:
        raise Failure("pipeline-publication-drift", "Accepted checkout changed before publication")
    cli = [sys.executable, "-I", str(Path(__file__).resolve().parents[1] / "engineer.py"), "query"]
    env = dict(os.environ, ENGINEER_ROOT=str(cwd))
    existing = subprocess.run([*cli, "pr.status", data["branch"]], cwd=cwd, env=env,
                              text=True, encoding="utf-8", errors="replace", capture_output=True,
                              timeout=60, shell=False)
    if existing.returncode:
        raise Failure("pipeline-publication", existing.stderr[-12000:])
    prior = json.loads(existing.stdout)
    if prior.get("url") and not prior.get("isDraft"):
        raise Failure("pipeline-publication", "Existing non-draft PR requires separate human delivery; no edit attempted")
    tasks = "\n".join("- " + t["id"] + ": " + t["status"] for t in data["tasks"])
    body = ("## Goal\nImplement the explicitly enqueued tasks for pipeline " + data["id"]
            + ".\n\n## Changes\n" + tasks + "\n\n## Verification\n"
            "Unverified. The runner required committed changes and matching outcome receipts, "
            "but did not execute or independently certify tests or acceptance.\n\n## Known gaps\n"
            + ("All implementation remains independently unverified. "
               "Blocked or failed tasks above remain unresolved; consult durable pipeline logs and receipts.")
            + "\n\n## Risks or rollback\nReview the complete diff and task evidence before acceptance. "
            "Preserved attempt worktrees are not deleted. Revert reviewed commits to roll back.\n\n## Stack\n"
            + "Pipeline base revision: `" + data["base"] + "`; head: `" + data["head"]
            + "`. This draft does not authorize a merge.\n")
    argv = [*cli, "pr.open", data["branch"], "--title", str(args.get("title", "feat: pipeline " + data["id"])),
            "--body", body]
    if args.has("pr-base"):
        argv.extend(["--base", str(args.get("pr-base"))])
    # Persist mutation intent first; delivery.open performs existing-PR lookup/readback on resume.
    data["publication"] = {"requested": True, "status": "publishing", "branch": data["branch"],
                           "head": data["head"], "title": argv[argv.index("--title") + 1], "body": body}
    _save(directory, data)
    result = subprocess.run(argv, cwd=cwd, env=env,
                            text=True, encoding="utf-8", errors="replace", capture_output=True,
                            timeout=180, shell=False)
    if result.returncode:
        return {"requested": True, "published": False, "status": "pending",
                "error": result.stderr[-12000:], "branch": data["branch"], "head": data["head"]}
    packet = json.loads(result.stdout)
    if not packet.get("isDraft"):
        raise Failure("pipeline-publication", "Provider did not report a draft PR; no merge attempted", publication=packet)
    return {"requested": True, "published": True, "status": "draft", "url": packet["url"],
            "branch": data["branch"], "head": data["head"], "verification": "unverified"}


def _track_failure(task, data):
    from . import issues
    attempt = task["attempts"][-1] if task["attempts"] else {}
    title = "Pipeline " + data["id"] + ": " + task["id"] + " execution issue"
    values = [title, "--problem", str(task.get("reason", attempt.get("error", task["status"]))),
              "--expected", "The explicitly authorized task produces accepted committed work.",
              "--actual", task["status"], "--evidence", json.dumps(attempt, ensure_ascii=False),
              "--revision", str(attempt.get("base", data["head"])),
              "--scope", str(task.get("description") or task["id"]),
              "--acceptance", "Resolve the recorded failure and independently verify the original task acceptance.",
              "--publish"]
    try:
        with issues.budget(max(0, data["budget_seconds"]-data["spent_seconds"])):
            task["issue"] = issues.command(Args(values), "finding")
    except Exception as exc:
        task["issue"] = {"status": "pending", "error": str(exc)}


def _execute(directory, data, args):
    host, argv = _host(args, data)
    _recover(directory, data)
    if (directory / "cancel.json").exists():
        data["status"] = "cancelled"
        _save(directory, data)
        return data
    ref = "refs/heads/" + data["branch"]
    existing = _git("rev-parse", "--verify", ref, check=False)
    if existing.returncode:
        _git("update-ref", ref, data["head"], "0" * len(data["head"]))
    elif existing.stdout.strip() != data["head"]:
        raise Failure("pipeline-branch-drift", "Pipeline branch changed outside this runner")
    data.update(host=host, command=argv, status="running", runner={"pid": os.getpid(), "started": now()})
    _save(directory, data)
    tracked = set()
    while True:
        if (directory / "cancel.json").exists() or data["spent_seconds"] >= data["budget_seconds"]:
            break
        by_id = {t["id"]: t for t in data["tasks"]}
        selected = None
        for task in data["tasks"]:
            if task["status"] != "pending":
                continue
            dependencies = [by_id[d]["status"] for d in task["depends_on"]]
            if any(d in _TERMINAL and d != _DONE for d in dependencies):
                task.update(status="blocked", reason="Prerequisite did not produce accepted committed work")
            elif all(d == _DONE for d in dependencies):
                selected = task
                break
        if selected is None:
            break
        try:
            _attempt(directory, data, selected, argv)
        except (Failure, OSError, ValueError) as exc:
            if selected["attempts"] and selected["attempts"][-1]["status"] in ("launching", "running", "integrating"):
                _save(directory, data)
                raise  # Unknown worker ownership forbids another dispatch.
            selected.update(status="failed", reason=str(exc))
        latest = selected["attempts"][-1] if selected["attempts"] else {}
        if selected["status"] == "failed" and latest.get("retry_safe") and len(selected["attempts"]) <= selected["max_retries"]:
            selected["status"] = "pending"
        if args.has("track-issues") and selected["status"] in ("failed", "blocked", "interrupted"):
            before_tracking = time.monotonic()
            _track_failure(selected, data)
            data["spent_seconds"] += time.monotonic()-before_tracking
            tracked.add(selected["id"])
        if latest.get("retry_safe") is False and selected["status"] != _DONE:
            break  # Preserve serialization when descendants may still exist.
        _save(directory, data)
    statuses = [t["status"] for t in data["tasks"]]
    if args.has("track-issues"):
        for task in data["tasks"]:
            issue = task.get("issue", {})
            confirmed = bool(issue.get("url") and (issue.get("published") or issue.get("linked")))
            if task["status"] in ("failed", "blocked", "interrupted") and not confirmed and task["id"] not in tracked:
                before_tracking = time.monotonic()
                _track_failure(task, data)
                data["spent_seconds"] += time.monotonic()-before_tracking
    data["status"] = ("cancelled" if (directory / "cancel.json").exists() else
                      "completed_unverified" if all(s == _DONE for s in statuses) else
                      "budget_exhausted" if data["spent_seconds"] >= data["budget_seconds"] else "blocked")
    data.pop("runner", None)
    if args.has("publish"):
        before_publication = time.monotonic()
        try:
            data["publication"] = _publish(directory, data, args)
        except (Failure, OSError, ValueError, subprocess.TimeoutExpired) as exc:
            data["publication"] = {"requested": True, "published": False, "status": "pending", "error": str(exc)}
        data["spent_seconds"] += time.monotonic()-before_publication
    _save(directory, data)
    return data


def command(args, action):
    action = action.removeprefix("pipeline.")
    if action == "create":
        return _create(args)
    if action == "status" and (args.has("list") or args.arg() in (None, "list")):
        base = _directory()
        return {"pipelines": [load_json(p / "state.json") for p in sorted(base.iterdir()) if p.is_dir() and not p.is_symlink() and (p / "state.json").is_file()] if base.exists() else []}
    identifier = _identifier(args.need())
    directory, data = _load(identifier)
    if action == "status":
        return {**data, "cancel_requested": (directory / "cancel.json").exists()}
    if action == "cancel":
        write_json(directory / "cancel.json", {"requested": now(), "pipeline": identifier})
        return {"id": identifier, "cancel_requested": True, "message": "Active runner stops its worker tree; worktrees and commits are preserved"}
    if action not in ("run", "resume", "retry"):
        raise Failure("unknown-pipeline-action", action, 2)
    with _ownership(directory):
        directory, data = _load(identifier)
        if args.has("budget-seconds") and action in ("run", "resume"):
            data["budget_seconds"] = data["spent_seconds"]+_number(args.get("budget-seconds"), "budget-seconds", 28800, 1, 604800)
        if action == "retry":
            _recover(directory, data)
            task = next((t for t in data["tasks"] if t["id"] == args.get("task")), None)
            if not task or task["status"] not in ("failed", "blocked", "interrupted"):
                raise Failure("pipeline-retry", "Select a failed, blocked or interrupted --task", 2)
            if task["attempts"] and not task["attempts"][-1].get("retry_safe"):
                raise Failure("pipeline-worker-uncertain", "Retry requires proof the previous worker tree ended")
            if len(task["attempts"]) >= task["max_retries"] + 1:
                raise Failure("pipeline-retries-exhausted", "Task retry limit reached")
            task.pop("reason", None)
            task["status"] = "pending"
            for dependent in data["tasks"]:
                if dependent["status"] == "blocked" and not dependent["attempts"]:
                    dependent["status"] = "pending"
                    dependent.pop("reason", None)
            data["status"] = "pending"
            _save(directory, data)
            return data  # Retry explicitly schedules; run/resume performs execution.
        return _execute(directory, data, args)
