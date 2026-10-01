from typing import Any, Dict

from langchain_core.messages import HumanMessage

from telemetry.metrics.base import Metric


class StepEfficiencyMetric(Metric):
    """
    Step Efficiency Ratio: optimal_steps / actual_steps.

    Measures how directly the agent reached the solution, penalizing
    meandering reasoning and unnecessary tool invocations. Drops (e.g. to
    0.33) when the agent panics under a transient fault and needs extra
    steps to recover.
    """

    def __init__(self, optimal_steps: int):
        super().__init__(name="step_efficiency")
        self.optimal_steps = optimal_steps

    def compute(self, trajectory: Dict[str, Any]) -> float:
        messages = trajectory.get("messages", [])
        actual_steps = self.get_actual_steps(messages)
        if actual_steps == 0:
            return 0.0
        return self.optimal_steps / actual_steps

    def get_actual_steps(self, messages: list) -> int:
        """
        Counts reasoning + tool-execution steps. The initial HumanMessage is
        the task input, not a step taken by the agent, so it is excluded.
        """
        return sum(1 for m in messages if not isinstance(m, HumanMessage))
