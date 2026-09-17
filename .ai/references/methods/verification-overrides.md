# Verification decisions and overrides

A report entry is a pointer to a human decision, never permission to waive a
requirement. Match the exact acceptance ID and scope to an actual decision in
CONTEXT; ambiguous wording or fuzzy token overlap is insufficient.

When an approved outcome changes, verify the resulting outcome with source and
behavioral evidence. Record the decision's author/date and evidence explicitly.
An alternative implementation that appears intentional but lacks authorization
remains a finding for the coordinator. Do not create or apply an override yourself.
Unverified behavior cannot become a pass merely because an override exists.

An intentional alternative may satisfy the goal differently: session-based auth
instead of OAuth PKCE, for example.

If the approved contract already permits an alternative implementation, verify
that path. Otherwise report the discrepancy and affected acceptance ID to the coordinator.
A decision already given does not require repeated approval.

Incomplete implementation, unclear requirements and a desire to skip verification
are not grounds for a passing override. Several conflicting outcomes suggest the
plan/context needs reconciliation, not a batch of waived checks.

## Traceability format

A report can preserve an accepted change in this form (illustrative only):

```yaml
overrides:
  - acceptance: AUTH-01
    must_have: "OAuth2 PKCE flow implemented"
    reason: "Approved session-based authentication for this server-rendered app"
    accepted_by: "actual decision maker"
    accepted_at: "actual decision timestamp"
    decision: "03-CONTEXT.md, Decisions, authentication mechanism"
```

Do not fill identity or timestamp from guesses. Match the exact acceptance ID,
artifact and scope, not fuzzy token overlap. If a decision appears to apply to
several outcomes, resolve the ambiguity through the coordinator; do not apply it
to the first textual match.

## Verification procedure

1. Read the original criterion, current approved CONTEXT and implementation.
2. Confirm that the recorded decision actually changes that criterion and scope.
3. Verify the revised outcome with the same evidence standard as any other truth.
4. Report the original wording, revised outcome, decision reference and evidence.
5. If behavior remains unverified, keep `human_needed`; if required implementation
   is missing or fails, keep `gaps_found`. A report entry cannot waive either.

Example report:

| Acceptance | Current approved outcome | Status | Evidence |
|---|---|---|---|
| AUTH-01 | User authenticates using server sessions | VERIFIED | Named session test passes at the report revision; decision in CONTEXT |
| CHAT-01 | Chat renders persisted messages | FAILED | API returns an empty static list |

Only evidence-backed current outcomes count toward the score. Distinguish an
accepted scope change from successful implementation. Future-phase scheduling
cannot defer required current acceptance without the actual scope decision.

## Re-verification and lifecycle

Read prior decision references, then confirm they remain applicable to the
current revision and approved scope. Preserve decision history in CONTEXT/Git;
do not assume report metadata automatically carries forward or grants authority.
If implementation now meets the original criterion, report the observed behavior.
The coordinator reconciles PLAN/ROADMAP/CONTEXT when needed, then requests fresh
verification; the verifier remains read-only. Surface accepted deviations in
completion reviews so later maintainers can understand the delivered contract.
