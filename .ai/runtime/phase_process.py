"""Record a recoverable process identity before starting a phase worker."""
from pathlib import Path
import os
import subprocess
import sys

from phase_records import read_yaml
from phase_runner import atomic_yaml, process_identity


def main():
    spec = read_yaml(Path(sys.argv[1]).read_text(encoding="utf-8"))
    receipt_path = Path(spec["receipt"])
    receipt = {"pid": os.getpid(), "process_identity": process_identity(os.getpid()), "status": "starting"}
    atomic_yaml(receipt_path, receipt)
    with Path(spec["input"]).open("r", encoding="utf-8") as incoming, Path(spec["log"]).open("w", encoding="utf-8") as outgoing:
        try:
            process = subprocess.Popen(spec["argv"], cwd=spec["root"], stdin=incoming, stdout=outgoing, stderr=subprocess.STDOUT)
            receipt.update(status="running", child_pid=process.pid, child_identity=process_identity(process.pid))
            atomic_yaml(receipt_path, receipt)
            code = process.wait()
        except OSError as exc:
            outgoing.write(f"Could not start worker: {exc}\n")
            code = 127
    receipt.update(status="finished", returncode=code)
    atomic_yaml(receipt_path, receipt)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
