"""Bounded cited evidence inputs for discussion, research and pattern mapping."""
import re
from . import records
from .core import Failure, digest, read, safe_path


def inputs(args, kind):
    directory = records.phase_dir(args.arg(0, args.get("phase")))
    suffixes = {"discuss": ("SPEC", "CONTEXT", "DISCUSSION-LOG"), "research": ("SPEC", "CONTEXT", "RESEARCH"),
                "patterns": ("CONTEXT", "RESEARCH", "PATTERNS")}
    if kind not in suffixes:
        raise Failure("unknown-research-input-kind", kind, 2)
    paths = [safe_path(p) for suffix in suffixes[kind] for p in sorted(directory.glob("*-"+suffix+".md"))]
    shared = [records.planning()/name for name in ("PROJECT.md", "REQUIREMENTS.md", "ROADMAP.md", "STATE.md")]
    artifacts = [{"path": str(path), "digest": digest([path]), "content": read(path)} for path in paths+shared if path.is_file()]
    # Only explicit path tokens become mapping candidates. They are evidence
    # inputs, not a determination of which implementation pattern is correct.
    candidates, missing = set(), set()
    for artifact in artifacts:
        for value in re.findall(r"`([^`\n]+)`", artifact["content"]):
            if "/" not in value and "\\" not in value:
                continue
            try:
                path = safe_path(value)
                (candidates if path.is_file() else missing).add(str(path))
            except (Failure, OSError):
                continue
    return {"phase_dir": str(directory), "kind": kind, "artifacts": artifacts, "source_candidates": sorted(candidates),
            "missing_candidates": sorted(missing), "approval": "Requires actual recorded human decisions; not inferred from source presence"}
