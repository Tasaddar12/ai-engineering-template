# Manual checkpoints

These are workflow checkpoints, not executable or installed Git hooks.

| When | Check | On failure |
| --- | --- | --- |
| Before action | User approved the exact action and scope under RULES. | Report and wait. |
| Before recording | Correct template, ID, location and fact owner. | Correct the draft. |
| Before review | Agreed final validation is recorded; affected specs match the change. | Report missing evidence or repair within authority. |
| Before commit/push | Diff is scoped, message is nonempty, destination is authorized. | Stop the delivery step. |
| After an authorized merge | Host merge verified; target synchronized; exact branch safe to retire. | Keep cleanup pending and report why. |

Automating these checks is future work requiring its own intake, plan and decision.
