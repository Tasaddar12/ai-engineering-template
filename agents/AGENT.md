# Engineer agent catalog

Read the complete selected method before using it. This is an authoring catalog; run the pinned installer to register the host assets.

Resolve agent names, model and effort through `engineer_run query resolve-agent NAME`, `resolve-model NAME` and `resolve-effort NAME`. Omit host overrides when the resolved value is `inherit`. Dispatch only roles supported by the actual host.

| Method | Purpose |
|---|---|
| [code-fixer](code-fixer.md) | Applies fixes to code review findings from REVIEW.md. Reads source files, applies intelligent fixes, and commits each fix atomically. Spawned by /code-review --fix. |
| [code-reviewer](code-reviewer.md) | Reviews source files for bugs, security issues, and code quality problems. Produces structured REVIEW.md with severity-classified findings. Spawned by /code-review. |
| [codebase-mapper](codebase-mapper.md) | Explores codebase and writes structured analysis documents. Spawned by map-codebase with a focus area (tech, arch, quality, concerns). Writes documents directly to reduce orchestrator context load. |
| [debug-session-manager](debug-session-manager.md) | Manages multi-cycle /debug checkpoint and continuation loop in isolated context. Spawns debugger agents, handles checkpoints via AskUserQuestion, dispatches specialist skills, applies fixes. Returns compact summary to main context. Spawned by /debug command. |
| [debugger](debugger.md) | Investigates bugs using scientific method, manages debug sessions, handles checkpoints. Spawned by /debug orchestrator. |
| [doc-verifier](doc-verifier.md) | Verifies factual claims in generated docs against the live codebase. Returns structured JSON per doc. |
| [doc-writer](doc-writer.md) | Writes and updates project documentation. Spawned with a doc_assignment block specifying doc type, mode (create/update/supplement), and project context. |
| [dom-verifier](dom-verifier.md) | Verifies live-DOM acceptance criteria for a completed execution wave using a browser MCP server. Writes DOM-VERIFY.md. Additive — never blocks a wave. Spawned by the live-dom-uat capability at execute:wave:post. |
| [executor](executor.md) | Executes plans with atomic commits, deviation handling, checkpoint protocols, and state management. Spawned by execute-phase orchestrator or execute-plan command. |
| [integration-checker](integration-checker.md) | Verifies cross-phase integration and E2E flows. Checks that phases connect properly and user workflows complete end-to-end. |
| [nyquist-auditor](nyquist-auditor.md) | Fills Nyquist validation gaps by generating tests and verifying coverage for phase requirements |
| [pattern-mapper](pattern-mapper.md) | Analyzes codebase for existing patterns and produces PATTERNS.md mapping new files to closest analogs. Read-only codebase analysis spawned by /plan-phase orchestrator before planning. |
| [phase-researcher](phase-researcher.md) | Researches how to implement a phase before planning. Produces RESEARCH.md consumed by planner. Spawned by /plan-phase orchestrator. |
| [plan-checker](plan-checker.md) | Verifies plans will achieve phase goal before execution. Goal-backward analysis of plan quality. Spawned by /plan-phase orchestrator. |
| [planner](planner.md) | Creates executable phase plans with task breakdown, dependency analysis, and goal-backward verification. Spawned by /plan-phase orchestrator. |
| [security-auditor](security-auditor.md) | Verifies threat mitigations from PLAN.md threat model exist in implemented code. Returns structured security verdict (SECURED / OPEN_THREATS / ESCALATE). Spawned by /secure-phase. |
| [ui-auditor](ui-auditor.md) | Retroactive 6-pillar visual audit of implemented frontend code. Produces scored UI-REVIEW.md. Spawned by /ui-review orchestrator. |
| [ui-checker](ui-checker.md) | Validates UI-SPEC.md design contracts against 7 quality dimensions. Produces BLOCK/FLAG/PASS verdicts. Spawned by /ui-phase orchestrator. |
| [ui-researcher](ui-researcher.md) | Produces UI-SPEC.md design contract for frontend phases. Reads upstream artifacts, detects design system state, asks only unanswered questions. Spawned by /ui-phase orchestrator. |
| [verifier](verifier.md) | Verifies phase goal achievement through goal-backward analysis. Checks codebase delivers what phase promised, not just that tasks completed. Creates VERIFICATION.md report. |
