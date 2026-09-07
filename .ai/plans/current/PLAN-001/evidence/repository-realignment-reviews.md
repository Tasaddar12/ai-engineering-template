# Repository realignment review evidence

Recorded: 2026-09-07. Base commit: `d52d3c2dbb1b525843351cc697817e0a5e90ee29`.

This evidence concerns the docs-first installable workflow kit and repository cleanup. It is not an isolation approval or an execution verdict for the future autonomous-engine task graph. Repository development evidence remains under `.ai`; the reusable product lives under `docs`.

## Implementation and acceptance

Corrective implementation was delegated to `/root/repository_realign_sol` using `gpt-5.6-sol` with `xhigh` reasoning. `/root/agent_behavior_guides_sol` wrote the reusable role guides with the same model and effort. The coordinator independently authored the five installation acceptance tests.

The installer copies `docs/agents`, `docs/templates`, and `docs/workflows` into a fresh `.ai` or `.claude`, seeds empty project records from `docs/defaults`, and includes independent helper tools and schemas. Acceptance checks cover both providers, the actual document payload, multiple plans with plan-local task IDs, execution outside the source checkout, preserved host files, repeat installation, conflicting assets, failed task mutation, and persistence through a Git checkout with Windows line-ending settings.

## Independent code review

- Reviewer invocation: `/root/bootstrap_code_review_astra`.
- Model and effort: `gpt-6-astra`, `xhigh`.
- Final verdict: **PASS**, with no unresolved code findings.
- Independent validation: **13 tests passed** in 14.881 seconds on Python 3.13.14. Both installed namespaces produced correct missing-dependency guidance. The reviewer also reran the original temporary-file overwrite reproduction and confirmed unrelated bytes were preserved.
- Code fingerprint: `165a5a094310ffbb41b98af2574f09b3d2b4ae2b23036669a3e75d33d314519a`.
- Fingerprint scope: 61 files under `src/`, `tests/`, and `schemas/`, plus `pyproject.toml`, `.gitignore`, and `.gitattributes`. Exclude generated caches. Hash sorted entries of relative path, NUL, lowercase file SHA-256, and newline. This fingerprint remained stable during the final review.

All four initial code findings were corrected and covered by focused regressions: partial record writes now roll back; atomic replacement uses exclusively created temporary files; shared state and decision references are resolved and validated; failed installations remove newly created empty directories so retry succeeds.

## Independent documentation review

Reviewer invocation: `/root/product_docs_review_astra`, using `gpt-6-astra` with `xhigh` reasoning. Final verdict: **PASS**, with all four initial findings resolved and no unresolved documentation defects. The repairs clarify first-run authority, supported lifecycle operations, manual profile setup, and workflow navigation. A follow-up also ensures manual task completion updates and checks narrative links without changing structural identity.

The final review verified 44 Markdown files and 40 installed-relative links, with no broken links or concurrent file changes. Documentation fingerprint: `9fb4aece5ba503e897d486d17d44a296ad2c6b4942d997a186f863ae3747fbfd`. Hash sorted UTF-8 lines containing POSIX relative path, space, lowercase file SHA-256, and newline. The coordinator made the final narrow narrative-link instruction repair; Astra independently verified it.

## Scope and remaining work

This release installs a manual workflow kit, creates plan/task records, and validates records. It does not implement autonomous execution or whole-plan completion and archival. Those future transitions must preserve references and approval provenance. The revised engine graph remains proposed until separately reviewed.

Source-record validation passed after the documentation repair: 26 schemas, 119 artifacts, one plan with 39 tasks, 280 unordered task pairs, three archive manifests, and 120 local links. Staged and unstaged whitespace checks passed. The proposed graph digest is `79f1137d5bfc5cb0a5148b4d0f3d67487d5a7ff43ab218ea00e04c3bad315883`; it has no isolation review approval.

Local integration and removal of the completed corrective worktree and temporary verification environment remain pending at this review checkpoint.
