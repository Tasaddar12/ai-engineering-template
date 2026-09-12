# Working through a phase

A phase contains a coherent outcome and the files needed to deliver it. A small
bug, documentation correction, investigation or multi-component feature uses the
same process with only the necessary artifacts.

The [shared rules](../.ai/RULES.md) own authorization, conflict handling and
delivery boundaries. This guide explains how the pieces connect.

## From information to executable components

| Stage | Coordinator action | Artifact |
|---|---|---|
| Receive | Reuse a relevant phase or create a stable directory | CONTEXT and roadmap link |
| Discuss | Establish scope, acceptance, decisions and actual authorization | CONTEXT; optional discussion log |
| Research | Assign unanswered technical questions | Optional RESEARCH |
| Prepare | Split the outcome into bounded components with shared interfaces | IMPLEMENT files; optional VALIDATION |
| Check | Obtain independent assessment for substantial work and runtime readiness | Findings/resolutions in preparation notes |
| Execute | Start fresh workers when their dependencies/resources are ready | Component changes and SUMMARY |
| Verify | Assess the integrated outcome and correct required gaps | VERIFICATION |
| Accept/publish | Record human observations when required, then publish within authority | UAT and PR reference |

The coordinator maintains project navigation and phase decisions. Workers read
their relevant context and return results; they do not all edit the phase record.

## Inside a phase

```text
.ai/phases/03-authentication/
  03-CONTEXT.md
  03-DISCUSSION-LOG.md         Optional history
  03-RESEARCH.md               Optional findings
  03-VALIDATION.md             Optional shared strategy
  03-01-IMPLEMENT.md
  03-01-SUMMARY.md
  03-02-IMPLEMENT.md
  03-02-SUMMARY.md
  03-VERIFICATION.md
  03-UAT.md                    When acceptance needs it
  .continue-here.md            When pausing needs explanation
```

CONTEXT defines the target. IMPLEMENT describes one component's work and refers
to acceptance IDs such as A1. SUMMARY records what that worker actually did.
VERIFICATION assesses the integrated phase independently. See
[artifact responsibilities](../.ai/references/phase-artifacts.md).

Project SPECs and guides stay in their existing owners outside the phase folder.
The phase links to them and declares required documentation coverage.

## Example: authentication

The specific choices must come from the real project; this is a decomposition
example, not preapproved behavior.

| Component | Needs first | Responsibility | Proof |
|---|---|---|---|
| Session behavior | Existing user identity and settled interface | Establish session lifecycle | Lifecycle and failure checks |
| Sign-in interface | Integrated session interface | Connect the user-facing flow | End-to-end success/failure |
| Protected operations | Integrated session interface | Enforce access boundaries | Unauthorized access rejected |
| Guides and SPEC | Relevant integrated components | Explain actual behavior/configuration | Claims checked against code |

The two consumers of session behavior can run concurrently if their owned paths
and external resources are independent. They start after the session result is
integrated and checked in the phase branch. Substantial documentation can depend
on the code it describes.

Each fresh worker receives the component instruction, relevant decisions,
required reads, checks and dependency summaries. It does not inherit every
conversation from earlier workers. The runtime supplies the assigned checkout
and result destination through the [worker handoff](../.ai/references/worker-handoff.md).

## Running the prepared phase

Install and configure the runtime using its [guide](../.ai/runtime/README.md).
Run mutations from the assigned immediate-child integration worktree with
committed inputs. Example phase names below must match the actual project.

```text
python .ai/runtime/phase.py check 03-authentication
python .ai/runtime/phase.py run 03-authentication
python .ai/runtime/phase.py verify 03-authentication
python .ai/runtime/phase.py status 03-authentication
```

These are separate executable boundaries. The assistant follows the procedure
through already-authorized steps; it does not require another user confirmation
merely because the next command is separate. Newly discovered consequential
decisions still need resolution for affected work.

A worker commits its changes and SUMMARY. The coordinator audits output and
integrates successful results. Independent verification checks acceptance,
component wiring, regressions and documentation. Gaps remain visible until
corrected and checked again.

## Documentation and smaller changes

Required documents are declared in component instructions and accounted for in
summaries. Each obligation ends updated/verified, verified unchanged, not
applicable with a reason, or unresolved. The verifier assesses the actual claims.
A required unresolved obligation prevents completion.

Declare a required document on the component that will cover it. Coder results
are checked at integration, so a guide written by a later documentor belongs on
that dependent documentation component. The coder's prose references the handoff.

| Change | Minimum useful route |
|---|---|
| Known bug | Context and one component; reproduce, repair, prove regression, verify |
| Unknown failure | Bounded research; then prepare repair or resolve a decision |
| Documentation correction | Documentation component; inspect claims, edit, verify |
| Research-only request | Supported findings and explicit limits; no claim of delivered code |
| Larger project direction | Define outcomes in PROJECT/REQUIREMENTS, order phases, detail the next phase |

Current SPECs describe observed implemented behavior. Future changes remain in
CONTEXT until implemented. Significant decisions retain ADRs; ordinary changes
use Git and phase history without a separate journal or amendment.

## Interruption and correction

Use [phase-resume](../.ai/commands/phase-resume.md) when execution stops. Inspect
the worker processes, commits and summaries before asserting that workers have
stopped. Preserve worktrees and consume valid committed results where possible
instead of repeating them.

Independent verification retains a separate attempt. A stopped verifier's valid
current report can be reused. Use phase-verify with --workers-stopped after
inspection when a fresh review is needed; do not start a duplicate live verifier.

A correction changes affected code and invalidates corresponding evidence.
After reconciling the previous attempt, preserve completed assignments and add
bounded corrective components using the runtime's replan route. Review the
current inputs and rerun independent verification. Never clear failure evidence
or weaken acceptance merely to make another run start.

## Publication boundary

[Phase-ship](../.ai/commands/phase-ship.md) publishes one phase PR by default.
It requires real authorization, current verification, required checks and required
UAT. The runtime never merges. Review/fix the PR and leave it open when that is
the user's instruction.

CI can start only after publication. Read status with --remote to observe current
PR checks; do not declare readiness while required checks are pending or failed.
The publish command does not promise to wait for remote checks to finish.

Read-only status reports observed state. `sync` separately updates the compact
STATE view. A summary, a published PR and a verified merged result are distinct
facts. Unmerged and incomplete worktrees remain available for recovery.
