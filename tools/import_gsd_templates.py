"""Reproduce the complete pinned GSD authoring library without abridging its bodies.

Run with --source PATH to a clone containing SOURCE_REVISION. --check compares
the generated result without writing. No network, installation, or execution of
the imported GSD workflows is performed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

SOURCE_REVISION = "c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977"
SOURCE_REPOSITORY = "https://github.com/open-gsd/gsd-core"
SOURCE_URL = f"{SOURCE_REPOSITORY}/blob/{SOURCE_REVISION}/"
ROOT = Path(__file__).resolve().parents[1]
TREES = {
    "gsd-core/templates": ".ai/templates",
    "agents": ".ai/gsd/agents",
    "commands": ".ai/gsd/commands",
    "gsd-core/references": ".ai/gsd/references",
    "gsd-core/workflows": ".ai/gsd/workflows",
    "gsd-core/contexts": ".ai/gsd/contexts",
}
NOTE_MARKER = "<!-- LOCAL-ADOPTION:START -->"
NOTE = """

<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
"""
CONFLICTS = {
    "gsd-core/templates/phase-prompt.md": [
        ("# Execution wave (1, 2, 3...). Pre-computed at plan time.", "# Advisory execution wave (1, 2, 3...). Derived from dependencies at plan time."),
        ("| `wave` | Yes | Execution wave number (1, 2, 3...). Pre-computed at plan time. |", "| `wave` | Yes | Advisory execution wave number (1, 2, 3...), derived from dependencies at plan time. |"),
        ("**Wave is pre-computed:** Wave numbers are assigned during `/gsd:plan-phase`. Execute-phase reads `wave` directly from frontmatter and groups plans by wave number. No runtime dependency analysis needed.", "**Wave is advisory:** Wave numbers are assigned during preparation to explain the dependency graph. The local execute-phase runtime evaluates `depends_on`, integrated and checked prerequisites, file ownership, exclusive resources, and available capacity. Ready plans may start immediately; a displayed wave is not a global barrier. Declare every real prerequisite rather than relying on wave order."),
    ],
    "gsd-core/templates/copilot-instructions.md": [
        ("- After completing any `gsd-*` command (or any deliverable it triggers: feature, bug fix, tests, docs, etc.), ALWAYS: (1) offer the user the next step by prompting via `ask_user`; repeat this feedback loop until the user explicitly indicates they are done.", "- After completing any `gsd-*` command (or any deliverable it triggers: feature, bug fix, tests, docs, etc.), continue the next steps already authorized by the user. Ask only when a missing decision or genuinely new authorization blocks dependent work; do not repeatedly request permission for approved scope."),
        ("- Use the gsd-core skill when the user asks for GSD or uses a `gsd-*` command.", "- When the user asks for GSD or uses a `gsd-*` command, read `.ai/gsd/README.md` and `.ai/references/gsd-adaptation.md` to resolve the requested capability to its local procedure or retained upstream definition."),
        ("- Treat `/gsd-...` or `gsd-...` as command invocations and load the matching file from `.github/skills/gsd-*`.", "- Treat `/gsd-...` or `gsd-...` as requests for the matching capability. Definitions live in `.ai/gsd/commands/gsd/`; use the active `.ai/commands/` mapping when available. An imported definition does not register a slash command or install its runtime."),
        ("- When a command says to spawn a subagent, prefer a matching custom agent from `.github/agents`.", "- When authorized orchestration calls for a subagent, use the local `.ai/agents/` responsibility and assigned worktree contract; `.ai/gsd/agents/` retains the full upstream specialist guidance. The coordinator starts workers; workers do not dispatch other workers."),
    ],
}
COMPLETED_OLD = "requirements-completed: []  # REQUIRED — Copy ALL requirement IDs from this plan's `requirements` frontmatter field."
COMPLETED_NEW = "requirements-completed: []  # REQUIRED — Include only requirement IDs from this plan's `requirements` that the delivered changes and verification evidence actually complete. Record incomplete, failed, or blocked requirements under remaining gaps; never copy them here merely because they were assigned."
for _summary in ("summary.md", "summary.compact.md"):
    CONFLICTS["gsd-core/templates/" + _summary] = [(COMPLETED_OLD, COMPLETED_NEW)]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(source: Path, *args: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(source), *args])


def read_source(source: Path) -> dict[str, bytes]:
    paths = git(source, "ls-tree", "-r", "--name-only", SOURCE_REVISION).decode().splitlines()
    # Read canonical Git blobs, independent of platform checkout line endings.
    proc = subprocess.run(
        ["git", "-C", str(source), "cat-file", "--batch"],
        input="".join(f"{SOURCE_REVISION}:{path}\n" for path in paths).encode(),
        stdout=subprocess.PIPE, check=True,
    )
    result = {}
    position = 0
    for path in paths:
        end = proc.stdout.index(b"\n", position)
        size = int(proc.stdout[position:end].split()[-1])
        position = end + 1
        result[path] = proc.stdout[position:position + size]
        position += size + 1
    return result


def destinations(files: dict[str, bytes]) -> dict[str, str]:
    return {
        path: target + path[len(prefix):]
        for path in sorted(files)
        for prefix, target in TREES.items()
        if path.startswith(prefix + "/")
    }


def aliases(mapping: dict[str, str]) -> dict[str, str]:
    result = {}
    for source, destination in mapping.items():
        variants = {source}
        variants.update(prefix + source for prefix in (
            "~/.claude/", "$HOME/.claude/", "${HOME}/.claude/",
            "~/.codex/", "$HOME/.codex/", "~/.config/opencode/",
        ))
        if source.startswith("gsd-core/"):
            variants.add(source.removeprefix("gsd-core/"))
            variants.update(prefix + source for prefix in (
                "~/.claude/", "$HOME/.claude/", "${HOME}/.claude/",
                "~/.codex/", "$HOME/.codex/", "~/.config/opencode/",
            ))
        for variant in variants:
            result[variant] = destination
    return result


def generate(files: dict[str, bytes]) -> dict[str, bytes]:
    mapping = destinations(files)
    replacements = aliases(mapping | {source + "/": destination + "/" for source, destination in TREES.items()})
    # This upstream registry points at an untracked build product. Link the
    # actual pinned implementation rather than creating a fictitious local CLI.
    replacements["gsd-core/bin/lib/artifacts.cjs"] = SOURCE_URL + "src/artifacts.cts"
    pattern = re.compile(
        r"(?<![\w./-])(?:" + "|".join(re.escape(key) for key in sorted(replacements, key=len, reverse=True)) + r")(?![\w/-]|\.[\w])"
    )
    generated = {}
    entries = []
    for source, destination in mapping.items():
        original = files[source]
        transformations = []
        if source.endswith(".md"):
            body = original.decode("utf-8")
            conflicts = []
            for old, new in CONFLICTS.get(source, []):
                if body.count(old) != 1:
                    raise ValueError(f"Conflict adaptation no longer matches exactly once: {source}: {old}")
                conflicts.append({"original": old, "replacement": new, "count": 1})
                body = body.replace(old, new)
            file_replacements = dict(replacements)
            if source.startswith("gsd-core/templates/"):
                for reference in re.findall(r"(?<![\w/-])(?:src|scripts|docs)/[\w./-]+\.(?:md|cts|cjs)", body):
                    if reference in files:
                        file_replacements[reference] = SOURCE_URL + reference
                for filename in ("state.cts", "init.cts"):
                    file_replacements[filename] = SOURCE_URL + "src/" + filename
                file_replacements["ADR-3473"] = SOURCE_URL + "docs/adr/3473-enforcement-by-construction.md"
            file_pattern = pattern if file_replacements == replacements else re.compile(
                r"(?<![\w./-])(?:" + "|".join(re.escape(key) for key in sorted(file_replacements, key=len, reverse=True)) + r")(?![\w/-]|\.[\w])"
            )
            counts = {}
            for match in file_pattern.finditer(body):
                old = match.group()
                counts.setdefault(old, []).append(match.start())
            for old, offsets in sorted(counts.items()):
                transformations.append({"original": old, "replacement": file_replacements[old], "count": len(offsets), "offsets": offsets})
            content = (file_pattern.sub(lambda match: file_replacements[match.group()], body) + NOTE).encode()
        else:
            content = original
        generated[destination] = content
        entries.append({
            "source": source, "destination": destination,
            "source_url": SOURCE_URL + source,
            "source_sha256": sha256(original), "source_bytes": len(original),
            "destination_sha256": sha256(content),
            "reference_substitutions": transformations,
            "conflict_adaptations": conflicts if source.endswith(".md") else [],
            "local_note_appended": source.endswith(".md"),
        })
    generated[".ai/gsd/LICENSE"] = files["LICENSE"]
    manifest = {
        "format_version": 1, "repository": SOURCE_REPOSITORY,
        "revision": SOURCE_REVISION,
        "policy": "Complete Git blobs, enumerated reference/conflict adaptations, additive local boundary note. No abridgement.",
        "source_tree_counts": {prefix: sum(path.startswith(prefix + "/") for path in mapping) for prefix in TREES},
        "license": {"source": "LICENSE", "source_sha256": sha256(files["LICENSE"])},
        "files": entries,
    }
    generated[".ai/gsd/PROVENANCE.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    generated[".ai/gsd/REFERENCES.json"] = (json.dumps(reference_inventory(files, mapping, entries), indent=2, ensure_ascii=False) + "\n").encode()
    generated[".ai/gsd/TEMPLATE-CHANGES.md"] = template_changes(entries).encode()
    return generated


def template_changes(entries):
    lines = [
        "# Complete template adaptation log", "",
        f"Source: {SOURCE_REPOSITORY}, revision `{SOURCE_REVISION}`.", "",
        "Generated by `tools/import_gsd_templates.py`; append this section to the",
        "migration `changes.log`. Every template is listed, including unchanged",
        "bodies. No example, counterexample, section, or guidance is abridged.", "",
        "## Shared additive note", "",
        "Every imported Markdown template and Markdown supporting file receives",
        "the following separated local note after its complete upstream body.",
        "JSON and other non-Markdown files are byte-preserved. The note resolves",
        "local execution authority without deleting upstream system descriptions.", "",
        "````text", NOTE.strip(), "````", "",
        "## Per-template substitutions", "",
    ]
    for entry in entries:
        if not entry["source"].startswith("gsd-core/templates/"):
            continue
        lines.extend([f"### `{entry['destination']}`", "", f"Source: `{entry['source']}`.", ""])
        for edit in entry["conflict_adaptations"]:
            lines.extend([
                "Conflict correction: preserve dependency-driven local scheduling,",
                "truthful completion evidence, or existing authorization and local host routing.", "",
                "Before:", "```text", edit["original"], "```", "",
                "After:", "```text", edit["replacement"], "```", "",
            ])
        if entry["reference_substitutions"]:
            lines.extend(["| Before | After | Occurrences | Reason |", "|---|---|---:|---|"])
            for edit in entry["reference_substitutions"]:
                reason = "Resolve to the complete imported local method/template."
                if edit["replacement"].startswith(SOURCE_URL):
                    reason = "Link actual pinned upstream source; no local runtime installation claimed."
                if edit["original"] == "gsd-core/bin/lib/artifacts.cjs":
                    reason = "Upstream build artifact is absent; its real source is src/artifacts.cts."
                lines.append(f"| `{edit['original']}` | `{edit['replacement']}` | {edit['count']} | {reason} |")
            lines.append("")
        elif not entry["conflict_adaptations"]:
            lines.extend(["No upstream body substitutions; " + ("shared local note appended." if entry["local_note_appended"] else "original bytes retained exactly."), ""])
    lines.extend([
        "## Supporting source adaptations", "",
        "All 447 support files are complete. Existing concrete `gsd-core/templates/`,",
        "`agents/`, `commands/`, `gsd-core/references/`, `gsd-core/workflows/`, and",
        "`gsd-core/contexts/` paths, including host install prefixes and short method",
        "paths, resolve to the corresponding `.ai/templates/` or `.ai/gsd/` files.",
        "Each exact replacement, source offset, occurrence count, and original hash",
        "is in `.ai/gsd/PROVENANCE.json`. The same additive note is appended to",
        "supporting Markdown. Source CLI examples and specialized behavior are retained.", "",
        "Concrete runtime/code/documentation references resolve individually to",
        "verified pinned upstream source paths in `.ai/gsd/REFERENCES.json`.",
        "They are source evidence rather than local executable files. Source few-shot",
        "examples referring to `context-bridge.md` and `commands/gsd/misc.md` are",
        "historical illustrations, not missing local methods to fabricate.", "",
        "The full template inventory supersedes shortened local CONTINUE, CONTEXT,",
        "DISCUSSION-LOG, IMPLEMENT, PROJECT, RESEARCH, SPEC, SUMMARY, and VERIFICATION",
        "templates. Exact upstream casing/names are retained; IMPLEMENT's replacement",
        "is phase-prompt.md (producing phase-local PLAN.md), CONTINUE's is continue-here.md,",
        "and VERIFICATION's is verification-report.md. The former current-behavior SPEC",
        "is represented separately by the local CURRENT-SPEC template because upstream",
        "spec.md describes proposed product intent. ADR remains a local-only template.", "",
    ])
    return "\n".join(lines)


def reference_inventory(files, mapping, entries):
    """Audit concrete method/source links; keep illustrative project paths intact."""
    known = set(files)
    methods = re.compile(r"(?<![\w/-])(?:gsd-core/)?(?:templates|references|workflows|contexts|agents|commands)/[\w./-]+\.(?:md|json)")
    source_paths = re.compile(r"(?<![\w/-])(?:src|scripts|docs|tests|gsd-core/bin|hooks)/[\w./-]+\.(?:md|cts|cjs|ts|js|json|sh)")
    records = []
    unresolved = []
    for entry in entries:
        if not entry["source"].endswith(".md"):
            continue
        text = files[entry["source"]].decode()
        for reference in sorted(set(methods.findall(text) + source_paths.findall(text))):
            candidates = [reference, "gsd-core/" + reference]
            if reference.startswith("gsd-core/bin/lib/") and reference.endswith(".cjs"):
                candidates.append("src/" + reference.removeprefix("gsd-core/bin/lib/").removesuffix(".cjs") + ".cts")
            resolved = next((path for path in candidates if path in known), None)
            row = {"in": entry["destination"], "reference": reference}
            if resolved:
                row.update(source=resolved, source_url=SOURCE_URL + resolved)
                if resolved in mapping:
                    row.update(kind="local-guidance", destination=mapping[resolved])
                else:
                    row.update(kind="upstream-source-only", boundary="Source evidence; not installed or executed locally.")
                records.append(row)
            else:
                row.update(kind="upstream-unresolved-or-example", boundary="Retained verbatim; no fabricated backing file. See source context before use.")
                unresolved.append(row)
    commands = {}
    for source, destination in mapping.items():
        if source.startswith("commands/gsd/") and source.endswith(".md"):
            commands["/gsd:" + Path(source).stem] = destination
    return {
        "revision": SOURCE_REVISION,
        "scope": "Concrete path tokens in retained source; project output/example paths and dynamic runtime paths are not asserted to exist.",
        "references": records, "unresolved_or_examples": unresolved,
        "command_definitions": commands,
        "command_boundary": "Definitions retained as guidance; slash-command registration and the upstream Node runtime are not installed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        worktrees = git(ROOT, "worktree", "list", "--porcelain").decode()
        primary = Path(next(line.removeprefix("worktree ") for line in worktrees.splitlines() if line.startswith("worktree "))).resolve()
        if ROOT.parent.resolve() != (primary / ".worktrees").resolve():
            parser.error("Writes require an assigned immediate-child worktree under the primary checkout's .worktrees/; --check is read-only.")
        if not git(ROOT, "branch", "--show-current").strip():
            parser.error("Writes require the assigned branch, not a detached HEAD.")
    output = generate(read_source(args.source))
    changed = []
    for destination, data in output.items():
        path = ROOT / destination
        if not path.exists() or path.read_bytes().replace(b"\r\n", b"\n") != data:
            changed.append(destination)
            if not args.check:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
    if args.check and changed:
        print("Import differs:\n" + "\n".join(changed))
        return 1
    print(f"{'Checked' if args.check else 'Imported'} {len(output)} files at {SOURCE_REVISION}; {len(changed)} differences.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
