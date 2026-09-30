
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

 