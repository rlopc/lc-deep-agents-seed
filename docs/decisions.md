# Decisions

Architectural and tooling decisions for this repository, with the reasoning behind them.
This is a template project meant to grow into production, so decisions here are made as
if a real project depended on them — not as shortcuts for a learning exercise.

Update this file whenever a decision is made or revised; do not let it go stale. Tools
(including project skills) should derive context from this file rather than hardcode it.

## Packaging

- **Build backend: hatchling, not `uv_build`.** `uv_build` is uv's own default since mid-2025
  and is faster, but it only supports pure-Python projects with no build hooks. Astral's own
  docs point to hatchling once you need dynamic (VCS-derived) versioning, non-code data files,
  or custom build hooks — exactly the things a project tends to need once it moves toward
  production. Switching later is a two-line change, so this is a low-cost, forward-looking
  choice, not a strong opinion.
- **`src/` layout, installable package.** Required for `langgraph.json`'s
  `"dependencies": ["."]` to work — LangGraph installs the project as a package rather than
  importing loose files.
- **No upper version bounds on dependencies** (`uv add pkg`, not `pkg<X`), unless a specific
  known incompatibility exists. Community consensus (Henry Schreiner and others) is that
  upper bounds mostly cause unsolvable dependency trees without preventing real breakage —
  and Dependabot needs a lower bound to open update PRs at all, so an unconstrained add still
  gets that coverage. `uv add` writes a lower bound automatically; reproducibility comes from
  `uv.lock`, not from the range in `pyproject.toml`.
- **Python 3.14.** Declared supported by `langchain` 1.3.15; picked for maximum support
  runway over 3.12/3.13.
- **License: MIT.** The repo is meant to be reused as a starting point, not kept private.

## Agent code

- **`create_deep_agent` is called from a factory (`agent.py:make_agent`), never built as a
  module-level graph.** Building the agent instantiates the model client, which needs
  `ANTHROPIC_API_KEY`. A factory defers that until the agent is actually invoked, so
  importing the module — and therefore collecting tests — never requires credentials.
- The factory takes an optional `RunnableConfig` parameter even though it's unused today:
  `langgraph.json` can point at a graph-building function instead of a compiled graph, and
  when it does, LangGraph calls it with a config argument. Dropping the parameter breaks
  `langgraph dev`.
- **CLI entry point is named `greet`**, not the Spanish `hola`: everything published in the
  repository (code, comments, docs, commits) is in English, per house style, even though the
  working conversation is in Spanish.

## CI / CD and tooling

- **Pin GitHub Actions and pre-commit hooks to exact tags, not floating majors.** Some
  repositories publish floating major tags (`actions/checkout@v7` is valid); others don't
  (`astral-sh/setup-uv@v10` does not exist — only `v10.0.0` and `v10.0.1` are published tags).
  The initial CI run failed on exactly this. Before pinning a version found via a package
  registry or release page, verify the tag actually exists as a ref
  (`git ls-remote --tags <repo-url>`) rather than assuming the latest release number is a
  valid tag.
- **Repository is public.** Two reasons: it's meant to be a reusable template, and GitHub's
  secret scanning push protection is free on public repos but part of a paid tier on private
  ones.
- **`main` is protected via a ruleset**: PR required, the CI status check required, branches
  must be up to date before merging, force-push and deletion blocked. Required approvals are
  set to 0 — this is a single-maintainer repo; raise it to 1+ if collaborators join.
- **Two independent Dependabot mechanisms, not duplicates:** `dependabot.yml` handles routine
  weekly version updates (grouped into one PR for minor/patch bumps); the repo-level
  "Dependabot security updates" setting opens an immediate PR the moment a known vulnerability
  is published, independent of the weekly cycle. Both are enabled, along with "Grouped
  security updates" for the same reason `dependabot.yml` groups routine bumps.
