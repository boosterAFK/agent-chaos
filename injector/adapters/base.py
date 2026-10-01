# injector/adapters/base.py
from abc import ABC, abstractmethod
from typing import Callable, Any



class ToolAdapter(ABC):
    @abstractmethod
    def get_name(self, tool: v) -> str: ...
    @abstractmethod
    def get_callable(self, tool: Any) -> Callable: ...          # the func to wrap
    @abstractmethod
    def clone_with_callable(self, tool: Any, fn: Callable) -> Any: ...  # poisoned clone
