# Workflow transitions and invariants

Transitions are commands applied by a pure reducer with guards and evidence; state files must not be edited to bypass gates. JSON schemas restrict vocabulary; semantic validators enforce relationships and transitions.

| Entity | Permitted progression / branches | Required guard |
| --- | --- | --- |
| Plan | draft → isolation → approved → running → integration_review → delivery_ready → delivering → completed | Approved graph; all live tasks accepted; integrated validation/review; CI + observed merge |
| Plan recovery | running/integration_review → replanning → isolation → approved → running | Transactional rewrite; new approval; preserved acceptance already valid |
| Plan pause | Any nonterminal → blocked; blocked → recorded resume_state | Reason and recovery action; gates rechecked |
| Task | backlog → ready → running → validating → review_1 → review_2 → accepted → completed | Dependency integration; scope lease; validation; both reviews; final observed plan merge |
| Task repair | validating/review_1/review_2 → repairing → validating | New attempt/candidate, old approvals invalidated |
| Task structural | Nonterminal except completed → replanning → superseded, or backlog | Recovery proposal and re-approved graph; superseded requires successors |
| Task pause | Any nonterminal → blocked; blocked → recorded resume_state | Lease quiescence and reconciled inputs |
| Task later invalidation | accepted → ready | New dependency/context invalidates candidate; record why |
| Run | queued → running → paused/succeeded/failed/cancelled; paused → running | Explicit cancellation; terminal failure means infrastructure/policy exhaustion, not ordinary review defect |
| Agent run | queued → running → succeeded/failed/cancelled/unknown; unknown → reconciled status | Provider observation; valid output required for success |
| Worktree | planned → active → retained/cleanup_pending → removed | Registered Git identity; cleanup guards |
| PR | prepared → open → checks_pending → ready → merged; open/checks_pending/ready → closed | Exact remote head checks; merge authorization and observed result |

Completed and superseded tasks are terminal. Integration gaps create new tasks; do not reopen completed work. `accepted` means both task reviews passed, not project completion. Task readiness is recomputed from graph and accepted integrated dependencies, not just a stored word. An approved plan may hold backlog tasks until prerequisites become eligible.

Review failure is a recorded verdict and workflow branch, not a terminal task state. Material edits, base changes, checklist changes, graph/spec/ADR/interface/handoff changes invalidate candidate fingerprints. R2 material fixes restart validation and R1, then R2. R1 fixes do the same. Terminal reviews are immutable; retries produce new IDs.

Plan completion records the merge observation before archive. Archiving is an independent boolean with an immutable manifest. Blocks preserve their prior state. Unknown remote outcomes pause only affected resources while safe independent tasks continue.
