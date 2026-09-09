# Plan lifecycle

| Folder | Meaning | Typical next step |
| --- | --- | --- |
| intake | Problems, bugs, drift and unplanned requests | Report and decision; promote to a linked backlog plan if requested. |
| backlog | Draft or accepted work that has not started | Active after explicit execution approval. |
| active | Approved work being performed | Review when its agreed work and validation are ready. |
| review | A proposal or result awaiting a user/reviewer decision | Backlog for an accepted proposal; active for authorized repairs; done for an accepted result. |
| blocked | Work cannot proceed; blocker and resume condition recorded | Return to its recorded previous phase once resolved and still authorized. |
| abandoned | Work intentionally stopped | Historical; create a new linked plan if revived. |
| done | Work accepted and its authorized delivery completed | Historical; follow-ups start in intake. |

Move the existing file, retain its ID/slug, update frontmatter and repair references.
Record transitions in the journal and update STATE. A folder move grants no authority.
Plans use `review_type: proposal` or `review_type: result` while in review.
A push-only draft may remain in review after pushing; a push is not acceptance.
