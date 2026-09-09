# Record policy

## Requirements

### Fact ownership and structure

Follow [truth-map](../truth-map.md). Each fact has one owner; other documents link to
it. Follow paths and IDs in [config](../config.yaml). Allocate IDs across all lifecycle
folders of the kind, never reuse them, and retain their ID/slug when moving a record.

Use the relevant template and fill every section. Keep YAML identity/status consistent
with the filename and lifecycle folder. State Unknown or Not applicable with a reason.
Do not invent source evidence, user decisions or completed work.

### Intake and confirmed defects

Intake holds unconfirmed observations, waiting questions, suspected documentation
drift and requests awaiting planning. Confirmed bugs and small defects use a FIX,
with expected/observed behavior and reproduction or other confirming evidence.
Confidence in the cause is separate from confirmation that a defect exists.

When an intake is confirmed, link it to the FIX and retain its original evidence.
The FIX owns the confirmed defect and outcome; reference earlier evidence rather
than copying it. A direct confirmed report may start as a FIX without an intake.
Use the [fix lifecycle](../fixes/README.md) for open/done transitions.

A bounded repair may keep its scope, acceptance and approval in the FIX. If a PLAN
is needed for multiple features or dependencies, that PLAN owns execution scope and
the FIX links to it. A record is not implementation authority.

### Mutability tiers

| Tier | Records | Requirement |
| --- | --- | --- |
| Working | Intake, open fixes, draft plans/research, PROJECT, STATE, proposed decisions | Edit within authorized scope; journal material decisions. |
| Maintained | Current specs and accepted plan execution notes | Keep accurate; amend before changing an accepted contract's meaning. |
| Contract | Policies, gate definitions, RULES, truth-map, config, agent/workflow contracts, accepted ADRs | Obtain approval for an AMD before changing an accepted obligation. |
| Historical | Journal entries, accepted AMDs, retired ADRs, done/abandoned plans, done fixes, completed research | Preserve; append a correction or create a linked successor. |

Templates enter the contract tier when a change alters required fields or meaning.
The current unaccepted scaffold can be refined under explicit drafting instructions.
Typo/link corrections without changed meaning can be made within an approved
documentation action; record the correction.

### Amendments

1. Draft an AMD identifying the owning contract, old/new obligation, reason and impact.
2. Present its decision summary and wait for user approval.
3. After approval, update the maintained contract, accept the AMD and journal the
   application together. Rejected proposals remain rejected records.
4. Preserve accepted ADR rationale. A new accepted ADR may supersede it; move the old
   file to decisions/retired, repair references and retain its original body.

### Current state and history

Specs describe the current checked-out behavior. Update affected specs in every
feature/fix PR, including documentation-only changes. The same merge updates source
and specs; no recursive post-merge spec commit is required.

STATE owns Now / Next / Blockers. Journals are append-only daily logs; correct an old
entry with a new timestamped entry. Gate results belong in the selected plan's evidence
section, otherwise its FIX or INTAKE; the journal records that an evaluation occurred.
New verification of a historical done plan is appended to the journal with the plan,
revision and evidence. A report-only snapshot is returned without repository writes.

## Evidence

Use the owning record, accepted amendment where required, and dated journal entry.
Review-ready and delivery-ready gates inspect the relevant record evidence.
