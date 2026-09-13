---
status: complete
component: guides
source_revision: 40e4781
---

# Template migration guides and local extensions

## Outcome

Documented the complete planning-to-delivery workflow, separated project storage
from reusable tooling, cataloged all 40 upstream templates, and expanded the two
local-only templates with complete authoring guidance.

## Coverage

| Assigned path | Result | Evidence |
|---|---|---|
| `README.md` | Updated and verified | Entry points, `.planning` storage, runtime/config boundary, draft/final delivery and evidence limits checked against integrated runtime/source |
| `docs/PHASE-WORKFLOW.md` | Updated and verified | Full onboarding/discussion/research/planning/check/execution/documentation/verification/UAT/delivery/recovery lifecycle; compared scheduler, publish and STATE behavior with source |
| `docs/WORKFLOW-FEATURES.md` | Updated and verified | Capability inventory, exact storage, safeguards and limits; distinguishes local executable runtime from supplied upstream guidance |
| `docs/TEMPLATE-GUIDE.md` | Created and verified | All 40 pinned source files accounted for with links, destinations and producer/consumer guidance |
| `docs/ONBOARDING-PROMPTS.md` | Updated and verified | New/existing project requests, full PLAN inputs, draft progress, authorized merge/cleanup and read-only status boundaries |
| `docs/AGENT-SKILLS.md` | Updated and verified | PLAN and `.planning` references; existing skill provenance distinguished from new complete upstream import |
| `.ai/templates/ADR.md` | Expanded and verified | Purpose, producer/consumer, complete fillable artifact, instructions, good/bad examples with rationale, handoff and lifecycle |
| `.ai/templates/CURRENT-SPEC.md` | Created and verified | Same teaching coverage; evidenced current behavior explicitly separate from upstream desired phase `spec.md` |

## Commits

- `f253a12`: Expand local decision and current behavior templates with authoring guidance.
- `e241c1d`: Document planning workspace and full parallel workflow feature lifecycle.
- `849e7fe`: Catalog all upstream templates and update onboarding and skill usage guidance.
- Final summary commit: clarify checkpoint dispatch and STATE section preservation from integrated source audit.

## Checks

- Verified absolute assigned root and branch before writes:
  `D:/Codex Projects/ai-engineering-template/.worktrees/gsd-guides`,
  `codex/gsd-guides`.
- Read rules, documentor role, project/state baseline, worktree/onboard/status
  procedures, documentation reference and documentation-reconcile skill.
- Compared guide claims against integrated parent revision `40e4781`, including
  `phase_records.load_phase`, PLAN autonomous/setup gates, `Phase.fingerprint`,
  `phase_runner.run_phase`, `publish_phase`, `status_text`, `sync_state`, recovery
  identity handling, and `.ai/runtime/TEMPLATE-CONTRACT.md`.
- Checked 111 local links across all eight assigned docs/templates against the
  integrated parent checkout: zero missing targets.
- Compared template catalog links against all 40 pinned upstream template source
  files: zero omissions.
- Searched assigned files for stale `.ai` project-record paths, IMPLEMENT naming
  and blanket no-milestone/no-schema claims: no matches.
- `git diff --check` passed for completed slices and final guide corrections.
- No runtime tests added or rerun for documentation-only work. Runtime behavior
  checks and independent final verification remain the coordinator's integration
  obligations. Inspected source is evidence for claims, not a live agent trial.

## Decisions and proposed changes.log entries

1. Preserve the old current-behavior SPEC role as local `CURRENT-SPEC.md`, because
   upstream lowercase `spec.md` specifies desired phase requirements. Different
   names avoid both semantic confusion and Windows case collisions.
2. Expand local ADR/current-spec templates to the upstream teaching pattern:
   purpose, consumers, complete skeleton, detailed steps, positive/negative
   examples with reasons, lifecycle and handoff. No upstream template shortened.
3. Rewrite human guides around `.planning/` data, full PLAN artifacts and
   explicit Python/upstream execution boundaries. Preserve the prior skill
   adaptation's historical source attribution rather than relabeling it as the
   new upstream import.
4. Document draft PR progress as a coordinator forge operation, separate from
   runtime verified `publish --draft`; keep runtime never-merge boundary while
   explaining already-authorized coordinator merge and safe cleanup.
5. Document STATE as full authored session memory with a derived Runtime Status
   section, and preserve checkpoint plans as artifacts while requiring actual
   coordinator checkpoint handling before autonomous dispatch.

## Deviations and remaining

- No writes outside assigned paths and this SUMMARY; no branch changes,
  integration, push, merge or worker delegation performed.
- One oversized shell write was automatically rejected with the generic reason
  `blocked by policy`. The identical authorized documentation edits completed
  safely through apply_patch and smaller literal writes; no approval requested.
- Reported one source-only editorial finding to the coordinator: new_phase's
  roadmap append contained a mojibake separator. Source repair is outside this
  documentor's ownership.
- Broader native GSD skills/commands/agents/workflows installation remains the
  user's subsequent stage and is not claimed complete by these guides.
- Coordinator must integrate the final commit, add the proposed adaptations to
  `changes.log`, run final independent review/checks and complete authorized
  publication, merge and cleanup. No required assigned guide coverage remains.

## Follow-up: project-owned naming and proposed entry workflows

**Authorization:** The user's subsequent direction removes source branding from
our active system while retaining heavy methodological inspiration and complete
instructional depth. The user also proposed feature-change, bug-fix and
small-change entry workflows for the next stage.

**Assigned baseline:** Clean `codex/gsd-guides` checkout at `b18b6dc`, with the
absolute assigned root verified again before writes.

### Completed slices

- `f7d803f`: Reconciled all eight assigned active guides/local templates to
  project-owned terminology and `.ai/library/` paths. The skill methods table
  now links local supporting guidance, including bare specialist filenames.
  Source attribution is referenced through THIRD-PARTY-NOTICES/provenance.
- `ae43dd9`: Added `docs/WORKFLOW-DIRECTION.md` and navigation from README,
  PHASE-WORKFLOW and WORKFLOW-FEATURES. Records three proposed entry paths,
  research/questions before phase goals, optional feature/milestone grouping,
  common execution safeguards, open choices and demonstration-based validation.
- Final follow-up commit: corrected a trailing table space and recorded evidence.

### Decisions and changes.log additions

1. Active guides use our own library/workflow terminology. Source attribution and
   exact revision history remain separate in third-party notices and provenance.
   The importer/coordinator was informed to preserve the earlier skill-method
   source pin separately from the full template import revision.
2. All references to supporting methods now target `.ai/library/`; specialist
   filenames drop the source prefix. Full templates were not abbreviated, and
   the local ADR/current-spec teaching content remains intact.
3. The three entry workflows are a proposed next-stage design. This slice creates
   no new runtime route, host command or mandatory feature-group registry.
4. The proposed flow begins with the request and relevant source inspection,
   uses research/questions to resolve material uncertainty, then derives phase
   goals. Small changes do not automatically require a separate research report.
5. Feature/milestone grouping is recorded as an open design choice. Existing
   phase execution, evidence and ownership remain the shared foundation.

### Follow-up verification and limits

- Inspected 130 local links across the nine assigned active files. Twenty target
  the planned library/notice migration; each library method resolves through its
  known original source mapping. Zero unexplained missing targets.
- Final active-prose scan found no source brand, old source revision strings,
  old library path, or duplicate replacement wording in assigned files.
- Final `git diff --check` passed after correcting the table whitespace.
- The prior history above is retained as migration evidence. This follow-up does
  not rewrite the actual original attribution or authorization history.
- No runtime behavior changed or runtime tests added. Final actual renamed-target
  navigation checks remain for integration after the parallel library rename.
- No push, integration, merge, branch switch or worker delegation performed.
