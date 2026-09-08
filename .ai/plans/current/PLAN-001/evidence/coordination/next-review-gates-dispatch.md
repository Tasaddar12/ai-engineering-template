# TASK-020 coordination reminders

The user's single-stage decision applies to reviewing this implementation task.
The runtime behavior specified below remains the approved product contract; do not
silently remove its stages while broader product refinements are deferred.

Dispatch only after actual003/017/018/019/038 acceptance. Own reviews.py, its
reviews_gates leaf and TASK-020 handoff. Consume accepted ReviewService/ReviewRequest/
ReviewResult and actual configuration, fake agent, validation and candidate APIs.

R1 implementation review and R2 consistency review must be distinct fresh higher-
capability invocations/sessions from each other and from implementation. Match
request, candidate ref/fingerprint, graph/checklist, model/profile provenance and
stage. R2 additionally binds a passed R1 for the identical candidate. Reject
substituted stage/profile, lower capability, stale report, missing/duplicate check,
empty evidence for applicable passing checks, and unresolved major/blocking
findings. A reviewer string in an untrusted report alone proves no invocation.

After a material R1 or R2 fix, run fresh validation and both review stages. Keep
terminal reviews immutable and preserve failed history across attempts; do not
delete old R2 results when the next attempt fails before reaching R2. A report for
a prior base/head/context/checklist cannot remain current by changing a status.

Use injected fake adapter observations for deterministic tests of start, wait,
unknown/cancel, report import and exact two-stage linkage. Document simulated
provenance honestly without claiming a real provider invocation or adding v1
fields. Do not turn configured:false recommendations into actual model bindings.
Actual coordinator/source policies remain unmodified during this manual development.

This service enforces gates and emits typed outcomes; recovery algorithms,
canonical journal transactions and integration effects remain other owners.
Preserve existing representations for invocation/history evidence and report a
concrete prerequisite gap rather than inventing another shared contract.
