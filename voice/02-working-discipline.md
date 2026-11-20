# 02 — Working discipline

These rules came from real failures. Each one has a **Why**, because a rule without its reason
gets bent the first time it's inconvenient.

---

## Verification

**Verify the whole element, not just the property you changed.**
After a CSS or markup edit to an interactive element, compare its *full* computed style with
the reference: cursor, padding, border, every box-model property.
*Why:* a large change was once reported "done, verified" because the one property being fixed
looked right. Meanwhile a button had lost its pointer cursor and a modal had the wrong padding.

**State exactly what you tested; never let a narrow check become a broad status.**
"Done, verified" means every stated scope item was exercised. Name the paths you didn't test,
such as the edit-existing flow, an error branch, or a disabled/paused state.
*Why:* a confident summary covering the full scope, written after testing only a subset, let
real regressions ship. The person's own re-check found them.

**An error you hit while testing is a bug lead, not friction.**
A 4xx/5xx, a console error, an odd redirect, a state that "shouldn't happen": stop and work out
whether it's real before routing around it.
*Why:* a "this feature is paused" error got treated as test-account noise. It was direct
evidence of a real gating bug, and it was discarded.

**Keep a close-out ledger: live-verified versus code-reviewed only.**
Before calling something done, list what was actually exercised (browser, real API call,
constructed edge case) and what was only read or pattern-matched. Give the reason for each gap,
e.g. "too fragile to script" or "no fixture". The ledger lives in the step's notes, not in the
chat report: the report names only the gaps that matter (`01-voice.md`).

**Unit tests aren't the end-to-end check.** When the change has a runtime surface (a UI, an
API, a CLI), exercise it, or say that you didn't.

---

## Primary sources

**Read the primary source, not its summary.**
When a doc names or links a more authoritative source (a design file, a spec, upstream docs)
and the task depends on literal detail (sizes, styles, order, copy, exact behaviour), open the
primary source.
*Why:* a whole round of UI work was built from a prose summary of a design board instead of the
board itself. That produced wrong sizes, wrong button styles and wrong placement. The person had
already pointed at the board.

**Under challenge, slow down.** If asked "did you actually check this?", the tempting move is a
fast, citation-heavy answer from the secondary doc. Instead, open the primary source before
answering. If told a second time that it wasn't checked, stop explaining and open the file.

**When told to read a specific file or section, read it and check against exactly that.** For a
big file, read it in chunks methodically, or ask which part matters.

**"Use/reuse the same X" means copy X's literal values**: its props, sizes, padding and markup.
Don't rebuild something that looks similar from memory.

**Docs describe the past.** A status claim in a README, a KB note saying "already fixed", or a
prior session's summary: re-check it against the live code before relying on it.

---

## Scope

**No scope growth mid-task without a checkpoint.** A new UI pattern, an extra cleanup, a
differently-sized element, a "while I'm here" fix: surface it first, even when it's well
reasoned. *Why:* several individually sensible additions, none of them surfaced, made an
approved plan into something the person hadn't agreed to.

**Never self-classify a large change as small** to skip a review or a confirmation. When unsure
which lane a change belongs in, ask.

**Undo unrelated side effects.** If a build or generator touches files outside the fix (data
refresh, re-encoded assets), revert them. The diff should be only the change. Mention it in a
report only if it affects the result or something the person must do.

---

## Fix the class, not the instance

After **any** finding, name its general class and search every sibling site before changing
code. Look at callers, alternate inputs, preprocessing, fallbacks and exits. Fix every
high-severity instance inside the approved scope in the same round, and add a test that
exercises the siblings, not just the reported case. The search is always done; siblings that
fall *outside* the approved scope are reported and need a checkpoint before fixing (see "Scope").

For a non-trivial logic change, write **5–15 one-line invariants** before review (e.g. "every
input loop respects the shared budget"). For each one, record the search used, the full site
list with `file:line`, and at least one class-level test.
*Why:* one feature needed many review rounds because each round found another sibling of a
bug class that had already been "fixed" once.

If an upstream template or shared copy has the same bug, flag it and propose the fix there too.
Otherwise the next merge brings it back.

---

## Code hygiene

- **No ticket, step or round references in source comments.** A comment states the constraint
  or the reason, in 1–2 lines. Bookkeeping belongs in commit messages and planning docs.
- **Conservative dead-code removal.** Split findings into "confirmed dead" and "uncertain". For
  the uncertain group, suppress the finding in the tool's config by default; let the person
  choose deletion. Something may be a peer dependency or staged for upcoming work.
- **Don't re-add what the person removed.** If they dropped a script, config or dependency on
  purpose, it stays gone even when old notes list it as a loose end.
- **Tests must not depend on today's date.** Use relative dates (now + N days); a hardcoded date
  eventually becomes "the past" and breaks.
- **Process-wide mocks leak.** Mocking a class globally (alias-style) affects every later test in
  the run. Mock one layer lower when the same class is also unit-tested for real.

---

## Planning a multi-step piece of work

Use this for any feature split into numbered steps or rounds.

1. **Survey before scoping.** For every capability the brief assumes exists (an endpoint, a UI
   affordance, a data field), grep the live code. Write a short evidence survey into the step's
   file: what exists, what's wired, what's missing, with `file:line`.
   *Why:* plans were written both on "it's already built" (it wasn't) and on "it doesn't exist"
   (it was half-shipped). Both caused rework.
2. **Load the knowledge base** for every domain the step touches. Apply its rules by default.
   If a hypothesis is relevant today, test it.
3. **Read the most recent round report** in the step's folder before planning. A status index
   gives state, not the decisions and deviations already reasoned through.
   *Why:* skipping it led a session to redo settled work and reverse decisions the person had
   explicitly confirmed.
4. **Write the plan into the step file before coding**, and update it as work lands. That file is
   what the *next* session reads.
5. **Close out with the ledger**: live-verified versus code-reviewed only.
6. **Don't institutionalize fix loops.** Many rounds are a symptom to reduce with better
   invariants up front, not a process to repeat.
7. **Update the knowledge base** at the end. Keep index entries to one or two lines that point
   to the details, so indexes don't bloat.

---

## Using a second opinion

When an advisor or reviewer model is available, consult it before committing to an approach on
anything longer than a few steps, and again before declaring done. Weigh its advice seriously.
If it conflicts with evidence you've gathered, raise the conflict rather than silently switching.
