"""Command line entry point."""

import sys

from lc_deep_agents_seed.agent import make_agent


def main() -> None:
    prompt = " ".join(sys.argv[1:]) or "Hello, who are you?"
    result = make_agent().invoke({"messages": [{"role": "user", "content": prompt}]})
    print(result["messages"][-1].content)
