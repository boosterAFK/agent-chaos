from __future__ import annotations

from typing import  Any, Callable, Optional, Protocol

from injector.base import Fault


class FaultDispatcher(Protocol):
    """
    Minimal contract the ChaosToolProxy needs from the orchestrator: given
    an observed tool call, return the fault to apply or None.
    """

    def dispatch(self, tool_name: str) -> Optional[Fault]:
        ...


class ChaosToolProxy:
    def __init__(self, tool_name: str, original_callable: Callable[..., Any], dispatcher: FaultDispatcher) -> None:
        self.tool_name = tool_name
        self.original_callable = original_callable
        self.dispatcher = dispatcher

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        fault = self.dispatcher.dispatch(self.tool_name)
        if fault is not None:
            return fault.apply(self.tool_name, self.original_callable, *args, **kwargs)
        return self.original_callable(*args, **kwargs)

    def __repr__(self) -> str:
        return f"ChaosToolProxy(tool_name={self.tool_name!r}, original={self.original_callable!r})"
