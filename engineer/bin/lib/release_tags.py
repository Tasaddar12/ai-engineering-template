"""Preflight an explicit local release-tag map before creating annotated tags."""
from pathlib import Path
from . import config
from .core import Failure, input_json, root, run, safe_path


def load_map(value):
    packet = input_json(value)
    entries = packet.get("repositories") if isinstance(packet, dict) else packet
    if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
        raise Failure("invalid-release-map", "Supply an array or {repositories: [...]} of repository release entries", 2)
    return packet, entries


def command(args):
    if not args.has("map"):
        raise Failure("release-map-required", "Supply --map FILE", 2)
    _, entries = load_map(args.get("map"))
    settings = config.load()
    configured = config.lookup(settings, "planning.sub_repos", settings.get("sub_repos", []))
    if not isinstance(configured, list) or not all(isinstance(item, str) for item in configured):
        raise Failure("invalid-sub-repositories", "sub_repos must be an array of repository paths", 2)
    allowed = {safe_path(value).resolve() for value in configured}
    results, selected, seen = [], [], set()
    for entry in entries:
        name = entry.get("repo")
        if not isinstance(name, str) or not name:
            raise Failure("invalid-release-repository", "Each release entry requires repo", 2)
        repository = safe_path(name)
        if repository == root() or repository not in allowed:
            raise Failure("release-repository-not-configured", name, 2)
        actual = Path(run(["git", "rev-parse", "--show-toplevel"], repository).stdout.strip()).resolve()
        if actual != repository:
            raise Failure("release-repository-root", name, 2)
        tag = entry.get("tag")
        record = {"repo": name, "tag": tag, "ref": entry.get("ref", "HEAD")}
        if tag is None or tag is False or tag == "" or config.lookup(settings, "git.create_tag", True) is False:
            results.append({**record, "status": "skipped"})
            continue
        if not isinstance(tag, str) or tag.startswith("-") or run(["git", "check-ref-format", "refs/tags/" + tag], repository, check=False).returncode:
            raise Failure("invalid-release-tag", str(tag), 2)
        if (repository, tag) in seen:
            raise Failure("duplicate-release-tag", name + ":" + tag, 2)
        seen.add((repository, tag))
        reference = record["ref"]
        message = entry.get("message", "Release " + tag)
        if not isinstance(reference, str) or not reference or not isinstance(message, str) or not message.strip():
            raise Failure("invalid-release-entry", "ref and message must be nonempty text", 2)
        commit = run(["git", "rev-parse", "--verify", "--end-of-options", reference + "^{commit}"], repository).stdout.strip()
        existing = run(["git", "rev-parse", "--verify", "--end-of-options", "refs/tags/" + tag + "^{commit}"], repository, check=False)
        exists = run(["git", "show-ref", "--verify", "--quiet", "refs/tags/" + tag], repository, check=False).returncode == 0
        if exists and existing.returncode:
            raise Failure("release-tag-conflict", name + ":" + tag + " does not resolve to a commit")
        if not existing.returncode and existing.stdout.strip() != commit:
            raise Failure("release-tag-conflict", name + ":" + tag + " already points to a different commit")
        status = "already_tagged" if not existing.returncode else "would_tag"
        record.update(commit=commit, status=status)
        results.append(record)
        if status == "would_tag":
            selected.append((repository, tag, commit, message, record))
    # The complete map is valid before the first tag is written. No force or push.
    created = 0
    if not args.has("dry-run"):
        for repository, tag, commit, message, record in selected:
            try:
                run(["git", "tag", "-a", tag, commit, "-m", message], repository)
            except Failure as error:
                raise Failure("release-tag-create", error.message, completed=results, created=created) from error
            record["status"] = "tagged"
            created += 1
    return {"dry_run": args.has("dry-run"), "results": results, "created": created, "pushed": False}
