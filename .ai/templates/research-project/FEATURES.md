# Features Research Template

Template for `.planning/research/FEATURES.md` — feature landscape for the project domain.

<template>

```markdown
# Feature Research

**Domain:** [domain type]
**Researched:** [date]
**Confidence:** [HIGH/MEDIUM/LOW]

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| [feature] | [user expectation] | LOW/MEDIUM/HIGH | [implementation notes] |
| [feature] | [user expectation] | LOW/MEDIUM/HIGH | [implementation notes] |
| [feature] | [user expectation] | LOW/MEDIUM/HIGH | [implementation notes] |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| [feature] | [why it matters] | LOW/MEDIUM/HIGH | [implementation notes] |
| [feature] | [why it matters] | LOW/MEDIUM/HIGH | [implementation notes] |
| [feature] | [why it matters] | LOW/MEDIUM/HIGH | [implementation notes] |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| [feature] | [surface appeal] | [actual problems] | [better approach] |
| [feature] | [surface appeal] | [actual problems] | [better approach] |

## Feature Dependencies

```
[Feature A]
    └──requires──> [Feature B]
                       └──requires──> [Feature C]

[Feature D] ──enhances──> [Feature A]

[Feature E] ──conflicts──> [Feature F]
```

### Dependency Notes

- **[Feature A] requires [Feature B]:** [why the dependency exists]
- **[Feature D] enhances [Feature A]:** [how they work together]
- **[Feature E] conflicts with [Feature F]:** [why they're incompatible]

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] [Feature] — [why essential]
- [ ] [Feature] — [why essential]
- [ ] [Feature] — [why essential]

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] [Feature] — [trigger for adding]
- [ ] [Feature] — [trigger for adding]

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] [Feature] — [why defer]
- [ ] [Feature] — [why defer]

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| [feature] | HIGH/MEDIUM/LOW | HIGH/MEDIUM/LOW | P1/P2/P3 |
| [feature] | HIGH/MEDIUM/LOW | HIGH/MEDIUM/LOW | P1/P2/P3 |
| [feature] | HIGH/MEDIUM/LOW | HIGH/MEDIUM/LOW | P1/P2/P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Competitor A | Competitor B | Our Approach |
|---------|--------------|--------------|--------------|
| [feature] | [how they do it] | [how they do it] | [our plan] |
| [feature] | [how they do it] | [how they do it] | [our plan] |

## Sources

- [Competitor products analyzed]
- [User research or feedback sources]
- [Industry standards referenced]

---
*Feature research for: [domain]*
*Researched: [date]*
```

</template>

<guidelines>

**Table Stakes:**
- These are non-negotiable for launch
- Users don't give credit for having them, but penalize for missing them
- Example: A community platform without user profiles is broken

**Differentiators:**
- These are where you compete
- Should align with the Core Value from PROJECT.md
- Don't try to differentiate on everything

**Anti-Features:**
- Prevent scope creep by documenting what seems good but isn't
- Include the alternative approach
- Example: "Real-time everything" often creates complexity without value

**Feature Dependencies:**
- Critical for roadmap phase ordering
- If A requires B, B must be in an earlier phase
- Conflicts inform what NOT to combine in same phase

**MVP Definition:**
- Be ruthless about what's truly minimum
- "Nice to have" is not MVP
- Launch with less, validate, then expand

</guidelines>


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
