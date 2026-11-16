---
name: po-review-claude
description: Run the independent product-owner / code-quality review before declaring a larger change complete, with Claude as reviewer, falling back once to Codex on quota, auth failure or missing CLI. Invariant audit, ≤2,000-char brief, shared 180-second deadline, three-round cap. Skip it for small scoped fixes.
---

# Product-owner review — Claude preferred

Run the independent product-owner / code-quality review with **Claude** as the preferred
reviewer. The full procedure — size gate, invariant audit, ≤2,000-character brief, launch
guard, rounds, severity and stop rules, speed budget — is in
`claude-memory/scripts/PO-REVIEW.md` (adjust the path to your memory repo). Read it in full
first and follow it exactly, passing `--reviewer claude` wherever it says `--reviewer REVIEWER`.

If Claude is out of quota, not logged in or not installed, the runner falls back once to
Codex; say which reviewer produced the verdict in the report. Add `--fallback off` only when
the user asks for Claude alone.
