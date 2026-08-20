"""Smoke tests that never reach the network."""

import pytest

from lc_deep_agents_seed.agent import make_agent


@pytest.fixture(autouse=True)
def _fake_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")


def test_agent_builds() -> None:
    agent = make_agent()
    # A compiled LangGraph exposes the standard runnable entry points.
    assert hasattr(agent, "invoke")
