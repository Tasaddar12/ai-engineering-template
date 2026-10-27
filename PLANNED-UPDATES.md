# PLANNED-UPDATES

Overhaul plan: make the downloaded GSD-core copy (`agents/`, `commands/`,
`engineer/`) the canonical workflow tree, delete what this project does not
use, re-stitch the improvements that live in `.ai/` and `.planning/`, add the
selected upstream features, and replace upstream's Node tooling with a Python
runtime driven from bash.

- **Baseline commit:** `9443672` (branch `manual-override`). Every line number in
  this document refers to that commit. Read an anchor with
  `git show 9443672:<path> | sed -n '<start>,<end>p'`.
- **Upstream copy:** open-gsd/gsd-core, downloaded into `1eb6c97`. The exact
  upstream revision is not recorded (highest issue reference seen: `#5640`); see
  [D-08](#9-decisions).
- **Original local adaptation:** `.ai/` and `.planning/`, adapted from gsd-core
  `c0b2a05` (templates, workflows, references) and `4713ffba` (agents). The full
  `c0b2a05` snapshot is in Git at `2969562:.ai/gsd/`.

### Review scope override — PR #127, review 5669934629

The [human review](https://github.com/Tasaddar12/ai-engineering-template/pull/127#pullrequestreview-5669934629) overrides conflicting deletion/reconciliation rows below. Retain these complete copied GSD methods:

- `commands/extract-learnings.md`
- `engineer/workflows/execute-phase/steps/codebase-drift-gate.md`
- `engineer/workflows/new-milestone/steps/project-md-milestone-write.md`
- `engineer/workflows/quick/steps/discussion-phase.md`
- `engineer/workflows/quick/steps/research-phase.md`
- `engineer/workflows/diagnose-issues.md`
- `engineer/workflows/extract-learnings.md`
- `engineer/workflows/graduation.md`
- `engineer/workflows/list-seeds.md`
- `engineer/workflows/note.md`
- `engineer/workflows/scan.md`
- `engineer/workflows/session-report.md`
- `engineer/workflows/plant-seed.md`

Copy the complete body of `engineer/workflows/discuss-phase/modes/analyze.md` into `engineer/workflows/discuss-phase.md`; remove only the optional-mode wrapper and the no-analysis fallback. This is the native discussion method and requires no flag.

Quick tasks ask clarifying questions by default, then research as needed to establish scope and support the plan. Retain the full copied discussion and research steps. Runtime implementation and tests remain deferred by the user.

## Contents

1. [Goals and end state](#1-goals-and-end-state)
2. [Ground rules](#2-ground-rules)
3. [Target layout and naming](#3-target-layout-and-naming)
4. [Planned features and improvements](#4-planned-features-and-improvements)
5. [Work phases](#5-work-phases)
6. [Automation scripts to write](#6-automation-scripts-to-write)
7. [Working a row with AI assistance](#7-working-a-row-with-ai-assistance)
8. [Known local defects not to carry over](#8-known-local-defects-not-to-carry-over)
9. [Decisions](#9-decisions)
10. [Delete list](#10-delete-list)
11. [Reconciliation: agents](#11-reconciliation-agents)
12. [Reconciliation: commands and workflows](#12-reconciliation-commands-and-workflows)
13. [Reconciliation: references, templates, rules and config](#13-reconciliation-references-templates-rules-and-config)
14. [Reconciliation: runtime, verbs, hooks, tests](#14-reconciliation-runtime-verbs-hooks-tests)

### Row index

| Prefix | Rows | Section | Phase |
|---|---|---|---|
| `R-AG` | 355 | 11 | 4 |
| `R-WF` | 824 | 12 | 5, 8 |
| `R-TP` | 53 | 13 | 6 |
| `R-RF` | 105 | 13 | 6 |
| `R-RL` | 29 | 13 | 6 |
| `R-RT` | 85 | 14 | 2 |
| `V` | 154 | 14 | 2, 7 |
| `C` | 43 | 14 | 2 |

---

## 1. Goals and end state

| Goal | End state you can check |
|---|---|
| One workflow tree | `.ai/` is gone. `agents/`, `commands/`, `engineer/`, `hooks/`, `bin/`, `skills/` hold everything. `.planning/` holds only project records. |
| No Node | `grep -rnE "gsd-tools\|\.cjs\|npx \|node (-e\|-p\|-c\|\")" agents commands engineer hooks bin skills` returns nothing. The kept upstream files contain about 97 inline `node -e` JSON helpers and two `.cjs` probe scripts; rows V-150 to V-152 replace them with `--pick` or Python. |
| One runtime command | Every workflow calls `engineer_run query <verb>`. `engineer_run` is a bash shim that runs `engineer/bin/engineer.py` with Python 3. |
| No dangling upstream plumbing | `grep -rn "gsd_run\|gsd-core\|/gsd:" agents commands engineer` returns nothing. |
| Our behavior preserved | The unattended execute → verify → ship chain, mandatory worktree isolation, phase authority, receipts, frozen-revision verification, issue/PR automation and exact-approval cleanup all work as on `main`. `python -m unittest discover -s tests` passes. |
| New features working | `/secure-phase`, `/validate-phase`, `/add-tests`, `/audit-uat`, `/audit-fix`, `/spec-phase`, `/code-review --fix`, `/ui-phase`, `/ui-review`, `/fast`, `/quick-batch` run on the Python runtime with this project's rules. |
| Traceable | Every commit names the row IDs it completes (`Rows: R-AG-01, R-AG-02`). `scripts/progress.py` reports what is left. |

## 2. Ground rules

- Work in `.worktrees/<name>` branched from `origin/manual-override`. Never edit the main checkout.
- One work phase (section 5) per branch and pull request. Open the PR as a draft on the first push. Never merge; the user merges.
- Process a file's rows **bottom-up** (highest GSD line number first) so the remaining line numbers stay valid. When a file has already been edited, find the anchor text with `git show 9443672:<path>` and locate it by content.
- Copy local text **from the cited line range**, then apply the renames in [3.2](#32-mechanical-renames) to the copied text.
- Do not carry anything listed in [section 8](#8-known-local-defects-not-to-carry-over).
- Python 3.11+, standard library only. Run repository scripts with `python -I`. Shell glue is POSIX `sh`/bash. No Node, npm or npx.
- Agent-facing text (rules, workflows, commands, agents, references, hook messages): write direct imperatives with exact commands. Keep rationale in commit messages and in this document.
- After each phase, run its `check` block (section 5) with `python -I scripts/check.py --phase <N>`. A phase is done when every check passes.

## 3. Target layout and naming

### 3.1 Layout

| Path | Holds | Comes from |
|---|---|---|
| `agents/<role>.md` | Agent role definitions | GSD `agents/gsd-<role>.md` + `.ai/agents/*.md` |
| `agents/AGENT.md` | Agent catalog: roles, spawn rules, model/effort policy | `.ai/agents/README.md` |
| `commands/<name>.md` | Slash-command entry points | GSD `commands/` + `.ai/commands/` |
| `commands/COMMAND.md` | Command catalog | `.ai/commands/README.md` |
| `engineer/workflows/<name>.md` (+ `<name>/steps/`) | Workflow procedures | GSD `engineer/workflows/` + `.ai/workflows/` |
| `engineer/workflows/WORKFLOW.md` | Workflow index and shared launcher rules | `.ai/guides/PHASE-WORKFLOW.md` (corrected) |
| `engineer/references/` | Methods and shared rules | GSD `engineer/references/` + `.ai/references/` + `.ai/references/methods/` |
| `engineer/references/REFERENCE.md` | Reference index | `.ai/references/methods/README.md` |
| `engineer/templates/` | Artifact templates | GSD `engineer/templates/` + `.ai/templates/` |
| `engineer/templates/TEMPLATE.md` | Template catalog and artifact registry | `.ai/templates/README.md` + GSD `engineer/templates/README.md` |
| `engineer/RULES.md`, `engineer/truth-map.md` | Project rules and fact ownership | `.ai/RULES.md`, `.ai/truth-map.md` |
| `engineer/rules/README.md` | Modular project rule catalog | `.ai/rules/README.md` |
| `engineer/references/template-contract.md` | Runtime-owned sections and record contract | `.ai/runtime/TEMPLATE-CONTRACT.md` |
| `docs/` | Human guides (phase workflow, requests, features, artifacts) | `.ai/guides/` |
| `THIRD-PARTY-NOTICES.md` (repository root) | Provenance and upstream pin | `.ai/THIRD-PARTY-NOTICES.md` |
| `engineer/bin/engineer_run` | Bash shim: finds Python, runs `engineer.py` | `.ai/bin/phase_run`, `.ai/workflows/_runtime.snippet.sh` |
| `engineer/bin/engineer.py`, `engineer/bin/lib/` | Python runtime | `.ai/runtime/phase.py`, `.ai/runtime/lib/` |
| `hooks/` | Host hooks; `hooks/worktree-path-guard.py` is the Python port of `worktree-guard.sh` (warn only) | `.ai/hooks/` |
| `scripts/cleanup.py` | Exact-approval cleanup CLI | `.ai/hooks/cleanup.py` |
| `bin/install.py`, `bin/update.py`, `bin/migrate.py` | Install, pinned update, migration | `.ai/install.py`, `.ai/update.py` + `.ai/install_update.py`, `.ai/install_migration.py` |
| `skills/<name>/SKILL.md` | Skill mirror of commands | `.agents/skills/` |
| `scripts/` | Overhaul tooling (section 6) | New |
| `docs/INVENTORY.md` | Generated inventory of every workflow file | `scripts/inventory.py` |
| `.planning/` | Project records only (PROJECT, STATE, ROADMAP, REQUIREMENTS, config.yaml, phases, quick, todos) | Unchanged |

### 3.2 Mechanical renames

Apply with `scripts/rename.py` (section 6). Never hand-apply these across many files.

| Find | Replace | Scope |
|---|---|---|
| `gsd_run query <verb>` / `gsd_run <cmd>` | `engineer_run query <verb>` / `engineer_run <cmd>` | All kept files |
| `gsd-tools query` / `gsd-tools.cjs` launcher blocks | The launcher in `engineer/workflows/_runtime-launcher.snippet.sh` | Workflows and commands |
| `~/.claude/gsd-core/references/` | `engineer/references/` | All kept files |
| `~/.claude/gsd-core/templates/` | `engineer/templates/` | All kept files |
| `~/.claude/gsd-core/workflows/` | `engineer/workflows/` | All kept files |
| `gsd-core/workflows/` (in `section-manifest.json`-style reads) | `engineer/workflows/` | All kept files |
| `/gsd:<name>` and `name: gsd:<name>` | `/<name>` and `name: <name>` | Commands, workflows, templates |
| `gsd-<role>` (agent names) | `<role>` | All kept files |
| `.ai/references/methods/<x>` | `engineer/references/<x>` | Text copied from `.ai/` |
| `.ai/references/<x>`, `.ai/templates/<x>`, `.ai/workflows/<x>` | `engineer/references/<x>`, `engineer/templates/<x>`, `engineer/workflows/<x>` | Text copied from `.ai/` |
| `phase_run query` | `engineer_run query` | Text copied from `.ai/` |

### 3.3 Role names

Upstream role names without the `gsd-` prefix (matches the existing `agents/executor.md`). Local role names become aliases in `agents/AGENT.md` only.

| Final file | Upstream source | Local source | Kind |
|---|---|---|---|
| `agents/executor.md` | `gsd-executor` (already redrafted) | `.ai/agents/coder.md` | Worker |
| `agents/planner.md` | `gsd-planner` | `.ai/agents/phase-preparer.md` | Worker |
| `agents/plan-checker.md` | `gsd-plan-checker` | `.ai/agents/phase-checker.md` | Read-only |
| `agents/phase-researcher.md` | `gsd-phase-researcher` | `.ai/agents/researcher.md` | Worker |
| `agents/verifier.md` | `gsd-verifier` | `.ai/agents/verifier.md` | Read-only |
| `agents/code-reviewer.md` | `gsd-code-reviewer` | `.ai/agents/code-reviewer.md` | Read-only |
| `agents/debugger.md` | `gsd-debugger` | `.ai/agents/debugger.md` | Read-only unless assigned |
| `agents/doc-writer.md` | `gsd-doc-writer` | `.ai/agents/doc-writer.md` | Worker |
| `agents/doc-verifier.md` | `gsd-doc-verifier` | `.ai/agents/doc-verifier.md` | Read-only |
| `agents/integration-checker.md` | `gsd-integration-checker` | `.ai/agents/integration-checker.md` | Read-only |
| `agents/codebase-mapper.md` | `gsd-codebase-mapper` | `.ai/agents/codebase-mapper.md` | Worker |
| `agents/coordinator.md` | none | `.ai/agents/coordinator.md` | Orchestrator |
| `agents/scout.md` | none | `.ai/agents/scout.md` | Read-only leaf |
| `agents/targeted-fixer.md` | none | `.ai/agents/targeted-fixer.md` | Worker (cheap) |
| `agents/security-auditor.md` | `gsd-security-auditor` | none | Read-only |
| `agents/nyquist-auditor.md` | `gsd-nyquist-auditor` | none | Worker (writes tests) |
| `agents/pattern-mapper.md` | `gsd-pattern-mapper` | none | Read-only |
| `agents/code-fixer.md` | `gsd-code-fixer` | none | Source only; dispatches `targeted-fixer` |
| `agents/ui-researcher.md` | `gsd-ui-researcher` | none | Worker (writes UI-SPEC) |
| `agents/ui-checker.md` | `gsd-ui-checker` | none | Read-only |
| `agents/ui-auditor.md` | `gsd-ui-auditor` | none | Read-only |
| `agents/dom-verifier.md` | `gsd-dom-verifier` | none | Read-only (browser MCP) |

## 4. Planned features and improvements

Each row says what changes, why, and where you feel the benefit. "Source" points to the lines to bring over; the row IDs in sections 11 to 14 carry the exact ranges.

### 4.1 Carried over from `.ai/` (our improvements)

| ID | Feature | Why | Where the benefit is felt | Source | Phase |
|---|---|---|---|---|---|
| F-01 | Python runtime `engineer_run` replaces Node `gsd-tools.cjs` | One interpreter on every host, Windows-safe, unit-testable, one verb surface instead of a 3 KB launcher line per workflow | Every workflow step; installs need only Python 3 | `.ai/runtime/`, `.ai/bin/phase_run` | 2 |
| F-02 | Runtime-owned planning records + integrity snapshot around every verb | Hand edits drift; the runtime detects drift as it happens | STATE, ROADMAP, REQUIREMENTS, PROJECT stay consistent without manual repair | `.ai/runtime/phase.py:88-101`, `lib/planning_integrity.py` | 2 |
| F-03 | Unattended execute → verify → ship chain | Upstream stops at every hand-off and asks you to type the next command | A phase runs from execution to an open PR in one session; you answer only the merge question | `.ai/workflows/execute-phase.md:14-22,214-223,795-799`, `verify-work.md:640-645`, `ship.md:405-469` | 5 |
| F-04 | Mandatory worktree isolation, wave merge with deletion guard | Shared trees interleave commits; undeclared deletions slip through | Parallel coders never collide; every plan is attributable and revertable | `lib/worktrees.py:150-163,424-430,551-572`, `execute-phase.md:272-290` | 2, 5 |
| F-05 | Verification receipts and parallel independent checks | Upstream reruns every test command every time | Faster verify/ship; unchanged inputs reuse a passing receipt | `lib/verification_checks.py:173-200,261-308` | 2 |
| F-06 | Frozen-revision read-only verification batch | Evidence from different revisions cannot be combined safely | One verdict tied to one SHA; checks, verifier, integration and doc checks run concurrently | `verify-work.md:195-197,357-371,585-626` | 5 |
| F-07 | Measured context handoff (percent or token ceiling, both hosts) | Upstream guesses context use; Codex had no monitor | Subagents hand off before they degrade; the orchestrator never stops | `lib/handoff.py:48-66`, `.ai/hooks/context-handoff.sh` | 2 |
| F-08 | Codebase-map freshness from Git history | Recorded SHAs break after squash merges | Planning starts from current maps; stale maps rebuild automatically | `lib/codebase.py:72-80`, `plan-phase.md:219-224` | 2, 5 |
| F-09 | Planning integrity commit hook, warn-only `planning.validate`, closed STATE sections | Broken records were found only by reading them | Bad PLAN/CONTEXT/SUMMARY frontmatter is blocked at commit; STATE never grows dead sections | `.ai/hooks/planning-integrity.*`, `lib/validate.py`, `.ai/runtime/TEMPLATE-CONTRACT.md:376-394` | 2, 6 |
| F-10 | GitHub delivery: draft PR per wave, check waits, issue-link audit, merge only on instruction | Upstream opens a PR at the end and leaves CI to you | Reviewers see progress per wave; CI repairs run automatically; merges stay your call | `lib/delivery.py:112-183,280-320`, `lib/phase_issues.py:338-363`, `ship.md` | 2, 5 |
| F-11 | Issue publication through preview token and readback | Ad-hoc `gh issue create` publishes unchecked text | Every published issue is validated and confirmed | `lib/todo_issues.py:199-261`, `lib/issue_format.py`, `.ai/templates/issue.md` | 2, 5 |
| F-12 | Exact-approval cleanup with per-deletion revalidation | A yes/no prompt can delete state that changed after the preview | Cleanup never deletes a branch or worktree that changed since you approved | `lib/cleanup.py:500-610`, `.ai/workflows/cleanup.md:25-90` | 2, 5 |
| F-13 | Per-role model and effort, cheap scouts and targeted-fixer | One model per workflow overspends on extraction and small fixes | Lower cost per phase; expensive roles stop doing bulk reading | `lib/models.py:78-123`, `.ai/agents/scout.md`, `targeted-fixer.md`, `.ai/references/scout-dispatch.md` | 2, 4 |
| F-14 | Phase authority and discussion gates | Upstream can auto-advance into implementation | Nothing is implemented until you say so; every phase has a recorded discussion | `.ai/RULES.md:77-119`, `.ai/templates/context.md:7-11,35` | 4, 5, 6 |
| F-15 | "Issues found while working" routing (no stops, no todos) | Runs stopped to ask about every finding | Runs finish; open items appear once in the closing report | `.ai/RULES.md:244-271` | 5, 6 |
| F-16 | Coordinator-owned shared writes, SUMMARY `status` handoff | Workers in one wave collided on shared records | Clean integration; a missing or blocked SUMMARY is detected automatically | `.ai/references/worker-handoff.md:28-32`, `.ai/agents/coder.md:43,732-760` | 4 |
| F-17 | Stronger templates: PLAN/SUMMARY `acceptance`, `documentation`, `checks` (argv), `issue_refs`, threat model, Deliverable Coverage, UAT authoring contract, VALIDATION 2-in-3 | Upstream fields were unchecked or contradictory | Plans and summaries are machine-validated; UAT scripts are runnable by a person | `.ai/templates/phase-prompt.md:27-38`, `summary.md:57-71,113-177`, `UAT.md`, `VALIDATION.md:72` | 6 |
| F-18 | Documentation coverage contract | Doc updates were optional | Required docs block phase completion until verified | `.ai/references/documentation.md:23-26` | 6 |
| F-19 | Dual-host install and pinned, reviewed update | `npx …@latest` changes behavior without review | Reproducible installs on Claude Code and Codex; updates are dry-run diffs | `.ai/install.py`, `.ai/update.py:67-100` | 2 |

### 4.2 New from upstream (selected features)

| ID | Feature | Why | Where the benefit is felt | Upstream files kept | Local conventions to apply | Phase |
|---|---|---|---|---|---|---|
| F-20 | Security audit after implementation (`/secure-phase`, `security-auditor`) | Local checks threats only at plan time (Dimension 7d) and in code review | Every PLAN threat mitigation is confirmed in code before ship; ASVS level is configurable | `commands/secure-phase.md`, `engineer/workflows/secure-phase.md`, `agents/gsd-security-auditor.md`, `engineer/templates/SECURITY.md` | Read-only auditor returns a report; coordinator writes `NN-SECURITY.md`; runs inside the verify-work frozen batch; open threats follow threat-issue reconciliation | 8a |
| F-21 | Requirement-level test gap filling (`/validate-phase`, `nyquist-auditor`) | VALIDATION.md and the Nyquist method exist locally but nothing writes the missing tests | Each requirement gets an automated check; sampling gaps close before ship | `commands/validate-phase.md`, `engineer/workflows/validate-phase.md`, `agents/gsd-nyquist-auditor.md` | Worker in `isolation="worktree"`, commits SUMMARY with `status`; added to the write-capable list in the worktree guard | 8b |
| F-22 | Test generation from UAT and SUMMARY (`/add-tests`) | Manual UAT findings rarely become tests | Accepted behavior is locked in by tests | `commands/add-tests.md`, `engineer/workflows/add-tests.md` | Same worker rules as F-21 | 8b |
| F-23 | Regression gate | Later phases can silently break earlier ones | Prior phases' tests run before a wave is accepted | `engineer/workflows/execute-phase/steps/regression-gate.md`, `regression-gate-run.md` | Runs through `verification.run-checks` receipts | 8b |
| F-24 | TDD applicability and machine-checked RED evidence | Local TDD guidance has no per-format RED check | A test proven to fail before the fix, per report format; RED→GREEN ordered by commit ancestry | `execute-phase/steps/tdd-applicability-resolution.md`, `engineer/references/tdd.md`, `execute-mvp-tdd.md` | New verbs in the runtime (section 14) | 8b |
| F-25 | UAT audit and audit→fix pipeline (`/audit-uat`, `/audit-fix`) | Open UAT items across phases are not tracked together | One view of unaccepted behavior; fixes routed through bounded correction | `commands/audit-uat.md`, `audit-fix.md`, matching workflows | Fixes dispatch `targeted-fixer`; findings follow issue routing | 8b |
| F-26 | Spec completeness probes (`/spec-phase`, edge, prohibition, specless fallback) | Specs miss boundary and must-NOT cases, so tests miss them | Test cases cover edges and prohibitions; probe fixtures make the probes testable | `commands/spec-phase.md`, `engineer/workflows/spec-phase.md`, `engineer/references/edge-probe.md`, `prohibition-probe.md`, `specless-probe-fallback.md`, both `*-probe-fixtures/` | Output feeds PLAN `acceptance` and VALIDATION | 8b |
| F-27 | Pattern mapping before planning (`pattern-mapper`) | Phase-checker Dimension 12 reads PATTERNS.md, which nothing produces | New code follows existing house patterns; Dimension 12 stops skipping | `agents/gsd-pattern-mapper.md`, plan-phase §7.8 | Read-only; coordinator writes `NN-PATTERNS.md` | 8c |
| F-28 | Code review with fixes (`/code-review --fix`) | Local fixes one diagnosed defect at a time | All review findings fixed in one run, each as its own commit | `commands/code-review.md`, `engineer/workflows/code-review.md`, `code-review-fix.md`, `code-review/steps/dispatch-fix.md`, `agents/gsd-code-fixer.md` (source only) | `--fix` dispatches `targeted-fixer` once per finding via bounded correction dispatch; coordinator owns worktrees | 8d |
| F-29 | UI design contract and audit (`/ui-phase`, `/ui-review`, `dom-verifier`) | No UI track locally | UI work is specified before planning and audited after build; acceptance checked in a live browser | `commands/ui-phase.md`, `ui-review.md`, matching workflows, 4 UI agents, `UI-SPEC.md`, `ui-consideration-probe.md`, `verify-work/steps/automated-ui-verification.md` | ui-phase runs between discuss and plan; audits run in verify-work's batch; no new stop points | 8e |
| F-30 | Fast lane (`/fast`, `/quick-batch`, `--wave N`) | Trivial edits pay the full quick-task cost | Tiny fixes run inline; independent quick tasks run in parallel worktrees | `commands/fast.md`, `quick-batch.md`, matching workflows and `quick-batch/steps/`, `execute-phase/steps/partial-wave.md` | Quick-batch keeps bounded-batch rules (no implicit deletions); fast still commits through a session | 8f |
| F-31 | Upstream method fixes since our pin | Real defects fixed upstream after `c0b2a05` | Fewer false-passing gates; correct threat IDs in gap plans | `engineer/references/planner-verify-command-grounding.md`, `verify-command-path-resolvability.md`, `planner-reversibility.md`, `checkpoints.md`, `planner-gap-closure.md`, UAT `resolved_by`, report `covered_digest` | KEEP-UPSTREAM rows in section 13 | 6 |

## 5. Work phases

Each phase is one branch and one PR. Rows are in sections 10 to 14. The `check` block is what `scripts/check.py` runs.

### Phase 0: Tooling

- Write the scripts in section 6 under `scripts/`, with unit tests in `tests/test_overhaul_scripts.py`.
- Generate `docs/INVENTORY.md`.

```check
python -I scripts/inventory.py --check
python -m unittest tests.test_overhaul_scripts
```

### Phase 1: Delete Batch A

- Run `python -I scripts/delete_batch.py --batch A` (dry run), review, then add `--apply`.
- Commit: `chore(overhaul): delete unused upstream files (batch A)`.

```check
python -I scripts/delete_batch.py --batch A --verify
```

### Phase 2: Runtime, hooks, installer (rows R-RT, V, C)

- Port `.ai/runtime/` to `engineer/bin/` (rows R-RT in section 14).
- Port hooks to `hooks/` and installers to `bin/`.
- Repoint tests and CI.
- Fix `config-get` first: honour `--default <value>`, exit non-zero on a missing key, and support `--pick <field>` (row V-24). Every upstream `|| echo default` fallback depends on it.
- Leave `.ai/` in place until Phase 9; the old and new runtimes must both pass tests during the transition.

```check
sh engineer/bin/engineer_run verbs >/dev/null
python -m unittest discover -s tests
python -I scripts/verbs.py --report
```

### Phase 3: Mechanical renames

- Run `python -I scripts/rename.py` (dry run), review the per-file counts, then `--apply`.
- Rename agent files per [3.3](#33-role-names) with `git mv`.

```check
! grep -rn "gsd_run\|gsd-tools\|~/.claude/gsd-core\|/gsd:" agents commands engineer
python -I scripts/links.py
```

### Phase 4: Agents (rows R-AG)

```check
python -I scripts/progress.py --prefix R-AG --require-done
! grep -rln "gsd_run\|mandatory-initial-read\|agent-skills-bootstrap" agents
```

### Phase 5: Commands and workflows (rows R-WF)

```check
python -I scripts/progress.py --prefix R-WF --require-done
python -m unittest tests.test_unattended_flow tests.test_workflow_links
```

### Phase 6: References, templates, rules, config (rows R-RF, R-TP, R-RL), then Batch B

```check
python -I scripts/progress.py --prefix R-RF --prefix R-TP --prefix R-RL --require-done
python -I scripts/delete_batch.py --batch B --verify
python -m unittest discover -s tests
```

### Phase 7: Missing runtime verbs and Node removal (rows V with action NEW or REPLACE)

- Implement each NEW verb in the module its row names, with a unit test.
- Replace every inline `node -e/-p/-c` helper (V-150) and the `.cjs` probe scripts (V-151, V-152). Use the bundled `*-probe-fixtures/` as test oracles.
- Delete the call sites of DROP verbs as their rows say.

```check
python -I scripts/verbs.py --fail-on-unknown
! grep -rnE "node (-e|-p|-c)|\.cjs" agents commands engineer
python -m unittest discover -s tests
```

### Phase 8: Feature ports (one PR each, in this order)

| Sub-phase | Features | Why this order |
|---|---|---|
| 8a | F-20 security audit | Smallest (about 380 lines) and closes a real gap |
| 8b | F-21 to F-26 testing and spec probes | Largest benefit to code and test accuracy |
| 8c | F-27 pattern mapper | Unblocks plan-checker Dimension 12 |
| 8d | F-28 code review with fixes | Builds on targeted-fixer from Phase 4 |
| 8e | F-29 UI track | Needs a browser MCP for `dom-verifier` |
| 8f | F-30 fast lane | Depends on stable session and receipt verbs |

For each feature workflow, apply the local conventions listed in its R-WF rows: authority gate, `engineer_run query dispatch-isolation`, `resolve-model`/`resolve-effort` inline, report-only auditors, issue routing, no next-step prompts.

```check
python -I scripts/verbs.py --fail-on-unknown
python -m unittest discover -s tests
```

### Phase 9: Retire `.ai/`

- `git rm -r .ai .agents` after `bin/install.py` installs from the new layout into a scratch repository and the full test suite passes against it.
- Update `AGENTS.md` links to `engineer/RULES.md`, `engineer/truth-map.md`, `agents/AGENT.md`, `commands/COMMAND.md`.
- Update `THIRD-PARTY-NOTICES.md` (moved to the repository root) with the recorded upstream revision (D-08).

```check
test ! -e .ai
! grep -rn "\.ai/" AGENTS.md README.md agents commands engineer hooks bin skills tests .github
python -m unittest discover -s tests
```

## 6. Automation scripts to write

All under `scripts/`, Python 3.11+, standard library only, run with `python -I`. Every script defaults to a dry run and prints what it would do; `--apply` changes files. Add a test module per script.

| Script | Purpose | Inputs | Output / behavior |
|---|---|---|---|
| `manifest.json` | Single source for the delete batches and role renames | Section 10, [3.3](#33-role-names) | `{"batch_a": [...], "batch_b": [...], "renames": {"agents/gsd-planner.md": "agents/planner.md", ...}}` |
| `delete_batch.py` | Delete a batch | `--batch A\|B`, `--apply`, `--verify` | Dry run lists files; `--apply` runs `git rm -r --`; `--verify` exits 1 if any listed path still exists |
| `rename.py` | Apply [3.2](#32-mechanical-renames) | `--apply`, `--path` filter | Per-file substitution counts; refuses to touch `.ai/`, `.planning/`, `.git/`; `--apply` writes files with LF endings |
| `check.py` | Run a phase's `check` block from this document | `--phase N`, `--all` | Extracts fenced `check` blocks under `### Phase N`, runs each line with `bash -c` from the repository root, prints PASS/FAIL per line, exits non-zero if any line fails. A leading `!` inverts the exit status as in bash. |
| `progress.py` | Track rows | `--prefix`, `--require-done`, `--list` | Parses row IDs from sections 11 to 14, scans `git log --format=%B` for `Rows:` trailers, prints done/remaining; `--require-done` exits 1 if any row in the prefix is open |
| `verbs.py` | Verb coverage | `--report`, `--fail-on-unknown` | Scans `engineer_run query <verb>` in kept files, compares with `VERBS` in `engineer/bin/engineer.py`, lists unknown verbs with file:line |
| `links.py` | Link integrity | none | Resolves markdown links and `@path` includes in `agents/ commands/ engineer/ skills/`; lists broken targets |
| `inventory.py` | Inventory | `--check` | Writes `docs/INVENTORY.md`: every file in the tree with origin (upstream, reconciled, local-only), line count and remaining `gsd` references; `--check` fails if the file is stale |
| `anchor.py` | Show a row's lines at the baseline | `<row-id>` | Prints the GSD and local line ranges from `git show 9443672:<path>` side by side, to paste into an AI prompt |

## 7. Working a row with AI assistance

1. Create the phase worktree: `git worktree add .worktrees/overhaul-p<N> -b overhaul-p<N> origin/manual-override`.
2. Pick one target file. Collect its rows: `python -I scripts/anchor.py R-WF-07` (repeat per row).
3. Give the assistant this prompt, filled in:

   ```text
   Read PLANNED-UPDATES.md sections 2, 3 and 8. Apply rows <IDs> to <target file>
   exactly as their Instruction column says. Process rows bottom-up by GSD line.
   Copy local text from the cited ranges at commit 9443672, then apply the renames
   in section 3.2. Do not carry anything in section 8. Do not change other files.
   Run: python -I scripts/check.py --phase <N>
   Commit with the trailer line: Rows: <IDs>
   ```

4. Review the diff against the anchors. Push and update the draft PR.
5. Run `python -I scripts/progress.py --prefix <prefix>` to see what is left.

To do a row by hand, follow the same steps without the prompt: open both anchors, edit, run the check, and commit with the `Rows:` trailer.

## 8. Known local defects not to carry over

| Location (baseline `9443672`) | Defect | Correct behavior |
|---|---|---|
| `.ai/references/template-adaptation.md:42` | Says the coordinator merges automatically after verification | Merge only on the user's explicit instruction |
| `.ai/workflows/execute-phase.md:818` | Says the dispatch hook blocks unisolated runs | The hook warns; `dispatch-isolation` refuses |
| `.ai/workflows/discuss-phase/modes/auto.md:7,32` | Points to `modes/chain.md` and `auto_advance`, which do not exist | Remove the references |
| `.ai/guides/PHASE-WORKFLOW.md:102` | "Checkpoints go to the user" | Checkpoints follow issue routing without stopping the run |
| `.ai/guides/PHASE-WORKFLOW.md:116`, `.ai/workflows/quick.md:495` | Offer todos for gaps | Workflows never create todos |
| `.ai/RULES.md:125`, `.ai/truth-map.md:22`, `.ai/references/documentation.md:20,37` | Name ADRs as fact owners after the ADR subsystem was removed | Decisions live in PROJECT.md Key Decisions via `state.add-decision` |
| `.ai/templates/README.md:25` | "28 artifact templates"; `rule.md` missing from the table | Generate the count and table from the files |
| `.ai/references/universal-anti-patterns.md:10` | Says not to read agent files | Read your role file (AGENTS.md) |
| `.ai/THIRD-PARTY-NOTICES.md:26-30` | Pins `4713ffba`/`b956bb7` while the vendored copy was `c0b2a05` | Record the new upstream revision (D-08) |
| `.ai/commands/ship.md` argument-hint | Omits `--no-merge` | List every flag the workflow reads |
| `.ai/commands/execute-phase.md` | Repeats "Phase number: $ARGUMENTS (required)." twice | State it once |
| `.ai/agents/README.md:73` vs installer since #99 | Says definitions carry no `model:` but the installer writes it for four roles | State the installer-written frontmatter and that dispatch values override it |
| `.ai/agents/codebase-mapper.md` `<why_this_matters>` and other rationale blocks | Explanatory prose in agent-facing text | Directive text only |

## 9. Decisions

Record each decision with `engineer_run query state.add-decision` once made. Defaults below apply until you change them.

| ID | Decision | Default | Alternatives |
|---|---|---|---|
| D-01 | Role names | Upstream names without `gsd-` (as in `agents/executor.md`); local names are aliases | Keep local names (`coder`, `phase-preparer`, ...) |
| D-02 | Progressive loading (`section-manifest.json`, `steps/` read only when a flag or state matches) | Not adopted; manifest deleted in Batch A; kept `steps/` are read unconditionally | Adopt the manifest for faster, smaller context loads |
| D-03 | Compact template variants | Not adopted (`RULES.md` "complete template use") | Adopt `.compact.md` with a `workflow.compact_content` switch |
| D-04 | Project initialization command | `commands/new-project.md` carries the local onboard body; `/onboard` is an alias | Rename to `onboard` only |
| D-05 | Merge policy | `/ship` merges only on the user's explicit instruction | Never merge from workflows |
| D-06 | Worktree guard hook | Warn only; the runtime refuses unisolated dispatch | Block in the hook |
| D-07 | `CONTRIBUTING.md` (emptied in `80ceb20`) | Restore the writing standard from `35b8bf0:CONTRIBUTING.md`, updated to the new layout | Leave empty |
| D-08 | Upstream revision of the download | Look up the gsd-core commit that contains issue `#5640` changes and record its SHA | Record the download date only |
| D-09 | Config format | `.planning/config.yaml` with a template at `engineer/templates/config.yaml` | Upstream `config.json` |
| D-10 | Feature flags for new features | `workflow.security_enforcement: true`, `workflow.nyquist_validation: true`, `workflow.ui_phase: auto` (on when the phase touches UI) | All off by default |

## 10. Delete list

Batch A removes upstream files with no local counterpart and no selected feature. Batch B removes upstream originals of files we rewrote, after their reconciliation rows are done. Files not listed are kept. Empty placeholders you created (`agents/AGENT.md`, `commands/COMMAND.md`, `engineer/workflows/WORKFLOW.md`, `engineer/references/REFERENCE.md`, `engineer/templates/TEMPLATE.md`, `engineer/bin/engineer_run`, `bin/*.py`, `hooks/worktree-path-guard.py`, `scripts/SCRIPT.py`, `skills/SKILL/SKILL.md`, `docs/INVENTORY.md`) are kept and filled per section 3.1.
### Batch A: delete now (227 files)

#### `agents/` (16)

```text
agents/gsd-advisor-researcher.md
agents/gsd-ai-researcher.md
agents/gsd-assumptions-analyzer.md
agents/gsd-debug-session-manager.md
agents/gsd-doc-classifier.md
agents/gsd-doc-synthesizer.md
agents/gsd-domain-researcher.md
agents/gsd-eval-auditor.md
agents/gsd-eval-planner.md
agents/gsd-framework-selector.md
agents/gsd-intel-updater.md
agents/gsd-mempalace-curator.md
agents/gsd-project-researcher.md
agents/gsd-research-synthesizer.md
agents/gsd-roadmapper.md
agents/gsd-user-profiler.md
```

#### `commands/` (44)

```text
commands/ai-integration-phase.md
commands/audit-milestone.md
commands/autonomous.md
commands/config.md
commands/debug.md
commands/docs-update.md
commands/eval-review.md
commands/explore.md
commands/extract-learnings.md
commands/forensics.md
commands/graphify.md
commands/health.md
commands/help.md
commands/import.md
commands/inbox.md
commands/ingest-docs.md
commands/manager.md
commands/map-codebase.md
commands/mempalace-capture.md
commands/mempalace-recall.md
commands/mvp-phase.md
commands/ns-context.md
commands/ns-ideate.md
commands/ns-manage.md
commands/ns-project.md
commands/ns-review.md
commands/ns-workflow.md
commands/onboard.md
commands/pause-work.md
commands/plan-review-convergence.md
commands/pr-branch.md
commands/profile-user.md
commands/resume-work.md
commands/review-backlog.md
commands/review.md
commands/settings.md
commands/sketch.md
commands/spike.md
commands/stats.md
commands/surface.md
commands/thread.md
commands/undo.md
commands/workspace.md
commands/workstreams.md
```

#### `engineer/workflows/` (58)

```text
engineer/workflows/add-backlog.md
engineer/workflows/ai-integration-phase.md
engineer/workflows/analyze-dependencies.md
engineer/workflows/audit-milestone.md
engineer/workflows/autonomous.md
engineer/workflows/debug.md
engineer/workflows/diagnose-issues.md
engineer/workflows/discuss-phase-assumptions.md
engineer/workflows/discuss-phase-power.md
engineer/workflows/do.md
engineer/workflows/docs-update.md
engineer/workflows/eval-review.md
engineer/workflows/execute-plan.md
engineer/workflows/explore.md
engineer/workflows/extract-learnings.md
engineer/workflows/forensics.md
engineer/workflows/graduation.md
engineer/workflows/health.md
engineer/workflows/help.md
engineer/workflows/import.md
engineer/workflows/inbox.md
engineer/workflows/ingest-docs.md
engineer/workflows/list-phase-assumptions.md
engineer/workflows/list-seeds.md
engineer/workflows/list-workspaces.md
engineer/workflows/manager.md
engineer/workflows/map-codebase.md
engineer/workflows/mvp-phase.md
engineer/workflows/new-workspace.md
engineer/workflows/node-repair.md
engineer/workflows/note.md
engineer/workflows/onboard.md
engineer/workflows/pause-work.md
engineer/workflows/plan-review-convergence.md
engineer/workflows/plant-seed.md
engineer/workflows/pr-branch.md
engineer/workflows/profile-user.md
engineer/workflows/reapply-patches.md
engineer/workflows/remove-workspace.md
engineer/workflows/resume-project.md
engineer/workflows/review.md
engineer/workflows/scan.md
engineer/workflows/section-manifest.json
engineer/workflows/session-report.md
engineer/workflows/settings-advanced.md
engineer/workflows/settings-integrations.md
engineer/workflows/settings.md
engineer/workflows/sketch-wrap-up.md
engineer/workflows/sketch.md
engineer/workflows/smart-entry.md
engineer/workflows/spike-wrap-up.md
engineer/workflows/spike.md
engineer/workflows/stats.md
engineer/workflows/sync-skills.md
engineer/workflows/thread.md
engineer/workflows/transition.md
engineer/workflows/ultraplan-phase.md
engineer/workflows/undo.md
```

#### `engineer/workflows/autonomous/steps/` (5)

```text
engineer/workflows/autonomous/steps/converge-banner.md
engineer/workflows/autonomous/steps/converge-dispatch-bg.md
engineer/workflows/autonomous/steps/converge-dispatch-inline.md
engineer/workflows/autonomous/steps/converge-fail-fast.md
engineer/workflows/autonomous/steps/converge-loop.md
```

#### `engineer/workflows/autonomous/templates/` (1)

```text
engineer/workflows/autonomous/templates/minimal-context.md
```

#### `engineer/workflows/code-review/steps/` (1)

```text
engineer/workflows/code-review/steps/structural-pre-pass.md
```

#### `engineer/workflows/complete-milestone/detail/` (1)

```text
engineer/workflows/complete-milestone/detail/elaboration.md
```

#### `engineer/workflows/complete-milestone/steps/` (3)

```text
engineer/workflows/complete-milestone/steps/git-tag.md
engineer/workflows/complete-milestone/steps/project-md-evolution-review.md
engineer/workflows/complete-milestone/steps/release-map.md
```

#### `engineer/workflows/discuss-phase-assumptions/steps/` (1)

```text
engineer/workflows/discuss-phase-assumptions/steps/auto-advance-dispatch.md
```

#### `engineer/workflows/discuss-phase/modes/` (5)

```text
engineer/workflows/discuss-phase/modes/advisor.md
engineer/workflows/discuss-phase/modes/analyze.md
engineer/workflows/discuss-phase/modes/batch.md
engineer/workflows/discuss-phase/modes/chain.md
engineer/workflows/discuss-phase/modes/power.md
```

#### `engineer/workflows/docs-update/detail/` (1)

```text
engineer/workflows/docs-update/detail/elaboration.md
```

#### `engineer/workflows/docs-update/steps/` (1)

```text
engineer/workflows/docs-update/steps/dispatch-monorepo-packages.md
```

#### `engineer/workflows/execute-phase/detail/` (1)

```text
engineer/workflows/execute-phase/detail/elaboration.md
```

#### `engineer/workflows/execute-phase/steps/` (2)

```text
engineer/workflows/execute-phase/steps/codebase-drift-gate.md
engineer/workflows/execute-phase/steps/wave-post-gate-hooks.md
```

#### `engineer/workflows/help/modes/` (5)

```text
engineer/workflows/help/modes/brief.md
engineer/workflows/help/modes/default.md
engineer/workflows/help/modes/full.compact.md
engineer/workflows/help/modes/full.md
engineer/workflows/help/modes/topic.md
```

#### `engineer/workflows/new-milestone/steps/` (2)

```text
engineer/workflows/new-milestone/steps/project-md-milestone-write.md
engineer/workflows/new-milestone/steps/reset-phase-safety.md
```

#### `engineer/workflows/new-project/detail/` (1)

```text
engineer/workflows/new-project/detail/elaboration.md
```

#### `engineer/workflows/new-project/steps/` (2)

```text
engineer/workflows/new-project/steps/auto-mode-config.md
engineer/workflows/new-project/steps/auto-mode-detection.md
```

#### `engineer/workflows/plan-phase/detail/` (1)

```text
engineer/workflows/plan-phase/detail/elaboration.md
```

#### `engineer/workflows/plan-phase/steps/` (8)

```text
engineer/workflows/plan-phase/steps/adr-ingest-express-path.md
engineer/workflows/plan-phase/steps/auto-advance-check.md
engineer/workflows/plan-phase/steps/chunked-planning-mode.md
engineer/workflows/plan-phase/steps/prd-express-gate.md
engineer/workflows/plan-phase/steps/prd-express-path.md
engineer/workflows/plan-phase/steps/research-only-early-exit.md
engineer/workflows/plan-phase/steps/research-only-modifiers.md
engineer/workflows/plan-phase/steps/reviews-prerequisite.md
```

#### `engineer/workflows/progress/steps/` (2)

```text
engineer/workflows/progress/steps/forensic-audit.md
engineer/workflows/progress/steps/mvp-display.md
```

#### `engineer/workflows/quick/steps/` (2)

```text
engineer/workflows/quick/steps/discussion-phase.md
engineer/workflows/quick/steps/research-phase.md
```

#### `engineer/workflows/review/steps/` (2)

```text
engineer/workflows/review/steps/reviewer-instances-note-1.md
engineer/workflows/review/steps/reviewer-instances-note-2.md
```

#### `engineer/workflows/transition/steps/` (1)

```text
engineer/workflows/transition/steps/workstream-collision-check.md
```

#### `engineer/workflows/update/steps/` (1)

```text
engineer/workflows/update/steps/channel-banner.md
```

#### `engineer/workflows/verify-work/detail/` (1)

```text
engineer/workflows/verify-work/detail/elaboration.md
```

#### `engineer/workflows/verify-work/steps/` (1)

```text
engineer/workflows/verify-work/steps/mvp-uat-framing.md
```

#### `engineer/references/` (45)

```text
engineer/references/agent-skills-bootstrap.md
engineer/references/ai-evals.md
engineer/references/ai-frameworks.md
engineer/references/api-coverage.md
engineer/references/autonomous-smart-discuss.md
engineer/references/autonomous-ui-design-contract.md
engineer/references/compact-content-gate.md
engineer/references/continuation-format.md
engineer/references/decimal-phase-calculation.md
engineer/references/doc-conflict-engine.md
engineer/references/execute-phase-between-wave-reset.md
engineer/references/execute-phase-context-guard.md
engineer/references/execute-phase-quota-recovery.md
engineer/references/execute-phase-requirement-revert.md
engineer/references/execute-phase-response-language.md
engineer/references/execute-phase-wave-guard.md
engineer/references/git-planning-commit.md
engineer/references/gsd-run-resolver.md
engineer/references/loop-hook-dispatch.md
engineer/references/mandatory-initial-read.md
engineer/references/model-profile-resolution.md
engineer/references/mvp-concepts.md
engineer/references/offer-next.md
engineer/references/phase-argument-parsing.md
engineer/references/phase-id-convention.md
engineer/references/planner-failing-direction.md
engineer/references/planner-graphify-auto-update.md
engineer/references/planner-human-verify-mode.md
engineer/references/planning-config.md
engineer/references/project-skills-discovery.md
engineer/references/response-language-directive.md
engineer/references/reviewer-instances.md
engineer/references/run-resolver.md
engineer/references/runtime-aware-dispatch.md
engineer/references/skeleton-template.md
engineer/references/sketch-interactivity.md
engineer/references/sketch-theme-system.md
engineer/references/sketch-tooling.md
engineer/references/sketch-variant-patterns.md
engineer/references/spidr-splitting.md
engineer/references/thinking-partner.md
engineer/references/ui-brand.md
engineer/references/user-profiling.md
engineer/references/user-story-template.md
engineer/references/workstream-flag.md
```

#### `engineer/templates/` (13)

```text
engineer/templates/AI-SPEC.md
engineer/templates/DEBUG.md
engineer/templates/config.json
engineer/templates/copilot-instructions.md
engineer/templates/dev-preferences.md
engineer/templates/milestone-archive.md
engineer/templates/retrospective.md
engineer/templates/summary-complex.md
engineer/templates/summary-minimal.md
engineer/templates/summary-standard.md
engineer/templates/summary.compact.md
engineer/templates/user-profile.md
engineer/templates/user-setup.compact.md
```

### Batch B: delete after the R-RF rows that read them are done (6 files)

#### `engineer/references/` (6)

```text
engineer/references/agent-contracts.md
engineer/references/artifact-types.md
engineer/references/dispatch-isolation-gate.md
engineer/references/git-integration.md
engineer/references/model-profiles.md
engineer/references/revision-loop.md
```

## 11. Reconciliation: agents

355 rows (R-AG). Phase 4.

How to read the rows:

- **GSD target lines** are in the downloaded GSD copy at `9443672` (`agents/`, `commands/`, `engineer/`). "after X:N" is an insertion point.
- **Local source lines** are in `.ai/`, `.planning/` or `AGENTS.md` at `9443672`.
- **Action:** STITCH inserts the local block; REPLACE swaps GSD lines for local lines; REMOVE deletes GSD lines; NEW FILE creates the target from the local source; RENAME moves a file; KEEP-UPSTREAM keeps newer upstream content on purpose; DROP-LOCAL leaves local content behind on purpose.
- Apply the renames in [3.2](#32-mechanical-renames) to every copied block. Section 3.3 gives the final role names.
- Process each file bottom-up. Commit with a `Rows:` trailer naming the IDs done.

### Cross-cutting conventions (apply to every agents/*.md target below)

Evidence base: line numbers verified at HEAD 9443672 (`git diff`-equivalent `diff agents/<gsd> .ai/agents/<local>`). Runtime verb support checked against `.ai/runtime/phase.py:801-915` (VERBS). Wording-only drift (GSD→"workflow" nouns, `#NNNN` issue tags, `gsd:write-continue` sentinel names, `/clear` phrasing) is ignored in every subsection unless it carries a rule.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-001 | REPLACE | every `@~/.claude/gsd-core/<x>`, `~/.claude/gsd-core/<x>`, bare `gsd-core/<x>`, `@~/.claude/references/<x>`, `.claude/references/<x>`, `@~/.claude/templates/<x>` | — | Rewrite to `engineer/<x>` (`@engineer/<x>` for @-includes, `../engineer/<x>` for Markdown links). |
| R-AG-002 | REPLACE | every stitched local link | `.ai/agents/*.md` links `../references/methods/<x>`, `../references/<x>`, `../templates/<x>`, `../commands/<x>`, `../workflows/<x>`, `@.ai/references/<x>` | Rewrite to `../engineer/references/<x>`, `../engineer/references/<x>`, `../engineer/templates/<x>`, `../commands/<x>`, `../engineer/workflows/<x>`, `@engineer/references/<x>` respectively. |
| R-AG-003 | REPLACE | every stitched local link | `../RULES.md`, `../rules/README.md`, `../runtime/TEMPLATE-CONTRACT.md`, `../hooks/context-handoff.sh`, `README.md` (catalog) | Rewrite to the relocated targets chosen by the references/runtime sections (`engineer/RULES.md`, `engineer/rules/README.md`, `engineer/references/template-contract.md`, `hooks/context-handoff.sh`), and `README.md` → `AGENT.md`. |
| R-AG-004 | REPLACE | every `gsd_run`/`gsd-tools`/`_GSD_SHIM_NAME` launcher | local `phase_run query`, `python .ai/runtime/phase.py query` | Use `engineer_run query <verb>` only for verbs present in `.ai/runtime/phase.py:801-915`; remove calls to absent verbs (`state.load`, `state.record-metric`, `requirements.mark-complete`, `check *`, `windows`, `verify.*`, `frontmatter.*`, `plan.task-structure`, `phase.list-*`, `history-digest`, `learnings.query`, `estimate-check`, `research-plan`, `research-store`, `classify-confidence`, `websearch`, `package-legitimacy`, `summary-extract`, `run-with-timeout`, `user-story.validate`, `verification.fingerprint`, `graphify`, `intel`). |
| R-AG-005 | KEEP-UPSTREAM | every `CLAUDE.md` mention | Original copied GSD text | Preserve `CLAUDE.md` and `.claude/CLAUDE.md`; do not substitute `AGENTS.md` in shared source. |
| R-AG-006 | REPLACE | every `/gsd:<cmd>` and `/gsd-<cmd>` | — | Replace with the bare command name (`plan-phase`, `execute-phase`, `verify-work`, `ui-phase`, `ui-review`, `secure-phase`, `code-review`) present in `commands/`. |
| R-AG-007 | REPLACE | stitched local prose role names | role mapping in `.ai/agents/README.md:11-24` | Rename whole-word local roles in stitched text: coder→executor, phase-preparer/preparer→planner, phase-checker→plan-checker, researcher→phase-researcher (leave ui-researcher/scout/targeted-fixer/coordinator unchanged). |
| R-AG-008 | REPLACE | every `agent_skills: self-load per @.../agent-skills-bootstrap.md (agent type: ...)` | `.ai/agents/coder.md:81` | Replace with `**agent_skills:** self-load from \`.claude/skills/\` or \`.agents/skills/\``. |
| R-AG-009 | REPLACE | every `4. Do NOT load full \`AGENTS.md\` files (100KB+ context cost)` | `.ai/agents/code-reviewer.md:79` | Replace with `4. Read repository \`AGENTS.md\`; do not load unrelated large agent catalogs`. |
| R-AG-010 | REPLACE | every `2. Read \`SKILL.md\` for each skill (lightweight index ~130 lines)` | `.ai/agents/code-reviewer.md:77` | Replace with `2. Read \`SKILL.md\` for each applicable or assigned skill (select by its description)`. |
| R-AG-011 | REPLACE | every `@.../mandatory-initial-read.md` include | `.ai/agents/coder.md:45` | Replace with `@engineer/references/worker-handoff.md`. |
| R-AG-012 | REPLACE | every frontmatter `name: gsd-<x>` | — | Set `name:` to the target filename stem (e.g. `planner`). |

Done when:
- `grep -lE "gsd_run|gsd-tools|_GSD_SHIM|phase_run|\.ai/runtime/phase\.py" agents/*.md` prints nothing.
- `grep -lE "~/\.claude|gsd-core/|\(\.\./references/|@\.ai/" agents/*.md` prints nothing.
- `grep -lE "/gsd[:-]|agent-skills-bootstrap|mandatory-initial-read" agents/*.md` prints nothing.
- `grep -l "^name: gsd-" agents/*.md` prints nothing.

### agents/executor.md (from agents/executor.md; local source .ai/agents/coder.md)

Wording-only drift ignored. The redraft already carries coder.md:523-524 (executor.md:501-502) and uses `engineer_run`.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-013 | REPLACE | agents/executor.md:3-4 | .ai/agents/coder.md:3-4 | Replace description and tools with coder's (adds `Agent` and the context7 MCP tools); keep `name: executor`. |
| R-AG-014 | STITCH | after agents/executor.md:12 | .ai/agents/coder.md:14-36 | Insert coder's `<local_workflow>` block before `<role>`. |
| R-AG-015 | REPLACE | agents/executor.md:14-22 | .ai/agents/coder.md:38-47 | Replace `<role>` with coder's role (returns proposed STATE updates; includes worker-handoff and worktree-path-safety). |
| R-AG-016 | REPLACE | agents/executor.md:24-29 | .ai/agents/coder.md:49-69 | Replace `<documentation_lookup>` with coder's version-specific lookup procedure. |
| R-AG-017 | REPLACE | agents/executor.md:31-44 | .ai/agents/coder.md:71-84 | Replace `<project_context>` with coder's (AGENTS.md, rule catalog, inline skill self-load, AGENTS.md enforcement). |
| R-AG-018 | REPLACE | agents/executor.md:48-68 | .ai/agents/coder.md:88-119 | Replace `load_project_state` (drops `init.execute-phase`, `executor_model`, `state.load`) with coder's file reads, verify-only `<worktree_branch_check>`, `<project_root_pin>` guard, no-branch-switch rule and report-don't-reconstruct STATE rule. |
| R-AG-019 | REPLACE | agents/executor.md:85-102 | .ai/agents/coder.md:136-147 | Replace `<worktree_metadata_capture>` with coder's `<base_revision_capture>` (WORK_ROOT/WORK_BRANCH/WORK_BASE recorded in SUMMARY). |
| R-AG-020 | STITCH | after agents/executor.md:118 | .ai/agents/coder.md:166-169 | Insert the `## Task execution` heading and iOS-scaffold pointer (`engineer/references/ios-scaffold.md`). |
| R-AG-021 | REPLACE | agents/executor.md:124 | .ai/agents/coder.md:175 | Replace `/plan-phase` rerun wording with coder's `plan-phase` wording (keep precondition rule). |
| R-AG-022 | STITCH | after agents/executor.md:132 | .ai/agents/coder.md:185-195 | Insert the early-integration-slice item (tracer as `type="auto"`, halt expansion on failed slice). |
| R-AG-023 | REPLACE | agents/executor.md:194 | .ai/agents/coder.md:256 | Replace `re-run /plan-phase --research-phase` with coder's coordinator research route. |
| R-AG-024 | REPLACE | agents/executor.md:214-216 | .ai/agents/coder.md:274-278 (fix) | Replace the `engineer_run query state.add-blocker` block with "record the blocker in SUMMARY Remaining and return the checkpoint" (resolves coder.md:277 vs 736 conflict). |
| R-AG-025 | REPLACE | agents/executor.md:240 | .ai/agents/coder.md:299 | Replace `deferred-items.md` logging with SUMMARY Remaining/Deferred for the coordinator. |
| R-AG-026 | REPLACE | agents/executor.md:283-285 | .ai/agents/coder.md:338-343 | Replace "Auto mode is active" with coder's no-auto-approval rule. |
| R-AG-027 | REPLACE | agents/executor.md:300-321 | .ai/agents/coder.md:356-378 | Replace the `NEEDS REVISION` auto-mode block with coder's early-integration note, blocking-human precedence and three checkpoint types. |
| R-AG-028 | REPLACE | agents/executor.md:370-388 | .ai/agents/coder.md:426-434 | Replace `<tdd_execution>` (drops unsupported `engineer_run check tdd-red-evidence`) with coder's TDD evidence rule pointing at `engineer/references/tdd.md` and `execute-mvp-tdd.md`. |
| R-AG-029 | STITCH | after agents/executor.md:388 | .ai/agents/coder.md:436-466 | Insert `<role_and_context_boundary>` (no self-review, 60%/250k stop, `status: blocked`, `handoff.write` digest, `<handoff>` continuation). |
| R-AG-030 | STITCH | before agents/executor.md:393 | .ai/agents/coder.md:471-478 | Insert coder step 0 (verify root/branch against assignment, ownership check, record starting revision). |
| R-AG-031 | KEEP-UPSTREAM | agents/executor.md:393-435 | .ai/agents/coder.md:480-490 | Keep concrete 0a/0b guards (upstream executable drift checks); append coder 0b's ownership/symlink rule after line 431. |
| R-AG-032 | KEEP-UPSTREAM | agents/executor.md:437-460 | .ai/agents/coder.md:492-496 | Keep the detached/protected HEAD script (`git.base-branch --is-protected` exists, phase.py:165-177); delete the `git.allow_default_branch_commits`/`config.json` hint on line 458. |
| R-AG-033 | REPLACE | agents/executor.md:469 | .ai/runtime/lib/worktrees.py:54-55 | Widen the allow-list regex to `^((worktree-)?agent-\|worktree-wf_\|phase-\|quick-\|review-\|verify-\|milestone-\|onboard-)[A-Za-z0-9._/-]+$` and update message line 470. |
| R-AG-034 | STITCH | after agents/executor.md:479 | .ai/agents/coder.md:501-502 | Insert the canonical Git workflow pointer (exact-path staging, preserve unrelated dirty files). |
| R-AG-035 | REMOVE | agents/executor.md:515 | — | Delete the multi-repo `sub_repos`/`commit-to-subrepo` hash line. |
| R-AG-036 | KEEP-UPSTREAM | agents/executor.md:517-526 | .ai/agents/coder.md:537-544 | Keep `git show --first-parent` deletion check; correct for merge commits. |
| R-AG-037 | REPLACE | agents/executor.md:532-576 | .ai/agents/coder.md:550-591 | Replace worktree-only `git clean` rationale, the `reset --hard` startup exception and the throwaway-branch WIP alternative with coder's shared-checkout prohibition. |
| R-AG-038 | REPLACE | agents/executor.md:608 | .ai/agents/coder.md:620 | Point the template include at `@engineer/templates/summary.md`. |
| R-AG-039 | STITCH | after agents/executor.md:610 | .ai/agents/coder.md:622-625 | Insert coder's contract (acceptance IDs, documentation paths, `status: complete\|blocked`, nonempty Checks). |
| R-AG-040 | REPLACE | agents/executor.md:623-637 | .ai/agents/coder.md:627-647 | Replace the dangling "protocol 0c" `plan-head-before` git-dir ledger with coder's assigned-base `git rev-list --count` rule; keep `plan_head_after`. |
| R-AG-041 | REPLACE | agents/executor.md:674-687 | .ai/agents/coder.md:681-685 | Replace the `engineer_run windows append` / `.planning/WINDOWS.md` ledger with coder's SUMMARY Remaining rule. |
| R-AG-042 | STITCH | after agents/executor.md:699 | .ai/agents/coder.md:699-704 | Insert canonical threat tracking (Threat Outcomes, Pending requests, no shared PLAN edits). |
| R-AG-043 | STITCH | after agents/executor.md:709 | .ai/agents/coder.md:715-718 | Insert Threat Outcomes self-check bullets. |
| R-AG-044 | KEEP-UPSTREAM | agents/executor.md:714 | .ai/agents/coder.md:722 | Keep `merge-base --is-ancestor`; checks reachability, not any ref. |
| R-AG-045 | REPLACE | agents/executor.md:722-778 | .ai/agents/coder.md:730-755 | Replace every `engineer_run query state.*`/`roadmap.*`/`requirements.mark-complete` call with coder's proposal-return checklist. |
| R-AG-046 | REPLACE | agents/executor.md:780-820 | .ai/agents/coder.md:757-765 | Replace the `engineer_run query commit` SUMMARY+STATE+ROADMAP+REQUIREMENTS commit and envelope list with coder's exact-path commit of SUMMARY and owned files only. |
| R-AG-047 | REPLACE | agents/executor.md:831-833 | .ai/agents/coder.md:775 | Replace the `<worktree_metadata>` JSON block with `**Base:** {WORK_BRANCH} @ {WORK_BASE}`. |
| R-AG-048 | REPLACE | agents/executor.md:854-856 | .ai/agents/coder.md:795-797 | Replace STATE/ROADMAP-updated criteria with proposals-returned criteria. |

Done when:
- `grep -cE "state\.(advance-plan|update-progress|record-metric|add-decision|record-session|load|add-blocker)|requirements\.mark-complete|roadmap\.update-plan-progress|windows append|query commit" agents/executor.md` returns 0.
- `grep -cE "worktree_metadata|deferred-items\.md|WINDOWS\.md|NEEDS REVISION|Auto mode is active|sub_repos|tdd-red-evidence" agents/executor.md` returns 0.
- `grep -c "<local_workflow>" agents/executor.md` returns 1; `grep -c "<role_and_context_boundary>" agents/executor.md` returns 1.
- `grep -c "250,000 tokens" agents/executor.md` returns 1; `grep -c "status: blocked" agents/executor.md` ≥ 1.
- `grep -c "Do not stage STATE, ROADMAP or REQUIREMENTS" agents/executor.md` returns 1.
- `grep -c "phase-|quick-|review-|verify-" agents/executor.md` ≥ 1.

### agents/planner.md (from agents/gsd-planner.md; local source .ai/agents/phase-preparer.md)

Wording-only drift ignored (lines 15, 23, 827-836 wording, sentinels 817-818).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-049 | RENAME | agents/gsd-planner.md | — | Rename to `agents/planner.md` with `git mv`. |
| R-AG-050 | REPLACE | agents/gsd-planner.md:2-4 | .ai/agents/phase-preparer.md:2-4 | Set `name: planner`, preparer description, and tools with `Agent` prepended. |
| R-AG-051 | STITCH | after agents/gsd-planner.md:13 | .ai/agents/phase-preparer.md:14-41 | Insert `<local_workflow>` (scout routing, no implementation permission, PLAN/VALIDATION-only writes). |
| R-AG-052 | REPLACE | agents/gsd-planner.md:18-21 | .ai/agents/phase-preparer.md:47-50 | Replace `--gaps`/`--reviews` flag spawn modes with assignment-based modes. |
| R-AG-053 | REPLACE | agents/gsd-planner.md:25 | .ai/agents/phase-preparer.md:54 | Replace mandatory-initial-read include with the worker-handoff include. |
| R-AG-054 | REPLACE | agents/gsd-planner.md:29 | .ai/agents/phase-preparer.md:58 | Replace fixed "2-3 tasks each" with sizing-target wording tied to `estimate_scope`. |
| R-AG-055 | REPLACE | agents/gsd-planner.md:46-47 | .ai/agents/phase-preparer.md:75-76 | Replace project-skills-discovery include with inline skills check and rule catalog. |
| R-AG-056 | REPLACE | agents/gsd-planner.md:64 | .ai/agents/phase-preparer.md:93 | Accept `Agent Discretion` alongside `Claude's Discretion`. |
| R-AG-057 | REPLACE | agents/gsd-planner.md:69 | .ai/agents/phase-preparer.md:98 | Replace the `check.decision-coverage-plan` gate note with the citation-review rule. |
| R-AG-058 | REPLACE | agents/gsd-planner.md:89-98 | .ai/agents/phase-preparer.md:118-128 | Replace budget-driven phase split with commit-complete-plans-and-continue plus human-gated `PHASE SPLIT RECOMMENDED`. |
| R-AG-059 | REPLACE | agents/gsd-planner.md:104-108 | .ai/agents/phase-preparer.md:134-138 | Replace source-audit wording so research suggestions are evidence, not scope authority. |
| R-AG-060 | REPLACE | agents/gsd-planner.md:118-123 | .ai/agents/phase-preparer.md:148-152 | Replace the ">50% context" split reason with `estimate_scope` splits and named blockers. |
| R-AG-061 | REPLACE | agents/gsd-planner.md:134-159 | .ai/agents/phase-preparer.md:163-184 | Replace Mandatory Discovery Levels 0-3 and the `--research-phase` hint with the Discovery gate (Resolved / One missing fact / Unresolved). |
| R-AG-062 | REPLACE | agents/gsd-planner.md:191 | .ai/agents/phase-preparer.md:216 | Replace the Nyquist `MISSING — Wave 0` placeholder rule with "Verification planning". |
| R-AG-063 | REPLACE | agents/gsd-planner.md:193 | .ai/agents/phase-preparer.md:218-225 | Replace `prior_verify_commands` reuse (no local init field) with the command/expected-result/failure-condition rule. |
| R-AG-064 | KEEP-UPSTREAM | agents/gsd-planner.md:195 | .ai/agents/phase-preparer.md:227-229 | Keep the gate-baseline sentence; read-only grep baseline is safe. Prepend local line 227's grounding pointer. |
| R-AG-065 | REPLACE | agents/gsd-planner.md:198 | .ai/agents/phase-preparer.md:232 | Downgrade comment-text discipline from HARD GATE to review rule. |
| R-AG-066 | REPLACE | agents/gsd-planner.md:211 | .ai/agents/phase-preparer.md:245 | Replace auto-inserted `checkpoint:decision` with coordinator decision only when unauthorized. |
| R-AG-067 | REPLACE | agents/gsd-planner.md:217-219 | .ai/agents/phase-preparer.md:251-253 | Replace `workflow.tdd_mode` toggle with assignment-required TDD. |
| R-AG-068 | REPLACE | agents/gsd-planner.md:251 | .ai/agents/phase-preparer.md:285 | Replace `workflow.human_verify_mode` with coordinator UAT handoff. |
| R-AG-069 | REPLACE | agents/gsd-planner.md:255-261 | .ai/agents/phase-preparer.md:289-299 | Replace mandatory `type="tracer"` with tracer-as-design using `type="auto"`. |
| R-AG-070 | REPLACE | agents/gsd-planner.md:264-269 | .ai/agents/phase-preparer.md:302-307 | Replace the tracer task example with the `type="auto"` example. |
| R-AG-071 | REPLACE | agents/gsd-planner.md:273-280 | .ai/agents/phase-preparer.md:311-316 | Replace expansion rule plus `--no-tracer`/`MVP_MODE`/`WALKING_SKELETON`/`/gsd:mvp-phase`/SKELETON.md block with local retained-production and user-story wording. |
| R-AG-072 | REPLACE | agents/gsd-planner.md:297-301 | .ai/agents/phase-preparer.md:334-338 | Replace `estimate-calibration` emission with optional uncalibrated advisory estimate. |
| R-AG-073 | REPLACE | agents/gsd-planner.md:314-318 | .ai/agents/phase-preparer.md:351-359 | Replace frontmatter `wave`/`depends_on`/`requirements` comments and add `acceptance`, `documentation`, `resources`, `checks` fields. |
| R-AG-074 | REPLACE | agents/gsd-planner.md:321-325 | .ai/agents/phase-preparer.md:362-365 | Replace calibrated `estimate` block with `calibration: uncalibrated` block. |
| R-AG-075 | REPLACE | agents/gsd-planner.md:341-342 | .ai/agents/phase-preparer.md:381-382 | Point plan context includes at `@commands/execute-phase.md` and `@engineer/templates/summary.md`. |
| R-AG-076 | KEEP-UPSTREAM | agents/gsd-planner.md:375-376 | — | Keep phase-unique threat-ID numbering; prevents reused IDs. |
| R-AG-077 | REPLACE | agents/gsd-planner.md:381 | .ai/agents/phase-preparer.md:419 | Replace the package-legitimacy-gate `T-{phase}-SC` row with dependency-identity mitigation. |
| R-AG-078 | REPLACE | agents/gsd-planner.md:404-413 | .ai/agents/phase-preparer.md:442-460 | Replace wave/estimate field descriptions and "Execute-phase reads wave" with TEMPLATE-CONTRACT fields and `phase-plan-index` scheduling. |
| R-AG-079 | REPLACE | agents/gsd-planner.md:457-465 | .ai/agents/phase-preparer.md:504-532 | Replace `security_enforcement` toggle and Package legitimacy gate with `## Security planning gate` and `**Dependency identity:**`. |
| R-AG-080 | STITCH | after agents/gsd-planner.md:484 | .ai/agents/phase-preparer.md:552-553 | Insert the ASVS trust-boundary pointer. |
| R-AG-081 | REPLACE | agents/gsd-planner.md:541 | .ai/agents/phase-preparer.md:610 | Replace REFACTOR line with the concrete refactor/omit-commit rule. |
| R-AG-082 | STITCH | after agents/gsd-planner.md:550 | .ai/agents/phase-preparer.md:620-625 | Insert `<quick_batch_mode>`. |
| R-AG-083 | REPLACE | agents/gsd-planner.md:552-563 | .ai/agents/phase-preparer.md:627-638 | Replace `--gaps`/`--reviews` flag triggers with assignment triggers. |
| R-AG-084 | REPLACE | agents/gsd-planner.md:569-584 | .ai/agents/phase-preparer.md:644-654 | Replace `init.plan-phase`/`state.load` and model fields with direct record reads. |
| R-AG-085 | REPLACE | agents/gsd-planner.md:588-597 | .ai/agents/phase-preparer.md:658-670 | Replace mode-loading block with assignment modes and bounded revision rule. |
| R-AG-086 | REPLACE | agents/gsd-planner.md:622-626 | .ai/agents/phase-preparer.md:695-697 | Replace graphify/`gsd_run` launcher graph context with supplied-map-only rule. |
| R-AG-087 | REPLACE | agents/gsd-planner.md:630-643 | .ai/agents/phase-preparer.md:701-711 | Replace ROADMAP listing/"ask which phase" with assigned-phase rule and single discovery gate. |
| R-AG-088 | REPLACE | agents/gsd-planner.md:647-693 | .ai/agents/phase-preparer.md:715-724 | Replace `history-digest` 2-4-phase selection and RETROSPECTIVE read with consumed-interface SUMMARY reads. |
| R-AG-089 | REPLACE | agents/gsd-planner.md:697 | .ai/agents/phase-preparer.md:728-730 | Replace `learnings.query` with project-record lessons. |
| R-AG-090 | REPLACE | agents/gsd-planner.md:701-716 | .ai/agents/phase-preparer.md:734-746 | Replace wildcard CONTEXT/RESEARCH/DISCOVERY cat with already-loaded inputs and conflict return. |
| R-AG-091 | REPLACE | agents/gsd-planner.md:725 | .ai/agents/phase-preparer.md:751 | Replace `TRACER_MODE` lead rule with default `type="auto"` slice. |
| R-AG-092 | REPLACE | agents/gsd-planner.md:753-761 | .ai/agents/phase-preparer.md:779-785 | Replace implicit file-overlap wave bump with depends_on/resources rule. |
| R-AG-093 | REPLACE | agents/gsd-planner.md:763-765 | .ai/agents/phase-preparer.md:787-789 | Replace external-review-before-PR-open with draft-PR delivery rule and coupling pointer. |
| R-AG-094 | REPLACE | agents/gsd-planner.md:773 | .ai/agents/phase-preparer.md:798 | Replace plan sizing line with one-outcome sizing target. |
| R-AG-095 | REPLACE | agents/gsd-planner.md:795 | .ai/agents/phase-preparer.md:820-823 | Replace budget check with task-cap/granularity/handoff-threshold bullets. |
| R-AG-096 | REPLACE | agents/gsd-planner.md:799 | .ai/agents/phase-preparer.md:827 | Replace "Auto-approve in yolo mode" with recorded-authorization rule. |
| R-AG-097 | REPLACE | agents/gsd-planner.md:811 | .ai/agents/phase-preparer.md:839 | Restrict `Edit` to assigned PLAN/VALIDATION and forbid worker ROADMAP/STATE edits. |
| R-AG-098 | REPLACE | agents/gsd-planner.md:820 | — | Keep the `tail -n 5` truncation check but delete the `verify.plan-structure` call (verb absent). |
| R-AG-099 | KEEP-UPSTREAM | agents/gsd-planner.md:827,834 | — | Keep `02.1` decimal examples; runtime has `phase.next-decimal`. |
| R-AG-100 | REPLACE | agents/gsd-planner.md:848-869 | .ai/agents/phase-preparer.md:874-887 | Replace `frontmatter.validate`/`verify.plan-structure` with the TEMPLATE-CONTRACT self-check. |
| R-AG-101 | REPLACE | agents/gsd-planner.md:872-896 | .ai/agents/phase-preparer.md:890-932 | Replace worker ROADMAP `Edit` with proposal return plus coordinator `roadmap.set-plans`/`phase.edit` instructions. |
| R-AG-102 | REPLACE | agents/gsd-planner.md:898-903 | .ai/agents/phase-preparer.md:934-938 | Replace `gsd_run query commit ... ROADMAP.md` with exact-path PLAN/VALIDATION commit. |
| R-AG-103 | REPLACE | agents/gsd-planner.md:921-922 | .ai/agents/phase-preparer.md:956-963 | Replace "No re-reads" rules with read-once/reopen-with-reason rules. |
| R-AG-104 | REPLACE | agents/gsd-planner.md:932 | .ai/agents/phase-preparer.md:973 | Replace "orchestrator dispatches on exact marker strings" with outcome-marker wording. |
| R-AG-105 | STITCH | after agents/gsd-planner.md:939 | .ai/agents/phase-preparer.md:981-994 | Insert `## PLANNING PARTIAL` return (context-limit converge with digest). |
| R-AG-106 | REPLACE | agents/gsd-planner.md:957 | .ai/agents/phase-preparer.md:1012-1013 | Clarify checkpoint is never the context limit. |
| R-AG-107 | REPLACE | agents/gsd-planner.md:976-977,985,991 | .ai/agents/phase-preparer.md:1032-1033,1041,1047 | Replace success criteria for STATE history, Level 0-3, 2-3 tasks and `security_enforcement`. |
| R-AG-108 | STITCH | after agents/gsd-planner.md:993 | .ai/agents/phase-preparer.md:1050 | Insert threat issue-link success criterion. |

Done when:
- `grep -cE "Level [0-3]|package-legitimacy|security_enforcement|tdd_mode|human_verify_mode|TRACER_MODE|MVP_MODE|WALKING_SKELETON|type=\"tracer\"" agents/planner.md` returns 0.
- `grep -cE "history-digest|learnings\.query|frontmatter\.validate|verify\.plan-structure|estimate-calibration|init\.plan-phase|state\.load" agents/planner.md` returns 0.
- `grep -c "## Discovery gate" agents/planner.md` returns 1; `grep -c "## Security planning gate" agents/planner.md` returns 1; `grep -c "Dependency identity" agents/planner.md` returns 1.
- `grep -c "## PLANNING PARTIAL" agents/planner.md` returns 1; `grep -c "roadmap.set-plans" agents/planner.md` returns 1.
- `grep -cE "^acceptance: \[\]|^documentation: \[\]|^checks: \[\]" agents/planner.md` returns 3.

### agents/plan-checker.md (from agents/gsd-plan-checker.md; local source .ai/agents/phase-checker.md)

Wording-only drift ignored (lines 11, 73, 99, 112-113, 378, 383, 597, 637, 682, 700, 705 labels).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-109 | RENAME | agents/gsd-plan-checker.md | — | Rename to `agents/plan-checker.md` with `git mv`. |
| R-AG-110 | REPLACE | agents/gsd-plan-checker.md:2-4 | .ai/agents/phase-checker.md:2-4 | Set `name: plan-checker`, description and tools with `Agent`. |
| R-AG-111 | STITCH | after agents/gsd-plan-checker.md:7 | .ai/agents/phase-checker.md:8-30 | Insert `<local_workflow>` (read-only, findings to coordinator). |
| R-AG-112 | REPLACE | agents/gsd-plan-checker.md:23,30,37,40-42 | .ai/agents/phase-checker.md:47,54,61,64-66 | Replace presumption-of-failure stance and severity definitions with evidence-based ones. |
| R-AG-113 | REPLACE | agents/gsd-plan-checker.md:53 | .ai/agents/phase-checker.md:77-79 | Replace "implements the Revision Gate" with workflow-owned revision loop. |
| R-AG-114 | REPLACE | agents/gsd-plan-checker.md:64-66 | .ai/agents/phase-checker.md:90-92 | Replace skill/AGENTS.md loading steps. |
| R-AG-115 | REPLACE | agents/gsd-plan-checker.md:78 | .ai/agents/phase-checker.md:104 | Accept `Agent Discretion`. |
| R-AG-116 | REPLACE | agents/gsd-plan-checker.md:92-93 | .ai/agents/phase-checker.md:118-119 | Route missing review incorporation to `## PLAN REVIEW` evidenced finding. |
| R-AG-117 | REPLACE | agents/gsd-plan-checker.md:205-207 | .ai/agents/phase-checker.md:231-237 | Replace wave-number arithmetic with `phase-plan-index` coordinator grouping. |
| R-AG-118 | REPLACE | agents/gsd-plan-checker.md:222-249 | .ai/agents/phase-checker.md:252-275 | Replace "ALWAYS INFO" same-wave coupling with evidence-graded race/dependency check. |
| R-AG-119 | REPLACE | agents/gsd-plan-checker.md:254-259 | .ai/agents/phase-checker.md:280-284 | Replace coupling example with blocker-dependency example. |
| R-AG-120 | REPLACE | agents/gsd-plan-checker.md:299-315 | .ai/agents/phase-checker.md:324-336 | Replace `estimate-check --calibrated` smart-zone check with context-estimate review. |
| R-AG-121 | REPLACE | agents/gsd-plan-checker.md:322-343 | .ai/agents/phase-checker.md:343-363 | Replace 4/5+ task and 15-file thresholds with configured task cap and separate-outcome rule. |
| R-AG-122 | REPLACE | agents/gsd-plan-checker.md:383 | .ai/agents/phase-checker.md:403 | Accept `Agent Discretion` in CONTEXT parsing. |
| R-AG-123 | REPLACE | agents/gsd-plan-checker.md:462 | .ai/agents/phase-checker.md:482-484 | Replace ISSUES FOUND fix path with `Verdict: needs-revision`. |
| R-AG-124 | REPLACE | agents/gsd-plan-checker.md:487-516 | .ai/agents/phase-checker.md:509-544 | Replace tier-compliance severity and example with authority-graded version. |
| R-AG-125 | STITCH | after agents/gsd-plan-checker.md:518 | .ai/agents/phase-checker.md:547-563 | Insert `## Dimension 7d: Security Planning Gate` (link `planner.md#security-planning-gate`). |
| R-AG-126 | REPLACE | agents/gsd-plan-checker.md:526-530 | .ai/agents/phase-checker.md:571-574 | Replace `{FAILING_DIRECTIONS}` probe consumption with read-and-apply failing-direction. |
| R-AG-127 | REPLACE | agents/gsd-plan-checker.md:549 | .ai/agents/phase-checker.md:593-595 | Replace data-contract severity. |
| R-AG-128 | REPLACE | agents/gsd-plan-checker.md:608 | .ai/agents/phase-checker.md:654 | Fail research resolution only for blocked dependent scope. |
| R-AG-129 | STITCH | after agents/gsd-plan-checker.md:657 | .ai/agents/phase-checker.md:704-708 | Insert pattern-compliance severity rule. |
| R-AG-130 | REPLACE | agents/gsd-plan-checker.md:660-676 | .ai/agents/phase-checker.md:711-733 | Replace pattern examples with `id`/`authority` examples. |
| R-AG-131 | KEEP-UPSTREAM | agents/gsd-plan-checker.md:698 | — | Keep read-only gate-baseline check item 4; catches pre-passing gates. |
| R-AG-132 | REPLACE | agents/gsd-plan-checker.md:702-703 | .ai/agents/phase-checker.md:758-759 | Replace `{VERIFY_PATHS}` probe with direct target inspection. |
| R-AG-133 | REPLACE | agents/gsd-plan-checker.md:707-713 | .ai/agents/phase-checker.md:763-769 | Make CONTEXT the decision authority and grade measurement conflicts. |
| R-AG-134 | REPLACE | agents/gsd-plan-checker.md:728-758 | .ai/agents/phase-checker.md:784-799 | Replace `init.phase-op`, `phase.list-*`, `roadmap.get-phase`, `estimate-check` loop with correction-review packet and direct reads. |
| R-AG-135 | REPLACE | agents/gsd-plan-checker.md:762-784 | .ai/agents/phase-checker.md:803-814 | Replace `verify.plan-structure` loop with TEMPLATE-CONTRACT inspection (optional `engineer_run query planning.review`). |
| R-AG-136 | REPLACE | agents/gsd-plan-checker.md:788-794 | .ai/agents/phase-checker.md:818 | Replace `frontmatter.get must_haves` with direct YAML read. |
| R-AG-137 | REPLACE | agents/gsd-plan-checker.md:833-853 | .ai/agents/phase-checker.md:857-862 | Replace `verify.plan-structure`/`plan.task-structure` task check with direct inspection. |
| R-AG-138 | REPLACE | agents/gsd-plan-checker.md:866 | .ai/agents/phase-checker.md:875-883 | Replace wave-consistency validation with `phase-plan-index` bullets. |
| R-AG-139 | REPLACE | agents/gsd-plan-checker.md:880-885 | .ai/agents/phase-checker.md:897-901 | Replace `plan.task-structure`/`frontmatter.get` counts and 4/5+ thresholds with configured cap. |
| R-AG-140 | REPLACE | agents/gsd-plan-checker.md:897-901 | .ai/agents/phase-checker.md:913-922 | Replace passed/issues_found status with approved/needs-revision rules. |
| R-AG-141 | REPLACE | agents/gsd-plan-checker.md:916-925 | .ai/agents/phase-checker.md:938-957 | Add `id` and `authority` to the issue schema and the universal-fields paragraph. |
| R-AG-142 | REPLACE | agents/gsd-plan-checker.md:942-957 | .ai/agents/phase-checker.md:974-1002 | Replace count-based severity definitions with evidence definitions and single-Markdown-record rule. |
| R-AG-143 | REPLACE | agents/gsd-plan-checker.md:963-1029 | .ai/agents/phase-checker.md:1008-1129 | Replace `## VERIFICATION PASSED`/`## ISSUES FOUND` returns with `## PLAN REVIEW` + `Verdict: approved\|needs-revision` templates. |
| R-AG-144 | REPLACE | agents/gsd-plan-checker.md:1042,1060,1068,1071-1073 | .ai/agents/phase-checker.md:1142,1160,1168,1171-1174 | Update anti-pattern and success criteria to task cap, approved/needs-revision and single records. |

Done when:
- `grep -cE "## VERIFICATION PASSED|## ISSUES FOUND|issues_found" agents/plan-checker.md` returns 0.
- `grep -c "## PLAN REVIEW" agents/plan-checker.md` ≥ 3; `grep -c "Verdict: needs-revision" agents/plan-checker.md` ≥ 1; `grep -c "Verdict: approved" agents/plan-checker.md` ≥ 1.
- `grep -c "## Dimension 7d: Security Planning Gate" agents/plan-checker.md` returns 1.
- `grep -cE "estimate-check|verify\.plan-structure|plan\.task-structure|frontmatter\.get|phase\.list-|init\.phase-op" agents/plan-checker.md` returns 0.

### agents/phase-researcher.md (from agents/gsd-phase-researcher.md; local source .ai/agents/researcher.md)

Wording-only drift ignored (lines 15, 63, 75, 188, 192, 865).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-145 | RENAME | agents/gsd-phase-researcher.md | — | Rename to `agents/phase-researcher.md` with `git mv`. |
| R-AG-146 | REPLACE | agents/gsd-phase-researcher.md:2-4 | .ai/agents/researcher.md:2-4 | Set `name: phase-researcher`, consumer `planner`, tools with `Agent`. |
| R-AG-147 | STITCH | after agents/gsd-phase-researcher.md:13 | .ai/agents/researcher.md:14-36 | Insert `<local_workflow>` (RESEARCH cannot lock scope; return unresolved choices). |
| R-AG-148 | REPLACE | agents/gsd-phase-researcher.md:17 | .ai/agents/researcher.md:41 | Replace `--research-phase` spawn with coordinator assignment. |
| R-AG-149 | REPLACE | agents/gsd-phase-researcher.md:33 | .ai/agents/researcher.md:57 | Replace `gsd-tools query package-legitimacy check` provenance requirement with registry identity cross-check. |
| R-AG-150 | REPLACE | agents/gsd-phase-researcher.md:95-167 | .ai/agents/researcher.md:123-158 | Replace the research-plan seam (resolver blob 121, `research-plan`, `websearch`, `research-store`) with the Bounded Research Plan Steps A-D. |
| R-AG-151 | STITCH | after agents/gsd-phase-researcher.md:167 | .ai/agents/researcher.md:160-205 | Insert `<context_limit>` "converge, do not halt" block. |
| R-AG-152 | REPLACE | agents/gsd-phase-researcher.md:171-179 | .ai/agents/researcher.md:209-213 | Replace `classify-confidence` seam with evidence-based confidence tiers. |
| R-AG-153 | REPLACE | agents/gsd-phase-researcher.md:202 | .ai/agents/researcher.md:237 | Replace `security_enforcement: false` check item with scope rationale. |
| R-AG-154 | REPLACE | agents/gsd-phase-researcher.md:214-235 | .ai/agents/researcher.md:249-265 | Replace `package-legitimacy check` SLOP/SUS/OK verdicts with manual CONFIRMED/UNRESOLVED/REJECTED identity procedure. |
| R-AG-155 | REPLACE | agents/gsd-phase-researcher.md:253,262 | .ai/agents/researcher.md:283,292 | Replace "~9% rate" and seam-rated `[SUS]` with local wording. |
| R-AG-156 | REPLACE | agents/gsd-phase-researcher.md:327-334 | .ai/agents/researcher.md:357-364 | Replace audit table dispositions with CONFIRMED/REJECTED/UNRESOLVED rows. |
| R-AG-157 | STITCH | after agents/gsd-phase-researcher.md:438 | .ai/agents/researcher.md:469-479 | Insert `## Not Yet Researched` template section. |
| R-AG-158 | REPLACE | agents/gsd-phase-researcher.md:455,484 | .ai/agents/researcher.md:496,525 | Replace `nyquist_validation`/`security_enforcement` toggles with assignment scope. |
| R-AG-159 | STITCH | after agents/gsd-phase-researcher.md:521 | .ai/agents/researcher.md:563 | Insert `**Coverage:** [complete \| partial (context limit)]`. |
| R-AG-160 | REPLACE | agents/gsd-phase-researcher.md:538-546 | .ai/agents/researcher.md:580-586 | Replace `init.phase-op` and `config.json` toggle with direct assigned reads of `.planning/config.yaml`. |
| R-AG-161 | REPLACE | agents/gsd-phase-researcher.md:567-608 | .ai/agents/researcher.md:607-614 | Replace Step 1.3 `graphify` graph context with repository tracing. |
| R-AG-162 | REPLACE | agents/gsd-phase-researcher.md:661 | .ai/agents/researcher.md:667 | Require only inventory-needed migration/code-edit tasks. |
| R-AG-163 | STITCH | after agents/gsd-phase-researcher.md:728 | .ai/agents/researcher.md:735-743 | Insert Step 2.9 (open RESEARCH.md early). |
| R-AG-164 | REPLACE | agents/gsd-phase-researcher.md:731-735 | .ai/agents/researcher.md:746-750 | Replace seam-driven domain loop and nyquist skip with bounded steps. |
| R-AG-165 | REPLACE | agents/gsd-phase-researcher.md:756,762,804 | .ai/agents/researcher.md:771,777,819 | Replace `commit_docs` notes with assignment write scope and draft-finishing rule. |
| R-AG-166 | REPLACE | agents/gsd-phase-researcher.md:806-810 | .ai/agents/researcher.md:821-826 | Replace `gsd_run query commit` with exact-path `git add --`/`git commit`. |
| R-AG-167 | STITCH | after agents/gsd-phase-researcher.md:845 | .ai/agents/researcher.md:862-889 | Insert `## RESEARCH PARTIAL` return. |
| R-AG-168 | STITCH | after agents/gsd-phase-researcher.md:847 | .ai/agents/researcher.md:892-898 | Insert BLOCKED-is-never-the-context-limit rule. |
| R-AG-169 | REPLACE | agents/gsd-phase-researcher.md:888 | .ai/agents/researcher.md:939 | Replace seam success criterion. |
| R-AG-170 | STITCH | after agents/gsd-phase-researcher.md:893 | .ai/agents/researcher.md:945-950 | Insert context-limit success criteria. |

Done when:
- `grep -cE "research-plan|research-store|classify-confidence|package-legitimacy|graphify|websearch|nyquist_validation|security_enforcement|init\.phase-op" agents/phase-researcher.md` returns 0.
- `grep -c "<context_limit>" agents/phase-researcher.md` returns 1; `grep -c "## RESEARCH PARTIAL" agents/phase-researcher.md` ≥ 2; `grep -c "## Not Yet Researched" agents/phase-researcher.md` ≥ 2.
- `grep -c "converge, do not halt" agents/phase-researcher.md` returns 1.

### agents/verifier.md (from agents/gsd-verifier.md; local source .ai/agents/verifier.md)

Wording-only drift ignored (lines 302, 613, 863, 871, 882, 884).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-171 | RENAME | agents/gsd-verifier.md | — | Rename to `agents/verifier.md` with `git mv`. |
| R-AG-172 | REPLACE | agents/gsd-verifier.md:2-4 | .ai/agents/verifier.md:2-4 | Set `name: verifier`, report-returning description, tools with `Agent`. |
| R-AG-173 | STITCH | after agents/gsd-verifier.md:13 | .ai/agents/verifier.md:14-51 | Insert `<local_workflow>` (read-only, provisional assessment until joined results, report for host capture). |
| R-AG-174 | REPLACE | agents/gsd-verifier.md:37-38 | .ai/agents/verifier.md:76-77 | Classify missing required connections as FAILED, not WARNING. |
| R-AG-175 | REPLACE | agents/gsd-verifier.md:77-87 | .ai/agents/verifier.md:117-120 | Delete the Resolver Bootstrap block and keep the few-shot and thinking-model pointers. |
| R-AG-176 | REPLACE | agents/gsd-verifier.md:102-104 | .ai/agents/verifier.md:135-137 | Replace re-verification shortcut with revision-applicable reuse. |
| R-AG-177 | REPLACE | agents/gsd-verifier.md:110-117 | .ai/agents/verifier.md:143-148 | Replace `ls`/`roadmap.get-phase` load with direct reads and HEAD==assigned revision check. |
| R-AG-178 | STITCH | after agents/gsd-verifier.md:120 | .ai/agents/verifier.md:152-160 | Insert canonical threat tracking and Issue-link audit bullets. |
| R-AG-179 | REPLACE | agents/gsd-verifier.md:127-131 | .ai/agents/verifier.md:167-169 | Replace `roadmap.get-phase --raw` with direct ROADMAP read plus CONTEXT acceptance. |
| R-AG-180 | REPLACE | agents/gsd-verifier.md:159-164 | .ai/agents/verifier.md:197-204 | Replace ADR-550 prohibition tiers (`dispositionForProhibition()`, autonomous soft-gate) with local negative-constraint rule. |
| R-AG-181 | REPLACE | agents/gsd-verifier.md:170,175,189 | .ai/agents/verifier.md:210,215,229-236 | Start from CONTEXT acceptance and consume specialist receipts. |
| R-AG-182 | REPLACE | agents/gsd-verifier.md:209-211 | .ai/agents/verifier.md:256-258 | Replace override-as-PASSED with recorded human decision still needing evidence. |
| R-AG-183 | REPLACE | agents/gsd-verifier.md:216-246 | .ai/agents/verifier.md:263 | Replace inline 80%-token override matching with the verification-overrides method pointer. |
| R-AG-184 | REPLACE | agents/gsd-verifier.md:250-273 | .ai/agents/verifier.md:267-275 | Replace `verify.artifacts` with source/specialist artifact accounting. |
| R-AG-185 | REPLACE | agents/gsd-verifier.md:326-341 | .ai/agents/verifier.md:328-343 | Replace `verify.key-links` with evidence-based WIRED/PARTIAL/NOT_WIRED tracing. |
| R-AG-186 | REPLACE | agents/gsd-verifier.md:385-402 | .ai/agents/verifier.md:387-397 | Replace `summary-extract`/`verify.commits` with `git show --stat`/`git diff --name-status`. |
| R-AG-187 | REPLACE | agents/gsd-verifier.md:422-426 | .ai/agents/verifier.md:417-426 | Replace debt-marker, re-verification evidence gate and category definitions. |
| R-AG-188 | STITCH | after agents/gsd-verifier.md:431 | .ai/agents/verifier.md:432-438 | Insert Shared-evidence (receipt) rule. |
| R-AG-189 | REPLACE | agents/gsd-verifier.md:460 | .ai/agents/verifier.md:467-470 | Establish behavior checks from matching receipts first. |
| R-AG-190 | STITCH | after agents/gsd-verifier.md:483 | .ai/agents/verifier.md:494-498 | Insert Shared-receipt exception. |
| R-AG-191 | REPLACE | agents/gsd-verifier.md:500-506 | .ai/agents/verifier.md:515-524 | Replace `gsd_run run-with-timeout` probe loop with receipt-first bounded `subprocess.run`. |
| R-AG-192 | STITCH | after agents/gsd-verifier.md:518 | .ai/agents/verifier.md:537-545 | Insert SUMMARY deterministic coverage contract paragraph. |
| R-AG-193 | REPLACE | agents/gsd-verifier.md:521-539 | .ai/agents/verifier.md:548-576 | Replace human-verification triggers, `human_verify_mode` harvest and UAT sink with local UAT authoring contract. |
| R-AG-194 | REPLACE | agents/gsd-verifier.md:553 | .ai/agents/verifier.md:590 | Include required key link PARTIAL in gaps rule. |
| R-AG-195 | REPLACE | agents/gsd-verifier.md:567 | .ai/agents/verifier.md:604 | Replace `verification.status` seam note with local status contract. |
| R-AG-196 | REPLACE | agents/gsd-verifier.md:571-572 | .ai/agents/verifier.md:608-609 | Replace score counting (no PASSED-override). |
| R-AG-197 | REPLACE | agents/gsd-verifier.md:588-598 | .ai/agents/verifier.md:625-632 | Replace `roadmap.analyze --raw` deferral with direct ROADMAP read and explicit-later-assignment rule. |
| R-AG-198 | REPLACE | agents/gsd-verifier.md:652-671 | .ai/agents/verifier.md:686-695 | Replace MVP mode/`user-story.validate`/`/gsd:mvp-phase` with assignment-requested user-flow method. |
| R-AG-199 | REPLACE | agents/gsd-verifier.md:679-683 | .ai/agents/verifier.md:703-713 | Replace Write VERIFICATION.md and `verification.fingerprint` with return-for-host-capture and `covered_files` rule. |
| R-AG-200 | REPLACE | agents/gsd-verifier.md:692-694 | .ai/agents/verifier.md:722-724 | Replace `covered_digest` with `revision` and redefine `overrides_applied`. |
| R-AG-201 | STITCH | after agents/gsd-verifier.md:746 | .ai/agents/verifier.md:777-792 | Insert Acceptance, Integration, Documentation, Findings report sections. |
| R-AG-202 | REMOVE | agents/gsd-verifier.md:827-840 | .ai/agents/verifier.md:872-874 | Delete the `## Self-check the written status` section (`verification.status` read-back); keep the closing fence on line 826. |
| R-AG-203 | REPLACE | agents/gsd-verifier.md:886-888 | .ai/agents/verifier.md:919-924 | Replace "flag when uncertain" and "use grep, not running the app" rules. |
| R-AG-204 | REPLACE | agents/gsd-verifier.md:965 | .ai/agents/verifier.md:1001 | Replace fingerprint success criterion with exact-revision criterion. |

Done when:
- `grep -cE "verify\.(artifacts|key-links|commits)|summary-extract|run-with-timeout|roadmap\.(analyze|get-phase)|user-story\.validate|verification\.(fingerprint|status)|covered_digest|Resolver Bootstrap" agents/verifier.md` returns 0.
- `grep -cE "^## (Acceptance|Integration|Documentation|Findings)$" agents/verifier.md` returns 4.
- `grep -c "provisional" agents/verifier.md` ≥ 1; `grep -c "Create .\.planning/phases/{phase_dir}" agents/verifier.md` returns 0.

### agents/code-reviewer.md (from agents/gsd-code-reviewer.md; local source .ai/agents/code-reviewer.md)

Wording-only drift ignored (lines 149, 157 tags, 358).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-205 | RENAME | agents/gsd-code-reviewer.md | — | Rename to `agents/code-reviewer.md` with `git mv`. |
| R-AG-206 | REPLACE | agents/gsd-code-reviewer.md:2-4 | .ai/agents/code-reviewer.md:2-4 | Set `name: code-reviewer`, findings description, tools with `Agent`. |
| R-AG-207 | STITCH | after agents/gsd-code-reviewer.md:9 | .ai/agents/code-reviewer.md:10-38 | Insert `<local_workflow>` (read-only, report for host capture, bounded-correction routing). |
| R-AG-208 | REPLACE | agents/gsd-code-reviewer.md:13 | .ai/agents/code-reviewer.md:43 | Replace "produce REVIEW.md in the phase directory" with external capture. |
| R-AG-209 | REPLACE | agents/gsd-code-reviewer.md:18 | .ai/agents/code-reviewer.md:48 | Treat `<structural_findings>` as evidence candidates, not ground truth. |
| R-AG-210 | REPLACE | agents/gsd-code-reviewer.md:32-33 | .ai/agents/code-reviewer.md:62-64 | Replace severity definitions (demonstrated defect = BLOCKER; add INFO). |
| R-AG-211 | REPLACE | agents/gsd-code-reviewer.md:108-109 | .ai/agents/code-reviewer.md:139-140 | Make `review_path` an external destination; never derive from `phase_dir`. |
| R-AG-212 | REPLACE | agents/gsd-code-reviewer.md:128-141 | .ai/agents/code-reviewer.md:159-169 | Replace `gsd_run check evaluation-scope` with `diff_base`-or-fail and filtered `git diff --name-only`. |
| R-AG-213 | REPLACE | agents/gsd-code-reviewer.md:157 | .ai/agents/code-reviewer.md:186 | File verified external claims under their severity section, not Narrative Findings. |
| R-AG-214 | REPLACE | agents/gsd-code-reviewer.md:177 | .ai/agents/code-reviewer.md:206 | Replace "Review generically" with inputs/outputs/error-path inspection. |
| R-AG-215 | REPLACE | agents/gsd-code-reviewer.md:179-190 | .ai/agents/code-reviewer.md:208-219 | Replace "create REVIEW.md" empty-exit with returned `status: skipped` report. |
| R-AG-216 | REPLACE | agents/gsd-code-reviewer.md:212,249 | .ai/agents/code-reviewer.md:241,278 | Classify demonstrated empty-catch/logic defects as Critical. |
| R-AG-217 | REPLACE | agents/gsd-code-reviewer.md:273 | .ai/agents/code-reviewer.md:302-304 | Replace "Create REVIEW.md at review_path" with return-complete-report step. |
| R-AG-218 | REPLACE | agents/gsd-code-reviewer.md:290-302 | .ai/agents/code-reviewer.md:321-336 | Add `skipped` status, count rules, Summary/Critical/Warnings headings, `critical` only (no `blocker:`), exact `files_reviewed_list`. |
| R-AG-219 | STITCH | after agents/gsd-code-reviewer.md:313 | .ai/agents/code-reviewer.md:348-355 | Insert Structural Findings and Narrative Findings template sections. |
| R-AG-220 | REPLACE | agents/gsd-code-reviewer.md:318-337 | .ai/agents/code-reviewer.md:360-379 | Always include Summary/Critical/Warnings with `None`. |
| R-AG-221 | REPLACE | agents/gsd-code-reviewer.md:369-371 | .ai/agents/code-reviewer.md:411-413 | Replace "ALWAYS use Write to create REVIEW.md" with host capture / assigned external path only. |

Done when:
- `grep -cE "evaluation-scope|\{phase_dir\}/\{phase\}-REVIEW\.md|ground truth" agents/code-reviewer.md` returns 0.
- `grep -c "status: clean | issues_found | skipped" agents/code-reviewer.md` returns 1.
- `grep -c "bounded-correction-dispatch" agents/code-reviewer.md` returns 1.

### agents/debugger.md (from agents/gsd-debugger.md; local source .ai/agents/debugger.md)

Wording-only drift ignored (lines 15, 686, 1129).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-222 | RENAME | agents/gsd-debugger.md | — | Rename to `agents/debugger.md` with `git mv`. |
| R-AG-223 | REPLACE | agents/gsd-debugger.md:2-4 | .ai/agents/debugger.md:2-4 | Set `name: debugger`, spawned-by `next / verify-work`, tools with `Agent`. |
| R-AG-224 | STITCH | after agents/gsd-debugger.md:13 | .ai/agents/debugger.md:14-35 | Insert `<local_workflow>` (read-only unless record path assigned; bounded fix proposal; no stash/reset/merge). |
| R-AG-225 | REPLACE | agents/gsd-debugger.md:19-20 | .ai/agents/debugger.md:42-43 | Replace `/gsd:debug` and `diagnose-issues` spawners with coordinator assignment. |
| R-AG-226 | REPLACE | agents/gsd-debugger.md:39-40 | .ai/agents/debugger.md:62-64 | Replace project-skills-discovery include with rule catalog plus skills. |
| R-AG-227 | REPLACE | agents/gsd-debugger.md:591 | .ai/agents/debugger.md:615 | Replace MemPalace semantic-first recall with local KB recall. |
| R-AG-228 | REPLACE | agents/gsd-debugger.md:700-717 | .ai/agents/debugger.md:724-729 | Replace active-session listing/`$ARGUMENTS` prompt with assigned-record resume. |
| R-AG-229 | REPLACE | agents/gsd-debugger.md:721-729 | .ai/agents/debugger.md:733-743 | Replace "Create debug file IMMEDIATELY"/`mkdir -p .planning/debug` with assigned-path-only creation. |
| R-AG-230 | REPLACE | agents/gsd-debugger.md:755 | .ai/agents/debugger.md:772 | Replace MemPalace query with KB read. |
| R-AG-231 | REPLACE | agents/gsd-debugger.md:808 | .ai/agents/debugger.md:825 | Replace "/clear - run /gsd:debug" with continuation handoff. |
| R-AG-232 | REPLACE | agents/gsd-debugger.md:904-908 | .ai/agents/debugger.md:921-931 | Add `guardrail_verdict: incomplete` and outcome-confirmation-not-permission rule. |
| R-AG-233 | REPLACE | agents/gsd-debugger.md:947-1022 | .ai/agents/debugger.md:970-992 | Replace archive `mv`, `state.load` resolver blob, `gsd_run query commit` debug/KB commits and MemPalace indexing with proposed-KB-entry return to coordinator. |
| R-AG-234 | REPLACE | agents/gsd-debugger.md:1149,1153 | .ai/agents/debugger.md:1119,1123 | Replace human-only resolution gate wording. |
| R-AG-235 | REPLACE | agents/gsd-debugger.md:1225-1236 | .ai/agents/debugger.md:1195-1206 | Restrict `find_and_fix` to authorized repair and coordinator archival. |
| R-AG-236 | REPLACE | agents/gsd-debugger.md:1270,1275 | .ai/agents/debugger.md:1240,1245 | Replace debug-file and `/clear` success criteria. |

Done when:
- `grep -ciE "mempalace" agents/debugger.md` returns 0; `grep -cE "mkdir -p \.planning/debug|mv \.planning/debug|state\.load|query commit" agents/debugger.md` returns 0.
- `grep -c "bounded-correction-dispatch" agents/debugger.md` returns 1; `grep -c "guardrail_verdict: incomplete" agents/debugger.md` returns 1.

### agents/doc-writer.md (from agents/gsd-doc-writer.md; local source .ai/agents/doc-writer.md)

Wording-only drift ignored (lines 15, 439, 562).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-237 | RENAME | agents/gsd-doc-writer.md | — | Rename to `agents/doc-writer.md` with `git mv`. |
| R-AG-238 | REPLACE | agents/gsd-doc-writer.md:2,4 | .ai/agents/doc-writer.md:2,4 | Set `name: doc-writer`, tools with `Agent`. |
| R-AG-239 | STITCH | after agents/gsd-doc-writer.md:13 | .ai/agents/doc-writer.md:14-72 | Insert `<local_workflow>` with Runtime documentation assignment and fix-mode routing. |
| R-AG-240 | REPLACE | agents/gsd-doc-writer.md:17-27 | .ai/agents/doc-writer.md:77-87 | Replace `/gsd:docs-update` spawn and docs-init JSON with optional XML plus committed SUMMARY return. |
| R-AG-241 | REPLACE | agents/gsd-doc-writer.md:32 | .ai/agents/doc-writer.md:92 | Replace SECURITY note with ownership-bounded fields and conflict reporting. |
| R-AG-242 | REPLACE | agents/gsd-doc-writer.md:57,70,86,103,624 | .ai/agents/doc-writer.md:117,130,146,163,671 | Rename marker to `<!-- generated-by: doc-writer -->`. |
| R-AG-243 | KEEP-UPSTREAM | agents/gsd-doc-writer.md:123-128,200-205,219-220,487-490,617-618 | — | Keep rules 10/11 (no standalone run mode; verify Makefile inputs); prevents fabricated run steps. |
| R-AG-244 | REPLACE | agents/gsd-doc-writer.md:608-610,616 | .ai/agents/doc-writer.md:657-659,665 | Replace "NEVER include GSD methodology" and "NEVER touch CHANGELOG (/gsd:ship)" with target-project and assigned-changelog rules. |
| R-AG-245 | REPLACE | agents/gsd-doc-writer.md:626 | .ai/agents/doc-writer.md:673 | Replace methodology success criterion. |

Done when:
- `grep -c "generated-by: gsd-doc-writer" agents/doc-writer.md` returns 0; `grep -c "generated-by: doc-writer" agents/doc-writer.md` ≥ 5.
- `grep -c "## Runtime documentation assignment" agents/doc-writer.md` returns 1; `grep -c "no standalone run mode" agents/doc-writer.md` ≥ 3.

### agents/doc-verifier.md (from agents/gsd-doc-verifier.md; local source .ai/agents/doc-verifier.md)

Wording-only drift ignored.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-246 | RENAME | agents/gsd-doc-verifier.md | — | Rename to `agents/doc-verifier.md` with `git mv`. |
| R-AG-247 | REPLACE | agents/gsd-doc-verifier.md:2,4 | .ai/agents/doc-verifier.md:2,4 | Set `name: doc-verifier`, tools with `Agent`. |
| R-AG-248 | STITCH | after agents/gsd-doc-verifier.md:13 | .ai/agents/doc-verifier.md:14-37 | Insert `<local_workflow>` (read-only, host capture, revision, no `.planning/tmp`). |
| R-AG-249 | REPLACE | agents/gsd-doc-verifier.md:17-22 | .ai/agents/doc-verifier.md:42-46 | Drop the in-checkout `result_path` input and return JSON for host capture. |
| R-AG-250 | REPLACE | agents/gsd-doc-verifier.md:40 | .ai/agents/doc-verifier.md:64 | Split partial claims into FAIL/UNVERIFIABLE subclaims. |
| R-AG-251 | REPLACE | agents/gsd-doc-verifier.md:71-77 | .ai/agents/doc-verifier.md:95-101 | Add python/py/pwsh command claims and inspect-don't-execute rule. |
| R-AG-252 | REPLACE | agents/gsd-doc-verifier.md:85,92,97 | .ai/agents/doc-verifier.md:109,116,121 | Require route/definition/manifest inspection, not grep hits. |
| R-AG-253 | REPLACE | agents/gsd-doc-verifier.md:103 | .ai/agents/doc-verifier.md:127 | Retain VERIFY-marker claims as unverifiable. |
| R-AG-254 | REPLACE | agents/gsd-doc-verifier.md:116-119 | .ai/agents/doc-verifier.md:140-143 | Return full schema for missing file (`claims_checked: 1`, revision) and non-Node manifests. |
| R-AG-255 | REPLACE | agents/gsd-doc-verifier.md:131-147 | .ai/agents/doc-verifier.md:155-172 | Replace check methods, counts and "Write result JSON to result_path" with exact-path inspection, unverifiable counts and Return step. |
| R-AG-256 | REPLACE | agents/gsd-doc-verifier.md:153-158 | .ai/agents/doc-verifier.md:178-186 | Add `revision`, `claims_unverifiable`, `unverifiable` to the JSON shape. |
| R-AG-257 | REPLACE | agents/gsd-doc-verifier.md:179-194 | .ai/agents/doc-verifier.md:207-222 | Replace `verify_assignment.doc_path` and written-to-result_path confirmation. |
| R-AG-258 | REPLACE | agents/gsd-doc-verifier.md:200-205 | .ai/agents/doc-verifier.md:228-233 | Replace existence-only command rule, write-JSON rule and SKIP-excluded counting with UNVERIFIABLE. |
| R-AG-259 | REPLACE | agents/gsd-doc-verifier.md:213-214 | .ai/agents/doc-verifier.md:241-242 | Replace success criteria with host-capture return. |

Done when:
- `grep -cE "result_path|SKIP" agents/doc-verifier.md` returns 0.
- `grep -c "claims_unverifiable" agents/doc-verifier.md` ≥ 2; `grep -c "\"revision\"" agents/doc-verifier.md` returns 1.

### agents/integration-checker.md (from agents/gsd-integration-checker.md; local source .ai/agents/integration-checker.md)

Wording-only drift ignored (line 97 tag).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-260 | RENAME | agents/gsd-integration-checker.md | — | Rename to `agents/integration-checker.md` with `git mv`. |
| R-AG-261 | REPLACE | agents/gsd-integration-checker.md:2,4 | .ai/agents/integration-checker.md:2,4 | Set `name: integration-checker`, tools with `Agent`. |
| R-AG-262 | STITCH | after agents/gsd-integration-checker.md:7 | .ai/agents/integration-checker.md:8-31 | Insert `<local_workflow>` (read-only, component-boundary use, grep counts never prove flow). |
| R-AG-263 | REPLACE | agents/gsd-integration-checker.md:31-32 | .ai/agents/integration-checker.md:56-57 | Add UNVERIFIED status and blocker for broken error/empty handling. |
| R-AG-264 | REPLACE | agents/gsd-integration-checker.md:62,83,349,392,458,474 | .ai/agents/integration-checker.md:87,108,374,417,483,499 | Replace "milestone auditor" consumer with coordinator. |
| R-AG-265 | REPLACE | agents/gsd-integration-checker.md:440 | .ai/agents/integration-checker.md:465 | Add `UNVERIFIED` to the requirement-integration status column. |

Done when:
- `grep -c "milestone auditor" agents/integration-checker.md` returns 0; `grep -c "UNVERIFIED" agents/integration-checker.md` ≥ 2.

### agents/codebase-mapper.md (from agents/gsd-codebase-mapper.md; local source .ai/agents/codebase-mapper.md)

Wording-only drift ignored (lines 15, 43-56).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-266 | RENAME | agents/gsd-codebase-mapper.md | — | Rename to `agents/codebase-mapper.md` with `git mv`. |
| R-AG-267 | REPLACE | agents/gsd-codebase-mapper.md:2-4 | .ai/agents/codebase-mapper.md:2-4 | Set `name: codebase-mapper`, onboarding/research description, tools with `Agent`. |
| R-AG-268 | STITCH | after agents/gsd-codebase-mapper.md:13 | .ai/agents/codebase-mapper.md:14-37 | Insert `<local_workflow>` (assigned `.planning/codebase/` paths, commit the map). |
| R-AG-269 | REPLACE | agents/gsd-codebase-mapper.md:17 | .ai/agents/codebase-mapper.md:42 | Replace `/gsd:map-codebase` spawner with `onboard`/coordinator. |
| R-AG-270 | REPLACE | agents/gsd-codebase-mapper.md:107-109 | .ai/agents/codebase-mapper.md:132-134 | Replace drift-gate `--paths` note and whole-repo fallback with strict path validation (Windows/UNC/globs) and no fallback. |
| R-AG-271 | REPLACE | agents/gsd-codebase-mapper.md:844 | .ai/agents/codebase-mapper.md:869 | Replace "DO NOT COMMIT" with "Commit assigned mapping documents before returning". |

Done when:
- `grep -c "DO NOT COMMIT" agents/codebase-mapper.md` returns 0; `grep -c "Commit assigned mapping documents" agents/codebase-mapper.md` returns 1.
- `grep -c "fall back to the default whole-repo scan" agents/codebase-mapper.md` returns 0.

### agents/ui-researcher.md (from agents/gsd-ui-researcher.md; feature agent, no local counterpart)

Template: artifact-writer conventions from `.ai/agents/researcher.md:14-36` and `.ai/references/worker-handoff.md:99-108`.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-272 | RENAME | agents/gsd-ui-researcher.md | — | Rename to `agents/ui-researcher.md` with `git mv`. |
| R-AG-273 | REPLACE | agents/gsd-ui-researcher.md:2-4 | .ai/agents/researcher.md:4 | Set `name: ui-researcher`, spawner `ui-phase`, prepend `Agent` to tools. |
| R-AG-274 | STITCH | after agents/gsd-ui-researcher.md:12 | .ai/agents/researcher.md:14-36 | Insert a `<local_workflow>` adapted from researcher's (write only assigned UI-SPEC path and commit; CONTEXT owns decisions). |
| R-AG-275 | STITCH | after agents/gsd-ui-researcher.md:20 | .ai/agents/coder.md:45 | Insert `@engineer/references/worker-handoff.md`. |
| R-AG-276 | REPLACE | agents/gsd-ui-researcher.md:40-48 | .ai/agents/coder.md:74,81; .ai/agents/code-reviewer.md:77,79 | Apply AGENTS.md, inline skill self-load and skill-selection lines. |
| R-AG-277 | REPLACE | agents/gsd-ui-researcher.md:60 | .ai/agents/phase-preparer.md:93 | Accept `Agent Discretion`. |
| R-AG-278 | REPLACE | agents/gsd-ui-researcher.md:305-317 | .ai/references/scout-dispatch.md:10,25 | Route the unknown-location `find`/`grep` UI inventory to one discovery scout; keep the `ls` config check. |
| R-AG-279 | REPLACE | agents/gsd-ui-researcher.md:288-290 | .ai/agents/researcher.md:771,819 | Replace `commit_docs` notes with assignment write scope. |
| R-AG-280 | REPLACE | agents/gsd-ui-researcher.md:337 | — | Read template from `engineer/templates/UI-SPEC.md`. |
| R-AG-281 | REPLACE | agents/gsd-ui-researcher.md:354-359 | .ai/agents/researcher.md:821-826 | Replace the resolver blob and `gsd_run query commit` with exact-path `git add -- <UI-SPEC>` and `git commit`. |
| R-AG-282 | STITCH | after agents/gsd-ui-researcher.md:363 | .ai/references/worker-handoff.md:99-108 | Insert artifact-role context-limit rule (write partial UI-SPEC, name gaps, return partial, digest via `engineer_run query handoff.write`). |

Done when:
- `grep -cE "gsd_run|_GSD_SHIM|commit_docs|~/.claude" agents/ui-researcher.md` returns 0; `grep -c "<local_workflow>" agents/ui-researcher.md` returns 1.

### agents/ui-checker.md (from agents/gsd-ui-checker.md; feature agent, no local counterpart)

Template: read-only reviewer from `.ai/agents/phase-checker.md:8-30`. Already read-only (tools 4, rules 391-392): no write conflicts.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-283 | RENAME | agents/gsd-ui-checker.md | — | Rename to `agents/ui-checker.md` with `git mv`. |
| R-AG-284 | REPLACE | agents/gsd-ui-checker.md:2-4 | .ai/agents/phase-checker.md:4 | Set `name: ui-checker`, spawner `ui-phase`, prepend `Agent` to tools. |
| R-AG-285 | STITCH | after agents/gsd-ui-checker.md:6 | .ai/agents/phase-checker.md:8-30 | Insert an adapted `<local_workflow>` (read-only verdict to coordinator; scout only for named packets). |
| R-AG-286 | REPLACE | agents/gsd-ui-checker.md:11 | — | Replace `gsd-ui-researcher` with `ui-researcher`. |
| R-AG-287 | REPLACE | agents/gsd-ui-checker.md:61-69 | .ai/agents/coder.md:74,81; .ai/agents/code-reviewer.md:77,79 | Apply AGENTS.md, inline skill self-load and skill-selection lines. |
| R-AG-288 | STITCH | after agents/gsd-ui-checker.md:394 | .ai/references/worker-handoff.md:110-112 | Insert reviewer context-limit rule (report examined scope, name unreached scope, return). |

Done when:
- `grep -cE "gsd-ui-researcher|/gsd:|~/.claude" agents/ui-checker.md` returns 0; `grep -c "<local_workflow>" agents/ui-checker.md` returns 1.

### agents/ui-auditor.md (from agents/gsd-ui-auditor.md; feature agent, no local counterpart)

Template: read-only host-capture reviewer from `.ai/agents/doc-verifier.md:14-37` and `.ai/references/agent-adaptation.md:25-26`.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-289 | RENAME | agents/gsd-ui-auditor.md | — | Rename to `agents/ui-auditor.md` with `git mv`. |
| R-AG-290 | REPLACE | agents/gsd-ui-auditor.md:2-4 | .ai/agents/doc-verifier.md:4 | Set `name: ui-auditor`, spawner `ui-review`, tools `Agent, Read, Bash, Grep, Glob, Skill` (drop `Write`). |
| R-AG-291 | STITCH | after agents/gsd-ui-auditor.md:12 | .ai/agents/doc-verifier.md:14-37 | Insert an adapted `<local_workflow>` (read-only checkout; return UI-REVIEW for host capture; captures only under coordinator-assigned external path). |
| R-AG-292 | REPLACE | agents/gsd-ui-auditor.md:27 | — | Change "Write UI-REVIEW.md" to "Return UI-REVIEW.md content for host capture". |
| R-AG-293 | REPLACE | agents/gsd-ui-auditor.md:49-56 | .ai/agents/coder.md:74,81; .ai/agents/code-reviewer.md:79 | Apply AGENTS.md, inline skill self-load and AGENTS.md read lines. |
| R-AG-294 | REPLACE | agents/gsd-ui-auditor.md:77-97 | .ai/agents/doc-verifier.md:36 (host-capture rule) | Replace the `.planning/ui-reviews/.gitignore` gate with "require an assigned external `capture_dir` outside the checkout; skip captures when absent". |
| R-AG-295 | REPLACE | agents/gsd-ui-auditor.md:114-115 | — | Set `SCREENSHOT_DIR` to the assigned external `capture_dir`, not `.planning/ui-reviews`. |
| R-AG-296 | KEEP-UPSTREAM | agents/gsd-ui-auditor.md:138-268 | — | Keep interaction capture; INTERACTION_DIR inherits external SCREENSHOT_DIR. |
| R-AG-297 | REPLACE | agents/gsd-ui-auditor.md:419-421 | .ai/agents/code-reviewer.md:411-413 | Replace "Write to `$PHASE_DIR/...-UI-REVIEW.md`" with return-for-host-capture. |
| R-AG-298 | REPLACE | agents/gsd-ui-auditor.md:519-521,555 | — | Replace Step 7 write and return path with returned report and external capture path. |
| R-AG-299 | REPLACE | agents/gsd-ui-auditor.md:569,576 | — | Replace .gitignore-gate and UI-REVIEW-written criteria with capture-outside-checkout and report-returned criteria. |

Done when:
- `grep -cE ".planning/ui-reviews|Write to: " agents/ui-auditor.md` returns 0; `grep -c "^tools:.*Write" agents/ui-auditor.md` returns 0.

### agents/dom-verifier.md (from agents/gsd-dom-verifier.md; feature agent, no local counterpart)

Template: read-only host-capture reviewer from `.ai/agents/doc-verifier.md:14-37`. No Bash (line 45), so no Git/runtime conflicts.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-300 | RENAME | agents/gsd-dom-verifier.md | — | Rename to `agents/dom-verifier.md` with `git mv`. |
| R-AG-301 | REPLACE | agents/gsd-dom-verifier.md:2-11 | — | Set `name: dom-verifier`, description "returns DOM-VERIFY report", tools `Agent, Read, Glob, Grep, mcp__chrome-devtools__*, mcp__claude-in-chrome__*` and delete the `Write` echo hook comment. |
| R-AG-302 | STITCH | after agents/gsd-dom-verifier.md:12 | .ai/agents/doc-verifier.md:14-37 | Insert an adapted `<local_workflow>` (read-only; return DOM-VERIFY for host capture). |
| R-AG-303 | REPLACE | agents/gsd-dom-verifier.md:18-19 | — | Replace `workflow.live_dom_uat` hook spawn with coordinator assignment during verify-work. |
| R-AG-304 | REPLACE | agents/gsd-dom-verifier.md:48-55 | .ai/agents/doc-verifier.md:36 | Replace "Write is the only way DOM-VERIFY.md can be produced" and phase-dir write with return-for-host-capture. |
| R-AG-305 | REPLACE | agents/gsd-dom-verifier.md:117 | — | Replace "Write `{phase_dir}/{phase_num}-DOM-VERIFY.md`" with "Return this report". |

Done when:
- `grep -cE "live_dom_uat|DOM-VERIFY written|^Write " agents/dom-verifier.md` returns 0; `grep -c "^tools:.*Write" agents/dom-verifier.md` returns 0.

### agents/security-auditor.md (from agents/gsd-security-auditor.md; feature agent, no local counterpart)

Template: read-only reviewer from `.ai/agents/integration-checker.md:8-31`; threat tracking from `.ai/agents/phase-checker.md:558-562`. Already returns a verdict without writes (lines 16, 20, 93).

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-306 | RENAME | agents/gsd-security-auditor.md | — | Rename to `agents/security-auditor.md` with `git mv`. |
| R-AG-307 | REPLACE | agents/gsd-security-auditor.md:2-9 | — | Set `name: security-auditor`, spawner `secure-phase`, add `- Agent` to the tools list. |
| R-AG-308 | STITCH | after agents/gsd-security-auditor.md:11 | .ai/agents/integration-checker.md:8-31 | Insert an adapted `<local_workflow>` (read-only verdict to coordinator; coordinator persists SECURITY.md). |
| R-AG-309 | STITCH | after agents/gsd-security-auditor.md:18 | .ai/agents/coder.md:45 | Insert `@engineer/references/worker-handoff.md`. |
| R-AG-310 | REPLACE | agents/gsd-security-auditor.md:53-57 | .ai/agents/coder.md:81; .ai/agents/code-reviewer.md:77,79 | Apply inline skill self-load and AGENTS.md read lines. |
| R-AG-311 | STITCH | after agents/gsd-security-auditor.md:72 | .ai/agents/phase-checker.md:558-562 | Insert canonical threat tracking (six-column register, issue link, Pending dependency). |
| R-AG-312 | REPLACE | agents/gsd-security-auditor.md:146 | — | Replace `/gsd:secure-phase` with `secure-phase`. |

Done when:
- `grep -cE "/gsd:|agent-skills-bootstrap" agents/security-auditor.md` returns 0; `grep -c "canonical-threat-tracking" agents/security-auditor.md` returns 1.

### agents/nyquist-auditor.md (from agents/gsd-nyquist-auditor.md; feature agent, no local counterpart)

Template: source-changing worker from `.ai/agents/coder.md:14-36,757-765` and `.ai/references/worker-handoff.md:28-44`.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-313 | RENAME | agents/gsd-nyquist-auditor.md | — | Rename to `agents/nyquist-auditor.md` with `git mv`. |
| R-AG-314 | REPLACE | agents/gsd-nyquist-auditor.md:2-11 | — | Set `name: nyquist-auditor`, add `- Agent` to tools. |
| R-AG-315 | STITCH | after agents/gsd-nyquist-auditor.md:13 | .ai/agents/coder.md:14-36 | Insert an adapted `<local_workflow>` (write only assigned test/fixture paths and assigned VALIDATION path; commit them and the SUMMARY; shared records coordinator-owned). |
| R-AG-316 | STITCH | after agents/gsd-nyquist-auditor.md:20 | .ai/agents/coder.md:45 | Insert `@engineer/references/worker-handoff.md`. |
| R-AG-317 | REPLACE | agents/gsd-nyquist-auditor.md:22 | — | Limit VALIDATION.md edits to an explicitly assigned path. |
| R-AG-318 | REPLACE | agents/gsd-nyquist-auditor.md:55-59 | .ai/agents/coder.md:81; .ai/agents/code-reviewer.md:77,79 | Apply inline skill self-load and AGENTS.md read lines. |
| R-AG-319 | REPLACE | agents/gsd-nyquist-auditor.md:150-151,172-173,205 | .ai/agents/coder.md:757-765; .ai/references/worker-handoff.md:30-33 | Replace "Files for Commit"/"listed for commit" with exact-path commit of owned tests plus SUMMARY (`status: complete\|blocked`) and returned hashes. |
| R-AG-320 | STITCH | after agents/gsd-nyquist-auditor.md:126 | .ai/agents/coder.md:441-453 | Insert the 60%/250k context stop with `status: blocked` SUMMARY. |

Done when:
- `grep -c "Files for Commit" agents/nyquist-auditor.md` returns 0; `grep -c "status: complete" agents/nyquist-auditor.md` ≥ 1; `grep -c "250,000 tokens" agents/nyquist-auditor.md` returns 1.

### agents/code-fixer.md (from agents/gsd-code-fixer.md; feature agent, no local counterpart)

Template: leaf fixer from `.ai/agents/targeted-fixer.md:9-81` and `.ai/references/bounded-correction-dispatch.md:1-12`.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-321 | RENAME | agents/gsd-code-fixer.md | — | Rename to `agents/code-fixer.md` with `git mv`. |
| R-AG-322 | REPLACE | agents/gsd-code-fixer.md:2-4 | .ai/agents/targeted-fixer.md:4-5 | Set `name: code-fixer`, spawner `code-review --fix`, keep tools and add `disallowedTools: Agent, Task`. |
| R-AG-323 | STITCH | after agents/gsd-code-fixer.md:8 | .ai/agents/targeted-fixer.md:9-15 | Insert an adapted `<local_workflow>` (repair only assigned findings; no children; discovery via coordinator; worktree safety). |
| R-AG-324 | REPLACE | agents/gsd-code-fixer.md:11-15 | — | Replace `gsd-code-reviewer` with `code-reviewer` and state that REVIEW-FIX content is the assigned SUMMARY. |
| R-AG-325 | REPLACE | agents/gsd-code-fixer.md:24-32 | .ai/agents/coder.md:74,81; .ai/agents/code-reviewer.md:77,79 | Apply AGENTS.md, inline skill self-load and AGENTS.md read lines. |
| R-AG-326 | REMOVE | agents/gsd-code-fixer.md:215-433 | .ai/agents/targeted-fixer.md:37,49 | Delete `setup_worktree` (own worktree/branch creation, recovery sentinel, fast-forward cleanup tail) and replace with "verify supplied checkout/branch and HEAD == assigned revision; never create worktrees, switch branches, merge". |
| R-AG-327 | STITCH | after agents/gsd-code-fixer.md:438 | .ai/agents/targeted-fixer.md:17-34 | Insert the required assignment fields (`checkout`, `branch`, `revision`, `owned_paths`, `checks`, `summary_path`). |
| R-AG-328 | REPLACE | agents/gsd-code-fixer.md:443 | — | Replace in-phase-dir `fix_report_path` with assigned `summary_path`. |
| R-AG-329 | REPLACE | agents/gsd-code-fixer.md:534-551 | .ai/agents/coder.md:500-532 | Replace resolver blob and `gsd_run query commit` with exact-path `git add --` and `git commit -m`. |
| R-AG-330 | REPLACE | agents/gsd-code-fixer.md:592-657 | .ai/agents/targeted-fixer.md:54-74 | Write the REVIEW-FIX body as the assigned SUMMARY, commit it, and return the structured result instead of leaving it uncommitted. |
| R-AG-331 | REMOVE | agents/gsd-code-fixer.md:665-674,686-691 | — | Delete worktree-mandate, `workflow.use_worktrees`, "where verification ran" and cleanup-tail rules. |
| R-AG-332 | KEEP-UPSTREAM | agents/gsd-code-fixer.md:676-684 | — | Keep reparse-point `rm -rf` prohibition; prevents Windows data loss. |
| R-AG-333 | KEEP-UPSTREAM | agents/gsd-code-fixer.md:64-93 | .ai/agents/coder.md:592-595 | Keep per-file `git checkout -- {file}` rollback; matches coder's single-file discard. |
| R-AG-334 | KEEP-UPSTREAM | agents/gsd-code-fixer.md:718,768 | Original copied GSD text | Preserve the original CLAUDE.md conventions. |

Done when:
- `grep -cE "git worktree|setup_worktree|use_worktrees|review-fix-recovery|gsd-reviewfix|query commit|_GSD_SHIM" agents/code-fixer.md` returns 0.
- `grep -c "disallowedTools: Agent, Task" agents/code-fixer.md` returns 1; `grep -c "summary_path" agents/code-fixer.md` ≥ 2.

### agents/pattern-mapper.md (from agents/gsd-pattern-mapper.md; feature agent, no local counterpart)

Template: artifact writer from `.ai/agents/codebase-mapper.md:14-37,869`.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-335 | RENAME | agents/gsd-pattern-mapper.md | — | Rename to `agents/pattern-mapper.md` with `git mv`. |
| R-AG-336 | REPLACE | agents/gsd-pattern-mapper.md:2-4 | .ai/agents/codebase-mapper.md:4 | Set `name: pattern-mapper`, spawner `plan-phase`, tools `Agent, Read, Bash, Glob, Grep, Write, Skill`. |
| R-AG-337 | STITCH | after agents/gsd-pattern-mapper.md:12 | .ai/agents/codebase-mapper.md:14-37 | Insert an adapted `<local_workflow>` (write only assigned PATTERNS path and commit it). |
| R-AG-338 | REPLACE | agents/gsd-pattern-mapper.md:35-41 | .ai/agents/coder.md:74,81; .ai/agents/code-reviewer.md:77,79 | Apply AGENTS.md, inline skill self-load and AGENTS.md read lines. |
| R-AG-339 | STITCH | after agents/gsd-pattern-mapper.md:164 | .ai/agents/codebase-mapper.md:869 | Insert "Commit the assigned PATTERNS.md with `git add --` before returning, unless told not to commit". |
| R-AG-340 | REPLACE | agents/gsd-pattern-mapper.md:47 | .ai/agents/phase-preparer.md:85 | Replace `/gsd:discuss-phase` with the recorded phase discussion. |

Done when:
- `grep -cE "/gsd:" agents/pattern-mapper.md` returns 0; `grep -c "git add --" agents/pattern-mapper.md` ≥ 1.

### agents/coordinator.md, agents/scout.md, agents/targeted-fixer.md (NEW FILES)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-341 | NEW FILE | agents/coordinator.md | .ai/agents/coordinator.md:1-205 | Copy whole file, applying cross-cutting path/runtime/role renames (lines 37-42, 139-140, 191, 195, 197 `phase_run` → `engineer_run`; 48 `../runtime/README.md` → runtime guide target; role names throughout 143-186 → executor/planner/plan-checker/phase-researcher; 137 `README.md` → `AGENT.md`). |
| R-AG-342 | NEW FILE | agents/scout.md | .ai/agents/scout.md:1-43 | Copy whole file; rewrite `../RULES.md` and `../references/scout-dispatch.md` links. |
| R-AG-343 | NEW FILE | agents/targeted-fixer.md | .ai/agents/targeted-fixer.md:1-81 | Copy whole file; rewrite links in lines 11-14. |
| R-AG-344 | REPLACE | relocated engineer/references/bounded-correction-dispatch.md (cross-ref; references section) | .ai/references/bounded-correction-dispatch.md:19-22,33 | Rewrite `phase_run` to `engineer_run` and the prompt to `Follow agents/targeted-fixer.md.` so coordinator.md:20's link stays valid. |

Done when:
- `test -f agents/coordinator.md -a -f agents/scout.md -a -f agents/targeted-fixer.md` succeeds.
- `grep -cE "phase_run|\.ai/|\bcoder\b|phase-preparer|phase-checker" agents/coordinator.md agents/scout.md agents/targeted-fixer.md` totals 0.
- `grep -c "disallowedTools: Agent, Task, Write, Edit, MultiEdit, NotebookEdit, Bash" agents/scout.md` returns 1.

### agents/AGENT.md (catalog; empty placeholder, 0 lines)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-345 | NEW FILE | agents/AGENT.md:1 | .ai/agents/README.md:1-7 | Write the intro with links to `engineer/RULES.md` and `../engineer/references/agent-adaptation.md`. |
| R-AG-346 | NEW FILE | agents/AGENT.md (table) | .ai/agents/README.md:9-24 | Copy the role table with renamed roles (executor, planner, plan-checker, phase-researcher) and linked `agents/<role>.md` files. |
| R-AG-347 | STITCH | agents/AGENT.md (table) | — | Add rows for ui-researcher, ui-checker, ui-auditor, dom-verifier, security-auditor, nyquist-auditor, code-fixer, pattern-mapper with dispatcher and input→result→consumer. |
| R-AG-348 | NEW FILE | agents/AGENT.md (routing) | .ai/agents/README.md:26-48 | Copy the routing, fresh code-reviewer and scout-only spawning paragraphs. |
| R-AG-349 | NEW FILE | agents/AGENT.md (dispatch) | .ai/agents/README.md:50-102 | Copy "Dispatching an agent", replacing `python .ai/runtime/phase.py query` with `engineer_run query` and the installed-namespace paragraph (lines 64-69) with the shim form. |
| R-AG-350 | NEW FILE | agents/AGENT.md (native hosts) | .ai/agents/README.md:104-148 | Copy native host definitions and the Codex model table with renamed roles; repoint the methods catalog link to `../engineer/references/REFERENCE.md`. |

Done when:
- `wc -l < agents/AGENT.md` > 100.
- `grep -cE "\[(Executor|Planner|Plan checker|Phase researcher|Scout|Targeted fixer|Coordinator)\]" agents/AGENT.md` ≥ 7.
- `grep -cE "ui-auditor|dom-verifier|security-auditor|nyquist-auditor|code-fixer|pattern-mapper|ui-checker|ui-researcher" agents/AGENT.md` ≥ 8.
- `grep -cE "phase\.py|\.ai/" agents/AGENT.md` returns 0.

### Model/effort frontmatter policy

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-AG-351 | KEEP-UPSTREAM | all agents/*.md frontmatter | .ai/agents/README.md:76-79,96-102 | Keep shared files free of `model:`, `effort:`, `maxTurns:` (none present at HEAD); never add them. |
| R-AG-352 | REPLACE | .ai/install.py:144-145 (installer section) | .ai/agents/README.md:77-78 | Re-key installer Claude defaults to `scout`/`targeted-fixer` haiku, `executor` sonnet, `planner` opus+`effort: medium`. |
| R-AG-353 | REPLACE | .planning/config.yaml:101,110,116,125 | .ai/agents/README.md:80-89 | Rename `agents:` keys coder→executor, phase-preparer→planner, researcher→phase-researcher, phase-checker→plan-checker. |
| R-AG-354 | KEEP-UPSTREAM | .ai/runtime/lib/models.py:81,106 | .ai/agents/README.md:129-137 | Keep scout/targeted-fixer fixed resolution unchanged in the Python port. |
| R-AG-355 | REMOVE | agents/executor.md:58; agents/gsd-planner.md:578 | — | Delete `executor_model`/`planner_model`/`researcher_model`/`checker_model` init-JSON extraction (dispatch-time resolution only). |

Done when:
- `grep -lE "^(model|effort|maxTurns):" agents/*.md` prints nothing.
- `grep -cE "_model\`" agents/executor.md agents/planner.md` totals 0.
- `grep -cE "^  (coder|phase-preparer|phase-checker|researcher):" .planning/config.yaml` returns 0.

## 12. Reconciliation: commands and workflows

824 rows (R-WF). Phase 5 for the core loop; the feature subsections are worked in Phase 8.

How to read the rows:

- **GSD target lines** are in the downloaded GSD copy at `9443672` (`agents/`, `commands/`, `engineer/`). "after X:N" is an insertion point.
- **Local source lines** are in `.ai/`, `.planning/` or `AGENTS.md` at `9443672`.
- **Action:** STITCH inserts the local block; REPLACE swaps GSD lines for local lines; REMOVE deletes GSD lines; NEW FILE creates the target from the local source; RENAME moves a file; KEEP-UPSTREAM keeps newer upstream content on purpose; DROP-LOCAL leaves local content behind on purpose.
- Apply the renames in [3.2](#32-mechanical-renames) to every copied block. Section 3.3 gives the final role names.
- Process each file bottom-up. Commit with a `Rows:` trailer naming the IDs done.

### Conventions applied to every target below

Verified at HEAD 9443672 (branch manual-override). Line ranges are inclusive. "after X:N" is an insertion point. IDs are numbered in file order across all subsections.

- Rewrite `gsd_run` → `engineer_run` and carried local `phase_run` → `engineer_run`.
- Rewrite `@~/.claude/gsd-core/<x>`, `gsd-core/<x>` and `@~/.ai/<x>` → `engineer/<x>`; `/gsd:<name>` → `/<name>`.
- Replace every pasted `engineer/workflows/_runtime-launcher.snippet.sh` launcher with the contents of `.ai/workflows/_runtime.snippet.sh:1-28` (renamed function `engineer_run`).
- Rename upstream `gsd-*` agents to the final role names in section 3.3 (`executor`, `planner`, `plan-checker`, `phase-researcher`, `verifier`, `code-reviewer`, `debugger`, `integration-checker`, `doc-writer`, `doc-verifier`, `codebase-mapper`, `scout`, `targeted-fixer`, plus the feature roles). When copying local text, rename `executor`→`executor`, `planner`→`planner`, `plan-checker`→`plan-checker`, `phase-researcher`→`phase-researcher` and resolve model/effort inline per `.ai/workflows/execute-phase.md:55-72`.
- Route issues per `.ai/RULES.md:244-272` (no stops, no todos); gate implementation per `.ai/RULES.md:77-120`.

Stale local lines that must NOT be carried (rows below repeat them in context):
`.ai/workflows/execute-phase.md:817-818` (dispatch hook "will block"; hook is advisory per L288-292) · `.ai/workflows/discuss-phase/modes/auto.md:5-8,32` (chain.md/auto_advance) · `.ai/guides/PHASE-WORKFLOW.md:102,116-117` (checkpoints to user; gaps as todos) · `.ai/workflows/quick.md:495-496` (offers todos) · `.ai/commands/ship.md:4` argument-hint lacks `--no-merge` (workflow parses it at `.ai/workflows/ship.md:58-60`) · plus extras found: `.ai/workflows/plan-phase.md:190-192` ("Plan anyway"), `.ai/workflows/quick.md:58,450,546-555`, `.ai/workflows/check-todos.md:109` (nonexistent `phases.list`), local Next Up `/clear` blocks in add-phase, insert-phase, discuss-phase, plan-phase, new-milestone, onboard, complete-milestone.

### engineer/workflows/execute-phase.md (+ commands/execute-phase.md)

Line numbers verified at HEAD 9443672. Local source = `.ai/workflows/execute-phase.md` unless prefixed. Insert-points name the GSD line the new block goes after; "replace" ranges are inclusive.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-001 | REPLACE | engineer/workflows/execute-phase.md:1-7 | .ai/workflows/execute-phase.md:1-6 | Replace the `gsd:loop-host` header (loop points execute:pre/wave:pre/wave:post/post) with the local `workflow` header naming roles orchestrator, executor, code-reviewer. |
| R-WF-002 | REPLACE | engineer/workflows/execute-phase.md:8-10 | .ai/workflows/execute-phase.md:8-24 | Replace the purpose with the local purpose, keeping "carry the phase through to publication", the never-resume/`/clear` list, the CONTEXT HANDOFF clause and the issues-found-while-working routing link. |
| R-WF-003 | REMOVE | engineer/workflows/execute-phase.md:16-18 | — | Delete the #2508 runtime-aware-dispatch (kimi `resolve-dispatch-type`) note. |
| R-WF-004 | REMOVE | engineer/workflows/execute-phase.md:20-42 | — | Delete `<runtime_compatibility>` (Copilot/other-runtime sequential inline fallback) because every plan must run as an isolated `executor` subagent. |
| R-WF-005 | REPLACE | engineer/workflows/execute-phase.md:44-49 | .ai/workflows/execute-phase.md:26-43 | Replace `<required_reading>` with the local required_reading plus `<isolation_reading>` block, rewriting `@~/.ai/references/` to `engineer/references/`. |
| R-WF-006 | REPLACE | engineer/workflows/execute-phase.md:51-67 | .ai/workflows/execute-phase.md:45-53 | Replace the gsd-* agent list with the local exact names executor, code-reviewer, doc-writer, verifier, debugger, targeted-fixer. |
| R-WF-007 | STITCH | after engineer/workflows/execute-phase.md:67 | .ai/workflows/execute-phase.md:55-72 | Insert `<model_selection>` (resolve-model/resolve-effort inline, omit on `inherit`) with `phase_run` renamed `engineer_run`. |
| R-WF-008 | STITCH | after engineer/workflows/execute-phase.md:67 | .ai/workflows/execute-phase.md:74-78; .ai/RULES.md:88-99 | Insert the `<authority>` block so execution never starts without the user's explicit instruction for this phase recorded in CONTEXT. |
| R-WF-009 | STITCH | after engineer/workflows/execute-phase.md:69 | .ai/workflows/execute-phase.md:82-87 | Insert the "every execution exit uses `review_phase_issues`" preamble immediately after `<process>`. |
| R-WF-010 | REMOVE | engineer/workflows/execute-phase.md:71 | — | Delete the Compact Content Gate paragraph and its `execute-phase/detail/elaboration.md` read. |
| R-WF-011 | REPLACE | engineer/workflows/execute-phase.md:73-83 | .ai/workflows/execute-phase.md:89-97 | Replace parse_args with the local flags `--plan`, `--wave`, `--sequential`, `--resume`, `--no-review`, dropping `--gaps-only` (local safe_resume runs every un-summarized plan, including gap plans) and `--cross-ai`/`--no-cross-ai`. |
| R-WF-012 | REPLACE | engineer/workflows/execute-phase.md:86-100 | .ai/workflows/execute-phase.md:101-137; .ai/workflows/_runtime.snippet.sh:1-28 | Replace the `gsd-run-resolver` include, `--ws` parsing, `gsd_run query init.execute-phase` and `agent-skills gsd-executor` with the `_runtime.snippet.sh` launcher, `engineer_run query phase.locate`, the quoted `cd` into `worktree`, and `engineer_run query init.execute-phase`. |
| R-WF-013 | REPLACE | engineer/workflows/execute-phase.md:102 | .ai/workflows/execute-phase.md:139-146 | Replace the parsed-field list with the local list (`plan_index`, `checks_configured`, `models`, `efforts`, `agents_installed`, `missing_agents`, `context_window`, …) and the "bundle says nothing about isolation" note. |
| R-WF-014 | KEEP-UPSTREAM | engineer/workflows/execute-phase.md:104 | — | Keep the threat-ID duplicate hard stop (duplicate IDs break canonical threat tracking), conditioned on `init.execute-phase` emitting `threat_id_duplicate_count`. |
| R-WF-015 | REMOVE | engineer/workflows/execute-phase.md:106 | — | Delete the `section_manifest` gating paragraph; kept step files are read unconditionally when their step applies. |
| R-WF-016 | REMOVE | engineer/workflows/execute-phase.md:108 | — | Delete the `executor_model` inherit paragraph; model/effort come from the stitched `<model_selection>`. |
| R-WF-017 | REPLACE | engineer/workflows/execute-phase.md:110 | .ai/workflows/execute-phase.md:148-150 | Replace the response-language include with the inline local response_language rule. |
| R-WF-018 | REMOVE | engineer/workflows/execute-phase.md:112-119 | — | Delete the wave-failure handoff-file reset (the post-merge gate it feeds is replaced by `run_checks`). |
| R-WF-019 | REMOVE | engineer/workflows/execute-phase.md:121-125 | — | Delete the `RUNTIME` and `workflow.use_worktrees` config reads. |
| R-WF-020 | KEEP-UPSTREAM | engineer/workflows/execute-phase.md:126-127 | — | Keep the executor stall interval/threshold `config-get` reads (renamed `engineer_run`); stall detection feeds handoff continuation. |
| R-WF-021 | REMOVE | engineer/workflows/execute-phase.md:129-136 | — | Delete the inline isolation comment block and ISOLATION-not-RUNTIME note; the stitched `resolve_isolation` step owns both. |
| R-WF-022 | REMOVE | engineer/workflows/execute-phase.md:138-150 | — | Delete the submodule `SUBMODULE_PATHS` computation that exists to drop plans out of isolation. |
| R-WF-023 | REMOVE | engineer/workflows/execute-phase.md:152-154 | — | Delete the `USE_WORKTREES=false` forced-`none` and #683 base-check auto-degrade paragraphs. |
| R-WF-024 | REPLACE | engineer/workflows/execute-phase.md:156-173 | .ai/workflows/execute-phase.md:139-142,406-408 | Replace the `config-get context_window` read and thin/rich prompt rules with the bundle's `context_window` and the local ≥500000 prior-wave-summaries rule only. |
| R-WF-025 | REPLACE | engineer/workflows/execute-phase.md:175-177 | .ai/workflows/execute-phase.md:113-122,152-161 | Replace the error lines (incl. "Offer reconstruct or continue") with the local phase-not-found, inconsistent-locator, no-plans and `agents_installed` stops. |
| R-WF-026 | REPLACE | engineer/workflows/execute-phase.md:179 | .ai/workflows/execute-phase.md:93-94 | Replace "parallelization false → sequential" with the `--sequential` rule that keeps every plan isolated. |
| R-WF-027 | REMOVE | engineer/workflows/execute-phase.md:181-187 | — | Delete Copilot runtime detection and `COPILOT_SEQUENTIAL` inline execution. |
| R-WF-028 | REMOVE | engineer/workflows/execute-phase.md:189-200 | — | Delete the `--auto` / `workflow._auto_chain_active` chain-flag sync block. |
| R-WF-029 | REMOVE | engineer/workflows/execute-phase.md:202-216 | — | Delete `MVP_MODE`, `loop render-hooks execute:post`, `TDD_MODE` and the contribution-hook note. |
| R-WF-030 | STITCH | before engineer/workflows/execute-phase.md:218 | .ai/workflows/execute-phase.md:164,166-212 | Close `initialize` with `</step>` (upstream never closes it) and insert the `open_session` step (session.adopt/session.open routing, re-init inside the session worktree, "do not deliver it here"). |
| R-WF-031 | REPLACE | engineer/workflows/execute-phase.md:218-239 | .ai/workflows/execute-phase.md:214-223 | Replace the evaluation-scope safe-resume gate and its three ask-the-user recovery options with the local no-ask rule: run only plans whose `summary` is null and go to `aggregate_results` when all have one. |
| R-WF-032 | REMOVE | engineer/workflows/execute-phase.md:241-270 | — | Delete the TDD RED-commit gate (and its `check evaluation-scope`, `state.update last_gate_trip`, `execute-mvp-tdd.md` read), keeping the closing `</step>` at 271. |
| R-WF-033 | REPLACE | engineer/workflows/execute-phase.md:292-294 | .ai/workflows/execute-phase.md:239-241 | Replace "stop and ask the user for clarification" with: answer from codebase/history, else apply the most direct preventive mechanism, name the row in the closing report, and continue; drop the jump to `check_interactive_mode`. |
| R-WF-034 | REMOVE | engineer/workflows/execute-phase.md:297-301 | — | Delete `check_interactive_mode` (`--interactive` inline execution without subagents). |
| R-WF-035 | REPLACE | engineer/workflows/execute-phase.md:303-339 | .ai/workflows/execute-phase.md:244-263 | Replace `handle_branching` (branch from origin/HEAD, "user handles merging") with the local `preflight` step: dirty-tree check outside `.planning/`, and stop if the current branch is the default branch because the session was not opened. |
| R-WF-036 | STITCH | after engineer/workflows/execute-phase.md:339 (new preflight) | .ai/workflows/execute-phase.md:265-313 | Insert the `resolve_isolation` step: `engineer_run query dispatch-isolation --raw --phase`, the two-value table, "no third value, no opt-out", advisory worktree-guard note, `worktree.reap-orphans`, exit-42 backstop, one-line report. |
| R-WF-037 | KEEP-UPSTREAM | engineer/workflows/execute-phase.md:341-353 | — | Keep `validate_phase` with `engineer_run query state.begin-phase` (verb exists in the Python runtime). |
| R-WF-038 | STITCH | engineer/workflows/execute-phase.md:356-362 | .ai/workflows/execute-phase.md:316-326 | Keep the `phase-plan-index` call and ready-wave-gate read, and add the local grouping rules: dependency waves and overlapping `files_modified` forced into a later wave. |
| R-WF-039 | REPLACE | engineer/workflows/execute-phase.md:364 (the `--gaps-only` sentences) | — | Delete the `--gaps-only` filter and its `gap_closure` key stop from the filtering paragraph, keeping the `has_summary`, `blocked_by`, `ready: false` and `WAVE_FILTER` skips. |
| R-WF-040 | REPLACE | engineer/workflows/execute-phase.md:376-429 | .ai/workflows/execute-phase.md:222 | Replace the verification-status/roadmap.analyze routing (condition 3 and its arms, including "present next_command") with: every plan summarized → continue at `aggregate_results`, then the normal tail ending in `run_verify_work`; keep conditions 1, 2 and 2b as closing-report blockers. |
| R-WF-041 | STITCH | engineer/workflows/execute-phase.md:431-444 | .ai/workflows/execute-phase.md:327-340 | Append the cycle-is-a-planning-defect stop and the parallel-status assignment table to the execution-plan report. |
| R-WF-042 | REMOVE | engineer/workflows/execute-phase.md:448-454 | — | Delete the `cross_ai_delegation` step. |
| R-WF-043 | REPLACE | engineer/workflows/execute-phase.md:457 | .ai/workflows/execute-phase.md:344-350 | Replace "parallel if PARALLELIZATION" with: dispatch every plan of a wave in one message with multiple Agent calls unless `--sequential` or one plan, refreshing parallel-status at dispatch, observation and join. |
| R-WF-044 | KEEP-UPSTREAM | engineer/workflows/execute-phase.md:459-531 | — | Keep the orchestrator cwd-drift guard (prevents merging from an agent worktree); add an assertion that `ORCHESTRATOR_WT` equals the session `worktree`. |
| R-WF-045 | REPLACE | engineer/workflows/execute-phase.md:533-552 | .ai/workflows/execute-phase.md:348-350 | Replace the `[checkpoint]` heartbeat block (and its `/gsd:manager` reference) with the parallel-status refresh rule. |
| R-WF-046 | REMOVE | engineer/workflows/execute-phase.md:556-558 | — | Delete the wave-guard include (USE_WORKTREES/baseRef degrade) and context-guard include (tells the user to `/gsd:pause-work` and resume fresh). |
| R-WF-047 | REPLACE | engineer/workflows/execute-phase.md:560-593 | .ai/workflows/execute-phase.md:324-325 | Replace the overlap warn-and-sequentialize sub-step with a pointer that overlap was already resolved by regrouping in `discover_and_group_plans`. |
| R-WF-048 | REMOVE | engineer/workflows/execute-phase.md:597-603 | — | Delete the wave-start heartbeat instruction inside sub-step 2, keeping the "describe what's being built" text. |
| R-WF-049 | REPLACE | engineer/workflows/execute-phase.md:621-627 | — | Replace the per-plan worktree decision with: read `per-plan-worktree-gate.md` to extract `PLAN_FILES`/`PLAN_DELETIONS` and block (never de-isolate) any plan touching a submodule. |
| R-WF-050 | REMOVE | engineer/workflows/execute-phase.md:629-637 | — | Delete `execute:wave:pre` `loop render-hooks` dispatch. |
| R-WF-051 | REMOVE | engineer/workflows/execute-phase.md:641-644,648,650 | — | Delete the plan-start heartbeat, the sentinel `plan_id` substitution note and the per-plan Part 2 isolation re-record (local resolves isolation once per phase). |
| R-WF-052 | STITCH | engineer/workflows/execute-phase.md:652 | .ai/workflows/execute-phase.md:450-452 | Keep executor routing but default `EXECUTOR_TYPE` to `executor` and resolve model/effort for the routed type inline. |
| R-WF-053 | KEEP-UPSTREAM | engineer/workflows/execute-phase.md:654 | — | Keep the TDD-applicability resolution read only if `engineer_run` gains `phase.tdd-applicable`; otherwise delete this line and line 738. |
| R-WF-054 | REPLACE | engineer/workflows/execute-phase.md:656-674 | .ai/workflows/execute-phase.md:352-362 | Replace the `USE_WORKTREES` gate and temp `WAVE_WORKTREE_MANIFEST` creation with `EXPECTED_BASE=$(git rev-parse HEAD)` plus the declared-scope note; keep `DISPATCH_TS` and `EXPECTED_BRANCH`. |
| R-WF-055 | REPLACE | engineer/workflows/execute-phase.md:676-686 | .ai/workflows/execute-phase.md:364-382 | Replace the three-model note and one-Agent-per-message rule with the local per-ISOLATION branches: `worktree.record-agent "${plan_id}" --phase --branch --base --files --deletions` (harness) or `worktree.create "${plan_id}" --phase --base --files --deletions` (orchestrator). |
| R-WF-056 | REPLACE | engineer/workflows/execute-phase.md:688-777 | .ai/workflows/execute-phase.md:386-456 | Replace the gsd-executor Agent template with the local executor template (handoff block, required_reading, constraints, `worktree_branch_check` or `project_root_pin` by ISOLATION, output with `issue_refs`, inline model/effort, `isolation="worktree"` under harness). |
| R-WF-057 | STITCH | into local executor `<constraints>` | engineer/workflows/execute-phase.md:705,719-729 | Add to the executor constraints: do not modify STATE.md or ROADMAP.md, and write then commit SUMMARY.md before returning. |
| R-WF-058 | REPLACE | engineer/workflows/execute-phase.md:779 | .ai/workflows/execute-phase.md:364-370 | Replace the `--manifest` record-agent call and "stop and ask for recovery" with the local `worktree.record-agent` signature; a missing field marks the plan blocked. |
| R-WF-059 | REPLACE | engineer/workflows/execute-phase.md:781 | .ai/workflows/execute-phase.md:458-461 | Replace the recovery-policy pointer with the exit-42 rule: mark blocked, preserve the worktree, do not count the wave successful. |
| R-WF-060 | REPLACE | engineer/workflows/execute-phase.md:783 | .ai/workflows/execute-phase.md:463-466 | Replace the Codex orchestrator rule with the local runtime-neutral ORCHESTRATOR RULE. |
| R-WF-061 | REPLACE | engineer/workflows/execute-phase.md:785 | .ai/workflows/execute-phase.md:372-382,434-437 | Replace the process-spawn orchestrator-worktree pointer with: `worktree.create` per plan and dispatch the same executor Agent with a `project_root_pin` from `sequential-root-pin.md`. |
| R-WF-062 | REMOVE | engineer/workflows/execute-phase.md:787-818 | — | Delete the Sequential mode branch (unisolated main-tree executors and its success criteria). |
| R-WF-063 | REMOVE | engineer/workflows/execute-phase.md:822-830 | — | Delete the plan-complete heartbeat lines. |
| R-WF-064 | KEEP-UPSTREAM | engineer/workflows/execute-phase.md:832-834 | — | Keep completion reconciliation (artifacts decide abnormal ends, never re-dispatch completed work). |
| R-WF-065 | REPLACE | engineer/workflows/execute-phase.md:836-841 | .ai/workflows/execute-phase.md:479-493 | Replace the stall prompt (`continue waiting` / `kill and retry` / `kill and switch to inline execution`) with: after the threshold, reconcile, then continue the plan from its handoff in a fresh isolated checkout, at most twice, without asking. |
| R-WF-066 | STITCH | after engineer/workflows/execute-phase.md:845 | .ai/workflows/execute-phase.md:468-493 | Insert verify-on-disk (`phase-plan-index`, `git log`), the complete-without-SUMMARY-is-blocked rule and the `handoff.list`/re-dispatch/`handoff.consume` continuation procedure. |
| R-WF-067 | REMOVE | engineer/workflows/execute-phase.md:847-858 | — | Delete the `worktree_skip_hooks` post-wave hook run and its "Fix hook issues now?" prompt. |
| R-WF-068 | REPLACE | engineer/workflows/execute-phase.md:860-898 | .ai/workflows/execute-phase.md:496-539 | Replace manifest-based worktree cleanup with the local `integrate_wave` step: clean-tree check, `worktree.merge-wave --phase`, the blocked/conflict/missing/empty table, advisory `out_of_scope`, `worktree.cleanup-wave --phase`, never `--force`. |
| R-WF-069 | REMOVE | engineer/workflows/execute-phase.md:900-944 | — | Delete the cleanup-tail snippet (`git worktree remove --force`, `git branch -D`) and the skip conditions for unisolated waves. |
| R-WF-070 | KEEP-UPSTREAM | engineer/workflows/execute-phase.md:946 | — | Keep the never-edit-main recovery sentence (matches local anti-pattern 822-823). |
| R-WF-071 | REPLACE | engineer/workflows/execute-phase.md:948-959 | .ai/workflows/execute-phase.md:584-608 | Replace the post-merge build/test gate with the local `run_checks` step (`verification.run-checks` against the integrated wave, receipt reuse, bounded correction on failure, rerun after repair). |
| R-WF-072 | REPLACE | engineer/workflows/execute-phase.md:961-991 | .ai/workflows/execute-phase.md:541-560 | Replace the per-wave ROADMAP/STATE tracking commit with the local `track_integrated_slice` step (`review_phase_issues`, push session branch, `pr.open --draft`, update the same draft each wave); plan ticks move to `update_roadmap`. |
| R-WF-073 | REMOVE | engineer/workflows/execute-phase.md:993-1009 | — | Delete `execute:wave:post` loop render-hooks dispatch and its gate/step/contribution handling. |
| R-WF-074 | REPLACE | engineer/workflows/execute-phase.md:1011-1048 | .ai/workflows/execute-phase.md:602-607; .ai/RULES.md:249-253 | Replace the "Fix now / Continue" test-failure prompt with no-ask routing: a failing check blocks dependent waves and goes to bounded correction, debugger or executor/preparer. |
| R-WF-075 | REPLACE | engineer/workflows/execute-phase.md:1052-1064 | .ai/workflows/execute-phase.md:470-477 | Replace the heartbeat and `check evaluation-scope` spot-check and "Retry plan? / Continue?" prompt with the local on-disk verification; a failed check marks the plan blocked and the wave continues. |
| R-WF-076 | REPLACE | engineer/workflows/execute-phase.md:1080-1099 | .ai/workflows/execute-phase.md:574-578,605 | Replace `agent.classify-failure`, the quota-recovery and between-wave-reset includes and "ask Continue/Stop" with: failed plan blocked, only dependents skipped, unknown causes to debugger, all other waves continue. |
| R-WF-077 | REPLACE | engineer/workflows/execute-phase.md:1104-1152 | .ai/workflows/execute-phase.md:562-582 | Replace `checkpoint_handling` (auto-mode auto-approve, present-to-user loop) with the local delegated-discretion route (`state.add-decision`) or blocked-for-a-person in the closing report, re-dispatching into a fresh isolated checkout. |
| R-WF-078 | STITCH | engineer/workflows/execute-phase.md:1154-1181 | .ai/workflows/execute-phase.md:610-635 | Keep the execution summary table and add threat reconciliation, uncovered-requirement gaps and the still-open list with "Do not create todos"; delete lines 1178-1180 (verify:post note). |
| R-WF-079 | REPLACE | engineer/workflows/execute-phase.md:1183-1187 | — | Replace the section-manifest-gated partial-wave block with "If `--wave` was passed, read and execute `execute-phase/steps/partial-wave.md`." |
| R-WF-080 | STITCH | after engineer/workflows/execute-phase.md:1187 | .ai/workflows/execute-phase.md:637-687 | Insert the local blocking `code_review_gate` step (frozen revision, code-reviewer + `verification.run-checks` concurrently, critical findings block, bounded correction). |
| R-WF-081 | STITCH | after the stitched code_review_gate | .ai/workflows/execute-phase.md:689-732 | Insert the `review_phase_issues` step (`phase.issue-declare`/`issue-preview`/`issue-publish`/`issue-update`, `phase.handoff` must be `ready: true`). |
| R-WF-082 | REMOVE | engineer/workflows/execute-phase.md:1189-1305 | — | Delete `verify_phase_goal` (shared verifier include, human_needed UAT write, gaps-found `/clear` Next Up) because verification runs in `/verify-work` via `run_verify_work`. |
| R-WF-083 | REMOVE | engineer/workflows/execute-phase.md:1307-1320 | — | Delete the gap-closure-artifacts and regression-gate section markers. |
| R-WF-084 | REPLACE | engineer/workflows/execute-phase.md:1322-1354 | .ai/workflows/execute-phase.md:734-745 | Replace `phase.complete` (marks phase complete before verification) with per-plan `engineer_run query roadmap.update-plan-progress "${plan_id}"` for complete SUMMARYs only. |
| R-WF-085 | STITCH | after engineer/workflows/execute-phase.md:1354 | .ai/workflows/execute-phase.md:747-764 | Insert `pending_todo_reconciliation` (folded TODOs stay pending until /ship) and `update_state` (`state.update-progress`, `state.record-session`, `commit`). |
| R-WF-086 | REMOVE | engineer/workflows/execute-phase.md:1356-1384 | — | Delete `auto_copy_learnings`. |
| R-WF-087 | REMOVE | engineer/workflows/execute-phase.md:1386-1418 | — | Delete `close_phase_todos` (pre-merge todo auto-close). |
| R-WF-088 | REMOVE | engineer/workflows/execute-phase.md:1420-1429 | — | Delete `delegate_post_completion_to_transition` and its `transition.md` include. |
| R-WF-089 | STITCH | before engineer/workflows/execute-phase.md:1431 | .ai/workflows/execute-phase.md:766-799 | Insert `session_handoff`, `completion` and `run_verify_work` so `run_verify_work` is the final step before `</process>`. |
| R-WF-090 | REMOVE | engineer/workflows/execute-phase.md:1433-1442 | — | Delete `<context_efficiency>` (inline-without-subagents and `/clear` advice). |
| R-WF-091 | REPLACE | engineer/workflows/execute-phase.md:1444-1452 | .ai/RULES.md:244-272 | Replace `<failure_handling>` asks ("ask user how to proceed", "Skip this plan?") with the issues-found-while-working routing link; keep the systemic all-agents-fail stop. |
| R-WF-092 | REPLACE | engineer/workflows/execute-phase.md:1454-1458 | .ai/workflows/execute-phase.md:214-222 | Replace `<resumption>` with the no-ask resume rule using `/execute-phase {phase}`. |
| R-WF-093 | STITCH | after engineer/workflows/execute-phase.md:1458 | .ai/workflows/execute-phase.md:803-816,819-835 | Append the local `<anti_patterns>` block, excluding lines 817-818. |
| R-WF-094 | REPLACE | (do not carry) | .ai/workflows/execute-phase.md:817-818 | Do not carry "the dispatch hook will block it"; write "Don't look for a way to run a plan unisolated — there is no opt-out" because worktree-guard is advisory (local 288-292). |
| R-WF-095 | STITCH | after the appended anti_patterns | .ai/workflows/execute-phase.md:837-863 | Append the local `<success_criteria>` (authority, isolation, merge-wave, no todos, `/verify-work` in the same session). |
| R-WF-096 | REPLACE | commands/execute-phase.md:2-4 | .ai/commands/execute-phase.md:2-4 | Rename to `execute-phase`, use the local description, and set argument-hint `<phase> [--plan <id>] [--wave <n>] [--sequential] [--resume] [--no-review]`. |
| R-WF-097 | STITCH | commands/execute-phase.md:16 | — | Extend `requires` to `[phase, verify-work, ship]` because the chain invokes ship. |
| R-WF-098 | REPLACE | commands/execute-phase.md:23-38 | .ai/commands/execute-phase.md:16-36 | Replace the objective with the local how-it-works list, same-session verify/ship chain and authority clause. |
| R-WF-099 | REPLACE | commands/execute-phase.md:40-43 | .ai/commands/execute-phase.md:38-40 | Replace `@~/.claude/gsd-core/workflows/execute-phase.md` and `ui-brand.md` includes with `engineer/workflows/execute-phase.md` and `engineer/references/ui-brand.md`. |
| R-WF-100 | REPLACE | commands/execute-phase.md:49-65 | .ai/commands/execute-phase.md:42-49 | Replace the flag docs (`--gaps-only`, `--interactive`, `gsd-tools query`) with the local context, carrying the duplicated "Phase number: $ARGUMENTS (required)" line (local 44/46) once. |
| R-WF-101 | REPLACE | commands/execute-phase.md:67-70 | .ai/commands/execute-phase.md:51-58 | Replace the process with the MANDATORY read-the-workflow-first instruction pointing at `engineer/workflows/execute-phase.md`. |
| R-WF-102 | STITCH | after commands/execute-phase.md:70 | .ai/commands/execute-phase.md:60-69 | Append the local `<success_criteria>`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM_NAME\|gsd-core/\|/gsd:\|gsd-executor\|gsd-verifier" engineer/workflows/execute-phase.md` → 0
- `grep -ci "use_worktrees\|cross_ai\|cross-ai\|_auto_chain\|auto-advance\|render-hooks\|section_manifest\|compact_content\|transition\|TDD_MODE\|COPILOT_SEQUENTIAL\|--interactive\|--gaps-only\|/clear" engineer/workflows/execute-phase.md` → 0
- `grep -c "learnings.copy\|close_phase_todos\|resolves_phase\|phase.complete\|check evaluation-scope\|agent.classify-failure" engineer/workflows/execute-phase.md` → 0
- `grep -c "AskUserQuestion\|ask the user\|Retry plan?\|Fix now" engineer/workflows/execute-phase.md` → 0
- `grep -o '<step name="[a-z_]*"' engineer/workflows/execute-phase.md | tail -1` → `<step name="run_verify_work"`
- `grep -c 'session.open\|session.adopt\|dispatch-isolation\|worktree.merge-wave\|worktree.cleanup-wave\|pr.open\|phase.handoff\|verification.run-checks\|resolve-model\|resolve-effort' engineer/workflows/execute-phase.md` → ≥10
- `grep -n '<authority>' engineer/workflows/execute-phase.md` → 1 hit before `<process>`
- `grep -c "dispatch hook will block" engineer/workflows/execute-phase.md` → 0
- `grep -c "gsd:\|gaps-only\|interactive\|tdd\|gsd-tools" commands/execute-phase.md` → 0; `grep -n "no-review" commands/execute-phase.md` → argument-hint line

### engineer/workflows/execute-phase/steps/code-review-disposition.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-103 | REPLACE | engineer/workflows/execute-phase/steps/code-review-disposition.md:792 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the gsd-tools launcher one-liner with the `_runtime.snippet.sh` launcher defining `engineer_run`. |
| R-WF-104 | REPLACE | engineer/workflows/execute-phase/steps/code-review-disposition.md:1013,1017 | — | Rename `gsd_run query` to `engineer_run query`. |
| R-WF-105 | REPLACE | engineer/workflows/execute-phase/steps/code-review-disposition.md:19,190,283,336,708,809 | .ai/workflows/execute-phase.md:48 | Rename `gsd-code-reviewer` to `code-reviewer`. |
| R-WF-106 | REPLACE | engineer/workflows/execute-phase/steps/code-review-disposition.md:267 | — | Rename `/gsd:code-review` to `/code-review`. |
| R-WF-107 | REPLACE | engineer/workflows/execute-phase/steps/code-review-disposition.md:25-31 | .ai/workflows/execute-phase.md:637-687 | Rewrite the caller comment: the only dispatcher is `code-review-fix.md` (`record_disposition`); execute-phase's blocking `code_review_gate` no longer reads REVIEW.md through this step. |
| R-WF-108 | KEEP-UPSTREAM | engineer/workflows/execute-phase/steps/code-review-disposition.md:17,282,351,470,771,857,882 | — | Keep `--auto` references; they denote code-review's own fix loop, not phase chaining. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM_NAME\|gsd-code-reviewer\|/gsd:" engineer/workflows/execute-phase/steps/code-review-disposition.md` → 0

### engineer/workflows/execute-phase/steps/completion-reconciliation.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-109 | REPLACE | engineer/workflows/execute-phase/steps/completion-reconciliation.md:27 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the gsd-tools launcher with the `_runtime.snippet.sh` launcher. |
| R-WF-110 | REPLACE | engineer/workflows/execute-phase/steps/completion-reconciliation.md:30-36 | .ai/workflows/execute-phase.md:470-473 | Replace the `check evaluation-scope` commit probe (absent from engineer_run) with `engineer_run query phase-plan-index` plus `git log --oneline` on the plan's reported branch. |
| R-WF-111 | REPLACE | engineer/workflows/execute-phase/steps/completion-reconciliation.md:42 | .ai/RULES.md:258-262 | Replace "stop for the user" on an unavailable probe with: mark only that plan blocked, list it in the closing report, continue independent plans. |
| R-WF-112 | REPLACE | engineer/workflows/execute-phase/steps/completion-reconciliation.md:20-21 | — | Drop "sequential dispatch" and "process spawns" from the scope list; both isolation models dispatch Agent calls. |

Done when:
- `grep -c "gsd_run\|evaluation-scope\|stop for the user\|sequential dispatch" engineer/workflows/execute-phase/steps/completion-reconciliation.md` → 0

### engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-113 | REPLACE | engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:8-104 | .ai/workflows/execute-phase.md:265-313 | Replace "Resolve ISOLATION" (fail-closed-to-`none`, `USE_WORKTREES=false` opt-out, base-check auto-degrade, `--force-isolation` re-persist, three-row table) with the local resolve_isolation text: two values only, failure stops and reports, `worktree.reap-orphans`. |
| R-WF-114 | REPLACE | engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:106-123 | .ai/workflows/execute-phase.md:278,364-370,453 | Replace the `harnessFlag` lookup with the literal `isolation="worktree"` on Claude plus `worktree.record-agent "${plan_id}" --phase --branch --base --files --deletions`. |
| R-WF-115 | REPLACE | engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:125-374 | .ai/workflows/execute-phase.md:372-382,434-437 | Replace the process-spawn orchestrator-worktree path (worker-record/worker-status/worker-complete, `EXECUTOR_PROMPT` shell assignment, `.claude/worktrees` paths, manifest) with: `worktree.create "${plan_id}" --phase --base --files --deletions`, then the same executor Agent dispatch carrying a `project_root_pin` for that path. |

Done when:
- `grep -ci "gsd_run\|use_worktrees\|ISOLATION=none\|base-check\|worker-record\|worker-status\|--manifest\|gsd-executor\|\.claude/worktrees" engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md` → 0
- `grep -c "worktree.create\|worktree.record-agent\|reap-orphans" engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md` → ≥3

### engineer/workflows/execute-phase/steps/executor-progress-policy.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-116 | REPLACE | engineer/workflows/execute-phase/steps/executor-progress-policy.md:20-22,27-29 | .ai/workflows/execute-phase.md:479-493 | Replace "the pause in step 3 … asks the user" with: after the no-progress threshold, reconcile artifacts and continue the plan from its handoff in a fresh isolated checkout, without asking. |
| R-WF-117 | REPLACE | engineer/workflows/execute-phase/steps/executor-progress-policy.md:39-43 | .ai/references/worktree-recovery-policy.md:23-38 | Replace the `kill and switch to inline execution` section with: a stalled isolated plan is re-attempted only in a fresh worktree; inline/primary-checkout execution is never offered. |

Done when:
- `grep -ci "asks the user\|inline execution" engineer/workflows/execute-phase/steps/executor-progress-policy.md` → 0

### engineer/workflows/execute-phase/steps/gap-closure-artifacts.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-118 | REPLACE | engineer/workflows/execute-phase/steps/gap-closure-artifacts.md:18-19,50 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the launcher and rename `gsd_run query find-phase`/`commit` to `engineer_run query` (both verbs exist in the Python runtime). |
| R-WF-119 | KEEP-UPSTREAM | engineer/workflows/execute-phase/steps/gap-closure-artifacts.md:3-52 | — | Keep the decimal-phase parent UAT/debug closure; its caller becomes verify-work, not execute-phase. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM_NAME" engineer/workflows/execute-phase/steps/gap-closure-artifacts.md` → 0

### engineer/workflows/execute-phase/steps/partial-wave.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-120 | REPLACE | engineer/workflows/execute-phase/steps/partial-wave.md:5-6 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the launcher and rename to `engineer_run query phase-plan-index`. |
| R-WF-121 | REMOVE | engineer/workflows/execute-phase/steps/partial-wave.md:11 | — | Delete the `--gaps-only` filter rule. |
| R-WF-122 | REPLACE | engineer/workflows/execute-phase/steps/partial-wave.md:19-26 | .ai/workflows/execute-phase.md:19-20,776-792 | Replace the `/gsd:execute-phase` next-command block with a completion report listing remaining waves and plans, with no command hand-off. |

Done when:
- `grep -c "gsd_run\|/gsd:\|gaps-only" engineer/workflows/execute-phase/steps/partial-wave.md` → 0

### engineer/workflows/execute-phase/steps/per-plan-executor-routing.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-123 | REPLACE | engineer/workflows/execute-phase/steps/per-plan-executor-routing.md:23 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the launcher with the `_runtime.snippet.sh` launcher. |
| R-WF-124 | REPLACE | engineer/workflows/execute-phase/steps/per-plan-executor-routing.md:5,10,16,27,31,46 | .ai/workflows/execute-phase.md:47 | Replace default `gsd-executor` with `executor` and `gsd_run` with `engineer_run` (`resolve-agent` exists in the Python runtime). |
| R-WF-125 | STITCH | after engineer/workflows/execute-phase/steps/per-plan-executor-routing.md:33 | .ai/workflows/execute-phase.md:60-70 | Add: resolve model and effort for the routed `EXECUTOR_TYPE` with `resolve-model`/`resolve-effort` and omit `inherit`. |
| R-WF-126 | REMOVE | engineer/workflows/execute-phase/steps/per-plan-executor-routing.md:35-40,49-54 | — | Delete the orchestrator-worktree "cannot route subagent types" note and scope section; both isolation models use Agent dispatch. |
| R-WF-127 | REPLACE | engineer/workflows/execute-phase/steps/per-plan-executor-routing.md:56-77 | .ai/workflows/execute-phase.md:562-582 | Replace the auto-mode auto-approval / `_auto_chain_active` checkpoint rule with the local delegated-discretion-or-blocked checkpoint rule. |

Done when:
- `grep -c "gsd-executor\|gsd_run\|_auto_chain\|auto-mode\|auto-approv" engineer/workflows/execute-phase/steps/per-plan-executor-routing.md` → 0

### engineer/workflows/execute-phase/steps/per-plan-worktree-gate.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-128 | KEEP-UPSTREAM | engineer/workflows/execute-phase/steps/per-plan-worktree-gate.md:7-18 | .ai/workflows/execute-phase.md:359-362 | Keep the `PLAN_FILES`/`PLAN_DELETIONS`/`plan_id` extraction (feeds `--files`/`--deletions`). |
| R-WF-129 | REPLACE | engineer/workflows/execute-phase/steps/per-plan-worktree-gate.md:1-5,20-118 | .ai/RULES.md:258-262 | Replace the submodule intersection that sets `USE_WORKTREES_FOR_PLAN=false` with: a plan whose declared paths intersect a submodule (or are unparseable in a submodule project) is marked blocked for a person and never run unisolated. |
| R-WF-130 | REMOVE | engineer/workflows/execute-phase/steps/per-plan-worktree-gate.md:120-141 | — | Delete Part 2 (per-plan `dispatch-isolation --plan --force-isolation` sentinel re-record). |
| R-WF-131 | REPLACE | engineer/workflows/execute-phase/steps/per-plan-worktree-gate.md:143-145 | .ai/workflows/execute-phase.md:364-382 | Point `--files`/`--deletions` reuse at the local `worktree.record-agent "${plan_id}" --phase …` and `worktree.create "${plan_id}" --phase …` signatures. |

Done when:
- `grep -ci "use_worktrees\|force-isolation\|gsd_run\|_GSD_SHIM_NAME" engineer/workflows/execute-phase/steps/per-plan-worktree-gate.md` → 0

### engineer/workflows/execute-phase/steps/post-merge-gate.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-132 | REPLACE | engineer/workflows/execute-phase/steps/post-merge-gate.md:1-169 | .ai/workflows/execute-phase.md:584-608 | Replace the sniffed build/test gate, wave-failure handoff file and "Fix now / Continue" options with the local `run_checks` body (`engineer_run query verification.run-checks` on the integrated wave, receipt reuse, bounded correction, rerun after repair). |

Done when:
- `grep -c "gsd_run\|BUILD_CMD\|TEST_CMD\|gsd-handoff\|Fix now" engineer/workflows/execute-phase/steps/post-merge-gate.md` → 0
- `grep -c "verification.run-checks" engineer/workflows/execute-phase/steps/post-merge-gate.md` → ≥1

### engineer/workflows/execute-phase/steps/protected-branch.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-133 | REPLACE | engineer/workflows/execute-phase/steps/protected-branch.md:1-21 | .ai/workflows/execute-phase.md:256-262 | Replace the `branching_strategy: none` warn-and-continue with the preflight rule: if the current branch is the default branch, stop and open the session rather than execute; invoke it from `preflight`. |

Done when:
- `grep -c "gsd_run\|branching_strategy\|will continue here" engineer/workflows/execute-phase/steps/protected-branch.md` → 0

### engineer/workflows/execute-phase/steps/ready-wave-gate.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-134 | KEEP-UPSTREAM | engineer/workflows/execute-phase/steps/ready-wave-gate.md:1-24,34-37 | — | Keep the readiness skip; it never dispatches a plan over incomplete predecessors. |
| R-WF-135 | REPLACE | engineer/workflows/execute-phase/steps/ready-wave-gate.md:25-32 | .ai/workflows/execute-phase.md:787-789 | Replace "dispatch the ready wave, then re-run" with: list waiting plans and their predecessors under "Blocked for a person" in the closing report. |

Done when:
- `grep -c "then re-run" engineer/workflows/execute-phase/steps/ready-wave-gate.md` → 0

### engineer/workflows/execute-phase/steps/regression-gate.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-136 | REPLACE | engineer/workflows/execute-phase/steps/regression-gate.md:40 | .ai/workflows/execute-phase.md:589-607 | Replace the regression-gate-run read with `engineer_run query verification.run-checks` (configured checks cover prior-phase suites) and receipt reuse. |
| R-WF-137 | REPLACE | engineer/workflows/execute-phase/steps/regression-gate.md:50-66 | .ai/RULES.md:249-262 | Replace the three-option AskUserQuestion with no-ask routing: an in-scope regression is fixed via bounded correction/debugger; one changing locked acceptance is reported as a blocker. |

Done when:
- `grep -c "AskUserQuestion\|TEXT_MODE\|Options:" engineer/workflows/execute-phase/steps/regression-gate.md` → 0

### engineer/workflows/execute-phase/steps/regression-gate-run.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-138 | REPLACE | engineer/workflows/execute-phase/steps/regression-gate-run.md:13-60 | .ai/workflows/execute-phase.md:589-607 | Replace the launcher, `config-get workflow.test_command` sniffing, `normalize-test-command` and `run-with-timeout` (absent from engineer_run) with `engineer_run query verification.run-checks` and its bounded output tails. |
| R-WF-139 | KEEP-UPSTREAM | engineer/workflows/execute-phase/steps/regression-gate-run.md:62 | — | Keep "halt verification on a timed-out runner"; never silently continue. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM_NAME\|normalize-test-command\|run-with-timeout" engineer/workflows/execute-phase/steps/regression-gate-run.md` → 0

### engineer/workflows/execute-phase/steps/sequential-root-pin.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-140 | RENAME | engineer/workflows/execute-phase/steps/sequential-root-pin.md | — | Rename to `orchestrator-root-pin.md` and update the reference from `executor-isolation-dispatch.md` and execute-phase L785 replacement. |
| R-WF-141 | REPLACE | engineer/workflows/execute-phase/steps/sequential-root-pin.md:1-25 | .ai/workflows/execute-phase.md:40-42,434-437 | Re-scope the root-pin embed to `orchestrator-worktree`, substituting `{PINNED_ROOT}` with the plan's `worktree.create` path (single-quoted) from `engineer/references/worktree-path-safety.md`. |
| R-WF-142 | REMOVE | engineer/workflows/execute-phase/steps/sequential-root-pin.md:27-35 | — | Delete the wave-serialization rules for de-isolated plans and `USE_WORKTREES=false`. |

Done when:
- `test -f engineer/workflows/execute-phase/steps/orchestrator-root-pin.md && ! test -f engineer/workflows/execute-phase/steps/sequential-root-pin.md`
- `grep -rci "use_worktrees\|sequential mode\|gsd-core/" engineer/workflows/execute-phase/steps/orchestrator-root-pin.md` → 0

### engineer/workflows/execute-phase/steps/tdd-applicability-resolution.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-143 | REPLACE | engineer/workflows/execute-phase/steps/tdd-applicability-resolution.md:10-14 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the launcher and rename `gsd_run query phase.tdd-applicable` to `engineer_run`, porting that verb to the Python runtime first (it is absent, so this step would always halt). |
| R-WF-144 | REPLACE | engineer/workflows/execute-phase/steps/tdd-applicability-resolution.md:22-25 | .ai/workflows/execute-phase.md:386-456 | Replace the `AGENT_SKILLS` marker check with checks for the local executor template's conditionals (`handoff`, `context_window`, `ISOLATION`, `TDD_APPLICABLE`). |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM_NAME\|AGENT_SKILLS" engineer/workflows/execute-phase/steps/tdd-applicability-resolution.md` → 0

### engineer/workflows/execute-phase/steps/threat-id-gate.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-145 | REPLACE | engineer/workflows/execute-phase/steps/threat-id-gate.md:16,21-22 | — | Rename the `GSD ►` banner, rewrite `@~/.claude/gsd-core/references/planner-gap-closure.md` to `engineer/references/planner-gap-closure.md`, and `/gsd:execute-phase` to `/execute-phase`. |
| R-WF-146 | STITCH | engineer/workflows/execute-phase/steps/threat-id-gate.md:8-11 | .ai/workflows/execute-phase.md:618-624 | Add that renumbering must preserve canonical threat-tracker identities per `engineer/references/git-workflow.md#canonical-threat-tracking`. |

Done when:
- `grep -c "gsd-core/\|/gsd:\|GSD ►" engineer/workflows/execute-phase/steps/threat-id-gate.md` → 0

### engineer/workflows/execute-phase/steps/worktree-base-check.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-147 | REPLACE | engineer/workflows/execute-phase/steps/worktree-base-check.md:3-25 | .ai/workflows/execute-phase.md:302-306,458-461 | Replace the degrade-to-sequential rule with: a fork-base mismatch is caught by the executor's branch check (exit 42), the plan is blocked and its worktree preserved; isolation is never downgraded. |

Done when:
- `grep -ci "use_worktrees\|degrade\|sequential" engineer/workflows/execute-phase/steps/worktree-base-check.md` → 0

### engineer/workflows/execute-phase/steps/worktree-recovery-policy.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-148 | REPLACE | engineer/workflows/execute-phase/steps/worktree-recovery-policy.md:3-11 | .ai/references/worktree-recovery-policy.md:1-49 | Replace the body with the local policy, which adds "Cleanup needs merge evidence" (ancestor-of-HEAD rule, shared resources not isolated). |

Done when:
- `grep -c "Cleanup needs merge evidence" engineer/workflows/execute-phase/steps/worktree-recovery-policy.md` → 1

### engineer/workflows/execute-phase/steps/verify-phase-goal.md

Consumer changes: execute-phase no longer includes this file (R-WF rows above remove L1189-1305). It survives only if the verify-work slice routes `complete_session` to it; apply conventions here regardless.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-149 | REPLACE | engineer/workflows/execute-phase/steps/verify-phase-goal.md:4-13 | .ai/workflows/execute-phase.md:795-799 | Rewrite the header to say only verify-work includes this file; execute-phase hands off via `run_verify_work`. |
| R-WF-150 | REPLACE | engineer/workflows/execute-phase/steps/verify-phase-goal.md:24-34 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the launcher, delete `TDD_MODE` render-hooks (L29) and `--ws` parsing (L30-31), and resolve `VERIFIER_SKILLS` for `verifier` via `engineer_run`. |
| R-WF-151 | REPLACE | engineer/workflows/execute-phase/steps/verify-phase-goal.md:38-65 | .ai/RULES.md:258-262 | Replace the `verify:post` render-hooks dispatch and `/gsd:secure-phase` next-step text with: when `*-SECURITY.md` has `threats_open > 0`, record it as a blocker in the report. |
| R-WF-152 | REMOVE | engineer/workflows/execute-phase/steps/verify-phase-goal.md:67-112 | — | Delete the advisory code-review Skill/gate-hook step and TDD escalation; review is owned by execute-phase `code_review_gate` and the verify-work frozen batch. |
| R-WF-153 | REPLACE | engineer/workflows/execute-phase/steps/verify-phase-goal.md:114-126 | — | Remove `section_manifest` conditions so gap-closure-artifacts and regression-gate are read whenever they apply. |
| R-WF-154 | REPLACE | engineer/workflows/execute-phase/steps/verify-phase-goal.md:155-156 | .ai/workflows/execute-phase.md:55-72 | Replace `subagent_type="gsd-verifier"`/`model="{verifier_model}"` with `verifier` and inline resolve-model/resolve-effort (omit on `inherit`). |
| R-WF-155 | REPLACE | engineer/workflows/execute-phase/steps/verify-phase-goal.md:162 | .ai/workflows/execute-phase.md:463-466 | Replace the Codex orchestrator rule with the runtime-neutral ORCHESTRATOR RULE. |
| R-WF-156 | REPLACE | engineer/workflows/execute-phase/steps/verify-phase-goal.md:168-181 | — | Rename `gsd_run` to `engineer_run`, porting `verification.fingerprint` to the Python runtime (absent today) or dropping the fingerprint call. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM_NAME\|render-hooks\|gsd-verifier\|/gsd:\|section_manifest\|TDD_MODE" engineer/workflows/execute-phase/steps/verify-phase-goal.md` → 0
### engineer/workflows/plan-phase.md (+ commands/plan-phase.md)

Runtime note: `engineer_run` (port of `.ai/runtime/phase.py`) has no `state.planned-phase`, `roadmap.annotate-dependencies`, `check.decision-coverage-plan`, `check verify-command-paths`, `check verify-failure-directions`, `check ui-plan-gate`, `phase.mvp-mode`, `loop render-hooks`, `verify context-drift`, `verify codebase-drift`, `intel api-surface`, `teams-status`, `check auto-mode`; and `init.plan-phase` emits no `phase_status`, `prior_verify_commands`, `granularity`, `nyquist_validation_enabled`, `research_enabled`, `plan_checker_enabled`, `threat_id_duplicates`, `*_path` fields (it emits `paths`, `models`, `efforts`, `research_partial`, `has_spec`, `text_mode`). Rows below remove or replace every upstream call that depends on them.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-157 | REPLACE | engineer/workflows/plan-phase.md:1-7 | .ai/workflows/plan-phase.md:1-6 | Replace the `gsd:loop-host` header (plan:pre/plan:post points) with the local `workflow` header naming orchestrator, phase-researcher, planner, plan-checker. |
| R-WF-158 | REPLACE | engineer/workflows/plan-phase.md:8-10 | .ai/workflows/plan-phase.md:8-15 | Replace the purpose with the local purpose (preparer writes plans, checker verifies goal-backward, orchestrator routes only). |
| R-WF-159 | STITCH | after engineer/workflows/plan-phase.md:10 | .ai/RULES.md:88-98 | Insert an `<authority>` block stating that planning never grants implementation permission and that completion reports implementation awaits an explicit instruction. |
| R-WF-160 | REPLACE | engineer/workflows/plan-phase.md:12-20 | .ai/workflows/plan-phase.md:17-21 | Replace required_reading with the local set rewritten to `@engineer/references/...` (universal-anti-patterns, planner-guidance, failing-direction). |
| R-WF-161 | REPLACE | engineer/workflows/plan-phase.md:22-28 | .ai/workflows/plan-phase.md:23-29 | Replace the gsd-* agent list with phase-researcher, planner, plan-checker, codebase-mapper (drop gsd-pattern-mapper). |
| R-WF-162 | REPLACE | engineer/workflows/plan-phase.md:30-56 | .ai/workflows/plan-phase.md:31-48 | Replace `<runtime_compatibility>` (manager/autonomous, `--chain`/`--auto`, gsd-* names) with the local `<model_selection>` block using `engineer_run query resolve-model/resolve-effort` inline and omit-on-`inherit`. |
| R-WF-163 | REMOVE | engineer/workflows/plan-phase.md:60-62 | — | Delete the "do not create branches" invariant because `session.open` owns the phase branch. |
| R-WF-164 | REMOVE | engineer/workflows/plan-phase.md:64-66 | — | Delete the §0.5 Compact Content Gate and its `detail/elaboration.md` read. |
| R-WF-165 | REPLACE | engineer/workflows/plan-phase.md:68-100 | .ai/workflows/plan-phase.md:52-83 + .ai/workflows/_runtime.snippet.sh | Replace the gsd-tools launcher, flag regexes (GRAN/PRD/INGEST/RESEARCH_PHASE/REVIEWS/CHUNKED/GAPS_EXEC_FLAG), `GSD_WS`, `AGENT_SKILLS_*`, `MVP_MODE_CFG` with the runtime snippet, `engineer_run query phase.locate`, the quoted `cd` to the locator worktree and `init.plan-phase`. |
| R-WF-166 | REMOVE | engineer/workflows/plan-phase.md:102 | — | Delete the TDD-via-plan:pre-render-hooks paragraph. |
| R-WF-167 | REMOVE | engineer/workflows/plan-phase.md:106 | — | Delete the `prior_verify_commands` paragraph because `init.plan-phase` does not emit it. |
| R-WF-168 | REPLACE | engineer/workflows/plan-phase.md:108-116 | .ai/workflows/plan-phase.md:85-102 | Replace the parse list, `*_model` inherit rule, `*_path` list and `/gsd:new-project` error with the local field list (`paths`, `models`, `efforts`, `research_partial`, `agents_installed`/`missing_agents` stop) and banner. |
| R-WF-169 | STITCH | after engineer/workflows/plan-phase.md:116 | .ai/workflows/plan-phase.md:115-161 | Insert the `open_session` step (`session.open`/`session.adopt` routing, re-init inside the worktree, one-line session report, no delivery). |
| R-WF-170 | STITCH | engineer/workflows/plan-phase.md:118-120 | .ai/workflows/plan-phase.md:163-175 | Keep the closed-phase-gate step read at `engineer/workflows/plan-phase/steps/closed-phase-gate.md` and add the local `--gaps` exemption to its description. |
| R-WF-171 | REPLACE | engineer/workflows/plan-phase.md:124 | .ai/workflows/plan-phase.md:105-112 | Replace the flag list with `--skip-research`, `--research`, `--gaps`, `--text`, `--force` and set `MODE` to `standard` or `gap_closure`. |
| R-WF-172 | REMOVE | engineer/workflows/plan-phase.md:126-147 | — | Delete research-only mode (`--research-phase`/`--view`) because its step files are deleted. |
| R-WF-173 | REMOVE | engineer/workflows/plan-phase.md:149 | — | Delete `--granularity` because `init.plan-phase` emits no granularity. |
| R-WF-174 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:151 | .ai/workflows/plan-phase.md:110 | Text mode matches local `--text`/`text_mode`. |
| R-WF-175 | REMOVE | engineer/workflows/plan-phase.md:153-195 | — | Delete MVP/TDD/tracer/reversibility flag handling, Walking Skeleton and `--prd`/`--ingest` express-path argument parsing. |
| R-WF-176 | REPLACE | engineer/workflows/plan-phase.md:197 | .ai/commands/plan-phase.md:36 | Replace phase auto-detect with "phase number is required; `phase.locate` validates it". |
| R-WF-177 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:199-206 | — | Creates phase dir from `expected_phase_dir`; runtime emits it. |
| R-WF-178 | REMOVE | engineer/workflows/plan-phase.md:208-223 | — | Delete `CHUNKED_MODE` and the reviews-prerequisite step read. |
| R-WF-179 | REMOVE | engineer/workflows/plan-phase.md:225-244 | — | Delete §3 Validate Phase (`phase.locate` already validates), `phase.mvp-mode`, and the prd-express-gate/adr-ingest step reads. |
| R-WF-180 | REPLACE | engineer/workflows/plan-phase.md:246-294 | .ai/workflows/plan-phase.md:177-200 | Replace §4 with local `load_context` (read CONTEXT.md, extract decisions/canonical_refs/code_context/deferred, read SPEC.md when `has_spec`) but offer only "Discuss first"/"Cancel" when CONTEXT.md is missing (RULES.md:79-86), dropping `DISCUSS_MODE` assumptions and `/gsd:` hand-off text. |
| R-WF-181 | REMOVE | engineer/workflows/plan-phase.md:296-309 | — | Delete §4.5 AI-SPEC resolution (ai-integration-phase not kept). |
| R-WF-182 | REMOVE | engineer/workflows/plan-phase.md:311-348 | — | Delete §4.6 context-drift gate (`loop render-hooks plan:pre`, `verify context-drift`). |
| R-WF-183 | STITCH | after engineer/workflows/plan-phase.md:348 | .ai/workflows/plan-phase.md:202-253 | Insert `refresh_codebase_maps` (focus selection, `engineer_run query codebase.status`, codebase-mapper dispatch per missing/stale relevant map, `CURRENT_CODEBASE_MAP_PATHS`). |
| R-WF-184 | REPLACE | engineer/workflows/plan-phase.md:350-445 | .ai/workflows/plan-phase.md:255-368 | Replace §5 Handle Research with local `handle_research` (warranted-only decision without asking, phase-researcher dispatch with handoff/continuation blocks, return routing table, ≤2 partial continuations, `handoff.consume`), dropping research-only sections, `--auto` branches, teams-status and render-hooks research fragment. |
| R-WF-185 | REMOVE | engineer/workflows/plan-phase.md:447-475 | — | Delete §5.5 Nyquist validation strategy (`nyquist_validation_enabled`/`research_enabled` not emitted; validate-phase owns VALIDATION.md). |
| R-WF-186 | REPLACE | engineer/workflows/plan-phase.md:477-505 | .ai/workflows/plan-phase.md:535-543 | Replace the security render-hooks gate with one preparer constraint that new threat IDs continue after the phase's highest `T-{phase}-NN`, leaving reconciliation to `handle_preparer_return`. |
| R-WF-187 | REMOVE | engineer/workflows/plan-phase.md:507-590 | — | Delete §5.6 plan:pre capability dispatch, `check ui-plan-gate`, `AUTO_CHAIN`, `Skill(... --auto)` UI/AI dispatch and the `/gsd:ui-phase` exit. |
| R-WF-188 | REMOVE | engineer/workflows/plan-phase.md:592-605 | — | Delete §5.65 codebase-drift pre-check (replaced by `refresh_codebase_maps`). |
| R-WF-189 | REPLACE | engineer/workflows/plan-phase.md:607-613 | .ai/workflows/plan-phase.md:370-378 | Replace §6 with local `check_existing_plans` (Replace/Review/Cancel, call out plans that already have SUMMARY.md). |
| R-WF-190 | REPLACE | engineer/workflows/plan-phase.md:615-651 | .ai/workflows/plan-phase.md:90-94 | Replace the node `_gsd_field` extraction with reads from INIT `paths`, keeping only SPEC and the `*-UI-SPEC.md` lookup (644-645) and dropping REVIEWS/PATTERNS/SPIKE/SKETCH paths and the `--reviews` paragraph. |
| R-WF-191 | REMOVE | engineer/workflows/plan-phase.md:653-674 | — | Delete §7.5 Nyquist artifact check. |
| R-WF-192 | REMOVE | engineer/workflows/plan-phase.md:676-714 | — | Delete §7.8 gsd-pattern-mapper dispatch (agent not kept). |
| R-WF-193 | REMOVE | engineer/workflows/plan-phase.md:716-731 | — | Delete §7.9 intel API-SURFACE regeneration. |
| R-WF-194 | REMOVE | engineer/workflows/plan-phase.md:733-743 | — | Delete §7.95 spec-less probe fallback (depends on node `spec-section` helper). |
| R-WF-195 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:745-749 | — | Kept stall-detection step; rewrite path to `engineer/workflows/plan-phase/steps/`. |
| R-WF-196 | REPLACE | engineer/workflows/plan-phase.md:751-758 | .ai/workflows/plan-phase.md:381-391 | Replace the planner banner with `PLAN_INPUT_REVISION=$(git rev-parse HEAD)` capture and the planner banner. |
| R-WF-197 | REPLACE | engineer/workflows/plan-phase.md:762-895 | .ai/workflows/plan-phase.md:396-438 | Replace `<planning_context>` with the local one (repository, branch, input revision, mode, handoff block, CURRENT_CODEBASE_MAP_PATHS, 1M enrichment, requirement IDs, CLAUDE.md/AGENTS.md and `.agents/skills/`), dropping proven_verify_commands, intel hint, AGENT_SKILLS, review incorporation, render-hooks contributions, TRACER/REVERSIBILITY/MVP/WALKING_SKELETON/granularity and specless fallback. |
| R-WF-198 | REPLACE | engineer/workflows/plan-phase.md:822-834 | .ai/workflows/plan-phase.md:471-476 | Replace the tracked-source-paths block with the local version (no `.gsd/capabilities` mirrors). |
| R-WF-199 | REPLACE | engineer/workflows/plan-phase.md:836-861 | .ai/workflows/plan-phase.md:450-469 | Replace the failing-direction contract reference with `@engineer/references/methods/failing-direction.md` per the local block. |
| R-WF-200 | REPLACE | engineer/workflows/plan-phase.md:897-909 | .ai/workflows/plan-phase.md:440-448 | Replace `<downstream_consumer>` with the local list (`wave`, `depends_on`, `files_modified`, `requirements`, read_first/acceptance_criteria, must_haves, Artifacts section), consumed by `/execute-phase`. |
| R-WF-201 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:904-906 | — | SPEC/UI-SPEC must_haves lifts serve kept spec-phase/ui-phase; drop EDGE_ABSENT/PROHIB_ABSENT else-clauses. |
| R-WF-202 | STITCH | engineer/workflows/plan-phase.md:911-940 | .ai/workflows/plan-phase.md:486 | Keep upstream deep_work_rules and add rule 4 requiring `<verify>` with `<automated>` and `<fails_when>`. |
| R-WF-203 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:942-958 | — | Quality gate checklist matches local plan contract. |
| R-WF-204 | STITCH | after engineer/workflows/plan-phase.md:958 | .ai/workflows/plan-phase.md:489-508 | Insert the local `<constraints>` (no re-litigation, split/waves, observed edit scope, split recommendation, [ASSUMED] for unresearched questions, PLANNING PARTIAL at context limit) and the `<continuation>` block. |
| R-WF-205 | REPLACE | engineer/workflows/plan-phase.md:966-974 | .ai/workflows/plan-phase.md:509-520 | Replace the `gsd-planner` Agent call with `subagent_type="planner"`, inline model/effort from `models`/`efforts` omitted on `inherit`, and the local `<output>` contract (PLANNING COMPLETE/PARTIAL). |
| R-WF-206 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:963-965,976-978 | — | Kept stall-detection wait gate; add `## PLANNING PARTIAL` marker. |
| R-WF-207 | REMOVE | engineer/workflows/plan-phase.md:980-984 | — | Delete the chunked-planning-mode branch and step read. |
| R-WF-208 | REPLACE | engineer/workflows/plan-phase.md:986-993 | .ai/workflows/plan-phase.md:525-550 | Replace §9 return routing with local `handle_preparer_return` (`engineer_run query phase-plan-index`, stop on zero plans, canonical threat reconciliation, one PLANNING PARTIAL continuation without asking). |
| R-WF-209 | STITCH | engineer/workflows/plan-phase.md:995-1003 | — | Keep the 9a filesystem fallback via `engineer_run query find-phase` and delete its `detail/elaboration.md` reference. |
| R-WF-210 | REPLACE | engineer/workflows/plan-phase.md:1005-1007 | .ai/workflows/plan-phase.md:552-554 | Replace the 9b split menu with surfacing the split recommendation and stopping (roadmap change via `/phase --insert`). |
| R-WF-211 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:1009-1011 | — | Source-audit gap routing has no local equivalent; drop elaboration reference. |
| R-WF-212 | REPLACE | engineer/workflows/plan-phase.md:1013-1020 | .ai/workflows/plan-phase.md:557-569 | Replace the checker banner with `PLAN_REVIEWED_REVISION=$(git rev-parse HEAD)` capture and the plan-checker banner. |
| R-WF-213 | REMOVE | engineer/workflows/plan-phase.md:1022-1038 | — | Delete the `check verify-command-paths`/`verify-failure-directions` probes (absent from `engineer_run`). |
| R-WF-214 | REPLACE | engineer/workflows/plan-phase.md:1040-1110 | .ai/workflows/plan-phase.md:571-615 | Replace the checker prompt and `gsd-plan-checker` call with the local plan-checker dispatch (input/reviewed revisions, handoff block, goal-backward checks, canonical `## PLAN REVIEW` / `Verdict:` contract, inline model/effort). |
| R-WF-215 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:1112-1117 | — | Kept stall gate; change markers to `## PLAN REVIEW`. |
| R-WF-216 | REPLACE | engineer/workflows/plan-phase.md:1119-1126 | .ai/workflows/plan-phase.md:617-629 | Replace §11 with merged-continuation coverage and verdict routing (`needs-revision` revises, `approved` continues and shows INFO), deleting the thinking-partner elaboration line. |
| R-WF-217 | STITCH | engineer/workflows/plan-phase.md:1128-1136 | — | Keep 11a checker filesystem fallback with `engineer_run query find-phase`, `## PLAN REVIEW` markers and no elaboration reference. |
| R-WF-218 | REPLACE | engineer/workflows/plan-phase.md:1138-1295 | .ai/workflows/plan-phase.md:624-756 | Replace §12 with local `revision_loop` (correction `<revision_context>` packet, planner revision dispatch, integrate commit, fresh plan-checker, evidence reuse rules, map refresh via `codebase.status`, 3-iteration cap then user escalation), dropping REVIEWS.md conflict persistence and `/gsd:debug`. |
| R-WF-219 | REMOVE | engineer/workflows/plan-phase.md:1297-1301 | — | Delete §12.5 plan bounce. |
| R-WF-220 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:1303-1352 | — | Deterministic requirement-coverage backstop to the checker. |
| R-WF-221 | REMOVE | engineer/workflows/plan-phase.md:1354-1420 | — | Delete §13a decision-coverage gate (`check.decision-coverage-plan` absent; checker verifies locked decisions). |
| R-WF-222 | REPLACE | engineer/workflows/plan-phase.md:1432-1444 | .ai/workflows/plan-phase.md:758-848 | Replace §13c `roadmap.annotate-dependencies` with local `update_roadmap` (`roadmap.get-phase`, `phase-plan-index`, preconditions, single `roadmap.set-plans` call, post-write comparison, never hand-edit). |
| R-WF-223 | REPLACE | engineer/workflows/plan-phase.md:1422-1430 | .ai/workflows/plan-phase.md:850-861 | Replace §13b `state.planned-phase` with local `update_state` (`state.begin-phase --status "Ready to execute"`, `state.record-session`), ordered after update_roadmap. |
| R-WF-224 | REPLACE | engineer/workflows/plan-phase.md:1446-1454 | .ai/workflows/plan-phase.md:863-867 | Replace the `commit_docs`-gated commit with the unconditional `engineer_run query commit "docs(${padded_phase}): plan phase"` including STATE.md and ROADMAP.md. |
| R-WF-225 | REMOVE | engineer/workflows/plan-phase.md:1456-1504 | — | Delete §13e plan:post render-hooks gap-analysis dispatch. |
| R-WF-226 | REPLACE | engineer/workflows/plan-phase.md:1506-1508 | .ai/workflows/plan-phase.md:869-876 + .ai/RULES.md:93-97 | Replace §14 routing with the local completion report ending "Implementation awaits an explicit instruction to execute phase {N}" and no Next Up block. |
| R-WF-227 | REMOVE | engineer/workflows/plan-phase.md:1510-1512 | — | Delete §15 Auto-Advance Check and its auto-advance-check.md launch of execute-phase. |
| R-WF-228 | REMOVE | engineer/workflows/plan-phase.md:1516-1552 | — | Delete `<offer_next>` (Next Up, `/clear`, `/gsd:execute-phase`, `/gsd:review`). |
| R-WF-229 | KEEP-UPSTREAM | engineer/workflows/plan-phase.md:1554-1556 | — | Kept Windows troubleshooting step; rewrite path to `engineer/workflows/`. |
| R-WF-230 | STITCH | before engineer/workflows/plan-phase.md:1558 | .ai/workflows/plan-phase.md:894-905 | Insert the local `<anti_patterns>` block (no self-planning, no PR/merge, keep session open). |
| R-WF-231 | REPLACE | engineer/workflows/plan-phase.md:1559-1574 | .ai/workflows/plan-phase.md:907-919 | Replace success_criteria with the local list (maps fresh, preparer/checker, 3-iteration cap, roadmap matches, session joined and left open) and drop "User knows next steps". |
| R-WF-232 | REPLACE | engineer/workflows/plan-phase.md (all) | .ai/workflows/_runtime.snippet.sh | Replace every remaining `gsd_run` with `engineer_run`, `~/.claude/gsd-core/` and `gsd-core/` with `engineer/`, `/gsd:` with `/`, and `GSD ►` banners with `►`. |
| R-WF-233 | REMOVE | — | .ai/workflows/plan-phase.md:878-889 | Do not carry the local `## ▶ Next Up` / `/clear` then `/execute-phase` hand-off. |
| R-WF-234 | REMOVE | — | .ai/workflows/plan-phase.md:190-192 | Do not carry the "Plan anyway" option; RULES.md:79-86 requires discussion before planning. |
| R-WF-235 | RENAME | commands/plan-phase.md:2 | .ai/commands/plan-phase.md:2 | Rename `gsd:plan-phase` to `plan-phase`. |
| R-WF-236 | REPLACE | commands/plan-phase.md:4 | .ai/commands/plan-phase.md:4 | Replace argument-hint with `"<phase> [--skip-research] [--research] [--gaps] [--text] [--force]"`. |
| R-WF-237 | REPLACE | commands/plan-phase.md:16 | — | Replace `requires: [discuss-phase, phase, review, update]` with `requires: [discuss-phase, phase]`. |
| R-WF-238 | REPLACE | commands/plan-phase.md:23-36 | .ai/commands/plan-phase.md:15-28 | Replace the objective (research-only mode, gsd-planner/gsd-plan-checker) with the local six-step objective. |
| R-WF-239 | REPLACE | commands/plan-phase.md:38-41 | .ai/commands/plan-phase.md:30-32 | Replace `@~/.claude/gsd-core/...` execution_context with on-demand loading of `engineer/workflows/plan-phase.md`. |
| R-WF-240 | REPLACE | commands/plan-phase.md:47-65 | .ai/commands/plan-phase.md:34-42 | Replace the context/flag list with "phase required; located with `engineer_run query phase.locate` before `init.plan-phase`". |
| R-WF-241 | REPLACE | commands/plan-phase.md:67-70 | .ai/commands/plan-phase.md:44-61 | Replace the process with the MANDATORY read of `engineer/workflows/plan-phase.md` and append the local success_criteria. |

Done when:
- `grep -c "gsd_run\|gsd-tools\|gsd-core\|/gsd:\|gsd-planner\|gsd-plan-checker\|gsd-phase-researcher\|gsd-pattern-mapper" engineer/workflows/plan-phase.md commands/plan-phase.md` → 0 each
- `grep -c "auto_advance\|_auto_chain\|auto-advance\|--auto\|--chain\|/clear\|Next Up\|offer_next" engineer/workflows/plan-phase.md` → 0
- `grep -c "compact_content\|compact-content\|detail/elaboration\|section_manifest\|render-hooks\|auto-advance-check\|prd-express\|adr-ingest\|chunked-planning\|research-only\|reviews-prerequisite\|bounce\|mempalace\|graphify\|nyquist\|pattern-mapper\|api-surface\|planned-phase\|annotate-dependencies\|decision-coverage-plan" engineer/workflows/plan-phase.md` → 0
- `grep -n "phase.locate\|session.open\|session.adopt\|codebase.status\|roadmap.set-plans\|state.begin-phase\|resolve-model\|resolve-effort" engineer/workflows/plan-phase.md` → each ≥1
- `grep -n 'subagent_type="planner"\|subagent_type="plan-checker"\|subagent_type="phase-researcher"' engineer/workflows/plan-phase.md` → each ≥1
- `grep -n "awaits an explicit instruction" engineer/workflows/plan-phase.md` → ≥1
- `grep -n "^name: plan-phase$" commands/plan-phase.md` → 1

### engineer/workflows/plan-phase/steps/closed-phase-gate.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-242 | REPLACE | engineer/workflows/plan-phase/steps/closed-phase-gate.md:3,5,17 | .ai/workflows/plan-phase.md:164 | Derive the closed status from `engineer_run query roadmap.get-phase` status `Complete` (or add `phase_status` to `init.plan-phase`) because `engineer_run` emits no `phase_status`. |
| R-WF-243 | STITCH | engineer/workflows/plan-phase/steps/closed-phase-gate.md:17 | .ai/workflows/plan-phase.md:164 | Skip the gate when `--gaps` is passed. |
| R-WF-244 | REMOVE | engineer/workflows/plan-phase/steps/closed-phase-gate.md:18-28 | — | Delete the `--reviews` branch (reviews workflow not kept). |
| R-WF-245 | REPLACE | engineer/workflows/plan-phase/steps/closed-phase-gate.md:30-37 | .ai/workflows/plan-phase.md:166-172 | Replace the refusal text with the local message pointing at `/phase`, `/phase --insert {N}` and `--gaps`, retaining the `--force` override line rewritten to `/plan-phase`. |
| R-WF-246 | KEEP-UPSTREAM | engineer/workflows/plan-phase/steps/closed-phase-gate.md:40-43 | — | Explicit `--force` replan escape hatch with warning. |

Done when:
- `grep -c "/gsd:\|--reviews\|phase_status" engineer/workflows/plan-phase/steps/closed-phase-gate.md` → 0
- `grep -n "\-\-gaps" engineer/workflows/plan-phase/steps/closed-phase-gate.md` → ≥1

### engineer/workflows/plan-phase/steps/stall-detection-helpers.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-247 | REPLACE | engineer/workflows/plan-phase/steps/stall-detection-helpers.md:91 | .ai/workflows/_runtime.snippet.sh | Replace the gsd-tools launcher one-liner with the runtime snippet defining `engineer_run`. |
| R-WF-248 | REPLACE | engineer/workflows/plan-phase/steps/stall-detection-helpers.md:92,96,97 | — | Replace `gsd_run query config-get` with `engineer_run query config-get` (verb exists in the Python runtime). |
| R-WF-249 | RENAME | engineer/workflows/plan-phase/steps/stall-detection-helpers.md:6,10,24,50,64,111-174 | — | Rename `gsd_stall_should_recover`/`gsd_stall_watch` to `engineer_stall_should_recover`/`engineer_stall_watch` and update callers at engineer/workflows/plan-phase.md:976,1115,1212. |

Done when:
- `grep -c "gsd_run\|gsd-tools\|gsd_stall" engineer/workflows/plan-phase/steps/stall-detection-helpers.md engineer/workflows/plan-phase.md` → 0 each

### engineer/workflows/plan-phase/steps/windows-troubleshooting.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-250 | REPLACE | engineer/workflows/plan-phase/steps/windows-troubleshooting.md:18,22 | — | Replace `/gsd:plan-phase` with `/plan-phase`. |

Done when:
- `grep -c "/gsd:" engineer/workflows/plan-phase/steps/windows-troubleshooting.md` → 0

### engineer/workflows/discuss-phase.md (+ commands/discuss-phase.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-251 | REPLACE | engineer/workflows/discuss-phase.md:1-7 | .ai/workflows/discuss-phase.md:1-6 | Replace the `gsd:loop-host` header (discuss:pre/post points) with the local header producing CONTEXT.md and DISCUSSION-LOG.md. |
| R-WF-252 | STITCH | after engineer/workflows/discuss-phase.md:12 | .ai/RULES.md:79-92 | Insert an `<authority>` block: every phase is discussed before planning, the discussion records only actual questions/options/evidence/replies, and discussion completion never grants implementation permission. |
| R-WF-253 | REPLACE | engineer/workflows/discuss-phase.md:14-18 | .ai/workflows/discuss-phase.md:18-22 | Rewrite required_reading to `@engineer/references/...`. |
| R-WF-254 | REPLACE | engineer/workflows/discuss-phase.md:20-40 | .ai/workflows/discuss-phase.md:24-39 | Replace the progressive-disclosure table with the local one (all/auto/text/default + templates), dropping power, chain, batch, analyze and advisor rows and the byte-budget note. |
| R-WF-255 | REPLACE | engineer/workflows/discuss-phase.md:42-50 | .ai/workflows/discuss-phase.md:41-51 | Rename downstream consumers to phase-researcher and planner. |
| R-WF-256 | REMOVE | engineer/workflows/discuss-phase.md:112 | — | Delete the `/gsd:plan-phase --prd` express-path note. |
| R-WF-257 | REPLACE | engineer/workflows/discuss-phase.md:114-137 | .ai/workflows/discuss-phase.md:135-171 + .ai/workflows/_runtime.snippet.sh | Replace the gsd-tools launcher, `GSD_WS`, `AGENT_SKILLS_ADVISOR` and init with the runtime snippet, `engineer_run query phase.locate`, the quoted `cd` to the locator worktree and `init.phase-op`, and the `/progress` not-found message. |
| R-WF-258 | REPLACE | engineer/workflows/discuss-phase.md:128 | .ai/workflows/discuss-phase.md:174-178 | Replace the parse list with the local fields (`expected_phase_dir`, `goal`, `text_mode`, `paths`, `state`); drop `spec_path`. |
| R-WF-259 | REPLACE | engineer/workflows/discuss-phase.md:139-159 | .ai/workflows/discuss-phase.md:185-192 | Replace mode dispatch with all/auto/text/default only, deleting advisor detection (141-148), `--power` (150), `--chain` (154) and batch/analyze/advisor reads (156-158). |
| R-WF-260 | REPLACE | engineer/workflows/discuss-phase.md:182 | .ai/workflows/discuss-phase.md:224 | Route "no blocking rows" to `open_session` instead of `check_spec` (local 220-221 skips open_session; fix, do not copy). |
| R-WF-261 | STITCH | after engineer/workflows/discuss-phase.md:183 | .ai/workflows/discuss-phase.md:224-270 | Insert the `open_session` step (`session.open`/`session.adopt`, re-init with `init.phase-op` in the worktree, session line, no delivery) and end it with "continue to `check_spec`". |
| R-WF-262 | REPLACE | engineer/workflows/discuss-phase.md:186-189 | .ai/workflows/discuss-phase.md:273-283 | Locate the SPEC from `has_spec` and the INIT `artifacts` spec entry because `engineer_run` emits no `spec_path`. |
| R-WF-263 | REPLACE | engineer/workflows/discuss-phase.md:238-248 | .ai/workflows/discuss-phase.md:336-347 | Replace STATE.md cat, DECISIONS-INDEX and `find` with INIT `state` and `engineer_run query phases.list`, reading at most 3 prior CONTEXT.md files. |
| R-WF-264 | REMOVE | engineer/workflows/discuss-phase.md:252-262 | — | Delete spike/sketch findings detection and the `/gsd:spike`/`/gsd:sketch` notice (workflows not kept). |
| R-WF-265 | REPLACE | engineer/workflows/discuss-phase.md:264 | .ai/workflows/discuss-phase.md:353-354 | Drop "From Spike/Sketch Findings" from `<prior_decisions>`. |
| R-WF-266 | REMOVE | engineer/workflows/discuss-phase.md:296-301 | — | Delete `dispatch_discuss_pre_hooks` (`loop render-hooks discuss:pre`). |
| R-WF-267 | REMOVE | engineer/workflows/discuss-phase.md:323 | — | Delete the advisor-mode hand-off. |
| R-WF-268 | REPLACE | engineer/workflows/discuss-phase.md:356 | .ai/workflows/discuss-phase.md:467 | End present_gray_areas with "Continue to `discuss_areas`" only. |
| R-WF-269 | REPLACE | engineer/workflows/discuss-phase.md:360-373 | .ai/workflows/discuss-phase.md:471-479 | Replace mode list with `--auto`, default and `--text` overlay, deleting advisor (362), batch/analyze overlays (368-369) and overlay stacking (371). |
| R-WF-270 | REMOVE | engineer/workflows/discuss-phase.md:415-420 | — | Delete `dispatch_discuss_post_hooks` (`loop render-hooks discuss:post`). |
| R-WF-271 | REPLACE | engineer/workflows/discuss-phase.md:422-450 | .ai/workflows/discuss-phase.md:538-551 + .ai/RULES.md:93-97 | Replace confirm_creation with the decisions/deferred summary plus "Planning and implementation await your instruction", deleting Next Up, `/clear`, `/gsd:plan-phase`, `--chain` and `/gsd:ui-phase` lines. |
| R-WF-272 | STITCH | after engineer/workflows/discuss-phase.md:450 | .ai/workflows/discuss-phase.md:569-581 | Insert `record_decisions` (validate technology choices with a run spike; `engineer_run query state.add-decision ... --rationale ... --outcome "Accepted"`; a handful per phase). |
| R-WF-273 | STITCH | engineer/workflows/discuss-phase.md:453-462 | .ai/RULES.md:81-84 | State DISCUSSION-LOG.md is required, records only actual questions/options/evidence/replies, and the commit stops if it is missing. |
| R-WF-274 | REPLACE | engineer/workflows/discuss-phase.md:470-472 | .ai/workflows/discuss-phase.md:606-610 | Commit CONTEXT.md, DISCUSSION-LOG.md, `.planning/PROJECT.md` and `.planning/STATE.md` via `engineer_run query commit`. |
| R-WF-275 | REMOVE | engineer/workflows/discuss-phase.md:489-495 | — | Delete the `auto_advance` step and its chain.md read. |
| R-WF-276 | REPLACE | engineer/workflows/discuss-phase.md:499-520 | .ai/workflows/discuss-phase.md:628-649 | Replace success_criteria with the local list (Key Decisions recorded with validated technology choices, session joined and left open), deleting the `--chain`/`--auto` auto-advance and size-budget bullets (517-519). |
| R-WF-277 | REPLACE | engineer/workflows/discuss-phase.md (all) | .ai/workflows/_runtime.snippet.sh | Replace every remaining `gsd_run` with `engineer_run`, `~/.claude/gsd-core/` with `engineer/`, `/gsd:` with `/`, and gsd-* agent names with local names. |
| R-WF-278 | REMOVE | — | .ai/workflows/discuss-phase.md:552-565 | Do not carry the local `## ▶ Next Up` / `/clear` then `/plan-phase` hand-off. |
| R-WF-279 | RENAME | commands/discuss-phase.md:2 | .ai/commands/discuss-phase.md:2 | Rename `gsd:discuss-phase` to `discuss-phase`. |
| R-WF-280 | REPLACE | commands/discuss-phase.md:4 | .ai/commands/discuss-phase.md:4 | Replace argument-hint with `"<phase> [--all] [--auto] [--text]"`. |
| R-WF-281 | REMOVE | commands/discuss-phase.md:13-14 | — | Delete the context7 MCP tool entries. |
| R-WF-282 | REPLACE | commands/discuss-phase.md:15 | — | Replace `requires: [config, phase]` with `requires: [phase]` (config command not kept). |
| R-WF-283 | REPLACE | commands/discuss-phase.md:22-34 | .ai/commands/discuss-phase.md:15-31 | Replace the objective with the local seven steps including recording Key Decisions. |
| R-WF-284 | REPLACE | commands/discuss-phase.md:45-49 | .ai/commands/discuss-phase.md:44-51 | Replace context with `engineer_run query phase.locate`, `init.phase-op` and `todo.match-phase`. |
| R-WF-285 | REPLACE | commands/discuss-phase.md:51-71 | .ai/commands/discuss-phase.md:53-64 | Replace the gsd-tools mode routing (`--assumptions`, `workflow.discuss_mode`, list-phase-assumptions, discuss-phase-assumptions, power) with the single MANDATORY read of `engineer/workflows/discuss-phase.md` and the lazy-loading note. |
| R-WF-286 | REPLACE | commands/discuss-phase.md:73-81 | .ai/commands/discuss-phase.md:66-75 | Replace success_criteria with the local list. |

Done when:
- `grep -c "gsd_run\|gsd-tools\|gsd-core\|/gsd:\|gsd-phase-researcher\|gsd-planner\|gsd-advisor" engineer/workflows/discuss-phase.md commands/discuss-phase.md` → 0 each
- `grep -c "auto_advance\|_auto_chain\|chain.md\|--chain\|/clear\|Next Up\|render-hooks\|advisor\|power.md\|batch.md\|analyze.md\|--assumptions\|--prd\|spike\|sketch" engineer/workflows/discuss-phase.md commands/discuss-phase.md` → 0 each
- `grep -n '<step name="open_session">\|<step name="record_decisions">\|state.add-decision\|DISCUSSION-LOG' engineer/workflows/discuss-phase.md` → each ≥1
- `grep -n "never grants implementation" engineer/workflows/discuss-phase.md` → ≥1
- `grep -n "^name: discuss-phase$" commands/discuss-phase.md` → 1

### engineer/workflows/discuss-phase/modes/auto.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-287 | REPLACE | engineer/workflows/discuss-phase/modes/auto.md:5-8 | — | Reduce the lazy-load note to "Read this file when `--auto` is present" and drop the chain.md/auto_advance sentence. |
| R-WF-288 | REMOVE | engineer/workflows/discuss-phase/modes/auto.md:32 | — | Delete "After `write_context`, auto-advance to plan-phase via `modes/chain.md`." |
| R-WF-289 | REPLACE | engineer/workflows/discuss-phase/modes/auto.md:37-38 | — | Replace "then auto_advance" with "then `record_decisions`, `git_commit` and `update_state`, and stop". |
| R-WF-290 | REPLACE | engineer/workflows/discuss-phase/modes/auto.md:46-53 | — | Keep only "`--auto --text`: text overlay is a no-op" and delete the batch/analyze/power combination rules. |
| R-WF-291 | REMOVE | — | .ai/workflows/discuss-phase/modes/auto.md:5-8 | Do not carry the local chain.md/auto_advance lazy-load note. |
| R-WF-292 | REMOVE | — | .ai/workflows/discuss-phase/modes/auto.md:32 | Do not carry the local auto-advance-via-chain.md bullet. |
| R-WF-293 | REMOVE | — | .ai/workflows/discuss-phase/modes/auto.md:38 | Do not carry the local "then auto_advance" phrase. |
| R-WF-294 | REMOVE | — | .ai/workflows/discuss-phase/modes/auto.md:48-50 | Do not carry the local orphaned continuation lines left after deleting their bullets. |

Done when:
- `grep -c "chain\|auto_advance\|auto-advance\|batch\|analyze\|power" engineer/workflows/discuss-phase/modes/auto.md` → 0

### engineer/workflows/discuss-phase/modes/all.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-295 | REPLACE | engineer/workflows/discuss-phase/modes/all.md:14-15 | — | Replace with "- Never advances to planning; the discussion ends after `update_state`." |
| R-WF-296 | REMOVE | engineer/workflows/discuss-phase/modes/all.md:27-30 | — | Delete the `--all --chain` and batch/analyze combination rules, keeping only `--all --text` as a layered overlay. |
| R-WF-297 | REMOVE | — | .ai/workflows/discuss-phase/modes/all.md:14,26-27 | Do not carry the local orphaned continuation lines (including "auto-advance to plan/execute"). |

Done when:
- `grep -c "chain\|auto-advance\|batch\|analyze" engineer/workflows/discuss-phase/modes/all.md` → 0

### engineer/workflows/discuss-phase/modes/default.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-298 | REPLACE | engineer/workflows/discuss-phase/modes/default.md:6-8 | .ai/workflows/discuss-phase/modes/default.md:6-7 | Layer only the `--text` overlay (no `--batch`/`--analyze`). |
| R-WF-299 | REPLACE | engineer/workflows/discuss-phase/modes/default.md:101 | — | Point the thinking-partner signal list at `engineer/references/thinking-partner.md` (file exists) instead of deleting it. |

Done when:
- `grep -c "batch\.md\|analyze\|gsd-core" engineer/workflows/discuss-phase/modes/default.md` → 0

### engineer/workflows/discuss-phase/modes/text.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-300 | REPLACE | engineer/workflows/discuss-phase/modes/text.md:22-23 | .ai/workflows/discuss-phase/modes/text.md:22-23 | Use `/discuss-phase --text` and `engineer_run query config-set workflow.text_mode true`. |

Done when:
- `grep -c "gsd" engineer/workflows/discuss-phase/modes/text.md` → 0

### engineer/workflows/discuss-phase/templates/context.md (+ checkpoint.json, discussion-log.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-301 | REPLACE | engineer/workflows/discuss-phase/templates/context.md:65 | .ai/workflows/discuss-phase/templates/context.md:65 | Replace `gsd-planner` with `planner`. |
| R-WF-302 | REPLACE | engineer/workflows/discuss-phase/templates/context.md:70 | .ai/workflows/discuss-phase/templates/context.md:70 | Point the reversibility reference at `engineer/references/planner-reversibility.md`. |
| R-WF-303 | KEEP-UPSTREAM | engineer/workflows/discuss-phase/templates/checkpoint.json:1-18 | .ai/workflows/discuss-phase/templates/checkpoint.json:1-18 | Identical content; line endings only differ. |
| R-WF-304 | KEEP-UPSTREAM | engineer/workflows/discuss-phase/templates/discussion-log.md:1-52 | .ai/workflows/discuss-phase/templates/discussion-log.md:1-52 | Byte-identical to local. |

Done when:
- `grep -c "gsd" engineer/workflows/discuss-phase/templates/context.md` → 0
- `ls engineer/workflows/discuss-phase/modes/` → exactly `all.md auto.md default.md text.md`
### engineer/workflows/verify-work.md (+ commands/verify-work.md)

Decision: the upstream body is a conversational UAT loop (`extract_tests` → `create_uat_file` → `present_test` → `process_response` → `complete_session` → transition). It depends on runtime verbs the Python port does not register (`uat.classify-coverage`, `uat.render-checkpoint`, `uat.complete-session`, `phase uat-passed`, `frontmatter.set`, `audit-open`, `loop render-hooks`; verb table `.ai/runtime/phase.py:800-930`). Replace it with the local frozen-revision read-only batch. Human acceptance is carried by local `prepare_human_acceptance` and the UAT template, not by the upstream question loop.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-305 | REPLACE | engineer/workflows/verify-work.md:1-7 | .ai/workflows/verify-work.md:1-6 | Replace the `gsd:loop-host` header with the local `workflow` header naming verifier, integration-checker, doc-verifier and code-reviewer roles and producing `{NN}-VERIFICATION.md`. |
| R-WF-306 | REPLACE | engineer/workflows/verify-work.md:8-12 | .ai/workflows/verify-work.md:8-22 | Replace the conversational-UAT purpose with the local purpose, including the unattended `/ship {N}` hand-on, the no-`/clear`/no-resume rule and issue routing per RULES `#issues-found-while-working`. |
| R-WF-307 | REPLACE | engineer/workflows/verify-work.md:14-18 | .ai/workflows/verify-work.md:30-38 | Replace the `gsd-planner`/`gsd-plan-checker` agent list with the local list (verifier, integration-checker, doc-verifier, planner, executor, targeted-fixer). |
| R-WF-308 | STITCH | after engineer/workflows/verify-work.md:18 | .ai/workflows/verify-work.md:40-57 | Insert the local `<model_selection>` block so every dispatch passes `resolve-model`/`resolve-effort` inline and omits `inherit`. |
| R-WF-309 | REMOVE | engineer/workflows/verify-work.md:20-28 | — | Delete the `<philosophy>` "user tests, Claude records" block. |
| R-WF-310 | REPLACE | engineer/workflows/verify-work.md:30-32 | .ai/workflows/verify-work.md:24-28 | Replace the `@~/.claude/gsd-core/templates/UAT.md` template include with the local `<required_reading>` (universal-anti-patterns, honest-verifier, verifier-evidence-gate) at `engineer/references/` paths. |
| R-WF-311 | REMOVE | engineer/workflows/verify-work.md:36 | — | Delete the Compact Content Gate paragraph and its `verify-work/detail/elaboration.md` read. |
| R-WF-312 | REPLACE | engineer/workflows/verify-work.md:38-67 | .ai/workflows/verify-work.md:61-118 | Replace the upstream `initialize` (inline `gsd-tools.cjs` shim at L46, `--ws` parsing, `agent-skills`, MVP_MODE L61-66) with the local initialize: `_runtime.snippet.sh` launcher, `phase.locate`, `cd` to the locator worktree, `init.verify-work`, the parsed field list and the `summary_count == 0` exit. |
| R-WF-313 | STITCH | after engineer/workflows/verify-work.md:67 | .ai/workflows/verify-work.md:120-166 | Insert the local `open_session` step (`session.adopt`/`session.open` routing, re-run `init.verify-work` in the session worktree, "Do not deliver it here"). |
| R-WF-314 | REMOVE | engineer/workflows/verify-work.md:69-119 | — | Delete the `verify_pre_hooks` step (`loop render-hooks verify:pre`, gate/step dispatch, `VERIFY_PRE_PRODUCED`). |
| R-WF-315 | REPLACE | engineer/workflows/verify-work.md:121-166 | .ai/workflows/verify-work.md:168-177 | Replace `check_active_session` (active UAT table, "Wait for user response") with the local `check_existing_verification` currentness check against `verification-evidence.md`. |
| R-WF-316 | REMOVE | engineer/workflows/verify-work.md:168-170 | — | Delete the `gsd:section automated-ui-verification` manifest gate; the step is invoked from `prepare_human_acceptance` instead (next row). |
| R-WF-317 | STITCH | engineer/workflows/verify-work.md:168-170 (re-home) | .ai/workflows/verify-work.md:390-394 | At the start of the stitched `prepare_human_acceptance`, read `engineer/workflows/verify-work/steps/automated-ui-verification.md` when `{phase_dir}/*-UI-SPEC.md` exists, before the human script is prepared. |
| R-WF-318 | REPLACE | engineer/workflows/verify-work.md:172-182 | .ai/workflows/verify-work.md:179-192 | Replace `find_summaries` intro with the local `scan_phase_artifacts` step (SUMMARYs, plan `must_haves`, CONTEXT, ROADMAP criteria, visible mismatches reported before any agent). |
| R-WF-319 | KEEP-UPSTREAM | engineer/workflows/verify-work.md:183-215 | — | Keep the commit-claim reconciliation as a mismatch bullet inside `scan_phase_artifacts`, reporting findings as warnings for the verifier (executor writes `plan_head_before` only — `.ai/agents/coder.md:638`). Reason: summaries are claims; cheap git evidence. |
| R-WF-320 | REMOVE | engineer/workflows/verify-work.md:218-304 | — | Delete `extract_tests` (mvp-uat-framing read L219-221, `uat.classify-coverage`, produced-artefact seam, prose extraction, cold-start smoke injection). |
| R-WF-321 | REPLACE | engineer/workflows/verify-work.md:306-375 | .ai/workflows/verify-work.md:194-211 | Replace `create_uat_file` with the local `run_checks` step: capture `frozen_revision`, start `verification.run-checks` with receipt reuse alongside the provisional verifier. |
| R-WF-322 | REPLACE | engineer/workflows/verify-work.md:377-400 | .ai/workflows/verify-work.md:213-302 | Replace `present_test` with the local `spawn_verifier` step: one read-only batch (checks + provisional verifier + applicable integration-checker, doc-verifier, code-reviewer) against `frozen_revision`, the verifier `Agent(...)` prompt with issue-link audit ownership, the ORCHESTRATOR wait rule and handoff continuation. |
| R-WF-323 | REPLACE | engineer/workflows/verify-work.md:402-509 | .ai/workflows/verify-work.md:304-355 | Replace `process_response` (pass/skip/blocked/deferred/severity inference) with the local `check_integration` and `verify_docs` dispatch steps. |
| R-WF-324 | REPLACE | engineer/workflows/verify-work.md:511-526 | .ai/workflows/verify-work.md:357-371 | Replace `reconcile_gaps` and `resume_from_file` with the local `reconcile_evidence` step (join all results, resume the verifier, discard provisional decision after any source edit). |
| R-WF-325 | REPLACE | engineer/workflows/verify-work.md:528-545 | .ai/workflows/verify-work.md:373-417 | Replace the `complete_session` count/`uat.complete-session` block with the local `prepare_human_acceptance` step (UAT template, UAT issue variant, PENDING HUMAN acceptance, one author per issue). |
| R-WF-326 | REMOVE | engineer/workflows/verify-work.md:547-581 | — | Delete the Deferred Follow-Ups "[P] Promote to ROADMAP.md 999.x backlog / [K] Keep" prompt and its backlog commit. |
| R-WF-327 | REPLACE | engineer/workflows/verify-work.md:583-604 | .ai/workflows/verify-work.md:419-449 | Replace the "UAT Complete" table and issues routing with the local `persist_nonpass_report` and `handle_result` steps (human_needed reported as shipping blocker without asking). |
| R-WF-328 | REMOVE | engineer/workflows/verify-work.md:605-643 | — | Delete the `verify:post` render-hooks dispatch, the `Skill(gsd-secure-phase)` auto-dispatch and the SECURITY.md advancement block. |
| R-WF-329 | REMOVE | engineer/workflows/verify-work.md:644-731 | — | Delete the `human_needed` canonicalization (`phase uat-passed`, `frontmatter.set`), the `verify-phase-goal.md` re-dispatch via `init.execute-phase`, and the "blocked until canonical verification passes" prompt. |
| R-WF-330 | REPLACE | engineer/workflows/verify-work.md:733-748 | .ai/workflows/verify-work.md:511-583 | Replace "Auto-transition" (inline `transition.md`, next-step options) with the local `update_roadmap` (clean-tree check, `pre_bookkeeping_revision`, `phase.complete`), `close_requirements` (`requirements.close-phase`) and `update_state` (`state.record-session`, guarded `bookkeeping_commit`, `planning.validate` warn-only) steps. |
| R-WF-331 | STITCH | after the stitched update_state | .ai/workflows/verify-work.md:585-626 | Insert the local `final_frozen_reconciliation` step, including the bounded compensation link to `verification-evidence.md#compensating-a-failed-final-verification` and the ship-repair/return-to-caller paragraph (L618-625). |
| R-WF-332 | REMOVE | engineer/workflows/verify-work.md:751-781 | — | Delete the upstream `scan_phase_artifacts` (`audit-open` and the "Proceed anyway? [Y/n]" stop). |
| R-WF-333 | REPLACE | engineer/workflows/verify-work.md:783-785 | .ai/workflows/verify-work.md:451-465 | Replace `diagnose_issues` with the local `plan_gap_closure` routing preamble (no asking; in-scope fix now, out-of-scope stays in report, locked-decision change is a blocker; bounded correction dispatch; debugger for unknown causes). |
| R-WF-334 | REPLACE | engineer/workflows/verify-work.md:787-794 | .ai/workflows/verify-work.md:467-501 | Replace the `gsd-planner --gaps` dispatch with the local `planner` gap-closure `Agent(...)`, execution through `engineer/workflows/execute-phase.md`, mandatory re-verification and "Do not create todos". |
| R-WF-335 | REMOVE | engineer/workflows/verify-work.md:796-807 | — | Delete `verify_gap_plans` (`gsd-plan-checker` loop and detail § 2 read). |
| R-WF-336 | REPLACE | engineer/workflows/verify-work.md:809-864 | .ai/workflows/verify-work.md:504-509 | Replace the planner↔checker revision loop (REVISION_CONFLICT user question, "Force proceed / Provide guidance / Abandon") with the local verify→close→re-verify loop capped at 3 rounds that reports blockers without asking. |
| R-WF-337 | REPLACE | engineer/workflows/verify-work.md:867-892 | .ai/workflows/verify-work.md:628-647 | Replace "FIXES READY" + "Next Up `/clear` then `/gsd:execute-phase --gaps-only`" with the local `present_ready`, which invokes the `ship` skill on `passed` (except a refresh returned to an active `/ship`) and reports blockers otherwise. |
| R-WF-338 | REMOVE | engineer/workflows/verify-work.md:896-929 | — | Delete `<update_rules>` and `<severity_inference>` (UAT batched-write and severity rules). |
| R-WF-339 | STITCH | after engineer/workflows/verify-work.md:894 | .ai/workflows/verify-work.md:651-663 | Insert the local `<anti_patterns>` block, rewriting L657 "escalate to the user" to "report the outstanding gaps as the blocker" to match L507-508. |
| R-WF-340 | REPLACE | engineer/workflows/verify-work.md:931-943 | .ai/workflows/verify-work.md:665-677 | Replace the UAT success criteria with the local list ending in "On `passed`, `/ship` run in this same session". |
| R-WF-341 | RENAME | whole file (carried text) | .ai/workflows/verify-work.md:25-27,46-47,70-199,439-579 | Rename `phase_run` → `engineer_run`, `@~/.ai/references/` → `@engineer/references/` and `../templates/` links → `engineer/templates/` in every carried line. |
| R-WF-342 | REPLACE | commands/verify-work.md:1-14 | .ai/commands/verify-work.md:1-13 | Set `name: verify-work`, the local description and `argument-hint: "<phase>"`, add `AskUserQuestion`, drop `--ws`, and keep `requires: [execute-phase, phase]`. |
| R-WF-343 | REPLACE | commands/verify-work.md:20-26 | .ai/commands/verify-work.md:15-33 | Replace the conversational-UAT objective with the local frozen-revision objective. |
| R-WF-344 | REPLACE | commands/verify-work.md:28-31 | — | Replace `@~/.claude/gsd-core/workflows/verify-work.md` and `@~/.claude/gsd-core/templates/UAT.md` with `@engineer/workflows/verify-work.md` and `@engineer/templates/UAT.md`. |
| R-WF-345 | REPLACE | commands/verify-work.md:33-39 | .ai/commands/verify-work.md:39-48 | Replace the optional-phase/active-session context with the local required-phase context, keeping one "Phase number" line (drop the duplicate at L45). |
| R-WF-346 | REPLACE | commands/verify-work.md:41-44 | .ai/commands/verify-work.md:50-56 | Replace the process block with the local MANDATORY read-the-workflow instruction pointing at `engineer/workflows/verify-work.md`. |
| R-WF-347 | STITCH | after commands/verify-work.md:44 | .ai/commands/verify-work.md:59-71 | Append the local `<success_criteria>`, replacing L68 "recorded as todos with the user's agreement" with "left in VERIFICATION.md and the closing report, with no todos created". |

Done when:
- `grep -c "gsd_run\|gsd-core\|/gsd:\|render-hooks\|section_manifest\|compact-content\|detail/elaboration\|mvp-uat-framing\|transition\|gsd-planner\|gsd-plan-checker\|uat\.\(classify-coverage\|render-checkpoint\|complete-session\)\|uat-passed\|audit-open\|Next Up\|--gaps-only" engineer/workflows/verify-work.md` → 0
- `grep -c "phase_run\|~/.ai/" engineer/workflows/verify-work.md commands/verify-work.md` → 0
- `grep -n '<step name=' engineer/workflows/verify-work.md` lists, in order: initialize, open_session, check_existing_verification, scan_phase_artifacts, run_checks, spawn_verifier, check_integration, verify_docs, reconcile_evidence, prepare_human_acceptance, persist_nonpass_report, handle_result, plan_gap_closure, revision_loop, update_roadmap, close_requirements, update_state, final_frozen_reconciliation, present_ready
- `grep -n "present_ready" engineer/workflows/verify-work.md` is the last step and `grep -n "invoke the \`ship\` skill" engineer/workflows/verify-work.md` → ≥1
- `grep -n "subagent_type=\"\(verifier\|integration-checker\|doc-verifier\|planner\)\"" engineer/workflows/verify-work.md` → 4 hits
- `grep -n "verification-evidence.md#compensating-a-failed-final-verification\|requirements.close-phase\|phase.complete\|frozen_revision" engineer/workflows/verify-work.md` → each present
- `grep -n "automated-ui-verification.md" engineer/workflows/verify-work.md` → 1 hit inside `prepare_human_acceptance`
- `grep -c "Wait for user response\|Proceed anyway\|Force proceed\|escalate to the user" engineer/workflows/verify-work.md` → 0
- `grep -c "todos with the user's agreement\|gsd:verify-work\|--ws" commands/verify-work.md` → 0

### engineer/workflows/verify-work/steps/automated-ui-verification.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-348 | REPLACE | engineer/workflows/verify-work/steps/automated-ui-verification.md:4-7 | .ai/workflows/verify-work.md:390-394 | Replace the `state:ui-phase-active` gate prose with "Run from `prepare_human_acceptance` when `{phase_dir}/*-UI-SPEC.md` exists, to check each proposed human action against the actual UI before handoff." |
| R-WF-349 | REPLACE | engineer/workflows/verify-work/steps/automated-ui-verification.md:22-25 | .ai/workflows/verify-work.md:395-400 | Replace "automatically mark checkpoints as passed … present only those as manual UAT questions" with: record screenshots and comparisons as evidence for `reconcile_evidence`, mark unverifiable entry points BLOCKED, and keep `PENDING HUMAN acceptance` (automated checks never supply the human decision). |
| R-WF-350 | REPLACE | engineer/workflows/verify-work/steps/automated-ui-verification.md:34-35 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the `gsd-tools.cjs` shim line with the `_runtime.snippet.sh` launcher and call `engineer_run query config-get workflow.live_dom_uat --raw`. |
| R-WF-351 | REMOVE | engineer/workflows/verify-work/steps/automated-ui-verification.md:27,48 | — | Delete the `<!-- gsd:live-dom-families -->` section markers. |
| R-WF-352 | REPLACE | engineer/workflows/verify-work/steps/automated-ui-verification.md:50-58 | .ai/workflows/verify-work.md:390-399 | Replace "fall back to the standard manual checkpoint questions" with "fall back to the concrete human acceptance script from `prepare_human_acceptance`", and keep the `UI checkpoints:` summary line. |

Done when:
- `grep -c "gsd_run\|gsd-tools\|gsd:live-dom\|state:ui-phase-active\|manual UAT questions\|checkpoint questions" engineer/workflows/verify-work/steps/automated-ui-verification.md` → 0
- `grep -n "engineer_run query config-get workflow.live_dom_uat" engineer/workflows/verify-work/steps/automated-ui-verification.md` → 1 hit
- `grep -n "PENDING HUMAN" engineer/workflows/verify-work/steps/automated-ui-verification.md` → ≥1
- `test ! -e engineer/workflows/verify-work/steps/mvp-uat-framing.md && test ! -e engineer/workflows/verify-work/detail`

### engineer/workflows/ship.md (+ commands/ship.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-353 | REPLACE | engineer/workflows/ship.md:1-7 | .ai/workflows/ship.md:1-6 | Replace the `gsd:loop-host` header (ship:pre/ship:post points) with the local `workflow` header (code-reviewer, verifier; produces PR, merged base, closed session). |
| R-WF-354 | REPLACE | engineer/workflows/ship.md:8-10 | .ai/workflows/ship.md:8-18 | Replace the purpose with the local session-delivery purpose (merge only with explicit user authorization; no merge on a non-green verdict). |
| R-WF-355 | REPLACE | engineer/workflows/ship.md:12-14 | .ai/workflows/ship.md:20-22 | Replace "Read all files referenced by the invoking prompt" with `@engineer/references/universal-anti-patterns.md`. |
| R-WF-356 | REPLACE | engineer/workflows/ship.md:16-19 | .ai/workflows/ship.md:24-30 | Replace the `gsd-mempalace-curator` agent list with code-reviewer, verifier, debugger and targeted-fixer. |
| R-WF-357 | STITCH | after engineer/workflows/ship.md:19 | .ai/workflows/ship.md:32-49 | Insert the local `<model_selection>` block (inline `resolve-model`/`resolve-effort`, omit `inherit`, bounded correction dispatch). |
| R-WF-358 | REPLACE | engineer/workflows/ship.md:23-54 | .ai/workflows/ship.md:53-114 | Replace `initialize` (gsd shim L31, `--ws`, `init.phase-op`, `state.load` branching_strategy, `git.base-branch`) with the local initialize: flags `--draft`/`--review`/`--no-push`/`--no-merge`, `session.status` single-open-session inference, `phase.locate`, `cd` to session worktree, `init.ship`, identity re-check. |
| R-WF-359 | STITCH | after engineer/workflows/ship.md:54 | .ai/workflows/ship.md:116-125 | Insert the local `resolve_session` step (use the locator session; never `session.open` or fall back to the current branch). |
| R-WF-360 | REPLACE | engineer/workflows/ship.md:56-74 | .ai/workflows/ship.md:127-168 | Replace preflight item 1 with the local `phase.handoff` `ready: true` gate, canonical threat reconciliation, issue-link audit inspection and verification `passed` + currentness check. |
| R-WF-361 | REPLACE | engineer/workflows/ship.md:76-80 | .ai/workflows/ship.md:170-178 | Replace "ask user to commit or stash" with the local clean-session-worktree rule (commit the phase's work, report anything else as blocker). |
| R-WF-362 | REPLACE | engineer/workflows/ship.md:82-93 | .ai/workflows/ship.md:180-198 | Replace the protected-branch warning and "offer to create a branch now" with the local session-branch check and the non-empty `SESSION_BASE..SESSION_BRANCH` range check. |
| R-WF-363 | REPLACE | engineer/workflows/ship.md:95-105 | .ai/workflows/ship.md:200-229 | Replace remote/`gh` checks with the local remote, `gh auth status` and `verification.run-checks` receipt-reuse items. |
| R-WF-364 | REMOVE | engineer/workflows/ship.md:107-123,136-192 | — | Delete the `ship:pre` capability dispatch (`loop render-hooks ship:pre`, broken-windows ledger, generic gate/step evaluator). |
| R-WF-365 | KEEP-UPSTREAM | engineer/workflows/ship.md:124-134 | — | Keep the SECURITY.md `threats_open == 0` fail-closed check as a plain preflight item 8 run whenever `{phase_dir}/*-SECURITY.md` exists, without hook resolution. Reason: secure-phase is kept; open threats must block. |
| R-WF-366 | STITCH | before engineer/workflows/ship.md:195 | .ai/workflows/ship.md:232-298 | Insert the local `optional_review` (`--review` code-reviewer on the frozen revision), `prepare_shipping_record` (`state.record-session` "Preparing publication", skip when unchanged) and `final_reconciliation` steps ahead of the push. |
| R-WF-367 | REPLACE | engineer/workflows/ship.md:195-208 | .ai/workflows/ship.md:300-309 | Replace `push_branch` with the local session-worktree `push -u` that skips on `--no-push` and never force-pushes. |
| R-WF-368 | REPLACE | engineer/workflows/ship.md:210-264 | .ai/workflows/ship.md:311-350 | Replace the hand-built PR body sections with the local `generate_pr_body` (copy `engineer/templates/pull-request.md` File Template, `requirements.list`, `planning.validate` Record health, canonical issue URLs, issue-link audit comparison). |
| R-WF-369 | REMOVE | engineer/workflows/ship.md:266-313 | — | Delete the `ship.pr_body_sections` configured-sections extension. |
| R-WF-370 | REMOVE | engineer/workflows/ship.md:315-362 | — | Delete the TDD Audit section and the aggregate `gate-status:` trailer. |
| R-WF-371 | REPLACE | engineer/workflows/ship.md:365-384 | .ai/workflows/ship.md:352-375 | Replace `gh pr create` with `engineer_run query pr.open "${SESSION_BRANCH}" --title … --body-file … --draft`, always draft on first PR, plus the published-body readback for the audit. |
| R-WF-372 | STITCH | after the stitched create_pr | .ai/workflows/ship.md:377-404 | Insert the local `refresh_issue_link_audit` step (fresh non-author `verifier` dispatch with revision, PR head SHA, body/link snapshot and provider readback). |
| R-WF-373 | STITCH | after refresh_issue_link_audit | .ai/workflows/ship.md:406-441 | Insert the local `judge_checks` step: `pr.checks "${SESSION_BRANCH}" --wait 240` repeated up to 12 calls, the verdict table, at most 2 repair rounds, and `/verify-work` ship-repair/return-to-caller re-verification before re-push. |
| R-WF-374 | STITCH | after judge_checks | .ai/workflows/ship.md:443-527 | Insert the local `merge_and_close` step (skip on `--no-push`/`--no-merge`, merge only with explicit authorization asked once via AskUserQuestion, `pr.merge` readback, `pr.sync`, `phase.reconcile-todos` for folded TODOs, `state.sync-todos`, `session.close` without `--force`). |
| R-WF-375 | REMOVE | engineer/workflows/ship.md:386-477 | — | Delete the upstream `optional_review` (external `workflow.code_review_command` via `run-with-timeout` and the "Run a code review before merge?" AskUserQuestion). |
| R-WF-376 | REPLACE | engineer/workflows/ship.md:479-529 | .ai/workflows/ship.md:529-534 | Replace `track_shipping` (post-push `state.update` ship-note commit, `[ci skip]` push, empty CI-trigger commit) with the local rule: no tracked post-push bookkeeping commit; report the `pr.open` URL. |
| R-WF-377 | REMOVE | engineer/workflows/ship.md:531-579 | — | Delete `ship_post_capability_dispatch` (`loop render-hooks ship:post`, mempalace curator, `Skill(gsd-… --auto)`). |
| R-WF-378 | REPLACE | engineer/workflows/ship.md:581-601 | .ai/workflows/ship.md:536-546,555-557 | Replace the report with the local PR/Base/Session/Verification/Checks/Merge fields plus the not-merged reason and open-session lines, dropping the "Next steps" list. |
| R-WF-379 | REMOVE | engineer/workflows/ship.md:605-611 | — | Delete `<offer_next>` (`/gsd:complete-milestone`, `/gsd:progress`, `/gsd:execute-phase {next}`). |
| R-WF-380 | STITCH | after engineer/workflows/ship.md:603 | .ai/workflows/ship.md:565-584 | Insert the local `<anti_patterns>` block. |
| R-WF-381 | REPLACE | engineer/workflows/ship.md:613-619 | .ai/workflows/ship.md:586-600 | Replace success criteria with the local list (no stray `</output>` from local L601). |
| R-WF-382 | RENAME | whole file (carried text) | .ai/workflows/ship.md:21,38-39,65-517 | Rename `phase_run` → `engineer_run` and `@~/.ai/`/`../references/`/`../templates/` links → `engineer/references/` and `engineer/templates/` in every carried line. |
| R-WF-383 | REPLACE | commands/ship.md:1-13 | .ai/commands/ship.md:1-13 | Set `name: ship`, the local description, `argument-hint: "[phase] [--draft] [--review] [--no-push] [--no-merge]"` (all four flags parsed at `.ai/workflows/ship.md:55-58`), add `Agent` to allowed-tools, and change `requires: [review, verify-work]` to `requires: [verify-work]` (`review` is not a kept command). |
| R-WF-384 | REPLACE | commands/ship.md:19-23 | .ai/commands/ship.md:15-38 | Replace the objective with the local 8-step objective (add `--no-merge` stops after PR open/update). |
| R-WF-385 | REPLACE | commands/ship.md:25-29 | .ai/commands/ship.md:40-60 | Replace the `@~/.claude/gsd-core/workflows/ship.md` include and trailing line with the local context (single-open-session inference, `phase.locate` before `init.ship`) and MANDATORY process reading `engineer/workflows/ship.md`. |
| R-WF-386 | STITCH | after commands/ship.md:29 | .ai/commands/ship.md:62-72 | Append the local `<success_criteria>`. |

Done when:
- `grep -c "gsd_run\|gsd-core\|/gsd:\|render-hooks\|mempalace\|TDD Audit\|gate-status\|pr_body_sections\|code_review_command\|run-with-timeout\|offer_next\|ci skip\|gh pr create\|windows status\|Next steps" engineer/workflows/ship.md` → 0
- `grep -c "phase_run\|~/.ai/" engineer/workflows/ship.md commands/ship.md` → 0
- `grep -n "pr.checks" engineer/workflows/ship.md` → 2 hits, both with `--wait 240`; `grep -n "up to 12 calls" engineer/workflows/ship.md` → 1; `grep -n "at most 2 rounds" engineer/workflows/ship.md` → 1
- `grep -n "pr.open .*\|--draft" engineer/workflows/ship.md` shows the `pr.open` call ending `--draft`
- `grep -n "session.close\|pr.merge\|pr.sync\|phase.reconcile-todos\|phase.handoff\|--no-merge" engineer/workflows/ship.md` → each present
- `grep -n '<step name=' engineer/workflows/ship.md` lists, in order: initialize, resolve_session, preflight_checks, optional_review, prepare_shipping_record, final_reconciliation, push_branch, generate_pr_body, create_pr, refresh_issue_link_audit, judge_checks, merge_and_close, track_shipping, report
- `grep -c "## What's Next\|\`/next\`\|\`/progress\`" engineer/workflows/ship.md` → 0
- `grep -n "argument-hint" commands/ship.md` shows `--no-merge`; `grep -c "gsd:ship\|review, verify-work" commands/ship.md` → 0

### Stale local lines not to carry (this slice)

- `.ai/commands/ship.md:4` — argument-hint omits `--no-merge`; fixed by the commands/ship.md frontmatter row.
- `.ai/workflows/ship.md:547-553` — `## What's Next` with `/next`/`/progress` suggestions; excluded from the report row.
- `.ai/workflows/ship.md:155` — "Run `/verify-work {N}` …" tells the user to run a command; carry as "Cannot ship Phase {N}: verification is {status}" blocker text only.
- `.ai/workflows/ship.md:600` — stray `</output>` closing tag.
- `.ai/workflows/verify-work.md:657` — "escalate to the user" contradicts L507-508 (report, do not ask).
- `.ai/commands/verify-work.md:68` — "recorded as todos with the user's agreement" contradicts no-todos rule (`.ai/workflows/verify-work.md:501,673`).
- `.ai/commands/verify-work.md:43,45` — duplicated "Phase number" line.
### engineer/workflows/quick.md (+ commands/quick.md)

Upstream `--full`/`--discuss`/`--research` paths go, because `quick/steps/discussion-phase.md` and `research-phase.md` are deleted. Quick keeps `--validate` and `--text` only. Every executor runs isolated, and the session is delivered by this workflow.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-387 | REPLACE | engineer/workflows/quick.md:1-13 | .ai/workflows/quick.md:8-16 | Replace the purpose with the local single-outcome purpose (planner + executor, `--validate` only). |
| R-WF-388 | STITCH | engineer/workflows/quick.md:15-17 | .ai/workflows/quick.md:18-21 | Add `@engineer/references/worktree-sessions.md` to required_reading. |
| R-WF-389 | REPLACE | engineer/workflows/quick.md:19-27 | .ai/workflows/quick.md:23-31 | Replace the gsd-* agent list with phase-researcher, planner, plan-checker, executor, verifier, code-reviewer. |
| R-WF-390 | STITCH | engineer/workflows/quick.md:28 (insert before `<process>` at 29) | .ai/workflows/quick.md:33-50 | Insert the `<model_selection>` block (resolve-model/resolve-effort inline, omit on `inherit`). |
| R-WF-391 | STITCH | engineer/workflows/quick.md:28 (insert before `<process>` at 29) | .ai/workflows/quick.md:52-57 | Insert the `<scope_guardrail>` block, ending at local line 57. |
| R-WF-392 | REPLACE | .ai/workflows/quick.md:58 (do not carry) | .ai/RULES.md:255-260 | Do not carry "New capability ... is a todo (`/capture`)". Write "record it in the SUMMARY Deferred section" instead. |
| R-WF-393 | REPLACE | engineer/workflows/quick.md:30-113 | .ai/workflows/quick.md:63-110 | Replace flag parsing, the gsd launcher and the banners with local `parse_arguments` (`--validate`, `--text`, `_runtime.snippet.sh` + `engineer_run query init.quick`, agents_installed stop). |
| R-WF-394 | REMOVE | engineer/workflows/quick.md:117-149 | — | Delete the Step 2 gsd init, the agent-skills calls, the STATE/PROJECT path derivation and the `USE_WORKTREES`/`RUNTIME` config reads. |
| R-WF-395 | REMOVE | engineer/workflows/quick.md:151-165 | .ai/workflows/quick.md:363 | Delete the dispatch-isolation-gate read and the `USE_WORKTREES`-conditional reap-orphans, because isolation resolves at `execute` via `dispatch-isolation --plan`. |
| R-WF-396 | KEEP-UPSTREAM | engineer/workflows/quick.md:167-181 | — | Keep the submodule path parse (a safety guard for isolated commits). |
| R-WF-397 | REPLACE | engineer/workflows/quick.md:183 | .ai/RULES.md:262-265 | Replace "re-run with `workflow.use_worktrees=false`" with "mark the task blocked and list it for a human". |
| R-WF-398 | REPLACE | engineer/workflows/quick.md:185-187 | .ai/workflows/quick.md:99-100 | Replace the `/gsd:new-project` error with a stop that tells the user to run `/new-project` (or `/onboard`). |
| R-WF-399 | STITCH | engineer/workflows/quick.md:189 (after Step 2) | .ai/workflows/quick.md:114-125 | Insert the `check_open_tasks` step (show open tasks from init, start new or resume). |
| R-WF-400 | REPLACE | engineer/workflows/quick.md:191-248 | .ai/workflows/quick.md:127-154 | Replace Step 2.5 quick-task branching with `open_session` (`engineer_run query session.open quick`, run everything from `worktree`, stop on failure). |
| R-WF-401 | REPLACE | engineer/workflows/quick.md:252-281 | .ai/workflows/quick.md:156-167 | Replace the manual mkdir task-directory steps with `quick.create` (runtime allocates the id, directory and QUICK.md). |
| R-WF-402 | REMOVE | engineer/workflows/quick.md:285-295 | — | Delete the Step 4 ordering note and the discussion-phase/research-phase section-manifest reads. |
| R-WF-403 | REPLACE | engineer/workflows/quick.md:299-367 | .ai/workflows/quick.md:169-232 | Replace the planner spawn (render-hooks plan:pre, gsd-planner) with local `plan`, which records PLAN_INPUT_REVISION and dispatches planner with inline model/effort and the orchestrator rule. |
| R-WF-404 | STITCH | engineer/workflows/quick.md:368 (after planner) | .ai/workflows/quick.md:234-240 | Insert `reconcile_plan_threats` (canonical threat tracking, both modes). |
| R-WF-405 | REPLACE | engineer/workflows/quick.md:371-373 | .ai/workflows/quick.md:242-243 | Replace the section-manifest gate with "When `VALIDATE_MODE` is true, read and execute `engineer/workflows/quick/steps/plan-checker-loop.md`". |
| R-WF-406 | REPLACE | engineer/workflows/quick.md:377-379 | — | Replace the `state:worktrees-enabled` section gate with an unconditional read of `engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md`. |
| R-WF-407 | REMOVE | engineer/workflows/quick.md:385-419 | .ai/workflows/execute-phase.md:281-286 | Delete the #1941 base-check auto-degrade to `ISOLATION=none` and the `--force-isolation` re-persist, because isolation has no opt-out. |
| R-WF-408 | REPLACE | engineer/workflows/quick.md:421-431 | .ai/workflows/quick.md:351-374 | Replace manifest setup with local `execute` preamble (`quick.update --status in_progress`, `dispatch-isolation --raw --plan`, EXPECTED_BASE, `worktree.create` under orchestrator-worktree / `worktree.record-agent` under harness-worktree). |
| R-WF-409 | KEEP-UPSTREAM | engineer/workflows/quick.md:440-473 | — | Keep the harness branch-check embed and plan materialization (isolation guard); drop the CONTEXT/RESEARCH materialization lines 457-473 with the removed modes. |
| R-WF-410 | REPLACE | engineer/workflows/quick.md:474-478 | .ai/workflows/execute-phase.md:433-438 | Replace the `<sequential_execution>` branch with the `<project_root_pin>` block from `worktree-path-safety.md` for orchestrator-worktree. |
| R-WF-411 | REPLACE | engineer/workflows/quick.md:480-487 | .ai/workflows/quick.md:384-387 | Replace required_reading with the PLAN plus CLAUDE.md/AGENTS.md, without CONTEXT/RESEARCH. |
| R-WF-412 | REPLACE | engineer/workflows/quick.md:512,522 | .ai/RULES.md:262-265 | Replace the "Re-run with workflow.use_worktrees=false" / "rerun with worktrees disabled" guard text with "report blocked; a human decides". |
| R-WF-413 | REPLACE | engineer/workflows/quick.md:525-533 | .ai/workflows/quick.md:391-398 | Replace constraints with local ones: execute only planned tasks, commit atomically, write and commit `${QUICK_ID}-SUMMARY.md`, stop if the plan is wrong. Keep the submodule-guard bullet. |
| R-WF-414 | REPLACE | engineer/workflows/quick.md:535-538 | .ai/workflows/quick.md:405-410 | Dispatch `subagent_type="executor"` with inline model/effort and `isolation="worktree"` under harness-worktree. |
| R-WF-415 | REPLACE | engineer/workflows/quick.md:544-561 | .ai/workflows/quick.md:413-430 | Replace manifest append + cleanup with the local SUMMARY/commit check and `worktree.merge-wave` / `worktree.cleanup-wave --phase "quick-${QUICK_ID}"`, escalating `blocked`. |
| R-WF-416 | KEEP-UPSTREAM | engineer/workflows/quick.md:563 | — | Keep the isolated-run fail-safe (never recover on the primary checkout). |
| R-WF-417 | STITCH | engineer/workflows/quick.md:574 (after Step 6) | .ai/workflows/quick.md:433-440 | Insert `reconcile_summary_threats`. |
| R-WF-418 | STITCH | engineer/workflows/quick.md:574 (after threats) | .ai/workflows/quick.md:442-451 | Insert `run_checks` (`engineer_run query verification.run-checks`) and keep only "a failing check blocks completion; hand it to the executor". |
| R-WF-419 | REPLACE | .ai/workflows/quick.md:450 (do not carry "or stop for the user") | .ai/RULES.md:246-254 | Route a failing check as in-scope work for the executor/debugger; never stop to ask. |
| R-WF-420 | STITCH | engineer/workflows/quick.md:574 (after checks) | .ai/workflows/quick.md:453-469 | Insert `track_integrated_slice` (push session branch, `engineer_run query pr.open ... --draft`). |
| R-WF-421 | REMOVE | engineer/workflows/quick.md:577-628 | — | Delete Step 6.25 auto code review (`--full`-gated, loop render-hooks, `check evaluation-scope`, gsd-code-reviewer). |
| R-WF-422 | REPLACE | engineer/workflows/quick.md:632-634 | .ai/workflows/quick.md:471-472 | Replace the section-manifest gate with "When `VALIDATE_MODE` is true, read and execute `engineer/workflows/quick/steps/quick-verification.md`". |
| R-WF-423 | REPLACE | engineer/workflows/quick.md:638-702 | .ai/workflows/quick.md:499-512 | Replace hand-edited STATE.md "Quick Tasks Completed" tables (`quick-tasks-migrate`/`quick-tasks-append`) with `complete_task` (`quick.update --status complete`, `state.record-session`, `commit`). |
| R-WF-424 | REPLACE | engineer/workflows/quick.md:706-736 | .ai/workflows/quick.md:508-511 | Replace the Step 8 `commit_docs` staging block with the local single `engineer_run query commit ... --files "${QUICK_DIR}" .planning/STATE.md`. |
| R-WF-425 | STITCH | engineer/workflows/quick.md:737 (before completion) | .ai/workflows/quick.md:514-533 | Insert `deliver_session` (push, pr.open, pr.checks, merge only on an explicit instruction, pr.sync, session.close; no delivery when blocked). |
| R-WF-426 | REPLACE | engineer/workflows/quick.md:738-773 | .ai/workflows/quick.md:535-545 | Replace both completion banners and "Ready for next task: /gsd:quick" with the local completion block, ending at local line 545. |
| R-WF-427 | REMOVE | .ai/workflows/quick.md:546-555 (do not carry) | — | Do not carry the `## What's Next` multi-command list; the closing report ends at the record path. |
| R-WF-428 | STITCH | engineer/workflows/quick.md:775 (before `</process>` close) | .ai/workflows/quick.md:560-570 | Add the local `<anti_patterns>` block after `</process>`. |
| R-WF-429 | REPLACE | engineer/workflows/quick.md:777-793 | .ai/workflows/quick.md:572-584 | Replace success_criteria with the local list (runtime record, preparer plan, checks, session delivered). |
| R-WF-430 | REPLACE | commands/quick.md:2-4 | .ai/commands/quick.md:2-4 | Set `name: quick`, the local description and `argument-hint: "[list \| status <slug> \| resume <slug>] <description> [--validate] [--text]"`. |
| R-WF-431 | REMOVE | commands/quick.md:14 | — | Delete `requires: [phase]`. |
| R-WF-432 | REPLACE | commands/quick.md:21-45 | .ai/commands/quick.md:16-31 | Replace the objective (drop `--full`/`--discuss`/`--research`, planner + executor, the scope rule offering `/phase`); keep the three subcommand bullets. |
| R-WF-433 | REPLACE | commands/quick.md:47-49 | .ai/commands/quick.md:33-35 | Point execution_context at `engineer/workflows/quick.md`. |
| R-WF-434 | REPLACE | commands/quick.md:78-81,155-158 | — | Replace `gsd-tools query frontmatter.get` / `gsd-tools query init.quick` with `engineer_run query quick.list` / `engineer_run query init.quick`. |
| R-WF-435 | REPLACE | commands/quick.md:131 | — | Change `/gsd:quick resume {slug}` to `/quick resume {slug}`. |
| R-WF-436 | REPLACE | commands/quick.md:160 | .ai/workflows/quick.md:114-154 | Resume through the workflow's `check_open_tasks` + `open_session` (session reuse) instead of an ad-hoc resume context. |
| R-WF-437 | REPLACE | commands/quick.md:174 | — | Replace "STATE.md Quick Tasks Completed table is updated" with "`quick.update` records completion; STATE.md gets `state.record-session`". |
| R-WF-438 | REPLACE | commands/quick.md:182 | — | Replace `gsd-tools query frontmatter.get` with `engineer_run query quick.list`. |

Done when:
- `grep -c "gsd_run\|gsd-tools\|/gsd:\|gsd-planner\|gsd-executor\|gsd-verifier\|gsd-code-reviewer" engineer/workflows/quick.md commands/quick.md` → 0 each
- `grep -c "use_worktrees\|USE_WORKTREES\|ISOLATION=none\|sequential_execution\|section_manifest\|render-hooks\|--full\|--discuss\|--research\|quick-tasks-append" engineer/workflows/quick.md` → 0
- `grep -n "session.open quick\|quick.create\|reconcile_plan_threats\|reconcile_summary_threats\|verification.run-checks\|track_integrated_slice\|deliver_session\|session.close" engineer/workflows/quick.md` → each present
- `grep -c "resolve-model\|resolve-effort" engineer/workflows/quick.md` ≥ 2
- `grep -c -i "todo\|/capture\|What's Next\|Ready for next task" engineer/workflows/quick.md` → 0

### engineer/workflows/quick/steps/plan-checker-loop.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-439 | REMOVE | engineer/workflows/quick/steps/plan-checker-loop.md:12-23 | — | Delete the verify-command path probe (gsd launcher, `gsd_run check verify-command-paths`, which has no runtime verb, and its exit-code branch). |
| R-WF-440 | REPLACE | engineer/workflows/quick/steps/plan-checker-loop.md:25-83 | .ai/workflows/quick.md:245-277 | Replace the gsd-plan-checker dispatch with the local plan-checker dispatch (PLAN_REVIEWED_REVISION, canonical PLAN REVIEW contract, inline model/effort). |
| R-WF-441 | REPLACE | engineer/workflows/quick/steps/plan-checker-loop.md:85-86 | .ai/workflows/quick.md:279,342-348 | Route on `Verdict: approved \| needs-revision`, show INFO as advisory without revision, and keep the fail-closed BLOCKER count. |
| R-WF-442 | REPLACE | engineer/workflows/quick/steps/plan-checker-loop.md:88-141 | .ai/workflows/quick.md:279-340 | Replace the planner revision prompt (PLAN_PRE_HOOKS_JSON, gsd-planner) with the local correction-packet dispatch to planner, then a fresh plan-checker recheck. |
| R-WF-443 | KEEP-UPSTREAM | engineer/workflows/quick/steps/plan-checker-loop.md:143-165 | — | Keep REVISION_CONFLICT bounded handling (conflicts don't burn iterations). |
| R-WF-444 | REPLACE | engineer/workflows/quick/steps/plan-checker-loop.md:125 | — | Change `gsd-core/references/planner-revision.md` to `engineer/references/planner-revision.md`. |
| R-WF-445 | KEEP-UPSTREAM | engineer/workflows/quick/steps/plan-checker-loop.md:167-171 | .ai/workflows/quick.md:347-348 | Keep the two-iteration cap and escalation choice. |

Done when:
- `grep -c "gsd_run\|gsd-plan-checker\|gsd-planner\|PLAN_PRE_HOOKS_JSON\|AGENT_SKILLS\|GSD ►" engineer/workflows/quick/steps/plan-checker-loop.md` → 0
- `grep -n "subagent_type=\"plan-checker\"\|subagent_type=\"planner\"" engineer/workflows/quick/steps/plan-checker-loop.md` → both present

### engineer/workflows/quick/steps/quick-verification.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-446 | REPLACE | engineer/workflows/quick/steps/quick-verification.md:12-29 | .ai/workflows/quick.md:474-493 | Replace the gsd-verifier dispatch with the local `verifier` dispatch (inline model/effort, `## VERIFICATION Status: passed \| gaps_found \| human_needed`). |
| R-WF-447 | REPLACE | engineer/workflows/quick/steps/quick-verification.md:33-47 | .ai/workflows/quick.md:483-486 | Read status from the verifier's structured return; `engineer_run query verification.status` takes a phase, not `${QUICK_DIR}`. |
| R-WF-448 | REPLACE | engineer/workflows/quick/steps/quick-verification.md:52 | .ai/RULES.md:246-265 | On `gaps_found`, dispatch the executor (isolated) to fix in-scope gaps and re-verify once. Put out-of-scope gaps in the SUMMARY Deferred section. Never offer todos. |
| R-WF-449 | REPLACE | .ai/workflows/quick.md:495-496 (do not carry) | .ai/RULES.md:244-272 | Do not carry "ask whether to fix now or capture them as todos"; route per issues-found-while-working. |
| R-WF-450 | REPLACE | engineer/workflows/quick/steps/quick-verification.md:53 | .ai/RULES.md:262-265 | Re-run the verifier once on an unusable status, then mark the task blocked with the status named. Remove the menu. |
| R-WF-451 | REMOVE | engineer/workflows/quick/steps/quick-verification.md:55-65 | — | Delete the `next_action`/`next_command` rationale, which was tied to the upstream verification.status projection. |

Done when:
- `grep -c "gsd_run\|gsd-verifier\|AGENT_SKILLS\|GSD ►\|Accept as-is" engineer/workflows/quick/steps/quick-verification.md` → 0
- `grep -c -i "todo" engineer/workflows/quick/steps/quick-verification.md` → 0

### engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-452 | REPLACE | engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md:3-12 | .ai/workflows/execute-phase.md:281-286 | Make the step unconditional, because isolation is always on. Delete the `USE_WORKTREES === "false"` skip text and the CONTEXT/RESEARCH mentions. |
| R-WF-453 | REPLACE | engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md:15-19 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the gsd launcher with the `_runtime.snippet.sh` block and `engineer_run query config-get commit_docs`. |
| R-WF-454 | REMOVE | engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md:18,62 | — | Remove the `if [ "${USE_WORKTREES}" != "false" ]` wrapper and its closing `fi`. |
| R-WF-455 | REMOVE | engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md:27-32 | — | Remove the DISCUSS_MODE/RESEARCH_MODE path additions. |
| R-WF-456 | REMOVE | engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md:40-43 | — | Remove the `workflow.worktree_skip_hooks` `--no-verify` branch; never skip hooks. |

Done when:
- `grep -c "USE_WORKTREES\|gsd_run\|--no-verify\|DISCUSS_MODE\|RESEARCH_MODE" engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md` → 0

### engineer/workflows/next.md (+ commands/next.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-457 | REPLACE | engineer/workflows/next.md:1 | — | Change `@~/.claude/gsd-core/references/response-language-directive.md` to `@engineer/references/response-language-directive.md`. |
| R-WF-458 | REPLACE | engineer/workflows/next.md:3-6 | .ai/workflows/next.md:8-14 | Replace the purpose with the local purpose (decides and proceeds; `/progress` only reports). |
| R-WF-459 | REPLACE | engineer/workflows/next.md:14-38 | .ai/workflows/next.md:22-40 | Replace detect_state (gsd launcher, `state.json`) with `_runtime.snippet.sh` + `engineer_run query init.progress`, stopping on a missing roadmap with `/new-project` or `/phase`. |
| R-WF-460 | STITCH | engineer/workflows/next.md:40-46 | .ai/workflows/next.md:42-44 | State that `--force` overrides only on the user's explicit instruction, never by inference. |
| R-WF-461 | KEEP-UPSTREAM | engineer/workflows/next.md:47-86 | — | Keep gates 1-3 (checkpoint, error state, failed verification hard stops). |
| R-WF-462 | REPLACE | engineer/workflows/next.md:71 | — | Change "Run `/gsd:health`" to "Run `/progress` to see record health". |
| R-WF-463 | STITCH | engineer/workflows/next.md:87 (before line 88) | .ai/workflows/next.md:46-48 | Add the gate for uncommitted `.planning` changes (`git status --porcelain .planning` non-empty → report and stop). |
| R-WF-464 | STITCH | engineer/workflows/next.md:87 (before line 88) | .ai/workflows/next.md:49-50 | Add the gate for STATE.md blockers. |
| R-WF-465 | STITCH | engineer/workflows/next.md:87 (before line 88) | .ai/workflows/next.md:51-54 | Add the implementation-authority gate (never start execute-phase without explicit instruction; follow RULES phase authority). |
| R-WF-466 | REPLACE | engineer/workflows/next.md:91-153 | .ai/workflows/next.md:57-68 | Replace the roadmap.analyze/find-phase scan that auto-invokes execute-phase with `incomplete_phase` from init.progress. Present `/execute-phase {N}`, and run it only when implementation is explicitly authorized. |
| R-WF-467 | REPLACE | engineer/workflows/next.md:155-209 | .ai/workflows/next.md:70-75 | Replace the defer-to-backlog menu (hand-written 999.x ROADMAP entries) with the local finding-and-let-the-user-decide check. |
| R-WF-468 | REMOVE | engineer/workflows/next.md:211-232 | — | Delete spike_sketch_notice (spike/sketch not kept). |
| R-WF-469 | REPLACE | engineer/workflows/next.md:234-268 | .ai/workflows/next.md:77-98 | Replace Routes 1-8 (resume-work, plan-review-convergence) with the local artifact-state table driven by `engineer_run query init.phase-op`. |
| R-WF-470 | REPLACE | engineer/workflows/next.md:270-346 | .ai/workflows/next.md:100-116 | Replace show_and_execute (converge/cross-ai args, run without confirmation, `--auto` re-chain) with the local announce-then-act. Run discuss/plan/verify/milestone end to end; present execute and stop unless authorized; `--dry-run` reports only. |
| R-WF-471 | STITCH | engineer/workflows/next.md:348 (after `</process>`) | .ai/workflows/next.md:120-125 | Add the local `<anti_patterns>` block. |
| R-WF-472 | REPLACE | engineer/workflows/next.md:350-368 | .ai/workflows/next.md:127-133 | Replace success_criteria with the local list (authority-gated execute). |
| R-WF-473 | REPLACE | commands/next.md:1-35 | .ai/commands/next.md:1-57 | Replace the smart-entry launcher command with the local command body, executing `engineer/workflows/next.md` (smart-entry.md is not kept). |

Done when:
- `grep -c "gsd_run\|/gsd:\|SlashCommand\|--auto\|converge\|cross-ai\|smart-entry\|resume-work\|spike\|sketch" engineer/workflows/next.md commands/next.md` → 0
- `grep -n "git status --porcelain .planning" engineer/workflows/next.md` → present
- `grep -n -i "explicitly" engineer/workflows/next.md` → present in safety_gates and show_and_execute
- `grep -n "next.md" commands/next.md` → `engineer/workflows/next.md`

### engineer/workflows/progress.md (+ commands/progress.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-474 | REPLACE | engineer/workflows/progress.md:1 | — | Change the response-language reference to `@engineer/references/response-language-directive.md`. |
| R-WF-475 | REPLACE | engineer/workflows/progress.md:3-5 | .ai/workflows/progress.md:8-12 | Replace the purpose with the local report-and-route purpose. |
| R-WF-476 | REPLACE | engineer/workflows/progress.md:16-32 | .ai/workflows/progress.md:20-36 | Replace the launcher, `--forensic`/`--ws` parsing and the discuss_mode read with `_runtime.snippet.sh` + `engineer_run query init.progress` and the local field list. |
| R-WF-477 | REPLACE | engineer/workflows/progress.md:34-70 | .ai/workflows/progress.md:38-47 | Replace the init_incomplete/Route F `/gsd:new-project` + `/clear` branches with the local missing-roadmap stop. |
| R-WF-478 | REPLACE | engineer/workflows/progress.md:73-98 | .ai/workflows/progress.md:50-57 | Replace load/analyze_roadmap (`state-snapshot`, separate `roadmap.analyze`) with local `load`, using init.progress fields and the context-authority note. |
| R-WF-479 | REPLACE | engineer/workflows/progress.md:100-109 | .ai/workflows/progress.md:59-67 | Replace `summary-extract` (no runtime verb) with the local three-newest-summaries read. |
| R-WF-480 | REPLACE | engineer/workflows/progress.md:111-118 | .ai/workflows/progress.md:31-33 | Take position, `pending_todos` and `open_quick` from init.progress, and remove the debug-session count. |
| R-WF-481 | STITCH | engineer/workflows/progress.md:119 (before report) | .ai/workflows/progress.md:69-76 | Insert `record_health` (`engineer_run query planning.validate`, report only, never fix). |
| R-WF-482 | REPLACE | engineer/workflows/progress.md:126-131 | .ai/workflows/progress.md:84 | Use `engineer_run query progress.bar --raw` (runtime verb exists) and drop the `progress.json` reference. |
| R-WF-483 | REMOVE | engineer/workflows/progress.md:139-140 | — | Remove the Profile and Discuss mode report lines. |
| R-WF-484 | REPLACE | engineer/workflows/progress.md:159-160 | .ai/workflows/progress.md:103-105 | Change `/gsd:capture --list` to `/capture --list`, shown only when the count is non-zero. |
| R-WF-485 | REPLACE | engineer/workflows/progress.md:162-177 | .ai/workflows/progress.md:107-113 | Replace Open Windows (`gsd_run windows status`) and Active Debug Sessions with Open Quick Tasks and Record Health. |
| R-WF-486 | REMOVE | engineer/workflows/progress.md:185-187 | — | Delete the mvp-display section-manifest read (progress/steps not kept). |
| R-WF-487 | REPLACE | engineer/workflows/progress.md:192-245 | .ai/workflows/progress.md:123-149 | Replace the Route 0 jq scan with `incomplete_phase` from init.progress. Recommend `/execute-phase {N}` without `/clear` and stop. |
| R-WF-488 | KEEP-UPSTREAM | engineer/workflows/progress.md:247-259 | — | Keep the Step 1 live plan/summary counts via `engineer_run query find-phase`. |
| R-WF-489 | REPLACE | engineer/workflows/progress.md:261-272 | — | Grep only `status: partial` UAT (the local UAT template has no `diagnosed` state) and drop `uat_with_gaps`. |
| R-WF-490 | REMOVE | engineer/workflows/progress.md:274-316 | — | Delete the Step 1.6 cross-phase debt audit (`gsd_run query audit-uat` has no runtime verb). |
| R-WF-491 | REPLACE | engineer/workflows/progress.md:318-330 | — | Call `engineer_run query verification.status "${CURRENT_PHASE}"` (it takes a phase) and use only `.status`; it has no next_action/next_command. |
| R-WF-492 | KEEP-UPSTREAM | engineer/workflows/progress.md:332-345 | — | Keep the route table; delete its `uat_with_gaps` row. |
| R-WF-493 | REPLACE | engineer/workflows/progress.md:349-689 | .ai/workflows/progress.md:151-177 | Rewrite every route block as one recommended command without `/clear`, "Also available" lists or `${PROJECT_CODE}`/`${GSD_WS}`. Route V/V.gaps/V.human and E.2 recommend `/verify-work {N}`. |
| R-WF-494 | REMOVE | engineer/workflows/progress.md:445-469 | — | Delete Route E (diagnosed UAT gaps). |
| R-WF-495 | REMOVE | engineer/workflows/progress.md:374-379,580-585 | — | Delete the `UI hint` probes and ui-phase alternates; a single recommendation is required. |
| R-WF-496 | REPLACE | engineer/workflows/progress.md:691-698 | .ai/workflows/progress.md:180-189 | Replace edge_cases (`/gsd:resume-work`, plan-phase offers) with the local edge cases. |
| R-WF-497 | REMOVE | engineer/workflows/progress.md:700-702 | — | Delete the forensic-audit section-manifest read. |
| R-WF-498 | STITCH | engineer/workflows/progress.md:704 (after `</process>`) | .ai/workflows/progress.md:193-198 | Add the local anti_patterns, including "Don't start the recommended work". |
| R-WF-499 | REPLACE | engineer/workflows/progress.md:706-714 | .ai/workflows/progress.md:200-206 | Replace success_criteria, removing "User confirms before any action" and "Seamless handoff". |
| R-WF-500 | REPLACE | commands/progress.md:1-54 | .ai/commands/progress.md:1-53 | Replace with the local command (`name: progress`, `argument-hint: "[--no-resume]"`, no `--next`/`--do`/`--forensic`, no SlashCommand tool, execution via `engineer/workflows/progress.md`). |

Done when:
- `grep -c "gsd_run\|/gsd:\|/clear\|Also available\|forensic\|section_manifest\|audit-uat\|windows status\|summary-extract\|resume-work" engineer/workflows/progress.md` → 0
- `grep -n "planning.validate" engineer/workflows/progress.md` → present in record_health
- `grep -c "\-\-next\|\-\-do\|SlashCommand\|do.md\|next.md" commands/progress.md` → 0

### engineer/workflows/cleanup.md (+ commands/cleanup.md)

Decision: the local exact-approval worktree/branch cleanup fully REPLACEs GSD's milestone phase-archive flow. Phase/quick archival belongs to `clean-planning` (`planning.archive`, NEW FILE in another slice) and to `milestone.complete`. GSD's ungated `git branch -D` on gone upstreams contradicts the exact-approval contract, so branch pruning is REMOVED; `cleanup-apply` deletes only approved owned local branches.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-501 | REPLACE | engineer/workflows/cleanup.md:1-14 | .ai/workflows/cleanup.md:1-6 | Replace the purpose and required_reading with the local review-then-exact-approval purpose. |
| R-WF-502 | REMOVE | engineer/workflows/cleanup.md:17-22 | — | Delete the gsd launcher and the response_language read (cleanup uses the standalone `cleanup.py` CLI, not a runtime verb). |
| R-WF-503 | REMOVE | engineer/workflows/cleanup.md:25-91 | — | Delete identify_completed_milestones, determine_phase_membership and identify_quick_tasks. |
| R-WF-504 | REPLACE | engineer/workflows/cleanup.md:93-171 | .ai/workflows/cleanup.md:10-73 | Replace show_dry_run with `resolve_and_preview` (`python CLI cleanup-preview --repo`) and `exact_human_approval` (exact snapshot reply, approval envelope). |
| R-WF-505 | REMOVE | engineer/workflows/cleanup.md:173-203 | — | Delete archive_phases and archive_quick_tasks (`milestone.archive-quick` has no runtime verb; archival lives in clean-planning). |
| R-WF-506 | REMOVE | engineer/workflows/cleanup.md:205-219 | .ai/workflows/cleanup.md:82-88 | Delete prune_local_branches (unapproved `git branch -D`). |
| R-WF-507 | REPLACE | engineer/workflows/cleanup.md:221-247 | .ai/workflows/cleanup.md:75-103 | Replace commit/report with `apply_and_report` (`python CLI cleanup-apply --approval-file`, no planning commit, report removed/preserved/failed). |
| R-WF-508 | REPLACE | engineer/workflows/cleanup.md:251-262 | .ai/workflows/cleanup.md:34-49,94-99 | Rewrite success_criteria: preview read-only, real exact-snapshot reply, apply validated, outcomes reported, no override flag. |
| R-WF-509 | REPLACE | .ai/workflows/cleanup.md:11-18 | — | When stitching, change `../RULES.md`, `../references/cleanup.md` and the `.ai/hooks/cleanup.py` namespace text to the engineer-layout paths of RULES, cleanup reference and `cleanup.py`. |
| R-WF-510 | REPLACE | commands/cleanup.md:1-25 | .ai/commands/cleanup.md:1-21 | Replace with the local command (`name: cleanup`, no Write/AskUserQuestion, no `requires`, execute `engineer/workflows/cleanup.md`, exact approval). |

Done when:
- `grep -c "gsd_run\|milestones/v\|archive-quick\|git branch -D\|git fetch --prune\|AskUserQuestion" engineer/workflows/cleanup.md` → 0
- `grep -n "cleanup-preview\|cleanup-apply\|Approve exact cleanup snapshot" engineer/workflows/cleanup.md` → all present
- `grep -c "gsd-core\|gsd:cleanup" commands/cleanup.md` → 0

### engineer/workflows/complete-milestone.md (+ commands/complete-milestone.md)

`complete-milestone/steps/*` and `detail/` are not kept. Branch merge, tagging and release maps go. `milestone.complete` owns the entry and roadmap markers, and phase directories stay as evidence.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-511 | REPLACE | engineer/workflows/complete-milestone.md:1-5 | .ai/workflows/complete-milestone.md:9-13 | Replace the purpose with the local purpose (honest close, runtime-owned entry, no tag). |
| R-WF-512 | REPLACE | engineer/workflows/complete-milestone.md:7-15 | .ai/workflows/complete-milestone.md:15-17 | Replace required_reading (the milestone-archive template is no longer used) with the local line. |
| R-WF-513 | REMOVE | engineer/workflows/complete-milestone.md:17-36 | .ai/workflows/complete-milestone.md:197 | Delete `<archival_behavior>`, which covers REQUIREMENTS `git rm`, ROADMAP overwrite and UI screenshot cleanup. |
| R-WF-514 | REMOVE | engineer/workflows/complete-milestone.md:40 | — | Delete the Compact Content Gate line. |
| R-WF-515 | STITCH | engineer/workflows/complete-milestone.md:41 (new first step) | .ai/workflows/complete-milestone.md:21-49 | Insert `init_context` (`_runtime.snippet.sh` + `engineer_run query init.complete-milestone "${VERSION}"`, exit when there is no target milestone). |
| R-WF-516 | REPLACE | engineer/workflows/complete-milestone.md:42-73 | .ai/workflows/complete-milestone.md:51-72 | Replace the `audit-open` audit and acknowledge-all path with the per-phase `init.phase-op` artifact audit. |
| R-WF-517 | REPLACE | engineer/workflows/complete-milestone.md:75-108 | .ai/workflows/complete-milestone.md:74-87 | Replace the `init.manager` readiness check and override_closeout "Proceed anyway" with `ready_to_complete` and the no-force-path exit. |
| R-WF-518 | KEEP-UPSTREAM | engineer/workflows/complete-milestone.md:110-140 | — | Keep the requirements completion presentation (surfaces unchecked REQ ids). |
| R-WF-519 | REPLACE | engineer/workflows/complete-milestone.md:142-147 | .ai/workflows/complete-milestone.md:133-146 | Route unchecked requirements to `record_deferrals` instead of the proceed/audit-milestone/abort menu (audit-milestone not kept). |
| R-WF-520 | REMOVE | engineer/workflows/complete-milestone.md:149-180 | — | Delete the config-check and yolo/interactive mode blocks. |
| R-WF-521 | REPLACE | engineer/workflows/complete-milestone.md:184-209 | .ai/workflows/complete-milestone.md:89-98 | Take counts from `milestone_phases` and keep only the commit/diff stats (drop the LOC `find`). |
| R-WF-522 | REPLACE | engineer/workflows/complete-milestone.md:211-237 | .ai/workflows/complete-milestone.md:100-105 | Replace the `summary-extract` loop (no runtime verb) with reading each SUMMARY `**Delivered:**` line. |
| R-WF-523 | KEEP-UPSTREAM | engineer/workflows/complete-milestone.md:239-245 | — | Keep the note that milestone.complete writes the entry; change `gsd_run` to `engineer_run`. |
| R-WF-524 | REMOVE | engineer/workflows/complete-milestone.md:247-262 | — | Delete the early `init.complete-milestone` section-manifest probe and the project-md-evolution-review step read. |
| R-WF-525 | REPLACE | engineer/workflows/complete-milestone.md:264-324 | .ai/workflows/complete-milestone.md:107-121 | Replace archive_milestone with `engineer_run query milestone.complete "${VERSION}" --name "${NAME}" --confirm`, without `--archive-quick`, `--release-map` or `--no-archive-phases`. |
| R-WF-526 | STITCH | engineer/workflows/complete-milestone.md:325 (after archive) | .ai/workflows/complete-milestone.md:123-131 | Insert `review_entry` (improve MILESTONES.md prose, keep facts, add What's next text). |
| R-WF-527 | REMOVE | engineer/workflows/complete-milestone.md:326-438 | .ai/workflows/complete-milestone.md:197-198 | Delete reorganize_roadmap_and_delete_originals (hand ROADMAP rewrite, allow-shrink sentinel, safety commit, `git rm REQUIREMENTS.md`). |
| R-WF-528 | KEEP-UPSTREAM | engineer/workflows/complete-milestone.md:440-499 | — | Keep write_retrospective (hand-written narrative prose). Use `engineer/templates/retrospective.md` and `engineer_run query commit`. |
| R-WF-529 | STITCH | engineer/workflows/complete-milestone.md:500 (before update_state) | .ai/workflows/complete-milestone.md:133-146 | Insert `record_deferrals` (`state.add-deferred`, `requirements.set-status ... Deferred`). |
| R-WF-530 | REPLACE | engineer/workflows/complete-milestone.md:501-521 | .ai/workflows/complete-milestone.md:148-155 | Replace hand STATE.md edits with `state.record-session` and `state.add-decision`. |
| R-WF-531 | REMOVE | engineer/workflows/complete-milestone.md:523-534 | — | Delete handle_branches (squash/merge/delete branches; merging is `/ship`'s, on explicit instruction). |
| R-WF-532 | REMOVE | engineer/workflows/complete-milestone.md:536-538 | — | Delete the git-tag section read. |
| R-WF-533 | REMOVE | engineer/workflows/complete-milestone.md:540-544 | — | Delete push_release_tags (release-map step). |
| R-WF-534 | REPLACE | engineer/workflows/complete-milestone.md:546-558 | .ai/workflows/complete-milestone.md:157-169 | Replace the REQUIREMENTS-deletion commit with the local `engineer_run query commit` of the planning records plus `planning.validate` warnings. |
| R-WF-535 | REPLACE | engineer/workflows/complete-milestone.md:560-589 | .ai/workflows/complete-milestone.md:172-177 | Replace offer_next with a closing report (version, phases, plans, MILESTONES.md path), with no Next Up, `/clear` or tag line. |
| R-WF-536 | REMOVE | .ai/workflows/complete-milestone.md:179-188 (do not carry) | — | Do not carry the `## What's Next` command list. |
| R-WF-537 | KEEP-UPSTREAM | engineer/workflows/complete-milestone.md:593-612 | — | Keep milestone_naming and what_qualifies (guidance only). |
| R-WF-538 | STITCH | engineer/workflows/complete-milestone.md:592 (after `</process>`) | .ai/workflows/complete-milestone.md:193-199 | Add the local anti_patterns (no force path, no hand entry, no deleting phase dirs, no renumbering). |
| R-WF-539 | REPLACE | engineer/workflows/complete-milestone.md:614-643 | .ai/workflows/complete-milestone.md:201-208 | Replace success_criteria with the local list, omitting "User knows the next step". |
| R-WF-540 | REPLACE | commands/complete-milestone.md:2-11 | .ai/commands/complete-milestone.md:2-11 | Set `name: complete-milestone`, `argument-hint: "[milestone-version]"` and AskUserQuestion. Drop `type` and `requires`. |
| R-WF-541 | REPLACE | commands/complete-milestone.md:18-42 | .ai/commands/complete-milestone.md:14-37 | Replace the objective/context (no archive or tag claims), executing `engineer/workflows/complete-milestone.md` only. |
| R-WF-542 | REPLACE | commands/complete-milestone.md:44-125 | .ai/commands/complete-milestone.md:39-46 | Replace the inline 8-step process (audit-milestone, REQUIREMENTS delete, tag, next steps) with "Read and execute the workflow end to end". |
| R-WF-543 | REPLACE | commands/complete-milestone.md:127-148 | .ai/commands/complete-milestone.md:48-54 | Replace success_criteria and delete critical_rules. |

Done when:
- `grep -c "gsd_run\|/gsd:\|gsd-core\|section_manifest\|audit-open\|init.manager" engineer/workflows/complete-milestone.md` → 0
- `grep -c "handle_branches\|git tag\|push_release_tags\|release-map\|git rm\|allow-shrink\|archive-quick\|offer_next\|/clear" engineer/workflows/complete-milestone.md` → 0
- `grep -n "record_deferrals\|state.add-deferred\|milestone.complete\|planning.validate" engineer/workflows/complete-milestone.md` → all present
- `grep -c "audit-milestone\|git tag\|REQUIREMENTS.md\` deleted\|gsd:" commands/complete-milestone.md` → 0

### engineer/workflows/new-milestone.md (+ commands/new-milestone.md)

Seeds scanning is REMOVED because `plant-seed`/`list-seeds` are not kept and its only consumer was `--auto`. The roadmapper writing ROADMAP.md is replaced by runtime `phase.add`. Numbering never resets.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-544 | REPLACE | engineer/workflows/new-milestone.md:1-5 | .ai/workflows/new-milestone.md:8-12 | Replace the purpose with the local purpose. |
| R-WF-545 | REPLACE | engineer/workflows/new-milestone.md:13-18 | .ai/workflows/new-milestone.md:18-22 | Replace gsd-project-researcher/synthesizer/roadmapper with phase-researcher and codebase-mapper. |
| R-WF-546 | STITCH | engineer/workflows/new-milestone.md:19 (before `<process>`) | .ai/workflows/new-milestone.md:24-41 | Insert the `<model_selection>` block. |
| R-WF-547 | REPLACE | engineer/workflows/new-milestone.md:24-70 | .ai/workflows/new-milestone.md:45-81 | Replace argument parsing (`--reset-phase-numbers`, `--ws`, `.gsd-ws-arg`), the early section-manifest init and MILESTONE-CONTEXT.md with `load_context` (`_runtime.snippet.sh` + `engineer_run query init.new-milestone`, project/roadmap existence stop). |
| R-WF-548 | STITCH | engineer/workflows/new-milestone.md:71 (before §2) | .ai/workflows/new-milestone.md:83-95 | Insert `check_open_work` (open phases → close first / start anyway / cancel). |
| R-WF-549 | REPLACE | engineer/workflows/new-milestone.md:72-84 | .ai/workflows/new-milestone.md:97-107 | Replace MILESTONE-CONTEXT.md branching with local gather_goal questions; keep the upstream text-mode note. |
| R-WF-550 | REMOVE | engineer/workflows/new-milestone.md:86-133 | — | Delete §2.5 Scan Planted Seeds, including the `--auto` auto-select. |
| R-WF-551 | KEEP-UPSTREAM | engineer/workflows/new-milestone.md:135-169 | — | Keep version suggestion and pre-write confirmation (no conflict). |
| R-WF-552 | REMOVE | engineer/workflows/new-milestone.md:171-198 | — | Delete §4 (project-md-milestone-write section read; Evolution block citing `/gsd-transition`). |
| R-WF-553 | REPLACE | engineer/workflows/new-milestone.md:200-240 | .ai/workflows/new-milestone.md:153-165 | Replace `state.milestone-switch` (no runtime verb) with `engineer_run query milestone.create "${MILESTONE_NAME}" --goal "${MILESTONE_GOAL}"`. |
| R-WF-554 | REMOVE | engineer/workflows/new-milestone.md:242-298 | .ai/workflows/new-milestone.md:178,227 | Delete §6 (`phases.clear` archive, outgoing-milestone temp files, mid-flow commit), because numbering continues and archival is clean-planning's. |
| R-WF-555 | REMOVE | engineer/workflows/new-milestone.md:300-338 | .ai/workflows/new-milestone.md:59-61 | Delete §7 re-init, agent-skills, the npx installer warning and the reset-phase-safety section; use models/efforts from load_context. |
| R-WF-556 | KEEP-UPSTREAM | engineer/workflows/new-milestone.md:340-356 | — | Keep the research-or-skip question without persisting config. |
| R-WF-557 | REPLACE | engineer/workflows/new-milestone.md:358-461 | .ai/workflows/new-milestone.md:109-142 | Replace the four parallel gsd-project-researchers and the synthesizer with one `phase-researcher` dispatch (inline model/effort, RESEARCH PARTIAL usable). |
| R-WF-558 | KEEP-UPSTREAM | engineer/workflows/new-milestone.md:465-530 | .ai/workflows/new-milestone.md:144-151 | Keep requirements scoping. Add the local rules that REQ ids continue the existing sequence and that an explicit out-of-scope list is required. |
| R-WF-559 | REPLACE | engineer/workflows/new-milestone.md:531-538 | — | Replace the `.gsd-ws-arg`/`_gsd_field` path derivation with `paths.requirements` from init and `engineer_run query commit`. |
| R-WF-560 | REPLACE | engineer/workflows/new-milestone.md:541-633 | .ai/workflows/new-milestone.md:167-182 | Replace the gsd-roadmapper spawn and ROADMAP rewrite with `break_into_phases` (`engineer_run query phase.add ... --goal --requirements` per phase, runtime-derived numbers, no plans). |
| R-WF-561 | STITCH | engineer/workflows/new-milestone.md:634 (after phases) | .ai/workflows/new-milestone.md:184-191 | Insert `update_state` (`state.begin-phase`, `state.add-roadmap-evolution`). |
| R-WF-562 | STITCH | engineer/workflows/new-milestone.md:634 (after state) | .ai/workflows/new-milestone.md:193-198 | Insert the final `git_commit` of ROADMAP/REQUIREMENTS/PROJECT/STATE. |
| R-WF-563 | REMOVE | engineer/workflows/new-milestone.md:635-683 | — | Delete §10.5 (hand-editing todo frontmatter with `resolves_phase`); discuss-phase matches todos via `todo.match-phase`. |
| R-WF-564 | REPLACE | engineer/workflows/new-milestone.md:685-710 | .ai/workflows/new-milestone.md:200-209 | Replace §11 Done (artifact table, Next Up, `/clear`, `/gsd:discuss-phase`) with the local completion summary, ending at local line 209. |
| R-WF-565 | REMOVE | .ai/workflows/new-milestone.md:210-221 (do not carry) | — | Do not carry the local `## ▶ Next Up` / `/clear` then block. |
| R-WF-566 | STITCH | engineer/workflows/new-milestone.md:712 (after `</process>`) | .ai/workflows/new-milestone.md:226-232 | Add the local anti_patterns (continuous numbering, no plans, no ROADMAP hand edits). |
| R-WF-567 | REPLACE | engineer/workflows/new-milestone.md:714-730 | .ai/workflows/new-milestone.md:234-241 | Replace success_criteria (gsd-roadmapper, todo tagging) with the local list, omitting "User knows the next step". |
| R-WF-568 | REPLACE | commands/new-milestone.md:2-12 | .ai/commands/new-milestone.md:2-12 | Set `name: new-milestone` and `argument-hint: "<milestone-name>"`, without `--ws`, `--reset-phase-numbers` or `requires`. |
| R-WF-569 | REPLACE | commands/new-milestone.md:19-31 | .ai/commands/new-milestone.md:15-20 | Replace the objective; delete "After: `/gsd:plan-phase [N]`" (line 31). |
| R-WF-570 | REPLACE | commands/new-milestone.md:34-40 | — | Point execution_context at `engineer/workflows/new-milestone.md`, `engineer/references/questioning.md`, `engineer/references/ui-brand.md` and `engineer/templates/{project,requirements}.md`. |
| R-WF-571 | REPLACE | commands/new-milestone.md:48-51 | .ai/commands/new-milestone.md:24-31 | Replace the process with the local mandatory-read instruction; remove "roadmap approval" gate wording tied to the roadmapper. |

Done when:
- `grep -c "gsd_run\|/gsd:\|gsd-project-researcher\|gsd-research-synthesizer\|gsd-roadmapper\|gsd-ws-arg\|section_manifest" engineer/workflows/new-milestone.md` → 0
- `grep -c "reset-phase-numbers\|phases.clear\|milestone-switch\|SEED-\|resolves_phase\|--auto\|/clear\|Next Up" engineer/workflows/new-milestone.md` → 0
- `grep -n "check_open_work\|milestone.create\|phase.add\|state.begin-phase" engineer/workflows/new-milestone.md` → all present
- `grep -c "reset-phase-numbers\|--ws\|gsd:" commands/new-milestone.md` → 0

### engineer/workflows/milestone-summary.md (+ commands/milestone-summary.md)

The summary is read-only by default. It writes and commits only with `--write`, and it never mutates STATE.md.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-572 | REPLACE | engineer/workflows/milestone-summary.md:1 | — | Change the response-language reference to `@engineer/references/response-language-directive.md`. |
| R-WF-573 | REPLACE | engineer/workflows/milestone-summary.md:10-26 | .ai/workflows/milestone-summary.md:20-41 | Replace version resolution with `_runtime.snippet.sh` + `engineer_run query milestone.list` (current, else newest shipped), pointing at `/new-milestone` when there is none. |
| R-WF-574 | REPLACE | engineer/workflows/milestone-summary.md:28-80 | .ai/workflows/milestone-summary.md:43-60 | Replace archive-path guessing and the init.progress phase scan (lines 66-68 launcher) with `engineer_run query init.complete-milestone "${VERSION}"` → `milestone_phases`, using the local read budget. |
| R-WF-575 | KEEP-UPSTREAM | engineer/workflows/milestone-summary.md:82-116 | — | Keep the read-only git statistics fallbacks. |
| R-WF-576 | KEEP-UPSTREAM | engineer/workflows/milestone-summary.md:118-189 | .ai/workflows/milestone-summary.md:97-101 | Keep the seven-section template; require an explicit Known Gaps statement even when there are none. |
| R-WF-577 | REPLACE | engineer/workflows/milestone-summary.md:120 | .ai/workflows/milestone-summary.md:110-113 | Present the summary in the response by default. Write the file only when `--write` is passed. |
| R-WF-578 | REPLACE | engineer/workflows/milestone-summary.md:191-206 | .ai/workflows/milestone-summary.md:112-117 | Make write + `engineer_run query commit` conditional on `--write`; keep the overwrite guard. |
| R-WF-579 | REPLACE | engineer/workflows/milestone-summary.md:226-227 | — | Delete the next-steps suggestion (`/gsd:new-milestone`, `/gsd:progress`) and keep the Q&A offer. |
| R-WF-580 | REMOVE | engineer/workflows/milestone-summary.md:229-235 | — | Delete Step 9 `state.record-session`, because the summary is read-only. |
| R-WF-581 | STITCH | engineer/workflows/milestone-summary.md:235 (append) | .ai/workflows/milestone-summary.md:122-127 | Append the local anti_patterns (no ROADMAP-only summary, no unsupported verification claims, no hidden gaps). |
| R-WF-582 | REPLACE | commands/milestone-summary.md:2-5 | .ai/commands/milestone-summary.md:2-4 | Set `name: milestone-summary` and `argument-hint: "[milestone-version] [--write]"`; drop `type: prompt`. |
| R-WF-583 | REPLACE | commands/milestone-summary.md:18-55 | .ai/commands/milestone-summary.md:14-53 | Replace the objective, execution_context (`engineer/workflows/milestone-summary.md`) and success_criteria ("written when `--write`", no "STATE.md updated"). |

Done when:
- `grep -c "gsd_run\|/gsd:\|gsd-core\|state.record-session" engineer/workflows/milestone-summary.md` → 0
- `grep -n "\-\-write" engineer/workflows/milestone-summary.md commands/milestone-summary.md` → present in both
- `grep -c "STATE.md updated\|gsd:" commands/milestone-summary.md` → 0
### engineer/workflows/new-project.md (+ commands/new-project.md, new-project/steps/codebase-map-offer.md, onboard alias)

Decision: replace the GSD new-project body with the local onboard steps and keep the file name `new-project`. GSD `commands/onboard.md` (51 lines) and `engineer/workflows/onboard.md` (280 lines) are not in the kept lists, so they are deleted. That removes the name collision. Recommendation: reuse the freed `commands/onboard.md` slot as a thin alias that executes `engineer/workflows/new-project.md`. AGENTS.md, README and the local guides all say `/onboard`, so the alias keeps every existing reference valid without a second workflow.

Note on the runtime: the Python port exposes `init.onboard` (`.ai/runtime/lib/bundles.py:285`) and has no `init.new-project`. Keep calling `init.onboard`.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-584 | REPLACE | engineer/workflows/new-project.md:1-3 | .ai/workflows/onboard.md:1-15 | Replace the purpose with the local workflow header comment and purpose ("only workflow that creates the records every other workflow reads"). |
| R-WF-585 | REPLACE | engineer/workflows/new-project.md:5-7 | .ai/workflows/onboard.md:17-20 | Replace required_reading with the local list, rewriting `@~/.ai/references/` to `engineer/references/` (questioning.md and universal-anti-patterns.md both exist there). |
| R-WF-586 | REPLACE | engineer/workflows/new-project.md:9-14 | .ai/workflows/onboard.md:22-26 | Replace the gsd-project-researcher/gsd-research-synthesizer/gsd-roadmapper list with the local `phase-researcher` and `codebase-mapper` agent types. |
| R-WF-587 | STITCH | engineer/workflows/new-project.md:14 (insert after) | .ai/workflows/onboard.md:28-45 | Insert the local `<model_selection>` block (resolve-model/resolve-effort inline, omit on `inherit`) with `phase_run` renamed to `engineer_run`. |
| R-WF-588 | REMOVE | engineer/workflows/new-project.md:16-22 | — | Delete the `<auto_mode>` block and its section-manifest read of `new-project/steps/auto-mode-detection.md`. |
| R-WF-589 | REMOVE | engineer/workflows/new-project.md:26 | — | Delete the Compact Content Gate paragraph and its read of `new-project/detail/elaboration.md`. |
| R-WF-590 | REPLACE | engineer/workflows/new-project.md:28-103 | .ai/workflows/onboard.md:49-82 | Replace `## 1. Setup` (GSD_ARGS heredoc, gsd-tools launcher, agent-skills, npx install hint, instruction-file probe, init_incomplete branches) with the local `setup` step, using the `.ai/workflows/_runtime.snippet.sh` launcher, `engineer_run query init.onboard`, and the "Already set up" AskUserQuestion that routes to `/new-milestone`. |
| R-WF-591 | KEEP-UPSTREAM | engineer/workflows/new-project.md:105-109 | — | Keep the nested-`.git` guard (prevents nesting a repo inside a worktree), rewritten to derive `has_git` and the nesting state from `git rev-parse --show-toplevel` because `init.onboard` returns neither. |
| R-WF-592 | REPLACE | engineer/workflows/new-project.md:111-123 | .ai/workflows/onboard.md:84-127 | Replace `## 2. Brownfield Offer` (auto-mode skip, manifest-gated codebase-map-offer read, auto-mode-config read) with the local `detect_existing_code` step, which reads `engineer/workflows/new-project/steps/codebase-map-offer.md` unconditionally when there is existing code. |
| R-WF-593 | REPLACE | engineer/workflows/new-project/steps/codebase-map-offer.md:1-18 | .ai/workflows/onboard.md:92-126 | Replace the offer that exits to `/gsd:map-codebase` with the local inline `codebase-mapper` dispatch (STACK.md/ARCHITECTURE.md, inline model/effort, wait rule, `engineer_run query codebase.status` confirmation). |
| R-WF-594 | REMOVE | engineer/workflows/new-project.md:125-129 | — | Delete `## 2b. Prior Spike/Sketch Detection`; the spike/sketch workflows are not kept and the section reads `detail/elaboration.md`. |
| R-WF-595 | REPLACE | engineer/workflows/new-project.md:131-193 | .ai/workflows/onboard.md:129-165 | Replace `## 3. Deep Questioning` with the local `questioning` step, dropping the auto-mode skip and the `workflow.research_before_questions` branch. |
| R-WF-596 | REPLACE | engineer/workflows/new-project.md:195-300 | .ai/workflows/onboard.md:167-176 | Replace `## 4. Write PROJECT.md` (including the `/gsd-transition` evolution text at 277-289 and the early `docs: initialize project` commit) with the local `write_project` step and its no-placeholder rule. |
| R-WF-597 | REPLACE | engineer/workflows/new-project.md:302-683 | .ai/workflows/onboard.md:178-199 | Replace `## 5`, `## 5.1 Sub-Repo Detection` and `## 5.5 Resolve Model Profile` (config.json, compact_content, model_profile, ship.pr_body_sections, `/gsd:settings`, planning.sub_repos) with the local `workflow_preferences` step, which writes `.planning/config.yaml` through `engineer_run query config-set` (context_window and verification.commands). |
| R-WF-598 | REPLACE | engineer/workflows/new-project.md:684-788 | .ai/workflows/onboard.md:201-243 | Replace `## 6. Research Decision` (four parallel researchers, synthesizer, #222 self-heal) with the local optional single `phase-researcher` dispatch, the validated spike rule, and `engineer_run query state.add-decision ... --outcome "Accepted"`. |
| R-WF-599 | REPLACE | engineer/workflows/new-project.md:790-940 | .ai/workflows/onboard.md:245-258 | Replace `## 7. Define Requirements` (auto-mode category loop, gsd_run commit) with the local `define_requirements` step, which makes the out-of-scope list mandatory. |
| R-WF-600 | REMOVE | engineer/workflows/new-project.md:942-955 | — | Delete `## 7.5. Project Structure Mode` (the MVP/PROJECT_MODE prompt and its auto-mode default). |
| R-WF-601 | REPLACE | engineer/workflows/new-project.md:957-1122 | .ai/workflows/onboard.md:260-282 | Replace `## 8. Create Roadmap` (gsd-roadmapper spawn, approval loop, `generate-claude-md`) with the local `create_roadmap` step, using `engineer_run query milestone.create` and `phase.add` per phase, with no plans. |
| R-WF-602 | STITCH | engineer/workflows/new-project.md:1122 (insert after) | .ai/workflows/onboard.md:284-303 | Insert the local `initialize_state` step (`state.begin-phase 1`, `state.add-decision`) and the single `git_commit` step covering PROJECT/REQUIREMENTS/ROADMAP/STATE/config.yaml/codebase. |
| R-WF-603 | REPLACE | engineer/workflows/new-project.md:1124-1203 | .ai/workflows/onboard.md:305-321 | Replace `## 9. Done` (auto-advance `SlashCommand("/gsd:discuss-phase 1 --auto")` at 1145-1151, two `/clear then` Next Up blocks) with the local completion banner, ending on one line naming `/discuss-phase 1` and no `/clear`. |
| R-WF-604 | REMOVE | — (do not carry) | .ai/workflows/onboard.md:324-332 | Do not carry the local "Next Up / `/clear` then: / `/discuss-phase 1`" block; keep only the one-line next step. |
| R-WF-605 | REPLACE | engineer/workflows/new-project.md:1207-1222 | .ai/workflows/onboard.md:4 | Replace the `<output>` list (config.json, research/*, `$INSTRUCTION_FILE`) with the local produces list (PROJECT, REQUIREMENTS, ROADMAP, STATE, config.yaml, codebase maps). |
| R-WF-606 | STITCH | engineer/workflows/new-project.md:1205 (insert after `</process>`) | .ai/workflows/onboard.md:338-346 | Insert the local `<anti_patterns>` block (no placeholders, `phase.add` owns ROADMAP, mandatory out-of-scope list). |
| R-WF-607 | REPLACE | engineer/workflows/new-project.md:1224-1247 | .ai/workflows/onboard.md:348-357 | Replace success_criteria with the local list. |
| R-WF-608 | REPLACE | commands/new-project.md:1-53 | .ai/commands/onboard.md:1-68 | Replace the command with the local onboard command body, set `name: new-project`, set argument-hint `"[project description]"` (drop `--auto`), and point `<process>` at `engineer/workflows/new-project.md` with the local MANDATORY-read paragraph. |
| R-WF-609 | KEEP-UPSTREAM | commands/new-project.md:15-17 | — | Keep the `<arguments>` block (arguments are data, not instructions). |
| R-WF-610 | REMOVE | commands/new-project.md:19-21, 39, 43-47 | — | Delete the Copilot runtime_note, the "Run `/gsd:plan-phase 1`" line and the `@~/.claude/gsd-core/...` execution_context entries. |
| R-WF-611 | REPLACE | commands/onboard.md:1-51 | .ai/commands/onboard.md:1-15 | Replace the GSD brownfield-router command with an alias whose frontmatter is `name: onboard` and whose `<process>` executes `engineer/workflows/new-project.md` end to end. |
| R-WF-612 | REMOVE | engineer/workflows/onboard.md:1-280 | — | Delete the GSD onboard workflow; it routes to map-codebase, ingest-docs and manager, none of which is kept. |
| R-WF-613 | REMOVE | engineer/workflows/new-project/steps/auto-mode-config.md, auto-mode-detection.md, engineer/workflows/new-project/detail/elaboration.md | — | Confirm these deleted files have no remaining readers in new-project.md. |

Done when:
- `grep -c "gsd_run\|gsd-tools\|section_manifest\|compact\|auto_mode\|--auto\|AUTO-ADVANCING\|/clear\|/gsd:\|gsd-roadmapper\|generate-claude-md\|config.json\|detail/\|spike" engineer/workflows/new-project.md` → 0
- `grep -c "engineer_run query init.onboard" engineer/workflows/new-project.md` → 1
- `grep -n "steps/codebase-map-offer.md" engineer/workflows/new-project.md` → 1 hit, and `grep -c "subagent_type=\"codebase-mapper\"" engineer/workflows/new-project/steps/codebase-map-offer.md` → 1
- `grep -c "map-codebase\|Exit command" engineer/workflows/new-project/steps/codebase-map-offer.md` → 0
- `grep -n "phase.add\|milestone.create\|state.begin-phase\|state.add-decision\|resolve-effort" engineer/workflows/new-project.md` → each present
- `test ! -e engineer/workflows/onboard.md && test ! -e engineer/workflows/new-project/steps/auto-mode-config.md && test ! -e engineer/workflows/new-project/detail/elaboration.md`
- `grep -n "^name:" commands/new-project.md commands/onboard.md` → `new-project`, `onboard`; `grep -c "engineer/workflows/new-project.md" commands/onboard.md` → 1; `grep -c "--auto\|gsd" commands/new-project.md commands/onboard.md` → 0

### .ai/guides/PHASE-WORKFLOW.md (do not carry)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-614 | REMOVE | — (do not carry into any engineer/ or docs/ guide) | .ai/guides/PHASE-WORKFLOW.md:102 | Do not carry "Checkpoints go to the user."; checkpoints are decided within delegated discretion or left blocked without stopping the run (`.ai/workflows/execute-phase.md:562-582`, `.ai/RULES.md:244-272`). |
| R-WF-615 | REMOVE | — (do not carry) | .ai/guides/PHASE-WORKFLOW.md:116-117 | Do not carry "Gaps are either closed and re-verified, or recorded as todos with the user's agreement."; gaps are fixed or routed to SUMMARY Deferred with no todos created (`.ai/RULES.md:246-247`). |

Done when:
- `grep -rn "Checkpoints go to the user\|recorded as todos" engineer/ commands/ docs/` → 0 hits

### engineer/workflows/add-phase.md (+ commands/phase.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-616 | REPLACE | engineer/workflows/add-phase.md:1-4 | .ai/workflows/add-phase.md:1-12 | Replace the response-language include and purpose with the local header comment and purpose. |
| R-WF-617 | REPLACE | engineer/workflows/add-phase.md:13-28 | .ai/workflows/add-phase.md:20-39 | Replace parse_arguments with the local version that supports `--goal` and `--requirements`, with `/phase` usage strings. |
| R-WF-618 | REPLACE | engineer/workflows/add-phase.md:30-50 | .ai/workflows/add-phase.md:41-67 | Replace init_context (GSD_ARGS, gsd-tools launcher, `--ws`, `@file:`) with the `_runtime.snippet.sh` launcher plus `engineer_run query init.phase-op 0`, the "Run onboarding" error and the response_language rule. |
| R-WF-619 | REPLACE | engineer/workflows/add-phase.md:52-69 | .ai/workflows/add-phase.md:69-90 | Replace add_phase with the local call `engineer_run query phase.add "${description}" --goal "${goal}"`, which also extracts `goal` and keeps the checklist/Progress table text. |
| R-WF-620 | REPLACE | engineer/workflows/add-phase.md:71-81 | .ai/workflows/add-phase.md:92-103 | Replace the hand-edited STATE.md "Roadmap Evolution" with `engineer_run query state.add-roadmap-evolution "Phase ${phase_number} added: ${description}"`. |
| R-WF-621 | STITCH | engineer/workflows/add-phase.md:82 (insert after) | .ai/workflows/add-phase.md:105-114 | Insert the local `commit` step (`engineer_run query commit "docs(roadmap): add phase ${padded}"`). |
| R-WF-622 | REPLACE | engineer/workflows/add-phase.md:83-112 | .ai/workflows/add-phase.md:116-127 | Replace completion with the local summary, ending with one line naming `/discuss-phase {phase_number}`, with no `/clear then`, no "Next Up" block and no `/plan-phase` "plan without discussing" shortcut (RULES phase authority requires discussion before planning). |
| R-WF-623 | REMOVE | — (do not carry) | .ai/workflows/add-phase.md:130-144 | Do not carry the local Next Up `/clear` block or its "`/plan-phase` — plan without discussing first" option (contradicts `.ai/RULES.md:79-80`). |
| R-WF-624 | STITCH | engineer/workflows/add-phase.md:114 (insert after `</process>`) | .ai/workflows/add-phase.md:151-156 | Insert the local anti_patterns. |
| R-WF-625 | REPLACE | engineer/workflows/add-phase.md:116-122 | .ai/workflows/add-phase.md:158-165 | Replace success_criteria with the local list. |
| R-WF-626 | REPLACE | commands/phase.md:1-11 | .ai/commands/phase.md:1-12 | Replace the frontmatter with `name: phase` and the local allowed-tools, adding AskUserQuestion for edit-phase. |
| R-WF-627 | KEEP-UPSTREAM | commands/phase.md:13-15 | — | Keep the `<arguments>` data-not-instructions block. |
| R-WF-628 | REPLACE | commands/phase.md:38-43 | .ai/commands/phase.md:35-40 | Replace the `@~/.claude/gsd-core/workflows/*.md` execution_context with `engineer/workflows/{add,insert,remove,edit}-phase.md`. |
| R-WF-629 | REPLACE | commands/phase.md:45-61 | .ai/commands/phase.md:42-70 | Replace context/process with the local version (remove passes `[--force]`, add passes `--goal`, `engineer_run query init.phase-op`, MANDATORY-read paragraph, success_criteria). |

Done when:
- `grep -c "gsd_run\|gsd-tools\|GSD_WS\|/gsd\|/clear\|Next Up\|without discussing" engineer/workflows/add-phase.md commands/phase.md` → 0
- `grep -n "state.add-roadmap-evolution\|engineer_run query commit\|/discuss-phase" engineer/workflows/add-phase.md` → each present
- `grep -n "^name: phase$" commands/phase.md` → 1 hit

### engineer/workflows/insert-phase.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-630 | REPLACE | engineer/workflows/insert-phase.md:1-5 | .ai/workflows/insert-phase.md:1-13 | Replace the include and purpose with the local header and purpose. |
| R-WF-631 | REPLACE | engineer/workflows/insert-phase.md:13-33 | .ai/workflows/insert-phase.md:21-41 | Replace parse_arguments with the local version (`--goal`, `/phase --insert` usage, phase-number validation that is not integer-only). |
| R-WF-632 | REPLACE | engineer/workflows/insert-phase.md:35-54 | .ai/workflows/insert-phase.md:43-72 | Replace init_context with the runtime snippet plus `engineer_run query init.phase-op "${after_phase}"` and the local `phase_found` check. |
| R-WF-633 | REPLACE | engineer/workflows/insert-phase.md:56-71 | .ai/workflows/insert-phase.md:74-90 | Replace insert_phase with `engineer_run query phase.insert "${after_phase}" "${description}" --goal "${goal}"`. |
| R-WF-634 | REPLACE | engineer/workflows/insert-phase.md:73-103 | .ai/workflows/insert-phase.md:92-99 | Replace update_project_state (`state.patch`, which the Python runtime lacks, and the flagged `add-roadmap-evolution --phase/--action/--urgent` form) with the local single-string `engineer_run query state.add-roadmap-evolution "... (URGENT): ..."`. |
| R-WF-635 | STITCH | engineer/workflows/insert-phase.md:104 (insert after) | .ai/workflows/insert-phase.md:101-105 | Insert the local `commit` step. |
| R-WF-636 | REPLACE | engineer/workflows/insert-phase.md:105-136 | .ai/workflows/insert-phase.md:107-118 | Replace completion with the local summary, ending on one line naming `/discuss-phase {phase_number}` and the dependency-impact review; drop the `/clear then` block. |
| R-WF-637 | REMOVE | — (do not carry) | .ai/workflows/insert-phase.md:121-128 | Do not carry the local Next Up `/clear` block. |
| R-WF-638 | REPLACE | engineer/workflows/insert-phase.md:140-148 | .ai/workflows/insert-phase.md:141-147 | Replace anti_patterns with the local list, dropping GSD's "Don't commit changes" (148), which contradicts the commit step. |
| R-WF-639 | REPLACE | engineer/workflows/insert-phase.md:150-159 | .ai/workflows/insert-phase.md:149-155 | Replace success_criteria with the local list (no `state.patch` item). |

Done when:
- `grep -c "gsd_run\|state.patch\|--urgent\|/gsd\|/clear\|Don't commit" engineer/workflows/insert-phase.md` → 0
- `grep -n "engineer_run query commit \"docs(roadmap): insert phase" engineer/workflows/insert-phase.md` → 1 hit

### engineer/workflows/remove-phase.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-640 | REPLACE | engineer/workflows/remove-phase.md:1-5 | .ai/workflows/remove-phase.md:1-12 | Replace the include and purpose with the local header and purpose. |
| R-WF-641 | REPLACE | engineer/workflows/remove-phase.md:13-28 | .ai/workflows/remove-phase.md:20-39 | Replace parse_arguments with the local version (`--force`, `--no-renumber`, `/phase --remove` usage). |
| R-WF-642 | REPLACE | engineer/workflows/remove-phase.md:30-47 | .ai/workflows/remove-phase.md:41-65 | Replace init_context with the runtime snippet plus `engineer_run query init.phase-op "${target}"`, extracting `status`, `plans_complete`, `summary_count` and `state`, with the phase_found error. |
| R-WF-643 | REPLACE | engineer/workflows/remove-phase.md:49-68 | .ai/workflows/remove-phase.md:67-87 | Replace validate_future_phase with the local version (`state.position.Phase`, require `plans_complete`=0 and `summary_count`=0, and no `/gsd:pause-work`, which is not kept). |
| R-WF-644 | REPLACE | engineer/workflows/remove-phase.md:70-85 | .ai/workflows/remove-phase.md:89-104 | Replace confirm_removal with the local version, which accepts only an explicit yes and mentions `--no-renumber`. |
| R-WF-645 | REPLACE | engineer/workflows/remove-phase.md:87-108 | .ai/workflows/remove-phase.md:106-127 | Replace execute_removal with `engineer_run query phase.remove` and the local result fields (`removed`, `name`, `directory`, `renumbered`). |
| R-WF-646 | REPLACE | engineer/workflows/remove-phase.md:110-118 | .ai/workflows/remove-phase.md:129-136 | Replace the commit with `engineer_run query commit "chore(roadmap): remove phase ..." --files .planning`. |
| R-WF-647 | REPLACE | engineer/workflows/remove-phase.md:120-143 | .ai/workflows/remove-phase.md:138-160 | Replace completion with the local summary (`/progress`, no `/gsd:`). |
| R-WF-648 | REPLACE | engineer/workflows/remove-phase.md:147-163 | .ai/workflows/remove-phase.md:164-178 | Replace anti_patterns and success_criteria with the local lists (user confirmation required). |

Done when:
- `grep -c "gsd_run\|/gsd\|gsd-remove-phase\|pause-work" engineer/workflows/remove-phase.md` → 0
- `grep -n "\-\-no-renumber" engineer/workflows/remove-phase.md` → present

### engineer/workflows/edit-phase.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-649 | REPLACE | engineer/workflows/edit-phase.md:1-5 | .ai/workflows/edit-phase.md:1-13 | Replace the include and purpose with the local header and purpose. |
| R-WF-650 | REPLACE | engineer/workflows/edit-phase.md:13-33 | .ai/workflows/edit-phase.md:21-40 | Replace parse_arguments with the local `/phase --edit` usage. |
| R-WF-651 | REPLACE | engineer/workflows/edit-phase.md:35-55 | .ai/workflows/edit-phase.md:42-62 | Replace init_context with the runtime snippet plus `engineer_run query init.phase-op "${target}"`. |
| R-WF-652 | REPLACE | engineer/workflows/edit-phase.md:57-83 | .ai/workflows/edit-phase.md:64-82 | Replace load_phase with `engineer_run query roadmap.get-phase` (dotted verb) and the local field list, with no raw section parsing. |
| R-WF-653 | REPLACE | engineer/workflows/edit-phase.md:85-117 | .ai/workflows/edit-phase.md:84-109 | Replace check_phase_status (`roadmap analyze` disk_status mapping) with the local status mapping from `roadmap.get-phase` and `/phase --edit {target} --force`. |
| R-WF-654 | REPLACE | engineer/workflows/edit-phase.md:119-185 | .ai/workflows/edit-phase.md:111-142 | Replace present_current_values and collect_edits with the local AskUserQuestion version; drop success_criteria regeneration, because `phase.edit` takes only name/goal/depends-on/requirements. |
| R-WF-655 | REPLACE | engineer/workflows/edit-phase.md:187-212 | .ai/workflows/edit-phase.md:144-165 | Replace validate_depends_on with the local version using `engineer_run query roadmap.analyze`. |
| R-WF-656 | REPLACE | engineer/workflows/edit-phase.md:214-240 | .ai/workflows/edit-phase.md:167-182 | Replace show_diff_and_confirm with the local field diff; drop hand-built section text. |
| R-WF-657 | REPLACE | engineer/workflows/edit-phase.md:242-278 | .ai/workflows/edit-phase.md:184-214 | Replace write_updated_phase (hand-written ROADMAP section, `roadmap milestone-scope` before/after rollback, flagged add-roadmap-evolution) with `engineer_run query phase.edit`, the `roadmap.get-phase` re-read and the single-string `state.add-roadmap-evolution`. |
| R-WF-658 | REPLACE | engineer/workflows/edit-phase.md:280-298 | .ai/workflows/edit-phase.md:216-234 | Replace completion with the local What's Next (`/progress`, `/discuss-phase`, `/plan-phase`) without `/gsd:`. |
| R-WF-659 | REPLACE | engineer/workflows/edit-phase.md:302-327 | .ai/workflows/edit-phase.md:238-258 | Replace anti_patterns and success_criteria with the local lists (runtime renames the directory; no raw Write on ROADMAP.md). |

Done when:
- `grep -c "gsd_run\|/gsd\|gsd-edit-phase\|milestone-scope\|success_criteria regeneration\|roadmap analyze\|roadmap get-phase" engineer/workflows/edit-phase.md` → 0
- `grep -n "engineer_run query phase.edit" engineer/workflows/edit-phase.md` → 1 hit

### engineer/workflows/add-todo.md (+ commands/capture.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-660 | REPLACE | engineer/workflows/add-todo.md:1-3 | .ai/workflows/add-todo.md:1-12 | Replace the purpose with the local header and purpose. |
| R-WF-661 | REPLACE | engineer/workflows/add-todo.md:11-35 | .ai/workflows/add-todo.md:20-42 | Replace init_context with the runtime snippet plus `engineer_run query init.todos` (extract `text_mode`) and drop the `mkdir -p` (todo.add owns the directories). |
| R-WF-662 | REPLACE | engineer/workflows/add-todo.md:37-97 | .ai/workflows/add-todo.md:44-107 | Replace extract_content, infer_area and infer_severity with the local versions (`/capture` examples, severity carried into `--severity`). |
| R-WF-663 | REPLACE | engineer/workflows/add-todo.md:120-148 | .ai/workflows/add-todo.md:124-160 | Replace create_file (generate-slug plus hand-written file) with `engineer_run query todo.add ... --severity --files`, extracting `file` and `todoId` and setting `todo_name`. |
| R-WF-664 | STITCH | engineer/workflows/add-todo.md:149 (insert after create_file) | .ai/workflows/add-todo.md:162-238 | Insert the local `publish_issue` step (`todo.issue-preview` → reviewed public title/body → `todo.issue-publish --existing-issue\|--no-match`, `issue.validate`, blocked-publication handling, no second create). |
| R-WF-665 | REPLACE | engineer/workflows/add-todo.md:150-156 | .ai/workflows/add-todo.md:240-252 | Replace update_state (re-run init.todos and hand-replace the section) with `engineer_run query state.sync-todos`. |
| R-WF-666 | REPLACE | engineer/workflows/add-todo.md:158-168 | .ai/workflows/add-todo.md:254-262 | Replace git_commit with the local commit of the exact `todo_file` plus STATE, committed even when publication is blocked. |
| R-WF-667 | REPLACE | engineer/workflows/add-todo.md:170-186 | .ai/workflows/add-todo.md:264-285 | Replace confirm with the local output (verified issue URL or blocked report, `/capture --list`). |
| R-WF-668 | STITCH | engineer/workflows/add-todo.md:188 (insert after `</process>`) | .ai/workflows/add-todo.md:289-295 | Insert the local anti_patterns. |
| R-WF-669 | REPLACE | engineer/workflows/add-todo.md:190-198 | .ai/workflows/add-todo.md:297-306 | Replace success_criteria with the local list. |
| R-WF-670 | REPLACE | commands/capture.md:1-13 | .ai/commands/capture.md:1-12 | Replace the frontmatter with `name: capture`, `argument-hint: "<description> \| --list [area]"` and the local description. |
| R-WF-671 | KEEP-UPSTREAM | commands/capture.md:15-17 | — | Keep the `<arguments>` data-not-instructions block. |
| R-WF-672 | REPLACE | commands/capture.md:19-42 | .ai/commands/capture.md:14-36 | Replace the objective and routing with the local two-route table and the issue-publication authorization paragraph. |
| R-WF-673 | REMOVE | commands/capture.md:24-28, 36-40, 46-51, 58-61 | — | Delete the `--note`, `--backlog`, `--seed` and `--list-seeds` routes and their note/add-backlog/plant-seed/list-seeds/ui-brand includes (not kept). |
| R-WF-674 | REPLACE | commands/capture.md:44-70 | .ai/commands/capture.md:38-71 | Replace execution_context, context and process with `engineer/workflows/add-todo.md` and `engineer/workflows/check-todos.md`, `engineer_run query init.todos`, the MANDATORY-read paragraph and the local success_criteria. |

Done when:
- `grep -c "gsd_run\|generate-slug\|mkdir -p\|/gsd\|gsd-add-todo\|pending_todos_markdown" engineer/workflows/add-todo.md` → 0
- `grep -n "todo.issue-preview\|todo.issue-publish\|state.sync-todos\|engineer_run query todo.add" engineer/workflows/add-todo.md` → each present
- `grep -c "\-\-note\|\-\-backlog\|\-\-seed\|list-seeds\|plant-seed\|gsd" commands/capture.md` → 0

### engineer/workflows/check-todos.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-675 | REPLACE | engineer/workflows/check-todos.md:1-3 | .ai/workflows/check-todos.md:1-11 | Replace the purpose with the local header and purpose (publish/link before routing). |
| R-WF-676 | REPLACE | engineer/workflows/check-todos.md:11-44 | .ai/workflows/check-todos.md:19-45 | Replace init_context with the runtime snippet plus `engineer_run query init.todos` (extract `commit_docs`, `text_mode`, `roadmap_exists`) and the local empty message pointing to `/capture`. |
| R-WF-677 | REPLACE | engineer/workflows/check-todos.md:46-99 | .ai/workflows/check-todos.md:47-103 | Replace parse_filter, list_todos, handle_selection and load_context with the local versions (severity shown, `todo_file`/`todo_name` captured). |
| R-WF-678 | REPLACE | engineer/workflows/check-todos.md:101-108 | .ai/workflows/check-todos.md:105-116 | Replace check_roadmap with `engineer_run query todo.match-phase` for the next one or two open phases. |
| R-WF-679 | REMOVE | — (do not carry) | .ai/workflows/check-todos.md:109 | Do not carry the pseudo-loop `phase_run query phases.list --raw \| ...`; `phases.list` is not a runtime verb, so take the open phases from `engineer_run query roadmap.analyze`. |
| R-WF-680 | STITCH | engineer/workflows/check-todos.md:109 (insert after check_roadmap) | .ai/workflows/check-todos.md:118-196 | Insert the local `publish_selected_issue` step (preview/publish the selected TODO only, stop before actions on failure, `state.sync-todos` plus an exact-path commit). |
| R-WF-681 | REPLACE | engineer/workflows/check-todos.md:110-134 | .ai/workflows/check-todos.md:198-224 | Replace offer_actions with the local options ("Fold into that phase", "Make it a quick task", "Make it a phase"), all keeping the TODO pending. |
| R-WF-682 | REPLACE | engineer/workflows/check-todos.md:136-155 | .ai/workflows/check-todos.md:226-255 | Replace execute_action (the `mv` to completed on "Work on it now") with the local `engineer_run query todo.complete` after demonstrated resolution and a CLOSED linked issue, under the existing implementation-authorization rules. |
| R-WF-683 | REPLACE | engineer/workflows/check-todos.md:157-176 | .ai/workflows/check-todos.md:257-276 | Replace update_state and git_commit (`git rm --cached`, hand-rendered section) with `state.sync-todos` and the exact-path completion commit. |
| R-WF-684 | REPLACE | engineer/workflows/check-todos.md:180-189 | .ai/workflows/check-todos.md:280-293 | Replace success_criteria with the local anti_patterns and success_criteria. |

Done when:
- `grep -c "gsd_run\|mv \"\.planning/todos\|git rm --cached\|phases.list\|/gsd\|gsd-add-todo" engineer/workflows/check-todos.md` → 0
- `grep -n "publish_selected_issue\|todo.issue-publish\|todo.complete\|todo.match-phase" engineer/workflows/check-todos.md` → each present

### engineer/workflows/update.md (+ commands/update.md)

Decision: REPLACE, not STITCH. The upstream flow (npm version check, `npx @opengsd/gsd-core`, `gsd-local-patches/`, cache clearing, `--sync`/`--reapply`/`--next`) installs the incompatible Node package. The local flow uses a pinned Git ref with the reviewed `update.py` plan and apply.

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-685 | REPLACE | engineer/workflows/update.md:1-615 | .ai/workflows/update-workflows.md:1-166 | Replace the whole workflow with the local role-dispatched update (pin scope, updater plan, scout FACT_EXTRACTION packet, executor resolutions, code-reviewer before apply, `--apply --reviewed-plan-sha256`, named verification), keeping the file name `update.md`. |
| R-WF-686 | REPLACE | engineer/workflows/update.md (new body, from local :17-19) | .ai/workflows/update-workflows.md:17-19 | Rewrite `AGENTS.md, RULES.md` and `../references/scout-dispatch.md` to their post-retirement locations; `engineer/references/scout-dispatch.md` does not exist yet. |
| R-WF-687 | REPLACE | engineer/workflows/update.md (new body, from local :24-35, :75) | .ai/workflows/update-workflows.md:24-27, 35, 75 | Rewrite `query ...` calls to `engineer_run query ...` and point the source-side updater at `bin/update.py`, keeping installed-host `.codex/update.py`/`.claude/update.py` paths only if the installer still lays them out that way. |
| R-WF-688 | REPLACE | commands/update.md:1-53 | .ai/commands/update-workflows.md:1-24 | Replace the command with the local body under `name: update`, with no argument-hint flags, and `<execution_context>` reading `engineer/workflows/update.md`. |
| R-WF-689 | REMOVE | commands/update.md:35-39, 43-47, 50-53 | — | Delete the `--sync`, `--reapply` and `--next/--rc` flags and the sync-skills/reapply-patches includes (not kept). |
| R-WF-690 | KEEP-UPSTREAM | commands/update.md:15-17 | — | Keep the `<arguments>` data-not-instructions block. |

Done when:
- `grep -c "npm\|npx\|@opengsd\|gsd-local-patches\|reapply\|sync-skills\|--rc\|/gsd" engineer/workflows/update.md commands/update.md` → 0
- `grep -n "reviewed-plan-sha256\|scout_assignment\|code-reviewer" engineer/workflows/update.md` → each present
- `grep -n "^name: update$" commands/update.md` → 1 hit

### engineer/workflows/clean-planning.md (+ commands/clean-planning.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-691 | NEW FILE | engineer/workflows/clean-planning.md (new) | .ai/workflows/clean-planning.md:1-221 | Create the workflow from the local file, renaming `phase_run` to `engineer_run`. |
| R-WF-692 | NEW FILE | engineer/workflows/clean-planning.md (new, from local :19-24) | .ai/workflows/clean-planning.md:19-24 | Rewrite the links `../RULES.md`, `../truth-map.md`, `../references/scout-dispatch.md` and `../runtime/TEMPLATE-CONTRACT.md` to wherever those files land after `.ai/` retires (none exists under `engineer/` today), and replace "source `.ai/runtime/phase.py`" with the engineer runtime path. |
| R-WF-693 | NEW FILE | engineer/workflows/clean-planning.md (new, from local :55-60) | .ai/workflows/clean-planning.md:55-60 | Replace "when executing from `.ai/`" with the engineer source namespace. |
| R-WF-694 | NEW FILE | engineer/workflows/clean-planning.md (new, from local :90-94) | .ai/workflows/clean-planning.md:90-94 | Keep the `../templates/*.md` links (they resolve under `engineer/templates/`) and add `engineer/templates/ADR.md`, which is missing; alternatively, re-point the ADR link. |
| R-WF-695 | NEW FILE | commands/clean-planning.md (new) | .ai/commands/clean-planning.md:1-24 | Create the command from the local file, adding the `<arguments>` data block and rewriting `.ai/workflows/clean-planning.md` to `engineer/workflows/clean-planning.md`. |

Done when:
- `test -f engineer/workflows/clean-planning.md && test -f commands/clean-planning.md`
- `grep -c "phase_run\|\.ai/" engineer/workflows/clean-planning.md commands/clean-planning.md` → 0
- `grep -n "engineer_run query planning.review\|planning.repair --apply --expect\|planning.archive" engineer/workflows/clean-planning.md` → each present
- Every relative link in `engineer/workflows/clean-planning.md` resolves (`grep -o "](\.\./[^)]*)" ... | xargs test -f`)

### commands/install.md

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-696 | NEW FILE | commands/install.md (new) | .ai/commands/install.md:1-386 | Create the install guide command from the local file (local-only; GSD has no equivalent). |
| R-WF-697 | NEW FILE | commands/install.md (new, from local :11-12, 242, 256) | .ai/commands/install.md:11-12, 242, 256 | Rewrite the raw-URL installer path `/main/.ai/install.py` to the new source location `bin/install.py` once it is populated (currently 0 bytes). |
| R-WF-698 | NEW FILE | commands/install.md (new, from local :118, 133) | .ai/commands/install.md:118, 133 | Rewrite `[update-workflows](update-workflows.md)` to `[update](update.md)` and "its `.ai/update.py`" to `bin/update.py`. |
| R-WF-699 | NEW FILE | commands/install.md (new, from local :110-113) | .ai/commands/install.md:110-113 | Keep the "older installation with a separate `.ai` directory needs migration" paragraph and point it at `bin/migrate.py` (currently 0 bytes). |
| R-WF-700 | KEEP-UPSTREAM | commands/install.md (new; installed-layout lines 20-33, 101-102, 127-150, 342-386) | .ai/commands/install.md:20-33, 101-102, 127-150, 342-386 | Leave the installed host paths (`.codex/...`, `.claude/...`, venvs) unchanged unless the installer layout changes. |

Done when:
- `test -f commands/install.md`
- `grep -c "/\.ai/install\.py\|\.ai/update\.py\|update-workflows" commands/install.md` → 0
- `grep -c "bin/install.py" commands/install.md` ≥ 3
### Feature workflows — shared conventions (apply to every subsection below)

Local sources every feature workflow copies from (verified at HEAD 9443672):

- Launcher: `.ai/workflows/_runtime.snippet.sh:1-28` replaces every `_GSD_SHIM_NAME=...gsd_run()` one-liner; `phase_run` → `engineer_run`.
- Phase lookup + session: `.ai/workflows/plan-phase.md:52-70` (`phase.locate`) and `.ai/workflows/plan-phase.md:115-162` (`open_session`: `session.adopt`/`session.open phase`, re-init in worktree, "do not deliver here").
- Non-phase unit of work: `.ai/workflows/quick.md:127-154` (`open_session` quick), `.ai/workflows/quick.md:156-167` (`quick.create`), `.ai/workflows/quick.md:499-512` (`quick.update` + `state.record-session` + `commit`), `.ai/workflows/quick.md:514-533` (`deliver_session`).
- Authority gate: `.ai/workflows/execute-phase.md:74-78`, `.ai/RULES.md:88-98`.
- Isolation (no opt-out): `.ai/workflows/execute-phase.md:265-313`; dispatch/record/integrate: `.ai/workflows/execute-phase.md:343-494`, `.ai/workflows/execute-phase.md:496-539`.
- Checks with receipts: `.ai/workflows/execute-phase.md:584-608`.
- Model/effort inline: `.ai/workflows/execute-phase.md:55-72`.
- No next-step prompts: `.ai/workflows/execute-phase.md:19-23`.
- Issue routing (no stops, no todos): `.ai/RULES.md:244-272`; phase issue publication: `.ai/workflows/execute-phase.md:704-731`; threat tracking: `.ai/workflows/execute-phase.md:618-626`.
- Report-only specialist pattern (returns cited findings, coordinator writes the record): `.ai/workflows/verify-work.md:304-333`, code-reviewer prompt `.ai/workflows/execute-phase.md:654-686`.
- Decision recording: `.ai/workflows/discuss-phase.md:569-581`.

Agent name map (local roster `.ai/agents/`): `gsd-executor`→`executor`, `gsd-planner`→`planner`, `gsd-plan-checker`→`plan-checker`, `gsd-verifier`→`verifier`, `gsd-phase-researcher`→`phase-researcher`, `gsd-code-reviewer`→`code-reviewer`, `gsd-code-fixer`→`targeted-fixer` (via bounded correction dispatch). **No local equivalent:** `gsd-ui-researcher`, `gsd-ui-checker`, `gsd-ui-auditor`, `gsd-security-auditor`, `gsd-nyquist-auditor` (exist only as `agents/gsd-*.md`).

Runtime verbs these workflows call that `.ai/runtime/phase.py` does NOT provide (engineer_run gap — port or replace): `loop render-hooks`, `verification.append-audit`, `audit-uat`, `quick-batch *`, `dispatch-capacity`, `worktree.base-check`, `review-lane *`, `check evaluation-scope`, `init.code-review`, `init.quick-batch`, `state-snapshot`, `quick-tasks-append`/`quick-tasks-migrate`, `resolve-package-manager`, `normalize-test-command`, `run-with-timeout`, `frontmatter.get`, `agent-skills` (exists). Node `.cjs` libs referenced but absent from `engineer/bin/`: `ui-consideration-probe.cjs`, `edge-probe.cjs`, `code-review-flags.cjs`, `code-review-depth.cjs`, `fallow-runner.cjs`.

### engineer/workflows/ui-phase.md (+ commands/ui-phase.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-701 | REPLACE | engineer/workflows/ui-phase.md:21-32 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/plan-phase.md:52-70 | Replace the GSD shim, `--ws` parsing and `gsd_run query init.plan-phase` with the engineer launcher plus `engineer_run query phase.locate` then `init.plan-phase`. |
| R-WF-702 | STITCH | engineer/workflows/ui-phase.md:66 (insert before §2) | .ai/workflows/plan-phase.md:115-162 | Insert the phase `open_session` step so UI-SPEC.md is written and committed inside the phase session worktree, never the primary checkout. |
| R-WF-703 | REPLACE | engineer/workflows/ui-phase.md:46-50, 140, 183-185, 211, 234-236 | .ai/workflows/execute-phase.md:55-72 | Resolve model and effort with `engineer_run query resolve-model`/`resolve-effort` and pass both inline, omitting each on `inherit`. |
| R-WF-704 | REPLACE | engineer/workflows/ui-phase.md:13-14, 128, 183, 199, 234, 255 | — | Rename `gsd-ui-researcher`/`gsd-ui-checker` to their engineer agent names (no local equivalent; agents section decides). |
| R-WF-705 | REMOVE | engineer/workflows/ui-phase.md:40-43, 93-98, 153 | — | Delete sketch-findings detection and `/gsd:sketch` references because `sketch` is not kept. |
| R-WF-706 | REMOVE | engineer/workflows/ui-phase.md:174 | — | Delete the kimi-code runtime-aware-dispatch note. |
| R-WF-707 | REPLACE | engineer/workflows/ui-phase.md:343-432 | — | Replace the `ui-consideration-probe.cjs` resolver/node block with an `engineer_run` verb once ported, otherwise an agent-judged element table (engine absent from engineer/bin). |
| R-WF-708 | KEEP-UPSTREAM | engineer/workflows/ui-phase.md:109-114, 317, 453-468 | — | Keep in-workflow `--auto` answer selection; it never chains. |
| R-WF-709 | STITCH | engineer/workflows/ui-phase.md:510-514 (after commit) | .ai/workflows/discuss-phase.md:569-581 | Record design-system choices that outlive the phase with `engineer_run query state.add-decision`. |
| R-WF-710 | REPLACE | engineer/workflows/ui-phase.md:491-506 | .ai/workflows/execute-phase.md:19-23 | Replace the `▶ Next Up`/`/clear` block with a closing report that names no follow-on command. |
| R-WF-711 | REPLACE | engineer/workflows/ui-phase.md:513, 519-521 | — | Change `gsd_run query commit`/`state.record-session` to `engineer_run query ...`. |
| R-WF-712 | REPLACE | commands/ui-phase.md:2, 29-30 | .ai/commands/quick.md:1-14 | Rename `name: gsd:ui-phase` to `ui-phase` and point execution_context at `engineer/workflows/ui-phase.md` and `engineer/references/ui-brand.md`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|/gsd:\|/clear\|Next Up\|sketch\|\.cjs\|kimi" engineer/workflows/ui-phase.md` → 0
- `grep -n "phase.locate\|session.open\|session.adopt" engineer/workflows/ui-phase.md` → ≥1 each
- `grep -c "resolve-effort" engineer/workflows/ui-phase.md` → ≥1
- `grep -c "gsd:\|~/.claude/gsd-core" commands/ui-phase.md` → 0

### engineer/workflows/ui-review.md (+ commands/ui-review.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-713 | REPLACE | engineer/workflows/ui-review.md:18-34, 40-42 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/plan-phase.md:52-70; .ai/workflows/execute-phase.md:55-72 | Replace the shim/`init.phase-op` block with the engineer launcher, `phase.locate`, `init.phase-op`, and inline resolve-model/resolve-effort. |
| R-WF-714 | STITCH | engineer/workflows/ui-review.md:48 (insert before §1) | .ai/workflows/plan-phase.md:115-162 | Insert phase `open_session` so the UI-REVIEW record lands on the phase session branch. |
| R-WF-715 | REPLACE | engineer/workflows/ui-review.md:84-139 | .ai/workflows/verify-work.md:304-333 | Make the auditor read-only: it returns a cited `## UI REVIEW` packet against a captured revision and the coordinator writes `{padded}-UI-REVIEW.md`; no commit or SUMMARY from the agent. |
| R-WF-716 | REPLACE | engineer/workflows/ui-review.md:11, 29, 41, 84, 93, 132 | — | Rename `gsd-ui-auditor` to its engineer agent name (no local equivalent). |
| R-WF-717 | REMOVE | engineer/workflows/ui-review.md:123 | — | Delete the kimi-code runtime-aware-dispatch note. |
| R-WF-718 | STITCH | engineer/workflows/ui-review.md:160-165 | .ai/RULES.md:244-272; .ai/workflows/execute-phase.md:704-731 | Route each top fix as in-scope gap, Deferred item or `phase.issue-preview`/`phase.issue-publish` issue; never create todos. |
| R-WF-719 | REPLACE | engineer/workflows/ui-review.md:167-175 | .ai/workflows/execute-phase.md:19-23 | Delete the `▶ Next`/`/clear`/`/gsd:verify-work` block. |
| R-WF-720 | KEEP-UPSTREAM | engineer/workflows/ui-review.md:178-196 | — | Playwright-MCP screenshot pass is read-only evidence. |
| R-WF-721 | REPLACE | engineer/workflows/ui-review.md:201 | — | Change `gsd_run query commit` to `engineer_run query commit`. |
| R-WF-722 | REPLACE | commands/ui-review.md:2, 27-28 | .ai/commands/quick.md:1-14 | Rename to `ui-review` and repoint execution_context at `engineer/workflows/ui-review.md`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|/gsd:\|/clear\|kimi" engineer/workflows/ui-review.md` → 0
- `grep -n "Write to\|Write:" engineer/workflows/ui-review.md` shows no write instruction inside the auditor prompt
- `grep -c "todo" engineer/workflows/ui-review.md` → 0

### engineer/workflows/secure-phase.md (+ commands/secure-phase.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-723 | REPLACE | engineer/workflows/secure-phase.md:18-30, 36-40 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/plan-phase.md:52-70; .ai/workflows/execute-phase.md:55-72 | Replace shim/`init.phase-op`/resolve-model with the engineer launcher, `phase.locate`, `init.phase-op` and inline model+effort. |
| R-WF-724 | REPLACE | engineer/workflows/secure-phase.md:38, 43-45 | — | Replace the `loop render-hooks verify:post` capability gate with `engineer_run query config-get workflow.security_enforcement` (default on). |
| R-WF-725 | STITCH | engineer/workflows/secure-phase.md:48 (insert before §1) | .ai/workflows/plan-phase.md:115-162 | Insert phase `open_session` so SECURITY.md is written in the phase session. |
| R-WF-726 | REPLACE | engineer/workflows/secure-phase.md:102-140 | .ai/workflows/verify-work.md:304-333 | Keep the auditor read-only ("never modify implementation files") returning SECURED/OPEN_THREATS/ESCALATE with citations; the coordinator writes SECURITY.md. |
| R-WF-727 | REPLACE | engineer/workflows/secure-phase.md:11, 29, 37, 102, 123, 129 | — | Rename `gsd-security-auditor` to its engineer agent name (no local equivalent). |
| R-WF-728 | REMOVE | engineer/workflows/secure-phase.md:115 | — | Delete the kimi-code runtime-aware-dispatch note. |
| R-WF-729 | STITCH | engineer/workflows/secure-phase.md:137-140, 159-168 | .ai/workflows/execute-phase.md:618-626; .ai/workflows/execute-phase.md:704-731 | Reconcile OPEN_THREATS and accepted risks through canonical threat tracking (`phase.issue-preview`/`phase.issue-publish`/`phase.issue-update`) and record URLs. |
| R-WF-730 | REPLACE | engineer/workflows/secure-phase.md:153-157 | — | Replace `verification.append-audit` with an engineer_run verb once ported, otherwise a coordinator-appended `## Security Audit` table (runtime gap). |
| R-WF-731 | REPLACE | engineer/workflows/secure-phase.md:177-187 | .ai/workflows/execute-phase.md:19-23 | Replace `▶ /gsd:validate-phase`/`/gsd:verify-work` routing and the `/clear` reminder with a closing report. |
| R-WF-732 | REPLACE | engineer/workflows/secure-phase.md:173-174 | — | Change `gsd_run query commit` to `engineer_run query commit`. |
| R-WF-733 | REPLACE | commands/secure-phase.md:2, 31 | .ai/commands/quick.md:1-14 | Rename to `secure-phase` and repoint execution_context at `engineer/workflows/secure-phase.md`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|render-hooks\|/gsd:\|/clear\|kimi" engineer/workflows/secure-phase.md` → 0
- `grep -n "phase.issue-publish\|threat-tracking" engineer/workflows/secure-phase.md` → ≥1

### engineer/workflows/code-review.md + code-review/steps/dispatch-fix.md (+ commands/code-review.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-734 | REPLACE | engineer/workflows/code-review.md:26-72 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/plan-phase.md:52-70; .ai/workflows/execute-phase.md:55-72 | Replace the shim, `code-review-flags.cjs` node parser and `init.code-review` with the engineer launcher, plain `$ARGUMENTS` flag parsing, `phase.locate`, `init.phase-op` and inline model+effort. |
| R-WF-735 | STITCH | engineer/workflows/code-review.md:102 (after initialize) | .ai/workflows/plan-phase.md:115-162 | Insert phase `open_session` so REVIEW.md is committed on the phase session branch. |
| R-WF-736 | REPLACE | engineer/workflows/code-review.md:286 | .ai/workflows/execute-phase.md:659-661 | Replace `gsd_run check evaluation-scope` with a diff from the session `base` returned by `phase.locate`/`session.status` (runtime gap). |
| R-WF-737 | REPLACE | engineer/workflows/code-review.md:444-569 | — | Replace the `code-review-depth.cjs` resolver with `--depth` flag > `engineer_run query config-get workflow.code_review_depth` > `standard`. |
| R-WF-738 | REMOVE | engineer/workflows/code-review.md:588-607 | — | Delete `structural_pre_pass` and its read of the deleted `code-review/steps/structural-pre-pass.md`. |
| R-WF-739 | REMOVE | engineer/workflows/code-review.md:609-738 | — | Delete `dispatch_reviewer_lanes` (external `--codex`/`--agy` lanes are cross-AI delegation). |
| R-WF-740 | REMOVE | engineer/workflows/code-review.md:805-817 | — | Delete the `loop render-hooks` reviewer-contribution block. |
| R-WF-741 | REPLACE | engineer/workflows/code-review.md:819-869 | .ai/workflows/execute-phase.md:654-686 | Dispatch `code-reviewer` read-only against a frozen revision returning `## CODE REVIEW` findings; the coordinator writes `{padded}-REVIEW.md`. |
| R-WF-742 | REPLACE | engineer/workflows/code-review.md:871-908 | — | Drop the `LANE_RUN_DIR` cleanup and node frontmatter check; commit the coordinator-written REVIEW.md with `engineer_run query commit`. |
| R-WF-743 | REPLACE | engineer/workflows/code-review.md:910-912 | — | Replace the `section_manifest`-gated read with an unconditional read of `engineer/workflows/code-review/steps/dispatch-fix.md` when `--fix` is set. |
| R-WF-744 | STITCH | engineer/workflows/code-review.md:967-982 | .ai/RULES.md:244-272; .ai/workflows/execute-phase.md:680-686 | Route critical findings to bounded correction and out-of-scope findings to Deferred/`phase.issue-*`; delete the "Next steps: /gsd:code-review --fix" prompt. |
| R-WF-745 | REMOVE | engineer/workflows/code-review.md:825 | — | Delete the kimi-code runtime-aware-dispatch note. |
| R-WF-746 | REPLACE | engineer/workflows/code-review/steps/dispatch-fix.md:27-31 | — | Replace `Workflow(workflow="gsd-core/workflows/code-review-fix.md")` with `engineer/workflows/code-review-fix.md` and the `gsd-code-fixer` comment with `targeted-fixer`. |
| R-WF-747 | REPLACE | commands/code-review.md:2, 4, 12, 31-34, 40, 50-58, 71 | .ai/commands/quick.md:1-14 | Rename to `code-review`, drop reviewer-lane flags from argument-hint/objective, delete the "Outside a phase" review-lane section, set `requires: [phase, quick]`, and repoint at engineer paths. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|\.cjs\|review-lane\|render-hooks\|section_manifest\|structural-pre-pass\|fallow\|/gsd:\|kimi" engineer/workflows/code-review.md` → 0
- `grep -c "gsd-core\|gsd-code-fixer" engineer/workflows/code-review/steps/dispatch-fix.md` → 0
- `grep -c "review-lane\|--codex\|gsd:" commands/code-review.md` → 0
- `grep -n "subagent_type=\"code-reviewer\"" engineer/workflows/code-review.md` → 1

### engineer/workflows/code-review-fix.md (no commands/ file — invoked via `/code-review --fix`)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-748 | REPLACE | engineer/workflows/code-review-fix.md:18-87 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/plan-phase.md:52-70; .ai/workflows/execute-phase.md:55-72 | Replace shim/`init.phase-op`/agent-skills/resolve-model with the engineer launcher, `phase.locate`, `init.phase-op` and inline model+effort for `targeted-fixer` and `code-reviewer`. |
| R-WF-749 | STITCH | engineer/workflows/code-review-fix.md:18 (step top) | .ai/workflows/execute-phase.md:74-78; .ai/RULES.md:88-98 | Add the authority gate: run only when the phase's implementation authorization is recorded in CONTEXT or the user explicitly invoked `--fix`. |
| R-WF-750 | REPLACE | engineer/workflows/code-review-fix.md:88-106 | — | Replace the `loop render-hooks execute:post` gate with `engineer_run query config-get workflow.code_review`. |
| R-WF-751 | REPLACE | engineer/workflows/code-review-fix.md:197-256 | .ai/workflows/execute-phase.md:265-313; .ai/workflows/execute-phase.md:680-686 | Dispatch `targeted-fixer` per finding through bounded correction dispatch in an isolated worktree from `dispatch-isolation`, then integrate with `worktree.merge-wave` into the phase session branch. |
| R-WF-752 | STITCH | engineer/workflows/code-review-fix.md:257-406 | .ai/workflows/execute-phase.md:584-608 | After each fix iteration run `engineer_run query verification.run-checks` and obtain a fresh read-only `code-reviewer` review of the repaired revision. |
| R-WF-753 | KEEP-UPSTREAM | engineer/workflows/code-review-fix.md:257-406 | — | `--auto` is a capped fix/re-review loop, not chaining. |
| R-WF-754 | REPLACE | engineer/workflows/code-review-fix.md:407-452 | — | Commit REVIEW-FIX.md with `engineer_run query commit` and drop the node frontmatter probe. |
| R-WF-755 | KEEP-UPSTREAM | engineer/workflows/code-review-fix.md:453-476 | — | Disposition ledger uses kept `execute-phase/steps/code-review-disposition.md`. |
| R-WF-756 | REPLACE | engineer/workflows/code-review-fix.md:585-613 | .ai/workflows/execute-phase.md:19-23; .ai/RULES.md:244-272 | Replace "Next step: /gsd:verify-work"/"/gsd:code-review" echoes with a closing report listing unfixed findings routed as Deferred or issues. |
| R-WF-757 | REPLACE | engineer/workflows/code-review-fix.md:12-13, 31-36, 198, 217, 303-305, 341 | — | Rename `gsd-code-fixer`→`targeted-fixer` and `gsd-code-reviewer`→`code-reviewer`. |
| R-WF-758 | REMOVE | engineer/workflows/code-review-fix.md:210 | — | Delete the kimi-code runtime-aware-dispatch note. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|render-hooks\|gsd-code-fixer\|gsd-code-reviewer\|/gsd:\|kimi" engineer/workflows/code-review-fix.md` → 0
- `grep -n "dispatch-isolation\|merge-wave\|targeted-fixer" engineer/workflows/code-review-fix.md` → ≥1 each

### engineer/workflows/fast.md (+ commands/fast.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-759 | STITCH | engineer/workflows/fast.md:15-24 | .ai/workflows/execute-phase.md:74-78 | State that the explicit `/fast` invocation is the implementation instruction and that no chain may invoke `fast`. |
| R-WF-760 | STITCH | engineer/workflows/fast.md:45 (new step after scope_check) | .ai/workflows/quick.md:127-154; .ai/workflows/quick.md:156-167 | Insert `open_session` (`session.open quick <slug>`) and `quick.create` so the edit happens in `.worktrees/`, never the primary checkout. |
| R-WF-761 | REPLACE | engineer/workflows/fast.md:56-74 | .ai/workflows/quick.md:499-512 | Replace the shim and `git add -A`/`git commit` with an explicit-path `engineer_run query commit` inside the session worktree. |
| R-WF-762 | REPLACE | engineer/workflows/fast.md:76-95 | .ai/workflows/quick.md:499-512 | Replace `quick-tasks-migrate`/`quick-tasks-append` with `quick.update --status complete` and `state.record-session`. |
| R-WF-763 | STITCH | engineer/workflows/fast.md:96 (before done) | .ai/workflows/quick.md:514-533 | Insert `deliver_session` (push, `pr.open`, `pr.checks`, merge only on explicit instruction, `session.close`). |
| R-WF-764 | REPLACE | engineer/workflows/fast.md:10, 39-40, 115-116 | — | Replace `/gsd:quick` with `/quick`. |
| R-WF-765 | REPLACE | engineer/workflows/fast.md:112-114, 120-123 | — | Keep "no subagent" and "no PLAN/SUMMARY" but change success criteria to "edited in session worktree; delivered by PR". |
| R-WF-766 | REPLACE | commands/fast.md:2, 24-25, 30 | .ai/commands/quick.md:1-14 | Rename to `fast`, replace `/gsd:` prefixes and repoint execution_context at `engineer/workflows/fast.md`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|git add -A\|quick-tasks-append\|/gsd:" engineer/workflows/fast.md` → 0
- `grep -n "session.open\|deliver_session\|pr.open" engineer/workflows/fast.md` → ≥1 each

### engineer/workflows/quick-batch.md + quick-batch/steps/* (+ commands/quick-batch.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-767 | STITCH | engineer/workflows/quick-batch.md:30 (process top) | .ai/workflows/execute-phase.md:74-78 | State that the explicit `/quick-batch` invocation authorizes only the listed items. |
| R-WF-768 | REPLACE | engineer/workflows/quick-batch.md:33-77 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/execute-phase.md:55-72 | Replace shim, `gsd_run quick-batch parse-args`, `init.quick-batch` and agent-skills with the engineer launcher, `init.quick` and inline resolve-model/resolve-effort per role. |
| R-WF-769 | STITCH | engineer/workflows/quick-batch.md:130 (before Step 2) | .ai/workflows/quick.md:127-154 | Insert `open_session` (`session.open quick batch-<slug>`) so every merge lands on the batch session branch. |
| R-WF-770 | REMOVE | engineer/workflows/quick-batch.md:86, 118-123 | .ai/workflows/execute-phase.md:281-286 | Delete `USE_WORKTREES` config read and the `!= "false"` guard; always run `worktree.reap-orphans`. |
| R-WF-771 | REPLACE | engineer/workflows/quick-batch.md:110-116 | .ai/workflows/execute-phase.md:265-313 | Resolve `ISOLATION` with `engineer_run query dispatch-isolation --raw` and stop on failure; delete the `dispatch-isolation-gate.md` reference. |
| R-WF-772 | REPLACE | engineer/workflows/quick-batch.md:150-152, 184-186 | — | Replace `section_manifest`-gated reads with flag-gated reads (`--research`, `--validate`) of `engineer/workflows/quick-batch/steps/*.md`. |
| R-WF-773 | REPLACE | engineer/workflows/quick-batch.md:23-27; steps/plan-checker-loop.md:63, 110; steps/planner-wave.md:119; steps/research-phase.md:81; steps/verification-wave.md:39; steps/worktree-dispatch.md:122 | — | Rename agents to `phase-researcher`, `planner`, `plan-checker`, `executor`, `verifier`. |
| R-WF-774 | REMOVE | engineer/workflows/quick-batch/steps/worktree-dispatch.md:7-20, 142-144 | .ai/workflows/execute-phase.md:281-286 | Delete the fork-base auto-degrade to `none` and the `isolation == "none"` inline-on-primary branch. |
| R-WF-775 | REPLACE | engineer/workflows/quick-batch/steps/worktree-dispatch.md:91-140 | .ai/workflows/execute-phase.md:364-382 | Record harness branches with `worktree.record-agent` and create orchestrator checkouts with `worktree.create`, passing `--files`/`--deletions`. |
| R-WF-776 | REMOVE | engineer/workflows/quick-batch/steps/merge-wave.md:3-5 | — | Delete the "skip if ISOLATION none" clause. |
| R-WF-777 | REPLACE | engineer/workflows/quick-batch/steps/merge-wave.md:67-97 | .ai/workflows/execute-phase.md:507-538 | Integrate with `worktree.merge-wave` then `worktree.cleanup-wave` (no `--force`), preserving blocked/conflict entries as reported. |
| R-WF-778 | REMOVE | engineer/workflows/quick-batch/steps/planner-wave.md:24-32 | — | Delete the `loop render-hooks plan:pre` capability gate. |
| R-WF-779 | REPLACE | engineer/workflows/quick-batch/steps/completion.md:10-40 | .ai/workflows/quick.md:499-512 | Replace `quick-batch complete` and `git add` with per-item `quick.update --status complete`, `state.record-session` and one `engineer_run query commit`. |
| R-WF-780 | STITCH | engineer/workflows/quick-batch/steps/completion.md:41 (before final report) | .ai/workflows/quick.md:514-533 | Insert `deliver_session` for the batch session. |
| R-WF-781 | REPLACE | engineer/workflows/quick-batch/steps/completion.md:56, 60-65 | .ai/RULES.md:244-272 | Replace "Resume after resolving: /gsd:quick-batch --resume" with failed/human-needed items listed with options and a recommendation. |
| R-WF-782 | REPLACE | engineer/workflows/quick-batch/steps/*.md (all `gsd_run quick-batch ...`, `dispatch-capacity`, `worktree.base-check`, `generate-slug`, `frontmatter.get`) | — | Port the `quick-batch` verb family to engineer_run or rewrite the steps to use `quick.create`/`quick.update`/`quick.list` (runtime gap). |
| R-WF-783 | REPLACE | commands/quick-batch.md:2-3, 21-28, 47, 52, 87, 115 | .ai/commands/quick.md:1-14 | Rename to `quick-batch`, replace `/gsd:` prefixes and repoint at `engineer/workflows/quick-batch.md`. |

Done when:
- `grep -rc "USE_WORKTREES\|isolation == \"none\"\|ISOLATION=none\|section_manifest\|render-hooks\|_GSD_SHIM\|/gsd:" engineer/workflows/quick-batch.md engineer/workflows/quick-batch/steps/` → all 0
- `grep -rc "gsd-executor\|gsd-planner\|gsd-plan-checker\|gsd-verifier\|gsd-phase-researcher" engineer/workflows/quick-batch.md engineer/workflows/quick-batch/steps/` → all 0
- `grep -rn "worktree.merge-wave\|session.open\|deliver_session" engineer/workflows/quick-batch.md engineer/workflows/quick-batch/steps/` → ≥1 each

### engineer/workflows/add-tests.md (+ commands/add-tests.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-784 | STITCH | engineer/workflows/add-tests.md:13 (process top) | .ai/workflows/execute-phase.md:74-78; .ai/RULES.md:88-98 | Add the authority gate: write tests only when the user explicitly invoked `/add-tests` for that phase. |
| R-WF-785 | REPLACE | engineer/workflows/add-tests.md:32-74 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/plan-phase.md:52-70; .ai/workflows/plan-phase.md:115-162 | Replace the shim/`init.phase-op` with the engineer launcher, `phase.locate` and phase `open_session`. |
| R-WF-786 | REPLACE | engineer/workflows/add-tests.md:219-280 | .ai/workflows/execute-phase.md:265-313; .ai/workflows/execute-phase.md:343-539 | Dispatch test generation to an isolated `executor` (via `dispatch-isolation`) and integrate with `worktree.merge-wave` instead of writing tests inline. |
| R-WF-787 | REPLACE | engineer/workflows/add-tests.md:304-314 | .ai/workflows/execute-phase.md:584-608 | Replace `state-snapshot` and `git add`/`git commit` with `verification.run-checks` and `engineer_run query commit` of the coordinator records. |
| R-WF-788 | REPLACE | engineer/workflows/add-tests.md:300-301, 316-339 | .ai/RULES.md:244-272; .ai/workflows/execute-phase.md:704-731 | Route discovered bugs through `phase.issue-preview`/`phase.issue-publish` and delete the `▶ Next Up` `/gsd:quick`/`/gsd:verify-work` suggestions. |
| R-WF-789 | REPLACE | engineer/workflows/add-tests.md:4, 18, 24-26, 65 | — | Replace `/gsd:` prefixes with plain `/<name>`. |
| R-WF-790 | REPLACE | commands/add-tests.md:2, 16-17, 34 | .ai/commands/quick.md:1-14 | Rename to `add-tests` and repoint at `engineer/workflows/add-tests.md`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|git add\|git commit\|state-snapshot\|Next Up\|/gsd:" engineer/workflows/add-tests.md` → 0
- `grep -n "dispatch-isolation\|merge-wave\|phase.issue-publish" engineer/workflows/add-tests.md` → ≥1 each

### engineer/workflows/validate-phase.md (+ commands/validate-phase.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-791 | REPLACE | engineer/workflows/validate-phase.md:18-39 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/plan-phase.md:52-70; .ai/workflows/execute-phase.md:55-72 | Replace shim/`init.phase-op`/resolve-model with the engineer launcher, `phase.locate`, `init.phase-op` and inline model+effort. |
| R-WF-792 | REPLACE | engineer/workflows/validate-phase.md:38, 41-43 | — | Replace the `loop render-hooks verify:post` gate with `engineer_run query config-get workflow.nyquist_validation` (default on). |
| R-WF-793 | STITCH | engineer/workflows/validate-phase.md:46 (before §1) | .ai/workflows/plan-phase.md:115-162 | Insert phase `open_session`. |
| R-WF-794 | REPLACE | engineer/workflows/validate-phase.md:104-135 | .ai/workflows/verify-work.md:304-333 | Make the gap audit read-only (cited COVERED/PARTIAL/MISSING packet); the coordinator writes VALIDATION.md. |
| R-WF-795 | STITCH | engineer/workflows/validate-phase.md:96-103 ("Fix all gaps") | .ai/workflows/execute-phase.md:74-78; .ai/workflows/execute-phase.md:265-313; .ai/workflows/execute-phase.md:343-539 | Gate test-writing on recorded implementation authority and dispatch it to an isolated `executor` integrated with `worktree.merge-wave`. |
| R-WF-796 | REPLACE | engineer/workflows/validate-phase.md:11, 29, 37, 104, 118, 124 | — | Rename `gsd-nyquist-auditor` to its engineer agent name (no local equivalent). |
| R-WF-797 | REMOVE | engineer/workflows/validate-phase.md:110 | — | Delete the kimi-code runtime-aware-dispatch note. |
| R-WF-798 | REPLACE | engineer/workflows/validate-phase.md:148-152 | — | Replace `verification.append-audit` with a ported verb or coordinator-appended audit table (runtime gap). |
| R-WF-799 | REPLACE | engineer/workflows/validate-phase.md:156-161 | — | Replace orchestrator `git add`/`git commit` of test files with the executor's commits and `engineer_run query commit` of VALIDATION.md. |
| R-WF-800 | REPLACE | engineer/workflows/validate-phase.md:164-180 | .ai/workflows/execute-phase.md:19-23 | Replace `▶ Next: /gsd:audit-milestone`/`Retry` routing and the `/clear` reminder with a closing report (audit-milestone is not kept). |
| R-WF-801 | REPLACE | commands/validate-phase.md:2, 31 | .ai/commands/quick.md:1-14 | Rename to `validate-phase` and repoint at `engineer/workflows/validate-phase.md`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|render-hooks\|git add\|git commit\|audit-milestone\|/gsd:\|/clear\|kimi" engineer/workflows/validate-phase.md` → 0

### engineer/workflows/audit-uat.md (+ commands/audit-uat.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-802 | REPLACE | engineer/workflows/audit-uat.md:12-15 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace the shim and `gsd_run query audit-uat` with the engineer launcher and a ported `audit-uat` verb, or `verification.status` per phase from `phases.list` (runtime gap). |
| R-WF-803 | KEEP-UPSTREAM | engineer/workflows/audit-uat.md:31-101 | — | Read-only cross-phase categorization; writes nothing. |
| R-WF-804 | REPLACE | engineer/workflows/audit-uat.md:95-100 | .ai/workflows/execute-phase.md:19-23; .ai/RULES.md:244-272 | Replace "Recommended Actions" `/gsd:verify-work` prompts with a report of open items and their tracking issue URLs. |
| R-WF-805 | REPLACE | engineer/workflows/audit-uat.md:103-125 | .ai/workflows/verify-work.md:373-417 | Format the human test plan with the canonical UAT template/issue variant used by `prepare_human_acceptance`. |
| R-WF-806 | REPLACE | commands/audit-uat.md:2, 15 | .ai/commands/quick.md:1-14 | Rename to `audit-uat` and repoint at `engineer/workflows/audit-uat.md`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|/gsd:" engineer/workflows/audit-uat.md` → 0
- `grep -c "git commit\|Write(" engineer/workflows/audit-uat.md` → 0

### engineer/workflows/audit-fix.md (+ commands/audit-fix.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-807 | STITCH | engineer/workflows/audit-fix.md:15 (process top) | .ai/workflows/execute-phase.md:74-78; .ai/RULES.md:88-98 | State that only an explicit `/audit-fix` invocation without `--dry-run` authorizes fixes. |
| R-WF-808 | REPLACE | engineer/workflows/audit-fix.md:36-40 | .ai/workflows/_runtime.snippet.sh:1-28 | Replace shim and `gsd_run query audit-uat` with the engineer launcher and the audit-uat source chosen above. |
| R-WF-809 | STITCH | engineer/workflows/audit-fix.md:95 (before fix-loop) | .ai/workflows/quick.md:127-154; .ai/workflows/quick.md:156-167 | Insert `open_session` (`session.open quick audit-fix-<slug>`) and `quick.create`. |
| R-WF-810 | REPLACE | engineer/workflows/audit-fix.md:96-121 | .ai/workflows/execute-phase.md:265-313; .ai/workflows/execute-phase.md:680-686; .ai/workflows/execute-phase.md:55-72 | Dispatch each auto-fixable finding to `targeted-fixer` (bounded correction) in an isolated worktree with inline model+effort, replacing `gsd-executor`. |
| R-WF-811 | REPLACE | engineer/workflows/audit-fix.md:122-152 | .ai/workflows/execute-phase.md:584-608 | Replace the ad-hoc test-command detection/`run-with-timeout` with `engineer_run query verification.run-checks` on the integrated revision. |
| R-WF-812 | REPLACE | engineer/workflows/audit-fix.md:154-168 | .ai/workflows/execute-phase.md:507-538 | Replace `git add`/`git commit`/`git checkout --` with `worktree.merge-wave` on pass and leaving the failed worker branch unmerged and preserved on failure. |
| R-WF-813 | STITCH | engineer/workflows/audit-fix.md:171-190 | .ai/RULES.md:244-272; .ai/workflows/quick.md:499-533 | Route manual-only findings with options and a recommendation, then `quick.update`, `state.record-session` and `deliver_session`. |
| R-WF-814 | REMOVE | engineer/workflows/audit-fix.md:101 | — | Delete the kimi-code runtime-aware-dispatch note. |
| R-WF-815 | REPLACE | commands/audit-fix.md:3, 34 | .ai/commands/quick.md:1-14 | Rename to `audit-fix` and repoint at `engineer/workflows/audit-fix.md`. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|gsd-executor\|git add\|git commit\|git checkout\|run-with-timeout\|kimi" engineer/workflows/audit-fix.md` → 0
- `grep -n "dispatch-isolation\|merge-wave\|session.open\|deliver_session" engineer/workflows/audit-fix.md` → ≥1 each

### engineer/workflows/spec-phase.md (+ commands/spec-phase.md)

| ID | Action | GSD target lines | Local source lines | Instruction |
|---|---|---|---|---|
| R-WF-816 | REPLACE | engineer/workflows/spec-phase.md:58-62 | .ai/workflows/_runtime.snippet.sh:1-28; .ai/workflows/plan-phase.md:52-70 | Replace the shim and `gsd_run init phase-op` with the engineer launcher, `phase.locate` and `init.phase-op`. |
| R-WF-817 | STITCH | engineer/workflows/spec-phase.md:96 (after Step 1) | .ai/workflows/plan-phase.md:115-162 | Insert phase `open_session` so SPEC.md is written in the phase session. |
| R-WF-818 | KEEP-UPSTREAM | engineer/workflows/spec-phase.md:79-83, 130, 163, 175, 185, 367-378, 459-466 | — | In-workflow `--auto` answers; never chains to discuss/plan. |
| R-WF-819 | REPLACE | engineer/workflows/spec-phase.md:221-328 | — | Replace the `edge-probe.cjs` resolver/node block with a ported engineer_run verb or an agent-judged edge table (engine absent). |
| R-WF-820 | REPLACE | engineer/workflows/spec-phase.md:194, 387, 482 | — | Repoint `@~/.claude/gsd-core/references/edge-probe.md`, `prohibition-probe.md` and `templates/spec.md` at `engineer/`. |
| R-WF-821 | REPLACE | engineer/workflows/spec-phase.md:410-411 | — | Replace `/gsd:secure-phase` with `/secure-phase`. |
| R-WF-822 | REPLACE | engineer/workflows/spec-phase.md:513-515 | — | Change `gsd_run query commit` to `engineer_run query commit`. |
| R-WF-823 | REPLACE | engineer/workflows/spec-phase.md:529-530, 556, 71, 94 | .ai/workflows/execute-phase.md:19-23 | Replace `Next: /gsd:discuss-phase` and other `/gsd:` prompts with a closing report stating discuss-phase will load SPEC.md. |
| R-WF-824 | REPLACE | commands/spec-phase.md:2, 12, 36-37, 66 | .ai/commands/quick.md:1-14 | Rename to `spec-phase`, set `requires: [discuss-phase, phase]` and repoint at engineer paths. |

Done when:
- `grep -c "gsd_run\|_GSD_SHIM\|\.cjs\|~/.claude/gsd-core\|/gsd:" engineer/workflows/spec-phase.md` → 0
- `grep -n "session.open\|session.adopt" engineer/workflows/spec-phase.md` → ≥1

## 13. Reconciliation: references, templates, rules and config

53 template rows (R-TP), 105 reference rows (R-RF), 29 rules, guides and config rows (R-RL). Phase 6.

How to read the rows:

- **GSD target lines** are in the downloaded GSD copy at `9443672` (`agents/`, `commands/`, `engineer/`). "after X:N" is an insertion point.
- **Local source lines** are in `.ai/`, `.planning/` or `AGENTS.md` at `9443672`.
- **Action:** STITCH inserts the local block; REPLACE swaps GSD lines for local lines; REMOVE deletes GSD lines; NEW FILE creates the target from the local source; RENAME moves a file; KEEP-UPSTREAM keeps newer upstream content on purpose; DROP-LOCAL leaves local content behind on purpose.
- Apply the renames in [3.2](#32-mechanical-renames) to every copied block. Section 3.3 gives the final role names.
- Process each file bottom-up. Commit with a `Rows:` trailer naming the IDs done.

### Scope, method and conventions

- Verified at HEAD `9443672` (branch `manual-override`, clean). Upstream pin text was rebuilt byte-exact from `pin/.ai/gsd/PROVENANCE.json` (substitutions and conflict adaptations reversed, LOCAL-ADOPTION note stripped; 153 of 171 files sha-verified, the rest are fixture JSON with CRLF only). Every row comes from a three-way diff: pin to local (local adaptation) and pin to engineer (upstream drift). Table reflow, `*x*` to `_x_`, and added blank lines were treated as noise.
- Path conventions, applied wherever a row copies local text: `gsd_run` and `phase_run` and `python .ai/runtime/phase.py` become `engineer_run`; `~/.claude/gsd-core/x` and `gsd-core/x` become `engineer/x`; `.ai/references/methods/x` and `.ai/references/x` become `engineer/references/x`; `.ai/templates/x` becomes `engineer/templates/x`; `.ai/commands/x` becomes `commands/x`; `.ai/workflows/x` becomes `engineer/workflows/x`; `.ai/agents/x` becomes `agents/x`; `.planning/config.json` becomes `.planning/config.yaml`. `{runtime-contract}` stands for wherever `.ai/runtime/TEMPLATE-CONTRACT.md` lands; the runtime section owns that move.
- **Wording-only drift is skipped, by design.** That covers link-syntax conversion, agent and command renames (`gsd-planner` to `phase-preparer`, `/gsd:x` to `x`), stripped issue numbers (`#3172`), "Claude" to "the agent" substitutions (about 30 lines in checkpoints alone), example-path genericization (`gsd-core/...` to `example-project/...`, `~/.claude` to `~/.example-app`, `gsd backup` to `workflow backup`), and heading-level or case changes. The skipped hunks are listed per group so nothing is silently dropped.
- Engineer line numbers are given against the current `engineer/` files, not the pin. Where upstream inserted lines, the shift is already applied.

### Templates

| ID | Action | GSD target (path:lines) | Local source (path:lines) | Instruction |
|---|---|---|---|---|
| R-TP-01 | DROP-LOCAL | (none) | `.ai/templates/` LOCAL-ADOPTION blocks: UAT.md:375-392, VALIDATION.md:81-98, codebase/architecture.md:276-293, codebase/stack.md:207-224, context.md:375-392, continue-here.md:81-98, discussion-log.md:74-91, phase-prompt.md:656-673, planner-subagent-prompt.md:152-169, project.md:210-227, requirements.md:234-251, research-project/ARCHITECTURE.md:207-224, FEATURES.md:150-167, PITFALLS.md:203-220, STACK.md:123-140, SUMMARY.md:173-190, research.md:595-612, roadmap.md:205-222, spec.md:336-353, state.md:225-242, summary.md:353-370, user-setup.md:305-322, verification-report.md:362-379 | Do not copy any LOCAL-ADOPTION footer into `engineer/templates/`; record provenance once in THIRD-PARTY-NOTICES (R-RL-24). |
| R-TP-02 | STITCH | engineer/templates/phase-prompt.md:12 (insert after) | .ai/templates/phase-prompt.md:12-15 | Insert the planning-integrity note, pointing it at `{runtime-contract}#planning-record-integrity`. |
| R-TP-03 | REPLACE | engineer/templates/phase-prompt.md:19 | .ai/templates/phase-prompt.md:24 | Replace the "pre-computed wave" comment with "Declared planning label; execute-phase forms actual groups from dependencies and file overlap". |
| R-TP-04 | REPLACE | engineer/templates/phase-prompt.md:22-24 | .ai/templates/phase-prompt.md:27-28 | Replace the `files_deleted` comment so an undeclared deletion is out of scope and blocks, with no cleanup-wave carve-out. |
| R-TP-05 | STITCH | engineer/templates/phase-prompt.md:30 (insert after) | .ai/templates/phase-prompt.md:35-38 | Add the required `acceptance`, `documentation`, `checks` (argv lists) and `issue_refs` frontmatter keys. |
| R-TP-06 | STITCH | engineer/templates/phase-prompt.md:113 (insert after) | .ai/templates/phase-prompt.md:122-139 | Insert the `<threat_model>` block, whose Threat IDs link to canonical issues with a Pending fallback, and point it at `engineer/references/git-workflow.md#canonical-threat-tracking`. |
| R-TP-07 | REPLACE | engineer/templates/phase-prompt.md:144, 148 (insert after) | .ai/templates/phase-prompt.md:170, 175-178 | Replace the `wave` field-table row and append rows for `acceptance`, `documentation`, `checks` and `issue_refs`. |
| R-TP-08 | REPLACE | engineer/templates/phase-prompt.md:152-154 | .ai/templates/phase-prompt.md:182-193 | Replace "Wave is pre-computed" and the must-haves paragraph with the ordered-groups bullets and the coordinator-run `verify-work` sentence, rewriting `phase.py query init.execute-phase` to `engineer_run query init.execute-phase`. |
| R-TP-09 | REPLACE | engineer/templates/phase-prompt.md:59, 230, 256-258, 262-265, 514, 516 | .ai/templates/phase-prompt.md:67, 269, 295-296, 300-303, 552, 554 | Replace the sizing and split rules with the configured-cap, outcome-based split rules and the dependency-only SUMMARY-reference rule. |
| R-TP-10 | STITCH | engineer/templates/summary.md:6 (insert after) | .ai/templates/summary.md:6-10 | Insert the required current-record metadata list (`phase`, `plan`, `status`, `requirements-completed`, `acceptance`, `documentation`, `issue_refs`). |
| R-TP-11 | REPLACE | engineer/templates/summary.md:49 | .ai/templates/summary.md:53 | Replace "Copy ALL requirement IDs" with "include only IDs the delivered changes and evidence actually complete". |
| R-TP-12 | REPLACE | engineer/templates/summary.md:51-53 | .ai/templates/summary.md:55-62 | Replace the coverage header comments with the `acceptance`, `documentation` and `issue_refs` keys and the no-auto-approve coverage comment. |
| R-TP-13 | REPLACE | engineer/templates/summary.md:62 | .ai/templates/summary.md:71 | Replace the `human_judgment` comment so required human UAT is never waived. |
| R-TP-14 | STITCH | engineer/templates/summary.md:103 (insert after) | .ai/templates/summary.md:112-120 | Insert the `## Checks` section (tested revision, command, observed result, TDD Evidence note). |
| R-TP-15 | STITCH | engineer/templates/summary.md:155 (insert after), 165 (insert after) | .ai/templates/summary.md:168-190, 199-200 | Insert `## Threat Flags` and `## Threat Outcomes` before `## Next Phase Readiness`, and the canonical-threat-tracking bullet after the closing fence. |
| R-TP-16 | REPLACE | engineer/templates/summary.md:188, 203-208 | .ai/templates/summary.md:223, 238-242 | Replace the coverage Purpose line and the classifier contract with the mandatory coordinator/verifier classification (auto-pass needs non-empty passing evidence; required UAT stays pending); keep `engineer_run uat classify-coverage` only if the runtime implements it. |
| R-TP-17 | REPLACE | engineer/templates/summary.md:319 | .ai/templates/summary.md:342-349 | Replace "STATE.md updated" with the orchestrator-only STATE/CONTEXT/ROADMAP update rule, rewriting `phase.py query state.update-progress` to `engineer_run`. |
| R-TP-18 | STITCH | engineer/templates/UAT.md:3 (insert after) | .ai/templates/UAT.md:4-52 | Insert the Producer/Consumers lines and the full `## Authoring contract`, keeping the `issue.md#uat` links valid once R-TP-46 lands. |
| R-TP-19 | REPLACE | engineer/templates/UAT.md:11, 13 | .ai/templates/UAT.md:60, 62 | Remove `diagnosed` from the status enum and require one or more SUMMARY paths as `source`. |
| R-TP-20 | REPLACE | engineer/templates/UAT.md:20-60 | .ai/templates/UAT.md:68-110 | Replace the Current Test and Tests skeleton with the one-sentence expected result, entry point and fixtures, acceptance checklist, acceptance/action test entries, reply format and Human acceptance block. |
| R-TP-21 | STITCH | engineer/templates/UAT.md:73, 80-83 | .ai/templates/UAT.md:128-134 | Delete the `--gaps` comment and replace the four "Filled by diagnosis" fields with the bracketed diagnosis placeholders, keeping eng 76 `failed or resolved` and eng 84-85 `resolved_by`/`resolved_at`. |
| R-TP-22 | KEEP-UPSTREAM | engineer/templates/UAT.md:76, 84-85, 124-135 | (none) | Keep the gap `status: resolved` with `resolved_by`/`resolved_at` and its reconcile rule, rewriting `src/uat-predicate.cts` at eng 133 to the Python runtime predicate. |
| R-TP-23 | REPLACE | engineer/templates/UAT.md:104, 109, 111-112, 117, 123 | .ai/templates/UAT.md:151-154, 158, 160-161, 165, 170 | Replace the section rules: `awaiting: final human acceptance decision` state, unbracketed `pending`, explicit skip and blocked reasons, a `blocked` counter, and gaps feeding plan-phase. |
| R-TP-24 | REPLACE | engineer/templates/UAT.md:141-151 | .ai/templates/UAT.md:176-186 | Replace the diagnosis lifecycle so diagnosis runs while `status: partial` and never sets `diagnosed`. |
| R-TP-25 | REPLACE | engineer/templates/UAT.md:174-213 | .ai/templates/UAT.md:208-255 | Replace the lifecycle: `N PASS/FAIL/BLOCKED` replies, completion only when every action passes and an actual human acceptance is recorded, and no UAT runtime verbs. |
| R-TP-26 | REPLACE | engineer/templates/UAT.md:233-303 | .ai/templates/UAT.md:276-370 | Replace the good example with the fictional `status: partial` comments example. |
| R-TP-27 | REPLACE | engineer/templates/VALIDATION.md:4-5, 72 | .ai/templates/VALIDATION.md:4-5, 72 | Replace the status-lifecycle comments and the sampling rule with "at least 2 automated verifications in every consecutive 3-task window within a wave". |
| R-TP-28 | STITCH | engineer/templates/verification-report.md:90 (insert after) | .ai/templates/verification-report.md:91-101 | Insert the `## Deliverable Coverage` table and its classification paragraph. |
| R-TP-29 | REPLACE | engineer/templates/verification-report.md:203, 206-207, 209 | .ai/templates/verification-report.md:214, 217-218, 220 | Replace the Warning definition, the fix-plan handoff (the verifier returns gaps and does not author PLANs) and the task-cap wording. |
| R-TP-30 | KEEP-UPSTREAM | engineer/templates/verification-report.md:19 | (none) | Keep `covered_digest: "v4:sha256:..."` and do not restore local v1. |
| R-TP-31 | STITCH | engineer/templates/context.md:7 (insert before), 9 (insert before), 17 (insert after) | .ai/templates/context.md:7-15, 18-23, 33-37 | Insert the Discussion and Implementation gates, the required-frontmatter paragraph, and the `phase`/`discussion`/`issue_refs` frontmatter skeleton inside the File Template fence. |
| R-TP-32 | REPLACE | engineer/templates/state.md:9-14, 17 | .ai/templates/state.md:9-18, 21 | Replace the generator note (`scripts/gen-state-md-docs.cjs`, Node) with "derived by `state.save`" plus the closed-section-set paragraph, and rename `gsd_state_version` to `workflow_state_version` to match `.ai/runtime/lib/state.py:184`. |
| R-TP-33 | REMOVE | engineer/templates/state.md:46-64, 161-169 | .ai/templates/state.md:49-50 (section removed locally) | Delete the Performance Metrics section and its guidance, since it has no runtime writer. |
| R-TP-34 | REPLACE | engineer/templates/state.md:83, 89, 172, 174-180, 185 | .ai/templates/state.md:68-76, 82-83, 157-159, 161-168, 173-178 | Replace the Blockers, Deferred, Decisions, Pending Todos and Blockers guidance with the verb-backed versions (`state.clear-blocker`, `state.add-deferred`, `state.add-decision`), and add `### Roadmap Evolution`. |
| R-TP-35 | STITCH | engineer/templates/state.md:197, 204 (insert after), 206 (insert after) | .ai/templates/state.md:190, 198-201, 204-222 | Raise the size cap to 150 lines, add the `planning.validate` sentence, and insert the `<retirement>` table. |
| R-TP-36 | REPLACE | engineer/templates/discussion-log.md:7, 32 (insert after), 58 | .ai/templates/discussion-log.md:7-10, 36-37, 63-66 | Replace "NOT for LLM consumption" with the audit-record rule, add the Recommendation evidence field, and require the log for every discussion, written incrementally. |
| R-TP-37 | STITCH | engineer/templates/milestone.md:1 (insert after), 116 (insert after) | .ai/templates/milestone.md:2-28, 143-180 | Insert the purpose, producer and consumer header, and append the Counterexample, Division of labour and Completion criteria sections. |
| R-TP-38 | REPLACE | engineer/templates/milestone.md:20-24, 32-37, 54-61, 66, 82-86, 107-111 | .ai/templates/milestone.md:47-50, 58-63, 80-87, 92-94, 110-113, 134-137 | Replace LOC, task-count and day stats and `feat(XX-XX)` ranges with lines changed, phase/plan counts from `milestone_phases`, and `docs(NN)` or SHA ranges. |
| R-TP-39 | STITCH | engineer/templates/planner-subagent-prompt.md:13 (insert after), 30, 65, 71, 118 (insert after) | .ai/templates/planner-subagent-prompt.md:14-25, 42, 77-80, 86-88, 136-150 | Add the repository/branch/revision/owned-output fields and their placeholder rows, the host-pseudocode note, and the revision-assignment block that points at the engineer plan-phase correction packet. |
| R-TP-40 | REPLACE | engineer/templates/project.md:146-147 | .ai/templates/project.md:146-151 | Replace "implemented by workflows/transition.md" with the coordinator-applies-checklist paragraph, including "Completing one phase does not authorize the next". |
| R-TP-41 | STITCH | engineer/templates/codebase/architecture.md:255 (insert after) | .ai/templates/codebase/architecture.md:258-274 | Append the `<freshness>` block (`codebase.status`, 15-commit threshold, `codebase.staleness.architecture`). |
| R-TP-42 | STITCH | engineer/templates/codebase/stack.md:186 (insert after) | .ai/templates/codebase/stack.md:189-205 | Append the `<freshness>` block (1-commit threshold, `codebase.staleness.stack`). |
| R-TP-43 | KEEP-UPSTREAM | engineer/templates/README.md:1-83 | (none) | Keep the canonical artifact registry structure, including the eng 20 `/gsd:capture --backlog` upstream fix, rewriting `/gsd:` commands per convention. |
| R-TP-44 | REPLACE | engineer/templates/README.md:23, 58-59, 81 | .planning/config.yaml:1-158 | Point the config row at `config.yaml` (`engineer/templates/config.yaml`), set the AI-SPEC and DEBUG template cells to `*(none)*` because those templates are deleted, and replace `gsd-core/bin/lib/artifacts.cjs` with the Python runtime's artifact list. |
| R-TP-45 | STITCH | engineer/templates/README.md:31 (insert after), 60 (insert after) | .ai/references/phase-artifacts.md:10, 15, 17; .ai/templates/README.md:20-21 | Add registry rows for `NN-DISCUSSION-LOG.md`, `NN-VERIFICATION.md`, `.continue-here.md`, `.planning/specs/SPEC-*.md` (CURRENT-SPEC.md), `.planning/decisions/ADR-*.md` (ADR.md), and the issue/pull-request templates. |
| R-TP-46 | NEW FILE | engineer/templates/issue.md | .ai/templates/issue.md:1-365 | Create from local, keeping `../references/git-workflow.md` links (they resolve once R-RF-91 lands). |
| R-TP-47 | NEW FILE | engineer/templates/pull-request.md | .ai/templates/pull-request.md:1-128 | Create from local unchanged except the path convention. |
| R-TP-48 | NEW FILE | engineer/templates/ADR.md | .ai/templates/ADR.md:1-204 | Create from local, adding one line that the decision itself is owned by PROJECT.md Key Decisions (`state.add-decision`) and the ADR holds only its rationale (see R-RL-05). |
| R-TP-49 | NEW FILE | engineer/templates/CURRENT-SPEC.md | .ai/templates/CURRENT-SPEC.md:1-216 | Create from local unchanged. |
| R-TP-50 | NEW FILE | engineer/templates/rule.md | .ai/templates/rule.md:1-28 | Create from local unchanged. |
| R-TP-51 | STITCH | engineer/templates/TEMPLATE.md:1 (empty placeholder) | .ai/templates/README.md:3-7; .ai/references/template-adaptation.md:46-56; .ai/guides/ARTIFACT-GUIDE.md:15-36, 133-173 | Fill the placeholder with the read-full-template rule, the authoring sequence, the "connect a template to the Python runtime" table and boundaries, the handoff checklist, and the weak-versus-useful handoff table. |
| R-TP-52 | DROP-LOCAL | (none) | .ai/templates/README.md:1-2, 9-11, 13-30 | Do not carry the local catalog prose or the stale "These 28 artifact templates" count (line 25); R-TP-43 to R-TP-45 own the registry. |
| R-TP-53 | REMOVE | engineer/templates/{AI-SPEC,DEBUG,config.json,copilot-instructions,dev-preferences,milestone-archive,retrospective,user-profile,summary-complex,summary-minimal,summary-standard,summary.compact,user-setup.compact}.md/.json | (none) | Delete the 13 decided non-kept templates after R-TP-44 removes their registry references. |

Wording-only template drift (skipped): phase-prompt.md:3, 28, 48-51, 95, 288, 392-394, 550; summary.md:29, 217, 219 and upstream eng 13-14, 25, 184; context.md:25-26, 362-363; spec.md:11-12, 125, 221, 235-309; research.md:21, 571, 592; user-setup.md:70; VALIDATION.md:34; verification-report.md:15, 200, 202; codebase/architecture.md:149, 183; planner-subagent-prompt.md:3, 49, 92, 101, 134; project.md:173; UAT.md:186. roadmap.md, requirements.md, continue-here.md and research-project/* differ only by the footer (R-TP-01).

Done when:
- `grep -rc "LOCAL-ADOPTION" engineer/templates` reports 0 for every file.
- `grep -nE "^(acceptance|documentation|checks|issue_refs): \[\]" engineer/templates/phase-prompt.md` returns 4 lines, and `grep -n "<threat_model>" engineer/templates/phase-prompt.md` returns a hit.
- `grep -n "diagnosed" engineer/templates/UAT.md` returns nothing, while `grep -c "resolved_by" engineer/templates/UAT.md` is at least 2 and `grep -n "PENDING HUMAN acceptance" engineer/templates/UAT.md` returns a hit.
- `grep -nE "## (Checks|Threat Flags|Threat Outcomes)" engineer/templates/summary.md` returns 3 lines, and `grep -n "Copy ALL requirement IDs" engineer/templates/summary.md` returns nothing.
- `grep -n "## Deliverable Coverage" engineer/templates/verification-report.md` and `grep -n 'covered_digest: "v4' engineer/templates/verification-report.md` both return hits.
- `grep -n "at least 2 automated verifications" engineer/templates/VALIDATION.md` returns a hit.
- `grep -n "<retirement>" engineer/templates/state.md` returns a hit, while `grep -nE "Performance Metrics|gen-state-md-docs|gsd_state_version" engineer/templates/state.md` returns nothing.
- `grep -n "discussion: pending" engineer/templates/context.md` and `grep -n "<freshness>" engineer/templates/codebase/*.md` (2 hits) return hits.
- `ls engineer/templates/{ADR,CURRENT-SPEC,issue,pull-request,rule}.md` succeeds, `test -s engineer/templates/TEMPLATE.md` passes, and `grep -n "config.json" engineer/templates/README.md` returns nothing.

### References (shared)

| ID | Action | GSD target (path:lines) | Local source (path:lines) | Instruction |
|---|---|---|---|---|
| R-RF-01 | DROP-LOCAL | (none) | "Local method" banner in .ai/references/methods/: common-bug-patterns.md:3-7, debugger-bug-taxonomy.md:3-7, debugger-fix-acceptance.md:3-7, debugger-philosophy.md:3-7, debugger-prevention.md:3-7, debugger-rca-branching.md:3-7, debugger-repro-hardening.md:3-7, debugger-sbfl.md:3-7, debugger-techniques.md:3-7, executor-examples.md:3-7, ios-scaffold.md:3-7, thinking-models-debug.md:3-7, thinking-models-execution.md:3-7 | Do not copy the per-file banner; R-RF-62 states that boundary once in REFERENCE.md. |
| R-RF-02 | KEEP-UPSTREAM | engineer/references/{common-bug-patterns,debugger-philosophy,debugger-prevention,debugger-sbfl,domain-probes,questioning,research-philosophy,research-verification-protocol,scout-codebase,thinking-models-debug,thinking-models-execution,thinking-models-research,planner-reviews,verifier-wiring-patterns}.md (whole) | matching .ai/references{,/methods}/ files | Keep upstream as-is with the path convention, because the local drift in these files is wording, provenance or links only. |
| R-RF-03 | REPLACE | engineer/references/checkpoints.md:2-4 | .ai/references/methods/checkpoints.md:17-27 | Replace "Claude automates everything" with the six authority principles (prepare first, never infer approval, preserve authorization, stop only dependent work, secure credentials). |
| R-RF-04 | REPLACE | engineer/references/checkpoints.md:6-13 | .ai/references/methods/checkpoints.md:29-34 | Replace the golden rules, including rule 5's auto-approve, with the blocking-human paragraph, and add one sentence: an unattended `checkpoint:decision` may proceed only on its declared `auto_select` when recorded authorization delegates that choice, otherwise it escalates. |
| R-RF-05 | REPLACE | engineer/references/checkpoints.md:15-24 | .ai/references/methods/checkpoints.md:36-54 | Replace the `gate` auto-mode table and two-layer paragraph with the ordered condition/action table and the "no auto-approval configuration flag" rule. |
| R-RF-06 | KEEP-UPSTREAM | engineer/references/checkpoints.md:158, 177-178 | (none) | Keep the `auto_select="<option-id>"` attribute and its plan-structure validation, bound by R-RF-04. |
| R-RF-07 | DROP-LOCAL | engineer/references/checkpoints.md:34-38 (keep) | .ai/references/methods/checkpoints.md:64-66 | Keep upstream `human_verify_mode = end-of-phase`, which defers verification to UAT rather than approving it, and change only `config.json` to `config.yaml` on eng 38. |
| R-RF-08 | STITCH | engineer/references/checkpoints.md:125 | .ai/references/methods/checkpoints.md:142-147 | Change tracer row 2 so a tracer whose `<verify>` carries `<human-check>` STOPs in auto mode too, because a passing automated check cannot stand in for a human decision. |
| R-RF-09 | REPLACE | engineer/references/checkpoints.md:477-501 | .ai/references/methods/checkpoints.md:466-486 | Replace the paste-your-API-key example with the secure secret-entry guidance and example. |
| R-RF-10 | REPLACE | engineer/references/checkpoints.md:521, 524, 526 | .ai/references/methods/checkpoints.md:505-519 | Replace the `gsd_run run-with-timeout` readiness wait with the bounded bash loop, and replace port-kill and server-lifecycle with the owned-process rules. |
| R-RF-11 | REPLACE | engineer/references/checkpoints.md:528-541, 548-549, 556 | .ai/references/methods/checkpoints.md:521-528, 535-536, 543 | Replace the CLI auto-install table and protocol with "no silent install; report the missing capability", along with the matching failure rows and cross-platform note. |
| R-RF-12 | REPLACE | engineer/references/checkpoints.md:334, 340, 443, 813, 829-857, 864 | .ai/references/methods/checkpoints.md:330, 336, 433, 796, 812-819, 826 | Replace the auto-approving `checkpoint:tdd-review` with the TDD evidence review, and apply the record-the-answer resume and authorized-automation rule lines. |
| R-RF-13 | DROP-LOCAL | (none) | .ai/references/methods/checkpoints.md:1-15 | Do not carry the "XML is not a supported executable checkpoint in the Python runner" boundary, because engineer execute-phase handles checkpoints. |
| R-RF-14 | REPLACE | engineer/references/context-budget.md:13, 18-19 | .ai/references/methods/context-budget.md:7-8, 12-19 | Replace rule 1 ("never read agent definition files") with "read your assigned role and required inputs", and append the evidence-selection, scout-only nesting and handoff rules. |
| R-RF-15 | KEEP-UPSTREAM | engineer/references/context-budget.md:15-17, 21-28 | (none) | Keep the read-depth-by-`context_window` table, which local universal-anti-patterns and config.yaml:13-20 still use, reading `.planning/config.yaml`. |
| R-RF-16 | REPLACE | engineer/references/context-budget.md:32-39, 49, 51-85 | .ai/references/methods/context-budget.md:23-30, 40, 42-48 | Replace the `context_guard_mode` tiers, the structural-only claim and the MCP settings section with heuristic tiers, the independent-verification line and the host-neutral tool-cost paragraph. |
| R-RF-17 | REPLACE | engineer/references/context-budget.md:89-123 | .ai/references/methods/context-budget.md:52-88 | Replace mandatory `estimate` and `estimate-calibration`, "2-3 tasks maximum" and "ALWAYS split if" with the advisory estimate, configured task cap and `estimate_scope` split rules. |
| R-RF-18 | REPLACE | engineer/references/debugger-bug-taxonomy.md:44, 87-91 | .ai/references/methods/debugger-bug-taxonomy.md:50, 93-106 | Replace mandatory `rr` with "available record-replay tooling", and add the Tool availability section (no auto-install). |
| R-RF-19 | REPLACE | engineer/references/debugger-fix-acceptance.md:29-32, 50-52, 63, 66 (insert after), 74, 78, 82-83, 121-134 | .ai/references/methods/debugger-fix-acceptance.md:35-44, 62-64, 75, 79-84, 92, 96, 100-101, 139-151 | Replace Stryker-only mutation and `git stash`/`revert` with project-tool mutation in isolated diagnostic checkouts, add the skipped-and-incomplete verdicts, and replace the gauntlet timeouts with project-bounded checks. |
| R-RF-20 | REPLACE | engineer/references/debugger-rca-branching.md:77-79 | .ai/references/methods/debugger-rca-branching.md:83-86 | Replace "fix must address BOTH" with "record both conditions, then choose the smallest sufficient repair". |
| R-RF-21 | REPLACE | engineer/references/debugger-repro-hardening.md:21-22, 28 | .ai/references/methods/debugger-repro-hardening.md:27-29, 35 | Allow the shrinker only when a property framework is already configured, with no new installs. |
| R-RF-22 | STITCH | engineer/references/debugger-techniques.md:86, 212 (insert before) | .ai/references/methods/debugger-techniques.md:91, 217-220 | Make shrinking framework-optional, and require a coordinator-assigned diagnostic checkout before `git bisect`. |
| R-RF-23 | REPLACE | engineer/references/debugger-semantic-recall.md:1-81 | .ai/references/methods/debugger-semantic-recall.md:1-54 | Replace MemPalace recall with offline knowledge-base recall (`rg` plus semantic comparison, coordinator-owned writes, redaction, no new infrastructure). |
| R-RF-24 | KEEP-UPSTREAM | engineer/references/execute-mvp-tdd.md:13-21, 67-77 | (none) | Keep the RED-evidence gate that defers to tdd.md step 4 and the `check tdd-red-evidence` exit-69 rule, rewriting `gsd_run` to `engineer_run`. |
| R-RF-25 | REPLACE | engineer/references/execute-mvp-tdd.md:5-11 | .ai/references/methods/execute-mvp-tdd.md:7-15 | Replace TDD_MODE triggering with "applies when the committed assignment requires TDD (`type: tdd` or `tdd="true"`)", classifying config by effect rather than extension. |
| R-RF-26 | REPLACE | engineer/references/execute-mvp-tdd.md:53-54, 60-65 | .ai/references/methods/execute-mvp-tdd.md:49-53, 57-67 | Replace the worker's STATE `last_gate_trip` write and `--force-mvp-gate` with SUMMARY Remaining and coordinator reconciliation, the honored test-deferral rule, and the refactor-scope rules. |
| R-RF-27 | DROP-LOCAL | (none) | .ai/references/methods/execute-mvp-tdd.md:3-5, 19-34 | Do not carry "no evidence-check SDK command" or commit-prefix-only RED detection, because upstream's classifier is kept (R-RF-24, R-RF-52). |
| R-RF-28 | REPLACE | engineer/references/executor-examples.md:75-117, 118 (insert after) | .ai/references/methods/executor-examples.md:76-94 | Replace the `deferred-items.md` ledger and parsing rules with "record in the assigned SUMMARY Remaining", and add the checkpoint-contract pointer. |
| R-RF-29 | REPLACE | engineer/references/failing-direction.md:34-38 | .ai/references/methods/failing-direction.md:34-38 | Replace "treat this check as silent when `{FAILING_DIRECTIONS}` is absent" with the static `<fails_when>` inspection fallback, keeping the probe path when the probe is supplied. |
| R-RF-30 | STITCH | engineer/references/gates.md:9-16, 18-25, 26-34, 35-44, 46-59 | .ai/references/methods/gates.md:9-11, 18-20, 24-29, 33-37, 41-45, 56-58 | Add the authorization/ownership pre-flight, no-identical-retry and no-count-exemption revision, no-mode-flag escalation and ownership/uncertain-process abort rules, plus matrix rows for UAT, Publication and Recovery. |
| R-RF-31 | DROP-LOCAL | (none) | .ai/references/methods/gates.md:1-5, 13-16, 51-55, 60-62 | Do not carry the local retitle, the `.ai/runtime` planning.review bullet or the local-procedure rows that duplicate the upstream matrix. |
| R-RF-32 | STITCH | engineer/references/honest-verifier.md:21 (insert after), 58-69 | .ai/references/methods/honest-verifier.md:9-21 | Add the VERIFIED/FAILED/PRESENT_BEHAVIOR_UNVERIFIED/insufficient_spec case table, and replace the Node `probe-core` engine surface with the "plain-string or `statement` object, no parser service" paragraph. |
| R-RF-33 | STITCH | engineer/references/honest-verifier.md:70 (insert after) | .ai/references/methods/honest-verifier.md:60-70 | Insert the "Negative constraints and incidental success" section before Capable-tier. |
| R-RF-34 | REPLACE | engineer/references/ios-scaffold.md:23-31, 71 | .ai/references/methods/ios-scaffold.md:29-44, 84-85 | Replace mandatory XcodeGen and `brew install` with "preserve the project's build system, never auto-install a generator", and follow the generated-file policy. |
| R-RF-35 | REPLACE | engineer/references/nyquist-compliance.md:33-36, 49, 51-55, 68, 74 | .ai/references/methods/nyquist-compliance.md:25-28, 41, 43-47, 60, 66 | Replace "3 consecutive without automated verify" with "fewer than 2 in any 3-task window", "Wave 0" with "prerequisite dependency", and "max 3 loops" with "until resolved or blocked". |
| R-RF-36 | REPLACE | engineer/references/nyquist-compliance.md:11-14, 24-25 | .ai/references/methods/nyquist-compliance.md:3-7, 17 | Replace the `workflow.nyquist_validation` skip with applicability by Validation Architecture or assigned VALIDATION, unless config.yaml adopts that key (see R-RL-27). |
| R-RF-37 | REPLACE | engineer/references/plan-checker-examples.md:7-41 | .ai/references/methods/plan-checker-examples.md:7-52 | Replace the "5 tasks / 12 files exceeds budget" blocker example with the outcome-scoped D-07 warning example that carries `id` and `authority`. |
| R-RF-38 | REPLACE | engineer/references/planner-antipatterns.md:23, 232-256 | .ai/references/methods/planner-antipatterns.md:23, 234-239 | Replace "Claude should run vercel" with deployment-authorization wording, and replace the "external review before PR open" ordering with the draft-PR-first rule. |
| R-RF-39 | STITCH | engineer/references/planner-antipatterns.md:103, 130, 176, 182 | .ai/references/methods/planner-antipatterns.md:103, 130, 176, 182 | Keep the upstream `verify.plan-structure` gate only if `engineer_run` implements it; otherwise apply the local "review rule, marker is reviewer context" lines. |
| R-RF-40 | REPLACE | engineer/references/planner-chunked.md:3-5, 26-30, 46-47, 52-53 | .ai/references/methods/planner-chunked.md:3-5, 26-37, 51-52, 57-58 | Replace the `--chunked` and `chunked_parallel` dispatch with coordinator-assigned bounded plans, dependency/file-overlap waves and content-checked resume. |
| R-RF-41 | REPLACE | engineer/references/planner-coupling.md:3-7, 22-24, 33-35 | .ai/references/methods/planner-coupling.md:3, 18-20, 29-30 | Replace "re-wave" with "declare shared `resources`", and state that `coupling_justified` is review explanation, not a scheduling exemption. |
| R-RF-42 | REPLACE | engineer/references/planner-gap-closure.md:5, 15-16, 30, 49 | .ai/references/methods/planner-gap-closure.md:5, 15-16, 30-31, 50-52 | Read Findings, Acceptance and unresolved UAT instead of `status: diagnosed`, exclude deferred items only when authorized, and require complete PLAN contract fields. |
| R-RF-43 | KEEP-UPSTREAM | engineer/references/planner-gap-closure.md:64 | (none) | Keep threat-ID continuation after the existing `T-{phase}-NN` registers. |
| R-RF-44 | REPLACE | engineer/references/planner-guidance.md:5-7, 27, 41-46, 50-64, 72-74, 162, 167, 176 | .ai/references/methods/planner-guidance.md:5-7, 29, 43-48, 52-64, 72-74, 162, 167, 176 | Replace the solo-Claude framing, "2-3 tasks max" and the context-percentage sizing with cap/`estimate_scope` sizing, contract-then-thin-slice ordering, and "implementation requires explicit user authorization". |
| R-RF-45 | REPLACE | engineer/references/planner-interface-context.md:20, 41, 48 | .ai/references/methods/planner-interface-context.md:20, 41, 48 | Replace the "Wave 0 skeleton" with a real `depends_on` edge, and verify interfaces by typecheck against the dependency revision. |
| R-RF-46 | KEEP-UPSTREAM | engineer/references/planner-load-graph-context.md:5-47 | (none) | Keep the graphify `status` gate, CLI or built-in fallback and full-word query guidance, rewriting `gsd_run` to `engineer_run`. |
| R-RF-47 | STITCH | engineer/references/planner-load-graph-context.md:47 (insert after) | .ai/references/methods/planner-load-graph-context.md:9-17, 19-20 | Append the "verify relevant edges against current source, annotate stale ones, dependencies belong in `depends_on` and resources in `resources`" guidance. |
| R-RF-48 | REPLACE | engineer/references/planner-mvp-mode.md:3, 17, 32-42, 48 | .ai/references/methods/planner-mvp-mode.md:5-7, 21, 36-46, 52 | Require an explicit PLAN-recorded tracer exception, replace `WALKING_SKELETON`/`SKELETON.md` (skeleton-template.md is not kept) with decisions recorded in CONTEXT, and move scope splitting to the coordinator. |
| R-RF-49 | DROP-LOCAL | engineer/references/planner-mvp-mode.md:23 (keep) | .ai/references/methods/planner-mvp-mode.md:3-4, 27 | Keep upstream `type="tracer"` rather than local `type="auto"`, provided the Python runner accepts tracer tasks. |
| R-RF-50 | REPLACE | engineer/references/planner-preconditions.md:34-35, 59-60, 108-109, 124, 128-134 | .ai/references/methods/planner-preconditions.md:31-32, 56-57, 105-106, 121, 125-127 | Make `depends_on` inter-plan only, record cross-phase prerequisites in CONTEXT, preserve completed slices on an unmet precondition, and replace the `cmdVerifyPlanStructure` (Node) note. |
| R-RF-51 | REPLACE | engineer/references/planner-quick-batch.md:1-71 | .ai/references/methods/planner-quick-batch.md:1-40 | Replace quick-batch `quick_id` mode with bounded batch planning (sibling plan IDs, exact `files_modified`/`files_deleted`/`resources`, complete contract). |
| R-RF-52 | KEEP-UPSTREAM | engineer/references/tdd.md:81, 97-105, 188-213, 289, 296, 307-309, 319, 345 | (none) | Keep the RED-evidence format adapters (TAP, JUnit, swift-testing, unittest, go test), test-location patterns, letter-suffix phase IDs and commit-ancestry ordering, with `gsd_run` rewritten to `engineer_run`. |
| R-RF-53 | REPLACE | engineer/references/tdd.md:42-44, 116, 147, 164, 180, 283 | .ai/references/methods/tdd.md:51-54, 120, 151-156, 173, 189, 270 | Quote `plan: "NN"`, add the contract-fields comment, restrict refactors to changed code, install a framework only when authorized, and apply TDD to any assigned `type: tdd` plan. |
| R-RF-54 | REPLACE | engineer/references/tdd.md:325-343, 349-350 | .ai/references/methods/tdd.md:300-336 | Replace the auto-inserted advisory review checkpoint with the coordinator review table and the "Independent TDD evidence review" section (missing required evidence is a gap), keeping eng 345 as the gate-order rule. |
| R-RF-55 | DROP-LOCAL | (none) | .ai/references/methods/tdd.md:1-6, 108-109, 276, 283, 289-294 | Do not carry "no SDK / no pre-GREEN gate" or the classifier removals; carry only lines 7-8 (honor test deferral) into the eng 1 overview. |
| R-RF-56 | REPLACE | engineer/references/planner-reversibility.md:49-51, 57-59, 74-82 | .ai/references/methods/planner-reversibility.md:47-48, 54-55, 72-75 | Replace the `REVERSIBILITY_GATES=false` override with "an unattended run or mode label cannot authorize an unresolved one-way choice". |
| R-RF-57 | KEEP-UPSTREAM | engineer/references/planner-reversibility.md:23, 104-118, 129-130 | (none) | Keep the "Already settled" section and its table pointer, and fix "below" to "above" on eng 129. |
| R-RF-58 | REPLACE | engineer/references/planner-revision.md:13, 22, 25, 36-38, 46, 69, 86 (insert after) | .ai/references/methods/planner-revision.md:12-17, 26, 30-31, 42-48, 56-57, 80, 98-104 | Add the packet-bounded reading, finding `id`/`authority` fields, the legacy-issue authority rule, the `estimate_scope` scope fix and the affected-recheck/evidence-reuse paragraph. |
| R-RF-59 | REPLACE | engineer/references/planner-source-audit.md:25, 33, 52, 55, 64, 73 | .ai/references/methods/planner-source-audit.md:25, 33, 52, 55, 64, 73-77 | State that research cannot add or defer scope, keep authorized corrections moving, and replace context-cost splits with outcome splits. |
| R-RF-60 | REPLACE | engineer/references/planner-verify-command-grounding.md:3-7, 16 | .ai/references/methods/planner-verify-command-grounding.md:3-4, 13 | Read prior verified commands from committed SUMMARY evidence or a supplied `prior_verify_commands`, with no assumed injection. |
| R-RF-61 | KEEP-UPSTREAM | engineer/references/planner-verify-command-grounding.md:19-49 | (none) | Keep the HEAD-baseline rule for count/match gates and the root-relative path rule. |
| R-RF-62 | STITCH | engineer/references/REFERENCE.md:1 (empty placeholder) | .ai/references/methods/README.md:1-26; .ai/references/methods/common-bug-patterns.md:3-7 | Fill the placeholder with the catalog purpose, the read-only-what-you-need rule, the "methods add no commands or authority" paragraph and the stack-review pointer, plus the banner's ownership and no-install boundary as one paragraph. |
| R-RF-63 | REPLACE | engineer/references/research-documentation-lookup.md:1-31 | .ai/references/methods/research-documentation-lookup.md:1-19 | Replace the ctx7 `npm install -g` fallback with the manifest-first, official-docs, record-the-source procedure. |
| R-RF-64 | REPLACE | engineer/references/security-asvs-levels.md:3, 11 | .ai/references/methods/security-asvs-levels.md:3-7, 15-16 | State that these are review depths rather than certification, and require behavioral evidence rather than a grep hit for L1. |
| R-RF-65 | REPLACE | engineer/references/thinking-models-planning.md:21, 33, 41; engineer/references/thinking-models-verification.md:32, 38, 52 | .ai/references/methods/thinking-models-planning.md:21, 33, 41; .ai/references/methods/thinking-models-verification.md:32, 38, 52 | Apply the ownership-not-section MECE check, the coordinator decision for one-way choices, the no-invented-findings disconfirmation rule, counts as signals, and revision-scoped re-verification. |
| R-RF-66 | REPLACE | engineer/references/untrusted-input-boundary.md:4, 12 | .ai/references/methods/untrusted-input-boundary.md:4, 12 | Defer to the actual instruction hierarchy, and state that hooks are advisory, not an injection scanner. |
| R-RF-67 | REPLACE | engineer/references/verification-overrides.md:1-227 | .ai/references/methods/verification-overrides.md:1-71 | Replace fuzzy-matched `PASSED (override)` waivers with decision-reference traceability that never waives acceptance, then fix the `overrides_applied` consumers in engineer/templates/verification-report.md and agents/gsd-verifier.md. |
| R-RF-68 | STITCH | engineer/references/verification-patterns.md:1 (insert before), 486, 535, 568, 586-591, 620, 622 | .ai/references/methods/verification-patterns.md:2-6, 493-496, 545-551, 584-586, 604-613, 642, 644 | Add the "examples are discovery, not proof; no UAT pass from inspection" note, receipt reuse instead of rescans, precise human-routing conditions, and the no-auto-install lines. |
| R-RF-69 | REPLACE | engineer/references/verifier-evidence-gate.md:8-116, 157-158 | .ai/references/methods/verifier-evidence-gate.md:8-61, 102-103 | Replace timestamp/80%-token classification with revision-diff regression, plus "demonstrated failure blocks, unsupported preference is advisory, never turns missing verification into passed". |
| R-RF-70 | REPLACE | engineer/references/verifier-phase-gates.md:3-8, 10-64, 105, 165, 172, 183-203 | .ai/references/methods/verifier-phase-gates.md:3-6, 8-16, 57, 117, 124, 135-157 | Replace the `check.decision-coverage-verify` handler with the manual Decision Coverage section unless `engineer_run` ports it, replace "auto-pass UAT" on infrastructure phases with "do not invent UX checks", and add the supporting-reference pointers. |
| R-RF-71 | KEEP-UPSTREAM | engineer/references/verify-command-path-resolvability.md:9-17, 21-47 | (none) | Keep the probe contract, the quick-mode `--dir` caller and `outside_root` for absolute targets, rewriting `gsd_run` to `engineer_run`. |
| R-RF-72 | REPLACE | engineer/references/verify-command-path-resolvability.md:18-19, 29 | .ai/references/methods/verify-command-path-resolvability.md:9-17, 23 | Replace "treat this dimension as silent when `{VERIFY_PATHS}` is absent" with the manual literal-path inspection fallback. |
| R-RF-73 | REPLACE | engineer/references/verify-mvp-mode.md:3, 7-12, 16-20, 24, 30-56, 64-70 | .ai/references/methods/verify-mvp-mode.md:3-6, 10-13, 17-20, 24-27, 33-61, 69-84 | Replace `mode: mvp`/`/gsd:mvp-phase` gating with an assigned user story, use the UAT authoring contract and `N PASS/FAIL/BLOCKED` replies, and state that no framing auto-passes UAT. |
| R-RF-74 | REPLACE | engineer/references/worktree-branch-check.md:3-15, 18-25, 30, 33-34, 40 | .ai/references/worktree-branch-check.md:3-24, 27-33, 38, 41-42, 48 | Scope the guard to `harness-worktree` (the root pin covers `orchestrator-worktree`), and add the `phase-`/`quick-`/`review-`/`verify-` namespaces to the regex. |
| R-RF-75 | DROP-LOCAL | (none) | .ai/references/worktree-branch-check.md:55-65 | Do not carry the exit-42 orchestrator section, because engineer/workflows/execute-phase/steps/worktree-recovery-policy.md:7 already owns it. |
| R-RF-76 | REPLACE | engineer/references/worktree-path-safety.md:164-178 | .ai/references/worktree-path-safety.md:128-136 | Move "prefer relative paths" ahead of the guard, and replace bash `[[ "$ABS_PATH" != "$WT_ROOT"* ]]` with the POSIX `${ABS_PATH#"$WT_ROOT"}` test. |
| R-RF-77 | KEEP-UPSTREAM | engineer/references/worktree-path-safety.md:103-123, 179-499 | (none) | Keep the immediate-submodule allowance, the branch-check pointer and the new step 0c `<automated>` absolute-path guard, all bash. |
| R-RF-78 | REPLACE | engineer/references/universal-anti-patterns.md:9 | .ai/references/methods/context-budget.md:7-8 | Replace "Never read agent definition files" with the role-reading rule, and do not carry local universal-anti-patterns.md:10-12 (a known inconsistency). |
| R-RF-79 | REPLACE | engineer/references/universal-anti-patterns.md:11, 24-25, 37, 49-51, 53-58 | .ai/references/universal-anti-patterns.md:15-17, 37-42, 58-62, 81-83, 88-98 | Read `config.yaml`, use project agent names (pending the agents section), route state/roadmap writes through `engineer_run query`, and replace the yolo/gsd_run/plan-pattern rules with the runtime rules. |
| R-RF-80 | DROP-LOCAL | engineer/references/universal-anti-patterns.md:19, 60-64 (keep) | .ai/references/universal-anti-patterns.md:27-33, 100 | Keep upstream rule 8 (`.planning/logs/`) and the iOS rules, since ios-scaffold.md is kept. |
| R-RF-81 | REPLACE | engineer/references/gate-prompts.md:5 | .ai/references/gate-prompts.md:5 | Inline the checkpoint format, because ui-brand.md is not kept. |
| R-RF-82 | REPLACE | engineer/references/few-shot-examples/plan-checker.md:39, 43 | .ai/references/methods/few-shot-examples/plan-checker.md:39, 43 | Reframe the same-file example as a producer/consumer dependency finding (shared ownership already serializes dispatch). |
| R-RF-83 | KEEP-UPSTREAM | engineer/references/{edge-probe,prohibition-probe,ui-consideration-probe}.md, edge-probe-fixtures/, prohibition-probe-fixtures/ | (none) | Keep the feature probes and fixtures, applying only the path convention. |
| R-RF-84 | REPLACE | engineer/references/specless-probe-fallback.md:20-36 | (none) | Replace the `node spec-section.cjs` and `npm run build:lib` helper with an `engineer_run` or Python equivalent (no Node). |
| R-RF-85 | REMOVE | engineer/references/git-integration.md:1-309 | .ai/references/git-workflow.md:1-316 | Delete after R-RF-91 lands, first confirming that per-task commit formats (60-120) are covered and that `sub_repos` (259-309) is intentionally unsupported. |
| R-RF-86 | REMOVE | engineer/references/agent-contracts.md:1-97 | .ai/references/worker-handoff.md:1-190 | Delete after R-RF-92 lands, first moving any still-used marker regexes (83-97) into the engineer workflows that grep them. |
| R-RF-87 | REMOVE | engineer/references/revision-loop.md:1-204 | .ai/references/bounded-correction-dispatch.md:1-50 | Delete after R-RF-93 lands, because the max-3 escalation conflicts with local "no fixed review-count exemption" (gates.md:28). |
| R-RF-88 | REMOVE | engineer/references/artifact-types.md:1-138 | .ai/references/phase-artifacts.md:1-35 | Delete after R-RF-94 lands. |
| R-RF-89 | REMOVE | engineer/references/model-profiles.md:1-289 | .ai/runtime/lib/models.py | Delete after confirming that Dynamic Routing (167-209) is intentionally dropped in favor of config.yaml `agents:` overrides. |
| R-RF-90 | REMOVE | engineer/references/dispatch-isolation-gate.md:1-138 | .ai/runtime/lib/worktrees.py | Delete, because its "fail-closed to none" and project opt-out (20-56) contradict "no setting disables isolation" (RULES.md:288-292). |

Wording-only reference drift (skipped): domain-probes.md:3; gate-prompts.md:50, 81; scout-codebase.md:4; research-philosophy.md:1-5; thinking-models-*.md:5 (provenance line); debugger-*.md:3 ("Loaded by gsd-debugger") and "CLAUDE.md gauntlet" headings; debugger-techniques.md:253-258; planner-reviews.md:7, 44, 48, 55, 75, 83; verifier-wiring-patterns.md:3-5, 43; failing-direction.md:1-13, 54-72; verify-command-path-resolvability.md:1-3; worktree-path-safety.md:1-123 (header and comment prose, `gsd_pin_fail` to `pin_fail`, sentinel name), 139-147; checkpoints.md "Claude" to "the agent" lines; few-shot-examples/verifier.md (example paths); planner-chunked.md:1, 7, 9, 49 (heading levels).

Done when:
- `grep -rn "Local method: apply within" engineer/references` returns nothing, and `test -s engineer/references/REFERENCE.md` passes.
- `grep -nE "auto-approves|Auto-mode bypasses verification" engineer/references/checkpoints.md` returns nothing, while `grep -n "auto_select" engineer/references/checkpoints.md` returns at least 3 hits.
- `grep -rn "gsd_run\|gsd-tools\|~/.claude/gsd-core" engineer/references` returns nothing.
- `grep -n "PASSED (override)\|80% token overlap" engineer/references/verification-overrides.md` returns nothing.
- `grep -n "RED_EVIDENCE_OK" engineer/references/tdd.md engineer/references/execute-mvp-tdd.md` returns hits, and `grep -n "letter suffix" engineer/references/tdd.md` returns a hit.
- `grep -n "baseline at HEAD" engineer/references/planner-verify-command-grounding.md`, `grep -n "outside_root" engineer/references/verify-command-path-resolvability.md`, `grep -n "## Already settled" engineer/references/planner-reversibility.md` and `grep -n "T-{phase}-NN" engineer/references/planner-gap-closure.md` all return hits.
- `grep -n "REVERSIBILITY_GATES\|MemPalace\|ctx7\|npm i -g\|status: diagnosed" -r engineer/references` returns nothing.
- `grep -n "Never.*read agent definition" engineer/references/universal-anti-patterns.md engineer/references/context-budget.md` returns nothing.
- `ls engineer/references/{git-integration,agent-contracts,revision-loop,artifact-types,model-profiles,dispatch-isolation-gate}.md` fails, once batch B is done.

### References (local-only → new)

| ID | Action | GSD target (path:lines) | Local source (path:lines) | Instruction |
|---|---|---|---|---|
| R-RF-91 | NEW FILE | engineer/references/git-workflow.md | .ai/references/git-workflow.md:1-316 | Create from local, rewriting `phase_run` to `engineer_run` and leaving `../templates/issue.md` and `pull-request.md` links as they are (they resolve under engineer/). |
| R-RF-92 | NEW FILE | engineer/references/worker-handoff.md | .ai/references/worker-handoff.md:1-190 | Create from local, rewriting `phase_run`, `../commands/{progress,next,install}.md` to `../../commands/`, and `../hooks/context-handoff.sh` to the hooks location. |
| R-RF-93 | NEW FILE | engineer/references/bounded-correction-dispatch.md | .ai/references/bounded-correction-dispatch.md:1-50 | Create from local, rewriting `.ai/agents/targeted-fixer.md` (lines 3, 33) to `agents/targeted-fixer.md` and keep `../workflows/execute-phase.md`, which already resolves to engineer/workflows/execute-phase.md. |
| R-RF-94 | NEW FILE | engineer/references/phase-artifacts.md | .ai/references/phase-artifacts.md:1-35 | Create from local, pointing line 25 at `{runtime-contract}` and line 5 at `../templates/README.md`. |
| R-RF-95 | NEW FILE | engineer/references/scout-dispatch.md | .ai/references/scout-dispatch.md:1-176 | Create from local, applying the `phase_run` rewrite only. |
| R-RF-96 | NEW FILE | engineer/references/verification-evidence.md | .ai/references/verification-evidence.md:1-133 | Create from local, applying the `phase_run` rewrite, and keep the `#compensating-a-failed-final-verification` anchor that AGENTS.md:23 links to. |
| R-RF-97 | NEW FILE | engineer/references/documentation.md | .ai/references/documentation.md:1-19, 21-36, 38-60 | Create from local, rewriting line 20 to "Significant architectural choice: Key Decisions entry, with an optional ADR for rationale" and line 37 to "history in Git and Key Decisions"; do not carry the ADR-as-owner wording. |
| R-RF-98 | NEW FILE | engineer/references/parallel-status.md | .ai/references/parallel-status.md:1-83 | Create from local, adding a pointer to engineer/workflows/execute-phase/steps/executor-progress-policy.md (the "never steer a working executor" companion). |
| R-RF-99 | NEW FILE | engineer/references/worktree-sessions.md | .ai/references/worktree-sessions.md:1-216 | Create from local, applying the `phase_run` rewrite and pointing `../hooks/worktree-guard.sh` at the hooks location. |
| R-RF-100 | NEW FILE | engineer/references/cleanup.md | .ai/references/cleanup.md:1-87 | Create from local, rewriting lines 5-9 to the new CLI and library and workflow paths, and add one line that distinguishes it from engineer/workflows/cleanup.md (milestone phase archival). |
| R-RF-101 | NEW FILE | engineer/references/agent-adaptation.md | .ai/references/agent-adaptation.md:1-6, 28-33, 36-158 | Create from local without lines 8-26 (authority duplicates RULES.md, and 20-22 wrongly says "agents in a wave share one checkout") and without the stale `reviewer_command` sentence at 34-35. |
| R-RF-102 | STITCH | engineer/workflows/execute-phase/steps/worktree-recovery-policy.md:11 (insert after) | .ai/references/worktree-recovery-policy.md:40-49 | Append "Cleanup needs merge evidence" (ancestor-of-HEAD only, plus the shared database/port caveat). |
| R-RF-103 | DROP-LOCAL | (none) | .ai/references/worktree-recovery-policy.md:1-39 | Do not create a reference file, because engineer step lines 5-11 already carry both rules verbatim. |
| R-RF-104 | DROP-LOCAL | (none) | .ai/references/template-adaptation.md:1-28, 42 | Do not carry the `.ai` layer table, the upstream-history pointer or the auto-merge row 42 ("coordinator automatically merges... unless the user opts out"), which contradicts ship and git-workflow:43. |
| R-RF-105 | STITCH | engineer/templates/TEMPLATE.md (section "Runtime behavior") | .ai/references/template-adaptation.md:30-41, 43-44 | Move the behavior rows (project data, PLAN, metadata, configuration, waves, source-versus-current, checkpoints, verification, completion, publication, optional artifacts, recovery) into TEMPLATE.md, and drop the Merge row. |

Done when:
- `ls engineer/references/{git-workflow,worker-handoff,bounded-correction-dispatch,phase-artifacts,scout-dispatch,verification-evidence,documentation,parallel-status,worktree-sessions,cleanup,agent-adaptation}.md` succeeds.
- `grep -rn "phase_run\|\.ai/" engineer/references/*.md` returns nothing.
- `grep -n "Cleanup needs merge evidence" engineer/workflows/execute-phase/steps/worktree-recovery-policy.md` returns a hit, and `test ! -e engineer/references/worktree-recovery-policy.md` passes.
- `grep -rn "automatically merges" engineer/ commands/ docs/` returns nothing.
- `grep -n "share one checkout\|reviewer_command" engineer/references/agent-adaptation.md` returns nothing.

### Rules and guides

| ID | Action | GSD target (path:lines) | Local source (path:lines) | Instruction |
|---|---|---|---|---|
| R-RL-01 | RENAME | engineer/RULES.md | .ai/RULES.md:1-433 | Move RULES.md to engineer/RULES.md and apply the path convention throughout (links become `../commands/`, `workflows/`, `references/`, `../agents/`, `../.planning/`). |
| R-RL-02 | REPLACE | engineer/RULES.md (Layering) | .ai/RULES.md:15-35 | Rewrite the layer diagram to `commands/` to `engineer/workflows/` to `engineer/bin/engineer_run` plus `agents/`. |
| R-RL-03 | STITCH | engineer/RULES.md (Phase authority) | .ai/RULES.md:77-119 | Carry verbatim: discussion before planning, NEVER implement without an explicit instruction, record authorization in CONTEXT, and ownership of PROJECT/REQUIREMENTS/ROADMAP/CONTEXT. |
| R-RL-04 | STITCH | engineer/RULES.md (Retiring an entry, Deciding) | .ai/RULES.md:130-182 | Carry the retirement table and the validate-before-proposing decision rules verbatim, rewriting the verb invocations to `engineer_run query`. |
| R-RL-05 | REPLACE | engineer/RULES.md (Documents and conflicts) | .ai/RULES.md:123-128 | Rewrite lines 125-127 so PROJECT.md Key Decisions owns decisions and a significant ADR only preserves linked rationale; do not carry the ADR-supersession-as-owner wording. |
| R-RL-06 | STITCH | engineer/RULES.md (Issues found while working) | .ai/RULES.md:244-271 | Carry the three-way routing (in scope means fix, out of scope means SUMMARY Deferred, needs a human means block only dependent work), "never create todos" and the delegated-discretion `state.add-decision`. |
| R-RL-07 | STITCH | engineer/RULES.md (Worktrees, integration and cleanup) | .ai/RULES.md:273-333 | Carry the mandatory isolation (only two dispatch-isolation values), the advisory guard hook, merge-wave deletion guard and merge-evidence cleanup, with `.ai/hooks/worktree-guard.sh` pointing at the hooks location. |
| R-RL-08 | STITCH | engineer/RULES.md (Complete template use) | .ai/RULES.md:420-433 | Carry the full-template rule, pointing line 427 at engineer/templates/TEMPLATE.md and lines 432-433 at "`.planning/` for records; `engineer/` for reusable rules, workflows, templates and tooling". |
| R-RL-09 | STITCH | engineer/RULES.md (Session, Orchestration, Review, Interruption, Hooks, Modular rules) | .ai/RULES.md:37-75, 184-242, 335-418 | Carry these sections verbatim apart from the path rewrites; the agent-name list at 201-203 waits on the agents section. |
| R-RL-10 | RENAME | engineer/truth-map.md | .ai/truth-map.md:1-44 | Move truth-map.md to engineer/truth-map.md with the path convention (rows 29-38: RULES, agents, commands, workflows, references, install, config, runtime). |
| R-RL-11 | REPLACE | engineer/truth-map.md:22 | .ai/truth-map.md:22 | Change the "Significant rationale" row so its owner is PROJECT.md Key Decisions and `.planning/decisions/ADR-*.md` is optional linked rationale. |
| R-RL-12 | RENAME | docs/PHASE-WORKFLOW.md | .ai/guides/PHASE-WORKFLOW.md:1-169 | Move it into docs/ and apply the path convention. |
| R-RL-13 | RENAME | docs/REQUESTS.md | .ai/guides/REQUESTS.md:1-113 | Move it into docs/ and apply the path convention. |
| R-RL-14 | RENAME | docs/WORKFLOW-FEATURES.md | .ai/guides/WORKFLOW-FEATURES.md:1-146 | Move it into docs/ and apply the path convention. |
| R-RL-15 | RENAME | docs/ARTIFACT-GUIDE.md | .ai/guides/ARTIFACT-GUIDE.md:1-14, 37-132 | Move it into docs/, replacing sections 15-36 and 133-173 (now in TEMPLATE.md, R-TP-51) with a link, and fix rows 115-120 so the ADR template is optional rationale under Key Decisions. |
| R-RL-16 | RENAME | engineer/rules/README.md | .ai/rules/README.md:1-26 | Move it with the installed layout (alongside agents and templates), relinking line 8 to `../references/git-workflow.md` and line 10 to `../templates/rule.md`. |
| R-RL-17 | STITCH | AGENTS.md:7-11, 17, 20, 23, 30, 52, 61, 79-80, 85, 92, 102, 113, 116, 119, 121-122 | .ai/RULES.md, .ai/truth-map.md, .ai/references/* (new paths) | Repoint every `.ai/` link to engineer/RULES.md, engineer/truth-map.md, agents/, commands/, engineer/references/ and the runtime docs, and rewrite `python .ai/runtime/phase.py query` and `phase_run query` to `engineer_run query`. |
| R-RL-18 | STITCH | README.md:16, 19-22, 27-31 | .ai/guides/*.md | Repoint the guide links to docs/, and rewrite the layer diagram as in R-RL-02. |
| R-RL-19 | DROP-LOCAL | (none) | .ai/references/universal-anti-patterns.md:10-12 | Do not carry "Never read agent definition files" (it conflicts with RULES.md:45 "read ... your role"); R-RF-78 replaces it. |
| R-RL-20 | DROP-LOCAL | (none) | .ai/references/template-adaptation.md:42 | Do not carry the auto-merge row (also listed as R-RF-104 for traceability). |
| R-RL-21 | DROP-LOCAL | (none) | .ai/templates/README.md:25 | Do not carry "These 28 artifact templates", a stale count. |
| R-RL-22 | DROP-LOCAL | (none) | .ai/RULES.md:125-127; .ai/truth-map.md:22; .ai/references/documentation.md:20, 37 | Do not carry ADR-as-decision-owner wording; R-RL-05, R-RL-11 and R-RF-97 supply the corrected lines. |
| R-RL-23 | DROP-LOCAL | (none) | .ai/THIRD-PARTY-NOTICES.md:3, 6, 27-28, 69, 132, 145-146 | Do not carry the `4713ffba`, `c0b2a05` or `b956bb7` pins; they describe the retired `.ai/` copies. |
| R-RL-24 | NEW FILE | THIRD-PARTY-NOTICES.md (repo root) | .ai/THIRD-PARTY-NOTICES.md:1-173; .ai/templates/state.md:225-242 (footer intent) | Create one notice that pins the downloaded `engineer/` upstream revision, states the license and summarizes the local adaptations (no auto-approve, no waivers, Python runtime, closed STATE, etc.), replacing all per-file LOCAL-ADOPTION footers. |

Done when:
- `test -f engineer/RULES.md && test -f engineer/truth-map.md && test -f engineer/rules/README.md` passes.
- `ls docs/{PHASE-WORKFLOW,REQUESTS,WORKFLOW-FEATURES,ARTIFACT-GUIDE}.md` succeeds.
- `grep -n "\.ai/" AGENTS.md README.md engineer/RULES.md engineer/truth-map.md docs/*.md` returns nothing.
- `grep -nE "^## (Phase authority|Issues found while working|Worktrees, integration and cleanup|Complete template use)|^### Retiring an entry" engineer/RULES.md` returns 5 lines.
- `grep -n "ADR" engineer/truth-map.md engineer/RULES.md` shows ADRs only as rationale linked from Key Decisions.
- `grep -n "c0b2a05\|4713ffba\|b956bb7" THIRD-PARTY-NOTICES.md` returns nothing, and `grep -c "LOCAL-ADOPTION" -r engineer` reports 0.

### Config

| ID | Action | GSD target (path:lines) | Local source (path:lines) | Instruction |
|---|---|---|---|---|
| R-RL-25 | NEW FILE | engineer/templates/config.yaml | .planning/config.yaml:1-158 | Create the canonical config template from all local keys (`commit_docs`, `response_language`, `context_window`, `workflow.{text_mode,auto_advance,discuss_mode,isolation}`, `worktree.root`, `handoff.*`, `codebase.staleness.*`, `agents.*`, `verification.{commands,reuse,max_parallel}`), rewriting comment lines 1, 63 and 137-138 to `engineer_run`. |
| R-RL-26 | KEEP-UPSTREAM | engineer/templates/config.yaml (verification block) | .planning/config.yaml:135-158 | Keep `verification.commands: []` with its CHANGEME comment and the commented mapping example, so the template carries no invented checks. |
| R-RL-27 | DROP-LOCAL | engineer/templates/config.json:1-55 (deleted, R-TP-53) | (none) | Do not port the upstream JSON keys (`mode`, `granularity`, `workflow.research/plan_check/verifier/nyquist_validation/security_*`, `parallelization.*`, `gates.*`, `git.*`, `planning.sub_repos`, `project_code`, `agent_skills`, `claude_md_path`) unless an engineer workflow that is being kept reads one; give each such key a documented default in config.yaml. |
| R-RL-28 | REPLACE | engineer/references/checkpoints.md:38; context-budget.md:15, 28; nyquist-compliance.md:11; universal-anti-patterns.md:11, 50; planner-load-graph-context.md:18 | .planning/config.yaml | Rewrite `.planning/config.json` to `.planning/config.yaml`, and on universal-anti-patterns eng 50 replace "returns null silently on invalid JSON" with the YAML-default wording from local universal-anti-patterns.md:81-83. |
| R-RL-29 | REPLACE | engineer/templates/README.md:23 | .planning/config.yaml | Register `config.yaml` (template `config.yaml`, produced by onboard) in place of `config.json` (same edit as R-TP-44). |

Done when:
- `test -f engineer/templates/config.yaml && test ! -e engineer/templates/config.json` passes.
- `python -c "import yaml,sys; d=yaml.safe_load(open('engineer/templates/config.yaml')); assert {'commit_docs','context_window','workflow','worktree','handoff','codebase','agents','verification'} <= d.keys()"` exits 0.
- `grep -n "phase_run\|\.ai/runtime" engineer/templates/config.yaml` returns nothing.
- `grep -rn "config\.json" engineer/references/{checkpoints,context-budget,nyquist-compliance,universal-anti-patterns,planner-load-graph-context}.md engineer/templates/README.md` returns nothing.

## 14. Reconciliation: runtime, verbs, hooks, tests

85 layout, path, hook and test rows (R-RT), 154 verb rows (V), 43 config rows (C). Phases 2 and 7.

How to read the rows:

- **GSD target lines** are in the downloaded GSD copy at `9443672` (`agents/`, `commands/`, `engineer/`). "after X:N" is an insertion point.
- **Local source lines** are in `.ai/`, `.planning/` or `AGENTS.md` at `9443672`.
- **Action:** STITCH inserts the local block; REPLACE swaps GSD lines for local lines; REMOVE deletes GSD lines; NEW FILE creates the target from the local source; RENAME moves a file; KEEP-UPSTREAM keeps newer upstream content on purpose; DROP-LOCAL leaves local content behind on purpose.
- Apply the renames in [3.2](#32-mechanical-renames) to every copied block. Section 3.3 gives the final role names.
- Process each file bottom-up. Commit with a `Rows:` trailer naming the IDs done.

### Layout mapping

Evidence base: repo at `9443672` (branch `manual-override`, clean). Source lines below were read at that HEAD.
Layout rule the rows apply: in the source tree the namespace root is the repo root; installed, it is `.claude/` or `.codex/`. Under either root the same relative layout holds: `agents/`, `commands/`, `engineer/{bin,references,templates,workflows}`, `hooks/`, `skills/`, `scripts/`, `bin/`. The runtime engine dir is `engineer/bin/` (so `lib/x.py` `parents[2]` = `engineer/`, `parents[3]` = namespace root).

| ID | Source | Target | Action | Instruction |
|---|---|---|---|---|
| R-RT-01 | `.ai/runtime/phase.py` (955 lines, `VERBS` at 801-913, `main` at 916-955) | `engineer/bin/engineer.py` | RENAME+EDIT | Move with `git mv`; set `IDENTITY = {"packageName": "engineer-runtime", "contract": "2.0"}` (line 29); change usage strings (lines 7, 919) to `engineer_run query <verb>`; add global `--pick <dotted>` (print the picked field raw) and register every NEW verb in `VERBS`. |
| R-RT-02 | `.ai/bin/phase_run` (45 lines) | `engineer/bin/engineer_run` (empty placeholder) | PORT | Fill the placeholder as a POSIX `sh` shim: resolve own real dir (keep the symlink loop, lines 11-22), exec `"$dir/engineer.py"` (replace line 25 `$namespace_dir/runtime/phase.py`); venv candidates `<ns>-venv` (installed `.claude-venv`/`.codex-venv`) then `<root>/.venv`, then `python3`/`python` (replace lines 31-37); `chmod +x` and commit mode `100755`. |
| R-RT-03 | `.ai/runtime/lib/*.py` (31 modules) | `engineer/bin/lib/` | MOVE+EDIT | `git mv` the package; fix the namespace math listed in R-RT-29..R-RT-33 so templates resolve to `engineer/templates` and agents to `<ns>/agents`. |
| R-RT-04 | `.ai/runtime/requirements.txt` | `engineer/bin/requirements.txt` | MOVE | `git mv`; keep `PyYAML` pin unchanged. |
| R-RT-05 | `.ai/runtime/README.md` (719 lines) | `engineer/bin/README.md` | MOVE+EDIT | `git mv`; rewrite every `phase.py`/`phase_run`/`.ai/runtime` reference (R-RT-36); add the NEW verbs from the Verb mapping. |
| R-RT-06 | `.ai/runtime/TEMPLATE-CONTRACT.md` (445 lines) | `engineer/references/template-contract.md` | MOVE+EDIT | `git mv`; repoint `.ai/templates/` -> `engineer/templates/`, `.ai/agents/` -> `agents/` (R-RT-37). |
| R-RT-07 | `.ai/workflows/_runtime.snippet.sh` (27 lines) | `engineer/workflows/_runtime-launcher.snippet.sh` (overwrite upstream one-liner) | PORT | Replace the upstream Node launcher with a one-line bash snippet: candidates `${ENGINEER_RUN:-}`, `$ROOT/engineer/bin/engineer_run`, `$ROOT/.claude/engineer/bin/engineer_run`, `$ROOT/.codex/engineer/bin/engineer_run`, `${CLAUDE_CONFIG_DIR:-$HOME/.claude}/engineer/bin/engineer_run`, `${CODEX_HOME:-$HOME/.codex}/engineer/bin/engineer_run`; define `engineer_run() { "$ENGINEER_RUN" "$@"; }`; check `runtime-identity` contains `engineer-runtime`; append `export PATH` to `$CLAUDE_ENV_FILE` like upstream; delete `.ai/workflows/_runtime.snippet.sh`. |
| R-RT-08 | `.ai/hooks/worktree-guard.sh` (262 lines) + `lib/agent-roles.sh` | `hooks/worktree-path-guard.py` (empty placeholder) | PORT | Port to Python (placeholder is `.py`); keep both jobs and exit 0 (see Hooks R-RT-60). |
| R-RT-09 | `.ai/hooks/worktree-location.sh` (128 lines) | `hooks/worktree-location.sh` | MOVE | `git mv`; no old-path strings inside (grep clean). |
| R-RT-10 | `.ai/hooks/context-handoff.sh` (441) + `.ai/hooks/lib/{handoff-io,json-field,agent-roles}.sh` | `hooks/context-handoff.sh`, `hooks/lib/` | MOVE+EDIT | `git mv` the script and `lib/`; edit per R-RT-62. Wrap (keep bash): it already batches its Python work and a port is not required by the Python-or-shell rule. |
| R-RT-11 | `.ai/hooks/planning-integrity.sh` (11) + `.py` (315) | `hooks/planning-integrity.sh`, `hooks/planning-integrity.py` | MOVE+EDIT | `git mv` both; fix the `sys.path` join (R-RT-46). |
| R-RT-12 | `.ai/hooks/ai-tier-notice.sh` (91) | `hooks/ai-tier-notice.sh` | MOVE+EDIT | `git mv`; repoint `.ai/RULES.md` anchors (R-RT-44). |
| R-RT-13 | `.ai/hooks/cleanup.py` (31) | `scripts/cleanup.py` | MOVE+EDIT | `git mv` (it is a standalone CLI, not a hook); change line 8 to `parents[1] / "engineer" / "bin"`. |
| R-RT-14 | `.ai/hooks/README.md` (247) | `hooks/README.md` | MOVE+EDIT | `git mv`; repoint lines in R-RT-45; document the new script table. |
| R-RT-15 | `.ai/hooks/*.test.sh` (4 files) | `tests/hooks/*.test.sh` (worktree-guard -> `tests/test_worktree_path_guard.py`) | MOVE/PORT | `git mv` ai-tier-notice, context-handoff, worktree-location tests to `tests/hooks/`; port `worktree-guard.test.sh` (168 lines) cases to unittest. |
| R-RT-16 | `.ai/install.py` (941) | `bin/install.py` (empty placeholder) | MOVE+EDIT | Fill placeholder from `.ai/install.py`; edit per R-RT-47. |
| R-RT-17 | `.ai/install_migration.py` (239) | `bin/migrate.py` (empty placeholder) | MOVE+EDIT | Fill placeholder; extend `relocate_paths` (lines 15-30) with the new mapping (`.ai/runtime` and `.<host>/runtime` -> `<ns>/engineer/bin`, `.ai/templates` -> `<ns>/engineer/templates`, `.ai/workflows` -> `<ns>/engineer/workflows`, `.ai/references` -> `<ns>/engineer/references`, `.ai/agents\|commands\|hooks` -> `<ns>/agents\|commands\|hooks`, `phase_run` -> `engineer_run`). |
| R-RT-18 | `.ai/update.py` (482) + `.ai/install_update.py` (274) | `bin/update.py` (empty placeholder) | MERGE | Merge into one module: keep the installed-updater CLI (`update.py` `main`, line 417) and expose `plan_update` (install_update.py line 113) for `bin/install.py --update`; keep the two separate inventories behind one `inventory(root, mode)`; edit per R-RT-49/R-RT-50. |
| R-RT-19 | `.ai/install-assets/` (PROJECT/REQUIREMENTS/ROADMAP/STATE.txt, agent-entry.txt, README.md, `codex-agents/*.toml` x14) | `bin/install-assets/` | MOVE+EDIT | `git mv`; regenerate `codex-agents/*.toml` for the kept agent set (`agents/*.md`), each pointing at `agents/<name>.md` (R-RT-51). |
| R-RT-20 | `.ai/templates/issue.md`, `pull-request.md`, `ADR.md` | `engineer/templates/` | COPY | Add the three runtime-read templates absent from `engineer/templates/` (`issue_format.py:15` reads `issue.md`; `planning_review.py:446` names `ADR.md`; delivery body uses `pull-request.md`). |
| R-RT-21 | `.ai/templates/{state,roadmap,project,requirements,context,summary}.md` | `engineer/templates/` (same names, upstream versions differ in every file) | RECONCILE | Keep the runtime-parsed section shapes: e.g. local `state.md` has `### Roadmap Evolution` (line 73) that `state.add-roadmap-evolution` writes and upstream `state.md` lacks; merge the local section headings into the upstream files or keep the local files. |
| R-RT-22 | `tests/*.py` (24 modules) | `tests/` | EDIT | Stay in place; repoint per Tests and CI. |
| R-RT-23 | `.github/workflows/validate.yml` | `.github/workflows/validate.yml` | EDIT | Repoint lines 27-32 (R-RT-73). |
| R-RT-24 | `.agents/skills/<name>/SKILL.md` (17 dirs, present) | `skills/<name>/SKILL.md` (placeholder `skills/SKILL/SKILL.md`) | REGENERATE | Generate one `skills/<cmd>/SKILL.md` per kept `commands/<cmd>.md` (27 kept commands); `git rm -r .agents/skills`; the 3 local-only mirrors with no kept command (`clean-planning`, `onboard`, `update-workflows`) follow the commands section's decision. |
| R-RT-25 | `.planning/config.yaml` | `.planning/config.yaml` | EDIT | Repoint comments (R-RT-53) and apply the Config keys table. |
| R-RT-26 | `.ai/runtime/__pycache__`, `.ai/hooks/` lib caches | - | DROP | Do not move caches; `__pycache__/` stays ignored. |

Done when:
- `test -x engineer/bin/engineer_run && engineer/bin/engineer_run query runtime-identity --raw | grep -q engineer-runtime`
- `test ! -e .ai/runtime && test ! -e .ai/hooks && test ! -e .ai/bin && test ! -e .ai/install.py && test ! -e .agents/skills`
- `ls engineer/bin/lib/*.py | wc -l` prints at least `31`
- after the commands section removes dropped commands: `for c in commands/*.md; do n=$(basename "$c" .md); [ "$n" = COMMAND ] || test -f "skills/$n/SKILL.md" || echo "missing $n"; done` prints nothing
- `test -f engineer/templates/issue.md && test -f engineer/templates/pull-request.md && test -f engineer/templates/ADR.md`

### Hard-coded path references

Pattern searched: `\.ai/|\.ai\b|phase_run|PHASE_RUNTIME|\.codex/runtime|\.claude/runtime|ai-phase-runtime|phase\.py`, plus `"runtime"` path joins. Every file with a hit is listed.

| ID | File | Lines (count) | What is hard-coded | Action | Instruction |
|---|---|---|---|---|---|
| R-RT-27 | `.ai/runtime/phase.py` | 7, 29, 919 (3) | `python phase.py` usage, `ai-phase-runtime` identity | EDIT | Covered by R-RT-01. |
| R-RT-28 | `.ai/runtime/lib/__init__.py` | 1 (1) | docstring "for phase.py" | EDIT | Say `engineer.py`. |
| R-RT-29 | `.ai/runtime/lib/models.py` | 16, 22, 26, 58, 61-62, 67 (6) | `NAMESPACE = parents[2]`; `SKILL_ROOTS`; `NAMESPACE / "agents"`; `NAMESPACE.name == ".ai"` source test; `install-assets/codex-agents` | EDIT | Set `NAMESPACE = Path(__file__).resolve().parents[3]`; source test becomes `NAMESPACE.name not in (".claude", ".codex")`; codex TOML root `NAMESPACE / "bin/install-assets/codex-agents"` (source) else `NAMESPACE / "agents"`; add `"skills"` to `SKILL_ROOTS`. |
| R-RT-30 | `.ai/runtime/lib/worktrees.py` | 127-133 (1) | `parents[2].name` == `.claude`/`.codex` host detection | EDIT | Use `parents[3].name`. |
| R-RT-31 | `.ai/runtime/lib/bundles.py` | 22 (1, path join) | `parents[2] / "templates"` | KEEP | Resolves to `engineer/templates` after the move; update `tests/test_phase_runtime.py:881`. |
| R-RT-32 | `.ai/runtime/lib/issue_format.py` | 14-15 (1) | `parents[2] / "templates" / "issue.md"` + comment | EDIT | Keep join (now `engineer/templates`), fix comment, add `issue.md` (R-RT-20). |
| R-RT-33 | `.ai/runtime/lib/planning_review.py` | 22-25 (1) | `TEMPLATE_NAMESPACE = parents[2]`, `.ai` comment | EDIT | Keep join; rename comment to `engineer`. |
| R-RT-34 | `.ai/runtime/lib/config.py` | 27-28 (2) | comment `.ai/hooks/context-handoff.sh`, `phase_run` | EDIT | `hooks/context-handoff.sh`, `engineer_run`. |
| R-RT-35 | `.ai/runtime/lib/handoff.py`, `lib/validate.py` | handoff 3, 134; validate 113, 181, 216 (5) | `.ai/hooks/...` comments; user-facing `.ai/templates/state.md\|requirements.md\|project.md` repair hints | EDIT | Point messages at `engineer/templates/<name>.md`. |
| R-RT-36 | `.ai/runtime/README.md` | 3, 21, 32-33, 143, 457, 467-469, 472-473, 537, 556, 716 (14) | `python .ai/runtime/phase.py`, `.codex/runtime`, `.claude/runtime`, `phase_run` | EDIT | Replace with `engineer_run query ...` / `<ns>/engineer/bin/engineer.py`. |
| R-RT-37 | `.ai/runtime/TEMPLATE-CONTRACT.md` | 20, 43, 119, 142, 153, 317, 409, 423-425, 443 (11) | `.ai/templates/*`, `.ai/agents/`, `phase_run`, `.ai/install-assets/codex-agents/` | EDIT | Repoint to `engineer/templates/`, `agents/`, `engineer_run`, `bin/install-assets/codex-agents/`. |
| R-RT-38 | `.ai/workflows/_runtime.snippet.sh` | 2, 4, 8-14, 16-17, 24-27 (15) | `PHASE_RUNTIME`, `.ai\|.claude\|.codex/runtime/phase.py`, `phase_run`, `ai-phase-runtime` | PORT | Covered by R-RT-07. |
| R-RT-39 | `.ai/bin/phase_run` | 2, 4, 9, 25, 31 (5) | name, `runtime/phase.py`, `.ai-venv` | PORT | Covered by R-RT-02. |
| R-RT-40 | 63 kept files carrying the upstream launcher one-liner, including the snippet file itself (e.g. `agents/gsd-code-fixer.md:536`, `engineer/workflows/ship.md:31`, `engineer/workflows/quick.md:42`) | 1 per file (63) | `_GSD_SHIM_NAME="gsd-tools.cjs"` ... `node "$GSD_TOOLS"` | REPLACE | Replace each one-liner byte-for-byte with the R-RT-07 snippet; then `sed -i 's/\bgsd_run\b/engineer_run/g'` on the kept files. |
| R-RT-41 | 16 kept files with other `gsd-tools` mentions (34 lines; e.g. `engineer/workflows/update.md` 10 from line 22, `agents/gsd-verifier.md` 3 from 85, `commands/quick.md` 3 from 80, `executor-isolation-dispatch.md` 3 from 53) | 34 | prose/paths naming `gsd-tools.cjs` | EDIT | Rename to `engineer_run`/`engineer/bin/engineer.py` or delete the sentence. |
| R-RT-42 | `.ai/hooks/worktree-guard.sh` | 134, 211, 219, 253 (4) | `.ai/RULES.md#...`, `phase_run query session.open`, `.ai/references/worktree-path-safety.md` | PORT | In the Python port use `engineer_run query session.open`, `engineer/references/worktree-path-safety.md`, and the RULES path chosen by the docs section. |
| R-RT-43 | `.ai/hooks/context-handoff.sh` | 419 (1) | `phase_run query handoff.write` in the advisory text | EDIT | `engineer_run query handoff.write`. |
| R-RT-44 | `.ai/hooks/ai-tier-notice.sh` (+ `.test.sh` line 7) | 3, 72-73, 76, 79, 82, 85 (7) + 1 | `.ai/RULES.md` path match and anchors | EDIT | Repoint to the RULES file location chosen by the docs section; update the test's `*'.ai/RULES.md#'*` assertion. |
| R-RT-45 | `.ai/hooks/README.md` | 90-93, 135, 230 (6) | `bash .ai/hooks/*.test.sh`, `phase_run` | EDIT | `bash tests/hooks/*.test.sh`, `python -m unittest tests.test_worktree_path_guard`, `engineer_run`. |
| R-RT-46 | `.ai/hooks/planning-integrity.py`, `.sh`; `.ai/hooks/cleanup.py` | py 11-12; sh 10; cleanup 8 (path joins) | `parent.parent / 'runtime'`, `parents[1] / "runtime"` | EDIT | Use `parent.parent / 'engineer' / 'bin'` (hooks/ and engineer/ are siblings under the namespace root in source and install); fix the error text. |
| R-RT-47 | `.ai/install.py` | 28, 39, 51, 89, 91, 106, 115, 133, 146, 177, 179-182, 640, 643, 646, 802, 813, 874-875, 901, 910, 923 (22 + joins) | `ASSETS=".ai/install-assets/"`, `.ai-venv`, source prefixes `.ai/` + `.agents/skills/`, required `.ai/runtime/phase.py`, `.ai/agents/`, `(".ai", namespace)` destination, `.ai` regex rewrite, `runpy` of `.ai/install_migration.py`/`.ai/install_update.py`, `runtime/requirements.txt`, `runtime/phase.py`, `parent.name` host detection | EDIT | `ASSETS = "bin/install-assets/"`; select prefixes `agents/ commands/ engineer/ hooks/ scripts/ skills/ bin/`; destination `.{host}/<same path>` (`skills/` -> `skill_root(host)`); required file `engineer/bin/engineer.py`; rewrite regex targets `engineer_run`/namespace-relative paths instead of `\.ai(?![\w-])` (line 181); `runpy` `bin/migrate.py` and `bin/update.py`; deps from `engineer/bin/requirements.txt`; verify with `engineer/bin/engineer.py query runtime-identity`; host default from `parents[1].name` (line 901). Hook commands at 490/535 keep `.{host}/hooks/<script>`. |
| R-RT-48 | `.ai/install_migration.py` | 1, 23-30, 111-130, 146-147 (11) | legacy `.ai` source tree and `.ai-venv` | EDIT | Keep `.ai` as the legacy input; add `.<host>/runtime` legacy input; emit the new layout (R-RT-17). |
| R-RT-49 | `.ai/install_update.py` | 6, 123-134 (7) | `runtime/phase.py` presence test, `.ai` conflict | EDIT | Test `<ns>/engineer/bin/engineer.py`; keep `.ai` as "migrate first" signal. |
| R-RT-50 | `.ai/update.py` | 63-68, 109, 226-227, 459 (8) | `.{host}/runtime/phase.py`, `.ai/runtime/lib/config.py`, `.ai/` + `.agents/skills/` prefixes, protected roots | EDIT | `.{host}/engineer/bin/engineer.py`; `engineer/bin/lib/config.py`; new prefixes as R-RT-47; protected roots add `engineer`, `hooks`, `skills`. |
| R-RT-51 | `.ai/install-assets/` | agent-entry.txt 9, 11-13, 19, 21, 40, 49, 65, 69, 76, 88, 98, 101, 104, 106-107 (17); PROJECT.txt 48-49; REQUIREMENTS.txt 24; ROADMAP.txt 16; STATE.txt 64-65; README.md 26; `codex-agents/*.toml` line 5 (scout 6, targeted-fixer 7) x14 | `.ai/RULES.md`, `.ai/agents\|commands\|references`, `python .ai/runtime/phase.py`, `phase_run` | EDIT | Repoint to the new layout; regenerate the TOMLs (R-RT-19). |
| R-RT-52 | `.github/workflows/validate.yml` | 27, 29-32 (5) | `.ai/runtime/requirements.txt`, `bash .ai/hooks/*.test.sh` | EDIT | See R-RT-73. |
| R-RT-53 | `.planning/config.yaml` | 1, 63, 137-138 (4) | "read by .ai/runtime/phase.py", `phase_run query codebase.status`, `.ai/runtime/README.md`, `phase_run query verification.run-checks` | EDIT | `engineer/bin/engineer.py`, `engineer_run`, `engineer/bin/README.md`. |
| R-RT-54 | `tests/*.py` | 23 of 24 modules (see R-RT-66..R-RT-72) | `.ai/...` paths | EDIT | See Tests and CI. |

Done when:
- `grep -rnE '\.ai/|phase_run|PHASE_RUNTIME|\.codex/runtime|\.claude/runtime|ai-phase-runtime|phase\.py' engineer bin hooks scripts skills .github .planning/config.yaml` returns nothing
- `grep -rn 'gsd_run\|gsd-tools\|_GSD_SHIM_NAME' agents commands engineer` returns nothing
- `grep -rnE "/ ['\"]runtime['\"]" hooks scripts engineer/bin` returns nothing

### Verb mapping

145 upstream keys from `verbs.json` remain after dropping prose noise (`is on`, `launcher preamble`, `resolver of`, `shell function`, bare `query`, `verify-summary`) and folding the prose `audit-open` (complete-milestone.md:70) into `query audit-open`. Counts and examples are from `verbs.json`; sampled lines were re-read at HEAD. Rewrite every call to `engineer_run query <verb>`: non-`query` families become dotted names (`check evaluation-scope` -> `query check.evaluation-scope`, `quick-batch create` -> `query quick-batch.create`, `phase uat-passed` -> `query phase.uat-passed`).

| ID | Upstream verb | Uses (count: 2 examples) | Local verb | Action | Instruction |
|---|---|---|---|---|---|
| V-01 | `check` | 6: `engineer/workflows/execute-phase/steps/verify-phase-goal.md:95`, `engineer/workflows/plan-phase.md:1487` | - | DROP | Remove the generic `check ${hook.check.query}` gate dispatch; it only consumes `loop render-hooks` gate entries (loop hooks dropped). Replace each call with the direct gate named in V for `loop render-hooks`. |
| V-02 | `check evaluation-scope` | 7: `agents/gsd-code-reviewer.md:139`, `engineer/workflows/code-review.md:286` | `check.evaluation-scope` | NEW | Implement in `engineer/bin/lib/scope.py`: from `git log` on the current branch (optionally `--ref`, `--since`, `--committed-since`, `--max-commits`, `--pathspec`, `--milestone-bound`), return commits and changed files whose subject carries `(<phase>-<plan>)` or the phase scope; `--commits-only --raw` prints one SHA per line. Rewrite calls to `engineer_run query check.evaluation-scope ...`. |
| V-03 | `check predicate` | 4: `engineer/workflows/execute-phase/steps/verify-phase-goal.md:92`, `engineer/workflows/plan-phase.md:1491` | - | DROP | Remove `check predicate` gate evaluation together with the loop-hook gate block it sits in (plan-phase, ship, verify-work, verify-phase-goal). |
| V-04 | `check tdd-red-evidence` | 2: `engineer/references/execute-mvp-tdd.md:21`, `engineer/references/tdd.md:104` | `check.tdd-red-evidence` | NEW | Implement in `engineer/bin/lib/tdd.py`: read the RED record JSON, require a failing test run whose failure reason is not a collection/import error and whose test files precede the implementation commit; print `RED_EVIDENCE_OK` or `INVALID_RED:<reason>`; exit 69 when the record is unreadable. |
| V-05 | `check ui-plan-gate` | 1: `engineer/workflows/plan-phase.md:534` | `check.ui-plan-gate` | NEW | Implement in `engineer/bin/lib/ui.py`: for a phase whose ROADMAP/CONTEXT marks UI work, exit 1 with `{blocked:true, reason}` unless `<NN>-UI-SPEC.md` exists and is approved; exit 0 `{blocked:false}` otherwise. |
| V-06 | `check verify-command-paths` | 3: `engineer/workflows/plan-phase.md:1031`, `engineer/workflows/quick/steps/plan-checker-loop.md:20` | `check.verify-command-paths` | NEW | Implement in `engineer/bin/lib/plans.py`: parse every `<verify>` command in the phase's (or `--dir`) PLAN files, report referenced paths that neither exist nor are created by an earlier task's `files`; exit 1 when any are unresolvable. |
| V-07 | `check verify-failure-directions` | 2: `engineer/workflows/plan-phase.md:1032`, `engineer/references/failing-direction.md:37` | `check.verify-failure-directions` | NEW | Implement in `engineer/bin/lib/plans.py`: flag `<verify>` commands that cannot fail (e.g. `\|\| true`, `echo`, grep without `-q` check inversion); return per-task findings; exit 1 on any finding. |
| V-08 | `detect-custom-files` | 1: `engineer/workflows/update.md:312` | - | DROP | Delete the `detect-custom-files` path in `engineer/workflows/update.md`; `bin/update.py` already preserves user-modified files through its ownership manifest. |
| V-09 | `graphify query` | 2: `agents/gsd-phase-researcher.md:589`, `engineer/references/planner-load-graph-context.md:27` | - | DROP | Delete the graphify query block (graphify feature dropped) from `agents/gsd-phase-researcher.md` and `engineer/references/planner-load-graph-context.md`; drop that reference from every `read_first`/`@` include. |
| V-10 | `graphify status` | 2: `agents/gsd-phase-researcher.md:574`, `engineer/references/planner-load-graph-context.md:11` | - | DROP | Delete with `graphify query` (same files). |
| V-11 | `init phase-op` | 1: `engineer/workflows/spec-phase.md:60` | `init.phase-op` | MAP | Rewrite to `engineer_run query init.phase-op "${PHASE}"` (engineer.py keeps the `init` family alias, but use one form). |
| V-12 | `intel api-surface` | 1: `engineer/workflows/plan-phase.md:726` | - | DROP | Delete the intel `plan:pre` step (intel feature not kept; gated by `intel.enabled`) from `engineer/workflows/plan-phase.md`. |
| V-13 | `loop render-hooks` | 25: `engineer/workflows/code-review-fix.md:92`, `engineer/workflows/code-review.md:813` | - | DROP | Delete every `loop render-hooks` call and its JSON-dispatch block (capability registry dropped; no `capability.json` exists in the tree). Replace by point: `execute:post` -> `TDD_MODE=$(engineer_run query config-get workflow.tdd_mode --default false --raw)` and a direct `/code-review` step gated on `workflow.code_review`; `verify:post` -> direct secure-phase gate (`workflow.security_enforcement`) and validate-phase gate (`workflow.nyquist_validation`); `plan:pre` -> direct UI gate (`workflow.ui_phase` + `check.ui-plan-gate`) and TDD planner flag; `discuss:*`, `execute:wave:*`, `ship:*`, `plan:post`, `verify:pre` -> delete. |
| V-14 | `phase uat-passed` | 2: `engineer/workflows/verify-work.md:661`, `engineer/workflows/verify-work.md:715` | `phase.uat-passed` | NEW | Implement in `engineer/bin/lib/uat.py`: exit 0 when the phase's `*-UAT.md` has no pending/failed items (`--uat-only`), and with `--require-verification` also when `verification.status` is `passed`; exit 1 with the blocking items otherwise. |
| V-15 | `query agent-skills` | 32: `engineer/workflows/code-review-fix.md:31`, `engineer/workflows/code-review-fix.md:32` | `agent-skills` | MAP | Rewrite to `engineer_run query agent-skills <agent> --raw`; delete `${GSD_WS:+--ws=...}`; make `--raw` print the ready-to-inject `<agent_skills>` block; resolve names against repo-root `agents/`. |
| V-16 | `query agent.classify-failure` | 2: `engineer/workflows/execute-phase.md:1083`, `engineer/workflows/execute-phase.md:1446` | `agent.classify-failure` | NEW | Implement in `engineer/bin/lib/models.py`: classify an agent return body (after `--`) into `quota\|rate_limit\|context_exhausted\|crash\|unknown` by sentinel regex (`usage limit`, `429`, `RESOURCE_EXHAUSTED`, ...) with `retryable` and `wait_hint`. |
| V-17 | `query audit-open` | 3: `engineer/workflows/complete-milestone.md:48`, `engineer/workflows/verify-work.md:757` | `audit-open` | NEW | Implement in `engineer/bin/lib/audit.py`: list open items across the milestone (UAT pending/failed, verification `gaps_found`/`human_needed`, open STATE blockers, pending todos) as JSON with counts; `--json` is the default output. Also covers the prose `audit-open` key (complete-milestone.md:70). |
| V-18 | `query audit-uat` | 3: `engineer/workflows/audit-fix.md:38`, `engineer/workflows/audit-uat.md:14` | `audit-uat` | NEW | Implement in `engineer/bin/lib/uat.py`: scan every phase `*-UAT.md` and `*-VERIFICATION.md` human items; return outstanding items with phase, test id, status and file; `--raw` prints JSON. |
| V-19 | `query check` | 2: `engineer/workflows/execute-phase.md:1110`, `engineer/workflows/plan-phase.md:557` | `config-get workflow.auto_advance` | MAP | Replace `query check auto-mode --pick active\|auto_chain_active` with `engineer_run query config-get workflow.auto_advance --default false --raw`. |
| V-20 | `query check.decision-coverage-plan` | 1: `engineer/workflows/plan-phase.md:1371` | `check.decision-coverage-plan` | NEW | Implement in `engineer/bin/lib/decisions.py`: every `D-NN` decision in CONTEXT.md must be cited by at least one PLAN in the phase dir; exit 1 with uncovered IDs. |
| V-21 | `query check.decision-coverage-verify` | 1: `engineer/references/verifier-phase-gates.md:37` | `check.decision-coverage-verify` | NEW | Implement in `engineer/bin/lib/decisions.py`: every `D-NN` decision must appear in VERIFICATION.md evidence; exit 1 with uncovered IDs. |
| V-22 | `query classify-confidence` | 3: `agents/gsd-phase-researcher.md:174`, `agents/gsd-phase-researcher.md:176` | - | DROP | Delete the classify-confidence calls (research provider cache dropped); state the static tiers in prose: official docs/Context7 = HIGH, cited web = MEDIUM, unverified = LOW. |
| V-23 | `query commit` | 49: `agents/gsd-code-fixer.md:534`, `agents/gsd-code-fixer.md:537` | `commit` | MAP | Rewrite to `engineer_run query commit "<msg>" --files ...`; add `--files-removed` (stage deletions) to `lib/gitops.py`; replace the 2 `--amend` uses with a new commit. |
| V-24 | `query config-get` | 64: `agents/gsd-code-fixer.md:671`, `commands/discuss-phase.md:55` | `config-get` | MAP | Rewrite to `engineer_run query config-get <key>`; extend `verb_config_get` to honour `--default <v>` and to exit 1 with code `key-not-found` when the key is absent and no default is given (shell `\|\| echo` fallbacks depend on it). Keys: see Config keys. |
| V-25 | `query config-new-project` | 1: `engineer/workflows/new-project.md:625` | `config-new-project` | NEW | Implement in `engineer/bin/lib/config.py`: take the JSON choices, map them onto local keys (Config keys table), merge over `DEFAULTS`, write `.planning/config.yaml` (YAML, comments from template) only when absent. |
| V-26 | `query config-set` | 5: `engineer/workflows/discuss-phase/modes/text.md:23`, `engineer/workflows/execute-phase.md:198` | `config-set` | MAP | Rewrite to `engineer_run query config-set <key> <value>`; delete the `workflow._auto_chain_active`, `workflow.context_drift_action` and `workflow.plan_review_convergence` writes (Config keys). |
| V-27 | `query detect-custom-files` | 1: `engineer/workflows/update.md:311` | - | DROP | Same as `detect-custom-files`. |
| V-28 | `query dispatch-capacity` | 1: `engineer/workflows/quick-batch.md:107` | `dispatch-capacity` | NEW | Implement in `engineer/bin/lib/quick_batch.py`: return `quick_batch.capacity` (default 3) clamped to >=1; `--raw` prints the integer. |
| V-29 | `query dispatch-isolation` | 9: `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:33`, `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:53` | `dispatch-isolation` | MAP | Rewrite to `engineer_run query dispatch-isolation [--phase N] [--plan P] [--raw]`; delete every `--force-isolation` call (isolation is mandatory locally); treat `--json` as the default JSON output. |
| V-30 | `query estimate-check` | 1: `agents/gsd-plan-checker.md:754` | - | DROP | Delete the advisory smart-zone estimate loop in `agents/gsd-plan-checker.md` (already `\|\| true`). |
| V-31 | `query find-phase` | 8: `engineer/workflows/execute-phase/steps/gap-closure-artifacts.md:19`, `engineer/workflows/next.md:100` | `find-phase` | MAP | Rewrite to `engineer_run query find-phase <N>`; add `plan_count_all` and `artifacts` fields to `phases.find` output. |
| V-32 | `query frontmatter.get` | 3: `agents/gsd-plan-checker.md:791`, `agents/gsd-plan-checker.md:882` | `frontmatter.get` | NEW | Implement in `engineer/bin/lib/frontmatter.py` on `text.split_frontmatter`: print one field (`--raw` scalar, JSON for mappings/lists). |
| V-33 | `query frontmatter.set` | 1: `engineer/workflows/verify-work.md:665` | `frontmatter.set` | NEW | Implement in `engineer/bin/lib/frontmatter.py`: set `--field` to `--value` preserving key order and body; refuse files outside the repo. |
| V-34 | `query frontmatter.validate` | 1: `agents/gsd-planner.md:851` | `frontmatter.validate` | NEW | Implement in `engineer/bin/lib/frontmatter.py`: validate against `--schema plan\|summary\|verification` required keys/types; JSON `{valid, errors[]}`; exit 1 when invalid. |
| V-35 | `query generate-claude-md` | 1: `engineer/workflows/new-project.md:1113` | `generate-claude-md` | NEW | Implement in `engineer/bin/lib/project_record.py`: render the host instruction file (`--output`) from PROJECT.md + `bin/install-assets/agent-entry.txt`, replacing only the managed block. |
| V-36 | `query generate-slug` | 3: `engineer/workflows/add-todo.md:125`, `engineer/workflows/quick-batch/steps/research-phase.md:23` | `generate-slug` | MAP | Rewrite to `engineer_run query generate-slug "$text" --raw`. |
| V-37 | `query git.base-branch` | 6: `engineer/workflows/complete-milestone.md:527`, `engineer/workflows/execute-phase.md:313` | `git.base-branch` | MAP | Rewrite to `engineer_run query git.base-branch [--is-protected <branch>] --raw` (existing option). |
| V-38 | `query history-digest` | 1: `agents/gsd-planner.md:651` | `init.plan-phase .prior_context` | MAP | Replace with the `prior_context` field of `engineer_run query init.plan-phase <N>` (local `bundles.prior_context`). |
| V-39 | `query init.code-review` | 1: `engineer/workflows/code-review.md:67` | `init.code-review` | NEW | Add bundle in `engineer/bin/lib/bundles.py`: phase dir/number, padded phase, review/fixer models+efforts, `workflow.code_review*` config, last REVIEW.md commit, `--fix` flag echo. |
| V-40 | `query init.complete-milestone` | 5: `engineer/workflows/complete-milestone.md:255`, `engineer/workflows/complete-milestone.md:340` | `init.complete-milestone` | MAP | Rewrite call; delete `--ws`; verify consumed fields exist in `bundles.complete_milestone`. |
| V-41 | `query init.execute-phase` | 3: `engineer/workflows/execute-phase.md:97`, `engineer/workflows/execute-phase/steps/verify-phase-goal.md:15` | `init.execute-phase` | MAP | Rewrite call; delete `--ws`/`$WAVE_PARAM` passthrough unless added; verify consumed `jq` fields exist in `bundles.execute_phase`. |
| V-42 | `query init.manager` | 1: `engineer/workflows/complete-milestone.md:85` | `init.complete-milestone` | MAP | Replace with `init.complete-milestone`; add `all_phases_verified` and `progress_percent` to that bundle. |
| V-43 | `query init.new-milestone` | 6: `engineer/workflows/new-milestone.md:59`, `engineer/workflows/new-milestone.md:276` | `init.new-milestone` | MAP | Rewrite all 6 calls; delete `--ws` and `$RESET_PHASE_NUMBERS_PARAM` unless implemented. |
| V-44 | `query init.new-project` | 2: `engineer/workflows/new-project.md:39`, `engineer/workflows/new-project.md:654` | `init.onboard` | MAP | Register `init.new-project` as an alias of `bundles.onboard` and add the fields new-project.md reads (`project_exists`, `has_codebase_map`, `is_brownfield`, models). |
| V-45 | `query init.phase-op` | 13: `agents/gsd-phase-researcher.md:540`, `agents/gsd-plan-checker.md:732` | `init.phase-op` | MAP | Rewrite all 13 calls; delete `--ws`; keep `@file:` unwrap lines harmless or delete them. |
| V-46 | `query init.plan-phase` | 4: `agents/gsd-planner.md:574`, `engineer/workflows/plan-phase.md:93` | `init.plan-phase` | MAP | Rewrite; delete `--ws` and unsupported `$GRAN_PARAM $PRD_PARAM $INGEST_PARAM $RESEARCH_PHASE_PARAM $REVIEWS_PARAM $CHUNKED_PARAM` or accept them as ignored flags; add `phase_req_ids` for `--pick`. |
| V-47 | `query init.progress` | 2: `engineer/workflows/milestone-summary.md:68`, `engineer/workflows/progress.md:24` | `init.progress` | MAP | Rewrite; delete `--ws` and `$FORENSIC_PARAM`. |
| V-48 | `query init.quick` | 1: `engineer/workflows/quick.md:129` | `init.quick` | MAP | Rewrite; accept description + `--discuss/--research/--validate/--full` flags in `bundles.quick_bundle`. |
| V-49 | `query init.quick-batch` | 1: `engineer/workflows/quick-batch.md:68` | `init.quick-batch` | NEW | Add bundle in `engineer/bin/lib/bundles.py`/`quick_batch.py`: quick root, open batches, models/efforts for planner/executor/verifier, capacity, isolation mode. |
| V-50 | `query init.todos` | 4: `engineer/workflows/add-todo.md:21`, `engineer/workflows/add-todo.md:153` | `init.todos` | MAP | Rewrite 4 calls; delete `--ws`. |
| V-51 | `query init.verify-work` | 1: `engineer/workflows/verify-work.md:51` | `init.verify-work` | MAP | Rewrite; delete `--ws`. |
| V-52 | `query learnings.copy` | 1: `engineer/workflows/execute-phase.md:1380` | - | DROP | Delete the global-learnings copy step in `engineer/workflows/execute-phase.md` (learnings dropped; gated by `features.global_learnings`). |
| V-53 | `query learnings.query` | 1: `agents/gsd-planner.md:697` | - | DROP | Delete the learnings lookup paragraph in `agents/gsd-planner.md`. |
| V-54 | `query milestone` | 1: `engineer/workflows/complete-milestone.md:311` | `milestone.complete` | MAP | Rewrite `query milestone complete v[X.Y] --no-archive-phases --confirm` to `engineer_run query milestone.complete v[X.Y] --confirm --no-archive-phases`; add `--no-archive-phases` to `lib/milestones.py`. |
| V-55 | `query milestone.archive-quick` | 1: `engineer/workflows/cleanup.md:198` | `planning.archive` | MAP | Replace with the local `planning.archive` quick-task scope; confirm argument shape before rewriting cleanup.md:198. |
| V-56 | `query milestone.complete` | 3: `engineer/workflows/complete-milestone.md:241`, `engineer/workflows/complete-milestone.md:278` | `milestone.complete` | MAP | Rewrite to `engineer_run query milestone.complete "v[X.Y]" --name ... --confirm`; drop `$ARCHIVE_QUICK_FLAG`. |
| V-57 | `query normalize-test-command` | 3: `engineer/workflows/audit-fix.md:145`, `engineer/workflows/execute-phase/steps/post-merge-gate.md:145` | `verification.run-checks` | DROP | Delete; regression/post-merge/audit-fix gates call `engineer_run query verification.run-checks` (configured `verification.commands`). |
| V-58 | `query package-legitimacy` | 1: `agents/gsd-phase-researcher.md:217` | `package-legitimacy` | NEW | Implement in `engineer/bin/lib/packages.py` with `urllib`: query npm/PyPI/crates registries per package; verdict `OK\|SUS\|MISSING` from existence, age, release count and typo-distance to popular names; offline -> `UNKNOWN`, never crash. |
| V-59 | `query phase-plan-index` | 2: `engineer/workflows/execute-phase.md:359`, `engineer/workflows/execute-phase/steps/partial-wave.md:6` | `phase-plan-index` | MAP | Rewrite both calls. |
| V-60 | `query phase.add` | 3: `engineer/workflows/add-phase.md:53`, `engineer/workflows/add-phase.md:56` | `phase.add` | MAP | Rewrite to `engineer_run query phase.add "${description}"`. |
| V-61 | `query phase.complete` | 1: `engineer/workflows/execute-phase.md:1326` | `phase.complete` | MAP | Rewrite. |
| V-62 | `query phase.insert` | 3: `engineer/workflows/insert-phase.md:57`, `engineer/workflows/insert-phase.md:60` | `phase.insert` | MAP | Rewrite to `engineer_run query phase.insert <after> "<description>"`. |
| V-63 | `query phase.list-artifacts` | 2: `agents/gsd-plan-checker.md:746`, `agents/gsd-plan-checker.md:748` | `find-phase` | MAP | Replace with `engineer_run query find-phase <N>` and read `artifacts` (filter research/summary). |
| V-64 | `query phase.list-plans` | 1: `agents/gsd-plan-checker.md:744` | `phase-plan-index` | MAP | Replace with `engineer_run query phase-plan-index <N>`. |
| V-65 | `query phase.mvp-mode` | 3: `engineer/workflows/execute-phase.md:211`, `engineer/workflows/plan-phase.md:235` | `phase.mvp-mode` | NEW | Implement in `engineer/bin/lib/phases.py`: `active` = explicit `--mvp` flag OR ROADMAP phase `mode: mvp` OR `workflow.mvp_mode`; return `{active, source}`. |
| V-66 | `query phase.remove` | 5: `engineer/workflows/remove-phase.md:88`, `engineer/workflows/remove-phase.md:91` | `phase.remove` | MAP | Rewrite (`--force` already supported). |
| V-67 | `query phase.tdd-applicable` | 4: `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:182`, `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:185` | `phase.tdd-applicable` | NEW | Implement in `engineer/bin/lib/tdd.py`: `applicable` = plan frontmatter `type: tdd` or any task `tdd="true"`, AND `workflow.tdd_mode`; exit 1 only on unreadable plan. |
| V-68 | `query phases.clear` | 2: `engineer/workflows/new-milestone.md:258`, `engineer/workflows/new-milestone.md:260` | `planning.archive` | MAP | Replace with `engineer_run query planning.archive` for the outgoing milestone; delete the unarchived `--confirm` clear path. |
| V-69 | `query phases.list` | 1: `engineer/workflows/plan-phase.md:181` | `phases.list` | MAP | Rewrite; add `--type summaries\|plans` filtering with a `count` field. |
| V-70 | `query plan.task-structure` | 2: `agents/gsd-plan-checker.md:851`, `agents/gsd-plan-checker.md:881` | `plan.task-structure` | NEW | Implement in `engineer/bin/lib/plans.py`: parse `<task>` blocks into `{name,type,tdd,files,read_first,action,verify,done}`. |
| V-71 | `query progress` | 1: `engineer/workflows/progress.md:126` | `init.progress` | MAP | Replace prose reference with `init.progress`. |
| V-72 | `query progress.bar` | 1: `engineer/workflows/progress.md:130` | `progress.bar` | MAP | Make the percent positional optional (default: `roadmap.analyze.percent`). |
| V-73 | `query project-instruction-file` | 2: `engineer/workflows/new-project.md:94`, `engineer/workflows/new-project.md:96` | `project-instruction-file` | NEW | Implement in `engineer/bin/lib/models.py`: `claude` -> `CLAUDE.md`, `codex` -> `AGENTS.md`; default from `models.resolve_host()`. |
| V-74 | `query research-plan` | 2: `agents/gsd-phase-researcher.md:122`, `agents/gsd-phase-researcher.md:731` | - | DROP | Delete tool-strategy Steps B-D (research cache dropped); researchers call WebSearch/WebFetch/MCP tools directly. |
| V-75 | `query research-store` | 1: `agents/gsd-phase-researcher.md:157` | - | DROP | Delete with `research-plan`. |
| V-76 | `query resolve-agent` | 2: `engineer/workflows/execute-phase/steps/per-plan-executor-routing.md:31`, `engineer/workflows/execute-phase/steps/per-plan-executor-routing.md:43` | `resolve-agent` | MAP | Rewrite `--name "$PLAN_HINT"` to the positional form; add `--raw` printing the agent name, falling back to `executor`. |
| V-77 | `query resolve-dispatch-type` | 10: `engineer/workflows/audit-fix.md:101`, `engineer/workflows/code-review-fix.md:210` | - | DROP | Delete the "Runtime-aware dispatch (#2508)" blockquote in all 10 files (kimi-code built-in runtimes unsupported). |
| V-78 | `query resolve-model` | 10: `engineer/workflows/audit-fix.md:104`, `engineer/workflows/code-review-fix.md:35` | `resolve-model` | MAP | Rewrite; rename `gsd-executor` -> `executor`; add `engineer_run query resolve-effort <agent>` beside each call per AGENTS.md dispatch rule. |
| V-79 | `query resolve-package-manager` | 4: `engineer/workflows/audit-fix.md:131`, `engineer/workflows/execute-phase/steps/post-merge-gate.md:59` | `verification.run-checks` | DROP | Delete; use `verification.run-checks`. |
| V-80 | `query roadmap` | 5: `engineer/workflows/edit-phase.md:61`, `engineer/workflows/edit-phase.md:89` | `roadmap.get-phase / roadmap.analyze / phase.edit` | MAP | In `engineer/workflows/edit-phase.md` rewrite `roadmap get-phase` -> `roadmap.get-phase`, `roadmap analyze` -> `roadmap.analyze`, and replace the hand-written ROADMAP edit plus `roadmap milestone-scope` check with `engineer_run query phase.edit <N> --name/--goal/--depends-on/--requirements`. |
| V-81 | `query roadmap.analyze` | 7: `agents/gsd-verifier.md:589`, `engineer/workflows/execute-phase.md:382` | `roadmap.analyze` | MAP | Rewrite all 7 calls. |
| V-82 | `query roadmap.annotate-dependencies` | 1: `engineer/workflows/plan-phase.md:1441` | - | DROP | Delete the step (optional ROADMAP wave annotation); `roadmap.set-plans` already registers plans. |
| V-83 | `query roadmap.get-phase` | 11: `agents/gsd-plan-checker.md:747`, `agents/gsd-verifier.md:115` | `roadmap.get-phase` | MAP | Rewrite all 11; delete `--ws`; `--pick goal` needs the global `--pick`. |
| V-84 | `query roadmap.update-plan-progress` | 1: `engineer/workflows/execute-phase.md:975` | `roadmap.update-plan-progress` | MAP | Rewrite to `engineer_run query roadmap.update-plan-progress "${plan_id}"` (local takes the plan id only). |
| V-85 | `query state-snapshot` | 2: `engineer/workflows/add-tests.md:306`, `engineer/workflows/progress.md:78` | `state.get` | MAP | Replace with `engineer_run query state.get`. |
| V-86 | `query state.add-roadmap-evolution` | 3: `engineer/workflows/edit-phase.md:273`, `engineer/workflows/insert-phase.md:93` | `state.add-roadmap-evolution` | MAP | Rewrite to one text positional; expect `{added:true}` or duplicate-noop from the local verb. |
| V-87 | `query state.begin-phase` | 1: `engineer/workflows/execute-phase.md:349` | `state.begin-phase` | MAP | Rewrite `--phase N --name X --plans K` to `engineer_run query state.begin-phase N --status Executing`. |
| V-88 | `query state.get` | 1: `engineer/workflows/new-milestone.md:211` | `state.get` | MAP | Rewrite; add a `milestone` key (active ROADMAP milestone) to `State.view()` -- it is absent today, so `state.get milestone --raw` prints an empty line. |
| V-89 | `query state.json` | 1: `engineer/workflows/next.md:20` | `state.get` | MAP | Replace with `engineer_run query state.get`. |
| V-90 | `query state.load` | 4: `agents/gsd-debugger.md:962`, `agents/gsd-planner.md:582` | `state.get / init.ship` | MAP | Replace in debugger/planner with `state.get`; in ship.md:45 with `init.ship`. |
| V-91 | `query state.milestone-switch` | 1: `engineer/workflows/new-milestone.md:214` | `milestone.create` | MAP | Replace with `engineer_run query milestone.create "v[X.Y] [Name]"`. |
| V-92 | `query state.patch` | 2: `engineer/workflows/insert-phase.md:82`, `engineer/workflows/insert-phase.md:157` | `state.patch` | NEW | Implement in `engineer/bin/lib/state.py`: apply a JSON map of `Current Position` field -> value under `planning_lock`; return matched fields. |
| V-93 | `query state.planned-phase` | 1: `engineer/workflows/plan-phase.md:1427` | `roadmap.set-plans` | MAP | Replace with `engineer_run query roadmap.set-plans <N> --plans <ids...>`. |
| V-94 | `query state.record-session` | 3: `engineer/workflows/discuss-phase.md:481`, `engineer/workflows/milestone-summary.md:232` | `state.record-session` | MAP | Rewrite with `--stopped-at`, `--resume-file`, `--status`. |
| V-95 | `query state.update` | 2: `engineer/workflows/execute-phase.md:262`, `engineer/workflows/ship.md:483` | `state.update` | NEW | Implement in `engineer/bin/lib/state.py` beside `state.patch`: set one `Current Position` field (`Last Activity`, `last_gate_trip`). |
| V-96 | `query summary-extract` | 3: `agents/gsd-verifier.md:389`, `engineer/workflows/complete-milestone.md:222` | `summary-extract` | NEW | Implement in `engineer/bin/lib/summaries.py`: read SUMMARY frontmatter/body for `--fields one_liner,key-files,...` across one or many paths. |
| V-97 | `query task.is-behavior-adding` | 1: `engineer/workflows/execute-phase.md:245` | `task.is-behavior-adding` | NEW | Implement in `engineer/bin/lib/tdd.py`: true when the task adds/changes runtime behaviour (non-doc, non-test, non-config files in `files`, or action verbs add/implement/handle); return `{is_behavior_adding, reason}`. |
| V-98 | `query teams-status` | 1: `engineer/workflows/plan-phase.md:408` | - | DROP | Delete the agent-teams warning block in `engineer/workflows/plan-phase.md` (Claude experimental env probe). |
| V-99 | `query todo.match-phase` | 1: `engineer/workflows/discuss-phase.md:275` | `todo.match-phase` | MAP | Rewrite. |
| V-100 | `query uat.classify-coverage` | 1: `engineer/workflows/verify-work.md:228` | `uat.classify-coverage` | NEW | Implement in `engineer/bin/lib/uat.py`: classify SUMMARY `must_haves`/deliverables into `automated\|human\|not-testable` coverage buckets. |
| V-101 | `query uat.complete-session` | 1: `engineer/workflows/verify-work.md:542` | `uat.complete-session` | NEW | Implement in `engineer/bin/lib/uat.py`: set UAT frontmatter `status: complete`, timestamp, then commit through `gitops.commit` with `--message`. |
| V-102 | `query uat.render-checkpoint` | 1: `engineer/workflows/verify-work.md:383` | `uat.render-checkpoint` | NEW | Implement in `engineer/bin/lib/uat.py`: render the next pending test of the UAT file as the checkpoint text block. |
| V-103 | `query user-story.validate` | 1: `agents/gsd-verifier.md:664` | `user-story.validate` | NEW | Implement in `engineer/bin/lib/phases.py`: match `^As a .+, I want to .+, so that .+\.$`; return `{valid, errors[], slots}`. |
| V-104 | `query verification` | 3: `engineer/workflows/execute-phase.md:379`, `engineer/workflows/execute-phase.md:380` | `verification.status` | MAP | Rewrite `query verification status <dir>` to `engineer_run query verification.status <N\|dir> --pick status\|route`; accept a phase dir in `verification.status`; add `route`, `next_action`, `next_command` fields. |
| V-105 | `query verification.append-audit` | 2: `engineer/workflows/secure-phase.md:154`, `engineer/workflows/validate-phase.md:149` | `verification.append-audit` | NEW | Implement in `engineer/bin/lib/verification.py`: append a `## <heading>` audit row block to SECURITY/VALIDATION.md unless identical to the last block; return `{appended}`. |
| V-106 | `query verification.fingerprint` | 2: `agents/gsd-verifier.md:681`, `engineer/workflows/execute-phase/steps/verify-phase-goal.md:170` | `verification.fingerprint` | NEW | Implement in `engineer/bin/lib/verification.py` reusing `verification_checks` digests: hash the phase PLAN/SUMMARY files plus listed covered files (never the report); write it to VERIFICATION.md frontmatter. |
| V-107 | `query verification.resolve-file` | 1: `engineer/workflows/verify-work.md:650` | `verification.resolve-file` | MAP | Rewrite; accept a phase dir. |
| V-108 | `query verification.status` | 11: `agents/gsd-verifier.md:567`, `agents/gsd-verifier.md:833` | `verification.status` | MAP | Rewrite all 11; accept phase dir or number; support `--pick`. |
| V-109 | `query verify.artifacts` | 1: `agents/gsd-verifier.md:253` | `verify.artifacts` | NEW | Implement in `engineer/bin/lib/verify.py`: for PLAN `must_haves.artifacts`, check exists, non-stub (min lines / not TODO-only), `contains` patterns; exit 1 on any failure. |
| V-110 | `query verify.commits` | 1: `agents/gsd-verifier.md:395` | `verify.commits` | NEW | Implement in `engineer/bin/lib/verify.py`: each SHA exists and is an ancestor of HEAD; exit 1 listing missing. |
| V-111 | `query verify.key-links` | 1: `agents/gsd-verifier.md:331` | `verify.key-links` | NEW | Implement in `engineer/bin/lib/verify.py`: for PLAN `must_haves.key_links` `{from,to,via,pattern}`, grep `pattern` in `from`; exit 1 on unwired links. |
| V-112 | `query verify.plan-structure` | 3: `agents/gsd-plan-checker.md:770`, `agents/gsd-plan-checker.md:836` | `verify.plan-structure` | NEW | Implement in `engineer/bin/lib/plans.py`: required frontmatter (`phase, plan, type, wave, depends_on, files_modified, autonomous, must_haves`) and each task's `files/action/verify/done`; exit 1 with errors. |
| V-113 | `query websearch` | 1: `agents/gsd-phase-researcher.md:143` | - | DROP | Delete the `brave` provider row; use built-in WebSearch. |
| V-114 | `query worktree.base-check` | 5: `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:62`, `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:64` | - | DROP | Delete the degrade-to-sequential branches (`_SHOULD_DEGRADE`, `_QB_SHOULD_DEGRADE`, `_QUICK_SHOULD_DEGRADE`); local isolation is mandatory and `dispatch-isolation` fails instead. |
| V-115 | `query worktree.cleanup-wave` | 4: `engineer/workflows/execute-phase.md:897`, `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:332` | `worktree.cleanup-wave` | MAP | Rewrite `--manifest "$X"` to `--phase <N\|quick-id>`. |
| V-116 | `query worktree.create` | 2: `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:303`, `engineer/workflows/quick-batch/steps/worktree-dispatch.md:134` | `worktree.create` | MAP | Rewrite to `engineer_run query worktree.create <plan> --phase <N> --base ... --branch ... --files ... --deletions ...`; drop `--manifest/--agent-id/--path`. |
| V-117 | `query worktree.reap-orphans` | 3: `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:59`, `engineer/workflows/quick-batch.md:121` | `worktree.reap-orphans` | MAP | Rewrite all 3. |
| V-118 | `query worktree.record-agent` | 1: `engineer/workflows/execute-phase.md:779` | `worktree.record-agent` | MAP | Rewrite to `engineer_run query worktree.record-agent <plan> --branch <b> --phase <N> --path <wt>`. |
| V-119 | `query worktree.worker-complete` | 1: `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:363` | - | DROP | Delete the orchestrator-exec background-process lane in `executor-isolation-dispatch.md` (Codex dispatches native subagents into `worktree.create` checkouts). |
| V-120 | `query worktree.worker-record` | 1: `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:349` | - | DROP | Delete with `worktree.worker-complete`. |
| V-121 | `query worktree.worker-status` | 1: `engineer/workflows/execute-phase/steps/executor-isolation-dispatch.md:132` | `worktree.list` | DROP | Delete the resume sweep; use `engineer_run query worktree.list` for leftover worktrees. |
| V-122 | `quick-batch cleanup-entry` | 1: `engineer/workflows/quick-batch/steps/merge-wave.md:37` | `quick-batch.cleanup-entry` | NEW | Implement in `engineer/bin/lib/quick_batch.py`: build the worktree cleanup entry `{quickId, path, branch, merged}` for one merged item. |
| V-123 | `quick-batch complete` | 1: `engineer/workflows/quick-batch/steps/completion.md:12` | `quick-batch.complete` | NEW | Implement in `engineer/bin/lib/quick_batch.py`: mark the batch record complete with per-item outcomes. |
| V-124 | `quick-batch create` | 2: `engineer/workflows/quick-batch/steps/batch-init.md:14`, `engineer/workflows/quick-batch/steps/batch-init.md:25` | `quick-batch.create` | NEW | Implement in `engineer/bin/lib/quick_batch.py`: parse `--file` task list into items, create `.planning/quick/batches/<id>.json` with `--base-revision`, one `quick.create` record per item. |
| V-125 | `quick-batch effective-concurrency` | 3: `engineer/workflows/quick-batch/steps/planner-wave.md:38`, `engineer/workflows/quick-batch/steps/research-phase.md:13` | `quick-batch.effective-concurrency` | NEW | Implement: `min(jobs, task_count, capacity)` floored at 1; force 1 when `--mutating` and isolation is not a worktree mode. |
| V-126 | `quick-batch filter-executed` | 1: `engineer/workflows/quick-batch/steps/worktree-dispatch.md:55` | `quick-batch.filter-executed` | NEW | Implement: return `--eligible` ids not in `--executed` (JSON arrays). |
| V-127 | `quick-batch merge-eligible` | 1: `engineer/workflows/quick-batch/steps/merge-wave.md:23` | `quick-batch.merge-eligible` | NEW | Implement: the ready ids forming the longest prefix of `--wave-order` (deterministic merge order). |
| V-128 | `quick-batch merge-routing` | 1: `engineer/workflows/quick-batch/steps/merge-wave.md:90` | `quick-batch.merge-routing` | NEW | Implement: map `--kind merge_failed\|conflict\|scope_violation` + `--detail` to `{action: retry\|block\|skip, message}`. |
| V-129 | `quick-batch parse-args` | 2: `commands/quick-batch.md:78`, `engineer/workflows/quick-batch.md:44` | `quick-batch.parse-args` | NEW | Implement: read argv text from `--stdin`; parse task list, `--jobs N`, `--validate`, `--research`, `--resume <id>`; JSON out, exit 1 on unknown flags. |
| V-130 | `quick-batch resume` | 3: `engineer/workflows/quick-batch/steps/completion.md:42`, `engineer/workflows/quick-batch/steps/resume-mode.md:13` | `quick-batch.resume` | NEW | Implement: load batch, report eligible/in-flight/done items and base drift vs `--current-base-revision`. |
| V-131 | `quick-batch spawn-plan` | 1: `engineer/workflows/quick-batch/steps/worktree-dispatch.md:74` | `quick-batch.spawn-plan` | NEW | Implement: next ids to spawn = first `capacity - in_flight` eligible ids. |
| V-132 | `quick-batch update` | 3: `engineer/workflows/quick-batch/steps/merge-wave.md:86`, `engineer/workflows/quick-batch/steps/planner-wave.md:145` | `quick-batch.update` | NEW | Implement: merge `--updates` JSON array by `quickId` into the batch record under `planning_lock`. |
| V-133 | `quick-batch verification-routing` | 1: `engineer/workflows/quick-batch/steps/verification-wave.md:64` | `quick-batch.verification-routing` | NEW | Implement: map verification `--status` to `{route: merge\|fix\|human\|block}`. |
| V-134 | `quick-tasks-append` | 6: `engineer/workflows/fast.md:92`, `engineer/workflows/quick.md:670` | `quick.create / quick.update` | MAP | fast.md: replace with `engineer_run query quick.create "$TASK"` + `quick.update <id> --status complete`; quick.md: replace with `quick.update "${quick_id}" --status "${VERIFICATION_STATUS}"` (QUICK.md records replace the STATE Quick Tasks table). |
| V-135 | `quick-tasks-migrate` | 2: `engineer/workflows/fast.md:91`, `engineer/workflows/quick.md:666` | - | DROP | Delete (legacy STATE table repair; local records live in `.planning/quick/*/QUICK.md`). |
| V-136 | `review-lane dispatch-step` | 2: `commands/code-review.md:55`, `engineer/workflows/code-review.md:684` | - | DROP | Delete external reviewer-lane dispatch in code-review.md and commands/code-review.md (cross-AI dropped). |
| V-137 | `review-lane explicit-from-argv` | 1: `engineer/workflows/code-review.md:648` | - | DROP | Delete with `review-lane dispatch-step`; `EXPLICIT_REVIEWER_SLUGS` stays empty, so remove the branch. |
| V-138 | `review-lane flags` | 2: `commands/code-review.md:34`, `engineer/workflows/next.md:286` | - | DROP | Delete the lane-flag loop in next.md:286 and the flag paragraph in commands/code-review.md:34. |
| V-139 | `review-lane sections` | 1: `commands/code-review.md:57` | - | DROP | Delete the `--explicit` paragraph in commands/code-review.md:57. |
| V-140 | `run-with-timeout` | 8: `agents/gsd-verifier.md:504`, `engineer/workflows/audit-fix.md:147` | `run-with-timeout` | NEW | Implement in `engineer/bin/lib/procs.py`: run argv after `--` with `subprocess.run(timeout=N)`, stream output, exit 124 on timeout, child exit code otherwise; regression/post-merge/audit-fix gates switch to `verification.run-checks`, verifier probes keep this verb. |
| V-141 | `verify codebase-drift` | 1: `engineer/workflows/plan-phase.md:599` | `codebase.status` | MAP | Replace with `engineer_run query codebase.status`; map `stale` to the drift warning. |
| V-142 | `verify context-drift` | 1: `engineer/workflows/plan-phase.md:329` | - | DROP | Delete the context-drift step and its `workflow.context_drift_action` hint in plan-phase.md (lines 329-346). |
| V-143 | `windows fixed` | 1: `engineer/workflows/ship.md:148` | - | DROP | Delete the windows-ledger block in ship.md (optional ledger; no `.planning/WINDOWS.md` locally). |
| V-144 | `windows status` | 5: `engineer/workflows/progress.md:167`, `engineer/workflows/progress.md:172` | - | DROP | Delete `Open Windows` rendering in progress.md:167-172 and the ledger gate in ship.md:139-159. |
| V-145 | `windows waive` | 1: `engineer/workflows/ship.md:149` | - | DROP | Delete with `windows status`. |

Cross-cutting call-shape and non-verb Node rows (same ID series):

| ID | Upstream pattern | Uses (count: 2 examples) | Local verb | Action | Instruction |
|---|---|---|---|---|---|
| V-146 | global `--pick <field>` | 29 lines in 15 files: `agents/gsd-verifier.md:664`, `engineer/workflows/execute-phase.md:211` | - | NEW | Implement in `engineer/bin/engineer.py` `main`: after a successful verb, resolve the dotted field in the result and print it raw (`true/false`, scalar, or compact JSON); exit 1 `pick-missing` when absent. |
| V-147 | `config-get ... --default <v>` | 19 lines in 15 files: `engineer/workflows/audit-fix.md:124`, `engineer/workflows/cleanup.md:19` | `config-get` | NEW option | Implement in `verb_config_get` (engineer.py; was phase.py 148-151): return `--default` when the key is absent; without it exit 1 (`key-not-found`). Today it prints an empty line and exits 0, which defeats every `\|\| echo "<default>"` fallback. |
| V-148 | workstreams `--ws` / `GSD_WS` | 69 `--ws` call lines in 25 files, 175 `GSD_WS` lines in 26 files: `engineer/workflows/add-phase.md:39`, `engineer/workflows/add-phase.md:40` | - | DROP | Delete the `GSD_WS=...` parse lines and every `${GSD_WS:+--ws=...}` / `$GSD_WS_ARG` argument (workstreams dropped; no local workstream model). |
| V-149 | `@file:` overflow unwrap | 55 lines in 34 files: `agents/executor.md:55`, `agents/gsd-debugger.md:963` | - | DROP | Delete the `[[ "$X" == @file:* ]] && X=$(cat ...)` lines; engineer.py always writes JSON to stdout. |
| V-150 | inline `node -e/-p/-c` JSON helpers | 97 lines in 26 files: `engineer/workflows/code-review.md:40` (21 in file), `agents/gsd-code-fixer.md:112` (8) | `--pick` / python | REPLACE | Replace each with `--pick` on the producing `engineer_run` call; where the input is not engineer output, use `python3 -c` (via the interpreter the launcher found) - never `node`. |
| V-151 | `node "$EDGE_PROBE_JS"` (edge-probe.cjs) | 10 lines: `engineer/workflows/spec-phase.md:228`, `engineer/references/specless-probe-fallback.md:70` | `spec.edge-probe` | NEW | Implement in `engineer/bin/lib/probes.py`: read the requirements JSON array, emit `{items[{requirement_id,category,status,verification,resolution,reason,probe}], coverage{applicable,unclassified,...}}`; exit 2 on bad shape; oracle = `engineer/references/edge-probe-fixtures/01..06`. |
| V-152 | `node "$SPEC_SECTION_JS"` (spec-section.cjs) | 6 lines: `engineer/references/specless-probe-fallback.md:30`, `engineer/references/specless-probe-fallback.md:36` | `spec.section` | NEW | Implement in `engineer/bin/lib/probes.py`: `spec.section <SPEC.md> edges\|prohibitions` -> `{supplied: bool, items[]}`. |
| V-153 | `node "$GSD_CHANGESET_CLI"`, `npx -y @opengsd/gsd-core@latest` | 5 + 2 lines: `engineer/workflows/update.md:230`, `engineer/workflows/_runtime-launcher.snippet.sh:1` | `bin/update.py` | DROP | Rewrite `engineer/workflows/update.md` around `python bin/update.py` (preview, apply); delete the changelog CLI preview. |
| V-154 | agent names passed to the runtime (`gsd-executor`, `gsd-code-reviewer`, ...) | in `agent-skills` (32) and `resolve-model` (10) calls: `engineer/workflows/execute-phase.md:99`, `engineer/workflows/audit-fix.md:104` | `models.agents_dir()` | MAP | Resolve names against `<ns>/agents/*.md`; rename `gsd-executor` -> `executor` (only `agents/executor.md` exists); use whatever final names the agents section fixes. |

Totals: 154 rows (V-01..V-154). Actions: MAP 62, NEW 55, DROP 36, REPLACE 1.

Done when:
- `grep -rn 'gsd_run\|gsd-tools\|GSD_WS\|@file:' agents commands engineer` returns nothing
- `grep -rnE 'node (-e|-p|-c|"\$)|npx -y @opengsd' agents commands engineer` returns nothing
- `grep -rn 'loop render-hooks\|review-lane\|graphify\|learnings\.\|windows status\|research-store\|teams-status' agents commands engineer` returns nothing
- `python -m unittest tests.test_verb_coverage` passes: every `engineer_run query <verb>` token in `agents/ commands/ engineer/` is listed by `engineer_run query help`

### Config keys

Local defaults live in `engineer/bin/lib/config.py` `DEFAULTS` (was `.ai/runtime/lib/config.py` lines 8-52); every NEW key gets its default there, not only in `.planning/config.yaml`. Occurrences are every `config-get`/`config-set` in kept files.

| ID | Upstream key (uses: examples) | Local key | Action | Default | Instruction |
|---|---|---|---|---|---|
| C-01 | `commit_docs` (6: `engineer/workflows/fast.md:64`, `engineer/workflows/new-milestone.md:274`) | `commit_docs` (config.yaml:7) | MAP | `true` | Keep. |
| C-02 | `response_language` (9: `engineer/workflows/cleanup.md:19`, `engineer/workflows/ship.md:32`) | `response_language` (config.yaml:11) | MAP | `null` | Keep; `--default ""` needs V-147. |
| C-03 | `context_window` (3: `engineer/workflows/execute-phase.md:159`, `engineer/workflows/plan-phase.md:98`) | `context_window` (config.yaml:20) | MAP | `200000` (DEFAULTS), `1000000` (project) | Keep. |
| C-04 | `runtime` (3: `engineer/workflows/execute-phase.md:124`, `engineer/workflows/quick.md:148`) | `runtime-identity .host` | MAP | inferred | Drop the key; add `host` (from `models.resolve_host()`) to `runtime-identity`; rewrite to `engineer_run query runtime-identity --pick host`. |
| C-05 | `workflow.use_worktrees` (4: `agents/gsd-code-fixer.md:671`, `engineer/workflows/quick-batch.md:86`) | `workflow.isolation` (config.yaml:35) | DROP | - | Delete; isolation is mandatory; branch on `engineer_run query dispatch-isolation --raw`. |
| C-06 | `executor.stall_detect_interval_minutes` (1: `engineer/workflows/execute-phase.md:126`) | `executor.stall_detect_interval_minutes` | NEW | `5` | Add to DEFAULTS. |
| C-07 | `executor.stall_threshold_minutes` (1: `engineer/workflows/execute-phase.md:127`) | `executor.stall_threshold_minutes` | NEW | `10` | Add to DEFAULTS. |
| C-08 | `planner.stall_detection_enabled` (1: `engineer/workflows/plan-phase/steps/stall-detection-helpers.md:92`) | same | NEW | `true` | Add to DEFAULTS. |
| C-09 | `planner.stall_detect_interval_minutes` (1: `stall-detection-helpers.md:96`) | same | NEW | `5` | Add to DEFAULTS. |
| C-10 | `planner.stall_threshold_minutes` (1: `stall-detection-helpers.md:97`) | same | NEW | `10` | Add to DEFAULTS. |
| C-11 | `features.global_learnings` (1: `engineer/workflows/execute-phase.md:1367`) | - | DROP | - | Delete with the learnings step (V `query learnings.copy`). |
| C-12 | `ship.pr_body_sections` (1: `engineer/workflows/ship.md:270`) | - | DROP | - | Delete; PR body comes from `engineer/templates/pull-request.md` via `pr.open`. |
| C-13 | `workflow.agent_hint_routing` (get 1 + set 1: `per-plan-executor-routing.md:25`, `:24`) | same | NEW | `true` | Add to DEFAULTS; replace the `gsd config-set` hint with `engineer_run query config-set`. |
| C-14 | `workflow.build_command` (1: `engineer/workflows/execute-phase/steps/post-merge-gate.md:13`) | `verification.commands` (config.yaml:143) | DROP | - | Delete; list the build as a `verification.commands` entry. |
| C-15 | `workflow.test_command` (3: `engineer/workflows/audit-fix.md:124`, `regression-gate-run.md:25`) | `verification.commands` | MAP | `[]` | Replace the test-command gate with `engineer_run query verification.run-checks`. |
| C-16 | `workflow.test_gate_timeout` (3: `engineer/workflows/audit-fix.md:146`, `post-merge-gate.md:146`) | `verification.commands[].timeout` | MAP | per-check | Delete the key read; timeouts live per check. |
| C-17 | `workflow.code_review` (1: `engineer/workflows/code-review.md:107`) | same | NEW | `true` | Add to DEFAULTS; also gates the execute-phase review step that replaces `execute:post` hooks. |
| C-18 | `workflow.code_review_command` (1: `engineer/workflows/ship.md:393`) | - | DROP | - | Delete the external review command (cross-AI). |
| C-19 | `workflow.code_review_depth` (1: `engineer/workflows/code-review.md:448`) | same | NEW | `standard` | Add to DEFAULTS (`quick\|standard\|deep`). |
| C-20 | `workflow.code_review_depth_overrides` (1: `engineer/workflows/code-review.md:449`) | same | NEW | `[]` | Add to DEFAULTS. |
| C-21 | `workflow.code_review_point` (2: `engineer/workflows/code-review.md:629`, `:811`) | - | DROP | - | Delete; review runs at one fixed point (end of execute). |
| C-22 | `workflow.context_coverage_gate` (2: `engineer/workflows/plan-phase.md:1364`, `engineer/references/verifier-phase-gates.md:34`) | same | NEW | `true` | Add to DEFAULTS (gates `check.decision-coverage-*`). |
| C-23 | `workflow.discuss_mode` (3: `commands/discuss-phase.md:55`, `engineer/workflows/progress.md:31`) | `workflow.discuss_mode` (config.yaml:28) | MAP | `discuss` | Keep. |
| C-24 | `workflow.human_verify_mode` (1: `engineer/references/checkpoints.md:137`) | same | NEW | `end-of-phase` | Add to DEFAULTS. |
| C-25 | `workflow.live_dom_uat` (1: `engineer/workflows/verify-work/steps/automated-ui-verification.md:35`) | same | NEW | `false` | Add to DEFAULTS. |
| C-26 | `workflow.mvp_mode` (1: `engineer/workflows/plan-phase.md:99`) | same | NEW | `false` | Add to DEFAULTS (read by `phase.mvp-mode`). |
| C-27 | `workflow.plan_chunked` (1: `engineer/workflows/plan-phase.md:214`) | same | NEW | `false` | Add to DEFAULTS. |
| C-28 | `workflow.plan_review_convergence` (get 2 + set 2: `engineer/workflows/next.md:303`, `engineer/workflows/plan-phase.md:1220`; set `commands/progress.md:33`, `engineer/workflows/next.md:310`) | - | DROP | - | Delete the convergence route (command `plan-review-convergence` is not kept). |
| C-29 | `workflow.security_asvs_level` (1: `engineer/workflows/secure-phase.md:39`) | same | NEW | `1` | Add to DEFAULTS. |
| C-30 | `workflow.security_block_on` (1: `engineer/workflows/secure-phase.md:40`) | same | NEW | `high` | Add to DEFAULTS. |
| C-31 | `security_enforcement` (prose, 9 lines in agents/engineer, e.g. `agents/gsd-phase-researcher.md:202`) | `workflow.security_enforcement` | NEW | `true` | Add to DEFAULTS; gates the direct secure-phase step that replaces `verify:post` hooks. |
| C-32 | `workflow.specless_probe_fallback` (1: `engineer/references/specless-probe-fallback.md:20`) | same | NEW | `true` | Add to DEFAULTS. |
| C-33 | `workflow.ui_interaction_capture` (1: `engineer/workflows/ui-review.md:32`) | same | NEW | `false` | Add to DEFAULTS. |
| C-34 | `workflow.ui_phase` (1: `engineer/workflows/ui-phase.md:55`) | same | NEW | `true` | Add to DEFAULTS. |
| C-35 | `workflow.worktree_skip_hooks` (2: `engineer/workflows/execute-phase.md:849`, `engineer/workflows/quick/steps/worktree-pre-dispatch-commit.md:40`) | - | DROP | - | Delete; it adds `--no-verify`, and hooks are never skipped. |
| C-36 | `workflow._auto_chain_active` (set 1: `engineer/workflows/execute-phase.md:198`; read via `check auto-mode`) | `workflow.auto_advance` (config.yaml:27) | MAP | `false` | Delete the transient write; read `workflow.auto_advance`. |
| C-37 | `workflow.text_mode` (set 1: `engineer/workflows/discuss-phase/modes/text.md:23`) | `workflow.text_mode` (config.yaml:25) | MAP | `false` | Keep. |
| C-38 | `workflow.context_drift_action` (set prose 1: `engineer/workflows/plan-phase.md:346`) | - | DROP | - | Delete with `verify context-drift`. |
| C-39 | `workflow.nyquist_validation` (set prose 1: `engineer/workflows/plan-phase.md:671`) | same | NEW | `true` | Add to DEFAULTS; gates validate-phase. |
| C-40 | `workflow.tdd_mode` (set 1: `engineer/workflows/plan-phase.md:163`; read via `--active-cap tdd` at `execute-phase.md:213`) | same | NEW | `false` | Add to DEFAULTS; read with `config-get workflow.tdd_mode --default false --raw`. |
| C-41 | (implied by `dispatch-capacity`, `engineer/workflows/quick-batch.md:107`) | `quick_batch.capacity` | NEW | `3` | Add to DEFAULTS and a commented line in config.yaml. |
| C-42 | agent model keys used by `resolve-model` with upstream names | `agents.<name>` (config.yaml:100-133, keyed `coder`, `debugger`, `doc-writer`, `phase-preparer`, `codebase-mapper`, `researcher`, `code-reviewer`, `verifier`, `phase-checker`, `doc-verifier`, `integration-checker`) | MAP | per role | Re-key the block to the kept agent file names (e.g. `executor`, `gsd-planner`, `gsd-verifier`) once the agents section fixes them; keep tier logic. |
| C-43 | noise tokens from the grep (`COMMAND`, `calls.`, `is`, `needed.`) | - | - | - | Ignore: prose around `config-get`, not keys. |

Done when:
- `python -c "import sys; sys.path.insert(0,'engineer/bin'); from lib.config import DEFAULTS as D; w=D['workflow']; assert all(k in w for k in ('code_review','code_review_depth','tdd_mode','ui_phase','security_asvs_level','security_block_on','security_enforcement','nyquist_validation','mvp_mode','plan_chunked','specless_probe_fallback','human_verify_mode','live_dom_uat','ui_interaction_capture','context_coverage_gate','agent_hint_routing'))"` exits 0
- `engineer_run query config-get workflow.nonexistent --raw; test $? -eq 1`
- `test "$(engineer_run query config-get workflow.nonexistent --default x --raw)" = x`
- `grep -rn 'use_worktrees\|worktree_skip_hooks\|plan_review_convergence\|global_learnings\|_auto_chain_active\|code_review_point\|pr_body_sections\|test_gate_timeout\|build_command' agents commands engineer` returns nothing

### Hooks

Registrations come from `.ai/install.py` `MANAGED_HOOKS` (lines 436-454) and `HOST_HOOKS` (lines 466-474); command shape at lines 490 and 535 (`bash "$(git rev-parse --show-toplevel)/.{host}/hooks/{script}"`).

| ID | Local hook | Event (matcher, timeout) | Behavior | Target | Action | Instruction |
|---|---|---|---|---|---|---|
| R-RT-55 | `planning-integrity.sh` + `.py` | `PreToolUse` `^(Bash\|exec_command\|shell_command\|shell)$`, 10 s | BLOCK: exit 2 with diagnostic on malformed planning records in a prospective commit | `hooks/planning-integrity.sh`, `hooks/planning-integrity.py` | MOVE | Fix the import path (R-RT-46); keep the sh probe launcher (python3/python). |
| R-RT-56 | `ai-tier-notice.sh` | `PostToolUse` `^(Bash\|Write\|Edit\|MultiEdit\|NotebookEdit\|apply_patch)$`, 10 s | WARN: NOTICE, always exit 0 | `hooks/ai-tier-notice.sh` | MOVE | Repoint RULES anchors (R-RT-44). |
| R-RT-57 | `worktree-guard.sh` (dispatch job) | `PreToolUse` `^(Agent\|Task)$`, 10 s | WARN: stderr warning when a write-capable dispatch lacks `isolation="worktree"`; exit 0; appends the active-agent stack `.planning/handoffs/.active-<slug>.jsonl` (lines 75-100) | `hooks/worktree-path-guard.py` | PORT | Port to Python with identical stdin JSON handling and the same JSONL record shape `context-handoff.sh` reads; fail open on any parse error. |
| R-RT-58 | `worktree-guard.sh` (write job) | `PreToolUse` `^(Write\|Edit\|MultiEdit\|NotebookEdit\|apply_patch)$`, 10 s | WARN: primary-checkout writes, scratchpad writes, absolute paths into another checkout; exit 0 | `hooks/worktree-path-guard.py` | PORT | Same script, dispatched on `tool_name`; keep warn-only and change `engineer/workflows/quick.md:531` ("denied by gsd-worktree-path-guard") to say it warns. |
| R-RT-59 | registration of the ported `.py` | as R-RT-57/58 | - | `bin/install.py` `hook_settings` (was 484-540), `managed_scripts` (477-481), stale detection (594-608) | EDIT | Register `bash ".../.{host}/hooks/python-hook.sh" worktree-path-guard.py` (new 10-line launcher probing venv/python3/python, same as `planning-integrity.sh`); add `worktree-guard.sh` to the stale-script list so `--update` replaces old registrations. |
| R-RT-60 | `context-handoff.sh` | `PostToolUse` `^(Bash\|Write\|Edit\|MultiEdit\|NotebookEdit\|apply_patch\|Agent\|Task)$` 10 s; `SubagentStop` 10 s; `Stop` 10 s; `SessionStart` 10 s (Codex only) | WARN: advisory `additionalContext`; writes `.planning/handoffs/`; never blocks | `hooks/context-handoff.sh` + `hooks/lib/` | MOVE | Edit line 419 (`engineer_run`); keep the config read of `.planning/config.yaml` (handoff-io.sh:187). |
| R-RT-61 | `hooks/lib/agent-roles.sh` lines 15, 26, 29 + `lib/handoff.py` lines 137-138 | used by R-RT-57/60 | - | `hooks/lib/agent-roles.sh`, `engineer/bin/lib/handoff.py`, Python port | EDIT | Replace local role names with kept agents: write-capable `executor gsd-code-fixer gsd-debugger gsd-doc-writer gsd-nyquist-auditor`; artifact `gsd-phase-researcher gsd-codebase-mapper gsd-planner gsd-pattern-mapper gsd-ui-researcher`; review `gsd-verifier gsd-code-reviewer gsd-doc-verifier gsd-plan-checker gsd-integration-checker gsd-security-auditor gsd-ui-auditor gsd-ui-checker gsd-dom-verifier`; have the Python port parse this file instead of keeping a third copy. |
| R-RT-62 | `worktree-location.sh` | `WorktreeCreate` 180 s, `WorktreeRemove` 60 s (Claude only) | BLOCK on failure: non-zero exit refuses the dispatch; creates `<root>/.worktrees/<name>` on `worktree-<name>` | `hooks/worktree-location.sh` | MOVE | No content edits. |
| R-RT-63 | `cleanup.py` | none (explicit CLI, not registered) | exit 2 on refusal/partial | `scripts/cleanup.py` | MOVE | Covered by R-RT-13; keep it unregistered (`tests/test_install.py:125` asserts that). |
| R-RT-64 | upstream hook names in kept files: `gsd-check-update.js` (`engineer/workflows/update.md:475`, `:482`), `gsd-agent-isolation-guard.js` / `isolation-sentinel.js` (`executor-isolation-dispatch.md:26`, `:78-79`; `engineer/workflows/quick.md:409-410`) | - | - | - | DROP | Delete these references; no such hooks ship. |

Done when:
- `python -m unittest tests.test_worktree_path_guard` passes
- `bash tests/hooks/ai-tier-notice.test.sh && bash tests/hooks/context-handoff.test.sh && bash tests/hooks/worktree-location.test.sh` pass
- `python -m unittest discover -s tests -p test_handoff.py` passes (role-list equality)
- `grep -rn 'gsd-check-update\|isolation-sentinel\|agent-isolation-guard' agents commands engineer` returns nothing
- `test ! -e hooks/worktree-guard.sh && grep -q worktree-path-guard bin/install.py`

### Tests and CI

| ID | Files (old-path lines) | Action | Instruction |
|---|---|---|---|
| R-RT-65 | Runtime subprocess tests: `test_phase_runtime.py` (8: 3, 17, 881, 969, 1717-1718, 1784, 1793); `test_handoff.py` (6: 3, 22, 75, 332, 337, 342); `test_planning_integrity.py` (11: 11-12, 118, 138, 395, 459, 565, 625, 692, 702, 758); `test_todo_issues.py` (4: 15, 462, 497, 501); `test_verification_receipts.py` (1: 13); `test_planning_archive.py` (1: 13); `test_session_delivery.py` (3: 3, 26, 28); `test_issue_format.py` (9: 11, 15, 68-69, 75, 79, 237, 241, 246); `test_planning_review.py` (5: 14, 427, 463, 533, 536); `test_phase_issues.py` (1: 297); `test_cleanup.py` (3: 42, 215, 217) | REPOINT | Set `RUNTIME = ROOT / "engineer/bin/engineer.py"` and `sys.path` to `engineer/bin`; `templates_dir` -> `engineer/templates`; `packageName` -> `engineer-runtime`; install assets -> `bin/install-assets`; hooks -> `hooks/`; cleanup CLI -> `scripts/cleanup.py`; installed fixtures `.codex/runtime` -> `.codex/engineer/bin`; `.ai` namespace fixtures -> repo-root layout. |
| R-RT-66 | Installer/update/migration tests: `test_install.py` (37: 19, 103, 120, 138-158, 173, 193, 330-396, 465-477, 524-575, 658, 672, 799, 949, 976-980, 1002, 1027, 1045, 1069); `test_install_migration.py` (54: 26-28 loaders, 33-130, 190-311 fixtures, 348-408 hook relocation); `test_install_update.py` (28: 28-29, 33-102, 157, 353-492, 564-571, 743-765); `test_migration_cli.py` (18: 20-36 legacy `.ai` fixture, 49-119); `test_update_line_endings.py` (13: 16-17, 72-90, 110, 198-199, 346) | REPOINT | Load `bin/install.py`, `bin/migrate.py`, `bin/update.py`; assert the installed layout `.{host}/{agents,commands,engineer/bin,hooks,skills}`; keep legacy `.ai` inputs as migration fixtures; add a fixture for legacy `.{host}/runtime` -> `.{host}/engineer/bin`. |
| R-RT-67 | Doc-contract tests that read `.ai` prose: `test_agent_sources.py` (26: 15-16, 23-173, 192-252); `test_efficiency_contracts.py` (21: 14-114); `test_threat_tracking_contract.py` (68: 9-46 file list, 155-467); `test_parallel_status_contract.py` (6: 8-11, 87, 154); `test_unattended_flow.py` (6: 14, 62-63, 76, 84, 112); `test_workflow_links.py` (8: 16, 19, 31, 51-54, 61); `test_entrypoint_git_routing.py` (3: 44, 46, 61); `test_verification_bookkeeping.py` (3: 101-102, 108) | REWRITE or RETIRE | For each assertion, find the surviving owner file in `agents/`, `commands/`, `engineer/` and repoint; delete the assertion when the docs/commands sections drop the asserted local text; never leave a path to a deleted `.ai` file. |
| R-RT-68 | Skills mirror assertion `test_agent_sources.py:192-240`, `test_planning_review.py:538-546` | REPOINT | Assert `skills/<n>/SKILL.md` mirrors `commands/<n>.md`; installed root stays `.claude/skills` / `.agents/skills` per host. |
| R-RT-69 | `test_workflow_links.py:16-19` scan roots `(".ai", ".codex", ".claude", ".agents", ".planning", "docs")` | REPOINT | Scan `agents commands engineer hooks skills .planning docs`; exclude `engineer/templates/` like the old `templates/` exclusion. |
| R-RT-70 | Hook bash tests (4) | MOVE/PORT | Covered by R-RT-15. |
| R-RT-71 | `.github/workflows/validate.yml` line 27 | EDIT | `python -m pip install -r engineer/bin/requirements.txt`. |
| R-RT-72 | `.github/workflows/validate.yml` lines 29-32 | EDIT | Run `bash tests/hooks/ai-tier-notice.test.sh`, `bash tests/hooks/context-handoff.test.sh`, `bash tests/hooks/worktree-location.test.sh`; drop the `worktree-guard.test.sh` step (ported test runs under line 28's discover). |
| R-RT-73 | `.github/workflows/validate.yml` (new step) | ADD | Add a step that fails on Node in the kept tree: `! grep -rnE 'gsd_run\|gsd-tools\|node (-e\|-p\|-c\|"\$)' agents commands engineer hooks bin scripts skills`. |

New tests for NEW verbs (all under `tests/`, stdlib `unittest`, temp git repos like `test_phase_runtime.py`):

| ID | New test module | Covers |
|---|---|---|
| R-RT-74 | `test_engineer_cli.py` | `--pick`, `config-get --default` and missing-key exit 1, dotted family names, `runtime-identity` `host`, `engineer_run` shim + snippet resolution from source and from a fake `.claude/` install |
| R-RT-75 | `test_verb_coverage.py` | every `engineer_run query <verb>` token in `agents/ commands/ engineer/` is in `engineer_run query help` |
| R-RT-76 | `test_scope.py` | `check.evaluation-scope` (`--plan`, `--phase`, `--commits-only`, `--pathspec`, `--max-commits`) |
| R-RT-77 | `test_tdd.py` | `check.tdd-red-evidence` (OK, each INVALID_RED reason, exit 69), `phase.tdd-applicable`, `task.is-behavior-adding` |
| R-RT-78 | `test_plan_checks.py` | `verify.plan-structure`, `plan.task-structure`, `check.verify-command-paths`, `check.verify-failure-directions`, `frontmatter.get/set/validate` |
| R-RT-79 | `test_verify_checks.py` | `verify.artifacts`, `verify.key-links`, `verify.commits`, `verification.fingerprint`, `verification.append-audit` (dedupe), `verification.status` with a dir argument and `route` field |
| R-RT-80 | `test_uat.py` | `phase.uat-passed`, `audit-uat`, `audit-open`, `uat.classify-coverage`, `uat.render-checkpoint`, `uat.complete-session` |
| R-RT-81 | `test_decision_coverage.py` | `check.decision-coverage-plan`, `check.decision-coverage-verify` |
| R-RT-82 | `test_quick_batch.py` | all 12 `quick-batch.*` verbs, `dispatch-capacity`, `init.quick-batch` |
| R-RT-83 | `test_spec_probes.py` | `spec.edge-probe` against `engineer/references/edge-probe-fixtures/01..06` (`requirements.json` -> `expected-coverage.json`, 06 with `resolutions.json`); `spec.section` |
| R-RT-84 | `test_ui_gate.py` | `check.ui-plan-gate` |
| R-RT-85 | `test_misc_verbs.py` | `agent.classify-failure`, `project-instruction-file`, `user-story.validate`, `phase.mvp-mode`, `state.patch`, `state.update`, `summary-extract`, `run-with-timeout` (exit 124), `package-legitimacy` with patched `urlopen` and offline `UNKNOWN`, `config-new-project`, `generate-claude-md`, `init.code-review`, `init.new-project` |

Done when:
- `python -m unittest discover -s tests -v` passes on ubuntu and windows CI legs
- `bash tests/hooks/ai-tier-notice.test.sh && bash tests/hooks/context-handoff.test.sh && bash tests/hooks/worktree-location.test.sh` pass
- `grep -rnE '\.ai/|"\.ai"|phase_run|ai-phase-runtime|runtime/phase\.py' tests .github` returns only legacy-migration fixtures in `test_install_migration.py` / `test_migration_cli.py`
- `grep -n '\.ai/' .github/workflows/validate.yml` returns nothing
