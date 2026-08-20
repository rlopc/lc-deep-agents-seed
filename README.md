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
uv tool install pre-commit
pre-commit install
```

## Layout

- `src/lc_deep_agents_seed/agent.py` — the agent factory; start here.
- `src/lc_deep_agents_seed/cli.py` — the `greet` command.
- `langgraph.json` — manifest read by `langgraph dev` and by deployments.
- `tests/` — smoke tests; they never reach the network.
