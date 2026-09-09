"""The sole subprocess boundary: argv, policy, bounded evidence and deadlines.

Trusted commands are not an OS sandbox. POSIX process groups and Windows taskkill
stop ordinary descendants; a hostile process needs provider-level containment.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, BinaryIO

from .constraints import ConstraintPolicy, command_tokens
from .errors import FrameworkError, PolicyError
from .io import reject_links, safe_path, utc_now, write_yaml


@dataclass(frozen=True)
class CommandResult:
    argv: list[str]
    cwd: str
    started_at: str
    finished_at: str
    returncode: int | None
    stdout: str
    stderr: str
    status: str
    # A stream is truncated if raw bytes were discarded OR its redacted display
    # was bounded. Complete output additionally requires successful EOF capture.
    stdout_truncated: bool = False
    stderr_truncated: bool = False
    output_complete: bool = True

    @property
    def ok(self) -> bool:
        return self.status in {"success", "expected_failure"}


class _Capture:
    def __init__(self, limit: int):
        self.limit = limit
        self.data = bytearray()
        self.lock = threading.Lock()
        self.truncated = False
        self.finished = False
        self.failed = False

    def drain(self, stream: BinaryIO) -> None:
        try:
            while chunk := stream.read(4096):
                with self.lock:
                    remaining = max(0, self.limit - len(self.data))
                    self.truncated |= len(chunk) > remaining
                    self.data.extend(chunk[:remaining])
        except (OSError, ValueError):
            with self.lock:
                self.failed = True
        finally:
            try:
                stream.close()
            except (OSError, ValueError):
                with self.lock:
                    self.failed = True
            with self.lock:
                self.finished = True

    def text(self) -> str:
        with self.lock:
            return self.data.decode("utf-8", errors="replace")


def _send_input(stream: BinaryIO, content: bytes) -> None:
    try:
        stream.write(content)
        stream.flush()
    except (OSError, ValueError):
        pass
    finally:
        stream.close()


class _WindowsJob:
    """Keep ordinary descendants owned even after their parent exits.

    The command starts suspended, is assigned to a kill-on-close job, then resumes.
    This also covers fast executable launchers that spawn their real interpreter.
    """

    def __init__(self, process: subprocess.Popen[bytes]):
        import ctypes
        from ctypes import wintypes

        class Basic(ctypes.Structure):
            _fields_ = [
                ("process_time", ctypes.c_longlong),
                ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD),
                ("min_working", ctypes.c_size_t),
                ("max_working", ctypes.c_size_t),
                ("active", wintypes.DWORD),
                ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD),
            ]

        class Limits(ctypes.Structure):
            _fields_ = [
                ("basic", Basic),
                ("io", ctypes.c_ulonglong * 6),
                ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t),
                ("peak_process", ctypes.c_size_t),
                ("peak_job", ctypes.c_size_t),
            ]

        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)  # type: ignore[attr-defined]
        self.kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        self.kernel.CreateJobObjectW.restype = wintypes.HANDLE
        self.kernel.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        self.kernel.SetInformationJobObject.restype = wintypes.BOOL
        self.kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        self.kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        self.kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel.TerminateJobObject.restype = wintypes.BOOL
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        self.kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenProcess.restype = wintypes.HANDLE
        self.kernel.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            *([ctypes.POINTER(wintypes.FILETIME)] * 4),
        ]
        self.kernel.GetProcessTimes.restype = wintypes.BOOL
        self.kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        self.kernel.TerminateProcess.restype = wintypes.BOOL
        self.root_pid = process.pid
        self.processes = {process.pid: int(process._handle)}  # type: ignore[attr-defined]
        self.handle = self.kernel.CreateJobObjectW(None, None)
        if not self.handle:
            raise OSError(ctypes.get_last_error(), "Cannot create process job")  # type: ignore[attr-defined]
        limits = Limits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.kernel.SetInformationJobObject(
            self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ) or not self.kernel.AssignProcessToJobObject(
            self.handle,
            int(process._handle),  # type: ignore[attr-defined]
        ):
            error = ctypes.get_last_error()  # type: ignore[attr-defined]
            self.close()
            raise OSError(error, "Cannot attach command to process job")

    def _lifespan(self, handle: int) -> tuple[int, int]:
        import ctypes
        from ctypes import wintypes

        times = [wintypes.FILETIME() for _ in range(4)]
        if not self.kernel.GetProcessTimes(handle, *(ctypes.byref(value) for value in times)):
            raise OSError(ctypes.get_last_error(), "Cannot verify descendant process identity")  # type: ignore[attr-defined]
        created, exited = times[:2]
        return (created.dwHighDateTime << 32) | created.dwLowDateTime, (
            exited.dwHighDateTime << 32
        ) | exited.dwLowDateTime

    def observe(self) -> None:
        """Track retained process handles, including venv descendants that leave a job.

        Parent/child creation times prevent a recycled PID from identifying an
        unrelated process. This is not a sandbox against hostile brokered spawning.
        """
        import ctypes
        from ctypes import wintypes

        class ProcessEntry(ctypes.Structure):
            _fields_ = [
                ("size", wintypes.DWORD),
                ("usage", wintypes.DWORD),
                ("pid", wintypes.DWORD),
                ("heap", ctypes.c_size_t),
                ("module", wintypes.DWORD),
                ("threads", wintypes.DWORD),
                ("parent", wintypes.DWORD),
                ("priority", wintypes.LONG),
                ("flags", wintypes.DWORD),
                ("executable", wintypes.WCHAR * 260),
            ]

        self.kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
        self.kernel.Process32FirstW.restype = wintypes.BOOL
        self.kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(ProcessEntry)]
        self.kernel.Process32NextW.restype = wintypes.BOOL
        snapshot = self.kernel.CreateToolhelp32Snapshot(2, 0)  # TH32CS_SNAPPROCESS
        if snapshot == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error(), "Cannot observe command descendants")  # type: ignore[attr-defined]
        entries: list[tuple[int, int]] = []
        try:
            entry = ProcessEntry()
            entry.size = ctypes.sizeof(entry)
            found = self.kernel.Process32FirstW(snapshot, ctypes.byref(entry))
            while found:
                entries.append((entry.pid, entry.parent))
                found = self.kernel.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            self.kernel.CloseHandle(snapshot)
        changed = True
        while changed:
            changed = False
            for pid, parent in entries:
                if pid in self.processes or parent not in self.processes:
                    continue
                handle = self.kernel.OpenProcess(0x1001, False, pid)
                if not handle:  # Already exited, or not inspectable; never guess its identity.
                    continue
                try:
                    created, _ = self._lifespan(handle)
                    parent_created, parent_exited = self._lifespan(self.processes[parent])
                    if created < parent_created or (parent_exited and created > parent_exited):
                        continue
                    if len(self.processes) >= 1024:
                        raise OSError("Command exceeded 1024 descendant process limit")
                    self.processes[pid] = handle
                    handle = None
                    changed = True
                finally:
                    if handle:
                        self.kernel.CloseHandle(handle)

    def resume(self, process: subprocess.Popen[bytes]) -> None:
        import ctypes
        from ctypes import wintypes

        class ThreadEntry(ctypes.Structure):
            _fields_ = [
                ("size", wintypes.DWORD),
                ("usage", wintypes.DWORD),
                ("thread", wintypes.DWORD),
                ("owner", wintypes.DWORD),
                ("base_priority", wintypes.LONG),
                ("delta_priority", wintypes.LONG),
                ("flags", wintypes.DWORD),
            ]

        self.kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
        self.kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
        self.kernel.Thread32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
        self.kernel.Thread32First.restype = wintypes.BOOL
        self.kernel.Thread32Next.argtypes = [wintypes.HANDLE, ctypes.POINTER(ThreadEntry)]
        self.kernel.Thread32Next.restype = wintypes.BOOL
        self.kernel.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self.kernel.OpenThread.restype = wintypes.HANDLE
        self.kernel.ResumeThread.argtypes = [wintypes.HANDLE]
        self.kernel.ResumeThread.restype = wintypes.DWORD
        snapshot = self.kernel.CreateToolhelp32Snapshot(4, 0)  # TH32CS_SNAPTHREAD
        if snapshot == ctypes.c_void_p(-1).value:
            raise OSError(ctypes.get_last_error(), "Cannot inspect suspended command")  # type: ignore[attr-defined]
        try:
            entry = ThreadEntry()
            entry.size = ctypes.sizeof(entry)
            found = self.kernel.Thread32First(snapshot, ctypes.byref(entry))
            while found:
                if entry.owner == process.pid:
                    thread = self.kernel.OpenThread(2, False, entry.thread)  # THREAD_SUSPEND_RESUME
                    if not thread:
                        raise OSError(ctypes.get_last_error(), "Cannot open command thread")  # type: ignore[attr-defined]
                    try:
                        if self.kernel.ResumeThread(thread) == 0xFFFFFFFF:
                            raise OSError(ctypes.get_last_error(), "Cannot resume command")  # type: ignore[attr-defined]
                    finally:
                        self.kernel.CloseHandle(thread)
                    return
                found = self.kernel.Thread32Next(snapshot, ctypes.byref(entry))
            raise OSError("Suspended command thread was not found")
        finally:
            self.kernel.CloseHandle(snapshot)

    def stop(self) -> bool:
        observed = True
        try:
            self.observe()
        except OSError:
            observed = False
        for handle in reversed(list(self.processes.values())):
            self.kernel.TerminateProcess(handle, 1)
        stopped = bool(self.kernel.TerminateJobObject(self.handle, 1))
        return observed and stopped

    def close(self) -> None:
        for pid, handle in self.processes.items():
            if pid != self.root_pid:
                self.kernel.CloseHandle(handle)
        self.processes = {}
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def _stop_tree(process: subprocess.Popen[bytes], job: _WindowsJob | None = None) -> str:
    """Never wait indefinitely, even if a child holds inherited output pipes."""
    warning = ""
    if job is not None:
        if not job.stop():
            warning = "Process-job termination could not be confirmed."
    elif os.name == "nt":
        # Absolute OS utility path avoids a project/PATH-supplied taskkill shim.
        taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/taskkill.exe"
        try:
            stopped = subprocess.run(
                [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
                check=False,
            )
            if stopped.returncode:
                warning = "Process-tree termination could not be confirmed."
        except (OSError, subprocess.SubprocessError):
            warning = "Process-tree termination could not be confirmed."
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)  # type: ignore[attr-defined]
        except ProcessLookupError:
            pass
        except OSError:
            warning = "Process-group termination could not be confirmed."
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        warning = "Process termination could not be confirmed."
    return warning


class CommandRunner:
    def __init__(
        self,
        root: Path,
        constraints: dict[str, Any],
        run_dir: Path | None = None,
        dry_run: bool = False,
        grants: Iterable[str] = (),
    ):
        self.root = Path(root).absolute()
        reject_links(self.root)
        self.policy = ConstraintPolicy(constraints, grants)
        self.policy.root = self.root
        self.dry_run = dry_run
        self.run_dir = self._contained(run_dir or self.root / ".ai/local/commands", exists=False)
        execution = constraints.get("execution", {})
        self.limit = execution.get("max_output_chars", 65536)
        if not isinstance(self.limit, int) or not 256 <= self.limit <= 1_000_000:
            raise FrameworkError("execution.max_output_chars must be 256..1000000")
        self.secrets = sorted(
            {os.environ[name] for name in execution.get("redact_env", []) if os.environ.get(name)},
            key=len,
            reverse=True,
        )

    def _contained(self, path: Path, *, exists: bool = True) -> Path:
        path = Path(path)
        if not path.is_absolute():
            path = self.root / path
        try:
            relative = path.relative_to(self.root)
            target = self.root if relative == Path(".") else safe_path(self.root, relative)
            reject_links(target)
        except (ValueError, FrameworkError) as exc:
            raise PolicyError("Command/evidence path must stay inside an unlinked project") from exc
        if exists and not target.is_dir():
            raise PolicyError(f"Command cwd is not a directory: {target}")
        return target

    def _redact(self, text: str, *, bounded: bool = True) -> str:
        for secret in self.secrets:
            text = text.replace(secret, "[REDACTED]")
            # The bounded capture can end midway through a secret.
            for length in range(min(len(secret) - 1, len(text)), 0, -1):
                if text.endswith(secret[:length]):
                    text = text[:-length] + "[REDACTED]"
                    break
        return text[: self.limit] if bounded else text

    def _executable(self, argv: Sequence[str]) -> list[str]:
        tokens = command_tokens(argv)
        executable = tokens[0]
        if executable == "python":
            executable = sys.executable
        elif not Path(executable).is_absolute():
            if "/" in executable or "\\" in executable:
                raise PolicyError("Executable paths must be absolute or configured program names")
            # Windows resolves the current directory before PATH unless explicitly excluded.
            search = []
            for entry in os.get_exec_path():
                candidate = Path(entry).absolute()
                if entry and not candidate.is_relative_to(self.root):
                    search.append(entry)
            found = shutil.which(executable, path=os.pathsep.join(search))
            if found is None:
                raise FileNotFoundError(f"Executable not found: {executable}")
            if Path(found).absolute().is_relative_to(self.root):
                raise PolicyError("Project executables require an explicit absolute-path rule")
            executable = found
        command_tokens([executable])  # Reject an implicitly resolved .cmd/.bat, too.
        return [executable, *tokens[1:]]

    def _environment(self, argv: list[str]) -> dict[str, str]:
        env = dict(os.environ)
        if command_tokens(argv)[0] == "git":
            env = {key: value for key, value in env.items() if not key.startswith("GIT_")}
            # Neither local hooks nor external diff/fsmonitor helpers belong to a Git primitive.
            configs = {
                "core.hooksPath": os.devnull,
                "core.fsmonitor": "false",
                "core.pager": "cat",
                "credential.helper": "",
                "diff.external": "",
            }
            env["GIT_CONFIG_COUNT"] = str(len(configs))
            for index, (key, value) in enumerate(configs.items()):
                env[f"GIT_CONFIG_KEY_{index}"] = key
                env[f"GIT_CONFIG_VALUE_{index}"] = value
            env.update(GIT_TERMINAL_PROMPT="0", GIT_PAGER="cat", GIT_OPTIONAL_LOCKS="0")
        return env

    def run(
        self,
        argv: Sequence[str],
        cwd: Path | None = None,
        *,
        timeout: float = 120,
        expected_exit_codes: Sequence[int] = (0,),
        role: str = "orchestrator",
        action: str | None = None,
        input_text: str | None = None,
    ) -> CommandResult:
        if not isinstance(timeout, (float, int)) or not 0 < timeout <= 86400:
            raise FrameworkError("Command timeout must be positive and at most one day")
        if input_text is not None and len(input_text.encode("utf-8")) > 2_000_000:
            raise FrameworkError("Command input exceeds size limit")
        started = utc_now()
        directory = self._contained(cwd or self.root)
        # Validate before logging; never serialize a caller-supplied shell string.
        tokens = command_tokens(argv)
        captures: list[_Capture] = []

        def finish(
            status: str, code: int | None, stdout: str = "", stderr: str = ""
        ) -> CommandResult:
            displayed = [self._redact(value, bounded=False) for value in (stdout, stderr)]
            truncated = [len(value) > self.limit for value in displayed]
            complete = bool(captures) and status in {"success", "expected_failure", "failed"}
            for index, capture in enumerate(captures):
                with capture.lock:
                    truncated[index] |= capture.truncated
                    complete &= capture.finished and not capture.failed
            complete &= not any(truncated)
            result = CommandResult(
                [self._redact(token) for token in tokens],
                self._redact(str(directory)),
                started,
                utc_now(),
                code,
                displayed[0][: self.limit],
                displayed[1][: self.limit],
                status,
                truncated[0],
                truncated[1],
                complete,
            )
            if not self.dry_run:
                destination = self._contained(self.run_dir, exists=False)
                write_yaml(destination / f"command-{uuid.uuid4().hex}.yaml", asdict(result))
            return result

        try:
            self.policy.check_command(tokens, role, action)
        except PolicyError as exc:
            finish("denied", None, stderr=str(exc))
            raise
        if self.dry_run:
            return finish("dry_run", None)
        process: subprocess.Popen[bytes] | None = None
        job: _WindowsJob | None = None
        captures = [
            _Capture(self.limit * 4 + max(map(len, self.secrets), default=0) * 4) for _ in range(2)
        ]
        try:
            process = subprocess.Popen(
                self._executable(tokens),
                cwd=directory,
                env=self._environment(tokens),
                stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                close_fds=True,
                creationflags=(
                    subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW | 4  # type: ignore[attr-defined]
                )  # CREATE_SUSPENDED
                if os.name == "nt"
                else 0,
                start_new_session=os.name != "nt",
            )
            if os.name == "nt":
                job = _WindowsJob(process)
                job.resume(process)
            assert process.stdout is not None and process.stderr is not None
            threads = []
            for capture, stream in zip(captures, (process.stdout, process.stderr), strict=True):
                thread = threading.Thread(target=capture.drain, args=(stream,), daemon=True)
                thread.start()
                threads.append(thread)
            if input_text is not None:
                assert process.stdin is not None
                thread = threading.Thread(
                    target=_send_input,
                    args=(process.stdin, input_text.encode("utf-8")),
                    daemon=True,
                )
                thread.start()
                threads.append(thread)
            deadline = time.monotonic() + timeout
            while process.poll() is None or any(thread.is_alive() for thread in threads):
                if job is not None:
                    job.observe()
                if time.monotonic() >= deadline:
                    warning = _stop_tree(process, job)
                    for thread in threads:
                        thread.join(timeout=0.2)
                    return finish(
                        "timeout",
                        process.returncode,
                        captures[0].text(),
                        captures[1].text() + "\n" + warning,
                    )
                time.sleep(0.01)
            code = process.returncode
            status = (
                "failed"
                if code not in expected_exit_codes
                else "success"
                if code == 0
                else "expected_failure"
            )
            return finish(status, code, captures[0].text(), captures[1].text())
        except PolicyError as exc:
            finish("denied", None, stderr=str(exc))
            raise
        except (OSError, subprocess.SubprocessError) as exc:
            if process is not None:
                _stop_tree(process, job)
            return finish("error", None, stderr=str(exc))
        finally:
            if job is not None:
                job.close()
