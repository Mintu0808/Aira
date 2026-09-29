from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph

from .database import pool
from .nodes import chatbot_node, memory_extractor_node
from .state import AgentConfiguredState


def create_agent_graph():
    builder = StateGraph(AgentConfiguredState)
    builder.add_node("chatbot", chatbot_node)
    builder.add_node("extractor", memory_extractor_node)
    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", "extractor")
    builder.add_edge("extractor", END)

    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    return builder.compile(checkpointer=checkpointer)