@.ai/library/references/response-language-directive.md

<purpose>
Orchestrate parallel debug agents to investigate UAT gaps and find root causes.

After UAT finds gaps, spawn one debug agent per gap. Each agent investigates autonomously with symptoms pre-filled from UAT. Collect root causes, update UAT.md gaps with diagnosis, then hand off to plan-phase --gaps with actual diagnoses.

Orchestrator stays lean: parse gaps, spawn agents, collect results, update UAT.
</purpose>

<available_agent_types>
Valid Workflow subagent types (use exact names — do not fall back to 'general-purpose'):
- debugger — Diagnoses and fixes issues
</available_agent_types>

<paths>
DEBUG_DIR=.planning/debug

Debug files use the `.planning/debug/` path (hidden directory with leading dot).
</paths>

<core_principle>
**Diagnose before planning fixes.**

UAT tells us WHAT is broken (symptoms). Debug agents find WHY (root cause). plan-phase --gaps then creates targeted fixes based on actual causes, not guesses.

Without diagnosis: "Comment doesn't refresh" → guess at fix → maybe wrong
With diagnosis: "Comment doesn't refresh" → "useEffect missing dependency" → precise fix
</core_principle>

<process>

<step name="parse_gaps">
**Extract gaps from UAT.md:**

Read the "Gaps" section (YAML format):
```yaml
- truth: "Comment appears immediately after submission"
  status: failed
  reason: "User reported: works but doesn't show until I refresh the page"
  severity: major
  test: 2
  artifacts: []
  missing: []
```

For each gap, also read the corresponding test from "Tests" section to get full context.

Build gap list:
```
gaps = [
  {truth: "Comment appears immediately...", severity: "major", test_num: 2, reason: "..."},
  {truth: "Reply button positioned correctly...", severity: "minor", test_num: 5, reason: "..."},
  ...
]
```
</step>

<step name="report_plan">
**Read worktree config:**

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
USE_WORKTREES=$(workflow_run query config-get workflow.use_worktrees --raw 2>/dev/null || echo "true")
RUNTIME=$(workflow_run query config-get runtime --default claude --raw 2>/dev/null || echo "claude")
```

**Resolve isolation now (#2584/#2652).** Read @.ai/library/references/dispatch-isolation-gate.md
and run its `Resolve ISOLATION`, `Single-agent dispatch sites`, and `Resolve the harness flag`
blocks in order; they set `ISOLATION`/`HARNESS_FLAG` via `query dispatch-isolation`.
`ISOLATION` — not `RUNTIME` — gates the worktree decision at spawn; the `spawn_agents` step
below consumes both variables.

**Report diagnosis plan to user:**

```
## Diagnosing {N} Gaps

Spawning parallel debug agents to investigate root causes:

| Gap (Truth) | Severity |
|-------------|----------|
| Comment appears immediately after submission | major |
| Reply button positioned correctly | minor |
| Delete removes comment | blocker |

Each agent will:
1. Create DEBUG-{slug}.md with symptoms pre-filled
2. Investigate autonomously (read code, form hypotheses, test)
3. Return root cause

This runs in parallel - all gaps investigated simultaneously.
```
</step>

<step name="spawn_agents">
**Load agent skills:**

```bash
AGENT_SKILLS_DEBUGGER=$(workflow_run query agent-skills debugger)
EXPECTED_BASE=$(git rev-parse HEAD)
```

**Pre-dispatch worktree base-check (#2649, mirrors execute-phase #683/#1369 and quick #1941).**
Claude Code's `isolation="worktree"` forks new worktrees from `origin/HEAD`, not the live local
HEAD. If local HEAD has advanced without an intervening `git push` (the documented Workflow steady
state — commit every step, push only on request), `origin/HEAD` is pinned to a stale ancestor
and the debug agent's `worktree_branch_check` guard halts with a base-mismatch fatal *after* the
worktree already exists, with no automatic degrade. Run the same pre-dispatch check the four
sibling dispatch sites run, and auto-degrade to sequential (main-tree) debug-agent dispatch when
the fork base cannot be reliably resolved. The verify-only `<worktree_branch_check>` guard below
stays active as a backstop in both cases.

```bash
if [ "$ISOLATION" = "harness-worktree" ]; then
  _DIAG_SHOULD_DEGRADE=$(workflow_run query worktree.base-check --mode "$ISOLATION" --pick shouldDegrade 2>/dev/null || true)
  if [ "$_DIAG_SHOULD_DEGRADE" = "true" ]; then
    _DIAG_DEGRADE_MSG=$(workflow_run query worktree.base-check --mode "$ISOLATION" --pick message 2>/dev/null || true)
    [ -n "$_DIAG_DEGRADE_MSG" ] && printf '%s\n' "$_DIAG_DEGRADE_MSG" >&2
    echo "⚠ [#2649] Worktree fork base diverged from orchestrator HEAD — auto-degrading to sequential mode for diagnosis to avoid a base-mismatch halt." >&2
    ISOLATION=none
    USE_WORKTREES=false
  fi
fi

# Re-record after the base-check degrade, immediately before the spawn below, so the
# #3045 sentinel matches the dispatch the guard is about to see (#3045).
workflow_run query dispatch-isolation --raw --force-isolation "$ISOLATION" >/dev/null 2>&1 || true

# Model resolution for the debugger spawns below (#3602).
DEBUGGER_MODEL=$(workflow_run query resolve-model debugger --raw)
```

**Spawn debug agents — parallel only when each one is isolated:**

**`ISOLATION` decides the fan-out, not just the flag (#2652).** When
`ISOLATION = "harness-worktree"`, spawn all agents in a single message: each gets its own
worktree, so concurrent edits cannot collide. When `ISOLATION = "none"` — including after the
`orchestrator-worktree` fallback and after the #2649 base-check degrade — the agents would all
run against the **primary checkout**, so spawn them **one at a time**, waiting for each to
return before spawning the next. Fanning out unisolated debuggers is the outcome the
`orchestrator-worktree` degrade exists to avoid; degrading the flag while keeping the
parallelism would announce sequential mode and then do the opposite.

For each gap, fill the debug-subagent-prompt template and spawn:

Print: `◆ Spawning diagnostics agent... (each runs in a subagent — no output until they return, ~1–5 min; expected, not a freeze)`

Before spawning, materialize the guard into WORKTREE_GUARD: read `.ai/library/references/worktree-branch-check.md`, substitute `{EXPECTED_BASE}` with `$EXPECTED_BASE`, and use the resulting `<worktree_branch_check>` block (the runnable guard) as WORKTREE_GUARD below.

**Only when `ISOLATION = "harness-worktree"`.** When `ISOLATION = "none"` the agent runs on
the main working tree, where the guard's HEAD assertion cannot hold — set `WORKTREE_GUARD` to
the empty string instead, or every diagnostic agent halts on a base mismatch it was never
meant to check (#2652).

**Substitute `{harnessFlag}` in the `Agent()` call below** with `$HARNESS_FLAG` followed by a
comma when `ISOLATION = "harness-worktree"`, and with the empty string otherwise — the same
build-time substitution `execute-phase.md` performs. `{harnessFlag}` is a template
placeholder, not a shell variable.

<!-- #2508 runtime-aware-dispatch -->

> **Runtime-aware dispatch (#2508 Phase 4).** Workflow workflows dispatch specialized subagents by role. Before dispatching on a built-in-only runtime (kimi-code — three built-ins only), resolve the role to a built-in via `workflow_run query resolve-dispatch-type --requested <role> --raw`. On named-dispatch runtimes (Claude/OpenCode/…) the role is returned unchanged; on kimi-code it maps to `coder`/`explore`/`plan` by role-suffix. The persona rides `${AGENT_SKILLS_<ROLE>}` (Phase 3) regardless. See @.ai/library/references/runtime-aware-dispatch.md.

<!-- #2517 model-omit-on-inherit -->

> **Model omission (#2517).** Omit the `model` parameter entirely when the value it would carry (`DEBUGGER_MODEL`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model. See @.ai/library/references/model-profile-resolution.md.

```
Agent(
  prompt=filled_debug_subagent_prompt + "\n\n" + WORKTREE_GUARD + "\n\n<required_reading>\n- {phase_dir}/{phase_num}-UAT.md\n- {state_path}\n</required_reading>\n${AGENT_SKILLS_DEBUGGER}",
  subagent_type="debugger",
  model="{DEBUGGER_MODEL}",
  {harnessFlag}
  description="Debug: {truth_short}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above to spawn debug agent(s), stop working on this task immediately. Do not read more files, edit code, or run tests related to these gaps while the subagent(s) are active. Wait for all subagents to return before proceeding. This prevents duplicate work, conflicting edits, and wasted context.

**All agents spawn in a single message (parallel execution) ONLY when `ISOLATION = "harness-worktree"`.** When `ISOLATION = "none"`, spawn one agent per message and wait for each to return — see the fan-out rule above (#2652).

Template placeholders:
- `{truth}`: The expected behavior that failed
- `{expected}`: From UAT test
- `{actual}`: Verbatim user description from reason field
- `{errors}`: Any error messages from UAT (or "None reported")
- `{reproduction}`: "Test {test_num} in UAT"
- `{timeline}`: "Discovered during UAT"
- `{goal}`: `find_root_cause_only` (UAT flow - plan-phase --gaps handles fixes)
- `{slug}`: Generated from truth
</step>

<step name="collect_results">
**Collect root causes from agents:**

Each agent returns with:
```
## ROOT CAUSE FOUND

**Debug Session:** ${DEBUG_DIR}/{slug}.md

**Root Cause:** {specific cause with evidence}

**Evidence Summary:**
- {key finding 1}
- {key finding 2}
- {key finding 3}

**Files Involved:**
- {file1}: {what's wrong}
- {file2}: {related issue}

**Suggested Fix Direction:** {brief hint for plan-phase --gaps}
```

Parse each return to extract:
- root_cause: The diagnosed cause
- files: Files involved
- debug_path: Path to debug session file
- fix_hint: NON-BINDING example route for the gap closure plan — the binding payload is
  `root_cause`; a gap plan that removes the root cause by a smaller or different mechanism has
  closed the gap in full

If agent returns `## INVESTIGATION INCONCLUSIVE`:
- root_cause: "Investigation inconclusive - manual review needed"
- Note which issue needs manual attention
- Include remaining possibilities from agent return
</step>

<step name="update_uat">
**Update UAT.md gaps with diagnosis:**

For each gap in the Gaps section, add artifacts and missing fields:

```yaml
- truth: "Comment appears immediately after submission"
  status: failed
  reason: "User reported: works but doesn't show until I refresh the page"
  severity: major
  test: 2
  root_cause: "useEffect in CommentList.tsx missing commentCount dependency"
  artifacts:
    - path: "src/components/CommentList.tsx"
      issue: "useEffect missing dependency"
  missing:
    - "Add commentCount to useEffect dependency array"
    - "Trigger re-render when new comment added"
  debug_session: .planning/debug/comment-not-refreshing.md
```

Update status in frontmatter to "diagnosed".

Commit the updated UAT.md:
```bash
workflow_run query commit "docs({phase_num}): add root causes from diagnosis" --files ".planning/phases/XX-name/{phase_num}-UAT.md"
```
</step>

<step name="report_results">
**Report diagnosis results and hand off:**

Display:
```
### Workflow ► DIAGNOSIS COMPLETE

| Gap (Truth) | Root Cause | Files |
|-------------|------------|-------|
| Comment appears immediately | useEffect missing dependency | CommentList.tsx |
| Reply button positioned correctly | CSS flex order incorrect | ReplyButton.tsx |
| Delete removes comment | API missing auth header | api/comments.ts |

Debug sessions: ${DEBUG_DIR}/

Proceeding to plan fixes...
```

Return to verify-work orchestrator for automatic planning.
Do NOT offer manual next steps - verify-work handles the rest.
</step>

</process>

<context_efficiency>
Agents start with symptoms pre-filled from UAT (no symptom gathering).
Agents only diagnose—plan-phase --gaps handles fixes (no fix application).
</context_efficiency>

<failure_handling>
**Agent fails to find root cause:**
- Mark gap as "needs manual review"
- Continue with other gaps
- Report incomplete diagnosis

**Agent times out:**
- Check DEBUG-{slug}.md for partial progress
- Can resume with /workflow:debug

**All agents fail:**
- Something systemic (permissions, git, etc.)
- Report for manual investigation
- Fall back to plan-phase --gaps without root causes (less precise)
</failure_handling>

<success_criteria>
- [ ] Gaps parsed from UAT.md
- [ ] Debug agents spawned in parallel
- [ ] Root causes collected from all agents
- [ ] UAT.md gaps updated with artifacts and missing
- [ ] Debug sessions saved to ${DEBUG_DIR}/
- [ ] Hand off to verify-work for automatic planning
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
