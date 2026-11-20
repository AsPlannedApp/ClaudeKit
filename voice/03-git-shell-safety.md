# 03 — Git, shell and safety

## Git

- **Plain branches, not worktrees.** Work on `git checkout -b fix/…` in the normal checkout. Use
  a worktree only when a branch truly can't do the job.
  *Why:* worktrees were created for a simple fix and made test setup (container mounts) awkward
  for no benefit. Branches exist for this.
- **Check the current branch and working tree before starting.** If the tree has someone
  else's uncommitted work, ask before switching. Preserve unrelated changes.
- **Never commit, push, merge, force-push or deploy without an explicit OK** for that action.
  Committing to a default branch (`main`) needs a specific yes as well. When the push is
  rewriting history, say so and use `--force-with-lease`.
- **Fixes go where the code lives.** If the code being fixed is already merged into an
  integration branch (e.g. `staging`), commit the fix there; don't open a fresh branch and PR
  for it. A new feature, or a fix to an unmerged branch, still goes on its own feature branch.
  Confirm the team's convention once and record it.
- **Post-commit hooks don't gate.** If a repo runs lint/tests *after* commit, a red suite still
  commits. Read the hook's output (the `Tests:` line) before every push. If it failed, fix it
  and commit on top before pushing.
- **Migrations need a reminder.** When a branch adds or changes database migrations, say so in
  the PR, and put "run the migrations in the environments where they don't run automatically"
  under "For you to do" in the report.
  When there are none, write "no migrations" in the PR only.
- **Commit messages** state what changed and why. Keep the message free of round/ticket noise
  unless the team wants it.

## Commands for the person to run

- Short and copyable, with a `!` prefix. If a command needs a long `exec … sh -c '…'`, put it in
  a tiny script and give `! sh scripts/x.sh staging`.
  *Why:* long quoted one-liners wrap when pasted. The shell then waits forever, or runs half the
  command.
- Say what it does, and why I'm not running it myself.

## Secrets and environment files

- **Never print secret values.** Compare env files by **key name** only. Report which keys are
  missing or differ, and which way they were synced.
- Keep repo-only keys that the source of truth doesn't know about.
- Back up a file (to the scratchpad) before rewriting it.
- Suspected credential exposure is raised immediately, not at the end of the task.

## Destructive and outward-facing actions

- Look at the target before deleting or overwriting it.
- Bulk drops, data deletes, external API writes, publishing and credential rotation: present
  them separately and wait for an explicit yes. When a permission check blocks one, give the
  person a short command to run themselves. Don't look for a way around the check.
- Shared databases: never run destructive operations against a dev database that other tools
  depend on. Don't run test suites that touch a real database concurrently or in parallel; a
  half-finished `down()` migration can corrupt the schema.
- Drafts stay drafts. Content gets staged unpublished; publishing is a separate, explicit
  action.

## Long-running and background jobs

- If a background job shows no output, check CPU and progress early (`ps -eo etime,pcpu,args`,
  output file counts). Don't just wait for the notification.
  *Why:* a script runner that silently opened an interactive REPL sat at 0% CPU for 15 minutes.
- Time a big job on a small slice first (e.g. `N=50`).
- Interactive tools in containers often wait on stdin. Pass `< /dev/null`, or use their
  non-interactive "execute" flag.

## Checking rendered output

- When a viewer or proxy shows something missing (an email button, an embedded asset), check the
  raw source, or render it locally, before calling it a bug. Some viewers strip markup.
- `redeploy`-style commands may reuse an old environment snapshot. To pick up changed env vars,
  trigger a fresh build.

## Tool versions

- Global CLIs installed through a version manager (nvm, pyenv…) disappear on each version bump.
  When a CLI goes missing after an upgrade, that's why. Ask before reinstalling.
