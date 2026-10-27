"""Decision identifiers are explicit coverage obligations."""
import re
from . import config, records
from .core import read, safe_path


def coverage(args, kind):
    if not config.lookup(config.load(), "workflow.context_coverage_gate", True):
        return {"passed": True, "skipped": True, "uncovered": []}, 0
    directory = safe_path(args.get("dir")) if args.has("dir") else records.phase_dir(args.arg(0, args.get("phase")))
    contexts = list(directory.glob("*-CONTEXT.md"))
    ids = set(re.findall(r"\bD-\d+\b", "\n".join(read(p) for p in contexts)))
    files = list(directory.glob("*-PLAN.md" if kind == "plan" else "*-VERIFICATION.md"))
    evidence = "\n".join(read(p) for p in files)
    uncovered = sorted(identifier for identifier in ids if not re.search(r"\b"+re.escape(identifier)+r"\b", evidence))
    return {"passed": not uncovered, "decisions": sorted(ids), "uncovered": uncovered,
            "files": [str(p) for p in files]}, int(bool(uncovered))
