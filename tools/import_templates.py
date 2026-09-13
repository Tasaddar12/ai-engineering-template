"""Reproduce the complete pinned authoring library without abridging its bodies.

Run with --source PATH to a clone containing SOURCE_REVISION. --check compares
the generated result without writing. No network, installation, or execution of
the imported workflows is performed. Source names remain only in audit machinery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
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
    "agents": ".ai/library/agents",
    "commands": ".ai/library/commands",
    "gsd-core/references": ".ai/library/references",
    "gsd-core/workflows": ".ai/library/workflows",
    "gsd-core/contexts": ".ai/library/contexts",
}
NOTE_MARKER = "<!-- LOCAL-ADOPTION:START -->"
NOTE = """

<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
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
        path: target + path[len(prefix):].replace("/gsd/", "/").replace("/gsd-", "/")
        for path in sorted(files)
        for prefix, target in TREES.items()
        if path.startswith(prefix + "/")
    }


def apply_recorded(text, replacements):
    """Apply non-overlapping substitutions and retain offsets for exact reversal."""
    if not replacements:
        return text, []
    pattern = re.compile("|".join(re.escape(key) for key in sorted(replacements, key=len, reverse=True)))
    counts = {}
    for match in pattern.finditer(text):
        counts.setdefault(match.group(), []).append(match.start())
    edits = [{"original": old, "replacement": replacements[old], "count": len(offsets), "offsets": offsets}
             for old, offsets in sorted(counts.items())]
    return pattern.sub(lambda match: replacements[match.group()], text), edits


def source_pointer(url, catalog, destination, markdown=False):
    key = "source-" + sha256(url.encode())[:16]
    catalog[key] = url
    path = ".ai/library/SOURCES.md"
    if markdown:
        path = posixpath.relpath(path, posixpath.dirname(destination))
    return path + "#" + key


def resolve_markdown_links(body, source, destination, files, mapping, catalog):
    replacements = {}
    for match in re.finditer(r"(?<=\]\()([^\s)]+)(?=\))", body):
        original = match.group()
        if original.startswith(("http:", "https:", "#", "mailto:")):
            continue
        path, sep, fragment = original.partition("#")
        candidates = [posixpath.normpath(posixpath.join(posixpath.dirname(source), path))]
        # These source links assumed a different installed/source directory depth.
        candidates.extend([path.lstrip("./"), "docs/" + path.split("docs/", 1)[-1]] if "docs/" in path else [path.lstrip("./")])
        resolved = next((candidate for candidate in candidates if candidate in files), None)
        if not resolved:
            continue
        if resolved in mapping:
            target = posixpath.relpath(mapping[resolved], posixpath.dirname(destination))
            if sep:
                target += "#" + fragment
        else:
            target = source_pointer(SOURCE_URL + resolved + (sep + fragment if sep else ""), catalog, destination, markdown=True)
        if original != target:
            replacements[original] = target
    return apply_recorded(body, replacements)


def neutral_namespace(body, destination, mapping, catalog):
    replacements = {
        ".ai/gsd/commands/gsd/": ".ai/library/commands/",
        ".ai/gsd/": ".ai/library/",
        ".ai/references/gsd-adaptation.md": ".ai/references/template-adaptation.md",
        "commands/gsd/": "commands/",
        "Open GSD": "the upstream authors (see third-party notices)",
        "Get Shit Done": "Project workflow",
        "get-shit-done": "project-workflow",
    }
    for source, target in mapping.items():
        if source.startswith("agents/gsd-"):
            replacements[Path(source).stem] = Path(target).stem
    for match in re.finditer(r"open-gsd/gsd-core(?:#(\d+))?", body):
        url = SOURCE_REPOSITORY + ("/issues/" + match.group(1) if match.group(1) else "/tree/" + SOURCE_REVISION)
        replacements[match.group()] = source_pointer(url, catalog, destination)
    # URLs must remain real. Move source-brand URLs to a dedicated provenance
    # catalog instead of fabricating renamed hosts or repositories.
    for match in re.finditer(r"https?://[^\s<>`\"')]+", body):
        url = match.group().rstrip(".,;")
        if re.search("gsd|get-shit-done", url, re.IGNORECASE):
            markdown = body[max(0, match.start() - 2):match.start()] == "](" 
            replacements[url] = source_pointer(url, catalog, destination, markdown=markdown)
    stage_one, first = apply_recorded(body, replacements)
    spellings = {match.group() for match in re.finditer("gsd", stage_one, re.IGNORECASE)}
    stage_two, second = apply_recorded(stage_one, {spelling: "Workflow" if spelling[0].isupper() else "workflow" for spelling in spellings})
    return stage_two, [first, second]


def aliases(mapping: dict[str, str]) -> dict[str, str]:
    result = {}
    for source, destination in mapping.items():
        variants = {source}
        variants.update(prefix + source for prefix in (
            "~/.claude/", "$HOME/.claude/", "${HOME}/.claude/",
            "~/.codex/", "$HOME/.codex/", "~/.config/opencode/", "./.claude/", ".claude/",
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
    directories = {source + "/": destination + "/" for source, destination in TREES.items()}
    directories.update({posixpath.dirname(source) + "/": posixpath.dirname(destination) + "/" for source, destination in mapping.items()})
    replacements = aliases(mapping | directories)
    # This upstream registry points at an untracked build product. Link the
    # actual pinned implementation rather than creating a fictitious local CLI.
    replacements["gsd-core/bin/lib/artifacts.cjs"] = SOURCE_URL + "src/artifacts.cts"
    pattern = re.compile(
        r"(?<![\w./-])(?:" + "|".join(re.escape(key) for key in sorted(replacements, key=len, reverse=True)) + r")(?![\w/-]|\.[\w])"
    )
    generated = {}
    entries = []
    catalog = {}
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
            body, markdown_edits = resolve_markdown_links(body, source, destination, files, mapping, catalog)
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
            body = file_pattern.sub(lambda match: file_replacements[match.group()], body)
            body, namespace_stages = neutral_namespace(body, destination, mapping, catalog)
            content = (body + NOTE).encode()
        else:
            body = original.decode()
            counts = {}
            for match in pattern.finditer(body):
                counts.setdefault(match.group(), []).append(match.start())
            transformations = [{"original": old, "replacement": replacements[old], "count": len(offsets), "offsets": offsets}
                               for old, offsets in sorted(counts.items())]
            body = pattern.sub(lambda match: replacements[match.group()], body)
            body, namespace_stages = neutral_namespace(body, destination, mapping, catalog)
            content = body.encode()
            markdown_edits = []
        generated[destination] = content
        entries.append({
            "source": source, "destination": destination,
            "source_url": SOURCE_URL + source,
            "source_sha256": sha256(original), "source_bytes": len(original),
            "destination_sha256": sha256(content),
            "reference_substitutions": transformations,
            "markdown_substitutions": markdown_edits,
            "namespace_stages": namespace_stages,
            "conflict_adaptations": conflicts if source.endswith(".md") else [],
            "local_note_appended": source.endswith(".md"),
        })
    generated[".ai/library/LICENSE"] = files["LICENSE"]
    manifest = {
        "format_version": 2, "repository": SOURCE_REPOSITORY,
        "audience": "Provenance-only; source identity is not the active workflow namespace.",
        "revision": SOURCE_REVISION,
        "policy": "Complete Git blobs, reversible reference/namespace/conflict adaptations, additive local boundary note. No abridgement.",
        "source_tree_counts": {prefix: sum(path.startswith(prefix + "/") for path in mapping) for prefix in TREES},
        "license": {"source": "LICENSE", "source_sha256": sha256(files["LICENSE"])},
        "files": entries,
    }
    generated[".ai/library/PROVENANCE.json"] = (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode()
    generated[".ai/library/REFERENCES.json"] = (json.dumps(reference_inventory(files, mapping, entries), indent=2, ensure_ascii=False) + "\n").encode()
    generated[".ai/library/TEMPLATE-CHANGES.md"] = template_changes(entries).encode()
    generated[".ai/library/SOURCES.md"] = ("# Source evidence catalog\n\nProvenance-only: original third-party URLs and source identity live here.\nThese are references, not installed commands or local runtime dependencies.\n\n" + "\n".join(
        f'<a id="{key}"></a>\n\n## {key}\n\n[Original source]({url})\n' for key, url in sorted(catalog.items())
    )).encode()
    generated[".ai/library/THIRD-PARTY-NOTICES.md"] = (
        "# Third-party attribution\n\nThis file preserves source identity for licensing and provenance only.\n"
        "The active project uses its own workflow namespace.\n\n"
        "## Open GSD / GSD-Core\n\n"
        f"Source: [{SOURCE_REPOSITORY}]({SOURCE_REPOSITORY}/tree/{SOURCE_REVISION})\n\n"
        f"Pinned revision: `{SOURCE_REVISION}`.\n\n"
        "Copyright (c) 2026 Open GSD. Licensed under the MIT License; the complete\n"
        "copyright and permission notice is retained in [LICENSE](LICENSE).\n\n"
        "All 40 templates and 447 supporting files retain their full source content\n"
        "with enumerated namespace, reference, and local conflict adaptations.\n"
        "[PROVENANCE.json](PROVENANCE.json) records exact original hashes, source\n"
        "paths, and reversible edits. [SOURCES.md](SOURCES.md) resolves source links.\n"
        "\n## Earlier engineering-method adaptation\n\n"
        "The repository's earlier engineering skills also drew on Open GSD guidance\n"
        "at revision `a0270a79452f94360d7c4acda81038d51a4df7a1`. This is a separate\n"
        "historical source pin, not the complete-template import revision above.\n"
        "Source: [earlier method revision](https://github.com/open-gsd/gsd-core/tree/a0270a79452f94360d7c4acda81038d51a4df7a1).\n"
        "The MIT attribution above also applies to this adapted guidance.\n"
    ).encode()
    return generated


def template_changes(entries):
    lines = [
        "# Complete template adaptation log", "",
        f"Source: {SOURCE_REPOSITORY}, revision `{SOURCE_REVISION}`.", "",
        "Generated by `tools/import_templates.py`; append this section to the",
        "migration `changes.log`. Every template is listed, including unchanged",
        "bodies. No example, counterexample, section, or guidance is abridged.", "",
        "## Shared additive note", "",
        "Every imported Markdown template and Markdown supporting file receives",
        "the following separated local note after its complete upstream body.",
        "Non-Markdown files receive only reversible namespace/reference substitutions",
        "where needed, without an appended note; config.json remains byte-preserved.",
        "The note resolves",
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
        for label, edits in [("Markdown destination repairs", entry["markdown_substitutions"])] + [(f"Namespace substitutions, stage {number}", edits) for number, edits in enumerate(entry["namespace_stages"], 1)]:
            if edits:
                lines.extend([label + ":", "", "| Before | After | Occurrences |", "|---|---|---:|"])
                for edit in edits:
                    lines.append(f"| `{edit['original']}` | `{edit['replacement']}` | {edit['count']} |")
                lines.append("")
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
        "paths, resolve to the corresponding `.ai/templates/` or `.ai/library/` files.",
        "Each exact replacement, source offset, occurrence count, and original hash",
        "is in `.ai/library/PROVENANCE.json`. The same additive note is appended to",
        "supporting Markdown. Source CLI examples and specialized behavior are retained.", "",
        "Concrete runtime/code/documentation references resolve individually to",
        "verified pinned upstream source paths in `.ai/library/REFERENCES.json`.",
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
        "User-directed namespace changes remove source branding from active guidance:",
        "the library directory is `.ai/library`, agent files use role names, command",
        "definitions are directly under `commands/`, command examples use `/workflow:*`,",
        "and engine examples use `workflow-tools`. These are vocabulary changes, not",
        "runtime installation. Source-branded URLs resolve through `SOURCES.md` with",
        "stable anchors; actual URLs and MIT attribution remain in provenance files.",
        "Every namespace substitution is reversible, with original offsets in the",
        "manifest. All Markdown links to available imported methods are repaired;",
        "external source documents resolve through the source catalog, including",
        "their original fragments. No unavailable source documents are fabricated.", "",
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
            commands["/workflow:" + Path(source).stem] = destination
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
