# Architecture

The framework is a Python3.11+ package named `ai_engineering`. Authored modules live directly under `src`. Reusable project assets live at repository root in `agents`, `templates`, `workflows`, `constraints` and `framework.yaml`; initialization installs them into a project's `.ai` directory.

Plans, tasks, features and bugs are Markdown records under `.ai`. `STATE.yaml` indexes current work; Git supplies source revision and merge identity. The coordinator serializes state changes, reserves identifiers, prepares managed worktrees and owns delivery. Implementation workers receive a fixed worktree, branch and declared scope. Hard blocks are metadata on the current lifecycle phase; drafts are unstarted work.

Planning and implementation authority are separate. Discussing, creating, revising, approving or merging a plan does not grant implementation. Dispatch and replay require current coordinator-owned plan, action, delivered revision and scope authority. An explicit implementation operation creates that authority through the coordinator boundary.

Every product subprocess passes through `CommandRunner`. Focused constraint documents define coding standards, named and scoped commands, file/external-action permissions and execution limits. Agent Markdown carries inline model/provider/reasoning settings and role permissions. Provider adapters enforce their supported operating-system confinement and keep shared Git/control writes coordinator-owned.

The workflow layer connects initialization, research, planning, implementation, validation, review, bugfix, recovery, delivery, cleanup and state reconciliation. Delivery targets a reviewed or explicitly authorized implementation revision, creates a PR to main, observes merge and retires the exact merged worktree and branch. Validation and review are configurable workflow stages; the current implementation pass explicitly defers testing and compatibility checks at the user's request.

Current implementation scope is [PLAN-003](.ai/plans/completed/PLAN-003.md). Obsolete project history is deleted. Unresolved implementation defects are recorded under `.ai/bugs/open`.
