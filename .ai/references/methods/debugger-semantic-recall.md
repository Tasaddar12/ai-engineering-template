# Local Knowledge-Base Recall

> Adapted for offline use. Source attribution is in
> [third-party notices](../../THIRD-PARTY-NOTICES.md).

## Purpose

A prior resolution of "requests hang under load" may explain a new "API times
out when many users connect" even when the report shares few literal keywords.
Combine local text search with semantic comparison of the candidate entries.
No memory service, embedding pipeline, CLI installation or network call is needed.

## Durable source and write boundary

Use `.planning/debug/knowledge-base.md` when the project already has one.
It is the durable plain-text source, not a cache. Workers return proposed entries
in their assigned result; the coordinator owns shared updates and archival.
Do not create debug records for a read-only assignment or invent project history.

After verification, prepare the agent-authored Resolution summary: confirmed
root causes, fix, changed files, why the failure escaped, and a concrete
recurrence guard. Do not copy raw user-supplied Symptoms into a cross-session
record. Redact API keys, bearer tokens, JWTs, passwords, personal data and
credentials, including secret-shaped values echoed by error strings.

## Read at investigation Phase 0

1. Extract distinctive nouns, error substrings and identifiers (function,
   variable, endpoint or configuration names) from the current symptoms.
2. Use local file reading or `rg -n -i` with literal search terms against the
   knowledge base. Two or more overlapping tokens are a useful starting signal,
   not a mandatory threshold that hides a strong identifier match.
3. Read each matching entry in full, including its root cause and recurrence
   guard. Compare causes and operating conditions, not just wording. If the file
   is small, read all entries to find synonyms missed by literal search.
4. Surface a bounded shortlist, usually three to five entries, with the source
   location, matching conditions, differences and the experiment that would
   distinguish that prior cause from a new failure.
5. Add candidates to Evidence as hypotheses. A historical fix is never proof
   of the current diagnosis. Verify the relevant code and guard still exist.

## Missing or stale knowledge

If no knowledge base exists or nothing matches, record that fact and continue
normal evidence gathering. Do not install or configure an external recall tool.
If a referenced guard no longer exists, record the stale reference and pass a
correction to its owner. Never silently treat missing history as a passing check.

## Scope

This method improves recall using existing local records. It does not require
new infrastructure, authorize shared writes, or replace reproduction and
hypothesis testing. A future project may explicitly adopt a memory service, but
that is outside this method and must not become an implicit dependency.
