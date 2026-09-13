## 2a. Auto Mode Config (auto mode only)

**If auto mode:** Collect config settings upfront before processing the idea document.

YOLO mode is implicit (auto = YOLO). Ask remaining config questions:

**Round 1 — Core settings (3 questions, no Mode question):**

```
AskUserQuestion([
  {
    header: "Granularity",
    question: "How finely should scope be sliced into phases?",
    multiSelect: false,
    options: [
      { label: "Coarse (Recommended)", description: "Fewer, broader phases (3-5 phases, 1-3 plans each)" },
      { label: "Standard", description: "Balanced phase size (5-8 phases, 3-5 plans each)" },
      { label: "Fine", description: "Many focused phases (8-12 phases, 5-10 plans each)" }
    ]
  },
  {
    header: "Execution",
    question: "Run plans in parallel?",
    multiSelect: false,
    options: [
      { label: "Parallel (Recommended)", description: "Independent plans run simultaneously" },
      { label: "Sequential", description: "One plan at a time" }
    ]
  },
  {
    header: "Git Tracking",
    question: "Commit planning docs to git?",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Planning docs tracked in version control" },
      { label: "No", description: "Keep .planning/ local-only (add to .gitignore)" }
    ]
  }
])
```

**Round 2 — Workflow agents (same as Step 5):**

```
AskUserQuestion([
  {
    header: "Research",
    question: "Research before planning each phase? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Investigate domain, find patterns, surface gotchas" },
      { label: "No", description: "Plan directly from requirements" }
    ]
  },
  {
    header: "Plan Check",
    question: "Verify plans will achieve their goals? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Catch gaps before execution starts" },
      { label: "No", description: "Execute plans without verification" }
    ]
  },
  {
    header: "Verifier",
    question: "Verify work satisfies requirements after each phase? (adds tokens/time)",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Confirm deliverables match phase goals" },
      { label: "No", description: "Trust execution, skip verification" }
    ]
  },
  {
    header: "Drift Guard",
    question: "Enable the plan drift-guard? It verifies that symbols your plans cite (decorators, classes, functions, CLI flags) actually exist in your source at review time, catching hallucinated names before execution. [Y/n]",
    multiSelect: false,
    options: [
      { label: "Yes (Recommended)", description: "Resolve symbol references against live source during plan review — catches hallucinated names before execution" },
      { label: "No", description: "Skip symbol grounding — plan review proceeds without source verification" }
    ]
  }
])

// Model profile uses a two-question split because AskUserQuestion enforces a hard
// 4-option cap and there are 5 valid profiles (quality, balanced, budget, adaptive,
// inherit). Q1 routes between adaptive/standard-tier/inherit; Q2 (shown only when
// Q1 = "Standard tier…") picks among the three standard profiles. Mirrors the
// /workflow:settings split (#3784, #1516).
AskUserQuestion([
  {
    header: "AI Models",
    question: "Which AI models for planning agents?",
    multiSelect: false,
    options: [
      { label: "Adaptive (Recommended)", description: "Role-based cost optimization: heavy roles use the highest-tier model available on the active runtime, light roles use the cheapest. Best balance of quality and cost across all supported runtimes (Claude, Codex, Gemini, OpenRouter, local)." },
      { label: "Standard tier…", description: "Choose Quality, Balanced, or Budget — flat tier applied to all agents" },
      { label: "Inherit", description: "Use the current session model for all agents (required for non-Claude runtimes: Codex, Gemini CLI, OpenCode /model, OpenRouter, local models)" }
    ]
  }
])

**Conditional visibility — model_profile (Q2):**
  Only ask this question when Q1's answer is "Standard tier…".
  If Q1 = "Adaptive (Recommended)" → write model_profile=adaptive and SKIP Q2.
  If Q1 = "Inherit"                → write model_profile=inherit and SKIP Q2.
  If user cancels Q2 after picking "Standard tier…" → leave existing model_profile value unchanged.

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
//   Q1 "Adaptive (Recommended)"         → model_profile = "adaptive"
//   Q1 "Inherit"                        → model_profile = "inherit"
//   Q1 "Standard tier…" + Q2 "Quality"  → model_profile = "quality"
//   Q1 "Standard tier…" + Q2 "Balanced" → model_profile = "balanced"
//   Q1 "Standard tier…" + Q2 "Budget"   → model_profile = "budget"
```

**Round 3 — PR body onboarding:**

Ask which optional PRD-style sections `/workflow:ship` should append to generated PR bodies. These map to `ship.pr_body_sections`; selected sections are written with `"enabled": true`, unselected seeded sections are written with `"enabled": false` so the project can enable them later without editing `ship.md`.

Prefer lean/agile PRD sections that make the delivered increment clear: user stories, acceptance criteria, Definition of Done or release criteria, risks, dependencies, and stakeholder review.

```
AskUserQuestion([
  {
    header: "PR Body",
    question: "Which optional PRD-style sections should /workflow:ship include in PR bodies?",
    multiSelect: true,
    options: [
      { label: "User Stories & Acceptance Criteria", description: "Append user-facing stories and acceptance checks from REQUIREMENTS.md" },
      { label: "Risks & Dependencies", description: "Append rollout risks, dependencies, and rollback notes from PLAN.md" },
      { label: "Success Metrics & Release Criteria", description: "Append measurable Definition of Done and release checks for stakeholder review" },
      { label: "Stakeholder Review & Approval", description: "Append approval checklist for projects that need sign-off traceability" }
    ]
  }
])
```

Build `ship.pr_body_sections` from those choices. For selected options, set `enabled: true`; for seeded but unselected options, set `enabled: false`. If the user selects none, use `"ship":{"pr_body_sections":[]}`.

Create `.planning/config.json` with all settings (CLI fills in remaining defaults automatically):

```bash
_Workflow_SHIM_NAME="workflow-tools.cjs"; _Workflow_RUNTIME_ROOT="${RUNTIME_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"; Workflow_TOOLS="${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}"; _workflow_at() { for _p; do if [ -f "$_p" ]; then Workflow_TOOLS="$_p"; return 0; fi; done; return 1; }; if _workflow_at "${_Workflow_RUNTIME_ROOT}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.claude/workflow-core/bin/${_Workflow_SHIM_NAME}" "${_Workflow_RUNTIME_ROOT}/.codex/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; elif unset -f workflow_run; _G="$(command -v workflow_run)"; then Workflow_TOOLS="$_G"; workflow_run() { "$Workflow_TOOLS" "$@"; }; elif _workflow_at "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${HERMES_HOME:-$HOME/.hermes}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CURSOR_CONFIG_DIR:-$HOME/.cursor}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEX_HOME:-$HOME/.codex}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GEMINI_CONFIG_DIR:-$HOME/.gemini}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${COPILOT_CONFIG_DIR:-$HOME/.copilot}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${WINDSURF_CONFIG_DIR:-$HOME/.codeium/windsurf}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${AUGMENT_CONFIG_DIR:-$HOME/.augment}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${TRAE_CONFIG_DIR:-$HOME/.trae}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${QWEN_CONFIG_DIR:-$HOME/.qwen}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CODEBUDDY_CONFIG_DIR:-$HOME/.codebuddy}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${CLINE_CONFIG_DIR:-$HOME/.cline}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${GROK_AGENTS_HOME:-$HOME/.agents}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${ANTIGRAVITY_CONFIG_DIR:-$HOME/.gemini/antigravity}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${OPENCODE_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/opencode}/workflow-core/bin/${_Workflow_SHIM_NAME}" "${KILO_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/kilo}/workflow-core/bin/${_Workflow_SHIM_NAME}"; then workflow_run() { node "$Workflow_TOOLS" "$@"; }; else echo "ERROR: workflow-tools.cjs not found at $Workflow_TOOLS and workflow_run is not on PATH. Run: npx -y @openworkflow/workflow-core@latest --claude --local" >&2; exit 1; fi; Workflow_IDENTITY_STATUS=unverified; case "$(workflow_run runtime-identity --raw 2>/dev/null || true)" in '{"packageName":"@openworkflow/workflow-core"'*'}') Workflow_IDENTITY_STATUS=ok;; esac; export Workflow_IDENTITY_STATUS; [ "$Workflow_IDENTITY_STATUS" = ok ] || echo "WARNING: \"$Workflow_TOOLS\" did not prove it is @openworkflow/workflow-core - it is either a different package or an @openworkflow/workflow-core older than the runtime-identity verb. See docs/how-to/diagnose-a-foreign-workflow-tools.md" >&2; if [ -n "${CLAUDE_ENV_FILE:-}" ] && [ -n "${Workflow_TOOLS:-}" ]; then printf "export PATH='%s':\"\$PATH\"\n" "${Workflow_TOOLS%/*}" >> "$CLAUDE_ENV_FILE" 2>/dev/null || true; fi
mkdir -p .planning
workflow_run query config-new-project '{"mode":"yolo","granularity":"[selected]","parallelization":true|false,"commit_docs":true|false,"model_profile":"quality|balanced|budget|adaptive|inherit","workflow":{"research":true|false,"plan_check":true|false,"verifier":true|false,"nyquist_validation":true|false,"auto_advance":true},"plan_review":{"source_grounding":true|false},"ship":{"pr_body_sections":[{"heading":"User Stories & Acceptance Criteria","enabled":true|false,"source":"REQUIREMENTS.md ## User Stories || REQUIREMENTS.md ## Acceptance Criteria","fallback":"- Acceptance criteria are covered by the linked requirements and verification evidence."},{"heading":"Risks & Dependencies","enabled":true|false,"source":"PLAN.md ## Risks || PLAN.md ## Dependencies","fallback":"- No known high-risk rollout dependencies."},{"heading":"Success Metrics & Release Criteria","enabled":true|false,"source":"REQUIREMENTS.md ## Definition of Done || VERIFICATION.md ## Release Criteria","fallback":"- Release when automated verification and required manual checks pass."},{"heading":"Stakeholder Review & Approval","enabled":true|false,"template":"- Product owner approval pending for {phase_name}."}]}}'
```

**If commit_docs = No:** Add `.planning/` to `.gitignore`.

**Commit config.json:**

```bash
mkdir -p .planning
workflow_run query commit "chore: add project config" --files .planning/config.json
```

**Persist auto-advance chain flag to config (survives context compaction):**

```bash
workflow_run query config-set workflow._auto_chain_active true
```

Proceed to Step 4 (skip Steps 3 and 5).


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
