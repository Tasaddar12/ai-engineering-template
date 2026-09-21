# Universal Anti-Patterns

Rules that apply to ALL workflows and agents. Individual workflows may add their
own specific anti-patterns.

---

## Context Budget Rules

1. **Never** read agent definition files (`agents/*.md`) — `subagent_type` loads
   them automatically. Reading them into the orchestrator wastes context on
   content already injected into the subagent's session.
2. **Never** inline large files into subagent prompts — tell agents to read the
   files from disk. Agents have their own context windows.
3. **Read depth scales with context window** — check `context_window` in
   `.planning/config.yaml`. Below 500000: read frontmatter, status fields or
   summaries only. At 500000 or above (1M-class model): full body reads are
   permitted when the content is needed for an inline decision.
4. **Delegate** heavy work to subagents — the orchestrator routes; it does not
   build, analyse, research, investigate or verify.
5. **Proactive pause warning**: if you have already consumed significant context
   (large file reads, several subagent results), tell the user: "Context budget
   is getting heavy. Consider checkpointing progress."

## File Reading Rules

6. **SUMMARY.md read depth scales with context window** — below 500000, read
   frontmatter only from prior phase summaries. At 500000 or above, full body
   reads are permitted for direct-dependency phases. Transitive dependencies
   (two or more phases back) stay frontmatter-only regardless.
7. **Never** read full PLAN.md files from other phases — only the current phase's.
8. **Do not** re-read full file contents when frontmatter is sufficient.
   Frontmatter carries status, key files and commits.

## Subagent Rules

9. **NEVER** use generic agent types (`general-purpose`, `Explore`, `Plan`, and
   the like) — always use the project's own agents by name: `researcher`,
   `phase-preparer`, `phase-checker`, `coder`, `verifier`, `code-reviewer`,
   `doc-writer`, `doc-verifier`, `integration-checker`, `codebase-mapper`,
   `debugger`. Those definitions carry project-aware prompts and workflow
   context; generic agents bypass all of it.
10. **Do not** re-litigate decisions already locked in CONTEXT.md (or the
    PROJECT.md context section) — locked decisions are respected unconditionally.

## Questioning Anti-Patterns

11. **Do not** walk through checklists — asking items one by one from a list is
    the single worst questioning pattern. Use progressive depth: start broad,
    dig where it is interesting.
12. **Do not** use corporate speak — avoid "stakeholder alignment", "synergize",
    "deliverables". Use plain language.
13. **Do not** apply premature constraints — do not narrow the solution space
    before understanding the problem. Ask about the problem first, then constrain.

## State Management Anti-Patterns

14. **No direct Write/Edit to STATE.md or ROADMAP.md for mutations.** Always go
    through `phase_run query` (`state.*`, `roadmap.*`, `phase.*`). Direct Write
    bypasses the safe update path, the planning lock and frontmatter derivation,
    and is unsafe when more than one session is open. Exception: first-time
    creation of STATE.md from its template.

## Behavioral Rules

15. **Do not** create artifacts the user did not approve — confirm before writing
    new planning documents.
16. **Do not** modify files outside the workflow's stated scope — check the plan's
    declared files.
17. **Do not** suggest several next actions without a clear priority — one primary
    suggestion, alternatives listed as secondary.
18. **Do not** use `git add .` or `git add -A` — stage specific files only.
19. **Do not** put secrets (API keys, passwords, tokens) into planning documents
    or commits.

## Error Recovery Rules

20. **Git lock detection**: if a git operation fails with "Unable to create lock
    file", check for a stale `.git/index.lock` and advise the user to remove it.
    Do not remove it automatically.
21. **Config fallback awareness**: configuration loading falls back to defaults.
    If a workflow depends on a configured value, check whether it is actually set
    and warn the user rather than proceeding on a default silently.
22. **Partial state recovery**: if STATE.md references a phase directory that does
    not exist, do not proceed silently. Warn the user and suggest diagnosing the
    mismatch.

## Runtime Rules

23. **Prefer `phase_run query`** for every planning-record read and write. The
    runtime owns numbering, slugs, directory layout, the roadmap checklist, the
    progress table and STATE.md frontmatter derivation. A workflow that edits
    those by hand will drift from them.
24. **Plan files MUST follow the `{padded_phase}-{NN}-PLAN.md` pattern**
    (for example `01-01-PLAN.md`). Never `PLAN-01.md` or `plan-01.md` — plan
    detection depends on this exact spelling.
25. **Do not start the next plan before writing the current plan's SUMMARY.md** —
    downstream plans and the milestone record read it.
