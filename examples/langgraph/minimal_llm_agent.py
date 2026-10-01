import os
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

@tool
def fetch_data(query: str) -> str:
    """Fetches system data."""
    return f"Data for {query}"

@tool(extras={"terminal": True})
def report_unavailable(reason: str) -> str:
    """Use this when fetch_data fails and cannot be retried."""
    return f"Unavailable: {reason}"

TOOLS_REGISTRY = {t.name: t for t in [fetch_data, report_unavailable]}

load_dotenv()

llm = ChatOpenAI(model="gpt-5.2", temperature=0)
llm_with_tools = llm.bind_tools(list(TOOLS_REGISTRY.values()))

def llm_node(state: AgentState):

    messages = state["messages"]
    
    response = llm_with_tools.invoke(messages)
    
    return {"messages": [response]}

def tool_node(state: AgentState):    
    responses = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_instance = TOOLS_REGISTRY.get(tool_call["name"])

        if not tool_instance:
            responses.append(ToolMessage(
                content=f"Error: Tool {tool_call['name']} not found.",
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
                status="error"
            ))
            continue

        try:
            result = tool_instance.invoke(tool_call["args"])
            responses.append(ToolMessage(
                content=str(result), 
                tool_call_id=tool_call["id"], 
                name=tool_instance.name, 
                additional_kwargs={"terminal": bool((tool_instance.metadata or {}).get("terminal"))}))
        except Exception as e:
            responses.append(ToolMessage(
                content=f"Error: {e}",
                tool_call_id=tool_call["id"],
                name=tool_instance.name,
                status="error"
            ))
            
    return {"messages": responses}

def router(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "tools"
    return END

workflow = StateGraph(AgentState)
workflow.add_node("llm", llm_node)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("llm")
workflow.add_conditional_edges("llm", router, {"tools": "tools", END: END})
workflow.add_edge("tools", "llm")