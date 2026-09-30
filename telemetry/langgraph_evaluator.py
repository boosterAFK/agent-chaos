
from typing import List,Any

from telemetry.evaluator import MetricEvaluator
from langchain_core.messages import HumanMessage, ToolMessage


class LanggraphEvaluator(MetricEvaluator):
    def __init__(self, optimal_steps: int):
        super().__init__(optimal_steps)

    def get_actual_steps(self, messages: List[Any]) -> int:
        """
        Determines the actual steps taken in the final state.
        """
        actual_steps = sum(1 for m in messages if not isinstance(m, HumanMessage))  # Exclude human messages from step count
        return actual_steps

    def is_last_tool_call_safenet(self, messages: List[Any]) -> Any:
        """
        Retrieves the last tool call from the final state.
        """
        last_tool = next((m for m in reversed(messages) if isinstance(m, ToolMessage)), None)
        if last_tool is None:
            return 0.0
        return 1.0 if last_tool.additional_kwargs.get("terminal") else 0.0

 