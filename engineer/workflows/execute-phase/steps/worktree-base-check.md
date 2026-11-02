<step name="worktree_base_check">
Capture the orchestrator HEAD before dispatch. Under harness isolation, embed the verify-only `worktree-branch-check.md` guard with that base in each executor prompt. A mismatch stops the worker with exit 42 and preserves the checkout for coordinator diagnosis. Under runtime isolation, create the checkout at the captured base and pin the native worker to its returned root. Never degrade to a shared checkout.
</step>
