# Scout usage redesign

PR62 replaces repeated planning gates, schemas and return protocols with one
short authoritative contract in `references/scout-dispatch.md`. It routes
discovery and requested mechanical evidence to the configured cheap scout,
preserves owner decisions and known-source inspection, reuses valid evidence,
and gives a brief coordinator fallback. Role search examples point to that rule.

The plan-phase command, skill and workflow return to the baseline procedure.
Static checks cover the intended routing and evidence contract, links and host
adapter parity rather than the removed wording or state machine.

Validation: 12 agent-source, 9 efficiency-contract and 3 workflow-link tests
passed, plus Codex/Claude installed role parity and guidance links (2 checks).
Independent review and automatic CI are recorded in the PR description. No
benchmarks, product changes or mechanical enforcement claims are added.
