import copy

from runner.base import AgentRunner

from logging import warning
from typing import Dict, List, List, Optional
from typing import Any

from langchain_core.tools import BaseTool
from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph, StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver

from injector.base import FaultInjector

class LangGraphRunner(AgentRunner):
    _uncompiled_graph: Optional[StateGraph]
    _checkpointer: Optional[BaseCheckpointSaver]
    _tools: Optional[List[BaseTool]] 
    _fault_injector: Optional[FaultInjector] 

    def __init__(self, uncompiled_graph, tools: Optional[List[BaseTool]] = None, fault_injector: Optional[FaultInjector] = None, checkpointer: Optional[BaseCheckpointSaver] = None):
        super().__init__(tools, fault_injector)
        
        self._uncompiled_graph = uncompiled_graph
        self._checkpointer = checkpointer or InMemorySaver()
        self.app: Optional[CompiledStateGraph] = None

    def _bind_and_poison_tools(self) -> None:
        """
        Mutates the tool instance in-place. 
        Overrides the invoke method to guarantee the FaultInjector intercepts 
        the call when the LangGraph node triggers execution.
        """
        if not self._fault_injector:
            return

        faults = self._fault_injector.get_faults()
        for tool in self._tools:
            if tool.name not in faults:
                continue

            original_func = tool.func
            poisoned_func = self._fault_injector.intercept(tool.name, original_func)
            
            # Mutate the function reference
            tool.func = poisoned_func


    def _async_wrap(self, sync_wrapper):
        async def wrapper(*args, **kwargs):
            return sync_wrapper(*args, **kwargs)
        return wrapper

    def _compile(self) -> CompiledStateGraph:
        self._app = self._uncompiled_graph.compile(checkpointer=self._checkpointer)
        return self._app

    def _invoke(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.app.invoke(input_data, config=config)
        except GraphRecursionError:
            # The checkpoint already holds the steps taken before the limit.
            # Return that state so trajectory metrics can still be scored.
            warning(
                "Recursion limit reached for thread '%s' (limit=%s). Returning the last checkpointed state.",
                config.get("configurable", {}).get("thread_id"),
                config.get("recursion_limit"),
            )
            return self._get_state(config)

    def _get_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state_snapshot = self.app.get_state(config)
        return state_snapshot.values

    def _update_state(self, config: Dict[str, Any], new_state: Dict[str, Any], as_node: Optional[str] = None) -> None:
        self.app.update_state(config, new_state, as_node=as_node)