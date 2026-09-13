<purpose>
Interactive configuration of Workflow workflow agents (research, plan_check, verifier) and model profile selection via multi-question prompt. Updates .planning/config.json with user preferences. Optionally saves settings as global defaults (~/.workflow/defaults.json) for future projects.
</purpose>

<required_reading>
Read all files referenced by the invoking prompt's execution_context before starting.
</required_reading>

<process>

<step name="ensure_and_load_config">
Ensure config exists and load current state:

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
RESPONSE_LANGUAGE=$(workflow_run query config-get response_language --raw --default "" 2>/dev/null || echo "")
workflow_run query config-ensure-section
INIT=$(workflow_run query state.load)
if [[ "$INIT" == @file:* ]]; then INIT=$(cat "${INIT#@file:}"); fi
# `state.load` returns STATE frontmatter JSON from the SDK — it does not include `config_path`. Orchestrators may set `Workflow_CONFIG_PATH` from init phase-op JSON; otherwise resolve the same path workflow-tools uses for flat vs active workstream (#2282).
if [[ -z "${Workflow_CONFIG_PATH:-}" ]]; then
  if [[ -f .planning/active-workstream ]]; then
    WS=$(tr -d '\n\r' < .planning/active-workstream)
    Workflow_CONFIG_PATH=".planning/workstreams/${WS}/config.json"
  else
    Workflow_CONFIG_PATH=".planning/config.json"
  fi
fi
```

**If `response_language` is set:** All user-facing output of this workflow — narration between tool calls, status updates, progress notes, findings, questions, prompts, and explanations — MUST be presented in `{response_language}`. Technical terms, code, file paths, and subagent prompts stay in English — only user-facing output is translated.

Creates `config.json` (at the resolved path) with defaults if missing. `INIT` still holds `state.load` output for any step that needs STATE fields.
Store `$Workflow_CONFIG_PATH` — all subsequent reads and writes use this path, not a hardcoded `.planning/config.json`, so active-workstream installs target the correct file (#2282).
</step>

<step name="read_current">
```bash
cat "$Workflow_CONFIG_PATH"
```

Parse current values (default to `true` if not present):
- `workflow.research` — spawn researcher during plan-phase
- `workflow.plan_check` — spawn plan checker during plan-phase
- `workflow.verifier` — spawn verifier during execute-phase
- `plan_review.source_grounding` — verify plan symbols against live source during plan review (default: true if absent; set `plan_review.source_grounding_authority` to select the resolver adapter: `grep` (default), `intel`, `treesitter`, `lsp`, or `scip`)
- `workflow.nyquist_validation` — validation architecture research during plan-phase (default: true if absent)
- `workflow.pattern_mapper` — run pattern-mapper between research and planning (default: true if absent)
- `workflow.ui_phase` — generate UI-SPEC.md design contracts for frontend phases (default: true if absent)
- `workflow.ui_safety_gate` — prompt to run /workflow:ui-phase before planning frontend phases (default: true if absent)
- `workflow.ai_integration_phase` — framework selection + eval strategy for AI phases (default: true if absent)
- `workflow.tdd_mode` — enforce RED/GREEN/REFACTOR gate sequence during execute-phase (default: false if absent)
- `workflow.code_review` — enable /workflow:code-review and /workflow:code-review --fix commands (default: true if absent)
- `workflow.code_review_depth` — default depth for /workflow:code-review: `quick`, `standard`, or `deep` (default: `"standard"` if absent; only relevant when `code_review` is on)
- `workflow.ui_review` — run visual quality audit (/workflow:ui-review) in autonomous mode (default: true if absent)
- `commit_docs` — whether `.planning/` files are committed to git (default: true if absent)
- `intel.enabled` — enable queryable codebase intelligence (/workflow:map-codebase --query) (default: false if absent)
- `graphify.enabled` — enable project knowledge graph (/workflow:graphify) (default: false if absent)
- `graphify.auto_update` — opt-in: auto-rebuild graph after main HEAD advances (#3347) (default: `false`)
- `model_profile` — which model each agent uses (default: `balanced`)
- `git.branching_strategy` — branching approach (default: `"none"`)
- `workflow.use_worktrees` — whether parallel executor agents run in worktree isolation (honored when the runtime declares a `dispatch.isolation` primitive — `harness-worktree` or `orchestrator-worktree`; runtimes declaring `none` default it to `false` and fail closed on an explicit `true` — #1521, #2486, #2584)
- `workflow.compact_content` — load token-minimized instruction variants where they exist, trading rarely-needed elaboration for a smaller always-loaded instruction window (default: false if absent; #4139)
- `model_policy.provider` — provider slug for model policy (default: `null`; known values: anthropic, openai, google, qwen; set via /workflow:config --advanced)
- `model_policy.budget` — budget level for model policy (default: `null`; known values: high, medium, low; set via /workflow:config --advanced)
- `model_policy.high` — model ID for high-cost tier (default: `null`; set via /workflow:config --advanced)
- `model_policy.medium` — model ID for medium-cost tier (default: `null`; set via /workflow:config --advanced)
- `model_policy.low` — model ID for low-cost tier (default: `null`; set via /workflow:config --advanced)
</step>

<step name="present_settings">

**Text mode (`workflow.text_mode: true` in config or `--text` flag):** Set `TEXT_MODE=true` if `--text` is present in `$ARGUMENTS` OR `text_mode` from init JSON is `true`. When TEXT_MODE is active, replace every `AskUserQuestion` call with a plain-text numbered list and ask the user to type their choice number. This is required for non-Claude runtimes (OpenAI Codex, Gemini CLI, etc.) where `AskUserQuestion` is not available.

**Non-Claude runtime note:** If `TEXT_MODE` is active (i.e. the runtime is non-Claude), prepend the following notice before the model profile question:

```
Note: Quality, Balanced, Budget, and Adaptive profiles assign semantic tiers
(Opus/Sonnet/Haiku) to each agent. When `runtime` is set in .planning/config.json,
tiers resolve to runtime-native model IDs — on Codex that's gpt-5.6-sol / gpt-5.6-terra /
gpt-5.6-luna with appropriate reasoning effort. See "Runtime-Aware Profiles" in
docs/CONFIGURATION.md.

If `runtime` is unset on a non-Claude runtime, the profile tiers have no effect on
actual model selection — agents use the runtime's default model. Choose "Inherit" to
force session-model behavior, set `runtime` + a profile to get tiered models, or
configure `model_overrides` manually in .planning/config.json to target specific
models per agent.
```

**Isolation resolution for the Worktrees question (#2486):** resolve the runtime's declared executor-isolation primitive and the current worktrees value before presenting the questions. Use `inspect-dispatch-isolation`, the **sentinel-free** inspection verb — never `dispatch-isolation`, whose #3045 contract records the resolved decision to the executor-dispatch sentinel as an unconditional side effect; a settings menu must not be able to stamp a sentinel the isolation guards then enforce against real dispatches. Sentinel-free is the exact claim: the shared CLI bootstrap still runs, but nothing it does can block a dispatch. The worktrees read deliberately carries no `--default`/fallback: an absent key must stay distinguishable from an explicit `false` (empty output = key absent), which the pre-selection rule below depends on.

A failed query is not a capability verdict, so track the two apart: settings still fails closed, but
says so instead of claiming the runtime declares no primitive. The verb fail-closes an unknown runtime — or an
internal resolution error — to `none` and exits 0, so `INSPECTED_RESOLVED=false` means only "the query did not answer"
(#2486 review):

```bash
_INSPECTED_RAW=$(workflow_run query inspect-dispatch-isolation --raw 2>/dev/null)
_ISOLATION_RC=$?
if [ $_ISOLATION_RC -ne 0 ] || [ -z "$_INSPECTED_RAW" ]; then
  INSPECTED_ISOLATION=none
  INSPECTED_RESOLVED=false      # no verdict learned — not the same as "declares none"
else
  INSPECTED_ISOLATION="$_INSPECTED_RAW"
  INSPECTED_RESOLVED=true
fi
case "$INSPECTED_ISOLATION" in
  harness-worktree|orchestrator-worktree|none) ;;
  *) INSPECTED_ISOLATION=none; INSPECTED_RESOLVED=false ;;   # out of vocabulary is not a verdict either
esac
USE_WORKTREES_CURRENT=$(workflow_run query config-get workflow.use_worktrees --raw 2>/dev/null)
```

Use AskUserQuestion with current values pre-selected. Questions are grouped into six visual sections; the first question in each section carries the section-denoting `header` field (AskUserQuestion renders abbreviated section tags for grouping, max 12 chars).

Section layout:

### Planning
Research, Plan Checker, Drift Guard, Pattern Mapper, Nyquist, UI Phase, UI Gate, AI Phase

### Execution
Verifier, TDD Mode, Code Review, Code Review Depth _(conditional — only when code_review=on)_, UI Review

### Docs & Output
Commit Docs, Skip Discuss, Worktrees

### Features
Intel, Graphify, Graph auto-update _(conditional — only when graphify=on)_

### Model & Pipeline
Model Profile, Auto-Advance, Branching

### Misc
Context Warnings, Compact Content, Research Qs

**Conditional visibility — code_review_depth:** This question is shown only when the user's chosen `code_review` value (after they answer that question, or the pre-selected value if unchanged) is on. If `code_review` is off, omit the `code_review_depth` question from the AskUserQuestion block and preserve the existing `workflow.code_review_depth` value in config (do not overwrite). Implementation: ask the Model + Planning + Execution-up-to-Code-Review questions first; if `code_review=on`, include `code_review_depth` in the same batch; otherwise skip it. Conceptually this is a one-branch split on the `code_review` answer.

**Conditional visibility — graphify.auto_update:** This question is shown only when the user's chosen `graphify.enabled` value is on. If `graphify.enabled` is off, omit the `graphify.auto_update` question and preserve the existing `graphify.auto_update` value in config (do not overwrite). Implementation: ask Graphify first; only ask Graph auto-update when Graphify is enabled.

**Conditional options — Worktrees (#2486):** whether a runtime can honor `workflow.use_worktrees: true` depends on its **declared `dispatch.isolation` capability, not its name** (#2584): `harness-worktree` (the host isolates each executor) and `orchestrator-worktree` (Workflow drives the worktrees) both run parallel; `none` fails closed on an explicit `true`. Branch on the same negotiation the execution gate resolves, via the sentinel-free `inspect-dispatch-isolation` verb, which fail-closes unknown/undeclared/`undocumented` to `none`. The rule is one-directional: **never persist a value the isolation gate would fail closed on.** **Do not add a runtime-name test here.** Branch on `$INSPECTED_ISOLATION`:

- **If `INSPECTED_ISOLATION` ≠ `none`** (`harness-worktree` or `orchestrator-worktree`): present the Worktrees question exactly as written below — unchanged behavior. The `none` branch is the entirety of the #2486 change.
- **If `INSPECTED_ISOLATION` = `none`:** replace the question's options with the two below — do NOT offer an enabling option, and NEVER write `workflow.use_worktrees: true` from this workflow when the runtime declares no isolation primitive, regardless of the user's answer:

```
{
  question: "Use git worktrees for parallel agent isolation?",
  header: "Worktrees",
  multiSelect: false,
  options: [
    { label: "No (Recommended)", description: "Write use_worktrees: false. {FINDING}, so parallel plans run sequentially and {CONSEQUENCE}." },
    { label: "Leave unchanged", description: "Do not write the key. {ABSENCE}; an existing explicit value is kept intact (e.g. for a worktree-capable install sharing this config)." }
  ]
}
```

**The three placeholders** carry the only difference between a capability Workflow resolved and one it could not, so no text in this branch ever asserts a verdict that was not reached. Substitute them everywhere they appear — the two `description`s above, the pre-selection rationale, and the notice — from whichever column applies:

| | `INSPECTED_RESOLVED=true` | `INSPECTED_RESOLVED=false` |
|---|---|---|
| `{FINDING}` | this runtime has no usable executor-isolation primitive | Workflow could not resolve this runtime's executor-isolation capability |
| `{CONSEQUENCE}` | execution fails closed on an explicit true | Workflow cannot tell whether execution will accept an explicit true |
| `{ABSENCE}` | absent, it resolves to false wherever this emit stamped that default | absent, it is the safe state until the capability resolves |

Failing closed is right in both columns — never write `workflow.use_worktrees: true` from this branch either way. Only the explanation changes.

  Persistence: "No (Recommended)" → write `workflow.use_worktrees: false`; "Leave unchanged" → do not write `workflow.use_worktrees` at all (preserve the existing value or absence).

  Pre-selection: the generic "current values pre-selected" rule does not apply when `INSPECTED_ISOLATION` is `none` — an explicit `true` has no matching option by design. Pre-select "No (Recommended)" in every case, including an absent key (`$USE_WORKTREES_CURRENT` empty, the no-`--default` read's absent signal): absence resolves to `false` only where this emit stamped that default and to `true` otherwise, so leaving it absent can preserve the very state this branch prevents, while an explicit `false` is correct under either emit (#2486 review). The same applies when it is an explicit non-false value — the broken-inheritance case the notice below covers. "Leave unchanged" remains available for the deliberate shared-config case, but is never the default here. The default must be the repair the "(Recommended)" label points to, so accepting it never keeps a value this branch could not justify. In TEXT_MODE, mark that option as the default in the numbered list.

  Additionally, if `$USE_WORKTREES_CURRENT` is non-empty and not `false` (the config carries an explicit `true` — e.g. inherited from a worktree-capable install sharing the repo; empty means the key is absent, which needs no notice), prepend this notice before the question:

```
Note: the project config currently sets workflow.use_worktrees: true.
{FINDING}, so {CONSEQUENCE}. Choose "No" to repair it for this runtime, or
"Leave unchanged" to keep it for a worktree-capable install that shares this
config.
```

```
// Model profile is selected via a two-question split because AskUserQuestion enforces a
// hard 4-option cap and there are 5 valid profiles (quality, balanced, budget, adaptive,
// inherit). Q1 routes between adaptive/standard-tier/inherit; Q2 (shown only when the
// user chose "Standard tier" in Q1) picks among the three standard profiles. (#3784)
AskUserQuestion([
  {
    question: "Which model profile for agents?",
    header: "Model",
    multiSelect: false,
    options: [
      { label: "Adaptive (Recommended)", description: "Role-based cost optimization: heavy roles use the highest-tier model available on the active runtime, light roles use the cheapest. Best balance of quality and cost across all supported runtimes (Claude, Codex, Gemini, OpenRouter, local)." },
      { label: "Standard tier…", description: "Choose Quality, Balanced, or Budget — flat tier applied to all agents" },
      { label: "Inherit", description: "Use current session model for all agents (required for non-Claude runtimes: Codex, Gemini CLI, OpenRouter, local models)" }
    ]
  }
])

**Conditional visibility — model_profile (Q2):**
  Only ask this question when Q1's answer is "Standard tier…".
  If Q1 = "Adaptive (Recommended)" → write model_profile=adaptive and SKIP Q2.
  If Q1 = "Inherit"                → write model_profile=inherit and SKIP Q2.
  If user cancels Q2 after picking "Standard tier…" → leave existing model_profile value unchanged (mirror code_review_depth's cancellation rule).

AskUserQuestion([
  {
    question: "Which standard profile? (Quality / Balanced / Budget)",
    header: "Model Tier",
    multiSelect: false,
    options: [
      { label: "Quality", description: "Opus everywhere except verification (highest cost) — Claude only" },
      { label: "Balanced", description: "Opus for planning, Sonnet for research/execution/verification — Claude only" },
      { label: "Budget", description: "Sonnet for writing, Haiku for research/verification (lowest cost) — Claude only" }
    ]
  }
])

// Map UI choices → config values:
//   Q1 "Adaptive (Recommended)" → model_profile = "adaptive"
//   Q1 "Inherit"                → model_profile = "inherit"
//   Q1 "Standard tier…" + Q2 "Quality"   → model_profile = "quality"
//   Q1 "Standard tier…" + Q2 "Balanced"  → model_profile = "balanced"
//   Q1 "Standard tier…" + Q2 "Budget"    → model_profile = "budget"

AskUserQuestion([
  {
    question: "Spawn Plan Researcher? (researches domain before planning)",
    header: "Research",
    multiSelect: false,
    options: [
      { label: "Yes", description: "Research phase goals before planning" },
      { label: "No", description: "Skip research, plan directly" }
    ]
  },
  {
    question: "Spawn Plan Checker? (verifies plans before execution)",
    header: "Plan Check",
    multiSelect: false,
    options: [
      { label: "Yes", description: "Verify plans meet phase goals" },
      { label: "No", description: "Skip plan verification" }
    ]
  },
  {
    question: "Spawn Execution Verifier? (verifies phase completion)",
    header: "Verifier",
    multiSelect: false,
    options: [
      { label: "Yes", description: "Verify must-haves after execution" },
      { label: "No", description: "Skip post-execution verification" }
    ]
  },
  {
    question: "Enable Plan Drift Guard? (verifies that symbols cited in plans exist in source at review time)",
    header: "Drift Guard",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Resolve symbol references (decorators, classes, functions, CLI flags) against live source — catches hallucinated names before execution. Authority controlled by plan_review.source_grounding_authority (default: grep)." },
      { label: "No", description: "Skip symbol grounding. Plan review proceeds without source verification." }
    ]
  },
  {
    question: "Enable TDD Mode? (RED/GREEN/REFACTOR gates for eligible tasks)",
    header: "TDD",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Execute tasks normally. Tests written alongside implementation." },
      { label: "Yes", description: "Planner applies type:tdd to business logic/APIs/validations; executor enforces gate sequence. End-of-phase review checks compliance." }
    ]
  },
  {
    question: "Enable Code Review? (/workflow:code-review and /workflow:code-review --fix commands)",
    header: "Code Review",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Enable /workflow:code-review commands for reviewing source files changed during a phase." },
      { label: "No", description: "Commands exit with a configuration gate message. Use when code review is handled externally." }
    ]
  },
  // Conditional: include the following code_review_depth question ONLY when the user's
  // chosen code_review value is "Yes". If code_review is "No", omit this question from
  // the AskUserQuestion call and do not touch the existing workflow.code_review_depth value.
  {
    question: "Code Review Depth? (default depth for /workflow:code-review — override per-run with --depth=)",
    header: "Review Depth",
    multiSelect: false,
    options: [
      { label: "Standard (Recommended)", description: "Per-file analysis. Balanced cost and signal." },
      { label: "Quick", description: "Pattern-matching only. Fastest, lowest cost." },
      { label: "Deep", description: "Cross-file analysis with import graphs. Highest cost, highest signal." }
    ]
  },
  {
    question: "Enable UI Review? (visual quality audit via /workflow:ui-review in autonomous mode)",
    header: "UI Review",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Run visual quality audit after phase execution in autonomous mode." },
      { label: "No", description: "Skip the UI audit step. Good for backend-only projects." }
    ]
  },
  {
    question: "Auto-advance pipeline? (discuss → plan → execute automatically)",
    header: "Auto",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Manual /clear + paste between stages" },
      { label: "Yes", description: "Chain stages via Agent() subagents (same isolation)" }
    ]
  },
  {
    question: "Run Pattern Mapper? (maps new files to existing codebase analogs between research and planning)",
    header: "Pattern Mapper",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "pattern-mapper runs between research and plan steps. Surfaces conventions so new code follows house style." },
      { label: "No", description: "Skip pattern mapping. Faster; lose consistency hinting for new files." }
    ]
  },
  {
    question: "Enable Nyquist Validation? (researches test coverage during planning)",
    header: "Nyquist",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Research automated test coverage during plan-phase. Adds validation requirements to plans. Blocks approval if tasks lack automated verify." },
      { label: "No", description: "Skip validation research. Good for rapid prototyping or no-test phases." }
    ]
  },
  // Note: Nyquist validation depends on research output. If research is disabled,
  // plan-phase automatically skips Nyquist steps (no RESEARCH.md to extract from).
  {
    question: "Enable UI Phase? (generates UI-SPEC.md design contracts for frontend phases)",
    header: "UI Phase",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Generate UI design contracts before planning frontend phases. Locks spacing, typography, color, and copywriting." },
      { label: "No", description: "Skip UI-SPEC generation. Good for backend-only projects or API phases." }
    ]
  },
  {
    question: "Enable UI Safety Gate? (prompts to run /workflow:ui-phase before planning frontend phases)",
    header: "UI Gate",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "plan-phase asks to run /workflow:ui-phase first when frontend indicators detected." },
      { label: "No", description: "No prompt — plan-phase proceeds without UI-SPEC check." }
    ]
  },
  {
    question: "Enable AI Phase? (framework selection + eval strategy for AI phases)",
    header: "AI Phase",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Run /workflow:ai-integration-phase before planning AI system phases. Surfaces the right framework, researches its docs, and designs the evaluation strategy." },
      { label: "No", description: "Skip AI design contract. Good for non-AI phases or when framework is already decided." }
    ]
  },
  {
    question: "Git branching strategy?",
    header: "Branching",
    multiSelect: false,
    options: [
      { label: "None (Recommended)", description: "Commit directly to current branch" },
      { label: "Per Phase", description: "Create branch for each phase (workflow/phase-{N}-{name})" },
      { label: "Per Milestone", description: "Create branch for entire milestone (workflow/{version}-{name})" }
    ]
  },
  {
    question: "Create git tags on milestone completion?",
    header: "Git Tagging",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Tag releases with version (e.g., v1.0) on milestone completion" },
      { label: "No", description: "Skip git tagging — use if your project doesn't use tags or uses a different release convention" }
    ]
  },
  {
    question: "Enable context window warnings? (injects advisory messages when context is getting full)",
    header: "Ctx Warnings",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Warn when context usage exceeds 65%. Helps avoid losing work." },
      { label: "No", description: "Disable warnings. Allows Claude to reach auto-compact naturally. Good for long unattended runs." }
    ]
  },
  {
    question: "Use token-minimized instruction content where available? (smaller context footprint)",
    header: "Compact Content",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Full instruction detail loaded every time." },
      { label: "Yes", description: "Terser instructions where a compact variant exists; canonical detail loads only when actually needed." }
    ]
  },
  {
    question: "Research best practices before asking questions? (web search during new-project and discuss-phase)",
    header: "Research Qs",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Ask questions directly. Faster, uses fewer tokens." },
      { label: "Yes", description: "Search web for best practices before each question group. More informed questions but uses more tokens." }
    ]
  },
  {
    question: "Commit .planning/ files to git? (controls whether plans/artifacts are tracked in your repo)",
    header: "Commit Docs",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Commit .planning/ to git. Plans, research, and phase artifacts travel with the repo." },
      { label: "No", description: "Do not commit .planning/. Keep planning local only. Automatic when .planning/ is in .gitignore." }
    ]
  },
  {
    question: "Skip discuss-phase in autonomous mode? (use ROADMAP phase goals as spec)",
    header: "Skip Discuss",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Run smart discuss before each phase — surfaces gray areas and captures decisions." },
      { label: "Yes", description: "Skip discuss in /workflow:autonomous — chain directly to plan. Best for backend/pipeline work where phase descriptions are the spec." }
    ]
  },
  {
    question: "Use git worktrees for parallel agent isolation?",
    header: "Worktrees",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Each parallel executor runs in its own worktree branch — no conflicts between agents." },
      { label: "No", description: "Disable worktree isolation. Agents run sequentially on the main working tree. Use if EnterWorktree creates branches from wrong base (known cross-platform issue)." }
    ]
  },
  {
    question: "Enable Intel? (queryable codebase intelligence via /workflow:map-codebase --query — builds a JSON index in .planning/intel/)",
    header: "Intel",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Skip intel indexing. Use when codebase is small or intel queries are not needed." },
      { label: "Yes", description: "Enable /workflow:map-codebase --query commands. Builds and queries a JSON index of the codebase." }
    ]
  },
  {
    question: "Enable Graphify? (project knowledge graph via /workflow:graphify — builds a graph in .planning/graphs/)",
    header: "Graphify",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Skip knowledge graph. Use when dependency graphs are not needed." },
      { label: "Yes", description: "Enable /workflow:graphify commands. Builds and queries a project knowledge graph." }
    ]
  },
  {
    question: "Auto-rebuild graph after main HEAD advances? (only effective if Graphify is enabled — #3347)",
    header: "Graph auto-update",
    multiSelect: false,
    options: [
      { label: "No (Recommended)", description: "Manual /workflow:graphify build only. Conservative default — opt in if you want fresh context on every /workflow:quick or /workflow:plan-phase." },
      { label: "Yes", description: "Auto-rebuild the graph in a detached background process after git commit/merge/pull/rebase --continue/cherry-pick on the default branch. Hook returns instantly; rebuild runs out-of-band. No-op if Graphify is disabled." }
    ]
  }
])
```
</step>

<step name="update_config">
Merge new settings into existing config.json:

```json
{
  ...existing_config,
  "model_profile": "quality" | "balanced" | "budget" | "adaptive" | "inherit",
  "commit_docs": true/false,
  "workflow": {
    "research": true/false,
    "plan_check": true/false,
    "verifier": true/false,
    "auto_advance": true/false,
    "nyquist_validation": true/false,
    "pattern_mapper": true/false,
    "ui_phase": true/false,
    "ui_safety_gate": true/false,
    "ai_integration_phase": true/false,
    "tdd_mode": true/false,
    "code_review": true/false,
    "code_review_depth": "quick" | "standard" | "deep",
    "ui_review": true/false,
    "text_mode": true/false,
    "research_before_questions": true/false,
    "discuss_mode": "discuss" | "assumptions",
    "skip_discuss": true/false,
    "use_worktrees": true/false,  // never written as true when the runtime's dispatch.isolation is none; omitted entirely when the user chose "Leave unchanged" (#2486)
    "compact_content": true/false
  },
  "plan_review": {
    "source_grounding": true/false
  },
  "intel": {
    "enabled": true/false
  },
  "graphify": {
    "enabled": true/false,
    "auto_update": true/false
  },
  "git": {
    "branching_strategy": "none" | "phase" | "milestone",
    "quick_branch_template": <string|null>,
    "create_tag": true/false
  },
  "hooks": {
    "context_warnings": true/false,
    "workflow_guard": true/false
  },
  "model_policy": {
    // Read-only in this flow — written only by /workflow:config --advanced (Section 8).
    // Listed here so safe-merge never clobbers an existing model_policy object.
    "provider": <existing|null>,
    "budget": <existing|null>,
    "high": <existing|null>,
    "medium": <existing|null>,
    "low": <existing|null>
  }
}
```

**Safe merge:** Apply each chosen value so unrelated keys are never clobbered. Use the appropriate write path per key:

- **Capability hook-gate keys** (owned by a capability in the registry — see `registry.configSchema`): write via the capability writer:
  ```bash
  workflow_run capability set <owner> --gate <key>=<value> [--config-dir "$RUNTIME_CONFIG_DIR"]
  ```
  The capability-owned keys written by this workflow and their owners are:
  | Key | Owner capability |
  |---|---|
  | `workflow.research` | `research` |
  | `workflow.nyquist_validation` | `nyquist` |
  | `workflow.pattern_mapper` | `pattern-mapper` |
  | `workflow.ui_phase` | `ui` |
  | `workflow.ui_safety_gate` | `ui` |
  | `workflow.ai_integration_phase` | `ai-integration` |
  | `workflow.tdd_mode` | `tdd` |
  | `workflow.code_review` | `code-review` |
  | `workflow.code_review_depth` | `code-review` |
  | `workflow.ui_review` | `ui` |
  | `intel.enabled` | `intel` |
  | `graphify.enabled` | `graphify` |

  `code_review_depth` is written only if the `code_review` question was answered `on`; otherwise leave the existing value in place.

- **Non-capability keys** (`model_profile`, `commit_docs`, `workflow.plan_check`, `workflow.verifier`, `workflow.auto_advance`, `workflow.text_mode`, `workflow.compact_content`, `workflow.research_before_questions`, `workflow.discuss_mode`, `workflow.skip_discuss`, `workflow.use_worktrees`, `plan_review.source_grounding`, `graphify.auto_update`, `git.*`, `hooks.*`, `model_policy.*`): write via `workflow_run query config-set <key.path> <value>` as before.

`model_profile` is written on Q1 "Adaptive (Recommended)" (→ adaptive) or Q1 "Inherit" (→ inherit) immediately; for Q1 "Standard tier…", `model_profile` is written from Q2's answer. If Q1 = "Standard tier…" but Q2 is cancelled, leave the existing `model_profile` value unchanged — do not write any new value.

Write updated config to `$Workflow_CONFIG_PATH` (the workstream-aware path resolved in `ensure_and_load_config`). Never hardcode `.planning/config.json` — workstream installs route to `.planning/workstreams/<slug>/config.json`.
</step>

<step name="save_as_defaults">
Ask whether to save these settings as global defaults for future projects:

```
AskUserQuestion([
  {
    question: "Save these as default settings for all new projects?",
    header: "Defaults",
    multiSelect: false,
    options: [
      { label: "Yes", description: "New projects start with these settings (saved to ~/.workflow/defaults.json)" },
      { label: "No", description: "Only apply to this project" }
    ]
  }
])
```

If "Yes": write the same config object (minus project-specific fields like `brave_search`) to `~/.workflow/defaults.json`:

```bash
mkdir -p ~/.workflow
```

Write `~/.workflow/defaults.json` with:
```json
{
  "mode": <current>,
  "granularity": <current>,
  "model_profile": <current>,
  "commit_docs": <current>,
  "parallelization": <current>,
  "branching_strategy": <current>,
  "quick_branch_template": <current>,
  "workflow": {
    "research": <current>,
    "plan_check": <current>,
    "verifier": <current>,
    "auto_advance": <current>,
    "nyquist_validation": <current>,
    "pattern_mapper": <current>,
    "ui_phase": <current>,
    "ui_safety_gate": <current>,
    "ai_integration_phase": <current>,
    "tdd_mode": <current>,
    "code_review": <current>,
    "code_review_depth": <current>,
    "ui_review": <current>,
    "skip_discuss": <current>,
    "compact_content": <current>
  },
  "plan_review": {
    "source_grounding": <current>
  },
  "intel": {
    "enabled": <current>
  },
  "graphify": {
    "enabled": <current>,
    "auto_update": <current>
  }
}
```
</step>

<step name="confirm">
Display:

```
### Workflow ► SETTINGS UPDATED

| Setting              | Value |
|----------------------|-------|
| Model Profile        | {quality/balanced/budget/adaptive/inherit} |
| Plan Researcher      | {On/Off} |
| Plan Checker         | {On/Off} |
| Pattern Mapper       | {On/Off} |
| Execution Verifier   | {On/Off} |
| TDD Mode             | {On/Off} |
| Code Review          | {On/Off} |
| Plan Drift Guard     | {On/Off} |
| Code Review Depth    | {quick/standard/deep} |
| UI Review            | {On/Off} |
| Commit Docs          | {On/Off} |
| Intel                | {On/Off} |
| Graphify             | {On/Off} |
| Auto-Advance         | {On/Off} |
| Nyquist Validation   | {On/Off} |
| UI Phase             | {On/Off} |
| UI Safety Gate       | {On/Off} |
| AI Integration Phase | {On/Off} |
| Git Branching        | {None/Per Phase/Per Milestone} |
| Git Tagging          | {On/Off} |
| Skip Discuss         | {On/Off} |
| Context Warnings     | {On/Off} |
| Compact Content      | {On/Off} |
| Saved as Defaults    | {Yes/No} |

These settings apply to future /workflow:plan-phase and /workflow:execute-phase runs.

Quick commands:
- /workflow:config --integrations — configure API keys (Brave/Firecrawl/Exa), review.models CLI routing, and agent_skills injection
- /workflow:config --profile <profile> — switch model profile
- /workflow:plan-phase --research — force research
- /workflow:plan-phase --skip-research — skip research
- /workflow:plan-phase --skip-verify — skip plan check
- /workflow:config --advanced — power-user tuning (plan bounce, timeouts, branch templates, cross-AI, context window, model policy)
```
</step>

</process>

<success_criteria>
- [ ] Current config read
- [ ] User presented with 25 settings (profile + workflow toggles + features + git branching + git tagging + ctx warnings + compact content), grouped into six sections: Planning, Execution, Docs & Output, Features, Model & Pipeline, Misc. `code_review_depth` is conditional on `code_review=on`. Model profile uses a two-question split (Q1: Adaptive / Standard tier / Inherit; Q2: Quality / Balanced / Budget — only when Standard tier chosen) to stay within the 4-option AskUserQuestion cap while exposing all 5 valid profiles (#3784). Drift Guard (`plan_review.source_grounding`) is in the Planning section.
- [ ] Config updated with model_profile, workflow, and git sections
- [ ] User offered to save as global defaults (~/.workflow/defaults.json)
- [ ] Changes confirmed to user
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
