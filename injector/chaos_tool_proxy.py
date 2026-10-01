from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, Protocol

from telemetry.instrumentation import Instrumentation
from openinference.semconv.trace import SpanAttributes, OpenInferenceSpanKindValues

if TYPE_CHECKING:
    from injector.base import Fault


class FaultDispatcher(Protocol):
    """
    Minimal contract the ChaosToolProxy needs from the orchestrator: given
    an observed tool call, return the fault to apply or None.
    """

    def dispatch(self, tool_name: str) -> Optional[Fault]: ...

    @property
    def instrumentation(self) -> Instrumentation: ...


class ChaosToolProxy:
    def __init__(self, tool_name: str, original_callable: Callable[..., Any], dispatcher: FaultDispatcher) -> None:
        self.tool_name = tool_name
        self.original_callable = original_callable
        self.dispatcher = dispatcher
        self.instrumentation = dispatcher.instrumentation

    def __call__(self, *args, **kwargs):
        span = self.instrumentation.start_span(
            self.tool_name,  # span name
            **{
                SpanAttributes.OPENINFERENCE_SPAN_KIND: OpenInferenceSpanKindValues.TOOL.value,
                SpanAttributes.TOOL_NAME: self.tool_name,
            },
        )
        try:
            fault = self.dispatcher.dispatch(self.tool_name)
            if fault is not None:
                span.set_attributes({"fault.injected": True, "fault.type": type(fault).__name__})
                result = fault.apply(self.tool_name, self.original_callable, *args, **kwargs)
            else:
                span.set_attributes({"fault.injected": False})
                result = self.original_callable(*args, **kwargs)
        except Exception as e:
            self.instrumentation.end_span(span, status="error", **{"error.type": type(e).__name__})
            raise
        self.instrumentation.end_span(span, status="ok")
        return result

    def __repr__(self) -> str:
        return f"ChaosToolProxy(tool_name={self.tool_name!r}, original={self.original_callable!r})"
