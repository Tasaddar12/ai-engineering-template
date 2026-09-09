# Plan lifecycle

| Folder | Meaning | Typical next step |
| --- | --- | --- |
| intake | Unconfirmed observations, waiting questions, suspected drift and requests awaiting planning | Clarify or investigate; link a FIX when confirmed, or a PLAN when planned. |
| backlog | Draft or accepted work that has not started | Active after explicit execution approval. |
| active | Approved work being performed | Review when its agreed work and validation are ready. |
| review | A proposal or result awaiting a user/reviewer decision | Backlog for an accepted proposal; active for authorized repairs; done for an accepted result. |
| blocked | Work cannot proceed; blocker and resume condition recorded | Return to its recorded previous phase once resolved and still authorized. |
| abandoned | Work intentionally stopped | Historical; create a new linked plan if revived. |
| done | Work accepted and its authorized delivery completed | Historical; follow-ups use intake or FIX according to evidence. |

Move the existing file, retain its ID/slug, update frontmatter and repair references.
Record transitions in the journal and update STATE. A folder move grants no authority.
Plans use `review_type: proposal` or `review_type: result` while in review.
A push-only draft may remain in review after pushing; a push is not acceptance.
Intake records are not plans and have no plan stage. Confirmed defects follow the
[fix lifecycle](../fixes/README.md). Use [plan-status](../commands/plan-status.md) for
all stages and [plan-verify](../commands/plan-verify.md) for completed work.
