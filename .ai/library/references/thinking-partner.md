# Thinking Partner Integration

Conditional extended thinking at workflow decision points. Activates when `features.thinking_partner: true` in `.planning/config.json` (default: false).

---

## Tradeoff Detection Signals

The thinking partner activates when developer responses contain specific signals indicating competing priorities:

**Keyword signals:**
- "or" / "versus" / "vs" connecting two approaches
- "tradeoff" / "trade-off" / "tradeoffs"
- "on one hand" / "on the other hand"
- "pros and cons"
- "not sure between" / "torn between"

**Structural signals:**
- Developer lists 2+ competing options
- Developer asks "which is better" or "what would you recommend"
- Developer reverses a previous decision ("actually, maybe we should...")

**When NOT to activate:**
- Developer has already made a clear choice
- The "or" is rhetorical or trivial (e.g., "tabs or spaces" — use project convention)
- Simple yes/no questions
- Developer explicitly asks to move on

---

## Integration Points

### 1. Discuss Phase — Tradeoff Deep-Dive

**When:** During `discuss_areas` step, after a developer answer reveals competing priorities.

**What:** Pause the normal question flow and offer a brief structured analysis:
```
I notice competing priorities here — {X} optimizes for {A} while {Y} optimizes for {B}.

Want me to think through the tradeoffs before we decide?
[Yes, analyze tradeoffs] / [No, I've decided]
```

If yes, provide a brief (3-5 bullet) analysis covering:
- What each approach optimizes for
- What each approach sacrifices
- Which aligns better with the project's stated goals (from PROJECT.md)
- A recommendation with reasoning

Then return to the normal discussion flow.

### 2. Plan Phase — Architectural Decision Analysis

**When:** During step 11 (Handle Checker Return), when the plan-checker flags issues containing architectural tradeoff keywords.

**What:** Before sending to the revision loop, analyze the architectural decision:
```
The plan-checker flagged an architectural tradeoff: {issue description}

Brief analysis:
- Option A: {approach} — {pros/cons}
- Option B: {approach} — {pros/cons}
- Recommendation: {choice} because {reasoning aligned with phase goals}

Apply this recommendation to the revision? [Yes] / [No, let me decide]
```

### 3. Explore — Approach Comparison (requires #1729)

**When:** During Socratic conversation, when multiple viable approaches emerge.
**Note:** This integration point will be added when /workflow:explore (#1729) lands.

---

## Configuration

```json
{
  "features": {
    "thinking_partner": true
  }
}
```

Default: `false`. The thinking partner is opt-in because it adds latency to interactive workflows.

---

## Design Principles

1. **Lightweight** — inline analysis, not a separate interactive session
2. **Opt-in** — must be explicitly enabled, never activates by default
3. **Skippable** — always offer "No, I've decided" to bypass
4. **Brief** — 3-5 bullets max, not a full research report
5. **Aligned** — recommendations reference PROJECT.md goals when available


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
