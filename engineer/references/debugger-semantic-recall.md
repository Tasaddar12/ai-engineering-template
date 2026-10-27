# Offline diagnostic knowledge recall

Search existing project knowledge before repeating a failed diagnosis. This method adds no service, infrastructure, installation or authority.

## Inputs

- Assigned diagnostic question and observed behavior.
- Exact checkout, revision and owned diagnostic outputs.
- Existing debug notes, committed summaries, issue references and project knowledge paths.

## Procedure

1. Extract concrete terms from the symptom: error text, boundary, state transition, component and failure shape. 2. Use `rg` on existing repository knowledge and Git-visible diagnostics. Start with exact error text, then identifiers, then related behavior terms. Do not scan secrets or unrelated user files. 3. Read relevant matches with surrounding context. Compare the old preconditions, mechanism, failing revision and resolution with current source. 4. Record similarities and differences. A semantic resemblance is a hypothesis, not proof the same cause exists. 5. Reproduce or inspect the current mechanism independently. Preserve disconfirming evidence and reject a recalled explanation when the current path differs. 6. Return cited read-only evidence to the coordinator: source path/line, prior cause, current match/difference and the next bounded check. 7. The coordinator decides whether a reusable knowledge note should be written and assigns its exact path.
## Safe knowledge writes

Redact credentials, personal data, private customer payloads and access tokens. Retain a sanitized symptom, preconditions, root cause, minimal repair and evidence sufficient to distinguish this case from superficially similar failures. Link canonical issues and actual commit revisions. Do not create a second decision registry; consequential decisions belong in PROJECT Key Decisions.

## Example

A prior note says a comments list missed a refresh dependency. Current symptoms look similar, but current source subscribes correctly. Record that difference and inspect the API response/caching boundary rather than applying the old dependency patch automatically.

## Result

Return either relevant recalled evidence with current corroboration, a rejected hypothesis with disconfirming evidence, or `no relevant prior record found` with searched terms and paths. Absence of a match never proves a new failure class.
