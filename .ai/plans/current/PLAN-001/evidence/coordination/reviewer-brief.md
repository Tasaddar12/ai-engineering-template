# Manual independent review procedure

Use only the dispatched exact task worktree as read-only candidate source. Write
only the named ROOT review report and optional companion evidence files. Root
canonical state is coordinator-owned. Do not edit source, task, graph, policy,
R1 evidence, or commits. A source/base change invalidates both task stages.

Read .ai/AGENTS.md, the role guide in docs/agents, selected task/spec/plan, current
graph and approved isolation, frozen service contracts, relevant explicit ADRs,
accepted dependency handoffs, task handoff, actual Git diff and tests. R1 uses
all 11 implementation checks; R2 all 12 consistency checks and passing R1.
Check every applicable criterion with concrete evidence. Do not treat passing
unit tests as sufficient proof of cross-task interface consistency. Do not fail
on speculative preferences or require unowned concrete downstream behavior.

The selected native configuration is OpenAI gpt-6-astra xhigh, review_high rank4;
implementation is Sol xhigh rank3. Coordinator observes submitted native model/
effort. Separate provider-returned identity/effort is unavailable. Describe this
honestly using evidence/effort-provenance-clarification.md; no schema fields added.

Candidate verification: raw git diff --binary BASE HEAD hashes to diff_sha256.
Context refs hash raw committed task-worktree file bytes; validation refs hash
ROOT evidence bytes. policy_model_digest is SHA256 of raw ROOT policy.json
concatenated with agent-models.json, no separator. Root/worktree CRLF-only policy
differences previously reconciled with equal Git and semantic JSON. Fingerprint
is canonical candidate JSON excluding fingerprint, sort_keys=True, compact
separators, ensure_ascii=False. Recompute and verify clean actual head/base.

Use ROOT/.ai/local/full-plan-venv/Scripts/python.exe from task worktree. The
declared command is in selected plan commands/test.TASK-NNN.json; imports must
resolve task worktree src, not editable root source. Observe a nonzero count.
Root tests discovery currently covers24bootstrap, not new leaves. Run relevant
meaningful independent checks; avoid repeated broad checks without justification.

Report Markdown plus schemas/v1/review-result.schema.json compliant JSON. Fields
include exact candidate ref/fingerprint, stage, unique request/invocation/session
IDs, implementation session identity, checklist version PLAN-001-v1 and complete
numbered checks with rationale/evidence. R2 review_1_ref is required and must
point to applicable same-candidate R1 JSON. Never fabricate absent evidence.
Validate your final report schema. Reports are immutable after FINAL. End with
verdict/paths and stop all worktree access so coordinator can integrate safely.

Keep the written reports proportionate and concise: identify the candidate and
provenance once, a compact complete checklist with decisive evidence, actual
validation results, and concrete findings. Do not repeat the full context manifest
several times in prose or repeat every passing assertion. JSON still needs every
required field and check; concise rationales with precise evidence are sufficient.

## Available Linux validation

WSL Ubuntu-24.04 is available for meaningful platform checks. Use the project-local
Linux interpreter /mnt/d/Codex Projects/ai-engineering-template/.ai/local/full-plan-linux-venv/bin/python
with the declared jsonschema dependency. The system Ubuntu jsonschema4.10.3 is too
old. Invoke wsl.exe -d Ubuntu-24.04 --cd '<Linux candidate tree>' --exec '<Linux
interpreter>' followed by the declared arguments. Always use --exec to preserve
argv without the default WSL shell interpreting metacharacters. Imports must still
resolve the exact candidate src. Prioritize Linux for OS-backed code; avoid repeated
platform-neutral suites without a concrete verification purpose. Record skips and
actual coverage honestly; never call an environment setup failure a source defect.

## Minimum-version validation runtimes

Project-local Python3.11.16 with declared jsonschema4.26.0 is available on both hosts:
Windows ROOT/.ai/local/full-plan-py311-venv/Scripts/python.exe;
Linux /mnt/d/Codex Projects/ai-engineering-template/.ai/local/full-plan-linux-py311-venv/bin/python.
Use Linux through WSL Ubuntu-24.04 --exec and exact candidate cwd. Use these for
meaningful minimum-version checks or final packaging; do not repeat unrelated
suites after they pass. Existing Python3.12 environments remain the declared
coordinator test default. No remote CI execution is implied by local WSL testing.

## Required project material

Current user instruction: every required runtime helper, regression test and reusable
usage instruction must be versioned in its task-owned source, tests or canonical
docs. A private helper invoked by product code is part of the runtime closure.
No required behavior may depend on ignored .ai/local, a session script, an editable
root install or an untracked fixture. Keep local material only for disposable
execution/cache; give new helper files a concrete purpose and reuse existing tools.
Report useful local discoveries and their tracked disposition in the task handoff.
See the tracked coordination README and local-material-audit.md for this plan's
manual tools; those are not installed product dependencies.
