from logging import warning
from typing import Any, Dict, Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph, StateGraph

from runner.base import AgentRunner

class LangGraphRunner(AgentRunner):
    def __init__(
        self,
        uncompiled_graph: StateGraph,
        checkpointer: Optional[BaseCheckpointSaver] = None,
    ):
        super().__init__()
        self._uncompiled_graph = uncompiled_graph
        self._checkpointer = checkpointer or InMemorySaver()
        self.app: Optional[CompiledStateGraph] = None

    def _compile(self) -> CompiledStateGraph:
        return self._uncompiled_graph.compile(checkpointer=self._checkpointer)

    def _get_config(self, thread_id: str, recursion_limit: Optional[int] = None) -> Dict[str, Any]:
        config: Dict[str, Any] = {"configurable": {"thread_id": thread_id}}
        if recursion_limit is not None:
            config["recursion_limit"] = recursion_limit
        return config

    def _invoke(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return self.app.invoke(input_data, config=config)
        except GraphRecursionError:
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
