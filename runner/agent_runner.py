from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from typing import Any

from runner.fault_injector import FaultInjector

class AgentRunner(ABC):
    """
    Standardizes execution and state mutation for agentic risk evaluation.
    This interface ensures the testing harness can arbitrarily pause, inspect, 
    and mutate state regardless of the specific agent implementation.
    """
    _is_compiled: bool

    _fault_injector: Optional[FaultInjector]
    _tools:  Optional[List[Any]] = None

    app: Optional[Any]

    def __init__(self, tools: Optional[List[Any]] = None, fault_injector: Optional[FaultInjector] = None):
        self._is_compiled = False
        self.app = None
        self._fault_injector = fault_injector
        self._tools = tools or []

    def compile(self) -> Any:
        if self._fault_injector:
            self._bind_and_poison_tools()
        
        app = self._compile()
        self._is_compiled = True
        self.app = app
        return app

    def invoke(self, input_data: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        """Validates compilation and delegates execution."""
        if not self._is_compiled:
            self.compile()
        return self._invoke(input_data, self._get_config(thread_id))

    def get_state(self, thread_id: str) -> Dict[str, Any]:
        """Validates compilation and delegates state retrieval."""
        self._ensure_compiled()
        return self._get_state(self._get_config(thread_id))

    def update_state(self, thread_id: str, new_state: Dict[str, Any], as_node: Optional[str] = None) -> None:
        """Validates compilation and delegates state mutation."""
        self._ensure_compiled()
        self._update_state(self._get_config(thread_id), new_state, as_node)

    def _ensure_compiled(self) -> None:
        if not self._is_compiled:
            raise RuntimeError("The agent graph must be compiled before accessing or mutating state.")

    def _get_config(self, thread_id: str) -> Dict[str, Any]:
        return {"configurable": {"thread_id": thread_id}}

    @abstractmethod
    def _compile(self) -> Any:
        pass

    @abstractmethod
    def _invoke(self, input_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _get_state(self, config: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _update_state(self, config: Dict[str, Any], new_state: Dict[str, Any], as_node: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def _bind_and_poison_tools(self) -> None:
        """
        Concrete subclasses must implement this to iterate over their specific 
        framework's tools and wrap them using self.fault_injector.intercept()
        """
        pass
