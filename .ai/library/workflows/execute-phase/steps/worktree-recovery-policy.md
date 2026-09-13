Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Worktree Recovery Policy

## ORCHESTRATOR FAIL-CLOSED RULE (#48)

> **ORCHESTRATOR FAIL-CLOSED RULE (#48):** `worktree_branch_check` is verify-only — an executor that hits a base/HEAD-namespace mismatch prints `FATAL:` and exits **42** instead of self-recovering. If any executor result reports a `FATAL:`/`exit 42` (or its commits never appear because it halted at the check), mark that plan **blocked**: do NOT merge or clean up its worktree (preserve it for inspection), do NOT count the wave as successful, and surface the mismatch with recovery guidance to the user. The orchestrator — the worktree lifecycle owner — performs any base correction (e.g. recreate the worktree on `{EXPECTED_BASE}`); the sub-agent never does. Never proceed past a halted executor on the assumption it succeeded.

## ISOLATED-RUN RECOVERY — FAIL SAFE (#1292)

> **ISOLATED-RUN RECOVERY — FAIL SAFE (#1292):** When an isolated (worktree) run is *rejected* — the user declines to merge it, the orchestrator surfaces recovery guidance for a blocked/halted plan, or the run over-reached the requested scope — the worktree-isolation contract MUST hold through recovery. Do **NOT** propose continuing on `main`/the primary checkout as the default or recommended recovery path. Default to a **safe halt** and offer: (a) re-attempt in a **fresh, narrowly-scoped worktree**, or (b) inspect or discard the rejected worktree without merging. Any path that edits the primary checkout requires an **explicit, clearly-labeled confirmation** from the user first — editing `main` directly is never the proposed or default option for a run the user configured to be isolated.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
