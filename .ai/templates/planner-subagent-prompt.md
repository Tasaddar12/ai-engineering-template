# Planner Subagent Prompt Template

Template for spawning planner agent. The agent contains all planning expertise - this template provides planning context only.

---

## Template

```markdown
<planning_context>

**Phase:** {phase_number}
**Mode:** {standard | gap_closure}
**Checkout:** {absolute_worktree_path}
**Branch:** {assigned_branch}
**Input revision:** {commit_sha}
**Owned outputs:** {exact_PLAN_and_VALIDATION_paths}

**Source inputs:**
- {repository_relative_path} — {exact_symbol_and_question_this_file_answers}

**Consumed prior components:**
- {exact_SUMMARY_path} — {export_schema_command_or_decision_consumed}
Use `None` when this phase consumes no prior component; do not select history
just to fill this field.

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
Output consumed by execute-phase
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
| `{absolute_worktree_path}`, `{assigned_branch}`, `{commit_sha}` | Verified assigned Git checkout | Absolute root, branch and full input revision |
| `{exact_PLAN_and_VALIDATION_paths}` | Coordinator-owned output assignment | Exact repository-relative paths; omit VALIDATION when unneeded |
| Source/dependency fields | Inspected code and actual component prerequisites | Path, symbol and the question or contract it supplies |
| `{standard \| gap_closure}` | Coordinator-assigned planning mode | `standard` |

---

## Usage

The `Task(...)` examples are host pseudocode. Use the available host dispatcher with the installed `phase-preparer` role; they are not Python runtime commands.

**From plan-phase (standard mode):**
```python
Task(
  prompt=filled_template,
  subagent_type="phase-preparer",
  description="Plan Phase {phase}"
)
```

**From plan-phase with the recorded verification gaps (gap closure mode):**
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

For revision assignments, replace the standard context block with the exact
checkout/branch/revision, CONTEXT path, affected PLAN paths, prior checker report
and finding IDs, and changed source/contract paths. Apply
[correction rounds](../commands/plan-phase.md).
Do not paste PLAN bodies or the previous agent conversation. The preparer reads
the canonical files and preserves every concrete requirement it edits.


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

Read this complete authoring guide, including its examples and methods.
Source attribution is available in `.ai/THIRD-PARTY-NOTICES.md`.

Read `.ai/agents/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local runtime behavior,
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
