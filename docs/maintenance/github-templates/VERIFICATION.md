---
phase: github-publication-template-maintenance
verified: 2026-11-06T15:06:23Z
status: passed
score: 8/8 must-haves verified
candidate: f12b8234d554d590d1802b989fdb72e496fbf27c
base: 97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_candidate: b0f7df95f3f96c9b7442f6ecca9b0072ea4fb9f2
  previous_score: 6/8
  gaps_closed:
    - V-01 malformed PR template cannot disable required-section validation.
    - V-02 local installs select project templates despite retained global assets.
  warnings_closed:
    - V-03 UAT guide names the correct source and installed paths.
  gaps_remaining: []
  regressions: []
human_verification: []
---

# GitHub publication template verification

The final frozen candidate passes this bounded independent verification: **31 repository tests, zero failures, zero skips**, independent YAML/content-preservation checks, the original failure probes, and configured static checks. Both initial runtime blockers and the local-guide warning are resolved with evidence. No remaining in-scope finding was identified.

This qualifies the source migration and tested installer/runtime behavior. It does not certify live GitHub rendering, full cross-platform CI, PR readiness, consumer adoption, or merge authority.

## Scope and evidence boundary

Original base: 97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46. Initial candidate with reproduced defects: b0f7df95f3f96c9b7442f6ecca9b0072ea4fb9f2. Final tested candidate: f12b8234d554d590d1802b989fdb72e496fbf27c.

Source checkout D:\Codex\2026-11-06\task-6\verify remained at that final revision with a clean tracked tree. Tests used Windows and Python 3.11.9 at D:\Codex\2026-10-16\task-7\python-runtime\python.exe. Independent YAML parsing used PyYAML 6.0.3; installer/runtime code remains standard-library only.

This report states the commands, revisions, observations and limits directly. Supporting raw output, exact argv/exit-code/duration JSON and probe scripts remain **local, uncommitted evidence** under D:\Codex\2026-11-06\task-6\verification-final-logs. Initial failures and report are retained under verification-logs, including VERIFICATION-initial.md. These local paths are not published evidence URLs and are not required to understand the findings below.

Independent commands ran in parallel processes with isolated disposable fixtures; all finished before judgment. No adopting-project identity or planning phase was seeded. No GitHub mutation, push, merge or change to PR #194 was performed by this verifier.

## Goal achievement

| # | Observable truth | Status | Direct evidence |
|---|---|---|---|
| 1 | Actual Git workflow and two old authoring files are removed. | VERIFIED | Candidate lacks engineer/references/git-workflow.md, engineer/templates/issue.md and engineer/templates/pull-request.md. The actual requested workflow location was a reference, not workflows/. |
| 2 | Five GitHub YAML forms preserve original issue bodies. | VERIFIED | Independent PyYAML parsing and comparison with original Git-content fenced blocks passed for Bug, Enhancement, Decision required, Security risk and UAT. |
| 3 | Supported GitHub PR template preserves original visible body. | VERIFIED | .github/pull_request_template.md visible Markdown equals the original fenced body, ignoring terminal whitespace. Authoring instructions remain HTML comments. |
| 4 | Clean installs export and use templates for both hosts/scopes. | VERIFIED | Actual installed Codex/Claude runtimes validate every form and PR body in four combinations. Local uses project .github; global uses namespace .github without writing home-root .github. |
| 5 | Shared local templates preserve customizations and ownership. | VERIFIED | Codex then Claude installation succeeds; customized form causes conflict and survives install. Installed bytes and manifest source paths match canonical source. |
| 6 | Structural/publication checks and repeat installs work. | VERIFIED | 19 format, 8 misc/publication, 3 GitHub-installer and 1 no-op tests pass, zero skips. No-op covers both hosts/scopes. |
| 7 | Malformed nonempty PR template cannot disable required sections. | VERIFIED | Original independent comment-only/incomplete-template probes now reject with invalid-pr-body; added tests cover optional-only headings and authoring-comment isolation. |
| 8 | Scope changes select correct templates despite retained copies. | VERIFIED | Original actual Codex global-to-local probe selects project .github. Real both-host global-to-local-to-global regression damages retired copies and validates the active schema. |

## Independent content and syntax observations

All five YAML documents independently parse with unique canonical names, supported name/description/body top-level structure, Markdown introduction, and a required report textarea with label, description and value. Every decoded default equals its original fenced issue body, ignoring terminal whitespace. Runtime extraction agrees with independent YAML decoding, and GitHub's added Report heading does not break structural validation.

Thus original headings, tables, UAT numbered steps and human-acceptance fields are preserved. PR visible Markdown likewise equals the original fenced body. Expected content comes from original Git history plus an independent parser, not runtime-generated expected values.

The guide no longer links to ../../engineer/templates/UAT.md. It explicitly names engineer/templates/UAT.md for source; .codex/engineer/templates/UAT.md and .claude/engineer/templates/UAT.md for installations; and the project root/local versus selected home/global context. Original UAT authoring instructions remain. No second publication-template copy was introduced outside .github.

No live GitHub issue form was rendered or submitted. Activation on the default branch is outside this draft-source verification.

## Exact repository checks and actual outcomes

PY denotes the exact executable above. All commands ran from the frozen verify checkout. Disposable Git fixture initialization required unsandboxed test execution. This final independent batch had no environment setup failure.

| Exact command | Actual outcome |
|---|---|
| PY -m unittest discover -s tests -p test_issue_format.py -v | 19 tests passed in 6.468 seconds; zero skips. |
| PY -m unittest discover -s tests -p test_misc_verbs.py -v | 8 tests passed in 17.855 seconds; zero skips. |
| PY -m unittest discover -s tests -p test_installer_runtime.py -k github -v | 3 tests passed in 137.446 seconds; zero skips. Covers real both-host scope roundtrips with poisoned retired templates, clean four-combination installation/runtime validation, and customization protection. |
| PY -m unittest discover -s tests -p test_installer_runtime.py -k clean_installs_both_hosts_and_scopes_are_noop_on_rerun -v | 1 test passed in 80.289 seconds; zero skips; four host/scope combinations and repeat-install no-op. |
| PY -I scripts/links.py | Passed: 0 broken targets. |
| PY -I scripts/check_markdown_python.py | Passed: 335 tracked Markdown files scanned; 0 findings. |
| PY -I scripts/verbs.py --fail-on-unknown | Passed: 324 registered verbs, 598 call sites, 0 unknown. |
| git diff --check 97a2f0dc03b739f4ba0ad89dc5f5298269d8cd46 HEAD | Passed: no whitespace errors. |

Additional independent probe commands and observed results:

| Exact command | Method and actual outcome |
|---|---|
| PY D:\Codex\2026-11-06\task-6\verification-final-logs\check_templates.py | PyYAML decoded all five forms; compared Report defaults with original base's fenced Markdown via git show; compared PR visible body; checked removed files; checked runtime/YAML agreement and repaired guide. All assertions passed. |
| PY D:\Codex\2026-11-06\task-6\verification-final-logs\check_pr_malformed.py | Supplied comment-only and incomplete nonempty canonical PR template input while validating arbitrary heading-free text. Both cases rejected with invalid-pr-body. Exit 0. |
| PY D:\Codex\2026-11-06\task-6\verification-final-logs\check_scope_transition.py | Actual pinned Codex global install then local install in the same disposable target both complete; manifest records local; installed runtime selects project .github despite retained global assets. Exit 0. |

The final probe wrappers reuse original scripts from verification-logs, replacing only the candidate pin where needed. These are the same original failure scenarios, not substitutes. Raw local logs corroborate these observations but are not claimed as published artifacts.

## Initial findings and resolution

| Finding at initial candidate | Initial deterministic observation | Final repair and evidence | Disposition |
|---|---|---|---|
| V-01 — BLOCKER: malformed PR schema disables requirements. | Comment-only template accepted arbitrary heading-free PR text. | delivery.validate_body rejects an empty parsed required-heading list. Original independent probe and added repository regressions pass. | Resolved at final revision. |
| V-02 — BLOCKER: local runtime consumes retained global templates. | Real global then local install recorded local scope but selected .codex/.github. | github_directory reads installed manifest scope; invalid scope fails. Original actual-install probe and both-host poisoned-copy roundtrip regression pass. | Resolved at final revision. |
| V-03 — WARNING: local guide assumes source layout. | Source-relative UAT link was absent in a local consumer layout. | Doc-writer replaced it with explicit source and both-host installed paths plus scope context; independent guide assertion passes. | Resolved at final revision. |

No override was applied, and no unresolved finding was downgraded. Initial failure provenance remains in local initial logs/report.

## Test quality and limits

Selected tests exercise real disposable installs and actual installed Python runtimes. Publication-safety tests intentionally simulate provider calls. No selected case was skipped or disabled. The scope regression poisons retained files before validation, so directory presence alone cannot conceal wrong source selection. Migration parity uses original source content and an independent parser.

The complete historical suite, Linux, live GitHub form rendering, real provider publication/integration and consumer adoption were not run under this bounded assignment. Draft CI skips platform validation. PR readiness, actual human acceptance and merge are not certified by this report.

No phase roadmap/CONTEXT records exist for this maintenance task; phase decision-coverage, fingerprint and roadmap requirement gates are not applicable. No artificial manual installer acceptance step is added. The requested PR review remains the coordinator's separate delivery action.
