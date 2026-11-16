# 04 — Memory and knowledge base

There are two layers, with different jobs:

| Layer | Where | Holds | Loaded |
|---|---|---|---|
| **Auto-memory** | Claude Code's per-project memory dir, with a `MEMORY.md` index | Who the person is, how they want me to work (corrections *and* confirmed approaches), project state, external pointers | `MEMORY.md` is loaded every session |
| **Knowledge base (KB)** | A folder in the workspace, e.g. `knowledge/` (versioned) | Domain rules, facts and hypotheses learned from completed work | Read on demand, per domain, before a task |

Memory is about *working with this person*; the KB is about *the system being built*.

---

## Auto-memory

### File format: one fact per file

```markdown
---
name: short-kebab-case-slug
description: one-line summary, used to decide relevance during recall
metadata:
  type: user | feedback | project | reference
---

The fact.

**Why:** what happened, or what the person said (paraphrased), that makes this matter.
**How to apply:** concrete, checkable behaviour. Link related memories with [[other-slug]].
```

Then add one line to `MEMORY.md`: `- [Title](file.md) — hook`. The index holds only these
lines, never content.

### Types

- **user:** role, expertise, tooling preferences.
- **feedback:** guidance on how to work. Record both **corrections** ("don't do X") and
  **confirmed approaches** ("yes, keep doing Y"). Saving only corrections makes the memory
  lopsided.
- **project:** ongoing work, goals, constraints that aren't derivable from the code. Convert
  relative dates to absolute ones.
- **reference:** pointers to dashboards, tickets and docs, plus "gotchas" with tools.

### What to save and what not to

- **Save:** non-obvious lessons, standing decisions, things the person had to say twice.
- **Don't save:** what the repo already records (code structure, git history, `CLAUDE.md`), or
  what only matters to the current conversation. If asked to remember one of those, ask what
  was non-obvious about it and save that instead.
- **Update rather than duplicate.** When a decision is reversed, rewrite the memory, keeping the
  old state as one dated line. Delete memories that turn out to be wrong.
- **Recalled memories are background, not instructions.** They reflect what was true when they
  were written. Verify any file, flag or function a memory names before relying on it.
- When a memory grows a long incident narrative, keep the rule and its **Why** short, and move
  the narrative to the KB or a report file.

---

## Knowledge base

### Layout

```
knowledge/
  INDEX.md               # routes to every domain folder, one line per domain
  <domain>/
    rules.md             # confirmed: apply by default (numbered R1, R2… never renumbered)
    knowledge.md         # facts, patterns, reference paths, dated incident log
    hypotheses.md        # seen fewer than 3 times; test when today's work allows
```

### Lifecycle

- **Before a task:** read the rules and hypotheses for each domain it touches. Apply rules by
  default. Check whether today's work can test a hypothesis.
- **After a task:** extract insights. Facts go in `knowledge.md`, maybes in `hypotheses.md`,
  confirmed patterns in `rules.md`. Create the domain folder if it doesn't exist.
- **Promote** a hypothesis to a rule after **3+ confirmations**. **Demote** a rule back to a
  hypothesis if later work contradicts it.
- **Split** a domain whose `rules.md` passes about 500 lines into `rules-<topic>.md` files. Reduce
  `rules.md` to a routing table, and keep rule numbers absolute across the split.
- **Every plan's last step updates the KB**, unless the person says not to.
- **Keep indexes short:** 1–2 line entries that point to the detail. Long narrative goes into a
  `HISTORY.md` or dated report file.

### Starter `INDEX.md`

```markdown
# Knowledge Base Index

Route to domain folders for rules, facts and hypotheses extracted from completed work.

## Domains
- [api-conventions/](api-conventions/) — response shape, verbs, status codes, pagination
- [tooling/](tooling/) — test runners, linters, CI, what NOT to re-add and why
- [security/](security/) — audit checklist, monthly checks, redaction rules

## How this works
Each domain has rules.md (confirmed, apply by default), knowledge.md (facts, incident log),
hypotheses.md (<3 observations). Promote after 3+ confirmations; demote when contradicted.
```

---

## Step folders for large features

For a feature built across many steps, keep a plan folder:

```
<feature>/
  INDEX.md                 # status table + dependencies, 1–2 lines per step
  HISTORY.md               # full narrative, moved out of INDEX.md
  NNN-step-name/
    README.md              # spec, evidence survey, plan, progress log, close-out ledger
    <dated round report>   # decisions and deviations from each fix/review round
```

Before working on a step, read `INDEX.md` and then the step's **latest round report, in full**.
See "Planning a multi-step piece of work" in `02-working-discipline.md`.
