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
  `uv.lock`, not from the range in `pyproject.toml`. **This applies to `requires-python` too**,
  which is why it reads `>=3.13` and not `>=3.13,<4.0`: the same source is blunt about it —
  *"Never provide an upper cap to your Python version"* — because a user cannot downgrade their
  interpreter to satisfy a cap, so the cap turns a hypothetical incompatibility into a certain
  install failure.
- **Every package imported directly is declared directly.** `agent.py` imports `langchain_core`
  and `langgraph`, so both are in `[project.dependencies]` even though `deepagents` already
  pulls them in. Relying on a transitive dependency means a change in someone else's dependency
  list breaks the import, and the lockfile gives no warning because nothing was ever declared.
- **Python 3.13, not 3.14.** 3.14 would give more support runway and `langchain` 1.3.15 does
  declare it, but it closes the deployment path: `langgraph build` composes the base image tag
  `langchain/langgraph-api:<python_version>`, and on Docker Hub `:3.11`, `:3.12` and `:3.13`
  resolve while `:3.14` returns 404. Images for `py3.14` exist only as pre-releases
  (`0.13.0rc4-py3.14`, `0.14.0.dev9-py3.14`), whereas `py3.13` has stable ones
  (`0.12.6-py3.13`). The ceiling is the published image, not the CLI — `langgraph_cli/config.py`
  only enforces `MIN_PYTHON_VERSION = "3.11"`. This is a lag, not a permanent limit; check
  whether it still applies with:

  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" \
    https://hub.docker.com/v2/repositories/langchain/langgraph-api/tags/3.14
  ```

  `langgraph.json` pins `"python_version": "3.13"` explicitly, because the CLI otherwise
  defaults to 3.11 and the deployed runtime would silently differ from the local one.
- **The package ships a `py.typed` marker.** It is fully annotated and checked under
  `mypy --strict`, and it is installed as a package (`langgraph.json` declares
  `"dependencies": ["."]`). Without the PEP 561 marker every type checker downstream silently
  ignores those annotations. Hatchling picks the file up automatically.
- **License: MIT.** The repo is meant to be reused as a starting point, not kept private.

## Agent code

- **`create_deep_agent` is called from a factory (`agent.py:make_agent`), never built as a
  module-level graph.** Importing a module should not build anything: a module-level graph
  makes every import pay for graph assembly, and it fixes the agent's shape at import time,
  which is exactly what `langgraph.json` pointing at a factory is meant to avoid.

  Note what this does *not* buy, because an earlier version of this file claimed it did:
  building the agent does **not** require credentials. `langchain-anthropic` defers
  authentication to request time, so `make_agent()` returns a compiled graph with
  `ANTHROPIC_API_KEY` unset. Verify with:

  ```bash
  env -u ANTHROPIC_API_KEY uv run python -c \
    "from lc_deep_agents_seed.agent import make_agent; make_agent()"
  ```

  Credentials are the CLI's problem, and `cli.py` checks for them before invoking — otherwise
  a missing key surfaces as a bare `TypeError` from inside the provider client.
- The factory keeps an optional `RunnableConfig` parameter even though it's unused today, so
  that a config-dependent agent stays a one-line change. This is forward-looking, not required:
  `langgraph_api._factory_utils._classify_factory` accepts factories with zero, one or two
  parameters, and `invoke_factory` calls a zero-parameter factory with no arguments. Dropping
  the parameter would not break `langgraph dev`.
- **CLI entry point is named `greet`**, not the Spanish `hola`: everything published in the
  repository (code, comments, docs, commits) is in English, per house style, even though the
  working conversation is in Spanish.
- **`MODEL` is a fixed constant, with no environment override.** An override was considered and
  rejected: nothing consumes it yet, and a configuration path with no consumer is a guess about
  the future. Add one when a second caller actually needs a different model — and note that
  `cli.py` hardcodes `ANTHROPIC_API_KEY`, which only stays correct while the model is Anthropic.

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
