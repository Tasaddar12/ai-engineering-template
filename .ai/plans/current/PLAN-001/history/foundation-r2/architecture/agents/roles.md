# Logical roles

Roles are bounded invocations, not permanent services. Deterministic roles may be Python services. No role independently writes canonical state or grants permissions.

| Role | Responsibility | Inputs | Outputs |
| --- | --- | --- | --- |
| Orchestrator | Coordinate lifecycle and own gates | Plan/state | Run checkpoints |
| Context Agent | Select minimal hashed context | Task/references | Context bundle |
| Repository Analyst | Observe repo architecture and commands | Git/files | Adoption inventory |
| Research Agent | Answer scoped research questions | Question/source policy | Research record |
| Evidence Agent | Verify provenance and claims | Research/command evidence | Evidence assessment |
| Requirements Agent | Map goals to measurable acceptance | Approved requirements | Spec proposal |
| Architecture Agent | Resolve boundaries and decisions | Specs/current architecture | ADR proposal |
| Planning Agent | Create bounded tasks | Spec/plan | Graph proposal |
| Task Isolation Reviewer | Review all ISO checks; propose rewrites | Whole proposed graph | Isolation report |
| Git/Worktree Agent | Observe/manage authorized Git operations | Operation intent | Observed facts |
| Implementation Agent | Inspect source; minimal edit; tests/docs | Task bundle | Handoff/discovery |
| Test Agent | Verify acceptance and failures | Task/code/commands | Validation evidence |
| Static Analysis Agent | Run configured static checks | Command suite | Command evidence |
| Runtime/E2E Agent | Exercise integrated behavior | Plan/runtime suite | Runtime evidence |
| Security Agent | Inspect concrete trust boundaries | Diff/spec/policy | Security findings |
| Implementation Reviewer | Independently run R1 checklist | Candidate/task | R1 report |
| Consistency Reviewer | Independently run R2 checklist | Candidate/plan/siblings/R1 | R2 report |
| Plan Integration Reviewer | Run INT checklist on combined tree | Plan/integrated candidate | Integration report |
| Task Recovery & Replanning Agent | Diagnose decomposition and rewrite | Failure histories/graph | Recovery proposal |
| Documentation Agent | Align task-owned docs with behavior | Accepted code/spec | Docs changes/handoff |
| PR Agent | Prepare/publish within policy; observe CI | Delivery intent | PR record |
| State Agent | Reconcile intent with observed facts | State/Git | Reconciliation proposal |
| Archive Agent | Retain history and eligible cleanup | Merge/evidence/retention | Archive manifest |
