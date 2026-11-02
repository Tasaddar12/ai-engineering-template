"""Select review evidence from actual branch history."""
import re
import fnmatch
from .core import Failure, root, run, safe_path


def evaluation(args):
    command = ["git", "log", "--format=%H%x00%s", str(args.get("ref", "HEAD"))]
    if args.has("since"):
        since = str(args.get("since"))
        if re.fullmatch(r"[a-fA-F0-9]{7,40}", since):
            revision = run(["git", "rev-parse", since+"^{commit}"], root()).stdout.strip()
            command[-1] = revision+".."+str(args.get("ref", "HEAD"))
        else:
            command.append("--since="+since)
    if args.has("committed-since"):
        command.append("--since="+str(args.get("committed-since")))
    limit = int(args.get("max-commits", 1000))
    if limit < 1:
        raise Failure("invalid-scope-limit", "max-commits must be positive", 2)
    command.append("--max-count="+str(limit))
    if args.has("pathspec"):
        command.extend(["--", *args.all("pathspec")])
    log = run(command, root()).stdout
    phase = str(args.get("phase", "")).lstrip("0") or None
    plan_value = str(args.get("plan", ""))
    if "-" in plan_value:
        inferred, plan_value = plan_value.split("-", 1)
        inferred = inferred.lstrip("0") or "0"
        if phase and phase != inferred:
            raise Failure("scope-phase-mismatch", "--phase disagrees with the plan identifier", 2)
        phase = inferred
    plan = plan_value.lstrip("0") or None
    if plan and not phase:
        raise Failure("scope-phase-required", "A bare plan number requires --phase", 2)
    commits, files, outside = [], set(), set()
    for line in log.splitlines():
        revision, subject = line.split("\0", 1)
        if args.has("milestone-bound") and re.search(r"\b(?:milestone|release)\b.*\bv\d|\bmilestone\.create\b", subject, re.I):
            break
        if phase:
            scoped = re.search(r"\((0*"+re.escape(phase)+r")(?:-(\d+))?\)", subject)
            broad = re.search(r"\bphase[ -]+0*"+re.escape(phase)+r"\b", subject, re.I)
            if not scoped and not (broad and not plan):
                outside.update(run(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", revision], root()).stdout.splitlines())
                continue
            if plan and (not scoped or not scoped.group(2) or scoped.group(2).lstrip("0") != plan):
                continue
        commits.append({"sha": revision, "subject": subject})
        diff = run(["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", revision], root()).stdout
        changed = diff.splitlines()
        if args.has("pathspec"):
            patterns = args.all("pathspec")
            changed = [path for path in changed if any(path == pattern or path.startswith(pattern.rstrip("/")+"/") or fnmatch.fnmatchcase(path, pattern) for pattern in patterns)]
        files.update(changed)
    if args.has("commits-only"):
        return "\n".join(c["sha"] for c in commits) if args.has("raw") else [c["sha"] for c in commits]
    truncated = len(log.splitlines()) >= limit
    return {"commits": commits, "files": sorted(files), "count": len(commits), "phase": phase, "plan": plan,
            "status": "partial" if truncated else "resolved" if commits else "unresolved",
            "reason": "History reached the configured bound; widen scope explicitly" if truncated else None if commits else "No matching captured task commits",
            "possibly_truncated": truncated,
            "outsideUnion": sorted(outside-files), "missingOnDisk": sorted(path for path in files if not safe_path(path).is_file())}
