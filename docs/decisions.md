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
- **Every package depended on directly is declared directly — including the ones with no
  import.** `agent.py` imports `langchain_core` and `langgraph`, so both are in
  `[project.dependencies]` even though `deepagents` already pulls them in. Relying on a
  transitive dependency means a change in someone else's dependency list breaks the import, and
  the lockfile gives no warning because nothing was ever declared. This rule was first written
  as "every package *imported* directly", and `langchain-anthropic` slipped through it for
  exactly that reason: nothing imports it. `agent.py` sets `MODEL = "anthropic:claude-opus-5"`,
  and `init_chat_model` resolves that prefix to `langchain_anthropic.chat_models.ChatAnthropic`
  at runtime, so the package is as load-bearing as any import while leaving no static trace to
  notice it by — which makes declaring it more important, not less. When adding a dependency,
  ask what breaks if it disappears, not what the import block says.
- **`pre-commit` is a dev dependency, not a `uv tool install`.** Either is normal practice, but
  the ruff hooks are `repo: local` and shell out to `uv run ruff`, so the hooks already require
  a synced `.venv`. Given that, installing pre-commit itself separately adds a second bootstrap
  step for no isolation that was not already given up: `uv sync` now brings the whole toolchain,
  and `uv run pre-commit install` is the only setup command.
- **No `authors` in `[project]`.** `uv init` writes one, and it was removed on purpose. This is
  a template meant to be copied, and `authors` would travel into the wheel metadata of every
  project that inherits it, crediting someone who never touched their code. A project that
  forks this should add its own.
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

- **Pin GitHub Actions by full commit SHA; pin pre-commit hooks to exact tags.** A git tag is a
  movable label: whoever controls the repository can repoint it at another commit, and nothing
  in this repository would change. Actions run inside CI with access to the checkout and the
  `GITHUB_TOKEN`, which is why GitHub documents a full-length SHA as "the only way to use an
  action as an immutable release" — and why the `tj-actions/changed-files` compromise of March
  2025 worked by moving a tag. The usual objection is the maintenance burden of hand-updating
  hashes; it does not apply here, because Dependabot already covers `github-actions` and
  rewrites the trailing `# v7.0.1` comment on every bump. Third-party pre-commit hooks stay on
  tags: they run locally, not with repository credentials. The ruff hooks are not pinned here at
  all — see "ruff runs from the project environment" below.

  Two traps when resolving a version to a SHA:

  - Verify the ref exists rather than trusting a release page. `astral-sh/setup-uv@v10` does
    not exist — only `v10.0.0` and `v10.0.1` are published — and the initial CI run failed on
    exactly that.
  - `git ls-remote --tags <url>` prints the *tag object* for annotated tags, not the commit.
    Dereference with `git ls-remote <url> 'refs/tags/v1.2.3^{}'` and use that SHA; if the
    dereferenced ref is absent the tag is lightweight and the first SHA is already the commit.
- **Repository is public.** Two reasons: it's meant to be a reusable template, and GitHub's
  secret scanning push protection is free on public repos but part of a paid tier on private
  ones.
- **`main` is protected via a ruleset**: PR required, the CI status check required, branches
  must be up to date before merging, force-push and deletion blocked. Required approvals are
  set to 0 — this is a single-maintainer repo; raise it to 1+ if collaborators join.
- **`line-length` is declared in two places on purpose.** `pyproject.toml` sets ruff's 88
  explicitly — it is ruff's own default, so the line is redundant for the tool — and
  `.editorconfig` mirrors it as `max_line_length` under `[*.py]`, so the editor draws the
  guide that CI enforces. **Change both together.** The limit is set for Python only: no tool
  checks line length in Markdown or YAML, and Markdown here holds URLs and tables well past
  400 characters that should not be flagged.
- **`trailing-whitespace` runs with `--markdown-linebreak-ext=md`.** Markdown encodes a hard
  line break as two trailing spaces, which is why `.editorconfig` sets
  `trim_trailing_whitespace = false` for `*.md`. The hook does not read `.editorconfig`, so
  without this argument the two configurations contradicted each other and the hook silently
  won, stripping intentional line breaks on every commit. Every other file type is still
  trimmed.
- **Two independent Dependabot mechanisms, not duplicates:** `dependabot.yml` handles routine
  weekly version updates (grouped into one PR for minor/patch bumps); the repo-level
  "Dependabot security updates" setting opens an immediate PR the moment a known vulnerability
  is published, independent of the weekly cycle. Both are enabled, along with "Grouped
  security updates" for the same reason `dependabot.yml` groups routine bumps. Routine updates
  also sit in a three-day `cooldown`, because yanked releases and same-week regressions are
  common; security updates ignore cooldown by design. Note that only `default-days` is
  supported for the `uv` and `github-actions` ecosystems — the `semver-*-days` keys are not.
- **CI declares `permissions: contents: read`, a `concurrency` group and `timeout-minutes`.**
  The workflow only reads the repository, so it should not inherit whatever the repository
  default happens to be; a superseded push to a pull request should stop consuming runner
  minutes; and the job cap is set because GitHub's default is 360 minutes, which a single hung
  step would burn in full. The `concurrency` group is keyed on `github.workflow` rather than a
  hardcoded string, so a second workflow copied from this one cannot land in the same group and
  cancel unrelated runs.
- **`setup-uv` keeps its `auto` cache default; `enable-cache: true` was removed.** The
  documented behaviour of `auto` is "enabled on GitHub-hosted runners except for release, tag
  push, `pull_request_target`, and `workflow_run` events; disabled on self-hosted runners" —
  those exclusions exist because such events run with a write-capable token, so a cache poisoned
  from a fork would be restored into a privileged job. On the triggers this workflow actually
  declares (`push` to `main`, `pull_request`) `auto` and `true` behave identically, so forcing
  it bought nothing while removing the guard for whatever trigger a downstream project adds
  later. Left explained rather than merely deleted, so it is not "helpfully" reinstated.
- **No secrets are configured for CI.** The suite must pass with no API key and no network
  access; `tests/test_agent.py` stubs the compiled graph to keep it that way, and `make_agent`
  is deliberately buildable without credentials (see "Agent code"). A step that starts requiring
  a credential is not a configuration gap to fill in — it is the regression to investigate.
- **CI does not run the pre-commit hooks.** It was considered and rejected: the `ruff-check`
  hook carries `args: [--fix]`, so in CI it would rewrite files and fail with "files were
  modified by this hook" instead of a readable lint error. What matters is already covered —
  `uv sync --locked` does the job of the `uv-lock` hook, and `ruff format --check` covers
  formatting. The residual gap is trailing whitespace in YAML and Markdown for contributors who
  never ran `pre-commit install`; that is accepted rather than paid for with a second job.
- **The committed Claude Code allowlist is read-only, and there is no formatting hook.**
  `.claude/settings.json` is checked in (`.gitignore` excludes only `settings.local.json`, so
  personal overrides stay local) and pre-approves inspection commands only: `git` status, diff,
  log, show and ls-remote; `uv tree`; `uv run` for pytest, ruff, mypy and pre-commit; and
  `gh pr` view, list and checks.
  Commands that write are deliberately absent, `uv sync` and `uv lock` included: an allowlist
  entry removes the confirmation step, so it should only cover actions with no effect to undo.
  A `PostToolUse` hook running `ruff --fix` on every edited file was considered and rejected:
  such a hook only fires on the agent's own writes, whereas the `ruff-check` and `ruff-format`
  pre-commit hooks already cover every file from every author; and the usual shell wrapper ends
  in `2>/dev/null || true`, which hides a broken environment or a real ruff failure instead of
  reporting it.
- **`.vscode/settings.json` and `.vscode/extensions.json` are committed, and `.gitignore` has
  to fight for it.** A global ignore rule (`~/.config/git/ignore` or the equivalent) commonly
  excludes `.vscode/`, and Git does not descend into an excluded directory, so re-including one
  file is not enough — the repository's `.gitignore` re-includes the directory, re-excludes its
  contents, then lists the two shared files by name. The settings themselves are not personal
  taste: `ruff.importStrategy: "fromEnvironment"` makes the editor use the ruff in `.venv`
  rather than the one bundled with the extension, which updates independently and would then
  disagree with pre-commit and CI; `editor.codeActionsOnSave` runs lint fixes before formatting,
  the same order as `.pre-commit-config.yaml`, because a fix can leave the file unformatted.
  `extensions.json` exists because `settings.json` names `charliermarsh.ruff` as the Python
  formatter, and with the extension missing, format-on-save does nothing and says nothing.
  This complements `.editorconfig` rather than repeating it: that file covers charset, line
  endings, indentation and the 88-column guide; these cover which binaries the editor runs.
- **ruff runs from the project environment (`repo: local`), not from a pinned `rev`.** The
  conventional setup is `astral-sh/ruff-pre-commit` with `rev: vX.Y.Z`, which builds an isolated
  environment. That pins ruff a second time, independently of `uv.lock` — and the two pins have
  no shared bump mechanism, because `dependabot.yml` covers `uv` and `github-actions` while
  Dependabot supports no pre-commit ecosystem at all; only a manual `pre-commit autoupdate`
  moves the `rev`. The failure it invites is concrete: Dependabot raises ruff in `uv.lock`, CI
  and the editor pick the new version up, the hook keeps running the old one, and a commit that
  passes locally fails CI on a rule the hook never applied. Running `uv run ruff` from the
  project environment leaves one source of truth for all three. The price is that these hooks
  need a synced `.venv` and fail without one — accepted, because failing loudly beats silently
  running a different ruff. This is why `.vscode/settings.json` can claim the editor agrees with
  both pre-commit and CI: after this change it genuinely does.
- **`check-yaml` and `check-toml` run locally.** CI deliberately does not run the pre-commit
  hooks, so a malformed `ci.yml` would otherwise surface as a confusing workflow failure one
  push later, and a malformed `pyproject.toml` as a broken `uv sync`. Both hooks are cheap.
  `detect-private-key` sits alongside them but is narrower than it sounds: it matches PEM, SSH
  and PGP key headers, not a pasted `sk-ant-...` API key. Nothing in this repository scans for
  those — `.env` being gitignored is the actual protection, and gitleaks is the tool to add if
  that is not enough.
