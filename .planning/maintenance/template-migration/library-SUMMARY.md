---
status: complete
acceptance: []
documentation:
  - .ai/library/README.md
  - .ai/library/TEMPLATE-CHANGES.md
  - .ai/library/THIRD-PARTY-NOTICES.md
---

# Neutral authoring library and complete reference closure

## Changes

| Request | Delivered |
|---|---|
| Use project-owned names | `.ai/library/`, neutral agent role filenames, direct `commands/` definitions, `/workflow:*` examples, `workflow-tools` engine examples, `workflow_state_version` field. |
| Keep the complete source guidance | All 40 templates and 447 supporting files remain; reversible namespace/reference edits reconstruct all 487 exact source hashes. |
| Keep source identity out of working guidance | Source names, original URLs, and attribution are isolated in provenance files, the source catalog, and third-party notices. Active imported bodies and the library README contain no source brand. |
| Retain legal/source attribution | Complete original MIT LICENSE, current full-import pin, and separate older engineering-method pin recorded in THIRD-PARTY-NOTICES.md. |
| Repair real navigation | Six previously broken source-document links now reach stable local SOURCES.md anchors containing exact pinned URLs and original fragments. Local method links resolve to real imported files. |
| Preserve metadata references | Workflow section-manifest JSON read targets point to real local step files; nested fixture-directory and host-install reference variants map correctly. |
| Explain every adaptation | Regenerated TEMPLATE-CHANGES.md lists every template's conflict, reference, Markdown-link, and namespace substitutions. PROVENANCE.json retains exact offsets for reversal. |
| Use neutral tooling names | `tools/import_templates.py`, `tests/test_template_library.py`, and scoped LF attributes for `.ai/library/`. |

## Checks

Implementation revision: `9d88728`, after `baa22fb` and `aee38e6`.

| Check | Result |
|---|---|
| `python -m unittest discover -s tests -p test_template_library.py` | PASS, 10 tests. |
| `python tools/import_templates.py --source C:/Users/killi/AppData/Local/Temp/gsd-template-source-20260913 --check` | PASS, 493 generated files, zero differences. |

Checks cover full inventory, reversible original hashes, license retention,
real method paths, neutral active content, stale files, actual Markdown targets
and source-catalog anchors, workflow-step metadata targets, unmodified template
config.json, and truncation detection. Literal output placeholders and two
documented source examples are distinguished from real navigation links.

## Decisions and boundaries

- Source URLs are not mechanically renamed into nonexistent repositories. Working
  guidance links to local provenance anchors, which preserve actual pinned source
  URLs and fragments. Source-only documents are referenced accurately; no dummy
  files or recursive unrelated documentation import was introduced.
- The neutral engine/command vocabulary is descriptive source guidance. This work
  does not install the upstream Node runtime or register its command namespace.
  Active procedures and Python runtime remain the execution authority.
- Non-Markdown supporting metadata receives reversible path/namespace changes
  where required. The upstream template config.json remains byte-preserved.
- The root changes.log must replace its previous generated template section with
  the full current `.ai/library/TEMPLATE-CHANGES.md`, not retain both as current.
- Parent owns the three proposed workflow entry paths and corresponding active
  guide/command/role/runtime reconciliation. This worker did not broaden scope
  into a new runtime or implement the later workflow feature expansion.

## Integration commits

1. `baa22fb` — Adopt neutral authoring library namespace with reversible provenance.
2. `aee38e6` — Repair retained step metadata and source navigation after namespace migration.
3. `9d88728` — Resolve nested fixture directories and installed-path reference variants.
4. This summary commit records the completed component and integration boundary.
