# ClaudeKit

A reusable Claude Code setup in two layers:

1. **Voice (user level)** — how Claude plans, verifies, remembers, reviews and **talks**. Applies
   to every project. Lives in `voice/`, installed to `~/.claude/`.
2. **Workspace (project level)** — a root `CLAUDE.md` for a multi-repo SaaS workspace (marketing
   site + logged-in app + backend API + shared design system, etc.), its skills and scripts, and a
   kit for generating per-repo docs.

Both were distilled from months of daily work on a multi-repo product. Nothing here is magic: the
rules work because they are concrete (good/bad pairs, explicit report shapes, a reason for each).

## What's in here

| Path | What it is | Install it as |
|---|---|---|
| `voice/CLAUDE.md` | Compact core: non-negotiables, pointers to the chapters | `~/.claude/CLAUDE.md` |
| `voice/01-voice.md` | How Claude speaks, reports, explains and hands off | `~/.claude/voice/` |
| `voice/02-working-discipline.md` | Verification, scope, primary sources, fix-the-class, planning | same |
| `voice/03-git-shell-safety.md` | Branches, commits, hooks, user commands, secrets, background jobs | same |
| `voice/04-memory-and-knowledge.md` | Auto-memory format and a per-domain knowledge base | same |
| `voice/05-review-loop.md` | The size-gated independent product-owner (PO) review | same |
| `voice/06-setup-guidelines.md` | Settings, hooks, MCP servers, repo docs, as recommendations | read once while setting up |
| `CLAUDE.md` | Workspace root guidance: repo table, cross-repo conventions, skill triggers | symlink at the workspace root |
| `skills/po-review-claude/` | PO review with a fresh read-only headless Claude, falling back to Codex | `.claude/skills/` |
| `skills/po-review-codex/` | The same review with Codex, falling back to Claude | `.claude/skills/` |
| `skills/api-review/` | REST endpoint/consumer review against a house standard (`{{…}}` placeholders) | `.claude/skills/`, if the project has an HTTP API |
| `skills/playwright-session/` | Bootstraps an authenticated browser session before visual tests | `.claude/skills/`, adapt to your app |
| `scripts/` | `codex-po-review.sh` (the PO runner for both reviewers) + `PO-REVIEW.md` (its procedure) + `tests/`, `git-msg.sh` (one-line commit subject from the diff, needs `codex`), `logs/` | your memory repo's `scripts/` |
| `repository/` | Templates for a per-repo `CLAUDE.md` + `ARCHITECTURE.md`, with Laravel, Vue 3 and Next.js starting points | copy into a repo temporarily |

Install one or both PO skills: each sets the preferred reviewer, and the runner falls back once
to the other when the preferred one is out of quota, not logged in or not installed (both CLIs
needed for the fallback; `--fallback off` disables it). Rules: `voice/05-review-loop.md`.

## Layer 1 — voice

1. **Personalise, then put the core in place.** First fill in "About the person I work with" in
   `voice/CLAUDE.md` (working preferences only, no personal data). It loads the chapters through
   `@` import lines. The commands below never overwrite existing files (`cp -n`); back up first, and
   merge by hand wherever a file already exists. Pick one layout:

   **User level (recommended; applies to every project).** The imports already point here:
   ```bash
   mkdir -p ~/.claude/voice
   [ -e ~/.claude/CLAUDE.md ] && cp -n ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak.$(date +%Y%m%d%H%M%S)
   cp -n ClaudeKit/voice/0*.md ~/.claude/voice/
   cp -n ClaudeKit/voice/CLAUDE.md ~/.claude/CLAUDE.md   # skipped if it exists: merge by hand
   ```

   **Project level (one project only).** Keep the kit in its own folder so the project's
   `CLAUDE.md` stays free to be generated or edited:
   ```bash
   mkdir -p <project>/.claude/voice
   cp -n ClaudeKit/voice/0*.md <project>/.claude/voice/
   cp -n ClaudeKit/voice/CLAUDE.md <project>/.claude/voice/core.md
   ```
   In `core.md`, swap the five `@~/.claude/voice/…` lines for the commented `@./0…` block below
   them. Then add **one line** to the top of the project's own `CLAUDE.md` (create it if
   missing):
   ```
   @.claude/voice/core.md
   ```
   Imports resolve relative to the file that contains them, so `core.md` finds its sibling
   chapters. When `repository/` generates or regenerates a `CLAUDE.md`, keep that import line.
   To change your preferences later, edit the installed copy (`~/.claude/CLAUDE.md` or
   `<project>/.claude/voice/core.md`), not the kit.
2. **Settings.** Go through `voice/06-setup-guidelines.md` and apply what fits.
3. **Knowledge base.** Create the folder described in `voice/04-memory-and-knowledge.md` the
   first time a task produces a lesson. Don't pre-fill it.

## Layer 2 — workspace

The workspace `CLAUDE.md` points to the voice chapters under `~/.claude/voice/` instead of
repeating them, so install Layer 1 first, at **user level**. With the project-level layout,
change those pointers to `.claude/voice/`.

### Set up the workspace layer

1. Copy this `ClaudeKit/` folder to the root of your multi-repo workspace, alongside your other repos
   (e.g. `my-workspace/ClaudeKit/`, `my-workspace/public-app/`, `my-workspace/backend-php/`, …).
2. Symlink `CLAUDE.md` to the workspace root so Claude Code picks it up automatically:
   ```bash
   [ -e CLAUDE.md ] || ln -s ClaudeKit/CLAUDE.md CLAUDE.md   # an existing CLAUDE.md: merge by hand
   ```
3. Edit `CLAUDE.md`: replace the repo table, tech stack, brand tokens, and external services with
   your actual project's details. Search for `{{...}}` placeholders in the Design System section.
4. Point Claude Code at `skills/` (e.g. symlink or copy into `.claude/skills/`) if you want
   `/api-review`, `/playwright-session`, `/po-review-claude` or `/po-review-codex` available, and adjust their
   `SKILL.md` content to match your actual endpoints/ports.
   - Both PO skills run `scripts/codex-po-review.sh` (Python 3.9+), which assumes it sits at
     `<workspace-root>/<memory-repo>/scripts/` (it derives the workspace root as two levels up).
     Copy `scripts/` — including `scripts/logs/.gitignore` — into your memory repo so that holds,
     or set `CODEX_PO_WORKSPACE_ROOT` if it lives elsewhere; the skill invokes it as
     `./claude-memory/scripts/codex-po-review.sh`, so adjust that path (in the skills and
     `scripts/PO-REVIEW.md`) to match. Set `CODEX_PO_REPOS` to your real repo list (edit the
     default in the script). The runner needs `claude` and/or `codex` on `PATH`; `git-msg.sh`
     needs `codex`. Check it with `python3 -m unittest discover -s scripts/tests`.

### Generate per-repo docs with `repository/`

For each sub-repo that needs its own `CLAUDE.md` + `ARCHITECTURE.md`:

1. Copy `repository/CLAUDE.template.md`, `repository/ARCHITECTURE.template.md`, and
   `repository/INSTRUCTIONS.md` into that repo's root.
2. Open Claude Code in that repo and tell it: **"Follow INSTRUCTIONS.md."**
3. Claude will inspect the real codebase (framework, scripts, folder structure, patterns) and
   produce a filled-in `CLAUDE.md` and `ARCHITECTURE.md`, dropping any template sections that
   don't apply (e.g. API conventions in a repo with no API surface).
4. Once you're happy with the result, let Claude delete the three template/instruction files from
   that repo — they're bootstrapping-only and aren't meant to ship alongside the generated docs.

## What this kit can't carry over

- **The accumulated memories and knowledge base** were deliberately left behind: they were about
  one product. The *method* for building them is in `voice/04`; the new project will grow its own.
- **The habits that came from corrections** are written as rules, each with its reason. The
  reasons matter. Keep them when you edit the rules, since a rule without its "why" tends to get
  argued away under pressure.
- **Tooling differs.** MCP servers, CLIs and hooks are recommendations; `voice/06` says what each one
  was for, so you can find an equivalent.

## Keeping it generic

Before sharing this repo, grep for anything personal or project-specific that slipped back in:

```bash
grep -rniE "<your-name>|<your-product>|<your-email-domain>|<your-home-dir>" --include="*.md" --include="*.sh" .
```
