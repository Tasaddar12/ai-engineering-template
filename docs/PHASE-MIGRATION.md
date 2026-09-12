# Phase workflow migration

## Authorization and scope

The user requested this reference document and authorized implementation in a
new worktree, commits, pushing a pull request, independent review, and fixing
findings. The user explicitly prohibited merging. The migration implements the
phase-based recommendation from this conversation. It does not adopt the
template into a fictional product or fill in its project identity.

The user rejected INTAKE and standalone PLAN lifecycles, milestones, work-item
hierarchies, and JSON schema requirements. Those exclusions govern this work.
The approval also covers replacing the old rules that require those mechanisms,
mandatory routine amendments, fixed review counts, and separate preparation and
finalization PRs. Work remains confined to the assigned worktree.

## Objective

Replace the current record-heavy engineering workflow with phase-local context,
research, bounded component instructions, execution summaries, verification, and
user acceptance records. A coordinator can start independent coder assignments
concurrently, integrate them into a phase branch, verify the result, and publish
one phase PR without automatically merging it.

The structural inspiration is GSD-Core, inspected at commit
`a2331c01f16505aea338f7f91e9244842906c1ea`:

- [Phase planning](https://github.com/open-gsd/gsd-core/blob/a2331c01f16505aea338f7f91e9244842906c1ea/gsd-core/workflows/plan-phase.md)
- [Execution instructions](https://github.com/open-gsd/gsd-core/blob/a2331c01f16505aea338f7f91e9244842906c1ea/gsd-core/templates/phase-prompt.md)
- [Execution summary](https://github.com/open-gsd/gsd-core/blob/a2331c01f16505aea338f7f91e9244842906c1ea/gsd-core/templates/summary.md)
- [Phase verification](https://github.com/open-gsd/gsd-core/blob/a2331c01f16505aea338f7f91e9244842906c1ea/gsd-core/templates/verification-report.md)

These sources inform the design; this is an implementation for this template,
not an installation or vendored copy of GSD.

## Target files and ownership

```text
.ai/
  PROJECT.md                 Human purpose, boundaries, and success
  REQUIREMENTS.md            Identified desired outcomes and phase mapping
  ROADMAP.md                 Phase goals, dependencies, and links
  STATE.md                   Compact derived status and next action
  RULES.md                   Shared authority, scope, evidence, and delivery
  config.yaml               Worker routes, concurrency, and checks
  truth-map.md              Index of each fact's owner
  codebase/                 Optional maps of the existing system
  phases/
    03-authentication/
      03-CONTEXT.md          Decisions, scope, authorization, open questions
      03-DISCUSSION-LOG.md   Optional discussion history
      03-RESEARCH.md         Optional technical findings
      03-VALIDATION.md       Checking strategy, including documentation
      03-01-IMPLEMENT.md     Component instructions
      03-01-SUMMARY.md       Component results and evidence
      03-02-IMPLEMENT.md     Another component, not another lifecycle
      03-02-SUMMARY.md
      03-VERIFICATION.md     Independent phase assessment
      03-UAT.md              Acceptance session when applicable
      .continue-here.md      Interruption and resume context
  specs/                    Current verified behavior
  decisions/                Significant architectural rationale
  agents/                   Coordinator, researcher, preparer, checker,
                            coder, documentor, verifier
  commands/                 Phase and onboarding entry points
  references/               Details loaded only for relevant operations
  templates/                Markdown artifact examples
  runtime/                  Phase inspection, dispatch, integration, recovery
docs/                       Product guides and this migration reference
```

Phase folders have stable paths. The example is illustrative and is not seeded
as real adopting-project work. Optional artifacts are created only when useful.
Component instruction/result pairs are local to a phase; they are not standalone
work items, PLAN records, or another directory lifecycle.

## Phase process

1. **Receive and discuss.** Create a phase from a request, record its goal in the
   roadmap, and collect scope, acceptance, decisions, unresolved questions, and
   authorization in CONTEXT. Preserve original discussion separately only when
   useful. Research and notes are evidence, not automatic scope approval.
2. **Research.** Inspect relevant source, tests, and references. Save only what
   later workers would otherwise need to rediscover. Record source revisions.
3. **Prepare.** Produce one IMPLEMENT document per bounded component. Include
   explicit prerequisites, ownership, resources, acceptance references, commands,
   and documentation obligations. Establish shared interfaces before parallel
   dispatch. A separate checker verifies coverage and feasibility.
4. **Execute.** A fresh worker handles each ready component. Independent owners
   run concurrently in separate immediate-child worktrees. Intersecting paths or
   exclusive resources serialize. Workers commit their changes and SUMMARY.
5. **Integrate.** The coordinator audits actual changes, merges each successful
   component into the phase branch, and runs integration checks. Dependent
   components start only after their own prerequisite is integrated and checked.
   There is no barrier requiring unrelated earlier-wave work to finish first.
6. **Document.** Coders can update comments and nearby explanations. A separately
   assigned documentor handles substantial specifications and guides, using
   actual implementation and summaries. Required docs stay attached to the phase.
7. **Verify and correct.** An independent verifier assesses acceptance, component
   wiring, regression results, and documentation. Findings remain visible. Scope
   and verification evidence cannot be weakened to turn a failure into success.
   Bounded corrections invalidate affected evidence and are reviewed again.
8. **Accept and ship.** UAT persists observable tests and unresolved gaps when
   needed. Publish one PR for the verified phase. Publishing is distinct from
   delivery; delivery requires observed merge evidence. No automatic merge.

Small bug phases require reproduction and a regression check but may omit
research and elaborate preparation. Documentation-only phases dispatch a
documentor without a coder. Research-only phases may finish as research without
claiming delivered code. Missing human decisions block only dependent work.

## Runtime contract

Human-authored inputs are Markdown with small YAML frontmatter and config.yaml.
There are no JSON schema files, execution-contract JSON fences, schema-enforced
worker outputs, or hand-authored orchestration snapshots. Runtime validates the
fields it actually uses and consumes committed Markdown summaries.

The CLI provides `new`, `check`, `status`, `run`, `resume`, `verify`, `uat`,
`publish`, and `sync`. Procedures cover discussion, research, preparation, and
human decisions. Command documents explain the CLI boundary honestly; Markdown
entry points are not claimed to be installed slash commands.

Component frontmatter carries its dependencies, files, exclusive resources,
kind (code/documentation), and verification commands. The body carries the
objective, required reading, acceptance, and documentation obligations. SUMMARY
frontmatter reports complete or blocked and checked acceptance/documentation
coverage; its body records evidence and deviations. The runtime audits paths,
requires committed nonempty work, checks configured commands, and distinguishes
process exit from verified completion.

Run-owned operational checkpoints may use internal YAML in the Git common
directory. The public interface remains Markdown. Record the initial revision,
input fingerprint, worker processes/results, integrated commits, and reviewed
revision. Persist a lock and checkpoint before dispatch. A crashed or interrupted
worker is not blindly replayed: inspect the process, worktree, commits, and
summary first. Preserve incomplete worktrees. Status is read-only; sync updates
the human view in the assigned worktree. Relevant Git operations are serialized.

Publication requires current verification, nonempty configured checks, and
authorization. The CLI creates/updates a PR and never invokes a merge command.
GitHub check results and actual remote merge state are reported separately.

## Documentation and consistency

- PROJECT owns intent; REQUIREMENTS owns desired outcomes; CONTEXT owns phase
  decisions; IMPLEMENT owns instructions; SUMMARY owns observed component results;
  VERIFICATION owns the independent phase assessment. ROADMAP and STATE are views
  or indexes, not alternate acceptance contracts.
- Existing SPECs describe current behavior. Planned changes stay in phase records
  until code makes them true. Guides and specifications are checked on the same
  deliverable revision; incomplete behavior cannot be excused by rewriting docs.
- Documentation obligations finish as updated, verified unchanged, not applicable
  with a reason, or unresolved. Unresolved required coverage prevents completion.
- Routine amendments and duplicate journals are retired. Git and phase records
  preserve ordinary changes; significant decisions retain ADRs.
- Distinguish a stale document, broken code, an approved transition, and conflicting
  human decisions. Correct the wrong side using evidence. Deferred discoveries
  stay in the affected phase or seed a separately authorized phase.
- Keep the mandatory rule core small. Load only the selected procedure, role,
  relevant constraints, required source, and dependency summaries per worker.

## Ordered implementation passes

| Pass | Work | Acceptance |
|---|---|---|
| 1 | Phase templates, document ownership, rules and config | One clear owner per fact; no adopting-project claims |
| 2 | Phase commands, agents and onboarding | Complete routes for fixes, investigation, docs and features |
| 3 | Phase-native runtime and bounded workers | Parallel independent components, checked integration, safe recovery |
| 4 | Documentation, status, UAT and delivery | Gaps remain visible; publication does not claim merge |
| 5 | Cutover, remove old active lifecycle, review and fixes | Consistent entry points, meaningful checks pass, unmerged PR ready |

Each pass is committed with a descriptive message. The reference is committed
before implementation. Active old entry points are replaced in the final batch;
historical records remain history. Old unfinished runs must use the preserved
original revision/runtime rather than being silently interpreted by the new one.

## Removal and preservation

Remove active plans/intake/fix lifecycle placeholders, old PLAN/INTAKE/FIX/ORCH
templates and commands, schedule.example.json, the old snapshot compiler and
schema-bound dispatcher, mandatory amendment/journal procedures, and redundant
track roles. Preserve the two historical FIX records and any real history without
pretending they were phase deliveries. Update links needed to keep history readable.
Reuse useful Git/process protection and regression-test ideas, not obsolete policy
assertions. Update both advisory hooks and their tests where paths or policy links
change. Preserve their advisory behavior.

## Required demonstrations before the PR is ready

- A bounded defect has reproduction and regression evidence.
- Documentation-only execution avoids unnecessary code workers.
- Independent components overlap in time; shared ownership/resources do not.
- Dependencies see their prerequisites' integrated code.
- Failed integration stops affected downstream work without losing results.
- A committed worker result survives interruption and resumes without duplicate work.
- Partial/uncommitted or out-of-scope worker output is not silently accepted.
- Changed inputs and stale verification are detected before reuse/publication.
- Missing behavior, wiring, or required documentation prevents phase completion.
- UAT records preserve pending, blocked, failed and passed cases across sessions.
- Publication creates a PR, reports checks, and never merges it.
- Active entry points contain no old PLAN/INTAKE workflow requirements.
- Python integration tests, both Bash hook suites, and link checks pass.

Use temporary real Git repositories and deterministic worker fixtures for runtime
tests. Test actual transitions and evidence, not just presence of wording. Review
the code and documentation independently, fix findings, repeat affected checks,
push, and leave the PR open for the user. Retain the implementation worktree.
