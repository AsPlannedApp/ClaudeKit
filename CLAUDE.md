# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Repository Overview

**Project** is a SaaS application. The workspace contains these codebases:

| Directory         | Tech                                | Purpose                                 | URL                                 |
|-------------------|-------------------------------------|-----------------------------------------|-------------------------------------|
| `claude-memory/`  | Claude KB and Plans                 | Keep Claude Code updated and consistent | -                                   |
| `public-app/`     | Next.js 16, TypeScript, Tailwind v4 | Marketing site + API backend            | project.app (Vercel)                |
| `logged-app/`     | Vue 3, JavaScript, Tailwind v4      | Logged-in SPA                           | me.project.app (Cloudflare Workers) |
| `backend-php/`    | Laravel 13, PHP 8.4                 | Backend API (iCal, data processing)     | Docker, port 4000                   |
| `api-collection/` | Bruno/Postman API Collection        | Centralized API endpints for test       | —                                   |
| `project-ui/`     | npm workspaces                      | Shared design-system component library  | localhost playgrounds               |
| `project-design/` | Static reference                    | Design tokens, fonts, preview HTML      | Claude Design                       |

Each sub-repo has its own `CLAUDE.md` with repo-specific detail, and an `ARCHITECTURE.md` with
structural rules and agent constraints. **Read `ARCHITECTURE.md` before writing any new code in a
sub-repo.** This root file covers cross-repo conventions only.

---

## claude-memory/ — Self-Memory Layer

`claude-memory/` is the cross-repo planning and memory layer for this project. It is **not** a
deployable codebase — it is Claude's persistent working memory for the Project: `knowledge/` holds
domain rules/facts/hypotheses (routed via its own `INDEX.md`), `plans/` holds the active feature
plans as numbered step folders, each with its own `README.md` spec.

**Before starting any plan work:** read `claude-memory/plans/INDEX.md` to check step status and
dependencies. Each step folder has its own `README.md` with the full spec for that step. **Then
check the target step's own folder for the most recent dated report** (a `TECH_REPORT.md`, a
`FIXES/` round file, or similar) and read it in full before planning — `INDEX.md` gives status, not
the decisions and deviations a prior round already made and reasoned through. Skipping this has
directly caused sessions to redo already-settled work and reverse explicit, user-confirmed decisions
they never saw recorded.

---

## Verification & Working Discipline

Behaviour rules (verification, primary sources, scope, fix-the-class, voice, git safety) live in the
user-level voice layer, installed from this kit's `voice/` to `~/.claude/voice/`. Apply them on
every task; `~/.claude/voice/02-working-discipline.md` has the full list with the reason for each
rule.

---

## Basic Knowledgebase

Use the per-domain knowledge base in `claude-memory/knowledge/<domain>/` (`knowledge.md`,
`hypotheses.md`, `rules.md`, routed by `claude-memory/knowledge/INDEX.md`): read the domain's rules
before a task, write lessons back at the end. Lifecycle and promotion rules:
`~/.claude/voice/04-memory-and-knowledge.md`.

---

## API Review

Whenever code in any codebase that touches the API contract changes — new routes, modified response
shapes, new client-side consumers — run `/api-review` against the affected endpoint and consumer.

The skill covers: response envelope shape, HTTP verb/status rules, 204 empty-body handling,
pagination shape, Bruno collection sync, and JS/Vue consumer alignment.

Trigger points by codebase:
- **backend-php**: any new/modified controller, route in `routes/api.php`, or `ApiResponse` usage
- **public-app**: any new/modified route in `pages/api/v1/`, changes to `helpers/api/api-util.ts`,
  or page code that destructures API responses
- **logged-app**: any `src/views/` or `App.vue` code that reads `element`, `collection`, or
  `pagination` from API data

---

## Independent product-owner review

Before declaring any **larger** multi-repository implementation complete (new feature, multi-file
implementation, design-facing change), run an independent product-owner / code-quality review with
`/po-review-codex` or `/po-review-claude`, whichever the user prefers. Both launch
`claude-memory/scripts/codex-po-review.sh` and follow `claude-memory/scripts/PO-REVIEW.md` (the
≤2,000-char What-asked/Plan/Implementation brief, invariant audit, rounds, visual-fidelity gate);
the rules and reasons are in `~/.claude/voice/05-review-loop.md`. The preferred reviewer falls back
once to the other on quota, login failure or a missing CLI. **Small, scoped fixes skip it**
(lint/tests green is enough). For a large change, ask the user to confirm the plan before running
the gate — do not self-classify a large change as "small".

---

## Rate limiting

If the workspace rate-limits any endpoints, keep the approach identical across codebases:

- **Every threshold is an env var**, never a code literal — e.g.
  `RL_<NAME>="<max>/<seconds>[,<max>/<seconds>]"`. A single `RATE_LIMIT_MULTIPLIER` scales every
  `max` (e.g. loosen staging), and `RATE_LIMIT_ENABLED=false` disables all limiters (local dev).
  Changing a limit is a redeploy, not a code edit.
- **Keyed per authenticated user, else per client IP.** Non-production honours a
  `X-RateLimit-Bypass: <secret>` header (used by automated tests).
- **Rejections return the standard error envelope** (status 429) plus `Retry-After` and
  `X-RateLimit-*` headers — the same envelope every other error uses.
- **Auth endpoints fail *open*** on limiter/store failure (an auth path must not go dark); other
  endpoints may fail closed.
- **Record rejections fire-and-forget and debounced** (e.g. one counter increment per reject,
  a durable write only on the first rejection of each key+window and then rate-limited) so a
  burst can't turn the limiter into a DB/log amplifier.

---

## Playwright Visual Testing

Before any Playwright MCP test against the logged-in Vue SPA, run `/playwright-session` to create a
throwaway account, confirm it, log in, and inject the auth cookies into the browser. Without this
step, protected routes immediately redirect to login.

Requires both dev servers running:
- `localhost:3000` — `public-app` (hosts the auth API)
- `localhost:3001` — `logged-app` (the Vue SPA under test)

Trigger points:
- **logged-app**: any time you want to visually test a feature in the logged-in SPA
- **public-app**: if you need to verify API-backed browser flows end-to-end

---

## public-app/ (Next.js marketing + API)

```bash
cd public-app
nvm use v22.22.3 && npm install
npm run dev         # http://localhost:3000 + Tailwind watch
npm run ci:check    # prettier:fix + tsc + jest — use before committing
```

Pages Router only (`appDir` disabled). See `public-app/CLAUDE.md` for Contentful CMS release
flow, Tailwind build details, and the full API route structure.

---

## logged-app (Vue 3 SPA)

```bash
cd logged-app
npm install
npm run dev         # Vite dev server at http://localhost:3001
npm run test        # Vitest
```

Deployed to Cloudflare Workers via `wrangler.toml`. See `logged-app/CLAUDE.md` for structure
(`src/views/`, `src/components/`), state management (no global store in use — a store library
may be installed but unused; `App.vue` holds state via `provide()`, don't add a store without
discussing it), and testing details.

---

## backend-php (Laravel API)

```bash
cd backend-php
npm run dev       # Docker services, port 4000
docker-compose exec php-fpm php artisan test
```

All routes under `/api/v1/`. See `backend-php/CLAUDE.md` for structure, Pint/PHPStan config,
and IDE-helper regeneration after migrations.

---


## project-ui (shared design system)

```bash
cd project-ui
npm install
npm run build --workspace @ProjectApp/tokens           # rebuild order: tokens → css → vue → web/react
npm run dev --workspace @ProjectApp/playground-design  # http://localhost:5173
```

npm workspaces monorepo: `@ProjectApp/{tokens,css,vue,web,react,fonts,email}`. See
`project-ui/CLAUDE.md` for full design-system details, token values, and component specs.

**Architectural rule:** `tokens → CSS variables / @theme → Vue components`. Lower layers must
never import higher layers.

---

## Design System Quick Reference

Brand colors (canonical values, used across all codebases):

| Role | Token | Hex |
|---|---|---|
| Brand primary | `--brand` | `#000000` (example) |
| Brand secondary | `--brand-light` | `#000000` (example) |
| CTA / accent | `--brand-opposite` | `#000000` (example) |
| Fill / accent 2 | `--brand-fill` | `#000000` (example) |

Fonts: **{{Heading font}}** (headings h1–h4), **{{Body font}}** (body/UI), **{{Wordmark font}}**
(logo wordmark), **{{Display font}}** (display accent). Served from `fonts.project.app` via
Cloudflare Worker (or your own font host).

Icons: pick one icon library and stick to it across every codebase (e.g. `@tabler/icons-vue` /
`@tabler/icons-react`) — outline style, consistent stroke width. Never use emoji as icons in the app
UI.

Buttons: pick one border-radius convention for the app shell (e.g. `14px`, not pill) and one for the
marketing site (e.g. pill). No gradients in production UI unless that's a deliberate brand choice.

---

## External services

- **CMS:** Contentful (blog/marketing content)
- **DB:** PostgreSQL via Docker (backend-php)
- **Cache:** Redis
- **Storage:** Amazon S3
- **Email:** Amazon SES + Nodemailer
- **Deploy:** Vercel (public-app), Cloudflare Workers (logged-app, project-ui/fonts)