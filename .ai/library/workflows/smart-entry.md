<purpose>
Workflow smart entry — the state-aware front door. Detect the current project situation via `workflow_run smart-entry --json`, present a short menu of the right next actions, and dispatch to exactly one existing Workflow command. This is a launcher/router only; it never does the work itself.

This is a *menu* front door, not a second router. For in-project forward motion (planning → executing → verify-pending) the recommended action is `/workflow:progress --next`, which delegates to the single gated advancement engine (`.ai/library/workflows/next.md`: Route 0 resume-incomplete-phase + Gates 1-3). smart-entry adds value only where `--next` cannot reach: pre-project, remediation (paused/blocked/verify-failed), and lifecycle exits (idle-stranded/complete). See `docs/adr/1787-workflow-next-smart-entry.md`.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's `execution_context` before starting.
</required_reading>

<process>

<step name="text_mode">
**TEXT_MODE handling (non-Claude runtimes).**

Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.
</step>

<step name="resolve">
**Resolve the workflow_run shim.**

Run this resolver block exactly. It locates `workflow-tools.cjs` across every supported runtime home and defines a `workflow_run` function. If it cannot find the tool, it prints the standard install hint and exits non-zero.

```bash
```
</step>

<step name="detect">
**Detect the situation.**

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
SNAPSHOT=$(workflow_run smart-entry --json 2>/dev/null)
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

Parse `SNAPSHOT` as JSON. It has the shape:

```json
{
  "situation": "executing",
  "recommended": "progress-next",
  "summary": "Phase 2 of 5 · 60% · executing",
  "signals": { "...": "..." },
  "actions": [
    { "id": "progress-next", "label": "Advance to the next step", "command": "/workflow:progress --next", "recommended": true },
    { "id": "execute-phase", "label": "Continue executing phase 2", "command": "/workflow:execute-phase", "recommended": false }
  ]
}
```

`situation` is one of: `no-project`, `paused`, `blocked`, `verify-failed`, `needs-first-phase`, `planning`, `executing`, `verify-pending`, `idle-stranded`, `complete`, `unknown`.

**Fallback (never strand the user):** `smart-entry --json` can fail for two reasons, and each has a different recovery. Parse `SNAPSHOT`; if it is empty, not valid JSON, or missing `actions`, apply the first matching recovery below — do NOT error.

1. **`workflow-tools` itself is broken** (the failure is a `Cannot find module ...` / Node crash, not just an empty result). Probe by running `workflow_run state-snapshot` — if THAT also errors, the whole tool layer is down and routing to `/workflow:progress` would dead-end too (it also needs workflow-tools). **Recover by reading state directly:**
   - Read `.planning/STATE.md` (frontmatter + body) with the Read tool. Extract: `status` (frontmatter `status:` or body `**Status:**`), `Phase:` from the body, `total_phases`/`percent` from a nested `progress:` frontmatter object if present, and any `## Blockers` items.
   - Synthesize a minimal result: `situation` = your best guess from the status text (`executing`/`verifying`/`planning`/`complete`/`paused`), `summary` = a one-line read ("Phase N of M · status"), and an `actions` list built from status (e.g. verifying → `/workflow:verify-work`, executing → `/workflow:execute-phase`, else `/workflow:progress`), always including `/workflow:quick` and `/workflow:help`.
   - Print one line first: `smart-entry unavailable (workflow-tools error) — reading state directly. The workflow-tools layer may need a rebuild (rm tsconfig.build.tsbuildinfo && npm run build).`
   - Proceed to the `present` step with this synthesized result.

2. **Only `smart-entry` is unavailable** (e.g. older workflow-core without the subcommand; `state-snapshot` still works). Run `/workflow:progress` and stop. Print one line first: `smart-entry unavailable — showing progress.`
</step>

<step name="present">
**Present the menu.**

Show the `summary` line to orient the user, then offer the actions.

**If TEXT_MODE is false:** call `AskUserQuestion` with:
- `header`: a short label derived from `situation` (e.g. `executing` → "Continue work", `blocked` → "Unblock", `no-project` → "Get started", `complete` → "What next?").
- `question`: the `summary` line, then "What would you like to do?"
- `options`: the first 4 entries of `actions[]` in order. For each, `label` = the action's `label`, `description` = the action's `command`. The recommended action is already first; surface it as the first option. The user may also type a custom command (handled automatically).

**If TEXT_MODE is true:** print the `summary`, then a numbered list of ALL `actions[]` (not capped to 4 — text has no limit), then ask the user to type the number of their choice:

```
{summary}

  1. {actions[0].label}  ({actions[0].command})
  2. {actions[1].label}  ({actions[1].command})
  ...

Type a number, or describe what you want to do.
```

Wait for the user's response before continuing. Map the chosen number to the corresponding action.
</step>

<step name="display">
**Show the routing decision.**

```
### Workflow ► SMART ENTRY

**Situation:** {situation}
**Routing to:** {chosen command}
```
</step>

<step name="dispatch">
**Dispatch and stop.**

Invoke the chosen action's `command`. If the user typed a free-form response instead of picking an action, treat it as freeform intent and route via `/workflow:progress --do "<their text>"`.

After invoking the command, **stop**. The dispatched command owns everything from here. Do not continue, do not chain, do not re-enter this workflow.
</step>

</process>

<success_criteria>
- [ ] Situation detected via `workflow_run smart-entry --json`
- [ ] Summary shown to orient the user
- [ ] Menu offered (AskUserQuestion, or numbered list under TEXT_MODE)
- [ ] Routing decision displayed before dispatch
- [ ] Exactly one command dispatched
- [ ] Any detection failure falls back to /workflow:progress (never strands the user)
- [ ] No work done directly — launcher only
</success_criteria>


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
