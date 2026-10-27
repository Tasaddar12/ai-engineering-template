# Reconcile executor completion

Apply this method to both native Agent dispatch modes. Worker terminal state is evidence to inspect, not the completion verdict. A session may end abnormally after its work was committed.

Run `engineer_run query phase-plan-index "${PHASE_NUMBER}"` and read the selected plan's actual SUMMARY status. Inspect `git log --oneline` on the reported worker branch and verify that the reported commits exist, affect declared ownership and contain the required SUMMARY. Compare its work root, branch, base and plan ID with the assignment and runtime lifecycle entry.

A complete committed SUMMARY plus matching owned commits establishes implementation completion even after an abnormal terminal message. Do not redispatch that completed work. A message claiming completion without the required committed artifact is blocked. An unavailable probe blocks only that plan; name it in the closing report and continue independent plans. Recent meaningful worker activity with a missing SUMMARY means keep waiting under executor-progress-policy.md, not immediate failure.

Before reassignment, obtain confirmed worker stop. A wait timeout never establishes exit. Preserve committed or dirty stranded work and reconcile the actual handoff before starting a fresh isolated continuation.
