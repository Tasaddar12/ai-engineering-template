# TASK-024 review question to resolve independently

The owner handoff says every new successor has exactly one mapped source scope
and rejects all write/read/resource expansion beyond it. Its first positive
replacement fixtures failed for new semantic resource claims and were changed
to inherit old resources. This is a reported implementation assumption, not an
accepted contract conclusion.

R1/R2 should independently reconcile that rule with the actual recovery workflow
and TASK-024 split/replace/sequence/augment acceptance. The workflow permits new
prerequisite/follow-up tasks while rejecting expanded product scope and broadened
permissions. Determine from the frozen plan/ADRs/contracts whether the proposed
graph may assign a new exact path/resource within the existing product and
unchanged permission subset, or whether the source-subset rule is required.

Do not fail on hypothetical preferences or require unowned025 application behavior.
If this rule prevents a required allowed proposal, demonstrate a concrete typed
case using accepted039/013/014 and cite the actual requirement. If it is consistent,
explain the supported augmentation boundary. This note neither approves the rule
nor authorizes source changes, scope expansion, a rewrite or a review verdict.
