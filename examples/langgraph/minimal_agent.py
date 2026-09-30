from typing import Annotated, List, TypedDict

from langgraph.graph import END
from langgraph.graph import StateGraph
from pydantic import Field
from langchain_core.messages import BaseMessage,  AIMessage, ToolMessage
from langchain_core.tools import tool

from langgraph.graph.message import add_messages

# Swap operator.add for add_messages to prevent silent key drops
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

@tool
def fetch_data(query: str) -> str:
    """Fetches system data."""
    return f"Data for {query}"

def llm_node(state: AgentState):
    return {"messages": [AIMessage(content="", tool_calls=[{"name": "fetch_data", "args": {"query": "system"}, "id": "1"}])]}

def tool_node(state: AgentState):
    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]
    
    try:
        result = fetch_data.invoke(tool_call["args"])
        return {"messages": [ToolMessage(content=str(result), tool_call_id=tool_call["id"])]}
    except Exception as e:
        return {"messages": [ToolMessage(content=f"Error: {str(e)}. Try again or use a fallback.", tool_call_id=tool_call["id"])]}

def router(state: AgentState):
    last_message = state["messages"][-1]
    if isinstance(last_message, ToolMessage) and "Error" in last_message.content:
        if len(state["messages"]) > 5:
            return END
        return "llm"
    if isinstance(last_message, ToolMessage):
        return END
    return "tools"

workflow = StateGraph(AgentState)
workflow.add_node("llm", llm_node)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("llm")
workflow.add_conditional_edges("llm", router, {"tools": "tools", END: END})
workflow.add_conditional_edges("tools", router, {"llm": "llm", END: END})