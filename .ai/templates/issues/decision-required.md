# Decision Required Issue Template

Use this template for Decision required issue bodies.

**Purpose:** Present an answerable choice and the work it will unblock.

**Key principle:** State a concrete choice and consequence for each option.

**Producer:** The coordinator or assigned author, using the actual blocking question.

**Downstream consumers:**

- Decision owner: compare evidence, alternatives and the recommendation.
- Planner and implementer: use the recorded choice and observable unblock condition.

**Destination:** A reviewed public issue body file.

Read this source in full, then copy only its fenced **File Template** into the
body file. Replace placeholders with known facts or explicit pending dependencies.
Follow the [Git workflow](../../references/git-workflow.md) for title and publication.

---

## File Template

```markdown
## Decision question
[One answerable sentence: decision and boundary.]

## Context
[2-3 sentences: current state, affected users/systems and impact.]

## Options

| Option | Choice | Consequence / tradeoff |
|---|---|---|
| A | [one-line choice] | [one-line consequence/tradeoff] |
| B | [one-line choice] | [one-line consequence/tradeoff] |
| C | [optional; one-line choice] | [optional; one-line consequence/tradeoff] |
| D | [optional; one-line choice] | [optional; one-line consequence/tradeoff] |

## Evidence
[1-3 actual safe evidence URLs/references; identify matching build/commit when applicable; no secrets.]

## Recommendation
[One sentence: preferred option and evidence-based reason.]

## Blocking dependency
| Blocked work | Decision needed | Observable unblock condition |
|---|---|---|
| [blocked work and actual issue/PR ref] | [choice required] | [one-sentence observable condition that allows work to resume] |

## Scope
- In: [bounded decision]
- Out: [related choices excluded]

## Acceptance
- [Outcome 1: record selected option and observable unblock condition]
- [Outcome 2: measurable decision outcome, if needed]
- [Outcome 3: if needed]

## Related links
[1-3 actual issue/PR/requirement references or accessible evidence URLs.]
```

## Good and bad examples

**Good example excerpt** (fictional):

```markdown
## Decision question
Should import previews expire after one day or seven days?

## Options
| Option | Choice | Consequence / tradeoff |
|---|---|---|
| A | Retain one day | Lower storage use; users repeat older previews. |
| B | Retain seven days | Longer review window; higher storage use. |

## Acceptance
- Record the selected retention period and the decision owner's rationale.
- Unblock implementation when the selected period is in the import requirement.
```

**Bad:** "Choose something for imports so we can continue."

## Guidelines

- Retain the File Template headings and order. Ask one bounded decision question;
  connect Context, Evidence and Recommendation to that choice.
- Provide two to four distinct options with concise consequences. Remove unused
  optional rows and record uncertainty beside the affected evidence.
- Identify the actual blocked work and observable unblock condition. Keep a
  recommendation distinct from the decision owner's recorded choice.

## Completion and downstream handoff

- Replace prompts and example values with the bounded question, alternatives,
  evidence and blocking dependency. If the decision is unmade, mark it pending.
- Hand off the reviewed body file to the decision owner under the Git workflow.
  Read back the saved body, then report its URL.
  If publication or readback fails, report the exact blocker.
