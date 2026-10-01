from abc import ABC, abstractmethod
from typing import Any

from injector.adapters.base import ToolAdapter
from runner.base import AgentRunner
from telemetry.evaluator import MetricEvaluator


class FrameworkProvider(ABC):
    """
    Abstract Factory producing a matched family of framework-specific objects
    (runner + evaluator + tool adapter). Concrete providers define their own
    constructor arguments per factory method, so the base stays permissive.
    """

    @abstractmethod
    def make_runner(self, *args: Any, **kwargs: Any) -> AgentRunner:
        ...

    @abstractmethod
    def make_tool_adapter(self, *args: Any, **kwargs: Any) -> ToolAdapter:
        ...

    @abstractmethod
    def make_evaluator(self, *args: Any, **kwargs: Any) -> MetricEvaluator:
        ...
