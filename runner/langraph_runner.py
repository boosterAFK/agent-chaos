import copy

from agent_runner import AgentRunner

from logging import warning
from typing import Dict, List, List, Optional
from typing import Any

from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from runner.fault_injector import FaultInjector

class LangGraphRunner(AgentRunner):
    uncompiled_graph: Optional[StateGraph]
    checkpointer: Optional[BaseCheckpointSaver]

    def __init__(self, uncompiled_graph, tools: Optional[List[BaseTool]] = None, fault_injector: Optional[FaultInjector] = None, checkpointer: Optional[BaseCheckpointSaver] = None):
        self._tools: list[BaseTool] = tools or []
        super().__init__(tools, fault_injector)
        
        self.uncompiled_graph = uncompiled_graph
        self.checkpointer = checkpointer or InMemorySaver()
        self.app: Optional[CompiledStateGraph] = None

    def _bind_and_poison_tools(self) -> None:
        poisoned_tools = []
        
        for tool in self._tools:
            if tool.name not in self._fault_injector.get_faults():
                poisoned_tools.append(tool)
                continue
                
            # Clone to protect the baseline environment during A/B benchmarks
            tool_clone = copy.copy(tool)
            tool_clone.func = self._fault_injector.intercept(tool.name, tool.func)
            
            if hasattr(tool, "coroutine") and tool.coroutine:
                tool_clone.coroutine = self._async_wrap(
                    self._fault_injector.intercept(tool.name, tool.coroutine)
                )
                
            poisoned_tools.append(tool_clone)
            
        self._tools = poisoned_tools

    def _async_wrap(self, sync_wrapper):
        async def wrapper(*args, **kwargs):
            return sync_wrapper(*args, **kwargs)
        return wrapper

    def _compile(self) -> CompiledStateGraph:
        self._app = self._uncompiled_graph.compile(checkpointer=self._checkpointer)
        return self._app

    def _invoke(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        return self.app.invoke(input_data, config=config)

    def _get_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state_snapshot = self.app.get_state(config)
        return state_snapshot.values

    def _update_state(self, config: Dict[str, Any], new_state: Dict[str, Any], as_node: Optional[str] = None) -> None:
        self.app.update_state(config, new_state, as_node=as_node)