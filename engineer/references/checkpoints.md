<overview>
Plans execute within recorded authorization. Checkpoints preserve human decisions and verification requirements.

**Authority principles:**

1. Prepare the concrete reviewable result before requesting a missing approval.
2. Never infer approval from silence, a mode flag, a recommendation or implementation readiness.
3. Preserve authorization already supplied for its stated scope; do not ask again.
4. Stop only work dependent on the missing decision; continue independent authorized work.
5. Secure credentials through masked/provider entry; never request secrets in conversation or expose them in logs.
6. Record the actual answer, its scope and resume action before continuation.

A `blocking-human` checkpoint requires an actual human answer in every mode. An unattended `checkpoint:decision` may proceed on its declared `auto_select` only when recorded authorization delegates that exact choice. Otherwise escalate; option position does not authorize selection.

| Condition, evaluated in order | Action |
|-------------------------------|--------|
| Actual required human judgment / blocking-human | Prepare and wait for actual human answer |
| Recorded authorization already covers the action | Proceed and preserve that authorization |
| Declared `auto_select` names a valid option and recorded discretion delegates the choice | Record selected option and authority, then proceed |
| Required verification can be deferred to end-of-phase UAT | Prepare UAT and leave acceptance pending |
| No authorized route | Escalate the exact dependent decision |

There is no auto-approval configuration flag. Both executor and coordinator enforce these conditions; a handoff cannot manufacture approval.
</overview>

<checkpoint_types>

<type name="human-verify">
## checkpoint:human-verify (Most Common - 90%)

**When:** Claude completed automated work, human confirms it works correctly.

> **Default mode (#3309): `workflow.human_verify_mode = end-of-phase`.** New projects do NOT halt mid-flight at _planner-emitted_ `checkpoint:human-verify` tasks. (The executor-synthesized **tracer feedback gate** is the one runtime checkpoint this mode also governs, with its own precedence chain — see "Tracer feedback gate (#3299)" below.) The planner suppresses those task emissions and embeds the verification details into the relevant `auto` task's `<verify><human-check>` block; the verifier harvests every `<verify><human-check>` at end-of-phase (Step 8) and consolidates them into the existing `human_needed` → `{phase_num}-UAT.md` flow in `workflows/execute-phase.md`. The user reviews everything in one batch.
>
> **Why this is the default:** every mid-flight halt costs a full executor cold-start (AGENTS.md, MEMORY.md, STATE.md, plan re-read on respawn) because subagent context is discarded across the pause. A plan with N human-verify checkpoints pays the cold-start cost N+1 times — measured at "tens of thousands of tokens" per round-trip on real projects.
>
> Set `workflow.human_verify_mode = mid-flight` in `.planning/config.yaml` to opt back into the pre-#3309 behavior of halting at every checkpoint. `checkpoint:decision` and `checkpoint:human-action` are unaffected by either value — those gate the work itself, not post-hoc verification.

**Use for:**

- Visual UI checks (layout, styling, responsiveness)
- Interactive flows (click through wizard, test user flows)
- Functional verification (feature works as expected)
- Audio/video playback quality
- Animation smoothness
- Accessibility testing

**Structure:**

```xml
<task type="checkpoint:human-verify" gate="blocking">
  <what-built>[What Claude automated and deployed/built]</what-built>
  <how-to-verify>
    [Exact steps to test - URLs, commands, expected behavior]
  </how-to-verify>
  <resume-signal>[How to continue - "approved", "yes", or describe issues]</resume-signal>
</task>
```

**Example: UI Component (shows key pattern: Claude starts server BEFORE checkpoint)**

```xml
<task type="auto">
  <name>Build responsive dashboard layout</name>
  <files>src/components/Dashboard.tsx, src/app/dashboard/page.tsx</files>
  <action>Create dashboard with sidebar, header, and content area. Use Tailwind responsive classes for mobile.</action>
  <verify>npm run build succeeds, no TypeScript errors</verify>
  <done>Dashboard component builds without errors</done>
</task>

<task type="auto">
  <name>Start dev server for verification</name>
  <action>Run `npm run dev` in background, wait for "ready" message, capture port</action>
  <verify>fetch http://localhost:3000 returns 200</verify>
  <done>Dev server running at http://localhost:3000</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Responsive dashboard layout - dev server running at http://localhost:3000</what-built>
  <how-to-verify>
    Visit http://localhost:3000/dashboard and verify:
    1. Desktop (>1024px): Sidebar left, content right, header top
    2. Tablet (768px): Sidebar collapses to hamburger menu
    3. Mobile (375px): Single column layout, bottom nav appears
    4. No layout shift or horizontal scroll at any size
  </how-to-verify>
  <resume-signal>Type "approved" or describe layout issues</resume-signal>
</task>
```

**Example: Xcode Build**

```xml
<task type="auto">
  <name>Build macOS app with Xcode</name>
  <files>App.xcodeproj, Sources/</files>
  <action>Run `xcodebuild -project App.xcodeproj -scheme App build`. Check for compilation errors in output.</action>
  <verify>Build output contains "BUILD SUCCEEDED", no errors</verify>
  <done>App builds successfully</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Built macOS app at DerivedData/Build/Products/Debug/App.app</what-built>
  <how-to-verify>
    Open App.app and test:
    - App launches without crashes
    - Menu bar icon appears
    - Preferences window opens correctly
    - No visual glitches or layout issues
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues</resume-signal>
</task>
```

### Tracer feedback gate (#3299)

A `type="tracer"` task is followed by an early integration checkpoint on the proven slice, run BEFORE any expansion task. This checkpoint is **synthesized by the executor at runtime** — no planner emits it — so planner-side `human_verify_mode` suppression cannot reach it. It must therefore consult the mode itself.

Evaluate the rows **in order** and take the first that matches — they are a precedence chain, not independent conditions:

| #   | Run                                        | Tracer `<verify>`                         | Behavior                                                                                             |
| --- | ------------------------------------------ | ----------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 1   | **Any run, any mode** (incl. auto)         | task carries `gate="blocking-human"`      | **STOP → `checkpoint:human-verify`.** Never auto-continued.                                          |
| 2 | Any mode, including unattended | `<verify>` carries `<human-check>` | STOP for the actual required human judgment; automated success does not replace it. |
| 3   | Interactive, `end-of-phase` (default)      | only `<automated>`                        | Re-run verify; HALT on failure, continue to expansion on success — **no checkpoint**                 |
| 4   | Interactive, `end-of-phase`                | carries `<human-check>`                   | STOP → `checkpoint:human-verify`                                                                     |
| 5   | Interactive, `mid-flight`                  | any                                       | STOP → `checkpoint:human-verify`                                                                     |

**Carve-outs — the #3299 auto-continue (row 3) applies ONLY when all three hold:** the run is interactive, the mode is `end-of-phase`, and the tracer's `<verify>` contains only `<automated>`. Anything with required human judgment stops; other authorized automated work proceeds only with actual passing evidence. HALT-on-failure is unconditional in rows 2 and 3 alike: a failing tracer never becomes an approvable checkpoint and never proceeds to expansion, because layering expansion onto a broken slice is the failure this gate exists to prevent.

Row 1 is deliberately **not** scoped to interactive runs. The authority principles above state that `gate="blocking-human"` stops for a human in _every_ mode including auto-mode, and a precedence chain that let an autonomous run continue past it would make this file assert two incompatible rules about the same gate. No planner emits `gate` on a `type="tracer"` task today, but the Python plan-structure validator parses only `type` and does not consult `gate` on non-checkpoint tasks, so a hand-authored, imported, or externally-generated `PLAN.md` can carry it and validate — unreachable by our planner is not unreachable.

Read `HUMAN_VERIFY_MODE` with an explicit default — the Python runtime defaults workflow.human_verify_mode to end-of-phase; unknown absent keys still fail unless an explicit --default is supplied:

```bash
HUMAN_VERIFY_MODE=$(engineer_run query config-get workflow.human_verify_mode --default end-of-phase --raw) || exit 1
```

</type>

<type name="decision">
## checkpoint:decision (9%)

**When:** Human must make choice that affects implementation direction.

**Use for:**

- Technology selection (which auth provider, which database)
- Architecture decisions (monorepo vs separate repos)
- Design choices (color scheme, layout approach)
- Feature prioritization (which variant to build)
- Data model decisions (schema structure)

**Structure:**

```xml
<task type="checkpoint:decision" gate="blocking" auto_select="option-a">
  <decision>[What's being decided]</decision>
  <context>[Why this decision matters]</context>
  <options>
    <option id="option-a">
      <name>[Option name]</name>
      <pros>[Benefits]</pros>
      <cons>[Tradeoffs]</cons>
    </option>
    <option id="option-b">
      <name>[Option name]</name>
      <pros>[Benefits]</pros>
      <cons>[Tradeoffs]</cons>
    </option>
  </options>
  <resume-signal>[How to indicate choice]</resume-signal>
</task>
```

`auto_select` is optional and names the `id` of the `<option>` auto-mode should pick when this checkpoint is reached unattended. Omit it and auto-mode escalates to a human instead of guessing from option order — the same treatment `gate="blocking-human"` already gets. An `auto_select` value that doesn't match any `<option id="…">` fails `verify plan-structure` at plan-parse time rather than silently falling back to the first option.

**Example: Auth Provider Selection**

```xml
<task type="checkpoint:decision" gate="blocking">
  <decision>Select authentication provider</decision>
  <context>
    Need user authentication for the app. Three solid options with different tradeoffs.
  </context>
  <options>
    <option id="supabase">
      <name>Supabase Auth</name>
      <pros>Built-in with Supabase DB we're using, generous free tier, row-level security integration</pros>
      <cons>Less customizable UI, tied to Supabase ecosystem</cons>
    </option>
    <option id="clerk">
      <name>Clerk</name>
      <pros>Beautiful pre-built UI, best developer experience, excellent docs</pros>
      <cons>Paid after 10k MAU, vendor lock-in</cons>
    </option>
    <option id="nextauth">
      <name>NextAuth.js</name>
      <pros>Free, self-hosted, maximum control, widely adopted</pros>
      <cons>More setup work, you manage security updates, UI is DIY</cons>
    </option>
  </options>
  <resume-signal>Select: supabase, clerk, or nextauth</resume-signal>
</task>
```

**Example: Database Selection**

```xml
<task type="checkpoint:decision" gate="blocking">
  <decision>Select database for user data</decision>
  <context>
    App needs persistent storage for users, sessions, and user-generated content.
    Expected scale: 10k users, 1M records first year.
  </context>
  <options>
    <option id="supabase">
      <name>Supabase (Postgres)</name>
      <pros>Full SQL, generous free tier, built-in auth, real-time subscriptions</pros>
      <cons>Vendor lock-in for real-time features, less flexible than raw Postgres</cons>
    </option>
    <option id="planetscale">
      <name>PlanetScale (MySQL)</name>
      <pros>Serverless scaling, branching workflow, excellent DX</pros>
      <cons>MySQL not Postgres, no foreign keys in free tier</cons>
    </option>
    <option id="convex">
      <name>Convex</name>
      <pros>Real-time by default, TypeScript-native, automatic caching</pros>
      <cons>Newer platform, different mental model, less SQL flexibility</cons>
    </option>
  </options>
  <resume-signal>Select: supabase, planetscale, or convex</resume-signal>
</task>
```

</type>

<type name="human-action">
## checkpoint:human-action (1% - Rare)

**When:** Action has NO CLI/API and requires human-only interaction, OR Claude hit an authentication gate during automation.

**Use ONLY for:**

- **Authentication gates** - Claude tried CLI/API but needs credentials (this is NOT a failure)
- Email verification links (clicking email)
- SMS 2FA codes (phone verification)
- Manual account approvals (platform requires human review)
- Credit card 3D Secure flows (web-based payment authorization)
- OAuth app approvals (web-based approval)

**Do NOT use for pre-planned manual work:**

- Deploying (use CLI - auth gate if needed)
- Creating webhooks/databases (use API/CLI - auth gate if needed)
- Running builds/tests (use Bash tool)
- Creating files (use Write tool)

**Structure:**

```xml
<task type="checkpoint:human-action" gate="blocking">
  <action>[What human must do - Claude already did everything automatable]</action>
  <instructions>
    [What Claude already automated]
    [The ONE thing requiring human action]
  </instructions>
  <verification>[What Claude can check afterward]</verification>
  <resume-signal>[How to continue]</resume-signal>
</task>
```

**Example: Email Verification**

```xml
<task type="auto">
  <name>Create SendGrid account via API</name>
  <action>Use SendGrid API to create subuser account with provided email. Request verification email.</action>
  <verify>API returns 201, account created</verify>
  <done>Account created, verification email sent</done>
</task>

<task type="checkpoint:human-action" gate="blocking">
  <action>Complete email verification for SendGrid account</action>
  <instructions>
    I created the account and requested verification email.
    Check your inbox for SendGrid verification link and click it.
  </instructions>
  <verification>SendGrid API key works: curl test succeeds</verification>
  <resume-signal>Type "done" when email verified</resume-signal>
</task>
```

**Example: Authentication Gate (Dynamic Checkpoint)**

```xml
<task type="auto">
  <name>Deploy to Vercel</name>
  <files>.vercel/, vercel.json</files>
  <action>Run `vercel --yes` to deploy</action>
  <verify>vercel ls shows deployment, fetch returns 200</verify>
</task>

<!-- If vercel returns "Error: Not authenticated", Claude creates checkpoint on the fly -->

<task type="checkpoint:human-action" gate="blocking">
  <action>Authenticate Vercel CLI so I can continue deployment</action>
  <instructions>
    I tried to deploy but got authentication error.
    Run: vercel login
    This will open your browser - complete the authentication flow.
  </instructions>
  <verification>vercel whoami returns your account email</verification>
  <resume-signal>Type "done" when authenticated</resume-signal>
</task>

<!-- After authentication, Claude retries the deployment -->

<task type="auto">
  <name>Retry Vercel deployment</name>
  <action>Run `vercel --yes` (now authenticated)</action>
  <verify>vercel ls shows deployment, fetch returns 200</verify>
</task>
```

**Key distinction:** Auth gates are created dynamically when Claude encounters auth errors. NOT pre-planned — The agent prepares authorized work first and requests secure credential entry only when needed; never collect secret values in conversation.
</type>
</checkpoint_types>

<execution_protocol>

When Claude encounters `type="checkpoint:*"`:

1. **Stop immediately** - do not proceed to next task
2. **Display checkpoint clearly** using the format below
3. **Wait for user response** - do not hallucinate completion
4. **Verify if possible** - check files, run tests, whatever is specified
5. **Resume execution** - continue to next task only after confirmation

**For checkpoint:human-verify:**

```
### CHECKPOINT: Verification Required

Progress: 5/8 tasks complete
Task: Responsive dashboard layout

Built: Responsive dashboard at /dashboard

How to verify:
  1. Visit: http://localhost:3000/dashboard
  2. Desktop (>1024px): Sidebar visible, content fills remaining space
  3. Tablet (768px): Sidebar collapses to icons
  4. Mobile (375px): Sidebar hidden, hamburger menu appears

---

**→ YOUR ACTION: Type "approved" or describe issues**
```

**For checkpoint:decision:**

```
### CHECKPOINT: Decision Required

Progress: 2/6 tasks complete
Task: Select authentication provider

Decision: Which auth provider should we use?

Context: Need user authentication. Three options with different tradeoffs.

Options:
  1. supabase - Built-in with our DB, free tier
     Pros: Row-level security integration, generous free tier
     Cons: Less customizable UI, ecosystem lock-in

  2. clerk - Best DX, paid after 10k users
     Pros: Beautiful pre-built UI, excellent documentation
     Cons: Vendor lock-in, pricing at scale

  3. nextauth - Self-hosted, maximum control
     Pros: Free, no vendor lock-in, widely adopted
     Cons: More setup work, DIY security updates

---

**→ YOUR ACTION: Select supabase, clerk, or nextauth**
```

**For checkpoint:human-action:**

```
### CHECKPOINT: Action Required

Progress: 3/8 tasks complete
Task: Deploy to Vercel

Attempted: vercel --yes
Error: Not authenticated. Please run 'vercel login'

What you need to do:
  1. Run: vercel login
  2. Complete browser authentication when it opens
  3. Return here when done

I'll verify: vercel whoami returns your account

---

**→ YOUR ACTION: Type "done" when authenticated**
```

</execution_protocol>

<authentication_gates>

**Auth gate = Claude tried CLI/API, got auth error.** Not a failure — a gate requiring human input to unblock.

**Pattern:** Claude tries automation → auth error → creates checkpoint:human-action → user authenticates → Claude retries → continues

**Gate protocol:**

1. Recognize it's not a failure - missing auth is expected
2. Stop current task - don't retry repeatedly
3. Create checkpoint:human-action dynamically
4. Provide exact authentication steps
5. Verify authentication works
6. Retry the original task
7. Continue normally

**Key distinction:**

- Pre-planned checkpoint: "I need you to do X" (wrong - Claude should automate)
- Auth gate: "I tried to automate X but need credentials" (correct - unblocks automation)

</authentication_gates>

<automation_reference>

**The rule:** If it has CLI/API, Claude does it. Never ask human to perform automatable work.

## Service CLI Reference

| Service     | CLI/API        | Key Commands                              | Auth Gate            |
| ----------- | -------------- | ----------------------------------------- | -------------------- |
| Vercel      | `vercel`       | `--yes`, `env add`, `--prod`, `ls`        | `vercel login`       |
| Railway     | `railway`      | `init`, `up`, `variables set`             | `railway login`      |
| Fly         | `fly`          | `launch`, `deploy`, `secrets set`         | `fly auth login`     |
| Stripe      | `stripe` + API | `listen`, `trigger`, API calls            | API key in .env      |
| Supabase    | `supabase`     | `init`, `link`, `db push`, `gen types`    | `supabase login`     |
| Upstash     | `upstash`      | `redis create`, `redis get`               | `upstash auth login` |
| PlanetScale | `pscale`       | `database create`, `branch create`        | `pscale auth login`  |
| GitHub      | `gh`           | `repo create`, `pr create`, `secret set`  | `gh auth login`      |
| Node        | `npm`/`pnpm`   | `install`, `run build`, `test`, `run dev` | N/A                  |
| Xcode       | `xcodebuild`   | `-project`, `-scheme`, `build`, `test`    | N/A                  |
| Convex      | `convex`   | `dev`, `deploy`, `env set`, `env get`     | `convex login`   |

## Environment Variable Automation

**Env files:** Use Write/Edit tools. Never ask human to create .env manually.

**Dashboard env vars via CLI:**

| Platform | CLI Command             | Example                                    |
| -------- | ----------------------- | ------------------------------------------ |
| Convex   | `convex env set`    | Secure provider/masked entry; never a secret value in argv |
| Vercel   | `vercel env add`        | `vercel env add STRIPE_KEY production`     |
| Railway  | `railway variables set` | `railway variables set API_KEY=value`      |
| Fly      | `fly secrets set`       | `fly secrets set DATABASE_URL=...`         |
| Supabase | `supabase secrets set`  | `supabase secrets set MY_SECRET=value`     |

**Secret collection pattern:**

```xml
<!-- WRONG: collecting a secret in chat -->
<task type="checkpoint:human-action">
  <action>Paste the production API key in the conversation</action>
</task>

<!-- RIGHT: user enters the secret through a secure provider/local prompt -->
<task type="checkpoint:human-action" gate="blocking-human">
  <action>Enter the API key through the provider's secure secret-entry flow</action>
  <instructions>Open the configured secret manager or local masked prompt. Do not paste the value into chat, logs, command arguments or committed files.</instructions>
  <verification>Confirm only that the named secret exists and the authorized integration succeeds; never print the value.</verification>
  <resume-signal>Confirm secure entry is complete</resume-signal>
</task>

<task type="auto">
  <name>Verify authorized secret configuration</name>
  <action>Use the configured secret reference through the provider's supported secure interface.</action>
  <verify>Check presence and a bounded authenticated request without exposing the value.</verify>
</task>
```

## Dev Server Automation

| Framework | Start Command                | Ready Signal                   | Default URL           |
| --------- | ---------------------------- | ------------------------------ | --------------------- |
| Next.js   | `npm run dev`                | "Ready in" or "started server" | http://localhost:3000 |
| Vite      | `npm run dev`                | "ready in"                     | http://localhost:5173 |
| Convex    | `convex dev`             | "Convex functions ready"       | N/A (backend only)    |
| Express   | `npm start`                  | "listening on port"            | http://localhost:3000 |
| Django    | `python manage.py runserver` | "Starting development server"  | http://localhost:8000 |

**Server lifecycle:**

```bash
# Run in background, capture PID
npm run dev &
DEV_SERVER_PID=$!

# Wait for ready (at most 30 attempts with a one-second bounded HTTP request)
# Wait at most 30 seconds using the installed Python interpreter.
for attempt in $(seq 1 30); do
  if python -c 'import urllib.request; urllib.request.urlopen("http://localhost:3000",timeout=1)' 2>/dev/null; then break; fi
  sleep 1
done
```

**Port conflicts:** inspect ownership. Never kill by port alone. Select another port or stop only a process this session created and positively identified.

**Server lifecycle:** retain owned processes through checkpoints, record PID/start command, then stop only those processes when no longer required. Shared databases and ports may serve other worktrees.

## CLI Installation Handling

Never silently install a CLI, framework or package. Use an existing configured capability. If a required executable is missing, report its exact name, attempted command, purpose and the dependent operation it blocks. Continue independent work. Install only when the user has authorized the installation; record what changed and verify availability before retrying.

## Pre-Checkpoint Automation Failures

| Failure            | Response                                                    |
| ------------------ | ----------------------------------------------------------- |
| Server won't start | Check error, fix issue, retry (don't proceed to checkpoint) |
| Port in use        | Verify owned process identity or use an alternate port                    |
| Missing dependency | Report missing dependency; install only under recorded authorization                                    |
| Build error        | Fix the error first (bug, not checkpoint issue)             |
| Auth error         | Create auth gate checkpoint                                 |
| Network timeout    | Retry with backoff, then checkpoint if persistent           |

**Never present a checkpoint with broken verification environment.** If the local server isn't responding, don't ask user to "visit localhost:3000".

> **Cross-platform note:** use the project's available Python HTTP client or configured readiness check; record a timeout as failed readiness, never a passing checkpoint.

```xml
<!-- WRONG: Checkpoint with broken environment -->
<task type="checkpoint:human-verify">
  <what-built>Dashboard (server failed to start)</what-built>
  <how-to-verify>Visit http://localhost:3000...</how-to-verify>
</task>

<!-- RIGHT: Fix first, then checkpoint -->
<task type="auto">
  <name>Fix server startup issue</name>
  <action>Investigate error, fix root cause, restart server</action>
  <verify>fetch http://localhost:3000 returns 200</verify>
</task>

<task type="checkpoint:human-verify">
  <what-built>Dashboard - server running at http://localhost:3000</what-built>
  <how-to-verify>Visit http://localhost:3000/dashboard...</how-to-verify>
</task>
```

## Automatable Quick Reference

| Action                           | Automatable?               | Claude does it? |
| -------------------------------- | -------------------------- | --------------- |
| Deploy to Vercel                 | Yes (`vercel`)             | YES             |
| Create Stripe webhook            | Yes (API)                  | YES             |
| Write .env file                  | Yes (Write tool)           | YES             |
| Create Upstash DB                | Yes (`upstash`)            | YES             |
| Run tests                        | Yes (`npm test`)           | YES             |
| Start dev server                 | Yes (`npm run dev`)        | YES             |
| Add env vars to Convex           | Yes (`convex env set`) | YES             |
| Add env vars to Vercel           | Yes (`vercel env add`)     | YES             |
| Seed database                    | Yes (CLI/API)              | YES             |
| Click email verification link    | No                         | NO              |
| Enter credit card with 3DS       | No                         | NO              |
| Complete OAuth in browser        | No                         | NO              |
| Visually verify UI looks correct | No                         | NO              |
| Test interactive user flows      | No                         | NO              |

</automation_reference>

<writing_guidelines>

**DO:**

- Automate everything with CLI/API before checkpoint
- Be specific: "Visit https://myapp.vercel.app" not "check deployment"
- Number verification steps
- State expected outcomes: "You should see X"
- Provide context: why this checkpoint exists

**DON'T:**

- Ask human to do work Claude can automate ❌
- Assume knowledge: "Configure the usual settings" ❌
- Skip steps: "Set up database" (too vague) ❌
- Mix multiple verifications in one checkpoint ❌

**Placement:**

- **After automation completes** - not before Claude does the work
- **After UI buildout** - before declaring phase complete
- **Before dependent work** - decisions before implementation
- **At integration points** - after configuring external services

**Bad placement:** Before automation ❌ | Too frequent ❌ | Too late (dependent tasks already needed the result) ❌
</writing_guidelines>

<examples>

### Example 1: Database Setup (No Checkpoint Needed)

```xml
<task type="auto">
  <name>Create Upstash Redis database</name>
  <files>.env</files>
  <action>
    1. Run `upstash redis create myapp-cache --region us-east-1`
    2. Capture connection URL from output
    3. Write to .env: UPSTASH_REDIS_URL={url}
    4. Verify connection with test command
  </action>
  <verify>
    - upstash redis list shows database
    - .env contains UPSTASH_REDIS_URL
    - Test connection succeeds
  </verify>
  <done>Redis database created and configured</done>
</task>

<!-- NO CHECKPOINT NEEDED - Claude automated everything and verified programmatically -->
```

### Example 2: Full Auth Flow (Single checkpoint at end)

```xml
<task type="auto">
  <name>Create user schema</name>
  <files>src/db/schema.ts</files>
  <action>Define User, Session, Account tables with Drizzle ORM</action>
  <verify>npm run db:generate succeeds</verify>
</task>

<task type="auto">
  <name>Create auth API routes</name>
  <files>src/app/api/auth/[...nextauth]/route.ts</files>
  <action>Set up NextAuth with GitHub provider, JWT strategy</action>
  <verify>TypeScript compiles, no errors</verify>
</task>

<task type="auto">
  <name>Create login UI</name>
  <files>src/app/login/page.tsx, src/components/LoginButton.tsx</files>
  <action>Create login page with GitHub OAuth button</action>
  <verify>npm run build succeeds</verify>
</task>

<task type="auto">
  <name>Start dev server for auth testing</name>
  <action>Run `npm run dev` in background, wait for ready signal</action>
  <verify>fetch http://localhost:3000 returns 200</verify>
  <done>Dev server running at http://localhost:3000</done>
</task>

<!-- ONE checkpoint at end verifies the complete flow -->
<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Complete authentication flow - dev server running at http://localhost:3000</what-built>
  <how-to-verify>
    1. Visit: http://localhost:3000/login
    2. Click "Sign in with GitHub"
    3. Complete GitHub OAuth flow
    4. Verify: Redirected to /dashboard, user name displayed
    5. Refresh page: Session persists
    6. Click logout: Session cleared
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues</resume-signal>
</task>
```

</examples>

<anti_patterns>

### ❌ BAD: Asking user to start dev server

```xml
<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Dashboard component</what-built>
  <how-to-verify>
    1. Run: npm run dev
    2. Visit: http://localhost:3000/dashboard
    3. Check layout is correct
  </how-to-verify>
</task>
```

**Why bad:** Claude can run `npm run dev`. User should only visit URLs, not execute commands.

### ✅ GOOD: Claude starts server, user visits

```xml
<task type="auto">
  <name>Start dev server</name>
  <action>Run `npm run dev` in background</action>
  <verify>fetch http://localhost:3000 returns 200</verify>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Dashboard at http://localhost:3000/dashboard (server running)</what-built>
  <how-to-verify>
    Visit http://localhost:3000/dashboard and verify:
    1. Layout matches design
    2. No console errors
  </how-to-verify>
</task>
```

### ❌ BAD: Asking human to deploy / ✅ GOOD: Claude automates

```xml
<!-- BAD: Asking user to deploy via dashboard -->
<task type="checkpoint:human-action" gate="blocking">
  <action>Deploy to Vercel</action>
  <instructions>Visit vercel.com/new → Import repo → Click Deploy → Copy URL</instructions>
</task>

<!-- GOOD: Claude deploys, user verifies -->
<task type="auto">
  <name>Deploy to Vercel</name>
  <action>Run `vercel --yes`. Capture URL.</action>
  <verify>vercel ls shows deployment, fetch returns 200</verify>
</task>

<task type="checkpoint:human-verify">
  <what-built>Deployed to {url}</what-built>
  <how-to-verify>Visit {url}, check homepage loads</how-to-verify>
  <resume-signal>Type "approved"</resume-signal>
</task>
```

### ❌ BAD: Too many checkpoints / ✅ GOOD: Single checkpoint

```xml
<!-- BAD: Checkpoint after every task -->
<task type="auto">Create schema</task>
<task type="checkpoint:human-verify">Check schema</task>
<task type="auto">Create API route</task>
<task type="checkpoint:human-verify">Check API</task>
<task type="auto">Create UI form</task>
<task type="checkpoint:human-verify">Check form</task>

<!-- GOOD: One checkpoint at end -->
<task type="auto">Create schema</task>
<task type="auto">Create API route</task>
<task type="auto">Create UI form</task>

<task type="checkpoint:human-verify">
  <what-built>Complete auth flow (schema + API + UI)</what-built>
  <how-to-verify>Test full flow: register, login, access protected page</how-to-verify>
  <resume-signal>Type "approved"</resume-signal>
</task>
```

### ❌ BAD: Vague verification / ✅ GOOD: Specific steps

```xml
<!-- BAD -->
<task type="checkpoint:human-verify">
  <what-built>Dashboard</what-built>
  <how-to-verify>Check it works</how-to-verify>
</task>

<!-- GOOD -->
<task type="checkpoint:human-verify">
  <what-built>Responsive dashboard - server running at http://localhost:3000</what-built>
  <how-to-verify>
    Visit http://localhost:3000/dashboard and verify:
    1. Desktop (>1024px): Sidebar visible, content area fills remaining space
    2. Tablet (768px): Sidebar collapses to icons
    3. Mobile (375px): Sidebar hidden, hamburger menu in header
    4. No horizontal scroll at any size
  </how-to-verify>
  <resume-signal>Type "approved" or describe layout issues</resume-signal>
</task>
```

### ❌ BAD: Asking user to run CLI commands

```xml
<task type="checkpoint:human-action">
  <action>Run database migrations</action>
  <instructions>Run: prisma migrate deploy && prisma db seed</instructions>
</task>
```

**Why bad:** Claude can run these commands. User should never execute CLI commands.

### ❌ BAD: Asking user to copy values between services

```xml
<task type="checkpoint:human-action">
  <action>Configure webhook URL in Stripe</action>
  <instructions>Copy deployment URL → Stripe Dashboard → Webhooks → Add endpoint → Copy secret → Add to .env</instructions>
</task>
```

**Why bad:** Stripe has an API. Claude should create the webhook via API and write to .env directly.

</anti_patterns>

<type name="tdd-review">
### Independent TDD evidence review

The coordinator reviews assigned TDD plans after integration and before verification. Record RED evidence, GREEN result, ancestry and optional refactor result in the review table. Missing required evidence is a gap; a checkpoint answer, unattended mode or worker assertion cannot convert it into a pass.

If the user explicitly deferred tests, preserve that instruction and its scope. Do not run deferred checks early; retain pending validation and continue independent authorized work. Resume only from the recorded answer and covered scope.
</type>

<summary>

Checkpoints formalize human-in-the-loop points for verification and decisions, not manual work.

**The golden rule:** Prepare and automate concrete work within recorded authority; capability alone does not authorize an external action or human decision.

**Checkpoint priority:**

1. **checkpoint:human-verify** (90%) - Claude automated everything, human confirms visual/functional correctness
2. **checkpoint:decision** (9%) - Human makes architectural/technology choices
3. **checkpoint:human-action** (1%) - Truly unavoidable manual steps with no API/CLI

**When NOT to use checkpoints:**

- Things Claude can verify programmatically (tests, builds)
- File operations (Claude can read files)
- Code correctness (tests and static analysis)
- Anything automatable via CLI/API
</summary>

## Tracer and resume contract

A tracer whose `<verify>` carries `<human-check>` stops for the required human decision in unattended mode too. A passing automated check does not replace that decision. Record the answer and its exact scope before resuming. `auto_select` is a declared option identifier, not approval by itself. Never auto-pass TDD review or human acceptance.
