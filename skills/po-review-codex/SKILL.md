---
name: po-review-codex
description: Run the independent product-owner / code-quality review before declaring a larger change complete, with Codex as reviewer, falling back once to Claude on quota, auth failure or missing CLI. Invariant audit, ≤2,000-char brief, shared 180-second deadline, three-round cap. Skip it for small scoped fixes.
---

# Product-owner review — Codex preferred

Run the independent product-owner / code-quality review with **Codex** as the preferred
reviewer. The full procedure — size gate, invariant audit, ≤2,000-character brief, launch
guard, rounds, severity and stop rules, speed budget — is in
`claude-memory/scripts/PO-REVIEW.md` (adjust the path to your memory repo). Read it in full
first and follow it exactly, passing `--reviewer codex` wherever it says `--reviewer REVIEWER`.

If Codex is out of quota, not logged in or not installed, the runner falls back once to
Claude; say which reviewer produced the verdict in the report. Add `--fallback off` only when
the user asks for Codex alone.
