# TASK-017 recovery evidence packaging

The independent recovery role finalized its recommendation and diagnostic output
before coordinator adoption. The diagnostic payload was named with a `.json`
extension but was not a v1 workflow artifact. Coordinator foundation validation
therefore exited1 with `artifact kind must be a string`. No product source or
task behavior failed in that check.

The coordinator changed only the storage names of two files, preserving their
exact final bytes. This keeps non-record diagnostic payloads outside live JSON
artifact discovery and preserves the original report's links as historical text.

| Original submitted name | Retained immutable bytes | SHA-256 |
| --- | --- | --- |
| TASK-017-recovery-assessment.md | [Original assessment](TASK-017-recovery-assessment.md.txt) | `64f3b3bfb6a0949efcd9a37741f8f84fc743d24ab751fec3c0c0a01139a83605` |
| TASK-017-recovery-assessment-verification.json | [Original diagnostic payload](TASK-017-recovery-assessment-verification.json.txt) | `814e4c7c567cba5477b9a91479b34dc3826a57c5df78126dd2ab946f0db0c3f0` |

The [original verification script](TASK-017-recovery-assessment-verification.py)
and [original final check](TASK-017-recovery-assessment-final.txt) remain unchanged.
Their command/output filenames describe the original execution, before this
packaging step. Neither script nor product tests were rerun to alter an outcome.
The coordinator decision links directly to the retained original assessment;
no independent recommendation, finding, observed result or final byte was rewritten.
