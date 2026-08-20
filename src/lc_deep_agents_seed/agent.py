"""Agent factory for the seed project."""

from typing import Any

from deepagents import create_deep_agent
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph

MODEL = "anthropic:claude-opus-5"

SYSTEM_PROMPT = """You are a concise assistant. Greet the user by name
when they give one, and explain in one sentence what a deep agent is."""

# The compiled graph is generic in four parameters; this seed narrows none of them.
type DeepAgentGraph = CompiledStateGraph[Any, Any, Any, Any]


# A factory, not a module-level graph: building the agent instantiates the model client,
# which needs credentials. Deferring it keeps imports — and therefore tests — key-free.
def make_agent(config: RunnableConfig | None = None) -> DeepAgentGraph:
    return create_deep_agent(
        model=MODEL,
        tools=[],
        system_prompt=SYSTEM_PROMPT,
    )
