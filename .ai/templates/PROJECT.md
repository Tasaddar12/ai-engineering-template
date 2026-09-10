---
tier: intent
authority: human
id: PROJECT
title: <Project name>
links: []
---

# <Project name>

> **`intent` tier — human authority.** Agents propose changes here; they do not
> make them. Everything else under `.ai/` is downstream of this file.

## Why this exists

Two or three sentences. The problem, and who has it. Not the solution.

## What success looks like

Observable outcomes, not features. "A new engineer ships a change on day one",
not "we have documentation".

- 
- 

## Non-goals

The most valuable section in this file. Every entry here is a spec an agent
will not write and a plan it will not propose. Be specific about the plausible
adjacent things you are deliberately not doing.

- 
- 

## Hard constraints

Things no spec may violate and no amendment may relax. If a constraint here
turns out to be wrong, a human changes it.

- 
- 

## Out of bounds for agents

Actions requiring a human, beyond the defaults in
[RULES.md](../RULES.md#when-you-are-genuinely-blocked). Examples: touching
production data, rotating credentials, publishing packages, changing billing.

- 

## Stakeholders

Who decides, who reviews, who to ask when blocked.

| Role | Who |
|---|---|
| Decides scope | |
| Reviews code | |
| Owns the specs | |
