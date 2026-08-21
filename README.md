# lc-deep-agents-seed

A production-shaped starting point for LangChain deep agents.

A "hello world" agent built with [deepagents](https://docs.langchain.com/oss/python/deepagents/overview),
wired the way a real project would be: locked dependencies, linting, type checking, tests
and CI.

## Requirements

- [uv](https://docs.astral.sh/uv/). It installs Python 3.13 on its own; nothing else is needed.
- An Anthropic API key.

## Setup

```bash
uv sync
cp .env.example .env   # then fill in ANTHROPIC_API_KEY
```

Run everything through `uv run`. A bare `python` or `pytest` may pick up a different
interpreter and report results that have nothing to do with this project.

## Running

Two entry points, one agent.

From the command line:

```bash
uv run --env-file .env greet "Hello, who are you?"
```

From the LangGraph development server, which also opens LangGraph Studio so you can
inspect every step the agent takes:

```bash
uv run --env-file .env langgraph dev
```

## Development

```bash
uv run ruff check .     # lint
uv run ruff format .    # format
uv run mypy             # types
uv run pytest           # tests
```

Install the git hooks once, and those same checks run before every commit:

```bash
uv run pre-commit install
```

## Layout

- `src/lc_deep_agents_seed/agent.py` — the agent factory; start here.
- `src/lc_deep_agents_seed/cli.py` — the `greet` command.
- `langgraph.json` — manifest read by `langgraph dev` and by deployments.
- `tests/` — smoke tests; they never reach the network.

## Known limits

The scaffolding around the agent is production-shaped. The agent itself is not, and these
gaps are deliberate — a starting point should not pretend to be finished.

1. **No persistence.** `langgraph.json` declares no checkpointer, so conversation state
   lives in the process and dies with it. Add one before anything needs to remember.
2. **No authentication and no store.** Both are unset in the manifest. `langgraph dev` is
   a development server; do not put it in front of anything.
3. **No tools.** `make_agent` passes `tools=[]`. A deep agent with no tools can only talk,
   which is enough to prove the wiring and nothing else.
4. **No observability.** LangSmith arrives as a transitive dependency and stays off unless
   `LANGSMITH_TRACING` is set, and nothing replaces it. A failing agent leaves no trace.
5. **The deployment path is unverified.** The manifest validates and the graph factory
   resolves, but no image has been built or deployed from this repository yet.
