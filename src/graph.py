"""LangGraph agent definition: a ReAct-style agent with tool access and memory."""
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from .config import get_llm
from .tools import ALL_TOOLS
from .prompts import get_system_prompt

# In-memory checkpointer so the agent remembers earlier turns in the session.
_checkpointer = MemorySaver()


def build_agent(provider: str, api_key: str = None):
    """Construct a LangGraph ReAct agent bound to the chosen LLM provider."""
    llm = get_llm(provider, api_key)
    agent = create_react_agent(
        model=llm,
        tools=ALL_TOOLS,
        prompt=get_system_prompt(),
        checkpointer=_checkpointer,
    )
    return agent


def run_agent(agent, user_message: str, thread_id: str = "default") -> str:
    """Send a user message to the agent and return its final text reply."""
    config = {"configurable": {"thread_id": thread_id}}
    result = agent.invoke({"messages": [{"role": "user", "content": user_message}]}, config=config)
    return result["messages"][-1].content