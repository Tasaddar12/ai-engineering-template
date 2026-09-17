# Architecture Research Template

Template for `.planning/research/ARCHITECTURE.md` — system structure patterns for the project domain.

<template>

```markdown
# Architecture Research

**Domain:** [domain type]
**Researched:** [date]
**Confidence:** [HIGH/MEDIUM/LOW]

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        [Layer Name]                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ [Comp]  │  │ [Comp]  │  │ [Comp]  │  │ [Comp]  │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
├───────┴────────────┴────────────┴────────────┴──────────────┤
│                        [Layer Name]                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    [Component]                       │    │
│  └─────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────┤
│                        [Layer Name]                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │ [Store]  │  │ [Store]  │  │ [Store]  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| [name] | [what it owns] | [how it's usually built] |
| [name] | [what it owns] | [how it's usually built] |
| [name] | [what it owns] | [how it's usually built] |

## Recommended Project Structure

```
src/
├── [folder]/           # [purpose]
│   ├── [subfolder]/    # [purpose]
│   └── [file].ts       # [purpose]
├── [folder]/           # [purpose]
│   ├── [subfolder]/    # [purpose]
│   └── [file].ts       # [purpose]
├── [folder]/           # [purpose]
└── [folder]/           # [purpose]
```

### Structure Rationale

- **[folder]/:** [why organized this way]
- **[folder]/:** [why organized this way]

## Architectural Patterns

### Pattern 1: [Pattern Name]

**What:** [description]
**When to use:** [conditions]
**Trade-offs:** [pros and cons]

**Example:**
```typescript
// [Brief code example showing the pattern]
```

### Pattern 2: [Pattern Name]

**What:** [description]
**When to use:** [conditions]
**Trade-offs:** [pros and cons]

**Example:**
```typescript
// [Brief code example showing the pattern]
```

### Pattern 3: [Pattern Name]

**What:** [description]
**When to use:** [conditions]
**Trade-offs:** [pros and cons]

## Data Flow

### Request Flow

```
[User Action]
    ↓
[Component] → [Handler] → [Service] → [Data Store]
    ↓              ↓           ↓            ↓
[Response] ← [Transform] ← [Query] ← [Database]
```

### State Management

```
[State Store]
    ↓ (subscribe)
[Components] ←→ [Actions] → [Reducers/Mutations] → [State Store]
```

### Key Data Flows

1. **[Flow name]:** [description of how data moves]
2. **[Flow name]:** [description of how data moves]

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-1k users | [approach — usually monolith is fine] |
| 1k-100k users | [approach — what to optimize first] |
| 100k+ users | [approach — when to consider splitting] |

### Scaling Priorities

1. **First bottleneck:** [what breaks first, how to fix]
2. **Second bottleneck:** [what breaks next, how to fix]

## Anti-Patterns

### Anti-Pattern 1: [Name]

**What people do:** [the mistake]
**Why it's wrong:** [the problem it causes]
**Do this instead:** [the correct approach]

### Anti-Pattern 2: [Name]

**What people do:** [the mistake]
**Why it's wrong:** [the problem it causes]
**Do this instead:** [the correct approach]

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| [service] | [how to connect] | [gotchas] |
| [service] | [how to connect] | [gotchas] |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| [module A ↔ module B] | [API/events/direct] | [considerations] |

## Sources

- [Architecture references]
- [Official documentation]
- [Case studies]

---
*Architecture research for: [domain]*
*Researched: [date]*
```

</template>

<guidelines>

**System Overview:**
- Use ASCII box-drawing diagrams for clarity (├── └── │ ─ for structure visualization only)
- Show major components and their relationships
- Don't over-detail — this is conceptual, not implementation

**Project Structure:**
- Be specific about folder organization
- Explain the rationale for grouping
- Match conventions of the chosen stack

**Patterns:**
- Include code examples where helpful
- Explain trade-offs honestly
- Note when patterns are overkill for small projects

**Scaling Considerations:**
- Be realistic — most projects don't need to scale to millions
- Focus on "what breaks first" not theoretical limits
- Avoid premature optimization recommendations

**Anti-Patterns:**
- Specific to this domain
- Include what to do instead
- Helps prevent common mistakes during implementation

</guidelines>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

Read this complete authoring guide, including its examples and methods.
Source attribution is available in `.ai/THIRD-PARTY-NOTICES.md`.

Read `.ai/agents/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/runtime/README.md` (Template runtime behavior) for local runtime behavior,
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
