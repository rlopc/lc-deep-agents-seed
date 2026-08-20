"""Smoke tests that never reach the network."""

import sys
from typing import Any

import pytest
from langchain_core.messages import AIMessage

from lc_deep_agents_seed import cli
from lc_deep_agents_seed.agent import make_agent


class _StubAgent:
    """Stands in for a compiled graph, so no request is ever made."""

    def __init__(self, message: AIMessage) -> None:
        self._message = message

    def invoke(self, _input: dict[str, Any]) -> dict[str, Any]:
        return {"messages": [self._message]}


def test_agent_builds_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # A compiled LangGraph exposes the standard runnable entry points.
    assert hasattr(make_agent(), "invoke")


def test_cli_prints_text_of_block_content(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(sys, "argv", ["greet", "hi"])
    # Block content is what Anthropic actually returns, and what .content would mangle.
    message = AIMessage(
        content=[
            {"type": "text", "text": "hola"},
            {"type": "text", "text": " mundo"},
        ]
    )
    # Patched where it is used, not where it is defined.
    monkeypatch.setattr(cli, "make_agent", lambda: _StubAgent(message))
    cli.main()
    assert capsys.readouterr().out.strip() == "hola mundo"


def test_cli_exits_without_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 1
