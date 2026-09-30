from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, List

class Fault(ABC):
    @abstractmethod
    def apply(self, tool_name: str, original_callable: Callable, *args, **kwargs) -> Any:
        pass

class FaultInjector(ABC):

    def __init__(self):
        self._fault_registry: dict[str, Fault] = {}

    def register_fault(self, target_tool: str, fault: Fault) -> None:
        self._fault_registry[target_tool] = fault

    def unregister_fault(self, target_tool: str) -> None:
        if target_tool in self._fault_registry:
            del self._fault_registry[target_tool]

    def clear_faults(self) -> None:
        self._fault_registry.clear()

    def get_faults(self) -> dict[str, Fault]:
        return self._fault_registry

    def intercept(self, tool_name: str, original_callable: Callable) -> Callable:
        """Returns a wrapped function if a fault is registered, else the original."""
        fault = self._fault_registry.get(tool_name)
        if not fault:
            return original_callable

        def wrapper(*args, **kwargs):
            return fault.apply(tool_name, original_callable, *args, **kwargs)
            
        return wrapper