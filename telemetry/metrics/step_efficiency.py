from typing import Any, Dict, Optional

from langchain_core.messages import HumanMessage

from telemetry.metrics.base import Metric


class StepEfficiencyMetric(Metric):
    """
    Step Efficiency Ratio: baseline_steps / actual_steps.

    Measures how directly the agent reached the solution, penalizing
    meandering reasoning and unnecessary tool invocations.

    Two baselines:
      - ``clean``       : ``optimal_steps`` for a no-fault run. Penalizes the
                          agent for faults it could not avoid (degradation /
                          blast-radius view).
      - ``fault_aware`` : ``optimal_steps + scheduler.forced_extra_steps()``.
                          Grades recovery quality given the scheduled faults
                          were unavoidable (a perfect recovery scores 1.0).
    """

    def __init__(self, optimal_steps: int, scheduler: Optional[Any] = None, baseline: str = "clean"):
        super().__init__(name=f"step_efficiency/{baseline}")
        self.optimal_steps = optimal_steps
        self.scheduler = scheduler
        self.baseline = baseline

    def compute(self, trajectory: Dict[str, Any]) -> float:
        messages = trajectory.get("messages", [])
        actual_steps = self.get_actual_steps(messages)
        if actual_steps == 0:
            return 0.0
        return self._baseline_steps() / actual_steps

    def _baseline_steps(self) -> int:
        if self.baseline == "fault_aware" and self.scheduler is not None:
            return self.optimal_steps + self.scheduler.forced_extra_steps()
        return self.optimal_steps

    def get_actual_steps(self, messages: list) -> int:
        """
        Counts reasoning + tool-execution steps. The initial HumanMessage is
        the task input, not a step taken by the agent, so it is excluded.
        """
        return sum(1 for m in messages if not isinstance(m, HumanMessage))
