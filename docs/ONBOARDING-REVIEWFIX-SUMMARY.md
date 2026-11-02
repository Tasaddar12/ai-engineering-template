# Onboarding and CI review corrections

Base candidate:93852b60592af885fab55204c58b104dcbf8d9c8.

Independent review reproduced that new-project creates config.yaml, then tries to
commit config.json. The workflow now consistently names config.yaml. A regression
executes its exact documented commit argv after config-new-project, reads the
committed YAML from Git, and verifies preserved configuration and no duplicate
commit on rerun. The test passed (1 test,2.183s).

The full Ubuntu and Windows suites at93852 each ran1613 tests and failed only
because2 issue-publication fixtures still read the relocated .ai template path.
Those fixtures now read engineer/templates/issue.md. Both passed (2 tests,3.355s).

Source links and strict runtime verb validation passed. Final full cross-platform
checks and independent re-review remain pending. The later user instruction keeps this PR targeted at manual-override; a separate
draft to main will remain unmerged. These corrections do not change main or its
legacy verification-successor code.
