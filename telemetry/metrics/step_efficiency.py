
from typing import Any, Dict

from telemetry.metrics.base import Metric


class StepEfficiencyMetric(Metric):
    def __init__(self, optimal_steps: int):
        self.optimal_steps = optimal_steps

    def evaluate(self, data: Dict[str, Any]) -> float:
        """
        Evaluates the Step Efficiency Metric based on the provided data.
        """
        messages = data.get("messages", [])
        actual_steps = self.get_actual_steps(messages)
        
        if actual_steps == 0:
            return 0.0
            
        return self.optimal_steps / actual_steps

    def get_actual_steps(self, messages: list) -> int:
        """
        Determines the actual steps taken in the final state.
        Each message represents a step (Human input, LLM reasoning, Tool execution).
        """
        return len(messages)