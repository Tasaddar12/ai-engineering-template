# Confirmed defects

Use this area for confirmed bugs and small defects. Unconfirmed reports, waiting
questions and suspected differences between documentation and behavior stay in
[intake](../plans/README.md) until evidence establishes a defect. The
[record policy](../policies/records.md) owns that distinction.

| Folder | Meaning | Exit condition |
| --- | --- | --- |
| open | Confirmed defect awaiting an approved repair, validation or acceptance | Agreed checks pass and the user accepts the result and its authorized delivery. |
| done | Accepted, validated repair with delivery evidence | Historical; a recurrence gets a new linked FIX. |

Create records with [fix.md](../templates/fix.md), using the filename and ID format
in [config](../config.yaml). An open record can be blocked; name the owner and resume
condition in its remaining-work section instead of adding more folders.

Link an originating intake when there is one; a directly confirmed defect needs no
duplicate intake. A bounded repair can use its FIX checklist and approval. Work with
multiple features or dependencies needs a linked PLAN owning that execution scope.
Use the existing implementation, review and delivery workflows.

Move a completed record with its ID/slug intact, repair links and journal the
transition. A commit or push alone does not close it. Empty folders retain .gitkeep.
