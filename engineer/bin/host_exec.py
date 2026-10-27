#!/usr/bin/env python3
"""Execute one pinned host request; never report completion before child exit."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import dispatch
from lib.core import Failure, load_json, now, run, write_json
from lib.locking import acquire
from lib.pipelines import _WindowsJob, _stop


def execute(path):
    path, request = dispatch.load_request(path)
    terminal = path.with_suffix(".terminal.json")
    with acquire(path.with_suffix(".lock"), timeout=0):
        if terminal.exists() or path.with_suffix(".started.json").exists():
            raise Failure("dispatch-already-started", "Reconcile the original request; never launch it twice")
        cwd = Path(request["cwd"])
        base = run(["git", "rev-parse", "HEAD"], cwd, timeout=30).stdout.strip()
        identity = {"request_id": request["id"], "request_digest": request["digest"], "path": str(cwd),
                    "branch": run(["git", "branch", "--show-current"], cwd, timeout=30).stdout.strip(),
                    "base": base, "pid": os.getpid(), "started": now(), "status": "launching"}
        write_json(path.with_suffix(".started.json"), identity)
        job = _WindowsJob()
        process = None
        timed_out = False
        try:
            options = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP | 0x4} if os.name == "nt" else {"start_new_session": True}
            process = subprocess.Popen([request["command"], *request["args"]], cwd=cwd, stdin=subprocess.PIPE,
                                       env={**os.environ, "ENGINEER_ROOT": str(cwd), "ENGINEER_HOST": request["host"]},
                                       shell=False, **options)
            job.assign(process)
            if os.name == "nt":
                job.resume(process)
            def send_prompt():
                try:
                    process.stdin.write(request["prompt"].encode("utf-8"))
                    process.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
            sender = threading.Thread(target=send_prompt, daemon=True)
            sender.start()
            try:
                code = process.wait(timeout=request["timeout"])
            except subprocess.TimeoutExpired:
                timed_out = True
                if not _stop(process, job):
                    raise Failure("dispatch-worker-uncertain", "Cannot prove host descendants stopped")
                code = 124
            if os.name == "nt":
                job.stop()
            else:
                # Kill only the owned group; normal leader exit may leave children.
                if not _stop(process):
                    raise Failure("dispatch-worker-uncertain", "Cannot prove host descendants stopped")
            sender.join(timeout=5)
            head = run(["git", "rev-parse", "HEAD"], cwd, timeout=30).stdout.strip()
            write_json(terminal, {**identity, "status": "terminal", "head": head, "exit_code": code,
                                  "timed_out": timed_out, "finished": now(), "terminal": True,
                                  "verification": "not-certified", "job_terminated": True})
            return code
        except BaseException:
            if process is not None:
                _stop(process, job)
            raise
        finally:
            job.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    try:
        return execute(args.request)
    except (Failure, OSError, TimeoutError, ValueError) as exc:
        print(json.dumps({"error": getattr(exc, "code", "host-exec-failed"), "message": str(exc)}), file=sys.stderr)
        return getattr(exc, "status", 1)


if __name__ == "__main__":
    raise SystemExit(main())
