# Planner Subagent Prompt Template

Template for spawning planner agent. The agent contains all planning expertise - this template provides planning context only.

---

## Template

```markdown
<planning_context>

**Phase:** {phase_number}
**Mode:** {standard | gap_closure}

**Project State:**
@.planning/STATE.md

**Roadmap:**
@.planning/ROADMAP.md

**Requirements (if exists):**
@.planning/REQUIREMENTS.md

**Phase Context (if exists):**
@.planning/phases/{phase_dir}/{phase_num}-CONTEXT.md

**Research (if exists):**
@.planning/phases/{phase_dir}/{phase_num}-RESEARCH.md

**Gap Closure (when Mode is gap_closure):**
@.planning/phases/{phase_dir}/{phase_num}-VERIFICATION.md
@.planning/phases/{phase_dir}/{phase_num}-UAT.md

</planning_context>

<downstream_consumer>
Output consumed by phase-start
Plans must be executable prompts with:
- Frontmatter (wave, depends_on, files_modified, autonomous)
- Tasks in XML format
- Verification criteria
- must_haves for goal-backward verification
</downstream_consumer>

<quality_gate>
Before returning PLANNING COMPLETE:
- [ ] PLAN.md files created in phase directory
- [ ] Each plan has valid frontmatter
- [ ] Tasks are specific and actionable
- [ ] Dependencies correctly identified
- [ ] Waves assigned for parallel execution
- [ ] must_haves derived from phase goal
</quality_gate>
```

---

## Placeholders

| Placeholder | Source | Example |
|-------------|--------|---------|
| `{phase_number}` | From roadmap/arguments | `5` or `2.1` |
| `{phase_dir}` | Phase directory name | `05-user-profiles` |
| `{phase}` | Phase prefix | `05` |
| `{standard \| gap_closure}` | Coordinator-assigned planning mode | `standard` |

---

## Usage

The `Task(...)` examples are host pseudocode. Use the available host dispatcher with the installed `phase-preparer` role; they are not Python runtime commands.

**From phase-prepare (standard mode):**
```python
Task(
  prompt=filled_template,
  subagent_type="phase-preparer",
  description="Plan Phase {phase}"
)
```

**From phase-prepare with the recorded verification gaps (gap closure mode):**
```python
Task(
  prompt=filled_template,  # with mode: gap_closure
  subagent_type="phase-preparer",
  description="Plan gaps for Phase {phase}"
)
```

---

## Continuation

For checkpoints, spawn fresh agent with:

```markdown
<objective>
Continue planning for Phase {phase_number}: {phase_name}
</objective>

<prior_state>
Phase directory: @.planning/phases/{phase_dir}/
Existing plans: @.planning/phases/{phase_dir}/*-PLAN.md
</prior_state>

<checkpoint_response>
**Type:** {checkpoint_type}
**Response:** {user_response}
</checkpoint_response>

<mode>
Continue: {standard | gap_closure}
</mode>
```

---

**Note:** Planning methodology, task breakdown, dependency analysis, wave assignment, TDD detection, and goal-backward derivation are baked into the planner agent. This template only passes context.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

Read this complete authoring guide, including its examples and methods.
Source attribution is available in `.ai/THIRD-PARTY-NOTICES.md`.

Read `.ai/agents/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. Only the documented local runtime commands are installed. Tool names and product
examples do not establish that a tool is available; inspect the actual project
configuration and host capabilities before using them. Bundled supporting methods provide local guidance for explicit assignments;
they do not install additional runtime features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
