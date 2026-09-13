# Stack Research Template

Template for `.planning/research/STACK.md` — recommended technologies for the project domain.

<template>

```markdown
# Stack Research

**Domain:** [domain type]
**Researched:** [date]
**Confidence:** [HIGH/MEDIUM/LOW]

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| [name] | [version] | [what it does] | [why experts use it for this domain] |
| [name] | [version] | [what it does] | [why experts use it for this domain] |
| [name] | [version] | [what it does] | [why experts use it for this domain] |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| [name] | [version] | [what it does] | [specific use case] |
| [name] | [version] | [what it does] | [specific use case] |
| [name] | [version] | [what it does] | [specific use case] |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| [name] | [what it does] | [configuration tips] |
| [name] | [what it does] | [configuration tips] |

## Installation

```bash
# Core
npm install [packages]

# Supporting
npm install [packages]

# Dev dependencies
npm install -D [packages]
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| [our choice] | [other option] | [conditions where alternative is better] |
| [our choice] | [other option] | [conditions where alternative is better] |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| [technology] | [specific problem] | [recommended alternative] |
| [technology] | [specific problem] | [recommended alternative] |

## Stack Patterns by Variant

**If [condition]:**
- Use [variation]
- Because [reason]

**If [condition]:**
- Use [variation]
- Because [reason]

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| [package@version] | [package@version] | [compatibility notes] |

## Sources

- [Context7 library ID] — [topics fetched]
- [Official docs URL] — [what was verified]
- [Other source] — [confidence level]

---
*Stack research for: [domain]*
*Researched: [date]*
```

</template>

<guidelines>

**Core Technologies:**
- Include specific version numbers
- Explain why this is the standard choice, not just what it does
- Focus on technologies that affect architecture decisions

**Supporting Libraries:**
- Include libraries commonly needed for this domain
- Note when each is needed (not all projects need all libraries)

**Alternatives:**
- Don't just dismiss alternatives
- Explain when alternatives make sense
- Helps user make informed decisions if they disagree

**What NOT to Use:**
- Actively warn against outdated or problematic choices
- Explain the specific problem, not just "it's old"
- Provide the recommended alternative

**Version Compatibility:**
- Note any known compatibility issues
- Critical for avoiding debugging time later

</guidelines>


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

The complete upstream body above is retained from GSD-Core at
`c0b2a05d2f310adc0a1f35fd71fbc9f28f4e4977`; only recorded reference substitutions
and explicit local conflict corrections have been made. See
`.ai/gsd/PROVENANCE.json` for exact source hashes and changes.

Read `.ai/gsd/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/gsd-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The upstream `config.json`, `/gsd:*` commands, tool
names, hooks, and Node CLI examples describe GSD's system; this import does not
install or activate that system. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
