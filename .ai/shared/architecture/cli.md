# CLI and major workflows

The current bootstrap CLI safely creates and lists plan bundles and adds plan-local task records. The installer and validator are separate flat entry points. They do not execute tasks or change lifecycle state. The following orchestration commands are the target contract for later tasks.

| Workflow | Entry points | Outcome |
| --- | --- | --- |
| Project lifecycle | `project init`, `project adopt`, `framework upgrade` | Safe installation and versioned upgrade |
| Research and decision | `research start`, `decision record` | Sourced findings and accepted rationale |
| Spec and plan | `plan create`, `plan review`, `plan status` | Spec-linked, isolation-approved task graph |
| Plan execution | `plan implement PLAN-ID`, `run resume RUN-ID`, `run cancel RUN-ID` | Parallel task attempts, reviews and recovery |
| Delivery | `plan deliver PLAN-ID` | Integration result, PR preparation, CI repairs and permitted merge |
| Reconciliation | `state reconcile`, `state status`, `state archive` | Compare observed facts, rebuild views, preserve history |

`plan implement` continues through authorized delivery automatically; `plan deliver` resumes the same workflow when external authorization becomes available. No second orchestration system.

Common flags: `--project PATH`, `--json`, `--dry-run`, `--run-id`, `--max-parallel N`. Destructive/publishing operations support dry-run; dry-run performs read-only observation and outputs intended actions, without creating branches, locks, state records, or contacting write endpoints. Resume uses stored policy and requires an explicit recorded change to broaden it.

Exit codes: 0 requested operation completed; 2 invalid input/configuration; 3 gate failed; 4 durable pause/authorization or budget needed; 5 transient infrastructure; 6 state/reconciliation conflict; 1 internal error. JSON output is versioned, includes status, run ID, evidence references and next actions. Human output stays concise.

The runtime is installed into an environment, while project assets are installed into Git. `project init` may initialize an empty Git repository; adopt never rewrites history and initially requires a clean index/worktree. Unborn projects get a local initial checkpoint before worktrees. Discovery of project validation commands produces a proposal, not arbitrary command execution.
