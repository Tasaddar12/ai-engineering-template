---
tier: contract
authority: agent
id: SPEC-002
title: Orchestration template interfaces
links: [RULES, TRUTH-MAP, AMD-002]
verification_refs: [PLAN-004]
---

# SPEC-002: Orchestration template interfaces

> Contract tier. Use the [amendment protocol](../RULES.md#the-amendment-protocol)
> for changed criteria; verification references identify current evidence.

## Requirement

This repository provides a navigable set of engineering instructions, record
formats and optional hook examples. The project being described is the
orchestration template, with its purpose in [PROJECT](../state/PROJECT.md).

## Acceptance criteria

- Given a fresh checkout, following AGENTS.md reaches current project intent,
  state, engagement rules and the indexes for roles and command procedures.
- Given a command or agent reference, its named file exists with matching case;
  templates are flat and refer to the record locations defined by config.
- Given a plan or fix, its directory determines its lifecycle stage; current
  specifications and historical evidence have separate owners in truth-map.
- Given this checkout, orchestration is operated through Markdown instructions;
  optional hook scripts are unregistered and do not provide a sandbox.

## Invariants

The owning paths and identifier formats are in [config](../config.yaml).
[Truth map](../truth-map.md) identifies normative owners. Source templates hold
placeholders; active project records contain the project's actual context.
Historical logs preserve the observations made at their recorded revision.

## Explicitly out of scope

Application behavior in projects adopting this template. Host-specific command
registration, a background launcher, and sandbox guarantees. The hook examples'
actual input/output and limitations are documented in [hooks](../hooks/README.md).
