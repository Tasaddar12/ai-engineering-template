# Commit assigned quick artifacts before isolated dispatch

This step is unconditional. The worker base must contain the actual QUICK record and complete PLAN; a preference about optional documentation commits cannot make the worker start without its assigned plan.

Read and execute engineer/workflows/_runtime-launcher.snippet.sh. Inspect `engineer_run query config-get commit_docs --raw` for optional documentation policy, then inspect the exact QUICK record and PLAN paths. Stage and commit only those actual assigned artifacts with engineer_run query commit when they changed. Preserve each path as one argument, including spaces and Unicode. Do not stage unrelated work or materialize unsupported mode artifacts.

If no artifact changed, preserve the existing committed plan revision. Read the actual last commit touching PLAN and its immediate parent when a branch-check base needs that provenance. Capture QUICK_PLAN_COMMIT after the commit attempt and QUICK_PLAN_PARENT only when that parent actually exists; a root commit has no parent. Never manufacture a parent SHA or treat a failed commit as no-change success.

Run hooks normally. A hook failure blocks executor dispatch with its diagnostic; never add a bypass flag or change configuration to skip it. Require a clean owned artifact state before capturing EXPECTED_BASE and creating the worker checkout.
