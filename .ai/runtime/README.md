# Phase runtime

`phase.py` executes the phase procedures described in
[the workflow guide](../guides/PHASE-WORKFLOW.md). It consumes Markdown records
with complete phase template bodies and additive YAML execution fields and
[config.yaml](../../.planning/config.yaml). The Python runtime requires no schema
files, schedule snapshots or separate work-item registry. Supporting agent methods are bundled locally under `references/methods/`;
reading the workflow does not require a separate SDK or external schema generator.
Python 3.11+ and PyYAML are required. Install `requirements.txt` into the host's
virtual environment. Git and the chosen worker executable must be available;
publication additionally requires an authenticated GitHub CLI.

Installation places this runtime under `.codex/runtime` or `.claude/runtime`.
It locates rules, role methods, workflow procedures and skills in the same host
layout. Project records remain under `.planning`. Commands and references in
the installed guides use the selected layout; the template authoring checkout
continues to use its internal layout.

New worker and verifier branches use the installed host name (`claude` or `codex`)
followed by `/phase-...`. The authoring checkout defaults to the Codex prefix.
Existing recorded branch names remain unchanged during recovery.

Run from an assigned immediate-child worktree under the primary checkout's
ignored `.worktrees/`. Commands use the current repository and named branch.
The primary checkout accepts inspection only. Config and phase inputs must be
committed, and the worktree must be clean before mutation.

## Commands

| Invocation | Effect |
|---|---|
| `python .ai/runtime/phase.py new authentication --title "Authentication"` | Allocate the next phase number across registered worktrees; commit pending CONTEXT and a roadmap link |
| `python .ai/runtime/phase.py check 03` | Read-only structural readiness and dependency checks; does not replace an independent feasibility review |
| `python .ai/runtime/phase.py status [03]` | Read-only local status, including pending components and next action |
| `python .ai/runtime/phase.py status 03 --remote` | Also observe the published PR and its checks without editing local status |
| `python .ai/runtime/phase.py run 03` | Dispatch ready components; audit and integrate committed results |
| `python .ai/runtime/phase.py resume 03 --workers-stopped` | Reconcile interrupted work after confirming old processes stopped; reuse committed output without replay |
| `python .ai/runtime/phase.py run 03 --replan --workers-stopped` | Explicit new attempt after reconciliation and approval; retain incorporated work and add correction components |
| `python .ai/runtime/phase.py verify 03` | Run checks, start a fresh independent verifier and commit the assessment |
| `python .ai/runtime/phase.py verify 03 --workers-stopped` | Reconcile an interrupted verifier; retry when its saved report is incomplete or stale |
| `python .ai/runtime/phase.py uat 03` | Create or show a persistent acceptance session |
| `python .ai/runtime/phase.py uat 03 --case 1 --result pass --note "Observed result"` | Commit an actual human observation; also accepts fail, blocked and skipped |
| `python .ai/runtime/phase.py publish 03 --authorized --base main [--draft]` | Push and create/update the phase PR; never merge it |
| `python .ai/runtime/phase.py sync` | Update only Runtime Status in the full STATE artifact |

Phase arguments accept a number or full directory name. Read-only status and
check do not launch agents, reserve IDs or write checkpoints. An empty template
has no phases and no verification commands until adoption.

## Input and result contract

[CONTEXT](../templates/context.md) owns goal, identified acceptance, decisions
and actual authorization. `approval: approved` is a recorded human instruction,
not permission a worker can invent. Open questions remain a coordinator
judgment: prepare only independent, decided scope for execution.

Each [PLAN](../templates/phase-prompt.md) declares kind (`code` or
`documentation`), prerequisite component IDs, owned paths, exclusive resources,
acceptance IDs, required documentation paths and meaningful argv checks. Paths
are exact repository-relative files or directory prefixes ending in `/`. Globs,
traversal, shared Git metadata and phase-record ownership are rejected. Its own
SUMMARY is automatically owned. Authorization matches exact Git path spelling,
including case and whitespace. Scheduling treats case variants conservatively
as overlapping across platforms, but that does not authorize a differently
spelled path during the committed-output audit.

[TEMPLATE-CONTRACT](TEMPLATE-CONTRACT.md) defines complete upstream artifact consumption,
local evidence extensions, checkpoint and decimal-numbering boundaries, and migration.

The coordinator also owns immutable PROJECT, REQUIREMENTS, RULES and config
inputs. Broad ownership such as `.ai/` is rejected because it contains those
inputs. Change them during preparation, then commit and explicitly replan.

Every acceptance outcome needs at least one component. Give substantive guide
or specification obligations to a documentor component that depends on the code;
the code component's body points to that handoff. Declare documentation on the
component responsible for completing or verifying it, not a predecessor finishing
before it exists. Overlapping files or resources serialize. Dependencies wait
for integrated commits and passing checks. Cross-phase dependencies need verified
code and its report on the fetched publication base.

Workers commit actual changes and [SUMMARY](../templates/summary.md), with
`status: complete|blocked`, acceptance and documentation coverage. The runner
audits every commit's paths, clean output, ancestry and nonempty implementation,
then reruns checks. Exit code zero and summary claims alone do not prove success.
Required documentation must exist and have summary coverage; the independent
verifier checks its truth. No runtime can infer product correctness from file
existence or a command that does not test the intended outcome.

## Worker adapters and context

Configuration commands are argument lists; no shell interpolation is performed.
Supported substitutions are `{worktree}`, `{assignment}`, `{result}`, `{kind}`,
`{component}` and `{sandbox}`. Runtime also provides `PHASE_WORKTREE`,
`PHASE_ASSIGNMENT`, `PHASE_RESULT`, `PHASE_KIND` and `PHASE_COMPONENT` environment
variables, plus the Markdown assignment on standard input. An optional
`execution.documentor_command` selects a separate executable/model route.

The coordinator starts fresh processes. Each gets the role, relevant core
constraints, CONTEXT, its PLAN, required source and dependency summaries.
Worker processes do not start agents. The template's Codex commands explicitly
select `gpt-5.6-terra` for coders and `gpt-5.6-luna` for documentors and verifiers
through `--model` in `.planning/config.yaml`. Other model settings, including
reasoning effort, retain the host defaults unless overridden in those commands.
Check the installed host's execution and worktree permissions;
prompts and Git auditing do not sandbox arbitrary commands or external services.

The [installer](../commands/install.md) selects initial routes by host: Codex for
`--host codex`, and [claude_worker.py](claude_worker.py) for a fresh `--host claude`
project. Existing `.planning/config.yaml` remains authoritative. To choose Claude
explicitly during onboarding, set
the worker, documentor and verifier command lists to:

```yaml
[python, .claude/runtime/claude_worker.py, --kind, "{kind}", --result, "{result}"]
```

The Claude adapter runs `claude -p --output-format json --no-session-persistence`
with the complete assignment on stdin and the assigned checkout as cwd. It uses
Claude's configured model and permission defaults, preserving project context
and hooks. Install/authenticate Claude separately and configure needed project
tool permissions before dispatch; permission denials return a failed result,
not a fabricated completion. No permission bypass or `--bare` mode is added.

For code/documentation, the final response goes to the runtime log and never
overwrites the worker's committed SUMMARY. The verifier exposes only Read, Glob
and Grep, separately denies MCP tools, and saves a successful final report to
the external result path without overwriting an existing file. Configured checks
run through the runtime; the Claude verifier cannot run Bash checks itself.
Tool restrictions and prompts are not an OS sandbox; configured host hooks can
still run, and the runtime audits verifier checkout changes. Failed CLI runs,
invalid result JSON, empty reports or permission denials fail the adapter.

Complete skills are installed directly under `.agents/skills` for Codex or
`.claude/skills` for Claude and travel with committed inputs into fresh worker
checkouts. Both hosts discover the full skills at those locations. Required methods are also named by path
in PLAN's Read first section. Other adapters can read those same Markdown paths.
The runtime needs no new skill configuration; follow the
[repository skill guide](../guides/AGENT-SKILLS.md) for selection and upkeep.

For code/documentation, PHASE_RESULT is the SUMMARY path inside the worker's
worktree. Do not use `--output-last-message` to write there after a commit.
For the verifier it is an external report path. The default verifier adapter
saves its final Markdown message there. Custom adapters may write it directly.
Preserve the complete upstream verification-report sections and add the local
evidence sections below. Verifier YAML is `status: passed|gaps_found|human_needed` and the exact assigned
`revision`. Required sections are Acceptance, Integration, Documentation and
Findings. The verifier has its own worktree; any tracked edit or commit invalidates
its result and preserves the worktree for inspection.

## Integration, failures and recovery

One operating-system lock in the common Git directory protects the coordinator
and shared Git operations. One coordinator runs per repository at a time;
components within that phase use `execution.max_parallel` (1–8). This deliberate
limit avoids concurrent coordinators allocating and integrating against each other.

Operational state is atomic internal YAML under the common Git directory's
`ai/phases/`, keyed by phase and assigned checkout. It records immutable inputs,
initial revision, worktrees, processes, checks and integrated commits. Assignment
prompts and logs live beside it. These are machine-maintained local checkpoints.
Durable summaries, reports and UAT travel with the phase; a fresh clone does not
inherit local process checkpoints.

A small supervisor records its process identity before launching the worker.
Recovery inspects both identities and refuses observable live writers, including
when a coordinator stopped before saving the worker PID. Missing or ambiguous
launch evidence requires inspection, not an automatic replay.

Interrupted workers are never automatically restarted. Confirm the recorded
processes stopped, inspect each worktree, then use resume. A clean committed
result can be audited and integrated without another worker. Dirty, missing,
blocked or out-of-scope output stays preserved. An already integrated component
whose checks failed is rechecked without rerunning its edits. Integration failure
does not release its dependents. Other successful outputs remain available.

Verifier attempts also preserve their source, worktree, process and result.
A stopped verifier's valid report can be reused for unchanged source. Use
`verify --workers-stopped` to retry an incomplete/stale attempt after inspection.
Checks that change tracked files or commits stop for inspection, even if the
check itself reports success. Commit or resolve preserved changes before retrying.
After inspecting and correcting a check mutation, use explicit replanning to
recheck incorporated work. Ordinary resume cannot clear an inspection finding.

Changes to execution inputs require explicit replanning. Keep incorporated
component instructions as history; add a new correction component instead of
rewriting completed instructions. Update CONTEXT only with authorized decisions,
commit inputs, and use `run --replan --workers-stopped`. Incomplete worktrees and
prior checkpoint generations are retained for audit. The runtime does not force
cleanup, retry indefinitely or merge a phase into its publication base.

Old dispatcher attempts must finish or be inspected using their original
repository revision. There is no silent conversion of old checkpoints.

## Verification, UAT and publication

Independent reports name the reviewed source revision and a content fingerprint.
Only generated STATE, this phase's verification/UAT and interruption note are
excluded from that fingerprint. Changed code, docs, instructions or checks
invalidate verification. Modifying the report invalidates its recorded attestation.
Component and project checks run again at publication.

When CONTEXT requires UAT, every acceptance case must have a current passing
observation and a note. Pending, failed, blocked and skipped cases prevent
publication; skipped means unresolved, even with a reason. Changes in tested
content start a new session after re-verification and retain prior observations.

`--authorized` records authorization already supplied by the human. Publication
pushes one phase branch and creates/updates its PR. It reports observed GitHub
checks. PR creation can start CI; it does not imply checks have finished or the
PR is ready. Configure `publication.required_checks` and use status with `--remote`
to inspect them. A delivered status requires an observed merge of the published
revision matching the current branch HEAD. A later commit must not be reported
as delivered using the older PR's merge observation. No command merges a PR or
moves the primary branch.

## Validation

In the upstream workflow source repository, run
`python -m unittest discover -s tests -v` from its test environment. The installer
does not copy that source test suite into projects. Configure the adopting
project's actual verification commands in `.planning/config.yaml` during onboarding.
Integration tests use temporary real repositories, isolated component worktrees,
deterministic workers and a local bare publication remote. Only GitHub's API
boundary is simulated. They test execution, ownership, dependency availability,
failure preservation, recovery, stale evidence and publication without merging.
The separate [hook suites](../hooks/README.md) check optional advisory notices.
