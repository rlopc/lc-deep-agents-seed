"""Command line entry point."""

import os
import sys

from lc_deep_agents_seed.agent import make_agent

# The factory is deliberately credential-free, so the CLI is the boundary that checks.
# Without this, a missing key surfaces as a bare TypeError from the provider client.
REQUIRED_ENV = "ANTHROPIC_API_KEY"


def main() -> None:
    if not os.environ.get(REQUIRED_ENV):
        print(
            f"{REQUIRED_ENV} is not set. Copy .env.example to .env and fill it in.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    prompt = " ".join(sys.argv[1:]) or "Hello, who are you?"
    result = make_agent().invoke({"messages": [{"role": "user", "content": prompt}]})
    # Anthropic answers with a list of content blocks; .content would print its repr.
    print(result["messages"][-1].text)
