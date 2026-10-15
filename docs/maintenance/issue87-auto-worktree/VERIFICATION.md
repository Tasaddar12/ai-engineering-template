---
phase: maintenance-issue87-auto-worktree
verified: "2026-10-15T22:57:20Z"
status: gaps_found
score: "3/8 acceptance outcomes verified at their declared evidence boundary"
revision: ef325b62c0df6efcf603d72cfae55b8269a3052e
behavior_unverified: 2
overrides_applied: 0
issue_refs: [87, 98]
---

# Issue 87 verification

Goal: move the same existing agent into an isolated worktree before source
mutation, with subsequent tools using the destination by default.

Independent verifier (gpt-6.1-sol/high) returned gaps_found for the exact clean
revision above after all specialists and local checks joined. This record
preserves its complete acceptance decision, findings, execution evidence and
required follow-up. The verifier performed no tests, writes, commits, provider
operations or child dispatches. [Joined review](REVIEW-01.md) preserves source,
integration and documentation causal evidence and exact source locations.

The conditional Claude implementation is substantive and connected. Three
concrete source defects and one false documentation claim prevent acceptance.
Live same-agent movement remains independently unverified.

## Acceptance

| ID | Verdict | Evidence and limit |
|---|---|---|
| AW-01 | UNCERTAIN: live behavior unverified | Source denial/native continuation prewrite.py:491-554 and callback:557-593 exist. Tests:75-127 explicitly simulate rebinding. CR-01 also breaks reliable Windows provider output. |
| AW-02 | VERIFIED: conditional contract | Protocol:12-26 gates actual tool/schema/role/policy/trust; :61-83 preserves existing-path approval. Installer adds EnterWorktree only to designated Claude roles. Refusal tests:356-372. This is instruction-contract evidence, not live model compliance. |
| AW-03 | FAILED | Narrow notes exist, but prewrite.py:464-477 grants external temp-note exemption after failed repository discovery. |
| AW-04 | UNCERTAIN: live behavior unverified | Real Git dirty/index snapshots and removal preservation tests:314-354,402-426; host transfer/lifecycle unobserved. |
| AW-05 | FAILED | Cancellation/fresh reconstruction/replay controls exist; failed-discovery target bypass violates confinement. Simulated edit does not establish live sequence. |
| AW-06 | FAILED | Installed exports/hooks/callback/adoption exist; four workflows cd before bootstrap, conflicting with primary-root requirement:304-307. |
| AW-07 | VERIFIED: bounded runtime/provider | Ticket validation, OS locking, collision/refusal/preservation:123-238,322-399,557-610; joined deterministic cases pass. Live behavior separate. |
| AW-08 | VERIFIED: evidence discipline | Fresh genuine RED/GREEN, independent RED review and specialists joined; missing/cancelled evidence is reported honestly. |

Three outcomes verified at their bounded layer; two behavior-unverified and
three demonstrated source failures. Documentation has one additional failure.

## Integration

Installer registers one editing group, advisory first/source decision second.
The source handler cancels the original mutation and emits a request without
precreating. Standing instructions require the same caller to gate/invoke its
native tool. WorktreeCreate validates reserved identity and creates at the pinned
base. Git-only confirmation adopts a new unit or validates an existing session;
instructions require fresh reads and one rebuilt edit.

`host_binding_verified:false` (`prewrite.py:381-399`) accurately separates Git
confirmation from host identity, permissions and loaded context. The fixture's
cwd, loaded_root and writable_root are test-owned simulated state. Journals
retain request/unit/identity metadata, not mutation bodies or transcripts.

Existing ordinary phase/quick tests preserve historical base, accumulated HEAD
and ownership without another checkout or fabricated native journal (:482-551),
but manually bootstrap from primary and miss CR-02. The integration-checker
independently confirmed that connection failure. No other source connection
failure was identified. Original-six overlapping regions showed no obvious
semantic incompatibility; actual combined-97 execution remains unverified.

| Connection | Verdict |
|---|---|
| Installer to hooks/roles/standing protocol | WIRED; installed fixture evidence |
| Source cancellation to same-caller native instructions | WIRED; live compliance unverified |
| Native callback to location provider | WIRED; CR-01 breaks legacy-encoding output |
| Native/default context to Git confirmation/adoption | WIRED; host binding deliberately not certified |
| Six workflow entry consumers | PARTIAL; four initial shell routes precede native gate |
| Git discovery to external-note classification | FAILED on indeterminate discovery |

## Documentation

The doc-verifier initially counted 41 checked claims and four live conditions
unverifiable. Its bounded follow-up supersedes the clean conclusion for README.

| Required document | Verdict |
|---|---|
| .ai/hooks/README.md | FAILED: no-Python-adapter statement; other checked claims supported |
| .ai/references/worktree-sessions.md | Contract/evidence limits supported; source ordering must be repaired |
| .ai/runtime/README.md | Interfaces/Git-only confirmation supported |
| .ai/RULES.md: Hooks and validation | Advisory/blocking, gates, notes and simulation/live boundaries supported |

The operative protocol rejects shell cd, argument retargeting, prepared roots,
cancellation alone and child/fork substitution. Later-turn/live requirements
remain open. Do not change valid requirements to excuse the source bug.

## Findings and required repair

### CR-01: BLOCKER — locale-dependent native provider output

Creation/journal success occurs at prewrite.py:587-593, then line640 prints the
destination through stdout's process codec. Legacy Windows encoding can emit
wrong bytes or fail on Unicode. Fixtures force UTF-8 and mask this boundary.
Emit exactly one explicit UTF-8 destination line and cover legacy stdout plus
an unrepresentable path. Preserve created state; never blindly retry creation.
The generic deferred Windows locale/session helper does not excuse this new
adapter defect. Native input and Git reads already use explicit UTF-8.

### CR-02: BLOCKER — native bootstrap follows session directory routing

Earlier cd/later native pairs: discuss165/224-234; plan81/115-124;
execute130/166-175; verify90/120-129. Following initial cd reaches a linked
checkout while workflow_request:307 requires primary. String-only consumer
checks and manually ordered fixture bootstrap miss this defect. Gate and enter
natively before first session cd/init, retain ordinary consumer behavior, and
add ordering-sensitive coverage for all four workflows.

### CR-03: BLOCKER — failed discovery permits an external temp source file

prewrite.py:464-465 interprets every failed rev-parse as repository=None; :476-477
then grants the temp-note exemption. A real external repository with invalid
config or rejected ownership can pass. Refuse indeterminate discovery; cover
malformed-config real external Git while retaining legitimate nongit temp notes.

### DOC-01: required adapter wording correction

README:88-90 contradicts source-prewrite.sh:16 and prewrite.py:631-644. Describe
registered shell scripts and their Python decision adapter precisely.

## Checks and test quality

No checks were rerun by the verifier. Joined receipts apply only to their named
revision/environment; passing exercised cases do not override direct defects.

| Receipt | Result |
|---|---|
| Frozen ef325b6 workflow links | 4 passed, 1.355s |
| Frozen ef325b6 agent sources | 16 passed, .102s |
| Integrated06b1b25 native tracer | 9 passed,75.258s; host SIMULATED |
| Integrated06b1b25 prewrite | 23 passed,46.489s; one Windows symlink privilege skip |
| Integrated06b1b25 migration | 18 passed,23.839s |
| Source06 Ubuntu CI38819567669/job116712553799 | 671 Python,208.881s,15 skips; Bash357 passed |
| Source06 Windows CI | Pending in supplied packet; no final result claimed |
| Frozenef CI38819917606 | Cancelled after required repairs identified; not passing evidence |

Author2b receipts: native9,prewrite23,installer41,updater66,session60,agent16,
links4, with documented skips; Bash source/location/advisory12/25/60. Real Git,
installed denial, dirty preservation and one rebuilt fixture edit are meaningful.
Fixture-supplied native rebinding/later-turn persistence are not live proof.
Missing coverage: legacy output codec, complete phase initialization ordering,
and failed external repository discovery. No separate probe ran (read-only
assignment prohibited tests); joined receipts supply bounded execution evidence.

## Requirements and decision coverage

All six must-have artifacts are substantive and have consumers; existence does
not close defects. ISSUE87 acceptance belongs to maintenance CONTEXT/PLAN.
Adoption PROJECT/STATE/ROADMAP/REQUIREMENTS remain unfilled and are not substituted
for this goal. Direct main diff confirmed advisory script byte-unchanged and no
.planning changes. No acceptance override applied.

Conditional Claude, source/note distinction, preservation intent, precise Codex
controller limitation and simulation/live separation are implemented as directed.
Original six drafts/provider work/infrastructure/real cleanup are excluded.
Threats01/02/03 remain OPEN per coordinator evidence; verifier made no provider
readback. Draft/no-merge/open-issue/frozen-head obligations are coordinator-owned.

## Live validation required

The executor has no callable native entry tool. This does not invalidate writing
the conditional Claude implementation; it prevents claiming actual same-agent
fulfillment. Codex's precise current-template unsupported controller result is
not a product-wide impossibility claim.

On an eligible live Claude host, after concrete repairs/checks/reviews:

1. Record actual version/schema, trust/policy, session/actor identity and dirty
   inventory; trigger source denial and prove the old mutation did not execute.
2. The same existing caller invokes native entry. Observe completion and default
   destination cwd/root, permissions and loaded context without overrides,
   including a later turn.
3. Freshly read and rebuild once; verify destination and account for all initial
   staged, unstaged, untracked and ignored data.
4. Exercise existing-path approval, denied/uncertain outcomes and lifecycle
   preservation. Every initial change must remain recoverable, without duplicate
   creation, replay or unauthorized removal.

## Outcome

Repair three source defects and one false documentation sentence, obtain affected
GREEN and fresh independent reconciliation at the resulting revision. Keep the
conditional route available for correction, PR97 draft and issues87/98 OPEN.
Neither simulated success nor this executor's missing native tool establishes
live goal completion. No merge or completion claim is supported.
