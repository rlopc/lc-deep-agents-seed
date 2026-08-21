# lc-deep-agents-seed

A production-shaped starting point for LangChain deep agents, not a disposable exercise.
Treat scaffolding decisions here as if a real project would inherit them.

## Commands

- `uv run ruff check .` / `uv run ruff format .` — lint / format
- `uv run mypy` — type check (strict)
- `uv run pytest` — tests
- `uv run --env-file .env greet "..."` — run the CLI
- `uv run --env-file .env langgraph dev` — local server + Studio

## Conventions

- No upper version bounds on dependencies (`uv add pkg`, never `pkg<X`) unless a specific
  incompatibility is known. Dependabot needs a lower bound to open PRs; upper bounds mostly
  cause unsolvable environments without preventing real breakage.
- `create_deep_agent` is called from a factory (`agent.py:make_agent`), never a module-level
  graph — importing a module should not build anything. Building the agent does *not* need
  credentials; `cli.py` is the boundary that checks for them.
- Anything depended on directly is declared directly in `[project.dependencies]`, even when a
  dependency already pulls it in transitively. "Directly" is not limited to `import` statements:
  a provider named in a model string (`"anthropic:..."`, resolved by `init_chat_model`) is just
  as hard a dependency, and leaves no import to notice it by.
- GitHub Actions are pinned by full commit SHA with a trailing `# vX.Y.Z` comment, because a
  tag can be moved to another commit; third-party pre-commit hooks stay on exact tags, since
  they run locally. Verify a ref exists (`git ls-remote --tags`) before pinning to it — and
  dereference annotated tags with `^{}`, or you will pin the tag object instead of the commit.
- ruff is a `repo: local` pre-commit hook running `uv run ruff`, so `uv.lock` is the only place
  its version is pinned — never reintroduce `ruff-pre-commit` with a `rev`, which would pin it
  a second time with nothing to keep the two in step.

## Workflow

- All changes land through a pull request; `main` is protected (PR + passing CI required,
  no force-push). Direct pushes to `main` are rejected.
