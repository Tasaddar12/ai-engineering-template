"""Select review evidence from actual branch history."""
import re
from .core import Failure, root, run


def evaluation(args):
    command = ["git", "log", "--format=%H%x00%s", str(args.get("ref", "HEAD"))]
    if args.has("since"):
        command.append("--since="+str(args.get("since")))
    if args.has("committed-since"):
        command.append("--since="+str(args.get("committed-since")))
    if args.has("max-commits"):
        command.append("--max-count="+str(int(args.get("max-commits"))))
    if args.has("pathspec"):
        command.extend(["--", *args.all("pathspec")])
    log = run(command, root()).stdout
    phase = str(args.get("phase", "")).lstrip("0") or None
    plan = str(args.get("plan", "")).lstrip("0") or None
    commits, files = [], set()
    for line in log.splitlines():
        revision, subject = line.split("\0", 1)
        if args.has("milestone-bound") and re.search(r"\b(?:milestone|release)\b.*\bv\d|\bmilestone\.create\b", subject, re.I):
            break
        if phase:
            scoped = re.search(r"\((0*"+re.escape(phase)+r")(?:-(\d+))?\)", subject)
            broad = re.search(r"\bphase[ -]+0*"+re.escape(phase)+r"\b", subject, re.I)
            if not scoped and not (broad and not plan):
                continue
            if plan and (not scoped or not scoped.group(2) or scoped.group(2).lstrip("0") != plan):
                continue
        commits.append({"sha": revision, "subject": subject})
        diff = run(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", revision], root()).stdout
        files.update(diff.splitlines())
    if args.has("commits-only"):
        return "\n".join(c["sha"] for c in commits) if args.has("raw") else [c["sha"] for c in commits]
    return {"commits": commits, "files": sorted(files), "count": len(commits), "phase": phase, "plan": plan}
