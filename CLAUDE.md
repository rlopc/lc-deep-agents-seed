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
  graph — building it instantiates the model client, which needs credentials. This keeps
  imports, and therefore tests, key-free.
- GitHub Actions and pre-commit hook versions are pinned to exact tags, not floating majors —
  some repos (e.g. `astral-sh/setup-uv`) don't publish floating major tags. Verify a tag
  exists (`git ls-remote --tags`) before pinning to it, don't assume the release page's
  latest-version number is a valid ref.

## Workflow

- All changes land through a pull request; `main` is protected (PR + passing CI required,
  no force-push). Direct pushes to `main` are rejected.
