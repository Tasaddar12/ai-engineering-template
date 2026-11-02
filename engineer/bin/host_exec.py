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
from lib import processes


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
        process = None
        try:
            def record_ownership(ownership):
                write_json(path.with_suffix('.started.json'),{**identity,'process_ownership':ownership})
            process = processes.start_owned([request["command"],*request["args"]],cwd,
                env={**os.environ,"ENGINEER_ROOT":str(cwd),"ENGINEER_HOST":request["host"]},
                input=request["prompt"],timeout=request["timeout"],on_prepare=record_ownership)
            write_json(path.with_suffix(".started.json"),{**identity,"status":"running","process_ownership":process.ownership})
            code = process.wait()
            head = run(["git","rev-parse","HEAD"],cwd,timeout=30).stdout.strip()
            write_json(terminal,{**identity,"status":"terminal","head":head,"exit_code":code,
                "timed_out":process.proof.get("reason") == "timeout","finished":now(),"terminal":True,
                "verification":"not-certified","job_terminated":True,"process_ownership":process.ownership,"process_terminal":process.proof})
            return code
        except BaseException:
            if process is not None:
                process.stop("runner-error")
            raise
        finally:
            if process is not None and process.proof:
                process.close()


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
