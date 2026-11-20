# 05 — The independent product-owner review

A second, independent reviewer reads the change as a product owner and code-quality gate before
I call larger work complete. **The reviewer is a fresh, read-only agent** started headless. It has
none of my implementation context, which is the point. Which agent runs it comes from the
skill the person picks: `/po-review-claude` (a headless Claude) or `/po-review-codex` (Codex).
Either one falls back once to the other when its provider is out of quota, not logged in or not
installed. The review log records which reviewer produced the verdict.

The runnable steps are in those skills and the procedure they share (`scripts/PO-REVIEW.md` in
the memory repo).

---

## When it runs: size-gated

| Change | Gate |
|---|---|
| **Small, scoped fix:** a targeted bug fix, one review comment, a one-file correction | Skip the review. Green lint/tests is enough. |
| **Larger:** a new feature, a multi-file implementation, a design-facing change | **Confirm the plan with the person first**, then implement, then run the review before reporting done. |

Never classify a large change as small yourself; ask when unsure.
*Why:* the person wants to be in the loop on what's about to be reviewed and shipped, not just
see a pass/fail afterwards.

---

## The brief: at most 2,000 characters

Three headings: **What was asked**, **Plan** (including approved exceptions), and
**Implementation** (what changed, tests actually run with their results, and gaps not verified).

- **Launch only behind a guard:** `n=$(wc -m < "$B"); [ "$n" -le 1900 ] && <launch>`. Trim and
  retry if it fails. Never launch in the same command as an unguarded edit.
- **Between rounds, replace** the single "Rounds 2–N fixed: …" line. Don't append a line per
  round, or the brief creeps over the limit.
- **Cut first:** test-count detail, file lists, live-check narration. **Keep:** what was asked,
  decisions, changes, tests, and gaps.
- Don't ask the reviewer to read the whole planning history, and don't reference findings from
  a session it can't see.

*Why:* an oversized brief got rejected one or two times per review, again and again, because
round notes kept being appended and the gate was launched anyway.

---

## Invariants and evidence (non-trivial logic)

Before round 1, write **5–15 one-line invariants**. For each one, give:
- the search used, and the **complete** list of sites (`file:line`), covering callers, alternate
  inputs, preprocessing, fallbacks and exits;
- at least one class-level test, with its actual result.

Hand these to the reviewer as a separate evidence file. Reviewers must verify them, not trust
them. Each invariant comes back **confirmed**, **violated** (with sites), or **unverifiable**
(with reason).

---

## Severity and stop rules

- **P1:** wrong results or data loss on realistic inputs, or a concrete user-visible regression.
  **Blocks.**
- **P2:** wrong only on rare or exotic inputs, or a guarantee violated without visible harm.
  Doesn't block; goes to follow-ups.
- **P3:** test or documentation gaps. Doesn't block; goes to follow-ups.

Strict wording doesn't promote an exotic issue to P1.

- After **any** finding, name its class and search all sibling sites. Fix every P1 sibling
  inside the approved scope in the same round; report the ones outside it and checkpoint
  before fixing them.
- P2/P3 go into `follow-ups.md`, with source round and sites. Don't loop just to clear them.
  Fix a trivial one only if it's useful. Never point the person at that file: one
  that needs them becomes a "For you to decide" item (`01-voice.md`).
- **At most three rounds.** If round 3 still fails, stop and present the unresolved P1s,
  uncertainty and options to the person. Don't restart the session to dodge the cap.
- **Fix rounds review the delta**, plus previous P1s and class siblings, not the whole branch
  again. Without commits, the delta is the cumulative working tree against the frozen base.
- **Keep each round fast** with a hard time budget (a few minutes). Packing whole files into
  parallel parts, each owning specific invariant classes, beats several reviewers each
  re-reading everything.
- **Snapshots:** with the person's OK to commit, commit each reviewed snapshot and use its SHA as
  the next base. Without it, review the working tree (including untracked files) against a fixed
  base. The skill has both paths.
- **Invalid output, a timeout or a crash is an unsuccessful review, never a PASS.**

---

## Visual fidelity

A text-diff review can't establish that a UI matches a design. When there's a design reference,
compare screenshots at matched widths yourself, check the full computed style of the changed
interactive elements, and say in the brief what was checked.

---

## Reporting the result

Report the result in the shape of `01-voice.md`: the outcome, not the history of the rounds (only
when asked). Review details (skipped, reviewer, base, a trivial follow-up fixed) appear only when
they affect the outcome or something the person decides or does. Follow-ups that need the person
become "For you to decide" items; never point them at the follow-ups file. If the cap was reached,
lead with that.
