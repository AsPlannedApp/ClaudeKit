# 06 — Setup guidelines

These are recommendations, not requirements. Each item says what it was *for*, so an equivalent
can be found if the new environment differs.

---

## Settings (`~/.claude/settings.json`)

```json
{
  "permissions": { "defaultMode": "plan" },
  "effortLevel": "medium",
  "advisorModel": "opus"
}
```

- **`defaultMode: "plan"`** makes every session start by exploring and proposing; edits happen
  only after the plan is approved. This is the single biggest contributor to "plan, confirm,
  build". Keep it, and don't let a health check talk you into switching to auto mode.
- **Effort medium**, raised per task for hard planning or debugging.
- **An advisor/reviewer model**, if the setup offers one: Claude consults it before committing to
  an approach and before declaring done.
- **Permissions:** allowlist read-only commands you run constantly (`git status`, `git diff`,
  test runners) to cut prompts. Keep writes to external systems (GitHub API, deploys, DB drops)
  behind a prompt.

### Stop-hook notification (macOS only)

Plays a sound and shows a notification when Claude finishes. That's useful when you switch away
during long tasks.

```json
{
  "hooks": {
    "Stop": [{ "hooks": [{ "type": "command",
      "command": "osascript -e 'display notification \"Claude has finished\" with title \"Claude Code\" sound name \"Glass\"'" }] }]
  }
}
```

On Linux, use `notify-send`; on Windows, a PowerShell toast.

---

## File layout that worked

```
<workspace>/
  CLAUDE.md -> <memory-repo>/CLAUDE.md     # cross-repo conventions, symlinked from a versioned repo
  AGENTS.md -> <memory-repo>/AGENTS.md     # same content, for any other coding agent you use
  .claude/skills -> <memory-repo>/.claude/skills
  <memory-repo>/                           # versioned: knowledge/, feature plans, scripts, security/
  repo-a/  CLAUDE.md  ARCHITECTURE.md
  repo-b/  CLAUDE.md  ARCHITECTURE.md
```

- **Keep a versioned "memory repo".** The KB, feature step folders and helper scripts live in a
  normal git repo, so they survive machines and can be reviewed. The workspace root symlinks
  into it.
- **Each repo gets a `CLAUDE.md` and an `ARCHITECTURE.md`.** `CLAUDE.md` holds commands, structure
  and config. `ARCHITECTURE.md` holds layering rules, patterns with ✅/❌ examples, and agent
  constraints. Rule: **read `ARCHITECTURE.md` before writing new code in a repo.** Generate both
  with the kit's `repository/` templates.
- **The root `CLAUDE.md` covers only cross-repo conventions**: a repo table (directory, tech,
  purpose, URL), the design system quick reference, external services, and which skill runs
  when.
- **An unrelated product in the same workspace** gets a routing note at the top of the root file:
  "for anything in `other-product/`, read its own `AGENTS.md`; none of these rules apply". Better
  still, start the session inside that folder.

---

## MCP servers worth having

| Server | What it was for | Notes |
|---|---|---|
| **Playwright** | Visual checks and end-to-end flows in a real browser: screenshots at matched widths, computed styles, network/console reads | Pair it with a "session bootstrap" skill (below). |
| **Context7** (or any up-to-date docs server) | Current library/framework docs, instead of answers from training memory | Use it even for well-known frameworks; APIs change. |
| **Framework-specific dev MCP** (e.g. a backend framework's own) | Introspecting routes, schema and config | Only when its containers or dev servers are up. Judge it on real tasks and remove it if unused. |

**Evaluated and rejected:** MCPs that duplicate built-in tools (filesystem, git, GitHub, generic
"memory" servers), and API-collection MCPs when the collection's CLI already works. *Why:* every
extra tool costs context tokens and adds a second way to do the same thing.

### Pattern: a session-bootstrap skill for authenticated UI tests

Protected routes redirect to login, so every browser test needs a session first. A small skill
handles that: it creates a throwaway account, confirms it (a disposable inbox works), signs in
through the real login page, or injects auth cookies, and states which dev servers must be
running. Write one per app as `.claude/skills/<app>-session/SKILL.md`.

---

## CLIs worth installing

- **`gh`**, for PRs, issues and API calls.
- **Your API collection's CLI** (Bruno, Postman/Newman, Hurl…). `/api-review` runs the affected
  requests against the local environment only.
- **The `claude` CLI itself**, which runs headless (`claude -p`) as the PO reviewer.
- **Note:** global CLIs installed under a version manager vanish on each version bump.

---

## Security routine

- **A monthly checklist** for dependency advisories, secret scanning, exposed ports and expiring
  credentials. These checks only inspect: they never fix, install, restart or rotate on their
  own.
- **Security hardening** happens on a dedicated branch per repo, one reviewable step at a time.
  Each step stops with the diff, the rationale, the exact verification, the gaps and the next
  proposed step.
- **Urgent advisories and suspected credential exposure** are raised immediately.
- **Reports never contain secrets or private user data.**

---

## Health checks

If you run a setup doctor, have it skip suggestions you've already declined (like switching to
auto mode). Record the decline in memory so it isn't asked again.
