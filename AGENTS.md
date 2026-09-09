# Operating index

Implement the current `.ai/plans/active/PLAN-003.md` and read `.ai/STATE.yaml`. The user explicitly requests all features completed and delivered to GitHub main, obsolete framework data deleted, and no test suites, compatibility probes or validation loops during this pass. Fix straightforward bugs while coding and record unresolved bugs under `.ai/bugs/open`. A final review may happen after implementation.

Use Python3.11+ with authored modules directly under src and the installed ai_engineering namespace. Reusable assets live at root agents, templates, workflows, constraints and framework.yaml. All product subprocesses use the central runner. Coordinator owns workflow state and Git delivery; implementation workers edit their declared files in the assigned managed checkout without switching branches or changing Git metadata.

All plans and plan-specific contracts must be PLAN-NNN Markdown files under `.ai/`, with explicit task and feature references. Tasks/features also live under `.ai/`. Do not retain obsolete plans, archived framework data or historical execution receipts as active inputs. Do not add legacy migration code solely to preserve deleted data.

Local reversible edits, local commits, the requested cleanup, and delivery to main are authorized. Do not run tests now or claim they passed. Keep exact managed paths and branch names when performing Git cleanup; do not rewrite unrelated Git history or touch credentials. Implementation subagents use GPT-5.6 Sol/xhigh; final reviewers, if used, may use GPT-6 Astra/xhigh.
