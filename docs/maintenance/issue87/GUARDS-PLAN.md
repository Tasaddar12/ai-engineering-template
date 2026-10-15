---
phase: issue87-maintenance
plan: guards
type: execute
wave: 1
depends_on: []
issue_refs:
  - https://github.com/Tasaddar12/ai-engineering-template/issues/87
input_revision: 77b5668f2003bea60127d87e8785469286abafb3
files_modified:
  - .ai/hooks/destructive-git-guard.py
  - .ai/runtime/lib/destructive_guard.py
  - tests/test_destructive_guard.py
  - .ai/install.py
  - tests/test_install.py
  - .ai/hooks/README.md
  - .ai/references/destructive-operations.md
  - .ai/RULES.md
  - .ai/runtime/lib/worktrees.py
files_deleted: []
autonomous: true
requirements: [ISSUE87-GUARD, ISSUE87-RED]
acceptance: [I87-A1, I87-A3]
documentation:
  - .ai/hooks/README.md
  - .ai/references/destructive-operations.md
resources: []
checks:
  - [python, -m, unittest, discover, -s, tests, -p, test_destructive_guard.py, -v]
  - [python, -m, unittest, discover, -s, tests, -p, test_install.py, -k, registered_hooks, -v]
user_setup: []
must_haves:
  truths:
    - A registered destructive-operation hook refuses recognized primary-checkout branch switches while permitting explicit checkout path restores.
    - Recognized branch and worktree deletion refuses open or unknown PR/MR state and preserves dirty, unowned or ambiguous work.
    - Recognized backup removal is refused without exact approved state; ordinary shell backup removal is denied and the dependent cleanup route owns approved deletion.
    - PR86 worktree-guard warnings and scratchpad behavior remain advisory.
  artifacts:
    - path: .ai/hooks/destructive-git-guard.py
      provides: PreToolUse JSON entrypoint
    - path: .ai/runtime/lib/destructive_guard.py
      provides: Bounded parser, read-only evidence collection and destructive policy
    - path: tests/test_destructive_guard.py
      provides: Offline GitHub/GitLab attack and false-positive matrix with RED/GREEN evidence
  key_links:
    - from: .ai/install.py
      to: .ai/hooks/destructive-git-guard.py
      via: Separate blocking PreToolUse registration for supported shell tools
    - from: .ai/hooks/destructive-git-guard.py
      to: .ai/runtime/lib/destructive_guard.py
      via: Relative installed-host import; no dependency on source .ai paths
---

<objective>
Deliver a separate destructive Git/backup guard; CLEANUP-PLAN.md consumes its parser, evidence and approval schema.

Purpose: Prevent accidental loss during parallel work without changing PR86's advisory editing and dispatch checks.
Output: GUARD implementation commit and SUMMARY. CLEANUP-PLAN.md is a distinct wave-2 child plan with a real dependency on this commit. Its worktree is created only after the guard worker returns; do not implement the child here.
</objective>

<execution_context>
@.ai/commands/execute-phase.md
@.ai/templates/summary.md
@.ai/references/methods/tdd.md
@.ai/runtime/TEMPLATE-CONTRACT.md

This is authorized upstream maintenance under docs/maintenance/issue87, not an adopting-project phase. Acceptance aliases map directly to CONTEXT numbered acceptance 1, 2 and 3. The supplied requirement IDs are maintenance-local aliases, not invented ROADMAP/REQUIREMENTS entries. Do not populate adoption skeletons or use phase allocation verbs. The coordinator supplies the committed CONTEXT alongside this plan before execution. Only the coordinator publishes; this plan grants no real cleanup deletion or merge authority.
</execution_context>

<context>
@docs/maintenance/issue87/CONTEXT.md
@.ai/RULES.md
@.ai/references/git-workflow.md
@.ai/references/worktree-path-safety.md
@.ai/references/worktree-recovery-policy.md
@.ai/hooks/README.md
@.ai/hooks/worktree-guard.sh
@.ai/install.py
@tests/test_install.py
@.ai/runtime/lib/worktrees.py
@.ai/runtime/lib/delivery.py

At the input revision, worktrees.cleanup_wave (467-510) requires manifest merged status and ancestry but can force deletion; close_session (938-975) uses session_merged and can also force deletion. Neither exposes a preview or exact-list approval contract. session_merged accepts MERGED provider evidence or ancestry fallback. This plan does not modify or present those legacy verbs as the new cleanup route. delivery.view collapses errors into absence and is GitHub-specific: do not treat its None result as safe evidence, and do not change that adapter. install.py MANAGED_HOOKS and hook_settings own host registration; README owns hook claims. PR86's worktree-guard remains byte-for-byte unchanged.
</context>

<tasks>
<task type="auto" tdd="true">
  <name>GUARD: prove refusal through the registered hook, then implement bounded destructive policy</name>
  <files>.ai/hooks/destructive-git-guard.py, .ai/runtime/lib/destructive_guard.py, tests/test_destructive_guard.py, .ai/install.py, tests/test_install.py, .ai/hooks/README.md, .ai/references/destructive-operations.md, .ai/RULES.md (Hooks and validation prose only), .ai/runtime/lib/worktrees.py (advisory dispatch module docstring only)</files>
  <read_first>docs/maintenance/issue87/CONTEXT.md, .ai/RULES.md (Hooks and validation), .ai/hooks/worktree-guard.sh, .ai/hooks/README.md, .ai/install.py, tests/test_install.py (InstallerTests.launcher_argv and test_registered_hooks_execute_from_installed_subdirectory), .ai/runtime/lib/worktrees.py (module docstring, listing, primary_checkout, load_sessions, load_manifest, session_merged), .ai/runtime/lib/delivery.py (gh and view), .ai/references/worktree-path-safety.md, .ai/references/worktree-recovery-policy.md, .ai/references/methods/tdd.md; read each new assigned file if it already exists</read_first>
  <behavior>
    - Registered PreToolUse pipeline receives a primary-checkout git switch payload: before implementation it allows; after implementation it denies with a reason and stable code.
    - Explicit git checkout -- path and git checkout REF -- path restore forms allow, including quoted paths and filenames resembling branches/options. Branch checkout, -b/-B, --orphan, switch -c/-C/--detach and checkout REF without -- deny in the primary checkout. Ambiguous checkout path-or-ref syntax there denies with guidance to add -- for a path restore.
    - Linked-worktree switches remain allowed when recognized and unrelated to deletion. Direct deletion of protected/current branches, primary/current worktrees, dirty/ignored/untracked work or unowned targets denies.
    - OPEN GitHub PR, opened GitLab MR, any open match among several matches, unavailable/malformed/partial evidence and target-identity mismatches deny branch/worktree deletion. Recognized explicit terminal-state, clean, owned targets can pass policy only when all required evidence is complete.
    - Backup deletion through supported filesystem commands denies absent exact pinned approval. Non-backup ordinary removals and read-only commands permit without provider calls.
  </behavior>
  <action>
Write the named registered-pipeline test first. Reuse installer's existing hook settings and launcher conventions in a temporary Git fixture: enumerate actual matching managed PreToolUse handlers, feed the payload, and observe the combined verdict without executing the payload command. With no destructive registration at base, the real pipeline allows git switch; assert expected deny so RED is an intentional behavioral assertion, not an import/file-not-found crash. Record command, named assertion, exit, expected/actual result and commit before GREEN. Add remaining table cases before their implementation. Missing production-module imports, missing executables, skipped tests and zero discovery are INVALID_RED.

Implement a standard-library-only library and a thin JSON stdin hook. Export evaluate_payload(payload, evidence_runner=None) returning a structured allow/deny decision with reason_code, operation and targets; isolate provider/Git subprocess calls behind an injectable argv runner, never shell=True. Entrypoint with no subcommand reads the host payload. Permit unrelated supported commands with no queries; deny malformed shell payloads on the registered shell tool, or recognized dangerous syntax whose target/context cannot be resolved. Emit host-compatible PreToolUse deny JSON and exit 2 on refusal; return success with no denial for allow. Document and test actual launcher propagation rather than inferring a live host session.

Use the grammar and matrix below. Resolve every effective Git repository from payload cwd, Git -C and --git-dir/--work-tree where supported; if a recognized destructive invocation uses unsupported context flags, deny. Inspect all supported compound-command segments; no early allow after the first harmless segment. Deny aliases that could conceal Git mutation, nested shell/interpreter/eval/source execution, substitution, dynamic operands and unsupported syntax when destructive intent is visible or a registered shell wrapper would otherwise hide its body. Do not execute commands to discover their expansion. Read configured Git aliases with read-only argv if needed; deny unresolved aliases rather than running them.

Collect canonical primary/common-dir identity, registered worktrees, exact branch tips, ownership records and full porcelain status including ignored content before deletions. A managed-looking path alone does not establish ownership. Resolve provider from repository remote plus existing metadata, never branch text alone. Use existing gh/glab read-only CLI surfaces through the local runner; keep all delivery/provider adapter files untouched. Query all relevant PR/MR matches with pagination or return unknown on incomplete enumeration. Match host/project, source repository, branch and head SHA; linked terminal records cannot authorize deletion after new local commits. Missing CLI/auth/network, ambiguous origin/fork, unsupported schema or no matching record means unknown, never merged. A current open record overrides any old terminal record and Git ancestry. Normalize GitHub OPEN/CLOSED/MERGED and GitLab opened/closed/merged without conflating unknown, locked or draft with terminal. Derive CLI argv from installed help/current repository conventions and pin it in offline contract tests; do not assume a GitLab adapter exists. No live provider writes are needed.

Register the Python hook separately for Bash and actual Codex shell tool names supported by installer matcher conventions, including exec_command where the host supplies it; document exact registered names. Handle script suffix/interpreter in hook_settings rather than invoking Python as bash. Resolve installed library relative to the hook in .codex or .claude. Extend the installed registered-hooks test to exercise allow and deny from nested directories with spaces/non-ASCII and Windows status propagation, while retaining existing advisory scratchpad/dispatch assertions. Keep --no-hooks and user hook settings behavior intact. No broad hook disabling, .ai/hooks/worktree-guard.sh edits, provider adapter changes or benchmark harness. Coordinator-authorized documentation amendment: qualify the Hooks and validation paragraph in .ai/RULES.md and correct only the stale advisory dispatch module docstring in .ai/runtime/lib/worktrees.py; no runtime logic, worktree creation/base/root/integration safeguards or scratchpad policy changes.
  </action>
  <verify>
    <automated>python -m unittest discover -s tests -p test_destructive_guard.py -v</automated>
    <fails_when>non-zero exit, Ran 0 tests, an unexpected skip of the guard matrix, or missing intended named RED assertion before GREEN</fails_when>
    <automated>python -m unittest discover -s tests -p test_install.py -k registered_hooks -v</automated>
    <fails_when>non-zero exit, Ran 0 tests, lost advisory scratchpad coverage, or installed denial failing to propagate through the launcher</fails_when>
  </verify>
  <acceptance_criteria>
    - Hook registration reaches the new Python entrypoint on both supported hosts and leaves existing worktree guard advisory.
    - Offline attack cases refuse before mutation; false-positive cases permit without unnecessary provider dependency.
    - Source/installed path tests exercise the real stdin entrypoint and exit/JSON contract, not only a policy helper.
    - The guard slice includes documented bounded coverage, observed RED and GREEN, exact commit IDs and a truthful interim SUMMARY.
  </acceptance_criteria>
  <done>Commit the tested GUARD slice and docs/maintenance/issue87/GUARDS-SUMMARY.md; return it to the coordinator. Do not implement CLEANUP in this checkout.</done>
</task>


</tasks>

## Shared interfaces and child ownership

Export command_segments(payload) as an immutable result containing supported/unsupported status, reason_code and ordered segments with canonical effective cwd and literal argv. It never evaluates a shell. Planning-integrity may reuse it only after this guard commit is integrated; it must refuse unsupported git-commit syntax rather than infer safety. Keep this parser interface separate from destructive verdicts so a non-destructive commit can still be inspected. The coordinator owns any later planning-integrity hook registration in .ai/install.py.

CLEANUP-PLAN.md depends_on guards and takes sequential ownership of .ai/hooks/destructive-git-guard.py, .ai/runtime/lib/destructive_guard.py, tests/test_destructive_guard.py, .ai/hooks/README.md and .ai/references/destructive-operations.md. It adds the cleanup command, skill, workflow and command catalog row; no simultaneous writers. Guard approval schema is schema_version, canonical repo/common-dir, snapshot_id, exact operation list and actual human approval text/reference; ordinary shell backup commands cannot claim approval from command text or environment. Only the child implements preview/apply and transient consumption receipts.

## Supported command grammar and attack matrix

The hook is a bounded preflight control, not an arbitrary-shell sandbox. Parse command strings as data and never execute expansion. Support literal argv with balanced single/double quotes, ordinary backslash escapes, leading literal environment assignments, literal cd followed by a supported separator, Git -C, executable paths ending in git/git.exe, and compound segments separated by newline, ;, &&, || or pipelines. Track literal cwd per segment and inspect every potentially executed branch conservatively. Recognize POSIX rm/rmdir and PowerShell Remove-Item/rm/ri/rmdir with literal targets, including -LiteralPath, when assessing backup removal. Do not claim full PowerShell, cmd.exe, Bash AST or interpreter evaluation.

| Family | Required deny cases | Required allow/precision cases |
|---|---|---|
| Branch switch | Primary checkout/switch, new/orphan/detached branch, Git -C pointing at primary, quoted executable/branch, compound later segment | Linked-worktree normal switch; primary checkout -- path and checkout REF -- path; git show/status/diff |
| Branch deletion | branch -d/-D/--delete, clustered destructive flags, multiple branches, push --delete or empty-source refspec, update-ref -d refs/heads/X, branch rename over an owned target | branch --list, branch -a, read-only show-ref; unsupported mutation variants deny rather than being guessed safe |
| Worktree deletion | worktree remove including --force, path containing spaces, absolute/relative/.. paths, primary/current target, unknown ownership | worktree list; worktree add is not deletion; no permission to delete from managed-looking directory alone |
| Context/wrappers | Alias-expanded Git mutation, env wrapper, literal cd chains, effective -C changes, unsupported Git context flag on mutation | Quoted text containing git switch inside echo/printf is data, not an invocation |
| Dynamic shell | Nested bash/sh/pwsh/powershell/cmd command bodies, eval/source, command substitution, backticks, variable targets, functions/loops/heredocs containing relevant mutations | Explicit unsupported-syntax reason; do not assert that opaque Python/Node/file contents are inspected; document that external scripts can exceed coverage |
| Backup removal | rm -rf, rm --, Remove-Item -Recurse -Force/-LiteralPath, wildcard/traversal/symlink aliases into protected backup paths, broad parent directory removal | Read/list backup; normal unrelated literal file removal; exact approved structured apply only for protected backup deletion |
| Provider evidence | OPEN/opened, draft-open, mixed terminal+open, timeout/auth/missing CLI, malformed JSON, empty or incomplete pages, mismatched host/fork/head | Both providers' complete matching terminal records; terminal status remains separate from integration/unique-commit checks |
| Approval/state | Forged broad override, list insertion/omission/reorder ambiguity, different repo, tip movement, reopen, new dirty/ignored data, backup digest change, lock contention, second use | Deterministically ordered exact approved snapshot; absence of deletion list never means approve everything |

For unsupported destructive syntax the decision is deny-with-guidance to use explicit literal argv or the cleanup entrypoint. For genuinely unrelated unsupported code, do not claim enforcement of hidden operations: document the limit and leave host permissions/instructions in force. Recognized wrappers that hide a shell body are denied rather than silently allowed. Git plumbing and remote deletion forms recognized above must refuse conservatively when no complete evidence/ownership rule applies; this scope does not authorize implementing remote cleanup.

## Multi-source coverage audit

| Source | ID | Outcome/constraint | Coverage |
|---|---|---|---|
| GOAL | issue87 maintenance context | Guard destructive operations and make cleanup deliberate | GUARD + CLEANUP |
| REQ | ISSUE87-GUARD / I87-A1 | Primary switch, open PR/MR and backup deletion refusal | GUARD policy + CLEANUP approval |
| REQ | ISSUE87-CLEANUP / I87-A2 | Eligible-only preview, exact approval, preservation and final state | CLEANUP |
| REQ | ISSUE87-RED / I87-A3 | Bypass/false-positive matrix and failing tests first | Both tasks' RED/GREEN evidence |
| RESEARCH | supplied scout evidence, checked at input revision | Existing cleanup guards/force paths; installer and README ownership | New entrypoint/library; no edits to legacy runtime |
| CONTEXT | Decisions 1, 2 | Preserve advisory guard and existing scoped authorization | GUARD tests; exact new destructive consent only |
| CONTEXT | Decisions 3, 5, 6 | Preserve providers, narrow disjoint scope, real stack dependency | Offline gh/glab evidence; exact paths; guard then cleanup |
| CONTEXT | Acceptance 4-7 / Decision 4 | Record validation, upstream comparison, progress and phase security tracking | Other coordinator-owned plans; excluded from this assigned component |

No adopting-project ROADMAP goal or requirement is claimed: those files remain unfilled source skeletons. No separate RESEARCH artifact was assigned; the cited scout/source evidence is the research input. No acceptance in this component is silently deferred.

<threat_model>
## Trust Boundaries

| Boundary | Description |
|---|---|
| Host payload to command parser | Untrusted shell strings, quoting, cwd and wrappers; bounded parsing never evaluates them |
| Repository and provider evidence to deletion | Ownership, identity, terminal state and pinned local tips are required; failures preserve work |
| Human approval to apply | Exact reviewed operations bind authority; file content alone cannot prove human provenance |
| Preview to mutation | State can change; lock, reinspection and expected-OID deletion reduce races; external processes need not honor this lock |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|---|---|---|---|---|---|
| I87-G-T1; https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t1 | Tampering | destructive command parsing | high | mitigate | GUARD bounded grammar, conservative unknown handling and offline attack matrix; do not claim arbitrary-shell protection |
| I87-G-T2; https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t2 | Spoofing | provider/ownership/approval evidence | high | mitigate | Exact project/source/head matching, real human instruction recorded by workflow, no broad overrides, unknown preserves |
| I87-G-T3; https://github.com/Tasaddar12/ai-engineering-template/issues/95#i87-g-t3 | Tampering | cleanup preview/apply state | high | mitigate | Revalidate, shared cleanup lock, expected ref OID, non-force worktree remove, backup digest and truthful partial results |

These are findings about the changed guard/deletion trust boundaries, not published exploit instructions. Coordinator owns canonical issue identity and safe tracking. Keep Pending until actual matching issue readback; never invent a URL or close a risk from a merge. A residual concurrent external filesystem race and opaque-script coverage limit must remain documented and independently assessed.
</threat_model>

<verification>
Before declaring implementation complete:
- Run both frontmatter focused unittest commands; record actual counts, pass/skip/fail and tested revision.
- Inspect history: registered-hook intended RED precedes GUARD GREEN. Fixture/import errors cannot count as RED.
- Run existing worktree-guard Bash suite when Git Bash is available to verify unchanged advisory behavior; report inability to run explicitly, never a pass.
- Inspect the actual Python launcher from both host namespaces; registered-hooks tests exercise Windows exit propagation where running on Windows.
- Independent review must assess parser coverage against the matrix, approval/provenance limits, exact ownership, provider identity and closed-unmerged preservation.
- Verify no edits to .ai/runtime/phase.py, worktrees.py runtime logic, .ai/RULES.md outside the Hooks and validation prose, provider adapters, adoption records, shell line-ending rules or unrelated source. The coordinator-authorized worktrees.py module docstring correction is documentation only.
</verification>

<success_criteria>
- The guard slice and its implementation SUMMARY are committed, with the exact tip available as the cleanup child's base.
- Every assigned I87 acceptance outcome has behavior evidence and all required focused checks pass.
- Recognized unknown/open/dirty/unowned deletion is refused; ordinary shell backup removal is denied pending the exact approved cleanup route.
- Documentation states actual supported forms, limitations and legacy-route differences; PR86 remains advisory.
- No real destructive cleanup, publication, issue closure or merge is performed by the worker.
</success_criteria>

<output>
Implementation worker creates docs/maintenance/issue87/GUARDS-SUMMARY.md, recording the guard commit IDs, actual checks, RED/GREEN evidence, acceptance/documentation coverage, Threat Outcomes and remaining limitations. The coordinator integrates, updates CONTEXT, reconciles canonical threat links and publishes authorized drafts. If a native phase_run facade is later desired, return its required interface to the coordinator; it is not part of this plan or a prerequisite for the standalone cleanup route.
</output>
