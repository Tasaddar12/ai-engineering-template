"""Plan an in-place refresh of an already-installed workflow, for either host.

This is the third installation mode, and the one the other two could not cover.
`plan_install` refuses to touch a file it did not write byte-for-byte, so a
newer template revision reached an installed project as a wall of conflicts;
`plan_migration` only accepts the legacy `.ai` layout, so it could not refresh a
`.codex` or `.claude` tree either. Between them there was no supported way to
move an installed project onto a newer revision at all.

What an update is, and is not:

* **Shipped workflow material is replaced.** Runtime, hooks, commands, agents,
  guides, references, templates, skills and rules come from the new revision.
* **Project data is never touched.** Everything in `PROJECT_RECORDS` -- intent,
  requirements, roadmap, state and `config.yaml` -- stays exactly as it is, as
  do phase records, specs and decisions.
* **Host settings and the entry file are merged, not overwritten.** User hooks
  survive; only the delimited managed block in AGENTS.md/CLAUDE.md is swapped.
* **Nothing is deleted by default.** A file the new template no longer ships is
  reported, not removed, because this module cannot tell a retired template file
  from one the project added. `--prune` is the user saying which it is.

This module performs no writes. The installer backs up and verifies every
returned file before applying any change, exactly as it does for a migration.
"""

from pathlib import Path


def is_incidental(path):
    """Build artefacts and per-machine host settings the installer never wrote.

    These must never be reported as orphaned or pruned: a `__pycache__` tree is
    regenerated noise, and `settings.local.*` is the user's own machine state
    that the workflow deliberately gitignores.
    """
    if path.suffix == ".pyc" or "__pycache__" in path.parts:
        return True
    return path.name.startswith("settings.local.")


def inventory(root, installer):
    """Walk without following links, including Windows directory junctions."""
    installer.safe_path(root)
    if not root.exists():
        return []
    if not root.is_dir():
        raise ValueError(f"Update requires a directory: {root}")
    files = []
    pending = [root]
    while pending:
        for path in sorted(pending.pop().iterdir()):
            installer.safe_path(path)
            if path.is_dir():
                pending.append(path)
            elif path.is_file():
                files.append(path)
            else:
                raise ValueError(f"Unsupported entry: {path}; nothing was installed.")
    return files


def replace_managed_block(current, incoming, installer, name):
    """Swap the delimited block, preserving the project's own guidance around it."""
    start, end = installer.AGENT_MARKER.encode(), installer.AGENT_END.encode()
    if current.count(start) > 1 or current.count(end) > 1:
        raise ValueError(f"Ambiguous managed workflow block in {name}; nothing was installed.")
    if start not in current or end not in current:
        # No delimiters: an entry file written before them existed, or by hand.
        # Appending is the only safe reading -- guessing which prose was ours
        # would risk deleting the project's.
        return installer.merge_agent(current, incoming, name)
    first, last = current.index(start), current.index(end)
    if last < first:
        raise ValueError(f"Malformed managed workflow block in {name}; nothing was installed.")
    return current[:first] + incoming.rstrip(b"\n") + current[last + len(end):]


def same_text(left, right):
    """Compare ignoring line endings, which Git rewrites on checkout."""
    return left.replace(b"\r\n", b"\n") == right.replace(b"\r\n", b"\n")


def summarize(label, names, limit=12):
    listed = sorted(names)
    if len(listed) > limit:
        shown = ", ".join(listed[:limit])
        return f"{label} ({len(listed)}): {shown}, and {len(listed) - limit} more"
    return f"{label} ({len(listed)}): " + ", ".join(listed)


def plan_update(source, target, host, hooks, installer, prune=False, previous=None):
    """Return writes/exact deletions, originals to back up, and report notes."""
    if host not in ("codex", "claude"):
        raise ValueError(f"Unknown host: {host}")
    source, target = Path(source), Path(target)
    namespace = "." + host
    root = target / namespace
    installer.safe_path(target)
    installer.safe_path(root)

    if not (root / "runtime/phase.py").is_file():
        raise ValueError(
            f"--update requires an existing {namespace} installation, and "
            f"{namespace}/runtime/phase.py is not there. Install normally for a new "
            "project, or use --migrate-existing for an older .ai layout. "
            "Nothing was installed.")
    if (target / ".ai").exists():
        raise ValueError(
            f"Both .ai and {namespace} exist. Finish the migration with "
            "--migrate-existing before updating. Nothing was installed.")
    other = ".claude" if host == "codex" else ".codex"
    if (target / other / "runtime/phase.py").is_file():
        raise ValueError(
            f"A second workflow exists under {other}; reconcile dual cores before "
            "updating. Nothing was installed.")

    incoming = installer.payload(source, host, hooks)
    baseline = installer.payload(Path(previous), host, hooks) if previous else {}
    entry = "CLAUDE.md" if host == "claude" else "AGENTS.md"

    desired = {}
    backups = set()
    refreshed, added, preserved, customized = [], [], [], []

    for name, content in incoming.items():
        destination = target / name
        installer.safe_path(destination)
        for parent in destination.parents:
            if parent.exists() and not parent.is_dir():
                raise ValueError(f"Update destination parent is not a directory: {parent}")
        if destination.exists() and not destination.is_file():
            raise ValueError(f"Update destination is not a file: {destination}")
        current = destination.read_bytes() if destination.is_file() else None

        # Intent, execution history and configuration are the project's, and a
        # template revision has no authority over them.
        if name in installer.PROJECT_RECORDS:
            if current is None:
                desired[name] = content
                added.append(name)
            else:
                preserved.append(name)
            continue

        if current is None:
            desired[name] = content
            added.append(name)
            continue

        if name == entry:
            installer.require_utf8(current, destination)
            rebuilt = replace_managed_block(current, content, installer, name)
            if rebuilt != current:
                backups.add(destination)
                desired[name] = rebuilt
                refreshed.append(name)
            continue

        if name in (".codex/config.toml", ".claude/settings.json"):
            merge = (installer.merge_codex_config if name.endswith(".toml")
                     else installer.merge_hooks)
            merged = merge(current, content, destination, replace=True)
            if merged != current:
                backups.add(destination)
                desired[name] = merged
                refreshed.append(name)
            continue

        if same_text(current, content):
            continue
        # With a --from-ref baseline this is decidable: a file that already
        # differed from the revision it was installed from carries the project's
        # own edit, not an upstream change. It is still replaced -- the verified
        # backup holds the original -- but it is named separately, so
        # reconciling it is a decision rather than a discovery weeks later.
        if name in baseline and not same_text(current, baseline[name]):
            customized.append(name)
        backups.add(destination)
        desired[name] = content
        refreshed.append(name)

    # The local ignore rules, added the way a fresh install adds them.
    ignore = target / ".gitignore"
    installer.safe_path(ignore)
    if ignore.exists() and not ignore.is_file():
        raise ValueError(f"Not a file: {ignore}")
    current_ignore = ignore.read_bytes() if ignore.exists() else b""
    installer.require_utf8(current_ignore, ignore)
    addition = installer.ignore_addition(current_ignore, namespace)
    if addition:
        if ignore.exists():
            backups.add(ignore)
        desired[".gitignore"] = current_ignore + addition

    # Files under the workflow's own roots that this revision does not ship.
    retained = {target / name for name in incoming}
    retained.add(ignore)
    scan_roots = [root]
    skills = target / installer.skill_root(host)
    try:
        skills.relative_to(root)
    except ValueError:
        scan_roots.append(skills)
    orphans = [path for scan in scan_roots for path in inventory(scan, installer)
               if path not in retained and not is_incidental(path)]

    notes = [
        f"Updating the installed {namespace} workflow in place.",
        "Project records under .planning are preserved; only shipped workflow "
        "material is replaced.",
        "Every replaced or removed original is copied to .workflow-backups/ and "
        "verified before anything is written.",
    ]
    if not previous:
        notes.append("No --from-ref baseline was given, so a local customization "
                     "cannot be told apart from an upstream change. Review the "
                     "refreshed list against the backup, or rerun with "
                     "--from-ref set to the revision this project was installed from.")
    if refreshed:
        notes.append(summarize("Refresh", refreshed))
    if added:
        notes.append(summarize("Add", added))
    if preserved:
        notes.append(summarize("Preserve (project records)", preserved))
    if customized:
        notes.append("REVIEW -- these differ from the revision they were installed "
                     "from, so a local edit is being replaced: "
                     + ", ".join(sorted(customized)))

    deletes = []
    relative_orphans = sorted(path.relative_to(target).as_posix() for path in orphans)
    if orphans and prune:
        for path in orphans:
            backups.add(path)
            deletes.append((path, None))
        notes.append(summarize("Prune (no longer shipped)", relative_orphans))
        notes.append("Pruning removes files only; a directory left empty by it remains.")
    elif orphans:
        notes.append(summarize("No longer shipped, left in place -- pass --prune to "
                               "remove them", relative_orphans))

    writes = []
    for name, content in sorted(desired.items()):
        destination = target / name
        if destination.is_file() and destination.read_bytes() == content:
            continue
        writes.append((destination, content))
    return writes + deletes, sorted(backups), notes
