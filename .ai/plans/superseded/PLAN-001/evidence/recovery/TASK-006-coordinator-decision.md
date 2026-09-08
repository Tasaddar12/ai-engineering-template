# TASK-006 coordinator recovery decision

Adopt the independent [recovery assessment](TASK-006-recovery-assessment.md)
in full for exactly one bounded test/handoff repair in a fresh TASK-006-a2.
The evidence establishes a cancellation-test synchronization defect, with no
demonstrated production or structural defect. Graph r4, all acceptance criteria,
scope, dependencies, schemas, ports and permissions remain unchanged.

The clean failed a1 remains at `ce4c8edb86b02268a856a5f870932ade0e7e9b91`.
Its c1 R1 FAIL and c2 R1 PASS / R2 FAIL, candidates and all companions remain
immutable history. Recovery finished independently and stopped all access before
this decision. The coordinator verified ROOT at
`a31474b0927bf85895ec44ef9695bb3a14e05605`, the assessment and its verification
output, and the finalized recovery session. Eight of 39 tasks are accepted;
TASK-006 and its 23 transitive descendants remain unaccepted and undispatched.

After this checkpoint, the coordinator may dispatch fresh a2 with the original
three-path ownership and component:commands resource. Its owner may cherry-pick
`c3c2ba21c6441abde52f6e340b29d0bf65910f8e`,
`86bc27af026d8b7b00303fa6d62b12218e0947b8`, and
`530cd085166ab51e2814486f4967ab52203375c2`, oldest first, as unaccepted salvage.
Before and after test repair, commands.py must retain Git blob
`39828108eb7d198d81d810c8fd9e136e3f64f8f0` and raw SHA-256
`700079bb47853a1d4cdebaa89bafcacf03885a81f9ef57687ec7203338ec29d0`.
All other production bytes must match the verified fresh base. Only the owned
command tests and handoff may change after salvage.

The assessment's five-part repair contract is binding: observed nonblocking
readiness under monotonic startup deadlines; proof of the exact inherited-pipe
post-parent-exit or detached-child/live-parent phase; separately bounded response
after cancellation and overall execution; immediately registered exact identities
with unconditional bounded finally cleanup and reader/signalling settlement;
and the exact suite on Windows/Linux Python 3.11/3.12 with actual origins,
counts, skips and cleanup facts. A blind longer timer, missing-PID suppression,
timing skip, unobserved fixture phase or pre-return killer cannot establish a pass.
Any failure-only watchdog intervention must fail the test. Production behavior,
native status assertions and meaningful timeout subcases remain unchanged.

The [native budget snapshot](TASK-006-native-invocations-69.txt) records 69/300
charged, including rejected attempts and the continuing coordinator. Reserve one
owner and two fresh reviews: 72/300 charged or reserved. Historical structural
rewrites remain 3/3 used, zero remaining. Two failed cycles trigger this recovery;
the next review pair is cumulative c3, not a reset to c1. No policy value changes
and no runtime run identity or recovery JSON is invented.

Coordinator generation advances 30 to 31 with this decision. TASK-006 moves to
ready solely for the bounded recovery dispatch. Before review, form a new exact
candidate with all four environment results bound before its fingerprint. Fresh
independent Astra/xhigh R1 and, only after its pass, distinct fresh Astra/xhigh R2
must assess that same current candidate. Any further candidate validation or
review failure returns immediately to recovery; no second repair is allowed.
Production changes, wider ownership or structural requirements exceed this
allowance. TASK-006 descendants remain fenced until acceptance.

Local independent work may continue: TASK-014 enters review after a2 dispatch;
after TASK-006 acceptance, TASK-007 and TASK-018 have priority. The retained
[Linux minimum-version baseline](../validation/python311-linux-accepted-baseline-3acfcb0d700b.txt)
passed 194 tests from bootstrap and the eight accepted leaves. It is not a full
plan or remote CI result. All 39 tasks, integrated validation and final review
remain required by the user's full implementation request.
