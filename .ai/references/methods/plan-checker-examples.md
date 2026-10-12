# Plan-Checker Examples

> Progressive-disclosure reference for [phase-checker](../../agents/phase-checker.md). The checker
> inlines this file from its `<examples>` block via `@`; the calibrated few-shot
> set lives separately in [few-shot-examples/plan-checker.md](few-shot-examples/plan-checker.md).

## Scope Boundary (separate outcome or configured cap)

**Plan 01 analysis:**
```
Tasks: 5
Files modified: 12
  - prisma/schema.prisma
  - src/app/api/auth/login/route.ts
  - src/app/api/auth/logout/route.ts
  - src/app/api/auth/refresh/route.ts
  - src/middleware.ts
  - src/lib/auth.ts
  - src/lib/jwt.ts
  - src/components/LoginForm.tsx
  - src/components/LogoutButton.tsx
  - src/app/login/page.tsx
  - src/app/dashboard/page.tsx
  - src/types/auth.ts
```

**Plan 01 tasks:** Tasks 1-4 implement account creation; Task 5 adds a billing
checkout and purchase receipt.

**Locked decision D-07:** This phase delivers account creation; billing is
deferred to a later phase.

Task 5 adds billing purchase, a separately deferred outcome from account creation. The 5-task and 12-file counts and uncalibrated context estimate alone prove no mandatory violation.

```yaml
issue:
  id: "PC-01-01-scope_sanity-01"
  plan: "01"
  dimension: scope_sanity
  severity: warning
  required_property: "The plan stays within the phase outcome fixed by D-07"
  authority: ".planning/phases/01/01-CONTEXT.md#Decisions/D-07"
  description: "Task 5 adds billing purchase, while D-07 scopes this phase to account creation and defers billing."
  task: 5
  fix_hint: "Remove the billing outcome from this plan or place it in an authorized phase."
```

The task/file counts and unmeasured context estimate are not grounds for this
warning. They do not establish a violated mandatory property; the warning is
grounded only in the separate outcome and cited phase decision. If that same
plan satisfies its governing outcomes and no configured positive task cap is
exceeded, any sizing preference is `info`.
