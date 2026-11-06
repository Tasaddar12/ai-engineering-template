---
phase: github-publication-template-maintenance
verified: 2026-11-06T15:26:56Z
status: passed
score: 8/8 must-haves verified
candidate: c6f8db6a1f598e06ee63d8ffb52f1f26f0bd3b27
base: 97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46
behavior_unverified: 0
overrides_applied: 0
gaps: []
human_verification: []
---

# GitHub template verification

**Passed at c6f8db6a1f598e06ee63d8ffb52f1f26f0bd3b27: 34 selected repository tests, zero failures and zero skips.** Independent syntax, preservation, runtime-selection, installed-byte/hash and static checks also passed. No remaining in-scope finding was identified.

The verified scope is eight issue forms and **only three named PR templates**: enhancement, feature and fix. The default .github/pull_request_template.md is removed and is not recreated/exported. Earlier retained-default evidence is superseded by this report.

## Scope and direct evidence

| Requirement | Verified observation |
|---|---|
| Remove obsolete source files. | engineer/references/git-workflow.md, engineer/templates/issue.md, engineer/templates/pull-request.md and .github/pull_request_template.md are absent. |
| Preserve original issue templates and add the requested types. | Independent PyYAML parsing confirms eight supported form documents. Decoded Report defaults for the original Bug, Enhancement, Decision required, Security risk and UAT equal original base Git content, ignoring terminal whitespace. New docs_issue.yml, chore.yml and feature_request.yml have distinct names, expected sections and acceptance outcomes. All eight agree with runtime extraction and validate with GitHub's Report wrapper. |
| Provide three separate PR bodies. | .github/PULL_REQUEST_TEMPLATE contains exactly enhancement.md, feature.md and fix.md. Each retains the original PR heading/table structure, complete embedded authoring guidance and distinct Goal/Changes/Verification prompts. Visible typed bodies equal the preceding expanded-scope revision; default deletion did not rewrite them. |
| Install canonical assets for both hosts/scopes. | Four independent real installs passed: Codex local/global and Claude local/global. Each exports exactly 12 assets: eight issue forms, their guide and three PR bodies. Every installed byte matches an independently read pinned Git archive; source_path and SHA-256 ownership digest match. No default PR file or default export/manifest source exists. Local exports project .github; global exports namespace .github without home-root .github. |
| Validate selected PRs without a default file. | Actual installed runtimes validate all eight issues and all three selected PRs. Named selection, missing selection-file and invalid/path-like name regressions pass. Independent pr.open probes confirm --template enhancement/feature/fix reaches validation before push/provider mutation; omission remains compatible through enhancement validation. |
| Preserve installer behavior. | Shared Codex/Claude installation and customization-conflict protection pass. Repeat-install no-op passes for both hosts and both scopes. |
| Retain fixes for independently discovered defects. | Original malformed-PR probe rejects comment-only/incomplete schemas. Original real global-to-local probe chooses project templates. Both-host global-to-local-to-global regressions deliberately poison retained copies and still validate the active schema. Corrected UAT guide paths remain. |
| Keep documentation/static wiring valid. | Eight-form catalog, GitHub template query parameters, runtime --template instructions and no-default installation guidance checked. Source links, Markdown/Python, verb registry and whole-diff whitespace checks pass. |

Git archive on this Windows setup converts LF to configured CRLF. The independent installer probe compares exact archive bytes and separately confirms normalized archive content equals raw Git blobs; it does not mistake that configured conversion for content corruption. Runtime code remains Python standard-library only; PyYAML is a verifier dependency.

## Exact commands and outcomes

All commands ran from D:\Codex\2026-11-06\task-6\verify at the frozen candidate above. Its tracked tree was clean afterward. PY means D:\Codex\2026-10-16\task-7\python-runtime\python.exe, Python 3.11.9 on Windows. PyYAML was 6.0.3. Independent processes used isolated disposable fixtures and all completed before judgment. Unsandboxed execution was required for Git fixture creation; this batch had no setup failures.

| Exact command | Actual result |
|---|---|
| PY -m unittest discover -s tests -p test_issue_format.py -v | 22 tests passed in 8.507s; zero skips. |
| PY -m unittest discover -s tests -p test_misc_verbs.py -v | 8 tests passed in 20.684s; zero skips. |
| PY -m unittest discover -s tests -p test_installer_runtime.py -k github -v | 3 tests passed in 147.114s; zero skips. |
| PY -m unittest discover -s tests -p test_installer_runtime.py -k clean_installs_both_hosts_and_scopes_are_noop_on_rerun -v | 1 test passed in 84.432s; zero skips. |
| PY -I scripts/links.py | 0 broken targets. |
| PY -I scripts/check_markdown_python.py | 339 tracked Markdown files scanned; 0 findings. |
| PY -I scripts/verbs.py --fail-on-unknown | 324 registered verbs, 598 call sites; 0 unknown. |
| git diff --check 97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46 HEAD | Passed; no whitespace errors. |

Independent probes ran with the same PY executable. Each command below exited 0; their methods and outcomes are stated directly so this report does not depend on unpublished files.

| Exact command | Independent observation |
|---|---|
| PY D:\Codex\2026-11-06\task-6\verification-no-default-logs\check_templates.py | Independent YAML decoding and original-five parity passed; three added form shapes, three typed PR bodies/common original structure, complete guidance, default absence and selection documentation checked. |
| PY D:\Codex\2026-11-06\task-6\verification-no-default-logs\check_installer_hashes.py | 12 assets in each of four actual host/scope installs exactly match pinned archive bytes, canonical source paths and actual SHA-256 manifest digests; default absent from archive, files and manifest exports. |
| PY D:\Codex\2026-11-06\task-6\verification-no-default-logs\check_pr_forwarding.py | All three pr.open --template values reach the selected validator before any push/provider mutation; Git/provider operations were intercepted. |
| PY D:\Codex\2026-11-06\task-6\verification-no-default-logs\check_pr_malformed.py | Both original malformed-schema cases reject with invalid-pr-body, using the named-template helper without a default file. |
| PY D:\Codex\2026-11-06\task-6\verification-no-default-logs\check_scope_transition.py | Actual pinned global then local installation completes; manifest says local and installed runtime selects project .github despite retained global assets. |

## Evidence boundary and limits

The exact argv/revision/exit-code/duration JSON, scripts and raw output are **local, uncommitted supporting evidence** under D:\Codex\2026-11-06\task-6\verification-no-default-logs. Earlier batches remain in separate local directories. These are not published URLs; the commands and observations needed to assess this result are included above.

Tests use actual installed Python runtimes. Publication-safety/forwarding probes intentionally intercept provider calls. No live GitHub mutation, push, merge or change to PR #194 was performed by this verifier. No source changes were made.

The full historical suite, Linux execution, live GitHub form rendering, live publication/provider integration and consumer adoption were not run. Draft CI is configured to skip platform validation. This report certifies neither PR readiness nor merge authority; the user's requested draft PR review remains the coordinator's delivery action. No phase identity or artificial manual installer acceptance step was added for this template-maintenance assignment.
