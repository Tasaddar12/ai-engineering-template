# Planner Subagent Prompt Template

Template for spawning planner agent. The agent contains all planning expertise - this template provides planning context only.

---

## Template

```markdown
<planning_context>

**Phase:** {phase_number}
**Mode:** {standard | gap_closure}
**Repository:** {repository_root}
**Branch:** {branch}
**Input revision:** {input_revision}
**Owned outputs:** {owned_outputs}
**Required reading:** {read_first}
**Checks:** {checks_argv}
**Issue references:** {issue_refs}

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

**Gap Closure (if --gaps mode):**
@.planning/phases/{phase_dir}/{phase_num}-VERIFICATION.md
@.planning/phases/{phase_dir}/{phase_num}-UAT.md

</planning_context>

<downstream_consumer>
Output consumed by /execute-phase
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
| `{standard \| gap_closure}` | Mode flag | `standard` |
| `{repository_root}` | Coordinator assignment | Absolute assigned checkout |
| `{branch}` | Coordinator assignment | Assigned branch |
| `{input_revision}` | Captured Git revision | Full SHA |
| `{owned_outputs}` | Exact output ownership | PLAN paths only |
| `{read_first}` | Required inputs | Exact existing paths |
| `{checks_argv}` | Configured / assigned checks | argv lists or explicit none |
| `{issue_refs}` | Canonical issue register | URLs or Pending reasons |

## Usage

**From /plan-phase (standard mode):**
The following is host pseudocode; use the actual Claude or Codex dispatch API.

```python
Task(
  prompt=filled_template,
  subagent_type="planner",
  description="Plan Phase {phase}"
)
```

**From /plan-phase --gaps (gap closure mode):**
The following is host pseudocode; use the actual Claude or Codex dispatch API.

```python
Task(
  prompt=filled_template,  # with mode: gap_closure
  subagent_type="planner",
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

## Revision assignments

A correction assignment includes the original input revision, current artifact digest, exact finding IDs and authority, owned paths, required affected rechecks, preserved passing evidence and first continuation. Read the bounded correction packet from `engineer/workflows/plan-phase.md`; do not rediscover the repository or reinterpret approved scope. Verify the assigned repository/branch/revision before editing. Return revised artifacts and an evidence-linked disposition for every finding.
