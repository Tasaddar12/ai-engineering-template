@~/.claude/engineer/references/response-language-directive.md

<purpose>
Orchestrate parallel debug agents to investigate UAT gaps and find root causes.

After UAT finds gaps, spawn one debug agent per gap. Each agent investigates autonomously with symptoms pre-filled from UAT. Collect root causes, update UAT.md gaps with diagnosis, then hand off to plan-phase --gaps with actual diagnoses.

Orchestrator stays lean: parse gaps, spawn agents, collect results, update UAT.
</purpose>

<available_agent_types>
Valid Engineer subagent types (use exact names — do not fall back to 'general-purpose'):
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
_ENGINEER_SHIM_NAME="engineer_run"; _ENGINEER_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; ENGINEER_TOOLS="${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}"; _engineer_at() { for _p; do if [ -f "$_p" ]; then ENGINEER_TOOLS="$_p"; return 0; fi; done; return 1; }; _engineer_id_ok() { case "$("$1" runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"engineer-runtime"'*'}') return 0;; *) return 1;; esac; }; _engineer_homes() { set -- "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "${CODEX_HOME:-$HOME/.codex}"; for _h; do _engineer_at "$_h/engineer/bin/${_ENGINEER_SHIM_NAME}" && return 0; done; return 1; }; if _engineer_at "${_ENGINEER_RUNTIME_ROOT}/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.claude/engineer/bin/${_ENGINEER_SHIM_NAME}" "${_ENGINEER_RUNTIME_ROOT}/.codex/engineer/bin/${_ENGINEER_SHIM_NAME}"; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif _engineer_homes; then engineer_run() { sh "$ENGINEER_TOOLS" "$@"; }; elif unset -f engineer_run; _G="$(command -v engineer_run)"; [ -n "$_G" ] && _engineer_id_ok "$_G"; then ENGINEER_TOOLS="$_G"; engineer_run() { "$ENGINEER_TOOLS" "$@"; }; else echo "ERROR: engineer_run not found at $ENGINEER_TOOLS and no identity-proving engineer_run is on PATH. Run: python -I bin/install.py --source <local-source> --ref <pinned-ref> --target <project-root> --host claude --local" >&2; exit 1; fi; ENGINEER_IDENTITY_STATUS=unverified; _engineer_id_ok engineer_run && ENGINEER_IDENTITY_STATUS=ok; export ENGINEER_IDENTITY_STATUS; [ "$ENGINEER_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$ENGINEER_TOOLS\" did not prove it is engineer-runtime - it is either a different package or an engineer-runtime older than the runtime-identity verb." >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${ENGINEER_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${ENGINEER_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
```

**Resolve isolation now.** Read @~/.claude/engineer/references/dispatch-isolation-gate.md
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
1. Create .planning/debug/{slug}.md with symptoms pre-filled
2. Investigate autonomously (read code, form hypotheses, test)
3. Return root cause

This runs in parallel - all gaps investigated simultaneously.
```
</step>

<step name="spawn_agents">
**Load agent skills:**

```bash
IFS= read -rd '' ENGINEER_ARGS <<'ENGINEER_ARGS_END' || true
$ARGUMENTS
ENGINEER_ARGS_END
ENGINEER_ARGS=${ENGINEER_ARGS%$'\n'}
AGENT_SKILLS_DEBUGGER=$(engineer_run query agent-skills debugger )
EXPECTED_BASE=$(git rev-parse HEAD)
```

Resolve mandatory isolation with `dispatch-isolation`; accept only `harness-worktree` or `orchestrator-worktree`. An unavailable mode blocks dispatch. Capture the expected base and embed the verify-only branch guard for harness workers; for runtime-created checkouts embed a root pin. Dispatch native debugger agents into their assigned checkouts and wait for all results, preserving lifecycle and confirmed-stop evidence.

For each gap, fill this prompt (the `Template placeholders` below define every `{…}` field) as `filled_debug_prompt`, then spawn:

```markdown
<objective>
Investigate issue: {slug}

**Summary:** {truth}
</objective>

<symptoms>
expected: {expected}
actual: {actual}
errors: {errors}
reproduction: {reproduction}
timeline: {timeline}
</symptoms>

<mode>
symptoms_prefilled: true
goal: find_root_cause_only
</mode>

<debug_file>
Create: .planning/debug/{slug}.md
</debug_file>
```

Print: `◆ Spawning diagnostics agent... (each runs in a subagent — no output until they return, ~1–5 min; expected, not a freeze)`

Before spawning, materialize the guard into WORKTREE_GUARD: read `engineer/references/worktree-branch-check.md`, substitute `{EXPECTED_BASE}` with `$EXPECTED_BASE`, and use the resulting `<worktree_branch_check>` block (the runnable guard) as WORKTREE_GUARD below.

**Only when `ISOLATION = "harness-worktree"`.** When `ISOLATION = "none"` the agent runs on
the main working tree, where the guard's HEAD assertion cannot hold — set `WORKTREE_GUARD` to
the empty string instead, or every diagnostic agent halts on a base mismatch it was never
meant to check.

**Substitute `{harnessFlag}` in the `Agent()` call below** with `$HARNESS_FLAG` followed by a
comma when `ISOLATION = "harness-worktree"`, and with the empty string otherwise — the same
build-time substitution `execute-phase.md` performs. `{harnessFlag}` is a template
placeholder, not a shell variable.

<!-- model-omit-on-inherit -->

> **Model omission.** Omit the `model` parameter entirely when the value it would carry (`DEBUGGER_MODEL`) is `"inherit"` or empty. An empty value 404s on runtimes without native tier aliases — the default on non-Claude runtimes. Omitting it inherits the orchestrator's model.

```
Agent(
  prompt=filled_debug_prompt + "\n\n" + WORKTREE_GUARD + "\n\n<required_reading>\n- {phase_dir}/{phase_num}-UAT.md\n- {state_path}\n</required_reading>\n${AGENT_SKILLS_DEBUGGER}",
  subagent_type="debugger",
  model="{DEBUGGER_MODEL}",
  {harnessFlag}
  description="Debug: {truth_short}"
)
```

> **ORCHESTRATOR RULE — CODEX RUNTIME**: After calling Agent() above to spawn debug agent(s), stop working on this task immediately. Do not read more files, edit code, or run tests related to these gaps while the subagent(s) are active. Wait for all subagents to return before proceeding. This prevents duplicate work, conflicting edits, and wasted context.

**All agents spawn in a single message (parallel execution) ONLY when `ISOLATION = "harness-worktree"`.** When `ISOLATION = "none"`, spawn one agent per message and wait for each to return — see the fan-out rule above.

Template placeholders:
- `{truth}`: The expected behavior that failed
- `{expected}`: From UAT test
- `{actual}`: Verbatim user description from reason field
- `{errors}`: Any error messages from UAT (or "None reported")
- `{reproduction}`: "Test {test_num} in UAT"
- `{timeline}`: "Discovered during UAT"
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
engineer_run query commit "docs({phase_num}): add root causes from diagnosis" --files ".planning/phases/XX-name/{phase_num}-UAT.md"
```
</step>

<step name="report_results">
**Report diagnosis results and hand off:**

Display:
```
### Engineer ► DIAGNOSIS COMPLETE

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
- Check .planning/debug/{slug}.md for partial progress
- Can resume with /debug

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
