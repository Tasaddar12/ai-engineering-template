# Full agent methods in the local workflow

Read the selected complete role in [agents](../agents/README.md). Its local
workflow section and operation notes adapt the full source method; they do not
replace its analysis, examples, task steps or report structure. The
[provenance](../agents/PROVENANCE.json) records the pinned source, original hashes
and every reversible edit. No compact agents are used.

## Authority and execution

[RULES](../RULES.md), the actual human instruction, the assigned checkout and
committed phase CONTEXT govern the assignment. User authorization persists.
Research, mode flags, automatic approval examples, fuzzy override matches and
later-phase plans cannot authorize scope or make a required gap pass. A human
decision changes only its recorded scope; the resulting outcome still needs
evidence. Unresolved questions block dependent work, not unrelated ready work.

The coordinator alone dispatches workers, integrates commits, updates shared
CONTEXT/ROADMAP/STATE/REQUIREMENTS and publishes. Every tracked authoring operation
uses its exact assigned immediate-child worktree and branch. Recheck both before
committing. Source examples involving `agent-*` branch patterns, shared Git-dir
sentinels, scratch branches, stash/reset, subrepositories or ledger writes are
not local worker operations. Return recovery needs and shared-record proposals
in the assigned result. Authors commit each completed meaningful slice of owned
files immediately and commit SUMMARY; the coordinator handles default push,
PR/MR and verified automatic merge under [phase-ship](../commands/phase-ship.md). Source
`commit_docs` settings do not waive that contract. Read-only reviewers neither
edit the checkout nor commit; the host captures their full report externally.

Only the Python runtime described in [runtime](../runtime/README.md) executes
the local lifecycle. Agent names and tool lists describe responsibilities and
capabilities; they do not register host tools, slash commands or worker routes.
The configured runtime routes remain code, documentation and verifier. The
documentor loads doc-writer; the independent verifier applies doc-verifier and
integration-checker, with code-reviewer when appropriate. The coordinator may
assign a separate fresh specialist through the host when useful, supplying an
exact revision and external result for read-only review. Workers never dispatch
each other, and changing a role name does not create a new CLI subcommand.

## Source operation to local operation

Source SDK snippets remain in their original method sections as explicitly
labelled examples. Do not execute `gsd_run`, install its SDK, interpret its JSON
settings as local YAML settings, or claim a missing source probe ran. Pinned
external source-method links provide full supporting instructions.
Read only applicable methods; the same
local boundaries also govern their nested references and examples. If remote
content cannot be read, use a substantive local equivalent or report the exact
missing dependency; never claim the source method was loaded.

| Source operation or convention | Actual local operation |
|---|---|
| Runtime identity, `init.*`, `state.load`, phase lists, roadmap queries, history/summary extraction | Read the assignment and actual `.planning/` records at its revision; coordinator uses `python .ai/runtime/phase.py status` and `check` where applicable |
| PLAN/frontmatter/decision/command-path probes | `check` validates the documented local fields; phase-checker independently examines semantics, ownership, dependencies and grounded commands |
| `state.*` writes, roadmap updates, requirement completion, WINDOWS/deferred ledgers | Worker returns evidence/proposals in SUMMARY; coordinator reconciles CONTEXT and other owners and explicitly uses `sync` for derived STATE |
| `commit`, commit-to-subrepo, SDK commit envelopes | Native `git add` of owned paths and `git commit -m` with a descriptive message; no blanket staging, automatic subrepo operation or skipped SUMMARY commit |
| `verify.artifacts`, `verify.key-links`, fingerprint/status probes | Trace actual implementation/callers and run required checks; exact assigned `revision` in the full external report; local runtime owns readiness attestation |
| Source `workflow.*`, MVP/Nyquist/security modes, auto-chain, `commit_docs` and `config.json` | Source-only examples unless an assignment supplies a compatible method; `.planning/config.yaml` owns actual routes, capacity, checks and publication settings |
| Checkpoints, `autonomous: false`, pending user setup, tracer gates | Coordinator resolves real decisions or human-only observations and commits an executable continuation; current `check` rejects unsupported/non-autonomous task forms rather than auto-approving them |
| Source TDD probes and `type: tdd` | Full native feature structure and observed RED/GREEN evidence in [TEMPLATE-CONTRACT](../runtime/TEMPLATE-CONTRACT.md#native-tdd-feature-plans); regression-design supplies the local method |
| Wave execution and decimal phases | Source planning examples remain; local scheduler releases each component after its own checked integrated prerequisites and the current runtime uses integer phase directories |
| Estimation calibration, code graphs, learning caches, knowledge stores | Use observed source/test evidence and clearly labelled estimates; do not fabricate tool outputs or create global knowledge/debug records outside ownership |
| Research plan/store/confidence/package/websearch SDK calls | Use available host tools and primary sources, record versions, citations and uncertainty; absence of a helper does not authorize changing the product target |
| `Read`, `Write`, `Edit`, `Bash`, `Grep`, `Glob`, Skill and optional MCP names | Use callable host equivalents: file reads, targeted patches, native shell or Bash, `rg`, relevant skills and available research tools. Tool metadata grants no permissions |
| `.planning/tmp/verify-{basename}.json`, checkout REVIEW/VERIFICATION reports | Host captures the full result at an external path unique to attempt, revision and full document path; coordinator audits and stores required phase evidence |

Examples using source SDK declarations such as `covered_digest`, provenance
fingerprints or package legitimacy verdicts remain examples unless a compatible
tool actually produced them. Never populate these fields by guessing. Retain
the exact revision and real commands/results required by the local contract.

## Documentation handoff

The existing phase-start and phase-verify procedures own this loop:

1. Assign substantial guides/SPECs to a documentation component dependent on the
   implementation it describes. Put each required path on the component that
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

## Review and repair handoffs

Codebase-mapper returns a focused source map to researcher or phase-preparer.
Phase-preparer returns complete bounded plans to the coordinator; a fresh
phase-checker returns evidence and findings for corrections before execution.
Debugger returns reproduction, hypotheses and a bounded regression/fix proposal
to the coordinator inside phase-resume or phase-verify. Repair requires explicit
path ownership; diagnosis alone does not authorize writes or new debug records.

During phase-verify, integration-checker traces both producer and consumer and
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
