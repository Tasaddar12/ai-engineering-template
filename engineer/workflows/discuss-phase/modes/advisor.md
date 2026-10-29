Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Advisor mode: research-backed comparisons

Load this mode only when `discuss-phase.md` has established `ADVISOR_MODE` from
the adopting user's profile. Without that profile, follow the standard
discussion mode and do not load this procedure.

## Calibrate the advice

Resolve the vendor philosophy from project configuration first, then the
user's profile, and default to `standard` when neither supplies a scored value.
Map conservative or thorough evaluation to `full_maturity`, opinionated to
`minimal_decisive`, and other values to `standard`. Record the source of the
calibration so the user can understand the framing.

Read the profile's technical background and explanation preferences. An
explicit technical background overrides inferred signals. Otherwise, use
guided learning, jargon frustration, or high-level explanation preferences as
signals to describe choices in terms of user-visible outcomes. Keep the
underlying tradeoffs intact.

## Research selected gray areas

After the user selects areas to compare, research each selected area in
parallel using the phase goal, project context, and calibration tier. Wait for
the results before synthesizing. For each area, present a comparison table
with option, benefits, costs, complexity, and recommendation, followed by a
short rationale grounded in this project's constraints. Match option count to
the tier where useful: three to five for full maturity, two to four for
standard, and one to two for minimal decisive.

Ask the user to choose an option or provide another. Treat a choice as a
decision only after the user makes it. Ask only focused follow-up questions
when the selected approach leaves a material planning ambiguity. Thinking
partner analysis remains governed by the normal feature setting and tradeoff
signals.

## Preserve scope and authority

If the user raises work outside this phase, capture it as a deferred idea and
return to the active decision. Summarize the selected options and unresolved
questions before writing context. Advisor research recommends choices; it does
not approve implementation or bypass the user's decision.
