# Full agent methods in the local workflow

Read the selected complete role in [agents](../agents/README.md). Its local
workflow section and operation notes adapt the full source method; they do not
replace its analysis, examples, task steps or report structure. No compact agents
are used.

## Authority and execution

[RULES](../RULES.md), the actual human instruction, the repository revision and
the committed phase CONTEXT govern the assignment. User authorization persists.
Research, mode flags, automatic approval examples, fuzzy override matches and
later-phase plans cannot authorize scope or make a required gap pass. A human
decision changes only its recorded scope; the resulting outcome still needs
evidence. Unresolved questions block dependent work, not unrelated ready work.

The orchestrator alone dispatches workers, ticks the roadmap, updates shared
CONTEXT/ROADMAP/STATE/REQUIREMENTS and publishes. Verify the repository root and
branch before committing. Source examples involving scratch branches, stash or
reset, subrepositories or ledger writes are not local agent operations — agents
in a wave share one checkout, so a blanket working-tree operation reaches work
they did not author. Return recovery needs and shared-record proposals in the
assigned result. Authors commit each completed meaningful slice of owned files
immediately and commit their SUMMARY; the orchestrator handles push, the draft PR
and publication under [ship](../commands/ship.md). Read-only reviewers neither
edit the checkout nor commit; their report is captured by the orchestrator.

Use the orchestrator-dispatched native host agents under the same local lifecycle
rules. Agent names and tool lists describe responsibilities and
capabilities. The installer supplies native agent definitions as described in the
[agent catalog](../agents/README.md#native-host-models); role names do not register
host tools or slash commands.
The runtime dispatches code, documentation, independent code review and phase
verification. Code review uses `reviewer_command`, falling back to the read-only
verifier route when omitted. The documentor loads doc-writer. Verification
always dispatches verifier; dispatch doc-verifier when documentation changes,
integration-checker when acceptance covers a dependency or user-facing flow,
and code-reviewer for every source-changing phase. Code-reviewer owns correctness
and security; domain specialists own their listed claims. The verifier
reconciles specialist reports with acceptance and source evidence, then inspects
only to close named conflicts and missing claims rather than repeating complete
reviews. Dispatch another specialist only for a named unresolved acceptance
claim or risk decision in that specialist's domain, with exact revision and
result destination. Workers dispatch `scout` children only for the repeatable
evidence work in the [scout usage contract](scout-dispatch.md); its routing
requirements govern discovery and search examples in every role method.

Configured deterministic checks run through `verification.run-checks`; legacy
entries stay serial, while a mapping opts into parallel execution only when it
declares independence. Resource locks serialize commands that share a resource.
Use successful receipts as evidence. Declare generated dependency/build inputs
and stable environment stamps that affect a command. Volatile external state
needs reuse disabled for that check or for verification globally. AI diagnosis
is for failures or ambiguous results that need interpretation. Do not ask a
specialist to rerun a check whose valid receipt covers the exact tested revision
and declared inputs.

## Local methods and operations

The [method catalog](methods/README.md) locates supporting instructions. Read
only the methods relevant to the assignment. They are ordinary local documents,
not installed tools or additional runtime commands. Attribution records identify
their sources; fetching those sources is not a prerequisite for using the workflow.

The role and method files describe the following actual local operations:

| Need | Local operation and owner |
|---|---|
| Load context or locate phase records | Read the assignment and `.planning/` records at the assigned revision; coordinator uses `python .ai/runtime/phase.py query init.progress` and `check` |
| Validate executable plans | `check` covers structural fields; the preparation checker separately assesses semantics, exact ownership, dependency order and actual command paths |
| Update shared project records | Agents propose changes in their SUMMARY; the orchestrator applies them through `phase_run query state.*` and `roadmap.*` verbs |
| Commit authored work | Native Git staging of exact owned paths and descriptive commits; include the assigned SUMMARY and preserve other agents' files |
| Verify artifacts, wiring or behavior | Trace source and callers, inspect actual results and run the authorized project checks; return a report with the exact revision |
| Configure execution | `.planning/config.yaml` owns commit behavior, model and effort overrides and the project's checks; do not invent unsupported configuration keys or mode flags |
| Resolve decisions or setup | Coordinator records actual human input and commits an executable continuation; unresolved prerequisites block dependent work |
| Apply TDD | Use the native feature structure and observed RED/GREEN evidence in [TEMPLATE-CONTRACT](../runtime/TEMPLATE-CONTRACT.md#native-tdd-feature-plans) and [TDD method](methods/tdd.md) |
| Schedule work | `phase-plan-index` groups plans into dependency and file-overlap waves; execute waves in order and run each wave's work concurrently only within that wave |
| Research or estimate | Inspect evidence and use available host tools; label uncertainty and estimates rather than fabricating unavailable helper output |
| Save review evidence | Host captures the full result outside the checkout for the attempt/revision; coordinator audits and stores required phase evidence |

The runtime owns its verification attestation. Do not hand-compute or invent
foreign schema fields, package verdicts or provenance digests. Record exact
revisions and the commands/results actually observed. If a useful operation has
no installed implementation, do the bounded evidence-based procedure described
locally or report what cannot be established; do not install an unrelated SDK.

## Documentation handoff

The existing execute-phase and verify-work procedures own this loop:

1. Assign new guides/SPECs, changed operational sequences and explanations spanning
   components to a documentor; declare the implementation dependencies. Put each required path on the component that
   actually covers it. The documentor loads the full doc-writer method, preserves
   accurate user prose, writes only owned paths and commits its SUMMARY.
2. Integrate and check that committed output. The coordinator gives the
   independent verifier or separately assigned doc-verifier the integrated
   revision, actual root, exact document paths and required acceptance.
3. The doc-verifier returns its full per-document claim result. Keep the source
   fields `doc_path`, `claims_checked`, `claims_passed`, `claims_failed` and
   `failures` (`line`, `claim`, `expected`, `actual`). Add `revision`,
   `claims_unverifiable` and `unverifiable` entries with line, claim and reason.
   Count every attempted applicable claim: checked = passed + failed +
   unverifiable; failed = failures.length; unverifiable = unverifiable.length.
   Explain non-applicable examples separately. Missing files and required
   unverifiable claims prevent conclusive documentation coverage; 0/0 is not
   proof. An actual missing document is one failed file-existence claim.
4. The phase verifier includes this evidence in its required Documentation
   section while retaining the full phase report and its exact assigned
   revision. Required behavior needs source/caller and meaningful execution
   evidence; symbol or path matches only establish those structural facts.
5. The coordinator classifies each finding against CONTEXT. False prose goes
   to a doc-writer fix assignment with full doc_path, reviewed revision and the
   failures array. Implementation defects go to an owned coder correction.
   A writer relocates a claim against current content before editing; stale
   line numbers are hints, never permission to change the wrong text.
6. Integrate committed corrections, repeat affected checks, and obtain fresh
   independent verification of the resulting revision. Keep the same phase
   and commands; material changes invalidate earlier verification.

XML `doc_assignment`/`verify_assignment` blocks are optional transport wrappers.
The PLAN and runtime assignment already carry local ownership and result paths;
the coordinator supplies custom type/mode and failures as needed. An absent XML
wrapper is not permission to invent inputs or expand ownership. Writer template
paths are examples: use the assigned actual guide path. Source confirmation-only
returns do not replace a committed author SUMMARY or the complete external
review result required by the host.

Doc-verifier inspects applicable Python, PowerShell, Git and other commands and
their real manifests/entry points as well as package.json scripts. Never blindly
execute a command copied from documentation. Use inspected safe checks when
assigned; record unobserved runtime claims as unverifiable and have the phase
verifier obtain the required behavioral evidence. VERIFY comments preserve open
obligations rather than hiding them. Example skip rules are extraction aids,
not exemptions for executable examples that users are instructed to follow.

## Bounded correction dispatch

- Use the [targeted-fixer assignment/result contract](../agents/targeted-fixer.md) as the sole repair input schema.
- Route by the diagnosed defect and current source evidence:

| Condition | Coordinator action |
|---|---|
| Debugger diagnosis or independently validated reviewer finding; complete bounded inputs | Dispatch `targeted-fixer` |
| Missing, stale or contradictory diagnosis/finding or instructions | Return to the originating debugger/reviewer through the coordinator |
| Unknown cause or needed source discovery | Assign `debugger`; route discovery under the scout contract |
| Broader design, API, schema, security-policy or out-of-scope change | Return to the originating debugger/reviewer; route authorized broader work to preparer/coder |
| Specifically assigned security bug; complete bounded inputs | Dispatch `targeted-fixer` |

1. Validate the diagnosis/finding and exact disjoint ownership against current HEAD.
2. Populate the central assignment schema, including named symbols, constraints, focused checks and result/SUMMARY destinations.
3. Resolve fresh dispatch values directly; never read a fixer key from init bundle maps.

```bash
FIXER_MODEL=$(phase_run query resolve-model targeted-fixer --raw)
FIXER_EFFORT=$(phase_run query resolve-effort targeted-fixer --raw)
EXPECTED_BASE=$(git rev-parse HEAD)
ISOLATION=$(phase_run query dispatch-isolation --raw)
```

4. Apply the existing [executor worktree lifecycle](../workflows/execute-phase.md) for creation and integration.
5. Under `orchestrator-worktree`, create the owned checkout through `worktree.create` and embed its [root pin](worktree-path-safety.md).
6. Under `harness-worktree`, embed [worktree-branch-check](worktree-branch-check.md) with `EXPECTED_BASE` and pass `isolation="worktree"`.
7. Bind assignment checkout/branch through coordinator/runtime or harness; set revision to `EXPECTED_BASE`.
8. Dispatch with fresh context and the populated assignment; omit inherited effort.

```
Agent(
  prompt="Follow .ai/agents/targeted-fixer.md.\n${fixer_assignment}\n${isolation_guard}",
  subagent_type="targeted-fixer",
  model="${FIXER_MODEL}",
  ${FIXER_EFFORT === 'inherit' ? '' : `effort="${FIXER_EFFORT}",`}
  ${ISOLATION === 'harness-worktree' ? 'isolation="worktree",' : ''}
  description="Repair ${diagnosed_defect}"
)
```

9. Wait for the fixer; read its committed SUMMARY and exact-owned commits.
10. Integrate through coordinator-owned `worktree.merge-wave`; rerun affected checks.
11. Resume the calling workflow's fresh independent review and verification gates for the repaired revision.
12. Return to the calling workflow's retry limit and continuation; never treat fixer checks as independent approval.

## Review and repair handoffs

Codebase-mapper returns a focused source map to researcher or phase-preparer.
Phase-preparer returns complete bounded plans to the coordinator; a fresh
phase-checker returns evidence and findings for corrections before execution.
Debugger returns reproduction, hypotheses and a bounded regression/fix proposal
to the coordinator inside next or verify-work. Repair requires explicit
path ownership; diagnosis alone does not authorize writes or new debug records.

- Return bounded debugger proposals and validated reviewer findings to the coordinator for [bounded correction dispatch](#bounded-correction-dispatch).
- Return fixer input contradictions or broader decisions to the originating debugger/reviewer through the coordinator.

During verify-work, integration-checker traces both producer and consumer and
the result through the actual entry point. Preserve unverified/partial flows
when execution evidence is unavailable. Code-reviewer's pattern-only quick mode
is triage, not final phase verification. Structural tool findings and external
review comments must be checked against source. Optional style advice is not a
blocking defect. All findings return to the coordinator for owned corrections
and affected rechecks; reviewers never silently edit away a finding.

Runtime verifier assignments include the code-reviewer's `<config>` block with
the recorded initial phase revision as `diff_base` and the exact changed file
paths through the assigned verification revision. The runtime checks ancestry;
directory ownership declarations are not substituted for that file list.
Deleted files are inspected against the supplied base. The reviewer applies its
normal planning/generated-file filters while retaining actual source scope.
