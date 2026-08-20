---
name: executed-review
description: Deep code review for this project that verifies by running the code, not by reading a diff. Checks findings against docs/decisions.md, requires a reproducible failure scenario per finding, and mutation-tests suspicious test coverage. Use for a thorough pass beyond the routine /code-review — e.g. before a release, or when reviewing a change to core logic (agent.py, cli.py). More expensive than /code-review; don't run it as the default for every small PR.
---

# Executed review

A review discipline for this repository. Distinct from the built-in `/code-review`: this
audits by *executing* code and tests, and checks findings against this project's own
documented decisions rather than generic best practices alone.

## Before reviewing: derive context, don't assume it

Read these fresh every time — do not rely on memory of a previous run, this project changes:

- `docs/decisions.md` — the project's own architectural decisions and their stated reasons.
  A finding that contradicts a documented decision needs to say so explicitly and explain why
  the decision no longer holds, rather than silently recommending the opposite.
- `pyproject.toml` — current dependencies, Python version, tool configuration.
- Recent `git log` — what actually changed and why, from commit messages.
- The current file tree under `src/` and `tests/` — don't assume yesterday's layout.

## Review discipline

- **Read files whole**, not excerpts. A finding based on a partial read of a file is not
  trustworthy.
- **Verify by running, not by reading.** Execute the relevant tests (`uv run pytest`), run
  the CLI or the agent factory directly, or reproduce the suspected failure with a small
  script — don't assert a defect exists without having triggered it.
- **Every finding needs a reproducible failure scenario**: concrete inputs or state that lead
  to a concrete wrong output or crash. "This could be a problem" is not a finding; "calling
  `make_agent()` before setting `ANTHROPIC_API_KEY` raises X" is.
- **Mutation-test suspicious test coverage.** If a test's ability to catch a real bug is in
  doubt, introduce the bug on purpose (locally, never committed) and confirm the test fails.
  A test that would pass either way is a finding in itself.
- **Re-review dependents after any fix.** If a change touches something with more than one
  caller (e.g. `make_agent`, `MODEL`), check every caller, not just the one that prompted the
  change.
- **Fix only unambiguous defects.** Anything that depends on a judgment call — naming,
  structure, a tradeoff already recorded in `docs/decisions.md` — goes to the user as a
  question or a flagged finding, not a silent edit.

## Boundaries

- Never commit. Report findings and, if asked to fix, leave the fix staged for the user to
  review and commit themselves.
- Never print secrets — not `.env` contents, not API keys, not tokens — even to illustrate a
  finding. Reference that a secret exists and where, never its value.
- This is a deep, model-expensive pass. Prefer `/code-review` for routine changes; reach for
  this skill for core-logic changes or before a release, not by default.

## Output

Report findings ranked by severity, each with: file and location, the concrete failure
scenario that proves it, and — when the finding touches something documented in
`docs/decisions.md` — a note on whether it conflicts with a recorded decision. If the
`ReportFindings` tool is available, use it; otherwise produce the same structure as a
message.
