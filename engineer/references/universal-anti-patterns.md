# Universal Anti-Patterns

Rules that apply to ALL workflows and agents. Individual workflows may have additional specific anti-patterns.

---

## Context Budget Rules

1. Read your assigned role and required inputs. The coordinator reads the dispatch contract before assigning work; do not assume host auto-loading satisfies required reading.
2. **Never** inline large files into subagent prompts -- tell agents to read files from disk instead. Agents have their own context windows.
3. Read `context_window` from `.planning/config.yaml` and use bounded evidence selection. Complete templates and assigned role inputs remain mandatory.
4. **Delegate** heavy work to subagents -- the orchestrator routes, it does not build, analyze, research, investigate, or verify.
5. **Proactive pause warning**: If you have already consumed significant context (large file reads, multiple subagent results), warn the user: "Context budget is getting heavy. Consider checkpointing progress."

## File Reading Rules

6. **SUMMARY.md read depth scales with context window** -- at context_window < 500000: read frontmatter only from prior phase SUMMARYs. At >= 500000: full body reads permitted for direct-dependency phases. Transitive dependencies (2+ phases back) remain frontmatter-only regardless.
7. **Never** read full PLAN.md files from other phases -- only current phase plans.
8. **Never** read `.planning/logs/` files -- only the health workflow reads these.
9. **Do not** re-read full file contents when frontmatter is sufficient -- frontmatter contains status, key_files, commits, and provides fields. Exception: at >= 500000, re-reading full body is acceptable when semantic content is needed.

## Subagent Rules

10. Dispatch exact project roles from `agents/AGENT.md`, with model and effort resolved inline; never substitute generic agents.
11. Preserve approved CONTEXT scope and PROJECT Key Decisions. Resolve evidence-based conflicts through the coordinator; do not relitigate settled choices.

## Questioning Anti-Patterns

Reference: `engineer/references/questioning.md` for the full anti-pattern list.

12. **Do not** walk through checklists -- checklist walking (asking items one by one from a list) is the #1 anti-pattern. Instead, use progressive depth: start broad, dig where interesting.
13. **Do not** use corporate speak -- avoid jargon like "stakeholder alignment", "synergize", "deliverables". Use plain language.
14. **Do not** apply premature constraints -- don't narrow the solution space before understanding the problem. Ask about the problem first, then constrain.

## State Management Anti-Patterns

15. Use `engineer_run query` for all runtime-owned STATE/PROJECT Key Decisions/ROADMAP/REQUIREMENTS/todo/quick/milestone changes. Narrative is authored only in its owner; initialization does not authorize arbitrary direct mutation.

## Behavioral Rules

16. **Do not** create artifacts the user did not approve -- always confirm before writing new planning documents.
17. **Do not** modify files outside the workflow's stated scope -- check the plan's files_modified list.
18. **Do not** suggest multiple next actions without clear priority -- one primary suggestion, alternatives listed secondary.
19. **Do not** use `git add .` or `git add -A` -- stage specific files only.
20. **Do not** include sensitive information (API keys, passwords, tokens) in planning documents or commits.

## Error Recovery Rules

21. **Git lock detection**: Before any git operation, if it fails with "Unable to create lock file", check for stale `.git/index.lock` and advise the user to remove it (do not remove automatically).
22. Config loading validates YAML. Use documented defaults or explicit `config-get KEY --default VALUE`; a malformed file or missing unknown key is an error, never silent success.
23. If STATE points to absent artifacts, report the exact mismatch and use reviewed runtime repair; do not invent a replacement phase or hand-edit shared structures.

## GSD-Specific Rules

24. Do not infer approval from unattended or automatic mode. Read supported YAML configuration, preserve recorded authority and use checkpoint rules for missing choices.
25. Use `engineer_run query VERB ARGS` for supported runtime operations. `config-get` fails on a missing key unless an explicit `--default VALUE` is supplied. Invalid YAML fails; never report a silent successful fallback.
26. PLAN filenames use `{padded_phase}-{NN}-PLAN.md`, with quoted plan identifiers and complete acceptance/documentation/checks argv/issue_refs contracts.
27. Commit the owned completed slice and required SUMMARY before reporting completion. Preserve pending tests and human acceptance; the coordinator owns shared records, integration and publication.

## iOS / Apple Platform Rules

28. **NEVER use `Package.swift` + `.executableTarget` (or `.target`) as the primary build system for iOS apps.** SPM executable targets produce macOS CLI binaries, not iOS `.app` bundles. They cannot be installed on iOS devices or submitted to the App Store. Use XcodeGen (`project.yml` + `xcodegen generate`) to create a proper `.xcodeproj`. See `engineer/references/ios-scaffold.md` for the full pattern.
29. **Verify SwiftUI API availability before use.** Many SwiftUI APIs require a specific minimum iOS version (e.g., `NavigationSplitView` is iOS 16+, `List(selection:)` with multi-select and `@Observable` require iOS 17). If a plan uses an API that exceeds the declared `IPHONEOS_DEPLOYMENT_TARGET`, raise the deployment target or add `#available` guards.
