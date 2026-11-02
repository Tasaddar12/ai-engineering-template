"""Goal-backward artifact, link, and commit checks."""
import re
from .core import Failure, read, root, run, safe_path
from .text import split_frontmatter


def command(args, kind):
    if kind == "commits":
        revisions = args.pos or args.all("commits")
        if not revisions:
            raise Failure("missing-commits", "At least one commit is required", 2)
        missing = []
        for revision in revisions:
            exists = run(["git", "cat-file", "-e", revision+"^{commit}"], root(), check=False).returncode == 0
            ancestor = exists and run(["git", "merge-base", "--is-ancestor", revision, "HEAD"], root(), check=False).returncode == 0
            if not ancestor:
                missing.append(revision)
        return {"valid": not missing, "missing": missing}, int(bool(missing))
    path = safe_path(args.arg(0, args.get("plan", "")))
    if not path.is_file():
        raise Failure("file-not-found", str(path))
    metadata, _ = split_frontmatter(read(path))
    obligations = metadata.get("must_haves", {})
    findings = []
    for item in obligations.get("artifacts" if kind == "artifacts" else "key_links", []):
        if not isinstance(item, dict):
            findings.append({"error": "Artifact/link must be a mapping", "item": item})
            continue
        source = safe_path(item.get("path" if kind == "artifacts" else "from", ""))
        errors = []
        if not source.is_file():
            errors.append("missing")
        else:
            body = read(source)
            if kind == "artifacts":
                meaningful = [line for line in body.splitlines() if line.strip() and not re.match(r"\s*(?:#|//|/\*|\*|TODO\b|pass\b|\.\.\.)", line)]
                if len(body.splitlines()) < int(item.get("min_lines", 1)) or not meaningful:
                    errors.append("stub-or-too-short")
                patterns = item.get("contains", [])
                if isinstance(patterns, str):
                    patterns = [patterns]
            else:
                patterns = [item.get("pattern", item.get("via", ""))]
                if not patterns[0]:
                    errors.append("missing-link-pattern")
            for pattern in patterns:
                try:
                    present = re.search(pattern, body, re.M) is not None
                except re.error as exc:
                    errors.append("invalid-pattern: "+str(exc))
                    present = True
                if not present:
                    errors.append("pattern-missing: "+pattern)
        if errors:
            findings.append({"path": str(source), "errors": errors})
    return {"valid": not findings, "findings": findings}, int(bool(findings))
