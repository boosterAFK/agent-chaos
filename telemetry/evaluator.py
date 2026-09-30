from abc import abstractmethod
from pyexpat.errors import messages
from typing import Dict, Any, List


class MetricEvaluator:

    def __init__(self, optimal_steps: int):
        self.optimal_steps = optimal_steps

    def calculate_efficiency_ratio(self, final_state: Dict[str, Any]) -> float:
        """
        Calculates Step Efficiency Ratio: Optimal Steps / Actual Steps Taken.
        """
        messages = final_state.get("messages", [])
        # Each message represents a step (Human input, LLM reasoning, Tool execution)
        actual_steps = self.get_actual_steps(messages)
        
        if actual_steps == 0:
            return 0.0
            
        return self.optimal_steps / actual_steps

    def calculate_recovery_rate(self, final_state: Dict[str, Any]) -> float:
        """
        Calculates the percentage of recovered states after encountering a tool error.
        """
        messages = final_state.get("messages", [])
        errors_encountered = self.get_errors_count(messages)
        
        if errors_encountered == 0:
            return 1.0 
            
        # A successful trajectory ends in a valid state (not an error) despite encountering one
        if self.is_last_message_error(messages):
            return 0.0 
            
        return 1.0

    def calculate_graceful_termination(self, final_state: Dict[str, Any]) -> float:
        """
        Determines if the final state is a graceful termination method call (not an error).
        Returns 1.0 for graceful termination, 0.0 otherwise.
        """
        messages = final_state.get("messages", [])
        return 1.0 if not self.is_last_tool_call_safenet(messages) else 0.0

    @abstractmethod
    def is_last_tool_call_safenet(self, messages: list) -> Any:
        """
        Abstract method to retrieve the last tool call from the final state.
        """
        pass

    @abstractmethod
    def get_actual_steps(self, messages: list) -> int:
        """
        Abstract method to determine the actual steps taken in the final state.
        """
        pass

    def get_errors_count(self, messages: List[Any]) -> int:
        """
        Counts the number of tool errors encountered in the final state.
        """
        errors_encountered = sum(1 for m in messages if getattr(m, "status", None) == "error")
        return errors_encountered

    def is_last_message_error(self, messages: List[Any]) -> bool:
        """
        Determines if the last message in the final state is an error message.
        """
        if not messages:
            return False
        last_message = messages[-1]
        return getattr(last_message, "status", None) == "error"